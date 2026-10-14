"""Wikimedia Commons: paintings, photographs, historical documents, scientific diagrams, footage, recordings and 3D
models, searched by keyword and downloaded by file name or URL."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

from ..errors import StudioError
from ..paths import Series
from .common import (
    check_is_free,
    choose_output_file_path,
    convert_html_to_plain_text,
    create_viewing_dir,
    cut_remote_clip,
    sanitize_file_stem,
    write_asset_bytes,
)
from .credits import record_credit
from .fetch import USER_AGENT, download, fetch_json, fetch_response
from .thumbnail_sheet import draw_placeholder_thumbnail, draw_thumbnail_sheet

API_URL = "https://commons.wikimedia.org/w/api.php"
SEARCH_FILTER_BY_MEDIA_TYPE_MAP = {"photo": "bitmap", "svg": "drawing", "video": "video", "audio": "audio", "3d": "3d"}
IMAGE_MEDIA_TYPES = ("BITMAP", "DRAWING")
FOLDER_NAME_BY_MEDIA_TYPE_MAP = {"BITMAP": "images", "DRAWING": "images", "VIDEO": "video", "AUDIO": "audio",
                                 "3D": "3d"}
# larger originals come as a scaled copy; Commons serves only standard widths (330, 500, 960, 1280, 1920, 3840)
MAX_IMAGE_WIDTH_PIXELS = 1920
MAX_CLIP_SECONDS = 120
MAX_VIDEO_HEIGHT_PIXELS = 720
METADATA_FILTER = "LicenseShortName|LicenseUrl|Artist|Credit|ObjectName|ImageDescription"


@dataclass
class CommonsFile:
    title: str
    url: str
    page_url: str
    mime_type: str
    media_type: str
    width_pixels: int
    height_pixels: int
    duration_seconds: float | None
    license: str
    license_url: str
    author: str
    object_name: str
    thumbnail_url: str | None

    @property
    def summary(self) -> str:
        size = f"{self.width_pixels}x{self.height_pixels}" if self.width_pixels else ""
        length = f"{self.duration_seconds:.0f} s" if self.duration_seconds else ""
        return " | ".join(part for part in (self.license, f"by {self.author}" if self.author else "", size, length,
                                            self.mime_type) if part)


def _parse_commons_file(page: dict) -> CommonsFile | None:
    image_info = (page.get("imageinfo") or [None])[0]
    if image_info is None:
        return None
    metadata_by_name_map = {key: convert_html_to_plain_text(value.get("value"))
                            for key, value in (image_info.get("extmetadata") or {}).items()}
    return CommonsFile(
        title=page["title"], url=image_info.get("url", ""), page_url=image_info.get("descriptionurl", ""),
        mime_type=image_info.get("mime", ""), media_type=image_info.get("mediatype", ""),
        width_pixels=image_info.get("width") or 0, height_pixels=image_info.get("height") or 0,
        duration_seconds=image_info.get("duration"), license=metadata_by_name_map.get("LicenseShortName", ""),
        license_url=metadata_by_name_map.get("LicenseUrl", ""),
        author=(metadata_by_name_map.get("Artist") or metadata_by_name_map.get("Credit", ""))[:200],
        object_name=metadata_by_name_map.get("ObjectName", ""), thumbnail_url=image_info.get("thumburl"))


def search(query: str, media_type: str | None, limit: int = 12) -> list[CommonsFile]:
    """Free-licence files matching `query`; without `media_type`, pictures (photographs, paintings and drawings)."""
    search_text = f"{query} filetype:{SEARCH_FILTER_BY_MEDIA_TYPE_MAP[media_type]}" if media_type else query
    response = fetch_json(API_URL, {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                    "gsrsearch": search_text, "gsrlimit": 50, "prop": "imageinfo",
                                    "iiprop": "url|size|mime|mediatype|extmetadata", "iiurlwidth": 320,
                                    "iiextmetadatafilter": METADATA_FILTER, "iiextmetadatalanguage": "en"})
    pages = sorted(response.get("query", {}).get("pages", {}).values(), key=lambda page: page.get("index", 0))
    found_files = []
    for page in pages:
        commons_file = _parse_commons_file(page)
        if commons_file is None or not check_is_free(commons_file.license):
            continue
        if media_type is None and commons_file.media_type not in IMAGE_MEDIA_TYPES:
            continue
        found_files.append(commons_file)
        if len(found_files) >= limit:
            break
    return found_files


def draw_search_result_thumbnail_sheet(files: list[CommonsFile]) -> Path | None:
    if not files:
        return None
    cells = []
    for number, commons_file in enumerate(files, start=1):
        thumbnail = None
        if commons_file.media_type == "AUDIO":
            thumbnail = draw_placeholder_thumbnail(f"audio\n{commons_file.duration_seconds or 0:.0f} s")
        elif commons_file.thumbnail_url:
            try:
                response = fetch_response(commons_file.thumbnail_url, timeout_seconds=30)
                thumbnail = Image.open(io.BytesIO(response.content))
                thumbnail.load()
            except (StudioError, OSError):
                thumbnail = None
        cells.append((thumbnail, f"{number}  {commons_file.license}"))
    return draw_thumbnail_sheet(cells, create_viewing_dir("commons") / "candidates.png")


def resolve_file_title(name_or_url: str) -> str:
    """'File:X.jpg' from a file name, a Commons page URL or an upload.wikimedia.org URL."""
    value = name_or_url.strip()
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        path = unquote(parsed.path)
        if "/wiki/" in path:
            value = path.split("/wiki/", 1)[1]
        else:
            parts = [part for part in path.split("/") if part]
            # thumbnails look like .../thumb/a/ab/Name.jpg/320px-Name.jpg; the original name is the folder
            value = parts[-2] if "thumb" in parts and len(parts) >= 2 else parts[-1]
    value = value.replace("_", " ")
    if not value.lower().startswith("file:"):
        value = f"File:{value}"
    return "File:" + value.split(":", 1)[1].strip()


def fetch_commons_file(title: str, thumbnail_width_pixels: int = MAX_IMAGE_WIDTH_PIXELS) -> tuple[CommonsFile, dict]:
    """The file's details, with `thumbnail_url` scaled to `thumbnail_width_pixels`."""
    response = fetch_json(API_URL, {"action": "query", "format": "json", "titles": title, "redirects": 1,
                                    "prop": "imageinfo|videoinfo", "iiprop": "url|size|mime|mediatype|extmetadata",
                                    "iiurlwidth": thumbnail_width_pixels, "iiextmetadatafilter": METADATA_FILTER,
                                    "iiextmetadatalanguage": "en", "viprop": "derivatives"})
    page = next(iter(response.get("query", {}).get("pages", {}).values()), {})
    commons_file = _parse_commons_file(page) if "missing" not in page else None
    if commons_file is None:
        raise StudioError(f"{title} is not on Wikimedia Commons", "the API found no such file",
                          "copy the exact file name from `explainer-studio asset commons search`")
    return commons_file, page


