"""`guide [<path>]`."""

from __future__ import annotations

from pathlib import Path

import click

from ..errors import StudioError
from .common import print_result

PACKAGE_DIR_PATH = Path(__file__).resolve().parent.parent
GUIDE_DIR_PATH = PACKAGE_DIR_PATH / "guide"
GUIDE_FILE_PATH = GUIDE_DIR_PATH / "guide.md"
SCENE_KIT_DIR_PATH = PACKAGE_DIR_PATH / "scene_kit"


def format_guide_header() -> str:
    from .. import __version__

    return "\n".join([f"Explainer Studio {__version__} guide",
                      f"guide folder (read-only; the paths in the guide are relative to it): {GUIDE_DIR_PATH}",
                      f"scene_kit folder: {SCENE_KIT_DIR_PATH}",
                      "print a file of the guide: explainer-studio guide <path>"])


def find_guide_path(path_text: str) -> Path:
    """The file or folder of the guide at `path_text`, relative to the guide folder. Raises StudioError for a path
    outside the guide or one that does not exist."""
    path = (GUIDE_DIR_PATH / path_text).resolve()
    if not path.is_relative_to(GUIDE_DIR_PATH) or not path.exists():
        raise StudioError(f"the guide has no {path_text}", "paths are relative to the guide folder",
                          "use a path the guide names, such as references/teaching/rules.md")
    return path


@click.command()
@click.argument("path_text", metavar="PATH", required=False)
def guide(path_text: str | None) -> None:
    """Print the guide to making videos with this version, or one of its files (PATH, relative to the guide folder).
    A folder lists its files."""
    if path_text is None:
        print_result(format_guide_header())
        print_result()
        print_result(GUIDE_FILE_PATH.read_text(encoding="utf-8").rstrip())
        return
    path = find_guide_path(path_text)
    if path.is_dir():
        for file_path in sorted(file_path for file_path in path.rglob("*") if file_path.is_file()):
            print_result(str(file_path.relative_to(GUIDE_DIR_PATH)))
        return
    print_result(path.read_text(encoding="utf-8").rstrip())
