"""Portraits: a Wikipedia article's lead image, kept only when Commons says it is public domain or CC0."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from ..errors import StudioError
from ..paths import Series
from .common import check_is_public_domain, choose_output_file_path, sanitize_file_stem, write_asset_bytes
from .commons import fetch_commons_file
from .credits import record_credit
from .fetch import fetch_json, fetch_response

PORTRAIT_WIDTH_PIXELS = 960  # a standard Commons thumbnail width
CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def resolve_wiki_language_code(article_title: str, language_code: str | None) -> str:
    if language_code:
        return language_code.lower()
    return "zh" if CJK_PATTERN.search(article_title) else "en"


def fetch_lead_image_name(article_title: str, language_code: str) -> tuple[str, str]:
    """(the article's resolved title, its lead image file name)."""
    response = fetch_json(f"https://{language_code}.wikipedia.org/w/api.php",
                          {"action": "query", "format": "json", "titles": article_title, "redirects": 1,
                           "prop": "pageimages", "piprop": "name"})
    page = next(iter(response.get("query", {}).get("pages", {}).values()), {})
    if "missing" in page or not page:
        raise StudioError(f"no {language_code}.wikipedia.org article named {article_title!r}",
                          "the title did not resolve",
                          "use the exact article title (or pass --language for another Wikipedia)")
    if "pageimage" not in page:
        raise StudioError(f"the article {page.get('title', article_title)} has no lead image", "Wikipedia lists none",
                          "use a silhouette with a name tag, or look for a portrait with `asset commons search`")
    return page.get("title", article_title), page["pageimage"]


def download_portrait(series: Series, article_title: str, destination_path: Path | None,
                      language_code: str | None) -> tuple[Path, str, str]:
    """Download the portrait; returns (path, licence, author)."""
    wiki_language_code = resolve_wiki_language_code(article_title, language_code)
    title, image_name = fetch_lead_image_name(article_title, wiki_language_code)
    try:
        commons_file, _ = fetch_commons_file(f"File:{image_name}", PORTRAIT_WIDTH_PIXELS)
    except StudioError:
        raise StudioError(f"the portrait of {title} is not on Wikimedia Commons",
                          "it is a local, usually non-free, upload to Wikipedia",
                          "use a silhouette with a name tag, or look for another portrait with `asset commons "
                          "search`") from None
    if not check_is_public_domain(commons_file.license):
        license = commons_file.license or "of an unknown licence"
        raise StudioError(f"the portrait of {title} is not public domain", f"{commons_file.title} is {license}",
                          "use a silhouette with a name tag, or look for a public-domain portrait with `asset commons "
                          "search`")
    original_suffix = Path(commons_file.url).suffix.lower()
    # a scaled copy when the original is large or not a JPEG or PNG (TIFF, SVG); Commons serves those as JPEG/PNG
    should_use_scaled_copy = commons_file.thumbnail_url and (commons_file.width_pixels > PORTRAIT_WIDTH_PIXELS
                                                             or original_suffix not in (".jpg", ".jpeg", ".png"))
    url = commons_file.thumbnail_url if should_use_scaled_copy else commons_file.url
    suffix = Path(urlparse(url).path).suffix.lower()
    file_name = f"{sanitize_file_stem(title)}{'.png' if suffix == '.png' else '.jpg'}"
    target_file_path = choose_output_file_path(series, "portraits", file_name, destination_path)
    write_asset_bytes(target_file_path, fetch_response(url, timeout_seconds=120).content)
    record_credit(series, target_file_path, f"{title} ({commons_file.title.removeprefix('File:')})",
                  commons_file.author, commons_file.license, commons_file.page_url, commons_file.license_url)
    return target_file_path, commons_file.license, commons_file.author
