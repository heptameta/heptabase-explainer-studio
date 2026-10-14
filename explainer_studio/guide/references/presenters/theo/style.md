# Theo's style: the blackboard (3Blue1Brown style)

Contents: [Measurements](#measurements) · [Colour](#colour) · [Type](#type) · [Camera](#camera) ·
[Aesthetic do and don't](#aesthetic-do-and-dont) · [Self-check](#self-check) ·
[Design system values](#design-system-values-manimgl-units)

A pure black canvas, Computer Modern serif, the Manim palette, quiet transitions. It suits content built on abstract
structure, such as mathematics, physics and computer science, and any series that wants the picture to look "like a
blackboard that moves".

Basis: close viewing of six 3Blue1Brown videos, and the colour constants in the ManimGL source code.

---

## Measurements

The numbers in this section are 3b1b's style, not the essence of teaching. Other good teachers can have completely
different jokes, question counts, lengths and cut rates and still teach very well. Use these numbers when you use this
style; with another style, that style's numbers govern.

### Script measurements (3b1b)

| Measure | 3b1b, measured | Our target |
|---|---|---|
| Speaking rate | 180–195 wpm (including silent animation time) | The language reference's rate |
| Length | 13–28 minutes, 2,500–5,600 English words | No default: as long as that one question needs (the plan decides; [teaching/plan.md](../../teaching/plan.md)) |
| Sentence length | Average 27–31 words; long sentences with short punches between them | Long sentences within the language reference's limit, mixed with short punches |
| Density of "you" | 17–21 per thousand words; "you and I" increases episode by episode | Second person dominant, "we" as company |
| Questions to the viewer | 3–12 per video (mostly embedded "you might be thinking…") | At least 6 per 20 minutes |
| Key-point labels | 1–3 | At most 3 |
| Causal recaps | 1–2 | One between each act |
| Humour | A low-key joke every 3–5 minutes, growing out of the sources themselves, never in the middle of an argument | The same |
| Opening to the first new idea | Can be late (for example at 16%), but the foil before it is content in itself | First question within 60 seconds, foil finished within 3 minutes |

The targets that depend on the language (speaking rate, sentence length) come from the narration language's guide
(`languages/<language>.md`).

### Visual rhythm (3b1b, measured; the range across five videos)

| Measure | Range |
|---|---|
| Hard cuts | 0.15–1.5 a minute (the fewest: a 27-minute video with only 4 cuts) |
| Small change | every 6.6–8.8 seconds |
| Large rearrangement | every 10.9–15.2 seconds |
| Completely new composition | every 19.2–52.7 seconds |

Targets:

- **Something appears or moves every 7 to 9 seconds** (a label, a box, a number ticking).
- **A large rearrangement every 12 to 15 seconds**; **a completely new composition every 20 to 50 seconds**.
- **Fewer than 1 hard cut a minute**, used only around live footage and when "switching layers". The longest single
  take runs 5 to 13 minutes.
- **"Build up step by step; do not replace"**: 2 to 4 frames in a row are often the same layout with one more element
  each time.

---

## Colour

### The colours of the two layers

| Layer | Colour | Share | Meaning |
|---|---|---|---|
| Main canvas | `#000000` pure black | 75–90% | The mathematical world: graphs, equations, 3D space |
| Commentary layer (meta) | `#1A1A1A` dark grey | 9–30% | "Words about the mathematics": recaps, the questioner, "last episode", question cards, section titles |
| Inset border | `#454545`–`#888888`, 1–2 px | | A scene shrunk onto the commentary layer |

**When stepping back to comment, shrink the current scene into a thin-bordered 16:9 inset on the dark grey
background.**

### Palette (ManimGL constants; measured to match)

| Role | Constant | Hex |
|---|---|---|
| Main emphasis, "look here" | `YELLOW` | `#FFFF00` (fill at about 0.3 opacity) |
| Second concept | `TEAL` | `#5CD0B3` |
| Blue family | `BLUE_C` / `BLUE_D` / `BLUE_E` | `#58C4DD` / `#29ABCA` / `#1C758A` |
| Red, annotation | `RED_C` | `#FC6255` |
| Others | `MAROON_C #C55F73`, `PURPLE_C #9A72AC`, `GOLD_C #F0AC5F`, `GREEN_C #83C167`, `PINK #D147BD` | |
| Text | Titles `WHITE`, body `GREY_A #DDDDDD` | |
| Dimmed | White at about 0.3 opacity | |

Grant's colour roles: `YELLOW` = look here, key word, difference vector; variables in order `BLUE` → `TEAL` →
`RED`/`PINK`; a graphed curve in `TEAL` (stroke width 3) with a moving point in `YELLOW`; helper lines white, stroke
width 1.

---

## Type

- **Almost everything is Computer Modern (LaTeX) serif:** mathematics, titles, labels, explanations, speech bubbles. No
  sans-serif UI font. The exceptions are brand logos, screenshots, and one deliberate block of monospace (for example a
  passage of "extra details for the especially curious").
- Latin text in CMU Serif, mathematics in LaTeX. The faces for another script are in that language's guide
  (`languages/<language>.md`).
- Sizes (as a share of the frame height): titles about 6% (`font_size` 60–72); labels and equations in use 3.5–5%
  (36–48); notes and image credits 2–2.5% (20–24); the star formula 7–8%.

---

## Camera

- **2D: mostly still.** Objects move, grow and fade; attention is guided by "adding" and "dimming", not by moving the
  camera.
- **3D: slow ambient rotation**, with an occasional dolly or pan. A 3D matrix turns to face the viewer before it is
  read.
- **Push into the inner layer:** stack → matrix → last column → list of probabilities.
- **Shrinking into an inset** is the standard way to "step back".
- Grant's principle: stay in 2D unless necessary, "like a blackboard".

---

## Aesthetic do and don't

**Do**

- Black canvas for the mathematics, the dark grey commentary layer for comments; when stepping back, shrink the scene
  into an inset.
- Serif type; titles about 6%, labels about 4%.
- The questioner appears briefly every 2 to 4 minutes, and only asks and reacts. (This is 3b1b's practice; the shared
  rules let the questioner voice a wrong guess too: [teaching/visual.md](../../teaching/visual.md).)

**Don't**

- Sans-serif UI fonts, gradients, shadows, fancy backgrounds.
- Let a character explain the content.
- Let the questioner do the explaining (the questioner may only ask and react).
- Hard cuts, except in a live-footage montage: fewer than 1 a minute.

## Self-check

When you use this style, add these items to the self-check (the style items of [craft.md](craft.md#e-self-check)):

- [ ] At least 6 questions per 20 minutes?
- [ ] Low-key humour every 3 to 5 minutes, never in the middle of an argument?

Grant's preferences in code: `SurroundingRectangle(...).set_stroke(YELLOW, 2)` plus `FlashAround`; `Indicate` rarely.

---

## Design system values (ManimGL units)

- Frame `FRAME_HEIGHT = 8`, `FRAME_WIDTH ≈ 14.22`. Buff: SMALL 0.1 / MED_SMALL 0.25 / MED_LARGE 0.5 / LARGE 1.0.
- Background `#000000` (ManimGL's default is `#333333`; change it); final output 1920×1080 at 30 fps.
- Font sizes: 72 (title) / 60 / 48 (default) / 36 (label) / 24 (note). `font_size=144` ≈ 1 unit high.
- Stroke widths: default 4; curves 1–3; grid lines 1; emphasis box `(YELLOW, 2)`; emphasis arrows 5–10; backstroke
  `(BLACK, 3–5)`.
