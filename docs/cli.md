# Command reference

Every `explainer-studio` command with its options, as `explainer-studio <command> --help` prints them. The agent runs
these as the guide says; you rarely need to. `scripts/release.py` generates this page from the commands, so edit their
help in `explainer_studio/cli/`, not here.

<!-- generated:cli begin: edit the source, then run scripts/release.py -->
## `explainer-studio`

```text
explainer-studio [--version] [--series PATH] setup|doctor|guide|plan|script|narrate|preview|render|video|deliver|feedback|gap|notes|cost|asset|dev-mode|upgrade
```

Heptabase Explainer Studio: make narrated explainer videos from teaching materials.

- `--version`: Show the version and exit.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio setup`

```text
explainer-studio setup [blender|narration|playwright]
```

Install what videos need besides Python packages: ffmpeg, LaTeX, fonts and map data, then render a test scene. Per-user,
no password, safe to run again (it repairs and upgrades).

#### `explainer-studio setup blender`

```text
explainer-studio setup blender
```

Install Blender (about 1 GB) for `asset blender render`, unless a recent one is already installed.

#### `explainer-studio setup narration`

```text
explainer-studio setup narration [elevenlabs|openai|voai|macos-say]
```

Choose a narration provider, enter its API key (hidden), test it and save it to credentials.toml.

Run it in your own terminal: the key is typed by you and never shown or passed to the agent.

#### `explainer-studio setup playwright`

```text
explainer-studio setup playwright
```

Install Playwright's Chromium (about 150 MB) for `asset playwright record`.

### `explainer-studio doctor`

```text
explainer-studio doctor [--json]
```

Check what making videos needs, without installing anything. Exits 1 when something required is missing.

- `--json`: Print the checks as JSON.

### `explainer-studio guide`

```text
explainer-studio guide [PATH]
```

Print the guide to making videos with this version, or one of its files (PATH, relative to the guide folder). A folder
lists its files.

### `explainer-studio plan`

```text
explainer-studio plan open|validate
```

Check or open the series plan (production/plan.yaml).

#### `explainer-studio plan open`

```text
explainer-studio plan open [--series PATH] [--no-browser]
```

Validate the plan, start the series page server if needed, and open the plan page in the browser.

- `--series PATH`: The series folder (default: found by walking up from the current folder).
- `--no-browser`: Start the page server and print the URL without opening a browser, to show it in your own pane.

#### `explainer-studio plan validate`

```text
explainer-studio plan validate [--series PATH]
```

Check plan.yaml's format, episode ids and episode folders. Changes nothing.

- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio script`

```text
explainer-studio script prepare-audience-review-prompt|validate
```

Check an episode's script or prepare its audience review.

#### `explainer-studio script prepare-audience-review-prompt`

```text
explainer-studio script prepare-audience-review-prompt EPISODE [--scenes IDS] [--series PATH]
```

Write the script audience review prompt to a file and print its path and the round header.

- `--scenes IDS`: Comma-separated scene ids to review (default: all).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio script validate`

```text
explainer-studio script validate EPISODE [--series PATH]
```

Check script.yaml's format and ids; warn about long lines, a short episode and known misreadings.

- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio narrate`

```text
explainer-studio narrate EPISODE [--beats IDS] [--series PATH]
```

Synthesize the episode's narration with the voice in plan.yaml.

Reuses every beat whose spoken text and voice are unchanged, so it is safe to run again; failed beats are retried on the
next run. Needs a finished script audience review and, for paid voices, an API key and room in the budget.

- `--beats IDS`: Comma-separated beat ids to redo even though their spoken text and voice are unchanged (for example a
  mispronounced line).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio preview`

```text
explainer-studio preview EPISODE [--scenes IDS] [--cover] [--end-credits] [--series PATH]
```

Render scenes (and the cover and end credits) for checking: clip, automatic checks and screenshots per scene.

No narration is needed: beats without current narration last an estimate of their spoken length, silently. With no
options, every scene, the cover (when cover.py exists) and the end credits page (unless plan.yaml turns it off) are
previewed.

- `--scenes IDS`: Comma-separated scene ids (default: every scene).
- `--cover`: Preview the cover (with --scenes: the cover too).
- `--end-credits`: Preview the end credits page (with --scenes: the page too).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio render`

```text
explainer-studio render EPISODE [--series PATH]
```

Render the whole episode at 1080p into render/: video, subtitles, cover, timeline, checks, screenshots.

Every beat must be narrated first. render/ is replaced only when every step succeeds. A five-minute episode takes about
a minute or two; run it in the background when the shell has a short time limit.

- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio video`

```text
explainer-studio video open
```

Open a delivered video's page.

#### `explainer-studio video open`

```text
explainer-studio video open EPISODE [--series PATH] [--no-browser]
```

Open the video page of the episode's latest delivery, where the user watches and comments.

- `--series PATH`: The series folder (default: found by walking up from the current folder).
- `--no-browser`: Start the page server and print the URL without opening a browser, to show it in your own pane.

### `explainer-studio deliver`

```text
explainer-studio deliver EPISODE [--skip-notes-check] [--series PATH]
```

Check the render, its automatic checks and the episode's cards (`notes check`), then move the video, subtitles and cover
to the series folder.

- `--skip-notes-check`: Deliver without checking the episode's cards (notes.yaml), when the user wants none. The video
  page then has no chapters view for it, and the series' whiteboard gets no cards from it.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio feedback`

```text
explainer-studio feedback add|resolve|share
```

Record comments on a delivered episode, resolve them, and share feedback with the team.

#### `explainer-studio feedback add`

```text
explainer-studio feedback add EPISODE TEXT [--at TIME] [--series PATH]
```

Record a comment the user made in chat, on the current video: about the moment --at, or without it about the whole
episode. With --at, also draw its comment screenshot sheet.

- `--at TIME`: The time in the video, as the player shows it (1:23).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio feedback resolve`

```text
explainer-studio feedback resolve EPISODE COMMENT NOTE --category question|teaching|production|direction [--series PATH]
```

Record the category of a comment and what was done about it, with the reason.

- `--category [question|teaching|production|direction]`: question: a learning question; teaching: how it was taught;
  production: how it was made; direction: what the series should do. [required]
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio feedback share`

```text
explainer-studio feedback share EPISODE [--dry-run] [--series PATH]
```

Send the episode's feedback bundle when it has comments, resolutions, survey answers or gaps not shared yet. Only with
the user's agreement.

- `--dry-run`: Print what would be sent, without sending.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio gap`

```text
explainer-studio gap add
```

Record what the product could not do and what was done instead (production/gaps.json).

#### `explainer-studio gap add`

```text
explainer-studio gap add --kind presenter|subject|visual|tool|other --need TEXT --workaround TEXT [--episode EPISODE] [--series PATH]
```

Add a gap. Read gaps.json first: record the same gap only once.

- `--kind [presenter|subject|visual|tool|other]`: What was missing. [required]
- `--episode EPISODE`: The episode it happened in (omit for the whole series).
- `--need TEXT`: What the video needed. [required]
- `--workaround TEXT`: What was used instead. [required]
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio notes`

```text
explainer-studio notes check
```

The delivered episode's chapters and cards (episodes/<episode>/notes.yaml), shown on the video page.

#### `explainer-studio notes check`

```text
explainer-studio notes check EPISODE [--series PATH]
```

Check notes.yaml against the episode's render (or, without one, its latest delivery): every scene once, in order, every
picture it names, and every arrow to a card of this or another episode. deliver checks the same.

- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio cost`

```text
explainer-studio cost show
```

What making the series took: working time, the agent's model calls and tokens, and paid narration.

#### `explainer-studio cost show`

```text
explainer-studio cost show [EPISODE] [--json] [--series PATH]
```

Show the cost of each episode up to its first delivery, step by step, and of planning the series.

Worked out from this computer's Claude Code transcripts (token counts, model settings, times and the commands run, never
what was said) and production/spending.jsonl. Nothing is stored. In dev mode, the agent's usage is also shown in dollars
when the local price table exists (`explainer-studio dev-mode`).

- `--json`: Print the report as JSON (the format in the feedback bundle).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio asset`

```text
explainer-studio asset bioicons|blender|commons|image|owid|pdf|playwright|wikipedia|worldbank
```

Find, fetch and make external material: Commons, Bioicons, portraits, data, PDFs, 3D and screen recordings.

#### `explainer-studio asset bioicons`

```text
explainer-studio asset bioicons download|search
```

Bioicons: about 2,800 free science icons (cells, organs, apparatus, molecules) as SVG.

##### `explainer-studio asset bioicons download`

```text
explainer-studio asset bioicons download ICON [--to PATH] [--series PATH]
```

Download one Bioicons SVG by its name (as a search printed it) and record its credit.

- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

##### `explainer-studio asset bioicons search`

```text
explainer-studio asset bioicons search QUERY [--limit N]
```

Search Bioicons and draw a numbered thumbnail sheet of the matches.

- `--limit N`: [default: 12; 1<=x<=40]

#### `explainer-studio asset blender`

```text
explainer-studio asset blender render
```

3D shots rendered by Blender (needs `explainer-studio setup blender`).

##### `explainer-studio asset blender render`

```text
explainer-studio asset blender render SPEC [--to PATH] [--series PATH]
```

Render a 3D shot from a YAML or JSON spec into <name>.mp4 and <name>.labels.json.

- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio asset commons`

```text
explainer-studio asset commons download|search
```

Wikimedia Commons: paintings, photographs, documents, diagrams, footage, recordings and 3D models.

##### `explainer-studio asset commons download`

```text
explainer-studio asset commons download FILE [--to PATH] [--start TIME] [--end TIME] [--series PATH]
```

Download one Commons file (a File: name or URL) and record its credit.

- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--start TIME`: Video and long audio: where the clip starts (seconds or m:ss).
- `--end TIME`: Video and long audio: where it ends (at most 120 s after --start).
- `--series PATH`: The series folder (default: found by walking up from the current folder).

