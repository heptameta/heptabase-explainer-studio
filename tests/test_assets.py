"""The asset commands' offline logic: licences, file names, credits, data filters, PDF crops, SVG thumbnails and
checked downloads."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest
from PIL import Image

from explainer_studio.assets import fetch
from explainer_studio.assets.common import check_is_free, check_is_public_domain, choose_output_file_path, keep_rows
from explainer_studio.assets.commons import resolve_file_title
from explainer_studio.assets.credits import record_credit
from explainer_studio.assets.pdf import crop, parse_box
from explainer_studio.assets.thumbnail_sheet import draw_svg_thumbnail
from explainer_studio.errors import StudioError
from explainer_studio.file_io import load_yaml_model
from explainer_studio.paths import Series
from explainer_studio.schemas.credits import Credits


@pytest.fixture
def series(tmp_path: Path) -> Series:
    (tmp_path / "production").mkdir()
    (tmp_path / "production" / "plan.yaml").write_text("title: x\n", encoding="utf-8")
    return Series(tmp_path)


@pytest.mark.parametrize(("license", "is_free", "is_public_domain"), [
    ("Public domain", True, True), ("PD-old-100", True, True), ("CC0", True, True), ("cc-0", True, True),
    ("CC BY 4.0", True, False), ("CC BY-SA 3.0", True, False), ("cc-by-sa-4.0", True, False),
    ("CC BY-NC 4.0", False, False), ("CC BY-NC-SA 2.0", False, False), ("CC BY-ND 4.0", False, False),
    ("GFDL", False, False), ("Fair use", False, False), ("", False, False),
])
def test_licenses(license: str, is_free: bool, is_public_domain: bool) -> None:
    assert check_is_free(license) is is_free
    assert check_is_public_domain(license) is is_public_domain


def test_code_licenses_count_only_for_icons() -> None:
    assert (not check_is_free("MIT") and check_is_free("MIT", should_accept_code_licenses=True)
            and check_is_free("BSD", should_accept_code_licenses=True))


@pytest.mark.parametrize("name_or_url", [
    "File:Mona Lisa.jpg", "Mona_Lisa.jpg", "file:Mona_Lisa.jpg",
    "https://commons.wikimedia.org/wiki/File:Mona_Lisa.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6a/Mona_Lisa.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Mona_Lisa.jpg/330px-Mona_Lisa.jpg",
])
def test_commons_file_names_and_urls_resolve_to_one_title(name_or_url: str) -> None:
    assert resolve_file_title(name_or_url) == "File:Mona Lisa.jpg"


def test_to_is_a_folder_or_a_file(series: Series, tmp_path: Path) -> None:
    assert (choose_output_file_path(series, "images", "a.jpg", None)
            == series.shared_assets_dir_path / "images" / "a.jpg")
    assert choose_output_file_path(series, "images", "a.jpg", tmp_path / "ep01") == tmp_path / "ep01" / "a.jpg"
    assert choose_output_file_path(series, "images", "a.jpg", tmp_path / "b.png") == tmp_path / "b.png"


def test_downloading_a_file_again_replaces_its_credit_and_keeps_hand_written_entries(series: Series) -> None:
    series.credits_file_path.write_text("# credits\ncredits:\n"
                                        "  - asset_file_path: shared/assets/images/own.png  # drawn by us\n"
                                        "    title: Ours\n    license: CC0\n    source_url: ''\n"
                                        "    downloaded_at: 2026-10-06T15:02:11+01:00\n", encoding="utf-8")
    target = series.shared_assets_dir_path / "images" / "mona.jpg"
    record_credit(series, target, "Mona Lisa", "Leonardo", "Public domain", "https://a")
    record_credit(series, target, "Mona Lisa", "Leonardo da Vinci", "Public domain", "https://b")
    text = series.credits_file_path.read_text(encoding="utf-8")
    assert text.count("asset_file_path: shared/assets/images/mona.jpg") == 1 and "https://b" in text
    assert "# drawn by us" in text
    credits = load_yaml_model(Credits, series.credits_file_path).credits
    assert [credit.asset_file_path for credit in credits] == ["shared/assets/images/own.png",
                                                          "shared/assets/images/mona.jpg"]


def test_data_rows_are_kept_by_entity_name_or_code_and_year() -> None:
    rows = [{"entity": "Japan", "code": "JPN", "year": "1990"}, {"entity": "Japan", "code": "JPN", "year": "2020"},
            {"entity": "France", "code": "FRA", "year": "2020"}, {"entity": "World", "code": "", "year": "2020"}]
    kept_rows = keep_rows(rows, ["jpn", "world"], (2000, 2030))
    assert [(row["entity"], row["year"]) for row in kept_rows] == [("Japan", "2020"), ("World", "2020")]


def test_pdf_crop_cuts_the_box_given_in_page_fractions(series: Series, tmp_path: Path) -> None:
    pdf_file_path = tmp_path / "source.pdf"
    Image.new("RGB", (720, 1080), "white").save(pdf_file_path, resolution=72)
    crop_file_path = crop(series, pdf_file_path, 1, parse_box("0.5,0,1,0.25"), None, dpi=72)
    assert crop_file_path == series.shared_assets_dir_path / "figures" / "source-p001-crop.png"
    assert Image.open(crop_file_path).size == (360, 270)
    with pytest.raises(StudioError):
        parse_box("0.6,0,0.5,1")


def test_svg_thumbnails_fill_shapes_and_keep_holes() -> None:
    svg_bytes = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill="#ff0000" '
                 b'fill-rule="evenodd" d="M0 0H100V100H0Z M40 40H60V60H40Z"/></svg>')
    image = draw_svg_thumbnail(svg_bytes, 100)
    assert image is not None
    corner, center = image.getpixel((10, 10)), image.getpixel((50, 50))
    assert corner[0] > 200 and corner[3] > 200 and center[3] == 0


def test_a_download_that_is_not_the_expected_file_is_deleted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"a program"
    monkeypatch.setattr(fetch, "create_client", lambda timeout_seconds: httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))))
    target_file_path = tmp_path / "ffmpeg.gz"
    with pytest.raises(StudioError, match="not the file Explainer Studio expects"):
        fetch.download("https://example.com/ffmpeg.gz", target_file_path, expected_sha256="0" * 64)
    assert list(tmp_path.iterdir()) == []
    fetch.download("https://example.com/ffmpeg.gz", target_file_path,
                   expected_sha256=hashlib.sha256(content).hexdigest())
    assert target_file_path.read_bytes() == content
