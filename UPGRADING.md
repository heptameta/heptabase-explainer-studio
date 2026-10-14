# Upgrading

What to change in a series made with an earlier version of Explainer Studio. `explainer-studio upgrade` prints the
sections of the releases it skipped over, and so does the first command on an episode last worked on with an earlier
release. Each step says how to tell whether a series needs it, so applying it to any series again is safe.

Add a step to `## Unreleased` in the change that needs it; a release turns the heading into its version. Earlier
versions read this file after upgrading, so it stays in the package at `explainer_studio/UPGRADING.md` and every
release heading stays `## X.Y.Z`.

## Unreleased
