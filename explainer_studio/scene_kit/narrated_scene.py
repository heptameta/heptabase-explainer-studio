"""NarratedScene: a scene whose timing follows the narration of its beats.

    with self.play_beat("water_levels") as beat:
        self.play_sound("whoosh_in")
        self.play(Write(title), run_time=beat.get_seconds_until(0.4))
        self.play(FadeIn(sub))
    # leaving the block waits until the line ends, plus the beat's pause_duration_seconds (default 0.3 s)

    with self.play_beat("intro_bach") as beat:      # the script leaves a 6 s pause after this line for the music
        self.play(FadeIn(score))
        self.wait(beat.remaining_seconds)
        self.play_sound("shared/assets/audio/air_on_g.ogg")  # starts as the line ends and plays through the pause
        self.play(light_up(bass_notes), run_time=6)

A narrated, current beat uses its WAV's length; in preview a beat without narration lasts the language table's
estimate, silently. The automatic checks run at the end of every beat. When the scene ends it writes its beats,
sounds, issues and file excerpts to the JSON sidecar `manim_runner` reads.
"""

from __future__ import annotations

import json
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from manimlib import InteractiveScene

from .. import user_dirs
from ..rendering import sound_effects
from ..schemas.timeline import TimelineSound, TimelineSoundEffect, TimelineSoundFile
from . import file_excerpts, layout_checks, style
from .context import get_scene_context

__all__ = ["Beat", "NarratedScene"]


@dataclass
class Beat:
    scene: NarratedScene
    id: str
    narration_text: str
    start_seconds: float
    duration_seconds: float

    @property
    def elapsed_seconds(self) -> float:
        return self.scene.time - self.start_seconds

    @property
    def remaining_seconds(self) -> float:
        return max(self.start_seconds + self.duration_seconds - self.scene.time, 0)

    def get_seconds_until(self, fraction: float) -> float:
        """Seconds from now until `fraction` of the line has been said (for run_time=)."""
        return max(self.start_seconds + fraction * self.duration_seconds - self.scene.time, 0)


class SceneError(Exception):
    """A mistake in the scene file that the runner reports with the file and line."""


def _probe_media(path: Path) -> tuple[float, bool]:
    """(length in seconds, whether it has sound) of an audio or video file."""
    ffprobe = user_dirs.find_tool("ffprobe") or "ffprobe"
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of",
                             "json", str(path)], capture_output=True, text=True, check=False)
    try:
        probe_output = json.loads(result.stdout)
        duration_seconds = float(probe_output["format"]["duration"])
    except (ValueError, KeyError):
        raise SceneError(f"cannot read the length of {path}: is it an audio or video file?") from None
    return duration_seconds, any(stream.get("codec_type") == "audio" for stream in probe_output.get("streams", []))


