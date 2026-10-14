"""Cards and text devices: title and quote cards, chips, question and reframe cards, claims to overturn, checklists,
answer cards and scoreboards for real runs, knobs, goal and explanation cards, the episode outline bar, and text
passages treated as objects."""

from __future__ import annotations

import textwrap

from manimlib import *

from ..parts import Parts
from ..style import (
    BODY_FONT_SIZE,
    FONT,
    HEADING_FONT_SIZE,
    LABEL_FONT_SIZE,
    QUOTE_COLOR,
    SMALL_FONT_SIZE,
    TITLE_FONT_SIZE,
    choose_local_text,
)

__all__ = [
    "add_checklist_row",
    "add_scoreboard_row",
    "animate_knob_to",
    "animate_outline_to",
    "get_answer_card",
    "get_answer_mark",
    "get_check_mark",
    "get_checklist",
    "get_checklist_strike_line",
    "get_claim",
    "get_explanation_card",
    "get_fact_chip",
    "get_goal_card",
    "get_knob",
    "get_outline_bar",
    "get_passage",
    "get_question_card",
    "get_quote",
    "get_reframe_card",
    "get_scoreboard",
    "get_section_label",
    "get_title_card",
    "highlight_phrase",
    "pin_evidence",
    "strike_claim",
]


def get_title_card(title: str, subtitle: str = "", color=WHITE) -> VGroup:
    title_mobject = Text(title, font_size=TITLE_FONT_SIZE).set_color(color)
    group = VGroup(title_mobject)
    if subtitle:
        subtitle_mobject = Text(subtitle, font_size=LABEL_FONT_SIZE).set_color(GREY_B)
        group.add(subtitle_mobject.next_to(title_mobject, DOWN, MED_LARGE_BUFF))
    group.add(Underline(title_mobject, buff=MED_SMALL_BUFF).set_stroke(GREY_B, 2))
    return group


def get_quote(quote: str, author: str, year: str = "", width: float = 11) -> VGroup:
    """A quotation: the quote with its attribution below."""
    quote_mobject = Text(choose_local_text(f"「{quote}」", f"“{quote}”"), font_size=BODY_FONT_SIZE).set_color(QUOTE_COLOR)
    quote_mobject.set_max_width(width)
    attribution = Text(f"— {author}" + (f", {year}" if year else ""), font_size=LABEL_FONT_SIZE).set_color(GREY_B)
    attribution.next_to(quote_mobject, DOWN, MED_LARGE_BUFF, aligned_edge=RIGHT)
    return VGroup(quote_mobject, attribution)


def get_section_label(text: str, color=WHITE, font_size=HEADING_FONT_SIZE) -> VGroup:
    """A quiet section title with a thin underline."""
    label = Text(text, font_size=font_size).set_color(color)
    return VGroup(label, Underline(label, buff=0.1).set_stroke(GREY_B, 2))


def get_fact_chip(text: str, color=GREY_A, font_size=SMALL_FONT_SIZE) -> VGroup:
    """A small rounded chip holding one fact, name or year."""
    label = Text(text, font_size=font_size).set_color(color)
    box = RoundedRectangle(width=label.get_width() + 0.35, height=label.get_height() + 0.25, corner_radius=0.12)
    box.set_fill(BLACK, 0.6).set_stroke(color, 1).move_to(label)
    return VGroup(box, label)


def get_question_card(text: str, color_by_word_map: dict | None = None, width: float = 5.5,
                      font_size=LABEL_FONT_SIZE + 4) -> VGroup:
    """A short question card (three lines at most) with key nouns in their concept colours."""
    label = Text(text, font_size=font_size, t2c=color_by_word_map or {}).set_max_width(width)
    box = SurroundingRectangle(label, buff=0.35).set_stroke(GREY_B, 1.5).set_fill(BLACK, 0.5)
    box.round_corners(0.15)
    return VGroup(box, label)


def get_reframe_card(old_question: str, new_question: str, color_by_word_map: dict | None = None) -> VGroup:
    """The old question (dim) turning into the new one (keywords coloured)."""
    old_mobject = Text(old_question, font_size=LABEL_FONT_SIZE + 4).set_color(GREY_C).set_max_width(4.5)
    new_mobject = Text(new_question, font_size=BODY_FONT_SIZE, t2c=color_by_word_map or {}).set_max_width(6.5)
    arrow = Arrow(LEFT, RIGHT, buff=0).set_stroke(GREY_A, 3).set_width(1.2)
    return VGroup(old_mobject, arrow, new_mobject).arrange(RIGHT, buff=0.4)


