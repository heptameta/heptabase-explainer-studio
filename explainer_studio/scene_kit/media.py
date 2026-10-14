"""Real pictures, vector diagrams, video clips and the overlays that point into them.

    art = get_image("shared/assets/images/mona_lisa.jpg", height=6)     # paths are relative to production/
    box = get_image_callout(art, (0.35, 0.18, 0.62, 0.36), "smile")       # u0, v0, u1, v1 from the top-left, 0..1
    center, width = resolve_image_focus(art, (0.35, 0.18, 0.62, 0.36))
    self.play(self.frame.animate.move_to(center).set_width(width))      # slow look at one detail
    cell = get_svg("shared/assets/svg/animal_cell.svg", height=5)       # vector: every part is a real shape
    self.play(cell.get_part("nucleus").animate.set_fill(YELLOW))
    clip = get_clip("episodes/ep01/assets/experiment.mp4"); self.add(clip); play_clip(self, clip, 2, 9)
"""

from __future__ import annotations

import re
from pathlib import Path

import svgelements as se
from manimlib import *

from .. import user_dirs
from .context import get_scene_context
from .layout_checks import mark_decorative
from .style import LABEL_FONT_SIZE, SMALL_FONT_SIZE

__all__ = [
    "PartsSVG",
    "check_does_svg_need_raster",
    "get_3d_label",
    "get_clip",
    "get_image",
    "get_image_callout",
    "get_image_point",
    "get_paper_figure",
    "get_svg",
    "get_ui_callout",
    "get_uv_grid",
    "play_clip",
    "resolve_image_focus",
]

_AUTO_ID_PATTERN = re.compile(r"^(path|g|rect|ellipse|circle|use|layer|svg|polygon|polyline|line|text|tspan|defs|"
                              r"clippath|stop|lineargradient|radialgradient|mask|image|a|flowroot)[-_]?\d+([-_]\d+)*$",
                              re.IGNORECASE)
_SHAPE_LABELS_BY_SVG_HASH_MAP: dict[int, list[list[str]]] = {}


def _find_production_file_path(path: str) -> Path:
    resolved = get_scene_context().resolve_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"{path} does not exist (paths in scene files are relative to production/: {resolved})")
    return resolved


def _list_labels(element) -> list[str]:
    labels = []
    attribute_values = getattr(element, "values", {}) or {}
    for key in ("id", "inkscape:label", "{http://www.inkscape.org/namespaces/inkscape}label", "data-name",
                "aria-label", "class"):
        value = attribute_values.get(key) if key != "id" else getattr(element, "id", None)
        if value and not _AUTO_ID_PATTERN.match(str(value)):
            labels.append(str(value))
    return labels


