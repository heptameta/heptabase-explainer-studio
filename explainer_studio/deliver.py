"""Delivery: hand the rendered video to the user and keep a record of it.

`deliver` checks the render and its automatic checks, moves the video, subtitles and cover to the series root as
`<NN>-<title>` (the subtitles as `<NN>-<title>.<language code>.srt`, in the episode's language), and keeps a delivery
record in `delivery-records/<delivered time>/` with the timeline and script that went into it. Only the latest
deliverable is kept, so the video at the series root is always the latest delivery's; the records are kept forever. A
record names the Explainer Studio version that delivered and any other versions used on the episode since the previous
delivery.
"""

from __future__ import annotations

import contextlib
import os
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import __version__
from .audience_review import find_scene_ids_settled_while_lost
from .errors import StudioError
from .explainer_studio_versions import clear_versions_since_last_delivery, list_earlier_versions_since_last_delivery
from .file_io import get_current_time, load_json_model, load_yaml_model, write_json_model
from .paths import Series
from .plan import load_plan
from .schemas.automatic_checks import AutomaticChecks
from .schemas.delivery_record import DeliveredFiles, DeliveredSubtitles, DeliveryRecord
from .schemas.script import Script, compute_script_narration_digest
from .schemas.timeline import Timeline
from .script import load_script

DELIVERY_RECORD_FILE_NAME = "metadata.json"


@dataclass
class DeliveryResult:
    record: DeliveryRecord
    record_dir_path: Path
    settled_while_lost_scene_ids: list[str] = field(default_factory=list)


# Reading records ----------------------------------------------------------------------------------------------------
def list_delivery_record_dir_paths(series: Series, episode_id: str) -> list[Path]:
    """The folders of the episode's delivery records, oldest first (they are named by the UTC delivered time, so they
    sort)."""
    delivery_records_dir_path = series.get_episode_paths(episode_id).delivery_records_dir_path
    if not delivery_records_dir_path.is_dir():
        return []
    return sorted(path for path in delivery_records_dir_path.iterdir() if (path / DELIVERY_RECORD_FILE_NAME).is_file())


def load_delivery_record(series: Series, record_dir_path: Path) -> DeliveryRecord:
    record_file_path = record_dir_path / DELIVERY_RECORD_FILE_NAME
    return load_json_model(DeliveryRecord, record_file_path,
                           series.convert_path_to_production_relative_path(record_file_path))


def load_latest_delivery_record(series: Series, episode_id: str) -> DeliveryRecord | None:
    record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
    return load_delivery_record(series, record_dir_paths[-1]) if record_dir_paths else None


def find_delivery_record_dir_path_in_effect_at(series: Series, episode_id: str, moment: datetime) -> Path | None:
    """The folder of the delivery record in effect at `moment`: the latest one delivered at or before it. None when
    the episode had not been delivered by then."""
    found = None
    for record_dir_path in list_delivery_record_dir_paths(series, episode_id):
        if load_delivery_record(series, record_dir_path).delivered_at > moment:
            break
        found = record_dir_path
    return found


def load_delivered_timeline(series: Series, record_dir_path: Path) -> Timeline | None:
    timeline_file_path = record_dir_path / "timeline.json"
    return load_json_model(Timeline, timeline_file_path,
                           series.convert_path_to_production_relative_path(timeline_file_path)) \
        if timeline_file_path.exists() else None


def load_delivered_script(series: Series, record_dir_path: Path) -> Script | None:
    script_file_path = record_dir_path / "script.yaml"
    return load_yaml_model(Script, script_file_path,
                           series.convert_path_to_production_relative_path(script_file_path)) \
        if script_file_path.exists() else None


# Delivering ---------------------------------------------------------------------------------------------------------
def find_delivery_problems(series: Series, episode_id: str, script: Script) -> list[str]:
    """Why delivery is refused, checked in the order the design gives."""
    episode_paths = series.get_episode_paths(episode_id)
    render_file_paths = (episode_paths.render_video_file_path, episode_paths.render_subtitles_file_path,
                         episode_paths.render_cover_file_path, episode_paths.render_timeline_file_path)
    missing_file_paths = [path for path in render_file_paths if not path.exists()]
    if missing_file_paths:
        return [f"render/{path.name} is missing: render the episode (explainer-studio render {episode_id})"
                for path in missing_file_paths]
    if not episode_paths.render_automatic_checks_file_path.exists():
        return [f"render/automatic-checks.json is missing: render again (explainer-studio render {episode_id})"]
    problems = []
    timeline = load_json_model(Timeline, episode_paths.render_timeline_file_path, f"{episode_id}/render/timeline.json")
    current_narration_digest = compute_script_narration_digest(script)
    if timeline.narration_digest != current_narration_digest:
        problems.append(f"the render has narration {timeline.narration_digest}, but the script's narration is now "
                        f"{current_narration_digest}: render again (explainer-studio render {episode_id})")
    automatic_checks = load_json_model(AutomaticChecks, episode_paths.render_automatic_checks_file_path,
                                       f"{episode_id}/render/automatic-checks.json")
    problems += [f"automatic check {issue.check_name} in scene {issue.scene_id}"
                 + (f", beat {issue.beat_id}" if issue.beat_id else "") + f": {issue.detail}"
                 for issue in automatic_checks.find_blocking_issues()]
    # the cards, so the video page shows the chapters and the whiteboard from the moment of delivery
    from .chapters import find_episode_notes_problems

    problems += find_episode_notes_problems(series, episode_id, timeline)
    return problems


