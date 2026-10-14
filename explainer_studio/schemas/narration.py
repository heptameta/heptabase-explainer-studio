"""episodes/<episode>/narration/narration.yaml: what `narrate` produced. Written by the tool only."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .plan import NarrationSettings


class NarratedBeat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    spoken_text: str  # the text sent to the voice
    duration_seconds: float = Field(gt=0)


class NarrationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    settings: NarrationSettings  # the plan's settings when these files were made, with only the fields it wrote
    beats: list[NarratedBeat] = []

    def find_narrated_beat(self, beat_id: str) -> NarratedBeat | None:
        return next((beat for beat in self.beats if beat.beat_id == beat_id), None)
