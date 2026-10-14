# Theo's procedure playbook: Reinvent a procedure

Contents: [Skeleton](#skeleton) · [Short version](#short-version-6-minutes-or-less) · [Quality bar](#quality-bar) ·
[Self-check](#self-check)

**The question it answers:** procedure, "How is it done?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can do it once on their own in
a new situation; and when they forget a step, they can say what question that step answers and work it back out.

**How it meets the must-haves:**

- **One complete run:** on an example small enough to do in your head, from start to finish; every step is the answer to
  the question the previous step left (which half the error is in → which column → which row). The real numbers stay
  on screen throughout; when done, check the answer another way (count the people again; the message taken out matches
  the original).
- **When the method has several equivalent forms, teach the one closest to real things:** the formula the viewer will
  take away and compute with is the form closest to "things you can count" ("sick people × positive rate : healthy
  people × false positive rate"), not the most elegant or most general one (prior odds × Bayes factor). The elegant form
  can come later, saying they are the same thing.
- **Every step's judgment said aloud:** each step first asks the question it answers, then does it, then states the
  judgment ("this group is already even, so this bit is set to 0").
- **A second run in a different situation:** a new input, done once more in full by the step card. Ask the viewer only
  before the one or two steps easiest to get wrong ([teaching/rules.md](../../../teaching/rules.md#guess-beats)), pause 2
  to 3 seconds, then reveal; the other steps follow the card with a short pause.
- **The common mistakes:** the mistakes learners make (with a real example or data, for example doctors choosing 90%)
  and the method's own limits (when the shortcut fails), each acted out on the same object, saying the symptom and how
  to avoid it.

**Use it for:** a procedure with **few steps, each of which can be worked out**: every step can be told as "the answer
to the question the previous step left", not as a convention. For example "How to encode and decode a Hamming code",
"How to multiply two matrices", "Given a test result, how to quickly estimate your chance of being ill", "How to take
the derivative of a composite function", "How to build a Huffman tree". A procedure whose most common mistake is
thinking wrong (a step of reasoning goes wrong). When the mistakes only show up when you run it (off by one, never
stopping), or the steps are conventions and interfaces, it goes to Mason ([presenters/README.md](../../README.md)).

**Not this one:** the viewer wants "why it works", not to do it themselves (Explain a mechanism:
[mechanism.md](mechanism.md)); "why it must be correct" (Find the proof: [proof.md](proof.md)). When the steps are
mainly conventions or interfaces (where to click, how to lay out a format), the procedure is long, or it takes many runs
to get fluent, it goes to Mason ([presenters/mason/question-types/procedure.md](../../mason/question-types/procedure.md)).
A skill that needs watching a real person's hands: Theo has no playbook for it; choose another presenter
([presenters/README.md](../../README.md)).

**Versus other presenters' procedure playbooks:** Mason has one (Show it once): he builds a minimal version that
really runs, each step runs and shows its value, the value is the basis of the judgment, and mistakes are visible on
screen. Fabian and Sophie have none. Both want the viewer able to do it in a new situation; they differ in **where each
step's reason comes from**. Mason's reason is "it ran and matched"; Theo's reason is "this step answers the question the
previous step left". So: every step can be worked out, the procedure is short enough, and the viewer wants to know why
each step (so they can work it back out after forgetting) → Theo; the rightness of each step only shows when run, the
steps are conventions, it takes several runs to get fluent → Mason
([presenters/README.md](../../README.md#the-same-question-type-several-presenters-playbooks)).

**The core idea of this playbook is "every step answers a question".** A memorized procedure breaks when you forget one
step. A reinvented procedure survives it: when you forget a step, ask yourself "what question did the previous step
leave?", and you can work it back out. The standard of the explanation is: **if the viewer forgot step three, could they
think it out from the question step two left?** (The way the Hamming code video is written: not explaining it in the
most direct way, but letting you invent it yourself.) But understanding is not being able to do it, so this playbook
always has a second complete run, and lets the viewer think first at the step easiest to get wrong.

**The foil is the memorized procedure:** a mnemonic, a formula, a flowchart someone handed you. Say fairly that it works
("do it this way and the answer is right"), then act out its problem: in a new situation you do not know which step to
change, and once you forget a step you cannot get back ([craft.md](../craft.md#i-motivation), technique 3). When the
viewer has an intuitive but wrong answer (doctors choosing 90%), use that as the foil and let it fail on real numbers
([teaching/rules.md](../../../teaching/rules.md#handling-a-misconception)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–7% | Something to get done, and the first method that comes to mind | The first 5 seconds are concrete (a scratched disc that still plays, a positive test report); the first method that comes to mind, or the memorized mnemonic, stated fairly in full: what it can do and where it falls short |
| 7–13% | What done looks like | Give the destination first: what you can do once it is done (256 bits using only 9 bits); say what this episode wants the viewer to be able to do, ideally as a few concrete situations ("given this set of numbers, you should be able to quickly estimate…") |
| 13–25% | A building block | Which simpler thing this procedure is built on (a parity check, a sample of a group of people, following i and j); what it can do and what it cannot: the thing it cannot do is the question the first step answers |
| 25–52% | Rebuild step by step: the first complete run | An example small enough to do in your head; each step: first ask the question it answers → do it → state the judgment → the conclusion stays on screen (principle 15 in [teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)); when done, check the answer another way; names (parity bit, Bayes factor) come only after it is done |
| 52–58% | Step card | Compress what was just done into three to five steps, one sentence and one judgment to watch for each; the card hangs on one side of the screen from here on (scene_kit's `get_checklist`) |
| 58–75% | A different situation | A new input; a second complete run by the step card, asking the viewer only before the one or two steps easiest to get wrong, pausing 2 to 3 seconds, revealing; the step being done lights up on the card |
| 75–88% | Common mistakes | First act out the mistakes learners make (a real example or data: the doctors' choices, "the derivative of a product = the product of the derivatives"), then the method's own limits (the shortcut failing with a large prior, two errors fooling the check); each done on the same object, saying the symptom and how to avoid it |
| 88–100% | Your turn | A situation not done in the video: guess the first step and the step easiest to get wrong, pause longer, reveal; one sentence on where else it can be used; the step card is the last picture |

**Measured pace** (four 3b1b videos): about 163–198 words a minute in English; the real numbers stay on screen from
start to finish; all four state the destination within the first 15%; the step card (when there is one) appears at
60–65%, followed by three situations done with it; where the viewer does it themselves the pause is 6 to 8 seconds
(Hamming code), which we change to 2 to 3 seconds per step. Other visual rhythm is in the style ([style.md](../style.md)).

---

## Short version (6 minutes or less)

As a short passage inside another episode (for example "now compute it once" at the end of a mechanism episode), or
when the plan's length is 6 minutes or less:

| Share | Section | Content |
|---|---|---|
| 0–8% | What to get done | One sentence of need + one sentence of destination |
| 8–50% | The first complete run | A small example, one question and one judgment per step |
| 50–58% | Step card | Three to five steps |
| 58–85% | A different situation | Ask the viewer at the step easiest to get wrong; the most common mistake is acted out here |
| 85–100% | One sentence | Where else it can be used |

**Leave out:** setting up the building block (one sentence), the method's own limits, your turn.
**Keep:** every step the answer to a question, the real numbers on screen, the step card, asking the viewer at the step
easiest to get wrong in the second run, one common mistake.
**Word count:** convert with the language reference's speaking rate.

---

## Quality bar

After watching, given an input not done in the video, the viewer can:

- do the first step, and guess most of the steps correctly before the reveal;
- point at any step and say what question it answers (so they can work it back out if they forget);
- say where the most common mistake will appear and how to avoid it.

What this adds to the models, concretely: 3b1b leaves the second run to the viewer (the Hamming code asks you to pause
and do it yourself; the chain rule gives a list of exercises without answers), which suits a viewer who pauses, and its
common mistakes lean towards the method's own limits. Every one of our episodes has a second complete run, the
viewer thinks first at the step easiest to get wrong, and "your turn" is always revealed; the mistakes learners make are
acted out first. Remembering only "I watched him do it once", without being able to say what each step answers, does
not count.

## Self-check

- [ ] The opening states the destination, and what this episode wants the viewer to be able to do (ideally as a few
      concrete situations).
- [ ] The first complete run: before each step, the question it answers was said, and after it, the judgment; no step is
      "here, just take this".
- [ ] When done, the answer was checked another way.
- [ ] The formula the viewer takes away to compute with is the form closest to real things (people, real objects).
- [ ] There is a step card of three to five steps, hanging on screen throughout the second run.
- [ ] The second run used a different situation in full, pausing before the one or two steps easiest to get wrong.
- [ ] At least one mistake learners make is acted out (symptom, cause, how to avoid it); the method's own limits are
      said too.
- [ ] The close has a "your turn" whose answer is revealed.
- [ ] The boundary was checked: every step really can be worked out, and the procedure is short enough; if not, this
      episode should go to Mason.
