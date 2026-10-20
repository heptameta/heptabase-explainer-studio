"""The episode's cards (notes.yaml): `notes check`, and the video page's chapters view, the latest delivery's
scenes grouped into the chapters of notes.yaml, each scene with its summary and its key frame. The cards are written
while the episode is made and must fit its render before it is delivered, so the chapters view and the series'
whiteboard have them from the moment of delivery. A card's pictures are the delivered video's frames (grabbed when they
are first asked for) or files in production/: a credited asset, or a picture made for the episode's cards in
`episodes/<episode>/card-images/`."""

from __future__ import annotations

import hashlib
import io
import re
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from . import user_dirs
from .deliver import (
    list_delivery_record_dir_paths,
    load_delivered_timeline,
    load_delivery_record,
    load_latest_delivered_timeline,
)
from .errors import StudioError
from .file_io import load_json_model, load_yaml_model, write_bytes_atomic
from .paths import Series
from .plan import load_plan
from .schemas.credits import Credits
from .schemas.notes import FRAME_SOURCE_PREFIX, PICTURE_LINE_PATTERN, Card, Notes, iterate_picture_sources
from .schemas.timeline import Timeline

# Markdown's ==highlight==, which Hepta Markdown does not have: Heptabase would show the equals signs. Code is left out,
# where == is an operator.
MARKDOWN_HIGHLIGHT_PATTERN = re.compile(r"==(?=\S)[^=\n]*?(?<=\S)==")
MARKDOWN_CODE_PATTERN = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
# the picture formats a Heptabase card shows, by Pillow's name
CARD_PICTURE_FORMAT_NAMES = ("PNG", "JPEG", "WEBP", "GIF")

FRAME_WIDTH_PIXELS = 960
# how long before the end of a beat's line its frame is taken, so the picture has settled but has not moved on
FRAME_LEAD_SECONDS = 0.1
CARD_IMAGES_DIR_NAME = "card-images"


def _load_credited_asset_file_paths(series: Series) -> set[str]:
    if not series.credits_file_path.exists():
        return set()
    return {credit.asset_file_path for credit in load_yaml_model(Credits, series.credits_file_path).credits}


def get_card_images_dir_path(episode_id: str) -> str:
    """Where the pictures made for an episode's cards go, relative to production/."""
    return f"episodes/{episode_id}/{CARD_IMAGES_DIR_NAME}/"


def check_is_card_image_file_path(series: Series, episode_id: str, file_path: str) -> bool:
    """Whether a picture's file path names a picture the episode's cards may show: a credited asset, or a picture in
    the episode's card-images folder, inside production/ and present."""
    if file_path not in _load_credited_asset_file_paths(series) \
            and not file_path.startswith(get_card_images_dir_path(episode_id)):
        return False
    resolved_file_path = (series.production_dir_path / file_path).resolve()
    return resolved_file_path.is_relative_to(series.production_dir_path.resolve()) and resolved_file_path.is_file()


def read_card_picture(file_path: Path) -> tuple[str, int, int]:
    """A picture file's media type, width and height; raises StudioError when it is not a picture a Heptabase card
    shows (a PNG, JPEG, WebP or GIF image)."""
    try:
        with Image.open(file_path) as image:
            format_name, (width, height) = image.format, image.size
    except (OSError, UnidentifiedImageError):
        format_name, width, height = None, 0, 0
    if format_name not in CARD_PICTURE_FORMAT_NAMES:
        raise StudioError(f"{file_path.name} is not a PNG, JPEG, WebP or GIF image",
                          "a Heptabase card shows only these", "convert the picture, or choose another one")
    return Image.MIME[format_name], width, height


def _find_card_picture_problems(series: Series, episode_id: str, card: Card, beat_ids: set[str]) -> list[str]:
    problems = []
    for line in card.content.splitlines():
        if "![" in line and not PICTURE_LINE_PATTERN.match(line.strip()):
            problems.append(f"card {card.id}: a picture must be a line of its own, ![caption](source), with no "
                            f"spaces or parentheses in the source: {line.strip()}")
    for source in iterate_picture_sources(card.content):
        if source.startswith(FRAME_SOURCE_PREFIX):
            if source.removeprefix(FRAME_SOURCE_PREFIX) not in beat_ids:
                problems.append(f"card {card.id}: {source} is not a beat of the delivered video")
        elif not check_is_card_image_file_path(series, episode_id, source):
            problems.append(f"card {card.id}: picture {source} is neither in credits.yaml nor a file in "
                            f"{get_card_images_dir_path(episode_id)}")
        else:
            try:
                read_card_picture(series.production_dir_path / source)
            except StudioError as error:
                problems.append(f"card {card.id}: picture {source}: {error.what} ({error.why}); {error.next_step}")
    return problems


