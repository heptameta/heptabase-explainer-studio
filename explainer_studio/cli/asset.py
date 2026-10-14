"""`asset ...`: find, fetch and make external material for scenes.

Downloads land in production/shared/assets/<kind>/ (or `--to`, a folder or a file path) and are recorded in
production/credits.yaml. Pictures meant only for the agent's eyes (thumbnail sheets, page thumbnail sheets, grids) go
to a temporary folder.
"""

from __future__ import annotations

from pathlib import Path

import click

from ..errors import StudioError
from ..paths import Series
from .common import (
    add_series_option,
    open_series,
    parse_list,
    parse_time_seconds,
    print_progress,
    print_result,
    print_warning,
)

TO_OPTION = click.option("--to", "destination_path", type=click.Path(path_type=Path), default=None,
                         help="Where to save: a folder (for example an episode's assets/) or a file path. "
                              "Default: production/shared/assets/<kind>/.")


@click.group()
def asset() -> None:
    """Find, fetch and make external material: Commons, Bioicons, portraits, data, PDFs, 3D and screen recordings."""


# Wikimedia Commons --------------------------------------------------------------------------------------------------
@asset.group()
def commons() -> None:
    """Wikimedia Commons: paintings, photographs, documents, diagrams, footage, recordings and 3D models."""


@commons.command("search")
@click.argument("query")
@click.option("--media-type", "media_type", type=click.Choice(["photo", "svg", "video", "audio", "3d"]), default=None,
              help="What to look for (default: pictures of any kind).")
@click.option("--limit", default=12, show_default=True, type=click.IntRange(1, 40), metavar="N")
def commons_search(query: str, media_type: str | None, limit: int) -> None:
    """Search Commons for freely licensed files and draw a numbered thumbnail sheet of the candidates."""
    from ..assets.commons import draw_search_result_thumbnail_sheet, search

    found_files = search(query, media_type, limit)
    if not found_files:
        print_result(f"no freely licensed {media_type or 'picture'} found for {query!r}; try other words or another "
                     "--media-type")
        return
    for number, commons_file in enumerate(found_files, start=1):
        print_result(f"{number}. {commons_file.title} | {commons_file.summary}")
    thumbnail_sheet = draw_search_result_thumbnail_sheet(found_files)
    if thumbnail_sheet:
        print_result(f"thumbnail sheet: {thumbnail_sheet}")
    hint = " --start <s> --end <s>" if media_type in ("video", "audio") else ""
    print_result(f'download one with: explainer-studio asset commons download "<File:...>"{hint}')


@commons.command("download")
@click.argument("name_or_url", metavar="FILE")
@TO_OPTION
@click.option("--start", "start_text", default=None, metavar="TIME",
              help="Video and long audio: where the clip starts (seconds or m:ss).")
@click.option("--end", "end_text", default=None, metavar="TIME",
              help="Video and long audio: where it ends (at most 120 s after --start).")
@add_series_option
def commons_download(name_or_url: str, destination_path: Path | None, start_text: str | None, end_text: str | None,
                     series_path: Path | None) -> None:
    """Download one Commons file (a File: name or URL) and record its credit."""
    from ..assets.commons import download_file

    series = open_series(series_path)
    start_seconds = parse_time_seconds(start_text, "--start") if start_text is not None else None
    end_seconds = parse_time_seconds(end_text, "--end") if end_text is not None else None
    path, license, warnings = download_file(series, name_or_url, destination_path, start_seconds, end_seconds,
                                            print_progress)
    print_result(f"saved {series.convert_path_to_production_relative_path(path)} ({license}); credit recorded in "
                 "production/credits.yaml")
    for message in warnings:
        print_warning(message)


# Bioicons -----------------------------------------------------------------------------------------------------------
@asset.group()
def bioicons() -> None:
    """Bioicons: about 2,800 free science icons (cells, organs, apparatus, molecules) as SVG."""


@bioicons.command("search")
@click.argument("query")
@click.option("--limit", default=12, show_default=True, type=click.IntRange(1, 40), metavar="N")
def bioicons_search(query: str, limit: int) -> None:
    """Search Bioicons and draw a numbered thumbnail sheet of the matches."""
    from ..assets.bioicons import draw_search_result_thumbnail_sheet, search

    found_icons = search(query, limit)
    if not found_icons:
        print_result(f"no Bioicons icon matches {query!r}; try a broader word (cell, neuron, flask)")
        return
    for number, icon in enumerate(found_icons, start=1):
        print_result(f"{number}. {icon.name} | {icon.category} | {icon.license} | by {icon.author}")
    thumbnail_sheet = draw_search_result_thumbnail_sheet(found_icons)
    if thumbnail_sheet:
        print_result(f"thumbnail sheet: {thumbnail_sheet}")
    print_result('download one with: explainer-studio asset bioicons download "<name>"')


