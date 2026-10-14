"""The interface every background music provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from ..schemas.timeline import Timeline

if TYPE_CHECKING:
    from . import BackgroundMusicProviderName


class BackgroundMusicProvider(ABC):
    name: ClassVar[BackgroundMusicProviderName]  # the plan's `provider_name`
    settings_model: ClassVar[type[BaseModel]]  # the plan's `background_music` fields for this provider

    @abstractmethod
    def make_track(self, timeline: Timeline, episode_number: int, settings: BaseModel, output_wav_file_path: Path,
                   sample_rate_hertz: int) -> bool:
        """Write a stereo track as long as the timeline to `output_wav_file_path`. Return False when there is no
        music."""
