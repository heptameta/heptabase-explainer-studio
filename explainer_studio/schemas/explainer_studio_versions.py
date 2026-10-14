"""episodes/<episode>/explainer-studio-versions.json: the Explainer Studio versions an episode was worked on with.

Written by every command on the episode (`explainer_studio_versions`); the agent never edits it.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExplainerStudioVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    last_used_version: str  # the version of the latest command on the episode
    # every version used on the episode since its last delivery, in order of first use; deliver empties it
    versions_since_last_delivery: list[str] = Field(default_factory=list)
