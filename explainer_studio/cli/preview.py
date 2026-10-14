"""`preview <episode> [--scenes a,b] [--cover] [--end-credits]`."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .common import add_series_option, open_series, parse_list, print_progress, print_result, print_warning


@click.command()
@click.argument("episode_id", metavar="EPISODE")
@click.option("--scenes", "scene_ids", default=None, metavar="IDS",
              help="Comma-separated scene ids (default: every scene).")
@click.option("--cover", "should_preview_cover", is_flag=True, help="Preview the cover (with --scenes: the cover too).")
@click.option("--end-credits", "should_preview_end_credits", is_flag=True,
              help="Preview the end credits page (with --scenes: the page too).")
@add_series_option
def preview(episode_id: str, scene_ids: str | None, should_preview_cover: bool, should_preview_end_credits: bool,
            series_path: Path | None) -> None:
    """Render scenes (and the cover and end credits) for checking: clip, automatic checks and screenshots per scene.

    No narration is needed: beats without current narration last an estimate of their spoken length, silently.
    With no options, every scene, the cover (when cover.py exists) and the end credits page (unless plan.yaml turns
    it off) are previewed."""
    from ..rendering.automatic_checks import format_issue_summary
    from ..rendering.preview import preview_episode

    series = open_series(series_path, episode_id)
    report = preview_episode(series, episode_id, parse_list(scene_ids), should_preview_cover, print_progress,
                             should_preview_end_credits)
    for warning in report.warnings:
        print_warning(warning)
    for scene in report.scenes:
        estimated = f", {scene.estimated_beat_count} with estimated timing" if scene.estimated_beat_count else ""
        print_result(f"{scene.scene_id}: {scene.duration_seconds:.1f} s, {scene.beat_count} beat(s){estimated}; "
                     f"{format_issue_summary(scene.issues)}")
        for note in scene.notes:
            print_result(f"  note: {note}")
        print_result(f"  checks: {scene.preview_dir_path / 'automatic-checks.json'}")
        print_result(f"  clip: {scene.preview_dir_path / 'clip.mp4'}")
        for path in scene.screenshots:
            print_result(f"  screenshot: {path}")
    if report.cover_file_path:
        print_result(f"cover: {report.cover_file_path}")
    if report.end_credits_file_path:
        print_result(f"end credits: {report.end_credits_file_path}")
    for name, lines in report.failure_lines_by_name_map.items():
        print_result(f"{name}: FAILED")
        for line in lines:
            print_result(f"  {line}")
    if report.scenes or report.cover_file_path or report.end_credits_file_path:
        print_result("Look at every screenshot before calling a scene done.")
    if report.failure_lines_by_name_map:
        sys.exit(1)
