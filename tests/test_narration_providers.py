"""Narration providers against recorded HTTP responses: requests, audio handling, retries and refusals.

ElevenLabs has no live test key yet, so these responses follow its API reference (text-to-speech/convert).
"""

from __future__ import annotations

import io
import json
import wave

import httpx
import pytest

from explainer_studio.errors import StudioError
from explainer_studio.narration_providers import base, elevenlabs, macos_say, openai, voai
from explainer_studio.narration_providers.base import SynthesisError


class RequestRecorder:
    """Stands in for httpx.request: answers with the queued responses and keeps the requests."""

    def __init__(self, *responses: httpx.Response) -> None:
        self.responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, method: str, url: str, **kwargs) -> httpx.Response:
        self.requests.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)


@pytest.fixture
def recorded(monkeypatch: pytest.MonkeyPatch):
    def install(*responses: httpx.Response) -> RequestRecorder:
        fake = RequestRecorder(*responses)
        monkeypatch.setattr(base.httpx, "request", fake)
        monkeypatch.setattr(base.time, "sleep", lambda seconds: None)
        return fake

    return install


def build_wav_bytes(duration_seconds: float = 0.5, sample_rate_hertz: int = 24000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate_hertz)
        audio.writeframes(b"\x01\x00" * int(sample_rate_hertz * duration_seconds))
    return buffer.getvalue()


ELEVENLABS_SETTINGS = elevenlabs.Settings(provider_name="elevenlabs", voice_id="JBFqnCBsd6RMkjVDRZzb",
                                          voice_settings={"stability": 0.5, "similarity_boost": 0.75})


