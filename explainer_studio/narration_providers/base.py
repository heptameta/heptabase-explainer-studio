"""The interface every narration provider implements, and the HTTP and pricing helpers they share.

A provider turns one beat's spoken text into a mono WAV at its native sample rate; `narrate` converts that to the
48 kHz files scenes use. Two kinds of failure are distinguished: `SynthesisError` means this beat failed and the next
one may work (a timeout, a server error after retries), while `StudioError` means no beat can work until the user
fixes something (a refused key, an exhausted quota, an unknown voice), so `narrate` stops.
"""

from __future__ import annotations

import re
import time
import wave
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import httpx
from pydantic import BaseModel

from .. import languages

if TYPE_CHECKING:
    from . import NarrationProviderName

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
# A POST makes audio the service bills for. It is sent again only when the service cannot have made that audio: the
# connection never opened, or the service itself answered that it did not. After a gateway's 502 or 504, or an answer
# lost on the way, it may have, and a second request could be charged again.
UNSENT_REQUEST_ERROR_CLASSES = (httpx.ConnectError, httpx.ConnectTimeout)
UNMADE_AUDIO_STATUS_CODES = {408, 429, 500, 503}
ATTEMPT_COUNT = 5
TIMEOUT_SECONDS = 120


class SynthesisError(Exception):
    """One beat could not be synthesized; other beats may still work. `was_possibly_charged`: the request may have
    reached the service and been billed although no audio came back."""

    def __init__(self, message: str, was_possibly_charged: bool = False):
        super().__init__(message)
        self.was_possibly_charged = was_possibly_charged


@dataclass(frozen=True)
class Synthesis:
    """What one synthesis call cost. `is_estimated` is true when the cost comes from a price table, not the service."""

    character_count: int
    cost_usd: float
    is_estimated: bool


@dataclass(frozen=True)
class SuggestedVoice:
    """A voice the plan page offers. `description` is written in the language of the list the voice is in."""

    id: str  # the value of the provider's voice field, such as an ElevenLabs voice_id
    display_name: str
    description: str = ""


class NarrationProvider(ABC):
    name: ClassVar[NarrationProviderName]  # the plan's `provider_name`
    is_paid: ClassVar[bool]
    # the environment variable that holds the API key; None for providers without a key
    api_key_env: ClassVar[str | None]
    display_name: ClassVar[str]  # the name people know the service by
    description: ClassVar[str]  # one line for the `setup narration` menu
    settings_model: ClassVar[type[BaseModel]]  # the plan's `narration` fields for this provider
    voice_field: ClassVar[str]  # the settings field that picks the voice
    # common voices to offer, the first being the default; any other value of the voice field still works
    suggested_voices: ClassVar[tuple[SuggestedVoice, ...]] = ()
    # where a user gets a key, for `setup narration`
    api_key_page_url: ClassVar[str] = ""
    # where a user can hear and browse the voices, for the plan page
    voices_page_url: ClassVar[str] = ""
    # the page of one voice, with `{voice_id}` for its id; empty when the provider has no such page
    voice_page_url_template: ClassVar[str] = ""

    @classmethod
    def check_does_support_language(cls, language_code: str) -> bool:
        """Whether the plan page offers this provider for a series in `language_code`."""
        return True

    @classmethod
    def list_suggested_voices(cls, language_code: str) -> tuple[SuggestedVoice, ...]:
        """The voices to offer for a series in `language_code`, the first being the default."""
        return cls.suggested_voices

    def require_available(self) -> None:
        """Raise StudioError when the provider cannot run on this computer."""

    @abstractmethod
    def estimate_cost_usd(self, text: str, settings: BaseModel) -> float:
        """The cost of synthesizing `text`, from the provider's price table."""

    @abstractmethod
    def synthesize(self, text: str, settings: BaseModel, output_wav_file_path: Path, api_key: str | None,
                   language_code: str, previous_spoken_text: str | None = None,
                   next_spoken_text: str | None = None) -> Synthesis:
        """Write `text` as speech to `output_wav_file_path` (mono WAV). Raise StudioError on a refusal the user must
        fix and SynthesisError when only this beat failed.

        `previous_spoken_text` and `next_spoken_text` are the neighboring beats' spoken text; a provider that can
        condition on them uses them so the beat's intonation continues its neighbors', and the voice never reads
        them."""

    def verify_api_key(self, api_key: str) -> None:
        """Make the cheapest request that proves the key works; raise StudioError if it does not."""


