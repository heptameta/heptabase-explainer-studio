"""production/heptabase-whiteboard.json: the Heptabase whiteboard the series' whiteboard was saved to, and the Heptabase
id of everything Studio put on it. Written by the page server; the file exists once the user pressed Save (an episode
is on the whiteboard once it has `imported_at`), and deleting it (unlinking) makes the next save create a new
whiteboard.

Studio makes every id. Before it asks Heptabase to add an episode it records the episode's ids here without
`imported_at`; `imported_at` is added once Heptabase confirmed. An episode with ids but no `imported_at` may or may not
be in Heptabase, and is sent again with the same ids, which Heptabase does not add twice. No token is ever written
here."""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HeptabaseWhiteboardChapter(StrictModel):
    section_id: str


class HeptabaseWhiteboardCard(StrictModel):
    card_id: str
    card_instance_id: str  # the card on this whiteboard


class HeptabaseWhiteboardEpisode(StrictModel):
    imported_at: AwareDatetime | None = None  # when Heptabase confirmed it has the episode
    section_id: str
    chapters: dict[str, HeptabaseWhiteboardChapter]  # by chapter id
    cards: dict[str, HeptabaseWhiteboardCard]  # by <episode>/<card id>
    # by <episode>/<card id>-><episode>/<card id>; an arrow from another episode is kept by the episode it leads into
    connections: dict[str, str]


class HeptabaseWhiteboard(StrictModel):
    issuer: str  # the Heptabase it is saved in: its OAuth issuer
    account_id: str  # the account that saved it
    whiteboard_id: str
    # the pictures uploaded for the cards, by their source: frame:<episode>/<beat id> or a path relative to production/
    files: dict[str, str]
    episodes: dict[str, HeptabaseWhiteboardEpisode]  # by episode id
