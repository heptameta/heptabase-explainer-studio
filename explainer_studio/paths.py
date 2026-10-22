"""Where every file of a series lives.

A series folder holds the delivered files at its root and everything else under `production/`. A series exists once
`production/plan.yaml` exists; there is no init command and no hidden folder.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import StudioError

PRODUCTION_DIR_NAME = "production"
PLAN_FILE_NAME = "plan.yaml"

EPISODE_ID_PATTERN = re.compile(r"^ep(\d{2,})$")


def format_episode_id(number: int) -> str:
    """The id of the n-th episode in plan order: ep01 … ep99, ep100."""
    return f"ep{number:02d}"


def parse_episode_number(episode_id: str) -> int:
    match = EPISODE_ID_PATTERN.match(episode_id)
    if not match:
        raise StudioError(f"{episode_id!r} is not an episode id", "episode ids look like ep01, ep02 … ep100",
                          "use the id written in production/plan.yaml")
    return int(match.group(1))


def _find_series_root(candidate_dir_path: Path) -> Path | None:
    """The series folder when `candidate_dir_path` is one or is its production/."""
    if (candidate_dir_path / PRODUCTION_DIR_NAME / PLAN_FILE_NAME).is_file():
        return candidate_dir_path
    if candidate_dir_path.name == PRODUCTION_DIR_NAME and (candidate_dir_path / PLAN_FILE_NAME).is_file():
        return candidate_dir_path.parent
    return None


def find_series_above(start_dir_path: Path | None = None) -> Path:
    """The series folder: walk up from `start_dir_path`, checking `production/plan.yaml` and `plan.yaml` at each level.
    Raises StudioError when no folder on the way is a series."""
    here_dir_path = (start_dir_path or Path.cwd()).resolve()
    for candidate_dir_path in [here_dir_path, *here_dir_path.parents]:
        root_dir_path = _find_series_root(candidate_dir_path)
        if root_dir_path is not None:
            return root_dir_path
    raise StudioError("no series found", f"no production/plan.yaml in {here_dir_path} or any folder above it",
                      "run the command inside a series folder, or pass --series <path to the series folder>")


def find_series(series_path: Path | None) -> Path:
    """The series folder for `--series`, which may point at the series folder, its production/ or plan.yaml; without
    it, the series above the current folder. Raises StudioError when there is no series there."""
    if series_path is None:
        return find_series_above()
    path = series_path.expanduser().resolve()
    if path.is_file() and path.name == PLAN_FILE_NAME:
        path = path.parent
    root_dir_path = _find_series_root(path)
    if root_dir_path is not None:
        return root_dir_path
    raise StudioError(f"{series_path} is not a series folder", "it has no production/plan.yaml",
                      "pass the folder that contains production/plan.yaml")


def sanitize_file_title(title: str, max_characters: int = 60) -> str:
    """A title usable in a file name on every platform: no separators or reserved characters, bounded length."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:max_characters].rstrip() or "untitled"


def convert_path_to_production_relative_path(path: Path, production_dir_path: Path) -> str:
    """A path as written in series files: relative to production/ when inside it."""
    try:
        return path.resolve().relative_to(production_dir_path.resolve()).as_posix()
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class Series:
    root_dir_path: Path

    @classmethod
    def find(cls, series_path: Path | None = None) -> Series:
        """The series at `--series` or above the current folder; raises StudioError when there is none."""
        return cls(find_series(series_path))

    # series level -----------------------------------------------------------------------------------------------
    @property
    def production_dir_path(self) -> Path:
        return self.root_dir_path / PRODUCTION_DIR_NAME

    @property
    def plan_file_path(self) -> Path:
        return self.production_dir_path / PLAN_FILE_NAME

    @property
    def series_bible_file_path(self) -> Path:
        return self.production_dir_path / "series-bible.md"

    @property
    def decisions_file_path(self) -> Path:
        return self.production_dir_path / "decisions.md"

    @property
    def gaps_file_path(self) -> Path:
        return self.production_dir_path / "gaps.json"

    @property
    def spending_file_path(self) -> Path:
        return self.production_dir_path / "spending.jsonl"

    @property
    def paid_narration_lock_file_path(self) -> Path:
        """Held by a narrate run that pays for its narration, so one such run in the series goes at a time."""
        return self.production_dir_path / "paid-narration.lock"

    @property
    def credits_file_path(self) -> Path:
        return self.production_dir_path / "credits.yaml"

    @property
    def heptabase_whiteboard_file_path(self) -> Path:
        """The Heptabase whiteboard the series' whiteboard was saved to, once the user saved it."""
        return self.production_dir_path / "heptabase-whiteboard.json"

    @property
    def sources_dir_path(self) -> Path:
        return self.production_dir_path / "sources"

    @property
    def research_dir_path(self) -> Path:
        return self.production_dir_path / "research"

    @property
    def shared_dir_path(self) -> Path:
        return self.production_dir_path / "shared"

    @property
    def shared_assets_dir_path(self) -> Path:
        return self.shared_dir_path / "assets"

    @property
    def episodes_dir_path(self) -> Path:
        return self.production_dir_path / "episodes"

    def get_episode_paths(self, episode_id: str) -> EpisodePaths:
        parse_episode_number(episode_id)
        return EpisodePaths(self, episode_id)

    def format_deliverable_stem(self, episode_id: str, title: str) -> str:
        return f"{parse_episode_number(episode_id):02d}-{sanitize_file_title(title)}"

    def convert_path_to_production_relative_path(self, path: Path) -> str:
        return convert_path_to_production_relative_path(path, self.production_dir_path)


