"""The chapter views of the video page: the latest delivery's scenes grouped into the parts of notes.yaml, each scene
with its summary, its key frame and its cards. The cards are written while the episode is made and must fit its
render before it is delivered, so the page shows them from the moment of delivery. A card's pictures are the delivered video's frames (grabbed
when the page first asks for them) or credited assets of the series."""

from __future__ import annotations

import hashlib
import io
from collections import Counter
from pathlib import Path
from typing import Any

from . import user_dirs
from .deliver import list_delivery_record_dir_paths, load_delivered_timeline, load_delivery_record
from .errors import StudioError
from .file_io import load_json_model, load_yaml_model, write_bytes_atomic
from .paths import Series
from .schemas.credits import Credits
from .schemas.notes import Card, Notes, iterate_points
from .schemas.timeline import Timeline

FRAME_WIDTH_PIXELS = 960
# how long before the end of a beat's line its frame is taken, so the picture has settled but has not moved on
FRAME_LEAD_SECONDS = 0.1


def _load_credited_asset_file_paths(series: Series) -> set[str]:
    if not series.credits_file_path.exists():
        return set()
    return {credit.asset_file_path for credit in load_yaml_model(Credits, series.credits_file_path).credits}


def find_notes_problems(notes: Notes, timeline: Timeline, credited_asset_file_paths: set[str]) -> list[str]:
    """Why notes.yaml does not fit the delivered video: its parts must hold every scene once, in the video's order,
    every frame and image it names must exist, and its cards' ids must be unique and their arrows lead to cards."""
    problems = []
    scene_ids = [scene.scene_id for scene in timeline.scenes]
    part_scene_ids = [segment_id for part in notes.parts for segment_id in part.segments]
    if part_scene_ids != scene_ids:
        problems.append(f"the parts hold {', '.join(part_scene_ids)}; the delivered video's scenes, in order, are "
                        f"{', '.join(scene_ids)}")
    beat_ids_by_scene_id_map = {scene.scene_id: {beat.beat_id for beat in scene.beats} for scene in timeline.scenes}
    all_beat_ids = set().union(*beat_ids_by_scene_id_map.values())
    cards = [card for segment in notes.segments.values() for card in segment.cards]
    card_ids = {card.id for card in cards}
    for card_id, count in Counter(card.id for card in cards).items():
        if count > 1:
            problems.append(f"card id {card_id} is used more than once")
    for card in cards:
        for target_id in card.leads_to:
            if "/" not in target_id and (target_id not in card_ids or target_id == card.id):
                problems.append(f"card {card.id}: leads_to {target_id} is not another card of these notes")
    for scene_id in scene_ids:
        segment = notes.segments.get(scene_id)
        if segment is None:
            problems.append(f"segments has no entry for scene {scene_id}")
            continue
        if segment.key_frame not in beat_ids_by_scene_id_map[scene_id]:
            problems.append(f"{scene_id}: key_frame {segment.key_frame} is not a beat of this scene")
        for card in segment.cards:
            for point in iterate_points(card.points):
                if point.frame and point.frame not in all_beat_ids:
                    problems.append(f"card {card.id}: frame {point.frame} is not a beat of the delivered video")
                if point.image and point.image not in credited_asset_file_paths:
                    problems.append(f"card {card.id}: image {point.image} has no credits.yaml entry")
    for segment_id in notes.segments:
        if segment_id not in beat_ids_by_scene_id_map:
            problems.append(f"segments has {segment_id}, which is not a scene of the delivered video")
    return problems


def _load_latest_timeline(series: Series, episode_id: str) -> Timeline | None:
    record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
    return load_delivered_timeline(series, record_dir_paths[-1]) if record_dir_paths else None


def _load_card_ids(series: Series, episode_id: str) -> set[str] | None:
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        return None
    try:
        notes = load_yaml_model(Notes, notes_file_path)
    except StudioError:
        return None
    return {card.id for segment in notes.segments.values() for card in segment.cards}


def find_episode_notes_problems(series: Series, episode_id: str, timeline: Timeline) -> list[str]:
    """Why the episode's notes.yaml does not fit `timeline` (its render's, when delivering): missing, unreadable, or
    with parts, pictures or arrows that do not fit, including arrows to other episodes' cards."""
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        guide_command = "explainer-studio guide references/cards.md"
        return [f"{episode_id}/notes.yaml is missing: write the episode's cards ({guide_command})"]
    try:
        notes = load_yaml_model(Notes, notes_file_path, f"{episode_id}/notes.yaml")
    except StudioError as error:
        return [error.format().removeprefix("error: ")]
    problems = find_notes_problems(notes, timeline, _load_credited_asset_file_paths(series))
    for segment in notes.segments.values():
        for card in segment.cards:
            for target in (target for target in card.leads_to if "/" in target):
                target_episode_id, target_card_id = target.split("/")
                target_card_ids = _load_card_ids(series, target_episode_id)
                if target_episode_id == episode_id or target_card_ids is None or target_card_id not in target_card_ids:
                    problems.append(f"card {card.id}: leads_to {target} is not a card of another episode's notes.yaml")
    return problems


