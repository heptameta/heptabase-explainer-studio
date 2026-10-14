# Mason's conceptual change playbook: Run the old method until it breaks

**The question it answers:** conceptual change, "How did people come to think this way, and where did the old idea fall
short?" ([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can say why the old
idea was reasonable, where it broke down, and what the new idea gains and costs.

**How it meets the must-haves:**

- **The old idea is presented as reasonable:** build the old method as a toy and first run it on inputs it suits, where
  it runs right; say who did it this way back then and why it was reasonable (simple, readable, good enough on the
  machines of the time).
- **Where it breaks down is concrete:** grow only one dimension (the number of words looked at, languages, new data);
  ask once before the run that will break, then run, and it breaks on a visible input (an infinity, a table that is nine
  tenths zeros, a sentence too long to fit).
- **The cost of the new idea is stated too:** the new method first produces the same answer on the old method's ground,
  then passes the test the old method failed; then the price it pays is run out too (more knobs to tune, new strange
  faults, harder to read), each item one run.

**Use it for:** an old idea that is an old method that can be built, where the reason for switching to the new method
can be rerun. For example:

- "Why did language models switch from counting in a table to neural networks?";
- "Why use BPE instead of plain characters or bytes?";
- "Why replace a fixed steering rule with one that corrects its direction?".

**Versus other presenters' conceptual change playbooks:**

- **Theo** (conceptual change goes to him by default): rebuilds a piece of intellectual history, making the old idea
  reasonable with what people of the time could see, with people, a timeline and original texts all doing work on
  screen. When the old idea is a view or a debate, or the viewer wants that history, it goes to Theo.
- **Sophie:** turns the old intuition into a case the viewer judges the old way, then uses a case to make it fail. For
  when the old intuition is still in the viewer's head.
- **Mason:** the old idea is an old method that can be built; its reasonableness, its breakdown and the cost are all
  run. When the old method can be built and run to results, and the viewer chose the "build a small toy and run it for
  you" telling in the presenter probe, it goes to Mason.
- Fabian has no playbook for conceptual change.

**Not this one:**

- The viewer wants how the new method works (how BPE merges step by step): that is mechanism or procedure
  ([mechanism.md](mechanism.md), [procedure.md](procedure.md)).
- The old idea is a worldview that cannot be built (people once thought heat was a fluid): it goes to Theo.
- The protagonist is events and people (who invented it in which year, how it spread): that is narrative, which Mason
  has no playbook for ([presenter.md](../presenter.md)).

How to build the toy, the beat of a run, laying it out and stepping down, honesty and language are in his script craft
([craft.md](../craft.md)); the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | Today's way, and one strange fault | The real thing working: how everyone does it today, and one concrete strange fault (a model that cannot count the letters in a word); the main question in one sentence: why do people do it this way? How was it done before? Say we will first build the old method |
| 8–25% | The old method, on its own ground | The smallest version of the old method, run on inputs it suits, the answer card ticked; say why it was reasonable, with one or two names and years only as sources; the first scoreboard line |
| 25–45% | Grow it, run it until it breaks | Grow only one dimension, a few times; ask only once, before the run that will break, "do you think it still holds?"; it breaks on a visible input, and the symptom stays on screen; if there is a patch (smoothing), apply it and grow again, saying what the patch cannot fix; say plainly which run is the most important |
| 45–62% | The new method: first the same answer | The new method produces the same number and the same output on the old method's ground, old and new side by side; say they are really two ways of doing the same thing; then on the input that broke the old method, it passes; what the old method's patch becomes inside the new method |
| 62–80% | The new method's bill | "Is anything worse with the new method?", then a pause (no guess); run out on the toy the price it pays: more knobs to tune, new strange faults, harder to read; each item one run, the scoreboard one line longer |
| 80–90% | A ledger | Two columns: old method, new method; three rows: where it is right, where it breaks, what it paid; every cell points back to a run on the scoreboard |
| 90–100% | Close | Use the new method's cost to untangle the opening's strange fault; set it beside the real thing and say what the toy left out; who is still trying to remove this cost (for example models that read bytes directly), not yet settled |

Measured pace: in the tokenizer video the two old methods together take 8.5 minutes, the new method 34 minutes, and the
cost comes at the end in 18.5 minutes; in the first makemore episode the old method takes about 58 minutes, and the new
method takes about 43 minutes to produce the same 2.45, while "it breaks" is only about a minute of spoken explanation.
At our lengths, the old method plus its breakdown should take four tenths, and can never be passed over in a minute as
the model does.

## Short version (6 minutes or less)

The old method runs once right and once broken; the new method once with the same answer and once passing; one cost.
The cost can never be cut.

## Quality bar

After watching, the viewer can say:

- in which run the old method was right, and why it was reasonable back then;
- on which concrete input it broke;
- how the new method first showed it had not changed anything;
- what the new method paid, pointing at the run that shows it.

Thinking the old method was stupid, or that the new method has no cost, does not count.

## Self-check (in addition to the craft self-check)

- [ ] The old method was really built and ran right on its own ground, not just told.
- [ ] The breakdown is one run: a visible input, a number; there was a pause before the run that broke.
- [ ] The new method first produced the same answer on the old method's ground, old and new side by side.
- [ ] At least one cost was run out on the toy, and you can say which run.
- [ ] The old method is treated fairly: why it was reasonable back then was said, with no mockery and no real person used
      as the bad example.
- [ ] Every cell of the ledger points back to a run; the opening's strange fault is untangled at the close.
