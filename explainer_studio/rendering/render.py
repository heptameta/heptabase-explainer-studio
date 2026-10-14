"""render <episode>: the whole episode at 1080p, ready for delivery.

Every beat must be narrated (current), every scene file must define one NarratedScene subclass, and cover.py must
exist. Scenes render in parallel; their clips are concatenated in script order behind the cover (held 1 s, then a
0.5 s cross-fade), so narration, sounds and subtitles start 1 s later. When plan.yaml's has_end_credits is on (the
default), the last scene cross-fades in 1 s into the end credits page (end_credits.py, or the default page), which
stays to the end of its 5 s. The mix (narration, sounds, background music ducked under both) is normalized to
-16 LUFS. Everything is written to a temporary folder first; render/ is
replaced only when every step succeeded, so a failed render leaves the previous one in place.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .. import user_dirs
from ..background_music_providers import get_provider
from ..errors import StudioError
from ..file_io import write_json_model, write_text_atomic
from ..narrate import find_beat_ids_needing_narration
from ..paths import Series, parse_episode_number
from ..plan import load_plan
from ..schemas.automatic_checks import Issue
from ..schemas.script import Script, compute_script_narration_digest
from ..schemas.timeline import Timeline, TimelineBeat, TimelineScene
from ..script import load_script
from . import audio_mix, automatic_checks, manim_runner, screenshots, subtitles
from .manim_runner import FPS, RENDER_RESOLUTION, SceneResult

COVER_DURATION_SECONDS = 1.0
COVER_FADE_SECONDS = 0.5
END_CREDITS_DURATION_SECONDS = 5.0  # the cross-fade from the last scene included
END_CREDITS_FADE_SECONDS = 1.0
VIDEO_CRF = 18


@dataclass
class RenderReport:
    video_file_path: Path
    duration_seconds: float
    elapsed_seconds: float
    loudness_lufs: float | None
    true_peak_decibels: float | None
    issues: list[Issue]
    warnings: list[str]
    screenshots: list[Path]


def require_renderable(series: Series, episode_id: str) -> Script:
    """The script; StudioError when a beat's narration, a scene file or the cover is missing or unusable."""
    plan = load_plan(series)
    script = load_script(series, episode_id)
    stale_beat_ids = find_beat_ids_needing_narration(series, plan, episode_id, script)
    if stale_beat_ids:
        raise StudioError(f"{len(stale_beat_ids)} beat(s) of {episode_id} are not narrated or their narration is out "
                          "of date",
                          "render uses the real narration of every beat",
                          f"run `explainer-studio narrate {episode_id}`, then render again", stale_beat_ids[:20])
    episode_paths = series.get_episode_paths(episode_id)
    for scene in script.scenes:
        manim_runner.validate_scene_file(episode_paths.get_scene_file_path(scene.id), f"scenes/{scene.id}.py")
    if not episode_paths.cover_scene_file_path.is_file():
        raise StudioError("cover.py is missing", "every episode opens on its cover (chat apps show the first frame)",
                          f"write {episode_paths.cover_scene_file_path} with one CoverScene subclass, preview it with "
                          "--cover")
    end_credits_file_paths = ([episode_paths.end_credits_scene_file_path]
                              if plan.has_end_credits and episode_paths.end_credits_scene_file_path.is_file() else [])
    manim_runner.lint_series_code(series, [episode_paths.get_scene_file_path(scene.id) for scene in script.scenes]
                                  + [episode_paths.cover_scene_file_path] + end_credits_file_paths)
    return script


def _require_every_beat_played(script: Script, result_by_scene_id_map: dict[str, SceneResult]) -> None:
    problems = []
    for scene in script.scenes:
        played_beat_ids = [beat["beat_id"] for beat in result_by_scene_id_map[scene.id].beats]
        missing_beat_ids = [beat.id for beat in scene.beats if beat.id not in played_beat_ids]
        if missing_beat_ids:
            problems.append(f"scenes/{scene.id}.py never plays {', '.join(missing_beat_ids)}")
    if problems:
        raise StudioError("some beats are not in the video", "every beat of script.yaml needs a play_beat block",
                          "add `with self.play_beat(\"<beat_id>\"):` for each, then render again", problems)


