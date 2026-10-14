"""The presenters the package knows, and which question types each has a playbook for.

The guide is the single source: `guide/references/presenters/<name>/question-types/<type>.md` is one playbook. An
episode whose presenter has no playbook for its question type uses a draft playbook, written in its `design.md`.
"""

from __future__ import annotations

import functools
from pathlib import Path

PACKAGE_DIR_PATH = Path(__file__).resolve().parent
PRESENTERS_DIR_PATH = PACKAGE_DIR_PATH / "guide" / "references" / "presenters"


def read_playbooks_by_presenter_name(presenters_dir_path: Path) -> dict[str, list[str]]:
    playbooks_by_presenter_name_map = {}
    for presenter_dir_path in sorted(path for path in presenters_dir_path.iterdir()
                                     if (path / "presenter.md").is_file()):
        playbooks_dir_path = presenter_dir_path / "question-types"
        playbooks_by_presenter_name_map[presenter_dir_path.name] = (
            sorted(playbook_file_path.stem for playbook_file_path in playbooks_dir_path.glob("*.md"))
            if playbooks_dir_path.is_dir() else [])
    return playbooks_by_presenter_name_map


@functools.cache
def list_playbooks_by_presenter_name() -> dict[str, list[str]]:
    return read_playbooks_by_presenter_name(PRESENTERS_DIR_PATH)


def check_has_playbook(presenter_name: str, question_type: str) -> bool:
    return question_type in list_playbooks_by_presenter_name().get(presenter_name, [])
