"""The series' whiteboard on the video page, and saving it to Heptabase.

One whiteboard for the whole series: a section per episode holding a section per chapter, a column of cards
per scene, and arrows between the cards, from every delivered episode whose cards pass `notes check`. The video page
shows it in Heptabase's own renderer, the web app's embedded whiteboard page in an iframe: Heptabase measures the
cards, Studio lays them out (in the page's script), and Heptabase shows them. Before the user saves, nothing leaves
the computer.

Saving puts every such episode on a new whiteboard in the user's Heptabase (`import_episodes`), and the series is then
linked to it (`production/heptabase-whiteboard.json`). Each episode goes onto it once, and only adds: whatever the
user changes there stays theirs. When the video page of a linked series opens, the episodes delivered since are laid
out below what the whiteboard holds and added the same way. Unlinking forgets the whiteboard (it stays in Heptabase);
the next save makes a new one.

The page's JSON is camelCase, as the page's other APIs."""

from __future__ import annotations

import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import heptabase_sign_in
from .chapters import find_frame_file_path, load_delivered_notes, read_card_picture
from .deliver import list_delivered_episodes, load_latest_delivery_record
from .errors import StudioError
from .file_io import get_current_time, hold_lock, load_json_model, write_json
from .paths import Series, parse_episode_number
from .plan import read_series_title
from .schemas.heptabase_whiteboard import (
    HeptabaseWhiteboard,
    HeptabaseWhiteboardCard,
    HeptabaseWhiteboardChapter,
    HeptabaseWhiteboardEpisode,
)
from .schemas.notes import FRAME_SOURCE_PREFIX, PICTURE_LINE_PATTERN, Card, Notes, iterate_picture_sources

EMBEDDED_WHITEBOARD_PATH = "/embed/whiteboard"
IMPORT_PATH = "/explainerStudio/importWhiteboardObjects"
UPLOAD_URL_PATH = "/getUploadUrl"
IMAGE_UPLOAD_TIMEOUT_SECONDS = 120
# pictures uploaded at once on a save
IMAGE_UPLOAD_WORKER_COUNT = 4
# Hepta Markdown's image of a file already in Heptabase
HEPTABASE_IMAGE_SOURCE_PREFIX = "hepta-image-ref:"
# Heptabase's refusals of the whiteboard itself: in the trash, deleted, or not the signed-in account's
WHITEBOARD_REFUSAL_CODES = ("whiteboard_trashed", "whiteboard_deleted", "forbidden")


class WhiteboardImportRefusedError(StudioError):
    """Studio did not ask Heptabase, for a reason on this computer; `code` tells the video page what can be done:
    `cards_changed` (lay the cards out again), `picture_unusable` (an agent fixes the card), `other_account` (another
    account than the one that saved the whiteboard is signed in)."""

    def __init__(self, code: str, what: str, why: str, next_step: str):
        super().__init__(what, why, next_step)
        self.code = code


@dataclass(frozen=True)
class WhiteboardEpisode:
    """A delivered episode whose cards pass `notes check` against its latest delivery."""
    id: str
    title: str
    notes: Notes

    @property
    def section_title(self) -> str:
        return f"EP{parse_episode_number(self.id):02d} {self.title}"

    def build_key(self, item_id: str) -> str:
        """The whiteboard key of one of the episode's chapters or cards: <episode>/<id>."""
        return f"{self.id}/{item_id}"

    def list_cards(self) -> list[tuple[str, Card]]:
        """Each card with its whiteboard key."""
        return [(self.build_key(card.id), card) for card in self.notes.list_cards()]

    @property
    def card_keys(self) -> set[str]:
        return {self.build_key(card.id) for card in self.notes.list_cards()}


# Pictures -------------------------------------------------------------------------------------------------------------
def build_image_key(source: str, episode_id: str) -> str:
    """A picture's key on the whiteboard: a frame names its episode (frame:<episode>/<beat id>), a file is its path in
    production/, so a credited asset two episodes show is one picture."""
    if source.startswith(FRAME_SOURCE_PREFIX):
        return f"{FRAME_SOURCE_PREFIX}{episode_id}/{source.removeprefix(FRAME_SOURCE_PREFIX)}"
    return source


