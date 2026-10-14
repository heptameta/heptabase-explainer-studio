"""What the asset commands share: where files go, file names, licences, data rows written as CSV, and folders for
pictures meant only for the agent's eyes (thumbnail sheets, page thumbnail sheets, grids)."""

from __future__ import annotations

import csv
import html
import io
import os
import re
import subprocess
import tempfile
import time
import unicodedata
from collections.abc import Callable
from pathlib import Path

from .. import user_dirs
from ..errors import StudioError
from ..paths import Series

_PUBLIC_DOMAIN_LICENSE_PATTERN = re.compile(r"public domain|^pd\b|\bpd-|cc0|cc-0|cc[- ]?zero|no restrictions",
                                            re.IGNORECASE)
# Free licences the search commands keep: public domain, CC0, CC BY and CC BY-SA (and MIT/BSD for icons).
_FREE_LICENSE_PATTERN = re.compile(_PUBLIC_DOMAIN_LICENSE_PATTERN.pattern + r"|\bcc[- ]by\b", re.IGNORECASE)
_NOT_FREE_LICENSE_PATTERN = re.compile(r"\bnc\b|non-?commercial|\bnd\b|no[- ]?deriv|fair use|copyrighted|all rights",
                                       re.IGNORECASE)
_PERMISSIVE_CODE_LICENSE_PATTERN = re.compile(r"^(mit|bsd)\b", re.IGNORECASE)


def check_is_free(license: str, should_accept_code_licenses: bool = False) -> bool:
    if not license or _NOT_FREE_LICENSE_PATTERN.search(license):
        return False
    return bool(_FREE_LICENSE_PATTERN.search(license)
                or (should_accept_code_licenses and _PERMISSIVE_CODE_LICENSE_PATTERN.search(license)))


def check_is_public_domain(license: str) -> bool:
    return (bool(license) and not _NOT_FREE_LICENSE_PATTERN.search(license)
            and bool(_PUBLIC_DOMAIN_LICENSE_PATTERN.search(license)))


