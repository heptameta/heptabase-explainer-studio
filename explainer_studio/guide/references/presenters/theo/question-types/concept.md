# Theo's concept playbook: Enclose a concept

Contents: [Skeleton](#skeleton) · [When the goal is use](#when-the-goal-is-use) ·
[Short version](#short-version-6-minutes-or-less) · [Quality bar](#quality-bar) · [Self-check](#self-check)

**The question it answers:** concept, "What is it, and how does it differ from things that look like it?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can tell examples from
non-examples and produce one of their own. Given something new, they can say whether it counts, and which part of the
definition decides.

**How it meets the must-haves:**

- **At least two examples:** one example is done from start to finish with real numbers in the "home"; then the same
  picture is used quickly 2 or 3 times in different worlds, changing one thing each time.
- **A close non-example:** drawn in the same home, labelled "not" in red, saying which condition it fails. At least one
  is a **near miss** (everything looks right until you look from another angle), and it forces the definition to
  become more precise.
- **The definition comes out of the difference:** the definition is "the line between the examples and the
  non-examples". Say it first in the picture's words (the grid lines stay parallel and evenly spaced), then match it to
  the textbook's words (additivity, scaling), and say why the textbook chose that wording.
- **A boundary case the viewer judges:** something between yes and no. Stop, let the viewer judge, reveal, and say
  which part of the definition decides.

**Use it for:** a **structural** concept: a kind of mathematical object, an operation, a property, a distinction in
probability or statistics, whose examples and non-examples can all be drawn in the same picture. For example "What is a
linear transformation?", "What is convolution, and how does it differ from multiplying term by term?", "What is a
p-value, and how does it differ from the probability that the hypothesis is true?", "What does it mean for two events
to be 'independent'?", "What is a vector?".

**Not this one:** the goal is to be able to do it (procedure: how to do it; see
[presenters/README.md](../../README.md)); why it works the way it does (Explain a mechanism:
[mechanism.md](mechanism.md)); how this definition was changed, step by step, into today's (How an idea changed:
[conceptual-change.md](conceptual-change.md)).

**Versus other presenters' concept playbooks:** Theo, Fabian, Mason and Sophie all have a concept playbook; choose by
the shape of the answer ([presenters/README.md](../../README.md)). Fabian: two worlds that differ in only one
condition, and the concept is that condition; fits a concept about the situation of actors (an institution, a kind of
competition). Mason: sweep one parameter, and the examples, non-examples and boundary run out by themselves; fits a
concept that is a behaviour of a system (convergence and divergence, overfitting). Sophie: first you give a
definition, then cases on the boundary break it; fits moral or legal distinctions where the judgment has no standard
answer. Theo: examples and non-examples drawn in the same home, the definition is the line that separates them, and
the boundary judgment **has a right answer**, decided by one part of the definition. A concept that is a structure (a
mathematical object, a probability) goes to Theo
([presenters/README.md](../../README.md#the-same-question-type-several-presenters-playbooks)).

**The core idea of this playbook is a line.** A concept is not a sentence of definition but a line that splits things
into two sides. Theo's job is to find a picture in which that line **can be seen**. So the most important decision of
the episode is the "home": choose a picture where examples and non-examples can both be drawn and clearly told apart,
and say why you did not choose another (convolution does not start from images, because images bring small
complications and are less representative).

**There are two kinds of foil**, chosen from the audience description. When the viewer has a common but too loose
definition in their head ("a vector is just a list of numbers", "linear means the line doesn't bend"), state it fairly,
then let a near miss make it fail, and the definition becomes more precise with it
([teaching/rules.md](../../../teaching/rules.md#handling-a-misconception)). When the viewer has only seen the textbook's
abstract definition, state it fairly, then prosecute it for not telling you "why the line is drawn here", and finally
come back to say why the textbook wrote it that way ([craft.md](../craft.md#i-motivation), technique 3).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–6% | A question, or a row of neighbours | The first 5 seconds are concrete: two lists of numbers and a "????"; three people's three ideas of the same word. Ask "what exactly is it, and how does it differ from these?" |
| 6–14% | Choose a home | Choose one picture as the episode's home, and say why this one and not another ("the arrows are too crowded, let's look at points instead", "images look nice but aren't representative enough"); this picture never changes from here on |
| 14–34% | Do the first example to the end, then name it | One example done from start to finish in the home with real numbers (the sum of two dice; where (−1, 2) lands); check it another way when you can (code, another method); give the name only after it is done, and say where the name comes from |
| 34–48% | Non-examples and near misses | Ask "do you think this one counts?", then act it out: one beat per non-example, the same picture, red labels showing which condition it fails; the last one is a near miss that makes the definition more precise, and the revised sentence stays on screen |
| 48–66% | Quick examples, new worlds | The same home, changing one thing each time, across 2 or 3 worlds (probability → averages → images); one guess before the first change ("What do you think this kernel will turn the picture into?"); each new example says in its first line what it is there to show |
| 66–82% | The textbook definition, and what it buys | Match the textbook's wording to the picture's definition item by item; say why the textbook chose that one (general, applies to things you never thought of); what this concept lets you do (every matrix is a transformation) |
| 82–94% | Hand the boundary to the viewer | Something between yes and no (does long multiplication count as a convolution? what about the carrying step?); guess, pause, reveal, and say which part of the definition decides |
| 94–100% | Close | A reframe: what should bring it to mind from now on; the takeaway card's "what it is not" is this episode's near miss |

**Measured pace** (four 3b1b videos): about 156–205 words a minute in English; every one has a small calculation with
real numbers; the name appears at 30–60% of the length; the non-example passage (when there is one) is about a minute,
4 to 8 seconds per non-example; we give each non-example one beat (principle 15 in
[teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)); each quick example takes 30 seconds
to 2 minutes. Other visual rhythm is in the style ([style.md](../style.md)).

---

## When the goal is use

The concept's goal is use ([teaching/question-types.md](../../../teaching/question-types.md#concept-the-other-goal-use)).
**Use it for:** a structure that can be computed, used as a tool (expected value, compound interest, opportunity
cost). The home never changes for the whole episode. Where telling apart gives its time to non-examples and the
boundary, use gives it to applications.

| Share | Section | Content |
|---|---|---|
| 0–6% | A decision to make | The first 5 seconds are a concrete choice ("A lottery ticket costs 50, the jackpot is a hundred million: is it worth buying?"); say how intuition judges it: that is the foil, and the deep case makes it lose once |
| 6–12% | Choose a home | As in the skeleton above: choose a picture, say why, never change it (one bar per outcome, its width the probability, its height the gain or loss) |
| 12–32% | Do the deep case to the end, give the name | Finish it with real numbers, and check it another way when you can; give the name once it is done (about 30% into the episode); next to the home, write the parts (probability, gain or loss) and the conditions it needs (it can be repeated many times; you can afford to lose): that is where the textbook definition sits |
| 32–62% | Apply it twice | Each one says in its first line what it tests; the same home, changing only labels and numbers; before the first, ask once ("Do you think an extended warranty is worth buying?"), pause, reveal, and give the conclusion using the name; one of them from a field the viewer would not expect (shoot a three or a two?) |
| 62–76% | The fence | A situation where it looks usable but gives a wrong answer (insurance: the expected value is negative, yet you should buy it, because it happens only once and you cannot afford to lose); in the home, the condition that fails is marked in red |
| 76–94% | Your turn | A case not seen before: guess, pause, reveal; then one sentence asking them to think of a recent choice of their own |
| 94–100% | Close | A reframe: which kind of choice should bring it to mind from now on, and what it buys; the takeaway card's "what it is not" is the fence |

- At most five situations; this is exactly where Theo goes wrong most easily. The home never changes, and each new
  world says in its first line what it is there to show.
- The quality bar is replaced by the one in the use section of
  [teaching/question-types.md](../../../teaching/question-types.md#concept-the-other-goal-use). In the self-check keep
  the items about the home and checking, and replace those about non-examples, the boundary and new worlds with the
  must-haves of the use row.
- Short version (6 minutes or less): one deep case, one application, one sentence of fence, one "your turn"; "your
  turn" can never be cut.

## Short version (6 minutes or less)

As a short passage inside another episode (for example "first, what exactly X is" inside a mechanism episode), or when
the plan's length is 6 minutes or less:

| Share | Section | Content |
|---|---|---|
| 0–8% | Question | A row of neighbours or a question; ask "what is it" within 10 seconds |
| 8–35% | Home and first example | One picture, one example done to the end, the name |
| 35–60% | One non-example, one near miss | The definition becomes precise here and stays on screen |
| 60–80% | One more example, in a new world | Change only one thing |
| 80–100% | Hand the boundary to the viewer | Guess, pause, reveal; one sentence of close |

**Leave out:** saying why you chose this home (just use it), the textbook definition, a long "what it buys".
**Keep:** examples before the name, non-examples drawn in the same picture, the near miss, the boundary the viewer
judges, the definition said in the picture's words.
**Word count:** convert with the language reference's speaking rate.

---

## Quality bar

After watching, the viewer can do these three things:

- given something not in the video, judge whether it counts, and say which part of the definition decides;
- produce an example of their own, and a near miss;
- say the definition in the picture's words (not a memorized textbook sentence).

What this playbook does, concretely: every episode has a near miss and a boundary the viewer judges, with one beat per
non-example; "what it buys" does not eat a third of the length, and if it is too long it becomes
another episode. Remembering a few examples without being able to say what something "is not" does not count.

## Self-check

- [ ] The episode has a "home": every example, non-example and boundary case is drawn in the same picture, and you said
      why you chose it.
- [ ] The first example is done to the end with real numbers, and the name is given only after.
- [ ] At least one non-example and one near miss, each with its own beat, with the failed condition marked on screen.
- [ ] The definition comes out of the difference between examples and non-examples, and the revised sentence stays on
      screen.
- [ ] At least two examples from different worlds, in the same picture, changing one thing each time.
- [ ] There is a boundary case the viewer judges: paused, revealed, and which part decides is said.
- [ ] The picture's definition is matched to the textbook's, with why the textbook wrote it that way (when the viewer
      will read textbooks).
- [ ] The takeaway card's "what it is not" is this episode's near miss.
