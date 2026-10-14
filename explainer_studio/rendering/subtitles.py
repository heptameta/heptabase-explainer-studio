"""Subtitles (SRT) from the beats in timeline.json.

A beat's line is shown while it is spoken. Lines too long for one subtitle are split at punctuation (CJK lines at
，。、；：！？, Latin lines at sentence and clause breaks) into consecutive cues, timed by their share of the text.
CJK cues drop a trailing comma or full stop, as Chinese subtitles do.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CJK_LINE_MAX_CHARACTERS = 20  # characters packed onto one subtitle line
CJK_CLAUSE_MAX_CHARACTERS = 28  # a single clause up to this long stays whole rather than being cut mid-phrase
LATIN_LINE_MAX_CHARACTERS = 42
CJK_BREAK_CHARACTERS = "，。；：！？…—"  # clause breaks; 、 (between list items) is used only when a clause is still too long
LATIN_BREAK_PATTERN = re.compile(r"(?<=[.!?;:,—])\s+")


@dataclass(frozen=True)
class Cue:
    start_seconds: float
    end_seconds: float
    text: str


def _check_is_cjk(text: str) -> bool:
    return sum(1 for character in text if "　" <= character <= "鿿" or "豈" <= character <= "﫿") > len(text) / 4


def _pack(pieces: list[str], max_characters: int, joiner: str) -> list[str]:
    """Greedily join consecutive pieces while they fit in `max_characters` characters."""
    lines: list[str] = []
    for piece in pieces:
        if lines and len(lines[-1]) + len(joiner) + len(piece) <= max_characters:
            lines[-1] = f"{lines[-1]}{joiner}{piece}"
        else:
            lines.append(piece)
    return lines


def _hard_split(text: str, max_characters: int, is_cjk: bool) -> list[str]:
    if len(text) <= max_characters:
        return [text]
    if is_cjk:
        piece_count = -(-len(text) // max_characters)
        piece_characters = -(-len(text) // piece_count)
        return [text[i:i + piece_characters] for i in range(0, len(text), piece_characters)]
    return _pack(text.split(" "), max_characters, " ")


def split_line(text: str) -> list[str]:
    """One beat's line as subtitle pieces, each short enough for one line."""
    text = re.sub(r"\s+", " ", text.strip())
    is_cjk = _check_is_cjk(text)
    if is_cjk:
        pieces = [piece.strip() for piece in re.split(f"(?<=[{CJK_BREAK_CHARACTERS}])", text) if piece.strip()]
        pieces = [part for piece in pieces
                  for part in (_pack(re.split("(?<=、)", piece), CJK_LINE_MAX_CHARACTERS, "")
                               if len(piece) > CJK_CLAUSE_MAX_CHARACTERS else [piece])]
        lines = _pack(pieces, CJK_LINE_MAX_CHARACTERS, "")
        lines = [piece for line in lines for piece in _hard_split(line, CJK_CLAUSE_MAX_CHARACTERS, True)]
        return [line.rstrip("，。、；") or line for line in lines]
    pieces = [piece for piece in LATIN_BREAK_PATTERN.split(text) if piece]
    lines = _pack(pieces, LATIN_LINE_MAX_CHARACTERS, " ")
    return [piece for line in lines for piece in _hard_split(line, LATIN_LINE_MAX_CHARACTERS, False)]


def build_beat_cues(start_seconds: float, duration_seconds: float, text: str) -> list[Cue]:
    pieces = split_line(text)
    total_characters = sum(len(piece) for piece in pieces) or 1
    cues, time_seconds = [], start_seconds
    for piece in pieces:
        cue_seconds = duration_seconds * len(piece) / total_characters
        cues.append(Cue(time_seconds, time_seconds + cue_seconds, piece))
        time_seconds += cue_seconds
    return cues


def _format_srt_time(seconds: float) -> str:
    milliseconds = round(max(seconds, 0) * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"


def serialize_srt(cues: list[Cue]) -> str:
    blocks = [f"{i}\n{_format_srt_time(cue.start_seconds)} --> {_format_srt_time(cue.end_seconds)}\n{cue.text}\n"
              for i, cue in enumerate(cues, start=1)]
    return "\n".join(blocks)
