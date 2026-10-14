"""Keep generated and version-bearing files in step with their sources.

    uv run python scripts/release.py              # regenerate everything from the current sources
    uv run python scripts/release.py --check      # exit 1 if anything is out of date (used by the tests)
    uv run python scripts/release.py --version 0.2.0   # a release: set the version, turn the
                                                       # Unreleased headings into it, then regenerate

Sources and what is generated from them:
- `--version X.Y.Z` (a release) -> pyproject.toml `version`, the only file that carries the version; uv.lock
  (`uv lock`); CHANGELOG.md's `## [Unreleased]` items go under `## [X.Y.Z] - <today>`, and UPGRADING.md's
  `## Unreleased` steps, if any, under `## X.Y.Z`. scripts/use_dev_build.py writes its dev build version into its
  snapshot's pyproject.toml the same way (`generate_versioned_files`).
- explainer_studio/question_types.py -> the table in references/teaching/question-types.md.
- explainer_studio/schemas -> the field tables in references/file-formats.md.
- explainer_studio/cli -> the command reference in docs/cli.md.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
import textwrap
import types
import typing
from pathlib import Path

from pydantic import AwareDatetime, BaseModel
from pydantic.fields import FieldInfo

REPOSITORY_DIR_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY_DIR_PATH))

# paths relative to a source tree: this repository, or a dev build's snapshot of one of its commits
GUIDE_DIR_PATH = Path("explainer_studio") / "guide"
PYPROJECT_TOML = Path("pyproject.toml")
CHANGELOG_MD = REPOSITORY_DIR_PATH / "CHANGELOG.md"
UPGRADING_MD = REPOSITORY_DIR_PATH / "UPGRADING.md"
QUESTION_TYPES_MD = REPOSITORY_DIR_PATH / GUIDE_DIR_PATH / "references" / "teaching" / "question-types.md"
FILE_FORMATS_MD = REPOSITORY_DIR_PATH / GUIDE_DIR_PATH / "references" / "file-formats.md"
CLI_MD = REPOSITORY_DIR_PATH / "docs" / "cli.md"

BEGIN_MARKER_TEMPLATE = "<!-- generated:{name} begin: edit the source, then run scripts/release.py -->"
END_MARKER_TEMPLATE = "<!-- generated:{name} end -->"


def replace_block(text: str, name: str, body: str) -> str:
    begin, end = BEGIN_MARKER_TEMPLATE.format(name=name), END_MARKER_TEMPLATE.format(name=name)
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    block = f"{begin}\n{body.rstrip()}\n{end}"
    if not pattern.search(text):
        raise SystemExit(f"missing generated block '{name}'; add the begin and end markers first")
    return pattern.sub(lambda _: block, text, count=1)


# Generators: each returns {path: new text} --------------------------------------------------------------------------
def generate_versioned_files(source_tree_dir_path: Path, version: str) -> dict[Path, str]:
    """The source tree's pyproject.toml, the only file that carries the version, with `version` written in."""
    pyproject_text = (source_tree_dir_path / PYPROJECT_TOML).read_text(encoding="utf-8")
    return {source_tree_dir_path / PYPROJECT_TOML: re.sub(r'^version = "[^"]+"', f'version = "{version}"',
                                                          pyproject_text, count=1, flags=re.MULTILINE)}


def generate_release_headings(version: str, release_date: str) -> dict[Path, str]:
    """CHANGELOG.md and UPGRADING.md with the Unreleased items under the new release's heading, the Unreleased heading
    kept, empty, above it. Nothing changes for a version that already has its heading."""
    changelog_text = CHANGELOG_MD.read_text(encoding="utf-8")
    if f"## [{version}]" in changelog_text:
        return {}
    unreleased_match = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## |\Z)", changelog_text, re.MULTILINE | re.DOTALL)
    if unreleased_match is None or not unreleased_match[1].strip():
        raise SystemExit("CHANGELOG.md has nothing under ## [Unreleased]: a release says what changed")
    text_by_path_map = {CHANGELOG_MD: changelog_text.replace(
        "## [Unreleased]\n", f"## [Unreleased]\n\n## [{version}] - {release_date}\n", 1)}
    upgrading_text = UPGRADING_MD.read_text(encoding="utf-8")
    upgrading_match = re.search(r"^## Unreleased\n(.*?)(?=^## |\Z)", upgrading_text, re.MULTILINE | re.DOTALL)
    if upgrading_match is not None and upgrading_match[1].strip():
        text_by_path_map[UPGRADING_MD] = upgrading_text.replace("## Unreleased\n", f"## Unreleased\n\n## {version}\n", 1)
    return text_by_path_map


