"""ElevenLabs text to speech (https://elevenlabs.io/docs/api-reference/text-to-speech/convert).

Audio is requested as raw 24 kHz PCM, which every plan may use (44.1 kHz PCM and WAV need the Pro plan). Each beat is
sent with its neighbors' spoken text as `previous_text` and `next_text`, so beats synthesized one at a time keep the
intonation of continuous speech; the service does not bill that text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..errors import StudioError
from .base import (
    NarrationProvider,
    SuggestedVoice,
    Synthesis,
    SynthesisError,
    parse_error_message,
    request,
    write_pcm_wav,
)

API_URL = "https://api.elevenlabs.io/v1"
SAMPLE_RATE_HERTZ = 24000

# Estimates: USD per 1,000 characters, from elevenlabs.io/pricing/api (checked 2026-10-06). Unknown models use the
# multilingual price, the higher of the two.
USD_PER_1000_CHARACTERS_BY_MODEL_ID_MAP = {
    "eleven_v4": 0.08,
    "eleven_v4_turbo": 0.04,
    "eleven_multilingual_v2": 0.08,
    "eleven_v3": 0.08,
    "eleven_flash_v2_5": 0.04,
    "eleven_turbo_v2_5": 0.04,
    "eleven_flash_v2": 0.04,
    "eleven_turbo_v2": 0.04,
}
DEFAULT_USD_PER_1000_CHARACTERS = 0.08
# models that refuse `previous_text` and `next_text` (HTTP 400 unsupported_model, checked 2026-10-11)
MODEL_ID_PREFIXES_WITHOUT_CONTEXT = ("eleven_v3",)

# Voice Library voices chosen by listening to Chinese narration with eleven_v4
CHINESE_VOICES = (
    SuggestedVoice("FS8UtxyDrvYcNCxVaziq", "Hardy", "台灣大叔，溫暖親切、帶點幽默"),
    SuggestedVoice("Z9RJEkFYQw307BCQULDR", "Kuo Yu", "男聲，沉穩內斂"),
    SuggestedVoice("fQj4gJSexpu8RDE2Ii5m", "Yu", "年輕有活力，適合教學"),
    SuggestedVoice("tSv4yoTPFFmCMaJpNf0A", "Ian", "清晰溫暖，節奏穩定"),
    SuggestedVoice("Z8Aisvg1z70p27kGvkZZ", "Ling", "女聲，平靜穩重，適合教學"),
    SuggestedVoice("r6qgCCGI7RWKXCagm158", "Anna Su", "清楚自然，適合紀錄片"),
)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["elevenlabs"]
    voice_id: str
    model_id: str = "eleven_v4"  # the most expressive model; eleven_multilingual_v2 is steadier but flatter
    voice_settings: dict[str, float | bool] | None = None


def _build_refusal_error(response, refused_subject: str) -> StudioError:
    detail = parse_error_message(response)
    return StudioError(f"ElevenLabs refused {refused_subject} (HTTP {response.status_code})", detail,
                       "check the key, plan and quota at elevenlabs.io; to replace the key, ask the user to run "
                       "`explainer-studio setup narration elevenlabs` in their own terminal")


class Provider(NarrationProvider):
    name = "elevenlabs"
    is_paid = True
    api_key_env = "ELEVENLABS_API_KEY"
    display_name = "ElevenLabs"
    description = "ElevenLabs: natural voices in many languages (paid)"
    settings_model = Settings
    voice_field = "voice_id"
    # ElevenLabs' default voices, for English and any language without its own list
    suggested_voices = (
        SuggestedVoice("JBFqnCBsd6RMkjVDRZzb", "George", "British man, warm storyteller"),
        SuggestedVoice("nPczCjzI2devNBz1zQrb", "Brian", "American man, deep, narration"),
        SuggestedVoice("pNInz6obpgDQGcFmaJgB", "Adam", "American man, deep, narration"),
        SuggestedVoice("onwK4e9ZLuTAKqWW03F9", "Daniel", "British man, authoritative, news"),
        SuggestedVoice("21m00Tcm4TlvDq8ikWAM", "Rachel", "American woman, calm, narration"),
        SuggestedVoice("pFZP5JQG7iQjIQuC4Bku", "Lily", "British woman, warm, narration"),
        SuggestedVoice("EXAVITQu4vr4xnSDxMaL", "Sarah", "American woman, soft, news"),
        SuggestedVoice("Xb7hH8MSUJpSbSDYk0k2", "Alice", "British woman, confident, news"),
        SuggestedVoice("XB0fDUnXU5powFXDhCwa", "Charlotte", "Swedish-accented woman, characters"),
    )
    api_key_page_url = "https://elevenlabs.io/app/settings/api-keys"
    voices_page_url = "https://elevenlabs.io/app/voice-library"
    voice_page_url_template = "https://elevenlabs.io/app/voice-library?voiceId={voice_id}"

    @classmethod
    def list_suggested_voices(cls, language_code: str) -> tuple[SuggestedVoice, ...]:
        return CHINESE_VOICES if language_code.lower().startswith("zh") else cls.suggested_voices

    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        assert isinstance(settings, Settings)
        return len(text) / 1000 * USD_PER_1000_CHARACTERS_BY_MODEL_ID_MAP.get(settings.model_id,
                                                                               DEFAULT_USD_PER_1000_CHARACTERS)

    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        assert isinstance(settings, Settings) and api_key
        body: dict = {"text": text, "model_id": settings.model_id}
        if not settings.model_id.startswith(MODEL_ID_PREFIXES_WITHOUT_CONTEXT):
            if previous_spoken_text:
                body["previous_text"] = previous_spoken_text
            if next_spoken_text:
                body["next_text"] = next_spoken_text
        if settings.voice_settings:
            body["voice_settings"] = settings.voice_settings
        response = request("POST", f"{API_URL}/text-to-speech/{settings.voice_id}", "ElevenLabs",
                           params={"output_format": f"pcm_{SAMPLE_RATE_HERTZ}"},
                           headers={"xi-api-key": api_key, "Accept": "audio/pcm"}, json=body)
        if response.status_code in (401, 402, 403, 404):
            refused_subject = f"voice {settings.voice_id}" if response.status_code == 404 else "the request"
            raise _build_refusal_error(response, refused_subject)
        if response.status_code != 200:
            raise SynthesisError(f"ElevenLabs HTTP {response.status_code}: {parse_error_message(response)}")
        if response.headers.get("content-type", "").startswith("application/json") or len(response.content) < 2:
            raise SynthesisError(f"ElevenLabs returned no audio: {parse_error_message(response)}")
        write_pcm_wav(output_wav_file_path, response.content[: len(response.content) // 2 * 2], SAMPLE_RATE_HERTZ)
        return Synthesis(len(text), self.estimate_cost_usd(text, settings), is_estimated=True)

    def verify_api_key(self, api_key: str) -> None:
        response = request("GET", f"{API_URL}/models", "ElevenLabs", headers={"xi-api-key": api_key})
        if response.status_code == 200:
            return
        # a key restricted to text to speech cannot list models, but it did authenticate
        if response.status_code == 401 and "missing_permissions" in response.text:
            return
        raise _build_refusal_error(response, "the API key")
