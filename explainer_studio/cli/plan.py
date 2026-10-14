"""`plan open` and `plan validate`."""

from __future__ import annotations

from pathlib import Path

import click

from ..plan import validate_plan
from .common import add_series_option, open_series, print_result


@click.group()
def plan() -> None:
    """Check or open the series plan (production/plan.yaml)."""


@plan.command("validate")
@add_series_option
def validate(series_path: Path | None) -> None:
    """Check plan.yaml's format, episode ids and episode folders. Changes nothing."""
    series = open_series(series_path)
    loaded, notes = validate_plan(series)
    print_result(f"plan.yaml is valid: {len(loaded.episodes)} episode(s), language {loaded.language_code}")
    for note in notes:
        print_result(f"note: {note}")


@plan.command("open")
@add_series_option
@click.option("--no-browser", "should_skip_browser", is_flag=True,
              help="Start the page server and print the URL without opening a browser, to show it in your own pane.")
def open_(series_path: Path | None, should_skip_browser: bool) -> None:
    """Validate the plan, start the series page server if needed, and open the plan page in the browser."""
    from ..web.launcher import open_page

    series = open_series(series_path)
    validate_plan(series)
    url = open_page(series, "plan", should_open_browser=not should_skip_browser)
    print_result(f"plan page: {url}")
