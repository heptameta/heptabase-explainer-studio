# Clio's style: the map table

A big map spread out: the portraits and goal cards of the people involved, arrows at the crossroads, dashed lines for
the roads not taken, a time bar along the top. Basis: close viewing of eight IWM and Johnny Harris videos
(how the base map only gains and never gets replaced, how portraits and goal cards are attached, where the map goes when
zooming in), and where viewers got lost in our own videos.

**In the same series as other presenters:** the background, the type and the series' concept colours (in the series
bible and the shared code under `production/shared/`) stay the series' own, so the pictures of several presenters in one
series look like the same programme. What differs is what is drawn: Theo draws the idea itself, Fabian a small world,
Mason something running, Sophie a case that does not run, Clio a real map and the people of that one time.

---

## The visual vocabulary

- **The big-picture map:** a regional map with `GeoMap(bounds=...)`, or a seat chart (`get_seat_chart`: each side is a
  round badge arranged around a table, with its claim beside it; someone else taking a seat is `swap_seat`, alliance
  lines are `get_seat_link`). Border changes use `morph_map`; each side's territory is coloured region by region with
  `map[key].animate.set_fill(...)`. How to use maps: see the maps section of `rendering/`.
- **One colour per side:** each side's territory, portrait border, goal card and arrows use the same colour, unchanged
  for the whole episode.
- **Portraits:** get public-domain portraits with `explainer-studio asset wikipedia download-portrait` and put them in
  round frames; when you cannot get one, use a silhouette with a name tag. One portrait per person, never changed for
  the whole series.
- **Goal cards:** a small card beside the portrait, at most three lines: what they want, what they fear, what they have
  in hand (`get_goal_card`). At a crossroads, the sides' cards sit side by side.
- **The crossroads:** two or three arrows on the same map (`.get_route`, `Arrow`), one sentence of reason each; the
  chosen one is drawn solid, and those not taken become dashed lines (`DashedLine`), staying on the map to the end.
  Crossroads already passed fade to thin grey lines, and goal cards appear only in the crossroads' own beat, so the
  picture does not grow ever more crowded; at the close all the dashed lines light up once more.
- **Time bar:** one bar along the top, marking only the years of turning points; it lights up as far as we have got.
- **Where "so" goes:** the conclusion of each zoom-out beat is always written in the same place above the big-picture
  map; from the position alone the viewer knows we are now saying "what this means".
- **Opinion cards:** in another colour, saying on the card whose opinion it is; facts and commentary never use the same
  kind of card.
- **Explanation cards** (argument): one for each of the two explanations of an event (`get_explanation_card`), on either
  side of the big-picture map, in neutral colours, not any side's; once a piece of evidence is read, a pin is stuck on
  (`pin_evidence`), with a solid border for what was written at the time and a dashed border for what was said
  afterwards.
- **Counterfactual lines** (argument): "if there had been no ___" uses a dotted line, labelled; the roads the people
  themselves did not take use dashed lines; never mix the two.
- **From faint to solid** (system): the whole finished system is drawn faintly (`dim`), each crossroads fills in one
  part solid (`undim`), and the options not chosen are dashed outlines beside it (`get_alternative`).
- **Document cards:** `get_passage` with its source, or a map or table from the book cropped with
  `explainer-studio asset pdf crop`; one card carries one turning point.
- **Replay:** at the close, and every minute or two, the big-picture map fast-forwards from the start to now, each step
  lighting up briefly (`Replay`: `mark` each change to the map, then `play` to replay).

## Rhythm

- One crossroads per beat ([craft.md](craft.md#b-the-beat-of-a-crossroads)): pause 3 seconds after the guess; pause
  (`pause_duration_seconds`) after "so".
- Something new on screen every 3 to 9 seconds, mostly one stroke on the big-picture map; zoom in and out with camera
  moves, not hard cuts.
- Narration at the language reference's speaking rate; short sentences, one thing per sentence.

## Tone

- Like a guide showing you a big map: clear, steady, with empathy for the people involved; no mockery, no hindsight
  wisdom.
- Commentary only on opinion cards, the narration first saying whose view it is.
- No jokes about death, war or persecution, and no sensational adjectives.

## Do and don't

**Do**

- One big-picture map from start to finish, every turning point happening on it; it leaves when zooming in and returns
  when zooming out.
- Lay out the roads of at least two sides at every crossroads.
- Roads not taken stay on the map throughout, and light up once more at the close.

**Don't**

- Switch to another picture, or go a whole section with no picture, as soon as the detail starts.
- Name a dozen or more people in one episode.
- Tell it only through the eyes of the side driving events.
- Use AI to make fake old photos or fake witnesses.
