# Contributing

Thank you for helping make explainer videos better. The easiest way in is your coding agent: open this repository in
Claude Code and describe the change. It follows [AGENTS.md](AGENTS.md) and the conventions in `.claude/skills/`, the
same ones this page points to.

## What to contribute

- **Fixes to the engine and tools:** a mispronounced word, text too small, a broken picture, a command that fails. Send
  the fix and, when the behaviour can regress, a test.
- **A language:** narration in a language Explainer Studio does not yet know well. Its rules (speaking rate, sentence
  length, how to say numbers and formulas) go in a language reference, `explainer_studio/guide/references/languages/`,
  and its limits in `explainer_studio/languages.py`; the pages' wording is in `explainer_studio/web/locales/`.
- **Teaching:** how the viewer is known, how a series is planned, the shared rules, a presenter's craft or a playbook.
  These change every video that uses them, so they need evidence: the same cause in videos made from two different
  sources. Read [judging-changes](.claude/skills/judging-changes/SKILL.md) before you start.

For anything larger than a fix, say what you have in mind on [Discord](https://discord.com/invite/KAkXjPX8Yn) or in an
issue first, so no one spends days on a change that does not fit.

## Making a change

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest -m "not render and not network"   # the fast tests, as CI runs them
```

Work on a branch from `main`. To try the change for real, install the Heptabase plugin as the
[README](README.md#install) says, then install your change as a dev build: `uv run python scripts/use_dev_build.py`
makes every chat on your computer use the command from your branch's latest commit, and
`uv run python scripts/use_release.py` goes back to the release. Then make an episode with it, as a user would. The
other commands to run before sending are in [AGENTS.md](AGENTS.md#commands).

The skill that installs the command is in the Heptabase plugin. Send changes to it to
[heptameta/heptabase-agent-plugins](https://github.com/heptameta/heptabase-agent-plugins).

## Sending a pull request

Follow the [commit and pull request convention](.claude/skills/commit-and-pull-request-convention/SKILL.md):

- **Title** in [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) form, which becomes the commit
  on `main`: `fix: keep the subtitles on after the video page reloads`.
- **Description** in up to four sections: Why, What changes, Trade-offs and Verification. A teaching change adds what
  judging-changes asks for: its evidence and its trade-offs in quality, cost and time, and rule complexity.
- **Changelog:** a `feat` or `fix` adds an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md), written for
  users.
- **Privacy:** describe sources and viewers by kind. Never include people's names, private materials or other people's
  feedback.

CI checks the code (lint, tests, generated files) and the pull request itself: the title, the changelog entry for a
`feat` or `fix`, and a sign-off on every commit. A maintainer reviews and squash-merges.

## Sign off your commits

Every commit in a pull request ends with a sign-off line, which `git commit -s` adds from your git settings:

    Signed-off-by: Your Name <you@example.com>

With it you certify the [Developer Certificate of Origin 1.1](https://developercertificate.org/): you wrote the
change, or otherwise have the right to submit it under this repository's license. Use your real name or the name you
are known by. Your contribution is licensed under the Apache License 2.0, like the rest of the repository (section 5 of
[LICENSE](LICENSE)).

## Talking to us

Questions and ideas are welcome on [Discord](https://discord.com/invite/KAkXjPX8Yn). Report a bug with the
[bug report form](https://github.com/heptameta/heptabase-explainer-studio/issues/new?template=bug_report.yml), and a security
problem privately, as [SECURITY.md](SECURITY.md) describes. Everyone taking part follows the
[Code of Conduct](CODE_OF_CONDUCT.md).
