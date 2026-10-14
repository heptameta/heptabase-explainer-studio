"""Smoke tests against the live services the asset commands use; they catch a changed API. Run with -m network."""

from __future__ import annotations

from pathlib import Path

import pytest

from explainer_studio.assets import bioicons, commons, owid, wikipedia, worldbank
from explainer_studio.assets.common import check_is_free
from explainer_studio.errors import StudioError
from explainer_studio.paths import Series

pytestmark = pytest.mark.network


@pytest.fixture
def series(tmp_path: Path) -> Series:
    (tmp_path / "production").mkdir()
    (tmp_path / "production" / "plan.yaml").write_text("title: x\n", encoding="utf-8")
    return Series(tmp_path)


def test_commons_search_returns_free_pictures_with_thumbnails() -> None:
    found_files = commons.search("Mona Lisa", None, limit=5)
    assert found_files and all(check_is_free(commons_file.license) and commons_file.thumbnail_url
                               for commons_file in found_files)


def test_commons_cuts_a_video_clip(series: Series) -> None:
    path, _, _ = commons.download_file(series, "File:Movie 1. Heart beating.ogv", None, 2, 4, lambda _: None)
    assert path.suffix == ".mp4" and path.stat().st_size > 10_000


def test_bioicons_search_finds_icons() -> None:
    assert any("mitochond" in icon.name for icon in bioicons.search("mitochondria"))


def test_portraits_are_public_domain_only(series: Series) -> None:
    path, license, _ = wikipedia.download_portrait(series, "Marie Curie", None, None)
    assert path.exists() and "public domain" in license.lower()
    with pytest.raises(StudioError, match="not public domain"):
        wikipedia.download_portrait(series, "Taylor Swift", None, None)


def test_data_downloads_filter_entities_and_years(series: Series) -> None:
    _, rows, _ = owid.download_chart(series, "life-expectancy", ["JPN"], (2000, 2001), None)
    assert {(row["code"], row["year"]) for row in rows} == {("JPN", "2000"), ("JPN", "2001")}
    _, rows, _ = worldbank.download_indicator(series, "SP.DYN.LE00.IN", ["JPN"], (2000, 2001), None)
    assert {(row["code"], row["year"]) for row in rows} == {("JPN", "2000"), ("JPN", "2001")}