def get_claim(text: str, tag: str, color_by_word_map: dict | None = None, width: float = 6.0,
              font_size: float = LABEL_FONT_SIZE + 2, color=GREY_A) -> VGroup:
    """A claim the episode is about to test or overturn (an intuition, a rival's view, a hypothesis), with its status
    on screen from the moment it appears: a small tag on a thin box around the sentence, so the screen read alone
    never passes it off as the point. Parts: .box, .text, .tag. strike_claim crosses it out."""
    label = Text(text, font_size=font_size).set_color(color)
    for word, word_color in (color_by_word_map or {}).items():
        label.select_parts(word).set_color(word_color)
    label.set_max_width(width)
    box = SurroundingRectangle(label, buff=0.3).set_stroke(GREY_B, 1.5).set_fill(BLACK, 0.5)
    box.round_corners(0.12)
    tag_mobject = Text(tag, font_size=SMALL_FONT_SIZE).set_color(GREY_B).next_to(box, UP, buff=0.1, aligned_edge=LEFT)
    group = Parts(box, label, tag_mobject)
    group.box, group.text, group.tag = box, label, tag_mobject
    return group


def strike_claim(scene, claim: VGroup, replacement_text: str = "", tag: str = "",
                 color_by_word_map: dict | None = None, direction=DOWN, color=RED,
                 run_time: float = 1.2) -> VGroup | None:
    """Cross out a get_claim the narration has just overturned and, given `replacement_text`, put the sentence that
    replaces it beside it, so the screen keeps both what was believed and what holds now. Returns the new claim or
    None."""
    line = Line(claim.text.get_left() + 0.1 * LEFT, claim.text.get_right() + 0.1 * RIGHT).set_stroke(color, 4)
    claim.add(line)
    scene.play(ShowCreation(line), claim.text.animate.set_opacity(0.45), claim.box.animate.set_stroke(GREY_D),
               run_time=run_time * 0.6)
    if not replacement_text:
        return None
    replacement = get_claim(replacement_text, tag=tag, color_by_word_map=color_by_word_map,
                            width=max(claim.text.get_width() + 1.0, 6.0), color=WHITE)
    if not tag:
        replacement.remove(replacement.tag)
    replacement.box.set_stroke(color=WHITE, width=2)
    replacement.next_to(claim, direction, buff=0.35)
    scene.play(FadeIn(replacement, shift=0.2 * direction), run_time=run_time * 0.6)
    return replacement


