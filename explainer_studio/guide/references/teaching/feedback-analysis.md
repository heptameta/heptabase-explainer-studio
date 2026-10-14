# Analysing comments

How to read the comments on a delivered episode: what each one is about, where the viewer really got stuck, what
caused it, and whether it is worth changing the video. Every comment gets an answer; few change the video.

## Categories

Every comment gets one category. The viewer never categorizes; you do.

| Category | The comment is about | Examples |
|---|---|---|
| `question` | the content: a learning question about what the video taught, or beyond it | "Why do protons flow to the low side?" |
| `teaching` | how it was taught: a passage they could not follow, a jump, an unclear line | "Lost me here", "Where did this formula come from?" |
| `production` | how it was made: a picture, a sound, a subtitle or a voice problem | "The label covers the curve", "That name is mispronounced" |
| `direction` | what the video should be: its length, depth, focus or audience | "The whole episode is too long", "I wanted more of the history" |

A comment worded as a question can be a teaching problem: "Why does it split here?" may be curiosity, or a sign that the
step before it did not land. Read the lines before it (next section) before you decide. The comment's resolution note
says the cause and what you did, for example "This line was badly written: two unfamiliar names in one sentence." It
describes the cause and the fix; it never pastes long passages of the sources.

## Where the viewer really got stuck

Viewers usually comment when "that last bit felt off", so the place they got stuck is often before the comment. Find
the line at the comment's time with the `timeline.json` of the delivery it was made on (`delivery-records/<delivery>/`,
next to that delivery's `script.yaml`). Read the two lines before it first, then go further back to where they began to
fall behind.

## The three causes of a teaching problem

| Cause | Examples | What to do |
|---|---|---|
| **The line was badly written** | two unfamiliar names in one sentence; an unfamiliar example first, the familiar one only in the next line | Change only this video: rewrite those lines, then narrate and render those scenes again |
| **The episode's arrangement** | the core idea is too abstract, with no concrete person or example before it; too much in one episode | Rearrange this episode by the planning rules ([teaching/plan.md](plan.md)), changing the plan when needed. Say so in the resolution note. Only when the same problem recurs across different videos is it the presenter's playbook that needs to change |
| **Something that always makes viewers stuck** | text too small to read; subtitles out of step with the voice | Fix this video first. Then record it as a gap (`explainer-studio gap add`), because the tools should catch it in every video |

## One comment is one moment

A comment shows this episode at this moment. Never conclude from one comment that a presenter's playbook is wrong.

## Is the problem systemic?

By default you answer: a learning question gets an answer, a confusing passage gets an explanation, a flaw is admitted
plainly. A change to the video is worth making when the problem is systemic:

- a whole stretch lost the viewer (several comments close together, or a first loss early in the episode);
- the same kind of problem repeats (one cause behind several comments);
- the video is meant for other people, so a flaw this viewer worked past will stop others.

## Answering learning questions

Answer with the images and examples the video already built: its spine object, its takeaway card's picture, the same
words it used. A recall uses the same sentence and the same picture as when it was taught
([teaching/rules.md](rules.md), principle 11); a new picture leaves the viewer reconciling two explanations. Compare the
question with the episode's transfer check in `design.md`: a question showing they cannot apply the idea to a new case
means the takeaway was not handed over.

## When the viewer got lost earlier than expected

Comments say more about this viewer than the opening probes did: where they first got lost, and in what kind of passage.
If they got lost earlier than the plan expected, lower the capacity one level, and record the evidence in the research
note about the viewer (what you assumed, what this episode showed). Then make the episodes not yet made lighter in
`plan.yaml` (smaller steps, fewer new terms per episode), including those whose script is already written. Change what
this episode taught you (for example: they cannot take three new terms in one episode; they need an example first), not
the whole plan.
