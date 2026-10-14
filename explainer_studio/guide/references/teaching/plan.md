# Planning the series

Contents: [What the plan must make clear](#what-the-plan-must-make-clear) ·
[What each episode records](#what-each-episode-records) · [The overall proposal](#the-overall-proposal) ·
[Planning: how many episodes, each answering what](#planning-how-many-episodes-each-answering-what) ·
[Inside each episode](#inside-each-episode) · [The coverage map](#the-coverage-map) ·
[Across episodes](#across-episodes) · [When the script departs from the plan](#when-the-script-departs-from-the-plan)

The plan says how many episodes there are, what question each answers, in what order, and who presents each. It is the
one thing the user confirms before production. Write it in full: `plan.yaml` holds what programs and the user read
([file-formats.md](../file-formats.md)), and the research notes hold the planning behind it.

How many episodes, and what each answers, depend on **the viewer and the sources**. Plan them with the method below.
Presenters do not decide it, and there is no separate scheme for each kind of source. The presenter decides how each
episode is taught. So the same sources and the same viewer give the same episodes whoever presents them, and a series
with two presenters still plans cleanly.

## What the plan must make clear

The user reads the plan to decide whether to start. At a glance they should be able to judge whether you overestimated
or underestimated them, and whether this set of videos is what they want. So the plan's text is written for them:
short, in their words, and shown exactly as written. Use plain words. Write no file names, field names or tool names,
unless the sources themselves are about them.

From the plan they must be able to see:

- your understanding of them: what they know now and what they want (the first paragraph of `audience.description`,
  and `goal`; see [teaching/audience.md](audience.md));
- each episode: its title and length, the question it answers, who presents it and whether it uses a draft playbook,
  where in the sources it comes from, and how it is told;
- the overall proposal: how many episodes and their total length, and a shorter option with what it would lose
  (`rationale`);
- what is left out, and why, in plain words (`excluded_topics`).

The rest of the audience description, the capacity, the vocabulary, your assumptions and the endpoints are your basis
for planning. They are not what the user needs to read first.

## What each episode records

**Fields the user reads.** They decide whether to start from these alone, so keep each short and in their words.

1. **`title`** and **`estimated_duration_seconds`**.
2. **`question`:** the question this episode answers, taken from the question map and worded so the viewer understands
   it. The script audience reviewer is told this is the question the episode answers.
3. **`presenter_name`:** who presents it. The user sees the presenter's name and the kind of teacher they are (for
   example "Theo, the teacher at the blackboard"). When the presenter has no playbook for the episode's question type,
   the episode uses a draft playbook, and this is marked. Which playbook is used is not for the user: it is for you.
4. **`source_scope`:** one line, with the sources' own chapter names, page numbers or file names, so they can find
   it. Use the page numbers of the file in their hands (the page their PDF reader jumps to). When the printed page
   numbers differ, the chapter name lets them match. Example: "Chapter 13, pp. 351–356: the Fed's structure, how the
   FOMC meets".
5. **`outline`:** how it is told, one line per step, like a table of contents: about a dozen words a line, enough to
   see how the story goes. The details of each step do not go here: they are the coverage items the coverage map
   assigns to that step. **Do not follow the sources' chapter order:** the episode's playbook decides the order.

**Fields for you.** Planning, writing the script and checking it afterwards rely on them, so fill them in too.

6. **`question_type`:** which of the nine types the main question is ([teaching/question-types.md](question-types.md)).
   When a concept episode should teach the viewer to apply a tool to new situations, also write `concept_goal: use`
   and word the `question` as "Using X to look at …, what will happen?".
7. **`takeaway`:** one sentence: what the viewer leaves with. It matches the question type's outcome ("afterwards the
   viewer can"). Later episodes' script reviews read it as something the viewer already knows.
8. **`taught_terms`:** every term the episode teaches, which includes all the unfamiliar ones it uses. How each is
   explained at its first use goes in the episode's `design.md`.

**Planning notes for you.** Keep these in the research notes, next to the question map. When you make the episode, its
teaching details move into its `design.md`.

- **The hook:** what grabs them in the first 30 seconds, ideally something from their own world.
- **For each outline step: its reason, its source, and the links it holds.** The reason: which part of the main question
  this step answers (the script says it at the start of the step, and that is the transition). The source: which page
  or passage of the sources it comes from. The links: the reasoning this step asks the viewer to follow, one link per
  line ("A, so B"). A step that looks like one item often holds several links or several pieces of evidence; only
  writing them out shows its load. In the script every link gets at least one beat
  ([teaching/rules.md](rules.md), principle 15). **Every step of a derivation is a link:** taking the log, turning a
  product into a sum, cancelling log and e, expanding the square, differentiating, setting it to zero, solving: one
  line each. "Differentiate, set it to zero, so μ is the mean" is not one link for a viewer who cannot yet do this; it
  is a whole derivation. Steps that are only opening, recall or close, with no new reasoning, need no links.
- **The hardest step for this viewer, and how you plan to teach it:** which concrete example, picture or guess. Pick it
  from "where they will get stuck" in the audience description, not the most exciting reveal. The opening is usually
  the easiest; viewers usually fall behind in the middle. The hardest step is usually the one just before the aha, or
  where the core formula first appears.
- **The episode's place in the series:** which endpoint it serves, which earlier episodes it needs (from the question
  map's prerequisites), and which segments it contains.
- **Load and numbers:** new terms, people with a role, places and years to remember, roughly how many numbers the
  narration says, how many steps the outline has, the length, and whether the order differs from the original book.
  These are not rules: they are your basis for judging the load, which must stay within the viewer's capacity
  (step 4 below). Names that only appear on screen and need not be remembered do not count.
- **Completeness:** which episode each coverage item goes to. Items placed nowhere go into the plan's
  `excluded_topics` with a reason. The user sees that list with the plan, so write the reason in plain words.

## The overall proposal

After the audience description comes your **recommended proposal**: given this viewer, what they need to fill in to
reach the understanding they want, the depth and purpose you suggest, and where it stops. Then a shorter option, saying
clearly what it loses. You also choose the angle, and say it in one sentence. Neither completeness nor clarity is
compromised; only how much goes into each episode can change. The shallower the viewer's level, the less goes into each
episode and the more episodes there are. Only when there are too many episodes do you discuss with the user lowering
the depth or the completeness. Write the gist of the proposal in `rationale`. When the user says the level or the
purpose is wrong, or it is too long or too short, change the audience description or the plan, and plan again.

**Episode length** (`estimated_duration_seconds`) is the time that question needs with this presenter's playbook: each
link one beat with a pause after its conclusion (about half a minute per link), plus the opening, the recalls and the
close. The script is written to this length. A script much shorter than it usually has links squeezed out
([teaching/rules.md](rules.md), principle 15).

## Planning: how many episodes, each answering what

**Inputs**

- The viewer (from the probes): their starting point (judged part by part), misconceptions, goal and **capacity**: how
  much new content they can take in per episode.
- The sources (from deep reading): the **question map** in the research notes: which type of question each part of
  the sources answers, where it comes from, which questions must be understood first (its prerequisites), and whether
  this viewer already knows it.
- The coverage list is the raw material: a heap of things to learn, with no order. What comes first is the plan's
  business; never follow the sources' chapter order.
- What the viewer already knows well is the best hook: look for the moment "you've actually used this idea already".

**Six steps**

1. **Write the endpoints:** what the viewer can do after the whole series. Each one is the outcome of some question type,
   for example "say why ranked-choice voting can elect someone most people dislike". Endpoints come from the viewer's
   goal and the core of the sources.
2. **Walk back from the endpoints:** find the questions each endpoint needs answered first, and follow the question
   map's prerequisites back until you reach something the viewer already knows. The questions on the way are what to
   teach. What is not on the way gets one sentence, for completeness, or goes into `excluded_topics` with a reason.
3. **Estimate the load:** how much is new to this viewer in each question on the way: unfamiliar terms, people, places
   and years to remember, how many links a causal chain or a proof has (write out each step's links; there are often
   more than they look), and how many pieces of evidence or rebuttals a claim needs (each one is a line the viewer has
   to follow, even one said in a single sentence).
4. **Cut into episodes:** one main question per episode, with a load within the viewer's capacity.
   - **Too heavy:** take its heaviest prerequisite question out and give it an episode first. Split by prerequisites;
     never cut one question in half.
   - **Very light, and a prerequisite of the next question:** merge it into the next episode as a segment, told as a
     short version that meets its own type's must-haves. Merge only if that episode stays within capacity; otherwise
     each gets its own episode.
   - **One main line per episode.** The main question asks one thing. When it is really two claims ("X, and also Y"),
     it is two questions: split them by prerequisites into two episodes, or make the first a segment of the second.
   - When an argument question sets a claim against several rivals ("why X and not A, B or C?"), each rival is one
     question. An argument episode tests only one rival, with one test, and the method of testing it takes away holds
     for that rival.
   - An argument carries only the one or two strongest pieces of evidence or rebuttals. The others go to the episode
     that needs them, or into `excluded_topics` with a plain reason. Never mention them in passing in this episode: a
     rival, a piece of evidence or a rebuttal mentioned in one sentence is still a line the viewer has to follow.
   - One chain of reasoning runs, without a break, for no more links than the viewer's capacity. An episode's total
     number of links has no cap: it decides how long the episode is. A piece of evidence that deserves an episode gets
     its own episode.
   - **A derivation is often another question.** A mechanism episode asks "how does it work"; the derivation answers
     "why must it be so" (why the best centre must be the mean), which is a proof question. In one episode they make
     two main lines. The mechanism episode sees the result on numbers; the proof gets its own episode.
   - **A derivation longer than the viewer's capacity** has two ways out. Either it becomes its own episode, cut into
     stretches that fit the capacity, with seams between them. Or this episode only verifies the result on numbers:
     first say in a sentence or two what the result looks like (what each term is, and so why it is the answer), then
     confirm it with one number or one picture (compute a table; see where the lowest point of the graph lands), and
     leave the derivation to the episode that needs it, or to the book. Verifying confirms; it is not another
     derivation. Do not compute a number at every step: one number per sentence keeps the viewer pausing. Then word
     the episode's `question` and `takeaway` truthfully, with "see" and "verify", not "derive". The script audience
     reviewer checks against them: given "derive", it asks for the derivation, and the script grows longer round after
     round.
   - The number of episodes is a result, never set first. One, three or ten episodes are all possible.
5. **Order them:** every question comes after the questions it needs. Within that, reach the question the viewer most
   wants answered as early as possible. When the answer must wait for prerequisites, the opening episode gives the
   answer's skeleton first: one sentence and one picture, saying which later episodes prove which part, and that it is
   not proven yet. A viewer should never finish an episode without knowing roughly what the answer looks like. Keep
   related questions together. Each episode opens by recalling the earlier episodes it needs.
6. **Check:** every endpoint is served by an episode; each episode has one main question, one main line, and a load
   within capacity; every question comes after the questions it needs; every coverage item has a place.

When the user set a length, step 4 instead fits the load into that length. A question that does not fit becomes the
next episode, or goes into `excluded_topics`.

**When the user chose only part of the sources:** the endpoints are what that part enables. What the part needs from
earlier chapters is arranged by prerequisites as a short stretch; never assume they read those chapters. When the next
part is made later, read it deeply, add its questions and coverage items to the same research notes, and continue the
plan after the existing episodes (the same series, colours and devices). Episodes already made are not affected.

**What the presenter does here:** the presenter does not cut episodes. They speak up in one case only: with their way of
teaching, an episode's main question cannot be finished within the viewer's capacity. Then they may ask for that episode
to be split again by prerequisites, with the reason in `rationale`.

## Inside each episode

For each episode, think through (in its `design.md` when you make it; enough of it while planning to write the
outline):

- the main question in one sentence, in two wordings: the naive one and the restated one. They are the same question:
  the guess, the title, the argument and the close all answer it. Do not guess with the naive wording and argue with
  the restated one;
- the foil (the familiar "standard account" to push against);
- the spine object;
- the acts, each opened by a question;
- the key-point labels (at most three);
- the closing reframe.

The skeleton follows the episode's playbook. For a short episode (6 minutes or less), use the short skeleton in the
playbook: one or two acts, one aha, no roadmap and no recap.

## The coverage map

Map every item of the coverage list to an episode, an act and a depth, in the research notes:

- **A, full:** with a picture, a derivation or an argument, and a question to the viewer.
- **B, one paragraph and one dedicated picture** (20 to 60 seconds).
- **C, one sentence and one visual marker** (a chip on a timeline, a ledger cell, a list of names).

Every item without a place needs a reason, in `excluded_topics`.

## Across episodes

- The episodes share one spine object: the question changes, the main line does not.
- Visual state shared across episodes (how an object looked at the end of the previous episode) is fixed in the series
  bible.
- **Cross-episode devices** (a ledger, a running list, a series map): in the episode where one first appears, build it
  in the body with one concrete moment (say what it is, fill its first cell). The close only fills cells; it never
  introduces a new structure. Later episodes recall the device after the main question is stated, with one sentence
  saying what it is. Never put it between the opening hook and the main question.

## When the script departs from the plan

The plan is the current plan. When writing the script shows that an episode needs something different, update the plan:
change the `outline`, `takeaway` or `taught_terms` so that later episodes' reviews read what was actually taught.
Record the departure and why in `decisions.md`; the user hears of it when the episode is delivered.
