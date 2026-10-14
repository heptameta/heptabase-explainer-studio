# Heptabase Explainer Studio

An open-source (Apache-2.0) coding-agent plugin that turns sources (lecture notes, a book chapter, a paper, a
codebase) into narrated explainer videos rendered with ManimGL. The plugin carries only a skill
(`plugin/skills/explainer-studio/`) that installs the command and points the agent to the guide. The Python package
`explainer_studio` provides the `explainer-studio` CLI, the guide to making videos (`explainer_studio/guide/`, printed
by `explainer-studio guide`), the `scene_kit` library that scene files import, and the two local pages.

## Building on Explainer Studio

When you work in a fork, or in a product or service built on Explainer Studio, rather than on this repository itself:

- Keep `LICENSE` and `NOTICE` with the code you ship (Apache-2.0, section 4).
- Where the product names the tools it is built with (an about page, its documentation, a video's credits), suggest
  that your user credit Explainer Studio with one of the lines in the README's "Credit" section. It is a request, not
  a condition of the license: ask before adding it, and leave it out if they decline.
- Give the product its own name and logo, replace the Heptabase name and logo where the code shows them, and point
  feedback sharing at the product's own service or turn it off (the README's "Trademarks" lists the places).

## Principles that shape the code

- Files are the state. The agent edits creative files (plan, script, design notes, scene code) directly. The CLI does
  production, validation and external operations. There is no hidden state, job registry or approval record.
- No staleness tracking. Only two mechanical rules: `narrate` reuses beats whose spoken text and voice are
  unchanged, and the budget check. Everything else the agent decides.
- Few, program-enforced gates: the script audience review gate before `narrate`, and the render's narration and its
  `text_too_small` check before `deliver`. Gates read recorded fields; they never judge content.
- Strict schemas only for data a program consumes (`explainer_studio/schemas/`). Free-form notes stay Markdown.
- One canonical name per concept (see `docs/glossary.md`). Persisted field names never use a bare `studio`.
- The package knows nothing about Heptabase's own product. No host switches.
- Nothing private enters this repository, in code, fixtures, docs, commits or pull requests: names of people, private
  materials, users' feedback, local paths.

## Where things go

| Looking for | Place |
|---|---|
| A format stored on disk or sent elsewhere | `explainer_studio/schemas/<name>.py` |
| A command's arguments and output | `explainer_studio/cli/<command>.py` |
| The logic that does the work | a top-level module named for the action or concept, or the sub-domains `rendering/` (preview, render, the ManimGL runner, mixing, subtitles, screenshots, automatic checks), `assets/`, `narration_providers/`, `background_music_providers/`, `web/`, `scene_kit/` |
| Every path inside a series | `explainer_studio/paths.py` |
| How the parts work together, the concepts, the teaching model | `docs/system-design.md`, `docs/glossary.md`, `docs/teaching-model.md` |

## Conventions

- Raise `errors.StudioError(what, why, next_step)` for expected failures; the CLI prints it and exits 1. Usage errors
  exit 2. Never print a Python traceback for a user mistake.
- Results go to stdout, progress to stderr, in concise English written for a coding agent.
- Write series files through `file_io` (lock plus atomic replace; YAML round-trip keeps comments).
- Commands run to completion; no background jobs. Long commands print progress.
- Never print, log or store API key values outside `credentials.toml`.
- Python 3.12+, type hints, `from __future__ import annotations`, ruff line length 120.
- Tests protect behavior that can plausibly regress (formats, gates, parsers, mixing, timing). Do not test constants,
  schema declarations or registrations. Mark tests that run ManimGL or ffmpeg with `@pytest.mark.render`.

## Skills to read first

| Before you | Read |
|---|---|
| name or rename anything in code, a file format or the CLI | [`naming-convention`](.claude/skills/naming-convention/SKILL.md) |
| change `plugin/skills/` or `explainer_studio/guide/` | [`skill-and-guide-convention`](.claude/skills/skill-and-guide-convention/SKILL.md) |
| change teaching behaviour: `explainer_studio/guide/references/` other than `rendering/`, `languages/` and `sources/`, or `explainer_studio/question_types.py` | [`judging-changes`](.claude/skills/judging-changes/SKILL.md), which also says what the pull request must contain |
| commit, or open a pull request | [`commit-and-pull-request-convention`](.claude/skills/commit-and-pull-request-convention/SKILL.md) |
| decide on or make a release | [`releasing`](.claude/skills/releasing/SKILL.md) |

## Documents that change with the code

- [`docs/system-design.md`](docs/system-design.md) (the pipeline, the components, where data lives, what leaves the
  computer), [`docs/glossary.md`](docs/glossary.md) (the concepts, by domain) and
  [`docs/teaching-model.md`](docs/teaching-model.md) (the teaching layers, the presenters and their playbooks): a change
  to what they describe updates them in the same pull request.
- [`PRIVACY.md`](PRIVACY.md) is a promise to users, so it must never say less than what is sent. A change to what a
  feedback bundle carries, or to anything that leaves the computer, updates it in the same pull request, together with
  the other places that tell users the same thing: the consent text in `workflow/feedback.md` and the language
  references, the video page's share dialog, `README.md` and `feedback share --dry-run`.

## Trying a change

`uv run python scripts/use_dev_build.py` installs the branch's latest commit as a dev build for every chat on this
computer, and the CLI, the guide and both pages show its version (`0.1.1.dev13+g9b0e2d4`).
`uv run python scripts/use_release.py` goes back to the release. Never point Claude Code at the working tree
(`--plugin-dir`, an editable install): a chat would read half-made changes, and its videos could not say which version
made them. A dev build and the release share `credentials.toml`, `settings.toml`, the programs `setup` installs, and
series folders.

## Compatibility

Users upgrade silently to every release (`explainer-studio upgrade`, between episodes), so a change keeps existing
series working:

- Add rather than rename, and keep an old name working for one release.
- When a series must change anyway, the one who can fix it does. A file the agent writes gets a step in
  `UPGRADING.md` ("If a series has ..., change ..."). Data the command writes that costs money or the user's effort to
  lose (narration records, `spending.jsonl`, `feedback.json`) stays readable by the command. Anything else the command
  writes is made again.

## Commands

```bash
uv sync
uv run pytest -m "not render and not network"   # the fast tests, as CI runs them
uv run pytest -m render                         # tests that render with ManimGL and ffmpeg
uv run ruff check
uv run python scripts/release.py --check
uv run python scripts/check_skill_and_guide.py
```