def test_elevenlabs_requests_pcm_and_wraps_it_as_wav(recorded, tmp_path) -> None:
    recorder = recorded(httpx.Response(200, content=b"\x00\x01" * 24000, headers={"content-type": "audio/pcm"}))
    output_wav_file_path = tmp_path / "beat.wav"
    synthesis = elevenlabs.Provider().synthesize("Hello there.", ELEVENLABS_SETTINGS, output_wav_file_path, "key", "en",
                                                 "Before.", "After.")
    request = recorder.requests[0]
    assert request["url"].endswith("/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb")
    assert request["params"] == {"output_format": "pcm_24000"} and request["headers"]["xi-api-key"] == "key"
    assert request["json"] == {"text": "Hello there.", "model_id": "eleven_v4",
                               "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                               "previous_text": "Before.", "next_text": "After."}
    with wave.open(str(output_wav_file_path)) as audio:
        assert audio.getframerate() == 24000 and audio.getnframes() == 24000
    assert synthesis.is_estimated and synthesis.cost_usd == pytest.approx(12 / 1000 * 0.08)


def test_elevenlabs_leaves_out_the_neighbors_for_a_model_that_refuses_them(recorded, tmp_path) -> None:
    recorder = recorded(httpx.Response(200, content=b"\x00\x01" * 100))
    settings = elevenlabs.Settings(provider_name="elevenlabs", voice_id="JBFqnCBsd6RMkjVDRZzb", model_id="eleven_v3")
    elevenlabs.Provider().synthesize("Hi.", settings, tmp_path / "a.wav", "key", "en", "Before.", "After.")
    assert recorder.requests[0]["json"] == {"text": "Hi.", "model_id": "eleven_v3"}


def test_elevenlabs_retries_rate_limits_and_stops_on_a_refused_key(recorded, tmp_path) -> None:
    recorder = recorded(httpx.Response(429, json={"detail": {"status": "too_many_concurrent_requests"}}),
                        httpx.Response(200, content=b"\x00\x01" * 100))
    elevenlabs.Provider().synthesize("Hi.", ELEVENLABS_SETTINGS, tmp_path / "a.wav", "key", "en")
    assert len(recorder.requests) == 2
    recorded(httpx.Response(401, json={"detail": {"status": "quota_exceeded", "message": "You exceeded your quota"}}))
    with pytest.raises(StudioError, match="ElevenLabs refused") as error:
        elevenlabs.Provider().synthesize("Hi.", ELEVENLABS_SETTINGS, tmp_path / "b.wav", "key", "en")
    assert "You exceeded your quota" in error.value.format()


def test_elevenlabs_accepts_a_key_restricted_to_speech(recorded) -> None:
    restricted = {"detail": {"status": "missing_permissions", "message": "missing models_read"}}
    recorded(httpx.Response(401, json=restricted))
    elevenlabs.Provider().verify_api_key("key")
    recorded(httpx.Response(401, json={"detail": {"status": "invalid_api_key", "message": "Invalid API key"}}))
    with pytest.raises(StudioError):
        elevenlabs.Provider().verify_api_key("bad")


def test_openai_sends_default_teacher_instructions_and_does_not_retry_an_empty_quota(recorded, tmp_path) -> None:
    settings = openai.Settings(provider_name="openai")
    recorder = recorded(httpx.Response(200, content=build_wav_bytes()))
    openai.Provider().synthesize("Hello.", settings, tmp_path / "a.wav", "key", "en")
    body = recorder.requests[0]["json"]
    assert body["instructions"] == openai.DEFAULT_INSTRUCTIONS and body["response_format"] == "wav"
    quota = {"error": {"code": "insufficient_quota", "message": "You exceeded your current quota"}}
    recorder = recorded(httpx.Response(429, json=quota))
    with pytest.raises(StudioError, match="OpenAI refused"):
        openai.Provider().synthesize("Hello.", settings, tmp_path / "b.wav", "key", "en")
    assert len(recorder.requests) == 1


def test_voai_tells_settings_errors_from_server_errors(recorded, tmp_path) -> None:
    settings = voai.Settings(provider_name="voai", speaker="不存在")
    recorded(httpx.Response(500, json={"msg": "speaker 錯誤"}))
    with pytest.raises(StudioError, match="VoAI refused"):
        voai.Provider().synthesize("你好", settings, tmp_path / "a.wav", "key", "zh-TW")
    recorder = recorded(*[httpx.Response(500, text="<html>upstream error</html>")] * base.ATTEMPT_COUNT)
    with pytest.raises(SynthesisError):
        voai.Provider().synthesize("你好", voai.Settings(provider_name="voai"), tmp_path / "b.wav", "key", "zh-TW")
    assert len(recorder.requests) == base.ATTEMPT_COUNT
    recorder = recorded(httpx.Response(200, content=build_wav_bytes()))
    voai.Provider().synthesize("你好", voai.Settings(provider_name="voai"), tmp_path / "c.wav", "key", "zh-TW")
    assert recorder.requests[0]["headers"]["x-output-format"] == "wav"
    assert json.loads(json.dumps(recorder.requests[0]["json"]))["speaker"] == "子墨"


def test_cost_estimates_follow_each_price_table() -> None:
    openai_settings = openai.Settings(provider_name="openai", speed=1.0)  # a minute of speech at this speed
    assert openai.Provider().estimate_cost_usd("word " * 170, openai_settings) == pytest.approx(0.015)
    assert openai.Provider().estimate_cost_usd("你" * 300, openai_settings) == pytest.approx(0.015)
    assert voai.Provider().estimate_cost_usd("你好" * 50, voai.Settings(provider_name="voai")) == pytest.approx(1 / 31)
    flash = elevenlabs.Settings(provider_name="elevenlabs", voice_id="v", model_id="eleven_flash_v2_5")
    assert elevenlabs.Provider().estimate_cost_usd("x" * 1000, flash) == pytest.approx(0.04)


def test_macos_voices_are_parsed_and_chosen_by_language(monkeypatch) -> None:
    listing = ("Eddy (Chinese (Taiwan)) zh_TW    # 你好，我叫Eddy。\n"
               "Meijia              zh_TW    # 你好，我叫美佳。\n"
               "Samantha            en_US    # Hello! My name is Samantha.\n"
               "Kyoko               ja_JP    # こんにちは、私の名前はKyokoです。\n")
    locale_by_voice_name_map = macos_say.parse_voices(listing)
    assert locale_by_voice_name_map["Eddy (Chinese (Taiwan))"] == "zh_TW" and len(locale_by_voice_name_map) == 4
    monkeypatch.setattr(macos_say, "list_installed_voices", lambda: locale_by_voice_name_map)
    assert macos_say.find_default_voice("zh-TW") == "Meijia"
    assert macos_say.find_default_voice("en-GB") == "Samantha"
    assert macos_say.find_default_voice("ja") == "Kyoko"
    assert macos_say.find_default_voice("fr") is None
