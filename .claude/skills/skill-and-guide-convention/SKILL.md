---
name: skill-and-guide-convention
description: What goes in the plugin skill (plugin/skills/explainer-studio/) and what goes in the guide (explainer_studio/guide/), and how both are written: in English, with everything specific to one language kept in references/languages/<language>.md. Use before writing or changing any file under plugin/skills/ or explainer_studio/guide/, and when reviewing such a change.
---

# Writing the skill and the guide

## What goes where

The plugin carries the skill; the command carries the guide. Every plugin that carries the skill (this repository's,
and Heptabase's) copies it, and a copy changes only when that plugin is released, so the skill holds only what must be
known before the command is installed, and changes rarely:

- the description that makes an agent use it;
- what holds whatever the agent does: the user's language, never handling an API key, needing a shell;
- getting the command ready (`doctor`, the install scripts, `setup`);
- running `explainer-studio guide`, and when to run it again.

Everything about making videos goes in the guide (`guide.md`, `workflow/`, `references/`): it is installed with the
command, so it always matches the version that runs. The skill depends only on `doctor`, `setup`, `guide` and the
install scripts; keep how they are called working, or add a new form beside the old one.

## Language

Agents read the skill and the guide to make videos in any language. Both are written in English, and what applies to
one language lives only in that language's language reference (`references/languages/<language>.md`), which an
agent loads when its series uses that language.

- **Main files are English and language-neutral.** `SKILL.md`, `guide.md`, `workflow/` and every reference outside
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

`uv run python scripts/check_skill_and_guide.py` fails on text in another script outside `references/languages/`. A
language-specific rule written in English is for you to catch.
