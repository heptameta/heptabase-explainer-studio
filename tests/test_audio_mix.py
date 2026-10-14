"""Narration lines are cleaned at their edges before they are mixed."""

from __future__ import annotations

import numpy as np

from explainer_studio.rendering.audio_mix import SAMPLE_RATE_HERTZ, clean_narration_line_edges


def _tone(seconds: float, amplitude: float) -> np.ndarray:
    index = np.arange(int(seconds * SAMPLE_RATE_HERTZ))
    return (amplitude * np.sin(2 * np.pi * 220 * index / SAMPLE_RATE_HERTZ)).astype(np.float32)


def test_a_burst_after_the_lines_closing_silence_is_silenced_and_speech_to_the_end_is_kept():
    speech, silence, burst = _tone(0.5, 0.3), np.zeros(int(0.3 * SAMPLE_RATE_HERTZ), np.float32), _tone(0.04, 0.2)
    cleaned = clean_narration_line_edges(np.concatenate([speech, silence, burst]))
    assert len(cleaned) == len(speech) + len(silence) + len(burst)  # the timeline keeps the line's length
    assert not np.any(cleaned[len(speech) + len(silence):])
    assert np.allclose(cleaned[1000:len(speech) - 1000], speech[1000:-1000])

    # a line that speaks up to its last sample loses nothing but its 15 ms fade-out
    cleaned = clean_narration_line_edges(np.concatenate([silence, speech]))
    assert np.allclose(cleaned[len(silence):-SAMPLE_RATE_HERTZ * 15 // 1000], speech[:-SAMPLE_RATE_HERTZ * 15 // 1000])
    assert cleaned[0] == 0 and cleaned[-1] == 0


def test_a_longer_burst_still_rising_at_the_end_is_silenced_but_a_last_word_that_fades_out_is_kept():
    speech, silence = _tone(0.5, 0.3), np.zeros(int(0.3 * SAMPLE_RATE_HERTZ), np.float32)
    rising_burst = _tone(0.13, 0.2) * np.linspace(0.1, 1, int(0.13 * SAMPLE_RATE_HERTZ), dtype=np.float32)
    cleaned = clean_narration_line_edges(np.concatenate([speech, silence, rising_burst]))
    assert not np.any(cleaned[len(speech) + len(silence):])  # a clipped "sh" of 130 ms

    fading_word = _tone(0.2, 0.3) * np.linspace(1, 0.05, int(0.2 * SAMPLE_RATE_HERTZ), dtype=np.float32)
    cleaned = clean_narration_line_edges(np.concatenate([speech, silence, fading_word]))
    word_start = len(speech) + len(silence)
    assert np.allclose(cleaned[word_start + 1000:-SAMPLE_RATE_HERTZ * 15 // 1000],
                       fading_word[1000:-SAMPLE_RATE_HERTZ * 15 // 1000])
