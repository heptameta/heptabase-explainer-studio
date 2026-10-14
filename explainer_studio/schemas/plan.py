"""production/plan.yaml: the series plan.

The agent writes it; the plan page edits single fields. Only fields with a programmatic consumer are strict here.
"""

from __future__ import annotations

from typing import Annotated, Any, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from .. import presenters, question_types
from ..background_music_providers import SETTINGS_MODELS as BACKGROUND_MUSIC_SETTINGS_MODELS
from ..errors import StudioError
from ..narration_providers import SETTINGS_MODELS as NARRATION_SETTINGS_MODELS
from ..paths import format_episode_id

NarrationSettings = Annotated[Union[NARRATION_SETTINGS_MODELS], Field(discriminator="provider_name")]  # noqa: UP007
BackgroundMusicSettings = Annotated[Union[BACKGROUND_MUSIC_SETTINGS_MODELS],  # noqa: UP007
                                    Field(discriminator="provider_name")]

# a BCP 47 language tag such as `en` or `zh-TW`; it becomes part of delivered file names and page URLs
LanguageCode = Annotated[str, Field(pattern=r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*$")]

DEFAULT_BACKGROUND_MUSIC_SETTINGS = TypeAdapter(BackgroundMusicSettings).validate_python(
    {"provider_name": "synthesized-piano"})


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Misconception(StrictModel):
    id: str
    belief: str
    evidence: str


class Audience(StrictModel):
    description: str = Field(min_length=1)
    unfamiliar_terms: list[str] = []
    misconceptions: list[Misconception] = []


class ExcludedTopic(StrictModel):
    topic: str
    reason: str


class Episode(StrictModel):
    id: str
    title: str = Field(min_length=1)
    question: str = Field(min_length=1)
    question_type: str
    concept_goal: str | None = None
    presenter_name: str
    outline: list[str] = Field(min_length=1)
    estimated_duration_seconds: int = Field(gt=0)
    taught_terms: list[str]
    takeaway: str = Field(min_length=1)
    source_scope: str | None = None
    language_code: LanguageCode | None = None
    narration: NarrationSettings | None = None
    background_music: BackgroundMusicSettings | None = None

    @field_validator("question_type")
    @classmethod
    def known_question_type(cls, value: str) -> str:
        if value not in question_types.QUESTION_TYPE_BY_NAME_MAP:
            raise ValueError(f"unknown question type {value!r}; use one of "
                             f"{', '.join(question_types.QUESTION_TYPE_BY_NAME_MAP)}")
        return value

    @field_validator("presenter_name")
    @classmethod
    def known_presenter(cls, value: str) -> str:
        playbooks_by_presenter_name_map = presenters.list_playbooks_by_presenter_name()
        if value not in playbooks_by_presenter_name_map:
            raise ValueError(f"unknown presenter {value!r}; use one of {', '.join(playbooks_by_presenter_name_map)}")
        return value

    @model_validator(mode="after")
    def concept_goal_only_for_concepts(self) -> Episode:
        if self.concept_goal is not None:
            if self.question_type != "concept":
                raise ValueError("concept_goal is only for question_type: concept")
            if self.concept_goal not in question_types.CONCEPT_GOAL_BY_NAME_MAP:
                raise ValueError(f"unknown concept_goal {self.concept_goal!r}; use one of "
                                 f"{', '.join(question_types.CONCEPT_GOAL_BY_NAME_MAP)}")
        return self


class Plan(StrictModel):
    title: str = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    language_code: LanguageCode
    narration_budget_usd: float | None = Field(default=20, ge=0)  # cumulative for the series; null: no limit
    narration: NarrationSettings | None = None
    background_music: BackgroundMusicSettings | None = None
    has_end_credits: bool = True  # render ends every episode on the end credits page (end_credits.py)
    audience: Audience
    goal: str = Field(min_length=1)
    rationale: str | None = None
    episodes: list[Episode] = Field(min_length=1)
    excluded_topics: list[ExcludedTopic] = []

    @model_validator(mode="after")
    def episode_ids_follow_plan_order(self) -> Plan:
        problems = []
        for number, episode in enumerate(self.episodes, start=1):
            expected = format_episode_id(number)
            if episode.id != expected:
                problems.append(f"episode {number} has id {episode.id!r}; it must be {expected!r} (ids follow plan "
                                "order; after reordering, rename the ids and the episode folders)")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def find_episode(self, episode_id: str) -> Episode:
        for episode in self.episodes:
            if episode.id == episode_id:
                return episode
        raise StudioError(f"{episode_id} is not in the plan",
                          f"the plan has {', '.join(episode.id for episode in self.episodes)}",
                          "use an episode id from production/plan.yaml")

    def resolve_episode_language_code(self, episode_id: str) -> str:
        return self.find_episode(episode_id).language_code or self.language_code

    def resolve_episode_narration_settings(self, episode_id: str) -> Any:
        """The narration settings in effect for an episode: its own block replaces the series block entirely."""
        return self.find_episode(episode_id).narration or self.narration

    def resolve_episode_background_music_settings(self, episode_id: str) -> Any:
        return (self.find_episode(episode_id).background_music or self.background_music
                or DEFAULT_BACKGROUND_MUSIC_SETTINGS)
