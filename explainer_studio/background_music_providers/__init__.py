"""Background music providers: one module per source, all implementing `base.BackgroundMusicProvider`.

To add a provider, write one module with a `Settings` model (its plan fields, including `provider_name: Literal[<its
name>]`) and a provider class that names it in `settings_model`, then add its name to `BackgroundMusicProviderName` and
register it in `PROVIDER_BY_NAME_MAP` below.

`render` mixes the track a provider returns under the narration and sounds; providers only make the track.
"""

from __future__ import annotations

from typing import Literal

from . import none, synthesized_piano
from .base import BackgroundMusicProvider

BackgroundMusicProviderName = Literal["synthesized-piano", "none"]

PROVIDER_BY_NAME_MAP: dict[BackgroundMusicProviderName, type[BackgroundMusicProvider]] = {
    module.Provider.name: module.Provider for module in (synthesized_piano, none)
}

SETTINGS_MODELS = tuple(provider.settings_model for provider in PROVIDER_BY_NAME_MAP.values())


def get_provider(provider_name: BackgroundMusicProviderName) -> BackgroundMusicProvider:
    return PROVIDER_BY_NAME_MAP[provider_name]()
