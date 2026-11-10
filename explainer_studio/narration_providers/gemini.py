"""Gemini text to speech through OpenRouter (https://openrouter.ai/docs/api/api-reference/tts/create-speech).

OpenRouter rather than Google AI Studio, whose paid Tier 1 allows about 100 requests a day per model, fewer than one
episode's beats. OpenRouter's speech endpoint takes OpenAI's request shape; the delivery note goes in `instructions`,
and Gemini also performs vocal tags written in the text ("[laughs]"). It answers with raw 16-bit mono PCM at 24 kHz
(`audio/pcm;rate=24000;channels=1`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict

from ..errors import StudioError
from .base import (
    NarrationProvider,
    SuggestedVoice,
    Synthesis,
    SynthesisError,
    estimate_speech_minutes,
    parse_error_message,
    request,
    write_pcm_wav,
)

API_URL = "https://openrouter.ai/api/v1"
DEFAULT_SAMPLE_RATE_HERTZ = 24000

# Used when the plan gives no `instructions`. Gemini has no speed setting, so the pace is asked for here.
DEFAULT_INSTRUCTIONS = ("Speak like a friend explaining something they find fascinating, in a relaxed, conversational "
                        "tone: a brisk, natural pace, real emphasis on the key word of each sentence, and small pauses "
                        "where a person would think. Never sound like an announcer, a newsreader or an advert.")

# Estimates: USD per million audio tokens, from OpenRouter's model pages (2026-10-15), and Gemini's 32 audio tokens per
# second of speech. Unknown models use the Flash price, the higher one.
USD_PER_MILLION_AUDIO_TOKENS_BY_MODEL_NAME_MAP = {
    "google/gemini-3.8-flash-tts": 9.0,
    "google/gemini-3.8-flash-lite-tts": 6.0,
}
DEFAULT_USD_PER_MILLION_AUDIO_TOKENS = 9.0
AUDIO_TOKENS_PER_SECOND = 32


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["gemini"]
    model: str = "google/gemini-3.8-flash-tts"  # Flash-Lite (google/gemini-3.8-flash-lite-tts) is cheaper, flatter
    voice: str = "Achernar"
    instructions: str | None = None


def _build_refusal_error(response: httpx.Response, refused_subject: str) -> StudioError:
    return StudioError(f"OpenRouter refused {refused_subject} (HTTP {response.status_code})",
                       parse_error_message(response),
                       "check the key, its credit and the voice/model in plan.yaml; to replace the key, ask the user to "
                       "run `explainer-studio setup narration gemini` in their own terminal")


def _parse_sample_rate_hertz(content_type: str) -> int | None:
    """The rate of a `audio/pcm;rate=...;channels=1` content type, the default when it names none, None when the
    content type is not mono PCM."""
    media_type, *parameters = (piece.strip().lower() for piece in content_type.split(";"))
    if media_type != "audio/pcm":
        return None
    parameter_by_name_map = dict(parameter.split("=", 1) for parameter in parameters if "=" in parameter)
    if parameter_by_name_map.get("channels", "1") != "1":
        return None
    rate = parameter_by_name_map.get("rate", str(DEFAULT_SAMPLE_RATE_HERTZ))
    return int(rate) if rate.isdigit() and int(rate) > 0 else None


class Provider(NarrationProvider):
    name = "gemini"
    is_paid = True
    api_key_env = "OPENROUTER_API_KEY"
    display_name = "Gemini"
    description = "Gemini through OpenRouter: expressive, conversational voices in many languages (paid)"
    settings_model = Settings
    voice_field = "voice"
    suggested_voices = (
        SuggestedVoice("Achernar", "Achernar", "soft"),
        SuggestedVoice("Sulafat", "Sulafat", "warm"),
        SuggestedVoice("Gacrux", "Gacrux", "mature"),
        SuggestedVoice("Kore", "Kore", "firm"),
        SuggestedVoice("Leda", "Leda", "youthful"),
        SuggestedVoice("Aoede", "Aoede", "breezy"),
    )
    api_key_page_url = "https://openrouter.ai/settings/keys"
    voices_page_url = "https://aistudio.google.com/generate-speech"

    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        assert isinstance(settings, Settings)
        usd_per_million_audio_tokens = USD_PER_MILLION_AUDIO_TOKENS_BY_MODEL_NAME_MAP.get(
            settings.model, DEFAULT_USD_PER_MILLION_AUDIO_TOKENS)
        speech_seconds = estimate_speech_minutes(text, self.name) * 60
        return speech_seconds * AUDIO_TOKENS_PER_SECOND * usd_per_million_audio_tokens / 1_000_000

    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        assert isinstance(settings, Settings) and api_key
        body = {"model": settings.model, "voice": settings.voice, "input": text, "response_format": "pcm",
                "instructions": settings.instructions or DEFAULT_INSTRUCTIONS}
        response = request("POST", f"{API_URL}/audio/speech", "OpenRouter", json=body,
                           headers={"Authorization": f"Bearer {api_key}"},
                           check_is_final_response=lambda response: response.status_code == 402)
        if response.status_code in (401, 402, 403, 404):  # 402: the key's credit is used up
            raise _build_refusal_error(response, "the request")
        if response.status_code == 400:  # an unknown model or voice: every beat would fail the same way
            raise _build_refusal_error(response, f"model {settings.model} with voice {settings.voice}")
        if response.status_code != 200:
            raise SynthesisError(f"OpenRouter HTTP {response.status_code}: {parse_error_message(response)}")
        sample_rate_hertz = _parse_sample_rate_hertz(response.headers.get("content-type", ""))
        if sample_rate_hertz is None or not response.content:
            raise SynthesisError(f"OpenRouter returned no mono PCM audio ({response.headers.get('content-type')})")
        pcm = response.content[:len(response.content) // 2 * 2]  # whole 16-bit samples
        write_pcm_wav(output_wav_file_path, pcm, sample_rate_hertz)
        return Synthesis(len(text), self.estimate_cost_usd(text, settings), is_estimated=True)

    def verify_api_key(self, api_key: str) -> None:
        response = request("GET", f"{API_URL}/key", "OpenRouter", headers={"Authorization": f"Bearer {api_key}"})
        if response.status_code != 200:
            raise _build_refusal_error(response, "the API key")
