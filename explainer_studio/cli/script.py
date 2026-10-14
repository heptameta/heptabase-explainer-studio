"""`script validate` and `script prepare-audience-review-prompt`."""

from __future__ import annotations

from pathlib import Path

import click

from ..script import find_script_warnings, load_script
from .common import add_series_option, open_series, parse_list, print_result, print_warning


@click.group()
def script() -> None:
    """Check an episode's script or prepare its audience review."""


@script.command("validate")
@click.argument("episode_id", metavar="EPISODE")
@add_series_option
def validate(episode_id: str, series_path: Path | None) -> None:
    """Check script.yaml's format and ids; warn about long lines, a short episode and known misreadings."""
    series = open_series(series_path, episode_id)
    loaded = load_script(series, episode_id)
    beats = loaded.list_beats()
    print_result(f"{episode_id}/script.yaml is valid: {len(loaded.scenes)} scene(s), {len(beats)} beat(s)")
    for message in find_script_warnings(series, episode_id, loaded):
        print_warning(message)


@script.command("prepare-audience-review-prompt")
@click.argument("episode_id", metavar="EPISODE")
@click.option("--scenes", "scene_ids", default=None, metavar="IDS",
              help="Comma-separated scene ids to review (default: all).")
@add_series_option
def prepare_audience_review_prompt(episode_id: str, scene_ids: str | None, series_path: Path | None) -> None:
    """Write the script audience review prompt to a file and print its path and the round header."""
    from ..audience_review import prepare_audience_review_prompt as prepare_episode_audience_review_prompt

    series = open_series(series_path, episode_id)
    prompt_file_path, header = prepare_episode_audience_review_prompt(series, episode_id, parse_list(scene_ids))
    print_result(f"prompt: {prompt_file_path}")
    print_result("Give the audience reviewer (a fresh subagent) only this path; it must not read any other file.")
    print_result("Append the reviewer's reply to audience-reviews/script.yaml under this header, then add a resolution "
                 "to each finding:")
    print_result(header)
