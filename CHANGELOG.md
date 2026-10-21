# Changelog

All notable changes to Explainer Studio are in this file, in the format of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). What a series made with an earlier version must change is
in [UPGRADING.md](UPGRADING.md).

## [Unreleased]

## [1.2.0] - 2026-10-21

### Added

- The video page has **Chapters**, which reads the episode from top to bottom: each chapter a large frame beside its
  scenes, with their key frames and core ideas. Choosing a scene plays it in its chapter's frame.
- **Whiteboard** shows every delivered episode's cards on one whiteboard for the series, drawn by Heptabase, with arrows
  between the cards, also across episodes. **Save to Heptabase** puts it in the user's own Heptabase after a one-time
  sign-in; each episode delivered later is added to it when its video page opens.
- The agent writes each episode's cards in `notes.yaml` while it makes the episode, and `deliver` checks them against
  the render (`explainer-studio notes check`); `deliver --skip-notes-check` delivers an episode without cards.
- When Heptabase answers that this version of Studio is too old for it, the whiteboard asks the user to update
  Explainer Studio.

### Changed

- `render` adds no background music unless the plan asks for it: set `background_music: {provider_name:
  synthesized-piano}` in `plan.yaml` to keep the piano. A series that never set it renders without music from now on.
- The video page keeps its mode in its address (`?mode=chapters`), so a reload, Back or a new tab shows the same
  screen; a page opened by `video open` starts with none on.

### Fixed

- The video page's keys work with Zhuyin and other input methods on.
- The video page's keys work after a click in the whiteboard, and **Restore** on a trashed whiteboard opens it in
  Heptabase.

## [1.1.1] - 2026-10-16

### Fixed

- A narration line no longer leaves a low hum between sentences. Some voices keep up to a second of rumble after a
  line's last word, which the mix made audible and then cut off when the next line began; the pause after the last
  word now fades to silence. Timing does not change and no narration is redone: render the episode again.

## [1.1.0] - 2026-10-16

### Added

- Before the first question, the agent tells a learner (the videos are for them) from a teacher (an author or teacher
  making videos for others), asking when the request does not say. A teacher is asked about their viewers, never
  tested on their own material. The user then chooses how many questions to answer: none, 2, the usual 4 to 6, or up
  to 9, told that each answer makes the videos fit better.

### Fixed

- The agent asks every question in the language the user writes in, options and quoted passages included: the guide
  said to quote the sources' sentences exactly, so a user writing Chinese about an English book was asked in English.
  The plan's new `user_language_code` keeps the plan and video pages in the user's language when the videos are in
  another.
- The agent picks an episode's question type by what the viewer takes away, not by how the question is worded, so an
  episode about how an idea was replaced is no longer told as a mechanism. When writing the script changes the
  takeaway, it picks the type again and replans the episode with that type's playbook.
- A distinction the viewer lacks and a story rests on goes into the plan as a concept question of its own, taught before
  the story uses it, often as its own episode by a presenter who teaches concepts. Such an episode picks up where the
  series stopped, uses the series' own examples and hands back to it. Each episode's outline now ends on its own answer:
  what undoes that answer waits for the episode about it.
- A script audience review finding that says the reasoning is missing something (a premise, what a piece of evidence
  is for, a reminder, one case of what a claim means) is fixed with its own beat even when it is marked minor, instead
  of being kept because a minor fix may not add a sentence. The reviewer counts a skipped causal step the reasoning
  depends on as a place it is lost.
- Theo's recaps, slogans, key-point labels and closes name the episode's concrete things instead of sounding like a
  summary through wordplay alone. A key-point label says its idea, and the first says how many there are, so "the
  second key idea" minutes later no longer leaves the viewer wondering what the first was. The script audience review
  counts an empty summary line, or a numbered label whose earlier members the viewer cannot name, as a place the
  viewer is lost.
- A dot sent along wires stays on them after the drawing moves or shrinks, an arrow spun in place stays in place, and an
  arc that should sweep out no longer swells out of a dot: the scene code guide says to move the path with the
  drawing, to rotate about the shape's own centre (for a curved arrow, `arrow.arc.get_arc_center()`) and to sweep
  with `ShowCreation` or an updater, and the screenshot check looks for these.
- Picking letters out of text in the code font (`text[8:10]`) picks the letters named: the font no longer joins "//"
  into one glyph, which moved every letter after it one place, so a web address had the wrong letters highlighted.
- An end credits page with more assets than fit at full size groups those with the same author and licence into one
  row ("… and 371 more") instead of shrinking the whole list into an unreadable sliver.

## [1.0.0] - 2026-10-14

The first public release.

### Added

- Your coding agent turns lecture notes, a book chapter, a paper, a design document or a codebase into a series of
  narrated, animated explainer episodes, each answering one question. Explainer Studio renders them on your computer
  with ManimGL.
- Five presenters, each with its own way of explaining: Theo (step-by-step derivation), Fabian (small-world
  simulation), Mason (hands-on workshop), Sophie (case-based reasoning) and Clio (historical storytelling).
- The plan page shows the series before anything is made. On the video page, press M where you got lost, and the agent
  makes the next version from your comments.
- Narration with your own ElevenLabs, OpenAI or VoAI key, or the free built-in voice on macOS. English and Traditional
  Chinese (Taiwan) have their own guides to spoken style, subtitles and fonts.
