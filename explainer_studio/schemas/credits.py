"""production/credits.yaml: where each external asset came from. Written by the asset commands; read only by the
scene_kit credits scene. Nothing gates on it."""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class Credit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_file_path: str  # relative to production/
    title: str
    author: str | None = None
    license: str
    license_url: str | None = None
    source_url: str
    downloaded_at: AwareDatetime


class Credits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credits: list[Credit] = []
