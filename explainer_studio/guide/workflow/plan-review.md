# Plan review

The plan is the one thing the user confirms before production. Production starts only when they agree in chat.

## Showing the plan

1. Run `explainer-studio plan validate`, then `explainer-studio plan open`. The page opens in their browser (or in your pane: see "Pages are optional" in `guide.md`); it shows
   the series, production settings, the audience, the goal, each episode, and your rationale.
2. In chat, summarize in a few lines: who you understood the viewer to be (for a teacher, their viewers) and what they
   want to be able to do, how many episodes and what each answers, and who presents each.
   - Mention each episode whose presenter has no playbook for its question type yet, in one sentence, for example
     "Clio's way of teaching this kind of question has not been tested yet, so this episode may be less polished;
     your feedback on it helps us most." (The page marks these episodes "not yet tested".)
   - Say once that narration is capped at $20 for the series by default, and that they can tell you another budget
     (or no limit) or set it on the page.
   - Recommend making the first episode (at most two) first and continuing after watching it; later episodes are
     adjusted from what the first one teaches you about the viewer.
3. End your turn. Do not wait for the page.

## When the user replies

- Read `plan.yaml` again before anything else: they may have edited it on the page. Run `plan validate`.
- Changes requested in chat: edit `plan.yaml`, validate, open the page again if the change is large, and summarize
  what changed.
- They say to start: production begins with the episodes they named (the first one by default). Their agreement
  covers narration costs within the budget, including retries and fixes. From here to delivery, do not ask them
  anything except for real blockers.
