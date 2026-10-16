"""Mixing narration, sounds and background music.

Narration sits at -20 dBFS RMS. Built-in effects play at fixed levels under it; audio files and clip sound are
levelled to the speech and then given their gain_decibels. Background music sits 15 dB under the speech and ducks a
further 7 dB while someone speaks or a sound with should_duck_background_music plays. `render` then normalizes the
whole mix to -16 LUFS with a true peak of at most -1.5 dBTP, in two passes.
"""

from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

from .. import user_dirs
from ..errors import StudioError
from ..schemas.timeline import TimelineSound, TimelineSoundEffect
from . import sound_effects

SAMPLE_RATE_HERTZ = 48000
SPEECH_RMS_DECIBELS = -20.0
EFFECT_PEAK_DECIBELS = -25.0  # an effect at level 1.0 peaks here (speech peaks near -11 dBFS)
MUSIC_UNDER_SPEECH_DECIBELS = -15.0
DUCK_DECIBELS = -7.0
LOUDNORM_TARGET_BY_PARAMETER_MAP = {"I": -16.0, "TP": -2.5, "LRA": 11.0}  # TP aimed 1 dB low: AAC encoding overshoots
MAX_TRUE_PEAK_DECIBELS = -1.5
# where speech has energy and the rumble a voice leaves in its pauses does not
VOICE_BAND_FILTER = signal.butter(4, 300, "highpass", fs=SAMPLE_RATE_HERTZ, output="sos")


def convert_decibels_to_gain(decibels: float) -> float:
    return 10 ** (decibels / 20)


def _find_ffmpeg() -> str:
    return user_dirs.find_tool("ffmpeg") or "ffmpeg"


def check_has_audio(path: Path) -> bool:
    ffprobe_path = user_dirs.find_tool("ffprobe") or "ffprobe"
    result = subprocess.run([ffprobe_path, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                             "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=False)
    return bool(result.stdout.strip())


def load_audio(path: Path, start_seconds: float = 0.0, duration_seconds: float | None = None,
               channel_count: int = 2) -> np.ndarray:
    """Any audio (or a video's sound) as float32 samples (n, channel_count) at SAMPLE_RATE_HERTZ; empty when it has
    none."""
    command = [_find_ffmpeg(), "-v", "error", *(["-ss", f"{start_seconds:.3f}"] if start_seconds else []),
               "-i", str(path),
               *(["-t", f"{duration_seconds:.3f}"] if duration_seconds is not None else []), "-vn", "-f", "f32le",
               "-ac", str(channel_count), "-ar", str(SAMPLE_RATE_HERTZ), "-"]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0 and path.is_file() and not check_has_audio(path):
        return np.zeros((0, channel_count), dtype=np.float32)  # a silent video: a Blender shot, a screen recording
    if result.returncode != 0:
        raise StudioError(f"cannot read the audio of {path}", result.stderr.decode(errors="replace").strip()[-300:],
                          "check that the file is an audio or video file ffmpeg can read")
    return np.frombuffer(result.stdout, dtype=np.float32).reshape(-1, channel_count)


def place(buffer: np.ndarray, signal: np.ndarray, start_seconds: float) -> None:
    i = round(start_seconds * SAMPLE_RATE_HERTZ)
    if i >= len(buffer) or not len(signal):
        return
    if i < 0:
        signal, i = signal[-i:], 0
    j = min(len(buffer), i + len(signal))
    buffer[i:j] += signal[:j - i]


def measure_rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64)))) if samples.size else 0.0


def _level_to_speech(samples: np.ndarray, gain_decibels: float) -> np.ndarray:
    level = measure_rms(samples)
    if level < 1e-5:
        return samples
    scaled = samples * (convert_decibels_to_gain(SPEECH_RMS_DECIBELS + gain_decibels) / level)
    peak = float(np.max(np.abs(scaled)))
    return scaled * (convert_decibels_to_gain(-1) / peak) if peak > convert_decibels_to_gain(-1) else scaled