def get_checklist(title: str, row_texts: list[str], checked_row_indices: tuple = (), width: float = 4.6,
                  font_size: float = SMALL_FONT_SIZE + 2, t2c_by_row_index_map: dict[int, dict] | None = None,
                  color_by_row_index_map: dict[int, str] | None = None) -> VGroup:
    """A numbered checklist (a rule card that grows, a list ticked off across a video). Parts: .title, .rows[i] =
    VGroup(box, label), .checks. Tick with get_check_mark, add rows with add_checklist_row."""
    title_mobject = Text(title, font_size=font_size + 6).set_color(WHITE)
    rows = VGroup()
    for i, row_text in enumerate(row_texts):
        box = Square(0.32).set_stroke(GREY_A, 1.5).set_fill(BLACK, 0.5)
        label = Text(f"{i + 1}. {row_text}", font_size=font_size, t2c=(t2c_by_row_index_map or {}).get(i, {}))
        if color_by_row_index_map and i in color_by_row_index_map:
            label.set_color(color_by_row_index_map[i])
        label.set_max_width(width - 0.6)
        rows.add(VGroup(box, label).arrange(RIGHT, buff=0.22))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
    group = Parts(title_mobject, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
    group.title, group.rows, group.checks = title_mobject, rows, VGroup()
    for i in checked_row_indices:
        group.checks.add(get_check_mark(group, i))
    group.add(group.checks)
    return group


def get_check_mark(checklist: VGroup, i: int, color=GREEN) -> VMobject:
    """A tick sized to row i's box of a get_checklist."""
    box = checklist.rows[i][0]
    size = box.get_width()
    tick = VMobject().set_points_as_corners([[-0.35, 0.0, 0], [-0.08, -0.3, 0], [0.42, 0.38, 0]])
    return tick.set_stroke(color, 4).set_width(0.85 * size).move_to(box.get_center() + 0.05 * size * UP)


def add_checklist_row(card: VGroup, text: str, color=YELLOW, font_size: float = SMALL_FONT_SIZE + 2) -> list[Animation]:
    """Animations that add one numbered row under the last row of a get_checklist."""
    box = Square(0.32).set_stroke(GREY_A, 1.5).set_fill(BLACK, 0.5)
    label = Text(f"{len(card.rows) + 1}. {text}", font_size=font_size).set_color(color)
    row = VGroup(box, label).arrange(RIGHT, buff=0.22).next_to(card.rows[-1], DOWN, buff=0.26, aligned_edge=LEFT)
    card.rows.add(row)
    return [FadeIn(row, shift=0.15 * DOWN)]


def get_checklist_strike_line(card: VGroup, i: int, color=RED) -> VMobject:
    """A line through row i of a get_checklist (a rule the new block makes unnecessary); draw it with ShowCreation
    and dim the row."""
    label = card.rows[i][1]
    return Line(label.get_left() + 0.08 * LEFT, label.get_right() + 0.08 * RIGHT).set_stroke(color, 4)


def get_answer_card(expected_value_by_label_map: dict | str, title: str, width: float = 3.8,
                    font_size: float = SMALL_FONT_SIZE + 2) -> VGroup:
    """A card set out before a run: what the answer should be, one row per expectation labelled by where it comes from
    or by side. Parts: .title, .rows[i] = VGroup(label, value, slot). Mark a row after the run with get_answer_mark."""
    if isinstance(expected_value_by_label_map, str):
        expected_value_by_label_map = {choose_local_text("應該是", "expected"): expected_value_by_label_map}
    title_mobject = Text(title, font_size=font_size + 2).set_color(GREY_B)
    rows = VGroup()
    for label, value in expected_value_by_label_map.items():
        slot = Square(0.42).set_stroke(GREY_C, 1.5).set_fill(BLACK, 0)
        rows.add(VGroup(Text(str(label), font_size=font_size).set_color(GREY_B),
                        Text(str(value), font_size=font_size + 4).set_color(WHITE), slot))
    label_width = max(row[0].get_width() for row in rows)
    for row in rows:
        row[1].set_max_width(width - label_width - 1.0)
        row.arrange(RIGHT, buff=0.3)
        row[0].shift((label_width - row[0].get_width()) / 2 * LEFT)
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
    body = VGroup(title_mobject, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
    box = SurroundingRectangle(body, buff=0.3).set_stroke(GREY_B, 1.5).set_fill(BLACK, 0.6).round_corners(0.12)
    card = Parts(box, body)
    card.box, card.title, card.rows = box, title_mobject, rows
    return card


def get_answer_mark(card: VGroup, i: int, is_correct: bool = True) -> VMobject:
    """A tick (green) or a cross (red) in row i's slot of a get_answer_card; add it with ShowCreation."""
    slot = card.rows[i][2]
    if is_correct:
        mark = VMobject().set_points_as_corners([[-0.35, 0.0, 0], [-0.08, -0.3, 0], [0.42, 0.38, 0]])
        mark.set_stroke(GREEN, 5)
    else:
        mark = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(RED, 5)
    return mark.set_width(0.7 * slot.get_width()).move_to(slot)


def get_scoreboard(columns: list[str], width: float = 4.4, font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """A board kept in a corner, one row per run (version, score, a bit of output). Starts with its header; add a
    row with self.play(*add_scoreboard_row(board, [...])). Parts: .header, .rows."""
    column_width = width / len(columns)
    header = VGroup(*[Text(str(column_name), font_size=font_size).set_color(GREY_B) for column_name in columns])
    for j, cell in enumerate(header):
        cell.set_max_width(column_width - 0.15).move_to((j + 0.5) * column_width * RIGHT)
    rule = Line(ORIGIN, width * RIGHT).set_stroke(GREY_C, 1.5).next_to(header, DOWN, buff=0.12)
    rule.set_x(width / 2)
    board = Parts(header, rule)
    board.header, board.rule, board.rows = header, rule, VGroup()
    board.column_width, board.font_size = column_width, font_size
    return board


def add_scoreboard_row(board: VGroup, values: list, should_highlight: bool = False) -> list[Animation]:
    """Animations that add one row under the last row of a get_scoreboard; should_highlight paints it yellow."""
    cells = VGroup(*[Text(str(value), font_size=board.font_size) for value in values])
    for j, cell in enumerate(cells):
        cell.set_max_width(board.column_width - 0.15).move_to(board.header[j].get_center())
        if should_highlight:
            cell.set_color(YELLOW)
    last_row = board.rows[-1] if len(board.rows) else board.rule
    cells.set_y(last_row.get_bottom()[1] - 0.12 - cells.get_height() / 2)
    board.rows.add(cells)
    board.add(cells)
    return [FadeIn(cells, shift=0.15 * DOWN)]


def get_knob(name: str, value: float, unit: str = "", min_value: float = 0.0, max_value: float = 1.0,
             decimal_place_count: int = 1, width: float = 3.2, color=YELLOW,
             font_size: float = SMALL_FONT_SIZE + 2) -> VGroup:
    """A named number with a unit, on screen and named before it turns: a track with a handle and the value that
    follows it. Turn it with self.play(animate_knob_to(knob, value)). Parts: .name, .track, .handle, .value, .unit,
    .tracker."""
    tracker = ValueTracker(value)
    name_mobject = Text(name, font_size=font_size).set_color(GREY_B)
    track = Line(ORIGIN, width * RIGHT).set_stroke(GREY_C, 3).next_to(name_mobject, DOWN, buff=0.3, aligned_edge=LEFT)
    handle = Circle(radius=0.12).set_fill(color, 1).set_stroke(WHITE, 1.5)
    number = DecimalNumber(value, num_decimal_places=decimal_place_count, font_size=font_size + 6).set_color(color)
    unit_mobject = Text(unit, font_size=font_size).set_color(color) if unit else VGroup()

    def convert_value_to_x(value):
        fraction = (value - min_value) / (max_value - min_value) if max_value != min_value else 0.0
        return track.get_start()[0] + np.clip(fraction, 0, 1) * width

    handle.add_updater(lambda mobject: mobject.move_to([convert_value_to_x(tracker.get_value()), track.get_y(), 0]))
    number.add_updater(lambda mobject: mobject.set_value(tracker.get_value()))
    number.add_updater(lambda mobject: mobject.next_to(name_mobject, RIGHT, buff=0.3))
    if unit:
        unit_mobject.add_updater(lambda mobject: mobject.next_to(number, RIGHT, buff=0.1, aligned_edge=DOWN))
    knob = Parts(name_mobject, track, handle, number, unit_mobject)
    knob.update()
    knob.name, knob.track, knob.handle, knob.value = name_mobject, track, handle, number
    knob.unit, knob.tracker = unit_mobject, tracker
    return knob


def animate_knob_to(knob: VGroup, value: float, **kwargs) -> Animation:
    """The animation that turns a get_knob to value; run_time and other animation arguments pass through."""
    animation = knob.tracker.animate.set_value(value)
    return animation.set_anim_args(**kwargs) if kwargs else animation


def get_goal_card(name: str, goal: str = "", fear: str = "", leverage: str = "", color=BLUE_C, width: float = 3.4,
                  font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """One party's goal card: the name, then what they want, fear and have in hand. Parts: .name, .rows, .box."""
    name_mobject = Text(name, font_size=font_size + 2).set_color(color)
    rows = VGroup()
    labels = (choose_local_text("要", "wants"), choose_local_text("怕", "fears"), choose_local_text("手上", "has"))
    for label, text in zip(labels, (goal, fear, leverage)):
        if text:
            value_text = Text(text, font_size=font_size).set_color(WHITE).set_max_width(width - 0.9)
            rows.add(VGroup(Text(label, font_size=font_size - 2).set_color(GREY_B), value_text)
                     .arrange(RIGHT, buff=0.15, aligned_edge=UP))
    label_width = max([row[0].get_width() for row in rows] + [0])
    for row in rows:
        row[1].shift((label_width - row[0].get_width()) * RIGHT)
    body = VGroup(name_mobject, rows.arrange(DOWN, aligned_edge=LEFT, buff=0.12))
    body.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    box = SurroundingRectangle(body, buff=0.2).set_stroke(color, 2).set_fill(BLACK, 0.7).round_corners(0.1)
    card = Parts(box, body)
    card.name, card.rows, card.box = name_mobject, rows, box
    return card


def get_explanation_card(title: str, claim: str, color=BLUE_C, width: float = 3.6,
                         font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """One side of a dispute about an event: whose explanation and what it says, with room below for evidence (add
    with pin_evidence). Parts: .title, .claim, .box, .pins."""
    title_mobject = Text(title, font_size=font_size + 2).set_color(color)
    claim_mobject = Text(claim, font_size=font_size).set_color(WHITE).set_max_width(width - 0.4)
    head = VGroup(title_mobject, claim_mobject).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    box = SurroundingRectangle(head, buff=0.22).set_stroke(color, 2).set_fill(BLACK, 0.7).round_corners(0.1)
    box.stretch_to_fit_width(width, about_edge=LEFT)
    card = Parts(box, head)
    card.title, card.claim, card.box, card.pins = title_mobject, claim_mobject, box, VGroup()
    card.color, card.font_size = color, font_size
    return card


def pin_evidence(card: VGroup, text: str, was_written_at_the_time: bool = True) -> list[Animation]:
    """Animations that pin one piece of evidence under a get_explanation_card: a solid chip for what was written at
    the time, a dashed one for what was said afterwards. Keep two to four pins a card."""
    label = Text(text, font_size=card.font_size - 2).set_color(GREY_A).set_max_width(card.box.get_width() - 0.5)
    chip = SurroundingRectangle(label, buff=0.08).set_stroke(card.color, 1.5)
    if not was_written_at_the_time:
        chip = DashedVMobject(chip, num_dashes=30).set_stroke(card.color, 1.5)
    pin = VGroup(chip, label)
    pin.next_to(card.pins[-1] if len(card.pins) else card.claim, DOWN, buff=0.15, aligned_edge=LEFT)
    card.pins.add(pin)
    card.add(pin)
    new_box = SurroundingRectangle(VGroup(card.title, card.claim, card.pins), buff=0.22).set_stroke(card.color, 2)
    new_box.set_fill(BLACK, 0.7).round_corners(0.1).stretch_to_fit_width(card.box.get_width(), about_edge=LEFT)
    new_box.align_to(card.box, LEFT)
    return [Transform(card.box, new_box), FadeIn(pin, shift=0.15 * DOWN)]


def get_outline_bar(part_names: list[str], width: float | None = None, height: float = 0.36, color=TEAL,
                    font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """A thin bar along the bottom naming the parts of the episode's answer, so the viewer sees how many parts there
    are, which one this is and what is left. Show it with animate_outline_to(bar, 0); move on at each seam with
    animate_outline_to(bar, i). Parts: .cells[i] = VGroup(box, label)."""
    width = width if width is not None else FRAME_WIDTH - 1.0
    cell_width = width / len(part_names)
    cells = VGroup()
    for name in part_names:
        box = Rectangle(width=cell_width, height=height).set_stroke(GREY_D, 1.5).set_fill(BLACK, 0)
        label = Text(str(name), font_size=font_size).set_color(GREY_C)
        if label.get_width() > cell_width - 0.2:
            label.set_width(cell_width - 0.2)
        cells.add(VGroup(box, label.move_to(box)))
    cells.arrange(RIGHT, buff=0)
    bar = Parts(cells).to_edge(DOWN, buff=0.12)
    bar.cells, bar.color = cells, color
    return bar


def animate_outline_to(bar: VGroup, i: int) -> list[Animation]:
    """Animations that make part i current: earlier parts done (muted), part i lit, later parts waiting."""
    animations = []
    for j, (box, label) in enumerate(bar.cells):
        if j < i:
            animations += [box.animate.set_fill(GREY_D, 0.55).set_stroke(GREY_D, 1.5), label.animate.set_color(GREY_B)]
        elif j == i:
            animations += [box.animate.set_fill(bar.color, 0.45).set_stroke(bar.color, 2),
                           label.animate.set_color(WHITE)]
        else:
            animations += [box.animate.set_fill(BLACK, 0).set_stroke(GREY_D, 1.5), label.animate.set_color(GREY_C)]
    return animations


def _wrap(text: str, width_characters: int) -> list[str]:
    """Wrap Latin text on spaces; CJK (no spaces) on characters."""
    if " " in text.strip():
        return textwrap.wrap(text, width=width_characters)
    return [text[i:i + width_characters] for i in range(0, len(text), width_characters)]


def get_passage(text: str, width: float = 10.0, font: str | None = None, font_size: float = BODY_FONT_SIZE - 12,
                color=GREY_A, line_spacing: float = 0.28, source: str = "", was_written_at_the_time: bool | None = None
                ) -> VGroup:
    """A block of text treated as an object (close reading, a statute, a primary source): wrapped to `width`,
    left-aligned, with an optional small source line. was_written_at_the_time=True frames it solid ("written at the
    time"), False dashed ("said afterwards"). Parts: .lines[i]; mark a phrase with highlight_phrase. Works for CJK,
    Latin, right-to-left and Indic scripts (look at the rendered frame for missing glyphs)."""
    font = font or FONT
    sample = text[:120]
    probe = Text(sample.replace(" ", " "), font=font, font_size=font_size)
    line_width_characters = max(4, int(0.95 * width / (probe.get_width() / max(len(sample), 1))))
    wrapped_lines = _wrap(text, line_width_characters)
    lines = VGroup(*(Text(line, font=font, font_size=font_size).set_color(color) for line in wrapped_lines))
    lines.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)
    group = Parts(lines)
    if source:
        source_mobject = Text(source, font_size=SMALL_FONT_SIZE - 4).set_color(GREY_C)
        group.add(source_mobject.next_to(lines, DOWN, 0.3, aligned_edge=RIGHT))
    group.center()
    if was_written_at_the_time is not None:
        border = SurroundingRectangle(group, buff=0.25).set_stroke(GREY_B, 1.5)
        if not was_written_at_the_time:
            border = DashedVMobject(border, num_dashes=60).set_stroke(GREY_B, 1.5)
        tag_text = choose_local_text("當時寫的", "written at the time") if was_written_at_the_time else choose_local_text(
            "事後說的", "said afterwards")
        tag = Text(tag_text, font_size=SMALL_FONT_SIZE - 2).set_color(GREY_B)
        tag.next_to(border, UP, buff=0.08, aligned_edge=LEFT)
        group.add(border, tag)
        group.border, group.kind_tag = border, tag
    group.lines, group.line_texts, group.line_separator = lines, wrapped_lines, (" " if " " in text.strip() else "")
    return group


def highlight_phrase(passage: VGroup, phrase: str, color=YELLOW, style: str = "box") -> VMobject | None:
    """Mark a phrase inside a get_passage: style "box", "underline" or "fill" (recolour the glyphs). A phrase that
    wraps onto the next line gets one marker per line. Returns the marker(s), or None for "fill"."""
    joined_text, line_starts = "", []
    for i, line_text in enumerate(passage.line_texts):
        if i:
            joined_text += passage.line_separator
        line_starts.append(len(joined_text))
        joined_text += line_text
    phrase_start = joined_text.find(phrase)
    if phrase_start < 0:
        raise ValueError(f"phrase not found in the passage: {phrase!r}")
    phrase_end = phrase_start + len(phrase)
    pieces = []
    for line, line_text, start in zip(passage.lines, passage.line_texts, line_starts):
        overlap_start, overlap_end = max(phrase_start, start), min(phrase_end, start + len(line_text))
        piece = line_text[overlap_start - start:overlap_end - start].strip() if overlap_end > overlap_start else ""
        if piece:
            pieces.append(line[piece])
    if style == "fill":
        for piece in pieces:
            piece.set_color(color)
        return None
    if style == "underline":
        marks = [Underline(piece, buff=0.05).set_stroke(color, 3) for piece in pieces]
    else:
        marks = [SurroundingRectangle(piece, buff=0.06).set_stroke(color, 2) for piece in pieces]
    return marks[0] if len(marks) == 1 else VGroup(*marks)
