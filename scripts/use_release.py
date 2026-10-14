"""Use the release on this computer again, after a dev build (scripts/use_dev_build.py).

    uv run python scripts/use_release.py

The marketplace heptabase-explainer-studio goes back to the GitHub repository that install.sh installs from. Claude
Code points a marketplace of the same name from GitHub to a local folder but refuses the other way, so a local one is
removed and added again; removing it uninstalls the plugin and deletes its Claude Code data, which this plugin has
none of. Then the plugin is installed, other enabled plugins named explainer-studio (for example a copy from another
marketplace) are disabled, and the CLI is installed from the GitHub tag of the plugin's version. The dev build folder is left as it is, for the next
`use_dev_build.py`.

New chats use the release, and running chats are told to print the guide again at their next command on an episode.
"""

from __future__ import annotations

import argparse
import sys

from installation import (
    MARKETPLACE_NAME,
    PLUGIN_ID,
    disable_other_plugins,
    find_claude,
    find_installed_plugin_version,
    find_marketplace,
    install_cli,
    install_plugin,
    run_claude_action,
    update_plugin,
)
from release import read_release_repo

from explainer_studio.errors import StudioError


def use_release() -> None:
    claude_path = find_claude()
    if claude_path is None:
        raise StudioError("claude is not on PATH", "the release to use is the plugin version Claude Code installs",
                          "run this where `claude` works")
    repo = read_release_repo()
    current_marketplace = find_marketplace(claude_path)
    is_github_marketplace = (current_marketplace is not None and current_marketplace.get("source") == "github"
                             and current_marketplace.get("repo") == repo)
    if is_github_marketplace:
        run_claude_action(claude_path, "plugin", "marketplace", "update", MARKETPLACE_NAME)  # the latest release
    else:
        if current_marketplace is not None:
            run_claude_action(claude_path, "plugin", "marketplace", "remove", MARKETPLACE_NAME)
        run_claude_action(claude_path, "plugin", "marketplace", "add", repo)
    install_plugin(claude_path)
    notes = update_plugin(claude_path)
    version = find_installed_plugin_version(claude_path)
    notes += disable_other_plugins(claude_path)
    studio_file_path = install_cli(f"explainer-studio @ git+https://github.com/{repo}@v{version}", version,
                                   should_reinstall=False)
    print(f"Using release {version}")
    for line in [f"CLI: {studio_file_path}", f"plugin: {PLUGIN_ID} {version}, from github.com/{repo}", *notes]:
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
