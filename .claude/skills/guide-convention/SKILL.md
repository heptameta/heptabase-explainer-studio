---
name: guide-convention
description: What goes in the guide (explainer_studio/guide/), what the skill in the Heptabase plugin relies on, and how the guide is written: in English, with everything specific to one language kept in references/languages/<language>.md. Use before writing or changing any file under explainer_studio/guide/ or the doctor, setup or guide commands, and when reviewing such a change.
---

# Writing the guide

## The guide and the skill

The command carries the guide. The skill that installs the command is in the Heptabase plugin
(`plugins/heptabase/skills/explainer-studio/` in `heptameta/heptabase-agent-plugins`), whose `AGENTS.md` says what it
holds: only getting the command ready and running `explainer-studio guide`. Every installed plugin keeps its copy until
the plugin is updated, so everything about making videos goes in the guide (`guide.md`, `workflow/`, `references/`):
it is installed with the command, so it always matches the version that runs.

The skill and the command depend on each other across the two repositories:

- the skill runs `doctor`, `setup` and `guide`;
- its install scripts install the latest release tag `v<version>` of this repository, with the Python that
  `PYTHON_VERSION` in `cli/upgrade.py` names;
- the command and the guide send the agent to the skill's `scripts/install.sh` and `scripts/install.ps1` to install uv
  and the latest release: when uv is missing, to upgrade on Windows, and when ManimGL is broken.

Keep these working, or add a new form beside the old one. A change on the skill's side goes to that repository, in a
pull request that raises the plugin's version.

## Language

Agents read the guide to make videos in any language. It is written in English, and what applies to one language
lives only in that language's language reference (`references/languages/<language>.md`), which an agent loads when
its series uses that language.

- **Main files are English and language-neutral.** `guide.md`, `workflow/` and every reference outside
  `references/languages/` contain no text in another script, and no rule, number, example or wording that applies to
  one language only.
- **Language-specific content goes in `references/languages/<language>.md`:** speaking rate and length conversions,
  sentence limits, spoken style, terms and names, fonts and typesetting, on-screen and cover wording, examples written
  in that language.
- **Split at one layer.** When a main file needs something that differs by language, it states the general rule in
  English and points to the language reference ("convert with the language reference's speaking rate",
  `languages/<language>.md`). The language reference holds the specifics. Never add a "for Chinese ..." aside or a
  `(zh-TW: ...)` parenthetical to a main file.
- **Words the agent says to the user** are written in English in the main file, and the agent says them in the series
  language. A language reference may fix the wording for its language when exact wording matters.
- **English is the base case.** A main file may give the figures for Latin script, with other scripts in their
  language references.
- Facts about the product (which scripts the video font covers, what `setup` installs) and content examples (a video
  by a Chinese creator) are not language-specific guidance; they may stay in a main file.
- Adding a language means adding `references/languages/<language>.md` with the same sections as `en.md`.

`uv run python scripts/check_guide.py` fails on text in another script outside `references/languages/`. A
language-specific rule written in English is for you to catch.
