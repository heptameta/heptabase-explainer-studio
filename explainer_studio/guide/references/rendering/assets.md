# Assets

Contents: [When to use external material](#when-to-use-external-material) · [Licences and credits](#licences-and-credits) ·
[The asset commands](#the-asset-commands) · [Pictures](#pictures) · [Vector diagrams and icons](#vector-diagrams-and-icons) ·
[Portraits](#portraits) · [Data](#data) · [Figures from PDFs](#figures-from-pdfs) · [Video clips and recordings](#video-clips-and-recordings) ·
[3D shots](#3d-shots) · [Screen recordings](#screen-recordings) · [Credits at the end](#credits-at-the-end)

## When to use external material

Draw natively whenever you can ([components.md](components.md)): a native picture can light up part by part, change
and follow the narration. Bring in external material for what native drawing cannot show: photographs, artworks,
historical documents, micrographs, real footage, recordings, real data, solid 3D models, real software.

The `explainer-studio asset ...` commands save time; they are not the only way to get material. Whatever you use, a
scene reads it from a file under `production/`: scenes never touch the network.

When the picture the video needs cannot be found or made, use the closest honest option and record it with
`explainer-studio gap add --kind visual --need "..." --workaround "..."`. A hand-drawn stand-in for a missing picture
is such a workaround and is always recorded; never pass one off silently as the real thing.

## Licences and credits

- Prefer freely licensed material. The search commands return only public domain, CC0, CC BY and CC BY-SA files
  (icons also MIT and BSD).
- Every download records its source, author and licence in `production/credits.yaml` (one entry per file; downloading
  the same file again replaces its entry). Material you obtained another way gets an entry added by hand, in the same
  format ([file-formats.md](../file-formats.md)).
- Material that needs attribution (CC BY, CC BY-SA) is credited on the end credits page
  ([end-credits.md](end-credits.md)). When the user has turned the page off, credit it in the frame where it appears,
  in small type in a corner.
- Never scan pictures out of a copyrighted book. Portraits and scans of original documents are public domain or
  clearly licensed.
- 3Blue1Brown's π creatures are not public and are 3Blue1Brown's brand: never use them.

## The asset commands

| Command | What it is for | Output |
|---|---|---|
| `asset commons search "<words>" [--media-type photo/svg/video/audio/3d] [--limit 12]` | photographs, paintings, historical documents, scientific diagrams, footage, recordings and 3D models on Wikimedia Commons | numbered candidates (file name, licence, author, size, length) and a thumbnail sheet |
| `asset commons download "<File:...>" [--start s --end s]` | one Commons file, by name or URL | `shared/assets/images/`, `video/`, `audio/` or `3d/` |
| `asset bioicons search "<words>"` / `download "<name>"` | about 2,800 science icons (cells, organelles, organs, lab apparatus, molecules) as SVG | `shared/assets/icons/` |
| `asset wikipedia download-portrait "<article>" [--language en]` | a person's portrait | `shared/assets/portraits/` |
| `asset owid download <chart> [--entities a,b] [--years 1950,2020]` | an Our World in Data chart's data (the slug in `ourworldindata.org/grapher/<slug>`) | `shared/assets/data/<chart>.csv` |
| `asset worldbank download <indicator> [--entities ...] [--years ...]` | a World Bank indicator (for example `NY.GDP.PCAP.CD`) with columns entity, code, year, value | `shared/assets/data/<indicator>.csv` |
| `asset pdf draw-page-thumbnail-sheets <pdf> [--first-page 1 --last-page 30]` | page thumbnails, six to a thumbnail sheet (at most 60 pages per run), to find the pages with figures, tables and formulas | page thumbnail sheets in a temporary folder |
| `asset pdf crop <pdf> --page 12 [--box x0,y0,x1,y1] [--dpi 200]` | one page, or a box of it, as a picture | `shared/assets/figures/`; before the series exists, a temporary file (or `--to`) |
| `asset image draw-grid <image>` | a copy of a picture with a labelled line every 10%, to read positions | a temporary file |
| `asset blender render <spec>` | a 3D shot rendered by Blender | `shared/assets/video/<name>.mp4` and `<name>.labels.json` |
| `asset playwright record <spec>` | a scripted screen recording of a web page | `shared/assets/video/<name>.mp4` and `<name>.steps.json` |

- Downloads go to `production/shared/assets/<kind>/`. `--to <folder or file>` saves elsewhere, for example the
  episode's own `assets/` folder; the path is relative to the current folder. Material used by several episodes
  stays in `shared/assets/`.
- Inside the series folder (or with `--series` for `pdf crop`), the PDF commands also accept a path relative to
  `production/` (`sources/paper.pdf`).
- Thumbnail sheets and grids are for your eyes only and go to a temporary folder; open the printed path.
- Blender and Playwright are installed separately from the rest; when one is missing, the command says what to
  install.

## Pictures

Find with `asset commons search` (look at the thumbnail sheet), download with `asset commons download`. Large pictures
come at 1920 px wide; TIFF scans are converted to JPEG.

| In the scene | What it does |
|---|---|
| `get_image(path, height=5.0, width=None, border_color=None, has_backdrop=False)` | a photograph, artwork or scan; `border_color=GREY_B` adds a thin frame (artworks look better without one); `has_backdrop=True` puts a transparent diagram on a light card. With a border or backdrop the result is a `Group` and the picture is `.picture` |
| `get_image_point(image, u, v)` | the frame point at `(u, v)`, fractions of width and height from the top-left |
| `get_image_callout(image, (u0, v0, u1, v1), "label")` | a box around a region, with a label (`[0]` the box, `[1]` the label) |
| `resolve_image_focus(image, (u0, v0, u1, v1))` | `(center, width)` for the camera to look closely at a region |
| `get_uv_grid(image)` | a labelled 10% grid over the picture, for one planning preview; remove it afterwards |

```python
art = get_image("shared/assets/images/dam.png", height=5)
box = get_image_callout(art, (0.45, 0.6, 0.6, 0.8), "turbine")
self.play(FadeIn(art))
self.play(ShowCreation(box[0]), FadeIn(box[1]))
center, width = resolve_image_focus(art, (0.45, 0.6, 0.6, 0.8))
self.play(self.frame.animate.move_to(center).set_width(width), run_time=2)
self.play(self.frame.animate.to_default_state(), run_time=1.5)
```

- Find the coordinates first: preview once with `get_uv_grid(art)` on screen (or run `asset image draw-grid` on the
  file), read the box off the grid, then remove the grid.
- A group holding a picture is a `Group`, never a `VGroup` (preview refuses the latter).
- Pictures are objects: show one whole, box the part that matters, then pull that part out. Walk the viewer through at
  least one detail of every original picture you show ([teaching/visual.md](../teaching/visual.md#do-and-dont)).

## Vector diagrams and icons

SVG diagrams (from Commons with `--media-type svg`, or Bioicons) can be drawn as native shapes whose parts light up.

| In the scene | What it does |
|---|---|
| `get_svg(path, height=4.5, width=None, mode="auto", has_backdrop=False)` | the diagram as shapes; `has_backdrop=True` for a diagram drawn for white paper (its black outlines vanish on black); then the diagram is `.picture` |
| `svg.get_part("nucleus")` | every shape in the group or element with that id or label (exact, else case-insensitive substring) |
| `svg.list_part_names()` | the meaningful ids and labels in the file, the names `get_part` takes |
| `svg.get_part_at(u, v)` | the structure at a point, for files that name nothing (find `(u, v)` with a grid preview) |
| `svg.get_parts_in((u0, v0, u1, v1))`, `svg.get_parts_by_color(color)`, `svg.count_fill_colors()` | shapes in a region; shapes of one fill colour; the fill colours used, with their shape counts |
| `check_does_svg_need_raster(path)` | whether the file will be shown as a picture instead |

```python
cell = get_svg("shared/assets/icons/cell.svg", height=4)
membrane = cell.get_part("membrane")
self.play(FadeIn(cell))
self.play(*dim(membrane), cell.get_part("nucleus").animate.set_fill(YELLOW))
self.play(Indicate(cell.get_part_at(0.72, 0.38)))
```

- Text inside an SVG is not drawn. Add the labels yourself in the episode's language.
- Gradients become their average flat colour. A file with filters, masks, embedded pictures or heavy shading
  (`mode="auto"`) is shown as a picture: you can still box and zoom, but not pick parts.
- `get_part(...)` returns a new group on every call: keep it in a variable when you dim it and undim it later.

## Portraits

- `asset wikipedia download-portrait "<article>"` downloads the article's lead image only when Commons says it is
  public domain or CC0. Otherwise it fails and says so.
- One person has one portrait for the whole series: keep it in `shared/assets/portraits/` and use the same file in
  every episode.
- When no free portrait exists, use the silhouette with a name tag: `get_portrait_card(name, original_name, years)`
  without `image_file_path=` ([components.md](components.md#history-and-series-devices)).

```python
card = get_portrait_card("Martin Luther", "Martin Luther", "1483–1546", school_color=BLUE_C,
                         image_file_path="shared/assets/portraits/Martin_Luther.jpg")
```

## Data

Download real data with `asset owid download` or `asset worldbank download`; the summary prints the first rows and
warns about entities with no data. Read it in the scene with `read_csv("shared/assets/data/<name>.csv")` (rows as
dicts of strings; convert numbers yourself) and draw it with the [charts](components.md#charts). Numbers taken from the
sources themselves are typed from the sources and checked against them.

## Figures from PDFs

1. `asset pdf draw-page-thumbnail-sheets sources/paper.pdf` and look at the page thumbnail sheets to find the page.
2. `asset pdf crop sources/paper.pdf --page 12` saves the whole page; `asset image draw-grid` on it gives the box; crop
   again with `--box 0.1,0.25,0.85,0.57`.
3. In the scene: `get_paper_figure("shared/assets/figures/paper-p012-crop.png", caption="Figure 2", source="Elhage et
   al. 2021, Fig. 2")`, a framed figure with a caption and a small source line. Treat it as an object: show it whole,
   box the part that matters, then pull that part out.

A crop from the user's own sources is not recorded in `credits.yaml`; its `source` line says where it comes from.

## Video clips and recordings

- Real footage, archive film and experiment recordings: `asset commons search "<words>" --media-type video`, then
  `asset commons download "<File:...>" --start 12 --end 40`. Only that stretch is fetched (at most 120 seconds, at most
  720p), with its sound. Recordings (`--media-type audio`) longer than 120 seconds also need `--start` and `--end`.
- The user's own videos go in the episode's `assets/` folder.
- A clip without a sound track (every Blender shot and screen recording, many silent films) adds no sound when it
  plays.

| In the scene | What it does |
|---|---|
| `get_clip(path, height=5.0, start_seconds=0.0, border_color=None)` | the clip as an object, showing the frame at `start_seconds` until it plays; with `border_color` it is a `Group` and the clip is `.picture` |
| `play_clip(self, clip, start_seconds, end_seconds, should_play_audio=True, gain_decibels=-3.0, speed=1.0)` | plays that stretch while the scene waits; its sound goes into the mix ([sound.md](sound.md#clip-and-score-sound)) |
| `get_paper_figure(path, caption="", source="", height=4.5)` | a figure with a thin border, caption and source line |

```python
clip = get_clip("episodes/ep02/assets/experiment.mp4", height=3.5, border_color=GREY_B)
self.play(FadeIn(clip))
play_clip(self, clip, 1, 3)
```

## 3D shots

Use 3D only when a flat drawing cannot show it (anatomy, mechanisms, molecular structure, the solar system, crystal
lattices). Blender renders the shot in the background from a spec, framing the subject and smoothing surfaces, and
records where each labelled part is on screen in every frame, so the labels are drawn by ManimGL in the episode's
language and follow the model as the camera turns.

```yaml
name: heart_turn                  # output name (default: the spec file's name)
objects:
  - {type: mesh, mesh_file_path: shared/assets/3d/heart.stl, name: heart, color: "#B03A2E",
     rotation_degrees: [90, 0, 0]}
  - {type: molecule, name: ethanol, smiles: CCO}
  - {type: primitive, shape: sphere, name: sun, size: 1.0, location: [0, 0, 0], color: "#FFCC00"}
highlight_color_by_part_map: {heart: "#FFFF00"}  # glow; a part inside a mesh file is "heart/<part name>"
dimmed_parts: [sun]               # drawn faded, as context
camera: {elevation_degrees: 20, orbit_degrees: 360, start_degrees: 0, focal_length_millimeters: 50}
duration_seconds: 6               # at most 60
is_still: false                   # true: one frame, to check framing and orientation first
labeled_parts: [heart]            # screen positions per frame go to <name>.labels.json
quality: final                    # final 1920x1080 at 30 fps; draft 640x360 at 24 fps
```

- Models: `asset commons search "<words>" --media-type 3d` (STL), or the user's glb, gltf, obj, ply, stl or fbx. Mesh
  paths are relative to the spec's folder or to `production/`. Primitive shapes: sphere, cube, cylinder, cone, torus.
- Render a still (`is_still: true`, `quality: draft`) first and look at it; then the full shot.
- In the scene, the label follows its part while the clip plays:

```python
clip = get_clip("shared/assets/video/heart_turn.mp4")
self.play(FadeIn(clip))
label = get_3d_label(clip, "shared/assets/video/heart_turn.labels.json", part_name="heart", text="heart")
self.add(label)
play_clip(self, clip)
```

## Screen recordings

For product walkthroughs, UX and tool demonstrations. A headless browser follows the steps with a visible cursor and
records each step's time and the box of the element it acted on.

```yaml
name: signup_flow
url: https://example.com          # or html: a page file, relative to the spec's folder or production/
viewport: [1280, 720]
steps:
  - click: "text=Sign up"         # Playwright selectors (css=, text=, role=...)
  - type: ["#email", "ada@example.com"]
  - press: Enter
  - scroll: 600                   # pixels down
  - hover: "#menu"
  - highlight: "css=.price"       # glide there and hold, without clicking
  - wait: 1.5                     # seconds
  - goto: https://example.com/pricing
```

- Never type real passwords or personal data into a recording; typing into a password field is refused. Use demo
  data or a filled demo page.
- In the scene, `get_ui_callout` boxes the element a step acted on (steps count from 0) and knows when the step
  happened (`call.start_seconds`, seconds into the clip): play the clip up to that moment, show the box, play on.

```python
screen = get_clip("shared/assets/video/signup_flow.mp4", height=5, border_color=GREY_B)
self.play(FadeIn(screen))
call = get_ui_callout(screen, "shared/assets/video/signup_flow.steps.json", 0, "Sign up here")
play_clip(self, screen, 0, call.start_seconds)
self.play(ShowCreation(call.rectangle), FadeIn(call.label))
play_clip(self, screen, call.start_seconds, call.start_seconds + 2)
```

## Credits at the end

`render` ends every episode on the end credits page, which lists the external material the episode shows from
`credits.yaml`: [end-credits.md](end-credits.md). Do not show credits in a scene as well.
