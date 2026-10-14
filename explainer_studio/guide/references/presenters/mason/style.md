# Mason's style: the workbench

One workbench: a toy that is really running, and what it produces; the answer card and the scoreboard appear only in
the beats that use them. At most three groups on screen at once
([teaching/visual.md](../../teaching/visual.md#attention-one-place-to-look-at-a-time)): the toy and this run's result,
plus one more. Basis: section-by-section breakdowns of three Karpathy videos and four Bret Victor works (how rules and
behaviour sit side by side, how time is laid out as space, how the scoreboard stays), and where viewers got lost in our
own videos.

**In the same series as other presenters:** the background, the type and the series' concept colours (in the series
bible and the shared code under `production/shared/`) stay the series' own, so the pictures of several presenters in one
series look like the same programme. What differs is what is drawn: Theo draws the idea itself (a number line, vectors,
a table), Fabian draws the people and things of a small world, Mason draws something running and its output.

---

## The visual vocabulary

- **Label the toy the moment it appears:** the narration says "this is a toy we built ourselves, not the real thing",
  and the toy's area carries a small "toy" label, clearly distinct from the real thing (labelled "real", with its
  source).
- **Rules and results side by side:** on one side the toy (a drawing of a machine, a computation graph, a few lines of
  code, a few steps), on the other what it produces (each step's value, a trajectory, a piece of output); point at one
  place in the rules and the part of the result it produced lights up, and the other way round. At most two or three
  linked representations in one picture, and the narration says every time where to look.
- **Running:** the input travels through the toy as a small marker (`get_flow_token`), each block lighting up as it
  passes, and the result appears at the end. Every run uses the same movement, so the viewer sees at once "now it is
  running".
- **Answer card:** a small card set out before the run (`get_answer_card`) saying what it should be (worked in your
  head, the previous version, the real thing; for an argument, two rows: the claim and the rival); after the run it gets
  a tick or a cross (`get_answer_mark`). The guess's question and options are written on the card too.
- **Scoreboard** (`get_scoreboard`, `add_scoreboard_row`): it appears after each version runs, one line longer (the
  version, a score or one key number, a short piece of output), and leaves on the next beat; at recaps and the close the
  whole board comes out. It is not on screen during details.
- **How big the whole thing is:** a thin bar showing how big the whole toy is (for example a hundred lines, six
  components), lighting up as far as you have got.
- **Time laid out as space:** each step of one run stays as a point, joined into a trajectory (`get_line_chart`, or a
  path you draw); many runs stacked together (`get_run_family`: thin, translucent lines, with `highlight_run` lighting
  one), or set out as a row of small pictures.
- **Shadow:** the result before a knob turned or a block changed stays as a faint copy (`get_shadow`), with the new one
  drawn on top.
- **Knob:** a number with a name and a unit ("steering angle 6.5°") appears first and is explained first, and only then
  is turned; while turning, the number ticks along (`get_knob`, `animate_knob_to`).
- **Small ladder:** a three-rung icon in the corner, the lit rung showing whether we are looking at one run, one whole
  trajectory, or everything.
- **Code:** with `get_code_panel`, at most one to three lines at once, the changed line boxed with `highlight_lines`;
  other lines folded away or dimmed. What can be drawn as a machine, a table or a picture is not shown as code.
- **The real thing:** appears only at the opening and the close: the real tool's output, the real system's numbers,
  with sources; when set beside the toy's result, the same input in the same position.

## Rhythm

- One beat ([craft.md](craft.md#b-the-beat-of-a-run)) takes one to two and a half minutes; pause 2 to 3 seconds after a
  guess, and pause (`pause_duration_seconds`) after the run and the answer check.
- Something new on screen every 3 to 9 seconds, mostly a result just produced; few hard cuts, the same workbench always
  there.
- Sweep a knob slowly, stopping at two or three key values.
- Narration at the language reference's speaking rate; short sentences, one thing per sentence.

## Tone

- Like trying things beside you at the workbench: "Let's try the dumbest way first." "Let's run it." "Huh, that's
  wrong." No panic at a mismatch: "Okay, let's find out why."
- Dry humour grows out of strange results the toy produces (the car spinning on the spot, the model writing a string of
  gibberish), never in the beat that says why.
- No contempt for existing tools or formulas; say why they look the way they do (designed for paper and pencil, for the
  machines of their time), then what we can see now that we could not before.

## Do and don't

**Do**

- One toy per episode, the first seventy percent on it.
- Every number really produced by the toy.
- Every layout first says what to look for; every pattern steps down to one run and its cause.

**Don't**

- Paste a full page of code as the picture.
- Five representations moving at once.
- A knob with no label.
- Produce a beautiful result without saying why it came out that way.
