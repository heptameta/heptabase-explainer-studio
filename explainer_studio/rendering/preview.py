"""preview <episode> [--scenes a,b] [--cover] [--end-credits]: render scenes for the agent to check while writing them.

Per scene, preview/<scene_id>/ is cleared and gets clip.mp4 (narration where it is current, sounds, no music),
automatic-checks.json, and screenshot sheets (every-2s-NN.png, by-beat-NN.png). The cover goes to
preview/cover/cover.png, the end credits page to preview/end-credits/end-credits.png.
Beats without current narration last the language table's estimate, silently. Preview never blocks anything; it
only refuses scene code that cannot work.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .. import user_dirs
from ..errors import StudioError
from ..paths import Series
from ..plan import load_plan
from ..schemas.automatic_checks import Issue
from ..script import load_script
from . import audio_mix, automatic_checks, manim_runner, screenshots
from .manim_runner import SceneResult

SCREENSHOT_INTERVAL_SECONDS = 2.0


@dataclass
class ScenePreview:
    scene_id: str
    duration_seconds: float
    beat_count: int
    estimated_beat_count: int
    issues: list[Issue]
    preview_dir_path: Path
    screenshots: list[Path]
    notes: list[str] = field(default_factory=list)


@dataclass
class PreviewReport:
    scenes: list[ScenePreview]
    failure_lines_by_name_map: dict[str, list[str]]
    cover_file_path: Path | None
    warnings: list[str]
    end_credits_file_path: Path | None = None


def mux(video_file_path: Path, track, output_file_path: Path, work_dir_path: Path) -> None:
    """The silent ManimGL video with an audio track, as an MP4 that starts playing before it finishes loading."""
    wav_file_path = work_dir_path / f"{output_file_path.stem}.wav"
    audio_mix.write_wav(wav_file_path, audio_mix.limit_peak(track))
    ffmpeg_path = user_dirs.find_tool("ffmpeg") or "ffmpeg"
    result = subprocess.run([ffmpeg_path, "-v", "error", "-y", "-i", str(video_file_path), "-i", str(wav_file_path),
                             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                             "-movflags", "+faststart", str(output_file_path)],
                             capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise StudioError("could not write the preview clip", result.stderr.strip()[-300:], "check the ffmpeg install")


def _finish_scene(series: Series, episode_id: str, result: SceneResult,
                  narration_text_by_beat_id_map: dict[str, str], scene_beat_ids: list[str],
                  work_dir_path: Path) -> ScenePreview:
    preview_dir_path = series.get_episode_paths(episode_id).get_preview_scene_dir_path(result.scene_id)
    screenshots_dir_path = preview_dir_path / "screenshots"
    screenshots_dir_path.mkdir(parents=True, exist_ok=True)
    narration_clips = [(beat["start_seconds"], Path(beat["audio_file_path"])) for beat in result.beats
                       if beat["audio_file_path"]]
    track = audio_mix.mix_voice_and_sounds(result.duration_seconds, narration_clips, result.sounds,
                                           series.production_dir_path)
    mux(result.video_file_path, track, preview_dir_path / "clip.mp4", work_dir_path)
    issues = automatic_checks.convert_records_to_issues(result.scene_id, result.issues)
    automatic_checks.write_automatic_checks(preview_dir_path / "automatic-checks.json", issues)
    automatic_checks.write_file_excerpts(preview_dir_path / "file-excerpts.json", result.file_excerpts)

    interval_times_seconds = screenshots.resolve_interval_times(result.duration_seconds, SCREENSHOT_INTERVAL_SECONDS)
    beat_screenshots = [
        screenshots.BeatScreenshot(beat["beat_id"],
                                   screenshots.resolve_beat_screenshot_time(beat, result.duration_seconds),
                                   narration_text_by_beat_id_map[beat["beat_id"]])
        for beat in result.beats]
    frame_by_time_map = screenshots.grab_frames(
        result.video_file_path,
        interval_times_seconds + [beat_screenshot.time_seconds for beat_screenshot in beat_screenshots])
    screenshot_sheet_file_paths = screenshots.write_interval_screenshot_sheets(
        [(time_seconds, frame_by_time_map[time_seconds]) for time_seconds in interval_times_seconds],
        screenshots_dir_path, "every-2s")
    screenshot_sheet_file_paths += screenshots.write_beat_screenshot_sheets(
        [(beat_screenshot, frame_by_time_map[beat_screenshot.time_seconds]) for beat_screenshot in beat_screenshots],
        screenshots_dir_path, "by-beat", column_count=3, row_count=3, tile_width_pixels=420)
    played_beat_ids = [beat["beat_id"] for beat in result.beats]
    notes = []
    missing_beat_ids = [beat_id for beat_id in scene_beat_ids if beat_id not in played_beat_ids]
    if missing_beat_ids:
        notes.append(f"no play_beat block, so render will refuse: {', '.join(missing_beat_ids)}")
    if [beat_id for beat_id in scene_beat_ids if beat_id in played_beat_ids] != played_beat_ids:
        notes.append("beats are played in a different order from script.yaml")
    return ScenePreview(result.scene_id, result.duration_seconds, len(result.beats),
                        sum(1 for beat in result.beats if not beat["audio_file_path"]), issues, preview_dir_path,
                        screenshot_sheet_file_paths, notes)


def _copy_still(result_by_name_map: dict, failure_lines_by_name_map: dict, name: str, report: PreviewReport,
                target_file_path: Path) -> Path | None:
    """Put a rendered still (the cover, the end credits) at target_file_path, or record its failure."""
    shutil.rmtree(target_file_path.parent, ignore_errors=True)
    if name in failure_lines_by_name_map:
        report.failure_lines_by_name_map[name] = failure_lines_by_name_map[name]
        return None
    target_file_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(result_by_name_map[name]), target_file_path)
    return target_file_path


def preview_episode(series: Series, episode_id: str, scene_ids: list[str] | None, should_preview_cover: bool,
                    report_progress: Callable[[str], None], should_preview_end_credits: bool = False) -> PreviewReport:
    script = load_script(series, episode_id)
    episode_paths = series.get_episode_paths(episode_id)
    all_scene_ids = [scene.id for scene in script.scenes]
    unknown_scene_ids = [scene_id for scene_id in scene_ids or [] if scene_id not in all_scene_ids]
    if unknown_scene_ids:
        raise StudioError(f"no scene {', '.join(unknown_scene_ids)} in {episode_id}/script.yaml",
                          f"the script's scenes are {', '.join(all_scene_ids)}", "pass scene ids from script.yaml")
    is_still_only = should_preview_cover or should_preview_end_credits
    chosen_scene_ids = scene_ids if scene_ids else ([] if is_still_only else all_scene_ids)
    should_include_cover = should_preview_cover or (not scene_ids and not is_still_only
                                                    and episode_paths.cover_scene_file_path.is_file())
    should_include_end_credits = should_preview_end_credits or (not scene_ids and not is_still_only
                                                                and load_plan(series).has_end_credits)
    if should_preview_cover and not episode_paths.cover_scene_file_path.is_file():
        raise StudioError("cover.py is missing", f"expected {episode_paths.cover_scene_file_path}",
                          "write cover.py with one CoverScene subclass (see scene_kit.cover)")
    for scene_id in chosen_scene_ids:
        manim_runner.validate_scene_file(episode_paths.get_scene_file_path(scene_id), f"scenes/{scene_id}.py")
    manim_runner.lint_series_code(series, [episode_paths.get_scene_file_path(scene_id) for scene_id in chosen_scene_ids]
                                  + ([episode_paths.cover_scene_file_path] if should_include_cover else [])
                                  + ([episode_paths.end_credits_scene_file_path] if should_include_end_credits
                                     and episode_paths.end_credits_scene_file_path.is_file() else []))

    work_dir_path = manim_runner.create_work_dir("preview")
    try:
        tasks: list[tuple[str, Callable[[], object]]] = [
            ("cover", lambda: manim_runner.render_cover(series, episode_id, work_dir_path / "cover"))
        ] if should_include_cover else []
        if should_include_end_credits:
            tasks.append(("end_credits", lambda: manim_runner.render_end_credits(series, episode_id,
                                                                                 work_dir_path / "end_credits")))
        tasks += [(scene_id, lambda scene_id=scene_id: manim_runner.render_scene(series, episode_id, scene_id,
                                                                                 "preview", work_dir_path / scene_id))
                  for scene_id in chosen_scene_ids]
        previewed_parts = [f"{len(chosen_scene_ids)} scene(s)"] if chosen_scene_ids else []
        previewed_parts += ["the cover"] if should_include_cover else []
        previewed_parts += ["the end credits"] if should_include_end_credits else []
        report_progress(f"previewing {' and '.join(previewed_parts)} of {episode_id} ...")
        result_by_name_map, failure_lines_by_name_map = manim_runner.render_in_parallel(tasks, report_progress)

        narration_text_by_beat_id_map = {beat.id: beat.narration_text.strip() for beat in script.list_beats()}
        report = PreviewReport([], {}, None, [])
        for scene_id in chosen_scene_ids:
            preview_dir_path = episode_paths.get_preview_scene_dir_path(scene_id)
            shutil.rmtree(preview_dir_path, ignore_errors=True)
            if scene_id in failure_lines_by_name_map:
                report.failure_lines_by_name_map[scene_id] = failure_lines_by_name_map[scene_id]
                continue
            result = result_by_name_map[scene_id]
            report.warnings += [warning for warning in result.warnings if warning not in report.warnings]
            scene_beat_ids = [beat.id for beat in script.get_scene(scene_id).beats]
            report.scenes.append(_finish_scene(series, episode_id, result, narration_text_by_beat_id_map,
                                               scene_beat_ids, work_dir_path / scene_id))
        if should_include_cover:
            report.cover_file_path = _copy_still(result_by_name_map, failure_lines_by_name_map, "cover", report,
                                                 episode_paths.preview_cover_dir_path / "cover.png")
        if should_include_end_credits:
            report.end_credits_file_path = _copy_still(
                result_by_name_map, failure_lines_by_name_map, "end_credits", report,
                episode_paths.preview_end_credits_dir_path / "end-credits.png")
        return report
    finally:
        shutil.rmtree(work_dir_path, ignore_errors=True)