@bioicons.command("download")
@click.argument("name_or_url", metavar="ICON")
@TO_OPTION
@add_series_option
def bioicons_download(name_or_url: str, destination_path: Path | None, series_path: Path | None) -> None:
    """Download one Bioicons SVG by its name (as a search printed it) and record its credit."""
    from ..assets.bioicons import download_icon

    series = open_series(series_path)
    path, icon = download_icon(series, name_or_url, destination_path)
    print_result(f"saved {series.convert_path_to_production_relative_path(path)} ({icon.license}, by {icon.author}); "
                 "credit recorded in production/credits.yaml")


# Wikipedia ----------------------------------------------------------------------------------------------------------
@asset.group()
def wikipedia() -> None:
    """Wikipedia: portraits of people."""


@wikipedia.command("download-portrait")
@click.argument("article_title", metavar="ARTICLE")
@TO_OPTION
@click.option("--language", "language_code", default=None, metavar="CODE",
              help="Which Wikipedia (en, zh, ja...). Default: zh for CJK titles, else en.")
@add_series_option
def wikipedia_download_portrait(article_title: str, destination_path: Path | None, language_code: str | None,
                                series_path: Path | None) -> None:
    """Download an article's lead image when Commons says it is public domain or CC0."""
    from ..assets.wikipedia import download_portrait

    series = open_series(series_path)
    path, license, author = download_portrait(series, article_title, destination_path, language_code)
    author_note = f", by {author}" if author else ""
    print_result(f"saved {series.convert_path_to_production_relative_path(path)} ({license}{author_note}); credit "
                 "recorded in production/credits.yaml")


# Data ---------------------------------------------------------------------------------------------------------------
ENTITIES_OPTION = click.option("--entities", default=None, metavar="ENTITIES",
                               help="Comma-separated country names or ISO codes (default: all).")
YEARS_OPTION = click.option("--years", default=None, metavar="FROM,TO",
                            help="From,to, inclusive, for example 1950,2020.")


def _print_data_summary(series, path: Path, rows: list[dict], title: str, entities: list[str] | None) -> None:
    print_result(f"saved {series.convert_path_to_production_relative_path(path)}: {title}, {len(rows)} rows, "
                 f"columns {', '.join(rows[0])}")
    for row in rows[:3]:
        print_result("  " + ", ".join(str(value) for value in row.values()))
    print_result("credit recorded in production/credits.yaml (CC BY 4.0)")
    found_entities = {str(row.get(key, "")).lower() for row in rows for key in ("entity", "code")}
    missing_entities = [entity for entity in entities or [] if entity.lower() not in found_entities]
    if missing_entities:
        print_warning(f"no data for {', '.join(missing_entities)}")


@asset.group()
def owid() -> None:
    """Our World in Data charts as CSV."""


@owid.command("download")
@click.argument("chart_slug", metavar="CHART")
@ENTITIES_OPTION
@YEARS_OPTION
@TO_OPTION
@add_series_option
def owid_download(chart_slug: str, entities: str | None, years: str | None, destination_path: Path | None,
                  series_path: Path | None) -> None:
    """Download a chart's data (the slug in ourworldindata.org/grapher/<slug>) as CSV."""
    from ..assets.common import parse_years
    from ..assets.owid import download_chart

    series = open_series(series_path)
    wanted_entities = parse_list(entities)
    path, rows, title = download_chart(series, chart_slug, wanted_entities, parse_years(years), destination_path)
    _print_data_summary(series, path, rows, title, wanted_entities)


@asset.group()
def worldbank() -> None:
    """World Bank indicators as CSV."""


@worldbank.command("download")
@click.argument("indicator_code", metavar="INDICATOR")
@ENTITIES_OPTION
@YEARS_OPTION
@TO_OPTION
@add_series_option
def worldbank_download(indicator_code: str, entities: str | None, years: str | None, destination_path: Path | None,
                       series_path: Path | None) -> None:
    """Download an indicator (for example NY.GDP.PCAP.CD) as CSV with columns entity, code, year, value."""
    from ..assets.common import parse_years
    from ..assets.worldbank import download_indicator

    series = open_series(series_path)
    wanted_entities = parse_list(entities)
    path, rows, indicator_name = download_indicator(series, indicator_code, wanted_entities, parse_years(years),
                                                    destination_path)
    _print_data_summary(series, path, rows, indicator_name, wanted_entities)


# PDF and images -----------------------------------------------------------------------------------------------------
def _open_series_if_any(series_path: Path | None) -> Series | None:
    """The series, or None outside one (while reading the sources, before plan.yaml exists); a --series that is not a
    series folder is still an error."""
    try:
        return open_series(series_path)
    except StudioError:
        if series_path is not None:
            raise
        return None


@asset.group()
def pdf() -> None:
    """Look at PDF sources and cut figures out of them."""