def build_timeline(script: Script, result_by_scene_id_map: dict[str, SceneResult],
                   end_credits_duration_seconds: float = 0.0) -> tuple[Timeline, list[tuple[float, Path]]]:
    """The timeline of the delivered video (cover and end credits included) and where each narration file starts."""
    offset_seconds, scenes, sounds, narration_clips = COVER_DURATION_SECONDS, [], [], []
    for scene in script.scenes:
        result = result_by_scene_id_map[scene.id]
        beats = [TimelineBeat(beat_id=beat["beat_id"], start_seconds=round(offset_seconds + beat["start_seconds"], 3),
                              duration_seconds=round(beat["duration_seconds"], 3))
                 for beat in result.beats]
        scenes.append(TimelineScene(scene_id=scene.id, start_seconds=round(offset_seconds, 3),
                                    duration_seconds=round(result.duration_seconds, 3), beats=beats))
        sounds += [sound.model_copy(update={"start_seconds": round(offset_seconds + sound.start_seconds, 3),
                                            "duration_seconds": round(sound.duration_seconds, 3)})
                   for sound in result.sounds]
        narration_clips += [(offset_seconds + beat["start_seconds"], Path(beat["audio_file_path"]))
                            for beat in result.beats]
        offset_seconds += result.duration_seconds
    timeline = Timeline(narration_digest=compute_script_narration_digest(script),
                        duration_seconds=round(offset_seconds + end_credits_duration_seconds, 3),
                        cover_duration_seconds=COVER_DURATION_SECONDS,
                        end_credits_duration_seconds=end_credits_duration_seconds, scenes=scenes,
                        sounds=sorted(sounds, key=lambda sound: sound.start_seconds))
    return timeline, narration_clips


def _run_ffmpeg(*arguments: str, what: str) -> None:
    ffmpeg_path = user_dirs.find_tool("ffmpeg") or "ffmpeg"
    result = subprocess.run([ffmpeg_path, "-v", "error", "-y", *arguments], capture_output=True, text=True,
                            check=False)
    if result.returncode != 0:
        raise StudioError(f"{what} failed", result.stderr.strip()[-400:], "check the ffmpeg install "
                          "(`explainer-studio doctor`), then render again")


def mix_audio(series: Series, episode_id: str, timeline: Timeline, narration_clips: list[tuple[float, Path]],
              work_dir_path: Path, report_progress: Callable[[str], None]) -> Path:
    """The episode's normalized mix as a WAV as long as the timeline."""
    plan = load_plan(series)
    track = audio_mix.mix_voice_and_sounds(timeline.duration_seconds, narration_clips, timeline.sounds,
                                           series.production_dir_path)
    music_settings = plan.resolve_episode_background_music_settings(episode_id)
    music_file_path = work_dir_path / "music.wav"
    report_progress(f"background music: {music_settings.provider_name}")
    if get_provider(music_settings.provider_name).make_track(timeline, parse_episode_number(episode_id),
                                                          music_settings, music_file_path, audio_mix.SAMPLE_RATE_HERTZ):
        busy_intervals = [(beat.start_seconds, beat.start_seconds + beat.duration_seconds)
                          for scene in timeline.scenes for beat in scene.beats]
        busy_intervals += [(sound.start_seconds, sound.start_seconds + sound.duration_seconds)
                           for sound in timeline.sounds if sound.should_duck_background_music]
        track = audio_mix.add_background_music(track, audio_mix.read_wav(music_file_path), busy_intervals)
    mixed, normalized = work_dir_path / "mix.wav", work_dir_path / "mix-normalized.wav"
    audio_mix.write_wav(mixed, audio_mix.limit_peak(track))
    audio_mix.normalize_loudness(mixed, normalized)
    return normalized


