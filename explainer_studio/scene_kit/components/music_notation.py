"""Music notation with sound: a score engraved by Verovio from ABC, MusicXML, MEI or Humdrum, drawn as native shapes
whose notes keep their ids, plus a plain piano rendering so notes light up exactly as they sound.

    score = get_score("X:1\nM:4/4\nL:1/4\nK:C\nC D E F | G2 G2 |]", width=11)
    self.play(score.notes[4].animate.set_color(YELLOW))   # notes in playing order
    play_score(self, score)                                  # notes light up in time; the sound goes into the mix
"""

from __future__ import annotations

import hashlib
import io

import numpy as np
from manimlib import *

from ... import user_dirs
from ...file_io import write_bytes_atomic
from ..context import get_scene_context
from ..media import PartsSVG
from ..parts import PartsMixin

__all__ = ["Score", "get_score", "play_score"]

SAMPLE_RATE_HERTZ = 48000
_FORMAT_BY_SUFFIX_MAP = {".abc": "abc", ".musicxml": "musicxml", ".xml": "musicxml", ".mxl": "musicxml",
                         ".mei": "mei", ".krn": "humdrum"}


def _read_score_source(source: str, format_name: str | None) -> tuple[str, str]:
    if len(source) < 300 and "\n" not in source:
        source_file_path = get_scene_context().resolve_path(source)
        if source_file_path.exists():
            format_name = format_name or _FORMAT_BY_SUFFIX_MAP.get(source_file_path.suffix.lower(), "auto")
            return source_file_path.read_text(encoding="utf-8"), format_name
    if format_name is None:
        if source.lstrip().startswith("X:"):
            format_name = "abc"
        else:
            format_name = "musicxml" if "<score-partwise" in source else "auto"
    return source, format_name


def _synthesize_piano_note(frequency_hertz: float, duration_seconds: float, velocity: float = 0.5) -> np.ndarray:
    sample_count = int((duration_seconds + 0.6) * SAMPLE_RATE_HERTZ)
    sample_times_seconds = np.arange(sample_count) / SAMPLE_RATE_HERTZ
    envelope = (np.exp(-sample_times_seconds * (2.2 + frequency_hertz / 900))
                * np.clip(sample_times_seconds / 0.005, 0, 1))
    tone = sum(amplitude * np.sin(2 * np.pi * frequency_hertz * harmonic * sample_times_seconds)
               for harmonic, amplitude in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.1)))
    release = np.clip((duration_seconds + 0.6 - sample_times_seconds) / 0.6, 0, 1)
    return (tone * envelope * release * velocity).astype(np.float32)


class Score(PartsMixin, PartsSVG):
    """Parts: .notes (in playing order; each a VGroup of the note's shapes), .note_ids, .events
    [(seconds, [ids starting], [ids ending])], .duration_seconds, .get_notes_at(time_seconds), .audio_file_path (a
    wav of the score)."""

    def get_notes_at(self, time_seconds: float) -> VGroup:
        """The notes sounding at time_seconds."""
        midi_values_by_note_id_map = self._midi_values_by_note_id_map
        return VGroup(*[self.notes[index] for index, note_id in enumerate(self.note_ids)
                        if midi_values_by_note_id_map[note_id][2] <= time_seconds
                        < midi_values_by_note_id_map[note_id][2] + midi_values_by_note_id_map[note_id][1]])


