# Scene code

Contents: [One scene file](#one-scene-file) · [A complete scene](#a-complete-scene) · [Timing](#timing) ·
[Shared code](#shared-code) · [Colours, fonts and text](#colours-fonts-and-text) · [Layout](#layout) ·
[ManimGL, not Manim Community](#manimgl-not-manim-community) · [ManimGL idioms](#manimgl-idioms) ·
[Scene transitions](#scene-transitions) · [Pitfalls](#pitfalls)

Start here before writing any scene. Every scene is ManimGL code (3Blue1Brown's engine, pinned to one commit) on top of
`scene_kit`, which adds narration timing, the automatic checks and the components. Related references:
[components.md](components.md) (what to draw with), [assets.md](assets.md) (pictures, data, clips),
[sound.md](sound.md), [cover.md](cover.md), [checks.md](checks.md) (reading preview output) and
[parallel-scenes.md](parallel-scenes.md). The visual principles are in
[teaching/visual.md](../teaching/visual.md).

## One scene file

- A scene in `script.yaml` is one file: `episodes/<episode>/scenes/<scene_id>.py`.
- The file starts with `from explainer_studio.scene_kit import *`. That gives the whole ManimGL namespace (and `np`),
  `NarratedScene`, the style constants, every component and the checks markers.
- The file defines exactly one `NarratedScene` subclass. Its name is free; use the scene id in PascalCase. A base class
  you want to share goes in `production/shared/`; a class whose base is imported from there still counts as the scene.
- `construct()` is a linear script. Before each beat, write a `# Beat: ...` comment, then one
  `with self.play_beat("<beat_id>") as beat:` block. Every beat of this scene in `script.yaml` is played exactly
  once, in script order. `preview` notes a beat that is never played or played out of order; `render` refuses the
  first.
- A scene usually has 3 to 10 beats, runs 20 to 90 seconds and works with one set of visual objects. It starts from an
  empty frame and ends by clearing it ([scene transitions](#scene-transitions)).
- Paths in scene code are relative to `production/`: `"shared/assets/images/dam.png"`,
  `"episodes/ep01/assets/clip.mp4"`, `"sources/app.py"`.
- Scenes never touch the network. Download pictures and data first ([assets.md](assets.md)).
- Check with `explainer-studio preview <episode> --scenes <scene_id>` and look at every screenshot
  ([checks.md](checks.md)). Preview needs no narration: a beat without current narration lasts an estimate of its spoken
  length, silently.

## A complete scene

The script of the scene:

```yaml
  - id: levels
    purpose: The energy of a dam is in the difference between its two water levels.
    beats:
      - id: two_levels
        narration_text: Picture a dam. The water stands 8 metres high on the left and 2 metres on the right.
        visual: The dam fades in; the two levels are labelled 8 m and 2 m.
      - id: difference
        narration_text: The 6 metres between them is what the water can give up as it falls.
        visual: A brace between the two levels, labelled 6 m in the energy colour.
      - id: conclusion
        narration_text: No difference, no flow. The energy lives in the gap.
        visual: The conclusion sentence appears above the dam and stays through the pause.
        pause_duration_seconds: 1.5
```

The series' shared code, `production/shared/series.py`:

```python
"""Shared code of the series: the concept colours from series-bible.md and the dam that returns in every episode."""

from explainer_studio.scene_kit import *

WATER = "#4A90D9"  # series bible: water
ENERGY = YELLOW  # series bible: energy


def get_dam(left: float = 3.0, right: float = 1.0, width: float = 7.0) -> Parts:
    """A wall with water at two heights. Parts: .wall, .left_water, .right_water."""
    wall = Rectangle(width=0.4, height=4.0).set_fill(GREY_C, 1).set_stroke(width=0)
    left_water = Rectangle(width=width / 2 - 0.2, height=left).set_fill(WATER, 0.8).set_stroke(width=0)
    right_water = Rectangle(width=width / 2 - 0.2, height=right).set_fill(WATER, 0.8).set_stroke(width=0)
    left_water.next_to(wall, LEFT, buff=0).align_to(wall, DOWN)
    right_water.next_to(wall, RIGHT, buff=0).align_to(wall, DOWN)
    dam = Parts(left_water, wall, right_water)
    dam.wall, dam.left_water, dam.right_water = wall, left_water, right_water
    return dam
```

The scene, `episodes/ep01/scenes/levels.py`:

```python
from explainer_studio.scene_kit import *

from shared.series import ENERGY, WATER, get_dam


class Levels(NarratedScene):
    def construct(self):
        dam = get_dam(left=3.2, right=0.8).shift(0.6 * DOWN)
        high = Text("8 m", font_size=LABEL_FONT_SIZE).set_color(WATER).next_to(dam.left_water, UP, buff=0.2)
        low = Text("2 m", font_size=LABEL_FONT_SIZE).set_color(WATER).next_to(dam.right_water, UP, buff=0.2)

        # Beat: the two water levels
        with self.play_beat("two_levels") as beat:
            self.play(FadeIn(dam), run_time=beat.get_seconds_until(0.3))
            self.play(FadeIn(high, shift=0.2 * UP), run_time=beat.get_seconds_until(0.6))
            self.play(FadeIn(low, shift=0.2 * UP))

        # Beat: the difference is what the water gives up
        corner = dam.right_water.get_corner(UR)
        gap = Line(corner, [corner[0], dam.left_water.get_top()[1], 0])
        brace = Brace(gap, RIGHT)
        drop = Text("6 m", font_size=LABEL_FONT_SIZE).set_color(ENERGY).next_to(brace, RIGHT)
        with self.play_beat("difference") as beat:
            self.play(GrowFromCenter(brace), FadeIn(drop), run_time=beat.get_seconds_until(0.5))

        # Beat: the conclusion, held through its pause
        conclusion = Text("The energy lives in the gap.", font_size=BODY_FONT_SIZE).to_edge(UP)
        with self.play_beat("conclusion") as beat:
            self.play(Write(conclusion), run_time=beat.get_seconds_until(0.7))
            self.play(FlashAround(drop, color=ENERGY))

        self.play(FadeOut(Group(dam, high, low, brace, drop, conclusion)))
```

What it shows: objects are built before their beat and animated inside it; each number the line says is written
next to what it measures; the conclusion sentence is on screen through the pause; the scene clears the frame at the
end. `gap` is only a measuring line and is never added.

## Timing

The narration decides time. A beat's block lasts as long as its line, plus the pause after it.

- `beat.duration_seconds`: the line's length in seconds. With current narration it is the real recording; otherwise the
  language table's estimate (preview says how many beats used an estimate).
- `beat.elapsed_seconds`, `beat.remaining_seconds`: seconds since the line started, and until it ends.
- `beat.get_seconds_until(f)`: seconds from now until fraction `f` of the line has been said. Use it as `run_time=`
  so an animation lands on a word: `self.play(Write(defn), run_time=beat.get_seconds_until(0.8))`. It returns 0 once
  that point has passed, and a play with `run_time=0` is instant. To land exactly on one word, split the line into
  two beats.
- Leaving the block waits until the line has ended and the beat's `pause_duration_seconds` (0.3 s when the script
  gives none) has passed. You never write a `self.wait` for a scripted pause, and whatever is on screen stays there
  during it.
- If the block's animations run longer than the line plus its pause, nothing is cut: the next line simply starts
  later, after silence. Make that a choice, not an accident.
- Time moves only in `self.play` (1 s by default) and `self.wait` (1 s by default). `self.add` is instant.
- Code between two blocks runs after the first beat's pause, in silence. Code before the first block delays the first
  line. Keep both short: build objects there, animate inside beats.
- Prefer `beat.get_seconds_until` and `beat.remaining_seconds` over fixed run times: when the real narration
  replaces the estimate, the scene adapts. Preview again after `narrate`.
- **Guess beats** (the script leaves about `pause_duration_seconds: 2.5` after a question): the options appear inside
  the beat and stay on screen through the pause; the answer comes in the next beat.
- **Conclusion beats** (a pause of about 1 to 1.5 s): the conclusion stays on screen through the pause and into the
  start of the next beat.
- Motion that is physics (oscillation, a falling body) uses `rate_func=linear` or a simulation
  ([components.md](components.md#simulations-and-toys)), so the time on screen is the true time.
- Sounds inside a beat or its pause: [sound.md](sound.md).

The automatic checks look at the frame when the block's code finishes (before the closing wait), and the by-beat
screenshot is taken when the line ends or when the code finishes, whichever is later.

## Shared code

Code used by more than one scene lives in `production/shared/<name>.py` and is imported as
`from shared.<name> import ...`. Shared code starts with `from explainer_studio.scene_kit import *` like a scene.

- **The series' look:** the concept colour constants from `series-bible.md`, recurring devices (a map, a ledger, the
  questioner), and builders for objects that come back. Name builders `get_*`, and give them parameters that rebuild
  any state a scene needs (`get_foundation(cracked=True, filled=False)`), so one scene can rebuild exactly what the
  previous one ended on.
- **Named parts:** return a `Parts` (from `scene_kit`) instead of a `VGroup` when you attach named parts
  (`dam.wall`). Parts keep pointing at the right objects after `.copy()`, `.animate`, `dim()` and `Transform`; a plain
  `VGroup` would keep pointing at the original.
- **Toy programs:** when the numbers on screen come from running a program (a toy model, a simulation, a small
  training run), the program is plain Python in `production/shared/<name>.py`, ends with a few `assert` lines that
  check its answers (worked by hand, the previous version, the sources' own numbers), and scenes import its
  results. A failing assert fails the render, which is the point. Heavy calls go through `run_toy(function, *args)`:
  the result is cached until the program's file changes.
- `preview` and `render` check shared code with the same rules as scenes.
- When several subagents write scenes, only the lead edits shared code ([parallel-scenes.md](parallel-scenes.md)).

## Colours, fonts and text

**Colours.** The concept colour table in `series-bible.md` is fixed for the whole series. Define each concept colour
once as a constant in shared code and use the constant; never retype a hex value in a scene. `scene_kit` also gives
semantic roles:

| Constant | Use |
|---|---|
| `HIGHLIGHT_COLOR`, `HIGHLIGHT_RECTANGLE_COLOR` | "look here", the key term; the stroke of a highlight box (yellow) |
| `CONTRADICTION_COLOR`, `AFFIRMATION_COLOR` | false, paradox, counterexample (red); true, proven, consistent (green) |
| `DIM_OPACITY` | de-emphasised material (0.35) |
| `META_BACKGROUND_COLOR` | the dark-grey commentary layer (`#1A1A1A`) |
| `FUNCTION_COLOR`, `YEAR_COLOR`, `NAME_COLOR`, `QUOTE_COLOR` | graphs, years, names, quotations |
| `TEX_TO_COLOR_MAP` | an example `t2c` map for `Tex` (`{"{x}": ..., "{y}": ...}`) |

**Fonts.** `Text(...)` uses the video font (`FONT`, Noto Sans TC, which covers Chinese and Latin) without a `font=`
argument. Code uses `MONO_FONT` (JetBrains Mono). Formulas use LaTeX (`Tex`). If a font is missing, a stand-in is used
and preview prints a warning.

**Sizes.** `TITLE_FONT_SIZE` 72, `HEADING_FONT_SIZE` 60, `BODY_FONT_SIZE` 48 (the ManimGL default),
`LABEL_FONT_SIZE` 36, `SMALL_FONT_SIZE` 24. The smallest readable size on screen is 16, measured after every scaling
and camera zoom; smaller text is the blocking check `text_too_small`.

**Text objects.**

- `Text("...")`: plain text in any language. Colour words with `t2c={"energy": YELLOW}` or afterwards with
  `text["energy"].set_color(YELLOW)`.
- `Tex(R"...")`: math mode, always a raw string. `TexText(R"...")`: LaTeX text mode with inline `$...$`.
- `get_cjk_tex(R"<text> $(A \mid B)$")`: text in a CJK script with inline math, compiled with xelatex. It is slower
  than `Text`; use it only when math sits inside the sentence. The language reference has an example.
- `choose_local_text(chinese, english)`: a default word in the episode's language, for helpers shared by series in
  different languages.
- Text in right-to-left and Indic scripts works through `Text(..., font=...)` with an installed font; look at the frame
  for missing glyphs.

## Layout

The frame is 16:9, about 14.2 units wide (`FRAME_WIDTH`) and 8 units high (`FRAME_HEIGHT`), origin at the centre.

- Decide which area of the frame each object takes before building it. Size components with their `width`,
  `height`, `max_width` or `max_height` arguments, then place them with `to_edge`, `to_corner`, `next_to`,
  `arrange` and `move_to`. Keep text about 0.5 units from the frame edges.
- Do not shrink a finished component to make it fit (`.scale(0.6)`, `set_max_width`): its labels fall under the
  minimum size. Build it smaller instead: fewer columns, shorter labels, a top-to-bottom diagram instead of a deep
  left-to-right one, or two pictures in two beats.
- Labels sit beside lines or inside boxes, never on a line or on other text (`text_overlap` reports only the
  second).
- Layout templates, the three-groups limit, dimming and what stays on screen are in
  [teaching/visual.md](../teaching/visual.md).

## ManimGL, not Manim Community

Models often write Manim Community code. `preview` and `render` refuse these lines before ManimGL runs and say what
to write instead:

| Refused | Write |
|---|---|
| `from manim import *`, `import manim` | `from explainer_studio.scene_kit import *` |
| `MathTex(...)` | `Tex(...)` (math mode; `TexText` for text mode) |
| `Create(...)` | `ShowCreation(...)` |
| `config.<x> = ...` | nothing: preview and render set the resolution |
| `self.camera.frame` | `self.frame` |
| `MovingCameraScene`, `ThreeDScene`, `ZoomedScene` | `NarratedScene`; move `self.frame` (3D works in any scene) |
| `x_length=`, `y_length=` | `Axes(..., width=, height=)` |
| `Circumscribe(...)` | `FlashAround(...)` or `get_highlight_rectangle(...)` |
| `Table(...)` | `get_table(...)` |
| `Star(...)` | `RegularPolygram` or your own `VMobject` |
| `AddTextLetterByLetter(...)` | `Write(...)` |
| `path_arc=` passed to `self.play(...)` itself | the animation takes it: `Transform(a, b, path_arc=PI / 2)` |
| `VGroup(...)` holding a picture (`get_image`, `get_clip`, `get_paper_figure`, `get_portrait_card`, `ImageMobject`) | `Group(...)`: pictures are not vector objects |
| `set_fill(..., family=...)` | `set_fill` recurses by default; `recurse=False` limits it |
| `set_opacity` on an arc or curve | `set_stroke(opacity=...)` or `dim(...)`: it would also fill the arc into a blob |
| `add_updater(lambda m, x=...: ...)` | `functools.partial`: a second lambda argument receives `dt` |
| `CurvedArrow(..., fill...)` | `get_curved_arrow(...)` |
| `\;\;` or `\!` in `Tex` | `\quad` or `\,` (a single `\;` is fine) |
| `self.add_sound(...)`, `self.sfx(...)` | `self.play_sound(...)` ([sound.md](sound.md)) |

Comments are not checked.

## ManimGL idioms

Every snippet below has been rendered with the pinned ManimGL.

**Several animations, each in its own stretch of one play:**

```python
self.play(
    FadeIn(square),
    GrowArrow(arrow, time_span=(1, 2)),
    FadeIn(label, lag_ratio=0.1, time_span=(1, 2)),
    run_time=3,
)
```

**Formulas.** Wrap variables in braces for colouring, so `"s"` does not also match the s inside `\cos`. Select parts by
substring or slice.

```python
t2c = {"{s}": YELLOW, "{t}": BLUE}
eq = Tex(R"F({s}) = \int_0^\infty f({t}) e^{-{s}{t}} d{t}", t2c=t2c, font_size=72)
self.play(Write(eq[:5]), run_time=beat.get_seconds_until(0.4))
self.play(FadeIn(eq[5:], lag_ratio=0.1))
rect = SurroundingRectangle(eq[R"\int_0^\infty"], buff=0.1).set_stroke(YELLOW, 2)
```

```python
swap = TransformMatchingTex(eq1, eq2, key_map={"+": "-"}, path_arc=45 * DEG, run_time=2)
self.play(swap)
```

`TransformMatchingStrings` does the same for `Text` and `TexText`; `TransformMatchingShapes` matches by shape. When a
symbol cannot be selected, build the `Tex` with `isolate=[...]`.

**A number inside a formula that follows something:**

```python
width = Tex(R"\text{width} = 2.00", font_size=60)
number = width.make_number_changeable("2.00")
number.f_always.set_value(circle.get_width)
self.play(VFadeIn(width))
```

**Appearing and changing:** `ShowCreation(curve)`, `Write(eq)`, `DrawBorderThenFill(shape)`,
`FadeIn(mob, shift=0.5 * UP)`, `FadeTransform(old, new)` (from one text to a different text), `TransformFromCopy(eq["r^2"], copy)`,
`ReplacementTransform(a, b)`, `GrowArrow(arrow)`, `GrowFromCenter(brace)`,
`LaggedStartMap(FadeIn, dots, shift=0.2 * DOWN, lag_ratio=0.1)`.

**Emphasis and focus:**

```python
brace = Brace(eq[R"x^2 + y^2"], DOWN, buff=SMALL_BUFF)
brace_label = brace.get_tex(R"\text{two squares}")
self.play(FlashAround(eq["r^2"], color=YELLOW, time_width=1.5))

dots.target = dots.generate_target()
dots.target.set_opacity(0.3)
dots.target[3].set_opacity(1).set_color(YELLOW)
self.play(MoveToTarget(dots))

eq.save_state()
self.play(eq.animate.set_fill(opacity=0.4))
self.play(Restore(eq))
```

`BackgroundRectangle(mob).set_fill(BLACK, 0.8)` puts a dark card behind text over a busy picture;
`mob.set_backstroke(BLACK, 5)` outlines text that sits on lines. For dimming whole objects use `dim()` and `undim()`
([components.md](components.md#emphasis-focus-and-insets)).

**Updaters:**

```python
t = ValueTracker(0)
dot = Dot().add_updater(lambda m: m.move_to(axes.i2gp(t.get_value(), graph)))
label = Text("x", font_size=LABEL_FONT_SIZE)
label.always.next_to(dot, UP)
top_brace = always_redraw(Brace, side, UP)
self.play(FadeIn(dot), VFadeIn(label))
self.play(t.animate.set_value(5), run_time=3)
```

Objects with updaters enter and leave with `VFadeIn` and `VFadeOut`. A plain `FadeIn` interpolates points that the
updater keeps changing; a number whose glyphs change then stops the scene with "operands could not be broadcast
together".

**Camera:**

```python
self.play(self.frame.animate.set_height(10, about_edge=UP), run_time=2)    # step back
self.play(self.frame.animate.move_to(eq).set_height(eq.get_height() * 3))  # push in on a formula
self.play(self.frame.animate.to_default_state())
```

Text keeps its minimum size relative to the frame: zooming out shrinks it on screen.

**3D** (no special scene class; move `self.frame`):

```python
axes = ThreeDAxes((-3, 3), (-3, 3), (-2, 2))
helix = ParametricCurve(lambda t: [np.cos(t), np.sin(t), 0.15 * t], t_range=(-8, 8, 0.05)).set_stroke(YELLOW, 3)
label = Tex(R"(\cos t, \sin t, 0.15\,t)").to_corner(UL).fix_in_frame()   # stays put while the camera moves
self.frame.reorient(20, 70)                                                 # theta, phi in degrees
self.play(FadeIn(axes), ShowCreation(helix), FadeIn(label))
self.play(self.frame.animate.reorient(-30, 60), run_time=3)
```

`self.frame.add_ambient_rotation(2 * DEG)` turns slowly until `self.frame.clear_updaters()`. Camera orbits usually
take 8 to 20 seconds. Solid 3D models
(organs, machines, molecules in space) come from `asset blender render` ([assets.md](assets.md)).

**Habits:** common run times are 1 to 4 seconds; `lag_ratio=0.1` for a gentle stagger; a play is usually followed by
a moment of stillness, which the beat's remaining time and pause give you.

## Scene transitions

- Every scene starts from an empty frame and ends by fading everything it shows to an empty frame
  (`self.play(FadeOut(Group(a, b, c)))` after the last beat). Scenes are joined without a transition, so a scene that
  does not clear the frame cuts hard into the next one.
- When a scene must continue a picture, it rebuilds that picture itself from shared builders at the start, and the
  previous scene still fades it out. The pair looks continuous because both draw the same thing in the same place.
  Write the hand-over state into the scene's notes (or the shared brief, when subagents write the scenes).
- Fade out the objects you hold in variables. Never pass `self.mobjects` whole: it contains the camera frame and an
  internal selection object, and animating those moves the camera or does nothing visible.

## Pitfalls

Observed with the pinned ManimGL. `scene_kit` already fixes several others (LaTeX compiled in parallel, thin spikes in
CJK glyphs, `\|` in formulas, the default font); write those as usual.

**Formulas**

- A lone `Tex(R"\iff")` fails to compile; inside a formula (`a \iff b`) it works.
- `\;\;` and `\!` fail ("Argument of \UseTextAccent has an extra }", "Missing delimiter"); a single `\;` works.
  Preview refuses the first two.
- The warning "Estimated size ... does not match true size" (common with `\{ ... \mid ... \}`) means substring
  colouring and `TransformMatchingTex` may pick the wrong glyphs (seen: `q^2<2` coloured wrongly). Use `isolate=[...]`,
  `{a \over b}`, braces around variables, or split a long formula into several `Tex` arranged in a `VGroup`.
- Spacing such as `\;` can vanish when you colour by substring, and formulas with `\mathrel` select the wrong glyphs.
  Split long formulas or index glyphs directly.

**Text**

- `Text(..., t2c=...)` followed by `.set_color(...)` wipes the `t2c` colours. Set the base colour first, then colour
  words with `text["word"].set_color(...)`.
- LaTeX in `Text` is printed literally: `Text("e^{-1/x^2}")` shows the braces. Use `Tex`, `get_cjk_tex`, or write
  `e^(−1/x²)`.
- Symbols the video font lacks (ℤ, ℚ, ℝ and other mathematical letters) come from another font or turn into plain
  letters. Write them with `Tex(R"\mathbb{Z}")`.
- A plain `Transform` from one text to a different text scrambles the glyphs halfway. Use `FadeTransform` or
  `TransformMatchingStrings`.

**Opacity and colour**

- `set_opacity` sets the fill too: an outline-only shape (circle, frame, `SurroundingRectangle`) suddenly gets a
  translucent fill, and a picture frame made from a filled rectangle tints the picture. Dim with `dim()`, or
  `set_stroke(opacity=...)`; build picture frames from four `Line`s.
- `fade()` on a `VMobject` scales opacity, but on a `Group` (anything holding a picture) it sets an absolute opacity:
  a faint part gets brighter and a hidden one appears. Use `dim()`.
- To bring back something dimmed, use `undim()` on the same object you dimmed. `box.animate.set_opacity(1)` on a card
  with a translucent fill makes the fill opaque and hides the text inside.
- `Indicate(chip)` recolours everything in it, background included. Use it on text only.

**Structure and updaters**

- `self.mobjects` contains the camera frame. Passing it whole to `Group(...)`, `FadeOut` or `shrink_to_inset` scales or
  moves the camera instead of the content. Filter it out (`[m for m in self.mobjects if m is not self.frame]`), or
  better, use the objects you hold.
- `FadeTransform` or `remove` on a child of a `VGroup` breaks the parent and stops its updaters.
- `if tracker:` is always false for a `ValueTracker`; write `if tracker is not None:`.
- An object whose states are different structures (a taut string that is one curve, a strained string that is a curve
  plus marks) breaks halfway through a `Transform` between them. Change it in two steps (straighten, then fade in the
  marks).
- `FunctionGraph(f, x_range=(a, b))` fails: it needs a step, `x_range=(a, b, 0.05)`. `axes.get_graph(f, x_range=(a, b))`
  accepts a pair.
- A `NumberLine` (including `get_timeline`) drawn with `ShowCreation(line)` and `FadeIn(line.numbers)` in the same play
  loses its numbers. Use `FadeIn(line)`.
- Inside an inset, line widths do not shrink with the content: a tick mark becomes a blob. Draw insets' marks thinner.
- A path you send something along (`MoveAlongPath`, `flow_along`) stays where it was made when the drawing moves or
  shrinks. Put the path in the group you move (with `set_stroke(opacity=0)`), or build it again from the drawn wires
  after they move. Moving a separate copy by hand to line it up again puts the dot beside the wire.
- `Rotate(mobject, angle, about_point=p)` spins something in place only when `p` is its own centre; anywhere else it
  sends it round in a circle. An arc's centre is `arc.get_arc_center()`. The arc of `get_curved_arrow(a, b, angle)` is
  centred wherever the two points and the angle put it, not at a point beside them that you computed.
- `Transform` from a tiny arc or line to a long one does not sweep along it: every point moves at once, so it swells
  out of a dot. To sweep it, draw the full shape with `ShowCreation`, or rebuild it each frame from the angle reached
  (`UpdateFromAlphaFunc`).

**3D**

- Before shrinking a 3D picture into an inset, bring the camera back (`self.frame.animate.to_default_state()`) and
  replace the 3D objects with a flat drawing of the current view; insets assume a flat camera.
