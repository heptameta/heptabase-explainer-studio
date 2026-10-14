"""Original background music synthesized from scratch: a slow felt piano over a warm pad.

Each episode gets its own key and mode, and a new phrase starts at each scene. Everything is generated here, so the
music is original and has no licence to track. The track is written at a neutral level: `render` sets it under the
narration and ducks it.
"""

from __future__ import annotations

import zlib
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict
from scipy.io import wavfile
from scipy.signal import butter, oaconvolve, sosfilt

from ..schemas.timeline import Timeline
from .base import BackgroundMusicProvider

ROOT_MIDI_NOTES = [55, 57, 60, 62, 63, 65]  # MIDI roots: G, A, C, D, E-flat, F
MAJOR_PROGRESSIONS = [[(0, "maj7"), (9, "m7"), (5, "maj7"), (7, "sus4")],
                      [(0, "maj7"), (5, "maj9"), (9, "m7"), (7, "sus4")],
                      [(5, "maj7"), (0, "maj7"), (7, "sus4"), (9, "m7")]]
MINOR_PROGRESSIONS = [[(0, "m9"), (8, "maj7"), (3, "maj7"), (10, "sus4")],
                      [(0, "m7"), (5, "m9"), (8, "maj7"), (7, "sus4")],
                      [(8, "maj7"), (3, "maj7"), (10, "sus4"), (0, "m9")]]
INTERVALS_BY_CHORD_QUALITY_MAP = {"maj7": [0, 4, 7, 11], "maj9": [0, 4, 7, 14], "m7": [0, 3, 7, 10],
                                  "m9": [0, 3, 7, 14], "sus4": [0, 5, 7, 10]}


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: Literal["synthesized-piano"]


def resolve_episode_theme(episode_number: int) -> tuple[int, str, int]:
    """(root MIDI note, mode, seed) for an episode: deterministic, and different from one episode to the next."""
    digest = zlib.crc32(f"ep{episode_number:02d}".encode())
    return ROOT_MIDI_NOTES[digest % len(ROOT_MIDI_NOTES)], "minor" if (digest >> 8) % 3 == 0 else "major", digest % 1000


def _convert_midi_note_to_frequency_hertz(midi_note: float) -> float:
    return 440.0 * 2 ** ((midi_note - 69) / 12)


class _Synthesizer:
    def __init__(self, sample_rate_hertz: int, seed: int):
        self.sample_rate_hertz = sample_rate_hertz
        self.random_generator = np.random.default_rng(seed)

    def synthesize_piano_note(self, frequency_hertz: float, duration_seconds: float, velocity: float) -> np.ndarray:
        """Felt-piano tone: slightly inharmonic partials, a soft attack and a long decay."""
        t = np.arange(int((duration_seconds + 2.5) * self.sample_rate_hertz)) / self.sample_rate_hertz
        waveform = np.zeros(len(t))
        for k in range(1, 7):
            partial_hertz = k * frequency_hertz * np.sqrt(1 + 0.0004 * k * k)
            if partial_hertz > 9000:
                break
            amplitude = velocity * (1 / k ** 1.7) * (0.8 if k == 1 else 1.0)
            waveform += amplitude * np.sin(2 * np.pi * partial_hertz * t + 0.3 * k) * np.exp(-t * (0.9 + 0.55 * k))
        attack = np.minimum(1, t / 0.012)
        release = np.clip(1 - (t - duration_seconds) / 1.2, 0, 1) ** 2
        return waveform * attack * np.where(t < duration_seconds, 1, release)

    def synthesize_pad(self, frequencies_hertz: list[float], duration_seconds: float, amplitude: float) -> np.ndarray:
        t = np.arange(int((duration_seconds + 3.0) * self.sample_rate_hertz)) / self.sample_rate_hertz
        waveform = np.zeros(len(t))
        for frequency_hertz in frequencies_hertz:
            for detune, weight in ((1.0, 1.0), (1.0023, 0.6), (0.9978, 0.6), (2.0, 0.18)):
                waveform += weight * np.sin(2 * np.pi * frequency_hertz * detune * t
                                            + self.random_generator.random() * 6.28)
        envelope = np.clip(t / 2.2, 0, 1) * np.clip(1 - (t - duration_seconds) / 2.8, 0, 1)
        return amplitude * waveform * np.sin(envelope * np.pi / 2) ** 2 / max(1, len(frequencies_hertz))

    def add(self, buffer: np.ndarray, signal: np.ndarray, start_seconds: float) -> None:
        i = int(start_seconds * self.sample_rate_hertz)
        if 0 <= i < len(buffer):
            j = min(len(buffer), i + len(signal))
            buffer[i:j] += signal[:j - i]


