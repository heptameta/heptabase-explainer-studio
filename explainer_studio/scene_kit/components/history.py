"""History and series devices: portraits, primary documents and quotations, lists and ledgers that return across
episodes, the series map, a questioner character, title cards, a parts strip, and the seat chart (who is at the
table, the big-picture board when there is no map)."""

from __future__ import annotations

import math

from manimlib import *

from ..context import get_scene_context
from ..layout_checks import mark_decorative
from ..parts import KeyedGroup, Parts
from ..style import BODY_FONT_SIZE, LABEL_FONT_SIZE, SMALL_FONT_SIZE, TITLE_FONT_SIZE, YEAR_COLOR, choose_local_text

__all__ = [
    "change_seat_claim",
    "get_document",
    "get_episode_title_card",
    "get_ledger",
    "get_parts_strip",
    "get_portrait_card",
    "get_portrait_placeholder",
    "get_quote_pair",
    "get_running_list",
    "get_seat_chart",
    "get_seat_link",
    "get_series_map",
    "play_questioner_entrance",
    "play_questioner_exit",
    "play_questioner_question",
    "swap_seat",
]


def get_portrait_placeholder(height: float = 2.4, color=GREY_B) -> VGroup:
    """A grey silhouette standing in for a portrait that is not available."""
    border_rectangle = Rectangle(width=0.78 * height, height=height).set_fill(GREY_E, 1).set_stroke(color, 1.5)
    head = Circle(radius=0.17 * height).set_fill(GREY_D, 1).set_stroke(width=0)
    head.move_to(border_rectangle.get_center() + 0.12 * height * UP)
    shoulders = Arc(0, PI, radius=0.3 * height).set_fill(GREY_D, 1).set_stroke(width=0)
    shoulders.close_path() if hasattr(shoulders, "close_path") else None
    shoulders.move_to(border_rectangle.get_bottom() + 0.16 * height * UP)
    return VGroup(border_rectangle, head, shoulders)


def get_portrait_card(name: str, original_name: str, years: str, school_color=GREY_B,
                      image_file_path: str | None = None, height: float = 2.4) -> Group:
    """A portrait card: the portrait (a path relative to production/, e.g. from `asset wikipedia download-portrait`)
    with a thin border in the person's school or stance colour, the name in the video's language and the original,
    and the life dates. Without an image, a grey silhouette stands in; one person keeps one portrait for the whole
    series."""
    if image_file_path is not None:
        picture = ImageMobject(str(get_scene_context().resolve_path(image_file_path))).set_height(height)
        # border made of 4 lines (no fill region), so dimming the card never tints the portrait
        top_left, top_right, bottom_right, bottom_left = (picture.get_corner(corner) for corner in (UL, UR, DR, DL))
        corner_pairs = [(top_left, top_right), (top_right, bottom_right), (bottom_right, bottom_left),
                        (bottom_left, top_left)]
        border = VGroup(*(Line(start, end) for start, end in corner_pairs)).set_stroke(school_color, 2)
        portrait = Group(picture, border)
    else:
        portrait = get_portrait_placeholder(height, school_color)
        portrait[0].set_stroke(school_color, 2)
    name_text = Text(name, font_size=LABEL_FONT_SIZE).set_color(school_color)
    original_name_text = Text(original_name, font_size=SMALL_FONT_SIZE).set_color(GREY_A)
    years_text = Text(years, font_size=SMALL_FONT_SIZE).set_color(YEAR_COLOR)
    caption = VGroup(name_text, original_name_text, years_text).arrange(DOWN, buff=0.08)
    caption.next_to(portrait, DOWN, 0.15)
    return Group(portrait, caption)


