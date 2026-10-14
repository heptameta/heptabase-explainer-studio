"""`upgrade`."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

from ..errors import StudioError
from .common import print_progress, print_result

# The Python the skill's install scripts install the command with. They are in the Heptabase plugin
# (heptameta/heptabase-agent-plugins): change both together.
PYTHON_VERSION = "3.13"


def find_uv() -> str:
    """uv, where the install scripts put it when it is not on PATH. Raises StudioError when it is missing."""
    home_dir_path = Path.home()
    candidates = [shutil.which("uv"), str(home_dir_path / ".local" / "bin" / "uv"),
                  str(home_dir_path / ".cargo" / "bin" / "uv")]
    uv_path = next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)
    if uv_path is None:
        raise StudioError("uv is missing", "the command is installed and upgraded as a uv tool",
                          "run the skill's install script (scripts/install.sh), which installs uv and the latest "
                          "release")
    return uv_path


def run_uv(uv_path: str, *arguments: str) -> str:
    """uv's stdout; its messages go to stderr as progress. Raises StudioError when it fails."""
    completed = subprocess.run([uv_path, *arguments], stdout=subprocess.PIPE, stderr=sys.stderr, text=True,
                               check=False)
    if completed.returncode != 0:
        raise StudioError(f"`uv {' '.join(arguments)}` failed", "see uv's messages above",
                          "fix the problem and run `explainer-studio upgrade` again")
    return completed.stdout


def replace_page_servers(studio_file_path: Path, version: str) -> None:
    """Replace the page servers an earlier version left running with `version`'s, through its `plan open`, so a page
    left open keeps working after a reload instead of running the earlier code against files the new version writes.
    A server whose series the new version cannot open (its plan no longer validates) is stopped."""
    from ..web.launcher import list_running_servers, stop_server

    for runtime_info, status in list_running_servers():
        if status.get("explainer_studio_version") == version:
            continue
        series_path = str(status.get("series_path"))
        completed = subprocess.run([str(studio_file_path), "plan", "open", "--no-browser", "--series", series_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if completed.returncode == 0:
            print_progress(f"restarted the page server of {series_path} with {version}")
        else:
            stop_server(runtime_info)
            print_progress(f"stopped the page server of {series_path}: {version} cannot open its plan yet "
                           "(`plan open` starts it again once the plan validates)")


@click.command()
def upgrade() -> None:
    """Install the latest release when it is newer than this version, then install what it needs (`setup`).
    Does nothing on a dev build. Prints what series made with this version may need to change."""
    from .. import __version__
    from ..releases import (
        RELEASE_REPO,
        fetch_latest_release_version,
        format_upgrading_sections,
        parse_release_version,
        read_upgrading_sections,
        write_latest_release_cache,
    )

    current_release = parse_release_version(__version__)
    if current_release is None:
        print_result(f"explainer-studio {__version__} is a dev build: not upgraded (scripts/use_release.py in the "
                     "repository switches back to the release)")
        return
    latest_version = fetch_latest_release_version()
    write_latest_release_cache(latest_version)
    if parse_release_version(latest_version) <= current_release:
        print_result(f"explainer-studio {__version__} is the latest release")
        return
    if os.name == "nt":
        raise StudioError(f"explainer-studio {latest_version} is out, but a running command cannot replace itself on "
                          "Windows", "Windows locks the files of a running program",
                          "run the skill's install script (scripts/install.ps1): it installs the latest release")
    uv_path = find_uv()
    print_progress(f"installing explainer-studio {latest_version}")
    run_uv(uv_path, "tool", "install", "--python", PYTHON_VERSION, "--force",
           f"explainer-studio @ git+https://github.com/{RELEASE_REPO}@v{latest_version}")
    # this process still runs the earlier version's code: the new version's command installs what it needs, and below
    # the earlier code reads the new UPGRADING.md (releases.UPGRADING_FILE_PATH says what that freezes)
    studio_file_path = Path(run_uv(uv_path, "tool", "dir", "--bin").strip()) / "explainer-studio"
    print_progress(f"explainer-studio setup ({latest_version})")
    if subprocess.run([str(studio_file_path), "setup"], stdout=sys.stderr, check=False).returncode != 0:
        raise StudioError(f"upgraded to {latest_version}, but setup did not finish", "see setup's messages above",
                          f"fix the problems, then run: {studio_file_path} setup")
    replace_page_servers(studio_file_path, latest_version)
    print_result(f"upgraded explainer-studio {__version__} -> {latest_version}")
    sections = read_upgrading_sections(__version__, latest_version)
    if sections:
        print_result(format_upgrading_sections(sections))
    print_result("Run `explainer-studio guide` again before your next step: it changed with this version.")
