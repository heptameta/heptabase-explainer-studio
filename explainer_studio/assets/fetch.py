"""HTTP for the asset commands and `setup`: one descriptive User-Agent (Wikimedia requires one), retries that honour
rate limits, and streaming downloads that land atomically."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from .. import __version__
from ..errors import StudioError
from ..releases import RELEASE_REPO

USER_AGENT = (f"explainer-studio/{__version__} (https://github.com/{RELEASE_REPO}; teaching-video tool) "
              f"httpx/{httpx.__version__}")
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
ATTEMPT_COUNT = 6
MAX_WAIT_SECONDS = 60
REPORT_ABOVE_BYTES = 20_000_000  # smaller downloads finish too fast to need progress


class _TransientStatusError(Exception):
    def __init__(self, why: str, wait_seconds: float):
        super().__init__(why)
        self.why = why
        self.wait_seconds = wait_seconds


def create_client(timeout_seconds: float = 60) -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=timeout_seconds)


def parse_host(url: str) -> str:
    return urlparse(url).netloc or url


def _compute_backoff_seconds(attempt: int) -> float:
    return min(MAX_WAIT_SECONDS, 2.0 * 2 ** attempt)


def _resolve_wait_seconds(response: httpx.Response, attempt: int) -> float:
    """How long a rate-limited or failing server asks us to wait (Wikimedia sends x-ratelimit-reset)."""
    for header in ("retry-after", "x-ratelimit-reset"):
        try:
            return min(MAX_WAIT_SECONDS, max(1.0, float(response.headers[header])))
        except (KeyError, ValueError):
            continue
    return _compute_backoff_seconds(attempt)


def _run_with_retries(url: str, attempt_once: Callable[[], Any], report_progress: Callable[[str], None] | None) -> Any:
    for attempt in range(ATTEMPT_COUNT):
        try:
            return attempt_once()
        except httpx.TransportError as error:
            why, wait_seconds = type(error).__name__, _compute_backoff_seconds(attempt)
        except _TransientStatusError as retry_error:
            why, wait_seconds = retry_error.why, retry_error.wait_seconds
        if attempt == ATTEMPT_COUNT - 1:
            raise StudioError(f"could not reach {parse_host(url)}", why,
                              "check the network connection and run the command again in a minute")
        if report_progress:
            report_progress(f"  {parse_host(url)}: {why}; retrying in {wait_seconds:.0f} s")
        time.sleep(wait_seconds)
    raise AssertionError("unreachable")


def _raise_for_status(response: httpx.Response, url: str, attempt: int) -> None:
    if response.status_code < 400:
        return
    if response.status_code in TRANSIENT_STATUS_CODES:
        raise _TransientStatusError(f"HTTP {response.status_code}", _resolve_wait_seconds(response, attempt))
    response.read()
    raise StudioError(f"{parse_host(url)} answered HTTP {response.status_code}",
                      response.text.strip()[:300] or response.reason_phrase,
                      "check the name or code you asked for, then run the command again")


def fetch_response(url: str, params: dict[str, Any] | None = None, timeout_seconds: float = 60,
                   report_progress: Callable[[str], None] | None = None) -> httpx.Response:
    """A GET that retries network errors and transient statuses, and raises StudioError for any other failure."""
    attempts = iter(range(ATTEMPT_COUNT))

    def fetch_once() -> httpx.Response:
        with create_client(timeout_seconds) as http:
            response = http.get(url, params=params)
        _raise_for_status(response, url, next(attempts))
        return response

    return _run_with_retries(url, fetch_once, report_progress)


def fetch_json(url: str, params: dict[str, Any] | None = None, timeout_seconds: float = 60) -> Any:
    response = fetch_response(url, params, timeout_seconds)
    try:
        return response.json()
    except ValueError:
        raise StudioError(f"{parse_host(url)} did not return JSON", response.text.strip()[:200],
                          "run the command again later") from None


def download(url: str, target_file_path: Path, report_progress: Callable[[str], None] | None = None,
             label: str | None = None, timeout_seconds: float = 120) -> Path:
    """Stream `url` to `target_file_path` with progress; a dropped or rate-limited download starts again."""
    target_file_path.parent.mkdir(parents=True, exist_ok=True)
    partial_file_path = target_file_path.with_name(target_file_path.name + ".part")
    label = label or target_file_path.name
    attempts = iter(range(ATTEMPT_COUNT))

    def download_once() -> Path:
        try:
            with create_client(timeout_seconds) as http, http.stream("GET", url) as response:
                _raise_for_status(response, url, next(attempts))
                # content-length counts the bytes on the wire, which a compressed response decompresses past
                total_bytes = int(response.headers.get("content-length") or 0)
                next_report_fraction = 0.1
                with partial_file_path.open("wb") as handle:
                    for chunk in response.iter_bytes(1 << 20):
                        handle.write(chunk)
                        done_fraction = response.num_bytes_downloaded / total_bytes if total_bytes else 0
                        if (report_progress and total_bytes > REPORT_ABOVE_BYTES
                                and done_fraction >= next_report_fraction):
                            report_progress(f"  {label}: {done_fraction:.0%} of {total_bytes / 1e6:.0f} MB")
                            next_report_fraction = done_fraction + 0.1
        except BaseException:
            partial_file_path.unlink(missing_ok=True)
            raise
        os.replace(partial_file_path, target_file_path)
        return target_file_path

    return _run_with_retries(url, download_once, report_progress)