def check_notes(series: Series, episode_id: str) -> list[str]:
    """The problems of the episode's notes.yaml against its render, or without one its latest delivery (raises when
    the episode has neither)."""
    render_timeline_file_path = series.get_episode_paths(episode_id).render_timeline_file_path
    timeline = (load_json_model(Timeline, render_timeline_file_path, f"{episode_id}/render/timeline.json")
                if render_timeline_file_path.exists() else _load_latest_timeline(series, episode_id))
    if timeline is None:
        raise StudioError(f"{episode_id} has not been rendered", "notes.yaml is checked against the rendered video",
                          f"render it first (explainer-studio render {episode_id})")
    return find_episode_notes_problems(series, episode_id, timeline)


def _dump_card(card: Card, episode_id: str) -> dict[str, Any]:
    """A card for the page, its id and its arrows' ids as the series' whiteboard names them: <episode>/<card id>."""
    return {"id": f"{episode_id}/{card.id}", "episodeId": episode_id, "title": card.title,
            **({"color": card.color} if card.color else {}),
            "points": [point.model_dump(exclude_none=True) for point in card.points],
            "leadsTo": [target if "/" in target else f"{episode_id}/{target}" for target in card.leads_to]}


def compute_page_chapters(series: Series, episode_id: str) -> dict[str, Any] | None:
    """The chapter views' data, or None when the episode has no notes.yaml or it does not fit the delivered video
    (`explainer-studio notes check` says why)."""
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        return None
    try:
        notes = load_yaml_model(Notes, notes_file_path)
        timeline = _load_latest_timeline(series, episode_id)
        if timeline is None or find_notes_problems(notes, timeline, _load_credited_asset_file_paths(series)):
            return None
    except StudioError:
        return None
    scene_by_id_map = {scene.scene_id: scene for scene in timeline.scenes}
    parts = []
    for part in notes.parts:
        segments = []
        for scene_id in part.segments:
            scene, segment = scene_by_id_map[scene_id], notes.segments[scene_id]
            segments.append({"id": scene_id, "title": segment.title, "summary": segment.summary,
                             "keyFrame": segment.key_frame, "startSeconds": scene.start_seconds,
                             "endSeconds": scene.start_seconds + scene.duration_seconds,
                             "beats": [{"id": beat.beat_id, "startSeconds": beat.start_seconds}
                                       for beat in scene.beats],
                             "cards": [_dump_card(card, episode_id) for card in segment.cards]})
        parts.append({"title": part.title, "segments": segments})
    return {"parts": parts}


def compute_page_board(series: Series, episodes: list[tuple[str, str]]) -> dict[str, Any] | None:
    """The series' whiteboard: the cards of every delivered episode whose notes fit its video, in plan order, as
    (episode id, title) gives them. An arrow to a card that is not on the board is left out. None without cards."""
    board_episodes = [{"id": episode_id, "title": title, "parts": chapters["parts"]} for episode_id, title in episodes
                      if (chapters := compute_page_chapters(series, episode_id))]
    if not board_episodes:
        return None
    cards = [card for episode in board_episodes for part in episode["parts"] for segment in part["segments"]
             for card in segment["cards"]]
    card_ids = {card["id"] for card in cards}
    for card in cards:
        card["leadsTo"] = [target for target in card["leadsTo"] if target in card_ids and target != card["id"]]
    return {"episodes": board_episodes}


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
    timeline = load_delivered_timeline(series, record_dir_paths[-1])
    video_file_path = series.root_dir_path / record.files.video_file_name
    time_seconds = find_frame_time_seconds(timeline, beat_id) if timeline else None
    if time_seconds is None or not video_file_path.is_file():
        return None
    key = hashlib.sha256(f"{series.root_dir_path.resolve()}|{episode_id}|{record.delivered_at.isoformat()}".encode())
    frame_file_path = user_dirs.ensure_scratch_dir("chapter-frames") / key.hexdigest()[:16] / f"{beat_id}.jpg"
    if frame_file_path.is_file():
        return frame_file_path
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


def find_handout_image_file_path(series: Series, episode_id: str, asset_file_path: str) -> Path | None:
    """A handout image: only a file the episode's notes.yaml names and credits.yaml lists, inside production/."""
    notes_file_path = series.get_episode_paths(episode_id).notes_file_path
    if not notes_file_path.exists():
        return None
    notes = load_yaml_model(Notes, notes_file_path)
    named = {point.image for segment in notes.segments.values() for card in segment.cards
             for point in iterate_points(card.points) if point.image}
    if asset_file_path not in named or asset_file_path not in _load_credited_asset_file_paths(series):
        return None
    image_file_path = (series.production_dir_path / asset_file_path).resolve()
    if not image_file_path.is_relative_to(series.production_dir_path.resolve()) or not image_file_path.is_file():
        return None
    return image_file_path
