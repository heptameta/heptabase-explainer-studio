"""Feedback on delivered episodes: comments, their resolutions and survey answers. `feedback_bundle` shares them.

`episodes/<episode>/feedback.json` is written only here, by the `feedback` commands and by the video page's server, each
change under the file's lock. Which video an item is about follows from its time: one given before the latest
delivery's `delivered_at` is about an older video. What was said at a comment's moment comes from the delivery record
in effect when the comment was made, so comments on older videos keep pointing at the right line. A comment about a
moment (a moment anchor) gets a comment screenshot sheet, drawn from the video at the series root when the comment is
made or its anchor changes, and deleted with the comment.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast, get_args

from .deliver import (
    find_delivery_record_dir_path_in_effect_at,
    list_delivery_record_dir_paths,
    load_delivered_script,
    load_delivered_timeline,
    load_delivery_record,
    load_latest_delivery_record,
)
from .errors import StudioError
from .file_io import get_current_time, hold_lock, load_json_model, write_bytes_atomic, write_json_model
from .paths import Series
from .schemas.feedback import (
    Comment,
    CommentAnchor,
    Feedback,
    MomentAnchor,
    RatingAnswer,
    Resolution,
    ResolutionCategory,
    SurveyAnswer,
    SurveyAnswerKind,
    WatchDepthAnswer,
)

MAX_COMMENT_CHARACTERS = 4000
RESOLUTION_CATEGORIES: tuple[str, ...] = get_args(ResolutionCategory)
# the survey's questions, in the order the video page asks them
SURVEY_ANSWER_MODEL_BY_KIND_MAP: dict[SurveyAnswerKind, type[RatingAnswer | WatchDepthAnswer]] = {
    "rating": RatingAnswer, "watch_depth": WatchDepthAnswer}


def format_time(time_seconds: float) -> str:
    whole_seconds = int(time_seconds)
    hours, remaining_seconds = divmod(whole_seconds, 3600)
    if hours:
        return f"{hours}:{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}"
    return f"{remaining_seconds // 60}:{remaining_seconds % 60:02d}"


def format_comment_anchor(anchor: CommentAnchor) -> str:
    """A comment's moment as a player shows it (1:23), or "-" for a comment about the whole episode."""
    return format_time(anchor.time_seconds) if isinstance(anchor, MomentAnchor) else "-"


# What was said when --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class DeliveredBeat:
    """A beat of a delivery placed in video time, with the narration text its script had then."""

    beat_id: str
    start_seconds: float
    narration_text: str


def load_delivered_beats(series: Series, record_dir_path: Path) -> tuple[DeliveredBeat, ...] | None:
    """A delivery's beats in video time, or None when its record lacks the timeline or the script."""
    timeline = load_delivered_timeline(series, record_dir_path)
    script = load_delivered_script(series, record_dir_path)
    if timeline is None or script is None:
        return None
    narration_text_by_beat_id_map = {beat.id: beat.narration_text for beat in script.list_beats()}
    beats = [DeliveredBeat(beat.beat_id, beat.start_seconds, narration_text_by_beat_id_map.get(beat.beat_id, ""))
             for scene in timeline.scenes for beat in scene.beats]
    return tuple(sorted(beats, key=lambda beat: beat.start_seconds))


def find_beat_at(beats: tuple[DeliveredBeat, ...] | None, time_seconds: float) -> DeliveredBeat | None:
    """The beat being said at `time_seconds`: the last one that had started (a pause belongs to the line before it)."""
    if beats is None:
        return None
    found = None
    for beat in beats:
        if beat.start_seconds > time_seconds + 1e-6:
            break
        found = beat
    return found


def find_comment_beat(series: Series, episode_id: str, comment: Comment) -> DeliveredBeat | None:
    """The beat being said at the comment's moment, in the video the comment was made on (the delivery record in
    effect when it was made). None for a comment about the whole episode."""
    if not isinstance(comment.anchor, MomentAnchor):
        return None
    record_dir_path = find_delivery_record_dir_path_in_effect_at(series, episode_id, comment.created_at)
    return (find_beat_at(load_delivered_beats(series, record_dir_path), comment.anchor.time_seconds)
            if record_dir_path else None)


# Which video an item is about ----------------------------------------------------------------------------------------
def find_latest_delivery_time(series: Series, episode_id: str) -> datetime | None:
    """When the episode was last delivered: the video at the series root is from then. None when it has not been
    delivered."""
    latest_record = load_latest_delivery_record(series, episode_id)
    return latest_record.delivered_at if latest_record else None


def require_latest_delivery_time(series: Series, episode_id: str) -> datetime:
    """When the episode was last delivered; raises StudioError when it has not been delivered."""
    latest_delivery_time = find_latest_delivery_time(series, episode_id)
    if latest_delivery_time is None:
        raise StudioError(f"{episode_id} has not been delivered", "feedback is about a delivered video",
                          f"explainer-studio deliver {episode_id}")
    return latest_delivery_time


