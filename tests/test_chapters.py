from __future__ import annotations

import copy
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from delivered_series import NOTES, create_series, write_delivery_record, write_notes, write_render
from PIL import Image

from explainer_studio import user_dirs
from explainer_studio.chapters import check_notes, find_frame_file_path, find_frame_time_seconds
from explainer_studio.deliver import deliver, load_delivered_timeline
from explainer_studio.errors import StudioError
from explainer_studio.web.pages import compute_video_page

# every test here delivers the fake render, which ffmpeg makes
pytestmark = pytest.mark.render


def deliver_with_notes(tmp_path: Path, notes: dict) -> object:
    series = create_series(tmp_path / "series")
    write_delivery_record(series, datetime.now(UTC) - timedelta(minutes=5))
    shutil.copy(series.get_episode_paths("ep01").render_video_file_path, series.root_dir_path / "01-v.mp4")
    write_notes(series, notes)
    return series


def test_the_video_page_has_chapters_when_the_notes_fit_the_delivered_video(tmp_path: Path) -> None:
    series = deliver_with_notes(tmp_path, NOTES)
    assert check_notes(series, "ep01") == []
    chapters = compute_video_page(series, "ep01")["chapters"]
    assert [chapter["title"] for chapter in chapters] == ["兩次移動等於一支箭頭", "首尾相接就是加法"]
    hook = chapters[0]["scenes"][0]
    assert (hook["keyFrame"], hook["startSeconds"], hook["endSeconds"]) == ("one_arrow", 1.0, 7.0)


def test_notes_that_skip_a_scene_or_name_a_missing_beat_show_no_chapters(tmp_path: Path) -> None:
    notes = copy.deepcopy(NOTES)
    notes["chapters"] = notes["chapters"][:1]
    hook = notes["chapters"][0]["scenes"][0]
    hook["key_frame"] = "no_such_beat"
    hook["cards"][0]["leads_to"] = ["no_such_card"]
    series = deliver_with_notes(tmp_path, notes)
    problems = check_notes(series, "ep01")
    assert any("the chapters hold hook" in problem for problem in problems)
    assert any("key_frame no_such_beat" in problem for problem in problems)
    assert any("leads_to no_such_card" in problem for problem in problems)
    assert compute_video_page(series, "ep01")["chapters"] is None


def test_a_cards_pictures_must_be_frames_credited_assets_or_its_own_card_images(tmp_path: Path) -> None:
    notes = copy.deepcopy(NOTES)
    card = notes["chapters"][0]["scenes"][0]["cards"][0]
    card["content"] += ("![](frame:no_such_beat)\n![](assets/not_credited.png)\n"
                        "![](episodes/ep01/card-images/drawn.png)\n![](episodes/ep01/card-images/icon.svg)\n")
    series = deliver_with_notes(tmp_path, notes)
    (series.production_dir_path / "assets").mkdir()
    Image.new("RGB", (4, 4)).save(series.production_dir_path / "assets" / "not_credited.png")
    card_images_dir_path = series.get_episode_paths("ep01").root_dir_path / "card-images"
    card_images_dir_path.mkdir()
    Image.new("RGB", (4, 4)).save(card_images_dir_path / "drawn.png")
    (card_images_dir_path / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    problems = check_notes(series, "ep01")
    assert any("frame:no_such_beat is not a beat" in problem for problem in problems)
    assert any("assets/not_credited.png is neither in credits.yaml" in problem for problem in problems)
    assert any("icon.svg: icon.svg is not a PNG, JPEG, WebP or GIF image" in problem for problem in problems)
    assert not any("drawn.png" in problem for problem in problems)


def test_markdown_highlights_are_reported_but_equality_in_code_is_not(tmp_path: Path) -> None:
    notes = copy.deepcopy(NOTES)
    cards = notes["chapters"][0]["scenes"][0]["cards"]
    cards[0]["content"] += "\n1. `a == b` holds when `c == d`, and x == y in prose.\n"
    series = deliver_with_notes(tmp_path, notes)
    assert check_notes(series, "ep01") == []
    cards[0]["content"] += "1. ==the key phrase==\n"
    write_notes(series, notes)
    assert any("==…== is not Hepta Markdown" in problem for problem in check_notes(series, "ep01"))


def test_a_beats_frame_is_taken_when_its_line_ends_and_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_dirs, "get_cache_dir_path", lambda: tmp_path / "cache")
    series = deliver_with_notes(tmp_path, NOTES)
    record_dir_path = max(series.get_episode_paths("ep01").delivery_records_dir_path.iterdir())
    timeline = load_delivered_timeline(series, record_dir_path)
    assert find_frame_time_seconds(timeline, "one_arrow") == pytest.approx(6.9)
    frame_file_path = find_frame_file_path(series, "ep01", "one_arrow")
    assert frame_file_path is not None and Image.open(frame_file_path).format == "JPEG"
    assert find_frame_file_path(series, "ep01", "one_arrow") == frame_file_path
    assert find_frame_file_path(series, "ep01", "no_such_beat") is None


def test_an_arrow_from_another_episode_must_name_a_card_of_an_earlier_episode(tmp_path: Path) -> None:
    notes = copy.deepcopy(NOTES)
    notes["chapters"][0]["scenes"][0]["cards"][0]["continues_from"] = ["ep02/moves_add"]
    series = deliver_with_notes(tmp_path, notes)
    series.get_episode_paths("ep02").notes_file_path.parent.mkdir(parents=True, exist_ok=True)
    write_notes(series, NOTES, "ep02")
    assert any("continues_from ep02/moves_add is not a card of an earlier episode's" in problem
               for problem in check_notes(series, "ep01"))


def test_deliver_refuses_an_episode_without_cards_that_fit_its_render(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    notes_file_path = series.get_episode_paths("ep01").notes_file_path
    notes_file_path.unlink()
    with pytest.raises(StudioError, match="cannot be delivered yet") as error:
        deliver(series, "ep01")
    assert any("notes.yaml is missing" in detail for detail in error.value.details)
    write_render(series)
    assert any("notes.yaml is missing" in problem for problem in check_notes(series, "ep01"))