def get_document(title: str, subtitle: str = "", year: str = "", width: float = 3.2, line_count: int = 10,
                 paper_color="#E9E3D2", ink_color="#3A342A", seed: int = 0) -> VGroup:
    """A stand-in for the first page of a primary text (text as an object): a prop, its small print exempt from the
    automatic checks."""
    random_generator = np.random.default_rng(seed)
    height = width * 1.35
    page = Rectangle(width=width, height=height).set_fill(paper_color, 1).set_stroke(GREY_B, 1)
    title_text = Text(title, font_size=22).set_color(ink_color)
    title_text.set_max_width(width * 0.85).move_to(page.get_top() + 0.35 * DOWN)
    document = VGroup(page, title_text)
    y = title_text.get_bottom()[1] - 0.2
    if subtitle:
        subtitle_text = Text(subtitle, font_size=14, slant=ITALIC).set_color(ink_color)
        subtitle_text.set_max_width(width * 0.8).move_to([page.get_x(), y - 0.1, 0])
        document.add(subtitle_text)
        y = subtitle_text.get_bottom()[1] - 0.15
    if year:
        year_text = Text(year, font_size=14).set_color(ink_color).move_to([page.get_x(), y - 0.1, 0])
        document.add(year_text)
        y = year_text.get_bottom()[1] - 0.25
    lines = VGroup()
    left = page.get_left()[0] + 0.25
    step = min(0.2, (y - 0.2 - page.get_bottom()[1]) / max(line_count, 1))
    for i in range(line_count):
        length = (width - 0.5) * (0.55 if i == line_count - 1 else random_generator.uniform(0.85, 1.0))
        line = Line([left, y - step * i, 0], [left + length, y - step * i, 0]).set_stroke(ink_color, 1.5, opacity=0.55)
        lines.add(line)
    document.add(lines)
    document.lines = lines
    return mark_decorative(document)


def get_quote_pair(original: str, translation: str, source: str = "", width: float = 11.0,
                   color_by_word_map: dict | None = None) -> VGroup:
    """A quotation in two languages: the original small and grey above, the translation large below, a small
    source line."""
    original_text = Text(original, font_size=24, slant=ITALIC).set_color(GREY_B)
    original_text.set_max_width(width)
    translation_text = Text(translation, font_size=BODY_FONT_SIZE - 4, t2c=color_by_word_map or {})
    translation_text.set_max_width(width)
    group = VGroup(original_text, translation_text).arrange(DOWN, buff=0.35)
    if source:
        source_text = Text(source, font_size=18).set_color(GREY_C)
        source_text.next_to(translation_text, DOWN, 0.3, aligned_edge=RIGHT)
        group.add(source_text)
    return group