def check_is_about_current_video(given_at: datetime, latest_delivery_time: datetime | None) -> bool:
    """Whether an item given at `given_at` is about the current video: it was given at or after the latest
    delivery."""
    return latest_delivery_time is None or given_at >= latest_delivery_time


def resolve_current_survey_answer(feedback: Feedback, kind: SurveyAnswerKind,
                                  latest_delivery_time: datetime | None) -> SurveyAnswer | None:
    """The current video's answer of `kind`: the latest of that kind given since the latest delivery."""
    current_answers = [answer for answer in feedback.survey_answers if answer.kind == kind
                       and check_is_about_current_video(answer.answered_at, latest_delivery_time)]
    return max(current_answers, key=lambda answer: answer.answered_at, default=None)


# Comment screenshot sheets -------------------------------------------------------------------------------------------
def draw_comment_screenshot_sheet(series: Series, episode_id: str, comment: Comment) -> Path | None:
    """Replace the comment's comment screenshot sheet with one of the seconds around its moment in the video at the
    series root. Returns the sheet, or None when there is none: the comment is about the whole episode, it was made on
    an older video (which is gone), or the video or its record cannot be read. Every failure leaves the comment without
    a sheet and raises nothing, since the comment itself is already saved."""
    episode_paths = series.get_episode_paths(episode_id)
    comment_screenshot_sheet_file_path = episode_paths.get_comment_screenshot_sheet_file_path(comment.id)
    try:
        comment_screenshot_sheet_file_path.unlink(missing_ok=True)
        if not isinstance(comment.anchor, MomentAnchor):
            return None
        moment_seconds = comment.anchor.time_seconds
        record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
        latest_record = load_delivery_record(series, record_dir_paths[-1]) if record_dir_paths else None
        if latest_record is None or not check_is_about_current_video(comment.created_at, latest_record.delivered_at):
            return None
        video_file_path = series.root_dir_path / latest_record.files.video_file_name
        if not video_file_path.is_file():
            return None
        from .rendering.screenshots import (
            build_comment_screenshot_sheet_jpeg,
            grab_frames,
            resolve_comment_screenshot_sheet_times,
        )

        timeline = load_delivered_timeline(series, record_dir_paths[-1])
        times_seconds = resolve_comment_screenshot_sheet_times(moment_seconds,
                                                               timeline.duration_seconds if timeline else None)
        time_seconds_to_frame_map = grab_frames(video_file_path, times_seconds)
        if not time_seconds_to_frame_map:  # a video without frames
            return None
        write_bytes_atomic(comment_screenshot_sheet_file_path, build_comment_screenshot_sheet_jpeg(
            [(time_seconds, time_seconds_to_frame_map[time_seconds]) for time_seconds in times_seconds],
            moment_seconds))
    except Exception:  # noqa: BLE001 - a damaged record or video, a full disk: no sheet, never a failed comment
        with contextlib.suppress(OSError):
            comment_screenshot_sheet_file_path.unlink(missing_ok=True)
        return None
    return comment_screenshot_sheet_file_path


# Reading and writing feedback.json -----------------------------------------------------------------------------------
def load_feedback(series: Series, episode_id: str) -> Feedback:
    feedback_file_path = series.get_episode_paths(episode_id).feedback_file_path
    if not feedback_file_path.exists():
        return Feedback(id=str(uuid.uuid4()))
    return load_json_model(Feedback, feedback_file_path, f"{episode_id}/feedback.json")


@contextlib.contextmanager
def edit_feedback(series: Series, episode_id: str) -> Iterator[Feedback]:
    """Read, change and write feedback.json under its lock."""
    feedback_file_path = series.get_episode_paths(episode_id).feedback_file_path
    with hold_lock(feedback_file_path):
        feedback = load_feedback(series, episode_id)
        yield feedback
        write_json_model(feedback_file_path, feedback)


def _find_comment(feedback: Feedback, episode_id: str, comment_id: str) -> Comment:
    for comment in feedback.comments:
        if comment.id == comment_id:
            return comment
    raise StudioError(f"{episode_id} has no comment {comment_id}",
                      f"its comments are {', '.join(comment.id for comment in feedback.comments) or 'none'}",
                      f"read production/episodes/{episode_id}/feedback.json for the comment ids")


def _clean_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise StudioError("the comment is empty", "a comment needs some text", "write what the viewer said")
    return cleaned[:MAX_COMMENT_CHARACTERS]


def _round_anchor_time(anchor: CommentAnchor) -> CommentAnchor:
    """The anchor with its moment kept to the hundredth of a second."""
    return (MomentAnchor(kind="moment", time_seconds=round(anchor.time_seconds, 2)) if isinstance(anchor, MomentAnchor)
            else anchor)