def compose(timeline: Timeline, episode_number: int, sample_rate_hertz: int) -> np.ndarray:
    """A mono track as long as the timeline: one progression per scene, a sparse right hand over a pad and bass."""
    root_midi_note, mode, seed = resolve_episode_theme(episode_number)
    synthesizer = _Synthesizer(sample_rate_hertz, seed)
    progressions = MAJOR_PROGRESSIONS if mode == "major" else MINOR_PROGRESSIONS
    beat_seconds = 60 / 50  # 50 bpm
    bar_seconds = 4 * beat_seconds
    sample_count = int(timeline.duration_seconds * sample_rate_hertz)
    piano, pad, bass = (np.zeros(sample_count + 6 * sample_rate_hertz) for _ in range(3))
    for index, scene in enumerate(timeline.scenes):
        start_seconds, end_seconds = scene.start_seconds, scene.start_seconds + scene.duration_seconds
        progression = progressions[index % len(progressions)]
        density = [0.35, 0.55, 0.45][index % 3]
        time_seconds, chord_index = start_seconds + 0.3, 0
        while time_seconds < end_seconds - 1.0:
            degree, quality = progression[chord_index % len(progression)]
            chord_root = root_midi_note + degree - (12 if degree >= 7 else 0)
            chord_notes = [chord_root + interval for interval in INTERVALS_BY_CHORD_QUALITY_MAP[quality]]
            chord_seconds = min(bar_seconds, end_seconds - time_seconds)
            pad_notes = [midi_note - 12 for midi_note in chord_notes[:3]] + [chord_notes[3]]
            pad_frequencies_hertz = [_convert_midi_note_to_frequency_hertz(midi_note) for midi_note in pad_notes]
            synthesizer.add(pad, synthesizer.synthesize_pad(pad_frequencies_hertz, chord_seconds, 0.09), time_seconds)
            bass_note = synthesizer.synthesize_piano_note(_convert_midi_note_to_frequency_hertz(chord_root - 24),
                                                          chord_seconds, 0.28)
            synthesizer.add(bass, bass_note, time_seconds)
            upper_notes = sorted({midi_note + 12 for midi_note in chord_notes} | {chord_notes[1] + 24})
            for step in range(4):
                if synthesizer.random_generator.random() < density or (step == 0 and chord_index % 2 == 0):
                    note = upper_notes[int(synthesizer.random_generator.integers(0, len(upper_notes)))]
                    note_seconds = beat_seconds * synthesizer.random_generator.choice([1, 1.5, 2])
                    velocity = 0.18 + 0.1 * synthesizer.random_generator.random()
                    piano_note = synthesizer.synthesize_piano_note(_convert_midi_note_to_frequency_hertz(note),
                                                                   note_seconds, velocity)
                    synthesizer.add(piano, piano_note,
                                    time_seconds + step * beat_seconds + synthesizer.random_generator.normal(0, 0.015))
            time_seconds += bar_seconds
            chord_index += 1
    if timeline.scenes:  # end on the tonic
        last_scene = timeline.scenes[-1]
        tonic_notes = [root_midi_note + interval
                       for interval in INTERVALS_BY_CHORD_QUALITY_MAP["maj7" if mode == "major" else "m9"]]
        tonic_frequencies_hertz = [_convert_midi_note_to_frequency_hertz(midi_note - 12) for midi_note in tonic_notes]
        synthesizer.add(pad, synthesizer.synthesize_pad(tonic_frequencies_hertz, 5.5, 0.1),
                        max(0.0, last_scene.start_seconds + last_scene.duration_seconds - 6))
    return (piano + pad + 0.5 * bass)[:sample_count]


def apply_reverb(mono: np.ndarray, sample_rate_hertz: int, tail_seconds: float = 2.6, wet: float = 0.32,
                 seed: int = 0) -> np.ndarray:
    """A stereo room: decaying noise impulse responses, a warm top and a clear low end for the voice."""
    random_generator = np.random.default_rng(seed)
    t = np.arange(int(tail_seconds * sample_rate_hertz)) / sample_rate_hertz
    channels = []
    for _ in range(2):
        impulse_response = random_generator.normal(0, 1, len(t)) * np.exp(-t / 0.55)
        impulse_response[:int(0.012 * sample_rate_hertz)] = 0
        impulse_response /= np.sqrt(np.sum(impulse_response ** 2))
        channels.append((1 - wet) * mono + wet * oaconvolve(mono, impulse_response)[:len(mono)])
    stereo = np.stack(channels, axis=1)
    stereo = sosfilt(butter(2, 6500, "low", fs=sample_rate_hertz, output="sos"), stereo, axis=0)
    return sosfilt(butter(2, 90, "high", fs=sample_rate_hertz, output="sos"), stereo, axis=0)


class Provider(BackgroundMusicProvider):
    name = "synthesized-piano"
    settings_model = Settings

    def make_track(self, timeline: Timeline, episode_number: int, settings: BaseModel, output_wav_file_path: Path,
                   sample_rate_hertz: int) -> bool:
        stereo = apply_reverb(compose(timeline, episode_number, sample_rate_hertz), sample_rate_hertz)
        peak = float(np.max(np.abs(stereo))) or 1.0
        wavfile.write(output_wav_file_path, sample_rate_hertz, (stereo / peak * 0.5 * 32767).astype(np.int16))
        return True
