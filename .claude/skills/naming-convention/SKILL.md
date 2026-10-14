---
name: naming-convention
description: Naming rules for Explainer Studio, covering verbs for functions, nouns for classes, booleans, maps, units, abbreviations, file format fields, CLI commands, GitHub workflows and the glossary. Use before naming or renaming anything in explainer_studio/ (Python and the pages' JavaScript), tests/ or scripts/, before adding a field to a file format, a CLI option or a GitHub workflow, and when reviewing names.
---

# Naming

A name says what a thing is, or what a function does, without opening it. A concept has one name everywhere (code, file
formats, CLI, skill, pages): the term in [`docs/glossary.md`](../../../docs/glossary.md). A new domain term goes into
its domain in the glossary in the same change. A term names what the thing holds or shows, never a bare container word
that a reader has to look up (`comment screenshot sheet`, not `comment sheet`; no standalone `sheet`, `item`, `data` or
`info`). Parallel things get parallel names: siblings doing the same kind of work share the verb, the word order and the
grammar.

## Functions and methods start with a verb

A noun alone (`latest_delivery()`, `media_duration()`) hides whether the function reads files, computes or
builds. These verbs have one meaning each; use them whenever that is the work, and never for other work:

| Verb | The function |
|---|---|
| `load` / `read` | reads from disk; `load_` returns a validated model, `read_` raw content or a plain value |
| `write` | writes to disk |
| `list` | returns every item of a kind (the ids in a folder, the installed voices) |
| `find` | looks on disk or in a collection for something that may be missing, or for every match (problems, warnings, ids); returns `None` or an empty list when there is none, or raises `StudioError` when the caller cannot go on (the docstring says which) |
| `fetch` / `download` | gets data over the network; `download_` saves it to a file |
| `resolve` | derives one answer from what it is given, by fixed rules, with no I/O |
| `build` | combines what it is given into a composite (a model, an image, a request), with no I/O |
| `compute` | works out a result from data it reads or is given (a digest, a cost report) |
| `format` | produces text for a person or an agent |
| `parse` | reads a grammar or a loose shape where failing is normal |
| `convert` | turns one valid representation into another: `convert_<source>_to_<target>` |
| `serialize` | produces the bytes or text that a format stores or sends |
| `check` | answers yes or no: `check_is_...`, `check_has_...`, `check_does_...` |
| `require` | raises `StudioError` when a precondition does not hold |
| `validate` | checks data against its schema or format rules; raises, or returns the problems |
| `verify` | checks a credential with its service |
| `ensure` | makes something exist when it is missing (a folder, an installed program) |
| `create` | makes a new thing every time |
| `get` | returns what already exists or is fixed, with no work worth naming: a part of the object it is called on, a fixed location (`get_config_dir_path`); in scene_kit, a new mobject, following ManimGL |

Other plain verbs (`add`, `record`, `render`, `mix`, `measure`, `estimate`, `draw`, `choose`, `share`, `deliver`,
`play`, `animate`) are fine when they say exactly what happens. Exempt: dunder methods, `main()`, `@property` (a
value: a noun, or a boolean under the rules below), pydantic validators, click command callbacks (named after the
command), pytest tests and fixtures, overrides of an external library's methods, and the doctor's `check_*`
functions, which return a doctor `Check`.

Two areas have their own families:

- **scene_kit**, which scene files call: `get_*` returns a new mobject; `animate_*_to` returns the animations that
  move a component to new values; `play_*` takes the scene and plays something (`play_beat`, `play_sound`);
  `solve_*` returns a simulated solution. Other helpers name their one change (`add_checklist_row`, `swap_seat`),
  including those that take the scene and play it (`shrink_to_inset`, `strike_claim`).
- **The pages' JavaScript:** `build*` returns a new DOM node; `show*` puts the current state on the page; `fetch*`
  gets data from the page server, and a call that changes something names the change (`patchComment`). `render` and
  `draw` are not used there: they mean video rendering and drawing images.

## Other names

- **Classes** are nouns. An exception class ends in `Error`.
- **Booleans** (variables, parameters, fields, properties, JSON keys) start with `is_`, `has_`, `can_`, `should_`,
  `does_` or `was_`; a function that returns one starts with `check_` (above). A CLI flag may read naturally
  (`--no-browser`) while its Python destination follows the rule (`should_skip_browser`).
- **Lookup maps** (a dict whose keys are all one kind and values all one kind) end in `_map`:
  `<key>_to_<value>_map` or `<value>_by_<key>_map`. A record-shaped dict (a JSON document, settings, `**kwargs`) is
  not a map. Lists and sets are plural nouns. A number is never a plural noun (`row_count`, not `rows`).
- **Numbers with a unit** end in the unit, spelled out: `_seconds`, `_milliseconds`, `_bytes`, `_pixels`, `_usd`,
  `_characters`, `_decibels`, `_hertz`. A count ends in `_count`. Scene coordinates and sizes in ManimGL units carry
  no suffix, since every scene length is in them.
- **No single letters or cryptic abbreviations** for values that are not mathematics, including comprehension and
  lambda variables (`time_seconds`, not `t`; `comment`, not `c`). Indices, coordinates and the symbols of a formula
  (`i`, `x`, `y`, `t` as a curve parameter, `theta`) are mathematics. Established terms (`id`, `url`, `json`, `pdf`,
  `svg`, `dir`, `tex`, `rgb`) are fine.
- **Module constants** are SCREAMING_SNAKE_CASE and follow the same rules
  (`COMMENT_SCREENSHOT_SHEET_INTERVAL_SECONDS`, `PROVIDER_BY_NAME_MAP`). A compiled regular expression ends in
  `_PATTERN`.
- **Ids, names and objects:** an id identifies an instance that is made while the product is used and can be many
  (an episode, a scene, a beat, a comment, a gap, the feedback id); a variable holding one ends in `_id`
  (`episode_id`, `scene_id`). A choice from a fixed set defined in code (a provider, a presenter, a harness, a model,
  a sound effect, a check) is not an id: it has a name, a variable holding it ends in `_name` (`provider_name`), it
  gets a `Literal` type where the set is fixed in code, and maps keyed by it end in `_BY_NAME_MAP` /
  `_by_<thing>_name_map`. Words that already say they are a classification stay bare (`kind`, `category`, `origin`,
  `step`, `question_type`). In every case the bare noun (`episode`, `provider`) holds the object. A language code is
  `language_code`; text for people to read ("ElevenLabs", "Theo") is `display_name` / `*_display_name`.
- **Paths:** a path ends in `_file_path` or `_dir_path` (plural `_file_paths`, `_dir_paths`), or is `path` (or
  `<thing>_path`) when it can be either a file or a folder (`series.plan_file_path` is the file, `load_plan()`
  returns the plan). A file or folder name without its folder ends in `_file_name` or `_dir_name`. `<thing>_file`
  names an open file object, never a path; a local may be called `handle`.
- **Plurals:** in a compound noun only the last word is plural (`comment_screenshot_sheets`, `page_thumbnail_sheets`,
  `scene_ids`). A path keeps the form of the file or folder it names (`episodes_dir_path`, `credits_file_path`).
- **Public names are complete;** a local may be short when its function makes it clear (`build`, `server`).
- **US spelling** in identifiers.

## File formats

- **Fields written to disk or printed as JSON:** an instance's own id is `id`; a reference to another instance is
  `<entity>_id`; a choice from a fixed set is `<thing>_name` (`provider_name: elevenlabs`), or the bare classification
  word (`kind: moment`); an object whose fields depend on a choice is a union discriminated by that choice (`kind`,
  or the choice's own field, such as `provider_name` in narration settings); counts end in `_count`;
  timestamps end in `_at` and are `AwareDatetime`; units and booleans as above. The pages' JSON uses the
  same names in camelCase.
- Renaming a field changes a format: change its writers, its readers, the guide (`explainer_studio/guide/`)
  and `references/file-formats.md` in the same change.
- **External names stay at the boundary:** provider request fields, ManimGL keyword arguments and library names keep
  their spelling where they are passed on.

## CLI commands

Every `explainer-studio` command has one of three shapes:

| Shape | Form | Commands |
|---|---|---|
| Production step | `<verb> <episode>` | `narrate`, `preview`, `render`, `deliver` |
| Concept group | `<noun> <verb>` or `<noun> <verb>-<object>` | `plan open`, `script prepare-audience-review-prompt`, `video open`, `feedback add`, `gap add`, `cost show`, `asset wikipedia download-portrait` |
| This computer | `setup [<part>]`, `doctor`, `upgrade`, `guide [<path>]`, `dev-mode [on\|off]` | installing parts, checking the installation, installing the latest release, the installed version's guide, a per-computer setting |

- **A group** is the glossary noun the commands act on, singular (`feedback`, `gap`). Under `asset`, the second level
  names the source (`asset commons`, `asset pdf`).
- **A leaf is an imperative verb, never a noun** (`feedback screenshots` and `asset image grid` are wrong). It is the
  bare verb when it acts on the group's concept or one item of it (`plan validate`; `feedback add` adds one comment).
  Otherwise it is `<verb>-<object>`, the object being the glossary term for what it makes or acts on (a plain noun
  when the glossary has none, as in `draw-grid`), plural when it makes several (`script prepare-audience-review-prompt`,
  `asset pdf draw-page-thumbnail-sheets`). Use the glossary term whole: no synonym and no shortening (`comment-sheets`
  for comment screenshot sheets).
- **Command verbs** keep the meanings of the function verb table, plus: `open` opens a local page; `show` prints a
  report; `validate` checks a file's format; `search` lists matches without downloading; `download` saves a file from
  the network; `draw` makes images for the agent or the user to look at; `render` renders with ManimGL or Blender;
  `record` captures a browser session; `prepare` writes a file for another agent to read; `add` appends one item;
  `share` sends something away with the user's consent. One verb per kind of work: images are drawn, never made,
  generated or saved.
- **Arguments** are named for what they hold, with glossary nouns: `<episode>` is an episode id (`ep01`); `<file>`,
  `<spec>`, `<query>`.
- **Options** have one name per meaning on every command:

  | Option | Holds |
  |---|---|
  | `--series` | the series folder |
  | `--to` | where the command writes: a folder, or a file path when it writes one file |
  | `--scenes`, `--beats` | comma-separated scene or beat ids |
  | `--start`, `--end`, `--at` | times in a video or clip, written as a player shows them (`83`, `1:23`) |
  | `--first-page`, `--last-page`, `--page` | PDF page numbers |
  | `--limit` | the most results to list |
  | `--json` | print JSON instead of text |
  | `--dry-run` | show what the command would do, without doing it |
  | `--no-browser` | do not open the page in a browser |

  Synonyms of these (`--out`, `--output`, `--dest`, `--preview` for a dry run, `--from` for a first page) are not
  used. A new option spells out what it holds (`--media-type`, not `--type`); a flag says what turning it on does
  (`--cover` also previews the cover).
- **Click destinations** follow the Python rules: `should_print_json`, `should_skip_browser`, `is_dry_run`,
  `scene_ids`. A callback is named after its command, prefixed with its group when one module holds several groups
  (`wikipedia_download_portrait` in `cli/asset.py`).
- A new or renamed command changes the guide and every mention of it in the same change.

## GitHub workflows

A workflow is named `<verb>-<object>`, and its file (`.github/workflows/<name>.yml`), its `name:` and its job id are
that same name, so the checks on a pull request say what each one decides.

| Verb | The workflow | Workflows |
|---|---|---|
| `check` | passes or fails, and changes nothing | `check-code`, `check-pull-request-conventions` |
| `publish` | puts something out of the repository: a tag, a GitHub Release | `publish-release` |

The object is what it checks or publishes, named as the glossary or the convention it enforces names it.