def _parse_frame_key(image_key: str) -> tuple[str, str] | None:
    """A frame's episode and beat id; None for a file."""
    if not image_key.startswith(FRAME_SOURCE_PREFIX):
        return None
    episode_id, beat_id = image_key.removeprefix(FRAME_SOURCE_PREFIX).split("/")
    return episode_id, beat_id


def _replace_picture_sources(content: str, episode_id: str, replace: Any) -> str:
    """The card's Hepta Markdown with each picture's source replaced by `replace(image key)`, the line's indentation (a
    picture under a point) kept."""
    lines = []
    for line in content.splitlines():
        match = PICTURE_LINE_PATTERN.match(line.strip())
        indentation = line[:len(line) - len(line.lstrip())]
        lines.append(f"{indentation}![{match.group(1)}]({replace(build_image_key(match.group(2), episode_id))})"
                     if match else line)
    return "\n".join(lines)


def _list_image_keys(episodes: list[WhiteboardEpisode]) -> list[str]:
    return list(dict.fromkeys(build_image_key(source, episode.id) for episode in episodes
                              for _, card in episode.list_cards() for source in iterate_picture_sources(card.content)))


def _build_image_url(image_key: str, episode_id: str) -> str:
    """Where the page reads a picture, below the page server's base URL."""
    frame = _parse_frame_key(image_key)
    if frame:
        return f"/media/{frame[0]}/frames/{quote(frame[1])}.jpg"
    return f"/media/{episode_id}/card-images/{quote(image_key)}"


def _compute_file_version(series: Series, image_key: str) -> str | None:
    """Which file a picture's key shows now: its size and modification time. None when there is no file yet."""
    file_path = series.production_dir_path / image_key
    if not file_path.is_file():
        return None
    stat = file_path.stat()
    return f"{stat.st_size}-{stat.st_mtime_ns}"


def _list_page_images(series: Series, episodes: list[WhiteboardEpisode]) -> list[dict[str, Any]]:
    """The episodes' pictures as the page reads them, each once: its key, where the page server serves it, and its
    version, so that a layout measured with another picture is refused (a frame's is its episode's delivery)."""
    delivered_at_by_episode_id_map = {}
    for episode in episodes:
        record = load_latest_delivery_record(series, episode.id)
        delivered_at_by_episode_id_map[episode.id] = record.delivered_at.isoformat() if record else None
    images = {}
    for episode in episodes:
        for image_key in _list_image_keys([episode]):
            frame = _parse_frame_key(image_key)
            version = delivered_at_by_episode_id_map.get(frame[0]) if frame else _compute_file_version(series, image_key)
            images[image_key] = {"key": image_key, "url": _build_image_url(image_key, episode.id), "version": version}
    return list(images.values())


def _find_image_file(series: Series, image_key: str) -> tuple[Path, str]:
    """A picture's file and its file name in Heptabase; raises WhiteboardImportRefusedError when it is missing."""
    frame = _parse_frame_key(image_key)
    if frame:
        episode_id, beat_id = frame
        frame_file_path = find_frame_file_path(series, episode_id, beat_id)
        if frame_file_path is None:
            raise WhiteboardImportRefusedError("picture_unusable", "a card's frame could not be taken from the video",
                                               f"no frame for {image_key}", "check the episode's delivered video")
        return frame_file_path, f"{beat_id}.jpg"
    file_path = series.production_dir_path / image_key
    if not file_path.is_file():
        raise WhiteboardImportRefusedError("picture_unusable", "a card's picture is missing", f"no file at {image_key}",
                                           "fix the card's picture and run notes check")
    return file_path, file_path.name


# The linked whiteboard ------------------------------------------------------------------------------------------------
def load_heptabase_whiteboard(series: Series) -> HeptabaseWhiteboard | None:
    if not series.heptabase_whiteboard_file_path.exists():
        return None
    return load_json_model(HeptabaseWhiteboard, series.heptabase_whiteboard_file_path)


