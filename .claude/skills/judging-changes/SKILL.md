---
name: judging-changes
description: How to decide whether and where to change Explainer Studio's teaching behaviour, how much evidence a change needs, and what its pull request must say. Use before changing anything under explainer_studio/guide/references/ or explainer_studio/question_types.py, when turning viewer feedback into a change, and when reviewing such a change.
---

# Judging a change

A change to how videos are made is judged on three things at once, and the pull request says how it trades them:

1. **Quality:** what gets better, how it was checked (which sources, how many episodes, what the viewers said),
   and what is still not solved.
2. **Cost and time:** tokens and waiting are part of the user's experience. Say how much more or less it costs per
   series (knowing the viewer, deep reading, planning: these grow with the sources) and per episode (these grow with
   the video's length), in tokens, rough dollars and minutes.
3. **Rule complexity:** every rule can overfit one source and can hold back the next, stronger model. Say which rules
   were added or removed and of which kind (below), and whether any rule exists for a single source.

None of the three may be bought without limit at the expense of the other two.

## Where a problem belongs

Find the cause first, then the layer. Each layer has its own place to change and its own reach:

| Layer | Example symptom | Change | Reaches |
|---|---|---|---|
| Engine and tools | a mispronounced word, text too small, a broken picture, a tool error | `explainer_studio/`, `references/rendering/`, `references/languages/`, `references/sources/` | every episode that uses it |
| Knowing the viewer | "I already knew this", "this word was never taught" | `references/teaching/audience.md` | every series |
| Planning | wrong goal, wrong main question type, bad split or order, more than the viewer's capacity | `references/teaching/plan.md`; question type definitions in `explainer_studio/question_types.py` | every series |
| Shared rules | something every presenter should do | `references/teaching/rules.md`, `visual.md` | every episode |
| A subject | what counts as understood in a subject, or how to be honest about it | `references/subjects/<subject>.md` | every episode in that subject |
| A presenter's craft | skipped steps, no example before the idea, in every question type | `references/presenters/<presenter>/craft.md`, `style.md` | every episode by that presenter |
| A playbook | the skeleton for one question type is wrong, e.g. a mechanism missing a link, an argument without the strongest objection | `references/presenters/<presenter>/question-types/<type>.md` | that presenter's episodes of that type |
| Choosing a presenter | this presenter's way never fits this kind of question or viewer | `references/presenters/README.md`, or a new presenter | episodes of that kind |

The paths under `references/` are inside `explainer_studio/guide/`. Report every change with the layers it
touches and roughly how many episodes of a real plan it reaches, so the reviewer can judge its range.

## How much evidence

- **Engine and tool errors:** seen once is enough. Fix them directly, with a test when the behaviour can regress.
- **Teaching changes:** the same cause must show up in two different sources. One viewer's discomfort on one
  source may belong to that source only, and a change made too early breaks what already worked. A change made on
  less evidence is marked as such in the pull request, and is the first to be re-checked later.
- **A new question type:** the sources keep asking a kind of question whose "after watching, the viewer can" none of
  the existing types describes. Every new type adds a way to misjudge an episode's main question type, so more types
  are not better.
- **A new playbook for a presenter:** the presenter's way can carry this question type, and episodes made with a
  draft playbook for it were judged good on two different sources.
- **A new presenter:** some question type or some viewer cannot be taught by any existing presenter's way, and the cause
  is the way, not the skeleton (for example, the viewer has to do something with their hands to understand). Try it
  first in episodes that use draft playbooks.
- **Merging:** two question types whose "after watching, the viewer can" have become the same, or two presenters whose
  ways turn out to be one.

## Four kinds of rule

| Kind | What it says | Example | With a stronger model |
|---|---|---|---|
| Fact about the viewer | what this viewer knows and can take in | capacity, which words need teaching again | still needed: no model knows the viewer |
| Goal | what a good video is | one question per episode; the viewer can say what each scene does | still needed, and met more often |
| Check | whether it was done | the audience review, a validation warning | still needed; it fires less often, so it costs less |
| Procedure | how to do it, step by step | build the chain of premises; do not open with the weaker reason | may become an obstacle: it patches today's model |

When something fails, look for the fix in this order: a missing fact about the viewer (change how the viewer is
known), an unclear goal (make it shorter and more exact), a check that does not catch it (add a check), and only when
the model knows the goal and sees the check's result and still fails, a procedure. What can be written as a goal is
not written as a procedure. Every procedure states, next to it or in its pull request, the failure it prevents and the
goal it serves, so it can be removed when a new model no longer needs it.

## Spending tokens or time

1. **What can be a rule should not cost tokens:** a rule is written once and is free in every episode after; tokens are
   paid again in every episode.
2. **Tokens buy finding problems:** reading or measuring again brings new information; doing the same thing again
   usually does not.
3. **Spend only on a signal, and with a limit:** no signal, no extra spending. When the limit is reached and it still
   fails, the problem is usually upstream (the plan, the choice of evidence): record it and change the rule or the plan.
4. **Compare with the failure it prevents:** an episode made again means narration and rendering again and the viewer
   watching again, so checks before narration are cheap.

## What the pull request says

The description has the sections of [`commit-and-pull-request-convention`](../commit-and-pull-request-convention/SKILL.md),
and a teaching change adds to them:

- **Why:** the evidence: what happened, on which kinds of source and for which kinds of viewer. Never names of
  people, private materials, users' comments or local paths; describe a source by its kind and the viewer by their
  level.
- **What changes:** the layers it touches, with their reach.
- **Trade-offs:** always there, with the three trade-offs above as bold items. One that does not move says so in a
  few words.
- **Verification:** what was tried, whether the evidence reaches the bar above (a change made on less is marked here),
  and what you expect to change in the next videos, so the next ones can confirm it.

A teaching change is a `feat` or a `fix`, so it also has a `CHANGELOG.md` entry.

```markdown
## Why

On two sources of different kinds (a physics textbook chapter, a machine learning paper), beginner viewers left 7
comments that a question felt forced; 5 were on guesses the per-act rule had placed.

## What changes

The guess beat appears only where the viewer would really ask, instead of once per act. The shared rules and Theo's
mechanism playbook change, so every presenter follows it.

## Trade-offs

- **Quality:** the remaining reveals land better. Not solved: some guesses still ask what the viewer cannot know yet.
- **Cost and time:** about 1k fewer tokens per episode; unchanged per series.
- **Rule complexity:** one goal rule replaces a procedure ("one guess per act"). No rule for a single source.

## Verification

Planned and scripted both sources with the old and new guide; the new guesses sit where viewers had commented.
Proofs are below the two-source bar (one episode). The next videos should show 1 or 2 guess beats per episode
instead of about 4.
```