def convert_html_to_plain_text(markup: str | None) -> str:
    """Commons metadata is HTML; keep only its text."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup or ""))
    return re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", text)).strip()


def sanitize_file_stem(text: str, max_characters: int = 80) -> str:
    """A file name stem that works on every platform: letters, digits, dot, dash and underscore."""
    text = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"[^\w.\-]+", "_", text, flags=re.UNICODE).strip("._")
    return cleaned[:max_characters].rstrip("._") or "asset"


def choose_output_file_path(series: Series | None, kind: str, file_name: str, destination_path: Path | None) -> Path:
    """production/shared/assets/<kind>/<file_name>, or `--to` (`destination_path`): a folder, or a file path when it
    has a suffix. Without a series, `destination_path` is required."""
    if destination_path is None:
        if series is None:
            raise ValueError("choose_output_file_path needs a series or a destination_path")
        return series.shared_assets_dir_path / kind / file_name
    path = destination_path.expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.suffix and not path.is_dir():
        return path
    return path / file_name


def create_viewing_dir(name: str) -> Path:
    """A fresh temporary folder for pictures only the agent looks at; nothing in the series refers to them."""
    base_dir_path = user_dirs.ensure_scratch_dir("viewing")
    return Path(tempfile.mkdtemp(prefix=f"{name}-", dir=base_dir_path))


def find_ffmpeg() -> str:
    path = user_dirs.find_tool("ffmpeg")
    if path is None:
        raise StudioError("ffmpeg is not installed", "this command converts media with ffmpeg",
                          "run `explainer-studio setup`")
    return path


SEEK_AFTER_SECONDS = 30  # earlier clips are cheaper to read from the start than to seek to
SEQUENTIAL_ATTEMPT_COUNT = 3


def write_asset_bytes(path: Path, content: bytes) -> None:
    """Write a downloaded file atomically, readable like any other file the user saves."""
    from ..file_io import write_bytes_atomic

    write_bytes_atomic(path, content)
    os.chmod(path, 0o644)


def write_asset_text(path: Path, text: str) -> None:
    from ..file_io import write_text_atomic

    write_text_atomic(path, text)
    os.chmod(path, 0o644)


def keep_rows(rows: list[dict[str, str]], entities: list[str] | None,
              years: tuple[int, int] | None) -> list[dict[str, str]]:
    """Rows whose entity or code is in `entities` (case-insensitive) and whose year is in `years`."""
    wanted_entities = {entity.lower() for entity in entities} if entities else None
    kept_rows = []
    for row in rows:
        if wanted_entities is not None and not any((row.get(key) or "").lower() in wanted_entities
                                                   for key in ("entity", "code")):
            continue
        if years is not None:
            try:
                year = int(str(row.get("year", "")).split("-")[0])
            except ValueError:
                continue
            if not years[0] <= year <= years[1]:
                continue
        kept_rows.append(row)
    return kept_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_asset_text(path, buffer.getvalue())


def measure_media_duration_seconds(path: Path) -> float:
    ffprobe_path = user_dirs.find_tool("ffprobe")
    if ffprobe_path is None or not path.exists():
        return 0.0
    done = subprocess.run([ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                           str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                          check=False)
    try:
        return float(done.stdout.strip())
    except ValueError:
        return 0.0


def cut_remote_clip(url: str, start_seconds: float, end_seconds: float, target_file_path: Path,
                    codec_arguments: list[str], user_agent: str, report_progress: Callable[[str], None]) -> None:
    """Cut start_seconds..end_seconds out of a remote media file without downloading all of it.

    A clip that starts late is first tried with seeking (a few range requests). Rate-limited servers (Wikimedia)
    refuse the many requests seeking in some formats (Ogg) needs, so the fallback, and the only way for early clips,
    reads the file once from the beginning and stops at `end_seconds`."""
    target_file_path.parent.mkdir(parents=True, exist_ok=True)
    partial_file_path = target_file_path.with_name(f".{target_file_path.stem}.part{target_file_path.suffix}")
    clip_seconds = end_seconds - start_seconds
    seek_arguments = ["-ss", f"{start_seconds:.3f}", "-i", url, "-t", f"{clip_seconds:.3f}"]
    sequential_arguments = ["-seekable", "0", "-i", url, "-ss", f"{start_seconds:.3f}", "-t", f"{clip_seconds:.3f}"]
    attempts = (([seek_arguments] if start_seconds > SEEK_AFTER_SECONDS else [])
                + [sequential_arguments] * SEQUENTIAL_ATTEMPT_COUNT)
    stderr, sequential_try_count = "", 0
    for input_arguments in attempts:
        done = subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-user_agent", user_agent, *input_arguments,
                               *codec_arguments, str(partial_file_path)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=1800, check=False)
        if done.returncode == 0 and measure_media_duration_seconds(partial_file_path) > 0:
            os.replace(partial_file_path, target_file_path)
            os.chmod(target_file_path, 0o644)
            return
        partial_file_path.unlink(missing_ok=True)
        stderr = done.stderr
        if input_arguments is seek_arguments:
            continue
        sequential_try_count += 1
        if "429" not in stderr or sequential_try_count == SEQUENTIAL_ATTEMPT_COUNT:
            break
        report_progress(f"  rate limited by the server; retrying in {30 * sequential_try_count} s")
        time.sleep(30 * sequential_try_count)
    raise StudioError("could not cut the clip", stderr.strip()[-400:] or "ffmpeg wrote nothing",
                      "check --start and --end against the file's length, then run the command again")


def run_ffmpeg(arguments: list[str], what: str, timeout_seconds: float = 900) -> None:
    done = subprocess.run([find_ffmpeg(), "-v", "error", "-y", *arguments], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False)
    if done.returncode != 0:
        raise StudioError(f"could not {what}", done.stderr.strip()[-400:] or f"ffmpeg exit {done.returncode}",
                          "check the source and the times, then run the command again")


def parse_years(value: str | None) -> tuple[int, int] | None:
    """--years 1950,2020 (inclusive) or a single year."""
    if not value:
        return None
    try:
        years = [int(part) for part in value.split(",") if part.strip()]
    except ValueError:
        raise StudioError(f"{value!r} is not a year range", "use two years, for example 1950,2020",
                          "fix --years") from None
    if not years or len(years) > 2:
        raise StudioError(f"{value!r} is not a year range", "use two years, for example 1950,2020", "fix --years")
    return min(years), max(years)


def load_spec(path: Path, model):
    """A YAML or JSON spec file validated against `model`."""
    from ..file_io import convert_yaml_document_to_plain_data, read_json, read_yaml_document, validate_model

    if not path.is_file():
        raise StudioError(f"{path} not found", "the spec file does not exist", "write the spec, then run again")
    raw_spec = (read_json(path) if path.suffix.lower() == ".json"
                else convert_yaml_document_to_plain_data(read_yaml_document(path)))
    return validate_model(model, raw_spec, path)


def find_spec_input(value: str, spec_dir_path: Path, series: Series) -> Path:
    """A file a spec names: absolute, or relative to the spec's folder, or to production/."""
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [spec_dir_path / path, series.production_dir_path / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise StudioError(f"{value} not found",
                      f"looked in {' and '.join(str(candidate.parent) for candidate in candidates)}",
                      "fix the path in the spec (relative to the spec's folder or to production/)")
