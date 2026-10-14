"""VoAI text to speech, Taiwanese Mandarin voices (https://connect.voai.ai/doc-vocal/).

`GET /TTS/GetSpeaker` lists the speakers and styles of each version (model).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..errors import StudioError
from .base import NarrationProvider, SuggestedVoice, Synthesis, SynthesisError, parse_error_message, request

API_URL = "https://connect.voai.ai"

# Estimate: one point per character; the smallest plan sells 90,000 points for NT$900 (www.voai.ai/voai-api, checked
# 2026-10-06), converted at about 31 TWD per USD. Larger plans are cheaper per point.
USD_PER_CHARACTER = 0.01 / 31


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["voai"]
    version: str = "Classic"
    speaker: str = "子墨"
    style: str = "平靜"
    speed: float = Field(default=1.0, ge=0.5, le=1.5)


def _parse_service_message(response) -> str | None:
    """VoAI reports its own errors (a bad key, speaker or style) as HTTP 500 with {"msg": ...}; retrying them is
    pointless. A 500 without that body is a real server error and is retried."""
    if response.status_code != 500:
        return None
    try:
        message = response.json().get("msg")
    except (ValueError, AttributeError):
        return None
    return message if isinstance(message, str) else None


def _check_does_affect_every_beat(message: str) -> bool:
    return any(word in message.lower() for word in ("api-key", "speaker", "style", "version", "model", "點", "額度"))


def _build_refusal_error(response, refused_subject: str) -> StudioError:
    return StudioError(f"VoAI refused {refused_subject} (HTTP {response.status_code})", parse_error_message(response),
                       "check the key and its remaining points at app.voai.ai, and the speaker and style in plan.yaml "
                       "(GET /TTS/GetSpeaker lists them); to replace the key, ask the user to run "
                       "`explainer-studio setup narration voai` in their own terminal")


class Provider(NarrationProvider):
    name = "voai"
    is_paid = True
    api_key_env = "VOAI_API_KEY"
    display_name = "VoAI"
    description = "VoAI: Taiwanese Mandarin voices (paid)"
    settings_model = Settings
    voice_field = "speaker"
    suggested_voices = (SuggestedVoice("子墨", "子墨", "男聲，沉穩，建議 Classic 模型、平靜風格"),)
    api_key_page_url = "https://app.voai.ai (API Key 管理)"
    voices_page_url = "https://www.voai.ai"

    @classmethod
    def check_does_support_language(cls, language_code: str) -> bool:
        return language_code.lower() in ("zh-tw", "zh-hant")  # Taiwanese Mandarin voices only

    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        return len(text) * USD_PER_CHARACTER

    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        assert isinstance(settings, Settings) and api_key
        body = {"version": settings.version, "speaker": settings.speaker, "style": settings.style, "text": text,
                "speed": settings.speed, "pitch_shift": 0, "style_weight": 0, "breath_pause": 0}
        sample_rate_hertz = "24000" if settings.version == "Sota+" else "32000"  # the highest each model accepts
        response = request("POST", f"{API_URL}/TTS/Speech", "VoAI", check_is_final_response=_parse_service_message,
                           json=body, headers={"x-api-key": api_key, "x-output-format": "wav",
                                               "x-sample-rate": sample_rate_hertz})
        message = _parse_service_message(response)
        if response.status_code in (401, 402, 403) or (message and _check_does_affect_every_beat(message)):
            raise _build_refusal_error(response, f"the request (version {settings.version}, speaker "
                                                 f"{settings.speaker}, style {settings.style})")
        if response.status_code != 200 or not response.content.startswith(b"RIFF"):
            raise SynthesisError(f"VoAI HTTP {response.status_code}: {parse_error_message(response)}")
        output_wav_file_path.write_bytes(response.content)
        return Synthesis(len(text), self.estimate_cost_usd(text, settings), is_estimated=True)

    def verify_api_key(self, api_key: str) -> None:
        response = request("GET", f"{API_URL}/Key/Usage", "VoAI", check_is_final_response=_parse_service_message,
                           headers={"x-api-key": api_key})
        if response.status_code != 200:
            raise _build_refusal_error(response, "the API key")
