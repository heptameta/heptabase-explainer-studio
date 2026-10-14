"""automatic-checks.json: the layout issues the scenes found at the end of every beat, and how to report them.

The checks themselves run inside ManimGL (`scene_kit.layout_checks`). This module turns their records into the
schema, writes the file (always, even empty), summarizes it for the command output, and compares the file excerpts
a render showed with what the last preview showed.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..file_io import read_json, write_json, write_json_model
from ..schemas.automatic_checks import BLOCKING_CHECK_NAMES, AutomaticChecks, Issue


def convert_records_to_issues(scene_id: str, records: list[dict]) -> list[Issue]:
    return [Issue(check_name=record["check_name"], scene_id=scene_id, beat_id=record["beat_id"],
                  detail=record["detail"])
            for record in records]


def write_automatic_checks(path: Path, issues: list[Issue]) -> None:
    write_json_model(path, AutomaticChecks(issues=issues))


def format_issue_summary(issues: list[Issue]) -> str:
    """"no issues", or the count per check with the blocking ones first and marked."""
    if not issues:
        return "no issues"
    issue_count_by_check_name_map = Counter(issue.check_name for issue in issues)
    ordered_check_names = sorted(issue_count_by_check_name_map,
                                 key=lambda check_name: (check_name not in BLOCKING_CHECK_NAMES, check_name))
    return ", ".join(f"{check_name} {issue_count_by_check_name_map[check_name]}"
                     + (" (blocks delivery)" if check_name in BLOCKING_CHECK_NAMES else "")
                     for check_name in ordered_check_names)


# File excerpts -------------------------------------------------------------------------------------------------------
def _build_excerpt_key(record: dict) -> tuple:
    return (record["path"], record["first_line_number"], record["last_line_number"], record["search_text"],
            record["following_line_count"])


def write_file_excerpts(path: Path, records: list[dict]) -> None:
    if records:
        write_json(path, {"file_excerpts": records})


def find_changed_file_excerpts(previewed_file_path: Path, rendered_excerpts: list[dict]) -> list[str]:
    """Excerpts whose text differs from what the scene's last preview showed: the file changed since the scene was
    looked at, so the lines on screen may no longer be the ones meant."""
    if not previewed_file_path.exists() or not rendered_excerpts:
        return []
    previewed_excerpts = read_json(previewed_file_path).get("file_excerpts", [])
    content_hash_by_excerpt_key_map = {_build_excerpt_key(record): record["content_hash"]
                                       for record in previewed_excerpts}
    changed_excerpts = []
    for record in rendered_excerpts:
        previewed_hash = content_hash_by_excerpt_key_map.get(_build_excerpt_key(record), record["content_hash"])
        if previewed_hash != record["content_hash"]:
            where = (f"lines {record['first_line_number'] or 1}-{record['last_line_number'] or 'end'}"
                     if record["search_text"] is None
                     else f"the line containing {record['search_text']!r}")
            changed_excerpts.append(f"{record['path']} ({where})")
    return changed_excerpts