def build_video_filter_graph(scenes_duration_seconds: float, has_end_credits: bool) -> str:
    """ffmpeg's filter graph: input 0 is the cover, 1 the scenes, 2 the end credits page. The cover cross-fades into
    the scenes; the scenes' last frame is held while it cross-fades into the end credits."""
    width, height = RENDER_RESOLUTION
    fit_still = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                 f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1")
    filter_graph = (f"[0:v]{fit_still}[cover];[1:v]fps={FPS},format=yuv420p,setsar=1[scenes];"
                    f"[cover][scenes]xfade=transition=fade:duration={COVER_FADE_SECONDS}"
                    f":offset={COVER_DURATION_SECONDS}")
    if not has_end_credits:
        return filter_graph + "[video]"
    return (filter_graph + f",tpad=stop_mode=clone:stop_duration={END_CREDITS_FADE_SECONDS}[body];"
            f"[2:v]{fit_still}[end_credits];"
            f"[body][end_credits]xfade=transition=fade:duration={END_CREDITS_FADE_SECONDS}"
            f":offset={COVER_DURATION_SECONDS + scenes_duration_seconds:.3f}[video]")


def encode_video(clip_file_paths: list[Path], cover_file_path: Path, end_credits_file_path: Path | None,
                 scenes_duration_seconds: float, output_file_path: Path, work_dir_path: Path) -> None:
    """The cover held, then cross-faded into the scenes, then into the end credits when there is a page: H.264
    without sound (the mix is added by mux)."""
    concat_list_file_path = work_dir_path / "scenes.txt"
    concat_list_file_path.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clip_file_paths),
                                     encoding="utf-8")
    end_credits_inputs = (["-loop", "1", "-framerate", str(FPS), "-t", f"{END_CREDITS_DURATION_SECONDS:.3f}",
                           "-i", str(end_credits_file_path)] if end_credits_file_path else [])
    filter_graph = build_video_filter_graph(scenes_duration_seconds, end_credits_file_path is not None)
    _run_ffmpeg("-loop", "1", "-framerate", str(FPS), "-t", f"{COVER_DURATION_SECONDS + COVER_FADE_SECONDS:.3f}",
                "-i", str(cover_file_path), "-f", "concat", "-safe", "0", "-i", str(concat_list_file_path),
                *end_credits_inputs, "-filter_complex", filter_graph, "-map", "[video]",
                "-c:v", "libx264", "-preset", "medium", "-crf", str(VIDEO_CRF), "-pix_fmt", "yuv420p",
                str(output_file_path), what="encoding the video")


def mux(video_file_path: Path, audio_file_path: Path, output_file_path: Path) -> None:
    """The video with the mix as AAC, its index first so it plays while it loads."""
    _run_ffmpeg("-i", str(video_file_path), "-i", str(audio_file_path), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(audio_mix.SAMPLE_RATE_HERTZ), "-ac", "2",
                "-movflags", "+faststart", str(output_file_path), what="adding the sound to the video")


def enforce_true_peak_limit(video_file_path: Path, work_dir_path: Path) -> tuple[float | None, float | None]:
    """Measure the delivered audio; when AAC pushed the true peak over the limit, turn it down and measure again."""
    loudness_lufs, true_peak_decibels = audio_mix.measure_loudness(video_file_path)
    if true_peak_decibels is not None and true_peak_decibels > audio_mix.MAX_TRUE_PEAK_DECIBELS:
        quieter_file_path = work_dir_path / "quieter.mp4"
        _run_ffmpeg("-i", str(video_file_path), "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
                    "-af", f"volume={audio_mix.MAX_TRUE_PEAK_DECIBELS - true_peak_decibels - 0.3:.2f}dB",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(quieter_file_path), what="lowering the true peak")
        quieter_file_path.replace(video_file_path)
        loudness_lufs, true_peak_decibels = audio_mix.measure_loudness(video_file_path)
    return loudness_lufs, true_peak_decibels


