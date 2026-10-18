"""Narration API keys, and credentials.toml, the user's secrets on this computer.

A key is read from the provider's environment variable first (CI and other hosts set it there), then from credentials.toml in
the user config directory, which `setup narration` and the Heptabase sign-in write, with mode 0600. Key values are never
printed, logged or copied anywhere else; callers only learn whether a key exists and where it came from.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomli_w

from . import user_dirs
from .errors import StudioError
from .file_io import hold_lock, write_text_atomic
from .narration_providers import PROVIDER_BY_NAME_MAP, NarrationProviderName

SETUP_NARRATION_STEP = ", then run `explainer-studio setup narration` in your own terminal"


@dataclass(frozen=True)
class ApiKey:
    value: str
    source: str  # "environment variable OPENAI_API_KEY" or the credentials file path

    def __repr__(self) -> str:  # never show the value in a traceback or debugger
        return f"ApiKey(source={self.source!r})"


def read_credentials(next_step_after_fix: str = "") -> dict[str, Any]:
    """credentials.toml's tables, {} when there is none. When it is not valid TOML, the error says to fix or delete it,
    then `next_step_after_fix`."""
    path = user_dirs.get_credentials_file_path()
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise StudioError(f"{path.name} is not valid TOML", str(error),
                          f"fix or delete {path}{next_step_after_fix}") from None


@contextmanager
def hold_credentials_lock() -> Iterator[None]:
    """Hold credentials.toml's lock for a read-modify-write, its directory made private (mode 0700) first."""
    path = user_dirs.get_credentials_file_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with hold_lock(path):
        yield


def write_credentials(credentials: dict[str, Any]) -> None:
    """Replace credentials.toml (mode 0600). The caller holds `hold_credentials_lock` and read it inside the lock."""
    write_text_atomic(user_dirs.get_credentials_file_path(), tomli_w.dumps(credentials), is_private=True)


def find_api_key(provider_name: NarrationProviderName) -> ApiKey | None:
    env_variable_name = PROVIDER_BY_NAME_MAP[provider_name].api_key_env
    if env_variable_name is None:
        return None
    value = os.environ.get(env_variable_name, "").strip()
    if value:
        return ApiKey(value, f"environment variable {env_variable_name}")
    table = read_credentials(SETUP_NARRATION_STEP).get(provider_name)
    value = table.get("api_key", "") if isinstance(table, dict) else ""
    if isinstance(value, str) and value.strip():
        return ApiKey(value.strip(), str(user_dirs.get_credentials_file_path()))
    return None


def write_api_key(provider_name: NarrationProviderName, value: str) -> Path:
    """Store a key in credentials.toml (mode 0600), keeping the other providers' keys."""
    with hold_credentials_lock():
        credentials = read_credentials(SETUP_NARRATION_STEP)
        credentials[provider_name] = {"api_key": value}
        write_credentials(credentials)
    return user_dirs.get_credentials_file_path()
