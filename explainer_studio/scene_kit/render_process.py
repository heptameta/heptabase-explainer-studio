"""The entry point of one ManimGL process: render one scene file (or the cover, or the end credits) as
`manim_runner` asked.

    EXPLAINER_STUDIO_JOB=<job.json> python -m explainer_studio.scene_kit.render_process <manimgl arguments>

ManimGL reads its configuration from sys.argv the moment manimlib is first imported (here, by the scene_kit package
itself), so the runner passes ManimGL's own arguments on this command line and the job (which class to look for,
where to report) through the environment. A failure is written to the job's error file as the exception plus the
frames inside the series, so the runner can name the scene file and line instead of printing a long traceback.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
import traceback
from pathlib import Path

from ..rendering.manim_runner import ENV_JOB


def _find_scene_class(module, kind: str):
    from manimlib import Scene

    from .cover import CoverScene
    from .credits import EndCreditsScene
    from .narrated_scene import NarratedScene

    base_class = NarratedScene if kind == "scene" else Scene
    still_class = {"cover": CoverScene, "end_credits": EndCreditsScene}.get(kind)
    scene_classes = [cls for _, cls in inspect.getmembers(module, inspect.isclass)
                     if issubclass(cls, base_class) and cls.__module__ == module.__name__]
    if still_class and len(scene_classes) > 1:
        scene_classes = [cls for cls in scene_classes if issubclass(cls, still_class)] or scene_classes
    if len(scene_classes) != 1:
        names = ", ".join(cls.__name__ for cls in scene_classes) or "none"
        class_description = f"{(still_class or NarratedScene).__name__} subclass"
        raise RuntimeError(f"the file must define exactly one {class_description}; it defines {names}. "
                           "Put shared base classes in production/shared/<name>.py")
    return scene_classes[0]


def _extract_user_frames(error: BaseException, production_dir_path: Path) -> list[dict]:
    def convert_path_to_production_relative_path(filename: str) -> str | None:
        try:
            return Path(filename).resolve().relative_to(production_dir_path.resolve()).as_posix()
        except ValueError:
            return None

    frames = [{"file_path": convert_path_to_production_relative_path(frame.filename), "line": frame.lineno,
               "function": frame.name, "code": (frame.line or "").strip()}
              for frame in traceback.extract_tb(error.__traceback__)
              if convert_path_to_production_relative_path(frame.filename)]
    if isinstance(error, SyntaxError) and error.filename and convert_path_to_production_relative_path(error.filename):
        frames.append({"file_path": convert_path_to_production_relative_path(error.filename), "line": error.lineno,
                       "function": "", "code": (error.text or "").strip()})
    return frames


def main() -> int:
    job = json.loads(Path(os.environ[ENV_JOB]).read_text(encoding="utf-8"))
    production_dir_path = Path(job["production_dir_path"])
    sys.path.insert(0, str(production_dir_path))  # scene files import shared code as `from shared.<name> import ...`
    try:
        from addict import Dict
        from manimlib.config import manim_config

        spec = importlib.util.spec_from_file_location(f"explainer_scene_{job['name']}", job["file_path"])
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        scene = _find_scene_class(module, job["kind"])(**Dict(manim_config.scene))
        scene.run()
    except BaseException as error:  # noqa: BLE001  (every failure goes to the runner)
        report = {"type": type(error).__name__, "message": str(error).strip(),
                  "frames": _extract_user_frames(error, production_dir_path),
                  "traceback": traceback.format_exception(type(error), error, error.__traceback__)[-6:]}
        Path(job["error_file_path"]).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
