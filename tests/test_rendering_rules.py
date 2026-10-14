"""Rules preview and render apply before and after ManimGL runs: scene code checks, subtitles, the mix's ducking,
which frames get a text-visibility check, stale file excerpts, and the narration requirement."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from explainer_studio.errors import StudioError
from explainer_studio.paths import Series
from explainer_studio.rendering import audio_mix, automatic_checks, manim_runner, scene_lint, screenshots, subtitles
from explainer_studio.rendering.render import require_renderable

FIXTURE_DIR_PATH = Path(__file__).parent / "fixtures" / "render_series"


@pytest.fixture
def series(tmp_path: Path) -> Series:
    shutil.copytree(FIXTURE_DIR_PATH, tmp_path / "series")
    return Series(tmp_path / "series")


def test_lint_names_manim_community_code_and_pitfalls_but_not_comments():
    text = """from manim import *
# self.play(Create(x))  is fine in a comment
        self.play(Create(circle))
        eq = MathTex(R"x")
        self.play(Transform(a, b), path_arc=PI)
        group = VGroup(get_image('a.png'), label)
        dot.add_updater(lambda m, d=dot: m.move_to(d))
        self.play(ShowCreation(circle))
        self.play(TransformMatchingTex(a, b, key_map={"(": ")"}, path_arc=PI / 2), run_time=2)
        self.play(
            Transform(a, b),  # not path_arc=PI here
            path_arc=PI,
        )
"""
    line_numbers = [line_number for line_number, _, _ in scene_lint.lint_text(text)]
    assert line_numbers == [1, 3, 4, 5, 6, 7, 12]


def test_scene_file_needs_exactly_one_narrated_scene(tmp_path: Path):
    def validate_source(source: str) -> None:
        scene_file_path = tmp_path / "scene.py"
        scene_file_path.write_text(source, encoding="utf-8")
        manim_runner.validate_scene_file(scene_file_path, "scenes/scene.py")

    validate_source("class A(NarratedScene):\n    pass\n")
    validate_source("from shared.base import Step\nclass A(Step):\n    pass\n")  # confirmed by the ManimGL process
    with pytest.raises(StudioError, match="2 NarratedScene subclasses"):
        validate_source("class Base(NarratedScene):\n    pass\nclass A(Base):\n    pass\n")
    with pytest.raises(StudioError, match="no NarratedScene subclass"):
        validate_source("class A:\n    pass\n")
    with pytest.raises(StudioError, match="not valid Python"):
        validate_source("class A(NarratedScene)\n")


def test_cjk_subtitles_split_at_clause_breaks_and_share_the_time():
    assert subtitles.split_line("我們先離開細胞，想一座水壩。壩的左邊水位很高，右邊很低。") == [
        "我們先離開細胞，想一座水壩", "壩的左邊水位很高，右邊很低"]
    assert subtitles.split_line("三個水壩的高度分別是 3、5 和 8 公尺。") == ["三個水壩的高度分別是 3、5 和 8 公尺"]
    cues = subtitles.build_beat_cues(1.0, 4.0, "把最右邊加高到 12 公尺，能拿出來的能量也跟著變多。")
    assert [cue.text for cue in cues] == ["把最右邊加高到 12 公尺", "能拿出來的能量也跟著變多"]
    assert cues[0].start_seconds == 1.0 and cues[-1].end_seconds == pytest.approx(5.0)
    assert subtitles.serialize_srt(cues) == ("1\n00:00:01,000 --> 00:00:03,080\n把最右邊加高到 12 公尺\n\n"
                                             "2\n00:00:03,080 --> 00:00:05,000\n能拿出來的能量也跟著變多\n")


@pytest.mark.render  # runs ffmpeg
def test_a_video_without_sound_adds_silence(tmp_path: Path):
    video = tmp_path / "blender-shot.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=30", "-t", "1",
                    str(video)], check=True)
    assert audio_mix.load_audio(video).shape == (0, 2)


def test_music_ducks_while_someone_speaks():
    sample_rate_hertz = audio_mix.SAMPLE_RATE_HERTZ
    duration_seconds = 12
    track = np.zeros((duration_seconds * sample_rate_hertz, 2), dtype=np.float32)
    music = np.full((duration_seconds * sample_rate_hertz, 2), 0.1, dtype=np.float32)
    mixed = audio_mix.add_background_music(track, music, busy_intervals=[(5.0, 8.0)])
    quiet, loud = np.abs(mixed[int(7.5 * sample_rate_hertz), 0]), np.abs(mixed[int(4.0 * sample_rate_hertz), 0])
    assert 20 * np.log10(quiet / loud) == pytest.approx(audio_mix.DUCK_DECIBELS, abs=1.0)


def test_text_visibility_picks_distinct_beats_by_each_risk():
    metrics_by_beat_id_map = {
        "small": {"min_font_size": 17.0, "edge_distance": 2.0},
        "small2": {"min_font_size": 18.0, "edge_distance": 2.0},
        "edge": {"min_font_size": 40.0, "edge_distance": 0.05},
        "small3": {"min_font_size": 19.0, "edge_distance": 2.0},
        "edge2": {"min_font_size": 40.0, "edge_distance": 0.1},
        "edge3": {"min_font_size": 40.0, "edge_distance": 0.2},
        "plain": {"min_font_size": 40.0, "edge_distance": 2.0},
        "no_text": {"min_font_size": None, "edge_distance": None},
    }
    assert screenshots.choose_text_visibility_beat_ids(metrics_by_beat_id_map) == [
        "small", "small2", "small3", "edge", "edge2", "edge3"]


def test_excerpt_changed_since_preview_is_named(tmp_path: Path):
    excerpt_record = {"path": "sources/app.py", "first_line_number": 3, "last_line_number": 8, "search_text": None,
                      "following_line_count": 0, "content_hash": "aaaa"}
    previewed_file_path = tmp_path / "file-excerpts.json"
    automatic_checks.write_file_excerpts(previewed_file_path, [excerpt_record])
    assert automatic_checks.find_changed_file_excerpts(previewed_file_path, [excerpt_record]) == []
    changed_excerpt = {**excerpt_record, "content_hash": "bbbb"}
    assert automatic_checks.find_changed_file_excerpts(previewed_file_path, [changed_excerpt]) == [
        "sources/app.py (lines 3-8)"]
    other_excerpt = {**changed_excerpt, "first_line_number": 4}
    assert automatic_checks.find_changed_file_excerpts(previewed_file_path, [other_excerpt]) == []


def test_render_refuses_beats_without_current_narration(series: Series):
    with pytest.raises(StudioError, match="5 beat\\(s\\) of ep01 are not narrated") as raised:
        require_renderable(series, "ep01")
    assert "explainer-studio narrate ep01" in raised.value.next_step