class NarratedScene(InteractiveScene):
    """The base class of every scene file: one subclass per scenes/<scene_id>.py."""

    def setup(self):
        super().setup()
        self.context = get_scene_context()
        self.recorded_beats: list[dict] = []
        self.recorded_sounds: list[dict] = []
        self.recorded_issues: list[dict] = []

    @property
    def _is_writing(self) -> bool:
        return not self.skip_animations

    @contextmanager
    def play_beat(self, beat_id: str):
        context = self.context
        timing = context.beat_timing_by_id_map.get(beat_id)
        if timing is None:
            raise SceneError(f"beat {beat_id!r} is not in {context.episode_id}/script.yaml; use a beat id of scene "
                             f"{context.scene_id}: {', '.join(context.list_scene_beat_ids()) or '(none)'}")
        if context.scene_id and timing.scene_id != context.scene_id:
            raise SceneError(f"beat {beat_id!r} belongs to scene {timing.scene_id!r} in script.yaml, "
                             f"not to {context.scene_id!r}")
        if any(recorded_beat["beat_id"] == beat_id for recorded_beat in self.recorded_beats):
            raise SceneError(f"beat {beat_id!r} is played twice; every beat is one play_beat block")
        if context.mode == "render" and timing.audio_file_path is None:
            raise SceneError(f"beat {beat_id!r} has no current narration; run `explainer-studio narrate "
                             f"{context.episode_id}` before render")
        start_seconds = self.time
        yield Beat(self, beat_id, timing.narration_text, start_seconds, timing.duration_seconds)
        check_time_seconds = self.time
        problems, metrics = layout_checks.run_automatic_checks(self)
        self.recorded_issues += [{"check_name": check_name, "beat_id": beat_id, "detail": detail}
                                 for check_name, detail in problems]
        self.recorded_beats.append({"beat_id": beat_id, "start_seconds": start_seconds,
                                    "duration_seconds": timing.duration_seconds,
                                    "pause_duration_seconds": timing.pause_duration_seconds,
                                    "audio_file_path": str(timing.audio_file_path) if timing.audio_file_path else None,
                                    "check_time_seconds": check_time_seconds, "metrics": metrics})
        remaining_seconds = start_seconds + timing.duration_seconds + timing.pause_duration_seconds - self.time
        if remaining_seconds > 1.0 / self.camera.fps:
            self.wait(remaining_seconds)

    def play_sound(self, name_or_path: str, gain_decibels: float = 0.0,
                   should_duck_background_music: bool | None = None, *, source_start_seconds: float = 0.0,
                   duration_seconds: float | None = None) -> None:
        """Play a sound from now: a built-in effect (whoosh_in, whoosh_out, ghost, questioner, bubble, title) or an
        audio file (relative to production/). Effects leave the background music alone by default; files duck it.
        source_start_seconds and duration_seconds play only part of a file. A video without sound adds nothing."""
        if sound_effects.check_is_effect(name_or_path):
            source = TimelineSoundEffect(kind="effect", effect_name=name_or_path)
            resolved_duration_seconds = (duration_seconds
                                         or sound_effects.DURATION_SECONDS_BY_EFFECT_NAME_MAP[name_or_path])
            should_duck = bool(should_duck_background_music)
        else:
            path = self.context.resolve_path(name_or_path)
            if not path.is_file():
                raise SceneError(f"sound {name_or_path!r} is neither a built-in effect "
                                 f"({', '.join(sound_effects.DURATION_SECONDS_BY_EFFECT_NAME_MAP)}) nor a file at "
                                 f"{path}")
            file_duration_seconds, has_audio = _probe_media(path)
            if not has_audio:
                return
            source_file_path = self.context.convert_path_to_production_relative_path(path)
            if Path(source_file_path).is_absolute():
                raise SceneError(f"{path} has sound but is outside production/, so the video's timeline cannot name "
                                 "it; copy it under production/ (shared/assets/ or the episode's assets/) and play it "
                                 "from there")
            source = TimelineSoundFile(kind="file", source_file_path=source_file_path,
                                       source_start_seconds=float(source_start_seconds))
            resolved_duration_seconds = (duration_seconds if duration_seconds is not None
                                         else max(0.0, file_duration_seconds - source_start_seconds))
            should_duck = True if should_duck_background_music is None else should_duck_background_music
        if self._is_writing:
            # recorded as the timeline stores a sound, in scene time
            sound = TimelineSound(start_seconds=float(self.time), sound=source,
                                  duration_seconds=float(resolved_duration_seconds),
                                  gain_decibels=float(gain_decibels), should_duck_background_music=should_duck)
            self.recorded_sounds.append(sound.model_dump(mode="json"))

    def tear_down(self):
        try:
            problems, _ = layout_checks.run_automatic_checks(self)
            self.recorded_issues += [{"check_name": check_name, "beat_id": None, "detail": detail}
                                     for check_name, detail in problems]
        finally:
            self._write_sidecar()
            super().tear_down()

    def _write_sidecar(self) -> None:
        sidecar_file_path = self.context.sidecar_file_path
        if sidecar_file_path is None:
            return
        unique_issues, seen_keys = [], set()
        for issue in self.recorded_issues:
            key = (issue["check_name"], issue["detail"])
            if key not in seen_keys:
                seen_keys.add(key)
                unique_issues.append(issue)
        sidecar = {"beats": self.recorded_beats, "sounds": self.recorded_sounds, "issues": unique_issues,
                   "file_excerpts": file_excerpts.RECORDED_FILE_EXCERPTS, "warnings": style.FONT_WARNINGS}
        # ManimGL keeps time and sizes as numpy floats
        sidecar_file_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=1,
                                                default=lambda value: value.item()),
                                     encoding="utf-8")
