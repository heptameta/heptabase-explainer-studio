"""episodes/<episode>/notes.yaml: the delivered episode as a few chapters made of its scenes, and for each scene a
short summary and its cards. The video page lists the chapters and scenes in its outline and shows the cards on
the series' whiteboard; the agent writes the file while the episode is made.

A card is one claim, written in Hepta Markdown (the Markdown Heptabase cards are made of): its heading is the claim, a
full sentence, and the numbered points under it are what supports it (reasons, evidence, examples, steps), with the key
phrase of a point highlighted. Arrows between cards show how the argument goes. Read without the video, the cards teach
what it teaches; read after it, their titles and highlights bring it back. All the series' episodes share one
whiteboard, so a card may continue from an earlier episode's card."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

KEY_PATTERN = r"^[a-z0-9_]+$"
# a picture is a line of its own: ![caption](source), the source a frame (frame:<beat id>) or a file in production/
PICTURE_LINE_PATTERN = re.compile(r"^!\[([^\]\n]*)\]\(([^()\s]+)\)$")
FRAME_SOURCE_PREFIX = "frame:"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Card(StrictModel):
    id: str = Field(pattern=KEY_PATTERN)  # unique in the episode; <episode>/<card id> elsewhere
    # yellow: one of the episode's central claims; green: a conclusion cards lead to; red: a common, costly mistake
    color: Literal["yellow", "green", "red"] | None = None
    # the arrows from this card to the cards of this episode the argument goes on to
    leads_to: list[Annotated[str, Field(pattern=KEY_PATTERN)]] = Field(default_factory=list)
    # the arrows into this card from earlier episodes' cards, as <episode>/<card id>: the argument picks up there
    continues_from: list[Annotated[str, Field(pattern=r"^[a-z0-9_]+/[a-z0-9_]+$")]] = Field(default_factory=list)
    content: str = Field(min_length=1)  # Hepta Markdown: the claim as the first heading, then numbered points


class Scene(StrictModel):
    id: str  # a scene id of the episode's script
    title: str = Field(min_length=1)  # the scene's knowledge point
    summary: str = Field(min_length=1)  # the scene's core knowledge, in one or two sentences
    key_frame: str  # a beat id of this scene
    cards: list[Card] = Field(min_length=1)


class Chapter(StrictModel):
    id: str = Field(pattern=KEY_PATTERN)  # unique in the episode
    title: str = Field(min_length=1)  # the chapter's knowledge point, in plain words
    scenes: list[Scene] = Field(min_length=1)  # in the video's order


class Notes(StrictModel):
    chapters: list[Chapter] = Field(min_length=1)

    def list_scenes(self) -> list[Scene]:
        return [scene for chapter in self.chapters for scene in chapter.scenes]

    def list_cards(self) -> list[Card]:
        return [card for scene in self.list_scenes() for card in scene.cards]


def iterate_picture_sources(content: str) -> Iterator[str]:
    """The sources of a card's pictures, in order: `frame:<beat id>` or a path relative to production/."""
    for line in content.splitlines():
        match = PICTURE_LINE_PATTERN.match(line.strip())
        if match:
            yield match.group(2)
