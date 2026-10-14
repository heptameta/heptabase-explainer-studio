"""The automatic checks NarratedScene runs on the frame at the end of every beat.

Checks: text_outside_frame, text_overlap, text_too_small and outside_container. All are reported for the agent to
fix; only text_too_small blocks delivery (see `schemas.automatic_checks.BLOCKING_CHECK_NAMES`).

`mark_decorative` exempts a prop's text (the small print on a document stand-in, a thumbnail); `keep_inside` registers
parts that must stay inside a container's drawn outline.
"""

from __future__ import annotations

import math

import numpy as np
from manimlib import Mobject, StringMobject, VMobject

__all__ = ["MIN_FONT_SIZE", "keep_inside", "mark_decorative", "measure_effective_font_size"]

MIN_FONT_SIZE = 16  # smallest readable on-screen size, in font_size units at the default frame height
FRAME_HEIGHT = 8.0


def mark_decorative(mobject: Mobject) -> Mobject:
    """Exempt a prop's text from the automatic checks: text that is texture, not reading (the small print on a
    document stand-in, a thumbnail, a faded copy left under its replacement)."""
    for part in mobject.get_family():
        part._is_decorative = True
    return mobject


def keep_inside(container: Mobject, *parts: Mobject, margin: float = 0.02) -> Mobject:
    """Say that parts belong inside a container (molecules in a bowl, organelles in a cell, dots on a map): a part that
    pokes out of the container's drawn outline at the end of a beat is reported as outside_container."""
    for part in parts:
        part._container_and_margin = (container, margin)
    return container


def measure_effective_font_size(mobject: Mobject, frame_height: float = FRAME_HEIGHT) -> float | None:
    font_size, base_size = getattr(mobject, "font_size", None), getattr(mobject, "_base_size", None)
    if not font_size or not base_size or base_size[0] * base_size[1] <= 0:
        return None
    scale = math.sqrt(mobject.get_width() * mobject.get_height() / (base_size[0] * base_size[1]))
    return font_size * scale * FRAME_HEIGHT / frame_height


# Helpers ------------------------------------------------------------------------------------------------------------
def _measure_opacity(mobject: Mobject) -> float:
    """How opaque a mobject draws itself: its fill or stroke for a vector shape, the alpha of its points for anything
    else (images, surfaces, dot clouds)."""
    if isinstance(mobject, VMobject):
        stroke_opacity = mobject.get_stroke_opacity() if mobject.get_stroke_width() > 0 else 0
        return max(mobject.get_fill_opacity(), stroke_opacity)
    point_data = mobject.data
    field_names = point_data.dtype.names or ()
    if not len(point_data):
        return 0.0
    if "opacity" in field_names:
        return float(point_data["opacity"].max())
    return float(point_data["rgba"][:, 3].max()) if "rgba" in field_names else 1.0


def _check_is_visible(mobject: Mobject) -> bool:
    return any(_measure_opacity(member) > 0.15 for member in mobject.family_members_with_points())


def format_mobject_label(mobject: Mobject) -> str:
    text = getattr(mobject, "string", None) or getattr(mobject, "text", None) or type(mobject).__name__
    return str(text).replace("\n", " ")[:24]


def _iterate_ancestors(mobject: Mobject):
    pending_parents, seen_ids = list(getattr(mobject, "parents", [])), set()
    while pending_parents:
        parent = pending_parents.pop()
        if id(parent) in seen_ids:
            continue
        seen_ids.add(id(parent))
        yield parent
        pending_parents.extend(getattr(parent, "parents", []))


def _list_type_names(mobject: Mobject) -> set[str]:
    return {cls.__name__ for cls in type(mobject).__mro__}


def _check_is_in_brace(mobject: Mobject) -> bool:
    """A Brace is drawn by LaTeX, but it is a line, not something to read."""
    return "Brace" in _list_type_names(mobject) or any("Brace" in _list_type_names(parent)
                                                       for parent in _iterate_ancestors(mobject))


def _check_is_text(mobject: Mobject) -> bool:
    return (isinstance(mobject, StringMobject) or hasattr(mobject, "_base_size")) and not _check_is_in_brace(mobject)


def _measure_bounds(mobject: Mobject) -> tuple[float, float, float, float]:
    return mobject.get_left()[0], mobject.get_right()[0], mobject.get_bottom()[1], mobject.get_top()[1]


def _find_outline(container: Mobject) -> np.ndarray | None:
    vector_members = [member for member in container.family_members_with_points() if isinstance(member, VMobject)]
    if not vector_members:
        return None
    biggest = max(vector_members, key=lambda member: member.get_width() * member.get_height())
    points = biggest.get_anchors()
    return points[:, :2] if len(points) >= 3 else None


def _check_is_inside_polygon(xy: np.ndarray, polygon: np.ndarray) -> np.ndarray:
    x, y = xy[:, 0][:, None], xy[:, 1][:, None]
    x1, y1 = polygon[:, 0][None, :], polygon[:, 1][None, :]
    x2, y2 = np.roll(polygon[:, 0], -1)[None, :], np.roll(polygon[:, 1], -1)[None, :]
    crosses = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / np.where(y2 == y1, 1e-12, y2 - y1) + x1)
    return crosses.sum(axis=1) % 2 == 1