def _flatten_gradients(root) -> None:
    """ManimGL cannot fill with gradients and paints those shapes black. Replace every fill/stroke url(#gradient)
    with the average of the gradient's stop colours (following xlink:href chains), so shaded diagrams keep their
    colours, flatly."""
    import xml.etree.ElementTree as ET  # noqa: F401
    resolve_tag_name = lambda element: element.tag.rsplit("}", 1)[-1]
    stop_colors_by_gradient_id_map, parent_id_by_gradient_id_map = {}, {}
    for element in root.iter():
        if resolve_tag_name(element) in ("linearGradient", "radialGradient") and element.get("id"):
            stop_colors = []
            for stop in element:
                if resolve_tag_name(stop) != "stop":
                    continue
                declarations = (stop.get("style") or "").split(";")
                value_by_style_property_map = dict(declaration.split(":", 1) for declaration in declarations
                                                   if ":" in declaration)
                stop_color = stop.get("stop-color") or value_by_style_property_map.get("stop-color", "").strip()
                if stop_color.startswith("#") and len(stop_color) in (4, 7):
                    stop_colors.append(stop_color)
            stop_colors_by_gradient_id_map[element.get("id")] = stop_colors
            href = element.get("{http://www.w3.org/1999/xlink}href") or element.get("href")
            if href:
                parent_id_by_gradient_id_map[element.get("id")] = href.lstrip("#")

    def resolve_gradient_color(gradient_id, depth=0):
        stop_colors = stop_colors_by_gradient_id_map.get(gradient_id, [])
        if not stop_colors and gradient_id in parent_id_by_gradient_id_map and depth < 8:
            return resolve_gradient_color(parent_id_by_gradient_id_map[gradient_id], depth + 1)
        if not stop_colors:
            return None
        full_colors = [stop_color if len(stop_color) == 7 else "#" + "".join(digit * 2 for digit in stop_color[1:])
                       for stop_color in stop_colors]
        rgb = np.mean([color_to_rgb(full_color) for full_color in full_colors], axis=0)
        return rgb_to_hex(rgb)

    url_pattern = re.compile(r"url\(\s*#([^)\s]+)\s*\)")
    for element in root.iter():
        for attribute_name in ("fill", "stroke"):
            match = url_pattern.search(element.get(attribute_name) or "")
            if match:
                flat_color = resolve_gradient_color(match.group(1))
                element.set(attribute_name, flat_color or "none")
        style_text = element.get("style")
        if style_text and "url(" in style_text:
            element.set("style", url_pattern.sub(lambda match: resolve_gradient_color(match.group(1)) or "none",
                                                 style_text))


