# File formats

Contents: [Overview](#overview) · [plan.yaml](#planyaml) · [script.yaml](#scriptyaml) · [design.md](#designmd) ·
[research](#research) · [series-bible.md](#series-biblemd) · [decisions.md](#decisionsmd) ·
[Audience reviews](#audience-reviews) · [Files the tools write](#files-the-tools-write)

The field tables are generated from the package's schemas; the prose and examples explain how to use them.

## Overview

| File | Written by | Strict format |
|---|---|---|
| `production/plan.yaml` | you; the plan page edits single fields | yes |
| `production/series-bible.md` | you | no |
| `production/decisions.md` | you, append only | no |
| `production/research/*.md` | you | no, but required parts (below) |
| `episodes/<episode>/design.md` | you | no |
| `episodes/<episode>/script.yaml` | you | yes |
| `episodes/<episode>/scenes/<scene_id>.py`, `cover.py`, `end_credits.py` | you | Python; one `NarratedScene` subclass per scene file |
| `episodes/<episode>/audience-reviews/script.yaml` | you, from the audience reviewer's reply | yes |
| `narration/`, `preview/`, `render/`, `delivery-records/`, `feedback.json`, `comment-screenshot-sheets/`, `explainer-studio-versions.json`, `gaps.json`, `spending.jsonl`, `credits.yaml` | the CLI | yes; read them, do not edit them (`credits.yaml` may also be added to and shortened by hand) |

Ids (scenes and beats) use lowercase letters, digits and underscores and start with a letter. A scene id is also its
Python file name. Beat ids are unique within an episode.

## plan.yaml

```yaml
title: Linear Algebra from Scratch
sources:
  - sources/notes.pdf
language_code: en                 # the videos' language: zh-TW, en, ...
user_language_code: zh-TW         # optional: the language the user writes in, for the pages (default: language_code)
narration_budget_usd: 20          # omitted: 20; null: no limit; cumulative for the whole series
narration:                        # required by narrate; fields depend on the provider (below)
  provider_name: elevenlabs
  voice_id: JBFqnCBsd6RMkjVDRZzb
  model_id: eleven_v4
background_music:                 # optional; omitted means synthesized-piano; {provider_name: none} turns it off
  provider_name: synthesized-piano
has_end_credits: true             # omitted: true; false: no end credits page (references/rendering/end-credits.md)
audience:
  description: |
    Who the viewer is, what they already picture, where they will get stuck and why, what explanations they like.
    Every judgment has its evidence; guesses are marked as not yet confirmed.
  unfamiliar_terms: [vector, coordinate, matrix]
  misconceptions:                 # only with concrete evidence
    - id: arrows_are_positions
      belief: A vector is the position of a point.
      evidence: The user answered this way in the first probe.
goal: See vector operations and linear maps geometrically.
rationale: |                      # optional: why the episodes are arranged this way
  Addition comes first so episode 2 can explain matrices as transformations.
episodes:
  - id: ep01
    title: Why can vectors be added?
    question: How do two arrows added together stand for two moves in a row?
    question_type: mechanism       # one of the nine (teaching/question-types.md)
    # concept_goal: use            # only for question_type: concept, when the viewer should apply a tool
    presenter_name: theo
    estimated_duration_seconds: 300
    source_scope: Notes chapter 2, PDF pages 8-12.
    taught_terms: [vector, vector addition]
    takeaway: Adding vectors joins two moves end to end.
    outline:
      - Start from two moves on a map.
      - Draw each move as an arrow.
      - Compare tip-to-tail with adding coordinates.
    # language_code: ...           # optional, overrides the series language
    # narration: {...}             # optional, replaces the series narration block entirely
    # background_music: {...}      # optional, replaces the series block entirely
excluded_topics:
  - topic: The axioms of a vector space
    reason: This series builds geometric intuition first.
```

Narration providers and their fields:

| `provider_name` | Fields |
|---|---|
| `elevenlabs` | `voice_id` (required), `model_id`, `voice_settings` |
| `openai` | `model`, `voice`, `instructions`, `speed` |
| `voai` | `version`, `speaker`, `style`, `speed` |
| `macos-say` | `voice`, `words_per_minute` (free, macOS only, mechanical voice: for trying things) |

`taught_terms` and `takeaway` feed the script audience review of later episodes ("what earlier episodes taught").
When the script departs from them, update the plan.

<!-- generated:plan begin: edit the source, then run scripts/release.py -->
**Plan**

| Field | Type | Required |
|---|---|---|
| `title` | text | yes |
| `sources` | list of text | yes |
| `language_code` | text | yes |
| `user_language_code` | text or null | no |
| `narration_budget_usd` | number or null | no |
| `narration` | settings with `provider_name`: `elevenlabs` / `openai` / `voai` / `macos-say` or null | no |
| `background_music` | settings with `provider_name`: `synthesized-piano` / `none` or null | no |
| `has_end_credits` | true / false | no |
| `audience` | Audience | yes |
| `goal` | text | yes |
| `rationale` | text or null | no |
| `episodes` | list of Episode | yes |
| `excluded_topics` | list of ExcludedTopic | no |

**Audience**

| Field | Type | Required |
|---|---|---|
| `description` | text | yes |
| `unfamiliar_terms` | list of text | no |
| `misconceptions` | list of Misconception | no |

**Misconception**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `belief` | text | yes |
| `evidence` | text | yes |

**Episode**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `title` | text | yes |
| `question` | text | yes |
| `question_type` | text | yes |
| `concept_goal` | text or null | no |
| `presenter_name` | text | yes |
| `outline` | list of text | yes |
| `estimated_duration_seconds` | integer | yes |
| `taught_terms` | list of text | yes |
| `takeaway` | text | yes |
| `source_scope` | text or null | no |
| `language_code` | text or null | no |
| `narration` | settings with `provider_name`: `elevenlabs` / `openai` / `voai` / `macos-say` or null | no |
| `background_music` | settings with `provider_name`: `synthesized-piano` / `none` or null | no |

**ExcludedTopic**

| Field | Type | Required |
|---|---|---|
| `topic` | text | yes |
| `reason` | text | yes |
<!-- generated:plan end -->

## script.yaml

```yaml
scenes:
  - id: dam
    purpose: Build the familiar dam first; energy sits in a height difference and only comes out through the wheel.
    beats:
      - id: water_levels
        narration_text: Let's leave the cell for a moment and picture a dam. The water is high on the left and low on the right.
        visual: Fade out the cell. A dam stands in the middle; the water is high on the left, low on the right.
      - id: flow_direction
        narration_text: With one side high and the other low, the water wants to flow from high to low.
        visual: A small arrow pointing right appears above the left water surface.
        pause_duration_seconds: 1       # silence after this beat
        citation: Molecular Biology of the Cell, ch. 14, p. 753
      - id: sigma
        narration_text: The spread is σ².
        visual: ...
        spoken_text_override: The spread is sigma squared.   # when the automatic rewrite is not enough
```

- `narration_text` is what the beat says, and what its subtitle shows. Before synthesis it is rewritten into the
  spoken text automatically (Greek letters by name, ² and ³, minus signs, and forms the narration language reads its
  own way, such as years). Set `spoken_text_override` only when that is not enough: the voice reads it instead, and
  the subtitle keeps the narration text.
- A sound in the middle of the narration: describe it in `visual` and leave time with `pause_duration_seconds`; the
  scene code plays it (`references/rendering/sound.md`).
- The episode id and title come from the folder and the plan; the real duration comes from narration and render.

<!-- generated:script begin: edit the source, then run scripts/release.py -->
**Script**

| Field | Type | Required |
|---|---|---|
| `scenes` | list of Scene | yes |

**Scene**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `purpose` | text | yes |
| `beats` | list of Beat | yes |

**Beat**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `narration_text` | text | yes |
| `visual` | text | yes |
| `pause_duration_seconds` | number or null | no |
| `citation` | text or null | no |
| `spoken_text_override` | text or null | no |
<!-- generated:script end -->

## design.md

Free-form thinking for one episode; no program reads it and the audience reviewer never sees it. Think through:
the opening question; the aha moment; the central image; the takeaway's aspects (when it applies, what it is
mistaken for, its limits); the promises you make and where you keep them; where each unfamiliar term is taught and
how; where each misconception is handled and how; a transfer check (a case the video does not show: can the viewer
reason about it?); your self-check against the question type's must-haves and the presenter's playbook.

## research

Markdown notes from the deep reading, in `production/research/`. They must contain:

1. **Coverage list**: every argument, example, person, number and quotation in the scope, with its location.
2. **Question map**: each question the sources answer, its question type, where it comes from, what it needs
   first, and whether this viewer already knows it. A question with "and" in it is usually two questions.
3. **To verify**: facts and legends to check, marked verified or open. Nothing open may reach the script.

Also the core claim of the sources, the causal chains of their key steps, and three or more candidate angles (aha moment,
the familiar "standard account" to push against, a central object) with the one you chose and why.

## series-bible.md

What must stay consistent across the series. Read it before writing any script or scene.

```markdown
# <series title>: series bible

## Audience and tone
## Concept colours   (fixed for the whole series; new concepts take unused colours)
| Concept | Colour | Hex |
## Recurring devices   (the questioner, a map that returns, ...)
## Terms and names   (translations used everywhere: subtitles, labels, narration)
| Original | Used in this series |
## Episode format   (cover, opening, closing)
```

## decisions.md

Append a dated line for every choice you made without asking: a colour, a translation, a supplement beyond the
sources, a departure from the plan, and why.

## Audience reviews

`script prepare-audience-review-prompt` prints a round header. Append it with the audience reviewer's reply to the
episode's `audience-reviews/script.yaml`, then add a `resolution` to every finding.

```yaml
# audience-reviews/script.yaml
rounds:
  - scene_ids: [hook, dam, membrane]
    reviewer_summary:               # the reviewer writes this
      question: How does the cell use the proton difference across its membrane?
      takeaway: The cell runs a motor on the proton difference.
      explained_terms: [cell membrane, proton]
      lost_beat_id: hole_reveal       # null when never lost
      most_engaging_beat_id: dam_intro
    findings:
      - scene_id: membrane            # the scene the beat was in when it was read
        beat_id: hole_reveal
        kind: lost                    # lost / wrong / minor
        problem: The pump works, so why can't the difference hold?
        resolution:                   # you write this
          action: fixed               # fixed / kept
          note: Added a beat: the pumped protons leak straight back through the hole.
```

<!-- generated:audience-reviews begin: edit the source, then run scripts/release.py -->
**ScriptRound**

| Field | Type | Required |
|---|---|---|
| `scene_ids` | list of text | yes |
| `reviewer_summary` | ReviewerSummary or null | no |
| `findings` | list of ScriptFinding | no |

**ReviewerSummary**

| Field | Type | Required |
|---|---|---|
| `question` | text | yes |
| `takeaway` | text | yes |
| `explained_terms` | list of text | no |
| `lost_beat_id` | text or null | no |
| `most_engaging_beat_id` | text or null | no |

**ScriptFinding**

| Field | Type | Required |
|---|---|---|
| `scene_id` | text | yes |
| `beat_id` | text | yes |
| `kind` | `lost` / `wrong` / `minor` | yes |
| `problem` | text | yes |
| `resolution` | FindingResolution or null | no |

**FindingResolution**

| Field | Type | Required |
|---|---|---|
| `action` | `fixed` / `kept` | yes |
| `note` | text | no |
<!-- generated:audience-reviews end -->

## Files the tools write

Read these; do not edit them.

**`narration/narration.yaml`**: the narration's receipt: the narration settings its audio was made with and, per
beat, the spoken text the voice read and the duration. `narrate` reuses a beat's audio while its spoken text and the
settings stay the same, so editing only a narration text that reads the same costs nothing.

<!-- generated:narration begin: edit the source, then run scripts/release.py -->
**NarrationRecord**

| Field | Type | Required |
|---|---|---|
| `settings` | settings with `provider_name`: `elevenlabs` / `openai` / `voai` / `macos-say` | yes |
| `beats` | list of NarratedBeat | no |

**NarratedBeat**

| Field | Type | Required |
|---|---|---|
| `beat_id` | text | yes |
| `spoken_text` | text | yes |
| `duration_seconds` | number | yes |
<!-- generated:narration end -->

**`render/timeline.json`**: where every scene, beat and sound sits in the final video, cover included (the first
second) and end credits included (the last `end_credits_duration_seconds`, 0 when the plan turns them off). Use it to find the line at a time, for example for a comment at 1:23. A sound's `sound` says what plays: a
built-in effect (`{kind: effect, effect_name}`) or a file by its path relative to `production/`
(`{kind: file, source_file_path, source_start_seconds}`).

<!-- generated:timeline begin: edit the source, then run scripts/release.py -->
**Timeline**

| Field | Type | Required |
|---|---|---|
| `narration_digest` | text | yes |
| `duration_seconds` | number | yes |
| `cover_duration_seconds` | number | no |
| `end_credits_duration_seconds` | number | no |
| `scenes` | list of TimelineScene | no |
| `sounds` | list of TimelineSound | no |

**TimelineScene**

| Field | Type | Required |
|---|---|---|
| `scene_id` | text | yes |
| `start_seconds` | number | yes |
| `duration_seconds` | number | yes |
| `beats` | list of TimelineBeat | no |

**TimelineBeat**

| Field | Type | Required |
|---|---|---|
| `beat_id` | text | yes |
| `start_seconds` | number | yes |
| `duration_seconds` | number | yes |

**TimelineSound**

| Field | Type | Required |
|---|---|---|
| `start_seconds` | number | yes |
| `sound` | TimelineSoundEffect or TimelineSoundFile | yes |
| `duration_seconds` | number | yes |
| `gain_decibels` | number | no |
| `should_duck_background_music` | true / false | yes |

**TimelineSoundEffect**

| Field | Type | Required |
|---|---|---|
| `kind` | `effect` | yes |
| `effect_name` | `whoosh_in` / `whoosh_out` / `ghost` / `questioner` / `bubble` / `title` | yes |

**TimelineSoundFile**

| Field | Type | Required |
|---|---|---|
| `kind` | `file` | yes |
| `source_file_path` | text | yes |
| `source_start_seconds` | number | no |
<!-- generated:timeline end -->

**`automatic-checks.json`** (in `preview/<scene>/` and `render/`):
`{"issues": [{check_name, scene_id, beat_id, detail}]}`, always written, empty when nothing was found. Checks:
`text_too_small` (blocks delivery), `text_overlap`, `text_outside_frame`, `outside_container`.

**`feedback.json`**: comments and survey answers across deliveries. A comment's `anchor` says what it is about: a
moment of the video (`{kind: moment, time_seconds}`) or the whole episode (`{kind: episode}`). A resolution's
categories: `question` (a learning question), `teaching` (how it was taught), `production` (how it was made),
`direction` (what the video should be). The survey is the fixed questions the video page asks about the delivered
video; an answer's `kind` is `rating` (good, okay or bad) or `watch_depth` (how closely the person watched: closely,
skimmed or partly; the video page asks in dev mode). Which video an item is about follows from its time: a comment or
answer given before the latest delivery's `delivered_at` is about an older video. The current video's answer of a kind
is the latest one given since the latest delivery (answering again replaces it). What was said at a comment's moment is
in the delivery record in effect at its `created_at`: the latest one delivered at or before it. `id` is the feedback
id, a UUID v4 that goes with every feedback bundle of the episode; a `shared_at` records the bundle that first carried
the item as it is now (a changed comment or answer is unshared again).

**`episodes/<episode>/comment-screenshot-sheets/<comment id>.jpg`**: the comment screenshot sheet of a comment about a
moment: six frames, every 2 seconds from 8 seconds before the moment to 2 seconds after, the one nearest the moment
outlined. Drawn from the video in the series folder when the comment is made; when its moment changes, drawn again if
the comment is on the current video and removed if it is on an older one; deleted with the comment.

<!-- generated:feedback begin: edit the source, then run scripts/release.py -->
**Feedback**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `last_comment_number` | integer | no |
| `comments` | list of Comment | no |
| `survey_answers` | list of RatingAnswer or WatchDepthAnswer | no |

**Comment**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `anchor` | MomentAnchor or EpisodeAnchor | yes |
| `text` | text | yes |
| `origin` | `page` / `chat` | yes |
| `created_at` | time with UTC offset | yes |
| `shared_at` | time with UTC offset or null | no |
| `resolution` | Resolution or null | no |

**MomentAnchor**

| Field | Type | Required |
|---|---|---|
| `kind` | `moment` | yes |
| `time_seconds` | number | yes |

**EpisodeAnchor**

| Field | Type | Required |
|---|---|---|
| `kind` | `episode` | yes |

**Resolution**

| Field | Type | Required |
|---|---|---|
| `category` | `question` / `teaching` / `production` / `direction` | yes |
| `note` | text | yes |
| `resolved_at` | time with UTC offset | yes |
| `shared_at` | time with UTC offset or null | no |

**RatingAnswer**

| Field | Type | Required |
|---|---|---|
| `kind` | `rating` | yes |
| `value` | `good` / `okay` / `bad` | yes |
| `answered_at` | time with UTC offset | yes |
| `shared_at` | time with UTC offset or null | no |

**WatchDepthAnswer**

| Field | Type | Required |
|---|---|---|
| `kind` | `watch_depth` | yes |
| `value` | `closely` / `skimmed` / `partly` | yes |
| `answered_at` | time with UTC offset | yes |
| `shared_at` | time with UTC offset or null | no |
<!-- generated:feedback end -->

**`gaps.json`**: what the product could not do (`gap add`). Append-only.

<!-- generated:gaps begin: edit the source, then run scripts/release.py -->
**Gap**

| Field | Type | Required |
|---|---|---|
| `id` | text | yes |
| `kind` | `presenter` / `subject` / `visual` / `tool` / `other` | yes |
| `episode_id` | text or null | no |
| `need` | text | yes |
| `workaround` | text | yes |
| `created_at` | time with UTC offset | yes |
| `shared_at` | time with UTC offset or null | no |
<!-- generated:gaps end -->

**`credits.yaml`**: where external assets came from, as a list under `credits`; the `asset` commands append to it.
Add an entry by hand for an asset you obtained another way. The credits component in scene code reads it.

<!-- generated:credits begin: edit the source, then run scripts/release.py -->
**Credits**

| Field | Type | Required |
|---|---|---|
| `credits` | list of Credit | no |

**Credit**

| Field | Type | Required |
|---|---|---|
| `asset_file_path` | text | yes |
| `title` | text | yes |
| `author` | text or null | no |
| `license` | text | yes |
| `license_url` | text or null | no |
| `source_url` | text | yes |
| `downloaded_at` | time with UTC offset | yes |
<!-- generated:credits end -->

**`spending.jsonl`**: one line per paid call:
`{kind, spent_at, episode_id, provider_name, character_count, cost_usd, is_estimated}`. `kind` says what was paid for;
today every record is `narration`, and the narration budget sums them.

**`delivery-records/<delivered time>/`**: one delivery record per delivery, kept forever: `metadata.json`
(`delivered_at`, `explainer_studio_version`, `earlier_explainer_studio_versions`, `files` with `video_file_name`,
`cover_file_name` and `subtitles`, a list of `{language_code, file_name}` with one subtitle file per language, named
`<NN>-<title>.<language code>.srt`; today one, in the episode's language), plus the `timeline.json` and `script.yaml` of
that delivery. The folder is named by the UTC delivered time, such as `2026-10-06T140211Z`, so the folders sort in
delivery order; `delivered_at` gives the time in the user's local time. The video in the series folder is the newest
record's. `earlier_explainer_studio_versions` lists the other Explainer Studio versions used on the episode since the
previous delivery (empty when the version did not change).

**`episodes/<episode>/explainer-studio-versions.json`**: `last_used_version` (the version of the latest command on the
episode that makes its video) and `versions_since_last_delivery`, kept by the commands that make the video: the
`script` commands, `narrate`, `preview`, `render`, `deliver` and `gap add`. Commands that only look at the video or
record feedback on it leave it alone.
