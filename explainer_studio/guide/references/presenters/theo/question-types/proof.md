# Theo's proof playbook: Find the proof

Contents: [Skeleton](#skeleton) · [Short version](#short-version-6-minutes-or-less) · [Quality bar](#quality-bar) ·
[Self-check](#self-check)

**The question it answers:** proof, "Why must this be true?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can state the key idea of the
proof and follow each step, confirming that it holds; and can say how a key idea like this could be found next time.

**How it meets the must-haves:**

- **The claim is first made clear with examples:** the claim becomes a picture and is read sentence by sentence on one
  concrete example; say "what counts as having proved it". Before the proof, make the viewer believe it (work out the
  answer on a simpler version, or run a simulation once), so the proof answers "why must it be".
- **The key idea is stated on its own:** a passage about it alone, before any details, with a text card on screen. Say
  also where it comes from: a heuristic written on a card (restate the problem in terms of what you added; give a vague
  idea a number; use the defining feature of each object).
- **Every step says why it is allowed:** one beat per step on the same picture, one reason per step. A small lemma it
  uses is proved on the spot on a clean picture, or you say plainly what it is and why it may be used. Deep in, pause
  and say "what we are doing now".
- **Say what it buys us:** walk the key idea once more in another case (low dimension → high dimension, odd → even), and
  say where it still relies on intuition. The close hands over something bigger than this problem (a heuristic, a tool,
  where this result leads).

**Use it for:** a claim for which these three questions have answers. Does the proof have **one thing you add** that
carries everything (a construction, another way of looking, an invariant, cutting into small pieces and comparing)? Can
the claim be **drawn in one picture**? Is there a **simpler version** to play with first? For example "Why is the area
of a sphere 4πr²?", "Why is the probability of this random process exactly 1/4?", "Why is Huffman coding always the
shortest?", "Why does the chain rule hold?", "Why is √2 not a fraction?". One key idea per episode; when a chapter has
several lemmas, the plan arranges them as several questions
([teaching/plan.md](../../../teaching/plan.md#planning-how-many-episodes-each-answering-what)).

**Not this one:** the viewer wants "why does it happen" (Explain a mechanism: [mechanism.md](mechanism.md)); "how to
compute it, how to write a proof" (procedure: [procedure.md](procedure.md)); how a method of proof or an axiom changed
over history (How an idea changed: [conceptual-change.md](conceptual-change.md)); why an empirical claim deserves
belief (Test an argument: [argument.md](argument.md)). When the whole passage is only algebra and no visible key idea
can be found, do not force it into this playbook: split it smaller through the plan, or give only the short version
inside another episode.

**Versus other presenters:** only Theo has a playbook for proof. Fabian's small world can only make a result look
plausible; Mason's run matching the answer shows only that the cases run are true; Sophie's evidence is the viewer's
judgment ([presenters/README.md](../../README.md)). Theo may borrow one move from Mason: run a simulation first so the
viewer **believes** it, but say clearly that this is not a proof; the proof is the "why" of every step that follows.

**The core idea of this playbook is "you could have found it too".** An ordinary proof video makes people nod along at
every step. This playbook wants the viewer to take away "how to find a step like this next time". So the key idea always
comes with where it came from, and the standard of the explanation is: **with these tools in your hands, would you have
thought of it too?** (What Grant calls a "rediscoverable proof"; [craft.md](../craft.md#c-principles-grant-has-stated).)

**The foil is the brute-force route:** integration, coordinate algebra, expanding all the way. Say fairly that it works
("yes, you can compute it"), then its problem: it can only verify, not make anyone understand, and it does not carry
over to the next problem ([craft.md](../craft.md#i-motivation), technique 3). When there is no brute-force route, the
foil is the viewer's intuition ("isn't this obvious?"); let it fail on an example
([teaching/rules.md](../../../teaching/rules.md#handling-a-misconception)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | The claim and the suspense | The first 5 seconds are the claim's picture (a sphere and four circles, a tetrahedron inside a sphere), not a line of formula; add a "why it deserves doubt, or why it is hard": the number is too clean, many people get it wrong, how can several statements be the same |
| 8–18% | The claim made clear on an example | Read the claim sentence by sentence, drawing one stroke on the same example for each, with the sentence being read marked on screen; finally say "what we must prove" as one checkable sentence; terms (focus, pivot) come after the example |
| 18–22% | Standard and route | Say this episode's standard once: not just the answer, but making you feel you could have found it. When there is a brute-force route, state it fairly here in full (the foil); with two routes, give a roadmap |
| 22–42% | Play first, believe first | Start from a simpler version (one dimension lower, two or three points, a small piece) and work out the answer there, or run a simulation so the ratio converges; the viewer guesses the simple version's answer first. Say "now we believe it; next we ask why it must be" |
| 42–52% | Stuck | Carry the simple version's method over to the original problem and it does not work; or voice a worry (could it run off outside?). This passage makes the key idea "have to appear" |
| 52–62% | The key idea | A passage about it alone, a text card on screen; then a heuristic card saying where it comes from; a guess: "With this idea, how do you think the answer will fall out?" |
| 62–80% | Step by step, each with its why | The same picture, one beat per step (principle 15 in [teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)); a small lemma is proved on the spot on a clean picture, and on cutting back you say "these two lines are the two lines from before"; after the hardest step, pause and restate the goal |
| 80–88% | Walk it again, and say where intuition remains | Another case (low → high dimension, odd → even, cone → cylinder): what in the key idea stays the same and which step changes; one sentence on where this proof relies on intuition and how the formal version differs (said here, not left to the video description) |
| 88–100% | What it buys | The portable heuristic appears once more and is applied to a problem not in the video (one sentence, one picture); where this result leads; the names (Dandelin spheres, invariant) are given here; a reframe, not a summary |

**Another order: see the whole first.** When the key idea adds a construction out of nowhere that the viewer could never
stumble on from the simple version (two spheres, projecting outwards), move "the key idea" to 15–25% and give a draft
without details first; drop "Stuck"; move "why would anyone think of it" to the close. Record which order you chose,
and why, in `design.md`.

**Measured pace** (four 3b1b videos): about 175–185 words a minute in English; the key idea appears at 15% (see the
whole first) to 55–60% (discovery order); each has 1 to 3 places where the viewer thinks for themselves, with a 5 to 14
second pause before the reveal; each has 2 to 4 text cards on screen with a heuristic or the key idea; hard cuts appear
almost only around live footage. Other visual rhythm is in the style ([style.md](../style.md)).

---

## Short version (6 minutes or less)

As a short passage inside another episode (for example the "why it must hold" passage in a mechanism episode), or when
the plan's length is 6 minutes or less:

| Share | Section | Content |
|---|---|---|
| 0–10% | The claim | One picture, one sentence of what to prove; ask "why must it be?" within 10 seconds |
| 10–25% | Believe first | A small example or one simulation (at most 40 seconds) |
| 25–40% | The key idea | One text card; one sentence on where it comes from |
| 40–85% | Every step with its why | Only the main-line steps; a small lemma in one sentence, with its name |
| 85–100% | What it buys | One sentence of heuristic + one sentence on where the result leads |

**Leave out:** the "Stuck" passage (just say "computing it directly is hard"), the roadmap, walking it again, a long
close.
**Keep:** the claim made clear on an example first, the key idea in its own passage, one reason per step, the heuristic
card, an honest sentence on where intuition remains.
**Word count:** convert with the language reference's speaking rate.

---

## Quality bar

After watching, the viewer can do these four things:

- state the key idea in one sentence ("the number of points on each side never changes"), without looking at the
  picture;
- point at any step of the proof and say why it is allowed;
- given a small variation (an even number of points, 2D to 3D), say whether the key idea still holds and which step
  changes;
- state the heuristic, and think of a place not in the video where it could be used.

What this adds to the models, concretely: 3b1b leaves part of the proof to the viewer, with the answer in the comments
or the video description (the sphere's second proof, the formal Putnam write-up, equal tangents on the cone), which
suits a viewer who pauses. Our viewers do not pause, so **every step is completed on screen, and every "try it yourself"
becomes a guess that is revealed**; how the formal version differs is said in one sentence in the video, not pushed to
the description. Only finding it "beautiful", without being able to state the key idea or the reason for any step, does
not count.

## Self-check

- [ ] Before the proof starts, the claim was read and drawn on a concrete example, and "what counts as having proved
      it" was said.
- [ ] Before the proof, the viewer already has a reason to believe it (the simple version's answer or a simulation),
      and the narration said "next we ask why it must be".
- [ ] The key idea has its own passage and a text card, and is stated before any details.
- [ ] The key idea comes with where it came from (a heuristic), and the heuristic is applied again in the close to a
      place not in the video.
- [ ] Every step has a reason said aloud; each small lemma used is proved on the spot, or named with why it may be used.
- [ ] The key idea is walked once more in another case, saying which step changes.
- [ ] One sentence said where this proof relies on intuition and how the formal version differs, without pushing it to
      the description.
- [ ] No "answer left to you" exercise; every "try it yourself" was paused and revealed.
- [ ] When there is a brute-force route, the foil states fairly what it can do and why it is still not enough.
