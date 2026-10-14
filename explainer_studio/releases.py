"""Releases: which one is the latest, and what an existing series needs after an upgrade.

A release is a tag `v<major>.<minor>.<patch>` of RELEASE_REPO on GitHub; the latest release is the highest such tag.
Tags are read with `git ls-remote`, which works without the GitHub API. `doctor` asks at most once a day (the answer
is cached); `upgrade` always asks.

UPGRADING.md says, per release, what to change in a series made with an earlier version. It ships in the package, so
an installed command reads the file of the version it is; a repository checkout run with `uv run` has none, and
prints no steps.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import user_dirs
from .errors import StudioError

RELEASE_REPO = "heptameta/heptabase-explainer-studio"
RELEASE_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
RELEASE_TAG_PATTERN = re.compile(r"refs/tags/v(\d+\.\d+\.\d+)$", re.MULTILINE)
LATEST_RELEASE_CHECK_INTERVAL_SECONDS = 24 * 60 * 60
LS_REMOTE_TIMEOUT_SECONDS = 20

# pyproject's force-include puts UPGRADING.md in the package. An earlier version's `upgrade` reads the new release's
# file here, with its own parser: keep the file at this path and its `## X.Y.Z` headings.
UPGRADING_FILE_PATH = Path(__file__).resolve().parent / "UPGRADING.md"
UPGRADING_SECTION_HEADING_PATTERN = re.compile(r"^## (\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class UpgradingSection:
    version: str
    text: str


def parse_release_version(version: str) -> tuple[int, int, int] | None:
    """(major, minor, patch) of a release version; None for anything else, such as a dev build's version."""
    match = RELEASE_VERSION_PATTERN.match(version)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def parse_latest_release_version(ls_remote_text: str) -> str | None:
    """The highest release version among the tags `git ls-remote --tags` printed; None when there is none."""
    versions = RELEASE_TAG_PATTERN.findall(ls_remote_text)
    return max(versions, key=parse_release_version) if versions else None


def fetch_latest_release_version() -> str:
    """The latest release on GitHub. Raises StudioError when it cannot be read (no network, no access)."""
    try:
        completed = subprocess.run(["git", "ls-remote", "--tags", "--refs", f"https://github.com/{RELEASE_REPO}.git",
                                    "v*"], capture_output=True, text=True, timeout=LS_REMOTE_TIMEOUT_SECONDS,
                                   env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise StudioError("cannot read the releases on GitHub", str(error), "check the network and try again") \
            from None
    latest_version = parse_latest_release_version(completed.stdout) if completed.returncode == 0 else None
    if latest_version is None:
        raise StudioError("cannot read the releases on GitHub", completed.stderr.strip()[-500:] or "no release tag",
                          "check the network and try again")
    return latest_version


def _get_latest_release_cache_file_path() -> Path:
    return user_dirs.get_cache_dir_path() / "latest-release.json"


def write_latest_release_cache(version: str) -> None:
    cache_file_path = _get_latest_release_cache_file_path()
    try:
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        cache_file_path.write_text(json.dumps({"version": version, "checked_at_seconds": time.time()}),
                                   encoding="utf-8")
    except OSError:
        pass  # only a cache: the next check asks GitHub again


def find_newer_release_version(current_version: str) -> str | None:
    """The latest release when it is newer than `current_version`, asking GitHub at most once a day; None when the
    current version is the latest, is a dev build, or GitHub cannot be reached."""
    current_release = parse_release_version(current_version)
    if current_release is None:
        return None
    latest_version = None
    try:
        cache = json.loads(_get_latest_release_cache_file_path().read_text(encoding="utf-8"))
        if time.time() - float(cache["checked_at_seconds"]) < LATEST_RELEASE_CHECK_INTERVAL_SECONDS:
            latest_version = str(cache["version"])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if latest_version is None:
        try:
            latest_version = fetch_latest_release_version()
        except StudioError:
            return None
        write_latest_release_cache(latest_version)
    latest_release = parse_release_version(latest_version)
    return latest_version if latest_release is not None and latest_release > current_release else None


def read_upgrading_sections(after_version: str, up_to_version: str) -> list[UpgradingSection]:
    """The UPGRADING.md sections of the releases after `after_version` up to and including `up_to_version`, oldest
    first. Empty when either is not a release version (a dev build), or when no release between them has a section."""
    after_release, up_to_release = parse_release_version(after_version), parse_release_version(up_to_version)
    if after_release is None or up_to_release is None or not UPGRADING_FILE_PATH.is_file():
        return []
    text = UPGRADING_FILE_PATH.read_text(encoding="utf-8")
    headings = list(UPGRADING_SECTION_HEADING_PATTERN.finditer(text))
    sections = []
    for index, heading in enumerate(headings):
        release = parse_release_version(heading[1])
        if release is None or not after_release < release <= up_to_release:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections.append(UpgradingSection(heading[1], text[heading.end():end].strip()))
    return sorted(sections, key=lambda section: parse_release_version(section.version))


def format_upgrading_sections(sections: list[UpgradingSection]) -> str:
    """What to tell the agent about the UPGRADING.md sections: the changes some existing series need."""
    introduction = ("Series made with an earlier version may need these changes (UPGRADING.md). Each step says how to "
                    "tell whether a series needs it; apply them to every series you work on:")
    return "\n".join([introduction, *(f"\n{section.version}\n{section.text}" for section in sections)])
