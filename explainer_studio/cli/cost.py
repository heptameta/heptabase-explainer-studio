"""`cost show [<episode>]`."""

from __future__ import annotations

from pathlib import Path

import click

from .common import add_series_option, open_series, print_result


@click.group()
def cost() -> None:
    """What making the series took: working time, the agent's model calls and tokens, and paid narration."""


@cost.command("show")
@click.argument("episode_id", metavar="EPISODE", required=False)
@click.option("--json", "should_print_json", is_flag=True,
              help="Print the report as JSON (the format in the feedback bundle).")
@add_series_option
def show(episode_id: str | None, should_print_json: bool, series_path: Path | None) -> None:
    """Show the cost of each episode up to its first delivery, step by step, and of planning the series.

    Worked out from this computer's Claude Code transcripts (token counts, model settings, times and the commands
    run, never what was said) and production/spending.jsonl. Nothing is stored. In dev mode, the agent's usage is also
    shown in dollars when the local price table exists (`explainer-studio dev-mode`)."""
    from ..cost import compute_cost_report, filter_cost_report_to_episode, format_cost_report
    from ..model_prices import load_dev_mode_model_prices
    from ..paths import parse_episode_number

    series = open_series(series_path)
    report = compute_cost_report(series)
    if episode_id is not None:
        parse_episode_number(episode_id)
        report = filter_cost_report_to_episode(report, episode_id)
    if should_print_json:
        print_result(report.model_dump_json(indent=2))
        return
    prices, problem = load_dev_mode_model_prices()
    for line in format_cost_report(report, series, prices):
        print_result(line)
    if problem:
        print_result(f"no dollars: {problem}")
