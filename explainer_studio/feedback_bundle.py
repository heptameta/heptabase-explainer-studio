"""Sharing feedback with the team: packing the feedback bundle, sending it, and marking what it carried as shared.

A feedback bundle is an episode's feedback plus what is needed to analyse it, as it stands when it is packed; the zip is
only how a share sends it. Paths in the zip are those in the series' `production/` folder, and the team reads the files
as they are:

- `episodes/<episode>/feedback.json`: the episode's comments with their resolutions, and its survey answers;
- `episodes/<episode>/comment-screenshot-sheets/<comment id>.jpg`: the comment screenshot sheet of every comment
  about a moment in that `feedback.json`, when it has one;
- `metadata.json`, `script.yaml` and `timeline.json` of every delivery record of the episode;
- `plan.yaml` and `gaps.json`;
- `environment.json`: the Explainer Studio version and the operating system;
- `cost.json`: the cost report of the series' planning and the episode (see `cost`).

A share from the video page and one agreed in chat send the same bundle. Every bundle is complete, so the latest bundle
of an episode supersedes its earlier ones. Never the sources, the video, the audio or any other file. The `shared_at`
fields record which bundle first carried each item as it is now (a changed comment or survey answer is unshared
again), so a share knows whether there is anything new to send.
"""

from __future__ import annotations

import io
import os
import platform
import zipfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from . import __version__
from .cost import check_has_episode_work, compute_cost_report, filter_cost_report_to_episode, format_episode_cost
from .deliver import list_delivery_record_dir_paths
from .errors import StudioError
from .feedback import edit_feedback, find_comment_beat, format_comment_anchor, load_feedback
from .file_io import get_current_time, hold_lock, serialize_json, write_json_model
from .gaps import load_gaps
from .paths import Series
from .schemas.cost import CostReport
from .schemas.feedback import Comment, Feedback, MomentAnchor, Resolution, SurveyAnswer
from .schemas.gaps import Gap, Gaps

# Where a share sends a bundle. EXPLAINER_STUDIO_FEEDBACK_URL overrides it (a local receiver while developing and
# testing).
FEEDBACK_URL = "https://api.heptabase.com/v1/explainerStudio/submitFeedbackBundle"
FEEDBACK_URL_ENV = "EXPLAINER_STUDIO_FEEDBACK_URL"
FEEDBACK_ID_HEADER = "X-Explainer-Studio-Feedback-Id"
EXPLAINER_STUDIO_VERSION_HEADER = "X-Explainer-Studio-Version"
DELIVERY_RECORD_FILE_NAMES = ("metadata.json", "script.yaml", "timeline.json")


