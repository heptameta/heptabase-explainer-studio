# Question types

Contents: [The two conditions](#the-two-conditions-a-question-type-meets) · [The nine](#the-nine) ·
[Concept, the other goal: use](#concept-the-other-goal-use) ·
[The neighbours most easily confused](#the-neighbours-most-easily-confused) ·
[A source with several question types](#a-source-with-several-question-types)

Every episode gives the viewer the answer to one question, and that question is one of the types below. A question type
defines only two things: **what the viewer can do afterwards**, and **the must-haves**. How to teach it is the
presenter's business. Each presenter writes, in their own way of making people understand, one playbook for every
question type they handle (`presenters/<presenter>/question-types/<type>.md`). Different presenters' playbooks for the
same question type can have completely different skeletons, but all of them meet the must-haves here.

## The two conditions a question type meets

1. It can be said in one sentence, without naming a subject or a kind of source.
2. What it lets the viewer do afterwards differs from all the other eight.

So "explain a paper" is not a question type: a paper is a kind of source. One paper may be answering "why should we
believe this claim?", or "how does this new method work?".

## The nine

<!-- generated:question-types begin: edit the source, then run scripts/release.py -->
| Question type | `question_type` | The question | Afterwards the viewer can | Must-haves |
|---|---|---|---|---|
| Mechanism | `mechanism` | Why does this happen? How does it work? | Explain the causal chain in their own words and predict what changes when one condition changes. | Every link of the causal chain is visible, with no skipped link; at least once the viewer predicts what happens when one condition changes. |
| Proof | `proof` | Why must this be true? | State the key idea of the proof and follow each step, confirming that it holds. | The claim is first made clear with examples; the key idea is stated on its own; every step says why it is allowed; the episode says what the result buys us. |
| Concept | `concept` | What is it, and how does it differ from things that look like it? | Tell examples from non-examples and produce an example of their own. | At least two examples and one close non-example; the definition comes out of their difference; one boundary case the viewer judges for themselves. |
| System | `system` | How do the parts of this system work together? | Given any part, say what it is responsible for and what a change to it would affect. | The whole picture comes first; one concrete thing is followed through every part; the episode says what changing one part would affect. |
| Procedure | `procedure` | How is it done? | Do it once on their own in a new situation. | One complete run; the judgment at each step is said out loud; a second run in a different situation; the common mistakes. |
| Narrative | `narrative` | What happened, and why did it happen that way? | Tell the main line, the turning points and their causes, and where things could have gone otherwise. | One main-line question; every turning point has its cause; the places where it could have gone otherwise are pointed out. |
| Conceptual change | `conceptual-change` | How did people come to think this way, and where did the old idea fall short? | Say why the old idea was reasonable, where it broke down, and what the new idea gains and costs. | The old idea is presented as reasonable; where it breaks down is concrete; the cost of the new idea is stated too. |
| Argument | `argument` | Why should we believe this claim? | State the claim, the strongest evidence and the strongest objection, and judge its credibility themselves. | The claim says clearly what it does and does not assert; each piece of evidence says what it supports; the strongest objection is presented; what is still unknown is said. |
| Perspectives | `perspectives` | On an open question, what are the views, and what does each rest on? | State the strongest version of each position and its cost, and know where they stand and why. | Each position in its strongest version; the same case tests all of them; no verdict for the viewer (a presenter who holds a position says so). |
<!-- generated:question-types end -->

The must-haves are also a checklist. The script audience review and your self-check both use this column to see
whether the episode met them. Whoever presents the episode, they must be there. When a concept episode's goal is use,
use the table in the next section instead.

## Concept, the other goal: use

When the sources hand the reader a thinking tool to take out again and again (a framework or a model: disruptive
innovation, expected value, queueing), a concept episode can have another goal. Both goals ask "what is it?"; they
differ in what the viewer later does with it. So it is still a concept episode, with only the outcome and the
must-haves replaced. Which goal it is depends on what the viewer wants to be able to do (the plan's `goal`); the
sources are only a hint. Tell them apart by the sentence the viewer will ask later, in a new situation:

- "Does this count as X?" → telling apart (the table above).
- "Looking at this through X, what will happen, and is it worth it?" → use (the table below).

<!-- generated:concept-goals begin: edit the source, then run scripts/release.py -->
| Goal | `concept_goal` | Afterwards the viewer can | Must-haves |
|---|---|---|---|
| Concept (use) | `use` | Apply the tool to a situation they have not seen and say, using its name, what will happen. | One case dug into deeply builds the tool: a picture whose shape never changes afterwards, labelled with the tool's parts and the conditions it needs, and the name given once the case is done, then used every time it is applied; at least two quick applications that change only labels and numbers, not the picture's shape, with a guess before the first, one of them from a field the viewer would not expect; a fence: a situation where the tool looks usable but gives the wrong answer, naming the condition that fails; your turn: a case not seen before, the viewer applies the tool, pause, reveal. |
<!-- generated:concept-goals end -->

- **Two kinds of things on the picture:** the parts are what you match one by one when applying the tool (disruptive
  innovation: big companies listen to their high-end customers; a new technology is first good enough at the low end).
  The conditions are what, when they fail, make the tool give a wrong answer (expected value: you can repeat it many
  times; you can afford to lose). The simplifications made so a toy or a small world is easy to draw (only one counter)
  are neither, and are not written on the picture.
- **What is swapped:** the non-example becomes a fence. A non-example is "something that is not X"; a fence is "a
  situation where using the tool gives a wrong answer". The more useful a tool, the more easily it is abused, so this
  part can never be skipped. When the fence shows the tool is missing a condition, add the condition on the spot. Where
  most of the time goes: for telling apart, to non-examples and boundaries; for use, to applications.
- **How fast, how many:** each application takes one to two minutes. The opening real case, the applications, the
  fence and "your turn" add up to at most five situations (toys and small worlds do not count).
- **After "your turn":** the video cannot see the viewer's own situation, so the reveal uses a concrete case not shown
  before. After the reveal, one more sentence asks them to think of their own (with no reveal).
- **Quality bar:** given a situation not in the video, the viewer can say, with the tool's name and its picture, what
  will happen, and can say where the tool does not apply. Remembering only the examples does not count.
- **Boundaries with the neighbours:** taking away a causal chain, asking why one thing happened, is mechanism. Taking
  away a set of steps to get something done is procedure. Taking away a named tool with a picture, matching its parts
  to a new situation and saying what happens next, is use. One source often has both: first a mechanism episode on
  why one company lost, then a use episode that turns it into a tool. Then the use episode's deep case shrinks to a
  recall of under a minute.
- **A principle about values:** using it to judge whether a new case counts (does this count as harm?) is telling
  apart. Using it to judge whether something is morally right (should the government ban smoking?) is split by
  argument versus perspectives, below. So Sophie has no playbook for use. A tool that works out whether a choice is
  worth it (expected value) is use.
- **Where it is written:** in the plan, that episode gets `concept_goal: use` (telling apart writes nothing). Its
  `question` reads "Using X to look at …, what will happen?", and "judge" is kept for "does it count?" (example: "Using
  disruptive innovation to look at a company the video never shows: will a new rival beat it?"). The script audience
  review and your self-check follow this row. The concept playbooks of Theo, Fabian and Mason each have a section for
  the use goal.

## The neighbours most easily confused

Decide by what the viewer takes away, not by the words of the question: write the takeaway first, then find the type
whose "afterwards the viewer can" it is.

- **Mechanism vs conceptual change:** if the viewer leaves with a causal chain in nature or in a machine (why bread
  rises), it is mechanism. If they leave with an idea people held, where it broke down, and what replaced it at what
  cost (how people came to accept that continents move), it is conceptual change, even when causal chains are explained
  on the way. Ask whose story the takeaway sentence tells: a thing's, or an idea's.
- **Mechanism vs system:** if the answer is a causal chain, it is mechanism; if it is a picture of parts working
  together, it is system. When the viewer should take away what each part is responsible for and who breaks when one is
  removed, it is system, even if the explanation passes through causal chains.
- **Mechanism vs proof:** if the question is "why does it happen", it is mechanism; if it is "why must it hold", it is
  proof.
- **Concept vs procedure:** if the goal is to recognize it (or to look at a new situation with a tool; see use, above),
  it is concept; if it is to be able to do it, it is procedure. An algorithm is usually mechanism: what the viewer
  mostly wants is "why does it work", not to compute it by hand.
- **Mechanism vs narrative:** remove the names, the years and the chance events; if the answer is still there, it is
  mechanism (for example "why do those in power keep a country from getting rich"). If it only makes sense with
  particular people, timing and chance, it is narrative (for example "how did this revolution happen"). A "why" in
  history often has both. If the viewer wants a causal chain that holds elsewhere too, it is mechanism. If they want to
  know how it really happened that one time, and where it could have gone otherwise, it is narrative.
- **Narrative vs conceptual change:** if the protagonist is an event, it is narrative; if it is an idea, it is
  conceptual change.
- **A concept under a story:** when following a narrative or a conceptual change needs a distinction the viewer does
  not have yet (a virus and a bacterium, in the story of how a cure was found), that distinction is a concept
  question. When the story's main line rests on it, it gets the concept must-haves before the story uses
  it (two examples, one close non-example, a boundary the viewer judges), in an episode of its own or a segment of this
  one, from a presenter whose playbook teaches concepts. A label and one example are not enough.
- **Conceptual change vs perspectives:** if the question is settled and the episode tells how the answer came about, it
  is conceptual change; if it is still unsettled today, it is perspectives.
- **Argument vs perspectives:** one claim put to the test is argument; several views side by side, with no verdict for
  the viewer, is perspectives. When unsure, ask: if all the facts were known, would the disagreement remain? If not
  (the disagreement is about evidence, and data could in principle settle it, for example "would open borders lower
  wages?"), it is argument: test the main claim against its strongest rival. If it would remain (the disagreement is
  about what matters most, how a text should be read, or where a concept's line is drawn, for example "should rich
  countries open their borders?"), it is perspectives.
- Scientific papers and literary studies are mostly both answering "why should we believe this claim?"; they differ in
  what the evidence looks like (data, or passages of text). That is the subject's business: see `subjects/`.

## A source with several question types

- When drawing the question map during deep reading, give each question one type ([teaching/plan.md](plan.md)).
- Each episode has one main question, and it decides what the episode must achieve. The other questions become short
  passages inside the episode, told as short versions that meet their own type's must-haves: for example one example,
  one picture, one sentence.
- The same source with a different viewer may have a different main question. Someone who wants to understand the
  biology asks a mechanism question; someone who wants to judge whether the author's hypothesis stands asks an argument
  question. Look at what the viewer wants to be able to do.
- A question that seems to fit none of the nine: use the closest type and record it with
  `explainer-studio gap add --kind other`.
