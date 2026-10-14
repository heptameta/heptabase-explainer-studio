"""Helpers shared by the command modules: the series option, list and time options, progress and result output.

Results go to stdout, progress to stderr. Output is concise English meant for a coding agent.
"""

from __future__ import annotations

import math
from pathlib import Path

import click

from ..errors import StudioError
from ..paths import Series


def add_series_option(function):
    """Accept `--series` on a subcommand too, so it works before or after the command name."""
    return click.option("--series", "series_path", type=click.Path(path_type=Path), default=None,
                        help="The series folder (default: found by walking up from the current folder).")(function)


def open_series(series_path: Path | None, episode_id: str | None = None) -> Series:
    """The series the command works on. A command that makes an episode's video (the script commands, `narrate`,
    `preview`, `render`, `deliver`, `gap add`) passes the episode id: before anything else, the episode's record of
    Explainer Studio versions is updated, and a version change since the episode's last command is reported on
    stderr, so a running chat learns that the guide it read may be out of date. Commands that only look at or comment on the
    video (`feedback`, `video open`, `cost show`) pass none, so a delivery's record names only the versions that made
    it."""
    context = click.get_current_context()
    root_context = context.find_root()
    chosen_series_path = series_path or (root_context.obj or {}).get("series_path")
    series = Series.find(chosen_series_path)
    if episode_id is not None:
        from .. import __version__
        from ..explainer_studio_versions import record_version_use

        notice = record_version_use(series, episode_id, __version__)
        if notice:
            print_progress(f"notice: {notice}")
    return series


def parse_list(value: str | None) -> list[str] | None:
    """A comma-separated option (`--scenes a,b`) as its items; None when the option is not given."""
    return [part.strip() for part in value.split(",") if part.strip()] if value else None


def parse_time_seconds(text: str, option_name: str) -> float:
    """Seconds from a time given to `option_name` as a player shows it: 83, 1:23, 1:02:03 or 1:23.5."""
    try:
        numbers = [float(part) for part in text.strip().split(":")]
    except ValueError:
        numbers = []
    if not numbers or len(numbers) > 3 or not all(math.isfinite(number) and number >= 0 for number in numbers) \
            or any(number >= 60 for number in numbers[1:]):
        raise StudioError(f"{option_name} {text!r} is not a time",
                          "write it as a player shows it: seconds, minutes:seconds or hours:minutes:seconds",
                          f"use a time such as {option_name} 1:23 or {option_name} 83 (seconds)")
    seconds = 0.0
    for number in numbers:
        seconds = seconds * 60 + number
    return seconds


def print_progress(message: str) -> None:
    click.echo(message, err=True)


def print_result(message: str = "") -> None:
    click.echo(message)


def print_warning(message: str) -> None:
    click.echo(f"warning: {message}")