def write_screenshots(video_file_path: Path, timeline: Timeline, script: Script,
                      result_by_scene_id_map: dict[str, SceneResult], output_dir_path: Path) -> list[Path]:
    narration_text_by_beat_id_map = {beat.id: beat.narration_text.strip() for beat in script.list_beats()}
    beat_screenshots, metrics_by_beat_id_map = [], {}
    for scene in timeline.scenes:
        result = result_by_scene_id_map[scene.scene_id]
        for beat in result.beats:
            time_seconds = scene.start_seconds + screenshots.resolve_beat_screenshot_time(beat, result.duration_seconds)
            beat_screenshots.append(screenshots.BeatScreenshot(beat["beat_id"], round(time_seconds, 3),
                                                               narration_text_by_beat_id_map[beat["beat_id"]]))
            metrics_by_beat_id_map[beat["beat_id"]] = beat["metrics"]
    interval_times_seconds = screenshots.resolve_interval_times(timeline.duration_seconds, 6.0)
    frame_by_time_map = screenshots.grab_frames(
        video_file_path,
        interval_times_seconds + [beat_screenshot.time_seconds for beat_screenshot in beat_screenshots])
    screenshot_file_paths = screenshots.write_interval_screenshot_sheets(
        [(time_seconds, frame_by_time_map[time_seconds]) for time_seconds in interval_times_seconds],
        output_dir_path, "every-6s")
    screenshot_file_paths += screenshots.write_beat_screenshot_sheets(
        [(beat_screenshot, frame_by_time_map[beat_screenshot.time_seconds]) for beat_screenshot in beat_screenshots],
        output_dir_path, "by-beat", column_count=2, row_count=3, tile_width_pixels=600)
    text_visibility_dir_path = output_dir_path / "text-visibility-check"
    text_visibility_dir_path.mkdir(parents=True, exist_ok=True)
    screenshot_by_beat_id_map = {beat_screenshot.beat_id: beat_screenshot for beat_screenshot in beat_screenshots}
    for beat_id in screenshots.choose_text_visibility_beat_ids(metrics_by_beat_id_map):
        screenshot_file_path = text_visibility_dir_path / f"{beat_id}.png"
        frame_by_time_map[screenshot_by_beat_id_map[beat_id].time_seconds].convert("RGB").save(screenshot_file_path)
        screenshot_file_paths.append(screenshot_file_path)
    return screenshot_file_paths


def replace_dir(source_dir_path: Path, target_dir_path: Path) -> None:
    """Put source_dir_path's contents at target_dir_path, swapping the old folder out only once the copy is complete."""
    staging_dir_path = target_dir_path.with_name(f".{target_dir_path.name}-new-{uuid.uuid4().hex[:8]}")
    shutil.copytree(source_dir_path, staging_dir_path)
    old_dir_path = None
    if target_dir_path.exists():
        old_dir_path = target_dir_path.with_name(f".{target_dir_path.name}-old-{uuid.uuid4().hex[:8]}")
        target_dir_path.rename(old_dir_path)
    staging_dir_path.rename(target_dir_path)
    if old_dir_path is not None:
        shutil.rmtree(old_dir_path, ignore_errors=True)


