"""Credits for the external material an episode shows, read from production/credits.yaml, and the end credits page.

The asset commands record every download there. Credits for files under production/shared/ and this episode's
folder are listed; another episode's assets are left out.

The end credits page is what render holds for the last seconds of every episode when plan.yaml's has_end_credits is
on (the default): what the episode is based on, the external material it shows, and at the bottom "Made with" over
the Heptabase app icon and name. end_credits.py in the episode folder holds one EndCreditsScene subclass that says
what to list and draws it in the series' type; without end_credits.py, render uses EndCreditsScene as it is:

    class EndCredits(EndCreditsScene):
        source_lines = ["Carl B. Boyer, A History of Mathematics (1968), chapters 19 and 20"]
        asset_name_by_file_path_map = {"shared/assets/portraits/Isaac_Newton.jpg": "Isaac Newton"}

get_credits_pages() builds credits pages for a scene of the episode itself; the end credits page replaces it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from manimlib import (
    DOWN,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREY_A,
    GREY_B,
    GREY_C,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    WHITE,
    InteractiveScene,
    Mobject,
    StringMobject,
    SVGMobject,
    Text,
    VGroup,
)

from ..file_io import load_yaml_model
from ..schemas.credits import Credit, Credits
from .context import get_scene_context
from .style import LABEL_FONT_SIZE, SMALL_FONT_SIZE, choose_local_text

__all__ = ["EndCreditsEntry", "EndCreditsScene", "get_credits_pages", "get_end_credits_page", "get_heptabase_icon",
           "group_end_credits_entries", "load_episode_credits", "resolve_end_credits_entries"]

# The Heptabase app icon, as in docs/images/logo-light.svg: a white rounded square with the dark H.
HEPTABASE_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" rx="17.8641" fill="#fff"/>'
    '<circle cx="58.8348" cy="56.505" r="4.85437" fill="#2e2e2e"/><path fill="#2e2e2e" fill-rule="evenodd" d="'
    "m20.9707 23.0906c0-2.4576 1.9923-4.4499 4.4498-4.4499 2.4576 0 4.4499 1.9923 4.4499 4.4499v26.699c0 2.4576-1.9923 "
    "4.4499-4.4499 4.4499-2.4575 0-4.4498-1.9923-4.4498-4.4499zm19.5793 7.12c0-2.4575 1.9923-4.4498 4.4498-4.4498 "
    "2.4576 0 4.4499 1.9923 4.4499 4.4498v26.6991c0 2.4576-1.9923 4.4498-4.4499 4.4498-2.4575 0-4.4498-1.9923-4.4498-"
    "4.4498v-10.2347c0-1.3431-.8197-2.5501-2.068-3.0455l-.3721-.1477c-2.0263-.8041-4.2902-.7638-6.2867.1118-1.1865."
    "5204-1.9528 1.6933-1.9528 2.9889v-13.1644c0 1.2956.7663 2.4685 1.9528 2.9888 1.9965.8757 4.2604.9159 6.2867.1118l"
    '.3721-.1476c1.2484-.4954 2.068-1.7025 2.068-3.0456z"/></svg>'
)
END_CREDITS_HEADING_FONT_SIZE = 30
END_CREDITS_BODY_FONT_SIZE = 22
END_CREDITS_CLOSING_FONT_SIZE = 20
END_CREDITS_CAPTION_FONT_SIZE = 18
END_CREDITS_ICON_HEIGHT = 0.34
END_CREDITS_ROW_SPACING = 0.44  # from the top of one row to the top of the next
END_CREDITS_NAME_COLOR = GREY_A
END_CREDITS_DETAIL_COLOR = GREY_C


def _load_credits() -> list[Credit]:
    context = get_scene_context()
    if context.series is None or not context.series.credits_file_path.exists():
        return []
    return load_yaml_model(Credits, context.series.credits_file_path, "credits.yaml").credits


def load_episode_credits() -> list[Credit]:
    """The credits.yaml entries for files this episode can use, in file order."""
    episode_folder_prefix = f"episodes/{get_scene_context().episode_id}/"
    return [credit for credit in _load_credits()
            if not credit.asset_file_path.startswith("episodes/")
            or credit.asset_file_path.startswith(episode_folder_prefix)]


def _get_credit_entry(credit: Credit, width: float) -> VGroup:
    title = Text(credit.title, font_size=SMALL_FONT_SIZE + 2).set_color(WHITE)
    detail = " · ".join(part for part in (credit.author, credit.license) if part)
    lines = VGroup(title, Text(detail, font_size=SMALL_FONT_SIZE - 2).set_color(GREY_B)) if detail else VGroup(title)
    for line in lines:
        line.set_max_width(width)
    return lines.arrange(DOWN, aligned_edge=LEFT, buff=0.08)


def get_credits_pages(title: str | None = None, entry_count_per_page: int = 6, width: float = 11.0,
                      extra_lines: list[str] = ()) -> list[VGroup]:
    """The credits as pages of at most `entry_count_per_page` entries (each a title over its author and licence),
    headed by `title` (default: "Credits" in the episode's language). `extra_lines` adds plain lines at the end, such
    as a credit for the series' sources. Returns [] when there is nothing to credit."""
    entries = [_get_credit_entry(credit, width) for credit in load_episode_credits()]
    entries += [Text(line, font_size=SMALL_FONT_SIZE).set_color(GREY_A).set_max_width(width) for line in extra_lines]
    heading = title or choose_local_text("素材出處", "Credits")
    pages = []
    for start in range(0, len(entries), entry_count_per_page):
        body = VGroup(*entries[start:start + entry_count_per_page]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        page = VGroup(Text(heading, font_size=LABEL_FONT_SIZE).set_color(GREY_A), body).arrange(DOWN, buff=0.5)
        page.set_max_height(7.0).to_edge(UP, buff=0.6)
        pages.append(page)
    return pages


# The end credits page ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EndCreditsEntry:
    name: str  # what the asset shows
    detail: str  # its author and licence


def resolve_end_credits_entries(credits: list[Credit], asset_name_by_file_path_map: dict[str, str]) -> list[
        EndCreditsEntry]:
    """The asset rows of the end credits. With a map: the files it names, in its order, under its names (an empty
    name keeps the credits.yaml title); a file without a credits.yaml entry raises ValueError. Without one: every
    credit given, under its title."""
    credit_by_file_path_map = {credit.asset_file_path: credit for credit in credits}
    if asset_name_by_file_path_map:
        missing_file_paths = [path for path in asset_name_by_file_path_map if path not in credit_by_file_path_map]
        if missing_file_paths:
            raise ValueError(f"no credits.yaml entry for {', '.join(missing_file_paths)}: add one by hand, or leave "
                             "the file out of asset_name_by_file_path_map")
        chosen = [(credit_by_file_path_map[path], name) for path, name in asset_name_by_file_path_map.items()]
    else:
        chosen = [(credit, "") for credit in credits]
    return [EndCreditsEntry(name or credit.title, " · ".join(part for part in (credit.author, credit.license) if part))
            for credit, name in chosen]


def get_heptabase_icon(height: float) -> SVGMobject:
    """The Heptabase app icon as it is: a white rounded square with the dark H."""
    return SVGMobject(svg_string=HEPTABASE_ICON_SVG, height=height).set_stroke(width=0)


def _get_closing(get_text) -> VGroup:
    """A small "Made with" (in the episode's language) over the Heptabase app icon and its name. The label is quieter
    than the list; the name is in the series' type, its H half as tall as the icon and centred on it."""
    caption = get_text(choose_local_text("製作工具", "Made with"), END_CREDITS_CAPTION_FONT_SIZE, [])
    icon = get_heptabase_icon(END_CREDITS_ICON_HEIGHT)
    name = get_text("Heptabase", END_CREDITS_BODY_FONT_SIZE, ["H"]).set_color(END_CREDITS_NAME_COLOR)
    name.scale(0.47 * icon.get_height() / name["H"].get_height())
    name.next_to(icon, RIGHT, buff=0.3 * icon.get_height())
    name.shift(UP * (icon.get_center()[1] - name["H"].get_center()[1]))
    return VGroup(caption.set_color(END_CREDITS_DETAIL_COLOR), VGroup(icon, name)).arrange(DOWN, buff=0.18)


def _get_asset_rows(entries: list[EndCreditsEntry], get_text) -> VGroup:
    """One row per asset: its name, then its author and licence in a second column. Each row is one piece of text, so
    both columns share its baseline."""
    rows = VGroup()
    for entry in entries:
        row = get_text(f"{entry.name}  {entry.detail}" if entry.detail else entry.name, END_CREDITS_BODY_FONT_SIZE,
                       [entry.name, entry.detail] if entry.detail else [entry.name])
        row.set_color(END_CREDITS_NAME_COLOR)
        row.name_part = row[entry.name]
        row.detail_part = row[entry.detail].set_color(END_CREDITS_DETAIL_COLOR) if entry.detail else VGroup()
        rows.add(row)
    if not rows:
        return rows
    detail_left_x = max(row.name_part.get_width() for row in rows) + 0.5
    for i, row in enumerate(rows):
        row.shift(LEFT * row.name_part.get_left()[0] + DOWN * (row.get_top()[1] + i * END_CREDITS_ROW_SPACING))
        if len(row.detail_part):
            row.detail_part.shift(RIGHT * (detail_left_x - row.detail_part.get_left()[0]))
    return rows


def group_end_credits_entries(entries: list[EndCreditsEntry], row_count: int) -> list[EndCreditsEntry]:
    """At most row_count rows. When there are more entries, the ones with the same author and licence share a row,
    named after the first ("Portrait of Euler and 11 more"); groups that still do not fit end in one "N more" row."""
    if len(entries) <= row_count:
        return entries
    names_by_detail_map: dict[str, list[str]] = {}
    for entry in entries:
        names_by_detail_map.setdefault(entry.detail, []).append(entry.name)
    grouped = [EndCreditsEntry(names[0] if len(names) == 1 else
                               choose_local_text(f"{names[0]} 等 {len(names)} 項", f"{names[0]} and {len(names) - 1} more"),
                               detail)
               for detail, names in names_by_detail_map.items()]
    if len(grouped) <= row_count:
        return grouped
    kept = grouped[:max(row_count - 1, 0)]
    left_count = len(entries) - sum(len(names_by_detail_map[entry.detail]) for entry in kept)
    return kept + [EndCreditsEntry(choose_local_text(f"另外 {left_count} 項素材", f"{left_count} more assets"), "")]


def get_end_credits_page(source_lines: list[str], entries: list[EndCreditsEntry], get_text=None) -> VGroup:
    """The end credits page: a heading, the source lines, the asset rows, and at the bottom "Made with" over the
    Heptabase app icon and name. get_text(text, font_size, isolate) draws text in the series' type (default: Text, the video
    font) and must return a StringMobject whose parts named in `isolate` can be picked out by indexing it with them.
    With nothing to list, the page is that closing alone."""
    get_text = get_text or (lambda text, font_size, isolate: Text(text, font_size=font_size, isolate=isolate))
    closing = _get_closing(get_text)
    sources = VGroup(*(get_text(line, END_CREDITS_BODY_FONT_SIZE, [line]).set_color(END_CREDITS_NAME_COLOR)
                       for line in source_lines)).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    heading = get_text(choose_local_text("素材出處", "Credits"), END_CREDITS_HEADING_FONT_SIZE, [])
    heading.set_color(GREY_A)
    closing.to_edge(DOWN, buff=0.85).set_x(0)
    # the heading and the list sit in the middle of the space above the closing; rows that do not fit at full size
    # are grouped by author and licence rather than shrunk until nobody can read them
    top_y, bottom_y = FRAME_HEIGHT / 2 - 0.9, closing.get_top()[1] + 0.6
    body_height = top_y - bottom_y - heading.get_height() - 0.75
    rows_height = body_height - (sources.get_height() + 0.55 if len(sources) else 0)
    entries = group_end_credits_entries(entries, max(int(rows_height // END_CREDITS_ROW_SPACING), 1))
    rows = _get_asset_rows(entries, get_text)
    body = VGroup(*(group for group in (sources, rows) if len(group)))
    if not len(body):
        return VGroup(closing.move_to(ORIGIN))
    body.arrange(DOWN, aligned_edge=LEFT, buff=0.55)
    body.set_max_width(FRAME_WIDTH - 2.0)
    body.set_max_height(body_height)
    body.next_to(heading, DOWN, buff=0.75).set_x(0)
    heading.set_x(0)
    VGroup(heading, body).set_y((top_y + bottom_y) / 2)
    return VGroup(heading, body, closing)


class EndCreditsScene(InteractiveScene):
    """Subclass it in end_credits.py. Set `source_lines` (what the episode is based on: a book with its authors and
    chapters, a paper, a talk) and `asset_name_by_file_path_map` (the credits.yaml files the episode shows, each with
    the name the page gives it; empty: every asset this episode can use, under its credits.yaml title). Override
    get_text() when the series sets its text in another type than the video font."""

    source_lines: ClassVar[list[str]] = []
    asset_name_by_file_path_map: ClassVar[dict[str, str]] = {}

    def get_text(self, text: str, font_size: float, isolate: list[str]) -> StringMobject:
        """Text in the series' type, as a StringMobject whose `isolate` parts can be picked out by indexing it."""
        return Text(text, font_size=font_size, isolate=isolate)

    def get_page(self) -> Mobject:
        credits = _load_credits() if self.asset_name_by_file_path_map else load_episode_credits()
        entries = resolve_end_credits_entries(credits, self.asset_name_by_file_path_map)
        return get_end_credits_page(self.source_lines, entries, self.get_text)

    def construct(self):
        self.add(self.get_page())
