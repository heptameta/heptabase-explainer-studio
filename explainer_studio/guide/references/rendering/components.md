# Components

Contents: [How components work](#how-components-work) · [By subject](#by-subject) ·
[Emphasis, focus and insets](#emphasis-focus-and-insets) · [Cards and text](#cards-and-text) ·
[Tables](#tables) · [Charts](#charts) · [Diagrams and data structures](#diagrams-and-data-structures) ·
[Code](#code) · [Time](#time) · [History and series devices](#history-and-series-devices) · [Maps](#maps) ·
[People](#people) · [Molecules](#molecules) · [Circuits](#circuits) · [Simulations and toys](#simulations-and-toys) ·
[Music](#music)

`scene_kit` builds the pictures explainer videos keep needing. Reach for a component first and adapt it only when it
is not enough: hand-written versions of the same pictures mostly fail on overlaps and on things running off the frame,
which the components already handle. Everything here comes with `from explainer_studio.scene_kit import *`. Pictures,
SVG diagrams, video clips, 3D shots, screen recordings, paper figures and credits are in [assets.md](assets.md); timing
and ManimGL syntax in [scene-code.md](scene-code.md).

Draw natively whenever you can: a native picture can light up part by part, transform and follow the narration. Use
an external picture or clip only for what native drawing cannot show. When nothing here can draw what the video needs,
use the closest option and record it with `explainer-studio gap add --kind visual`; never fake a picture silently.

## How components work

- **Full signatures.** The tables below give each component's main parameters and parts. For every option and the
  docstring, read the component's source, `scene_kit/components/<module>.py` in the installed `explainer_studio`
  package. Do not search the disk for it: the top of the guide says where it is installed.
- **Named parts.** A component returns an ordinary mobject with named parts: `chart.bars[i]`, `table.cells[r][c]`,
  `diagram.nodes["api"]`, `chart.graphs["loss"]`. Keyed parts (`nodes`, `edges`, `paths`, `graphs`, `seats`,
  `actors`) take a key, and also work whole: `FadeIn(diagram.nodes)` animates every node. Each part can be lit,
  boxed, dimmed or transformed on its own. Parts survive `.copy()`, `.animate`, `dim()` and `Transform`.
- **Three kinds of helpers.** Some return animations to play: a list (`self.play(*animate_bars_to(chart, values))`)
  or one (`self.play(animate_knob_to(knob, 12))`). Some play themselves and take the scene (`strike_claim(self, ...)`,
  `swap_content(self, ...)`, `shrink_to_inset(self, ...)`, `replay(self, ...)`, `play_clip(self, ...)`,
  `play_score(self, ...)`, the `play_questioner_*` helpers, `Replay.play(self)`). Some return a new object for you to
  draw (`get_answer_mark`, `get_checklist_strike_line`, `get_check_mark`, `get_cell_highlight`, `highlight_phrase`,
  `get_seat_link`, a map's `get_region_label`, `get_marker`, `get_route` and `get_crop_outline`). The name usually
  says which: `animate_*_to` returns the animations toward new values, `play_*` plays, `get_*` returns a new object.
- **A returned object is not part of the component.** When you clear the component, clear the object too, or add it
  to the component after drawing it: `self.play(ShowCreation(mark)); card.add(mark)`.
- **`swap_content` fades with `FadeOut` and `FadeIn`.** An object whose updater keeps changing its shape (a traced
  path, a counting number) cannot go through it; clear its updaters first or let it leave with `VFadeOut`
  ([scene-code.md](scene-code.md#manimgl-idioms)).
- **Size with arguments, never by shrinking.** Components take `width`, `height`, `max_width`, `max_height`,
  `font_size` or `cell_size`. Decide the area first, build at that size, then place with `to_edge`, `next_to` and
  `arrange`. Scaling a built component down pushes its labels under the minimum text size (`text_too_small`).
- **Checks.** Props whose text is texture (`get_document`, a `shrink_to_inset` thumbnail) are decorative, so the
  automatic checks skip their text. Your own props need `mark_decorative(...)`
  ([checks.md](checks.md#decorative-marking-and-keep_inside)).
- **Graph specs.** A node is `"api"` or `("api", "API server")` (id and shown text); an edge is `("a", "b")` or
  `("a", "b", "label")`.

## By subject

| Subject | Usually needs |
|---|---|
| Mathematics, physics | ManimGL itself ([scene-code.md](scene-code.md#manimgl-idioms)); [simulations](#simulations-and-toys); [circuits](#circuits); experiment footage ([assets.md](assets.md)) |
| Chemistry, biochemistry, pharmacy | [molecules](#molecules); molecular 3D and lab footage ([assets.md](assets.md)) |
| Biology, medicine | diagrams of cells and organs, micrographs, anatomy in 3D ([assets.md](assets.md)); population and epidemic models ([simulations](#simulations-and-toys)) |
| History, religion, art, literature | [maps](#maps); [time](#time); [history devices](#history-and-series-devices); works, documents, portraits and archive film ([assets.md](assets.md)); [people](#people) |
| Geography, economics, politics, society, statistics | [maps](#maps) and choropleths; [charts](#charts) from real data ([assets.md](assets.md)) |
| Music | [music](#music); recordings ([assets.md](assets.md)) |
| Law, philosophy, psychology, business cases | [people](#people); [cards](#cards-and-text) for claims and evidence; [diagrams](#diagrams-and-data-structures) for arguments and processes |
| Software, products | [diagrams](#diagrams-and-data-structures), sequence diagrams, [code](#code); screen recordings ([assets.md](assets.md)) |

## Emphasis, focus and insets

| Component | What it does | Notes |
|---|---|---|
| `get_highlight_rectangle(mobject, color=HIGHLIGHT_RECTANGLE_COLOR, buff=SMALL_BUFF, stroke_width=2)` | a thin box around something | |
| `dim(*mobjects, opacity=DIM_OPACITY)` / `undim(*mobjects)` | lists of animations that fade objects back and restore them exactly | lowers stroke and fill without giving outlines a fill; undim the same object you dimmed. A second `dim` fades further and `undim` still restores the look from before the first; `undim` leaves an object that is not dimmed alone |
| `swap_content(self, old_content, new_content, run_time=1.0, shift=ORIGIN)` | plays: the old content leaves, then the new arrives | `old_content`, `new_content` may be lists (pictures allowed). A `FadeOut` and a `FadeIn` in one play smear both pictures together |
| `get_brace_label(mobject, text, direction=DOWN, color=GREY_A, is_tex=False)` | a brace with a label | `VGroup(brace, label)` |
| `get_meta_background()` | the full-frame dark-grey commentary layer | |
| `get_inset(content=None, height=4.5, border_color=GREY_B)` | a black 16:9 window with a thin border | a `Group` |
| `shrink_to_inset(self, *mobjects, height=3.4, corner=UL, buff=0.45, run_time=1.5)` | plays: fades in the grey layer and shrinks the given content into a framed inset; returns `(meta_background, inset)` | plays `whoosh_out`; the inset's text is exempt from the size check |
| `expand_from_inset(self, meta_background, inset, run_time=1.5)` | plays: grows the inset back to full frame; returns the content | plays `whoosh_in`; checks apply again, except to what was decorative before the inset |
| `get_shadow(mobject, opacity=0.25)` | a faint copy of the current state, to keep under a change | `self.add(get_shadow(curve))`, then change `curve` |
| `Replay(board)` | snapshots of a big-picture board, played back fast | `replay.mark("1937")` after each change; `replay.play(self)` fast-forwards through the marks and returns to now |

Stepping back into the commentary layer:

```python
with self.play_beat("last_time"):
    meta_background, inset = shrink_to_inset(self, formula, label, box)
    note = Text("Last episode", font_size=HEADING_FONT_SIZE).to_edge(UP)
    self.play(FadeIn(note))
    self.play(FadeOut(note))
    back = expand_from_inset(self, meta_background, inset)
```

Pass the objects to shrink explicitly.

## Cards and text

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_title_card(title, subtitle="", color=WHITE)` | a title with an underline | |
| `get_section_label(text, color=WHITE, font_size=HEADING_FONT_SIZE)` | a quiet section title | |
| `get_quote(quote, author, year="", width=11)` | a quotation and its attribution | |
| `get_fact_chip(text, color=GREY_A, font_size=SMALL_FONT_SIZE)` | a small rounded chip for one fact, name or year | |
| `get_question_card(text, color_by_word_map=None, width=5.5)` | a short question (three lines at most), key nouns coloured | `color_by_word_map={"pump": YELLOW}` |
| `get_reframe_card(old_question, new_question, color_by_word_map=None)` | the old question (dim) becoming the new one | |
| `get_claim(text, tag, color_by_word_map=None, width=6.0)` | a claim the episode will test or overturn, with its status tag ("Intuition", "Rival", "Assumption") from the start | `.box`, `.text`, `.tag` |
| `strike_claim(self, claim, replacement_text="", tag="", color_by_word_map=None, direction=DOWN)` | plays: crosses the claim out and puts the sentence that replaces it beside it; returns the new claim | |
| `get_checklist(title, row_texts, checked_row_indices=(), width=4.6, t2c_by_row_index_map=None, color_by_row_index_map=None)` | a numbered list that grows or is ticked off | `.title`, `.rows[i]` = (box, label), `.checks`; `add_checklist_row(card, text)`, `get_checklist_strike_line(card, i)`, `get_check_mark(card, i)` |
| `get_answer_card(expected_value_by_label_map, title, width=3.8)` | set out before a run: what the answer should be, one row per source or side | `.rows[i]` = (label, value, slot); `get_answer_mark(card, i, is_correct=True)` |
| `get_scoreboard(columns, width=4.4)` | a corner board that gains a row per run | `.header`, `.rows`; `add_scoreboard_row(board, values, should_highlight=False)` |
| `get_knob(name, value, unit="", min_value=0, max_value=1, decimal_place_count=1, width=3.2)` | a named number with a unit on a track, shown before it turns | `.name`, `.track`, `.handle`, `.value`, `.tracker`; `animate_knob_to(knob, value, run_time=2)` |
| `get_goal_card(name, goal="", fear="", leverage="", color=BLUE_C)` | one party's goal card: what it wants, fears and has in hand | `.name`, `.rows`, `.box` |
| `get_explanation_card(title, claim, color=BLUE_C, width=3.6)` | one side's explanation of an event, with room for evidence below | `.title`, `.claim`, `.box`, `.pins`; `pin_evidence(card, text, was_written_at_the_time=True)` (solid chip: written at the time; dashed: said afterwards; two to four pins) |
| `get_outline_bar(part_names)` | a thin bar along the bottom naming the parts of the answer | `.cells[i]`; `animate_outline_to(bar, i)` |
| `get_passage(text, width=10.0, source="", was_written_at_the_time=None)` | a block of source text as an object, wrapped and left-aligned | `.lines[i]`; `highlight_phrase(passage, phrase, style="box" / "underline" / "fill")`; framed solid or dashed with a tag when `was_written_at_the_time` is given |

A claim overturned, then a list, an answer card and a scoreboard (one beat each):

```python
claim = get_claim("Heavier things fall faster.", tag="Intuition").shift(UP)
with self.play_beat("intuition"):
    self.play(FadeIn(claim))
    new_claim = strike_claim(self, claim, "Everything falls at the same rate.", tag="Galileo")

rules = get_checklist("Rules", ["Sign every line", "Keep a copy"]).to_edge(LEFT)
card = get_answer_card({"by hand": "2.0", "last version": "1.0"}, title="Expected").to_edge(RIGHT)
with self.play_beat("rules"):
    swap_content(self, [claim, new_claim], [rules, card])
    self.play(*add_checklist_row(rules, "Number the pages"))
    strike_line = get_checklist_strike_line(rules, 1)
    self.play(ShowCreation(strike_line), *dim(rules.rows[1]))
    marks = [get_answer_mark(card, 0, is_correct=True), get_answer_mark(card, 1, is_correct=False)]
    self.play(*map(ShowCreation, marks))
    card.add(*marks)

board = get_scoreboard(["version", "loss", "output"]).to_corner(UR)
knob = get_knob("steering angle", 6.5, unit="°", min_value=0, max_value=30).to_corner(DL)
with self.play_beat("runs"):
    swap_content(self, [rules, card, strike_line], [board, knob])
    self.play(*add_scoreboard_row(board, ["six layers", "2.31", "the"]))
    self.play(*add_scoreboard_row(board, ["eight layers", "1.94", "the cat"], should_highlight=True))
    self.play(animate_knob_to(knob, 12, run_time=2))
```

## Tables

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_table(rows, header=None, column_widths=None, row_height=0.6)` | a plain grid, lit cell by cell | `.cells[r][c]`, `.header_cells[c]`, `.get_row(r)`, `.get_column(c)`, `.grid`; `get_cell_highlight(table, r, c)` returns a box sized to the cell |
| `get_heatmap(values, row_labels=None, column_labels=None, cell_size=0.45, should_show_values=False)` | coloured squares: attention patterns, weight matrices | `.cells[i][j]`, `.row_labels`, `.column_labels`; reveal row by row |
| `get_vector_column(values, shown_entry_count=None, decimal_place_count=1)` | a column vector, optionally cut with ⋮ | `.entries[i]`, `.brackets` |

```python
table = get_table([["Paris", 2.1], ["Lyon", 0.5], ["Nice", 0.3]], header=["city", "millions"])
self.play(FadeIn(table))
self.play(ShowCreation(get_cell_highlight(table, 1, 1)))
```

A table with too many columns breaks the size check: keep only the columns the narration uses.

## Charts

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_bar_chart(values, labels=None, colors=None, max_value=None, width=8, height=4, y_label="")` | bars on a baseline with value labels | `.bars[i]`, `.value_labels[i]`, `.labels[i]`, `.baseline`, `.y_label`; `animate_bars_to(chart, values)` (labels count along) |
| `get_line_chart(x_values, {"name": y_values}, x_label="", y_label="", y_range=None, width=9, height=4.5)` | axes with one line per series and end labels | `.axes`, `.graphs[name]`, `.end_labels[name]`, `.x_label`, `.y_label` |
| `get_run_family(runs, x_values=None, x_label="", y_label="")` | many runs of one toy on one pair of axes, thin and translucent | `.axes`, `.lines[key]`; `highlight_run(family, run_key)`, `highlight_run(family, None)` restores all |
| `get_scatter({key: (x, y[, size])}, is_x_log_scale=False, x_label="", y_label="", label_keys=None)` | scatter or bubble chart (Rosling) | `.axes`, `.dots[key]`, `.labels[key]`; `animate_scatter_to(chart, {key: (x, y[, size])})` |
| `get_population_pyramid(groups, left_values, right_values)` | age groups, bars growing left and right | `.left_bars[i]`, `.right_bars[i]`, `.group_labels[i]` |
| `get_waterfall([(name, delta), ...], total_label=True)` | a total built up step by step | `.bars[i]`, `.value_labels[i]`, `.labels[i]`, `.connectors[i]`, `.baseline` |
| `get_sankey([(source, target, amount), ...], width=11, height=5.6)` | flows between stages: energy, money, people | `.nodes[name]`, `.bands[(source, target)]`, `.labels[name]` |
| `get_parliament({party: seats}, radius=3.6)` | seats in a hemicycle | `.seats[party]`, `.legend[party]`, `.majority` |
| `get_pie({name: value}, radius=2.2, inner_radius=0.0)` | pie, or donut when `inner_radius > 0` | `.slices[name]`, `.labels[name]` |
| `get_distribution(pdf, x_range, width=9, height=4)` with `build_normal_pdf(mu, sigma)` | a density curve | `.axes`, `.curve`, `.get_area_between(a, b)` returns the filled area |
| `get_histogram(values, bin_count=12, x_range=None)` | counts in equal bins | `.axes`, `.bars[i]`, `.bin_edges` |
| `get_area_under(axes, curve, fill_color=BLUE_C, opacity=0.4)` | the area under a curve, rebuilt from the curve every frame | follows any `Transform` or updater of the curve |
| `read_csv(path)` | rows of a CSV as dicts of strings | data from the asset commands ([assets.md](assets.md)) |

`CHART_COLORS` are the default series colours. The chart axes cross at the bottom left of the data range, so a
40 to 90 range stays on screen.

```python
chart = get_bar_chart([3, 5, 8], labels=["A", "B", "C"], colors=[BLUE_C, TEAL, YELLOW], max_value=13,
                      y_label="height (m)")
self.play(ShowCreation(chart.baseline), FadeIn(chart.labels), FadeIn(chart.y_label))
self.play(LaggedStart(*(GrowFromEdge(bar, DOWN) for bar in chart.bars)), FadeIn(chart.value_labels))
self.play(*animate_bars_to(chart, [3, 5, 12]), run_time=1.5)

lines = get_line_chart([0, 1, 2, 3, 4], {"train": [2.3, 1.6, 1.2, 1.0, 0.9], "test": [2.4, 1.9, 1.7, 1.7, 1.8]},
                       x_label="epoch", y_label="loss")
self.play(FadeIn(VGroup(lines.axes, lines.x_label, lines.y_label)))
self.play(ShowCreation(lines.graphs["train"]), FadeIn(lines.end_labels["train"]))

axes = Axes((0, 4), (0, 4), width=6, height=4)
curve = axes.get_graph(lambda x: 0.2 * x * x, x_range=(0, 4)).set_stroke(TEAL, 3)
area = get_area_under(axes, curve)
self.play(FadeIn(area))
self.play(Transform(curve, axes.get_graph(lambda x: 0.05 * x ** 3, x_range=(0, 4)).set_stroke(TEAL, 3)))
```

- Never transform a curve and a separately made area each on their own: their points do not correspond and they come
  apart halfway. `get_area_under` follows the curve.
- Plot only within the axes' range: a curve that runs past a drawn axis looks broken (the checks do not see it).
- `dim` lowers opacity to 0.35 at most; Sankey bands are already translucent, so dim them further with
  `dim(*bands, opacity=0.12)`.

## Diagrams and data structures

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_graph_diagram(nodes, edges, direction="LR", shape="box", dashed_edges=(), max_width=12.5, max_height=6.5)` | flowcharts, architectures, DAGs, laid out automatically in layers (like Graphviz dot); long edges bend around the layers between | `.nodes[id]` = (shape, label), `.edges[(a, b)]` = (line, tip[, label]), `.paths[(a, b)]`; `direction` LR, RL, TB or BT; `shape` box, round or circle; `dashed_edges`: a road not taken, a proposed link |
| `get_flow_token(color=YELLOW, label="")` + `flow_along(token, paths, run_time_per_edge=0.9)` | something travelling along edges: a request, a packet, current | one animation through a list of paths |
| `relabel(node, text)` | a node's label changing (a question cell becoming the name of what answers it) | one animation; undim a dimmed node in an earlier play first |
| `knock_out(diagram, node_id)` / `put_back(diagram, node_id)` | take one block out to show who suffers: the block and its edges dim, a cross goes over it; then bring it back as it was | lists of animations; the cross is the node's `.cross` |
| `get_alternative(part, label, direction=RIGHT)` | the option not chosen for one part: a dashed outline beside it | `.outline`, `.label` |
| `get_side_by_side(left, right, labels=("", ""))` | two versions side by side under labels, a divider between | `.left`, `.right`, `.labels`, `.divider`; `run_both(token_a, paths_a, token_b, paths_b, run_time=3)`: both arrive together |
| `get_tree(("root", [child, ...]), shape="circle")` | a tidy tree drawn top-down | `.nodes[path]` (path = tuple of child indices, root `()`), `.edges[path]`, `.node_by_label_map[label]` |
| `get_sequence_diagram(actors, [(from, to, text), ...])` | protocols and API calls (from == to: a self-call) | `.actors[id]`, `.lifelines[id]`, `.messages[i]` |
| `get_array(values)` | an array of boxes with indices | `.cells[i]` = (box, value), `.indices[i]`; `swap_cells(array, i, j)` |
| `get_pointer(target, label="", direction=UP)` | an arrow pointing at a cell (`i`, `head`) | move it by `Transform` to a new pointer |
| `get_linked_list(values)`, `get_stack(values)` | a singly linked list; a vertical stack (top is last) | `.nodes[i]`, `.links[i]`; `.elements[i]` |
| `get_curved_arrow(start, end, angle=-PI / 3)` | a thin curved arrow between two objects ("attends to", "affects") | `.arc`, `.tip`; draw `ShowCreation(arrow.arc)` then `FadeIn(arrow.tip)`. Mobjects are joined at their centres: pass points such as `a.get_top()` to land on an edge |

```python
d = get_graph_diagram(["user", ("api", "API server"), ("db", "Database"), "cache"],
                      [("user", "api"), ("api", "db", "read"), ("api", "cache")], dashed_edges=[("api", "cache")])
self.play(LaggedStartMap(FadeIn, d.nodes), LaggedStartMap(ShowCreation, d.edges))
token = get_flow_token(YELLOW, label="request")
self.play(flow_along(token, [d.paths[("user", "api")], d.paths[("api", "db")]]))
self.play(FadeOut(token))
self.play(*knock_out(d, "db"))
self.play(relabel(d.nodes["cache"], "Redis"))
```

`self.play(*put_back(d, "db"))` brings a knocked-out block back. A deep left-to-right diagram (more than about five layers) gets small text: switch to
`direction="TB"`, shorten edge labels, or split it into two pictures. A system that grows block by block: draw it
faint first (`dim`), `undim` one part at each fork, show its `get_alternative` beside it.

## Code

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_code_panel(code, language="python", font_size=22, should_show_line_numbers=True, width=None)` | syntax-highlighted code, one object per line | `.lines[i]` (0-based), `.numbers[i]`, `.background`; `box, animations = highlight_lines(panel, [i, ...])` boxes those lines and dims the rest |
| `read_file_excerpt(path, first_line_number=None, last_line_number=None, search_text=None, following_line_count=0)` | the text of a real file (lines `first_line_number` to `last_line_number`, 1-based, or the first line containing `search_text` plus `following_line_count` more) | records the file, the lines and a fingerprint; `render` warns when the file changed since the last preview |

```python
panel = get_code_panel(read_file_excerpt("sources/pump.py", search_text="kept = protons", following_line_count=3),
                       width=8)
self.play(FadeIn(panel.background), LaggedStartMap(FadeIn, panel.lines, lag_ratio=0.1))
box, animations = highlight_lines(panel, [1, 2])
self.play(ShowCreation(box), *animations)
```

- Real content on screen (code, configuration, logs, documents) always comes from `read_file_excerpt`, never typed by
  hand. `search_text=` survives edits above the line better than line numbers.
- Put real program output into `production/sources/` first and excerpt it from there.

## Time

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_timeline(start_year, end_year, step_years=10, width=12)` | a year line (a `NumberLine`) | `.numbers`; `get_event_marker(timeline, year, label, direction=UP)` |
| `get_timeline_chart(start_year, end_year, events=[(year, label)], periods=[(start, end, name)], lives=[(name, born, died)], label_by_tick_value_map=None)` | a year axis with lanes for periods (bands), lives (bars) and events (stems and labels), arranged so nothing overlaps | `.axis`, `.periods[name]`, `.lives[name]`, `.events[label]`, `.convert_year_to_x(year)` (the frame x of a year as built); `label_by_tick_value_map={6: "8/6", 9: "8/9"}` for an axis of days or hours |

```python
tl = get_timeline_chart(1500, 1700, events=[(1517, "95 theses"), (1648, "Westphalia")],
                        periods=[(1618, 1648, "Thirty Years' War")], lives=[("Luther", 1483, 1546)])
self.play(FadeIn(tl.axis))
self.play(FadeIn(tl.lives["Luther"]), FadeIn(tl.events["95 theses"]))
self.play(FadeIn(tl.periods["Thirty Years' War"]), FadeIn(tl.events["Westphalia"]))
```

## History and series devices

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_portrait_card(name, original_name, years, school_color=GREY_B, image_file_path=None, height=2.4)` | a portrait with a thin border in the person's school or stance colour, the name in the video's language, the original and the dates | `image_file_path` is a path ([assets.md](assets.md#portraits)); without it a grey silhouette stands in. A `Group` |
| `get_portrait_placeholder(height=2.4)` | the silhouette alone | |
| `get_document(title, subtitle="", year="", width=3.2)` | a stand-in for the first page of a primary text, its lines fake and its text decorative | |
| `get_quote_pair(original, translation, source="", width=11)` | a quotation in two languages: original small above, translation large below | |
| `get_running_list(title, [(question, answer), ...], row_count, active_index=None)` | a list that fills up across episodes; unfilled rows are placeholders | `.title`, `.rows` |
| `get_ledger(row_labels, column_labels, text_by_cell_map={(r, c): text}, active_row_index=None)` | a ledger table that returns across episodes | `.header`, `.body`, `.grid` |
| `get_series_map(titles, current_index)` | episode cells with the current one boxed, "you are here" | `current_index` is 0-based |
| `get_episode_title_card(series_name, episode_label, title, subtitle="", series_map=None)` | a title card | |
| `get_parts_strip(titles, active_part_number)` | the parts of a unit with the current one lit | `active_part_number` is 1-based |
| `get_seat_chart({key: {"name", "claim", "badge", "color"}}, title="")` | the parties of a court, council or faction round one table, each a badge with a name and a claim: the big-picture board when there is no map | `.table`, `.seats[key]` = (face, name, claim), `.link_by_seat_pair_map`; `swap_seat(chart, key, name, claim="")`, `change_seat_claim(chart, key, claim)`, `get_seat_link(chart, first_key, second_key, is_dashed=False, label="")` (solid: an alliance; dashed: a deal not yet made or broken) |
| `play_questioner_entrance(self, questioner)`, `play_questioner_question(self, questioner, text)`, `play_questioner_exit(self, questioner, *extra_mobjects)` | the series' questioner floating in, asking in a bubble (returns the bubble), leaving | play `questioner` and `bubble` sounds |

```python
chart = get_seat_chart({"pope": {"name": "Pope", "claim": "Burn the heretic"},
                        "emperor": {"name": "Emperor", "claim": "Keep the peace"},
                        "elector": {"name": "Elector", "claim": "Protect Luther"}}, title="Worms, 1521")
replay = Replay(chart)
self.play(FadeIn(chart))
replay.mark("1521")
self.play(*swap_seat(chart, "pope", "New pope", claim="Call a council"))
replay.mark("1523")
link = get_seat_link(chart, "emperor", "elector", is_dashed=True)
self.play(ShowCreation(link))
replay.play(self)
```

An explanation card grows downward as evidence is pinned: leave room below it.

**The questioner** is series code, not a `scene_kit` object. Write it once in `production/shared/` (the series bible
decides whether the series has one). `play_questioner_entrance` and `play_questioner_question` need an object with
`look_at(target)` and `get_bubble(text, font_size=...)` returning a bubble with `.body` and `.content`:

```python
"""production/shared/questioner.py: the series' questioner (series bible: a teal student who only asks)."""

from explainer_studio.scene_kit import *


def get_questioner(color=TEAL) -> VGroup:
    person = get_person(color, height=1.6, expression="thinking")

    def look_at(target) -> VGroup:
        return person   # a plain figure always faces right

    def get_bubble(text: str, font_size: float = LABEL_FONT_SIZE) -> VGroup:
        content = Text(text, font_size=font_size).set_color(BLACK)
        box = RoundedRectangle(width=content.get_width() + 0.5, height=content.get_height() + 0.4, corner_radius=0.2)
        box.set_fill(WHITE, 1).set_stroke(GREY_B, 2).next_to(person.head, UR, buff=0.2)
        content.move_to(box)
        bubble = VGroup(box, content)
        bubble.body, bubble.content = box, content
        return bubble

    person.look_at, person.get_bubble = look_at, get_bubble
    return person
```

```python
student = get_questioner().to_corner(DL)
with self.play_beat("student_asks"):
    play_questioner_entrance(self, student)
    bubble = play_questioner_question(self, student, "Why not just pump harder?")
with self.play_beat("answer"):
    play_questioner_exit(self, student, bubble)
```

## Maps

`GeoMap` draws countries, land, rivers, lakes, cities and any GeoJSON as native shapes, so a region can be coloured,
labelled, moved along or morphed beat by beat. Country keys are ISO alpha-3 codes (`FRA`, `DEU`, `TWN`). The map data
is Natural Earth (public domain, present-day borders), installed with the environment.

| Call | What it does |
|---|---|
| `GeoMap(projection="robinson")` | the world |
| `GeoMap(bounds=(west, south, east, north))` | a region, cropped to a lon/lat box, true shapes along its middle latitude |
| `GeoMap(projection="ortho", center=(lon, lat))` | a globe seen from a point; add `globe.get_sphere()` (the ocean) behind it |
| `GeoMap(regions=[...])` | only these codes, names or continents |
| `GeoMap(geojson="shared/assets/geo/1815.geojson", key_property="NAME", reference_map=other_map)` | your own data in the same frame as another map (`reference_map=`), so they line up |
| `map["FRA"]` | a region (a group of polygons); `.animate.set_fill(...)` colours it |
| `map.color_by_values({"CHN": 1.4e9, ...}, is_log_scale=True)` + `get_color_legend("fewer", "more")` | a choropleth and its legend |
| `map.get_region_label(key, text=None)`, `map.get_marker(lon, lat, "Paris")`, `map.get_route([(lon, lat), ...])` | a region's name (everyday name in the episode's language), a dot with a label, a great-circle route (`.path`, `.tip`) |
| `map.get_rivers()`, `map.get_lakes()`, `map.get_cities(names=[...])`, `map.get_graticule()`, `map.get_crop_outline()` | overlays; `get_crop_outline()` makes cropped edges read as a deliberate map frame |
| `map.project(lon, lat)`, `map.check_is_visible(lon, lat)`, `map.format_region_name(key)` | a frame point (follows the map after it moves or scales; do not rotate maps); whether a point is on the visible side of a globe |
| `morph_map(old_map, new_map)` | borders changing: the new regions fade in under, the old fade out on top; keep working with `new_map` afterwards |
| `merge_regions({"Frankish realm (approx.)": ["FRA", "DEU", "ITA"]})` | an approximate historical realm made from modern countries, for `GeoMap(geojson=..., key_property="NAME")` |

```python
europe = GeoMap(bounds=(-12, 34, 32, 60))
paris = europe.get_marker(2.35, 48.86, "Paris")
route = europe.get_route([(2.35, 48.86), (12.5, 41.9)])
outline = europe.get_crop_outline()
self.play(FadeIn(europe), ShowCreation(outline))
self.play(europe["FRA"].animate.set_fill(BLUE_C), FadeIn(europe.get_region_label("FRA")), FadeIn(paris))
self.play(ShowCreation(route.path))
self.play(FadeIn(route.tip))

realm = GeoMap(geojson=merge_regions({"Frankish realm (approx.)": ["FRA", "DEU", "ITA", "BEL", "NLD"]}),
               key_property="NAME", reference_map=europe, fill_color=GOLD_E)
self.play(morph_map(europe, realm))
```

- Overlays (labels, markers, routes, the crop outline) are returned, not added: clear them yourself.
- Historical borders: use a reliable GeoJSON and record where it came from in `credits.yaml`; without one, use
  `merge_regions` and say on screen or in the narration that the borders are modern approximations.
- Region labels default to everyday names in the episode's language (the language reference says which languages have
  them; English otherwise); pass `text=` to change one.

## People

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_person(color=BLUE_C, pose="stand", expression="neutral", height=2.2, hat=None, facing="right")` | a plain figure standing for a role (a king, a voter, a defendant), not a likeness | `.head`, `.face`, `.body`, `.arms`, `.legs`, `.hat`; poses stand, wave, point, arms_up, think, shrug; expressions neutral, happy, sad, surprised, angry, thinking, worried; hats crown, top, cap, helmet |
| `restyle(person, **changes)` | the same person with a new pose, expression, colour or facing, where it stands | `self.play(Transform(p, restyle(p, expression="happy")))` |
| `say(person, text, is_thought=False)` / `unsay(person)` | a speech or thought bubble; lists of animations | |
| `get_crowd(person_count, colors=None, row_count=None)` | people in staggered rows | `crowd[i]` |

```python
king = get_person(GOLD_C, hat="crown").shift(3 * LEFT)
voter = get_person(BLUE_C, facing="left").shift(3 * RIGHT)
self.play(FadeIn(king), FadeIn(voter))
self.play(*say(king, "Taxes double!"))
self.play(Transform(voter, restyle(voter, expression="angry", pose="arms_up")))
self.play(*unsay(king))

crowd = get_crowd(12)
self.play(FadeIn(crowd))
self.play(*(Transform(person, restyle(person, color=RED_C)) for person in crowd[:4]))   # a share, faces kept
```

Keep one body colour per character for the whole series. Recolouring a person with `set_color` paints the face too;
`restyle(color=...)` keeps it.

## Molecules

Geometry comes from RDKit; never draw a structure by hand.

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_molecule(smiles, bond_length=0.75, should_show_carbons=False)` | a skeletal formula: carbons implied, heteroatoms shown and coloured (molecules of two heavy atoms or fewer write every atom) | `.atoms[i]`, `.bonds[j]`, `.get_atom_point(i)`, `.get_bond_point(j)`, `.list_matches(smarts)` (atom index tuples), `.get_parts_for(indices)`, `.highlight(indices, color)` (an animation) |
| `get_reaction(left_smiles, right_smiles, label="")` | reactants → products in one row | `.left[i]`, `.right[i]` (molecules), `.arrow`, `.label` |
| `get_mechanism_arrow(source, ("atom", i), target, ("bond", j))` | a curly arrow: electrons from an atom (lone pair) or a bond to an atom or bond | `.arc`, `.tip` |

```python
acid = get_molecule("CC(=O)Oc1ccccc1C(=O)O").shift(2 * LEFT)
self.play(FadeIn(acid))
self.play(acid.highlight(acid.list_matches("C(=O)[OH]")[0], YELLOW))
reaction = get_reaction(["CBr", "[OH-]"], ["CO", "[Br-]"], label="SN2").to_edge(DOWN)
self.play(FadeIn(reaction))
arrow = get_mechanism_arrow(reaction.left[1], ("atom", 0), reaction.left[0], ("atom", 0))
self.play(ShowCreation(arrow.arc))
self.play(FadeIn(arrow.tip))
```

## Circuits

`get_circuit(component_specs, unit_size=1.2)` draws components between grid points; each spec is
`(kind, (x0, y0), (x1, y1), "label")`. Kinds: wire, resistor, capacitor, inductor, battery, source, ac_source, lamp,
switch_open, switch_closed, diode, led, ground, ammeter, voltmeter. Parts: `circuit["R1"]` (by label; unlabelled ones
are `"kind#i"`) with `.lead`, `.body`, `.label`; `.wires`; `.nodes` (dots where three or more ends meet);
`.get_grid_point(x, y)`; `.get_current_path(points)` (a path for `flow_along`). A switch flips by `Transform` to
`get_component("switch_closed", start, end)`.

```python
circuit = get_circuit([("battery", (0, 0), (0, 2), "9 V"), ("wire", (0, 2), (3, 2)),
                       ("resistor", (3, 2), (3, 0), "R1"), ("lamp", (3, 0), (0, 0), "lamp")], unit_size=1.4)
self.play(FadeIn(circuit))
token = get_flow_token(YELLOW)
current_path = circuit.get_current_path([(0, 2), (3, 2), (3, 0), (0, 0), (0, 2)])
self.play(flow_along(token, [current_path], run_time_per_edge=3))
```

Maps, circuits and molecules remember where their points are: move or scale them freely, but do not rotate them.

## Simulations and toys

Correct motion comes from solving the equations, never from guessing a curve.

| Call | What it gives |
|---|---|
| `solve(lambda t, y: [...], y0, t_end)` | a `Solution`: `.t`, `.y`, `.get_state_at(t)`, `.duration_seconds` |
| `replay(self, solution, lambda state, t: ..., speed=1)` | plays: advances simulated time with the video clock and moves objects every frame |
| `solve_pendulum(theta0=1.0, length=1.0, damping=0.0, t_end=8)` + `get_pendulum(length=2.5)` | the full nonlinear pendulum; `.set_angle(theta)`, `.rod`, `.bob` |
| `solve_orbit(e=0.5, period_count=1)` | a Kepler orbit, state (x, y, vx, vy) |
| `solve_sir(beta=0.3, gamma=0.1, duration_days=160)`, `solve_predator_prey(...)` | `(times, {label: series})`, ready for `get_line_chart` |
| `run_toy(function, *args)` | the result of a toy program's function, cached until the program's file changes |

```python
pendulum = get_pendulum(length=2.5)
solution = solve_pendulum(theta0=1.0, length=2.5, t_end=4)
self.play(FadeIn(pendulum))
replay(self, solution, lambda state, t: pendulum.set_angle(state[0]))
```

A toy program (`production/shared/toy.py`) and a chart of its numbers:

```python
def leak(protons: int = 1000, rate: float = 0.1, seconds: int = 10) -> list[int]:
    kept, history = protons, [protons]
    for _ in range(seconds):
        kept -= int(kept * rate)
        history.append(kept)
    return history


assert leak(1000, 0.1, 1) == [1000, 900]   # worked by hand
```

```python
from shared.toy import leak

history = run_toy(leak, 1000, 0.1, 10)
chart = get_line_chart(list(range(len(history))), {"protons": history}, x_label="second", y_label="kept")
```

For a traced path, ManimGL's `TracedPath(dot.get_center)` follows a moving dot. Its points keep growing, so call
`trail.clear_updaters()` before it leaves through `swap_content` or `FadeOut`; otherwise the scene stops with
"operands could not be broadcast together".

## Music

| Component | What it draws | Parts and helpers |
|---|---|---|
| `get_score(source, width=11.0, tempo_scale=1.0)` | a score engraved by Verovio from ABC, MusicXML, MEI or Humdrum text, or a file under `production/` | `.notes[k]` (in playing order), `.get_notes_at(time_seconds)`, `.events`, `.duration_seconds` |
| `play_score(self, score, color=YELLOW, should_play_audio=True)` | plays: each note lights while it sounds; a plain piano rendering goes into the mix | waits for the whole score |

```python
score = get_score("X:1\nM:4/4\nL:1/4\nK:C\nC D E F | G2 G2 |]", width=10)
self.play(FadeIn(score))
self.play(score.notes[4].animate.set_color(YELLOW))
```

How the score's sound and other sounds are timed: [sound.md](sound.md).
