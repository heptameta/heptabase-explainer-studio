"""Screenshot sheets: what the agent looks at, since it cannot watch a video.

- every-Ns-NN.png: a frame every N seconds with its time, 12 to a screenshot sheet (4 x 3);
- by-beat-NN.png: the frame at the end of each beat with the line printed under it;
- text-visibility-check/<beat>.png: full-size frames, chosen by the automatic checks' text metrics;
- comment screenshot sheets: the frames around a comment's moment, drawn when the comment is made (see `feedback`).

Frames come from one decoding pass over the video, from the keyframe before the first one. Captions use a CJK-capable
font: Noto Sans TC when setup installed it, otherwise the system's CJK font.
"""

from __future__ import annotations

import functools
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFont

from .. import user_dirs
from .manim_runner import FPS

BACKGROUND_COLOR = (40, 40, 40)
TILE_BACKGROUND_COLOR = (24, 24, 24)
TILE_SPACING_PIXELS = 6
NO_LINE_START_CHARACTERS = set("，。、；：！？）」』》〉,.;:!?)")
COMMENT_SCREENSHOT_SHEET_MARK_COLOR = (255, 196, 0)
# A viewer usually marks a moment after the trouble started, so a comment screenshot sheet looks further back than
# ahead.
COMMENT_SCREENSHOT_SHEET_LOOKBACK_SECONDS = 8.0
COMMENT_SCREENSHOT_SHEET_LOOKAHEAD_SECONDS = 2.0
COMMENT_SCREENSHOT_SHEET_INTERVAL_SECONDS = 2.0


@dataclass(frozen=True)
class BeatScreenshot:
    beat_id: str
    time_seconds: float  # into the video
    text: str


