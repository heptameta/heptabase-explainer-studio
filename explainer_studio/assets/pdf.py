"""Looking at PDF sources: page thumbnail sheets of six pages, and one page (or part of it) as an image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..errors import StudioError
from ..paths import Series
from .common import choose_output_file_path, create_viewing_dir, sanitize_file_stem

MAX_PAGE_COUNT_PER_RUN = 60
THUMBNAIL_WIDTH_PIXELS = 360
ROW_COUNT = 2
COLUMN_COUNT = 3


def find_pdf(pdf_file_path: Path, series: Series | None) -> Path:
    """A PDF path as given, or relative to production/ (where `sources/` lives)."""
    candidates = [pdf_file_path.expanduser()]
    if series is not None and not pdf_file_path.is_absolute():
        candidates.append(series.production_dir_path / pdf_file_path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise StudioError(f"{pdf_file_path} not found",
                      "looked in the current folder" + (" and production/" if series else ""), "pass the PDF's path")


def _open_pdf_document(path: Path):
    import pypdfium2 as pdfium

    try:
        return pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError as error:
        raise StudioError(f"cannot read {path.name}", str(error),
                          "check that the file is a PDF (and not encrypted)") from None


def draw_page_thumbnail_sheets(pdf_file_path: Path, first_page_number: int = 1,
                               last_page_number: int | None = None) -> tuple[list[Path], int, tuple[int, int]]:
    """Page thumbnail sheets of the pages first_page_number..last_page_number (at most 60). Returns (page thumbnail
    sheets, page count, (first, last) page numbers shown)."""
    document = _open_pdf_document(pdf_file_path)
    page_count = len(document)
    first_page_number = max(1, first_page_number)
    last_page_number = min(page_count, last_page_number or page_count,
                           first_page_number + MAX_PAGE_COUNT_PER_RUN - 1)
    if first_page_number > page_count:
        raise StudioError(f"{pdf_file_path.name} has only {page_count} pages",
                          f"asked to start at page {first_page_number}", "lower --first-page")
    output_dir_path = create_viewing_dir("pdf-pages")
    font = ImageFont.load_default(size=22)
    page_thumbnail_sheets = []
    page_count_per_thumbnail_sheet = ROW_COUNT * COLUMN_COUNT
    for start_page_number in range(first_page_number, last_page_number + 1, page_count_per_thumbnail_sheet):
        end_page_number = min(last_page_number, start_page_number + page_count_per_thumbnail_sheet - 1)
        page_numbers = list(range(start_page_number, end_page_number + 1))
        thumbnails = []
        for page_number in page_numbers:
            page = document[page_number - 1]
            thumbnails.append(page.render(scale=THUMBNAIL_WIDTH_PIXELS / page.get_width()).to_pil().convert("RGB"))
        max_height_pixels = max(thumbnail.height for thumbnail in thumbnails)
        filled_row_count = (len(thumbnails) + COLUMN_COUNT - 1) // COLUMN_COUNT
        page_thumbnail_sheet = Image.new("RGB", (COLUMN_COUNT * (THUMBNAIL_WIDTH_PIXELS + 8) + 8,
                                                 filled_row_count * (max_height_pixels + 8) + 8), (90, 90, 90))
        draw = ImageDraw.Draw(page_thumbnail_sheet)
        for index, (page_number, thumbnail) in enumerate(zip(page_numbers, thumbnails, strict=True)):
            x = 8 + (index % COLUMN_COUNT) * (THUMBNAIL_WIDTH_PIXELS + 8)
            y = 8 + (index // COLUMN_COUNT) * (max_height_pixels + 8)
            page_thumbnail_sheet.paste(thumbnail, (x, y))
            draw.rectangle([x, y, x + 64, y + 30], fill=(255, 255, 255))
            draw.text((x + 6, y + 3), f"p.{page_number}", fill=(220, 0, 0), font=font)
        page_thumbnail_sheet_file_path = output_dir_path / f"pages-{page_numbers[0]:03d}-{page_numbers[-1]:03d}.png"
        page_thumbnail_sheet.save(page_thumbnail_sheet_file_path)
        page_thumbnail_sheets.append(page_thumbnail_sheet_file_path)
    return page_thumbnail_sheets, page_count, (first_page_number, last_page_number)


def parse_box(box: str | None) -> tuple[float, float, float, float] | None:
    if not box:
        return None
    try:
        values = tuple(float(part) for part in box.split(","))
    except ValueError:
        values = ()
    if (len(values) != 4 or not all(0 <= value <= 1 for value in values) or values[0] >= values[2]
            or values[1] >= values[3]):
        raise StudioError(f"--box {box} is not a box", "use x0,y0,x1,y1 as fractions of the page from the top-left, "
                          "with 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1",
                          "read the position off `asset image draw-grid`")
    return values  # type: ignore[return-value]


def crop(series: Series | None, pdf_file_path: Path, page_number: int, box: tuple[float, float, float, float] | None,
         destination_path: Path | None, dpi: int = 200) -> Path:
    document = _open_pdf_document(pdf_file_path)
    if not 1 <= page_number <= len(document):
        raise StudioError(f"{pdf_file_path.name} has no page {page_number}", f"it has {len(document)} pages",
                          "fix --page")
    image = document[page_number - 1].render(scale=dpi / 72).to_pil().convert("RGB")
    file_stem = f"{sanitize_file_stem(pdf_file_path.stem)}-p{page_number:03d}"
    if box:
        width_pixels, height_pixels = image.size
        image = image.crop((round(box[0] * width_pixels), round(box[1] * height_pixels),
                            round(box[2] * width_pixels), round(box[3] * height_pixels)))
        file_stem += "-crop"
    if series is None and destination_path is None:
        target_file_path = create_viewing_dir("pdf-crop") / f"{file_stem}.png"
    else:
        target_file_path = choose_output_file_path(series, "figures", f"{file_stem}.png", destination_path)
    target_file_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(target_file_path)
    return target_file_path
