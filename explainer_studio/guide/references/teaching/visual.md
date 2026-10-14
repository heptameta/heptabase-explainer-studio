# Visual rules

Contents: [Pacing](#pacing) · [Two layers](#two-layers) · [Colour](#colour) ·
[Attention](#attention-one-place-to-look-at-a-time) · [Text](#text-the-picture-remembers-the-point-for-the-viewer) ·
[Layout templates](#layout-templates-169) · [Camera and attention](#camera-and-attention) ·
[Emphasis toolbox](#emphasis-toolbox) · [Openings, sections, endings](#openings-sections-endings) ·
[Text-heavy moments](#text-heavy-moments-without-turning-into-slides) · [Do and don't](#do-and-dont)

Visual principles that hold in any style and have nothing to do with taste. The presenter follows them. Concrete
palettes, fonts, pacing numbers and camera habits belong to the presenter's style (for example
[presenters/theo/style.md](../presenters/theo/style.md)).

Basis: close viewing of six explainer videos, and the colour constants in the ManimGL source.

## Pacing

The exact numbers depend on the style. These principles hold in any style:

- **Something is always happening on screen:** a label, a box, a number ticking. A long, completely still frame needs a
  reason.
- **Build up, do not replace:** consecutive frames are often the same layout with one more element each time.
- **Few cuts:** move forward by adding, dimming and transforming. Use hard cuts only for live footage and for switching
  layers.

## Two layers

- **Content layer:** the subject's own world (diagrams, formulas, systems, text objects).
- **Commentary layer (meta):** talk about the content: recaps, the questioner, "last episode", question cards, section
  titles.
- **To step back and comment, shrink the current scene into a small inset with a thin frame, placed on the commentary
  layer.**

The style decides the two layers' colours (in the 3b1b style, pure black and dark grey).

## Colour

### Colour carries meaning (most important)

- **One concept, one colour, for the whole video** (in Explainer Studio, for the whole series). In *Attention*, Q is always
  yellow, K always cyan, V always red: in matrix labels, vector arrows, grid headers, formulas and parameter counts
  alike.
- **Colour in a formula is a pointer:** colouring a symbol links it to the object of the same colour in the picture,
  with no arrow needed.
- **Budget:** most frames have 0 to 2 saturated hues plus white. Frames with 4 or more colours are under 8%. **A new
  colour appears only when a new concept enters.**
- Red and blue by sign in a matrix are texture, not meaning.

The concrete palette is in the style. The concept colour table is in the series bible, and defined in the series'
shared code under `production/shared/`.

## Attention: one place to look at a time

Whatever the subject or the presenter, the picture never overwhelms the viewer. Being overwhelmed feels like this:
several places on screen are talking at once, you do not know where to look, so you pause the video. In every beat:

- **One focus:** the viewer looks only at what the narration is talking about. Everything else on screen is needed to
  understand it (the axes of the same diagram, the conclusion just made); anything else leaves.
- **At most three groups of things in a frame:** the main picture being talked about, plus two more (the conclusion
  just made, a card, the options of a question). When a new group comes in, a finished one leaves first. When the same
  picture has been stacked on for six beats or more in a row, change the picture. When different subagents write
  different scenes, each scene follows this; do not each pile more on.
- **Finished things leave; they are not just dimmed:** what the next one or two beats do not mention fades out. Dimming
  is only for something that comes back right away, and a frame has at most one dimmed group.
- **At most three lines of derivation:** when a new line comes in, the oldest leaves (or collapses into a one-line
  summary). When a derivation is done, the whole column leaves before the next one starts.
- **Never fill the left and right halves at once:** in a side-by-side comparison, the side the narration is not talking
  about dims or shrinks. Never make a frame with both sides full.
- **Text for checking sources stays off screen:** page numbers, equation numbers, "these are the book's numbers; we did
  not run them". It goes in the beat's `citation`. On screen there is only one line of small text, in the beat that
  quotes the original, and it leaves when the beat is done.
- **When a section is done, clear the screen before the next:** at a section change, clear the picture; do not keep
  adding to the old one.
- **Check:** cover the narration and look at each frame: can you tell at a glance where to look?

## Text: the picture remembers the point for the viewer

The narration disappears once spoken. What stays on screen is the time the viewer has to finish thinking about it. The
standard: **a viewer who missed a line can rebuild the point just made from the text and pictures still on screen.**
Picture and narration complement each other; the viewer should not need full attention on both to piece it together.

- **What stays on screen is that link's conclusion itself.** In mathematics it is often a formula or a labelled
  diagram. In other subjects it is often one short complete sentence (who, what, so what; about one line), for example
  "A new king, the same set of rules", not two nouns like "new king" and "unchanged". Noun labels are for the objects
  themselves. The conclusion sentence is still there during the pause (`pause_duration_seconds`) and at the start of
  the next beat. Finished labels leave first; no label that is no longer discussed stays longer than the conclusion.
- **Mark what a statement is:** an intuition to be overturned, a rival's claim, an assumption, an unproven claim: the
  moment it appears, mark what it is ("Intuition:", "Rival:", "Assumption:", "The author's hypothesis"). When it is
  overturned, strike it through on screen and put the new sentence in its place (`get_claim` and `strike_claim` in
  `scene_kit`). Options ruled out in a guess are struck through too. A hypothetical case is not drawn into the real
  grid or column ("what if there were no parliament" is not a cross on the real country's parliament): draw it beside,
  marked "Hypothetical".
- **A quantity that keeps changing stays drawn the whole time:** what keeps changing along a causal chain
  (concentration, charge, the height of energy, who holds power) is an object always on screen, and it moves once at
  every link. A quantity that exists only in the narration, the viewer cannot hold on to.
- **Say the wrap-ups and transitions aloud:** a conclusion sentence on screen reinforces the narration; it does not
  replace it ([teaching/rules.md](rules.md), principle 16).
- **The big picture comes back at seams and steps aside for details:** at each seam, return to the presenter's picture
  the viewer has already seen (home picture, scene, conclusion board, scoreboard, position board, big-picture map),
  point at where we are, and let it leave after the two sentences. While explaining a detail, keep only the
  main-question line: small, faint, in a fixed place. No table-of-contents strip listing the names of later parts (the
  same principle).
- **Text never sits on lines:** text is never on an arrow, a frame, a curve or other text. A label goes beside the line
  or inside the box. The automatic checks report `text_overlap`; fix every one.
- **Text on screen at once:** usually 1 title plus 1 to 4 short labels or one group of formulas, plus the conclusion
  sentence of the link just made. No bullet lists, no paragraphs (see [Do and don't](#do-and-dont)).
- **Check with the narration covered:** `preview` writes `by-beat` screenshots: the frame at the end of each beat, with
  its narration printed under it. Cover the narration first and look only at each frame. Can you say the point just
  made? Can you tell which statement is about to be overturned? Can you tell which part of the main question this frame
  is about (at a seam, the whole route should be visible)? Does any text on screen contradict the narration's
  conclusion?
- Text handling specific to a subject is in its subject reference (for example, formulas growing piece by piece in
  mathematics). Fonts and sizes are in the style and the language reference.

## Layout templates (16:9)

The script's `visual` names a layout from T1 to T10. Make it concrete enough to write code from: the layout template,
the objects that appear, the animation verbs (Write, ShowCreation, TransformMatchingTex, FadeTransform, dim), the
colours (by the names in the series bible) and the camera. T3 needs the series to have a questioner. T6 is mainly for
derivations ([subjects/mathematics.md](../subjects/mathematics.md)). T10 is mainly for people and texts
([subjects/history.md](../subjects/history.md)).

On a black canvas, 65 to 82% of the pixels are near black. A typical frame is one focus object plus 1 to 3 satellites.

**T1 Single main object** (the most common): the object centred or slightly low, a title or formula above.

```
+------------------------------------------------+
|            title / formula (6%)                |
|        [  focus object, 50-60% wide  ]         |
|                              small label ->    |
+------------------------------------------------+
```

**T2 Commentary layer: title plus inset** (background `#1A1A1A`): "Last episode", "Key point #2", "Mini-lesson:
Softmax".

```
+------------------------------------------------+
|          Last episode / Key point #2           |
|   +----------------------------------------+   |
|   |  shrunk 16:9 scene, 60-75% wide,       |   |
|   |  thin grey frame                       |   |
|   +----------------------------------------+   |
+------------------------------------------------+
```

**T3 Classroom (questioner):** a student at the bottom left, the teacher at the bottom right, an inset at the top left,
speech bubbles.

**T4 Recap stack with dimming:** each row a thumbnail plus one sentence; rows other than the current one dimmed to 30%;
a yellow box around the key word; a yellow "Why?!".

```
| [thumb 1]  Light slows down in glass            |
| [thumb 2]  Slower => it bends                   |
| [thumb 3]  So different colours bend differently ... |
```

**T5 Split screen with a divider:** "How it started / How it's going", "The truth / A convenient lie",
"Temp=0 | Temp=5".

```
+-----------------------+------------------------+
|         Then          |          Now           |
+-----------------------+------------------------+
|  formula / [portrait] |     the modern picture |
+-----------------------+------------------------+
```

**T6 Derivation on the left, picture on the right** (a chart band may run along the top).

**T7 Question restated:** the old question (dim) → the new question (key words coloured), with an inset explaining it
below.

**T8 Pipeline:** input → [box] → output, with column titles above.

**T9 Running ledger:** the same table returns across episodes; rows not yet reached are dimmed, the current row is
white, the running total is boxed.

**T10 Document or portrait card:** see [subjects/history.md](../subjects/history.md).

## Camera and attention

- Guide attention by adding and removing things (briefly dimming), not by moving the camera.
- **Zoom into inner layers:** whole → part → finer part (for example stack → matrix → last column → probability list).
- **Shrinking into an inset** is the standard way to step back.
- Specific habits for 3D and camera motion are in the style.

## Emphasis toolbox

| Device | Spec | Example |
|---|---|---|
| SurroundingRectangle | thin (about 2 px at 1080p), concept colour, small buff; fades after being drawn | box both ω₁ in the formula and the reading |
| Brace plus label | white brace, coloured label | "12,288 coordinates" |
| Strike through and replace | a red line through it, the text turns grey, a red brace above with the new words | "Attention is ~~All~~ → About 1/3 of What You Need" |
| Dim the rest | opacity 25 to 35%, still on screen as context | recap stack, ledger |
| Recolour or fill | a token box filled yellow (low opacity); a vector turning yellow | |
| Arrow plus phrase | 1 to 3 words beside an arrow | "kicks the phase back" |
| Arc | "attends to", "affects" | |
| Glow running along a path | a bright dot moving along a path | |
| Placeholder | yellow box `???`; red `?` with an arrow | |
| ✓ / ✗ | green tick, red cross | |
| Live number | a DecimalNumber reading | "layers = 1,024 / phase kick = 0.013" |
| Ghost of the previous state | the old vector stays faintly, the new one is drawn over it | |
| Title transforming in place | "resonant frequency" → "resonant angular frequency ω_r" | |

Preferred ways to write these in code are in the style and the rendering references (`rendering/`).

## Openings, sections, endings

- **The first 5 seconds: a concrete hook, never a title card.** The 1-second cover at the very start of the delivered
  file is for chat-app previews; `render` adds it, and it is not part of the episode itself.
- **The title** comes at 0:20 to 0:45, after the hook.
- Then 30 to 90 seconds pin the question down (a questioner dialogue, a yellow "What are these?" callout), then a
  "quick recap".
- **Section changes are quiet:** centred serif text on black; or a title plus an inset on the commentary layer; or a
  question card. No wipe transitions: content fades out or transforms.
- **Series map:** a grid of episode thumbnails with the current group framed; "you are here".
- **Ending:** ✓ checklist → "next episode" inset → further resources → credits.

## Text-heavy moments without turning into slides

1. **The sentence itself is an object:** it is split into words, coloured, pointed at.
2. **Short question card:** at most 3 lines, key nouns in concept colours.
3. **Lists:** an agenda list (each item later becomes a section title), or a centred, unnumbered list of names that
   stays about 5 seconds as texture.
4. **A quotation is an object:** printed at the top of a notebook page, or a document scan. **Never a full-screen
   quotation slide.**
5. **Definitions** go into a formula or a labelled diagram.
6. **The rare dense text** is clearly marked optional ("for the especially curious"), so viewers can pause on their own.
7. **A ledger table** carries the accumulated detail, with only one row white at a time.

This matters most for the humanities, research explainers and specification documents: when the sources themselves are
text, turn the text into objects, not slides.

## Do and don't

**Do**

- One concept, one colour; the formula and the picture in the same colour.
- Bring things in step by step: keep something new appearing at the style's pace, and let finished things leave. Dim
  only what comes back right away ([attention](#attention-one-place-to-look-at-a-time)).
- Use `?` for unknowns; let future terms appear dimmed first.
- Let the questioner appear briefly (how often is in the style). It may ask, react, and also **voice the wrong guess a
  viewer might have and be corrected** (the dialogue version of a physics video taught more than plain explanation).
  Position characters for the humanities are in the subject reference.
- Show sources as physical objects or documents, held for 3 to 8 seconds.
- When you put up an original figure, table or text, walk the viewer through at least one cell or sentence of it (box
  it, read it, say what it means). Pasted up and never read, it is decoration to the viewer, and makes them feel they
  cannot understand it.
- Set up and pay off: recap stacks, "last episode", running ledgers, a "you are here" route map.
- A concrete hook in the first 5 seconds; the title after it.

**Don't**

- Cut often (the cut-rate limit is in the style).
- Bullet slides, or blocks of text over 3 lines (unless marked optional). Key results, formulas and labels that stay on
  screen through a long derivation are not slides: spoken words vanish, and conclusions needed later must stay
  visible.
- More than about 3 accent colours at once; colour as decoration.
- Full-screen portraits; slow Ken Burns pans and zooms used as content.
- A character replacing the derivation (finishing it for you).
- Fancy transitions (wipes, spins).
