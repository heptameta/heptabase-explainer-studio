"""episodes/<episode>/audience-reviews/script.yaml: script audience review rounds.

The prompt command prints each round's header; the audience reviewer returns findings in this format; the writing agent
pastes them and adds a resolution to each finding. The gate before narration reads this file.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FindingResolution(StrictModel):
    action: Literal["fixed", "kept"]
    note: str = ""


class ScriptFinding(StrictModel):
    scene_id: str  # the scene the beat was in when it was read: gates count by it, whatever is renamed later
    beat_id: str
    kind: Literal["lost", "wrong", "minor"]
    problem: str
    resolution: FindingResolution | None = None


class ReviewerSummary(StrictModel):
    question: str
    takeaway: str
    explained_terms: list[str] = []
    lost_beat_id: str | None = None
    most_engaging_beat_id: str | None = None


class ScriptRound(StrictModel):
    scene_ids: list[str]
    reviewer_summary: ReviewerSummary | None = None
    findings: list[ScriptFinding] = []


class ScriptReviews(StrictModel):
    rounds: list[ScriptRound] = []
