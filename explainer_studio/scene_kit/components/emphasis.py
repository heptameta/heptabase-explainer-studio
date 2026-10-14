"""Emphasis and focus: highlight boxes, dimming without filling outlines, clean screen swaps, the grey commentary
layer and insets, shadows of an earlier state, and fast replays of a big-picture board."""

from __future__ import annotations

from manimlib import (
    DOWN,
    FRAME_HEIGHT,
    GREY_A,
    GREY_B,
    ORIGIN,
    SMALL_BUFF,
    UL,
    UR,
    YELLOW,
    Animation,
    Brace,
    FadeIn,
    FadeOut,
    FullScreenRectangle,
    Group,
    Mobject,
    ScreenRectangle,
    SurroundingRectangle,
    Tex,
    Text,
    Transform,
    VGroup,
    VMobject,
)

from ..layout_checks import mark_decorative
from ..style import DIM_OPACITY, HIGHLIGHT_RECTANGLE_COLOR, LABEL_FONT_SIZE, META_BACKGROUND_COLOR, SMALL_FONT_SIZE

__all__ = [
    "Replay",
    "dim",
    "expand_from_inset",
    "get_brace_label",
    "get_highlight_rectangle",
    "get_inset",
    "get_meta_background",
    "get_shadow",
    "shrink_to_inset",
    "swap_content",
    "undim",
]


def get_highlight_rectangle(mobject: Mobject, color=HIGHLIGHT_RECTANGLE_COLOR, buff=SMALL_BUFF,
                            stroke_width=2) -> SurroundingRectangle:
    return SurroundingRectangle(mobject, buff=buff).set_stroke(color, stroke_width)


def _get_dimmed_copy(mobject: Mobject, opacity: float) -> Mobject:
    """Lower stroke and fill opacity separately, never raising either: set_opacity would give outline-only shapes
    (lines, frames, SurroundingRectangle) a sudden translucent fill."""
    dimmed_copy = mobject.copy()
    for member in dimmed_copy.family_members_with_points():
        if isinstance(member, VMobject):
            member.set_stroke(opacity=min(member.get_stroke_opacity(), opacity), recurse=False)
            if member.get_fill_opacity() > 0:
                member.set_fill(opacity=min(member.get_fill_opacity(), opacity), recurse=False)
        else:
            member.set_opacity(opacity)
    return dimmed_copy


def dim(*mobjects: Mobject, opacity: float = DIM_OPACITY) -> list[Animation]:
    """Animations that fade mobjects back without changing their fill: play with self.play(*dim(a, b)). Dimming
    again fades further and keeps the look from before the first dim for undim."""
    animations = []
    for mobject in mobjects:
        if not hasattr(mobject, "_undimmed_copy"):
            mobject._undimmed_copy = mobject.copy()
        animations.append(Transform(mobject, _get_dimmed_copy(mobject, opacity)))
    return animations


def undim(*mobjects: Mobject) -> list[Animation]:
    """Animations that bring dimmed mobjects back exactly as they were (never use set_opacity(1) on a card: its
    translucent fill would turn opaque and hide the text inside). Mobjects that are not dimmed are left alone."""
    return [Transform(mobject, mobject.__dict__.pop("_undimmed_copy")) for mobject in mobjects
            if hasattr(mobject, "_undimmed_copy")]


def swap_content(scene, old_content, new_content, run_time: float = 1.0, shift=ORIGIN) -> None:
    """Replace one screenful with the next: the old content leaves first, then the new one arrives (a FadeOut and a
    FadeIn in one play smear both pictures together). old_content and new_content may be lists; they become a Group,
    so pictures are fine."""
    old_content = Group(*old_content) if isinstance(old_content, (list, tuple)) else old_content
    new_content = Group(*new_content) if isinstance(new_content, (list, tuple)) else new_content
    scene.play(FadeOut(old_content, shift=shift), run_time=run_time * 0.45)
    scene.play(FadeIn(new_content, shift=shift), run_time=run_time * 0.55)


def get_brace_label(mobject: Mobject, text: str, direction=DOWN, color=GREY_A, is_tex: bool = False) -> VGroup:
    brace = Brace(mobject, direction, buff=SMALL_BUFF)
    label = Tex(text, font_size=LABEL_FONT_SIZE) if is_tex else Text(text, font_size=LABEL_FONT_SIZE)
    label.set_color(color).next_to(brace, direction, SMALL_BUFF)
    return VGroup(brace, label)


