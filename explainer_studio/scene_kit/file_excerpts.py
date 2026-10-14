"""Real file text shown on screen, with where it came from.

`read_file_excerpt` reads the lines when the scene renders and records the file, the line range and a hash of the text.
`preview` keeps those records; `render` warns when an excerpt's text differs from what the last preview of the scene
showed, because the file changed after the agent looked at the scene.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .context import get_scene_context

__all__ = ["read_file_excerpt"]

RECORDED_FILE_EXCERPTS: list[dict] = []


def read_excerpt_text(path: Path, first_line_number: int | None, last_line_number: int | None, search_text: str | None,
                      following_line_count: int) -> str:
    lines = path.read_text(encoding="utf-8").split("\n")
    if search_text is not None:
        found_index = next((line_index for line_index, line in enumerate(lines) if search_text in line), None)
        if found_index is None:
            raise ValueError(f"{path}: no line contains {search_text!r} any more; update the read_file_excerpt call")
        return "\n".join(lines[found_index:found_index + 1 + following_line_count])
    first_index = (first_line_number or 1) - 1
    if first_index >= len(lines):
        raise ValueError(f"{path} has only {len(lines)} lines; update the read_file_excerpt call")
    return "\n".join(lines[first_index:last_line_number if last_line_number is not None else len(lines)])


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_file_excerpt(path: str, first_line_number: int | None = None, last_line_number: int | None = None,
                      search_text: str | None = None, following_line_count: int = 0) -> str:
    """The text of a real file to show on screen: lines first_line_number..last_line_number (1-based, inclusive), or
    the first line containing `search_text` plus `following_line_count` more lines (survives edits above it), or the
    whole file. `path` is relative to production/ or absolute. Use it for every code panel, config, log or document
    shown as real; never copy the text by hand."""
    context = get_scene_context()
    resolved = context.resolve_path(path)
    text = read_excerpt_text(resolved, first_line_number, last_line_number, search_text, following_line_count)
    record = {"path": context.convert_path_to_production_relative_path(resolved),
              "first_line_number": first_line_number, "last_line_number": last_line_number, "search_text": search_text,
              "following_line_count": following_line_count, "content_hash": compute_content_hash(text)}
    if record not in RECORDED_FILE_EXCERPTS:
        RECORDED_FILE_EXCERPTS.append(record)
    return text
