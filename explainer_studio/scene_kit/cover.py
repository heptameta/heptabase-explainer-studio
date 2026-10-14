"""The episode cover: the still held for the first second of the video (chat apps show the first frame as the
preview) and delivered next to the video as its thumbnail.

cover.py in the episode folder holds one CoverScene subclass:

    class Cover(CoverScene):
        def get_visual(self):
            return the episode's central picture (a mobject)

The layout puts the visual on the left and the series title, the episode label and a large title on the right,
legible at about 400 px wide. Titles come from plan.yaml unless the class overrides them.
"""

from __future__ import annotations

from manimlib import (
    DOWN,
    GREY_A,
    GREY_C,
    LEFT,
    WHITE,
    YELLOW,
    Group,
    InteractiveScene,
    Mobject,
    RoundedRectangle,
    Text,
    VGroup,
)

from ..paths import parse_episode_number
from ..plan import load_plan
from .components.emphasis import get_meta_background
from .context import get_scene_context
from .style import FONT

__all__ = ["CoverScene", "format_episode_label", "get_episode_cover"]


def format_episode_label(episode_id: str, language_code: str) -> str:
    number = parse_episode_number(episode_id)
    return f"第 {number} 集" if language_code.lower().startswith("zh") else f"Episode {number}"


def get_episode_cover(title: str, series_title: str, label: str, visual: Mobject | None = None) -> Group:
    """Dark-grey layer; a black panel with the visual on the left; series title, episode label and a large title on
    the right. Write '\\n' in the title for a manual line break (two short lines read best when shrunk)."""
    panel = RoundedRectangle(width=7.0, height=6.6, corner_radius=0.25).set_fill("#000000", 1).set_stroke(GREY_C, 1.5)
    panel.move_to([-3.25, 0, 0])
    cover = Group(get_meta_background(), panel)
    if visual is not None:
        visual.set_max_width(0.88 * panel.get_width()).set_max_height(0.86 * panel.get_height()).move_to(panel)
        cover.add(visual)
    series_title_text = Text(series_title, font=FONT, font_size=46).set_color(GREY_A)
    label_text = Text(label, font=FONT, font_size=44).set_color(YELLOW)
    title_lines = VGroup(*(Text(line, font=FONT, font_size=104).set_color(WHITE) for line in title.split("\n")))
    title_lines.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    title_lines.set_max_width(5.8)
    column = VGroup(series_title_text, label_text, title_lines).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
    column.set_max_width(5.8)
    column.move_to([0, 0.35, 0]).set_x(panel.get_right()[0] + 0.55, LEFT)
    cover.add(column)
    return cover


class CoverScene(InteractiveScene):
    """Subclass it in cover.py and return the episode's central picture from get_visual(). Set `title` (with '\\n'
    for a line break), `series_title` or `label` to override what plan.yaml gives."""

    title: str | None = None
    series_title: str | None = None
    label: str | None = None

    def get_visual(self) -> Mobject | None:
        return None

    def construct(self):
        context = get_scene_context()
        title, series_title, label = self.title, self.series_title, self.label
        if context.series is not None and context.episode_id:
            plan = load_plan(context.series)
            title = title or plan.find_episode(context.episode_id).title
            series_title = series_title or plan.title
            language_code = plan.resolve_episode_language_code(context.episode_id)
            label = label or format_episode_label(context.episode_id, language_code)
        self.add(get_episode_cover(title or "", series_title or "", label or "", self.get_visual()))
