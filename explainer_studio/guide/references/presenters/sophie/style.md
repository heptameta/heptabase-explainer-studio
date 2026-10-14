# Sophie's style: the seminar

A seminar table: a sketch of the case, a position board, a row of verdict cards, a name card for each view, and a
passage card when an original text is read. Basis: section-by-section breakdowns of four Sandel pieces and four Big
Questions Dialectic videos (how the outline bar follows the sections, how verdicts are written onto the case's picture,
how positions get their names attached), and where viewers got lost in our own videos.

**In the same series as other presenters:** the background, the type and the series' concept colours (in the series
bible and the shared code under `production/shared/`) stay the series' own, so the pictures of several presenters in one
series look like the same programme. What differs is what is drawn: Theo draws the idea itself, Fabian a small world,
Mason something running, Sophie a case that does not run and a few views.

---

## The visual vocabulary

- **The case's sketch:** the same cast and the same setting, the same sketch from start to finish; each variation moves
  only one thing, the changed place lights up briefly, and the old version stays as a faint shadow (the ghost of the
  previous state, [teaching/visual.md](../../teaching/visual.md#emphasis-toolbox)). The sketch draws real things (rails,
  a courtroom, a contract), not metaphors.
- **Verdict cards:** two cards (switch / don't switch, guilty / not guilty) in the centre of the screen; until the
  viewer has chosen, no numbers of people or answers appear on the cards.
- **One colour per view:** its column, its name card and its verdict marks on the case's picture all use this colour,
  unchanged for the whole episode; from the colour alone the viewer knows which side is speaking now.
- **Verdicts are written onto the case's picture:** when it is a view's turn, its verdict (push / don't push, a green
  tick, a red cross) is marked straight onto the sketch in its colour.
- **The position board:** built with `get_table`; each column is a view (the column name is a plain-language claim),
  each row is a case: the row header is a small sketch of that case plus two or three words, not a sentence; cells hold
  only a verdict mark (✓ held, ✗ paid a price) plus at most two words, and the cell that paid a price is boxed with
  `get_cell_highlight`. At most three columns. The first time it appears, the narration first says what it answers ("for
  each case, see which side holds"), then reads one cell for the viewer on the spot. It appears when each case is
  judged, fills in one cell, and leaves; when zooming out and at the close, the whole board appears.
- **Name card:** one when a view enters: the plain-language claim large, the person's name and dates small, with
  thumbnails of the other name cards in the corner, so the viewer sees the whole line-up every time.
- **Reason cards:** hung under that column, marked with which voice it is ("you might say", "strongest version"); the
  other side's reply is a card in the other side's colour, joined underneath with an arrow.
- **Passage card:** with `get_passage`: translation, source, author; one sentence to one paragraph.
- **Your verdict:** a row of small empty boxes along the bottom, one per case, with the narration saying "fill in this
  box in your head"; it appears only in the beat of the verdict.
- **What is on screen at the same time**
  ([teaching/visual.md](../../teaching/visual.md#text-the-picture-remembers-the-point-for-the-viewer)): only the
  main-question line is always there; halfway through a case, the screen holds the case's sketch and the one card in
  use; when a verdict is done, the position board comes out to fill a cell, and when zooming out the whole board returns
  to the centre. No more than three groups of things in one picture ([teaching/visual.md](../../teaching/visual.md)).
  Name cards appear only at entrances; reason cards and passage cards one at a time, put away once used.

## Rhythm

- One case per beat ([craft.md](craft.md#b-the-beat-of-a-verdict)): pause 3 seconds after the verdict card; pause
  (`pause_duration_seconds`) after updating the account.
- Something new on screen every 3 to 9 seconds, mostly a change on the case's picture or a cell on the board; no talking
  heads holding up the picture: every section has a picture.
- Narration at the language reference's speaking rate; short sentences, one thing per sentence.

## Tone

- Like a seminar teacher: curious, respectful of every side, mocking no view; whichever side she speaks for, she makes
  its best case.
- Direct about "how to argue"; never giving the case's verdict for the viewer.
- No internet memes; no jokes on serious subjects.

## Do and don't

**Do**

- One set of cases and one sketch per episode, the first eighty percent on it.
- Each view's colour the same from start to finish.
- During details the screen holds only the case and one card; the position board appears at seams and leaves once
  done; no table-of-contents bar.

**Don't**

- A whole section with only a text card, or no picture.
- A position board with more than three columns.
- Numbers of people or answers on the cards before the viewer judges.
- Judging for the viewer by putting a side last or making it sound nicer.
