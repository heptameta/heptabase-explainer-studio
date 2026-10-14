"""What use_dev_build.py and use_release.py change on this computer: the `explainer-studio` command, installed as a uv
tool. The skill that runs it comes from the Heptabase plugin and is the same for both."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_DIR_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY_DIR_PATH))

from explainer_studio.cli.upgrade import PYTHON_VERSION
from explainer_studio.errors import StudioError

PACKAGE_NAME = "explainer-studio"


def print_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _build_environment() -> dict[str, str]:
    """The environment for uv: without the repository's virtual environment that `uv run` activated."""
    return {name: value for name, value in os.environ.items() if name not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}


def run(command: list[str], cwd: Path | None = None) -> str:
    """A command's stdout; a failure raises with its output."""
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=_build_environment(), check=False)
    if completed.returncode != 0:
        output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        raise StudioError(f"`{' '.join(command)}` failed (exit {completed.returncode})", output[-2000:])
    return completed.stdout


def install_cli(requirement: str, version: str, should_reinstall: bool) -> Path:
    """Install the CLI from `requirement` for this user and check that the installed command reports `version`.
    `should_reinstall` rebuilds it even when uv has a build of the same source cached."""
    uv_path = os.environ.get("UV") or shutil.which("uv")
    if uv_path is None:
        raise StudioError("uv is not on PATH", "the CLI is installed as a uv tool", "install uv (astral.sh/uv)")
    print_progress(f"installing the CLI: uv tool install {requirement}")
    command = [uv_path, "tool", "install", "--python", PYTHON_VERSION, "--force"]
    if should_reinstall:
        command += ["--reinstall-package", PACKAGE_NAME]
    completed = subprocess.run([*command, requirement], env=_build_environment(), stdout=sys.stderr, check=False)
    if completed.returncode != 0:
        raise StudioError("uv could not install the CLI", "see uv's messages above",
                          "fix the problem and run this script again")
    studio_file_name = "explainer-studio.exe" if os.name == "nt" else "explainer-studio"
    studio_file_path = Path(run([uv_path, "tool", "dir", "--bin"]).strip()) / studio_file_name
    reported_version = run([str(studio_file_path), "--version"]).strip()
    if reported_version != f"explainer-studio {version}":
        raise StudioError(f"the installed CLI reports {reported_version!r}, not explainer-studio {version}",
                          f"{studio_file_path} is not the command uv just installed, or uv reused an earlier build",
                          "run this script again; if it repeats, run `uv tool uninstall explainer-studio` first")
    return studio_file_path
