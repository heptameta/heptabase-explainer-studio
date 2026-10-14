# Subject: mathematics (and STEM whose language is mathematics)

Use this for mathematics, physics, theoretical computer science, machine learning, statistics, and any content whose
core is formulas and structures. The archetype and the examples come from 3Blue1Brown. Numbered techniques below refer
to [presenters/theo/craft.md](../presenters/theo/craft.md).

## 1. What explained means

The result should **feel discovered**, not dropped from the sky: the viewer finishes thinking "in their place, I might
have thought of that step too". Grant says a proof should be "rediscoverable", and distinguishes proofs that let you
understand morally why something holds from proofs you can only verify.

## 2. Spine objects

A number line, the graph of a function, vectors and matrices, geometric figures, grids and lattices, a toy model with
its assumptions stated (technique 11), a simulation whose parameters can be turned.

## 3. Its own ways of drawing

- **Formulas grow piece by piece:** the derivation column at the top left, lines joined by ⇓, each line coloured, the
  picture beside it. At most three lines at once: when a new line comes in, the oldest leaves, and when a derivation is
  done, the whole column leaves ([teaching/visual.md](../teaching/visual.md#attention-one-place-to-look-at-a-time)).
  Terms not yet discussed appear first at about 25% opacity ("F = −kx + c₂x² + …"); unknowns are placeholders `?` or
  `???`.
- **T6, derivation on the left, picture on the right:** the derivation column at the top left, a picture in the same
  colours on the right.
- **Colour in a formula is a pointer:** colouring a symbol links it to the object of the same colour in the picture
  ([teaching/visual.md](../teaching/visual.md#colour)).
- **Live readings:** when a parameter changes, the number on screen ticks with it (`DecimalNumber`).
- **Physical motion keeps its real time:** animations whose timing means something (oscillation, motion) use linear
  time, not the default easing (the timing is part of the mathematics; easing would hide it).
- The script techniques most used in mathematics: 12 exaggerate then take the limit, 13 numbers before symbols, 14 show
  or simulate before deriving, 15 read a formula term by term then push it to extremes, 16 cousin problems, 22 the
  picture before the paper's formula, 23 flag non-standard notation.

## 4. The typical foil

The textbook's standard account: definitions first, every step correct but unmotivated ("you can't say it's wrong, but
every piece falls from the sky").

## 5. Honesty rules

- **The picture of a quantity grows on the thing it measures:** the square of a distance is a square whose side is that
  distance (from the point to the centre); the area under a curve hugs the curve (use `scene_kit`'s `get_area_under`,
  which follows the curve when it moves). Grown off to the side, or deformed separately, the viewer cannot see that
  they are the same thing.
- A toy model states its assumptions, and questions them later (techniques 11 and 34).
- Say honestly where you wave your hands; offer skipped proofs as tiered exercises (technique 37).
- Explain artefacts of rendering (for example discretization, approximation).

## 6. The core that cannot be dropped

**Every episode has at least one real derivation or check, done step by step on screen.** Pretty pictures and a
conclusion are not enough. The derivation's length stays within the viewer's capacity: every algebraic step is a link
([teaching/plan.md](../teaching/plan.md), links). A derivation longer than the capacity becomes a check in this episode
(verify with real numbers, look at the lowest point of the graph); the derivation gets its own episode or is left to the
book. A check is finished mathematics too.

## 7. Common failures

- Opening with a definition.
- No real derivation at all; satisfaction replaces understanding (the "Feynman effect").
- A whole formula dropped on screen at once, never read term by term or pushed to extremes.
- The same symbol in different colours at different times.

## 8. Benchmark work

The whole 3Blue1Brown catalogue.

## How formulas are said

Say what it means; do not read it symbol by symbol. Language-specific details (for example how to say `q² < 2`, Greek
letters and large numbers in the narration language) are in the language reference ([languages/](../languages/)).

## Self-check

- [ ] Has every formula been read term by term and tested at its extremes?
- [ ] Does every derivation come after a demonstration or simulation?
- [ ] Does every episode complete at least one full derivation or check on screen?
- [ ] Have all numbers and derivations in the script been checked by recomputing them?
