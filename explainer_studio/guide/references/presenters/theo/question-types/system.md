# Theo's system playbook: Walk through a system

Contents: [Skeleton](#skeleton) · [How to tell it](#how-to-tell-it) · [Short version](#short-version-6-minutes-or-less) ·
[Quality bar](#quality-bar) · [Self-check](#self-check)

**The question it answers:** system, "How do the parts of this system work together?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can, given any part, say what
it is responsible for, who gets hurt if it is removed or changed, and which other cells are affected along with it; and
can say which hole it blocks.

**How it meets the must-haves:**

- **The whole picture first:** within 60 seconds at the latest, draw the finished system: a division-of-labour diagram
  (scene_kit's `get_graph_diagram`), one cell per part, each cell holding the plain question it answers ("How do we
  know this line was written by the owner?", "How does everyone make sure they keep the same ledger?"), not its name,
  dimmed at first (`dim`). The main question is one line above the diagram. Then let one concrete thing walk through it
  quickly (30 to 60 seconds, saying only where it passes, not why). After that, at every seam (before a block starts,
  after it is added) the diagram comes back and its cell lights up; while a hole or a detail is acted out, it leaves,
  and only the main-question line stays on screen (principle 16 in
  [teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)).
- **Follow one concrete thing through every part:** choose something small enough to see clearly (a payment, a
  sentence, a request, a triangle) and use only it for the whole episode. While rebuilding, it walks through each
  version of the system; once everything is built, it goes from entrance to exit in data-flow order, each cell lighting
  up as you say what it does to this thing.
- **Say who a change to one part affects:** before each block enters, let the thing walk through the version without
  it, acting out who gets hurt and how (Bob writes a payment line on Alice's behalf; Charlie owes money and never
  settles). Once everything is built, let the viewer think first: remove some block, have someone try to cheat, or let a
  component fail unexpectedly (a power cut, a disk that lies): who notices first, which block stops it, which other
  cells fail with it? At least one place with a large effect and one with a small effect (it only gets slower, not
  wrong; it only fails in rare cases; another block takes over).

**Use it for:** a system whose components behave as designed, where why each block is designed this way can be
explained by reasoning: a protocol, a processing pipeline, a program or a codebase. For example "How does Bitcoin make
everyone trust the same ledger without a bank?", "Why is each layer of a language model designed this way?", "How is a
game's picture computed frame by frame?", "How does a database keep its data after a power cut?", "From pressing a
button on a website to seeing the result, where does it pass?".

Try one question first: **can you say, for every block, "without it, who gets hurt"?**

- Yes: rebuild it with the skeleton below.
- Mostly not (a pipeline that splits up a job, conventions, interfaces left over by history): use a **tour** instead:
  the same diagram and the same thing, station by station saying what it does to this thing, and why only where the
  why can be explained by reasoning; do "remove it" at one or two stations. Do not invent holes.
- A few blocks cannot: rebuild the others by the skeleton; mention those few in one sentence each in the "knobs,
  transfer and omissions" passage, marked in another style on the diagram.

**Versus other presenters' system playbooks:** Theo, Fabian, Mason and Clio all have one; choose by the shape of the
answer ([presenters/README.md](../../README.md#the-same-question-type-several-presenters-playbooks)).

- **Fabian:** the parts are actors who make choices; change one rule and everyone changes what they do, even exploiting
  loopholes. The same Bitcoin, when the viewer wants to know why miners are willing to be honest and how the incentives
  are designed, goes to Fabian.
- **Mason:** all the components run together, and the effects only show when run. The same language model, when the
  viewer wants to see what that sentence actually becomes at each layer, goes to Mason.
- **Clio:** each part was a crossroads in its day, and the options not chosen are left as dashed versions.
- **Theo:** start from a version everyone understands that almost works; every block is a hole in the previous version,
  and "remove it and who gets hurt" is the reason each block enters.

**Not this one:**

- Only caring why one thing happens, with a causal chain as the answer (why a differential lets two wheels turn at
  different speeds): Explain a mechanism ([mechanism.md](mechanism.md)). Wanting what each block is responsible for
  (what the axle, the crossbar and the gears each do) is system. When one station is big enough for a whole episode,
  that episode follows mechanism, returning to the diagram once at the opening and once at the close.
- The viewer wants to build it or operate it once themselves: procedure ([procedure.md](procedure.md), or Mason).
- Each part's "why" is a few options at a table in some year: Clio
  ([presenters/clio/question-types/system.md](../../clio/question-types/system.md)).

**What this episode hands the viewer:** a division-of-labour diagram, one sentence per cell (what it is responsible for,
who gets hurt first without it). The takeaway card's ([teaching/rules.md](../../../teaching/rules.md#the-takeaway-card))
name is the system's name, and its one sentence is "which blocks stop which kinds of failure". The standard of the
explanation is one sentence, for yourself: **point at any cell and ask "remove it, and who gets hurt first?": can the
viewer answer?** The narration says one other sentence, once, at the opening: "This is how you might invent it, not how
it was actually invented" (the rebuild follows the order in which holes appear, not necessarily data-flow or historical
order).

**Foil:** an architecture diagram of nothing but nouns, or a vague metaphor ("like mining gold", "like a brain"). A
system episode's foil takes at most 20 seconds: one sentence plus a thumbnail whose words cannot be read, with the nouns
not read aloud (name after understanding, principle 8 in
[teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)). Its problem: every cell seems to fall
out of the sky; ask what changing one cell would do, and you cannot answer. When the viewer holds a reasonable but wrong
idea ("isn't this just a website everyone can see?"), let it be the simplest version and let the first hole make it fail
([teaching/rules.md](../../../teaching/rules.md#handling-a-misconception)).

**The picture:**

- The diagram is the episode's only big-picture marker (principle 16): the main question in one line above; built cells
  lit (`undim`) and given their names (`relabel`); the one being built boxed; those not yet built dimmed, keeping their
  questions; those covered in other episodes in thin dashed boxes; the cell this episode does not build is marked "not
  in this episode" from the start. In passages that build no block (the walk-through, breaking it), the whole diagram is
  boxed, with a title line saying what this passage does. During details it leaves.
- While building, what is enlarged in the middle of the screen is the cells of the diagram already built, in the same
  layout; do not draw a separate system picture. When one block takes more than 3 minutes, split sub-cells inside that
  cell and fold them back when done.
- A rule card (`get_checklist`, `add_checklist_row`, `get_checklist_strike_line`) is only for systems where the rules
  themselves are the answer (the ledger's rules); it is content, not a big-picture marker.
- Removing a block: `knock_out`. That cell and the cells depending on it dim together and are crossed out, and the
  thing takes a red failure path instead.
- Components and the things that flow through them get two colours, announced once and kept (rules and payments;
  weights and data).
- What the real system has beyond the rebuilt version is added to the diagram in another style in the "knobs, transfer
  and omissions" passage.

---

## Skeleton

The plan's outline steps follow this table: from outside, the simplest version, one step per block, the walk-through,
breaking it, knobs, close ([teaching/plan.md](../../../teaching/plan.md)).

| Share | Section | Content |
|---|---|---|
| 0–5% | From outside | The first 5 seconds are a concrete input and output ("Alice pays Bob 20 with no bank involved", "a sentence goes in, the next word comes out"); the main question: what happens in between that makes this possible? |
| 5–14% | The whole picture, faint | The foil in one sentence (within 20 seconds); the diagram drawn faintly, each cell holding a plain question, one cell marked "not in this episode"; the same thing walks through quickly in 30 to 60 seconds without saying why; the narration says once "this is how you might invent it"; the diagram leaves |
| 14–22% | The simplest version that almost works | A starting point everyone understands (a public ledger anyone can write in); the thing walks through once: what it achieves; state the one test every version must pass ("Can Bob trust this line?") |
| 22–66% | Growing it block by block (3 to 6 blocks) | One passage per block, one beat per arrow, each with a pause: the thing walks into the previous version → act out the hole: who gets hurt, and how → only for the most important block, a guess: what would have to be added to stop this? Give 2 to 4 options (a naive patch, an overkill one, the real one; [teaching/rules.md](../../../teaching/rules.md#guess-beats)), pause 2 to 3 seconds; for other blocks, pause after the hole is said → add the block, the same thing walks through again, the hole is closed → only now give the name, and that cell lights up → one sentence: what it is responsible for, who gets hurt first without it. One causal recap after the hardest block ("Because Bob could forge, there are signatures; because a signed line can be copied, there are serial numbers; what's still missing is…") |
| 66–76% | Follow one thing through the whole system | A recap before the walk; the diagram enlarged back to the centre, fully lit; the same thing goes from entrance to exit in data-flow order (not build order), each cell lighting up as you say what it does to this thing and which hole it blocks |
| 76–86% | Try to break it | A guess: remove a block, someone tries to cheat, or a component fails unexpectedly: who notices first, which block stops it, which other cells fail with it? Pause, reveal (`knock_out`, the dependent cells dimming with it); at least two places, one with a large effect and one with a small effect, saying why |
| 86–94% | Knobs, transfer and omissions | Ask one "what if we changed it" (pause after saying it, no guess): a number the real system tunes is changed: who gains, who loses (one block every ten minutes becomes one a minute); transfer: the same "remove it and who gets hurt first" used quickly on another system once (one picture, one sentence); what this rebuild left out, and which block is really a leftover of history |
| 94–100% | Close | Hand over the diagram: one sentence per cell; ask about the cell marked "not in this episode": from its question, what do you think it is responsible for, and who gets hurt first without it? Pause, give only the direction; the next episode covers it, continuing from this diagram |

Measured pace (used only to set proportions; speaking rate follows [style.md](../style.md) and the language reference):
3Blue1Brown's video on how Bitcoin works has its first component at 14%; seven blocks fill 14–78%, each from 43 seconds
to 4 minutes 17 seconds, median about 1 minute 40 seconds; the attack passage is 2 minutes; the knobs, about 2 minutes,
come after all the components are in place. Chapter 5 of the same channel's transformer series: a four-cell diagram plus
a three-and-a-half-minute quick walk-through (18 to 35 seconds per station). Branch Education's video on game graphics:
a three-station pipeline diagram at 1:12, returning twice afterwards. A 1937 instructional short on the car
differential: five blocks in 2 minutes 25 seconds, 15 to 35 seconds each. None of the four makes the viewer really stop
and guess. We guess once at the most important block and once when breaking it, at most twice per episode
([teaching/rules.md](../../../teaching/rules.md#guess-beats)).

How the craft items map onto a system episode: the roadmap is the diagram; the sceptic or victim is the person each
block saves from getting hurt; the acts are three passages, "the simplest version", "growing it" and "walk-through to
breaking it", with recaps after the hardest block and before the walk-through; the key-point labels are the one or two
most important cells of the diagram.

## How to tell it

- **When the system spans several episodes:** every episode opens on the same diagram, lighting this episode's cells
  (other episodes' in thin dashed boxes), and closes by handing back a diagram with a few more cells lit. How many
  episodes and which cells first is the plan's decision, by prerequisites
  ([teaching/plan.md](../../../teaching/plan.md#planning-how-many-episodes-each-answering-what)).
- **Tell a hole by its visible consequence:** in a codebase, remove this cache layer and every request waits three
  seconds longer; remove this check and the saved file gets corrupted. Not abstract reasons like "easier to maintain".
- **Use technology the viewer knows as a springboard, and say where the analogy does not hold.** For example, explaining
  venv to an engineer who writes React and Node, you can start from `node_modules`, but say what differs (a venv must be
  activated first, or its `python` run directly, before the packages can be found). Given only the analogy, without
  where it fails, engineers remember the wrong version.
- **When a metaphor does not land, chase one real file instead.** An abstract statement like "it is copied into the
  plugin" often loses the viewer; "this one `server.py` appears in three places", pointing at each one, makes it clear.
- **Questions the viewer has asked are the best list of misconceptions.** Make their exact words into a "you asked" card:
  first grant that it is reasonable, then let it fail on a real example, and finally give the new idea.
- **Common prerequisites in a codebase** (a reference when planning, not a fixed order): one of the user's actions is
  understood first; how the thing gets installed on the user's computer comes before rules and settings; state and
  memory come before "how the output is produced"; how to change it safely needs everything before it.

**Reading the sources:** for a codebase, see [sources/codebase.md](../../../sources/codebase.md) (how to read it, the
coverage list, real content on screen, verification).

---

## Short version (6 minutes or less)

A system episode of 6 minutes or less:

| Share | Section | Content |
|---|---|---|
| 0–8% | From outside, and the whole picture | One input and output; the diagram drawn faintly, cells holding questions |
| 8–18% | The simplest version | One sentence, one picture, and the test |
| 18–70% | Two or three blocks | Only the most important; each block: the hole → pause → patch → the cell lights up and gets its name |
| 70–90% | Walk-through, remove a block | The same thing goes through the whole system; one guess, "remove it and who gets hurt first", the dependent cells dimming with it |
| 90–100% | Close | One sentence per cell of the diagram; one sentence on what the unbuilt cells are responsible for |

**Leave out:** the quick walk-through, the rule card, the knobs. **Keep:** the diagram returning at every seam, the same
thing, the hole before each block enters, at least one guess, one removal. Word count from the language reference's
speaking rate.

**A short passage inside another episode** (60 seconds or less, for example "first, where it sits in the whole system"
at the start of a mechanism episode): the diagram appears faintly, the cell in question lights up, one sentence says
what it is responsible for and who gets hurt first without it, then it folds away; that episode's big-picture marker
follows that episode's playbook.

## Quality bar

After watching, given any cell of the diagram (including the question in the cell this episode does not cover), the
viewer can:

- say what it does to the thing;
- say who gets hurt first without it, and how (which hole it blocks);
- say which other cells are affected if it is removed or changed, and which are not.

Given a change not in the video ("double the number of entries each block can hold"), they can guess who gains and who
loses.

What this playbook does, concretely: the diagram comes within 60 seconds at the latest and never leaves; every block has
a named victim, and the viewer guesses once before it is patched; at the end, at least two removals, one large and one
small, acting out the chain of failures. Remembering only the order of the flow or a list of nouns, without being able
to say who gets hurt when a cell is removed, does not count.

## Self-check

- [ ] You first tried "can you say, for every block, who gets hurt without it?", and chose rebuild or tour by the answer.
- [ ] Within 60 seconds at the latest there is the finished diagram, with the main question in one line above, each cell
      holding a plain question, not a noun; it returns at every seam and leaves during details, with cell states as in
      "the picture"; there is no separate outline bar.
- [ ] The foil is within 20 seconds and reads no nouns aloud.
- [ ] The opening said once: this is "how you might invent it".
- [ ] The whole episode uses the same concrete thing, without a new example at every station; the transfer was done once
      in the "knobs, transfer and omissions" passage.
- [ ] Before each block enters, the version without it was acted out first: who gets hurt, and how; no block is "also,
      there's…".
- [ ] There was a pause before each block was patched; the name comes only after the patch.
- [ ] Every version was checked with the same test.
- [ ] Once everything was built, the same thing walked through the whole system in data-flow order, each cell saying
      what it does.
- [ ] At least two "remove it / someone cheats / something fails", with a pause before each reveal; one large effect
      and one small, with why; the dependent cells dimmed with it.
- [ ] The knobs passage asked one "what if we changed it".
- [ ] Components not forced by a hole were said plainly to be so; no hole was invented.
- [ ] The closing diagram has one sentence per cell, and the cell "not in this episode" was put to the viewer.
