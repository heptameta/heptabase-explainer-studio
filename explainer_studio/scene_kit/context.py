"""Which series, episode and scene the running scene file belongs to, and what its beats say.

`manim_runner` sets the environment variables below. A scene file run straight with `manimgl` falls back to its own
path (`production/episodes/<episode>/scenes/<scene>.py`), so it still finds its narration.
"""

from __future__ import annotations

import functools
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .. import languages
from ..narrate import find_beat_ids_needing_narration, load_narration_record
from ..paths import PRODUCTION_DIR_NAME, Series, convert_path_to_production_relative_path
from ..plan import load_plan
from ..rendering.manim_runner import ENV_EPISODE, ENV_MODE, ENV_SCENE, ENV_SERIES, ENV_SIDECAR
from ..script import load_script, resolve_pause_duration_seconds


@dataclass(frozen=True)
class BeatTiming:
    """When a beat's line plays in its scene: the line, its length, the pause after it and its audio."""

    id: str
    scene_id: str
    narration_text: str
    duration_seconds: float  # the narration's length, or the language table's estimate when it is not narrated yet
    pause_duration_seconds: float  # silence after the line
    audio_file_path: Path | None  # the narration WAV when the beat is narrated and current


@dataclass(frozen=True)
class SceneContext:
    series: Series | None
    episode_id: str | None
    scene_id: str | None
    mode: str
    sidecar_file_path: Path | None
    language_code: str
    beat_timing_by_id_map: dict[str, BeatTiming]

    @property
    def production_dir_path(self) -> Path:
        return self.series.production_dir_path if self.series else Path.cwd()

    def resolve_path(self, path: str | Path) -> Path:
        """A path written in a scene file: absolute, or relative to production/."""
        candidate = Path(path).expanduser()
        return candidate if candidate.is_absolute() else self.production_dir_path / candidate

    def convert_path_to_production_relative_path(self, path: Path) -> str:
        """How a file is written in series records: relative to production/ when inside it."""
        return convert_path_to_production_relative_path(path, self.production_dir_path)

    def list_scene_beat_ids(self) -> list[str]:
        return [beat.id for beat in self.beat_timing_by_id_map.values() if beat.scene_id == self.scene_id]


def _parse_scene_file_location(scene_file_path: Path | None) -> tuple[Path | None, str | None, str | None]:
    if scene_file_path is None:
        return None, None, None
    parts = scene_file_path.resolve().parts
    if len(parts) >= 5 and parts[-2] == "scenes" and parts[-4] == "episodes" and parts[-5] == PRODUCTION_DIR_NAME:
        return Path(*parts[:-5]), parts[-3], Path(parts[-1]).stem
    if len(parts) >= 4 and parts[-1] == "cover.py" and parts[-3] == "episodes" and parts[-4] == PRODUCTION_DIR_NAME:
        return Path(*parts[:-4]), parts[-2], None
    return None, None, None


def _load_beat_timings(series: Series, episode_id: str) -> tuple[str, dict[str, BeatTiming]]:
    plan = load_plan(series)
    script = load_script(series, episode_id)
    language_code = plan.resolve_episode_language_code(episode_id)
    narration_settings = plan.resolve_episode_narration_settings(episode_id)
    language = languages.resolve_language(language_code)
    stale_beat_ids = set(find_beat_ids_needing_narration(series, plan, episode_id, script))
    narration_record = load_narration_record(series, episode_id)
    episode_paths = series.get_episode_paths(episode_id)
    beat_timing_by_id_map = {}
    for scene in script.scenes:
        for beat in scene.beats:
            if beat.id in stale_beat_ids or narration_record is None:
                provider_name = narration_settings.provider_name if narration_settings else None
                duration_seconds = language.estimate_speech_seconds(beat.narration_text, provider_name)
                audio_file_path = None
            else:
                duration_seconds = narration_record.find_narrated_beat(beat.id).duration_seconds
                audio_file_path = episode_paths.get_narration_audio_file_path(beat.id)
            beat_timing_by_id_map[beat.id] = BeatTiming(beat.id, scene.id, beat.narration_text.strip(),
                                                        float(duration_seconds),
                                                        float(resolve_pause_duration_seconds(beat)), audio_file_path)
    return language_code, beat_timing_by_id_map


@functools.cache
def get_scene_context() -> SceneContext:
    """The context of this process's scene: the environment manim_runner sets, else the location of the scene file
    `manimgl` was given."""
    series_root_dir_path = os.environ.get(ENV_SERIES)
    episode_id = os.environ.get(ENV_EPISODE)
    scene_id = os.environ.get(ENV_SCENE)
    if not series_root_dir_path:
        scene_file_path = next((Path(arg) for arg in sys.argv[1:] if arg.endswith(".py")), None)
        found_root, episode_id, scene_id = _parse_scene_file_location(scene_file_path)
        series_root_dir_path = str(found_root) if found_root else None
    sidecar_file_path = os.environ.get(ENV_SIDECAR)
    mode = os.environ.get(ENV_MODE, "preview")
    if not series_root_dir_path:
        return SceneContext(None, None, None, mode, Path(sidecar_file_path) if sidecar_file_path else None, "en", {})
    series = Series(Path(series_root_dir_path))
    language_code, beat_timing_by_id_map = _load_beat_timings(series, episode_id) if episode_id else ("en", {})
    return SceneContext(series, episode_id, scene_id, mode, Path(sidecar_file_path) if sidecar_file_path else None,
                        language_code, beat_timing_by_id_map)