class PartsSVG(SVGMobject):
    """An SVG whose shapes remember the ids / Inkscape labels of their groups, so a diagram's parts can be picked
    out: svg.get_part("nucleus"). Text inside the SVG is not drawn (ManimGL skips it): add labels yourself."""

    def modify_xml_tree(self, element_tree):
        _flatten_gradients(element_tree.getroot())
        return super().modify_xml_tree(element_tree)

    def mobjects_from_svg(self, svg: se.SVG) -> list[VMobject]:
        labels_by_shape_id_map: dict[int, list[str]] = {}
        group_indices_by_shape_id_map: dict[int, list[int]] = {}      # the groups each shape sits in, outermost first
        for group_index, group in enumerate(element for element in svg.elements() if isinstance(element, se.Group)):
            group_labels = _list_labels(group)
            for element in group.select():
                if element is group or isinstance(element, se.Group):
                    continue
                group_indices_by_shape_id_map.setdefault(id(element), []).append(group_index)
                if group_labels:
                    labels_by_shape_id_map.setdefault(id(element), []).extend(group_labels)
        shapes, shape_names, shape_group_indices = [], [], []
        for shape in svg.elements():
            if isinstance(shape, (se.Group, se.Use)) or type(shape) == se.SVGElement:
                continue
            if isinstance(shape, se.Path):
                mobject = self.path_to_mobject(shape, svg)
            elif isinstance(shape, se.SimpleLine):
                mobject = self.line_to_mobject(shape)
            elif isinstance(shape, se.Rect):
                mobject = self.rect_to_mobject(shape)
            elif isinstance(shape, (se.Circle, se.Ellipse)):
                mobject = self.ellipse_to_mobject(shape)
            elif isinstance(shape, se.Polygon):
                mobject = self.polygon_to_mobject(shape)
            elif isinstance(shape, se.Polyline):
                mobject = self.polyline_to_mobject(shape)
            else:
                continue
            if not mobject.has_points():
                continue
            if isinstance(shape, se.GraphicObject):
                self.apply_style_to_mobject(mobject, shape)
            if isinstance(shape, se.Transformable) and shape.apply:
                self.handle_transform(mobject, shape.transform)
            shapes.append(mobject)
            shape_names.append(labels_by_shape_id_map.get(id(shape), []) + _list_labels(shape))
            shape_group_indices.append(tuple(group_indices_by_shape_id_map.get(id(shape), [])))
        self._pending_shape_labels = list(zip(shape_names, shape_group_indices))
        return shapes

    def init_svg_mobject(self) -> None:
        svg_hash = hash_obj(self.hash_seed)
        if svg_hash in SVG_HASH_TO_MOB_MAP and svg_hash in _SHAPE_LABELS_BY_SVG_HASH_MAP:
            shapes = [shape.copy() for shape in SVG_HASH_TO_MOB_MAP[svg_hash]]
            shape_labels = _SHAPE_LABELS_BY_SVG_HASH_MAP[svg_hash]
        else:
            shapes = self.mobjects_from_svg_string(self.svg_string)
            shape_labels = self._pending_shape_labels
            SVG_HASH_TO_MOB_MAP[svg_hash] = [shape.copy() for shape in shapes]
            _SHAPE_LABELS_BY_SVG_HASH_MAP[svg_hash] = shape_labels
        # each shape carries its own names, so removing shapes is safe
        for shape, (names, group_indices) in zip(shapes, shape_labels):
            shape._svg_names, shape._svg_group_indices = names, group_indices
        self.add(*shapes)
        self.flip(RIGHT)

    def list_part_names(self) -> list[str]:
        """Meaningful ids and labels in the file (auto ids like path1234 are left out)."""
        part_names = []
        for shape in self.submobjects:
            for name in getattr(shape, "_svg_names", []):
                if name not in part_names:
                    part_names.append(name)
        return part_names

    def get_part(self, name: str) -> VGroup:
        """Every shape inside the group/element with this id or label (exact match, else case-insensitive substring)."""
        shapes = self.submobjects
        hits = [shape for shape in shapes if name in getattr(shape, "_svg_names", [])]
        if not hits:
            lowered_name = name.lower()
            hits = [shape for shape in shapes
                    if any(lowered_name in part_name.lower() for part_name in getattr(shape, "_svg_names", []))]
        if not hits:
            raise KeyError(f"no part {name!r}; names in this SVG: {self.list_part_names()[:40]}")
        return VGroup(*hits)


    # -- most downloaded diagrams name nothing, so parts can also be picked by where they are or by colour --
    def _convert_uv_to_point(self, u: float, v: float) -> np.ndarray:
        return self.get_corner(UL) + u * self.get_width() * RIGHT + v * self.get_height() * DOWN

    def get_part_at(self, u: float, v: float, min_area_fraction: float = 0.004, should_grow_to_group: bool = True):
        """The structure at the point (u, v) of the drawing (0..1 from its top-left), e.g. the nucleus: the smallest
        filled shape covering the point (specks under min_area_fraction of the drawing are skipped), grown to the
        innermost SVG group it belongs to, since one structure is usually several shapes (membrane, inside, shading).
        should_grow_to_group=False returns just that one shape. Find (u, v) with a get_uv_grid(drawing) planning
        preview."""
        point = self._convert_uv_to_point(u, v)
        total_area = self.get_width() * self.get_height()
        hits = [shape for shape in self.submobjects if shape.has_points() and shape.get_fill_opacity() > 0
                and shape.get_width() * shape.get_height() >= min_area_fraction * total_area
                and shape.get_left()[0] <= point[0] <= shape.get_right()[0]
                and shape.get_bottom()[1] <= point[1] <= shape.get_top()[1]]
        if not hits:
            raise ValueError(f"nothing filled at ({u}, {v})")
        shape = min(hits, key=lambda shape: shape.get_width() * shape.get_height())
        if not should_grow_to_group:
            return shape
        for group_index in reversed(getattr(shape, "_svg_group_indices", ())):
            members = [member for member in self.submobjects
                       if group_index in getattr(member, "_svg_group_indices", ())]
            group = VGroup(*members)
            if 1 < len(members) and group.get_width() * group.get_height() <= 0.35 * total_area:
                return group
            if group.get_width() * group.get_height() > 0.35 * total_area:
                break
        return VGroup(shape)

    def get_parts_in(self, box: tuple[float, float, float, float]) -> VGroup:
        """Every shape whose centre lies in the region (u0, v0, u1, v1) of the drawing."""
        top_left, bottom_right = self._convert_uv_to_point(box[0], box[1]), self._convert_uv_to_point(box[2], box[3])
        return VGroup(*[shape for shape in self.submobjects
                        if top_left[0] <= shape.get_center()[0] <= bottom_right[0]
                        and bottom_right[1] <= shape.get_center()[1] <= top_left[1]])

    def count_fill_colors(self, top_count: int = 12) -> list[tuple[str, int]]:
        """The fill colours used, most common first: structures in a diagram usually share one colour."""
        shape_count_by_color_map: dict[str, int] = {}
        for shape in self.submobjects:
            if shape.has_points() and shape.get_fill_opacity() > 0:
                fill_color = shape.get_fill_color()
                color = fill_color.to_hex() if hasattr(fill_color, "to_hex") else str(fill_color)
                shape_count_by_color_map[color] = shape_count_by_color_map.get(color, 0) + 1
        return sorted(shape_count_by_color_map.items(), key=lambda color_and_count: -color_and_count[1])[:top_count]

    def get_parts_by_color(self, color, tolerance: float = 0.06) -> VGroup:
        """Every filled shape whose fill colour is within tol (0..1 per RGB channel) of color."""
        target = np.array(color_to_rgb(color))
        return VGroup(*[shape for shape in self.submobjects if shape.has_points() and shape.get_fill_opacity() > 0
                        and np.abs(np.array(color_to_rgb(shape.get_fill_color())) - target).max() <= tolerance])


