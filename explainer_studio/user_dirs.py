"""Per-user locations outside any series, and where the external programs are found.

`setup` installs programs it cannot expect on the system (ffmpeg, a user-level TeX, Blender) under the data
directory. Every subprocess that needs them gets `compute_tool_environment()`, whose PATH puts those folders first.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import platformdirs

APP_NAME = "explainer-studio"


def get_config_dir_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME, appauthor=False, roaming=True))


def get_data_dir_path() -> Path:
    return Path(platformdirs.user_data_dir(APP_NAME, appauthor=False))


def get_cache_dir_path() -> Path:
    return Path(platformdirs.user_cache_dir(APP_NAME, appauthor=False))


def get_credentials_file_path() -> Path:
    return get_config_dir_path() / "credentials.toml"


def get_settings_file_path() -> Path:
    """Settings for this computer's user, such as dev mode."""
    return get_config_dir_path() / "settings.toml"


def get_model_prices_file_path() -> Path:
    """The model price table dev mode works out dollars with (`model_prices`)."""
    return get_config_dir_path() / "model-prices.toml"


def get_page_server_dir_path() -> Path:
    """The running page servers' port, token, pid and log: per user, since they let a page change the series."""
    return get_cache_dir_path() / "pages"


# Files only the agent looks at (review prompts, thumbnail sheets) are kept this long, then removed.
SCRATCH_RETENTION_DAYS = 7


def ensure_scratch_dir(dir_name: str) -> Path:
    """A per-user folder for files only the agent reads; entries older than SCRATCH_RETENTION_DAYS are removed on
    each use."""
    scratch_dir_path = get_cache_dir_path() / dir_name
    scratch_dir_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    cutoff_time_seconds = time.time() - SCRATCH_RETENTION_DAYS * 24 * 3600
    for entry in scratch_dir_path.iterdir():
        try:
            if entry.lstat().st_mtime >= cutoff_time_seconds:
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        except OSError:
            pass  # in use or already gone: try again next time
    return scratch_dir_path


def get_geo_dir_path() -> Path:
    """Natural Earth map data (public domain), downloaded by `setup`."""
    return get_data_dir_path() / "geo"


def get_tinytex_dir_path() -> Path:
    """Where `setup` installs TinyTeX. TeX cannot work from a path with spaces or non-ASCII characters, which a
    Windows user name often puts in the data directory; TinyTeX's own installer falls back to ProgramData then."""
    data_dir_path = get_data_dir_path()
    if os.name == "nt" and (not str(data_dir_path).isascii() or " " in str(data_dir_path)):
        return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / APP_NAME / "TinyTeX"
    return data_dir_path / "TinyTeX"


def list_tool_dir_paths() -> list[Path]:
    """Folders with programs `setup` installed, searched before the system PATH."""
    data_dir_path = get_data_dir_path()
    candidates = [data_dir_path / "bin", data_dir_path / "ffmpeg", data_dir_path / "blender"]
    tinytex_bin_dir_path = get_tinytex_dir_path() / "bin"
    if tinytex_bin_dir_path.is_dir():
        candidates.extend(sorted(path for path in tinytex_bin_dir_path.iterdir() if path.is_dir()))
    return [path for path in candidates if path.is_dir()]


def compute_tool_environment(base_environment: dict[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ if base_environment is None else base_environment)
    tool_search_path = os.pathsep.join(str(path) for path in list_tool_dir_paths())
    if tool_search_path:
        environment["PATH"] = tool_search_path + os.pathsep + environment.get("PATH", "")
    return environment


def find_tool(name: str) -> str | None:
    """The full path of an external program, preferring the copies `setup` installed."""
    return shutil.which(name, path=compute_tool_environment()["PATH"])