def _write_heptabase_whiteboard(series: Series, whiteboard: HeptabaseWhiteboard) -> None:
    # an episode not confirmed yet has no imported_at at all
    write_json(series.heptabase_whiteboard_file_path, whiteboard.model_dump(mode="json", exclude_none=True))


def find_linked_whiteboard(series: Series, issuer: str | None) -> HeptabaseWhiteboard | None:
    """The whiteboard the series is linked to in the Heptabase at `issuer` (any, when it is unknown). A whiteboard
    saved in another Heptabase (while developing) counts as none: saving makes a new one there."""
    whiteboard = load_heptabase_whiteboard(series)
    return whiteboard if whiteboard and (issuer is None or whiteboard.issuer == issuer) else None


def _list_imported_episode_ids(whiteboard: HeptabaseWhiteboard | None) -> list[str]:
    return [episode_id for episode_id, episode in (whiteboard.episodes if whiteboard else {}).items()
            if episode.imported_at]


def _build_section_id_by_key_map(whiteboard: HeptabaseWhiteboard, episode_ids: list[str]) -> dict[str, str]:
    """The episodes' sections in Heptabase by their keys on the page: <episode>, and <episode>/<chapter>."""
    section_id_by_key_map = {}
    for episode_id in episode_ids:
        episode = whiteboard.episodes[episode_id]
        section_id_by_key_map[episode_id] = episode.section_id
        for chapter_id, chapter in episode.chapters.items():
            section_id_by_key_map[f"{episode_id}/{chapter_id}"] = chapter.section_id
    return section_id_by_key_map


def list_episodes_to_add(series: Series, whiteboard: HeptabaseWhiteboard | None) -> tuple[
        list[WhiteboardEpisode], list[dict[str, str]]]:
    """The delivered episodes not on the whiteboard yet, in plan order: those whose cards pass `notes check` against
    their latest delivery (they can be added), and those without such cards (each its id and title)."""
    imported_episode_ids = set(_list_imported_episode_ids(whiteboard))
    episodes, episodes_without_cards = [], []
    for delivered_episode in list_delivered_episodes(series):
        if delivered_episode["id"] in imported_episode_ids:
            continue
        delivered_notes = load_delivered_notes(series, delivered_episode["id"])
        if delivered_notes is None:
            episodes_without_cards.append(delivered_episode)
        else:
            episodes.append(WhiteboardEpisode(delivered_episode["id"], delivered_episode["title"], delivered_notes[0]))
    return episodes, episodes_without_cards


def _list_arrow_card_keys(whiteboard: HeptabaseWhiteboard | None, episodes: list[WhiteboardEpisode]) -> set[str]:
    """The cards an arrow from another episode may start at: those of the episodes on the whiteboard and of
    `episodes`, which come with them."""
    imported_card_keys = {card_key for episode_id in _list_imported_episode_ids(whiteboard)
                          for card_key in whiteboard.episodes[episode_id].cards}
    return imported_card_keys.union(*(episode.card_keys for episode in episodes))


def _dump_page_episode(episode: WhiteboardEpisode, arrow_card_keys: set[str]) -> dict[str, Any]:
    """An episode for the page to measure and lay out. Its arrows from other episodes are only those whose card is on
    the whiteboard or comes with it."""
    return {
        "id": episode.id, "number": parse_episode_number(episode.id), "sectionTitle": episode.section_title,
        "chapters": [{"id": chapter.id, "title": chapter.title, "scenes": [{"id": scene.id, "cards": [{
            "key": episode.build_key(card.id), "color": card.color,
            "content": _replace_picture_sources(card.content, episode.id, lambda image_key: image_key),
            "leadsTo": [episode.build_key(card_id) for card_id in card.leads_to],
            "continuesFrom": [card_key for card_key in card.continues_from if card_key in arrow_card_keys],
        } for card in scene.cards]} for scene in chapter.scenes]} for chapter in episode.notes.chapters],
    }


