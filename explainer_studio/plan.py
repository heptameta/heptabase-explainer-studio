"""Loading and checking production/plan.yaml."""

from __future__ import annotations

from .errors import StudioError
from .file_io import load_yaml_model
from .paths import EPISODE_ID_PATTERN, Series
from .presenters import check_has_playbook
from .schemas.plan import Plan


def load_plan(series: Series) -> Plan:
    return load_yaml_model(Plan, series.plan_file_path, "plan.yaml")


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
