"""Spending: one line in production/spending.jsonl per paid narration call, and the series budget check.

The budget (`narration_budget_usd` in plan.yaml) caps everything the series has spent on narration, across episodes,
retries and conversations. Costs come from each provider's price table, so they are marked as estimates.
"""

from __future__ import annotations

from typing import Any

from .errors import StudioError
from .file_io import append_jsonl, get_current_time, read_jsonl
from .narration_providers import NarrationProviderName
from .paths import Series
from .schemas.plan import Plan
from .schemas.spending import SpendingRecord


def format_usd(amount_usd: float) -> str:
    return f"${amount_usd:.2f}" if amount_usd >= 1 or amount_usd == 0 else f"${amount_usd:.4f}"


def read_narration_spending_records(series: Series) -> list[dict[str, Any]]:
    """The narration records of spending.jsonl, unvalidated. A record without a `kind` comes from an earlier format and
    is refused, so the budget never counts its money as nothing; a kind this version does not know is left out."""
    records = read_jsonl(series.spending_file_path)
    for record_number, record in enumerate(records, start=1):
        if "kind" not in record:
            raise StudioError(f"spending.jsonl record {record_number} has no kind",
                              "it was written in an earlier format, before each record said what was paid for",
                              f"convert {series.spending_file_path} as `explainer-studio guide "
                              "references/file-formats.md` describes (spending.jsonl)")
    return [record for record in records if record["kind"] == "narration"]


def compute_spent_usd(series: Series) -> float:
    """What the series has spent on narration."""
    return sum(float(record.get("cost_usd") or 0) for record in read_narration_spending_records(series))


def record_spending(series: Series, episode_id: str, provider_name: NarrationProviderName, character_count: int,
                    cost_usd: float, is_estimated: bool) -> None:
    record = SpendingRecord(kind="narration", spent_at=get_current_time(), episode_id=episode_id,
                            provider_name=provider_name, character_count=character_count,
                            cost_usd=round(cost_usd, 6), is_estimated=is_estimated)
    append_jsonl(series.spending_file_path, record.model_dump(mode="json"))


def require_within_budget(series: Series, plan: Plan, estimated_cost_usd: float) -> None:
    """Refuse a run whose estimate would take the series past its budget. A null budget means no limit."""
    budget_usd = plan.narration_budget_usd
    if budget_usd is None or estimated_cost_usd <= 0:
        return
    spent_usd = compute_spent_usd(series)
    if spent_usd + estimated_cost_usd > budget_usd:
        raise StudioError(
            "narration would go over the series budget",
            f"spent {format_usd(spent_usd)} of the {format_usd(budget_usd)} budget; this run is estimated at "
            f"{format_usd(estimated_cost_usd)} "
            "(costs are estimates from the provider's price table)",
            "ask the user whether to raise narration_budget_usd in production/plan.yaml (or on the plan page), or "
            "narrate fewer beats with --beats")
