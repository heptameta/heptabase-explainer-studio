"""episodes/<episode>/feedback.json: every comment and survey answer an episode received, across deliveries.

Which video an item is about follows from its time: one given before the latest delivery's `delivered_at` is about an
older video. Writes go through the `feedback` commands or the page server (same code); the agent reads the file
directly.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

ResolutionCategory = Literal["question", "teaching", "production", "direction"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Resolution(StrictModel):
    category: ResolutionCategory
    note: str
    resolved_at: AwareDatetime
    shared_at: AwareDatetime | None = None


class MomentAnchor(StrictModel):
    """A comment about a moment of the video it was made on."""

    kind: Literal["moment"]
    time_seconds: float = Field(ge=0, allow_inf_nan=False)


class EpisodeAnchor(StrictModel):
    """A comment about the whole episode."""

    kind: Literal["episode"]


# what a comment is about
CommentAnchor = Annotated[MomentAnchor | EpisodeAnchor, Field(discriminator="kind")]


class Comment(StrictModel):
    id: str  # c-1, c-2, ...
    anchor: CommentAnchor
    text: str
    origin: Literal["page", "chat"]
    created_at: AwareDatetime
    shared_at: AwareDatetime | None = None
    resolution: Resolution | None = None


# The survey: the fixed questions the video page asks about the delivered video. Each answer kind is one question.
class RatingAnswer(StrictModel):
    """How the user rated a delivered video."""

    kind: Literal["rating"]
    value: Literal["good", "okay", "bad"]
    answered_at: AwareDatetime
    shared_at: AwareDatetime | None = None


class WatchDepthAnswer(StrictModel):
    """How closely the user watched a delivered video (dev mode asks): how much their comments and rating can be read
    into."""

    kind: Literal["watch_depth"]
    value: Literal["closely", "skimmed", "partly"]
    answered_at: AwareDatetime
    shared_at: AwareDatetime | None = None


SurveyAnswer = Annotated[RatingAnswer | WatchDepthAnswer, Field(discriminator="kind")]
SurveyAnswerKind = Literal["rating", "watch_depth"]


class Feedback(StrictModel):
    # the feedback id: a UUID v4 made on the user's computer; every feedback bundle of the episode carries it
    id: str
    # the number in the last comment id handed out; it never goes down, so a deleted comment's id is never reused
    # (the team matches a comment across feedback bundles by its id)
    last_comment_number: int = 0
    comments: list[Comment] = []
    # the current answer of a kind is the latest of that kind given since the latest delivery
    survey_answers: list[SurveyAnswer] = []