def _list_font_candidates() -> list[Path]:
    home = Path.home()
    font_dir_paths = [user_dirs.get_data_dir_path() / "fonts", home / "Library" / "Fonts", Path("/Library/Fonts"),
                      home / ".local" / "share" / "fonts", home / ".fonts", Path("/usr/share/fonts"),
                      Path("/usr/local/share/fonts")]
    if os.name == "nt":
        font_dir_paths += [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
                           Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"]
    candidates = []
    for pattern in ("NotoSansTC*", "NotoSansCJK*", "NotoSansCJKtc*"):
        for font_dir_path in font_dir_paths:
            if font_dir_path.is_dir():
                candidates += sorted(font_dir_path.rglob(pattern))
    candidates += sorted(Path("/System/Library/AssetsV2").glob(
        "com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc"))
    candidates += [Path(path) for path in ("/System/Library/Fonts/PingFang.ttc",
                                           "/System/Library/Fonts/Hiragino Sans GB.ttc",
                                           "/System/Library/Fonts/STHeiti Medium.ttc",
                                           "/Library/Fonts/Arial Unicode.ttf", "C:/Windows/Fonts/msjh.ttc",
                                           "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")]
    return [path for path in candidates if path.is_file()]


@functools.cache
def find_caption_font_file_path() -> Path | None:
    candidates = _list_font_candidates()
    return candidates[0] if candidates else None


@functools.cache
def load_caption_font(size_pixels: int) -> ImageFont.ImageFont:
    font_file_path = find_caption_font_file_path()
    return (ImageFont.truetype(str(font_file_path), size_pixels) if font_file_path
            else ImageFont.load_default(size_pixels))


def grab_frames(video_file_path: Path, times_seconds: list[float]) -> dict[float, Image.Image]:
    """The frame shown at each time (seconds), from one decoding pass that starts at the keyframe before the first
    time, so frames late in a long video come quickly."""
    if not times_seconds:
        return {}
    container = av.open(str(video_file_path))
    try:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        frames_per_second = float(stream.average_rate or 30)
        start_pts = stream.start_time or 0
        # the times still waiting for their frame, in video order, each with the index of the frame shown then
        pending_times = sorted(times_seconds)
        frame_index_by_time_map = {time_seconds: max(0, round(time_seconds * frames_per_second))
                                   for time_seconds in pending_times}
        if pending_times[0] > 0 and stream.time_base:
            container.seek(start_pts + int(pending_times[0] / stream.time_base), stream=stream)
        image_by_time_map: dict[float, Image.Image] = {}
        previous_frame = None
        frame_index = -1
        for frame in container.decode(stream):
            frame_index = (round((frame.pts - start_pts) * stream.time_base * frames_per_second)
                           if frame.pts is not None and stream.time_base else frame_index + 1)
            image = None
            while pending_times and frame_index_by_time_map[pending_times[0]] <= frame_index:
                image = image or frame.to_image()
                image_by_time_map[pending_times.pop(0)] = image
            previous_frame = frame
            if not pending_times:
                break
        if previous_frame is not None and pending_times:  # times past the end show the last frame
            image_by_time_map.update(dict.fromkeys(pending_times, previous_frame.to_image()))
        return image_by_time_map
    finally:
        container.close()


def resolve_beat_screenshot_time(beat: dict, scene_duration_seconds: float) -> float:
    """When the beat's frame is taken: as its line ends, or when its animations finish if they run longer."""
    time_seconds = max(beat["start_seconds"] + beat["duration_seconds"], beat["check_time_seconds"]) - 1.0 / FPS
    return min(max(time_seconds, 0.0), max(scene_duration_seconds - 1.0 / FPS, 0.0))


def resolve_interval_times(duration_seconds: float, interval_seconds: float) -> list[float]:
    time_count = max(1, int(duration_seconds // interval_seconds)
                     + (1 if duration_seconds % interval_seconds > 0.5 else 0))
    return [min(i * interval_seconds, max(duration_seconds - 0.05, 0)) for i in range(time_count)]


def _format_clock_time(seconds: float) -> str:
    minutes, rest_seconds = divmod(seconds, 60)
    return f"{int(minutes)}:{rest_seconds:04.1f}"


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width_pixels: int) -> list[str]:
    """Break by width between words, where every CJK character counts as a word of its own."""
    tokens = re.findall(r"[\u2e80-\u9fff\uf900-\uffef]|[^\s\u2e80-\u9fff\uf900-\uffef]+|\s+", text)
    lines, line = [], ""
    for token in tokens:
        candidate = line + token
        # a closing mark never starts a line (kinsoku): it stays at the end of this one, a little over the width
        if (draw.textlength(candidate.rstrip(), font=font) > max_width_pixels and line.strip()
                and token not in NO_LINE_START_CHARACTERS):
            lines.append(line.rstrip())
            line = token.lstrip()
        else:
            line = candidate
    return [*lines, line.rstrip()] if line.strip() else lines


def _build_screenshot_sheet(tiles: list[Image.Image], column_count: int) -> Image.Image:
    rows = [tiles[row_start:row_start + column_count] for row_start in range(0, len(tiles), column_count)]
    tile_width_pixels = max(tile.width for tile in tiles)
    row_heights_pixels = [max(tile.height for tile in row) for row in rows]
    screenshot_sheet_width_pixels = column_count * (tile_width_pixels + TILE_SPACING_PIXELS) + TILE_SPACING_PIXELS
    screenshot_sheet_height_pixels = sum(row_heights_pixels) + TILE_SPACING_PIXELS * (len(rows) + 1)
    screenshot_sheet = Image.new("RGB", (screenshot_sheet_width_pixels, screenshot_sheet_height_pixels),
                                 BACKGROUND_COLOR)
    y = TILE_SPACING_PIXELS
    for row, row_height_pixels in zip(rows, row_heights_pixels, strict=True):
        for column, tile in enumerate(row):
            x = TILE_SPACING_PIXELS + column * (tile_width_pixels + TILE_SPACING_PIXELS)
            screenshot_sheet.paste(tile, (x, y))
        y += row_height_pixels + TILE_SPACING_PIXELS
    return screenshot_sheet


def _write_screenshot_sheets(tiles: list[Image.Image], output_dir_path: Path, file_prefix: str, column_count: int,
                             row_count: int) -> list[Path]:
    output_dir_path.mkdir(parents=True, exist_ok=True)
    tile_count_per_screenshot_sheet = column_count * row_count
    screenshot_sheet_file_paths = []
    for number, start in enumerate(range(0, len(tiles), tile_count_per_screenshot_sheet), start=1):
        screenshot_sheet_file_path = output_dir_path / f"{file_prefix}-{number:02d}.png"
        screenshot_sheet = _build_screenshot_sheet(tiles[start:start + tile_count_per_screenshot_sheet], column_count)
        screenshot_sheet.save(screenshot_sheet_file_path, optimize=False)
        screenshot_sheet_file_paths.append(screenshot_sheet_file_path)
    return screenshot_sheet_file_paths


def _build_time_tile(time_seconds: float, image: Image.Image, tile_width_pixels: int) -> Image.Image:
    """The frame scaled to `tile_width_pixels`, its time in the top-left corner."""
    font = load_caption_font(16)
    tile = image.convert("RGB").resize((tile_width_pixels, round(image.height * tile_width_pixels / image.width)),
                                       Image.LANCZOS)
    draw = ImageDraw.Draw(tile)
    label = _format_clock_time(time_seconds)
    box = draw.textbbox((6, 6), label, font=font)
    draw.rectangle((box[0] - 4, box[1] - 3, box[2] + 4, box[3] + 3), fill=(0, 0, 0))
    draw.text((6, 6), label, font=font, fill=(255, 255, 255))
    return tile


def write_interval_screenshot_sheets(frames: list[tuple[float, Image.Image]], output_dir_path: Path, file_prefix: str,
                                     column_count: int = 4, row_count: int = 3,
                                     tile_width_pixels: int = 480) -> list[Path]:
    """Frames at regular times, each labelled with its time."""
    tiles = [_build_time_tile(time_seconds, image, tile_width_pixels) for time_seconds, image in frames]
    return _write_screenshot_sheets(tiles, output_dir_path, file_prefix, column_count, row_count)


def resolve_comment_screenshot_sheet_times(comment_time_seconds: float,
                                           video_duration_seconds: float | None) -> list[float]:
    """Six times, every 2 s from 8 s before the comment to 2 s after it; near the start or end of the video the window
    moves inside it."""
    span_seconds = COMMENT_SCREENSHOT_SHEET_LOOKBACK_SECONDS + COMMENT_SCREENSHOT_SHEET_LOOKAHEAD_SECONDS
    start_seconds = max(comment_time_seconds - COMMENT_SCREENSHOT_SHEET_LOOKBACK_SECONDS, 0.0)
    if video_duration_seconds is not None:
        start_seconds = max(min(start_seconds, video_duration_seconds - 0.05 - span_seconds), 0.0)
    time_count = round(span_seconds / COMMENT_SCREENSHOT_SHEET_INTERVAL_SECONDS) + 1
    return [start_seconds + index * COMMENT_SCREENSHOT_SHEET_INTERVAL_SECONDS for index in range(time_count)]


def build_comment_screenshot_sheet_jpeg(frames: list[tuple[float, Image.Image]], comment_time_seconds: float,
                                        column_count: int = 3, tile_width_pixels: int = 480) -> bytes:
    """The frames around a comment, each labelled with its time; the one nearest the comment is outlined."""
    marked_index = min(range(len(frames)), key=lambda index: abs(frames[index][0] - comment_time_seconds))
    tiles = [_build_time_tile(time_seconds, image, tile_width_pixels) for time_seconds, image in frames]
    marked_tile = tiles[marked_index]
    ImageDraw.Draw(marked_tile).rectangle((0, 0, marked_tile.width - 1, marked_tile.height - 1),
                                          outline=COMMENT_SCREENSHOT_SHEET_MARK_COLOR, width=4)
    buffer = io.BytesIO()
    _build_screenshot_sheet(tiles, column_count).save(buffer, "JPEG", quality=80)
    return buffer.getvalue()


def write_beat_screenshot_sheets(beat_screenshots: list[tuple[BeatScreenshot, Image.Image]], output_dir_path: Path,
                                 file_prefix: str, column_count: int, row_count: int,
                                 tile_width_pixels: int) -> list[Path]:
    """The frame at the end of each beat, the beat id and time above the line printed under it."""
    scale_factor = tile_width_pixels / 420
    font, small_font = load_caption_font(round(17 * scale_factor)), load_caption_font(round(14 * scale_factor))
    line_height_pixels, padding_pixels = round(24 * scale_factor), round(8 * scale_factor)
    tiles = []
    for beat_screenshot, image in beat_screenshots:
        frame = image.convert("RGB").resize((tile_width_pixels, round(image.height * tile_width_pixels / image.width)),
                                            Image.LANCZOS)
        lines = _wrap_text(ImageDraw.Draw(frame), beat_screenshot.text, font, tile_width_pixels - 2 * padding_pixels)
        caption_height_pixels = line_height_pixels * len(lines) + round(22 * scale_factor) + 2 * padding_pixels
        tile = Image.new("RGB", (tile_width_pixels, frame.height + caption_height_pixels), TILE_BACKGROUND_COLOR)
        tile.paste(frame, (0, 0))
        draw = ImageDraw.Draw(tile)
        heading = f"{beat_screenshot.beat_id}  ({_format_clock_time(beat_screenshot.time_seconds)})"
        draw.text((padding_pixels, frame.height + padding_pixels), heading, font=small_font, fill=(150, 170, 200))
        for line_index, line in enumerate(lines):
            line_y = frame.height + padding_pixels + round(22 * scale_factor) + line_height_pixels * line_index
            draw.text((padding_pixels, line_y), line, font=font, fill=(235, 235, 235))
        tiles.append(tile)
    return _write_screenshot_sheets(tiles, output_dir_path, file_prefix, column_count, row_count)


def choose_text_visibility_beat_ids(metrics_by_beat_id_map: dict[str, dict], beat_count: int = 6) -> list[str]:
    """Beats whose end frames are most at risk for legibility: the smallest text and text closest to an edge; three of
    each, distinct, filled from the next candidates when they coincide."""
    text_metrics_by_beat_id_map = {beat_id: metrics for beat_id, metrics in metrics_by_beat_id_map.items()
                                   if metrics.get("min_font_size") is not None}
    rankings = [
        sorted(text_metrics_by_beat_id_map,
               key=lambda beat_id: text_metrics_by_beat_id_map[beat_id]["min_font_size"]),
        sorted((beat_id for beat_id, metrics in text_metrics_by_beat_id_map.items()
                if metrics.get("edge_distance") is not None),
               key=lambda beat_id: text_metrics_by_beat_id_map[beat_id]["edge_distance"]),
    ]
    chosen_beat_ids: list[str] = []
    count_per_ranking = max(1, beat_count // len(rankings))
    for ranking in rankings:
        taken_count = 0
        for beat_id in ranking:
            if taken_count == count_per_ranking:
                break
            if beat_id not in chosen_beat_ids:
                chosen_beat_ids.append(beat_id)
                taken_count += 1
    for beat_id in (ranked_beat_id for ranking in rankings for ranked_beat_id in ranking):
        if len(chosen_beat_ids) >= beat_count:
            break
        if beat_id not in chosen_beat_ids:
            chosen_beat_ids.append(beat_id)
    return chosen_beat_ids[:beat_count]
