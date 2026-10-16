# Cards: the episode's notes and the series' whiteboard

While each episode is made, you write its cards in `production/episodes/<episode>/notes.yaml` (format in
`file-formats.md`); `deliver` checks them. From the moment of delivery, the video page shows them two ways, next to
theater mode:

- **Chapters**: the episode's parts, each a key frame beside its segments (one per scene: a title, the core idea in a
  sentence or two, and its cards, opened on demand). Choosing a segment plays it.
- **Whiteboard**: one whiteboard for the whole series, drawn like a Heptabase whiteboard. Each delivered episode is a
  section, its parts are sections inside it, each segment is a column of cards, and arrows join the cards.

The cards are the teacher's prepared notes for the lesson the video gives, written from the sources, and may be richer
than the video. A viewer copies them into their own notes app.

## What the cards must do

1. **For someone who has not watched**: they can take in all of the episode's knowledge from the cards alone.
2. **For someone who has watched**: they can quickly recall every key point the video taught, and how they came to
   understand it.

Notes that do only the first are prose; notes that do only the second are a list of slogans. Both come from writing a
card this way:

- **One card, one claim.** The title is the claim itself, a full sentence the reader could agree or disagree with:
  "Ice floats because water expands when it freezes." Never a topic ("Density"), a question ("Why does ice float?")
  or a teaser. Reading only the titles, in order, gives the whole argument.
- **The body is numbered points** that support the claim: reasons, evidence, numbers, examples, the steps of the
  argument, each one or two plain sentences, in the order the argument goes. The cases or details of a point are its
  sub-points.
- **The key phrase of a point is highlighted**, so that reading the highlights alone brings the argument back. At most
  one per point; not every point needs one.
- **A term is bold where it is defined**, explained for the series' viewer the first time it appears.
- **Pictures are the video's frames** (or credited assets), under the point whose picture the reader will remember the
  video by: a few per episode, not one per point.
- **Colour marks the few cards that matter most**: yellow for the episode's central claims, green for a conclusion a
  chain of cards arrives at, red for a common, costly mistake. Most cards have no colour.

## Parts and segments

- A segment is one scene. Its `title` is the knowledge point it teaches and its `summary` that point in one or two
  sentences; they are what the chapters view lists, so a reader sees the episode's knowledge before watching.
- A part is a stretch of the argument: divide by the argument's structure and how much each stretch carries, with no
  fixed size. Its title is also a knowledge point, never a question or a teaser.
- A segment usually has two to four cards, a card two to six points. A point that needs three sentences is probably two
  points, or a card of its own.

## Arrows

`leads_to` draws an arrow from a card to the cards the argument goes on to: a claim to its cases, reasons to the
conclusion they reach, one step to the next. Draw them forward, as the argument goes; no arrows back to earlier cards,
which would cross the whole board while the flow already reaches the answer.

On the whiteboard a card sits one row below the cards of its segment that lead to it, so a segment reads downwards and a
claim's cases sit side by side. An arrow to a card of a later segment or part runs from side to side.

The series shares one whiteboard. When an episode picks up where an earlier one stopped, add an arrow from the earlier
episode's card to this one: in the earlier episode's `notes.yaml`, `leads_to: [<episode>/<card id>]`. Read the earlier
episodes' cards before writing, so that this episode's cards connect to them instead of repeating them.

## Writing them

1. While the narration and the scenes are made, write the cards in a subagent (in Claude Code, the Agent tool). They
   need the script and the sources, not the render. Give it this file, `file-formats.md` (the notes.yaml section), the
   plan's episode, `research/` (the audience note and the reading notes), the episode's `script.yaml` and `design.md`,
   the sources the episode covers, and the earlier episodes' `notes.yaml`. It writes `notes.yaml`, covering everything
   the video teaches in the video's order, in the series' language.
2. Read the titles in order, then the highlights: they must give the argument by themselves.
3. After rendering, run `explainer-studio notes check <episode>` and fix what it reports: the parts must hold every
   scene of the render once and in order, and every frame, image and arrow must lead somewhere. `deliver` refuses
   until they fit, so the video page shows the chapters and the whiteboard from the moment of delivery.

When an episode changes after delivery (a scene added, removed or rewritten), update its cards before delivering it
again. When the user asks for cards for episodes delivered before cards existed, write them the same way, one episode
at a time in plan order, and check each with `notes check`.