##### `explainer-studio asset commons search`

```text
explainer-studio asset commons search QUERY [--media-type photo|svg|video|audio|3d] [--limit N]
```

Search Commons for freely licensed files and draw a numbered thumbnail sheet of the candidates.

- `--media-type [photo|svg|video|audio|3d]`: What to look for (default: pictures of any kind).
- `--limit N`: [default: 12; 1<=x<=40]

#### `explainer-studio asset image`

```text
explainer-studio asset image draw-grid
```

Images: positions for marks.

##### `explainer-studio asset image draw-grid`

```text
explainer-studio asset image draw-grid FILE
```

Draw a copy of the image with a labeled line every 10%, to read where to place a mark.

#### `explainer-studio asset owid`

```text
explainer-studio asset owid download
```

Our World in Data charts as CSV.

##### `explainer-studio asset owid download`

```text
explainer-studio asset owid download CHART [--entities ENTITIES] [--years FROM,TO] [--to PATH] [--series PATH]
```

Download a chart's data (the slug in ourworldindata.org/grapher/<slug>) as CSV.

- `--entities ENTITIES`: Comma-separated country names or ISO codes (default: all).
- `--years FROM,TO`: From,to, inclusive, for example 1950,2020.
- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio asset pdf`

```text
explainer-studio asset pdf crop|draw-page-thumbnail-sheets
```

Look at PDF sources and cut figures out of them.

##### `explainer-studio asset pdf crop`

```text
explainer-studio asset pdf crop FILE --page PAGE [--box X0,Y0,X1,Y1] [--dpi DPI] [--to PATH] [--series PATH]
```

Save one PDF page, or a box of it, as a PNG.

Outside a series (while reading the sources, before plan.yaml exists) it goes to `--to`, or to a temporary folder for
your eyes only.

- `--page PAGE`: The PDF page number. [x>=1; required]
- `--box X0,Y0,X1,Y1`: x0,y0,x1,y1 as fractions of the page from the top-left (default: the whole page).
- `--dpi DPI`: [default: 200; 50<=x<=600]
- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

##### `explainer-studio asset pdf draw-page-thumbnail-sheets`

```text
explainer-studio asset pdf draw-page-thumbnail-sheets FILE [--first-page PAGE] [--last-page PAGE]
```

Draw page thumbnail sheets, six pages to a page thumbnail sheet, to find the pages with figures, tables and formulas.

- `--first-page PAGE`: The first page number. [default: 1; x>=1]
- `--last-page PAGE`: The last page number (at most 60 per run). [x>=1]

#### `explainer-studio asset playwright`

```text
explainer-studio asset playwright record
```

Screen recordings of web pages (needs `explainer-studio setup playwright`).

##### `explainer-studio asset playwright record`

```text
explainer-studio asset playwright record SPEC [--to PATH] [--series PATH]
```

Record a scripted walk through a web page into <name>.mp4 and <name>.steps.json.

- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio asset wikipedia`

```text
explainer-studio asset wikipedia download-portrait
```

Wikipedia: portraits of people.

##### `explainer-studio asset wikipedia download-portrait`

```text
explainer-studio asset wikipedia download-portrait ARTICLE [--to PATH] [--language CODE] [--series PATH]
```

Download an article's lead image when Commons says it is public domain or CC0.

- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--language CODE`: Which Wikipedia (en, zh, ja...). Default: zh for CJK titles, else en.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

#### `explainer-studio asset worldbank`

```text
explainer-studio asset worldbank download
```

World Bank indicators as CSV.

##### `explainer-studio asset worldbank download`

```text
explainer-studio asset worldbank download INDICATOR [--entities ENTITIES] [--years FROM,TO] [--to PATH] [--series PATH]
```

Download an indicator (for example NY.GDP.PCAP.CD) as CSV with columns entity, code, year, value.

- `--entities ENTITIES`: Comma-separated country names or ISO codes (default: all).
- `--years FROM,TO`: From,to, inclusive, for example 1950,2020.
- `--to PATH`: Where to save: a folder (for example an episode's assets/) or a file path. Default:
  production/shared/assets/<kind>/.
- `--series PATH`: The series folder (default: found by walking up from the current folder).

### `explainer-studio dev-mode`

```text
explainer-studio dev-mode [on|off]
```

Turn dev mode on or off for this computer, or show whether it is on.

Dev mode is for people improving Explainer Studio: the video page adds how closely you watched, and `deliver` and the
video page show each episode's cost report, with dollars worked out from the local model price table. It never changes
how videos are made. Open pages pick up a change when they reload.

### `explainer-studio upgrade`

```text
explainer-studio upgrade
```

Install the latest release when it is newer than this version, then install what it needs (`setup`). Does nothing on a
dev build. Prints what series made with this version may need to change.
<!-- generated:cli end -->