def _choose_video_source_url(page: dict, commons_file: CommonsFile) -> str:
    """The best transcode no taller than 720p: originals can be hundreds of megabytes."""
    derivatives = (page.get("videoinfo") or [{}])[0].get("derivatives") or []
    usable_derivatives = [derivative for derivative in derivatives
                          if 0 < (derivative.get("height") or 0) <= MAX_VIDEO_HEIGHT_PIXELS]
    if not usable_derivatives:
        return commons_file.url
    return max(usable_derivatives, key=lambda derivative: (derivative.get("height") or 0,
                                                           "vp9" in (derivative.get("transcodekey") or "")))["src"]


def download_file(series: Series, name_or_url: str, destination_path: Path | None, start_seconds: float | None,
                  end_seconds: float | None, report_progress) -> tuple[Path, str, list[str]]:
    """Download one Commons file and record its credit. Returns (path, licence, warnings)."""
    commons_file, page = fetch_commons_file(resolve_file_title(name_or_url))
    folder_name = FOLDER_NAME_BY_MEDIA_TYPE_MAP.get(commons_file.media_type, "files")
    stem = sanitize_file_stem(Path(commons_file.title.split(":", 1)[1]).stem)
    original_suffix = Path(commons_file.title).suffix.lower()
    warnings = []
    if not check_is_free(commons_file.license):
        warnings.append(f"{commons_file.title} is under {commons_file.license or 'an unknown licence'}, not a free "
                        "licence; check it before using it in a video")
    if commons_file.media_type == "VIDEO":
        if start_seconds is None or end_seconds is None:
            raise StudioError("a video needs --start and --end",
                              f"{commons_file.title} runs {commons_file.duration_seconds or 0:.0f} s; only the part "
                              "the video shows is fetched", "add --start and --end in seconds")
        target_file_path = choose_output_file_path(series, folder_name, f"{stem}.mp4", destination_path)
        _validate_clip_range(start_seconds, end_seconds, commons_file.duration_seconds)
        report_progress(f"cutting {end_seconds - start_seconds:g} s of {commons_file.title}")
        cut_remote_clip(_choose_video_source_url(page, commons_file), start_seconds, end_seconds, target_file_path,
                        ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                         "-vf", f"scale=-2:'min({MAX_VIDEO_HEIGHT_PIXELS},ih)'", "-c:a", "aac", "-b:a", "160k",
                         "-movflags", "+faststart"], USER_AGENT, report_progress)
    elif commons_file.media_type == "AUDIO" and (start_seconds is not None or end_seconds is not None
                                                 or (commons_file.duration_seconds or 0) > MAX_CLIP_SECONDS):
        if start_seconds is None or end_seconds is None:
            raise StudioError("this recording needs --start and --end",
                              f"{commons_file.title} runs {commons_file.duration_seconds or 0:.0f} s, longer than the "
                              f"{MAX_CLIP_SECONDS} s a clip may be", "add --start and --end")
        _validate_clip_range(start_seconds, end_seconds, commons_file.duration_seconds)
        target_file_path = choose_output_file_path(series, folder_name, f"{stem}.flac", destination_path)
        report_progress(f"cutting {end_seconds - start_seconds:g} s of {commons_file.title}")
        cut_remote_clip(commons_file.url, start_seconds, end_seconds, target_file_path, ["-vn", "-c:a", "flac"],
                        USER_AGENT, report_progress)
    elif commons_file.media_type in IMAGE_MEDIA_TYPES and commons_file.mime_type != "image/svg+xml":
        is_scaled = commons_file.width_pixels > MAX_IMAGE_WIDTH_PIXELS and commons_file.thumbnail_url
        url = commons_file.thumbnail_url if is_scaled else commons_file.url
        suffix = Path(urlparse(url).path).suffix.lower() or original_suffix
        is_tiff = suffix in (".tif", ".tiff")
        target_file_path = choose_output_file_path(series, folder_name, f"{stem}{'.jpg' if is_tiff else suffix}",
                                                   destination_path)
        report_progress(f"downloading {commons_file.title}")
        image_bytes = fetch_response(url, timeout_seconds=300, report_progress=report_progress).content
        if is_tiff:  # ManimGL and browsers cannot show TIFF
            converted = io.BytesIO()
            Image.open(io.BytesIO(image_bytes)).convert("RGB").save(converted, "JPEG", quality=92)
            image_bytes = converted.getvalue()
        write_asset_bytes(target_file_path, image_bytes)
    else:
        target_file_path = choose_output_file_path(series, folder_name, f"{stem}{original_suffix}", destination_path)
        report_progress(f"downloading {commons_file.title}")
        download(commons_file.url, target_file_path, report_progress, commons_file.title)
        target_file_path.chmod(0o644)
    credit_title = commons_file.object_name or Path(commons_file.title.split(":", 1)[1]).stem
    record_credit(series, target_file_path, credit_title, commons_file.author, commons_file.license,
                  commons_file.page_url, commons_file.license_url)
    return target_file_path, commons_file.license, warnings


def _validate_clip_range(start_seconds: float, end_seconds: float, duration_seconds: float | None) -> None:
    if end_seconds <= start_seconds or start_seconds < 0:
        raise StudioError("--end must come after --start", f"got {start_seconds:g} to {end_seconds:g} s",
                          "fix the times")
    if end_seconds - start_seconds > MAX_CLIP_SECONDS:
        raise StudioError(f"clips are limited to {MAX_CLIP_SECONDS} s", f"asked for {end_seconds - start_seconds:g} s",
                          "fetch only the stretch the video shows")
    if duration_seconds and start_seconds >= duration_seconds:
        raise StudioError("--start is past the end of the file", f"the file runs {duration_seconds:.0f} s",
                          "fix the times")
