"""`narrate`: what it reuses, remakes and deletes, how it keeps progress, and the gates in front of paid calls.

A fake provider stands in for the service; the conversion to 48 kHz WAV runs the real ffmpeg.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest

from explainer_studio import narration_providers
from explainer_studio.errors import StudioError
from explainer_studio.file_io import read_jsonl, read_yaml_document
from explainer_studio.narrate import (
    find_beat_ids_needing_narration,
    find_speech_rate_warnings,
    load_narration_record,
    narrate,
)
from explainer_studio.narration_providers.base import NarrationProvider, Synthesis, SynthesisError, write_pcm_wav
from explainer_studio.paths import Series
from explainer_studio.plan import load_plan
from explainer_studio.schemas.narration import NarratedBeat
from explainer_studio.script import load_script

PLAN = """\
title: Dams
sources: [sources/notes.md]
language_code: en
narration_budget_usd: {budget}
narration:
  provider_name: openai
  voice: {voice}
audience:
  description: Curious adults.
goal: Understand where a dam's energy is.
episodes:
  - id: ep01
    title: Dams
    question: Where is the energy?
    question_type: mechanism
    presenter_name: theo
    outline: [a dam]
    estimated_duration_seconds: 30
    taught_terms: [head]
    takeaway: In the height difference.
"""

SCRIPT = """\
scenes:
  - id: dam
    purpose: Build the dam.
    beats:
      - id: high
        narration_text: The water on the left stands high.
        visual: A dam.
      - id: low
        narration_text: On the right it is low.
        visual: Low water.
  - id: wheel
    purpose: Take the energy out.
    beats:
      - id: turn
        narration_text: Let it run through a wheel and the height becomes motion.
        visual: A wheel turns.
"""

REVIEWS = """\
rounds:
  - scene_ids: [dam, wheel]
    findings: []
