"""Finding or starting a series' page server, and opening a page in the browser.

One server per series serves both pages. Its runtime info (port, token, pid, package version) lives in a folder only
the user can open (`user_dirs.get_page_server_dir_path()`), keyed by the series path, never in the series folder.
`plan open` and `video open` reuse a running server of the same package version, replace one of another version, and
otherwise start one fully detached from the command (a new session on Unix, a detached process on Windows), so the
command returns at once. A restarted server takes the previous port and token when it can, so a page left open keeps
working after a reload. `upgrade` replaces the servers an earlier version left running in the same way.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any

import httpx
from filelock import FileLock

from .. import __version__, user_dirs
from ..errors import StudioError
from ..paths import Series

START_TIMEOUT_SECONDS = 20


def ensure_runtime_dir() -> Path:
    runtime_dir_path = user_dirs.get_page_server_dir_path()
    runtime_dir_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return runtime_dir_path


def get_runtime_file_path(series: Series) -> Path:
    key = hashlib.sha256(str(series.root_dir_path.resolve()).encode("utf-8")).hexdigest()[:16]
    return ensure_runtime_dir() / f"{key}.json"


def read_runtime_info(runtime_file_path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(runtime_file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def build_base_url(runtime_info: dict[str, Any]) -> str:
    return f"http://127.0.0.1:{runtime_info['port']}/{runtime_info['token']}"


def fetch_health(runtime_info: dict[str, Any] | None) -> dict[str, Any] | None:
    """What a running server says about itself, or None when nothing answers."""
    if not runtime_info or not runtime_info.get("pid"):
        return None
    try:
        response = httpx.get(f"{build_base_url(runtime_info)}/health", timeout=2, trust_env=False)
        return response.json() if response.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None


def list_running_servers() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Every page server that answers, as its runtime info and what it says about itself (version, series)."""
    running_servers = []
    for runtime_file_path in sorted(ensure_runtime_dir().glob("*.json")):
        runtime_info = read_runtime_info(runtime_file_path)
        status = fetch_health(runtime_info)
        if runtime_info and status:
            running_servers.append((runtime_info, status))
    return running_servers


def stop_server(runtime_info: dict[str, Any]) -> None:
    """Ask a running server to stop, and wait up to 5 seconds for it to stop answering."""
    try:
        httpx.post(f"{build_base_url(runtime_info)}/shutdown", timeout=2, trust_env=False)
    except httpx.HTTPError:
        pass
    deadline = time.monotonic() + 5
    while fetch_health(runtime_info) and time.monotonic() < deadline:
        time.sleep(0.1)


def _start_server(series: Series, runtime_file_path: Path) -> dict[str, Any]:
    log_file_path = runtime_file_path.with_suffix(".log")
    command = [sys.executable, "-m", "explainer_studio.web.server", "--series", str(series.root_dir_path),
               "--runtime-file", str(runtime_file_path)]
    popen_options: dict[str, Any] = {"stdin": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        popen_options["creationflags"] = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                                          | subprocess.CREATE_NO_WINDOW)
    else:
        popen_options["start_new_session"] = True
    with log_file_path.open("ab") as log_handle:
        process = subprocess.Popen(command, stdout=log_handle, stderr=log_handle, **popen_options)
    deadline = time.monotonic() + START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        runtime_info = read_runtime_info(runtime_file_path)
        if runtime_info and runtime_info.get("pid") == process.pid and fetch_health(runtime_info):
            return runtime_info
        if process.poll() is not None:
            break
        time.sleep(0.1)
    raise StudioError("the page server did not start", f"see its log: {log_file_path}",
                      "run the command again; if it fails again, report the log with explainer-studio gap add "
                      "--kind tool")


def ensure_server(series: Series) -> dict[str, Any]:
    runtime_file_path = get_runtime_file_path(series)
    with FileLock(str(runtime_file_path) + ".lock", timeout=START_TIMEOUT_SECONDS + 10):
        runtime_info = read_runtime_info(runtime_file_path)
        status = fetch_health(runtime_info)
        if (status and status.get("explainer_studio_version") == __version__
                and status.get("series_path") == str(series.root_dir_path)):
            return runtime_info  # type: ignore[return-value]
        if status:  # another package version: replace it
            stop_server(runtime_info)  # type: ignore[arg-type]
        return _start_server(series, runtime_file_path)


def build_page_url(runtime_info: dict[str, Any], page_name: str, episode_id: str | None = None) -> str:
    base_url = build_base_url(runtime_info)
    return f"{base_url}/plan" if page_name == "plan" else f"{base_url}/video/{episode_id}"


def open_page(series: Series, page_name: str, episode_id: str | None = None, should_open_browser: bool = True) -> str:
    """Make sure the series' server runs, open `page_name` ("plan" or "video") in the browser and return its URL."""
    if page_name not in ("plan", "video") or (page_name == "video" and not episode_id):
        raise ValueError(f"unknown page {page_name!r}")
    url = build_page_url(ensure_server(series), page_name, episode_id)
    if should_open_browser:
        webbrowser.open(url)
    return url