_RASTER_ONLY_PATTERN = re.compile(r"<(filter|mask|image|foreignObject)\b", re.IGNORECASE)
_GRADIENT_PATTERN = re.compile(r"<(linearGradient|radialGradient)\b", re.IGNORECASE)


def check_does_svg_need_raster(path: str) -> bool:
    """True when the file relies on things ManimGL cannot draw (filters, masks, embedded images) or is heavily
    shaded artwork (100+ gradients): as vectors it would fall apart, so show it as a picture instead.
    Text alone does not count: ManimGL drops SVG text, which is what you want when you relabel in Chinese."""
    svg_text = _find_production_file_path(path).read_text(encoding="utf-8", errors="ignore")
    return bool(_RASTER_ONLY_PATTERN.search(svg_text)) or len(_GRADIENT_PATTERN.findall(svg_text)) > 100


def _rasterize(path: str, size_pixels: int = 2400) -> Path:
    """Render an SVG to PNG once (rsvg-convert, Inkscape or macOS Quick Look), cached in the user cache."""
    import hashlib
    import shutil
    import subprocess

    source_file_path = _find_production_file_path(path)
    output_dir_path = user_dirs.get_cache_dir_path() / "raster"
    output_dir_path.mkdir(parents=True, exist_ok=True)
    source_digest = hashlib.sha256(source_file_path.read_bytes()).hexdigest()[:16]
    output_file_path = output_dir_path / f"{source_digest}_{size_pixels}.png"
    if output_file_path.exists():
        return output_file_path
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", str(size_pixels), "-o", str(output_file_path), str(source_file_path)],
                       capture_output=True, timeout=60, check=False)
    elif shutil.which("inkscape"):
        subprocess.run(["inkscape", str(source_file_path), "--export-type=png", f"--export-width={size_pixels}",
                        f"--export-filename={output_file_path}"], capture_output=True, timeout=120, check=False)
    elif shutil.which("qlmanage"):
        subprocess.run(["qlmanage", "-t", "-s", str(size_pixels), "-o", str(output_dir_path), str(source_file_path)],
                       capture_output=True, timeout=60, check=False)
        quick_look_output_file_path = output_dir_path / (source_file_path.name + ".png")
        if quick_look_output_file_path.exists():
            quick_look_output_file_path.replace(output_file_path)
    if not output_file_path.exists():
        raise RuntimeError(f"could not rasterize {source_file_path}; export it to PNG and use get_image")
    return output_file_path