def get_meta_background() -> FullScreenRectangle:
    """The dark-grey 'meta' layer used for commentary, cards and recaps."""
    return FullScreenRectangle().set_fill(META_BACKGROUND_COLOR, 1).set_stroke(width=0)


def get_inset(content: Mobject | None = None, height: float = 4.5, border_color=GREY_B) -> Group:
    """A black 16:9 inset window with a thin grey border."""
    screen_rectangle = ScreenRectangle(height=height).set_fill("#000000", 1).set_stroke(border_color, 1.5)
    group = Group(screen_rectangle)
    if content is not None:
        content.set_max_height(0.88 * height).set_max_width(0.88 * screen_rectangle.get_width())
        content.move_to(screen_rectangle)
        group.add(content)
    return group


def shrink_to_inset(scene, *mobjects, height: float = 3.4, corner=UL, buff: float = 0.45, run_time: float = 1.5):
    """Step back: fade in the grey layer and shrink the current content into a framed 16:9 inset (its text becomes a
    thumbnail, exempt from the checks). Returns (meta_background, inset); pass both to expand_from_inset."""
    mobjects = [mobject for mobject in mobjects
                if mobject is not getattr(scene, "frame", None) and type(mobject).__name__ != "CameraFrame"]
    meta_background = get_meta_background().set_fill(opacity=0)
    screen_rectangle = ScreenRectangle(height=FRAME_HEIGHT).set_fill("#000000", 1).set_stroke(GREY_B, 0)
    scene.add(meta_background, screen_rectangle)
    scene.bring_to_back(screen_rectangle)
    scene.bring_to_back(meta_background)
    inset = Group(screen_rectangle, *mobjects)
    if hasattr(scene, "play_sound"):
        scene.play_sound("whoosh_out")
    target = inset.copy().scale(height / FRAME_HEIGHT).to_corner(corner, buff=buff)
    target[0].set_stroke(GREY_B, 1.5)
    scene.play(meta_background.animate.set_fill(opacity=1), Transform(inset, target), run_time=run_time)
    inset._decorative_part_ids_before = {id(part) for part in inset.get_family()
                                         if getattr(part, "_is_decorative", False)}
    mark_decorative(inset)
    return meta_background, inset


def expand_from_inset(scene, meta_background, inset, run_time: float = 1.5):
    """Grow an inset made by shrink_to_inset back to full screen and fade out the grey layer."""
    scale = FRAME_HEIGHT / inset[0].get_height()
    target = inset.copy().scale(scale).move_to(ORIGIN)
    target[0].set_stroke(width=0)
    if hasattr(scene, "play_sound"):
        scene.play_sound("whoosh_in")
    scene.play(Transform(inset, target), meta_background.animate.set_fill(opacity=0), run_time=run_time)
    scene.remove(meta_background, inset[0])
    decorative_part_ids = getattr(inset, "_decorative_part_ids_before", set())
    for part in inset.get_family():  # full size again: the checks apply, except to what was decorative before
        if id(part) not in decorative_part_ids:
            part._is_decorative = False
    return inset[1:]


def get_shadow(mobject: Mobject, opacity: float = 0.25) -> Mobject:
    """A faded copy left where mobject is, so the result before a change stays visible under the new one:
    `self.add(get_shadow(curve))`, then change curve."""
    return mark_decorative(mobject.copy().clear_updaters().set_opacity(opacity))


class Replay:
    """Snapshots of a big-picture board (a map, a seat chart) taken as the story goes, played back fast:

        replay = Replay(board); replay.mark("1937")   # after each change of the board
        replay.play(self)                             # fast-forwards through the marks, then back to now
    """

    def __init__(self, board: Mobject):
        self.board, self.marks = board, []

    def mark(self, label: str = "") -> None:
        self.marks.append((self.board.copy(), label))

    def play(self, scene, step_seconds: float = 0.6, corner=UR, font_size: float = SMALL_FONT_SIZE + 4) -> None:
        if not self.marks:
            return
        current_board = self.board.copy()
        tag = VGroup()
        for mark_index, (snapshot, label) in enumerate(self.marks):
            new_tag = (Text(label, font_size=font_size).set_color(YELLOW).to_corner(corner, buff=0.5) if label
                       else VGroup())
            scene.play(Transform(self.board, snapshot.copy()), FadeOut(tag), FadeIn(new_tag),
                       run_time=step_seconds if mark_index else step_seconds * 1.5)
            tag = new_tag
        scene.play(Transform(self.board, current_board), FadeOut(tag), run_time=step_seconds)
