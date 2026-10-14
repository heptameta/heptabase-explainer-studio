"""Use the release on this computer again, after a dev build (scripts/use_dev_build.py).

    uv run python scripts/use_release.py

Installs the command from the latest release tag on GitHub, as the skill's install scripts do. New chats use the
release, and running chats are told to print the guide again at their next command on an episode.
"""

from __future__ import annotations

import argparse
import sys

from installation import install_cli

from explainer_studio.errors import StudioError
from explainer_studio.releases import RELEASE_REPO, fetch_latest_release_version


def use_release() -> None:
    version = fetch_latest_release_version()
    studio_file_path = install_cli(f"explainer-studio @ git+https://github.com/{RELEASE_REPO}@v{version}", version,
                                   should_reinstall=False)
    print(f"Using release {version}")
    print(f"  CLI: {studio_file_path}")
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
