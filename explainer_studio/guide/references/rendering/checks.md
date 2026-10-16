# Checks

Contents: [What preview and render write](#what-preview-and-render-write) · [The screenshot sheets](#the-screenshot-sheets) ·
[What to look for](#what-to-look-for) · [Automatic checks](#automatic-checks) ·
[Decorative marking and keep_inside](#decorative-marking-and-keep_inside) · [Notes and warnings](#notes-and-warnings)

You cannot watch a video; you look at pictures. A scene is not done until you have looked at its screenshots and fixed
every automatic check issue. Fix what you find before anyone else sees it.

## What preview and render write

| Command | Where | What |
|---|---|---|
| `preview <episode> [--scenes a,b] [--cover]` | `preview/<scene>/` (cleared on each run) | `clip.mp4` at 720p (current narration and sounds, no music), `automatic-checks.json`, `screenshots/every-2s-NN.png`, `screenshots/by-beat-NN.png` |
| | `preview/cover/cover.png` | the cover at 1080p |
| `render <episode>` | `render/` (replaced only when everything succeeded) | `video.mp4` at 1080p, `subtitles.srt`, `cover.png`, `timeline.json`, `automatic-checks.json`, `screenshots/every-6s-NN.png`, `screenshots/by-beat-NN.png`, `screenshots/text-visibility-check/<beat>.png` |

`preview` never blocks anything. `deliver` refuses while `render/automatic-checks.json` holds a `text_too_small`.
Preview the scene you are working on (`--scenes`); after fixing, preview it again and look again.

## The screenshot sheets

| Screenshot sheet | Contents | Look at it for |
|---|---|---|
| `every-2s` (preview) | a frame every 2 seconds, labelled with its time, 12 to a screenshot sheet (4 × 3, 480 px wide) | motion and layout over time: things appearing, leaving, crowding, a stretch where nothing happens; something that should stay on its line or in its place (a dot running along a wire, an arrow spinning) drifting off it, or a shape that should sweep out swelling from a dot instead |
| `by-beat` (preview) | the frame at the end of each beat, with the beat id, the time and the line printed under it, 9 to a screenshot sheet (3 columns, 420 px) | whether the picture shows what the line says |
| `every-6s` (render) | a frame every 6 seconds of the whole episode | the whole episode's rhythm, seams between scenes, repeats |
| `by-beat` (render) | the end of every beat, 6 to a screenshot sheet (2 columns, 600 px) | the same as in preview, for the whole episode |
| `text-visibility-check/<beat>.png` (render) | six full-size 1080p frames, chosen from the layout data: three with the smallest text, three with text closest to an edge | small text, a chip or source line cut off at the edge: the screenshot sheets' smaller frames hide these |

Read each `by-beat` tile with the line covered first: can you say the point just made from the picture alone? Then
read the line: does the picture point at the same thing?

## What to look for

- Text that runs off the frame, overlaps other text, sits on a line, arrow, brace or box outline, or is hidden behind
  something. Labels go beside lines or inside boxes.
- A curve that runs past the end of its axes: plot only within the axes' range (choose `x_range` inside it), or widen
  the range.
- More to read at once than the line leaves time for: split the beat into two pictures, or let finished things leave.
- Missing glyphs (empty boxes in place of characters), wrong symbols, LaTeX printed as text.
- Stray short lines left from a previous picture, and lines or arrows running off the frame.
- One place to look in each frame; at most three groups of things; at most three accent colours at once; concept
  colours as in the series bible ([teaching/visual.md](../teaching/visual.md)).
- Something new about every 8 seconds (or at the presenter style's own pace); no frame frozen for more than 15
  seconds unless it is a deliberate hold.
- Narration and picture about the same thing; every number the line says written next to what it refers to.
- Nothing on screen that neither this line nor the next one speaks of, other than what the line stands on (the
  picture or map being talked about, the conclusion just made, the main question, what the presenter's style keeps up
  on purpose): a card, a list, a quote, a difference drawn into the picture (two flows going opposite ways). The viewer
  stops to read it and wonders why it is there. Say it, or take it out; a name tag on what the line points at is fine.
- Seams: the scene starts from an empty frame and ends on one; no jump, no picture repeated from the scene before.
- At the cover: readable at 400 px wide ([cover.md](cover.md)).

## Automatic checks

They run inside the scene at the end of every beat (when the beat's code finishes) and on the scene's last frame
(reported with no beat). Each issue in `automatic-checks.json` has `check_name`, `scene_id`, `beat_id` and a `detail`
naming the text and where it is.

Fix every issue `preview` and `render` report; only `text_too_small` also blocks delivery.

| Check | Blocks delivery | Means | Fix |
|---|---|---|---|
| `text_overlap` | no | two pieces of text overlap | move them apart (`next_to`, `arrange` with a `buff`), or let one leave |
| `text_too_small` | yes | text under 16 on screen, after every scaling and camera zoom | usually a component shrunk to fit: rebuild it smaller instead (fewer columns, a top-to-bottom diagram when left-to-right is deeper than about five layers, shorter edge labels, two pictures in two beats). Small context you do not need read goes into an inset (`shrink_to_inset`), or better, leaves |
| `outside_container` | no | a part registered with `keep_inside` pokes out of its container's drawn outline | keep its motion inside the shape; check the part's final position |
| `text_outside_frame` | no | text partly off the frame | cut-off text reads as broken: move or shrink the layout |

What the checks do not see: text on a line, a curve past its axes, a crowded frame, a picture that stays still while
the line moves on, stray lines, lines and arrows off the frame, pictures overlapping text, colours, focus, and anything
in the middle of a beat (a camera move that crops a label and comes back is never checked). Those are yours: look at
the screenshots ([above](#what-to-look-for)).

## Decorative marking and keep_inside

`mark_decorative(mobject)` exempts the text in an object and everything in it from the checks. It returns the object,
so it can wrap a constructor. Use it for props whose text is texture, not reading (the small print on a document
stand-in, a thumbnail).

Already decorative: `get_document`, `get_uv_grid`, `get_shadow`, and everything inside a `shrink_to_inset` inset
(until `expand_from_inset`; what was decorative before the inset stays decorative).

`keep_inside(container, *parts, margin=0.02)` registers parts that belong inside a container: molecules in a bowl,
organelles in a cell, dots on a map, icons in a box. At the end of each beat, a part outside the container's drawn
outline (its largest shape, not its bounding rectangle) is reported as `outside_container`. Register every part that
drifts or moves.

```python
bowl = Circle(radius=2).set_stroke(GREY_B, 3)
dots = VGroup(*(Dot(0.8 * np.array([np.cos(a), np.sin(a), 0])) for a in np.linspace(0, TAU, 6)))
keep_inside(bowl, *dots)
```

## Notes and warnings

- `preview` prints per scene its length, how many beats used estimated timing, and a summary of the issues (blocking
  ones marked "blocks delivery"). Notes: "no play_beat block, so render will refuse" (a beat of this scene in the
  script is never played), "beats are played in a different order from script.yaml".
- A scene that fails prints the exception with the scene file and line; preview refuses Manim Community code and known
  ManimGL pitfalls before running anything ([scene-code.md](scene-code.md#manimgl-not-manim-community)).
- A font warning means the video font is missing on this machine and a stand-in was used.
- `render` warns when a `read_file_excerpt` shows text that changed since the scene's last preview: the file changed
  after you looked. Look at that scene's by-beat screenshots again.
- `render` prints the loudness and true peak of the mix, the automatic check summary and every screenshot path. Look at
  every screenshot before you deliver.
