---
name: releasing
description: How an Explainer Studio release is decided, prepared in a release pull request, and published by CI. Use when deciding whether to release, releasing a version, or checking a release afterwards.
---

# Releasing

A release is the tag `v<version>` on `main` and its GitHub Release. Every user's `explainer-studio upgrade` installs
the latest release before their next series or episode, without asking them, so a release reaches everyone within a
day. The skill in the Heptabase plugin installs whichever release is the latest, so a release changes nothing there.

## When

Releases are batched. Merged changes run as dev builds first; a release goes out when there is an improvement worth
telling users about and the videos made meanwhile show no regression. A fix for a tool error that stops videos from
being made goes out at once.

The version raises the patch number for fixes and the minor number when how videos are made changes.

## The release pull request

1. From the latest `main`, on a branch `release-X.Y.Z`: `uv run python scripts/release.py --version X.Y.Z`. It sets
   the version in `pyproject.toml` and moves the items under `## [Unreleased]` in `CHANGELOG.md` (and the steps under
   `## Unreleased` in `UPGRADING.md`, if any) under the new version's heading. It also updates `uv.lock`, which
   records the version.
2. Edit the new CHANGELOG section for users: most important first in each category, one entry per change a user or
   agent would notice, merged where several pull requests made one change. Check that every UPGRADING step says how
   to tell whether a series needs it.
3. Run the commands in `AGENTS.md`, commit `chore: release X.Y.Z`, and open the pull request with that title and the
   CHANGELOG section as its description. The `check-pull-request-conventions` workflow fails a pull request that
   changes the version without that title, or to a version that is not higher than the latest release, or without
   its CHANGELOG section.
4. A maintainer squash-merges it. The `publish-release` workflow then tags the merged commit `vX.Y.Z` and publishes the GitHub
   Release with the CHANGELOG section as its notes. Merge nothing else before the tag exists: the workflow run of a
   later merge could tag that merge's commit instead.

## After the release

`gh release view vX.Y.Z` shows the release. On a computer that runs the previous release, `explainer-studio upgrade`
installs it; on one that runs a dev build, `uv run python scripts/use_release.py` does.