@dataclass(frozen=True)
class FeedbackBundle:
    episode_id: str
    feedback: Feedback  # feedback.json as packed: `mark_bundle_shared` marks what it had unshared
    gaps: Gaps  # gaps.json as packed
    cost_report: CostReport  # cost.json
    path_to_content_map: dict[str, str | bytes]  # path in the zip -> content

    def serialize_zip(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, content in self.path_to_content_map.items():
                archive.writestr(path, content)
        return buffer.getvalue()


@dataclass(frozen=True)
class UnsharedItems:
    """What a bundle carries for the first time: the items no bundle has carried as they are now."""

    comments: list[Comment]
    comment_id_to_resolution_map: dict[str, Resolution]
    survey_answers: list[SurveyAnswer]
    gaps: list[Gap]

    @property
    def has_feedback(self) -> bool:
        """Whether there is new feedback, what the user gave: a comment or a survey answer. The video page's share
        needs some; resolutions and gaps travel with it."""
        return bool(self.comments or self.survey_answers)

    def __bool__(self) -> bool:
        return self.has_feedback or bool(self.comment_id_to_resolution_map or self.gaps)


def resolve_unshared_items(feedback: Feedback, gaps: Gaps) -> UnsharedItems:
    return UnsharedItems(
        comments=[comment for comment in feedback.comments if comment.shared_at is None],
        comment_id_to_resolution_map={comment.id: comment.resolution for comment in feedback.comments
                                      if comment.resolution is not None and comment.resolution.shared_at is None},
        survey_answers=[answer for answer in feedback.survey_answers if answer.shared_at is None],
        gaps=[gap for gap in gaps.gaps if gap.shared_at is None])


def _list_comment_screenshot_sheet_file_paths(series: Series, episode_id: str, feedback: Feedback) -> list[Path]:
    """The comment screenshot sheets of the comments about a moment in `feedback`: a sheet left behind by a deleted
    comment is never packed."""
    episode_paths = series.get_episode_paths(episode_id)
    return [episode_paths.get_comment_screenshot_sheet_file_path(comment.id) for comment in feedback.comments
            if isinstance(comment.anchor, MomentAnchor)]


def _read_series_file_bytes(series: Series, file_path: Path) -> bytes:
    """The bytes of a file in the series folder. Raises StudioError when a symbolic link or `..` below the series folder
    leads anywhere else: a bundle carries only the series' own files."""
    production_relative_path = series.convert_path_to_production_relative_path(file_path)
    if file_path.resolve() != series.root_dir_path.resolve() / file_path.relative_to(series.root_dir_path):
        raise StudioError(f"{production_relative_path} is a symbolic link or leads outside its folder",
                          "Explainer Studio never makes one, and a feedback bundle carries only the series' own files",
                          "nothing was sent: tell the user, replace it with the file itself or remove it, then share "
                          "again")
    return file_path.read_bytes()


def pack_feedback_bundle(series: Series, episode_id: str) -> FeedbackBundle:
    """The bundle the episode would send now."""
    feedback = load_feedback(series, episode_id)
    gaps = load_gaps(series)
    cost_report = filter_cost_report_to_episode(compute_cost_report(series), episode_id)
    episode_paths = series.get_episode_paths(episode_id)
    path_to_content_map: dict[str, str | bytes] = {
        series.convert_path_to_production_relative_path(episode_paths.feedback_file_path):
            serialize_json(feedback.model_dump(mode="json")),
        series.convert_path_to_production_relative_path(series.plan_file_path):
            _read_series_file_bytes(series, series.plan_file_path),
        series.convert_path_to_production_relative_path(series.gaps_file_path):
            serialize_json(gaps.model_dump(mode="json")),
    }
    delivery_record_file_paths = [record_dir_path / file_name
                                  for record_dir_path in list_delivery_record_dir_paths(series, episode_id)
                                  for file_name in DELIVERY_RECORD_FILE_NAMES]
    for packed_file_path in [*_list_comment_screenshot_sheet_file_paths(series, episode_id, feedback),
                             *delivery_record_file_paths]:
        if packed_file_path.is_file():
            production_relative_path = series.convert_path_to_production_relative_path(packed_file_path)
            path_to_content_map[production_relative_path] = _read_series_file_bytes(series, packed_file_path)
    path_to_content_map["environment.json"] = serialize_json({"explainer_studio_version": __version__,
                                                         "operating_system": platform.platform(terse=True)})
    path_to_content_map["cost.json"] = serialize_json(cost_report.model_dump(mode="json"))
    return FeedbackBundle(episode_id, feedback, gaps, cost_report, path_to_content_map)


def mark_bundle_shared(series: Series, episode_id: str, bundle: FeedbackBundle) -> None:
    """Record that `bundle` was sent: what it carried for the first time is now shared. Called only after the receiver
    accepted it. Anything added or changed since the bundle was packed stays unshared."""
    sent_at = get_current_time()
    new_items = resolve_unshared_items(bundle.feedback, bundle.gaps)
    comment_id_to_content_map = {comment.id: (comment.text, comment.anchor) for comment in new_items.comments}
    survey_answer_keys = {(answer.kind, answer.answered_at, answer.value) for answer in new_items.survey_answers}
    with edit_feedback(series, episode_id) as feedback:
        feedback.id = bundle.feedback.id  # the first bundle of an episode without feedback.json fixes its id
        for comment in feedback.comments:
            if comment.shared_at is None \
                    and comment_id_to_content_map.get(comment.id) == (comment.text, comment.anchor):
                comment.shared_at = sent_at
            packed_resolution = new_items.comment_id_to_resolution_map.get(comment.id)
            if comment.resolution is not None and packed_resolution is not None \
                    and comment.resolution.resolved_at == packed_resolution.resolved_at:
                comment.resolution.shared_at = sent_at
        for answer in feedback.survey_answers:
            if (answer.kind, answer.answered_at, answer.value) in survey_answer_keys and answer.shared_at is None:
                answer.shared_at = sent_at
    gap_ids = {gap.id for gap in new_items.gaps}
    if gap_ids:
        with hold_lock(series.gaps_file_path):
            gaps = load_gaps(series)
            for gap in gaps.gaps:
                if gap.id in gap_ids and gap.shared_at is None:
                    gap.shared_at = sent_at
            write_json_model(series.gaps_file_path, gaps)


def format_feedback_bundle_contents(series: Series, bundle: FeedbackBundle) -> list[str]:
    """What a bundle carries, for `feedback share --dry-run` and the agent's message asking the user."""
    new_items = resolve_unshared_items(bundle.feedback, bundle.gaps)
    lines = [f"feedback bundle for {bundle.episode_id} (feedback id {bundle.feedback.id}), new since the last share:"]
    for comment in new_items.comments:
        beat = find_comment_beat(series, bundle.episode_id, comment)
        beat_label = f" at beat {beat.beat_id}" if beat else ""
        comment_screenshot_sheet_path = series.convert_path_to_production_relative_path(
            series.get_episode_paths(bundle.episode_id).get_comment_screenshot_sheet_file_path(comment.id))
        comment_screenshot_sheet_label = (" + comment screenshot sheet"
                                          if comment_screenshot_sheet_path in bundle.path_to_content_map else "")
        lines.append(f"  comment {comment.id} {format_comment_anchor(comment.anchor)}{beat_label}: {comment.text}"
                     f"{comment_screenshot_sheet_label}")
    lines.append(f"  {len(new_items.comment_id_to_resolution_map)} resolution(s), "
                 f"{len(new_items.survey_answers)} survey answer(s), {len(new_items.gaps)} gap(s)")
    comment_screenshot_sheet_count = sum(
        series.convert_path_to_production_relative_path(comment_screenshot_sheet_file_path)
        in bundle.path_to_content_map
        for comment_screenshot_sheet_file_path in _list_comment_screenshot_sheet_file_paths(series, bundle.episode_id,
                                                                                            bundle.feedback))
    delivery_record_count = len(list_delivery_record_dir_paths(series, bundle.episode_id))
    lines.append(f"  also, whole: the episode's feedback.json (every comment, resolution and survey answer so "
                 f"far), {comment_screenshot_sheet_count} comment screenshot sheet(s) (the sheets of the comments "
                 f"about a moment that exist), {delivery_record_count} delivery record(s) (script and timeline), "
                 f"plan.yaml, gaps.json, environment.json ({__version__}, {platform.platform(terse=True)})")
    cost_report = bundle.cost_report
    unavailable_reason = cost_report.unavailable_reason or (
        None if check_has_episode_work(cost_report, bundle.episode_id)
        else "no work on this episode is in the agent's transcripts")
    lines.append(f"  cost of making it: not available ({unavailable_reason})" if unavailable_reason
                 else f"  cost of making it, {format_episode_cost(cost_report, bundle.episode_id)} (sent for the "
                      "series' plan and this episode: the agent's usage without dollars, and the narration's estimated "
                      "cost)")
    lines.append("  never: the source files, the video, the audio")
    return lines


# Sending -------------------------------------------------------------------------------------------------------------
def resolve_feedback_url() -> str:
    return os.environ.get(FEEDBACK_URL_ENV, "").strip() or FEEDBACK_URL


def share_feedback(series: Series, episode_id: str) -> UnsharedItems:
    """Send the episode's bundle when it has something new, and mark that shared. Returns what the bundle carried for
    the first time: empty when there was nothing new, and then nothing was sent. On failure nothing is marked and
    StudioError says so."""
    bundle = pack_feedback_bundle(series, episode_id)
    new_items = resolve_unshared_items(bundle.feedback, bundle.gaps)
    if not new_items:
        return new_items
    try:
        response = httpx.post(resolve_feedback_url(), content=bundle.serialize_zip(), timeout=120,
                              headers={"Content-Type": "application/zip", FEEDBACK_ID_HEADER: bundle.feedback.id,
                                       EXPLAINER_STUDIO_VERSION_HEADER: __version__,
                                       "User-Agent": f"explainer-studio/{__version__}"})
        failure = None if 200 <= response.status_code < 300 else f"the receiver answered HTTP {response.status_code}"
    except httpx.HTTPError as error:
        failure = f"{type(error).__name__}: {error}"
    if failure:
        raise StudioError("the feedback was not sent", failure,
                          "nothing was marked as shared; tell the user it was not sent and try again at the next "
                          "agreed share")
    mark_bundle_shared(series, episode_id, bundle)
    return new_items
