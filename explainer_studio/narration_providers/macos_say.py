"""The free macOS `say` voice, for trying the workflow without a paid key. It sounds mechanical."""

from __future__ import annotations

import functools
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..errors import StudioError
from .base import NarrationProvider, Synthesis, SynthesisError

# The voice used when the plan names none, by language code and then by its first part.
DEFAULT_VOICE_BY_LANGUAGE_CODE_MAP = {"zh-tw": "Meijia", "zh-hant": "Meijia", "zh-hk": "Sinji", "zh-cn": "Tingting",
                                      "zh-hans": "Tingting", "zh": "Meijia", "en": "Samantha"}
ADD_VOICE_INSTRUCTION = "add it in System Settings > Accessibility > Spoken Content > System voice > Manage Voices"


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["macos-say"]
    voice: str | None = None  # `say -v ?` lists the installed voices; None picks one for the series language
    words_per_minute: int | None = None


def parse_voices(listing: str) -> dict[str, str]:
    """Voice name -> locale from `say -v ?` lines like `Eddy (Chinese (Taiwan)) zh_TW    # 你好，我叫Eddy。`."""
    locale_by_voice_name_map = {}
    for line in listing.splitlines():
        match = re.match(r"^(.+?)\s+([a-z]{2,3}_[A-Za-z0-9]+)\s+#", line)
        if match:
            locale_by_voice_name_map[match.group(1).strip()] = match.group(2)
    return locale_by_voice_name_map


@functools.cache
def list_installed_voices() -> dict[str, str]:
    if shutil.which("say") is None:
        return {}
    listing = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=30, check=False)
    return parse_voices(listing.stdout)


def find_default_voice(language_code: str) -> str | None:
    locale_by_voice_name_map = list_installed_voices()
    normalized_code = language_code.lower()
    base_code = normalized_code.split("-")[0]
    for code in (normalized_code, base_code):
        if DEFAULT_VOICE_BY_LANGUAGE_CODE_MAP.get(code) in locale_by_voice_name_map:
            return DEFAULT_VOICE_BY_LANGUAGE_CODE_MAP[code]
    locale = normalized_code.replace("-", "_")
    return (next((voice_name for voice_name, voice_locale in locale_by_voice_name_map.items()
                  if voice_locale.lower() == locale), None)
            or next((voice_name for voice_name, voice_locale in locale_by_voice_name_map.items()
                     if voice_locale.split("_")[0].lower() == base_code), None))


class Provider(NarrationProvider):
    name = "macos-say"
    is_paid = False
    api_key_env = None
    display_name = "macOS"
    description = "macOS built-in voice: free, mechanical, macOS only (no key)"
    settings_model = Settings
    voice_field = "voice"

    def require_available(self) -> None:
        if sys.platform != "darwin" or shutil.which("say") is None:
            raise StudioError("the macos-say voice works only on macOS",
                              "it uses the `say` command that comes with macOS",
                              "set plan.yaml narration to elevenlabs, openai or voai, and ask the user to run "
                              "`explainer-studio setup narration` in their own terminal")

    def choose_voice(self, settings: Settings, language_code: str) -> str:
        if settings.voice:
            if settings.voice not in list_installed_voices():
                raise StudioError(f"the macOS voice {settings.voice!r} is not installed", "`say -v ?` does not list it",
                                  f"pick an installed voice in plan.yaml narration.voice, or {ADD_VOICE_INSTRUCTION}")
            return settings.voice
        chosen = find_default_voice(language_code)
        if chosen is None:
            raise StudioError(f"no macOS voice for {language_code}", "`say -v ?` lists no voice for this language",
                              f"{ADD_VOICE_INSTRUCTION}, or set narration.voice in plan.yaml")
        return chosen

    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        return 0.0

    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        assert isinstance(settings, Settings)
        voice = self.choose_voice(settings, language_code)
        with tempfile.TemporaryDirectory() as temporary_dir_path:
            text_file_path = Path(temporary_dir_path) / "text.txt"
            text_file_path.write_text(text, encoding="utf-8")
            command = ["say", "-v", voice, "-o", str(output_wav_file_path), "--file-format=WAVE",
                       "--data-format=LEI16@22050", "-f", str(text_file_path)]
            if settings.words_per_minute:
                command[3:3] = ["-r", str(settings.words_per_minute)]
            say_result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                        timeout=300, check=False)
        if say_result.returncode != 0 or not output_wav_file_path.exists() or output_wav_file_path.stat().st_size <= 44:
            raise SynthesisError(f"say failed: {say_result.stderr.strip()[:300] or 'no audio written'}")
        return Synthesis(len(text), 0.0, is_estimated=False)