@pdf.command("draw-page-thumbnail-sheets")
@click.argument("file_path", metavar="FILE", type=click.Path(path_type=Path))
@click.option("--first-page", "first_page_number", default=1, show_default=True, type=click.IntRange(min=1),
              metavar="PAGE", help="The first page number.")
@click.option("--last-page", "last_page_number", default=None, type=click.IntRange(min=1), metavar="PAGE",
              help="The last page number (at most 60 per run).")
def pdf_draw_page_thumbnail_sheets(file_path: Path, first_page_number: int, last_page_number: int | None) -> None:
    """Draw page thumbnail sheets, six pages to a page thumbnail sheet, to find the pages with figures, tables and
    formulas."""
    from ..assets.pdf import draw_page_thumbnail_sheets, find_pdf

    page_thumbnail_sheets, page_count, shown_page_range = draw_page_thumbnail_sheets(
        find_pdf(file_path, _open_series_if_any(None)), first_page_number, last_page_number)
    print_result(f"{file_path.name}: {page_count} pages; pages {shown_page_range[0]}-{shown_page_range[1]} on "
                 f"{len(page_thumbnail_sheets)} page thumbnail sheet(s):")
    for page_thumbnail_sheet in page_thumbnail_sheets:
        print_result(f"  {page_thumbnail_sheet}")
    if shown_page_range[1] < page_count:
        print_result(f"more: explainer-studio asset pdf draw-page-thumbnail-sheets {file_path} --first-page "
                     f"{shown_page_range[1] + 1}")


@pdf.command("crop")
@click.argument("file_path", metavar="FILE", type=click.Path(path_type=Path))
@click.option("--page", "page_number", required=True, type=click.IntRange(min=1), metavar="PAGE",
              help="The PDF page number.")
@click.option("--box", default=None, metavar="X0,Y0,X1,Y1",
              help="x0,y0,x1,y1 as fractions of the page from the top-left (default: the whole page).")
@click.option("--dpi", default=200, show_default=True, type=click.IntRange(50, 600), metavar="DPI")
@TO_OPTION
@add_series_option
def pdf_crop(file_path: Path, page_number: int, box: str | None, dpi: int, destination_path: Path | None,
             series_path: Path | None) -> None:
    """Save one PDF page, or a box of it, as a PNG.

    Outside a series (while reading the sources, before plan.yaml exists) it goes to `--to`, or to a temporary
    folder for your eyes only."""
    from ..assets.pdf import crop, find_pdf, parse_box

    series = _open_series_if_any(series_path)
    path = crop(series, find_pdf(file_path, series), page_number, parse_box(box), destination_path, dpi)
    if series is None and destination_path is None:
        print_result(f"saved {path} (a temporary file for your eyes only: no series yet to keep it in)")
    else:
        print_result(f"saved {series.convert_path_to_production_relative_path(path) if series else path}")


@asset.group()
def image() -> None:
    """Images: positions for marks."""


@image.command("draw-grid")
@click.argument("file_path", metavar="FILE", type=click.Path(path_type=Path))
def image_draw_grid(file_path: Path) -> None:
    """Draw a copy of the image with a labeled line every 10%, to read where to place a mark."""
    from ..assets.image_grid import draw_grid

    print_result(f"grid: {draw_grid(file_path.expanduser())}")


# Blender and Playwright ---------------------------------------------------------------------------------------------
@asset.group()
def blender() -> None:
    """3D shots rendered by Blender (needs `explainer-studio setup blender`)."""


@blender.command("render")
@click.argument("spec", type=click.Path(path_type=Path))
@TO_OPTION
@add_series_option
def blender_render(spec: Path, destination_path: Path | None, series_path: Path | None) -> None:
    """Render a 3D shot from a YAML or JSON spec into <name>.mp4 and <name>.labels.json."""
    from ..assets.blender import render

    series = open_series(series_path)
    output_file_path_by_kind_map = render(series, spec, destination_path, print_progress)
    for kind, path in output_file_path_by_kind_map.items():
        print_result(f"{kind}: {series.convert_path_to_production_relative_path(path)}")


@asset.group()
def playwright() -> None:
    """Screen recordings of web pages (needs `explainer-studio setup playwright`)."""


@playwright.command("record")
@click.argument("spec", type=click.Path(path_type=Path))
@TO_OPTION
@add_series_option
def playwright_record(spec: Path, destination_path: Path | None, series_path: Path | None) -> None:
    """Record a scripted walk through a web page into <name>.mp4 and <name>.steps.json."""
    from ..assets.playwright import record

    series = open_series(series_path)
    output_file_path_by_kind_map = record(series, spec, destination_path, print_progress)
    for kind, path in output_file_path_by_kind_map.items():
        print_result(f"{kind}: {series.convert_path_to_production_relative_path(path)}")
