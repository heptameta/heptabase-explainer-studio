"""World Bank indicators (for example NY.GDP.PCAP.CD, SP.DYN.LE00.IN) as CSV: entity, code, year, value."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

from ..errors import StudioError
from ..paths import Series
from .common import choose_output_file_path, keep_rows, sanitize_file_stem, write_csv
from .credits import record_credit
from .fetch import fetch_json

API_URL_TEMPLATE = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{2,3}$")


def _fetch_indicator_rows(indicator_code: str, country_query: str, years: tuple[int, int] | None) -> list[dict]:
    params = {"format": "json", "per_page": 20000}
    if years:
        params["date"] = f"{years[0]}:{years[1]}"
    url = API_URL_TEMPLATE.format(countries=quote(country_query, safe=";"), indicator=quote(indicator_code))
    rows, page, page_count = [], 1, 1
    while page <= page_count:
        response = fetch_json(url, {**params, "page": page}, timeout_seconds=180)
        if not isinstance(response, list) or len(response) < 2:
            is_message_list = isinstance(response, list) and response and isinstance(response[0], dict)
            message = response[0].get("message") if is_message_list else response
            raise StudioError(f"the World Bank API refused {indicator_code}", str(message)[:300],
                              "check the indicator code (data.worldbank.org/indicator) and the country codes")
        page_count = int(response[0].get("pages") or 1)
        rows.extend(response[1] or [])
        page += 1
    return rows


def download_indicator(series: Series, indicator_code: str, entities: list[str] | None, years: tuple[int, int] | None,
                       destination_path: Path | None) -> tuple[Path, list[dict[str, str]], str]:
    """Returns (path, rows, indicator name). Entities are ISO codes or country names."""
    should_query_by_code = entities is not None and all(COUNTRY_CODE_PATTERN.match(entity) for entity in entities)
    raw_rows = _fetch_indicator_rows(indicator_code.strip(), ";".join(entities) if should_query_by_code else "all",
                                     years)
    rows = [{"entity": raw_row["country"]["value"], "code": raw_row.get("countryiso3code") or raw_row["country"]["id"],
             "year": raw_row["date"], "value": raw_row["value"]}
            for raw_row in raw_rows if raw_row.get("value") is not None]
    if entities and not should_query_by_code:
        rows = keep_rows(rows, entities, None)
    rows.sort(key=lambda row: (row["entity"], row["year"]))
    if not rows:
        raise StudioError(f"no World Bank data for {indicator_code}",
                          "no rows with values for these entities and years",
                          "check the country codes or names and the years")
    indicator_name = raw_rows[0]["indicator"]["value"] if raw_rows else indicator_code
    target_file_path = choose_output_file_path(series, "data", f"{sanitize_file_stem(indicator_code)}.csv",
                                               destination_path)
    write_csv(target_file_path, rows)
    record_credit(series, target_file_path, f"{indicator_name} ({indicator_code}, World Bank)",
                  "World Bank", "CC BY 4.0", f"https://data.worldbank.org/indicator/{indicator_code}", LICENSE_URL)
    return target_file_path, rows, indicator_name
