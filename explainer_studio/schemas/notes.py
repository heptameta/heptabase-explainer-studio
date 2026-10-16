"""episodes/<episode>/notes.yaml: the delivered episode as a few parts made of its scenes, and for each scene a short
summary and a handout. The video page shows them as the chapters view and the whiteboard; the agent writes the file
after delivering.

A handout is cards, one claim each: the title is the claim, a full sentence, and the numbered points under it are what
supports it (reasons, evidence, examples, steps), with the key phrase of a point highlighted. Arrows between cards
show how the argument goes. Read without the video, the cards teach what it teaches; read after it, their titles and
highlights bring it back. All the series' episodes share one whiteboard, so a card may lead to another episode's card."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Part(StrictModel):
    title: str = Field(min_length=1)  # the part's knowledge point, in plain words
    segments: list[str] = Field(min_length=1)  # scene ids, in the video's order


class Point(StrictModel):
    """One numbered point of a card, written as its text alone or with sub-points and a picture under it. In the
    text, **bold** marks a term where it is defined and ==highlight== the key phrase."""
    text: str = Field(min_length=1)
    points: list[Point] = Field(default_factory=list)  # sub-points: a., b., then i., ii.
    frame: str | None = None  # a beat id: the video's picture when the beat's line ends
    image: str | None = None  # a credits.yaml asset_file_path (relative to production/)
    caption: str | None = None  # with frame or image

    @model_validator(mode="before")
    @classmethod
    def accept_text_alone(cls, value: Any) -> Any:
        return {"text": value} if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_picture(self) -> Point:
        if self.frame and self.image:
            raise ValueError("a point has one picture: a frame or an image, not both")
        if self.caption is not None and not (self.frame or self.image):
            raise ValueError("a caption belongs to a frame or an image")
        return self


class Card(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")  # unique in the episode
    title: str = Field(min_length=1)  # the claim, a full sentence
    # yellow: one of the episode's central claims; green: a conclusion cards lead to; red: a common, costly mistake
    color: Literal["yellow", "green", "red"] | None = None
    points: list[Point] = Field(min_length=1)
    # the arrows from this card on the series' whiteboard: a card id of this episode, or <episode>/<card id> of another
    leads_to: list[Annotated[str, Field(pattern=r"^(ep\d+/)?[a-z0-9_]+$")]] = Field(default_factory=list)


class Segment(StrictModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)  # the segment's core knowledge, in one or two sentences
    key_frame: str  # a beat id of this scene
    cards: list[Card] = Field(min_length=1)


class Notes(StrictModel):
    parts: list[Part] = Field(min_length=1)
    segments: dict[str, Segment]


def iterate_points(points: list[Point]) -> Iterator[Point]:
    """Every point and sub-point, depth first."""
    for point in points:
        yield point
        yield from iterate_points(point.points)
