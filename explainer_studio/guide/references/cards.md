# Cards: the episode's notes and the series' whiteboard

While each episode is made, you write its cards in `production/episodes/<episode>/notes.yaml` (format in
`file-formats.md`); `deliver` checks them. From the moment of delivery, the video page shows them in two views, next
to theater mode:

- **Outline**: the episode's chapters beside the video, each with its scenes: a key frame, the scene's title, where it
  starts and its core idea in a sentence or two. Choosing a scene plays it. The outline shows no cards.
- **Whiteboard**: one whiteboard for the whole series, drawn by Heptabase. Each delivered episode is a section, its
  chapters are sections inside it, each scene is a column of cards, and arrows join the cards. The user can save it to
  their Heptabase with one button; after that, each newly delivered episode is added to the same whiteboard when its
  video page opens.

The cards are the teacher's prepared notes for the lesson the video gives, written from the sources, and may be richer
than the video. A viewer copies them into their own notes app.

## What the cards must do

1. **For someone who has not watched**: they can take in all of the episode's knowledge from the cards alone.
2. **For someone who has watched**: they can quickly recall every key point the video taught, and how they came to
   understand it.

Notes that do only the first are prose; notes that do only the second are a list of slogans. Both come from writing a
card this way:

- **A card is Hepta Markdown**, the Markdown Heptabase cards are made of: `content` is the claim as the first heading
  (`# …`), then numbered points.
- **One card, one claim.** The title is the claim itself, a full sentence the reader could agree or disagree with:
  "Ice floats because water expands when it freezes." Never a topic ("Density"), a question ("Why does ice float?")
  or a teaser. Reading only the titles, in order, gives the whole argument.
- **The body is numbered points** that support the claim: reasons, evidence, numbers, examples, the steps of the
  argument, each one or two plain sentences, in the order the argument goes. The cases or details of a point are its
  sub-points.
- **The key phrase of a point is highlighted**, so that reading the highlights alone brings the argument back: at
  most one per point, and not every point needs one. Hepta Markdown highlights with
  `<hepta-color type="background" color="yellow">…</hepta-color>`; `==…==` is not Hepta Markdown.
- **A term is bold where it is defined** (`**…**`), explained for the series' viewer the first time it appears.
- **Pictures are mostly the video's frames**, under the point whose picture the reader will remember the video by: a
  few per episode, not one per point. A picture is a line of its own, `![caption](source)`, the source a frame
  (`frame:<beat id>`, the video at the end of that beat's line), a credited asset (its `credits.yaml` path), or a
  picture drawn for the cards (in `episodes/<episode>/card-images/`; only pictures you made go there). A file picture
  must be a PNG, JPEG, WebP or GIF image, the kinds a Heptabase card shows: an SVG icon, a video or a 3D model cannot
  be one.
- **Colour marks the few cards that matter most**: yellow for the episode's central claims, green for a conclusion a
  chain of cards arrives at, red for a common, costly mistake. Most cards have no colour.

## Chapters and scenes

- Each scene of the video appears once, in order. Its `title` is the knowledge point it teaches and its `summary` that
  point in one or two sentences; they are what the video page's outline lists, so a reader sees the episode's knowledge
  before watching.
- A chapter is a stretch of the argument: divide by the argument's structure and how much each stretch carries, with
  no fixed size. Its title is also a knowledge point, never a question or a teaser.
- A scene usually has two to four cards, a card two to six points. A point that needs three sentences is probably two
  points, or a card of its own.
- A card's `id` is who it is: a card whose id changes is another card.

## Arrows

`leads_to` draws an arrow from a card to the cards the argument goes on to: a claim to its cases, reasons to the
conclusion they reach, one step to the next. Draw them forward, as the argument goes; no arrows back to earlier cards,
which would cross the whole whiteboard while the flow already reaches the answer.

On the whiteboard a card sits one row below the cards of its scene that lead to it, so a scene reads downwards and a
claim's cases sit side by side. An arrow to a card of a later scene or chapter runs from side to side.

The series shares one whiteboard. When an episode picks up where an earlier one stopped, draw an arrow from the earlier
episode's card into this one: in this episode's `notes.yaml`, `continues_from: [<episode>/<card id>]` on the card the
argument picks up at. It is written in the later episode, so an episode already delivered (and perhaps already on the
user's whiteboard) never changes for it. Read the earlier episodes' cards before writing, so that this episode's cards
connect to them instead of repeating them. The arrow goes onto the whiteboard with this episode only when the earlier
episode is on it by then, or goes with it; when the earlier episode is added later (its cards were written afterwards),
the arrow is not drawn, and is added in Heptabase with the Heptabase CLI or MCP.

## Writing them

1. While the narration and the scenes are made, write the cards in a subagent (in Claude Code, the Agent tool). They
   need the script and the sources, not the render. Give it this file, `file-formats.md` (the notes.yaml section), the
   plan's episode, `research/` (the audience note and the reading notes), the episode's `script.yaml` and `design.md`,
   the sources the episode covers, and the earlier episodes' `notes.yaml`. It writes `notes.yaml`, covering everything
   the video teaches in the video's order, in the series' language.
2. Read the titles in order, then the highlights: they must give the argument by themselves.
3. After rendering, run `explainer-studio notes check <episode>` and fix what it reports: the chapters must hold every
   scene of the render once and in order, and every frame, picture and arrow must lead somewhere. `deliver` refuses
   until they fit, so the video page shows the chapters and the whiteboard from the moment of delivery. Only when the
   user does not want cards for the episode, deliver with `--skip-notes-check`; the episode then stays off the
   whiteboard until it has cards that pass.

When an episode changes after delivery (a scene added, removed or rewritten), update its cards before delivering it
again. For an episode already on the user's saved whiteboard, the change stays in notes.yaml and never reaches the
whiteboard (see below), and a card id changed there drops the arrows that later episodes draw to it. When the user
asks for cards for episodes delivered before cards existed, write them the same way, one episode at a time in plan
order, and check each with `notes check`.

## Once the whiteboard is saved

Saving copies each episode's cards to the user's Heptabase once, and the whiteboard is theirs from then on: Studio
only adds episodes, never changes what is there, and a later change to `notes.yaml` does not reach an episode already
on it. To change a card there, find its Heptabase card id in `production/heptabase-whiteboard.json` (by
`<episode>/<card id>`, under an episode that has `imported_at`: the others are not in Heptabase yet) and edit it with
the Heptabase CLI or MCP, signed in to the account that saved it (`account_id`). Saving needs the user: they press
**Save to Heptabase** on the video page.