def find_notes_problems(series: Series, episode_id: str, notes: Notes, timeline: Timeline) -> list[str]:
    """Why notes.yaml does not fit the video: its chapters must hold every scene once, in the video's order, every
    frame and picture it shows must exist, and its cards' ids must be unique and their arrows lead to its cards."""
    problems = []
    scene_ids = [scene.scene_id for scene in timeline.scenes]
    notes_scene_ids = [scene.id for scene in notes.list_scenes()]
    if notes_scene_ids != scene_ids:
        problems.append(f"the chapters hold {', '.join(notes_scene_ids)}; the delivered video's scenes, in order, are "
                        f"{', '.join(scene_ids)}")
    for chapter_id, count in Counter(chapter.id for chapter in notes.chapters).items():
        if count > 1:
            problems.append(f"chapter id {chapter_id} is used more than once")
    beat_ids_by_scene_id_map = {scene.scene_id: {beat.beat_id for beat in scene.beats} for scene in timeline.scenes}
    all_beat_ids = set().union(*beat_ids_by_scene_id_map.values())
    cards = notes.list_cards()
    card_ids = {card.id for card in cards}
    for card_id, count in Counter(card.id for card in cards).items():
        if count > 1:
            problems.append(f"card id {card_id} is used more than once")
    for card in cards:
        for target_id in card.leads_to:
            if target_id not in card_ids or target_id == card.id:
                problems.append(f"card {card.id}: leads_to {target_id} is not another card of these notes")
    for scene in notes.list_scenes():
        if scene.id in beat_ids_by_scene_id_map and scene.key_frame not in beat_ids_by_scene_id_map[scene.id]:
            problems.append(f"{scene.id}: key_frame {scene.key_frame} is not a beat of this scene")
        for card in scene.cards:
            problems += _find_card_picture_problems(series, episode_id, card, all_beat_ids)
            if MARKDOWN_HIGHLIGHT_PATTERN.search(MARKDOWN_CODE_PATTERN.sub("", card.content)):
                problems.append(f"card {card.id}: ==…== is not Hepta Markdown: highlight with "
                                '<hepta-color type="background" color="yellow">…</hepta-color>')
    return problems


def _load_notes(series: Series, episode_id: str) -> Notes | None:
    """The episode's notes.yaml, or None when it is missing or not valid."""
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        return None
    try:
        return load_yaml_model(Notes, notes_file_path)
    except StudioError:
        return None


def _check_episode_notes(series: Series, episode_id: str, timeline: Timeline) -> tuple[Notes | None, list[str]]:
    """The episode's notes.yaml, when it can be read, and why it does not fit `timeline`."""
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        guide_command = "explainer-studio guide references/cards.md"
        return None, [f"{episode_id}/notes.yaml is missing: write the episode's cards ({guide_command})"]
    try:
        notes = load_yaml_model(Notes, notes_file_path, f"{episode_id}/notes.yaml")
    except StudioError as error:
        return None, [error.format().removeprefix("error: ")]
    problems = find_notes_problems(series, episode_id, notes, timeline)
    # an arrow between episodes is written in the later one, so it is drawn when the later episode is added
    planned_episode_ids = [episode.id for episode in load_plan(series).episodes]
    earlier_episode_ids = planned_episode_ids[:planned_episode_ids.index(episode_id)] \
        if episode_id in planned_episode_ids else []
    card_ids_by_episode_id_map: dict[str, set[str]] = {}
    for card in notes.list_cards():
        for source in card.continues_from:
            source_episode_id, source_card_id = source.split("/")
            if source_episode_id in earlier_episode_ids and source_episode_id not in card_ids_by_episode_id_map:
                source_notes = _load_notes(series, source_episode_id)
                card_ids_by_episode_id_map[source_episode_id] = \
                    {source_card.id for source_card in source_notes.list_cards()} if source_notes else set()
            if source_card_id not in card_ids_by_episode_id_map.get(source_episode_id, set()):
                problems.append(f"card {card.id}: continues_from {source} is not a card of an earlier episode's "
                                "notes.yaml")
    return notes, problems


def find_episode_notes_problems(series: Series, episode_id: str, timeline: Timeline) -> list[str]:
    """Why the episode's notes.yaml does not fit `timeline` (its render's, when delivering): missing, unreadable, or
    with chapters, pictures or arrows that do not fit, including arrows from earlier episodes' cards."""
    return _check_episode_notes(series, episode_id, timeline)[1]


