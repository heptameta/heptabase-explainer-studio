"""The `explainer-studio` command."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import click

from .. import __version__
from ..errors import StudioError

# each command is the click command or group of the same name in the module of the same name in this package (with
# underscores for dashes)
COMMAND_NAMES = ("setup", "doctor", "guide", "plan", "script", "narrate", "preview", "render", "video", "deliver", "feedback",
                 "gap", "cost", "asset", "dev-mode", "upgrade")


class LazyGroup(click.Group):
    """Imports a command's module only when that command runs, so `--help` and quick commands stay fast."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(COMMAND_NAMES)

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name not in COMMAND_NAMES:
            return None
        module_name = name.replace("-", "_")
        return getattr(importlib.import_module(f"{__package__}.{module_name}"), module_name)


@click.group(cls=LazyGroup, context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 110})
@click.version_option(__version__, "--version", prog_name="explainer-studio", message="%(prog)s %(version)s")
@click.option("--series", "series_path", type=click.Path(path_type=Path), default=None,
              help="The series folder (default: found by walking up from the current folder).")
@click.pass_context
def cli(ctx: click.Context, series_path: Path | None) -> None:
    """Heptabase Explainer Studio: make narrated explainer videos from teaching materials."""
    ctx.obj = {"series_path": series_path}


def main() -> None:
    try:
        cli.main(standalone_mode=False)
    except StudioError as error:
        click.echo(error.format(), err=True)
        sys.exit(1)
    except click.exceptions.Abort:
        click.echo("aborted", err=True)
        sys.exit(1)
    except click.exceptions.Exit as exit_:
        sys.exit(exit_.exit_code)
    except click.ClickException as error:
        error.show()
        sys.exit(2 if isinstance(error, click.UsageError) else 1)
    except KeyboardInterrupt:
        click.echo("interrupted", err=True)
        sys.exit(130)
