# Writing scenes in parallel

Contents: [When](#when) · [Before dispatching](#before-dispatching) · [The shared brief](#the-shared-brief) ·
[Seams between scenes](#seams-between-scenes) · [Afterwards](#afterwards) · [Lessons from large productions](#lessons-from-large-productions)

Scene files are independent (one scene, one file, one `NarratedScene`), so the scenes of an episode can be written by
parallel subagents, one scene each (or a few consecutive scenes each). You are the lead: you prepare, dispatch, check
and fix.

## When

- Only after the script has passed the script audience review. A scene whose script is still going back and forth with
  the audience reviewers is not sent out: get the script understood first. (One subagent drawing a derivation once
  received twelve script changes and redrew it each time.)
- Narration can run at the same time: once the review is done, the narration does not change. Scenes previewed before
  narration use estimated timing; preview them again once `narrate` has finished.
- Scenes of several episodes can be written at once the same way; each still follows its own reviewed script.

## Before dispatching

- Write the shared code yourself, in `production/shared/`: the series' colours, recurring devices and builders that
  several scenes use. Give each builder parameters that rebuild any state a scene needs (`get_foundation(cracked=True,
  filled=False)`). Preview something built with it before anyone depends on it.
- Make the first one or two scenes yourself (typically the hook and the first seam), preview them and fix them. They
  are the template the subagents copy: imports, timing, sizes, how the frame clears.
- Write the hand-over state between consecutive scenes into the brief ([seams](#seams-between-scenes)).

## The shared brief

Write one brief for all subagents in your own scratch folder, never in the series folder. Then start each subagent
with the brief plus its own part: which scene ids it writes, and the real sources that scene shows (the files and
lines, the figures, the data). The brief contains:

- **Where:** the series folder, the episode, the path of `script.yaml`, that each scene file is
  `episodes/<episode>/scenes/<scene_id>.py`, and the installed `scene_kit` folder, where a component's full signature
  and docstring are.
- **What to read first:** `production/series-bible.md`, every file in `production/shared/`, the finished template
  scene, the rendering references (`references/rendering/scene-code.md` and `components.md`, plus `assets.md` or
  `sound.md` when the scene needs them), and the visual rules (`references/teaching/visual.md`).
- **Rules that matter most:**
  - Real content on screen (code, configuration, logs, documents, data) is read from the source with
    `read_file_excerpt` or `read_csv`; never typed or invented.
  - One `play_beat` block per beat, in script order; the scripted pauses come from the script, not from `self.wait`.
  - Guess beats keep their options on screen through the pause; conclusions stay on screen through theirs.
  - Text at least the minimum size; at most three groups of things in a frame; labels never on lines.
  - The scene starts from an empty frame and ends by fading to one.
- **How to check:** `explainer-studio preview <episode> --scenes <scene_id>`, open every screenshot it lists (`every-2s`
  and `by-beat`), fix every automatic check issue, preview again. A scene is not done until its screenshots were
  looked at. Several subagents previewing at once is safe, only slower.
- **Do not touch:** `script.yaml`, `plan.yaml`, `series-bible.md`, anything in `production/shared/`, other subagents'
  scene files, `cover.py` and `end_credits.py` (unless assigned), and the commands that spend money or change the episode: `narrate`,
  `render`, `deliver`. When shared code needs a change, report it instead of working around it.
- **Scratch files:** each subagent keeps its scratch scripts and logs in its own subfolder; shared scratch folders get
  overwritten.
- **What to report:** for each beat, how it is drawn; every place where the real source differs from what the script
  describes; anything it needed from shared code; anything the components could not draw (and what it used instead).

## Seams between scenes

- Every scene starts from an empty frame and ends by fading to an empty frame, so subagents never need to match each
  other's last frame.
- When a scene must pick up where the previous one ended (the same diagram, now with one block lit), the brief says
  exactly what that state is, and the later scene rebuilds it from the shared builder at the start.
- State that crosses episodes (the kite string is taut at the end of episode 1, so episode 2 starts with it taut) is
  fixed in the series bible before any of those scenes is written. Check it at every hand-over.

## Afterwards

- Preview the whole episode (`explainer-studio preview <episode>`) and look at every screenshot sheet yourself: seams,
  repeated pictures, colours and terms that drifted between scenes, pictures that do not match the script.
- When a subagent reports that the real source differs from the script, correct the script or the picture to match
  the source; never draw what the script says instead of what is true.
- After `render`, look at its screenshots yourself. Do not send what you find back to the subagents that wrote the
  scenes: their contexts are long and stale, and every return reloads all of it. Fix small things yourself. For larger
  ones, start a new subagent per scene file with only that file, what to fix in it and the shared brief.
- Changes to shared code are yours: make the change, preview the scenes that use it, and tell any subagent still
  working.

## Lessons from large productions

- A 74-page chapter made into six episodes had two scene writers per episode working in parallel, twelve in all.
  The lead wrote the shared code and the template scenes first, then checked every episode's screenshots and unified
  colours and translations across episodes (one episode had coloured a sphere red, which the series used for "wrong").
- When a script splits a long scene into sub-scenes, each is its own scene id and file; scene writers keep the ids
  exactly as the script has them.
- A library of shared devices written early and tested with previews is what lets scenes from different writers meet
  at the seams. When a writer finds a problem in it, the lead fixes the library and tells everyone; writers working
  around it each in their own way is how seams break.