def check_notes(series: Series, episode_id: str) -> list[str]:
    """The problems of the episode's notes.yaml against its render, or without one its latest delivery (raises when
    the episode has neither)."""
    render_timeline_file_path = series.get_episode_paths(episode_id).render_timeline_file_path
    timeline = (load_json_model(Timeline, render_timeline_file_path, f"{episode_id}/render/timeline.json")
                if render_timeline_file_path.exists() else load_latest_delivered_timeline(series, episode_id))
    if timeline is None:
        raise StudioError(f"{episode_id} has not been rendered", "notes.yaml is checked against the rendered video",
                          f"render it first (explainer-studio render {episode_id})")
    return find_episode_notes_problems(series, episode_id, timeline)


def load_delivered_notes(series: Series, episode_id: str) -> tuple[Notes, Timeline] | None:
    """The episode's notes.yaml and its latest delivery's timeline, when the notes pass `notes check` against that
    delivery; None when the episode is not delivered or its notes are missing or do not fit."""
    try:
        timeline = load_latest_delivered_timeline(series, episode_id)
        if timeline is None:
            return None
        notes, problems = _check_episode_notes(series, episode_id, timeline)
    except StudioError:
        return None
    return (notes, timeline) if notes and not problems else None


def compute_page_chapters(series: Series, episode_id: str) -> list[dict[str, Any]] | None:
    """The chapters view's chapters, or None when the episode has no notes.yaml or it does not fit the delivered video
    (`explainer-studio notes check` says why)."""
    delivered_notes = load_delivered_notes(series, episode_id)
    if delivered_notes is None:
        return None
    notes, timeline = delivered_notes
    scene_by_id_map = {scene.scene_id: scene for scene in timeline.scenes}
    chapters = []
    for chapter in notes.chapters:
        scenes = []
        for notes_scene in chapter.scenes:
            scene = scene_by_id_map[notes_scene.id]
            scenes.append({"title": notes_scene.title, "summary": notes_scene.summary, "keyFrame": notes_scene.key_frame,
                           "startSeconds": scene.start_seconds,
                           "endSeconds": scene.start_seconds + scene.duration_seconds})
        chapters.append({"id": chapter.id, "title": chapter.title, "scenes": scenes})
    return chapters


def find_frame_time_seconds(timeline: Timeline, beat_id: str) -> float | None:
    """When the beat's frame is taken: just before its line ends, and never past the start of the next beat."""
    beats = [beat for scene in timeline.scenes for beat in scene.beats]
    for index, beat in enumerate(beats):
        if beat.beat_id == beat_id:
            line_end_seconds = beat.start_seconds + beat.duration_seconds - FRAME_LEAD_SECONDS
            if index + 1 < len(beats):
                line_end_seconds = min(line_end_seconds, beats[index + 1].start_seconds - FRAME_LEAD_SECONDS)
            return max(beat.start_seconds, line_end_seconds)
    return None


def find_frame_file_path(series: Series, episode_id: str, beat_id: str) -> Path | None:
    """The JPEG of a beat's frame in the latest delivered video, grabbed on first use and kept in the user's cache
    (keyed by the series, the delivery and the beat). None when there is no such beat or video."""
    record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
    if not record_dir_paths:
        return None
    record = load_delivery_record(series, record_dir_paths[-1])
    key = hashlib.sha256(f"{series.root_dir_path.resolve()}|{episode_id}|{record.delivered_at.isoformat()}".encode())
    frame_file_path = user_dirs.ensure_scratch_dir("chapter-frames") / key.hexdigest()[:16] / f"{beat_id}.jpg"
    if frame_file_path.is_file():
        return frame_file_path
    timeline = load_delivered_timeline(series, record_dir_paths[-1])
    video_file_path = series.root_dir_path / record.files.video_file_name
    time_seconds = find_frame_time_seconds(timeline, beat_id) if timeline else None
    if time_seconds is None or not video_file_path.is_file():
        return None
    from .rendering.screenshots import grab_frames

    image = grab_frames(video_file_path, [time_seconds]).get(time_seconds)
    if image is None:
        return None
    image = image.convert("RGB")
    if image.width > FRAME_WIDTH_PIXELS:
        image = image.resize((FRAME_WIDTH_PIXELS, round(image.height * FRAME_WIDTH_PIXELS / image.width)))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=82)
    frame_file_path.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(frame_file_path, buffer.getvalue())
    return frame_file_path


def find_card_image_file_path(series: Series, episode_id: str, file_path: str) -> Path | None:
    """A picture file a card shows: only one the episode's notes.yaml names and may show (see
    `check_is_card_image_file_path`)."""
    notes = _load_notes(series, episode_id)
    if notes is None:
        return None
    named = {source for card in notes.list_cards() for source in iterate_picture_sources(card.content)}
    if file_path not in named or not check_is_card_image_file_path(series, episode_id, file_path):
        return None
    return (series.production_dir_path / file_path).resolve()
