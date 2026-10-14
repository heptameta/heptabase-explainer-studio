"""What use_dev_build.py and use_release.py change on this computer: the `explainer-studio` command (through uv) and
the Claude Code plugins that carry the skill (through `claude plugin`).

Users get the skill from the Heptabase plugin (`heptabase`, from heptameta/heptabase-agent-plugins or a plugin
directory). A dev build's skill is the plugin `explainer-studio@heptabase-explainer-studio`, whose marketplace is the
local dev build folder. Two skills of the same name in one chat contradict each other, and Claude Code turns plugins on
and off only as a whole, so a dev build disables the Heptabase plugin (its MCP tools too) and the release enables it
again. Claude Code's state is read from its `--json` output, never from its files.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY_DIR_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY_DIR_PATH))

from explainer_studio.errors import StudioError

MARKETPLACE_NAME = "heptabase-explainer-studio"
PLUGIN_NAME = "explainer-studio"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
HEPTABASE_PLUGIN_NAME = "heptabase"  # carries the released skill
HEPTABASE_MARKETPLACE_NAME = "heptabase-agent-plugins"
HEPTABASE_MARKETPLACE_REPO = "heptameta/heptabase-agent-plugins"
PYTHON_VERSION = "3.13"  # the Python the skill's install scripts install the CLI with


def print_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _build_environment() -> dict[str, str]:
    """The environment for uv and claude: without the repository's virtual environment that `uv run` activated."""
    return {name: value for name, value in os.environ.items() if name not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}


def run(command: list[str], cwd: Path | None = None) -> str:
    """A command's stdout; a failure raises with its output."""
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=_build_environment(), check=False)
    if completed.returncode != 0:
        output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        raise StudioError(f"`{' '.join(command)}` failed (exit {completed.returncode})", output[-2000:])
    return completed.stdout


# The CLI ------------------------------------------------------------------------------------------------------------
def install_cli(requirement: str, version: str, should_reinstall: bool) -> Path:
    """Install the CLI from `requirement` for this user and check that the installed command reports `version`.
    `should_reinstall` rebuilds it even when uv has a build of the same source cached (a local folder keeps its
    path)."""
    uv_path = os.environ.get("UV") or shutil.which("uv")
    if uv_path is None:
        raise StudioError("uv is not on PATH", "the CLI is installed as a uv tool", "install uv (astral.sh/uv)")
    print_progress(f"installing the CLI: uv tool install {requirement}")
    command = [uv_path, "tool", "install", "--python", PYTHON_VERSION, "--force"]
    if should_reinstall:
        command += ["--reinstall-package", PLUGIN_NAME]
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


# Claude Code --------------------------------------------------------------------------------------------------------
def find_claude() -> str | None:
    return shutil.which("claude")


def run_claude_list(claude_path: str, *arguments: str) -> list[dict[str, Any]]:
    """The JSON list a `claude ... list --json` command prints."""
    return json.loads(run([claude_path, *arguments, "--json"]))


def run_claude_action(claude_path: str, *arguments: str, cwd: Path | None = None) -> dict[str, Any]:
    """Run a `claude plugin` action; its --json result is the last line of stdout. The marketplace actions (add,
    remove, update) take no --json in Claude Code 2.1.286 and refuse the option; nothing reads their result."""
    if arguments[:2] == ("plugin", "marketplace"):
        run([claude_path, *arguments], cwd)
        return {}
    lines = run([claude_path, *arguments, "--json"], cwd).strip().splitlines()
    return json.loads(lines[-1]) if lines else {}


def find_marketplace(claude_path: str, name: str = MARKETPLACE_NAME) -> dict[str, Any] | None:
    return next((marketplace for marketplace in run_claude_list(claude_path, "plugin", "marketplace", "list")
                 if marketplace.get("name") == name), None)


def list_plugin_installs(claude_path: str) -> list[dict[str, Any]]:
    return run_claude_list(claude_path, "plugin", "list")


def resolve_install_cwd(install: dict[str, Any]) -> Path | None:
    """Where a `claude plugin` command about this install runs: its project for a project or local scope install."""
    return Path(install["projectPath"]) if install.get("scope") in ("project", "local") and install.get("projectPath") \
        else None


