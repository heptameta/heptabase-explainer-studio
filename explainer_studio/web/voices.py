"""The narration choices the plan page offers for the series language: the providers that speak it, and each provider's
suggested voices for it, with descriptions and where to hear more.

The page's voice menu also keeps the plan's current value and offers "Other" for any id the list does not have (a
cloned ElevenLabs voice, another VoAI speaker), so the list only has to cover the common choices.
"""

from __future__ import annotations

import subprocess
import sys

from ..narration_providers import PROVIDER_BY_NAME_MAP
from ..narration_providers.base import SuggestedVoice
from ..narration_providers.macos_say import list_installed_voices


def _list_macos_voices() -> list[tuple[str, str]]:
    """(name, locale) of the installed `say` voices; empty off macOS."""
    if sys.platform != "darwin":
        return []
    try:
        return list(list_installed_voices().items())
    except (OSError, subprocess.SubprocessError):
        return []


def _list_voices(provider_name: str, language_code: str) -> tuple[SuggestedVoice, ...]:
    if provider_name != "macos-say":
        return PROVIDER_BY_NAME_MAP[provider_name].list_suggested_voices(language_code)
    language_prefix = language_code.replace("-", "_").split("_")[0].lower()
    language_region = language_code.replace("-", "_").lower()
    matching_voices = [voice for voice in _list_macos_voices() if voice[1].lower().split("_")[0] == language_prefix]
    preferred_voices = [voice for voice in matching_voices if voice[1].lower() == language_region] or matching_voices
    return tuple(SuggestedVoice(voice_name, voice_name) for voice_name, _ in preferred_voices)


def _resolve_default_voice(provider_name: str, language_code: str) -> str | None:
    if provider_name == "macos-say":
        return None  # `say` picks the language's voice itself
    voices = PROVIDER_BY_NAME_MAP[provider_name].list_suggested_voices(language_code)
    return voices[0].id if voices else None


def get_voice_field(provider_name: str) -> str:
    return PROVIDER_BY_NAME_MAP[provider_name].voice_field if provider_name in PROVIDER_BY_NAME_MAP else "voice"


def find_voice_display_name(provider_name: str, voice_id: str, language_code: str) -> str | None:
    """The suggested voice's display name for `voice_id`, or None when it is not suggested for the language."""
    if provider_name not in PROVIDER_BY_NAME_MAP:
        return None
    suggested_voices = PROVIDER_BY_NAME_MAP[provider_name].list_suggested_voices(language_code)
    return next((voice.display_name for voice in suggested_voices if voice.id == voice_id), None)


def build_default_narration_settings(provider_name: str, language_code: str) -> dict[str, object]:
    """The narration block written when the page switches to `provider_name`."""
    settings: dict[str, object] = {"provider_name": provider_name}
    voice = _resolve_default_voice(provider_name, language_code)
    if voice is not None:
        settings[get_voice_field(provider_name)] = voice
    return settings


def list_narration_provider_choices(language_code: str) -> list[dict[str, object]]:
    """The page's provider menu for the series language, in `PROVIDER_BY_NAME_MAP` order (ElevenLabs first)."""
    return [{"name": provider_name, "displayName": provider.display_name, "isPaid": provider.is_paid,
             "voiceField": get_voice_field(provider_name),
             "voicesPageUrl": provider.voices_page_url or None,
             "voicePageUrlTemplate": provider.voice_page_url_template or None,
             "voices": [{"id": voice.id, "displayName": voice.display_name, "description": voice.description or None}
                        for voice in _list_voices(provider_name, language_code)],
             "hasAutomaticVoice": provider_name == "macos-say"}
            for provider_name, provider in PROVIDER_BY_NAME_MAP.items()
            if provider.check_does_support_language(language_code)]
