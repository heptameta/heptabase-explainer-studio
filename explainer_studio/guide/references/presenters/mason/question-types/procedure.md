# Mason's procedure playbook: Show it once

**The question it answers:** procedure, "How is it done?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can do it once on their own in
a new situation.

**How it meets the must-haves:**

- **One complete run:** from blank to running.
- **Every step's judgment said aloud:** for each step done, its value runs out beside it, and the narration says why
  this step is done this way.
- **A second run in a different situation:** run again with another input, asking the viewer first only at the step
  easiest to get wrong ([teaching/rules.md](../../../teaching/rules.md#guess-beats)).
- **The common mistakes:** they come up by themselves while running, the symptom is visible, then they are fixed; never
  only told.

**Use it for:** procedures that produce a result:

- A calculation: filling in backpropagation's slopes cell by cell; computing the interest on a loan.
- An algorithm worked by hand: binary search; merging the characters of a text pair by pair into words.
- A piece of code or a data-processing step: cleaning up a table; computing a metric from a log.
- Operating a software tool: making a pivot table; merging two branches with version control. The toy reproduces what
  the tool computes (every step's result can be checked); for the part about where to click, use the real tool's screen
  (screenshots or a recording), since the viewer has the tool in their hands.

For example "How do you compute backpropagation cell by cell?", "How do you write binary search so it never loops
forever?", "How do you clean up a table?". Asking "how to compute it, how to do it" is procedure; asking "why does it
work" is mechanism.

**Versus Theo's procedure:** both want the viewer able to do it in a new situation; they differ in where each step's
reason comes from. Theo's reason is "this step answers the question the previous step left", and every step can be
worked out; Mason's reason is "it ran and matched", and a mistake is visible on screen. When the rightness of each step
only shows when run, the steps are conventions or interfaces, or it takes several runs to get fluent, it goes to Mason;
when every step can be worked out, the procedure is short enough, and the viewer wants to know why each step, it goes to
Theo ([presenters/README.md](../../README.md)).

**Not this one:**

- A skill that needs watching a real person's hands (operating equipment, kneading dough, drawing by hand): Mason has no
  playbook for it; choose another presenter ([presenters/README.md](../../README.md)).
- The viewer wants "why it works", not to do it themselves: that is mechanism ([mechanism.md](mechanism.md)).
- Wanting "why it must hold" is proof; choose another presenter.

How to build the toy, the beat of a run, laying it out and stepping down, honesty and language are in his script craft
([craft.md](../craft.md)); the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | What done looks like, and the usual pain | Give the destination first: what it gives you once it is done. Then act out once where the usual way hurts: invisible, run in your head, often wrong |
| 8–18% | Fix an example first | Before starting, fix an input small enough to do in your head, and state the expected answer (the answer card) |
| 18–60% | From blank to running | One beat per step ([craft.md](../craft.md#b-the-beat-of-a-run)): do a step, its value runs out beside it, say the step's judgment; a common mistake comes up midway (for example dividing gives a decimal, and only then do you learn it must be rounded down), and is fixed |
| 60–78% | A different situation | Another input; ask the viewer at the step easiest to get wrong; the second common mistake comes up here (for example when the item searched for is not there, the loop never stops); find the cause and fix it |
| 78–90% | Back to the real thing | Beside the real tool or the example in the sources: the same input, the same answer; say what the real thing does in addition |
| 90–100% | Your turn | A step card (one sentence and one judgment to watch for per step); then a new situation for the viewer to walk through in their head, revealed at the end |

## Short version (6 minutes or less)

The example and the different situation are each done only once; only one common mistake; "back to the real thing"
shrinks to one side-by-side picture, but can never be cut.

## Quality bar

After watching, given an input not done in the video, the viewer can say:

- what the first step is;
- what to look at to judge each step;
- where the most common mistake will appear.

Remembering only "I watched him do it once", without being able to say each step's judgment, does not count.

## Self-check (in addition to the craft self-check)

- [ ] From blank to running, with no step that is "here, just take this".
- [ ] Every step has the value it produced beside it, and the narration said the step's judgment.
- [ ] At least one common mistake came out of running, with its symptom, cause and fix.
- [ ] A different situation was done again, with a pause before the step easiest to get wrong.
- [ ] The close has a step card, and a new situation the viewer walks through in their head.