def _get_paper_backdrop_group(mobject: Mobject, buff: float = 0.3, color: str = "#F3F1EC") -> Mobject:
    card = RoundedRectangle(width=mobject.get_width() + 2 * buff, height=mobject.get_height() + 2 * buff,
                            corner_radius=0.12)
    card.set_fill(color, 1).set_stroke(width=0).move_to(mobject)
    group = Group(card, mobject)
    group.card, group.picture = card, mobject
    return group


def get_svg(path: str, height: float = 4.5, width: float | None = None, mode: str = "auto",
            has_backdrop: bool = False, **kwargs):
    """A vector diagram or icon (a path relative to production/).
    mode "auto": native shapes (recolour, dim, animate any part) when the file is simple; files that need text,
    gradients or filters are shown as a picture instead (check_does_svg_need_raster). "vector" / "raster" force one.
    has_backdrop=True puts it on a light paper card: most downloaded diagrams are drawn for white paper, and their black
    outlines disappear on a black background. With a backdrop, the result is a Group; the diagram is .picture."""
    should_rasterize = mode == "raster" or (mode == "auto" and check_does_svg_need_raster(path))
    if should_rasterize:
        return get_image(str(_rasterize(path)), height=height, width=width, has_backdrop=has_backdrop)
    svg = PartsSVG(str(_find_production_file_path(path)), height=None, **kwargs)
    if width is not None:
        svg.set_width(width)
    else:
        svg.set_height(height)
    return _get_paper_backdrop_group(svg) if has_backdrop else svg


def get_image(path: str, height: float = 5.0, width: float | None = None, border_color=None,
              has_backdrop: bool = False) -> Mobject:
    """A photograph, artwork or scanned document (a path relative to production/). SVG files go through get_svg.
    border_color: a colour for a thin frame (artworks look better without one). has_backdrop: a light card behind a
    diagram with a transparent background. With a border or a backdrop the result is a Group; the picture itself is
    .picture."""
    if str(path).lower().endswith(".svg"):
        return get_svg(path, height=height, width=width, has_backdrop=has_backdrop)
    picture = ImageMobject(str(_find_production_file_path(path)))
    if width is not None:
        picture.set_width(width)
    else:
        picture.set_height(height)
    if has_backdrop:
        return _get_paper_backdrop_group(picture)
    if border_color is not None:
        border_rectangle = SurroundingRectangle(picture, buff=0, color=border_color, stroke_width=1.5)
        group = Group(picture, border_rectangle)
        group.picture = picture
        return group
    return picture


def _get_picture(mobject):
    return getattr(mobject, "picture", mobject)


def get_image_point(image: Mobject, u: float, v: float) -> np.ndarray:
    """The frame point at (u, v) of a picture, measured from its top-left corner as fractions of width and height."""
    picture = _get_picture(image)
    return picture.get_corner(UL) + u * picture.get_width() * RIGHT + v * picture.get_height() * DOWN


def get_image_callout(image: Mobject, box: tuple[float, float, float, float], label: str = "", color=YELLOW,
                      direction=RIGHT, font_size: float = SMALL_FONT_SIZE, stroke_width: float = 3) -> VGroup:
    """A box around a region of a picture (u0, v0, u1, v1 in 0..1 from the top-left) with an optional label."""
    u0, v0, u1, v1 = box
    top_left, bottom_right = get_image_point(image, u0, v0), get_image_point(image, u1, v1)
    rectangle = Rectangle(width=abs(bottom_right[0] - top_left[0]), height=abs(bottom_right[1] - top_left[1]))
    rectangle.move_to((top_left + bottom_right) / 2)
    rectangle.set_stroke(color, stroke_width).set_fill(opacity=0)
    callout = VGroup(rectangle)
    callout.rectangle = rectangle
    if label:
        label_text = Text(label, font_size=font_size).set_color(color).next_to(rectangle, direction, buff=0.15)
        callout.add(label_text)
        callout.label = label_text
    return callout


