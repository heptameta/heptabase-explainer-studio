"""`feedback add`, `feedback resolve` and `feedback share`."""

from __future__ import annotations

from pathlib import Path

import click

from ..feedback import RESOLUTION_CATEGORIES
from .common import add_series_option, open_series, parse_time_seconds, print_result


@click.group()
def feedback() -> None:
    """Record comments on a delivered episode, resolve them, and share feedback with the team."""


@feedback.command("add")
@click.argument("episode_id", metavar="EPISODE")
@click.argument("text")
@click.option("--at", "time_text", default=None, metavar="TIME",
              help="The time in the video, as the player shows it (1:23).")
@add_series_option
def add(episode_id: str, text: str, time_text: str | None, series_path: Path | None) -> None:
    """Record a comment the user made in chat, on the current video: about the moment --at, or without it about the
    whole episode. With --at, also draw its comment screenshot sheet."""
    from ..feedback import add_comment, find_comment_beat, format_comment_anchor
    from ..schemas.feedback import EpisodeAnchor, MomentAnchor

    series = open_series(series_path)
    anchor = (MomentAnchor(kind="moment", time_seconds=parse_time_seconds(time_text, "--at")) if time_text
              else EpisodeAnchor(kind="episode"))
    comment = add_comment(series, episode_id, text, anchor, origin="chat")
    if not isinstance(comment.anchor, MomentAnchor):
        print_result(f"added {comment.id} to {episode_id} with no time (about the whole episode)")
        return
    beat = find_comment_beat(series, episode_id, comment)
    narration_note = f', said: "{beat.narration_text}" (beat {beat.beat_id})' if beat else ""
    episode_paths = series.get_episode_paths(episode_id)
    comment_screenshot_sheet_file_path = episode_paths.get_comment_screenshot_sheet_file_path(comment.id)
    comment_screenshot_sheet_note = (
        f"; comment screenshot sheet: production/"
        f"{series.convert_path_to_production_relative_path(comment_screenshot_sheet_file_path)}"
        if comment_screenshot_sheet_file_path.is_file()
        else "; no comment screenshot sheet: the video in the series folder is missing or cannot be read")
    print_result(f"added {comment.id} to {episode_id} at {format_comment_anchor(comment.anchor)}{narration_note}"
                 f"{comment_screenshot_sheet_note}")


@feedback.command("resolve")
@click.argument("episode_id", metavar="EPISODE")
@click.argument("comment_id", metavar="COMMENT")
@click.argument("note")
@click.option("--category", required=True, type=click.Choice(RESOLUTION_CATEGORIES),
              help="question: a learning question; teaching: how it was taught; production: how it was made; "
                   "direction: what the series should do.")
@add_series_option
def resolve(episode_id: str, comment_id: str, note: str, category: str, series_path: Path | None) -> None:
    """Record the category of a comment and what was done about it, with the reason."""
    from ..feedback import record_comment_resolution

    comment = record_comment_resolution(open_series(series_path), episode_id, comment_id, category, note)
    print_result(f"resolved {comment.id} as {category}; the page now shows it collapsed")


@feedback.command("share")
@click.argument("episode_id", metavar="EPISODE")
@click.option("--dry-run", "is_dry_run", is_flag=True, help="Print what would be sent, without sending.")
@add_series_option
def share(episode_id: str, is_dry_run: bool, series_path: Path | None) -> None:
    """Send the episode's feedback bundle when it has comments, resolutions, survey answers or gaps not shared yet.
    Only with the user's agreement."""
    from ..feedback_bundle import (
        format_feedback_bundle_contents,
        pack_feedback_bundle,
        resolve_unshared_items,
        share_feedback,
    )

    series = open_series(series_path)
    if is_dry_run:
        bundle = pack_feedback_bundle(series, episode_id)
        if not resolve_unshared_items(bundle.feedback, bundle.gaps):
            print_result(f"nothing new to share for {episode_id}")
            return
        for line in format_feedback_bundle_contents(series, bundle):
            print_result(line)
        print_result("Nothing was sent. Ask the user, listing this; send only if they agree.")
        return
    shared_items = share_feedback(series, episode_id)
    if not shared_items:
        print_result(f"nothing new to share for {episode_id}")
        return
    print_result(f"sent the feedback bundle, new: {len(shared_items.comments)} comment(s), "
                 f"{len(shared_items.comment_id_to_resolution_map)} resolution(s), {len(shared_items.survey_answers)} "
                 f"survey answer(s), {len(shared_items.gaps)} gap(s); they are marked as shared")