def _check_is_outside_container(part: Mobject) -> bool:
    container, margin = part._container_and_margin
    polygon = _find_outline(container)
    if polygon is None:
        return False
    points = [(member.get_anchors() if isinstance(member, VMobject) else member.get_points())[:, :2]
              for member in part.family_members_with_points()]
    points = np.concatenate(points) if points else np.zeros((0, 2))
    if not len(points):
        return False
    center = polygon.mean(axis=0)
    grown_polygon = center + (polygon - center) * (1 + margin / max(float(np.abs(polygon - center).max()), 1e-6))
    return not bool(_check_is_inside_polygon(points, grown_polygon).all())


# The automatic checks -------------------------------------------------------------------------------------------------
def run_automatic_checks(scene) -> tuple[list[tuple[str, str]], dict]:
    """Layout problems in the scene's current frame as (check name, detail) pairs, and the frame's text metrics
    (smallest font size, closest distance of text to a frame edge) used to pick text-visibility frames."""
    frame = scene.frame
    center_x, center_y = frame.get_center()[:2]
    half_width, half_height = frame.get_width() / 2, frame.get_height() / 2
    text_mobjects, seen_ids, contained_parts = [], set(), []
    for top_mobject in scene.mobjects:
        if top_mobject is frame:
            continue
        for mobject in top_mobject.get_family():
            if id(mobject) in seen_ids:
                continue
            seen_ids.add(id(mobject))
            if getattr(mobject, "_container_and_margin", None) is not None and _check_is_visible(mobject):
                contained_parts.append(mobject)
            if (not getattr(mobject, "_is_decorative", False) and _check_is_text(mobject)
                    and _check_is_visible(mobject) and mobject.get_width() > 1e-3):
                text_mobjects.append(mobject)
    problems: list[tuple[str, str]] = []
    on_screen_ids = {id(mobject) for top_mobject in scene.mobjects for mobject in top_mobject.get_family()}
    margin = 0.05
    edge_distance = math.inf
    for mobject in text_mobjects:
        left, right, bottom, top_edge = _measure_bounds(mobject)
        edge_distance = min(edge_distance, left - (center_x - half_width), (center_x + half_width) - right,
                            bottom - (center_y - half_height), (center_y + half_height) - top_edge)
        sides = [side for side, is_past_edge in (("left", left < center_x - half_width - margin),
                                        ("right", right > center_x + half_width + margin),
                                        ("bottom", bottom < center_y - half_height - margin),
                                        ("top", top_edge > center_y + half_height + margin)) if is_past_edge]
        if sides:
            detail = f'"{format_mobject_label(mobject)}" runs off the {"/".join(sides)} edge'
            problems.append(("text_outside_frame", detail))
    for mobject in contained_parts:
        if id(mobject._container_and_margin[0]) in on_screen_ids and _check_is_outside_container(mobject):
            center = mobject.get_center()
            container_label = format_mobject_label(mobject._container_and_margin[0])
            detail = (f'"{format_mobject_label(mobject)}" pokes out of {container_label} '
                      f'at ({center[0]:.1f}, {center[1]:.1f})')
            problems.append(("outside_container", detail))
    smallest_font_size = math.inf
    for mobject in text_mobjects:
        font_size = measure_effective_font_size(mobject, frame.get_height())
        if font_size is None:
            continue
        smallest_font_size = min(smallest_font_size, font_size)
        if font_size < MIN_FONT_SIZE:
            detail = f'"{format_mobject_label(mobject)}" is {font_size:.1f} on screen, under {MIN_FONT_SIZE}'
            problems.append(("text_too_small", detail))
    for i in range(len(text_mobjects)):
        for j in range(i + 1, len(text_mobjects)):
            first_text, second_text = text_mobjects[i], text_mobjects[j]
            if first_text in second_text.get_family() or second_text in first_text.get_family():
                continue
            overlap_width = (min(first_text.get_right()[0], second_text.get_right()[0])
                             - max(first_text.get_left()[0], second_text.get_left()[0]))
            overlap_height = (min(first_text.get_top()[1], second_text.get_top()[1])
                              - max(first_text.get_bottom()[1], second_text.get_bottom()[1]))
            if overlap_width <= 0 or overlap_height <= 0:
                continue
            smaller_area = min(first_text.get_width() * first_text.get_height(),
                               second_text.get_width() * second_text.get_height())
            if smaller_area > 0 and overlap_width * overlap_height / smaller_area > 0.2:
                detail = f'"{format_mobject_label(first_text)}" overlaps "{format_mobject_label(second_text)}"'
                problems.append(("text_overlap", detail))
    metrics = {"min_font_size": None if math.isinf(smallest_font_size) else round(smallest_font_size, 1),
               "edge_distance": None if math.isinf(edge_distance) else round(float(edge_distance), 3)}
    return problems, metrics