def generate_question_type_table() -> dict[Path, str]:
    from explainer_studio.question_types import CONCEPT_GOAL_BY_NAME_MAP, QUESTION_TYPE_BY_NAME_MAP

    if not QUESTION_TYPES_MD.exists():
        return {}
    rows = ["| Question type | `question_type` | The question | Afterwards the viewer can | Must-haves |",
            "|---|---|---|---|---|"]
    rows += [f"| {question_type.display_name} | `{question_type.name}` | {question_type.question} | "
             f"{question_type.outcome} | {question_type.must_haves} |"
             for question_type in QUESTION_TYPE_BY_NAME_MAP.values()]
    goal_rows = ["| Goal | `concept_goal` | Afterwards the viewer can | Must-haves |", "|---|---|---|---|"]
    goal_rows += [f"| {concept_goal.display_name} | `{concept_goal.name}` | {concept_goal.outcome} | "
                  f"{concept_goal.must_haves} |" for concept_goal in CONCEPT_GOAL_BY_NAME_MAP.values()]
    text = QUESTION_TYPES_MD.read_text(encoding="utf-8")
    text = replace_block(text, "question-types", "\n".join(rows))
    text = replace_block(text, "concept-goals", "\n".join(goal_rows))
    return {QUESTION_TYPES_MD: text}


def format_type_name(annotation: object) -> str:
    origin = typing.get_origin(annotation)
    type_arguments = typing.get_args(annotation)
    null_text = " or null" if type(None) in type_arguments else ""
    if origin is typing.Annotated:
        return format_type_name(type_arguments[0])
    if origin in (typing.Union, types.UnionType):
        members = [argument for argument in type_arguments if argument is not type(None)]
        provider_names = [typing.get_args(member.model_fields["provider_name"].annotation)[0]
                          for member in members if isinstance(member, type) and issubclass(member, BaseModel)
                          and "provider_name" in member.model_fields]
        if provider_names and len(provider_names) == len(members):
            listed_provider_names = " / ".join(f"`{provider_name}`" for provider_name in provider_names)
            return f"settings with `provider_name`: {listed_provider_names}" + null_text
        if len(members) == 1 and typing.get_origin(members[0]) is typing.Annotated:
            return format_type_name(members[0]) + null_text
        type_names = [format_type_name(argument) for argument in members]
        return " or ".join(type_names) + null_text
    if origin is typing.Literal:
        return " / ".join(f"`{argument}`" for argument in type_arguments)
    if origin in (list, tuple):
        return f"list of {format_type_name(type_arguments[0])}" if type_arguments else "list"
    if origin is dict:
        return "mapping"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.__name__
    if annotation is AwareDatetime:
        return "time with UTC offset"
    return {str: "text", int: "integer", float: "number", bool: "true / false"}.get(annotation, str(annotation))


def format_field_rows(model: type[BaseModel]) -> list[str]:
    rows = ["| Field | Type | Required |", "|---|---|---|"]
    for field_name, field_info in model.model_fields.items():
        field_info: FieldInfo
        is_required_text = "yes" if field_info.is_required() else "no"
        rows.append(f"| `{field_name}` | {format_type_name(field_info.annotation)} | {is_required_text} |")
    return rows


def generate_schema_tables() -> dict[Path, str]:
    if not FILE_FORMATS_MD.exists():
        return {}
    from explainer_studio.schemas import audience_review, credits, feedback, gaps, narration, plan, script, timeline

    models_by_block_name_map = {
        "plan": [plan.Plan, plan.Audience, plan.Misconception, plan.Episode, plan.ExcludedTopic],
        "script": [script.Script, script.Scene, script.Beat],
        "audience-reviews": [audience_review.ScriptRound, audience_review.ReviewerSummary,
                             audience_review.ScriptFinding, audience_review.FindingResolution],
        "narration": [narration.NarrationRecord, narration.NarratedBeat],
        "timeline": [timeline.Timeline, timeline.TimelineScene, timeline.TimelineBeat, timeline.TimelineSound,
                     timeline.TimelineSoundEffect, timeline.TimelineSoundFile],
        "feedback": [feedback.Feedback, feedback.Comment, feedback.MomentAnchor, feedback.EpisodeAnchor,
                     feedback.Resolution, feedback.RatingAnswer, feedback.WatchDepthAnswer],
        "gaps": [gaps.Gap],
        "credits": [credits.Credits, credits.Credit],
    }
    text = FILE_FORMATS_MD.read_text(encoding="utf-8")
    for block_name, models in models_by_block_name_map.items():
        table_parts = []
        for model in models:
            table_parts.append(f"**{model.__name__}**\n")
            table_parts.append("\n".join(format_field_rows(model)) + "\n")
        text = replace_block(text, block_name, "\n".join(table_parts))
    return {FILE_FORMATS_MD: text}


def format_help_paragraphs(help_text: str, indent: str = "") -> list[str]:
    """Click help text as Markdown paragraphs wrapped at 120 columns, a blank line between them."""
    lines: list[str] = []
    for paragraph in help_text.strip().split("\n\n"):
        lines += textwrap.wrap(" ".join(paragraph.split()), 120, initial_indent=indent, subsequent_indent=indent,
                               break_long_words=False, break_on_hyphens=False)
        lines.append("")
    return lines


def list_documented_cli_parameters(command, context) -> list:
    """The command's arguments and options, without --help, which every command has."""
    import click

    return [parameter for parameter in command.get_params(context)
            if not (isinstance(parameter, click.Option) and set(parameter.opts) & set(context.help_option_names))]


