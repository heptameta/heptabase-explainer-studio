# Mason's concept playbook: Turn a knob to sort the kinds

Contents: [Skeleton](#skeleton) · [When the goal is use](#when-the-goal-is-use) ·
[Short version](#short-version-6-minutes-or-less) · [Quality bar](#quality-bar) ·
[Self-check](#self-check-in-addition-to-the-craft-self-check)

**The question it answers:** concept, "What is it, and how does it differ from things that look like it?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can tell examples from
non-examples and produce one of their own.

**How it meets the must-haves:**

- **At least two examples:** the same toy with the knob at two different values, producing two runs that differ in
  detail but belong to the same kind (for example learning rates 0.05 and 0.1 both converge, one fast, one slow).
- **A close non-example:** a run that looks as if it belongs to the kind on the usual chart and gives itself away on a
  second chart (the training loss falls beautifully while the dev loss climbs; every layer's distribution looks healthy,
  yet it is a stack of layers with no nonlinearity).
- **The definition comes out of the difference:** name the one quantity that separates the examples from the
  non-example (the gap between training and dev, the share of saturated units per layer); the definition is one
  sentence of "look at this quantity".
- **A boundary case the viewer judges:** a run that lands near the threshold, with only that quantity on screen; the
  viewer judges it first with the definition just given; then one run from each side of the threshold is played side by
  side in slow motion, revealed, with one sentence of why.
- **Produce one of their own:** an example is just a value of the knob, and the viewer can say "turn it to here and you
  get one".

**Use it for:** a concept that is a behaviour of a system, where the rules run as written and turning a knob moves it
from one kind to another. For example:

- "What does too high a learning rate mean: how do convergence, oscillation and divergence differ?";
- "Overfitting and underfitting";
- "A stable and an unstable controller".

**Versus other presenters' concept playbooks** (Theo, Fabian, Mason and Sophie all have one; choose by the shape of the
answer, [presenters/README.md](../../README.md)):

- **Theo:** derives the definition step by step from examples and non-examples, and the definition can be reasoned out;
  fits a structure (a probability, a kind of mathematical object).
- **Fabian:** two small worlds that differ in only one condition; the concept is about the situation of actors (an
  institution, a kind of competition).
- **Sophie:** first lets the viewer give a definition, then breaks it with cases on the boundary; moral or legal
  distinctions.
- **Mason:** the examples, the non-example and the boundary are all runs of the same toy at different knob values; the
  definition is a measurable check. When the threshold can only be found by running and there is no easy formula, it
  goes to Mason.

**Not this one:**

- The viewer wants "why does this happen" (why too high a learning rate diverges): that is mechanism
  ([mechanism.md](mechanism.md)). Both playbooks turn a knob: mechanism ends at a causal chain; concept ends at a ruler
  that sorts, and one boundary the viewer judges themselves (when the goal is use, at a tool to take away; see that
  section below).
- The viewer wants to be able to tune it themselves (find a good learning rate for a model): that is procedure
  ([procedure.md](procedure.md)).
- When the concept is a structure, a situation, or a distinction of values, choose another presenter (above).

How to build the toy, the beat of a run, laying it out and stepping down, honesty and language are in his script craft
([craft.md](../craft.md)); the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | The real thing shows this behaviour | A concrete symptom (a model scoring full marks on training questions and failing new ones; a car that makes the bend, then bounces wildly on the straight); the main question in one sentence: "What is this called, and how does it differ from what looks the same?"; say the toy is small |
| 8–18% | The toy and one knob | Rules and knob side by side, the knob labelled first (name, unit); run once at a normal value; when the viewer would really want to know, ask once what will happen |
| 18–40% | Turn the knob, stop at two or three values | Each beat as in [craft.md](../craft.md#b-the-beat-of-a-run); first run two examples in the same kind, the earlier one left as a shadow; say what they share, without the name yet; the scoreboard in the corner gains a line per value: the value, the quantity, a small picture |
| 40–55% | Lay it out: a whole family | First say what to look for, then run each value separately and stack them (or a row of small pictures, or a chart of "quantity against knob"); the kinds become regions; only now give the name (what this is called in the real thing) |
| 55–70% | The near miss | A run that looks as if it belongs to the kind on the same chart and gives itself away on a second chart; say the quantity that separates them as one sentence: that is the definition |
| 70–85% | The boundary: your call | A run near the threshold, with only that quantity on screen; the viewer judges with the definition, pause 2 to 3 seconds; step down: one run from each side of the threshold, side by side in slow motion, with one sentence of why |
| 85–100% | Close | Back to the opening's real thing, judged with this ruler; say what the toy left out; one card with three lines: how to recognize it (which quantity to look at), how to make one yourself (where to turn the knob), what is most often mistaken for it |

Measured pace: Karpathy sweeping the gain stops at 6 values in five and a half minutes, about 55 seconds each; for the
learning rate, three values tried by hand take about a minute and a half, then a sweep with a chart about 4 minutes.
Victor does only one move per section, always in the same order: control, climb up, step down.

## When the goal is use

The concept's goal is use ([teaching/question-types.md](../../../teaching/question-types.md#concept-the-other-goal-use)).
**Use it for:** a tool that is a system regularity which only shows when run (queueing: customers arrive at random, and
the wait explodes as utilization nears one hundred percent; feedback loops; bottlenecks). The toy is the same one for
the whole episode; real systems cannot be run, so what runs is always the toy, and the real system only supplies its
numbers and one known fact as the answer card.

| Share | Section | Content |
|---|---|---|
| 0–8% | The real thing shows this behaviour | A concrete symptom (the emergency room gets only ten percent more patients, yet the wait doubles); the main question: "Somewhere else, what will happen to the wait?"; say the toy is small |
| 8–18% | The toy and one knob | As in the skeleton above: rules and knob side by side, the knob labelled first; run once |
| 18–40% | Sweep the knob, build the tool | First say what to look for; sweep a few values, stack the whole family, and the regularity appears; step down at the run about to explode and say why in one sentence; give the name; beside it write the parts (utilization, wait) and the condition it needs (customers arrive at random); put the opening's real number into the toy and check it against the answer card |
| 40–66% | Match two real systems | For each, first say what its knob and quantity are, and put its numbers into the toy; for the first, guess "what will happen"; for the second, pause after it is told; run; the answer card is a known fact about that system (the account of a real incident, public numbers), compared side by side and said with the name; one from a field the viewer would not expect |
| 66–80% | The fence | A real system where a condition the tool needs does not hold (a clinic by appointment: customers do not arrive at random); change that condition and run again, and the wait does not explode; say which condition it is |
| 80–94% | Your turn to think | A system not seen before: the viewer thinks first, run, reveal; then one sentence asking them to find that knob around them |
| 94–100% | Close | One card with three lines: how to recognize it (which quantity to look at), when it happens (where the knob is turned), when it does not apply (which condition) |

- When the toy does not match the answer card, say what the toy is missing; never change numbers to fit the answer.
- The quality bar is replaced by the one in the use section of
  [teaching/question-types.md](../../../teaching/question-types.md#concept-the-other-goal-use). In the self-check keep
  the items about the toy, the knob, and stepping down to say why; replace those about the non-example, the boundary and
  making one yourself with the must-haves of the use row.
- Short version (6 minutes or less): one sweep of the knob, one real system matched, one sentence of fence, one "your
  turn to think"; "your turn to think" can never be cut.

## Short version (6 minutes or less)

One knob stopped at three values: an example, a near miss, a boundary; one stacked chart; one sentence of "look at this
quantity". The boundary run is judged by the viewer and can never be cut.

## Quality bar

After watching, given a run not shown in the video (two loss curves, a distribution chart), the viewer can say:

- which kind it belongs to, and which quantity they looked at;
- why it is not the one that looks like it;
- where to turn the knob to make an example themselves.

Remembering only the name, saying only "too big is bad", or sorting the runs in the video but failing to judge a new
one, does not count.

## Self-check (in addition to the craft self-check)

- [ ] The examples, the non-example and the boundary are all runs of the same toy, differing only in the knob's value
      or one condition; every one was really run.
- [ ] The knob was labelled before turning; only one knob turned at a time; each value run separately.
- [ ] Before laying out, what to look for was said; the name came only after the kinds appeared.
- [ ] The near miss really looks alike on the first chart; on the second chart that gives it away, where to look was
      said.
- [ ] The definition is one sentence of "look at this quantity", said only after the near miss.
- [ ] For the boundary run, the viewer judged first, with a real pause, before the reveal; the reveal stepped down,
      pointing at a pair of runs on either side of the threshold to say why.
- [ ] The close says how to make an example yourself.
