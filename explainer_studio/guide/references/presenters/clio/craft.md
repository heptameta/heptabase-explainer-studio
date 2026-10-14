# Clio's script craft

Contents: [A. One big-picture map](#a-one-big-picture-map) ·
[B. The beat of a crossroads](#b-the-beat-of-a-crossroads) · [C. Zooming in and out](#c-zooming-in-and-out) ·
[D. Honesty](#d-honesty) · [E. Names and years](#e-names-and-years) ·
[Self-check](#self-check-every-playbook-must-pass)

Basis: section-by-section breakdowns of four Imperial War Museums "Why did it happen" videos (Pearl Harbor, the German
invasion of the Soviet Union, the Falklands, the partition of India) and four Johnny Harris videos (the
Mexican–American War, the Panama Canal, the Pacific War, America's first constitution), the crossroads of Historia
Civilis, and where viewers got lost in our own videos. Each of her playbooks (`question-types/`) is built on these
techniques; the shared rules ([teaching/rules.md](../../teaching/rules.md)) apply as always.

---

## A. One big-picture map

An episode has only one big-picture map, used from the first minute to the last. It is the big-picture marker principle
16 asks for ([teaching/rules.md](../../teaching/rules.md#principles-every-presenter-follows)): zoom out back to it at
seams and crossroads, and let it step aside when zooming in on details.

1. **Draw the ending on first:** when the big-picture map first appears, the destination is already drawn faintly on it
   (the final borders, the people finally at the table); the viewer always knows where the road leads.
2. **With geography, use a map; without, use a seat chart:** wars, expansion and trade use a real map; courts,
   conferences, factions within one country, and the companies of one industry use a seat chart of "who is at the
   table": each side is a portrait or badge on the chart, with its claim written beside it. A seat chart progresses by
   someone else taking a seat, alliance lines drawn or erased, a seat left empty; an industry can also be drawn as a
   supply chain (who designs, who makes, who buys), or as factories on a real map. When neither a map nor a seat chart
   can be drawn (only an idea remains), it is not Clio's topic.
3. **Only add, never replace:** each turning point changes one stroke on the same map (colour a region, move a border,
   swap a face); the colouring is the progress bar.
4. **The main line is an icon on the big-picture map** (it leaves with the map when zooming in): the resource in short
   supply, the land in dispute, the position sought; any detail visibly belongs to one line.
5. **Time bar:** one bar along the top, marking only the years of turning points.
6. **Draw the boundary:** open zoomed all the way out, then say which stretch this episode covers; the part of the map
   not covered is greyed out and labelled "another episode".

## B. The beat of a crossroads

One crossroads is one beat (principle 15 in
[teaching/rules.md](../../teaching/rules.md#principles-every-presenter-follows)); how many depends on the playbook (three
to four in a narrative episode):

1. **Goal cards:** what the person wants, what they fear, what they have in hand. One for each main side, including the
   side being pushed.
2. **Lay out the roads:** two or three arrows on the same map, one sentence of reason each.
3. **Guess first:** "You are ___, it is ___, and this is all you know." Pause 3 seconds. The viewer already knows the
   ending, so do not ask them to guess what the ending gives away; what they guess is which road someone takes at a
   step the ending does not give away, which reason mattered most to them at the time, or what the other side expected
   them to do.
4. **Why they took this road:** said using only what could be seen at the time; what was learned afterwards may not be
   used to judge them.
5. **The road not taken stays as a dashed line.** The line is drawn, not said: the narration names the road in the words
   it was laid out with in step 2, and says what would have followed: "if at the time…, …". The first dashed line of an
   episode also says once what these lines are: roads that were nearly taken, which the close comes back to. Best when
   someone really did take the other road later, or it was nearly taken (one vote, one day). When the close lights them
   up again, each gets its "if at the time…" again, one beat each, and then what they add up to: it could have gone
   otherwise, so the ending was made at these crossroads (principle 15: a link only words can carry gets its steps).
6. **So:** what has just been established, and why we look at the next part (the two sentences of principle 16); pause
   (`pause_duration_seconds`).

## C. Zooming in and out

- **Zoom in on details within the same map:** the point on the big map lights up first, then zoom in to the harbour, a
  negotiating table, a document; when zooming back out, that point has been coloured. When zooming in to a separately
  drawn picture (a table, a document), the big-picture map leaves, and you zoom back out to it when done; do not keep a
  small map in the corner.
- **The "so"s build into a chain:** each crossroads leaves a point on the time bar at the top, with one sentence of its
  conclusion beside it; wherever we are, the viewer can see what has already been established.
- **One piece of evidence carries one turning point:** a document, someone's own words, an object, with its source, and
  one sentence saying what it proves.
- **Zoom out every minute or two:** "So far…", with the big-picture map fast-forwarding from the start to now.
- **When a mechanism appears within a section:** a stretch whose answer remains with names, years and chance removed
  (supply lines stretched too far, an alliance where nobody pays) gets its short version: one sentence and one picture,
  or a one-minute small world, then back to the named crossroads.

## D. Honesty

- **Keep facts and commentary apart:** commentary goes on an "opinion card" in another colour, saying whose opinion it is
  (the book's author, a particular historian, us). The narration first says "this is ___'s view".
- **Do not judge the past by the present:** explain people's choices with the information and situation they had then.
- **Say where chance came in:** the weather, a letter arriving late, someone falling ill at just that moment; do not tell
  chance as necessity, nor structure as chance.
- **Discount legends:** a famous story without grounds is called a legend.
- **Images:** public-domain or licensed portraits, maps and documents; when you cannot get one, use a silhouette with a
  name tag, each person with a different silhouette outline and border colour. When an object has no photo, draw it as
  an icon, with the source. No AI-made fake old photos, no staged fake witnesses.
- **Someone's own words must be heard as their own words:** the narration first says "he wrote", "he said in his
  diary", while a quotation card appears (original or translation, with source); then back to the narration's own
  words.
- **Historical borders:** when reliable GeoJSON exists, use it and cite it; when not, piece the approximate extent
  together from modern countries and say that it is approximate (see the maps section of `rendering/`).

## E. Names and years

- At most four or five named people per episode, all of them people who make a decision at a crossroads and will appear
  again; the moment a name appears it is attached to a portrait on the map, with their goal card beside it.
- Everyone else is called only by their seat or faction (the navy, the junta, parliament).
- Years are marked only at turning points; other times are "three years later", "that same winter".

---

## Self-check (every playbook must pass)

- [ ] The first minute has the ending (or the finished system) and a one-sentence main question, with the destination
      drawn faintly on the big-picture map; a narrative also says "to answer it, we have to go back to ___".
- [ ] The big-picture map is used from start to finish, only added to, never replaced; details are zoomed in on it, and
      no section leaves it entirely.
- [ ] Every crossroads has each side's goal cards, two or three arrows, a pause to guess first, a reason using only what
      was known at the time, a dashed line and an "if at the time" (in an argument, turning points on the road both sides
      agree on are not crossroads).
- [ ] The side being pushed also had its roads and reasons laid out.
- [ ] All commentary is on opinion cards, marked with whose opinion it is.
- [ ] No more than five named people; everyone else is called by seat or faction.
- [ ] The close says the whole chain once along the main line and answers the opening's main question (for argument: say
      what each side rests on and how far the consensus goes, and ask the viewer to judge).