def find_user_install(claude_path: str) -> dict[str, Any] | None:
    return next((install for install in list_plugin_installs(claude_path)
                 if install.get("id") == PLUGIN_ID and install.get("scope") == "user"), None)


def install_plugin(claude_path: str) -> None:
    """Install the plugin at user scope unless it already is."""
    if find_user_install(claude_path) is None:
        run_claude_action(claude_path, "plugin", "install", PLUGIN_ID, "--scope", "user")


def update_plugin(claude_path: str) -> list[str]:
    """Update every install of the plugin (user scope, and project or local scope in their projects) to its
    marketplace's version: a computer uses one version. Returns notes about installs left as they were."""
    notes = []
    for install in list_plugin_installs(claude_path):
        if install.get("id") != PLUGIN_ID:
            continue
        cwd = resolve_install_cwd(install)
        if install.get("scope") in ("project", "local") and (cwd is None or not cwd.is_dir()):
            notes.append(f"left the {install.get('scope')} scope install for {cwd or 'an unknown project'} at "
                         f"{install.get('version')}: the project folder is gone")
            continue
        run_claude_action(claude_path, "plugin", "update", PLUGIN_ID, "--scope", str(install.get("scope")), cwd=cwd)
    return notes


def read_plugin_name(install: dict[str, Any]) -> str:
    return str(install.get("id")).partition("@")[0]


def disable_plugins(claude_path: str, plugin_names: set[str]) -> list[str]:
    """Disable every enabled plugin named in `plugin_names` other than this repository's dev build plugin: each carries an
    explainer-studio skill. Returns what changed, for the summary."""
    lines = []
    for install in list_plugin_installs(claude_path):
        if read_plugin_name(install) not in plugin_names or install.get("id") == PLUGIN_ID or not install.get("enabled"):
            continue
        scope, cwd = str(install.get("scope")), resolve_install_cwd(install)
        if cwd is not None and not cwd.is_dir():
            continue
        run_claude_action(claude_path, "plugin", "disable", install["id"], "--scope", scope, cwd=cwd)
        lines.append(f"disabled {install['id']} ({scope} scope" + (f", in {cwd}" if cwd else "") + ")")
    return lines


def use_heptabase_plugin(claude_path: str) -> list[str]:
    """Bring every install of the Heptabase plugin up to its marketplace's version and enable it, one a dev build
    disabled or not; without an install, install it at user scope from its GitHub marketplace. Returns what changed."""
    installs = [install for install in list_plugin_installs(claude_path)
                if read_plugin_name(install) == HEPTABASE_PLUGIN_NAME]
    if not installs:
        if find_marketplace(claude_path, HEPTABASE_MARKETPLACE_NAME) is None:
            run_claude_action(claude_path, "plugin", "marketplace", "add", HEPTABASE_MARKETPLACE_REPO)
        plugin_id = f"{HEPTABASE_PLUGIN_NAME}@{HEPTABASE_MARKETPLACE_NAME}"
        run_claude_action(claude_path, "plugin", "install", plugin_id, "--scope", "user")
        return [f"installed {plugin_id} (user scope)"]
    for marketplace_name in sorted({str(install.get("id")).partition("@")[2] for install in installs}):
        run_claude_action(claude_path, "plugin", "marketplace", "update", marketplace_name)
    lines = []
    for install in installs:
        scope, cwd = str(install.get("scope")), resolve_install_cwd(install)
        if cwd is not None and not cwd.is_dir():
            continue
        run_claude_action(claude_path, "plugin", "update", install["id"], "--scope", scope, cwd=cwd)
        if not install.get("enabled"):
            run_claude_action(claude_path, "plugin", "enable", install["id"], "--scope", scope, cwd=cwd)
            lines.append(f"enabled {install['id']} ({scope} scope" + (f", in {cwd}" if cwd else "") + ")")
    return lines


def find_installed_plugin_version(claude_path: str) -> str:
    install = find_user_install(claude_path)
    if install is None:
        raise StudioError(f"{PLUGIN_ID} is not installed at user scope", "Claude Code did not install it",
                          f"run `claude plugin install {PLUGIN_ID} --scope user` to see why")
    return str(install.get("version"))