def load_sound_samples(sound: TimelineSound, production_dir_path: Path) -> np.ndarray:
    """One recorded sound as stereo samples at its level (before it is placed)."""
    source = sound.sound
    if isinstance(source, TimelineSoundEffect):
        samples = (sound_effects.synthesize(source.effect_name, SAMPLE_RATE_HERTZ)
                   * convert_decibels_to_gain(EFFECT_PEAK_DECIBELS + sound.gain_decibels))
        return samples[:int(sound.duration_seconds * SAMPLE_RATE_HERTZ)]
    samples = load_audio(production_dir_path / source.source_file_path, source.source_start_seconds,
                         sound.duration_seconds)
    return _level_to_speech(samples, sound.gain_decibels)


def clean_narration_line_edges(line: np.ndarray) -> np.ndarray:
    """One narration line (mono) without a stray burst at its end or rumble after its last word, faded in and out so
    it starts and ends at zero.

    A voice sometimes ends a line with silence and then the first tens of milliseconds of a breath or the next
    phrase, cut off mid-rise (ElevenLabs does, with the next line's text as context). Placed as is, that is a thump
    and a step: a pop between sentences, or a clipped "sh" when it runs past 80 ms. After at least 150 ms of silence at
    the very end, a sound of at most 80 ms is silenced, and so is one of up to 300 ms that is still getting louder at
    the last sample (its last 10 ms within 6 dB of its loudest): speech that ends on its own fades out first.

    A voice also often leaves up to a second of low rumble after its last word (ElevenLabs does, given both neighbors'
    text), which the speech gain makes audible and the line's end then cuts off. So 80 ms after the last sound in the
    voice band (above 300 Hz) the line fades to silence over 200 ms. The line keeps its length, so the timeline does
    not change.
    """
    frame_length = SAMPLE_RATE_HERTZ // 100  # 10 ms
    frame_count = len(line) // frame_length
    line = line.copy()
    end = len(line)
    if frame_count:
        frame_rms = np.sqrt(np.mean(np.square(line[:frame_count * frame_length].reshape(frame_count, frame_length),
                                              dtype=np.float64), axis=1))
        is_silent = frame_rms < convert_decibels_to_gain(-50)
        tail_frame_count = 0
        while tail_frame_count < frame_count and not is_silent[frame_count - 1 - tail_frame_count]:
            tail_frame_count += 1
        silence_frame_count = 0
        while (tail_frame_count + silence_frame_count < frame_count
               and is_silent[frame_count - 1 - tail_frame_count - silence_frame_count]):
            silence_frame_count += 1
        tail_rms = frame_rms[frame_count - tail_frame_count:]
        is_cut_off_rising = tail_frame_count > 0 and tail_rms[-1] >= tail_rms.max() * convert_decibels_to_gain(-6)
        if silence_frame_count >= 15 and (0 < tail_frame_count <= 8 or (tail_frame_count <= 30 and is_cut_off_rising)):
            end = (frame_count - tail_frame_count) * frame_length
        last_voiced_frame_index = _find_last_voiced_frame_index(line[:end], frame_length)
        if last_voiced_frame_index is not None:
            pause_fade_start = (last_voiced_frame_index + 1) * frame_length + SAMPLE_RATE_HERTZ * 80 // 1000
            if pause_fade_start < end:
                pause_fade_length = min(end - pause_fade_start, SAMPLE_RATE_HERTZ * 200 // 1000)
                line[pause_fade_start:pause_fade_start + pause_fade_length] *= np.square(
                    np.linspace(1, 0, pause_fade_length, dtype=np.float32))
                end = pause_fade_start + pause_fade_length
    line[end:] = 0
    fade_in_length = min(end, SAMPLE_RATE_HERTZ * 5 // 1000)
    fade_out_length = min(end, SAMPLE_RATE_HERTZ * 15 // 1000)
    line[:fade_in_length] *= np.linspace(0, 1, fade_in_length, dtype=np.float32)
    line[end - fade_out_length:end] *= np.linspace(1, 0, fade_out_length, dtype=np.float32)
    return line


def _find_last_voiced_frame_index(line: np.ndarray, frame_length: int) -> int | None:
    """The last 10 ms frame with sound in the voice band (above 300 Hz, at -60 dBFS or louder). A sound of at most
    300 ms that runs to the line's end after at least 150 ms without one, still getting louder at the last frame,
    does not count: it is the start of a breath or the next phrase, too quiet to be silenced as a burst, and it fades
    out with the pause."""
    frame_count = len(line) // frame_length
    if not frame_count:
        return None
    voice_band = signal.sosfiltfilt(VOICE_BAND_FILTER, line)[:frame_count * frame_length]
    voice_band_rms = np.sqrt(np.mean(np.square(voice_band.reshape(frame_count, frame_length), dtype=np.float64),
                                     axis=1))
    voiced_frame_indices = np.flatnonzero(voice_band_rms >= convert_decibels_to_gain(-60))
    if not len(voiced_frame_indices):
        return None
    gap_positions = np.flatnonzero(np.diff(voiced_frame_indices) > 15)  # a gap of at least 150 ms
    if voiced_frame_indices[-1] == frame_count - 1 and len(gap_positions):
        last_run_start = voiced_frame_indices[gap_positions[-1] + 1]
        last_run_rms = voice_band_rms[last_run_start:]
        if len(last_run_rms) <= 30 and last_run_rms[-1] >= last_run_rms.max() * convert_decibels_to_gain(-6):
            return int(voiced_frame_indices[gap_positions[-1]])
    return int(voiced_frame_indices[-1])


def _load_all(function, items: list) -> list:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(function, items))


def mix_voice_and_sounds(duration_seconds: float, narration_clips: list[tuple[float, Path]],
                         sounds: list[TimelineSound], production_dir_path: Path) -> np.ndarray:
    """Narration clips (start_seconds, wav) and sounds placed on a silent stereo track of `duration_seconds`. All
    narration takes one gain that brings its speech to SPEECH_RMS_DECIBELS, so the voice keeps its own dynamics from
    line to line."""
    track = np.zeros((round(duration_seconds * SAMPLE_RATE_HERTZ), 2), dtype=np.float32)
    lines = _load_all(lambda narration_clip: clean_narration_line_edges(
        load_audio(narration_clip[1], channel_count=1)[:, 0]), narration_clips)
    voiced_samples = (np.concatenate([line[np.abs(line) > convert_decibels_to_gain(-50)] for line in lines]) if lines
                      else np.zeros(0))
    voiced_rms = measure_rms(voiced_samples)
    gain = convert_decibels_to_gain(SPEECH_RMS_DECIBELS) / voiced_rms if voiced_rms > 1e-5 else 1.0
    for (start_seconds, _), line in zip(narration_clips, lines, strict=True):
        place(track, np.repeat((line * gain)[:, None], 2, axis=1), start_seconds)
    sound_samples = _load_all(lambda sound: load_sound_samples(sound, production_dir_path), sounds)
    for sound, samples in zip(sounds, sound_samples, strict=True):
        place(track, samples, sound.start_seconds)
    return track


def _smooth(target: np.ndarray, attack_seconds: float, release_seconds: float, rate_hertz: int) -> np.ndarray:
    """One-pole smoothing with separate attack (going down) and release (going up) times."""
    smoothed = np.empty_like(target)
    gain = target[0]
    down, up = np.exp(-1 / (attack_seconds * rate_hertz)), np.exp(-1 / (release_seconds * rate_hertz))
    for i, value in enumerate(target):
        coefficient = down if value < gain else up
        gain = coefficient * gain + (1 - coefficient) * value
        smoothed[i] = gain
    return smoothed


def build_duck_envelope(sample_count: int, busy_intervals: list[tuple[float, float]]) -> np.ndarray:
    """Music gain per sample: 1 normally, DUCK_DECIBELS while any (start, end) interval is busy, with smooth edges."""
    grid_rate_hertz = 100
    grid = np.ones(int(np.ceil(sample_count / SAMPLE_RATE_HERTZ * grid_rate_hertz)) + 1)
    for start_seconds, end_seconds in busy_intervals:
        grid[max(0, int(start_seconds * grid_rate_hertz)):max(0, int(end_seconds * grid_rate_hertz))] = (
            convert_decibels_to_gain(DUCK_DECIBELS))
    envelope = _smooth(grid, attack_seconds=0.25, release_seconds=0.9, rate_hertz=grid_rate_hertz)
    return np.interp(np.arange(sample_count) / SAMPLE_RATE_HERTZ, np.arange(len(envelope)) / grid_rate_hertz,
                     envelope).astype(np.float32)


def add_background_music(track: np.ndarray, music: np.ndarray,
                         busy_intervals: list[tuple[float, float]]) -> np.ndarray:
    """Music levelled under the speech, ducked while `busy_intervals`, faded in and out, added to the track."""
    sample_count = len(track)
    music = (music[:sample_count] if len(music) >= sample_count
             else np.pad(music, ((0, sample_count - len(music)), (0, 0))))
    level = measure_rms(music)
    if level < 1e-6:
        return track
    music = music * (convert_decibels_to_gain(SPEECH_RMS_DECIBELS + MUSIC_UNDER_SPEECH_DECIBELS) / level)
    index = np.arange(sample_count)
    fade = (np.clip(index / (3 * SAMPLE_RATE_HERTZ), 0, 1)
            * np.clip((sample_count - index) / (4 * SAMPLE_RATE_HERTZ), 0, 1))
    return track + music * (build_duck_envelope(sample_count, busy_intervals) * fade)[:, None]


def limit_peak(track: np.ndarray, peak_decibels: float = -1.0) -> np.ndarray:
    peak = float(np.max(np.abs(track))) if track.size else 0.0
    peak_gain = convert_decibels_to_gain(peak_decibels)
    return track * (peak_gain / peak) if peak > peak_gain else track


def write_wav(path: Path, track: np.ndarray) -> None:
    wavfile.write(path, SAMPLE_RATE_HERTZ, (np.clip(track, -1, 1) * 32767).astype(np.int16))


def read_wav(path: Path) -> np.ndarray:
    sample_rate_hertz, raw_samples = wavfile.read(path)
    samples = (raw_samples.astype(np.float32) / 32768.0 if raw_samples.dtype == np.int16
               else raw_samples.astype(np.float32))
    if samples.ndim == 1:
        samples = np.repeat(samples[:, None], 2, axis=1)
    if sample_rate_hertz != SAMPLE_RATE_HERTZ:
        raise StudioError(f"{path.name} is {sample_rate_hertz} Hz, not {SAMPLE_RATE_HERTZ} Hz",
                          "the mix works at one sample rate",
                          "write background music at the sample rate render asks for")
    return samples


def normalize_loudness(source_file_path: Path, output_file_path: Path) -> None:
    """Two-pass loudnorm to -16 LUFS integrated, aiming the true peak 1 dB under the -1.5 dBTP limit."""
    loudnorm_target = LOUDNORM_TARGET_BY_PARAMETER_MAP
    loudnorm_filter = f"loudnorm=I={loudnorm_target['I']}:TP={loudnorm_target['TP']}:LRA={loudnorm_target['LRA']}"
    measured = subprocess.run([_find_ffmpeg(), "-hide_banner", "-i", str(source_file_path), "-af",
                               loudnorm_filter + ":print_format=json", "-f", "null", "-"],
                              capture_output=True, text=True, check=False)
    blocks = re.findall(r"\{[^{}]*\}", measured.stderr, re.DOTALL)
    if measured.returncode != 0 or not blocks:
        raise StudioError("loudness measurement failed", measured.stderr.strip()[-300:], "check the ffmpeg install")
    measurement = json.loads(blocks[-1])
    second_pass_filter = (f"{loudnorm_filter}:measured_I={measurement['input_i']}"
                          f":measured_TP={measurement['input_tp']}:measured_LRA={measurement['input_lra']}"
                          f":measured_thresh={measurement['input_thresh']}:offset={measurement['target_offset']}"
                          ":linear=true")
    result = subprocess.run([_find_ffmpeg(), "-v", "error", "-y", "-i", str(source_file_path), "-af",
                             second_pass_filter, "-ar", str(SAMPLE_RATE_HERTZ), "-c:a", "pcm_s16le",
                             str(output_file_path)],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise StudioError("loudness normalization failed", result.stderr.strip()[-300:], "check the ffmpeg install")


def measure_loudness(media_file_path: Path) -> tuple[float | None, float | None]:
    """Integrated loudness (LUFS) and true peak (dBTP) of a file's audio."""
    result = subprocess.run([_find_ffmpeg(), "-hide_banner", "-i", str(media_file_path), "-map", "0:a", "-af",
                             "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=False)
    summary_text = result.stderr[result.stderr.rfind("Summary"):]
    integrated_match = re.search(r"I:\s*(-?[\d.]+) LUFS", summary_text)
    peak_match = re.search(r"Peak:\s*(-?[\d.]+) dBFS", summary_text)
    return (float(integrated_match.group(1)) if integrated_match else None,
            float(peak_match.group(1)) if peak_match else None)
