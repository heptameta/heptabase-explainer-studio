# Mason's argument playbook: Test an argument

**The question it answers:** argument, "Why should we believe this claim?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can state the claim, the
strongest evidence and the strongest objection, and judge its credibility themselves.

**How it meets the must-haves:** the claim and its strongest rival each run once on the same toy, measured with the same
ruler; every run is a piece of evidence.

- **The claim says clearly what it asserts and what it does not:** the opening states the claim as "which number will do
  what". What it does not assert is run out by letting the rival play on its most favourable ground: the cases the rival
  wins are what the claim does not assert.
- **Each piece of evidence says what it supports:** one run changes only one thing; first confirm it computes the same
  thing, then read the number on the ruler; the scoreboard gains a line, with one sentence on which part of the claim it
  supports and what it does not.
- **The strongest objection is told:** the rival, in its strongest version, first writes down its prediction by its own
  reasoning, then really runs in the case where it should win; the claim replies only once.
- **What is still unknown is said:** what still cannot be told apart after running, and the scales the toy cannot
  reach, said separately; numbers we cannot afford to run are labelled "from the paper; we did not run this".

**Use it for:** a claim about how something buildable behaves, where a small toy already shows the same direction. For
example:

- "This way of writing it is faster, even though it does more computation";
- "With good initialization, training is cheaper";
- "Residual connections make deep networks trainable".

**Versus other presenters' argument playbooks:**

- **Theo:** first builds the claim on an example, then reads real data, figures and studies item by item. When the
  evidence is a large experiment we cannot run, or a paper's figures to be understood, it goes to Theo.
- **Fabian:** the claim and the rival are each a small world of actors, and the evidence is outcomes that really
  happened in history. When the claim is about how actors behave, it goes to Fabian.
- **Sophie:** the evidence is judgments of cases and original texts. When the claim is normative or interpretive, it
  goes to Sophie.
- **Mason:** the evidence is runs we redo ourselves, the rival runs too, and on its strongest ground. When the claim can
  be reproduced on a small toy, it goes to Mason; when it only shows at large scale, it goes to Theo, or Mason gives only
  the short version and marks which numbers we did not run.

**Not this one:**

- The viewer wants "why it works" (why residuals let the slope pass straight through): that is mechanism
  ([mechanism.md](mechanism.md)).
- The viewer wants to be able to use it themselves (how to speed up their own training): that is procedure
  ([procedure.md](procedure.md)).
- Several methods side by side with no verdict for the viewer is perspectives, which Mason has no playbook for
  ([presenter.md](../presenter.md)).

One rival per episode, with one test
([teaching/plan.md](../../../teaching/plan.md#planning-how-many-episodes-each-answering-what)). How to build the toy, the
beat of a run, laying it out and stepping down, honesty and language are in his script craft ([craft.md](../craft.md));
the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | One claim, one number that changes | The claim in one plain sentence, and who says it; which number it predicts will do what (how much faster, how much lower the loss, whether it trains at all); the rival in one sentence, usually the viewer's common sense ("more computation is slower", "the optimizer will fix it on its own") |
| 8–18% | The same toy, the same ruler | The toy, the number to measure (the ruler), what must stay unchanged (the same answer, the same data); an answer card with two columns: the rival's prediction worked out by its own reasoning, and the claim's prediction; the viewer guesses |
| 18–45% | Evidence: change one thing at a time, two or three times | Each run is one beat ([craft.md](../craft.md#b-the-beat-of-a-run)): switch only one thing, first confirm what should stay the same really did, then read the ruler; the scoreboard gains a line; one sentence on which part of the claim this run supports and what it does not. In one of them the rival's prediction misses (it promised 8 times, and 3 times came out), and the claim explains the miss |
| 45–65% | The rival on its most favourable ground | The rival in its strongest version runs in the case where it should win (a very shallow network, regularization added); if it wins, say it won; the claim replies only once: move to the case the claim speaks of, and run again |
| 65–78% | Lay it out: where the claim holds | First say what to look for, then sweep the condition that decides the winner (depth, size, amount of data), one line for the claim and one for the rival, and find where they cross; step down: point at one run on each side of the crossing and say why in one sentence. Say what the claim asserts and what it does not |
| 78–90% | What is still unknown | What still cannot be told apart after running; scales the toy cannot reach (the real size, the real machines), with numbers labelled "from the paper; we did not run this"; what the original authors themselves say they do not know |
| 90–100% | Close | Zoom out on the scoreboard: what each line supports; set it beside the real thing (the paper's figure, the real tool's numbers): same direction or not; how far the presenter believes it and why, and the viewer judges for themselves; take away one method of testing: "to know whether X is true, run each on Y and look at Z" |

Measured pace: in Part 3 the scoreboard reaches three lines in 22 minutes; the GPT-2 speed-up section reaches six lines in
41 minutes, often with a long explanation between lines. For our episodes, three to four runs are enough, one to two and
a half minutes each.

## Short version (6 minutes or less)

One run of the claim, one run of the rival on its most favourable ground, one scoreboard line as the summary, one
sentence of what is still unknown. The rival's prediction on the answer card can never be cut.

## Quality bar

After watching, the viewer can say:

- what number the claim predicts, what the rival predicts, and which one came out;
- where the rival wins, and so what the claim does not assert;
- what is still unknown, and how far they believe it, and why.

Remembering only "X is better", or thinking the toy's numbers are the numbers at real scale, does not count.

## Self-check (in addition to the craft self-check)

- [ ] The opening has one sentence of claim and one of rival, both stated as "which number will do what"; only one rival
      per episode.
- [ ] The rival's prediction is on the answer card before running, worked out by its own reasoning.
- [ ] Every run changes only one thing, first confirming it computes the same thing; every run goes on the scoreboard,
      the rival's too, with numbers.
- [ ] The rival runs on its most favourable ground, and when it wins, that is said; the claim replies only once.
- [ ] Where the claim holds is swept out, not just said; one step down on each side of the crossing.
- [ ] What is still unknown is said; numbers we cannot afford to run carry their source and "we did not run this".
