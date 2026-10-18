"""Loading and checking production/plan.yaml."""

from __future__ import annotations

from typing import Any

from .errors import StudioError
from .file_io import convert_yaml_document_to_plain_data, load_yaml_model, read_yaml_document
from .paths import EPISODE_ID_PATTERN, Series
from .presenters import check_has_playbook
from .schemas.plan import Plan


def load_plan(series: Series) -> Plan:
    return load_yaml_model(Plan, series.plan_file_path, "plan.yaml")


def read_raw_plan(series: Series) -> tuple[Any, dict[str, Any], str | None]:
    """plan.yaml as written, even when it is not valid, for what shows as much of it as it can (the pages, the
    whiteboard): its YAML document (None when it cannot be read), its plain data ({} then), and why it cannot be read."""
    try:
        document = read_yaml_document(series.plan_file_path)
    except StudioError as error:
        return None, {}, f"{error.what}: {error.why}"
    except OSError as error:
        return None, {}, str(error)
    raw_plan = convert_yaml_document_to_plain_data(document)
    return document, (raw_plan if isinstance(raw_plan, dict) else {}), None


def list_raw_episode_ids(raw_plan: dict[str, Any]) -> list[str]:
    """The raw plan's episode ids that are valid ones, in plan order."""
    return [raw_episode["id"] for raw_episode in raw_plan.get("episodes") or []
            if isinstance(raw_episode, dict) and isinstance(raw_episode.get("id"), str)
            and EPISODE_ID_PATTERN.match(raw_episode["id"])]


def read_series_title(series: Series) -> str:
    return str(read_raw_plan(series)[1].get("title") or series.root_dir_path.name)


def validate_plan(series: Series) -> tuple[Plan, list[str]]:
    """The plan, or a StudioError listing every problem. Returns notes worth telling the user."""
    plan = load_plan(series)
    planned_episode_ids = {episode.id for episode in plan.episodes}
    if series.episodes_dir_path.is_dir():
        stray_episode_ids = sorted(path.name for path in series.episodes_dir_path.iterdir()
                                   if path.is_dir() and EPISODE_ID_PATTERN.match(path.name)
                                   and path.name not in planned_episode_ids)
        if stray_episode_ids:
            raise StudioError("episode folders do not match the plan",
                              "these folders are under production/episodes/ but not in plan.yaml",
                              "rename the folders to match the plan ids (after reordering), or remove them",
                              [f"production/episodes/{episode_id}" for episode_id in stray_episode_ids])
    notes = [f"{episode.id} uses a draft playbook: {episode.presenter_name} has no playbook for "
             f"{episode.question_type} yet"
             for episode in plan.episodes if not check_has_playbook(episode.presenter_name, episode.question_type)]
    return plan, notes
