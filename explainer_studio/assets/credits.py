"""Recording where a downloaded asset came from in production/credits.yaml.

One credit per asset file; downloading the same file again replaces its credit. The file is read and written
round-trip, so credits and comments the agent added by hand survive.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ..errors import StudioError
from ..file_io import get_current_time, hold_lock, read_yaml_document, write_yaml
from ..paths import Series
from ..schemas.credits import Credit


def record_credit(series: Series, asset_file_path: Path, title: str, author: str | None, license: str, source_url: str,
                  license_url: str | None = None) -> Credit:
    credit = Credit(asset_file_path=series.convert_path_to_production_relative_path(asset_file_path),
                    title=title.strip() or asset_file_path.name, author=(author or "").strip() or None,
                    license=license.strip() or "unknown", license_url=license_url or None, source_url=source_url,
                    downloaded_at=get_current_time())
    credits_file_path = series.credits_file_path
    with hold_lock(credits_file_path):
        document = (read_yaml_document(credits_file_path) if credits_file_path.exists() else None) or CommentedMap()
        if isinstance(document, dict) and document.get("credits") is None:
            document["credits"] = CommentedSeq()
        if not isinstance(document, dict) or not isinstance(document["credits"], list):
            raise StudioError("credits.yaml has no `credits:` list", "each credit is one asset file",
                              f"fix {credits_file_path} so it is `credits:` followed by a list of credits")
        entries = document["credits"]
        for index in reversed(range(len(entries))):
            entry = entries[index]
            if isinstance(entry, dict) and entry.get("asset_file_path") == credit.asset_file_path:
                del entries[index]
        entries.append(credit.model_dump(mode="json", exclude_none=True))
        write_yaml(credits_file_path, document)
    return credit