def get_uv_grid(image: Mobject, step: float = 0.1, color=RED, font_size: float = 14) -> VGroup:
    """A planning overlay (not for the final video): grid lines every `step` of a picture or drawing, labelled with
    their u / v values, so one preview shows the coordinates to use in get_part_at, get_image_callout and
    resolve_image_focus.
    Remove it once the coordinates are chosen."""
    picture = _get_picture(image)
    grid = VGroup()
    line_count = round(1 / step)
    for i in range(line_count + 1):
        fraction = i * step
        top_point, left_point = get_image_point(picture, fraction, 0), get_image_point(picture, 0, fraction)
        grid.add(Line(top_point, get_image_point(picture, fraction, 1)).set_stroke(color, 1, 0.7))
        grid.add(Line(left_point, get_image_point(picture, 1, fraction)).set_stroke(color, 1, 0.7))
        grid.add(Text(f"{fraction:.1f}", font_size=font_size).set_color(color).next_to(top_point, UP, buff=0.04))
        grid.add(Text(f"{fraction:.1f}", font_size=font_size).set_color(color).next_to(left_point, LEFT, buff=0.04))
    return mark_decorative(grid)


def resolve_image_focus(image: Mobject, box: tuple[float, float, float, float],
                        margin: float = 1.25) -> tuple[np.ndarray, float]:
    """Where to put the camera to look closely at a region: (center, frame width) for
    self.frame.animate.move_to(center).set_width(width). Keeps the 16:9 frame around the whole region."""
    u0, v0, u1, v1 = box
    top_left, bottom_right = get_image_point(image, u0, v0), get_image_point(image, u1, v1)
    region_width, region_height = abs(bottom_right[0] - top_left[0]), abs(bottom_right[1] - top_left[1])
    return (top_left + bottom_right) / 2, max(region_width, region_height * 16 / 9) * margin


# ---------------------------------------------------------------------------
# Video clips: real footage, experiments, archive film, screen recordings, renders from other tools
# ---------------------------------------------------------------------------
def get_clip(path: str, height: float = 5.0, width: float | None = None, start_seconds: float = 0.0,
             border_color=None) -> Mobject:
    """A video clip as a mobject (scale it, frame it, draw on top of it). It shows the frame at `start_seconds` until
    play_clip runs it. With border_color the result is a Group and the clip itself is .picture."""
    clip = VideoMobject(str(_find_production_file_path(path)), height=height, time=start_seconds)
    clip._video_file_path = str(_find_production_file_path(path))
    if width is not None:
        clip.set_width(width)
    if border_color is not None:
        border_rectangle = SurroundingRectangle(clip, buff=0, color=border_color, stroke_width=1.5)
        group = Group(clip, border_rectangle)
        group.picture = clip
        return group
    return clip


def play_clip(scene, clip: Mobject, start_seconds: float = 0.0, end_seconds: float | None = None,
              should_play_audio: bool = True, gain_decibels: float = -3.0, speed: float = 1.0) -> None:
    """Play a clip from `start_seconds` to `end_seconds` of the footage while the scene waits; its own sound, if it
    has any, goes into the mix and ducks the background music (should_play_audio=False keeps footage with sound
    silent under narration). Put it inside a play_beat block to run under speech, or between beats to let the
    footage speak for itself."""
    picture = _get_picture(clip)
    end_seconds = picture.get_duration() if end_seconds is None else min(end_seconds, picture.get_duration())
    duration_seconds = max(0.0, (end_seconds - start_seconds) / speed)
    picture.set_time(start_seconds)
    picture.add_updater(lambda mobject, dt: mobject.increment_time(dt * speed))
    if should_play_audio and speed == 1.0 and hasattr(scene, "play_sound"):
        scene.play_sound(getattr(picture, "_video_file_path", picture.video_path), gain_decibels,
                         should_duck_background_music=True, source_start_seconds=start_seconds,
                         duration_seconds=duration_seconds)
    scene.wait(duration_seconds)
    picture.clear_updaters()
    picture.set_time(end_seconds)


