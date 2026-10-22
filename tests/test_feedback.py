from __future__ import annotations

import copy
import shutil
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from delivered_series import SCRIPT, create_series, write_delivery_record
from feedback_receiver import Receiver

from explainer_studio import __version__
from explainer_studio.agent_transcripts.claude_code import SESSION_ENV
from explainer_studio.cli.common import parse_time_seconds
from explainer_studio.deliver import deliver, load_delivery_record
from explainer_studio.errors import StudioError
from explainer_studio.feedback import (
    add_comment,
    delete_comment,
    edit_comment,
    find_comment_beat,
    load_feedback,
    record_comment_resolution,
    set_survey_answer,
)
from explainer_studio.feedback_bundle import FEEDBACK_URL_ENV, pack_feedback_bundle, share_feedback
from explainer_studio.gaps import add_gap, load_gaps
from explainer_studio.schemas.feedback import EpisodeAnchor, MomentAnchor
from explainer_studio.web.pages import compute_video_page
from explainer_studio.web.server import PageServer


@pytest.mark.parametrize(("text", "seconds"), [("83", 83), ("1:23", 83), ("1:02:03", 3723), ("0:07.5", 7.5)])
def test_parse_time_reads_player_times(text: str, seconds: float) -> None:
    assert parse_time_seconds(text, "--at") == seconds


@pytest.mark.parametrize("text", ["1:99", "", "a:10", "-3"])
def test_parse_time_refuses_what_a_player_would_not_show(text: str) -> None:
    with pytest.raises(StudioError, match="--at"):
        parse_time_seconds(text, "--at")


def test_a_deleted_comments_id_is_never_reused(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    write_delivery_record(series, datetime.now(UTC) - timedelta(hours=1))
    add_comment(series, "ep01", "第一則", EpisodeAnchor(kind="episode"))
    last = add_comment(series, "ep01", "第二則", EpisodeAnchor(kind="episode"))
    delete_comment(series, "ep01", last.id)
    assert add_comment(series, "ep01", "第三則", EpisodeAnchor(kind="episode")).id == "c-3"


def test_which_video_feedback_is_about_follows_from_its_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    first_delivered_at = datetime(2026, 10, 8, 10, 0, tzinfo=UTC)
    moments = [first_delivered_at]
    monkeypatch.setattr("explainer_studio.feedback.get_current_time", lambda: moments[-1])

    def go_to(minutes: int) -> None:
        moments.append(first_delivered_at + timedelta(minutes=minutes))

    write_delivery_record(series, first_delivered_at)
    go_to(5)
    set_survey_answer(series, "ep01", "rating", "good")
    go_to(6)
    set_survey_answer(series, "ep01", "rating", "bad")  # rated again for the same video: replaces the rating
    go_to(7)
    comment = add_comment(series, "ep01", "為什麼要接在頭上？", MomentAnchor(kind="moment", time_seconds=8.0))
    second_script = copy.deepcopy(SCRIPT)
    second_script["scenes"][1]["beats"][0]["narration_text"] = "把第二支箭頭搬過來，尾巴接上頭。"
    write_delivery_record(series, first_delivered_at + timedelta(hours=1), second_script)
    go_to(65)
    set_survey_answer(series, "ep01", "rating", "okay")

    assert [(answer.kind, answer.value) for answer in load_feedback(series, "ep01").survey_answers] == [
        ("rating", "bad"), ("rating", "okay")]
    page = compute_video_page(series, "ep01")
    assert page["surveyAnswers"] == [{"kind": "rating", "value": "okay"}]
    assert page["comments"][0]["isOnOlderVideo"]
    # what was said at its moment in the video it was made on, not in the current one
    assert find_comment_beat(series, "ep01", comment).narration_text == \
        SCRIPT["scenes"][1]["beats"][0]["narration_text"]


def test_a_comment_is_saved_without_a_sheet_when_the_sheet_cannot_be_drawn(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    record_dir_path = write_delivery_record(series, datetime.now(UTC) - timedelta(hours=1))
    (series.root_dir_path / "01-v.mp4").write_bytes(b"not a video")
    (record_dir_path / "timeline.json").write_text("{", encoding="utf-8")  # a damaged record
    comment = add_comment(series, "ep01", "為什麼要接在頭上？", MomentAnchor(kind="moment", time_seconds=8.0))
    assert load_feedback(series, "ep01").comments == [comment]
    assert not series.get_episode_paths("ep01").get_comment_screenshot_sheet_file_path(comment.id).exists()


@pytest.fixture
def delivered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    series = create_series(tmp_path / "series")
    record_dir_path = deliver(series, "ep01").record_dir_path
    receiver = Receiver().start()
    monkeypatch.setenv(FEEDBACK_URL_ENV, receiver.url)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))  # no conversation records: no cost to work out
    monkeypatch.delenv(SESSION_ENV, raising=False)
    yield series, record_dir_path, receiver
    receiver.shutdown()


