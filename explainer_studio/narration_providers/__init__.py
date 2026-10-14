"""Narration providers: one module per service, all implementing `base.NarrationProvider`.

To add a provider, write one module with a `Settings` model (its plan fields, including `provider_name: Literal[<its
name>]`) and a provider class that names it in `settings_model`, then add its name to `NarrationProviderName` and
register it in `PROVIDER_BY_NAME_MAP` below. Everything else reads `PROVIDER_BY_NAME_MAP`: `schemas/plan.py` builds the
plan's `narration` field from the settings models, `setup narration` lists the providers with their `description`, and
the plan page offers them.
"""

from __future__ import annotations

from typing import Literal

from . import elevenlabs, macos_say, openai, voai
from .base import NarrationProvider

NarrationProviderName = Literal["elevenlabs", "openai", "voai", "macos-say"]

PROVIDER_BY_NAME_MAP: dict[NarrationProviderName, type[NarrationProvider]] = {
    module.Provider.name: module.Provider for module in (elevenlabs, openai, voai, macos_say)
}

SETTINGS_MODELS = tuple(provider.settings_model for provider in PROVIDER_BY_NAME_MAP.values())


def get_provider(provider_name: NarrationProviderName) -> NarrationProvider:
    return PROVIDER_BY_NAME_MAP[provider_name]()