def format_cli_synopsis(command, context) -> str:
    """How to call the command, with its real arguments, options and subcommands instead of click's [OPTIONS]
    COMMAND [ARGS]: arguments, then required options, then optional ones in brackets; a choice as its values."""
    import click

    def format_value(parameter) -> str:
        if isinstance(parameter.type, click.Choice):
            return "|".join(str(choice) for choice in parameter.type.choices)
        return parameter.metavar or (parameter.name.upper() if isinstance(parameter, click.Argument)
                                     else parameter.type.name.upper())

    arguments, options = [], []
    for parameter in list_documented_cli_parameters(command, context):
        if isinstance(parameter, click.Argument):
            piece = format_value(parameter) + ("..." if parameter.nargs == -1 else "")
            arguments.append(piece if parameter.required else f"[{piece}]")
        else:
            piece = "/".join([max(parameter.opts, key=len), *parameter.secondary_opts])
            piece += "" if parameter.is_flag else f" {format_value(parameter)}"
            options.append(piece if parameter.required else f"[{piece}]")
    pieces = [context.command_path, *arguments, *sorted(options, key=lambda piece: piece.startswith("["))]
    if isinstance(command, click.Group):
        subcommand_names = "|".join(name for name in command.list_commands(context)
                                    if not command.get_command(context, name).hidden)
        pieces.append(f"[{subcommand_names}]" if command.invoke_without_command else subcommand_names)
    return " ".join(pieces)


def format_cli_command_section(command, context, heading_level: int) -> list[str]:
    """The section of one command, then those of its subcommands one heading level down."""
    import click

    lines = [f"{'#' * heading_level} `{context.command_path}`", "", "```text", format_cli_synopsis(command, context),
             "```", ""]
    lines += format_help_paragraphs(command.help or "")
    for parameter in list_documented_cli_parameters(command, context):
        help_record = parameter.get_help_record(context) if isinstance(parameter, click.Option) else None
        if help_record is None:
            continue
        declaration, help_text = help_record
        lines += textwrap.wrap(f"- `{declaration}`: {' '.join(help_text.split())}", 120, subsequent_indent="  ",
                               break_long_words=False, break_on_hyphens=False)
    if lines[-1] != "":
        lines.append("")
    if isinstance(command, click.Group):
        for subcommand_name in command.list_commands(context):
            subcommand = command.get_command(context, subcommand_name)
            if subcommand is not None and not subcommand.hidden:
                lines += format_cli_command_section(
                    subcommand, click.Context(subcommand, info_name=subcommand_name, parent=context),
                    min(heading_level + 1, 6))
    return lines


def generate_cli_reference() -> dict[Path, str]:
    if not CLI_MD.exists():
        return {}
    import click

    from explainer_studio.cli.main import cli

    lines = format_cli_command_section(cli, click.Context(cli, info_name="explainer-studio", **cli.context_settings), 2)
    return {CLI_MD: replace_block(CLI_MD.read_text(encoding="utf-8"), "cli", "\n".join(lines))}


def generate_files() -> dict[Path, str]:
    text_by_path_map: dict[Path, str] = {}
    for generator in (generate_question_type_table, generate_schema_tables, generate_cli_reference):
        text_by_path_map.update(generator())
    return text_by_path_map


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", dest="is_check_only", action="store_true",
                        help="report out-of-date files and exit 1; change nothing")
    parser.add_argument("--version", help="release this version: set it in pyproject.toml and give it the Unreleased "
                                          "items of CHANGELOG.md and UPGRADING.md")
    arguments = parser.parse_args()
    is_release = bool(arguments.version) and not arguments.is_check_only
    from explainer_studio.releases import parse_release_version

    if is_release and parse_release_version(arguments.version) is None:
        raise SystemExit(f"{arguments.version} is not a release version: X.Y.Z, such as 0.2.0")
    text_by_path_map = generate_files()
    if is_release:
        text_by_path_map.update(generate_versioned_files(REPOSITORY_DIR_PATH, arguments.version))
        text_by_path_map.update(generate_release_headings(arguments.version, datetime.datetime.now(datetime.UTC).date().isoformat()))
    stale_paths = [path for path, text in text_by_path_map.items()
                   if not path.exists() or path.read_text(encoding="utf-8") != text]
    if arguments.is_check_only:
        for path in stale_paths:
            print(f"out of date: {path.relative_to(REPOSITORY_DIR_PATH)}")
        sys.exit(1 if stale_paths else 0)
    for path in stale_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text_by_path_map[path], encoding="utf-8")
        print(f"updated {path.relative_to(REPOSITORY_DIR_PATH)}")
    if not stale_paths:
        print("everything is up to date")
    if is_release:
        # uv.lock records the project's version; CI installs with `uv sync --locked`
        subprocess.run(["uv", "lock"], cwd=REPOSITORY_DIR_PATH, check=True)


if __name__ == "__main__":
    main()
