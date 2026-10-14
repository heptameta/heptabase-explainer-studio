"""automatic-checks.json under preview/<scene>/ and render/: layout issues found at the end of every beat.

Always written, even when empty, so "checked, nothing found" differs from "not checked". Which checks block delivery
is defined in code (`BLOCKING_CHECK_NAMES`), not stored.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

# the checks in `scene_kit.layout_checks`
CheckName = Literal["text_too_small", "text_overlap", "text_outside_frame", "outside_container"]
BLOCKING_CHECK_NAMES: frozenset[CheckName] = frozenset({"text_too_small"})


class Issue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_name: CheckName
    scene_id: str
    beat_id: str | None = None
    detail: str


class AutomaticChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issues: list[Issue] = []

    def find_blocking_issues(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.check_name in BLOCKING_CHECK_NAMES]
