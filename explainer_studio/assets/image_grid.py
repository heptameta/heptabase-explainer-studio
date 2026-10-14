"""A copy of an image with a line every 10%, labelled 0.1 to 0.9, for reading positions to mark in a scene."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..errors import StudioError
from .common import create_viewing_dir
from .thumbnail_sheet import draw_svg_thumbnail

LINE_COLOR = (255, 0, 160)


def draw_grid(image_file_path: Path) -> Path:
    if not image_file_path.is_file():
        raise StudioError(f"{image_file_path} not found", "the path does not point at a file", "pass the image's path")
    if image_file_path.suffix.lower() == ".svg":
        picture = draw_svg_thumbnail(image_file_path.read_bytes(), 1200)
        if picture is None:
            raise StudioError(f"cannot draw {image_file_path.name}", "the SVG could not be parsed",
                              "pass a PNG or JPEG copy")
        backdrop = Image.new("RGBA", picture.size, (255, 255, 255, 255))
        backdrop.alpha_composite(picture)
        picture = backdrop.convert("RGB")
    else:
        try:
            picture = Image.open(image_file_path).convert("RGB")
        except OSError as error:
            raise StudioError(f"cannot open {image_file_path.name}", str(error),
                              "pass a PNG, JPEG or SVG file") from None
    width_pixels, height_pixels = picture.size
    draw = ImageDraw.Draw(picture)
    font = ImageFont.load_default(size=max(12, min(width_pixels, height_pixels) // 45))
    line_width_pixels = max(1, min(width_pixels, height_pixels) // 600)
    for step in range(1, 10):
        x, y = round(width_pixels * step / 10), round(height_pixels * step / 10)
        draw.line([(x, 0), (x, height_pixels)], fill=LINE_COLOR, width=line_width_pixels)
        draw.line([(0, y), (width_pixels, y)], fill=LINE_COLOR, width=line_width_pixels)
        draw.text((x + 3, 3), f"{step / 10:.1f}", fill=LINE_COLOR, font=font, stroke_width=2, stroke_fill="white")
        draw.text((3, y + 3), f"{step / 10:.1f}", fill=LINE_COLOR, font=font, stroke_width=2, stroke_fill="white")
    output_file_path = create_viewing_dir("grid") / f"{image_file_path.stem}-grid.png"
    picture.save(output_file_path)
    return output_file_path
