"""episodes/<episode>/delivery-records/<delivered time>/metadata.json: one record per delivery, kept forever.

The folder is named by the UTC delivered time (`2026-10-08T110632Z`), so the folders sort in delivery order. The video
at the series root is always the newest record's.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class DeliveredSubtitles(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_code: str
    file_name: str  # <NN>-<title>.<language code>.srt


class DeliveredFiles(BaseModel):
    model_config = ConfigDict(extra="forbid")
    video_file_name: str
    cover_file_name: str
    subtitles: list[DeliveredSubtitles]  # today one: the episode's language

    def list_file_names(self) -> list[str]:
        """Every delivered file at the series root: the video, its subtitles and its cover."""
        return [self.video_file_name, *(subtitles.file_name for subtitles in self.subtitles), self.cover_file_name]


class DeliveryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivered_at: AwareDatetime
    explainer_studio_version: str
    # the other versions used on the episode since the previous delivery: a mixed delivery is not a clean sample of
    # its version
    earlier_explainer_studio_versions: list[str] = Field(default_factory=list)
    files: DeliveredFiles
