"""Bioicons: about 2,800 free science icons (cells, organelles, organs, lab apparatus, molecules) as SVG."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from .. import user_dirs
from ..errors import StudioError
from ..paths import Series
from .common import check_is_free, choose_output_file_path, create_viewing_dir, sanitize_file_stem, write_asset_bytes
from .credits import record_credit
from .fetch import fetch_response
from .thumbnail_sheet import draw_svg_thumbnail, draw_thumbnail_sheet

INDEX_URL = "https://bioicons.com/icons/icons.json"
ICON_URL_TEMPLATE = "https://bioicons.com/icons/{license}/{category}/{author}/{name}.svg"
INDEX_MAX_AGE_SECONDS = 7 * 86400
LICENSE_URL_BY_CODE_MAP = {
    "cc-0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "cc-by-3.0": "https://creativecommons.org/licenses/by/3.0/",
    "cc-by-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "cc-by-sa-3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "cc-by-sa-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "mit": "https://opensource.org/license/mit",
    "bsd": "https://opensource.org/license/bsd-3-clause",
}


@dataclass
class Icon:
    name: str
    category: str
    license_code: str
    author: str

    @property
    def license(self) -> str:
        license_code = self.license_code.lower()
        if license_code == "cc-0":
            return "CC0"
        return license_code.upper().replace("CC-BY-SA-", "CC BY-SA ").replace("CC-BY-", "CC BY ")

    @property
    def url(self) -> str:
        return ICON_URL_TEMPLATE.format(license=quote(self.license_code), category=quote(self.category),
                                        author=quote(self.author), name=quote(self.name))


def fetch_icon_index() -> list[Icon]:
    """The icon list, cached for a week in the user cache folder."""
    cache_file_path = user_dirs.get_cache_dir_path() / "bioicons.json"
    if not cache_file_path.exists() or time.time() - cache_file_path.stat().st_mtime > INDEX_MAX_AGE_SECONDS:
        write_asset_bytes(cache_file_path, fetch_response(INDEX_URL).content)
    raw_icons = json.loads(cache_file_path.read_text(encoding="utf-8"))
    return [Icon(raw_icon["name"], raw_icon["category"], raw_icon["license"], raw_icon["author"])
            for raw_icon in raw_icons]


def _split_words(text: str) -> list[str]:
    return [word for word in re.split(r"[\s_\-]+", text.lower()) if word]


def search(query: str, limit: int = 12) -> list[Icon]:
    # stems, so "mitochondria" also finds "mitochondrion"
    stems = [word[: max(4, len(word) - 2)] for word in _split_words(query)]
    scored = []
    for icon in fetch_icon_index():
        if not check_is_free(icon.license, should_accept_code_licenses=True):
            continue
        haystack = " ".join(_split_words(f"{icon.name} {icon.category}"))
        score = sum(stem in haystack for stem in stems)
        if score:
            scored.append((-score, len(icon.name), icon.name, icon))
    return [icon for *_, icon in sorted(scored, key=lambda scored_icon: scored_icon[:3])[:limit]]


def draw_search_result_thumbnail_sheet(icons: list[Icon]) -> Path | None:
    if not icons:
        return None
    cells = []
    for number, icon in enumerate(icons, start=1):
        try:
            thumbnail = draw_svg_thumbnail(fetch_response(icon.url, timeout_seconds=30).content, 200)
        except StudioError:
            thumbnail = None
        cells.append((thumbnail, f"{number}  {icon.license}"))
    return draw_thumbnail_sheet(cells, create_viewing_dir("bioicons") / "candidates.png")


def find_icon(name_or_url: str) -> Icon:
    value = name_or_url.strip()
    if value.startswith(("http://", "https://")):
        value = Path(unquote(urlparse(value).path)).stem
    icons = fetch_icon_index()
    exact_matches = ([icon for icon in icons if icon.name == value]
                     or [icon for icon in icons if icon.name.lower() == value.lower()])
    if not exact_matches:
        raise StudioError(f"no Bioicons icon named {value!r}", "download takes the exact name a search printed",
                          f"run `explainer-studio asset bioicons search \"{value}\"`")
    return exact_matches[0]


def download_icon(series: Series, name_or_url: str, destination_path: Path | None) -> tuple[Path, Icon]:
    icon = find_icon(name_or_url)
    target_file_path = choose_output_file_path(series, "icons", f"{sanitize_file_stem(icon.name)}.svg",
                                               destination_path)
    write_asset_bytes(target_file_path, fetch_response(icon.url).content)
    title = f"{icon.name.replace('_', ' ')} (Bioicons, {icon.category.replace('_', ' ')})"
    record_credit(series, target_file_path, title, icon.author.replace("_", " "), icon.license, icon.url,
                  LICENSE_URL_BY_CODE_MAP.get(icon.license_code.lower(), ""))
    return target_file_path, icon
