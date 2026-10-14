"""OpenAI text to speech (https://platform.openai.com/docs/api-reference/audio/createSpeech)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..errors import StudioError
from .base import (
    NarrationProvider,
    SuggestedVoice,
    Synthesis,
    SynthesisError,
    estimate_speech_minutes,
    parse_error_message,
    request,
)

API_URL = "https://api.openai.com/v1"

# Used when the plan gives no `instructions` (gpt-4o models only).
DEFAULT_INSTRUCTIONS = ("Speak like a warm, curious teacher explaining something to one person: unhurried, clear, "
                        "with natural emphasis on the key word of each sentence. Never sound like an announcer or an "
                        "advert.")

# Estimates from developers.openai.com/api/docs/pricing (checked 2026-10-06). gpt-4o-mini-tts bills audio tokens,
# about $0.015 per minute of speech; the older models bill characters.
USD_PER_MINUTE_BY_MODEL_ID_MAP = {"gpt-4o-mini-tts": 0.015}
USD_PER_CHARACTER_BY_MODEL_ID_MAP = {"tts-1": 15 / 1_000_000, "tts-1-hd": 30 / 1_000_000}


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["openai"]
    model: str = "gpt-4o-mini-tts"
    voice: str = "ash"
    instructions: str | None = None
    speed: float = Field(default=1.175, ge=0.25, le=4.0)  # 1.0 drags for explaining


def _build_refusal_error(response, refused_subject: str) -> StudioError:
    return StudioError(f"OpenAI refused {refused_subject} (HTTP {response.status_code})", parse_error_message(response),
                       "check the key, billing and the voice/model in plan.yaml; to replace the key, ask the user to "
                       "run `explainer-studio setup narration openai` in their own terminal")


class Provider(NarrationProvider):
    name = "openai"
    is_paid = True
    api_key_env = "OPENAI_API_KEY"
    display_name = "OpenAI"
    description = "OpenAI: good English and multilingual voices (paid)"
    settings_model = Settings
    voice_field = "voice"
    suggested_voices = (
        SuggestedVoice("ash", "Ash"),
        SuggestedVoice("marin", "Marin", "OpenAI's recommendation for the best quality"),
        SuggestedVoice("cedar", "Cedar", "OpenAI's recommendation for the best quality"),
        *(SuggestedVoice(name, name.capitalize()) for name in (
            "alloy", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse")),
    )
    api_key_page_url = "https://platform.openai.com/api-keys"
    voices_page_url = "https://www.openai.fm"

    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        assert isinstance(settings, Settings)
        if settings.model in USD_PER_CHARACTER_BY_MODEL_ID_MAP:
            return len(text) * USD_PER_CHARACTER_BY_MODEL_ID_MAP[settings.model]
        return (estimate_speech_minutes(text, self.name, settings.speed)
                * USD_PER_MINUTE_BY_MODEL_ID_MAP.get(settings.model, 0.015))

    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        assert isinstance(settings, Settings) and api_key
        body: dict = {"model": settings.model, "voice": settings.voice, "input": text, "response_format": "wav",
                      "speed": settings.speed}
        if settings.model.startswith("gpt-"):
            body["instructions"] = settings.instructions or DEFAULT_INSTRUCTIONS
        response = request("POST", f"{API_URL}/audio/speech", "OpenAI", json=body,
                           headers={"Authorization": f"Bearer {api_key}"},
                           check_is_final_response=lambda response: "insufficient_quota" in response.text)
        is_quota_exhausted = response.status_code == 429 and "insufficient_quota" in response.text
        if response.status_code in (401, 403, 404) or is_quota_exhausted:
            raise _build_refusal_error(response, "the request")
        if response.status_code != 200:
            raise SynthesisError(f"OpenAI HTTP {response.status_code}: {parse_error_message(response)}")
        if not response.content.startswith(b"RIFF"):
            raise SynthesisError(f"OpenAI returned no audio: {parse_error_message(response)}")
        output_wav_file_path.write_bytes(response.content)
        return Synthesis(len(text), self.estimate_cost_usd(text, settings), is_estimated=True)

    def verify_api_key(self, api_key: str) -> None:
        response = request("GET", f"{API_URL}/models", "OpenAI", headers={"Authorization": f"Bearer {api_key}"})
        if response.status_code != 200:
            raise _build_refusal_error(response, "the API key")
