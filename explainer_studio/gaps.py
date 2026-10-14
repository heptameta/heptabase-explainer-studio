"""Gaps: what the product could not do for a video, and what was done instead.

`production/gaps.json` is append-only: no gap is ever resolved or removed. Every feedback bundle carries the whole
file; a gap's `shared_at` records the first bundle that carried it.
"""

from __future__ import annotations

import re
from typing import get_args

from .errors import StudioError
from .file_io import get_current_time, hold_lock, load_json_model, write_json_model
from .paths import Series, parse_episode_number
from .schemas.gaps import Gap, GapKind, Gaps

GAP_KINDS: tuple[str, ...] = get_args(GapKind)


def load_gaps(series: Series) -> Gaps:
    return load_json_model(Gaps, series.gaps_file_path, "gaps.json") if series.gaps_file_path.exists() else Gaps()


def add_gap(series: Series, kind: str, need: str, workaround: str, episode_id: str | None = None) -> Gap:
    if kind not in GAP_KINDS:
        raise StudioError(f"{kind!r} is not a gap kind", f"use one of {', '.join(GAP_KINDS)}")
    if episode_id is not None:
        parse_episode_number(episode_id)
    if not need.strip() or not workaround.strip():
        raise StudioError("a gap needs both --need and --workaround", "the team needs to know what was missing and "
                          "what was done instead", 'say concretely, for example --need "a 3D heart with labelled '
                          'chambers" --workaround "a labelled 2D cross-section"')
    with hold_lock(series.gaps_file_path):
        gaps = load_gaps(series)
        last_gap_number = max((int(gap.id[2:]) for gap in gaps.gaps if re.fullmatch(r"g-\d+", gap.id)), default=0)
        gap = Gap(id=f"g-{last_gap_number + 1}", kind=kind,  # type: ignore[arg-type]
                  episode_id=episode_id, need=need.strip(), workaround=workaround.strip(),
                  created_at=get_current_time())
        gaps.gaps.append(gap)
        write_json_model(series.gaps_file_path, gaps)
    return gap