@dataclass(frozen=True)
class EpisodePaths:
    series: Series
    id: str

    @property
    def root_dir_path(self) -> Path:
        return self.series.episodes_dir_path / self.id

    @property
    def design_file_path(self) -> Path:
        return self.root_dir_path / "design.md"

    @property
    def script_file_path(self) -> Path:
        return self.root_dir_path / "script.yaml"

    @property
    def scenes_dir_path(self) -> Path:
        return self.root_dir_path / "scenes"

    def get_scene_file_path(self, scene_id: str) -> Path:
        return self.scenes_dir_path / f"{scene_id}.py"

    @property
    def cover_scene_file_path(self) -> Path:
        return self.root_dir_path / "cover.py"

    @property
    def end_credits_scene_file_path(self) -> Path:
        return self.root_dir_path / "end_credits.py"

    @property
    def assets_dir_path(self) -> Path:
        return self.root_dir_path / "assets"

    @property
    def audience_reviews_dir_path(self) -> Path:
        return self.root_dir_path / "audience-reviews"

    @property
    def script_reviews_file_path(self) -> Path:
        return self.audience_reviews_dir_path / "script.yaml"

    @property
    def feedback_file_path(self) -> Path:
        return self.root_dir_path / "feedback.json"

    @property
    def notes_file_path(self) -> Path:
        return self.root_dir_path / "notes.yaml"

    @property
    def comment_screenshot_sheets_dir_path(self) -> Path:
        return self.root_dir_path / "comment-screenshot-sheets"

    def get_comment_screenshot_sheet_file_path(self, comment_id: str) -> Path:
        return self.comment_screenshot_sheets_dir_path / f"{comment_id}.jpg"

    @property
    def narration_dir_path(self) -> Path:
        return self.root_dir_path / "narration"

    @property
    def narration_record_file_path(self) -> Path:
        return self.narration_dir_path / "narration.yaml"

    def get_narration_audio_file_path(self, beat_id: str) -> Path:
        return self.narration_dir_path / f"{beat_id}.wav"

    @property
    def preview_dir_path(self) -> Path:
        return self.root_dir_path / "preview"

    def get_preview_scene_dir_path(self, scene_id: str) -> Path:
        return self.preview_dir_path / scene_id

    @property
    def preview_cover_dir_path(self) -> Path:
        return self.preview_dir_path / "cover"

    @property
    def preview_end_credits_dir_path(self) -> Path:
        return self.preview_dir_path / "end-credits"

    @property
    def render_dir_path(self) -> Path:
        return self.root_dir_path / "render"

    @property
    def render_video_file_path(self) -> Path:
        return self.render_dir_path / "video.mp4"

    @property
    def render_subtitles_file_path(self) -> Path:
        return self.render_dir_path / "subtitles.srt"

    @property
    def render_cover_file_path(self) -> Path:
        return self.render_dir_path / "cover.png"

    @property
    def render_timeline_file_path(self) -> Path:
        return self.render_dir_path / "timeline.json"

    @property
    def render_automatic_checks_file_path(self) -> Path:
        return self.render_dir_path / "automatic-checks.json"

    @property
    def delivery_records_dir_path(self) -> Path:
        return self.root_dir_path / "delivery-records"

    @property
    def explainer_studio_versions_file_path(self) -> Path:
        return self.root_dir_path / "explainer-studio-versions.json"
