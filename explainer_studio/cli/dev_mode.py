"""`dev-mode [on|off]`."""

from __future__ import annotations

import click

from .common import print_result


@click.command("dev-mode")
@click.argument("state", required=False, type=click.Choice(["on", "off"]))
def dev_mode(state: str | None) -> None:
    """Turn dev mode on or off for this computer, or show whether it is on.

    Dev mode is for people improving Explainer Studio: the video page adds how closely you watched, and `deliver` and
    the video page show each episode's cost report, with dollars worked out from the local model price table. It never changes how videos are made. Open pages pick up a change when they reload."""
    from ..dev_mode import check_is_dev_mode_on, set_dev_mode
    from ..user_dirs import get_model_prices_file_path

    if state is not None:
        set_dev_mode(state == "on")
    print_result(f"dev mode is {'on' if check_is_dev_mode_on() else 'off'} for this computer")
    if check_is_dev_mode_on() and not get_model_prices_file_path().exists():
        print_result(f"no model price table at {get_model_prices_file_path()}: costs show tokens and time, "
                     "without dollars")
