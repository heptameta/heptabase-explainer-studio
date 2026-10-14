"""production/gaps.json: what the product could not do and what was done instead. Append-only."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

GapKind = Literal["presenter", "subject", "visual", "tool", "other"]


class Gap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str  # g-1, g-2, ...
    kind: GapKind
    episode_id: str | None = None
    need: str
    workaround: str
    created_at: AwareDatetime
    shared_at: AwareDatetime | None = None


class Gaps(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gaps: list[Gap] = []
