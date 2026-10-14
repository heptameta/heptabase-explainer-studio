"""render/timeline.json: where every scene, beat and sound sits in the finished video, cover and end credits
included."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimelineBeat(StrictModel):
    beat_id: str
    start_seconds: float
    duration_seconds: float


class TimelineScene(StrictModel):
    scene_id: str
    start_seconds: float
    duration_seconds: float
    beats: list[TimelineBeat] = []


# the built-in sound effects (`rendering.sound_effects`)
SoundEffectName = Literal["whoosh_in", "whoosh_out", "ghost", "questioner", "bubble", "title"]


class TimelineSoundEffect(StrictModel):
    kind: Literal["effect"]
    effect_name: SoundEffectName


class TimelineSoundFile(StrictModel):
    kind: Literal["file"]
    source_file_path: str  # relative to production/, never absolute: an audio file, or a video whose sound plays
    source_start_seconds: float = 0.0  # where in the file playback starts


TimelineSoundSource = Annotated[TimelineSoundEffect | TimelineSoundFile, Field(discriminator="kind")]


class TimelineSound(StrictModel):
    """A sound in the video. A scene's sidecar records its sounds in this shape too, in scene time."""

    start_seconds: float
    sound: TimelineSoundSource
    duration_seconds: float = Field(ge=0)
    gain_decibels: float = 0.0
    should_duck_background_music: bool


class Timeline(StrictModel):
    narration_digest: str
    duration_seconds: float
    cover_duration_seconds: float = 1.0
    end_credits_duration_seconds: float = 0.0  # the end credits page after the last scene
    scenes: list[TimelineScene] = []
    sounds: list[TimelineSound] = []

    def find_beat_at(self, time_seconds: float) -> TimelineBeat | None:
        for scene in self.scenes:
            for beat in scene.beats:
                if beat.start_seconds <= time_seconds < beat.start_seconds + beat.duration_seconds:
                    return beat
        return None