def get_score(source: str, format_name: str | None = None, width: float = 11.0, color=WHITE,
              tempo_scale: float = 1.0, scale: int = 60) -> Score:
    """Engrave a score (ABC text, MusicXML/MEI text, or a file relative to production/) with Verovio."""
    import verovio  # imported here: most scenes engrave no score
    source_text, format_name = _read_score_source(source, format_name)
    toolkit = verovio.toolkit()
    toolkit.setOptions({"inputFrom": format_name, "svgViewBox": True, "adjustPageHeight": True, "pageWidth": 2100,
                        "scale": scale, "header": "none", "footer": "none", "svgRemoveXlink": True})
    if not toolkit.loadData(source_text):
        raise ValueError("Verovio could not read this score (check the ABC/MusicXML)")
    svg = toolkit.renderToSVG(1)
    svg_hash = hashlib.sha1((svg + str(tempo_scale)).encode()).hexdigest()[:12]
    cache_dir_path = user_dirs.get_cache_dir_path() / "scores"
    cache_dir_path.mkdir(parents=True, exist_ok=True)
    svg_file_path = cache_dir_path / f"score_{svg_hash}.svg"
    svg_file_path.write_text(svg, encoding="utf-8")
    score = Score(str(svg_file_path), height=None)
    score.set_width(width)
    score.set_fill(color).set_stroke(color)
    # timing and pitch of every note
    events, midi_values_by_note_id_map = [], {}
    for event in toolkit.renderToTimemap():
        time_seconds = event["tstamp"] / 1000.0 / tempo_scale
        starting_note_ids, ending_note_ids = event.get("on", []), event.get("off", [])
        events.append((time_seconds, starting_note_ids, ending_note_ids))
        for note_id in starting_note_ids:
            midi_values = toolkit.getMIDIValuesForElement(note_id)
            midi_values_by_note_id_map[note_id] = (midi_values.get("pitch", 60),
                                                   midi_values.get("duration", 500) / 1000.0 / tempo_scale,
                                                   time_seconds)
    note_ids_in_order = [note_id for _, starting_note_ids, _ in events for note_id in starting_note_ids]
    notes = []
    for note_id in note_ids_in_order:
        try:
            notes.append(score.get_part(note_id))
        except KeyError:
            notes.append(VGroup())
    score.notes, score.note_ids, score.events = notes, note_ids_in_order, events
    score.duration_seconds = max((midi_values[2] + midi_values[1]
                                  for midi_values in midi_values_by_note_id_map.values()), default=0.0)
    score._midi_values_by_note_id_map = midi_values_by_note_id_map
    # a plain piano rendering of the score, for play_score
    samples = np.zeros(int((score.duration_seconds + 1.0) * SAMPLE_RATE_HERTZ), dtype=np.float32)
    for pitch, duration_seconds, time_seconds in midi_values_by_note_id_map.values():
        note_samples = _synthesize_piano_note(440 * 2 ** ((pitch - 69) / 12), duration_seconds)
        start_index = int(time_seconds * SAMPLE_RATE_HERTZ)
        samples[start_index:start_index + len(note_samples)] += note_samples[: len(samples) - start_index]
    peak = np.max(np.abs(samples)) or 1
    from scipy.io import wavfile
    # in the series, since a sound the mix plays is a file under production/ (outside a series, in the cache)
    series = get_scene_context().series
    wav_dir_path = series.shared_assets_dir_path / "audio" / "scores" if series else cache_dir_path
    wav_dir_path.mkdir(parents=True, exist_ok=True)
    wav_file_path = wav_dir_path / f"score_{svg_hash}.wav"
    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, SAMPLE_RATE_HERTZ, (samples / peak * 0.8 * 32767).astype(np.int16))
    # atomically, since scenes rendering in parallel can make the same score
    write_bytes_atomic(wav_file_path, wav_buffer.getvalue())
    score.audio_file_path = str(wav_file_path)
    return score


def play_score(scene, score: Score, color=YELLOW, should_play_audio: bool = True,
               gain_decibels: float = -4.0) -> None:
    """Play the score: each note lights up while it sounds and its sound goes into the final mix."""
    fill_color_by_object_id_map = {id(note): note.get_fill_color() for note in score.notes}
    elapsed = {"seconds": 0.0}
    note_ids_in_order, midi_values_by_note_id_map = score.note_ids, score._midi_values_by_note_id_map

    def update(mobject, dt):
        elapsed["seconds"] += dt
        elapsed_seconds = elapsed["seconds"]
        for index, note_id in enumerate(note_ids_in_order):
            _, note_duration_seconds, note_start_seconds = midi_values_by_note_id_map[note_id]
            is_sounding = note_start_seconds <= elapsed_seconds < note_start_seconds + note_duration_seconds
            note = score.notes[index]
            note_color = color if is_sounding else fill_color_by_object_id_map[id(note)]
            note.set_fill(note_color).set_stroke(note_color)

    if should_play_audio and hasattr(scene, "play_sound"):
        scene.play_sound(score.audio_file_path, gain_decibels, should_duck_background_music=True,
                         duration_seconds=score.duration_seconds + 0.5)
    score.add_updater(update)
    scene.wait(score.duration_seconds + 0.3)
    score.remove_updater(update)
    for note in score.notes:
        note.set_fill(fill_color_by_object_id_map[id(note)]).set_stroke(fill_color_by_object_id_map[id(note)])
