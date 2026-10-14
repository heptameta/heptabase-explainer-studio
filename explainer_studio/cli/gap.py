"""`gap add`."""

from __future__ import annotations

from pathlib import Path

import click

from ..gaps import GAP_KINDS
from .common import add_series_option, open_series, print_result


@click.group()
def gap() -> None:
    """Record what the product could not do and what was done instead (production/gaps.json)."""


@gap.command("add")
@click.option("--kind", required=True, type=click.Choice(GAP_KINDS), help="What was missing.")
@click.option("--episode", "episode_id", default=None, metavar="EPISODE",
              help="The episode it happened in (omit for the whole series).")
@click.option("--need", required=True, help="What the video needed.")
@click.option("--workaround", required=True, help="What was used instead.")
@add_series_option
def add(kind: str, episode_id: str | None, need: str, workaround: str, series_path: Path | None) -> None:
    """Add a gap. Read gaps.json first: record the same gap only once."""
    from ..gaps import add_gap
    from ..plan import load_plan

    series = open_series(series_path, episode_id)
    if episode_id is not None:
        load_plan(series).find_episode(episode_id)
    added = add_gap(series, kind, need, workaround, episode_id)
    print_result(f"added {added.id} ({added.kind}{', ' + added.episode_id if added.episode_id else ''}) to "
                 "production/gaps.json")
