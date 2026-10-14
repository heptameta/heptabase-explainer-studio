"""Use a dev build on this computer: the `explainer-studio` command made from a commit that is not released, for
developing and testing it without publishing.

    uv run python scripts/use_dev_build.py                    # the current commit; refuses uncommitted changes
    uv run python scripts/use_dev_build.py --ref <branch or tag>

The dev build's version names its commit (0.1.1.dev13+g9b0e2d4: see
explainer_studio_versions.convert_git_description_to_dev_build_version), so every video records which build made it. The
script exports the commit with `git archive` to a temporary folder, writes the version into its pyproject.toml as
release.py does, and installs the command from it (not editable: it stays as built). The skill stays the one in the
Heptabase plugin; the `doctor` and `guide` it runs are now the dev build's.

A computer uses one version at a time: new chats use the dev build, and running chats are told to print the guide again
at their next command on an episode. `scripts/use_release.py` switches back.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from installation import REPOSITORY_DIR_PATH, install_cli, print_progress, run
from release import generate_versioned_files

from explainer_studio.errors import StudioError
from explainer_studio.explainer_studio_versions import convert_git_description_to_dev_build_version


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


def write_snapshot(commit_id: str, version: str, snapshot_dir_path: Path) -> None:
    """Export `commit_id` into the empty folder `snapshot_dir_path`, with its version written in."""
    archive_bytes = run_bytes(["git", "-C", str(REPOSITORY_DIR_PATH), "archive", "--format=tar", commit_id])
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as tar:
        tar.extractall(snapshot_dir_path, filter="data")
    for path, text in generate_versioned_files(snapshot_dir_path, version).items():
        path.write_text(text, encoding="utf-8")


def run_bytes(command: list[str]) -> bytes:
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        raise StudioError(f"`{' '.join(command)}` failed", completed.stderr.decode(errors="replace").strip()[-2000:])
    return completed.stdout


def use_dev_build(ref: str | None) -> None:
    commit_id, version = find_commit_and_version(ref)
    with tempfile.TemporaryDirectory(prefix="explainer-studio-dev-build-") as temporary_dir_path:
        snapshot_dir_path = Path(temporary_dir_path)
        print_progress(f"dev build {version}: exporting {commit_id[:7]}")
        write_snapshot(commit_id, version, snapshot_dir_path)
        studio_file_path = install_cli(f"explainer-studio @ {snapshot_dir_path.as_uri()}", version,
                                       should_reinstall=True)
    ref_note = f", {ref}" if ref and not commit_id.startswith(ref) else ""
    print(f"Using dev build {version} ({commit_id[:7]}{ref_note})")
    print(f"  CLI: {studio_file_path}")
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
