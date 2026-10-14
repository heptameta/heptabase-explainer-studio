"""`setup`, `setup blender`, `setup playwright` and `setup narration [<provider>]`."""

from __future__ import annotations

import sys

import click

from ..errors import StudioError
from ..narration_providers import PROVIDER_BY_NAME_MAP, NarrationProviderName
from .common import print_progress, print_result, print_warning
from .doctor import format_check_summary_lines


def _format_api_key_line() -> str:
    from ..environment import get_operating_system

    line = ("Narration needs a paid API key (ElevenLabs, OpenAI or VoAI) before the first `narrate`; set it later "
            "with `explainer-studio setup narration` in your own terminal.")
    is_macos = get_operating_system() == "macos"
    return line + (" On macOS the free macos-say voice works without a key." if is_macos else "")


@click.group(invoke_without_command=True)
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Install what videos need besides Python packages: ffmpeg, LaTeX, fonts and map data, then render a test
    scene. Per-user, no password, safe to run again (it repairs and upgrades)."""
    if ctx.invoked_subcommand is not None:
        return
    from .. import environment

    failed_step_labels = []
    steps = [("ffmpeg", environment.ensure_ffmpeg), ("LaTeX", environment.ensure_tex),
             ("fonts", environment.ensure_fonts), ("map data", environment.ensure_geo)]
    for label, step in steps:
        try:
            print_result(step(print_progress))
        except StudioError as error:
            failed_step_labels.append(label)
            print_result(f"{label}: FAILED")
            click.echo(error.format(), err=True)
    if {"ffmpeg", "LaTeX"} & set(failed_step_labels):
        print_result("test render: skipped until ffmpeg and LaTeX are installed")
    else:
        try:
            print_result(f"test render: ok, last frame at {environment.render_test_scene(print_progress)}")
        except StudioError as error:
            failed_step_labels.append("test render")
            print_result("test render: FAILED")
            click.echo(error.format(), err=True)
    failing_checks = [check for check in environment.run_checks() if check.is_required and not check.is_ok]
    for line in format_check_summary_lines(failing_checks) if failing_checks else []:
        print_result(line)
    if failed_step_labels or failing_checks:
        print_result("setup is not complete; fix the problems above and run `explainer-studio setup` again")
        print_result(_format_api_key_line())
        sys.exit(1)
    print_result("setup complete: everything required for making videos is installed")
    print_result(_format_api_key_line())


@setup.command("blender")
def blender() -> None:
    """Install Blender (about 1 GB) for `asset blender render`, unless a recent one is already installed."""
    from ..environment import ensure_blender

    print_result(ensure_blender(print_progress))


@setup.command("playwright")
def playwright() -> None:
    """Install Playwright's Chromium (about 150 MB) for `asset playwright record`."""
    from ..environment import ensure_playwright

    print_result(ensure_playwright(print_progress))


@setup.command("narration")
@click.argument("provider_name", metavar="PROVIDER", required=False, type=click.Choice(list(PROVIDER_BY_NAME_MAP)))
def narration(provider_name: NarrationProviderName | None) -> None:
    """Choose a narration provider, enter its API key (hidden), test it and save it to credentials.toml.

    Run it in your own terminal: the key is typed by you and never shown or passed to the agent.
    """
    from ..credentials import find_api_key, write_api_key
    from ..narration_providers import get_provider
    from ..narration_providers.base import SynthesisError

    if not sys.stdin.isatty():
        raise StudioError("setup narration needs an interactive terminal", "it reads the API key with hidden input",
                          "ask the user to run `explainer-studio setup narration` in their own terminal")
    if provider_name is None:
        provider_names = list(PROVIDER_BY_NAME_MAP)
        for number, listed_provider_name in enumerate(provider_names, start=1):
            click.echo(f"{number}. {listed_provider_name:<11} {PROVIDER_BY_NAME_MAP[listed_provider_name].description}")
        provider_name = provider_names[click.prompt("Provider number", type=click.IntRange(1, len(provider_names))) - 1]
    provider = get_provider(provider_name)
    if provider.api_key_env is None:
        provider.require_available()
        print_result(f"{provider_name} needs no key. Use it with `narration: {{provider_name: {provider_name}}}` in "
                     "plan.yaml.")
        return
    existing_api_key = find_api_key(provider_name)
    if existing_api_key:
        click.echo(f"A {provider_name} key is already set ({existing_api_key.source}). A new key replaces the saved "
                   "one.")
    click.echo(f"Get a key at {provider.api_key_page_url}")
    api_key = click.prompt(f"{provider_name} API key (hidden)", hide_input=True).strip()
    if not api_key:
        raise StudioError("no key entered", "the input was empty", "run `explainer-studio setup narration` again")
    print_progress(f"testing the key with {provider_name}")
    try:
        provider.verify_api_key(api_key)
    except SynthesisError as error:
        raise StudioError(f"could not test the {provider_name} key", str(error),
                          "check the network connection and run `explainer-studio setup narration` again") from None
    credentials_file_path = write_api_key(provider_name, api_key)
    print_result(f"the {provider_name} key works and is saved in {credentials_file_path} (readable only by you)")
    if existing_api_key and existing_api_key.source.startswith("environment"):
        print_warning(f"{existing_api_key.source} is set and is used before the saved key; unset it to use the saved "
                      "one")
