"""preview and render on the fixture series, for real: ManimGL, ffmpeg and (for render) macOS `say` narration."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from say_narration import check_is_say_available, write_say_narration

from explainer_studio.file_io import read_json
from explainer_studio.paths import Series
from explainer_studio.rendering import audio_mix
from explainer_studio.rendering.preview import preview_episode
from explainer_studio.rendering.render import render_episode
from explainer_studio.schemas.automatic_checks import BLOCKING_CHECK_NAMES
from explainer_studio.schemas.script import compute_script_narration_digest
from explainer_studio.script import load_script

FIXTURE_DIR_PATH = Path(__file__).parent / "fixtures" / "render_series"
OVERLAP_SCENE = '''from explainer_studio.scene_kit import *


class Crowded(NarratedScene):
    def construct(self):
        with self.play_beat("crowded"):
            self.play(Write(Text("水壩的高度", font_size=60)), Write(Text("水車的能量", font_size=60).shift(0.2 * DOWN)))
'''

pytestmark = pytest.mark.render


@pytest.fixture
def series(tmp_path: Path) -> Series:
    shutil.copytree(FIXTURE_DIR_PATH, tmp_path / "series")
    return Series(tmp_path / "series")


def run_ffprobe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_preview_writes_clips_checks_and_screenshots_and_flags_overlapping_text(series: Series):
    episode_paths = series.get_episode_paths("ep01")
    script = episode_paths.script_file_path.read_text(encoding="utf-8")
    episode_paths.script_file_path.write_text(
        script + "  - id: crowded\n    purpose: Two labels on top of each other.\n    beats:\n"
        "      - id: crowded\n        narration_text: 兩個標籤疊在一起。\n        visual: 疊字。\n", encoding="utf-8")
    episode_paths.get_scene_file_path("crowded").write_text(OVERLAP_SCENE, encoding="utf-8")
    stale_file_path = episode_paths.get_preview_scene_dir_path("dam") / "stale.txt"
    stale_file_path.parent.mkdir(parents=True)
    stale_file_path.write_text("from an earlier preview")

    report = preview_episode(series, "ep01", None, False, lambda message: None)

    assert not report.failure_lines_by_name_map
    assert report.cover_file_path == episode_paths.preview_cover_dir_path / "cover.png"
    assert report.cover_file_path.exists()
    assert report.end_credits_file_path == episode_paths.preview_end_credits_dir_path / "end-credits.png"
    assert report.end_credits_file_path.exists()
    assert not stale_file_path.exists()
    scene_preview_by_id_map = {scene.scene_id: scene for scene in report.scenes}
    assert set(scene_preview_by_id_map) == {"dam", "heights", "crowded"}
    for scene in report.scenes:
        preview_dir_path = episode_paths.get_preview_scene_dir_path(scene.scene_id)
        clip_streams = run_ffprobe(preview_dir_path / "clip.mp4")["streams"]
        assert {stream["codec_type"] for stream in clip_streams} == {"video", "audio"}
        assert (preview_dir_path / "screenshots" / "every-2s-01.png").exists()
        assert (preview_dir_path / "screenshots" / "by-beat-01.png").exists()
        assert "issues" in read_json(preview_dir_path / "automatic-checks.json")
        assert scene.estimated_beat_count == scene.beat_count  # nothing is narrated yet
    crowded_issues = read_json(episode_paths.get_preview_scene_dir_path("crowded") / "automatic-checks.json")["issues"]
    assert any(issue["check_name"] == "text_overlap" and issue["beat_id"] == "crowded" for issue in crowded_issues)
    dam_issues = read_json(episode_paths.get_preview_scene_dir_path("dam") / "automatic-checks.json")["issues"]
    assert not [issue for issue in dam_issues if issue["check_name"] in BLOCKING_CHECK_NAMES]


@pytest.mark.skipif(not check_is_say_available(), reason="needs macOS say and ffmpeg")
def test_render_makes_a_complete_episode(series: Series):
    write_say_narration(series, "ep01")
    report = render_episode(series, "ep01", lambda message: None)
    render_dir_path = series.get_episode_paths("ep01").render_dir_path

    timeline = read_json(render_dir_path / "timeline.json")
    script = load_script(series, "ep01")
    assert timeline["narration_digest"] == compute_script_narration_digest(script)
    assert [scene["scene_id"] for scene in timeline["scenes"]] == ["dam", "heights"]
    first_beat = timeline["scenes"][0]["beats"][0]
    assert first_beat["start_seconds"] == pytest.approx(1.0)  # after the cover
    last_scene = timeline["scenes"][-1]
    assert timeline["end_credits_duration_seconds"] == 5.0  # the end credits fill the last five seconds
    assert last_scene["start_seconds"] + last_scene["duration_seconds"] + 5.0 == pytest.approx(timeline["duration_seconds"])
    assert [sound["sound"] for sound in timeline["sounds"]] == [
        {"kind": "effect", "effect_name": "whoosh_in"},
        {"kind": "file", "source_file_path": "shared/assets/audio/chord.ogg", "source_start_seconds": 0.0}]

    probe_result = run_ffprobe(render_dir_path / "video.mp4")
    assert float(probe_result["format"]["duration"]) == pytest.approx(timeline["duration_seconds"], abs=0.1)
    assert {stream["codec_type"] for stream in probe_result["streams"]} == {"video", "audio"}
    head_bytes = (render_dir_path / "video.mp4").read_bytes()[:100_000]
    assert head_bytes.find(b"moov") < head_bytes.find(b"mdat")  # faststart
    assert report.loudness_lufs == pytest.approx(-16, abs=1)
    assert report.true_peak_decibels <= audio_mix.MAX_TRUE_PEAK_DECIBELS

    srt_text = (render_dir_path / "subtitles.srt").read_text(encoding="utf-8")
    assert srt_text.startswith("1\n00:00:01,000 --> ")
    assert "想像一座水壩" in srt_text
    assert (render_dir_path / "cover.png").exists()
    assert read_json(render_dir_path / "automatic-checks.json") == {"issues": []}
    screenshots_dir_path = render_dir_path / "screenshots"
    assert (screenshots_dir_path / "every-6s-01.png").exists() and (screenshots_dir_path / "by-beat-01.png").exists()
    # every beat, the fixture has five
    assert len(list((screenshots_dir_path / "text-visibility-check").glob("*.png"))) == 5
