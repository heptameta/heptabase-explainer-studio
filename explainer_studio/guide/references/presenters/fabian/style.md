# Fabian's style: the small world

One fixed small world: a few groups of people, a few things, one spine picture that grows along with the episode, and a
board where the conclusions are written. Basis: close viewing of four CGP Grey videos (how icons and
colours are used, how the spine picture grows), and where viewers got lost in our own videos.

**In the same series as Theo:** the background, the type and the series' concept colours (in the series bible and the
shared code under `production/shared/`) stay the series' own, so the pictures of two presenters in one series look like
the same programme. What differs is what is drawn: Theo draws the idea itself (a number line, vectors, a molecular
machine, a table); Fabian draws the people and things of a small world.

---

## The visual vocabulary

- **One icon and one colour per actor:** the king, landowners, generals, peasants, voters, patients. Use the scene_kit
  figures (`get_person`, `get_crowd`) or a simple shape plus a colour. That colour appears in every chart (group boxes,
  bars, pie slices, maps), unchanged for the whole episode and ideally the whole series. The icon enters first, before
  it is put into a chart.
- **Icons draw the real thing:** a general is a general, a musketeer is a musketeer, a treasure chest is a treasure
  chest; no metaphors.
- **The spine picture:** a flowchart, a bar chart, a board written downwards layer by layer, changed on the same picture
  for the whole episode, never redrawn. Each step that runs adds one stroke; at the close it is the recap.
- **The conclusion board** (`get_checklist` or a column of short sentences): it appears after each step runs, one line
  longer, with that step's conclusion as one complete sentence, and leaves on the next beat; at seams, recaps and the
  close the whole board appears. It is not on screen during details.
- **Counting:** quantities first appear as individual icons (eighteen of twenty people raise their hands), and only
  once understood are collected into bars or pie slices. At most one key number per beat, rounded; numbers made up in
  the small world are labelled "illustrative", real numbers with their source.
- **Flow:** arrows only show things moving (ballots, treasure, germs, people), drawn in place on the spine picture, from
  whom to whom.
- **Statements carry their identity:** an intuition, the rival's account, an assumption carries a label from the moment
  it appears, and when overturned it is struck through and replaced with a new sentence (`get_claim`, `strike_claim`).
  When two worlds compare predictions, the two predictions sit side by side, each labelled with its name.
- **Real images** (maps, photos, old paintings, data charts) are only one cell of evidence, with a caption, at most one
  per beat; the argument is carried by the icons and the spine picture. Use a map only when location itself is part of
  the answer.

## Rhythm

- Something new on screen every 3 to 9 seconds; one to three elements per frame, plus the board.
- How many hard cuts does not matter; the same world and the same spine picture are always there.
- After a step has run and its conclusion is on the board, pause (`pause_duration_seconds`) before the next step. Pause
  2 to 3 seconds after a guess.
- Narration at the language reference's speaking rate; short sentences, one thing per sentence.

## Tone

- "You" is the person in the seat: only the hardest step switches to you; otherwise follow one actor.
- Dry humour grows out of the small world (an actor's reaction, an absurd result the rules produce), never in the beat
  that carries the reasoning; no jokes about death, slavery or forced labour.
- Never "inevitably" or "unavoidably"; say "under these conditions, tends to…".

## Do and don't

**Do**

- One world per episode, the first seventy percent inside it.
- Each actor's icon and colour the same from start to finish.
- Real cases one sentence and one picture each, placed after the small world has run.

**Don't**

- Switch between a dozen times and places in one episode, each with a backstory.
- Put metaphors that need translating into sentences of reasoning.
- Draw the rival's account uglier or dumber.
- Treat numbers made up in the small world as real.