# Pricing ------------------------------------------------------------------------------------------------------------
CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")


def estimate_speech_minutes(text: str, provider_name: NarrationProviderName, speed: float = 1.0) -> float:
    """How long the provider's voice takes to read `text`, for providers that bill by audio length. CJK characters
    are timed at the Chinese speaking rate in `languages`, other words at the English one."""
    cjk_character_count = len(CJK_PATTERN.findall(text))
    word_count = len(re.findall(r"[^\W_]+", CJK_PATTERN.sub(" ", text)))
    minutes = (cjk_character_count / languages.resolve_language("zh").resolve_units_per_minute(provider_name)
               + word_count / languages.resolve_language("en").resolve_units_per_minute(provider_name))
    return minutes / max(speed, 0.25)


# HTTP ---------------------------------------------------------------------------------------------------------------
def request(method: str, url: str, service_name: str,
            check_is_final_response: Callable[[httpx.Response], bool] | None = None, **kwargs) -> httpx.Response:
    """One HTTP request, retried with backoff on network errors and transient statuses (429, 5xx) unless
    `check_is_final_response` says the response will not change (an exhausted quota). A POST, which the service bills,
    is retried only when the service cannot have made the audio (UNMADE_AUDIO_STATUS_CODES); after any other failure
    SynthesisError says it may have been charged. Returns the last response, whatever its status, so the provider can
    explain it; raises SynthesisError when the service never answered."""
    is_billed = method == "POST"
    retry_status_codes = UNMADE_AUDIO_STATUS_CODES if is_billed else TRANSIENT_STATUS_CODES
    for attempt in range(ATTEMPT_COUNT):
        is_last_attempt = attempt == ATTEMPT_COUNT - 1
        try:
            response = httpx.request(method, url, timeout=TIMEOUT_SECONDS, **kwargs)
        except httpx.RequestError as error:
            if is_billed and not isinstance(error, UNSENT_REQUEST_ERROR_CLASSES):
                raise SynthesisError(f"no answer from {service_name} ({type(error).__name__}); not sent again, since "
                                     "it may have been charged", was_possibly_charged=True) from None
            if is_last_attempt:
                raise SynthesisError(f"could not reach {service_name}: {type(error).__name__}") from None
            wait_seconds = 2.0 * 2 ** attempt
        else:
            if is_billed and response.status_code in TRANSIENT_STATUS_CODES - UNMADE_AUDIO_STATUS_CODES:
                raise SynthesisError(f"{service_name} HTTP {response.status_code} from a gateway; not sent again, "
                                     "since it may have been charged", was_possibly_charged=True)
            if (response.status_code not in retry_status_codes or is_last_attempt
                    or (check_is_final_response and check_is_final_response(response))):
                return response
            wait_seconds = _parse_retry_after_seconds(response) or 2.0 * 2 ** attempt
        time.sleep(min(wait_seconds, 30.0))
    raise AssertionError("unreachable")


def _parse_retry_after_seconds(response: httpx.Response) -> float | None:
    try:
        return float(response.headers.get("retry-after", ""))
    except ValueError:
        return None


def parse_error_message(response: httpx.Response, max_characters: int = 300) -> str:
    """The service's own explanation of an error response, without echoing anything we sent."""
    try:
        body = response.json()
    except ValueError:
        return response.text.strip()[:max_characters] or f"HTTP {response.status_code}"
    for key_path in (("error", "message"), ("detail", "message"), ("detail",), ("message",), ("msg",), ("error",)):
        value = body
        for key in key_path:
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, str) and value:
            return value[:max_characters]
    return str(body)[:max_characters]


def write_pcm_wav(path: Path, pcm: bytes, sample_rate_hertz: int) -> None:
    """Raw 16-bit little-endian mono PCM as a WAV file."""
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate_hertz)
        handle.writeframes(pcm)
