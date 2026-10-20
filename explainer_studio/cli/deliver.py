"""`deliver <episode>`."""

from __future__ import annotations

from pathlib import Path

import click

from .common import add_series_option, open_series, print_result


@click.command()
@click.argument("episode_id", metavar="EPISODE")
@click.option("--skip-notes-check", "should_skip_notes_check", is_flag=True,
              help="Deliver without checking the episode's cards (notes.yaml), when the user wants none. The video "
                   "page then has no chapters view for it, and the series' whiteboard gets no cards from it.")
@add_series_option
def deliver(episode_id: str, should_skip_notes_check: bool, series_path: Path | None) -> None:
    """Check the render, its automatic checks and the episode's cards (`notes check`), then move the video, subtitles
    and cover to the series folder."""
    from ..cost import compute_cost_report, filter_cost_report_to_episode, format_cost_report
    from ..deliver import deliver as deliver_episode
    from ..dev_mode import check_is_dev_mode_on
    from ..model_prices import load_dev_mode_model_prices

    series = open_series(series_path, episode_id)
    delivery_result = deliver_episode(series, episode_id, should_check_notes=not should_skip_notes_check)
    record = delivery_result.record
    print_result(f"delivered {episode_id} at {record.delivered_at.isoformat()}:")
    for file_name in record.files.list_file_names():
        print_result(f"  {series.root_dir_path / file_name}")
    print_result(f"record: {delivery_result.record_dir_path.relative_to(series.root_dir_path).as_posix()}/")
    earlier_versions = record.earlier_explainer_studio_versions
    print_result(f"made with Explainer Studio {record.explainer_studio_version}"
                 + (f"; also used since the last delivery: {', '.join(earlier_versions)}" if earlier_versions else ""))
    if delivery_result.settled_while_lost_scene_ids:
        print_result("scenes where the script audience review stopped while the audience reviewer was still lost: "
                     + ", ".join(delivery_result.settled_while_lost_scene_ids))
    print_result("In the message that says the episode is ready, tell the user these scenes (if any) and where the "
                 "script departed from the plan.")
    if check_is_dev_mode_on():
        report = filter_cost_report_to_episode(compute_cost_report(series), episode_id)
        if report.unavailable_reason is None:
            print_result("dev mode is on: what making it cost (also on the video page):")
            prices, problem = load_dev_mode_model_prices()
            for line in format_cost_report(report, series, prices)[1:]:
                print_result(f"  {line}")
            if problem:
                print_result(f"  no dollars: {problem}")
            print_result("Include this cost, step by step, in the message that says the episode is ready.")
        else:
            print_result(f"dev mode is on, but the cost is not available: {report.unavailable_reason}")
    print_result(f"next: explainer-studio video open {episode_id}")