def get_3d_label(clip: Mobject, labels_file_path: str, part_name: str, text: str, color=YELLOW, direction=UP,
                 buff: float = 0.25, font_size: float = LABEL_FONT_SIZE - 4, has_dot: bool = True) -> VGroup:
    """A label that follows a part of an `asset blender render` turntable as the camera goes round (the render's
    .labels.json says where each part is on screen, frame by frame). Add it after the clip; play the clip with
    play_clip."""
    import json as _json
    labels_json = _json.loads(_find_production_file_path(labels_file_path).read_text(encoding="utf-8"))
    track, fps = labels_json["screen_positions_by_part_map"][part_name], labels_json["fps"]
    picture = _get_picture(clip)
    label = Text(text, font_size=font_size).set_color(color)
    dot_mark = Dot(radius=0.06, fill_color=color) if has_dot else VGroup()
    label_group = VGroup(dot_mark, label)

    def move_to_track_point(group):   # moves the group's own parts, so a copy of the label follows the clip too
        frame_index = min(len(track) - 1, max(0, round(picture.get_time() * fps)))
        u, v, _ = track[frame_index]
        point = picture.get_corner(DL) + u * picture.get_width() * RIGHT + v * picture.get_height() * UP
        if has_dot:
            group[0].move_to(point)
        group[1].next_to(point, direction, buff=buff)
    move_to_track_point(label_group)
    label_group.add_updater(move_to_track_point)
    return label_group


def get_ui_callout(clip: Mobject, steps_file_path: str, step_index: int, label: str = "", color=YELLOW, direction=DOWN,
                   padding_fraction: float = 0.06, font_size: float = SMALL_FONT_SIZE + 2) -> VGroup:
    """A box around the element an `asset playwright record` step acted on (from the recording's .steps.json), placed
    over the playing clip; .start_seconds is when that step happened (seconds into the clip). Parts: .rectangle,
    .label."""
    import json as _json
    steps_json = _json.loads(_find_production_file_path(steps_file_path).read_text(encoding="utf-8"))
    step_record = steps_json["steps"][step_index]
    if not step_record.get("box"):
        raise ValueError(f"step {step_index} ({step_record['action']}) acted on no element")
    u0, v0, u1, v1 = step_record["box"]
    callout = get_image_callout(clip, (u0, v0, u1, v1), label, color=color, direction=direction, font_size=font_size)
    callout.rectangle.scale(1 + padding_fraction)
    callout.start_seconds = step_record["start_seconds"]
    callout.end_seconds = step_record.get("end_seconds", step_record["start_seconds"])
    return callout


def get_paper_figure(path: str, caption: str = "", source: str = "", height: float = 4.5, border_color=GREY_B) -> Group:
    """A figure taken from a paper (`asset pdf crop`): the image with a thin border, an optional caption below and a
    small source line (e.g. "Elhage et al. 2021, Fig. 2"). Treat it as an object: show it whole, box the part that
    matters, then pull that part out."""
    picture = ImageMobject(str(_find_production_file_path(path))).set_height(height)
    top_left, top_right, bottom_right, bottom_left = (picture.get_corner(corner) for corner in (UL, UR, DR, DL))
    corner_pairs = [(top_left, top_right), (top_right, bottom_right), (bottom_right, bottom_left),
                    (bottom_left, top_left)]
    frame_lines = VGroup(*(Line(start, end) for start, end in corner_pairs)).set_stroke(border_color, 1.5)
    group = Group(picture, frame_lines)
    caption_lines = VGroup()
    if caption:
        caption_lines.add(Text(caption, font_size=SMALL_FONT_SIZE + 4).set_color(GREY_A))
    if source:
        caption_lines.add(Text(source, font_size=SMALL_FONT_SIZE - 4).set_color(GREY_C))
    if len(caption_lines):
        caption_lines.arrange(DOWN, buff=0.1).next_to(picture, DOWN, 0.2)
        group.add(caption_lines)
    group.picture, group.frame_lines = picture, frame_lines
    return group