"""


class FakeVoice(NarrationProvider):
    name = "openai"
    is_paid = True
    api_key_env = "OPENAI_API_KEY"

    def __init__(self) -> None:
        self.spoken_texts: list[str] = []
        self.neighbor_spoken_texts: list[tuple[str | None, str | None]] = []
        self.failing_text: str | None = None
        self.refuse_after_count: int | None = None

    def estimate_cost_usd(self, text, settings) -> float:
        return 0.01

    def synthesize(self, text, settings, output_wav_file_path, api_key, language_code, previous_spoken_text=None,
                   next_spoken_text=None) -> Synthesis:
        if self.refuse_after_count is not None and len(self.spoken_texts) >= self.refuse_after_count:
            raise StudioError("the service refused the key")
        self.spoken_texts.append(text)
        self.neighbor_spoken_texts.append((previous_spoken_text, next_spoken_text))
        if self.failing_text and self.failing_text in text:
            raise SynthesisError("timed out")
        seconds = len(text.split()) / 2.7
        samples = b"".join(struct.pack("<h", int(8000 * math.sin(i / 10))) for i in range(int(24000 * seconds)))
        write_pcm_wav(output_wav_file_path, samples, 24000)
        return Synthesis(len(text), 0.01, is_estimated=True)


@pytest.fixture
def series(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Series:
    production_dir_path = tmp_path / "production"
    episode_dir_path = production_dir_path / "episodes" / "ep01"
    (episode_dir_path / "audience-reviews").mkdir(parents=True)
    (production_dir_path / "plan.yaml").write_text(PLAN.format(budget="null", voice="ash"), encoding="utf-8")
    (episode_dir_path / "script.yaml").write_text(SCRIPT, encoding="utf-8")
    (episode_dir_path / "audience-reviews" / "script.yaml").write_text(REVIEWS, encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return Series(tmp_path)


@pytest.fixture
def voice(monkeypatch: pytest.MonkeyPatch) -> FakeVoice:
    fake = FakeVoice()
    monkeypatch.setattr(narration_providers, "get_provider", lambda provider_name: fake)
    return fake


def edit(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def find_ep01_beat_ids_needing_narration(series: Series) -> list[str]:
    return find_beat_ids_needing_narration(series, load_plan(series), "ep01", load_script(series, "ep01"))


@pytest.mark.render
def test_narrate_makes_48k_mono_files_then_reuses_and_redoes_only_what_changed(series, voice) -> None:
    run = narrate(series, "ep01")
    assert run.made_beat_ids == ["high", "low", "turn"] and run.reused_beat_ids == []
    with wave.open(str(series.get_episode_paths("ep01").get_narration_audio_file_path("high"))) as audio:
        assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (48000, 1, 2)
    record_file_path = series.get_episode_paths("ep01").narration_record_file_path
    # as the plan writes them, without defaults
    assert dict(read_yaml_document(record_file_path)["settings"]) == {"provider_name": "openai", "voice": "ash"}
    assert [beat.beat_id for beat in load_narration_record(series, "ep01").beats] == ["high", "low", "turn"]
    assert len(read_jsonl(series.spending_file_path)) == 3

    assert narrate(series, "ep01").made_beat_ids == []
    script_file_path = series.get_episode_paths("ep01").script_file_path
    edit(script_file_path, "it is low.", "it is much lower.")
    run = narrate(series, "ep01", forced_beat_ids=["turn"])
    assert run.made_beat_ids == ["low", "turn"] and run.reused_beat_ids == ["high"]
    # a redone beat hears its neighbors in the script, including a reused one
    assert voice.neighbor_spoken_texts[-2:] == [
        ("The water on the left stands high.", "Let it run through a wheel and the height becomes motion."),
        ("On the right it is much lower.", None)]
    assert find_ep01_beat_ids_needing_narration(series) == []
    # new narration text that the voice would say the same way keeps the audio
    edit(script_file_path, "narration_text: The water on the left stands high.",
         "narration_text: The water on the left stands HIGH.\n"
         "        spoken_text_override: The water on the left stands high.")
    assert find_ep01_beat_ids_needing_narration(series) == []


@pytest.mark.render
def test_a_failed_beat_keeps_its_old_audio_and_is_retried_next_time(series, voice) -> None:
    narrate(series, "ep01")
    before = series.get_episode_paths("ep01").get_narration_audio_file_path("low").read_bytes()
    edit(series.get_episode_paths("ep01").script_file_path, "it is low.", "it is lower.")
    voice.failing_text = "lower"
    run = narrate(series, "ep01")
    assert run.failure_by_beat_id_map == {"low": "timed out"}
    assert series.get_episode_paths("ep01").get_narration_audio_file_path("low").read_bytes() == before
    assert find_ep01_beat_ids_needing_narration(series) == ["low"]


@pytest.mark.render
def test_beats_removed_from_the_script_lose_their_audio(series, voice) -> None:
    narrate(series, "ep01")
    script_file_path = series.get_episode_paths("ep01").script_file_path
    script_file_path.write_text(script_file_path.read_text(encoding="utf-8").split("  - id: wheel")[0],
                                encoding="utf-8")
    edit(series.get_episode_paths("ep01").audience_reviews_dir_path / "script.yaml", "[dam, wheel]", "[dam]")
    run = narrate(series, "ep01")
    assert run.removed_beat_ids == ["turn"]
    assert not series.get_episode_paths("ep01").get_narration_audio_file_path("turn").exists()
    assert [beat.beat_id for beat in load_narration_record(series, "ep01").beats] == ["high", "low"]


@pytest.mark.render
def test_a_run_stopped_by_a_refusal_keeps_what_it_made_under_the_new_voice_only(series, voice) -> None:
    narrate(series, "ep01")
    edit(series.plan_file_path, "voice: ash", "voice: coral")
    voice.refuse_after_count = len(voice.spoken_texts) + 1
    with pytest.raises(StudioError) as error:
        narrate(series, "ep01")
    assert "made 1 beat(s) before stopping" in error.value.format()
    record = load_narration_record(series, "ep01")
    assert record.settings.voice == "coral" and [beat.beat_id for beat in record.beats] == ["high"]
    assert find_ep01_beat_ids_needing_narration(series) == ["low", "turn"]


@pytest.mark.render
def test_a_voice_switch_that_makes_nothing_leaves_the_old_narration_current(series, voice) -> None:
    narrate(series, "ep01")
    edit(series.plan_file_path, "voice: ash", "voice: coral")
    voice.refuse_after_count = len(voice.spoken_texts)
    with pytest.raises(StudioError):
        narrate(series, "ep01")
    edit(series.plan_file_path, "voice: coral", "voice: ash")
    assert find_ep01_beat_ids_needing_narration(series) == []


def test_the_budget_refuses_a_run_before_any_paid_call(series, voice) -> None:
    edit(series.plan_file_path, "narration_budget_usd: null", "narration_budget_usd: 0.025")
    with pytest.raises(StudioError, match="budget"):
        narrate(series, "ep01")
    assert voice.spoken_texts == []


def test_narrate_needs_a_key_and_a_finished_script_review(series, voice, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setattr("explainer_studio.user_dirs.get_config_dir_path", lambda: series.root_dir_path / "config")
    with pytest.raises(StudioError, match="no openai API key"):
        narrate(series, "ep01")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    (series.get_episode_paths("ep01").audience_reviews_dir_path / "script.yaml").unlink()
    with pytest.raises(StudioError, match="not ready for narration"):
        narrate(series, "ep01")
    assert voice.spoken_texts == []


def test_speech_rate_warnings_flag_clips_far_from_the_episodes_typical_rate() -> None:
    def build_narrated_beat(beat_id: str, word_count: int, duration_seconds: float) -> NarratedBeat:
        return NarratedBeat(beat_id=beat_id, spoken_text=" ".join(["word"] * word_count),
                            duration_seconds=duration_seconds)

    narrated_beats = [build_narrated_beat("a", 10, 4.0), build_narrated_beat("b", 12, 5.0),
                      build_narrated_beat("c", 11, 4.4), build_narrated_beat("skipped", 12, 1.0)]
    warnings = find_speech_rate_warnings(narrated_beats, "en", "openai")
    assert len(warnings) == 1 and warnings[0].startswith("beat skipped:")
