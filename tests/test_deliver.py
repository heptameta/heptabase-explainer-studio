from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner
from delivered_series import create_series, write_render

from explainer_studio import __version__
from explainer_studio.cli.main import cli
from explainer_studio.deliver import (
    deliver,
    format_delivery_record_dir_name,
    list_delivery_record_dir_paths,
    load_latest_delivery_record,
)
from explainer_studio.errors import StudioError


def test_delivery_record_folders_follow_the_moment_not_the_wall_clock() -> None:
    summer_time = datetime(2026, 10, 25, 1, 30, tzinfo=timezone(timedelta(hours=1)))  # 00:30 UTC
    after_the_clocks_went_back = datetime(2026, 10, 25, 1, 10, tzinfo=UTC)  # 40 minutes later
    assert format_delivery_record_dir_name(summer_time) == "2026-10-25T003000Z"
    assert format_delivery_record_dir_name(after_the_clocks_went_back) > format_delivery_record_dir_name(summer_time)


@pytest.mark.render
def test_deliver_refuses_only_text_too_small_among_the_automatic_checks(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    episode_paths = series.get_episode_paths("ep01")
    episode_paths.render_automatic_checks_file_path.write_text(json.dumps({"issues": [
        {"check_name": "text_too_small", "scene_id": "hook", "beat_id": "two_moves",
         "detail": "a label is 12 on screen"},
        {"check_name": "text_overlap", "scene_id": "hook", "beat_id": "one_arrow",
         "detail": "reported, not blocking"}]}),
        encoding="utf-8")
    with pytest.raises(StudioError) as refused:
        deliver(series, "ep01")
    [problem] = refused.value.details
    assert problem.startswith("automatic check text_too_small in scene hook, beat two_moves")
    assert episode_paths.render_video_file_path.exists() and load_latest_delivery_record(series, "ep01") is None


@pytest.mark.render
def test_deliver_refuses_a_render_of_other_narration_than_the_script(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    episode_paths = series.get_episode_paths("ep01")
    timeline = json.loads(episode_paths.render_timeline_file_path.read_text(encoding="utf-8"))
    episode_paths.render_timeline_file_path.write_text(json.dumps({**timeline, "narration_digest": "0" * 12}),
                                                       encoding="utf-8")
    with pytest.raises(StudioError) as refused:
        deliver(series, "ep01")
    [problem] = refused.value.details
    assert problem.startswith("the render has narration 000000000000")
    assert not episode_paths.delivery_records_dir_path.exists()


@pytest.mark.render
def test_deliver_moves_the_files_keeps_every_record_and_replaces_the_previous_video(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    first_result = deliver(series, "ep01")
    first = first_result.record
    video = series.root_dir_path / first.files.video_file_name
    assert first.files.video_file_name == "01-為什麼向量可以相加？.mp4"
    [subtitles] = first.files.subtitles  # in the episode's language
    assert (subtitles.language_code, subtitles.file_name) == ("zh-TW", "01-為什麼向量可以相加？.zh-TW.srt")
    assert video.exists() and (series.root_dir_path / subtitles.file_name).exists()
    assert (series.root_dir_path / first.files.cover_file_name).exists()
    assert not series.get_episode_paths("ep01").render_video_file_path.exists()
    assert {path.name for path in first_result.record_dir_path.iterdir()} == {"metadata.json", "timeline.json",
                                                                              "script.yaml"}
    assert set(json.loads((first_result.record_dir_path / "metadata.json").read_text(encoding="utf-8"))) == {
        "delivered_at", "explainer_studio_version", "earlier_explainer_studio_versions", "files"}

    series.plan_file_path.write_text(series.plan_file_path.read_text(encoding="utf-8").replace("title: 為什麼向量可以相加？",
                                                                           "title: 向量加法"), encoding="utf-8")
    write_render(series, tone_hertz=660)
    second_result = deliver(series, "ep01")
    assert list_delivery_record_dir_paths(series, "ep01") == [first_result.record_dir_path,
                                                              second_result.record_dir_path]
    assert not video.exists() and not (series.root_dir_path / first.files.cover_file_name).exists()
    assert not (series.root_dir_path / subtitles.file_name).exists()
    assert (series.root_dir_path / "01-向量加法.mp4").exists()
    assert load_latest_delivery_record(series, "ep01") == second_result.record


@pytest.mark.render
def test_a_delivery_after_a_version_change_names_the_earlier_version_and_starts_counting_again(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series")
    versions_file_path = series.get_episode_paths("ep01").explainer_studio_versions_file_path
    earlier = "0.1.1.dev13+g9b0e2d4"  # an earlier command on the episode ran with this dev build
    versions_file_path.write_text(json.dumps({"last_used_version": earlier, "versions_since_last_delivery": [earlier]}),
                                  encoding="utf-8")

    run = CliRunner().invoke(cli, ["deliver", "ep01", "--series", str(series.root_dir_path)], catch_exceptions=False)

    assert run.exit_code == 0, run.output
    assert f"changed from {earlier} to {__version__}" in run.stderr  # stdout stays the command's result
    assert f"made with Explainer Studio {__version__}; also used since the last delivery: {earlier}" in run.stdout
    record = load_latest_delivery_record(series, "ep01")
    assert (record.explainer_studio_version, record.earlier_explainer_studio_versions) == (__version__, [earlier])
    assert json.loads(versions_file_path.read_text(encoding="utf-8")) == {"last_used_version": __version__,
                                                                      "versions_since_last_delivery": []}
