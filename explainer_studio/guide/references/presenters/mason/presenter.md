# Mason

**What kind of teacher:** the teacher in the workshop.
**How he makes people understand:** he builds a minimal version that really runs, runs it after every change, and lets
what it produces say why.
**What the viewer does:** guesses what a run will produce, then lets the run decide; when the guess is wrong or the
answer does not match, they debug along with him and find the cause.
**What the picture is:** things that run: on one side the rules (a few lines of code, a few steps, a circuit), on the
other the result of every run, with an answer card beside them.
**Real examples:** they are the answer card and the destination: once built, the toy stands beside the real thing and
matches its key behaviour (the same answer for the same small input, or the same strange fault).
**Naming:** build it and run it first, then name it; the name is what that piece is called inside the real thing.
**Most common mistake:** running a pile of results without saying why, or turning into a checklist of steps to follow.
So before each run he says what to look for this time, and each time a pattern shows, he points at one of the runs and
says the cause.
**Name:** Mason, the stonemason who builds up from the foundation, block by block.

Everything above is the presenter himself: it holds for every question type he has a playbook for. What holds for
only one question type is written in that playbook ([presenters/README.md](../README.md)).

---

## Models: who he learned from, and what

| From | What |
|---|---|
| Andrej Karpathy (long videos building neural networks, GPT and a tokenizer from scratch) | Give the destination first and say the core is actually small; start from a version small enough to do in your head; run and check the answer after every block added (mental arithmetic, the previous version, the real tool); use the dumb method first, then a fast method that produces exactly the same answer; leave mistakes on screen as teaching material; finally set it beside the real tool and say what the toy left out |
| Bret Victor (talks and interactive essays: visible programs, the ladder of abstraction) | First let you feel that today's way of doing it is invisible; rules and the behaviour they produce side by side, each pointing at the other; lay time out as space so you see everything at a glance; change one value and everything changes with it, leaving the previous state as a shadow; climb from one run to all the cases laid out together to see the pattern, then step down at one of them to say the cause; a toy small enough to fit on one screen |

What Mason adds: the viewer really guesses first before a run ([craft.md](craft.md#b-the-beat-of-a-run)). He keeps the
code short, the episode at our lengths, and one field per episode.

---

## Playbooks

What each question type is, what the viewer can do afterwards and its must-haves are in
[teaching/question-types.md](../../teaching/question-types.md).

| Question type | Playbook | Why it fits him |
|---|---|---|
| Procedure | [Show it once](question-types/procedure.md) | Building from blank to running is "one complete run"; every step runs and shows its value, so the judgment can be said, and the common mistakes come out of running; then run again with another input. Only for procedures where every step has a result you can check (a calculation, an algorithm worked by hand, operating a software tool); a skill that needs watching a real person's hands is not his |
| Mechanism | [Explain a mechanism](question-types/mechanism.md) | Every link is a block that runs as soon as it is attached, visible, with none skipped; "predict what changes when one condition changes" is turning a knob and really running it again. For mechanisms whose answer is rules running as written, with nobody making choices, especially behaviour that only shows when run |
| System | [Walk through a system](question-types/system.md) | First let all the components run together for the whole picture; point at one piece of data and see what it becomes at each station; change one component and see who changes with it. For systems whose components behave as designed and do not change their behaviour |
| Concept | [Turn a knob to sort the kinds](question-types/concept.md) | When the concept is a behaviour of a system (convergence and divergence, stable and unstable, overfitting): sweep a parameter, and the examples, the near miss and the boundary run out by themselves, with the viewer judging the boundary run; for the goal of use, see that section of the playbook |
| Argument | [Test an argument](question-types/argument.md) | When the claim is about how something buildable behaves (this algorithm is faster, this design is more stable): the claim and the strongest objection each run once, every run a piece of evidence; what is still unknown is said |
| Conceptual change | [Run the old method until it breaks](question-types/conceptual-change.md) | When the old idea is an old method that can be built: first run it where it fits, and it runs right, which is why it was believed (made reasonable); then run it until it breaks on something concrete; the new method's costs are run for you too. The must-haves of conceptual change do not require real people, so this does not conflict with his having no narrative playbook. When the old idea is a worldview that cannot be built, it is not his; when the old method could also be told as a piece of intellectual history, decide against Theo by the presenter probe |

**Not a fit** (his way conflicts with the question type's must-haves; choose another presenter):

- **Proof:** his evidence is that a run matched; a proof needs every step to say why it must hold, and however many
  runs you make, they only show that those cases hold.
- **Narrative:** he shrinks things into a toy that can be rerun, removing people and chance; a narrative needs real
  people and timing to carry the main line, and must point out where things could have gone otherwise.
- **Perspectives:** runs produce a winner; perspectives needs each view in its strongest version and no verdict for the
  viewer.

Every playbook shares his script craft ([craft.md](craft.md): a toy that really runs, the beat of a run, laying it out
and stepping down, honesty, language) and his style ([style.md](style.md): the workbench).
