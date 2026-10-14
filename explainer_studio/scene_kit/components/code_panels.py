"""Code panels: syntax-highlighted code, one mobject per line, so lines can be highlighted, dimmed or revealed."""

from __future__ import annotations

import textwrap

from manimlib import *

from ..parts import Parts
from ..style import HIGHLIGHT_COLOR, MONO_FONT

__all__ = ["get_code_panel", "highlight_lines"]


# Pango's default features keep JetBrains Mono's contextual alternates, which draw ->, ==, != and // as one glyph.
FONT_FEATURES = "liga=0,dlig=0,clig=0,hlig=0,calt=0"
BASELINE_CHARACTERS = "abcdefhiklmnorstuvwxzABCDEFGHIKLMNOPRSTUVWXYZ0123456789"


def _get_code(text: str, **kwargs) -> Code:
    return Code(text, font=MONO_FONT, lsh=1.3, alignment="LEFT", global_config={"font_features": FONT_FEATURES},
                **kwargs)


def _lay_out_whole_block(source_lines: list[str], **kwargs) -> tuple[list[VGroup | None], tuple[int, float]] | None:
    """Lay the whole block out once (Pango keeps baselines and indentation exact), then cut its glyphs into lines.
    Also returns (line, y) of one line's baseline, from a glyph that sits on it. None when a glyph does not stand
    for one character (a combining accent, an emoji sequence, a zero-width space) or no glyph shows the baseline."""
    block_code = _get_code("\n".join(source_lines), **kwargs)
    glyph_counts = [len("".join(line.split())) for line in source_lines]
    if sum(glyph_counts) != len(block_code.submobjects):
        return None
    lines, start, anchor = [], 0, None
    for i, glyph_count in enumerate(glyph_counts):
        glyphs = block_code.submobjects[start:start + glyph_count]
        start += glyph_count
        lines.append(VGroup(*glyphs) if glyph_count else None)
        line_glyph_characters = "".join(source_lines[i].split())
        anchor_index = next((index for index, character in enumerate(line_glyph_characters)
                             if character in BASELINE_CHARACTERS), None)
        if anchor is None and anchor_index is not None:
            anchor = (i, glyphs[anchor_index].get_bottom()[1])
    return (lines, anchor) if anchor else None


def _lay_out_line_by_line(source_lines: list[str], **kwargs) -> tuple[list[VGroup | None], tuple[int, float]]:
    """Each line laid out on its own above an "M" that marks column 0 and the next baseline, then put in place."""
    probe = _get_code("M\nM", **kwargs)
    line_pitch = probe.submobjects[0].get_bottom()[1] - probe.submobjects[1].get_bottom()[1]
    lines = []
    for i, line in enumerate(source_lines):
        if not line.strip():
            lines.append(None)
            continue
        laid_out = _get_code(line + "\nM", **kwargs)
        marker = laid_out.submobjects[-1]
        glyphs = VGroup(*laid_out.submobjects[:-1])
        glyphs.shift((-marker.get_left()[0]) * RIGHT + (-i * line_pitch - marker.get_bottom()[1] - line_pitch) * UP)
        lines.append(glyphs)
    return lines, (0, 0.0)


def get_code_panel(code: str, language: str = "python", font_size: float = 22,
                   should_show_line_numbers: bool = True, style: str = "monokai", width: float | None = None,
                   background_color: str = "#111418") -> VGroup:
    """Syntax-highlighted code, one mobject per line so lines can be highlighted, dimmed or revealed.
    Parts: .lines[i] (0-based), .numbers[i], .background. Use highlight_lines(panel, [i, ...]). For a real file, pass
    read_file_excerpt(...) as code."""
    source_lines = textwrap.dedent(code).strip("\n").expandtabs(4).split("\n")
    options = {"font_size": font_size, "language": language, "code_style": style}
    glyph_lines, (anchor_line, baseline) = (_lay_out_whole_block(source_lines, **options)
                                            or _lay_out_line_by_line(source_lines, **options))
    left = min((line.get_left()[0] for line in glyph_lines if line is not None), default=0.0)
    line_number_text = Text("\n".join(str(i + 1) for i in range(len(source_lines))), font=MONO_FONT,
                            font_size=font_size, lsh=1.3, alignment="RIGHT").set_color(GREY_D)
    first_digit_index = sum(len(str(j + 1)) for j in range(anchor_line))
    line_number_text.next_to(left * RIGHT, LEFT, 0.35)
    line_number_text.shift((baseline - line_number_text.submobjects[first_digit_index].get_bottom()[1]) * UP)
    lines, numbers, digit_index = VGroup(), VGroup(), 0
    for i, line in enumerate(glyph_lines):
        digit_count = len(str(i + 1))
        number = VGroup(*line_number_text.submobjects[digit_index:digit_index + digit_count])
        digit_index += digit_count
        if line is None:
            line = VMobject()
            line.set_points_as_corners([[left, number.get_y(), 0]] * 2)
        line.text = source_lines[i].strip()
        lines.add(line)
        numbers.add(number)
    for line in list(lines) + list(numbers):
        line.font_size, line._base_size = font_size, (line.get_width(), line.get_height())
    if not should_show_line_numbers:
        numbers = VGroup()
    body = VGroup(numbers, lines)
    background = SurroundingRectangle(body, buff=0.35).set_fill(background_color, 1).set_stroke(GREY_D, 1)
    background.round_corners(0.12)
    panel = Parts(background, body)
    if width:
        panel.set_width(width)
    panel.center()
    panel.lines, panel.numbers, panel.background = lines, numbers, background
    return panel


def highlight_lines(panel: VGroup, indices: list[int], color=HIGHLIGHT_COLOR, dim_opacity: float = 0.3) -> tuple[Mobject, list[Animation]]:
    """Box the given lines and dim the rest. Returns (box, animations); play the animations, keep the box."""
    highlighted_lines = VGroup(*(panel.lines[i] for i in indices))
    box = SurroundingRectangle(highlighted_lines, buff=0.08).set_stroke(color, 2)
    box.stretch_to_fit_width(panel.background.get_width() - 0.15).match_x(panel.background)
    animations = []
    for i, line in enumerate(panel.lines):
        animations.append(line.animate.set_opacity(1 if i in indices else dim_opacity))
    return box, animations