def get_running_list(title: str, entries: list[tuple[str, str]], row_count: int, active_index: int | None = None,
                     placeholder: str = "……", width: float = 5.2) -> VGroup:
    """A list that accumulates across episodes (a question and its answer per row). Unfilled rows are dim
    placeholders."""
    title_mobject = Text(title, font_size=LABEL_FONT_SIZE + 4).set_color(WHITE)
    rows = VGroup()
    for i in range(row_count):
        if i < len(entries):
            question, answer = entries[i]
            question_text = Text(question, font_size=SMALL_FONT_SIZE + 4).set_color(WHITE)
            answer_text = Text(answer, font_size=SMALL_FONT_SIZE).set_color(GREY_A)
            answer_text.set_max_width(width)
            row = VGroup(question_text, answer_text).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            if active_index is not None and i != active_index:
                row.set_opacity(0.45)
            if active_index == i:
                question_text.set_color(YELLOW)
        else:
            row = VGroup(Text(placeholder, font_size=SMALL_FONT_SIZE + 4).set_color(GREY_D))
        rows.add(row)
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    group = VGroup(title_mobject, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    group.title, group.rows = title_mobject, rows
    return group

def get_ledger(row_labels: list[str], column_labels: list[str],
               text_by_cell_map: dict[tuple[int, int], str] | None = None, active_row_index: int | None = None,
               column_width: float = 3.4, row_height: float = 0.9, first_column_width: float = 1.6) -> VGroup:
    """A ledger table that returns across episodes. text_by_cell_map[(row_index, column_index)] = text
    (column_index counts column_labels from 0)."""
    text_by_cell_map = text_by_cell_map or {}
    table = VGroup()
    header = VGroup()
    column_widths = [first_column_width] + [column_width] * len(column_labels)
    column_xs = np.cumsum([0] + column_widths)
    for column_index, name in enumerate([""] + column_labels):
        header_text = Text(name, font_size=SMALL_FONT_SIZE + 2).set_color(GREY_A)
        header_text.move_to([(column_xs[column_index] + column_xs[column_index + 1]) / 2, 0, 0])
        header.add(header_text)
    table.add(header)
    body = VGroup()
    for row_index, name in enumerate(row_labels):
        y = -(row_index + 1) * row_height
        row = VGroup()
        label = Text(name, font_size=SMALL_FONT_SIZE + 4).move_to([(column_xs[0] + column_xs[1]) / 2, y, 0])
        row.add(label)
        for column_index in range(len(column_labels)):
            cell_text = text_by_cell_map.get((row_index, column_index), "")
            if cell_text:
                cell_mobject = Text(cell_text, font_size=SMALL_FONT_SIZE - 2).set_color(GREY_A)
                cell_mobject.set_max_width(column_widths[column_index + 1] - 0.3)
                cell_mobject.move_to([(column_xs[column_index + 1] + column_xs[column_index + 2]) / 2, y, 0])
                row.add(cell_mobject)
        if active_row_index is not None and row_index != active_row_index:
            row.set_opacity(0.35)
        body.add(row)
    table.add(body)
    lines = VGroup()
    total_width = column_xs[-1]
    for row_index in range(len(row_labels) + 1):
        y = -(row_index + 0.5) * row_height
        lines.add(Line([0, y, 0], [total_width, y, 0]).set_stroke(GREY_D, 1))
    for column_index in range(1, len(column_widths)):
        column_x = column_xs[column_index]
        lines.add(Line([column_x, -0.5 * row_height + 0.4, 0], [column_x, -(len(row_labels) + 0.5) * row_height, 0])
                  .set_stroke(GREY_D, 1))
    table.add(lines)
    table.header, table.body, table.grid = header, body, lines
    table.center()
    return table


def get_series_map(titles: list[str], current_index: int, width: float = 10, labels: list[str] | None = None) -> VGroup:
    """A row of episode thumbnails with the current one boxed ("you are here").
    titles: caption under each cell; labels: text inside each cell (default "1", "2", ...); current_index is 0-based."""
    labels = labels or [str(i + 1) for i in range(len(titles))]
    episode_count = len(titles)
    cards = VGroup()
    for label_text, caption_text in zip(labels, titles):
        box = Rectangle(width=width / episode_count - 0.15, height=0.8).set_stroke(GREY_C, 1).set_fill(BLACK, 0.6)
        if label_text.isdigit():
            label_mobject = Text(label_text, font_size=LABEL_FONT_SIZE).move_to(box)
        else:
            label_mobject = Text(label_text, font_size=LABEL_FONT_SIZE - 6).move_to(box)
        label_mobject.set_color(GREY_B)
        caption_mobject = Text(caption_text, font_size=SMALL_FONT_SIZE - 4).set_color(GREY_B).next_to(box, DOWN, 0.08)
        caption_mobject.set_max_width(box.get_width())
        cards.add(VGroup(box, label_mobject, caption_mobject))
    cards.arrange(RIGHT, buff=0.15)
    current_card = cards[current_index]
    current_card[0].set_stroke(YELLOW, 2.5)
    current_card[1].set_color(WHITE)
    current_card[2].set_color(WHITE)
    here = (Text(choose_local_text("你在這裡", "you are here"), font_size=SMALL_FONT_SIZE).set_color(YELLOW)
            .next_to(current_card, UP, 0.12))
    return VGroup(cards, here)


# ----------------------------------------------------------------------------
# Questioner character (optional). The character itself lives in the series' own code under production/shared/
# and must provide get_bubble(text) -> SpeechBubble and look_at(point_or_mob). Rules: it only asks and
# reacts, never explains; every 2–4 minutes, 5–15 seconds each, on the meta layer.
# ----------------------------------------------------------------------------
def play_questioner_entrance(scene, questioner, look_at_target=None, run_time: float = 0.8):
    """Bring the questioner in from below with a gentle float."""
    if look_at_target is not None:
        questioner.look_at(look_at_target)
    base_center = questioner.get_center().copy()
    questioner.float_seconds = 0.0

    def update_float(mobject, dt):
        mobject.float_seconds += dt
        mobject.move_to(base_center + 0.06 * np.sin(1.6 * mobject.float_seconds) * UP)

    if hasattr(scene, "play_sound"):
        scene.play_sound("questioner")
    scene.play(FadeIn(questioner, shift=0.6 * UP), run_time=run_time)
    questioner.add_updater(update_float)
    return questioner


def play_questioner_question(scene, questioner, text: str, run_time: float | None = None, font_size=LABEL_FONT_SIZE):
    """The questioner asks in a speech bubble. Returns the bubble (remove it with play_questioner_exit or FadeOut)."""
    questioner.suspend_updating()
    bubble = questioner.get_bubble(text, font_size=font_size)
    questioner.resume_updating()
    resolved_run_time = run_time or max(0.8, 0.08 * len(text))
    if hasattr(scene, "play_sound"):
        scene.play_sound("bubble")
    scene.play(FadeIn(bubble.body, scale=0.9), Write(bubble.content), run_time=resolved_run_time)
    return bubble


def play_questioner_exit(scene, questioner, *extra_mobjects, run_time: float = 0.7):
    questioner.clear_updaters()
    scene.play(FadeOut(questioner, shift=0.5 * DOWN), *(FadeOut(mobject) for mobject in extra_mobjects),
               run_time=run_time)


# ----------------------------------------------------------------------------
# Series framing: title card, parts strip, credits, cover. Code under production/shared/ can wrap these with the
# series' own text.
# ----------------------------------------------------------------------------
def get_episode_title_card(series_name: str, episode_label: str, title: str, subtitle: str = "",
                           series_map: Mobject | None = None) -> VGroup:
    """A title card: the series name, the episode label and title, an optional subtitle and series map."""
    series_text = Text(series_name, font_size=TITLE_FONT_SIZE)
    episode_text = Text(f"{episode_label} | {title}", font_size=LABEL_FONT_SIZE + 4).set_color(GREY_A)
    head = VGroup(series_text, episode_text)
    if subtitle:
        head.add(Text(subtitle, font_size=SMALL_FONT_SIZE).set_color(GREY_B))
    head.arrange(DOWN, buff=0.25)
    if series_map is None:
        return head
    return VGroup(head, series_map).arrange(DOWN, buff=1.0)


def get_parts_strip(titles: list[str], active_part_number: int, width: float = 9.0) -> VGroup:
    """Strip of the parts of a chapter/unit with the current one lit (active_part_number is 1-based)."""
    part_cards = VGroup()
    for i, title in enumerate(titles, start=1):
        box = RoundedRectangle(width=width / len(titles) - 0.2, height=0.7, corner_radius=0.1)
        is_active = i == active_part_number
        box.set_stroke(YELLOW if is_active else GREY_C, 2 if is_active else 1).set_fill(BLACK, 0.5)
        label_mobject = (Text(f"{i}. {title}", font_size=SMALL_FONT_SIZE + 2).move_to(box)
                         .set_color(WHITE if is_active else GREY_C))
        part_cards.add(VGroup(box, label_mobject))
    return part_cards.arrange(RIGHT, buff=0.2)



def _get_seat_face(label: str, color, radius: float, font_size: float) -> VGroup:
    disc = Circle(radius=radius).set_fill(color, 0.85).set_stroke(WHITE, 2)
    text = Text(label, font_size=font_size).set_color(WHITE)
    text.set_max_width(1.6 * radius)
    return VGroup(disc, text.move_to(disc))


def get_seat_chart(party_by_key_map: dict, title: str = "", width: float = 7.0, height: float = 3.6,
                   radius: float = 0.42, font_size: float = SMALL_FONT_SIZE, claim_width: float = 2.6) -> VGroup:
    """The parties of a court, a council, a faction fight or an industry seated round one table, each a badge with his
    name under it and his claim beside it, outward from the table. party_by_key_map: key -> {"name", "badge" (a few
    characters on the badge; defaults to the name's first two), "claim", "color"}; seats go clockwise from the top in
    order. The board stays all episode: someone else takes a seat with swap_seat, a claim changes with
    change_seat_claim, an alliance is drawn with get_seat_link. Parts: .table, .title, .seats[key] (VGroup(face, name,
    claim)), .link_by_seat_pair_map."""
    default_colors = [BLUE_C, RED_C, GOLD_C, TEAL, PURPLE_C, GREEN_C, MAROON_C, GREY_BROWN]
    table = Ellipse(width=width * 0.55, height=height * 0.5).set_fill(GREY_E, 0.6).set_stroke(GREY_C, 2)
    title_mobject = Text(title, font_size=font_size).set_color(GREY_B).move_to(table) if title else VGroup()
    seat_by_key_map = {}
    party_count = len(party_by_key_map)
    for index, (key, party) in enumerate(party_by_key_map.items()):
        angle = PI / 2 - TAU * index / party_count
        outward_direction = np.array([math.cos(angle), math.sin(angle), 0])
        center = np.array([width / 2 * outward_direction[0], height / 2 * outward_direction[1], 0])
        color = party.get("color", default_colors[index % len(default_colors)])
        badge_text = party.get("badge") or str(party.get("name", key))[:2]
        face = _get_seat_face(badge_text, color, radius, font_size).move_to(center)
        name_text = (Text(str(party.get("name", key)), font_size=font_size).set_color(color)
                     .next_to(face, DOWN, buff=0.08))
        claim_text = _get_seat_claim_text(party.get("claim", ""), font_size, claim_width)
        seat = VGroup(face, name_text, claim_text)
        seat.outward_direction, seat.claim_width = outward_direction, claim_width
        _place_claim(seat)
        seat_by_key_map[key] = seat
    chart = Parts(table, title_mobject, *seat_by_key_map.values())
    chart.table, chart.title, chart.seats = table, title_mobject, KeyedGroup(seat_by_key_map)
    chart.link_by_seat_pair_map = {}
    chart.font_size, chart.radius = font_size, radius
    return chart


def _get_seat_claim_text(claim: str, font_size: float, claim_width: float) -> VMobject:
    if not claim:
        return VGroup()
    text = Text(claim, font_size=font_size).set_color(GREY_A)
    return text.set_max_width(claim_width)


def _place_claim(seat: VGroup) -> None:
    face, name, claim = seat
    if not len(claim.get_points()) and not len(claim.submobjects):
        return
    outward_direction = seat.outward_direction
    if outward_direction[0] > 0.3:
        side = RIGHT
    elif outward_direction[0] < -0.3:
        side = LEFT
    else:
        side = UP if outward_direction[1] > 0 else DOWN
    anchor = VGroup(face, name) if side is DOWN else face
    claim.next_to(anchor, side, buff=0.2)


def swap_seat(chart: VGroup, key, name: str, claim: str = "", color=None, badge: str = "") -> list[Animation]:
    """Animations in which someone else takes seat key of a get_seat_chart (a new ruler, a new CEO): the old badge,
    name and claim fade out, the new ones fade in at the same place."""
    seat = chart.seats[key]
    face, old_name, old_claim = seat
    color = color or face[0].get_fill_color()
    new_face = _get_seat_face(badge or name[:2], color, chart.radius, chart.font_size).move_to(face)
    new_name = Text(name, font_size=chart.font_size).set_color(color).next_to(new_face, DOWN, buff=0.08)
    new_claim = _get_seat_claim_text(claim, chart.font_size, seat.claim_width)
    new_seat = VGroup(new_face, new_name, new_claim)
    new_seat.outward_direction, new_seat.claim_width = seat.outward_direction, seat.claim_width
    _place_claim(new_seat)
    animations = [FadeOut(face, scale=0.6), FadeOut(old_name), FadeOut(old_claim),
             FadeIn(new_face, scale=1.4), FadeIn(new_name), FadeIn(new_claim)]
    chart.remove(seat)
    chart.add(new_seat)
    chart.seats._part_by_key_map[key] = new_seat
    chart.seats.set_submobjects(list(chart.seats._part_by_key_map.values()))
    return animations


def change_seat_claim(chart: VGroup, key, claim: str) -> list[Animation]:
    """Animations that change what the party at seat key wants (the claim beside his badge)."""
    seat = chart.seats[key]
    new_claim = _get_seat_claim_text(claim, chart.font_size, seat.claim_width)
    placement_probe = VGroup(seat[0], seat[1], new_claim)
    placement_probe.outward_direction = seat.outward_direction
    _place_claim(placement_probe)
    old_claim = seat[2]
    seat.set_submobjects([seat[0], seat[1], new_claim])
    return [FadeOut(old_claim), FadeIn(new_claim)]


def get_seat_link(chart: VGroup, first_key, second_key, color=GREEN, is_dashed: bool = False,
                  label: str = "") -> VMobject:
    """A line between two seats of a get_seat_chart: an alliance (solid), or a deal not yet made or broken (dashed).
    Draw it with ShowCreation; remove it with Uncreate or FadeOut. It is kept in
    chart.link_by_seat_pair_map[(first_key, second_key)]."""
    first_face, second_face = chart.seats[first_key][0], chart.seats[second_key][0]
    start, end = first_face.get_center(), second_face.get_center()
    direction = (end - start) / (np.linalg.norm(end - start) or 1)
    start, end = start + direction * chart.radius * 1.1, end - direction * chart.radius * 1.1
    line = (DashedLine(start, end, dash_length=0.12) if is_dashed else Line(start, end)).set_stroke(color, 4)
    if label:
        tag = Text(label, font_size=chart.font_size - 2).set_color(color).next_to(line.get_center(), UP, buff=0.08)
        line = VGroup(line, tag)
    line.set_z_index(-1)
    chart.link_by_seat_pair_map[(first_key, second_key)] = line
    return line