@pytest.mark.render
def test_a_moment_comment_has_a_comment_screenshot_sheet_of_its_moment_while_it_exists(delivered) -> None:
    series, record_dir_path, _ = delivered
    video_file_name = load_delivery_record(series, record_dir_path).files.video_file_name
    delivered_video_file_path = series.root_dir_path / video_file_name
    comment = add_comment(series, "ep01", "為什麼要接在頭上？", MomentAnchor(kind="moment", time_seconds=3.0))
    episode_paths = series.get_episode_paths("ep01")
    comment_screenshot_sheet_file_path = episode_paths.get_comment_screenshot_sheet_file_path(comment.id)
    first_jpeg = comment_screenshot_sheet_file_path.read_bytes()
    assert first_jpeg.startswith(b"\xff\xd8")
    edit_comment(series, "ep01", comment.id, anchor=MomentAnchor(kind="moment", time_seconds=11.0))
    assert comment_screenshot_sheet_file_path.read_bytes() != first_jpeg  # drawn again at the new moment
    delete_comment(series, "ep01", comment.id)
    assert not comment_screenshot_sheet_file_path.exists()

    older = add_comment(series, "ep01", "整集太快", MomentAnchor(kind="moment", time_seconds=5.0))
    write_delivery_record(series, datetime.now(UTC) + timedelta(seconds=1))  # the video is delivered again
    shutil.copyfile(delivered_video_file_path, series.root_dir_path / "01-v.mp4")  # the new video at the series root
    edit_comment(series, "ep01", older.id, anchor=MomentAnchor(kind="moment", time_seconds=6.0))
    # its video is gone: the series root holds the new one, which is not what the comment was about
    assert not series.get_episode_paths("ep01").get_comment_screenshot_sheet_file_path(older.id).exists()


@pytest.mark.render
def test_a_bundle_carries_only_its_listed_files(delivered) -> None:
    series, record_dir_path, _ = delivered
    (series.production_dir_path / "sources").mkdir()
    (series.production_dir_path / "sources" / "notes.pdf").write_bytes(b"%PDF private material")
    add_comment(series, "ep01", "為什麼要接在頭上？", MomentAnchor(kind="moment", time_seconds=8.0))
    share_feedback(series, "ep01")
    add_comment(series, "ep01", "整集太快", EpisodeAnchor(kind="episode"))
    deleted = add_comment(series, "ep01", "刪掉的留言", MomentAnchor(kind="moment", time_seconds=4.0))
    episode_paths = series.get_episode_paths("ep01")
    deleted_sheet_jpeg = episode_paths.get_comment_screenshot_sheet_file_path(deleted.id).read_bytes()
    delete_comment(series, "ep01", deleted.id)
    # a sheet left behind by a deleted comment is not packed
    episode_paths.get_comment_screenshot_sheet_file_path(deleted.id).write_bytes(deleted_sheet_jpeg)
    bundle = pack_feedback_bundle(series, "ep01")
    record_prefix = f"episodes/ep01/delivery-records/{record_dir_path.name}"
    assert set(bundle.path_to_content_map) == {
        "episodes/ep01/feedback.json", "plan.yaml", "gaps.json", f"{record_prefix}/metadata.json",
        f"{record_prefix}/script.yaml", f"{record_prefix}/timeline.json",
        "episodes/ep01/comment-screenshot-sheets/c-1.jpg",  # every comment screenshot sheet, shared before or not
        "environment.json", "cost.json"}
    assert bundle.path_to_content_map["plan.yaml"] == series.plan_file_path.read_bytes()  # whole