def format_delivery_record_dir_name(moment: datetime) -> str:
    """A delivery record's folder name: the UTC delivered time without colons, so the folders sort in delivery order
    everywhere."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H%M%SZ")


def _choose_delivery_time(series: Series, episode_id: str) -> datetime:
    """Now, moved on by a second while a record folder of that second exists."""
    delivery_time = get_current_time()
    delivery_records_dir_path = series.get_episode_paths(episode_id).delivery_records_dir_path
    while (delivery_records_dir_path / format_delivery_record_dir_name(delivery_time)).exists():
        delivery_time += timedelta(seconds=1)
    return delivery_time


@contextlib.contextmanager
def _explain_replace_failure(path: Path):
    """Turn Windows' refusal to replace a file another program has open into a clear error."""
    try:
        yield
    except PermissionError:
        raise StudioError(f"could not replace {path.name}", "another program has the file open (a video player or "
                          "an editor)", f"close the program that has {path} open, then run deliver again") from None


def _remove_previous_delivered_files(series: Series, previous_record: DeliveryRecord | None) -> None:
    if previous_record is None:
        return
    for file_name in previous_record.files.list_file_names():
        with _explain_replace_failure(series.root_dir_path / file_name):
            (series.root_dir_path / file_name).unlink(missing_ok=True)


def deliver(series: Series, episode_id: str) -> DeliveryResult:
    plan = load_plan(series)
    title = plan.find_episode(episode_id).title
    language_code = plan.resolve_episode_language_code(episode_id)
    script = load_script(series, episode_id)
    problems = find_delivery_problems(series, episode_id, script)
    if problems:
        raise StudioError(f"{episode_id} cannot be delivered yet", f"{len(problems)} problem(s)",
                          "fix these, then run deliver again", problems)
    episode_paths = series.get_episode_paths(episode_id)
    previous_record = load_latest_delivery_record(series, episode_id)
    delivery_time = _choose_delivery_time(series, episode_id)
    deliverable_stem = series.format_deliverable_stem(episode_id, title)
    subtitles_file_name = f"{deliverable_stem}.{language_code}.srt"
    delivered_files = DeliveredFiles(
        video_file_name=f"{deliverable_stem}.mp4", cover_file_name=f"{deliverable_stem}.png",
        subtitles=[DeliveredSubtitles(language_code=language_code, file_name=subtitles_file_name)])
    earlier_versions = list_earlier_versions_since_last_delivery(series, episode_id, __version__)
    record = DeliveryRecord(delivered_at=delivery_time, explainer_studio_version=__version__,
                            earlier_explainer_studio_versions=earlier_versions, files=delivered_files)
    record_dir_path = episode_paths.delivery_records_dir_path / format_delivery_record_dir_name(delivery_time)

    # The record is complete before any file in the series folder moves, so moved files always have their record.
    # Creating the folder claims it, so a second deliver started in the same second stops here instead of removing
    # this one's record.
    record_dir_path.mkdir(parents=True)
    try:
        shutil.copyfile(episode_paths.render_timeline_file_path, record_dir_path / "timeline.json")
        shutil.copyfile(episode_paths.script_file_path, record_dir_path / "script.yaml")
        write_json_model(record_dir_path / DELIVERY_RECORD_FILE_NAME, record)
    except BaseException:
        shutil.rmtree(record_dir_path, ignore_errors=True)
        raise

    has_moved_any_file = False
    try:
        _remove_previous_delivered_files(series, previous_record)
        for source, file_name in ((episode_paths.render_video_file_path, delivered_files.video_file_name),
                                  (episode_paths.render_subtitles_file_path, subtitles_file_name),
                                  (episode_paths.render_cover_file_path, delivered_files.cover_file_name)):
            with _explain_replace_failure(series.root_dir_path / file_name):
                os.replace(source, series.root_dir_path / file_name)
            has_moved_any_file = True
    except BaseException:
        if not has_moved_any_file:  # nothing of this delivery reached the series folder: it did not happen
            shutil.rmtree(record_dir_path, ignore_errors=True)
        raise
    clear_versions_since_last_delivery(series, episode_id)
    return DeliveryResult(record, record_dir_path, find_scene_ids_settled_while_lost(series, episode_id, script))
