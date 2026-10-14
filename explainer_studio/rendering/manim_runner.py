"""Running scene files with ManimGL, one process per scene.

Each `scenes/<scene_id>.py` holds exactly one NarratedScene subclass; `cover.py` holds one CoverScene subclass and
`end_credits.py` one EndCreditsScene subclass. Every
process gets its own working folder (and, through scene_kit's patches, its own temporary directory), so parallel
renders never touch each other's files. A scene writes a JSON sidecar with its beats, sounds, automatic-check issues
and file excerpts; a failure comes back as the exception and the scene file's line, not a long traceback.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .. import user_dirs
from ..errors import StudioError
from ..paths import Series
from ..schemas.timeline import TimelineSound
from . import scene_lint

DEFAULT_END_CREDITS_FILE_PATH = Path(__file__).parent.parent / "scene_kit" / "default_end_credits.py"

# What a scene process reads (scene_kit.context and scene_kit.render_process). This module must not import
# scene_kit: importing it loads ManimGL, which parses the command line of whatever process imports it.
ENV_SERIES = "EXPLAINER_STUDIO_SERIES"
ENV_EPISODE = "EXPLAINER_STUDIO_EPISODE"
ENV_SCENE = "EXPLAINER_STUDIO_SCENE"
ENV_MODE = "EXPLAINER_STUDIO_MODE"  # preview | render
ENV_SIDECAR = "EXPLAINER_STUDIO_SIDECAR"
ENV_JOB = "EXPLAINER_STUDIO_JOB"
FPS = 30
PREVIEW_RESOLUTION = (1280, 720)
RENDER_RESOLUTION = (1920, 1080)
# The render re-encodes once more at the end, so its scene clips are kept close to lossless.
CRF_BY_MODE_MAP = {"preview": 20, "render": 12}


@dataclass
class SceneResult:
    scene_id: str
    video_file_path: Path
    duration_seconds: float
    beats: list[dict]
    sounds: list[TimelineSound]  # in scene time
    issues: list[dict]
    file_excerpts: list[dict]
    warnings: list[str]


class SceneRenderError(Exception):
    def __init__(self, scene_id: str, lines: list[str]):
        self.scene_id, self.lines = scene_id, lines
        super().__init__("\n".join(lines))


def choose_parallel_job_count(task_count: int) -> int:
    """How many ManimGL processes to run at once. They share the GPU: on an M4 Pro, eight scenes took 25 s with four
    processes, 31 s with three and 39 s with eight."""
    return max(1, min(task_count, 4, os.cpu_count() or 4))


# Checks before anything runs -----------------------------------------------------------------------------------
def _list_base_names(node: ast.ClassDef) -> list[str]:
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def validate_scene_file(path: Path, label: str) -> None:
    """Refuse a scene file that does not define exactly one NarratedScene subclass. A class whose base is imported
    from shared code may be a scene too; the ManimGL process confirms those."""
    if not path.is_file():
        raise StudioError(f"{label} is missing", "every scene in script.yaml needs scenes/<scene_id>.py",
                          f"write {path}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        raise StudioError(f"{label} is not valid Python", f"line {error.lineno}: {error.msg}",
                          f"fix line {error.lineno} of {path}") from None
    class_by_name_map = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def check_is_narrated_scene(class_name: str, seen: frozenset = frozenset()) -> bool:
        bases = _list_base_names(class_by_name_map[class_name])
        return "NarratedScene" in bases or any(base_name in class_by_name_map and base_name not in seen
                                               and check_is_narrated_scene(base_name, seen | {class_name})
                                               for base_name in bases)

    scene_class_names = [name for name in class_by_name_map if check_is_narrated_scene(name)]
    classes_with_imported_bases = [name for name in class_by_name_map if not check_is_narrated_scene(name)
                                   and any(base_name not in class_by_name_map
                                           for base_name in _list_base_names(class_by_name_map[name]))]
    if len(scene_class_names) > 1:
        raise StudioError(f"{label} defines {len(scene_class_names)} NarratedScene subclasses "
                          f"({', '.join(scene_class_names)})",
                          "each scene file holds exactly one; render uses it",
                          "keep one scene class; put shared base classes in production/shared/<name>.py")
    if not scene_class_names and not classes_with_imported_bases:
        raise StudioError(f"{label} defines no NarratedScene subclass",
                          "each scene file holds exactly one, which preview and render run",
                          "define `class <Name>(NarratedScene):` with a construct() method")


def lint_series_code(series: Series, file_paths: list[Path]) -> None:
    shared_file_paths = sorted(series.shared_dir_path.rglob("*.py")) if series.shared_dir_path.is_dir() else []
    scene_lint.require_clean_scene_code([*file_paths, *shared_file_paths], series.production_dir_path)


# Running --------------------------------------------------------------------------------------------------------
def _write_manim_config(work_dir_path: Path, resolution: tuple[int, int], crf: int) -> Path:
    width, height = resolution
    ffmpeg_path = user_dirs.find_tool("ffmpeg") or "ffmpeg"
    config_file_path = work_dir_path / "manim_config.yml"
    config_file_path.write_text("\n".join([
        "camera:", f"  resolution: ({width}, {height})", '  background_color: "#000000"', f"  fps: {FPS}",
        "file_writer:", f"  ffmpeg_bin: {json.dumps(ffmpeg_path)}", f"  crf: {crf}",
        "text:", '  alignment: "LEFT"',
        "log_level: ERROR",
    ]) + "\n", encoding="utf-8")
    return config_file_path


def _format_failure_lines(label: str, work_dir_path: Path, result: subprocess.CompletedProcess) -> list[str]:
    error_file_path = work_dir_path / "error.json"
    if error_file_path.exists():
        error_report = json.loads(error_file_path.read_text(encoding="utf-8"))
        lines = [f"{label} failed: {error_report['type']}: {error_report['message']}"]
        lines += [f"  {frame['file_path']}:{frame['line']} in {frame['function'] or '(module)'}: {frame['code']}"
                  for frame in error_report["frames"][-4:]]
        if not error_report["frames"]:
            lines += ["  " + line.rstrip() for chunk in error_report["traceback"][-3:] for line in chunk.splitlines()]
        return lines
    tail_lines = (result.stderr or result.stdout or "").strip().splitlines()[-12:]
    return [f"{label} failed (exit code {result.returncode})", *("  " + line for line in tail_lines)]


def _run_scene_process(series: Series, episode_id: str, name: str, file_path: Path, kind: str, mode: str,
                       work_dir_path: Path, resolution: tuple[int, int]) -> subprocess.CompletedProcess:
    work_dir_path.mkdir(parents=True, exist_ok=True)
    config_file_path = _write_manim_config(work_dir_path, resolution, CRF_BY_MODE_MAP[mode])
    job = {"kind": kind, "file_path": str(file_path), "name": name,
           "production_dir_path": str(series.production_dir_path), "error_file_path": str(work_dir_path / "error.json")}
    (work_dir_path / "job.json").write_text(json.dumps(job), encoding="utf-8")
    width, height = resolution
    command = [sys.executable, "-m", "explainer_studio.scene_kit.render_process", str(file_path), "-w",
               *(["-s"] if kind in ("cover", "end_credits") else []), "--config_file", str(config_file_path), "--video_dir",
               str(work_dir_path),
               "--file_name", "output", "-r", f"{width}x{height}", "-q"]
    environment = user_dirs.compute_tool_environment()
    environment.update({ENV_JOB: str(work_dir_path / "job.json"), ENV_SERIES: str(series.root_dir_path),
                        ENV_EPISODE: episode_id, ENV_MODE: mode, ENV_SIDECAR: str(work_dir_path / "sidecar.json"),
                        "PYTHONUNBUFFERED": "1"})
    if kind == "scene":
        environment[ENV_SCENE] = name
    else:
        environment.pop(ENV_SCENE, None)
    return subprocess.run(command, cwd=work_dir_path, env=environment, capture_output=True, text=True, check=False)


def render_scene(series: Series, episode_id: str, scene_id: str, mode: str, work_dir_path: Path) -> SceneResult:
    """Render one scene to work_dir_path/output.mp4 (silent) and read its sidecar. Raises SceneRenderError."""
    scene_file_path = series.get_episode_paths(episode_id).get_scene_file_path(scene_id)
    label = f"scenes/{scene_id}.py"
    resolution = RENDER_RESOLUTION if mode == "render" else PREVIEW_RESOLUTION
    result = _run_scene_process(series, episode_id, scene_id, scene_file_path, "scene", mode, work_dir_path, resolution)
    sidecar_file_path, video_file_path = work_dir_path / "sidecar.json", work_dir_path / "output.mp4"
    if result.returncode != 0 or not sidecar_file_path.exists() or not video_file_path.exists():
        raise SceneRenderError(scene_id, _format_failure_lines(label, work_dir_path, result))
    sidecar = json.loads(sidecar_file_path.read_text(encoding="utf-8"))
    return SceneResult(scene_id, video_file_path, measure_media_duration_seconds(video_file_path), sidecar["beats"],
                       [TimelineSound.model_validate(sound) for sound in sidecar["sounds"]], sidecar["issues"],
                       sidecar["file_excerpts"], sidecar["warnings"])


def render_cover(series: Series, episode_id: str, work_dir_path: Path) -> Path:
    """Render cover.py's last frame to work_dir_path/output.png at 1080p. Raises SceneRenderError."""
    cover_scene_file_path = series.get_episode_paths(episode_id).cover_scene_file_path
    result = _run_scene_process(series, episode_id, "cover", cover_scene_file_path, "cover", "render", work_dir_path,
                                RENDER_RESOLUTION)
    image_file_path = work_dir_path / "output.png"
    if result.returncode != 0 or not image_file_path.exists():
        raise SceneRenderError("cover", _format_failure_lines("cover.py", work_dir_path, result))
    return image_file_path


