"""`video open`."""

from __future__ import annotations

from pathlib import Path

import click

from ..errors import StudioError
from .common import add_series_option, open_series, print_result


@click.group()
def video() -> None:
    """Open a delivered video's page."""


@video.command("open")
@click.argument("episode_id", metavar="EPISODE")
@add_series_option
@click.option("--no-browser", "should_skip_browser", is_flag=True,
              help="Start the page server and print the URL without opening a browser, to show it in your own pane.")
def open_(episode_id: str, series_path: Path | None, should_skip_browser: bool) -> None:
    """Open the video page of the episode's latest delivery, where the user watches and comments."""
    from ..deliver import load_latest_delivery_record
    from ..web.launcher import open_page

    series = open_series(series_path)
    latest_delivery_record = load_latest_delivery_record(series, episode_id)
    if latest_delivery_record is None:
        raise StudioError(f"{episode_id} has not been delivered", "the video page plays the delivered video",
                          f"explainer-studio deliver {episode_id}")
    video_file_path = series.root_dir_path / latest_delivery_record.files.video_file_name
    if not video_file_path.is_file():
        raise StudioError(f"the delivered video of {episode_id} is missing",
                          f"{latest_delivery_record.files.video_file_name} is not in the series folder; it may have "
                          "been moved or renamed",
                          f"move it back to {video_file_path}, or render and deliver the episode again")
    url = open_page(series, "video", episode_id, should_open_browser=not should_skip_browser)
    print_result(f"video page: {url}")
