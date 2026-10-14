"""Use a dev build on this computer: Explainer Studio made from a commit that is not released, for developing and
testing it without publishing.

    uv run python scripts/use_dev_build.py                    # the current commit; refuses uncommitted changes
    uv run python scripts/use_dev_build.py --ref <branch or tag>

The dev build's version names its commit (0.1.1.dev13+g9b0e2d4: see
explainer_studio_versions.convert_git_description_to_dev_build_version), so every video records which build made it. The
script exports the commit with `git archive`, writes the version into the same files release.py does, makes the skill's
install scripts install this snapshot and its marketplace read the plugin from it (never the release on GitHub), and
replaces `<user data folder>/dev-build/` with it in one step, so no chat reads half-written files. That folder is the
source tree of the commit, so it is also a local Claude Code marketplace with the release's name. Then the CLI is
installed from it (not editable: it stays as built), Claude Code's marketplace is pointed at it and the plugin updated,
and any other enabled plugin named explainer-studio (for example a copy from another marketplace) is disabled.

A computer uses one version at a time: new chats use the dev build, and running chats are told to print the guide again
at their next command on an episode. `scripts/use_release.py` switches back.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from filelock import FileLock, Timeout
from installation import (
    MARKETPLACE_NAME,
    PLUGIN_ID,
    REPOSITORY_DIR_PATH,
    disable_other_plugins,
    find_claude,
    find_installed_plugin_version,
    find_marketplace,
    install_cli,
    install_plugin,
    print_progress,
    run,
    run_claude_action,
    update_plugin,
)
from release import (
    generate_install_scripts,
    generate_marketplace_file,
    generate_versioned_files,
)

from explainer_studio.errors import StudioError
from explainer_studio.explainer_studio_versions import convert_git_description_to_dev_build_version
from explainer_studio.user_dirs import get_data_dir_path


def run_git(*arguments: str) -> str:
    return run(["git", "-C", str(REPOSITORY_DIR_PATH), *arguments]).strip()


def find_commit_and_version(ref: str | None) -> tuple[str, str]:
    """The full commit id of `ref` (default: the current commit) and its dev build version."""
    if ref is None and run_git("status", "--porcelain", "--untracked-files=no"):
        raise StudioError("tracked files have uncommitted changes",
                          "a dev build's version names a commit, and these changes are in none",
                          "commit them first, or pass --ref <branch or tag> to build a commit as it is")
    try:
        commit_id = run_git("rev-parse", "--verify", f"{ref or 'HEAD'}^{{commit}}")
    except StudioError:
        raise StudioError(f"no commit named {ref!r}", "git cannot find that branch, tag or commit",
                          "pass a branch, tag or commit of this repository") from None
    try:
        git_description = run_git("describe", "--tags", "--match", "v[0-9]*", "--long", "--abbrev=7", commit_id)
    except StudioError:
        raise StudioError(f"no release tag comes before {commit_id[:7]}",
                          "a dev build's version counts the commits since the last release tag (v<version>), so the "
                          "same commit has the same version on every computer",
                          "fetch the tags (git fetch --tags) and run this again; a commit from before the first "
                          "release cannot be a dev build") from None
    return commit_id, convert_git_description_to_dev_build_version(git_description)


def write_snapshot(commit_id: str, version: str, dev_build_dir_path: Path) -> None:
    """Export `commit_id` with its version written in, then put it at `dev_build_dir_path` in place of the previous dev
    build."""
    archive_bytes = run_bytes(["git", "-C", str(REPOSITORY_DIR_PATH), "archive", "--format=tar", commit_id])
    staging_dir_path = Path(tempfile.mkdtemp(prefix=".dev-build-new-", dir=dev_build_dir_path.parent))
    previous_dir_path = dev_build_dir_path.parent / f"{staging_dir_path.name.replace('-new-', '-old-')}"
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as tar:
            tar.extractall(staging_dir_path, filter="data")
        for generator in (lambda: generate_versioned_files(staging_dir_path, version),
                          lambda: generate_install_scripts(staging_dir_path, dev_build_dir_path),
                          lambda: generate_marketplace_file(staging_dir_path, None)):
            for path, text in generator().items():
                path.write_text(text, encoding="utf-8")
        # two renames: a chat reading the dev build sees the old folder or the new one, never a mix
        if dev_build_dir_path.exists():
            os.replace(dev_build_dir_path, previous_dir_path)
        try:
            os.replace(staging_dir_path, dev_build_dir_path)
        except BaseException:
            if previous_dir_path.exists() and not dev_build_dir_path.exists():
                os.replace(previous_dir_path, dev_build_dir_path)
            raise
    finally:
        shutil.rmtree(staging_dir_path, ignore_errors=True)
        shutil.rmtree(previous_dir_path, ignore_errors=True)


def run_bytes(command: list[str]) -> bytes:
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        raise StudioError(f"`{' '.join(command)}` failed", completed.stderr.decode(errors="replace").strip()[-2000:])
    return completed.stdout


def use_in_claude_code(claude_path: str, dev_build_dir_path: Path, version: str) -> list[str]:
    """Point the marketplace at the dev build folder, install and update the plugin, disable other plugins named
    explainer-studio. Returns what changed, for the summary."""
    lines = []
    current_marketplace = find_marketplace(claude_path)
    is_dev_build_marketplace = (current_marketplace is not None and current_marketplace.get("source") == "directory"
                                and current_marketplace.get("path")
                                and Path(current_marketplace["path"]).resolve() == dev_build_dir_path.resolve())
    if not is_dev_build_marketplace:
        # Claude Code re-points a marketplace of the same name (from GitHub or another folder); its plugins stay
        run_claude_action(claude_path, "plugin", "marketplace", "add", str(dev_build_dir_path))
        previous_source = (None if current_marketplace is None else current_marketplace.get("repo")
                           or current_marketplace.get("path") or current_marketplace)
        previous_source_note = "" if previous_source is None else f" instead of {previous_source}"
        lines.append(f"marketplace {MARKETPLACE_NAME} now reads {dev_build_dir_path}{previous_source_note}")
    install_plugin(claude_path)
    lines += update_plugin(claude_path)
    installed_version = find_installed_plugin_version(claude_path)
    if installed_version != version:
        raise StudioError(f"Claude Code lists {PLUGIN_ID} {installed_version}, not {version}",
                          "the plugin update did not pick up the dev build",
                          f"run `claude plugin update {PLUGIN_ID} --scope user` to see why")
    return lines + disable_other_plugins(claude_path)


def use_dev_build(ref: str | None) -> None:
    commit_id, version = find_commit_and_version(ref)
    dev_build_dir_path = get_data_dir_path() / "dev-build"
    dev_build_dir_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(dev_build_dir_path) + ".lock", timeout=0)
    try:
        lock.acquire()
    except Timeout:
        raise StudioError("another use_dev_build.py is running", f"it holds {lock.lock_file}",
                          "wait for it to finish, then run this again if you still need to") from None
    with lock:
        for leftover_dir_path in dev_build_dir_path.parent.glob(".dev-build-*"):  # from a run that was killed
            shutil.rmtree(leftover_dir_path, ignore_errors=True)
        print_progress(f"dev build {version}: exporting {commit_id[:7]} to {dev_build_dir_path}")
        write_snapshot(commit_id, version, dev_build_dir_path)
        studio_file_path = install_cli(f"explainer-studio @ {dev_build_dir_path.as_uri()}", version,
                                       should_reinstall=True)
        claude_path = find_claude()
        lines = [f"CLI: {studio_file_path}"]
        if claude_path is None:
            lines.append("claude is not on PATH, so Claude Code's plugin is unchanged. Run this again where `claude` "
                         "works, or point the marketplace yourself: claude plugin marketplace add "
                         f"\"{dev_build_dir_path}\"")
        else:
            lines += use_in_claude_code(claude_path, dev_build_dir_path, version)
            lines.append(f"plugin: {PLUGIN_ID} {version}, read from {dev_build_dir_path / 'plugin'}")
    ref_note = f", {ref}" if ref and not commit_id.startswith(ref) else ""
    print(f"Using dev build {version} ({commit_id[:7]}{ref_note})")
    for line in lines:
        print(f"  {line}")
    print("New chats use it. Running chats are told at their next command on an episode to print the guide again.")
    print("Switch back to the release with: uv run python scripts/use_release.py")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", help="the branch, tag or commit to build (default: the current commit, which must "
                                      "have no uncommitted changes)")
    arguments = parser.parse_args()
    try:
        use_dev_build(arguments.ref)
    except StudioError as error:
        print(error.format(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
