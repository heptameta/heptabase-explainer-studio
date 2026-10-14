"""No background music."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..schemas.timeline import Timeline
from .base import BackgroundMusicProvider


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["none"]


class Provider(BackgroundMusicProvider):
    name = "none"
    settings_model = Settings

    def make_track(self, timeline: Timeline, episode_number: int, settings: BaseModel, output_wav_file_path: Path,
                   sample_rate_hertz: int) -> bool:
        return False
