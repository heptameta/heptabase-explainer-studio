"""Numbered thumbnail sheets of search results, and SVG thumbnails drawn without a browser or Cairo."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

BACKGROUND_COLOR = (28, 28, 30)
CELL_BACKGROUND_COLOR = (236, 236, 236)
LABEL_HEIGHT_PIXELS = 24


def draw_svg_thumbnail(svg_bytes: bytes, size_pixels: int) -> Image.Image | None:
    """Fill and stroke the SVG's shapes with Pillow. Good enough to recognise an icon; gradients and filters are
    drawn flat."""
    from svgelements import SVG, Close, Color, Line, Move, Shape
    from svgelements import Path as SvgPath

    try:
        svg = SVG.parse(io.BytesIO(svg_bytes), reify=True)
        box = svg.bbox()
    except Exception:  # noqa: BLE001 - a broken SVG only leaves an empty cell
        return None
    if box is None:
        return None
    x0, y0, x1, y1 = box
    span = max(x1 - x0, y1 - y0, 1e-6)
    supersample_factor = 3
    scale = (size_pixels - 8) * supersample_factor / span
    canvas_size_pixels = size_pixels * supersample_factor
    canvas = Image.new("RGBA", (canvas_size_pixels, canvas_size_pixels), (0, 0, 0, 0))
    offset = ((canvas_size_pixels - (x1 - x0) * scale) / 2, (canvas_size_pixels - (y1 - y0) * scale) / 2)

    def convert_svg_point_to_canvas(point) -> tuple[float, float]:
        return ((point[0] - x0) * scale + offset[0], (point[1] - y0) * scale + offset[1])

    def convert_path_to_polygons(path) -> list[list[tuple[float, float]]]:
        """The path's subpaths as point lists: lines as they are, curves sampled."""
        finished_polygons, current_polygon = [], []
        for segment in path:
            if isinstance(segment, Move):
                finished_polygons.append(current_polygon)
                current_polygon = [convert_svg_point_to_canvas(segment.end)]
            elif isinstance(segment, (Line, Close)):
                current_polygon.append(convert_svg_point_to_canvas(segment.end))
            elif segment.end is not None:
                current_polygon.extend(convert_svg_point_to_canvas(segment.point(t))
                                       for t in np.linspace(0, 1, 13)[1:])
        return [polygon for polygon in [*finished_polygons, current_polygon] if len(polygon) >= 2]

    for element in svg.elements():
        if not isinstance(element, Shape):
            continue
        try:
            subpaths = convert_path_to_polygons(SvgPath(element))
        except Exception:  # noqa: BLE001, S112 - skip a shape svgelements cannot flatten
            continue
        fill: Color | None = element.fill
        if fill is not None and fill.value is not None and fill.alpha:
            mask = Image.new("1", canvas.size, 0)
            for polygon in subpaths:  # even-odd: holes cancel out
                if len(polygon) >= 3:
                    layer = Image.new("1", canvas.size, 0)
                    ImageDraw.Draw(layer).polygon(polygon, fill=1)
                    mask = ImageChops.logical_xor(mask, layer)
            color_layer = Image.new("RGBA", canvas.size, (fill.red, fill.green, fill.blue, fill.alpha))
            canvas.paste(color_layer, (0, 0), mask.convert("L"))
        stroke: Color | None = element.stroke
        stroke_width_pixels = (element.stroke_width or 0) * scale
        if stroke is not None and stroke.value is not None and stroke.alpha and stroke_width_pixels > 0:
            draw = ImageDraw.Draw(canvas)
            for polygon in subpaths:
                draw.line(polygon, fill=(stroke.red, stroke.green, stroke.blue, stroke.alpha),
                          width=max(1, int(stroke_width_pixels)))
    return canvas.resize((size_pixels, size_pixels), Image.LANCZOS)


def draw_thumbnail_sheet(cells: list[tuple[Image.Image | None, str]], output_file_path: Path,
                         cell_size_pixels: int = 220, column_count: int = 4) -> Path:
    """A grid of thumbnails, each labelled below with its text (the candidate number first)."""
    row_count = max(1, (len(cells) + column_count - 1) // column_count)
    row_height_pixels = cell_size_pixels + LABEL_HEIGHT_PIXELS
    thumbnail_sheet = Image.new("RGB", (column_count * cell_size_pixels, row_count * row_height_pixels),
                                BACKGROUND_COLOR)
    draw = ImageDraw.Draw(thumbnail_sheet)
    font = ImageFont.load_default(size=14)
    for index, (thumbnail, label) in enumerate(cells):
        x, y = (index % column_count) * cell_size_pixels, (index // column_count) * row_height_pixels
        draw.rectangle([x + 3, y + 3, x + cell_size_pixels - 4, y + cell_size_pixels - 4], fill=CELL_BACKGROUND_COLOR)
        if thumbnail is not None:
            image = thumbnail.convert("RGBA")
            image.thumbnail((cell_size_pixels - 12, cell_size_pixels - 12))
            backdrop = Image.new("RGBA", image.size, CELL_BACKGROUND_COLOR + (255,))
            backdrop.alpha_composite(image)
            thumbnail_sheet.paste(backdrop.convert("RGB"), (x + (cell_size_pixels - image.width) // 2,
                                                            y + (cell_size_pixels - image.height) // 2))
        draw.text((x + 6, y + cell_size_pixels + 3), label[:30], fill=(235, 235, 235), font=font)
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_sheet.save(output_file_path)
    return output_file_path


def draw_placeholder_thumbnail(text: str, size_pixels: int = 200) -> Image.Image:
    """A cell for media without a picture (audio): its kind and length in large type."""
    image = Image.new("RGB", (size_pixels, size_pixels), CELL_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=22)
    lines = text.split("\n")
    for number, line in enumerate(lines):
        width_pixels = draw.textlength(line, font=font)
        draw.text(((size_pixels - width_pixels) / 2, size_pixels / 2 - 16 * len(lines) + number * 32), line,
                  fill=(60, 60, 60), font=font)
    return image