def render_episode(series: Series, episode_id: str, report_progress: Callable[[str], None]) -> RenderReport:
    started_monotonic_seconds = time.monotonic()
    script = require_renderable(series, episode_id)
    has_end_credits = load_plan(series).has_end_credits
    episode_paths = series.get_episode_paths(episode_id)
    work_dir_path = manim_runner.create_work_dir("render")
    try:
        tasks: list[tuple[str, Callable[[], object]]] = [
            ("cover", lambda: manim_runner.render_cover(series, episode_id, work_dir_path / "cover"))]
        if has_end_credits:
            tasks.append(("end_credits", lambda: manim_runner.render_end_credits(series, episode_id,
                                                                                 work_dir_path / "end_credits")))
        tasks += [(scene.id, lambda scene=scene: manim_runner.render_scene(series, episode_id, scene.id, "render",
                                                                           work_dir_path / scene.id))
                  for scene in script.scenes]
        stills = "the cover and the end credits" if has_end_credits else "the cover"
        report_progress(f"rendering {len(script.scenes)} scene(s) and {stills} of {episode_id} at 1080p ...")
        result_by_scene_id_map, failure_lines_by_name_map = manim_runner.render_in_parallel(tasks, report_progress)
        if failure_lines_by_name_map:
            failure_lines = [line for lines in failure_lines_by_name_map.values() for line in lines]
            raise StudioError(f"{len(failure_lines_by_name_map)} of {len(tasks)} render job(s) failed",
                              "see each failure below",
                              "fix the scene file and line named, preview it, then render again (render/ is "
                              "unchanged)", failure_lines)
        cover_file_path = Path(result_by_scene_id_map.pop("cover"))
        end_credits_file_path = Path(result_by_scene_id_map.pop("end_credits")) if has_end_credits else None
        _require_every_beat_played(script, result_by_scene_id_map)
        timeline, narration_clips = build_timeline(script, result_by_scene_id_map,
                                                   END_CREDITS_DURATION_SECONDS if has_end_credits else 0.0)

        report_progress("encoding the video while mixing narration, sounds and background music ...")
        with ThreadPoolExecutor(max_workers=1) as pool:  # the mix runs while ffmpeg encodes the picture
            audio_future = pool.submit(mix_audio, series, episode_id, timeline, narration_clips, work_dir_path,
                                       report_progress)
            silent_video_file_path = work_dir_path / "silent.mp4"
            encode_video([result_by_scene_id_map[scene.id].video_file_path for scene in script.scenes], cover_file_path,
                         end_credits_file_path,
                         timeline.duration_seconds - COVER_DURATION_SECONDS - timeline.end_credits_duration_seconds,
                         silent_video_file_path, work_dir_path)
            audio_file_path = audio_future.result()
        output_dir_path = work_dir_path / "render"
        output_dir_path.mkdir()
        video = output_dir_path / "video.mp4"
        mux(silent_video_file_path, audio_file_path, video)
        loudness_lufs, true_peak_decibels = enforce_true_peak_limit(video, work_dir_path)

        narration_text_by_beat_id_map = {beat.id: beat.narration_text.strip() for beat in script.list_beats()}
        cues = [cue for scene in timeline.scenes for beat in scene.beats
                for cue in subtitles.build_beat_cues(beat.start_seconds, beat.duration_seconds,
                                                     narration_text_by_beat_id_map[beat.beat_id])]
        write_text_atomic(output_dir_path / "subtitles.srt", subtitles.serialize_srt(cues))
        shutil.copyfile(cover_file_path, output_dir_path / "cover.png")
        write_json_model(output_dir_path / "timeline.json", timeline)
        issues = [issue for scene in script.scenes
                  for issue in automatic_checks.convert_records_to_issues(scene.id,
                                                                          result_by_scene_id_map[scene.id].issues)]
        automatic_checks.write_automatic_checks(output_dir_path / "automatic-checks.json", issues)
        report_progress("taking screenshots ...")
        screenshot_file_paths = write_screenshots(video, timeline, script, result_by_scene_id_map,
                                                  output_dir_path / "screenshots")

        warnings = []
        for result in result_by_scene_id_map.values():
            warnings += [warning for warning in result.warnings if warning not in warnings]
            previewed_file_path = episode_paths.get_preview_scene_dir_path(result.scene_id) / "file-excerpts.json"
            changed_excerpts = automatic_checks.find_changed_file_excerpts(previewed_file_path, result.file_excerpts)
            warnings += [f"scenes/{result.scene_id}.py shows {excerpt}, which changed since its last preview; look at "
                         "its by-beat screenshots" for excerpt in changed_excerpts]
        replace_dir(output_dir_path, episode_paths.render_dir_path)
        render_dir_path = episode_paths.render_dir_path
        return RenderReport(render_dir_path / "video.mp4", timeline.duration_seconds,
                            time.monotonic() - started_monotonic_seconds, loudness_lufs, true_peak_decibels, issues,
                            warnings,
                            [render_dir_path / path.relative_to(output_dir_path) for path in screenshot_file_paths])
    finally:
        shutil.rmtree(work_dir_path, ignore_errors=True)
