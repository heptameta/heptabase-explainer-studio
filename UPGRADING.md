# Upgrading

What to change in a series made with an earlier version of Explainer Studio. `explainer-studio upgrade` prints the
sections of the releases it skipped over, and so does the first command on an episode last worked on with an earlier
release. Each step says how to tell whether a series needs it, so applying it to any series again is safe.

Add a step to `## Unreleased` in the change that needs it; a release turns the heading into its version. Earlier
versions read this file after upgrading, so it stays in the package at `explainer_studio/UPGRADING.md` and every
release heading stays `## X.Y.Z`.

## Unreleased

- **Cards before delivery.** `deliver` now refuses an episode without `production/episodes/<episode>/notes.yaml`
  that fits its render: the cards the video page shows as chapters and on the series' whiteboard. A series needs this
  step if an episode in it is not delivered yet. Write that episode's cards as `references/cards.md` says
  (`explainer-studio guide references/cards.md`), alongside its scenes, and check them with `explainer-studio notes
  check <episode>`. Delivered episodes need nothing; write their cards when the user asks for them.
