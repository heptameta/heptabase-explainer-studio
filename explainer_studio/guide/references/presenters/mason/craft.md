# Mason's script craft

Contents: [A. A toy that really runs](#a-a-toy-that-really-runs) · [B. The beat of a run](#b-the-beat-of-a-run) ·
[C. Lay it out, then step down](#c-lay-it-out-then-step-down) · [D. Honesty](#d-honesty) ·
[E. Language and code](#e-language-and-code) · [Self-check](#self-check-every-playbook-must-pass)

Basis: section-by-section breakdowns of three Karpathy videos built from scratch (backpropagation in a neural network,
GPT, the tokenizer) and four Bret Victor works (learnable programming, the ladder of abstraction, visible programs, a
medium for thinking), and where viewers got lost in our own videos. Each of his playbooks (`question-types/`) is built
on these techniques; the shared rules ([teaching/rules.md](../../teaching/rules.md)) apply as always.

---

## A. A toy that really runs

An episode has only one toy, and all the reasoning rests on running it; the real thing enters only at the opening and
the close. In the beat where the toy first appears, say that it is not the real thing ("this is a toy we built
ourselves, not GPT"); otherwise the viewer thinks they have been watching the real thing all along.

1. **Give the destination first:** the opening first shows the real thing working (an output, a string of strange
   faults, a pain that is invisible today), then says its core is actually small ("the whole engine is about a hundred
   lines").
2. **Small enough to do in your head:** the toy starts from the smallest version that runs: a car with three sensors, a
   binary search over six letters, an equation with only two inputs, a text of eleven letters. The viewer can think out
   what it will do next without a calculator.
3. **One toy per episode:** no change of field, no change of toy; when the situation must change, what changes is the
   input or the environment, and the toy stays the same.
4. **The toy need not be a program:** a computation graph filled in cell by cell, merge steps worked by hand on paper, a
   3×3 table, a circuit: anything that runs by rules and produces results. When the sources have nothing that can be
   built and run to a result, the episode is not Mason's.
5. **It really runs:** write the toy as a small program in the series' shared code, `production/shared/<episode>_toy.py`
   (plain Python, numpy allowed). Scenes take every number and every piece of output from it; no numbers are typed by
   hand into a scene. The end of the file checks the answers with a few `assert` lines (values worked by hand, the
   previous version's results, numbers from the sources or the real tool). Scenes import the numbers with
   `from shared.<episode>_toy import ...`, so it runs once at every render, and a mismatch fails the render. Call heavy
   computations through scene_kit's `run_toy`, which caches the result and reruns only when the toy's file changes
   (see `rendering/`).

## B. The beat of a run

One beat is one link (principle 15 in
[teaching/rules.md](../../teaching/rules.md#principles-every-presenter-follows)); six to eight beats per episode:

1. **What to look for this time:** one sentence saying the question this beat answers. When growing block by block, it
   is where the previous version falls short on something concrete (the text it writes is gibberish; the slope should
   be 2 and it computes 1); when turning a knob, it is what happens at this value; in a procedure, it is what the next
   step should be.
2. **Change one thing:** attach a component, turn a labelled knob, or do the next step; the changed line or block lights
   up.
3. **The guess:** the question written on screen, with two or three options or one blank: bigger or smaller? About how
   much? The same as the previous version? Pause 2 to 3 seconds, and really let the viewer think. Guess a direction or a
   rough size, never decimals.
4. **Run:** the input flows through what has been built, and the result appears at the end.
5. **Check the answer:** the answer card (worked in your head, the previous version, the real thing) gets a tick or a
   cross; the scoreboard gains a line.
6. **One sentence:** why this block had to be added, or why this knob affects the result this way; pause
   (`pause_duration_seconds`).

**When it does not match:** once or twice per episode the answer card first gets a cross, the symptom is visible, and
you follow it to the cause and fix it. Use only mistakes that really happen: in a procedure, the ones beginners really
make; in a mechanism, the conditions that really make it run wrong (the same variable used twice; diverging when the
step is too big; deeper stacks that will not train). No typos. If you cannot find a mistake that really happens, do not
invent one.

## C. Lay it out, then step down

Use it to see a pattern or the whole picture (most common in mechanism and system):

1. **First say what to look for,** then lay it out: the viewer cannot pause, and a full screen without saying where to
   look shows them only lots of things moving.
2. **Lay time out as space:** each step of one run stays as a point, joined into a trajectory; many runs are stacked
   together, or set out as a row of small pictures, so everything is seen at a glance.
3. **The previous state stays as a shadow:** when turning a knob, the previous result stays faintly behind.
4. **Always step down:** each time a pattern shows, point at one of the runs (best is a pair that differ only slightly
   yet end very differently), play them side by side in slow motion, and say why in one sentence. Seeing the pattern is
   not understanding; being able to say why that run went that way is.
5. **A small ladder in the corner** marks whether we are now looking at one run or at all of them.

## D. Honesty

- **Every number and output on screen is something the toy really produced** ([A](#a-a-toy-that-really-runs), item 5).
  When we cannot run the sources' numbers (they need big machines or real data), label the source and "we did not run
  this".
- **Say what the toy left out:** when the close sets it beside the real thing, say clearly what is added at scale (more
  data, more layers, engineering details); never "the rest is just efficiency".
- **When growing block by block, every block is brought in by one concrete failure of the previous version;** when that
  is not possible, say directly "this block comes from experience, not from reasoning"; do not invent a failure.
- **Do not belittle formulas and derivations:** you may say "there is no easy formula here, so we run it"; when what is
  wanted is "why it must hold", that passage is not Mason's.
- **Mark personal preferences as opinions,** not conclusions.

## E. Language and code

- **Code is a supporting actor:** at most one to three lines of idea-carrying code on screen at once, in large type;
  the rest passed over in one sentence. A bar for "how big the whole thing is" (for example a hundred lines) lights up
  as far as you have got, so the viewer knows where they are in the whole.
- **What can be drawn as a machine, a table or a picture is not shown as code:** the viewer does not necessarily
  program.
- **Label a knob before turning it:** the viewer must know what the number means before you turn it for them.
- **Do not assume earlier things were watched:** each episode must stand on its own; components built in earlier
  episodes are filled in with one sentence and one picture.
- Short sentences, one thing per sentence; dry humour grows out of strange results the toy produces, never in the beat
  that says why.

---

## Self-check (every playbook must pass)

- [ ] The opening first shows the real thing working, and says the core is actually small.
- [ ] One toy per episode, small enough to do in your head; it really exists as `production/shared/<episode>_toy.py`,
      every number on screen comes from it, and its end has `assert` lines checking the answers.
- [ ] Every beat: what to look for this time, change one thing, pause to let the viewer think (ask only when they would
      really want to), run, check the answer, one sentence of why.
- [ ] The one or two mismatches are mistakes that really happen; once fixed, the cause can be said.
- [ ] Every layout first says what to look for, and every pattern steps down to one run with its cause said.
- [ ] The close sets it beside the real thing and says what the toy left out.
- [ ] Code on screen is never more than three lines at once; nothing that could be drawn is shown as code.
