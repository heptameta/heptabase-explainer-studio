# Mason's mechanism playbook: Explain a mechanism

**The question it answers:** mechanism, "Why does this happen? How does it work?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can tell the causal chain in
their own words and predict what changes when one condition changes.

**How it meets the must-haves:**

- **Every link of the causal chain visible, none skipped:** each link is a block of the toy that runs as soon as it is
  attached, or a knob that runs as soon as it is turned; the state at every step is laid out on screen, and no step has
  to be run in the viewer's head.
- **Predict what changes when one condition changes:** change the data or the environment and really run it again,
  guess first, then reveal.

**Use it for:** mechanisms whose answer is rules running as written, with nobody making choices, especially behaviour
that only shows when run (for example a control rule, a learning process, a system sensitive to its starting point). Two
common shapes:

- **Growing block by block:** the mechanism is made of a few components, each forced by the failure of the previous
  version. For example "How does a neural network learn?": start from nudging one number a little, each block forced by
  the previous version's failure.
- **Simple rules, behaviour hard to guess:** the rules are fixed; turn a knob and find the odd one in a whole family of
  behaviours. For example "Why does a steering rule get through this bend and not that one?", "Why are weather forecasts
  useless beyond two weeks?".

**Versus other presenters' mechanism playbooks:**

- **Theo** rebuilds the structure and makes the result look inevitable. When the answer still makes sense with "run it"
  taken away and only reasoning allowed, it goes to Theo by default.
- **Mason** really runs it; the run decides the result, and it can run wrong. When behaviour only shows when run and
  there is no easy formula, it goes to Mason; when reasoning works but the viewer chose the "build a small toy and run it
  for you" telling in the opening presenter probe, it also goes to Mason (the fourth question in
  [presenters/README.md](../../README.md#the-same-question-type-several-presenters-playbooks)).
- **Fabian's** world has actors with their own aims who make choices. Nobody in Mason's toy makes choices; the
  components only run by the rules.

**Not this one:**

- The viewer wants to be able to do it themselves: that is procedure ([procedure.md](procedure.md)).
- Proving that something must hold (proof), or how events happened (narrative): Mason has no playbook for those
  ([presenter.md](../presenter.md)).

How to build the toy, the beat of a run, laying it out and stepping down, honesty and language are in his script craft
([craft.md](../craft.md)); the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–7% | The real thing working | A concrete, strange behaviour (a model that cannot count letters; a car that suddenly bounces off at the end of a bend), or something invisible in how it is done today; the main question in one sentence; say the core is actually small |
| 7–17% | The smallest version that runs | The toy's few rules and what it produces, side by side; the first guess, the first run |
| 17–55% | Change one thing, run once: three to five beats | Each beat as in [craft.md](../craft.md#b-the-beat-of-a-run). Growing block by block: each block forced by the previous version's failure. Simple rules, behaviour hard to guess: turn a labelled knob and stop at two or three values. For the most important block or value, say plainly "this is the most important step" |
| Once among them | A mismatch | The answer card gets a cross, the symptom is visible, follow it to the cause, fix it |
| 55–72% | Lay it out, then step down | Lay many runs out together ([craft.md](../craft.md#c-lay-it-out-then-step-down)), first saying what to look for, then point out the pattern; then point at two runs that differ only slightly yet end very differently, play them side by side in slow motion, and say the cause in one sentence |
| 72–85% | Change one condition and run again | Change the data or the environment; a guess; stop; then run |
| 85–100% | Close | Use the finished toy to untangle the opening's strange behaviour; set it beside the real thing and say what the toy left out; map the toy's words back onto the sources' terms; hand off |

## Short version (6 minutes or less)

Only two beats of changing one thing; laying it out and stepping down shrink to one side-by-side picture and one
sentence; changing one condition can never be cut.

## Quality bar

After watching, the viewer can say:

- what each block of the toy (or the knob) does;
- which block causes the opening's strange behaviour;
- what happens when one condition changes.

Remembering only "it ran", without being able to say why, or thinking the real thing is identical to the toy, does not
count.

## Self-check (in addition to the craft self-check)

- [ ] Every link of the causal chain is a step the toy really ran; no step is merely announced by the narration.
- [ ] At least one rerun with one condition changed, with a pause before running to let the viewer think; the viewer
      can say which condition changed.
- [ ] The opening's strange behaviour is untangled by the toy at the close.
- [ ] At least one pattern seen in a layout steps down, pointing at one run to say the cause.