def test_a_bundle_refuses_a_symbolic_link_instead_of_packing_what_it_points_to(tmp_path: Path,
                                                                             monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    record_dir_path = write_delivery_record(series, datetime.now(UTC))
    private_file_path = tmp_path / "credentials"
    private_file_path.write_text("a private key", encoding="utf-8")
    (record_dir_path / "script.yaml").unlink()
    (record_dir_path / "script.yaml").symlink_to(private_file_path)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.delenv(SESSION_ENV, raising=False)
    with pytest.raises(StudioError, match="symbolic link"):
        pack_feedback_bundle(series, "ep01")


@pytest.mark.render
def test_share_marks_what_was_new_only_after_the_receiver_accepts_it(delivered) -> None:
    series, _, receiver = delivered
    comment = add_comment(series, "ep01", "整集太快", EpisodeAnchor(kind="episode"))
    set_survey_answer(series, "ep01", "rating", "okay")
    add_gap(series, "visual", "a moving arrow", "a fade", "ep01")

    receiver.failure_status_code = 503
    with pytest.raises(StudioError, match="not sent"):
        share_feedback(series, "ep01")
    assert load_feedback(series, "ep01").comments[0].shared_at is None

    receiver.failure_status_code = None
    shared_items = share_feedback(series, "ep01")
    assert (len(shared_items.comments), len(shared_items.survey_answers), len(shared_items.gaps)) == (1, 1, 1)
    [bundle] = receiver.bundles
    assert bundle.feedback_id == load_feedback(series, "ep01").id
    assert bundle.explainer_studio_version == __version__
    assert bundle.read_json("gaps.json")["gaps"][0]["need"] == "a moving arrow"
    feedback = load_feedback(series, "ep01")
    assert feedback.comments[0].shared_at and feedback.survey_answers[0].shared_at \
        and load_gaps(series).gaps[0].shared_at

    record_comment_resolution(series, "ep01", comment.id, "teaching", "the pace was set for a faster viewer")
    shared_again = share_feedback(series, "ep01")
    assert (len(shared_again.comments), len(shared_again.comment_id_to_resolution_map)) == (0, 1)
    [sent] = receiver.bundles[1].read_json("episodes/ep01/feedback.json")["comments"]
    assert sent["text"] == "整集太快" and sent["resolution"]["note"] == "the pace was set for a faster viewer"
    assert not share_feedback(series, "ep01")

    edit_comment(series, "ep01", comment.id, text="整集太快了")  # a changed comment is new again
    assert [shared_comment.id for shared_comment in share_feedback(series, "ep01").comments] == [comment.id]


@pytest.mark.render
def test_a_page_share_sends_the_whole_feedback(delivered) -> None:
    series, _, receiver = delivered
    asked = add_comment(series, "ep01", "為什麼要接在頭上？", MomentAnchor(kind="moment", time_seconds=8.0),
                        origin="page")
    record_comment_resolution(series, "ep01", asked.id, "question", "the tail step went by too fast")
    server = PageServer(series, "token", 0, 60)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        video_api_url = f"http://127.0.0.1:{server.port}/token/api/video/ep01"
        answered = httpx.put(f"{video_api_url}/survey-answers/watch_depth", json={"value": "skimmed"}, trust_env=False)
        share_url = f"{video_api_url}/share"
        listed = httpx.get(share_url, trust_env=False).json()
        sent = httpx.post(share_url, trust_env=False)
    finally:
        server.shutdown()
        server.server_close()
    assert answered.status_code == 200
    assert [listed_comment["id"] for listed_comment in listed["comments"]] == [asked.id] and not listed["isEmpty"]
    assert listed["surveyAnswers"] == [{"kind": "watch_depth", "value": "skimmed"}]
    assert sent.json()["isSent"]
    [bundle] = receiver.bundles
    [comment] = bundle.read_json("episodes/ep01/feedback.json")["comments"]
    assert comment["resolution"]["note"] == "the tail step went by too fast"
    assert f"episodes/ep01/comment-screenshot-sheets/{asked.id}.jpg" in bundle.path_to_content_map
    assert load_feedback(series, "ep01").survey_answers[0].shared_at
