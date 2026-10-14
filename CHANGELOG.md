# Changelog

All notable changes to Explainer Studio are in this file, in the format of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). What a series made with an earlier version must change is
in [UPGRADING.md](UPGRADING.md).

## [Unreleased]

### Fixed

- The agent picks an episode's question type by what the viewer takes away, not by how the question is worded, so an
  episode about how an idea was replaced is no longer told as a mechanism. When writing the script changes the
  takeaway, it picks the type again and replans the episode with that type's playbook.
- A distinction the viewer lacks and a story rests on goes into the plan as a concept question of its own, taught before
  the story uses it, often as its own episode by a presenter who teaches concepts. Such an episode picks up where the
  series stopped, uses the series' own examples and hands back to it. Each episode's outline now ends on its own answer:
  what undoes that answer waits for the episode about it.

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
