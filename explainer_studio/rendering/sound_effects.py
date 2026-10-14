"""The built-in sound effects, synthesized from scratch (original, no licence to track).

A scene plays one with `self.play_sound("<effect name>")`; the mix synthesizes it. Built-in effects do not duck the
background music by default: they are short and meant to sit on top of it.
"""

from __future__ import annotations

from typing import TypeGuard

import numpy as np
from scipy.signal import butter, sosfilt

from ..schemas.timeline import SoundEffectName

# the durations are fixed so a scene can record a sound without synthesizing it
DURATION_SECONDS_BY_EFFECT_NAME_MAP: dict[SoundEffectName, float] = {
    "whoosh_in": 0.75, "whoosh_out": 0.75, "ghost": 1.9, "questioner": 1.9, "bubble": 0.09, "title": 3.0}
# peak level of each effect, relative to the other effects (the mix sets the overall level against the speech)
_PEAK_LEVEL_BY_EFFECT_NAME_MAP: dict[SoundEffectName, float] = {
    "whoosh_out": 0.55, "whoosh_in": 0.55, "ghost": 0.8, "questioner": 0.8, "bubble": 0.35, "title": 0.9}


def check_is_effect(name: str) -> TypeGuard[SoundEffectName]:
    return name in DURATION_SECONDS_BY_EFFECT_NAME_MAP


def _synthesize_whoosh(sample_rate_hertz: int, is_reversed: bool) -> np.ndarray:
    sample_count = int(DURATION_SECONDS_BY_EFFECT_NAME_MAP["whoosh_in"] * sample_rate_hertz)
    t = np.linspace(0, 1, sample_count)
    noise = np.random.default_rng(1).normal(0, 1, sample_count)
    samples = np.zeros(sample_count)
    for low, high, center in ((300, 900, 0.35), (900, 2500, 0.5), (2500, 6000, 0.65)):
        band = sosfilt(butter(2, [low, high], "band", fs=sample_rate_hertz, output="sos"), noise)
        samples += band * np.exp(-((t - center) / 0.22) ** 2)
    samples *= np.sin(np.pi * t) ** 2
    if is_reversed:
        samples = samples[::-1]
    pan = 1 - t if is_reversed else t
    return np.stack([samples * (1 - 0.4 * pan), samples * (0.6 + 0.4 * pan)], axis=1)


def _synthesize_bell(sample_rate_hertz: int, frequency_hertz: float, duration_seconds: float) -> np.ndarray:
    t = np.arange(int(duration_seconds * sample_rate_hertz)) / sample_rate_hertz
    samples = sum(amplitude * np.sin(2 * np.pi * frequency_hertz * ratio * t) * np.exp(-t * (2.2 + 1.5 * ratio))
                  for ratio, amplitude in ((1, 1.0), (2.01, 0.35), (3.02, 0.18), (4.1, 0.08)))
    samples *= np.minimum(1, t / 0.004)
    return np.stack([samples, samples], axis=1)


def _synthesize_ghost(sample_rate_hertz: int) -> np.ndarray:
    first, second = _synthesize_bell(sample_rate_hertz, 1318.5, 1.6), _synthesize_bell(sample_rate_hertz, 1760.0, 1.6)
    samples = np.zeros((int(DURATION_SECONDS_BY_EFFECT_NAME_MAP["ghost"] * sample_rate_hertz), 2))
    samples[:len(first)] += first
    delay_sample_count = int(0.14 * sample_rate_hertz)
    samples[delay_sample_count:delay_sample_count + len(second)] += 0.7 * second[:len(samples) - delay_sample_count]
    return samples


def _synthesize_bubble(sample_rate_hertz: int) -> np.ndarray:
    t = np.arange(int(DURATION_SECONDS_BY_EFFECT_NAME_MAP["bubble"] * sample_rate_hertz)) / sample_rate_hertz
    frequency = 620 + 380 * (t / t[-1])
    samples = np.sin(2 * np.pi * np.cumsum(frequency) / sample_rate_hertz) * np.exp(-t * 45)
    return np.stack([samples, samples], axis=1)


def _synthesize_title(sample_rate_hertz: int, root_midi_note: int = 62) -> np.ndarray:
    samples = np.zeros((int(DURATION_SECONDS_BY_EFFECT_NAME_MAP["title"] * sample_rate_hertz), 2))
    for i, midi_note in enumerate([root_midi_note + 12, root_midi_note + 19, root_midi_note + 24]):
        bell = _synthesize_bell(sample_rate_hertz, 440.0 * 2 ** ((midi_note - 69) / 12), 2.6)
        delay_sample_count = int(i * 0.18 * sample_rate_hertz)
        samples[delay_sample_count:delay_sample_count + len(bell)] += 0.6 * bell[:len(samples) - delay_sample_count]
    return samples


def synthesize(effect_name: str, sample_rate_hertz: int) -> np.ndarray:
    """The effect as a stereo float array (n, 2), peak-normalized to its level."""
    maker_by_effect_name_map = {"whoosh_out": lambda: _synthesize_whoosh(sample_rate_hertz, False),
                                "whoosh_in": lambda: _synthesize_whoosh(sample_rate_hertz, True),
                                "ghost": lambda: _synthesize_ghost(sample_rate_hertz),
                                "questioner": lambda: _synthesize_ghost(sample_rate_hertz),
                                "bubble": lambda: _synthesize_bubble(sample_rate_hertz),
                                "title": lambda: _synthesize_title(sample_rate_hertz)}
    if effect_name not in maker_by_effect_name_map:
        raise KeyError(f"unknown sound effect {effect_name!r}; built-in effects: "
                       f"{', '.join(DURATION_SECONDS_BY_EFFECT_NAME_MAP)}")
    sound = maker_by_effect_name_map[effect_name]()
    return (sound / (np.max(np.abs(sound)) + 1e-9) * _PEAK_LEVEL_BY_EFFECT_NAME_MAP[effect_name]).astype(np.float32)
