---
name: commit-and-pull-request-convention
description: How Explainer Studio commits and pull requests are written, covering branches, Conventional Commits subjects, sign-offs, the changelog, and pull request titles and descriptions. Use before committing, pushing a branch, or opening or merging a pull request in this repository.
---

# Commits and pull requests

A pull request is squash-merged: one change becomes one commit on `main`. Its subject is the pull request title, and
its body is the messages of the pull request's commits (the repository's squash settings). Write both as if they will
be read by someone who never saw the conversation. The `check-pull-request-conventions` workflow checks the title, the changelog entry
and the sign-offs.

## Branches

- Work on a branch from `main` and commit locally as you go.
- Push only when the branch is ready for review: squash the work-in-progress commits into the ones a reviewer should
  read (usually one, whose message is the one `main` should get), and run the commands in `AGENTS.md` first.
- Nothing private enters the repository, in code, commit messages or pull requests: names of people, private
  materials, users' feedback, local paths.

## Commit messages

- **Subject:** [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), `<type>: <sentence>`, no scope.
  The sentence is English in the imperative (it completes "this commit will ..."), starts lowercase, has no trailing
  period, and says what changes for the user or the agent. Add the reason after a comma when it is not obvious.
- **Type:**

  | Type | When |
  |---|---|
  | `feat` | a user or the agent can do something they could not before |
  | `fix` | something that should already have worked now does |
  | `refactor` | the code changes and nothing anyone sees does |
  | `docs` | documentation and conventions for developers |
  | `test` | tests only |
  | `ci` | the workflows |
  | `chore` | anything else, such as a release |

  ```text
  feat: let a video page comment be about the whole episode
  fix: count a subagent's work in the step it is doing
  feat: install the plugin from the release tag, so a new install between releases gets the release
  refactor: move the skill's references into the package as the guide
  chore: release 0.2.0
  ```

  Not `feat: added theater mode` (past tense), `fix: theater mode bug` (no verb), `chore: update stuff` (says
  nothing), or `fix: edit upgrade.py and guide.md` (files, not the change).
- **Body,** when the subject is not enough: prose wrapped at 120 columns that says what was wrong or missing and what
  happens now. Not a list of the files edited, and not the story of how the fix was found.
- Use the glossary's terms and the code's names. Name every CLI command, file format field and scene_kit function
  that changes, since agents, scene files and series folders depend on them; for a sweeping rename, name the kinds of
  change with examples and say where the full list is.
- **Trailers:** every commit is signed off (`git commit -s`; see `CONTRIBUTING.md`). A commit an agent wrote also has
  the agent's `Co-Authored-By:` trailer. A maintainer who writes the squash message by hand keeps the `Signed-off-by:`
  lines at its end.

## Changelog

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the release notes are made from
it, so it is written in the pull requests rather than at release time.

- A `feat` or `fix` adds an entry under `## [Unreleased]`, in its category: Added, Changed, Deprecated, Removed, Fixed
  or Security. Write it for a user: what is different for them, not how the code changed. Other types get no entry;
  a change a user or the agent would notice is a `feat` or a `fix`.
- A change that existing series must follow adds a step under `## Unreleased` in `UPGRADING.md`, as its introduction
  says.
- Only a release pull request adds a version heading ([`releasing`](../releasing/SKILL.md)).

## Pull requests

- **Title:** the subject `main` should get, in the format above.
- **Description:** written for the reviewer deciding whether to merge, and for whoever later follows the commit back
  to it. Up to four sections, each answering one question, in this order:

  | Section | Answers | Holds |
  |---|---|---|
  | `## Why` | Is the problem worth solving? | what was wrong or missing |
  | `## What changes` | Is this the right change, and where to look? | what is different for a user or the agent: commands, file formats, rules |
  | `## Trade-offs` | Is the price acceptable? | what gets worse, what was given up, the alternative not taken |
  | `## Verification` | Is the risk acceptable? | what was checked beyond CI, what is still unchecked, what to watch for |

  Why and What changes are always there. Leave Trade-offs out when nothing was given up, and Verification out when CI
  is all there is; never fill a section for its own sake. A change to teaching behaviour adds what
  [`judging-changes`](../judging-changes/SKILL.md) asks for to these sections.
- **What changes** opens with one or two sentences that say what the change is as a whole; a single change ends
  there. Several separate changes follow as one level of bullets, each starting with the bold name of the thing that
  changes (a command, a file, a rule) and one sentence on how. Items that share attributes go in a table. No file
  lists, no nested bullets, and no order of implementation.
- The description ends with the agent's generated-with line when an agent wrote it.
- A maintainer reviews and merges.

An example (an engine change):

```markdown
## Why

Users install from a store listing and never update plugins, so most would keep the version they first installed.

## What changes

`explainer-studio upgrade` installs the latest release when it is newer, and the guide has the agent run it before
each series and episode, without asking the user.

- **`doctor`** shows a newer release as `latest_release`.
- **The install scripts** install the latest release instead of a version written into them.
- **`UPGRADING.md`** says what existing series must change; `upgrade` prints the steps of the releases it skipped.

## Trade-offs

The upgrade is silent, so a regression reaches every user within a day. Releases are batched and run as dev builds
first to make up for it.

## Verification

Not run: an actual upgrade install. The first release after this one is the test.
```
