"""Narration API keys.

A key is read from the provider's environment variable first (CI and other hosts set it there), then from credentials.toml in
the user config directory, which only `setup narration` writes, with mode 0600. Key values are never printed, logged or
copied anywhere else; callers only learn whether a key exists and where it came from.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

from . import user_dirs
from .errors import StudioError
from .file_io import hold_lock, write_text_atomic
from .narration_providers import PROVIDER_BY_NAME_MAP, NarrationProviderName


@dataclass(frozen=True)
class ApiKey:
    value: str
    source: str  # "environment variable OPENAI_API_KEY" or the credentials file path

    def __repr__(self) -> str:  # never show the value in a traceback or debugger
        return f"ApiKey(source={self.source!r})"


def _read_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise StudioError(f"{path.name} is not valid TOML", str(error), f"fix or delete {path}, then run "
                          "`explainer-studio setup narration` in your own terminal") from None


def find_api_key(provider_name: NarrationProviderName) -> ApiKey | None:
    env_variable_name = PROVIDER_BY_NAME_MAP[provider_name].api_key_env
    if env_variable_name is None:
        return None
    value = os.environ.get(env_variable_name, "").strip()
    if value:
        return ApiKey(value, f"environment variable {env_variable_name}")
    path = user_dirs.get_credentials_file_path()
    table = _read_file(path).get(provider_name)
    value = table.get("api_key", "") if isinstance(table, dict) else ""
    if isinstance(value, str) and value.strip():
        return ApiKey(value.strip(), str(path))
    return None


def write_api_key(provider_name: NarrationProviderName, value: str) -> Path:
    """Store a key in credentials.toml (mode 0600), keeping the other providers' keys."""
    path = user_dirs.get_credentials_file_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with hold_lock(path):
        credentials_by_provider_name_map = _read_file(path)
        credentials_by_provider_name_map[provider_name] = {"api_key": value}
        write_text_atomic(path, tomli_w.dumps(credentials_by_provider_name_map), is_private=True)
    return path
