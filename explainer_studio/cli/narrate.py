"""`narrate <episode> [--beats a,b]`."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .common import add_series_option, open_series, parse_list, print_progress, print_result, print_warning


@click.command()
@click.argument("episode_id", metavar="EPISODE")
@click.option("--beats", "beat_ids", default=None, metavar="IDS",
              help="Comma-separated beat ids to redo even though their spoken text and voice are unchanged (for "
                   "example a mispronounced line).")
@add_series_option
def narrate(episode_id: str, beat_ids: str | None, series_path: Path | None) -> None:
    """Synthesize the episode's narration with the voice in plan.yaml.

    Reuses every beat whose spoken text and voice are unchanged, so it is safe to run again; failed beats are retried
    on the next run. Needs a finished script audience review and, for paid voices, an API key and room in the budget.
    """
    from ..narrate import narrate as run_narration
    from ..spending import format_usd

    series = open_series(series_path, episode_id)
    run = run_narration(series, episode_id, parse_list(beat_ids), print_progress)
    cost_text = format_usd(run.cost_usd) + (" (estimated)" if run.is_cost_estimated else "")
    print_result(f"{episode_id} narration ({run.provider_name}): reused {len(run.reused_beat_ids)}, made "
                 f"{len(run.made_beat_ids)}, failed {len(run.failure_by_beat_id_map)}; cost {cost_text}")
    if run.removed_beat_ids:
        print_result(f"removed audio of beats no longer in the script: {', '.join(run.removed_beat_ids)}")
    for beat_id, reason in run.failure_by_beat_id_map.items():
        print_result(f"failed {beat_id}: {reason}")
    for message in run.warnings:
        print_warning(message)
    if run.failure_by_beat_id_map:
        print_result(f"next: run `explainer-studio narrate {episode_id}` again; it retries the failed beats and reuses "
                     "the rest")
        sys.exit(1)