def _parse_comment_number(comment: Comment) -> int:
    number_text = comment.id.removeprefix("c-")
    return int(number_text) if number_text.isdigit() else 0


def add_comment(series: Series, episode_id: str, text: str, anchor: CommentAnchor, origin: str = "chat") -> Comment:
    """Record a comment on the current video, and draw its comment screenshot sheet when it is about a moment."""
    require_latest_delivery_time(series, episode_id)
    with edit_feedback(series, episode_id) as feedback:
        # never reuse a number, even one whose comment was deleted (shares are matched on comment ids)
        feedback.last_comment_number = max([feedback.last_comment_number,
                                           *map(_parse_comment_number, feedback.comments)]) + 1
        comment = Comment(id=f"c-{feedback.last_comment_number}", anchor=_round_anchor_time(anchor),
                          text=_clean_text(text), origin=origin, created_at=get_current_time())
        feedback.comments.append(comment)
    draw_comment_screenshot_sheet(series, episode_id, comment)
    return comment


def edit_comment(series: Series, episode_id: str, comment_id: str, text: str | None = None,
                 anchor: CommentAnchor | None = None) -> Comment:
    """Change a comment's text or anchor (None keeps it). A changed comment is unshared again, so the next share
    carries it as new. A changed anchor draws its comment screenshot sheet again when the comment is about a moment of
    the current video, and removes it otherwise."""
    with edit_feedback(series, episode_id) as feedback:
        comment = _find_comment(feedback, episode_id, comment_id)
        previous_text, previous_anchor = comment.text, comment.anchor
        if text is not None:
            comment.text = _clean_text(text)
        if anchor is not None:
            comment.anchor = _round_anchor_time(anchor)
        if (comment.text, comment.anchor) != (previous_text, previous_anchor):
            comment.shared_at = None
    if comment.anchor != previous_anchor:
        draw_comment_screenshot_sheet(series, episode_id, comment)
    return comment


def delete_comment(series: Series, episode_id: str, comment_id: str) -> None:
    """Delete a comment and its comment screenshot sheet."""
    with edit_feedback(series, episode_id) as feedback:
        feedback.comments.remove(_find_comment(feedback, episode_id, comment_id))
    series.get_episode_paths(episode_id).get_comment_screenshot_sheet_file_path(comment_id).unlink(missing_ok=True)


def record_comment_resolution(series: Series, episode_id: str, comment_id: str, category: str, note: str) -> Comment:
    """Record how a comment was handled. A new note is unshared until the next agreed share."""
    if category not in RESOLUTION_CATEGORIES:
        raise StudioError(f"{category!r} is not a feedback category", f"use one of {', '.join(RESOLUTION_CATEGORIES)}")
    if not note.strip():
        raise StudioError("the resolution note is empty", "the note says why and what was done",
                          'write a note such as "this line was badly written: two unfamiliar names in one sentence"')
    with edit_feedback(series, episode_id) as feedback:
        comment = _find_comment(feedback, episode_id, comment_id)
        comment.resolution = Resolution(category=category, note=note.strip(),  # type: ignore[arg-type]
                                        resolved_at=get_current_time())
    return comment


def set_survey_answer(series: Series, episode_id: str, kind: str, value: str | None) -> None:
    """Record the user's answer to a survey question about the current video: `rating` (good, okay or bad) or
    `watch_depth` (closely, skimmed or partly, which dev mode asks); None removes the answer. Answering again since the
    latest delivery replaces the earlier answer, which is then unshared again. Raises StudioError for a question the
    survey does not ask or an answer it does not offer."""
    if kind not in SURVEY_ANSWER_MODEL_BY_KIND_MAP:
        raise StudioError(f"{kind!r} is not a survey question",
                          f"the survey asks {', '.join(SURVEY_ANSWER_MODEL_BY_KIND_MAP)}")
    survey_answer_kind = cast(SurveyAnswerKind, kind)
    answer_model = SURVEY_ANSWER_MODEL_BY_KIND_MAP[survey_answer_kind]
    values: tuple[str, ...] = get_args(answer_model.model_fields["value"].annotation)
    if value is not None and value not in values:
        raise StudioError(f"{value!r} is not an answer to {kind}", f"answer with one of {', '.join(values)}")
    latest_delivery_time = require_latest_delivery_time(series, episode_id)
    with edit_feedback(series, episode_id) as feedback:
        current = resolve_current_survey_answer(feedback, survey_answer_kind, latest_delivery_time)
        new_answer = None if value is None else answer_model(kind=survey_answer_kind,  # type: ignore[arg-type]
                                                               value=value, answered_at=get_current_time())
        if new_answer is None:
            if current is not None:
                feedback.survey_answers.remove(current)
        elif current is None:
            feedback.survey_answers.append(new_answer)
        elif current.value != new_answer.value:
            feedback.survey_answers[feedback.survey_answers.index(current)] = new_answer
