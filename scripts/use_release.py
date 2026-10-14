"""Use the release on this computer again, after a dev build (scripts/use_dev_build.py).

    uv run python scripts/use_release.py

Users get the skill from the Heptabase plugin, so the release does too. The dev build's marketplace
heptabase-explainer-studio is removed, which uninstalls its plugin; it has no Claude Code data to lose. Other enabled
plugins named explainer-studio are disabled. The Heptabase plugin is updated and enabled again (or installed from
heptameta/heptabase-agent-plugins), and the CLI is installed from the latest release tag on GitHub. The dev build folder
is left as it is, for the next `use_dev_build.py`.

New chats use the release, and running chats are told to print the guide again at their next command on an episode.
"""

from __future__ import annotations

import argparse
import sys

from installation import (
    MARKETPLACE_NAME,
    PLUGIN_ID,
    PLUGIN_NAME,
    disable_plugins,
    find_claude,
    find_marketplace,
    install_cli,
    run_claude_action,
    use_heptabase_plugin,
)
from release import read_release_repo

from explainer_studio.errors import StudioError
from explainer_studio.releases import fetch_latest_release_version


def use_release() -> None:
    claude_path = find_claude()
    if claude_path is None:
        raise StudioError("claude is not on PATH", "the release's skill is the Heptabase plugin Claude Code installs",
                          "run this where `claude` works")
    repo = read_release_repo()
    version = fetch_latest_release_version()
    lines = []
    if find_marketplace(claude_path) is not None:
        run_claude_action(claude_path, "plugin", "marketplace", "remove", MARKETPLACE_NAME)
        lines.append(f"removed the dev build's marketplace {MARKETPLACE_NAME} and its plugin {PLUGIN_ID}")
    lines += disable_plugins(claude_path, {PLUGIN_NAME})
    lines += use_heptabase_plugin(claude_path)
    studio_file_path = install_cli(f"explainer-studio @ git+https://github.com/{repo}@v{version}", version,
                                   should_reinstall=False)
    print(f"Using release {version}")
    for line in [f"CLI: {studio_file_path}", *lines]:
        print(f"  {line}")
    print("New chats use it. Running chats are told at their next command on an episode to print the guide again.")


def main() -> None:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    try:
        use_release()
    except StudioError as error:
        print(error.format(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
