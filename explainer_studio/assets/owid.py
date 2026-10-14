"""Our World in Data: a grapher chart's data as CSV, filtered to the entities and years a scene needs.

Scenes read the CSV; they never go online. OWID's own charts are CC BY 4.0; the citation names the original sources.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import quote

from ..errors import StudioError
from ..paths import Series
from .common import choose_output_file_path, keep_rows, sanitize_file_stem, write_csv
from .credits import record_credit
from .fetch import fetch_json, fetch_response

GRAPHER_URL_TEMPLATE = "https://ourworldindata.org/grapher/{slug}"
QUERY_STRING = "?v=1&csvType=full&useColumnShortNames=true"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


def download_chart(series: Series, slug: str, entities: list[str] | None, years: tuple[int, int] | None,
                   destination_path: Path | None) -> tuple[Path, list[dict[str, str]], str]:
    """Returns (path, rows, chart title)."""
    chart_url = GRAPHER_URL_TEMPLATE.format(slug=quote(slug.strip()))
    csv_text = fetch_response(f"{chart_url}.csv{QUERY_STRING}", timeout_seconds=180).content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        raise StudioError(f"Our World in Data returned no rows for {slug}", "the chart has no data",
                          "check the chart slug in its URL: ourworldindata.org/grapher/<slug>")
    kept_rows = keep_rows(rows, entities, years)
    if not kept_rows:
        sample_entities = sorted({row.get("entity", "") for row in rows})[:12]
        raise StudioError("no rows left after filtering", f"entities look like: {', '.join(sample_entities)}",
                          "check the entity names or ISO codes and the years")
    try:
        metadata = fetch_json(f"{chart_url}.metadata.json{QUERY_STRING}")
    except StudioError:
        metadata = {}
    chart = metadata.get("chart") or {}
    title = chart.get("title") or slug
    citation = chart.get("citation") or ""
    target_file_path = choose_output_file_path(series, "data", f"{sanitize_file_stem(slug)}.csv", destination_path)
    write_csv(target_file_path, kept_rows)
    author = "Our World in Data" + (f", from {citation}" if citation else "")
    record_credit(series, target_file_path, f"{title} (Our World in Data)", author, "CC BY 4.0", chart_url, LICENSE_URL)
    return target_file_path, kept_rows, title
