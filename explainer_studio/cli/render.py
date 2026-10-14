"""`render <episode>`."""

from __future__ import annotations

from pathlib import Path

import click

from .common import add_series_option, open_series, print_progress, print_result, print_warning


@click.command()
@click.argument("episode_id", metavar="EPISODE")
@add_series_option
def render(episode_id: str, series_path: Path | None) -> None:
    """Render the whole episode at 1080p into render/: video, subtitles, cover, timeline, checks, screenshots.

    Every beat must be narrated first. render/ is replaced only when every step succeeds. A five-minute episode
    takes about a minute or two; run it in the background when the shell has a short time limit."""
    from ..rendering.automatic_checks import format_issue_summary
    from ..rendering.render import render_episode

    series = open_series(series_path, episode_id)
    report = render_episode(series, episode_id, print_progress)
    for warning in report.warnings:
        print_warning(warning)
    loudness_text = "unmeasured" if report.loudness_lufs is None else f"{report.loudness_lufs:.1f} LUFS"
    true_peak_text = "" if report.true_peak_decibels is None else f", true peak {report.true_peak_decibels:.1f} dBTP"
    print_result(f"rendered {episode_id}: {report.duration_seconds:.1f} s video in {report.elapsed_seconds:.0f} s "
                 f"({loudness_text}{true_peak_text})")
    print_result(f"video: {report.video_file_path}")
    print_result(f"automatic checks: {format_issue_summary(report.issues)} "
                 f"({report.video_file_path.parent / 'automatic-checks.json'})")
    for path in report.screenshots:
        print_result(f"screenshot: {path}")
    print_result("Next: look at every screenshot and fix what you see (render again after fixing), then run "
                 f"`explainer-studio deliver {episode_id}`.")
