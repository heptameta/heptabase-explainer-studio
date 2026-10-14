"""production/spending.jsonl: one line per paid call, its `kind` saying what was paid for (only narration so far).
Append-only; the budget check sums the narration records."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ..narration_providers import NarrationProviderName


class SpendingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["narration"]
    spent_at: AwareDatetime
    episode_id: str
    provider_name: NarrationProviderName
    character_count: int
    cost_usd: float
    is_estimated: bool
