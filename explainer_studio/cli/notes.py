"""`notes check`."""

from __future__ import annotations

from pathlib import Path

import click

from ..errors import StudioError
from .common import add_series_option, open_series, print_result


@click.group()
def notes() -> None:
    """The delivered episode's chapters and cards (episodes/<episode>/notes.yaml), shown on the video page."""


@notes.command("check")
@click.argument("episode_id", metavar="EPISODE")
@add_series_option
def check(episode_id: str, series_path: Path | None) -> None:
    """Check notes.yaml against the episode's render (or, without one, its latest delivery): every scene once, in
    order, every picture it names, and every arrow to a card of this or another episode. deliver checks the same."""
    from ..chapters import check_notes

    series = open_series(series_path, episode_id)
    problems = check_notes(series, episode_id)
    if problems:
        raise StudioError(f"{episode_id}/notes.yaml does not fit the video", f"{len(problems)} problem(s)",
                          "fix these, then check again", problems)
    print_result(f"{episode_id}/notes.yaml fits the video: the video page shows its chapters and cards")
