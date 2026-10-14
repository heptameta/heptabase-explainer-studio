"""The cost report: what making a series took, from `cost show --json`, the video page and the feedback bundle.

Never stored in the series; worked out when asked (`explainer_studio/cost.py`). It records the agent's usage, not
prices, and paid narration with the provider's estimated cost, as five lists: the episodes, the agents that worked on
the series, the steps of the flow that had work, every model call and every paid narration call, each call belonging to
one step (by its `episode_id` and `step`). What a step took in calls and
tokens is the sum of its calls; the step itself keeps only what the calls cannot tell: its working time and how many
times its main command ran. Dollars for the model calls are worked out only for display, from a local price table
(`model_prices`), at the prices in effect on each call's day.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

# a harness whose transcripts `agent_transcripts` can read
HarnessName = Literal["claude-code"]

# The steps of the flow, in order: the series' planning (flow steps 1 to 4, `episode_id` None), then an episode's making
# up to its first delivery (flow step 5), then all its work after the first delivery, however many deliveries follow
# (flow step 6).
PLANNING_STEPS = ("audience", "deep_reading", "plan", "plan_review")
EPISODE_STEPS = ("script", "audience_review", "narration", "scenes", "render")
Step = Literal["audience", "deep_reading", "plan", "plan_review", "script", "audience_review", "narration", "scenes",
               "render", "after_delivery"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TokenUsage(StrictModel):
    non_cached_input_tokens: int = 0
    cache_read_tokens: int = 0
    five_minute_cache_write_tokens: int = 0
    one_hour_cache_write_tokens: int = 0
    output_tokens: int = 0


class DeliverySummary(StrictModel):
    """A delivery, from its record and its timeline."""

    delivered_at: AwareDatetime
    explainer_studio_version: str
    duration_seconds: float | None = None  # the video's length; None when the record lacks its timeline
    scene_count: int | None = None


class CostReportEpisode(StrictModel):
    episode_id: str
    # None while the episode is still being made; the boundary between its render step and after_delivery
    first_delivery: DeliverySummary | None = None


class CostReportAgent(StrictModel):
    """One conversation that worked on the series: the main agent the person talks to, or a subagent it started."""

    id: str  # agent-1, agent-2 … in the order of their first counted call; only meaningful within the report
    harness_name: HarnessName  # the harness the conversation ran in
    kind: Literal["main", "audience_reviewer", "scene_writer", "other_subagent"]
    parent_agent_id: str | None = None  # the agent that started this subagent; None for a main agent


class CostReportStep(StrictModel):
    """A step of the flow that had work: one per `episode_id` and `step`."""

    episode_id: str | None = None  # None for the series' planning steps
    step: Step
    working_duration_seconds: int = 0  # the agent or the CLI at work; waiting for the person is left out
    round_count: int | None = None  # audience_review: script audience review prompts prepared
    scene_preview_count: int | None = None  # scenes: scenes rendered by `preview` (previewing three counts 3)
    render_count: int | None = None  # render: renders of the whole episode


class CostReportModelCall(StrictModel):
    called_at: AwareDatetime
    agent_id: str
    episode_id: str | None = None
    step: Step
    turn_number: int  # 1 for the calls before the person first wrote to the agent again, 2 after that …
    model_name: str
    effort: str | None = None  # as the harness names it (high, xhigh …); None when its transcript does not say
    speed: str | None = None  # standard or fast
    is_waiting: bool = False  # every tool the call used only waited (a shell sleep, reading a background task)
    token_usage: TokenUsage = TokenUsage()


class CostReportNarrationCall(StrictModel):
    """A paid narration call, from spending.jsonl."""

    called_at: AwareDatetime
    episode_id: str
    step: Step
    provider_name: str
    character_count: int = 0
    cost_usd: float = 0  # the provider's estimate when the narration was made; the budget sums the same records
    is_estimated: bool = True


class CostReport(StrictModel):
    unavailable_reason: str | None = None  # None: the report could be worked out
    episodes: list[CostReportEpisode] = []
    agents: list[CostReportAgent] = []
    steps: list[CostReportStep] = []  # in the order of the flow
    model_calls: list[CostReportModelCall] = []  # in time order
    narration_calls: list[CostReportNarrationCall] = []  # in time order
