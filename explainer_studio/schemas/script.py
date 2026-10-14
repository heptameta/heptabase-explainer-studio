"""episodes/<episode>/script.yaml: scenes and beats. Everything else about teaching lives in the free-form design.md."""

from __future__ import annotations

import hashlib
import keyword
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_id(value: str, id_kind: str) -> str:
    if not ID_PATTERN.match(value):
        raise ValueError(f"{id_kind} id {value!r} must use lowercase letters, digits and underscores, starting with a "
                         "letter")
    if keyword.iskeyword(value):
        raise ValueError(f"{id_kind} id {value!r} is a Python keyword")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Beat(StrictModel):
    id: str
    narration_text: str = Field(min_length=1)  # what the beat says; the subtitle shows it
    visual: str = Field(min_length=1)
    pause_duration_seconds: float | None = Field(default=None, ge=0)
    citation: str | None = None
    spoken_text_override: str | None = None  # replaces the automatic rewrite of the narration text for the voice

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        return validate_id(value, "beat")

    @field_validator("citation", mode="before")
    @classmethod
    def citation_as_text(cls, value: object) -> object:
        return str(value) if isinstance(value, (int, float)) else value


class Scene(StrictModel):
    id: str
    purpose: str = Field(min_length=1)
    beats: list[Beat] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        return validate_id(value, "scene")


class Script(StrictModel):
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> Script:
        scene_ids = [scene.id for scene in self.scenes]
        beat_ids = [beat.id for scene in self.scenes for beat in scene.beats]
        duplicates = sorted({scene_id for scene_id in scene_ids if scene_ids.count(scene_id) > 1})
        if duplicates:
            raise ValueError(f"scene ids must be unique; repeated: {', '.join(duplicates)}")
        duplicates = sorted({beat_id for beat_id in beat_ids if beat_ids.count(beat_id) > 1})
        if duplicates:
            raise ValueError(f"beat ids must be unique within the episode; repeated: {', '.join(duplicates)}")
        return self

    def list_beats(self) -> list[Beat]:
        return [beat for scene in self.scenes for beat in scene.beats]

    def get_scene(self, scene_id: str) -> Scene:
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        raise KeyError(scene_id)


def compute_narration_digest(narration_texts: list[str]) -> str:
    """The fingerprint of an episode's narration text: only the words, in order."""
    return hashlib.sha256("\n".join(narration_texts).encode("utf-8")).hexdigest()[:12]


def compute_script_narration_digest(script: Script) -> str:
    return compute_narration_digest([beat.narration_text.strip() for beat in script.list_beats()])
