from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from delivered_series import NOTES, create_series, write_delivery_record, write_render
from PIL import Image
from pydantic import ValidationError

from explainer_studio import user_dirs
from explainer_studio.chapters import check_notes, find_frame_file_path, find_frame_time_seconds
from explainer_studio.deliver import deliver, load_delivered_timeline
from explainer_studio.errors import StudioError
from explainer_studio.schemas.notes import Card, Point
from explainer_studio.web.pages import compute_video_page


def deliver_with_notes(tmp_path: Path, notes: dict) -> object:
    series = create_series(tmp_path / "series")
    write_delivery_record(series, datetime.now(UTC) - timedelta(minutes=5))
    shutil.copy(series.get_episode_paths("ep01").render_video_file_path, series.root_dir_path / "01-v.mp4")
    series.get_episode_paths("ep01").notes_file_path.write_text(yaml.safe_dump(notes, allow_unicode=True),
                                                                encoding="utf-8")
    return series


@pytest.mark.parametrize("point", [{}, {"text": "a", "frame": "b", "image": "c"}, {"text": "a", "caption": "b"}])
def test_a_point_has_text_and_at_most_one_captioned_picture(point: dict) -> None:
    with pytest.raises(ValidationError):
        Point.model_validate(point)


def test_a_card_point_can_be_written_as_its_text_alone() -> None:
    card = Card.model_validate({"id": "a", "title": "一個主張。", "points": ["理由", {"text": "例子", "points": ["細節"]}]})
    assert [point.text for point in card.points] == ["理由", "例子"] and card.points[1].points[0].text == "細節"


def test_the_video_page_has_chapters_when_the_notes_fit_the_delivered_video(tmp_path: Path) -> None:
    series = deliver_with_notes(tmp_path, NOTES)
    assert check_notes(series, "ep01") == []
    chapters = compute_video_page(series, "ep01")["chapters"]
    assert [part["title"] for part in chapters["parts"]] == ["兩次移動等於一支箭頭", "首尾相接就是加法"]
    hook = chapters["parts"][0]["segments"][0]
    assert (hook["id"], hook["startSeconds"], hook["endSeconds"]) == ("hook", 1.0, 7.0)
    assert [beat["id"] for beat in hook["beats"]] == ["two_moves", "one_arrow"]
    assert (hook["cards"][0]["id"], hook["cards"][0]["leadsTo"]) == ("ep01/moves_add", ["ep01/tip_to_tail"])
    assert compute_video_page(series, "ep01")["board"]["episodes"][0]["id"] == "ep01"
    assert hook["cards"][0]["points"][1] == {"text": "合起來的移動是一支斜箭頭。", "points": [], "frame": "one_arrow",
                                             "caption": "斜的箭頭連起點和終點"}


def test_notes_that_skip_a_scene_or_name_a_missing_beat_show_no_chapters(tmp_path: Path) -> None:
    notes = {**NOTES, "parts": [{"title": "只有開頭", "segments": ["hook"]}]}
    hook = NOTES["segments"]["hook"]
    notes["segments"] = {**NOTES["segments"], "hook": {**hook, "key_frame": "no_such_beat",
                                                       "cards": [{**hook["cards"][0], "leads_to": ["no_such_card"]}]}}
    series = deliver_with_notes(tmp_path, notes)
    problems = check_notes(series, "ep01")
    assert any("the parts hold hook" in problem for problem in problems)
    assert any("key_frame no_such_beat" in problem for problem in problems)
    assert any("leads_to no_such_card" in problem for problem in problems)
    assert compute_video_page(series, "ep01")["chapters"] is None


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


def test_an_arrow_to_another_episode_must_name_one_of_its_cards(tmp_path: Path) -> None:
    hook = NOTES["segments"]["hook"]
    notes = {**NOTES, "segments": {**NOTES["segments"],
                                   "hook": {**hook, "cards": [{**hook["cards"][0], "leads_to": ["ep02/no_card"]}]}}}
    series = deliver_with_notes(tmp_path, notes)
    assert any("leads_to ep02/no_card" in problem for problem in check_notes(series, "ep01"))
    board = compute_video_page(series, "ep01")["board"]
    assert board["episodes"][0]["parts"][0]["segments"][0]["cards"][0]["leadsTo"] == []  # left off the board


def test_deliver_refuses_an_episode_without_cards_that_fit_its_render(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    notes_file_path = series.get_episode_paths("ep01").notes_file_path
    notes_file_path.unlink()
    with pytest.raises(StudioError, match="cannot be delivered yet") as error:
        deliver(series, "ep01")
    assert any("notes.yaml is missing" in detail for detail in error.value.details)
    write_render(series)
    assert any("notes.yaml is missing" in problem for problem in check_notes(series, "ep01"))