def render_end_credits(series: Series, episode_id: str, work_dir_path: Path) -> Path:
    """Render the end credits page (end_credits.py, or the default page when the episode has none) to
    work_dir_path/output.png at 1080p. Raises SceneRenderError."""
    end_credits_scene_file_path = series.get_episode_paths(episode_id).end_credits_scene_file_path
    has_own_file = end_credits_scene_file_path.is_file()
    result = _run_scene_process(series, episode_id, "end_credits",
                                end_credits_scene_file_path if has_own_file else DEFAULT_END_CREDITS_FILE_PATH,
                                "end_credits", "render", work_dir_path, RENDER_RESOLUTION)
    image_file_path = work_dir_path / "output.png"
    if result.returncode != 0 or not image_file_path.exists():
        label = "end_credits.py" if has_own_file else "the default end credits"
        raise SceneRenderError("end_credits", _format_failure_lines(label, work_dir_path, result))
    return image_file_path


def render_in_parallel(tasks: list[tuple[str, Callable[[], object]]], report_progress: Callable[[str], None]
                       ) -> tuple[dict[str, object], dict[str, list[str]]]:
    """Run (name, function) tasks in parallel processes' worth of threads; returns results and failures by name."""
    result_by_name_map, failure_lines_by_name_map = {}, {}

    def run_task(task):
        name, function = task
        try:
            result_by_name_map[name] = function()
            report_progress(f"  {name}: done")
        except SceneRenderError as error:
            failure_lines_by_name_map[name] = error.lines
            report_progress(f"  {name}: failed")

    with ThreadPoolExecutor(max_workers=choose_parallel_job_count(len(tasks))) as pool:
        list(pool.map(run_task, tasks))
    return result_by_name_map, failure_lines_by_name_map


def measure_media_duration_seconds(path: Path) -> float:
    ffprobe_path = user_dirs.find_tool("ffprobe") or "ffprobe"
    result = subprocess.run([ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                             str(path)], capture_output=True, text=True, check=False)
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise StudioError(f"cannot read the length of {path}", result.stderr.strip()[-300:],
                          "check that ffmpeg is installed (`explainer-studio doctor`)") from None


def create_work_dir(prefix: str) -> Path:
    """A fresh folder in the system temporary directory, outside the series."""
    return Path(tempfile.mkdtemp(prefix=f"explainer-studio-{prefix}-"))