def _dump_page_episodes(whiteboard: HeptabaseWhiteboard | None, episodes: list[WhiteboardEpisode]) -> list[
        dict[str, Any]]:
    arrow_card_keys = _list_arrow_card_keys(whiteboard, episodes)
    return [_dump_page_episode(episode, arrow_card_keys) for episode in episodes]


def _compute_cards_version(page_episodes: list[dict[str, Any]], page_images: list[dict[str, Any]]) -> str:
    """Which cards, with which pictures, the page was given to lay out: an import laid out from others is refused."""
    return hashlib.sha256(json.dumps({"episodes": page_episodes, "images": page_images}, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def compute_whiteboard_page(series: Series) -> dict[str, Any]:
    """What the video page's whiteboard needs: where Heptabase is, the email of the account this computer is signed in
    with, the linked whiteboard, the episodes to add (with their cards and pictures, and the version of those cards)
    and the delivered episodes without cards."""
    api_url = heptabase_sign_in.resolve_heptabase_api_url()
    app_url = heptabase_sign_in.resolve_heptabase_app_url()
    issuer = heptabase_sign_in.find_issuer(api_url)
    signed_in_email = heptabase_sign_in.find_signed_in_email(issuer) if issuer else None
    whiteboard = find_linked_whiteboard(series, issuer)
    imported_episode_ids = _list_imported_episode_ids(whiteboard)
    episodes, episodes_without_cards = list_episodes_to_add(series, whiteboard)
    page_episodes = _dump_page_episodes(whiteboard, episodes)
    page_images = _list_page_images(series, episodes)
    return {
        "title": read_series_title(series),
        "appUrl": app_url,
        "embeddedWhiteboardUrl": app_url + EMBEDDED_WHITEBOARD_PATH,
        "signedInEmail": signed_in_email,  # null when this computer is not signed in
        # saved once Heptabase confirmed an episode: a first save that was not confirmed is still a preview, whose
        # next save sends the same ids
        "savedWhiteboard": {"whiteboardId": whiteboard.whiteboard_id, "importedEpisodeIds": imported_episode_ids,
                            "sectionIdByKeyMap": _build_section_id_by_key_map(whiteboard, imported_episode_ids)}
        if whiteboard and imported_episode_ids else None,
        "episodesToAdd": page_episodes,
        "cardsVersion": _compute_cards_version(page_episodes, page_images),
        "episodesWithoutCards": [{"id": episode["id"], "number": parse_episode_number(episode["id"])}
                                 for episode in episodes_without_cards],
        "images": page_images,
    }


# Importing ------------------------------------------------------------------------------------------------------------
ObjectColor = Literal["yellow", "red", "blue", "green", "black", "orange", "purple", "white"]
ConnectionPosition = Literal["top", "right", "bottom", "left"]


class _LayoutModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _LaidOutBox(_LayoutModel):
    key: str
    x: float
    y: float
    width: Annotated[float, Field(gt=0)]
    height: Annotated[float, Field(gt=0)]


class _LaidOutSection(_LaidOutBox):
    color: ObjectColor | None = None


class _LaidOutConnection(_LayoutModel):
    key: str
    type: Literal["curve", "straight", "elbow"]
    begin_pos: ConnectionPosition = Field(alias="beginPos")
    end_pos: ConnectionPosition = Field(alias="endPos")


class WhiteboardLayout(_LayoutModel):
    """Where the page laid the episodes to add out, by their whiteboard keys: an episode's section is its id, a
    chapter's <episode>/<chapter id>, a card's <episode>/<card id>, an arrow's <card key>-><card key>."""
    episode_ids: list[str] = Field(alias="episodeIds", min_length=1)
    cards_version: str = Field(alias="cardsVersion")  # the version of the cards the page laid out
    sections: list[_LaidOutSection]
    cards: list[_LaidOutBox]
    connections: list[_LaidOutConnection]


def parse_whiteboard_layout(document: Any) -> WhiteboardLayout:
    try:
        return WhiteboardLayout.model_validate(document)
    except ValidationError as error:
        raise StudioError("the whiteboard's layout is not valid", str(error.errors()[0]["msg"])) from None


def _generate_id() -> str:
    return str(uuid.uuid4())


def _assign_episode_ids(episode: WhiteboardEpisode, record: HeptabaseWhiteboardEpisode | None,
                        connection_keys: list[str]) -> HeptabaseWhiteboardEpisode:
    """The episode's Heptabase ids: the ones a previous, unconfirmed attempt recorded, and new ones for the rest."""
    chapters = record.chapters if record else {}
    cards = record.cards if record else {}
    connections = record.connections if record else {}
    return HeptabaseWhiteboardEpisode(
        section_id=record.section_id if record else _generate_id(),
        chapters={chapter.id: chapters.get(chapter.id) or HeptabaseWhiteboardChapter(section_id=_generate_id())
                  for chapter in episode.notes.chapters},
        cards={card_key: cards.get(card_key) or HeptabaseWhiteboardCard(card_id=_generate_id(),
                                                                          card_instance_id=_generate_id())
               for card_key in episode.card_keys},
        connections={connection_key: connections.get(connection_key) or _generate_id()
                     for connection_key in connection_keys})


def _list_connection_keys(episode: WhiteboardEpisode, arrow_card_keys: set[str]) -> list[str]:
    """The episode's arrows: from its cards to the cards they lead to, and into its cards from the other episodes'
    cards they continue from, when those are on the whiteboard or come with it."""
    keys = []
    for card_key, card in episode.list_cards():
        keys += [f"{card_key}->{episode.build_key(card_id)}" for card_id in card.leads_to]
        keys += [f"{source_key}->{card_key}" for source_key in card.continues_from if source_key in arrow_card_keys]
    return keys


def _require_layout_covers(layout: WhiteboardLayout, section_keys: set[str], card_keys: set[str],
                         connection_keys: set[str]) -> None:
    for kind, laid_out_keys, expected_keys in (
            ("sections", {section.key for section in layout.sections}, section_keys),
            ("cards", {card.key for card in layout.cards}, card_keys),
            ("arrows", {connection.key for connection in layout.connections}, connection_keys)):
        if laid_out_keys != expected_keys:
            raise WhiteboardImportRefusedError("cards_changed", "the whiteboard's layout does not match the cards",
                                               f"the layout's {kind} differ from the episodes' cards",
                                               "lay the cards out again")


def _format_upload_time(file_path: Path) -> str:
    return datetime.fromtimestamp(file_path.stat().st_mtime, UTC).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z")


def _upload_image(series: Series, api_url: str, image_key: str, file_id: str) -> dict[str, Any]:
    """Put the picture where Heptabase keeps the file `file_id`, unless Heptabase has that file already (an earlier
    import made it), and the file's description for the import."""
    file_path, file_name = _find_image_file(series, image_key)
    try:
        media_type, width, height = read_card_picture(file_path)
    except StudioError as error:
        raise WhiteboardImportRefusedError("picture_unusable", error.what, f"{image_key}: {error.why}",
                                           error.next_step) from None
    content = file_path.read_bytes()
    response_body = heptabase_sign_in.call_rest_api(
        api_url, UPLOAD_URL_PATH, {"fileId": file_id, "lastModifiedTime": _format_upload_time(file_path)})
    if response_body.get("status") != "file_exists":  # Heptabase never replaces a file's bytes for Studio
        try:
            response = heptabase_sign_in.send_request("PUT", response_body["signedUrl"], content=content,
                                                      headers={"Content-Type": media_type},
                                                      timeout=IMAGE_UPLOAD_TIMEOUT_SECONDS)
        except httpx.HTTPError as error:
            raise StudioError("a picture was not uploaded to Heptabase", f"{type(error).__name__}: {error}",
                              "try again") from None
        if not 200 <= response.status_code < 300:
            raise StudioError("a picture was not uploaded to Heptabase",
                              f"the upload answered HTTP {response.status_code}", "try again")
    return {"id": file_id, "name": file_name, "type": media_type, "size": len(content), "width": width,
            "height": height}


def _create_whiteboard_record(issuer: str, account_id: str) -> HeptabaseWhiteboard:
    return HeptabaseWhiteboard(issuer=issuer, account_id=account_id, whiteboard_id=_generate_id(), files={},
                               episodes={})


def _find_whiteboard_to_import_into(series: Series, issuer: str, account_id: str) -> HeptabaseWhiteboard:
    """The linked whiteboard, or a new record for the first save. A first save that was not confirmed belongs to the
    account that made it: with another account signed in, the save starts over on a new whiteboard."""
    whiteboard = find_linked_whiteboard(series, issuer)
    if whiteboard is None or (not _list_imported_episode_ids(whiteboard) and whiteboard.account_id != account_id):
        return _create_whiteboard_record(issuer, account_id)
    if whiteboard.account_id != account_id:
        raise WhiteboardImportRefusedError("other_account", "another Heptabase account is signed in",
                                           "the whiteboard was saved with another account",
                                           "sign in again with the account that saved it")
    return whiteboard


def import_episodes(series: Series, layout: WhiteboardLayout) -> None:
    """Add the laid-out episodes that are not on the linked whiteboard yet, creating and linking the whiteboard the
    first time. Their ids are recorded before Heptabase is asked, and `imported_at` once it confirmed; an episode a
    previous attempt left unconfirmed goes again with the same ids, which Heptabase does not add twice. The layout must
    be of the cards as they are now."""
    api_url = heptabase_sign_in.resolve_heptabase_api_url()
    issuer = heptabase_sign_in.fetch_authorization_server(api_url).issuer
    account_id = heptabase_sign_in.require_signed_in_account_id(issuer)
    with hold_lock(series.heptabase_whiteboard_file_path):
        whiteboard = _find_whiteboard_to_import_into(series, issuer, account_id)
        episodes_to_add, _ = list_episodes_to_add(series, whiteboard)
        if _compute_cards_version(_dump_page_episodes(whiteboard, episodes_to_add),
                                  _list_page_images(series, episodes_to_add)) != layout.cards_version:
            raise WhiteboardImportRefusedError("cards_changed", "the cards changed after the page laid them out",
                                               "notes.yaml or the whiteboard changed", "lay the cards out again")
        episodes = [episode for episode in episodes_to_add if episode.id in layout.episode_ids]
        if not episodes:
            return
        try:
            _import_into(series, api_url, whiteboard, episodes, layout)
        except heptabase_sign_in.HeptabaseRequestError as error:
            # Nothing is linked before Heptabase confirmed an episode. When it refuses the whiteboard of a first save
            # (one made empty when its objects failed, then trashed or deleted, or another account's), the save goes
            # to a new whiteboard instead.
            if _list_imported_episode_ids(whiteboard) or error.code not in WHITEBOARD_REFUSAL_CODES:
                raise
            _import_into(series, api_url, _create_whiteboard_record(issuer, account_id), episodes, layout)


def _import_into(series: Series, api_url: str, whiteboard: HeptabaseWhiteboard, episodes: list[WhiteboardEpisode],
                 layout: WhiteboardLayout) -> None:
    """Record the episodes' ids, upload their pictures, ask Heptabase to add them, and record that it did. The caller
    holds the record's lock."""
    arrow_card_keys = _list_arrow_card_keys(whiteboard, episodes)
    records = {episode.id: _assign_episode_ids(episode, whiteboard.episodes.get(episode.id),
                                               _list_connection_keys(episode, arrow_card_keys))
               for episode in episodes}
    _require_layout_covers(
        layout,
        {key for episode in episodes
         for key in (episode.id, *(episode.build_key(chapter.id) for chapter in episode.notes.chapters))},
        set().union(*(episode.card_keys for episode in episodes)),
        {key for record in records.values() for key in record.connections})
    image_keys = _list_image_keys(episodes)
    whiteboard = whiteboard.model_copy(update={
        "files": {**whiteboard.files, **{key: whiteboard.files.get(key) or _generate_id() for key in image_keys}},
        "episodes": {**whiteboard.episodes, **records}})
    _write_heptabase_whiteboard(series, whiteboard)

    with ThreadPoolExecutor(max_workers=IMAGE_UPLOAD_WORKER_COUNT) as executor:
        files = list(executor.map(
            lambda image_key: _upload_image(series, api_url, image_key, whiteboard.files[image_key]), image_keys))
    heptabase_sign_in.call_rest_api(api_url, IMPORT_PATH, _build_import_body(
        read_series_title(series), whiteboard, episodes, layout, files))

    imported_at = get_current_time()
    _write_heptabase_whiteboard(series, whiteboard.model_copy(update={"episodes": {
        **whiteboard.episodes,
        **{episode.id: records[episode.id].model_copy(update={"imported_at": imported_at}) for episode in episodes}}}))


def _find_card_instance_id(whiteboard: HeptabaseWhiteboard, card_key: str) -> str:
    return whiteboard.episodes[card_key.split("/")[0]].cards[card_key].card_instance_id


def _build_import_body(title: str, whiteboard: HeptabaseWhiteboard, episodes: list[WhiteboardEpisode],
                       layout: WhiteboardLayout, files: list[dict[str, Any]]) -> dict[str, Any]:
    """Heptabase's importWhiteboardObjects body: plain whiteboard objects with Studio's ids and the page's positions.
    Heptabase knows nothing of episodes, chapters or Studio's keys."""
    section_by_key_map = {section.key: section for section in layout.sections}
    card_box_by_key_map = {card.key: card for card in layout.cards}
    connection_by_key_map = {connection.key: connection for connection in layout.connections}

    def place(box: _LaidOutBox) -> dict[str, float]:
        return {"x": box.x, "y": box.y, "width": box.width, "height": box.height}

    sections, cards, connections = [], [], []
    for episode in episodes:
        record = whiteboard.episodes[episode.id]
        sections.append({"id": record.section_id, "parentSectionId": None, "title": episode.section_title,
                         "color": section_by_key_map[episode.id].color, **place(section_by_key_map[episode.id])})
        for chapter in episode.notes.chapters:
            chapter_key = episode.build_key(chapter.id)
            chapter_section_id = record.chapters[chapter.id].section_id
            sections.append({"id": chapter_section_id, "parentSectionId": record.section_id, "title": chapter.title,
                             "color": section_by_key_map[chapter_key].color, **place(section_by_key_map[chapter_key])})
            for card in (card for scene in chapter.scenes for card in scene.cards):
                card_key = episode.build_key(card.id)
                content = _replace_picture_sources(card.content, episode.id,
                                                   lambda image_key: f"{HEPTABASE_IMAGE_SOURCE_PREFIX}{whiteboard.files[image_key]}")
                cards.append({"id": record.cards[card_key].card_id,
                              "cardInstanceId": record.cards[card_key].card_instance_id,
                              "sectionId": chapter_section_id, "color": card.color, "content": content,
                              **place(card_box_by_key_map[card_key])})
        for connection_key, connection_id in record.connections.items():
            begin_key, end_key = connection_key.split("->")
            connection = connection_by_key_map[connection_key]
            connections.append({"id": connection_id,
                                "beginId": _find_card_instance_id(whiteboard, begin_key),
                                "endId": _find_card_instance_id(whiteboard, end_key),
                                "type": connection.type, "beginPos": connection.begin_pos,
                                "endPos": connection.end_pos})
    return {"whiteboard": {"id": whiteboard.whiteboard_id, "title": title}, "files": files, "sections": sections,
            "cards": cards, "connections": connections}


def unlink(series: Series) -> None:
    """Forget the linked whiteboard; it stays in Heptabase, and the next save makes a new one."""
    with hold_lock(series.heptabase_whiteboard_file_path):
        series.heptabase_whiteboard_file_path.unlink(missing_ok=True)
