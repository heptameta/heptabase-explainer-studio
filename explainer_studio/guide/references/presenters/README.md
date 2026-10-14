# Presenters

Contents: [Question type, presenter, playbook](#question-type-presenter-playbook) · [The roster](#the-roster) ·
[Each presenter side by side](#each-presenter-side-by-side) ·
[The same question type, several presenters' playbooks](#the-same-question-type-several-presenters-playbooks) ·
[Precedents](#precedents) · [Choosing a presenter for each episode](#choosing-a-presenter-for-each-episode) ·
[Draft playbooks](#draft-playbooks) · [These files belong to Explainer Studio](#these-files-belong-to-explainer-studio)

## Question type, presenter, playbook

Three things, each answering one question:

| | What it is | Answers | Where it lives |
|---|---|---|---|
| **Question type** | What the viewer can do after the episode. It does not depend on who teaches it; there are nine, shared by every presenter | What this episode must achieve | [teaching/question-types.md](../teaching/question-types.md) |
| **Presenter** | A way of making people understand: the path the viewer takes from not understanding to understanding. Whatever question type the presenter answers, the path is the same | By what way this episode makes people understand | `presenters/<name>/`: `presenter.md`, the script craft `craft.md`, the style `style.md` |
| **Playbook** | A presenter's skeleton for answering one question type in their own way: how an episode runs from opening to close, and how it meets that question type's must-haves | How they tell this question type | `presenters/<name>/question-types/<question type id>.md` |

One presenter × one question type has at most one playbook. The same question type can have playbooks by several
presenters, with completely different skeletons, but all of them meet that question type's must-haves.

**Is a sentence about the presenter or about a playbook?** Move it to another question type the presenter has a
playbook for: does it still hold? If so, it is about the presenter; if it holds for only one question type, it is about
that playbook. Example: "the viewer takes an actor's seat and decides" holds in Fabian's mechanism, argument and system
alike, so it is Fabian himself; "change only one condition and play a new round" is how he meets "predict what changes
when one condition changes" when answering mechanism, so it is his mechanism playbook.

**When is it another presenter, and when only another playbook?**

- When the difference from the existing presenters holds for every question type they handle (what the viewer does is
  different, the picture is a different kind of thing, real examples play a different role), it is another presenter.
- When the difference is in only one question type (the same way, a different skeleton), it is a new version of that
  presenter's playbook.
- When the difference is only tone, colour or pace, it is style: still the same presenter.

**The presenter** is described by the same set of fields (at the top of their `presenter.md`, and side by side in
[the table below](#each-presenter-side-by-side)), each of which must hold for every question type they have a playbook
for: what kind of teacher, how they make people understand, what the viewer does, what the picture is, real examples,
naming, most common mistake. Then their models (whom they learned from), their script craft and style (shared by all
their playbooks), and their question types, derived from their way, each with a reason:

- **Playbooks:** the question types they have a playbook for.
- **Not a fit:** the question types whose must-haves conflict with their way.
- A question type in neither list could be tried: their way can meet its must-haves, but there is no playbook yet,
  so an episode of it would use a [draft playbook](#draft-playbooks).

**A playbook** covers only what belongs to that one question type: the question it answers, how it meets the
must-haves, what sources to use it for, how it differs from other presenters' playbooks for the same question type,
the skeleton, the short version, the quality bar and the self-check.

How many episodes there are and what each answers is not the presenter's decision: the plan decides it, from the viewer
and the sources ([teaching/plan.md](../teaching/plan.md#planning-how-many-episodes-each-answering-what)).

## The roster

| Presenter | What kind of teacher | How they make people understand | Playbooks | Files |
|---|---|---|---|---|
| **Theo** | The teacher at the blackboard | Rebuilds the idea step by step in pictures, until the result looks almost inevitable | Mechanism, argument, conceptual change, system, proof, concept, procedure | [theo/](theo/presenter.md) |
| **Fabian** | The teacher who runs a board game | Turns the problem into a small world and lets you play a round; the result grows by itself out of each actor's choices | Mechanism, argument, system, concept | [fabian/](fabian/presenter.md) |
| **Mason** | The teacher in the workshop | Builds a minimal version that really runs, runs it after every change, and lets what it produces say why | Procedure, mechanism, system, concept, argument, conceptual change | [mason/](mason/presenter.md) |
| **Sophie** | The seminar teacher | First has you judge a concrete case, then changes one thing and has you judge again; from where the two judgments do not fit together she draws out a principle, then puts each principle, in its strongest version, to the test on the same set of cases | Perspectives, argument (normative, interpretive), concept, conceptual change | [sophie/](sophie/presenter.md) |
| **Clio** | The teacher who spreads out a map and walks you through the crossroads | First shows you the ending and the main question on a big-picture map, then follows real people from the starting point; at each crossroads she stops and lays out which roads there were at the time, why this one was taken, and what might have happened instead | Narrative, argument, conceptual change, system | [clio/](clio/presenter.md) |

## Each presenter side by side

Each field holds for every question type the presenter has a playbook for, in the same words as the top of their
`presenter.md`.

| | Theo | Fabian | Mason | Sophie | Clio |
|---|---|---|---|---|---|
| What kind of teacher | The teacher at the blackboard | The teacher who runs a board game | The teacher in the workshop | The seminar teacher | The teacher who spreads out a map and walks you through the crossroads |
| How they make people understand | He rebuilds the idea step by step in pictures, until the result looks almost inevitable | He turns the problem into a small world and lets you play a round; the result grows by itself out of each actor's choices | He builds a minimal version that really runs, runs it after every change, and lets what it produces say why | First she has you judge a concrete case, then changes one thing and has you judge again; from where your two judgments do not fit together she draws out a principle, then puts each principle, in its strongest version, to the test on the same set of cases | First she shows you the ending and the main question on a big-picture map, then follows real people from the starting point; at each crossroads she stops and lays out which roads there were at the time, why this one was taken, and what might have happened instead |
| What the viewer does | Watches the idea being built, block by block; where they want to know, they think for a moment first, then see it confirmed | Takes an actor's seat and makes a decision, then sees what happens when everyone does the same | Guesses what a run will produce, then lets the run decide; when the guess is wrong or the answer does not match, they debug along with him and find the cause | Sits as the judge: gives a verdict on each case first, then sees that verdict tested by the next case or by the strongest reason | Stands where the people involved stood at the time, using only what they knew then, first guesses which road they will take, then sees how the real choice changes the big-picture map |
| What the picture is | The idea itself: a number line, vectors, a machine, a table | A small world: icons for a few groups of actors, one spine picture that grows along with the episode, a board where the conclusions are written | Things that run: on one side the rules (a few lines of code, a few steps, a circuit), on the other the result of every run, with an answer card beside them | A case that does not run (a simple sketch, changing one thing at a time), and a position board: one column per view, one row per case | One big-picture map used from start to finish (a real map, or a seat chart of "who is at the table"), with the portraits and goal cards of the people involved; a crossroads is a few arrows on the same map, with the roads not taken left as dashed lines |
| Real examples | They are the protagonist. Dig into one, let the whole episode turn around it, then apply it quickly elsewhere | Evidence only: once the small world has run, one sentence and one picture each | They are the answer card and the destination: once built, the toy stands beside the real thing and matches its key behaviour (the same answer for the same small input, or the same strange fault) | They are the exam hall: a real lawsuit, work or original text, on which every view must hand in its answer; the real verdict is one side's voice, not the answer | They are the protagonist: what happened that one time, itself; documents, people's own words and objects are evidence, one item carrying one turning point |
| Naming | Understand first; the name comes after | Actors get no personal names; the close maps the world's words back onto the sources' terms | Build it and run it first, then name it; the name is what that piece is called inside the real thing | Each view is first a plain-language claim, a handle the viewer holds while judging; the school and the names come along with it, and when a name is attached she reads a short passage of the person's own words | Only people who make a decision at a crossroads and will appear again get names; each gets a portrait and "what they want" the moment they enter, at most four or five per episode; everyone else is called by their seat or faction |
| Most common mistake | Following the sources' own cases, so one episode switches between several times and places, and stacking metaphors onto the sentences that carry the reasoning | Making a simplified model look more certain than it is. So at the very start he says whose model it is and that it is simplified, and every episode acts out where the model is wrong | Running a pile of results without saying why, or turning into a checklist of steps to follow. So before each run he says what to look for this time, and each time a pattern shows, he points at one of the runs and says the cause | Turning into a string of monologues taking turns, or judging on the quiet through order and tone. So every view answers on the same set of cases and is put at its strongest; when one is caught out, it gets one reply; and at the end of each case the board is updated once | Turning into a chronology: one event after another, crossroads passed over in a sentence, only the roads of the side driving events laid out (the Mexican–American War told only as what the United States wanted, not why Mexico would not sell), people judged with hindsight. So she stops for a beat at every crossroads, lays out the roads and reasons of at least two sides, and says why someone chose as they did using only what could be seen at the time |
| Models | 3Blue1Brown | CGP Grey, Nicky Case | Andrej Karpathy, Bret Victor | Michael Sandel, Big Questions Dialectic | Imperial War Museums, Johnny Harris, Historia Civilis |
| Script craft, style | [theo/craft.md](theo/craft.md), [style.md](theo/style.md) (the blackboard) | [fabian/craft.md](fabian/craft.md), [style.md](fabian/style.md) (the small world) | [mason/craft.md](mason/craft.md), [style.md](mason/style.md) (the workbench) | [sophie/craft.md](sophie/craft.md), [style.md](sophie/style.md) (the seminar) | [clio/craft.md](clio/craft.md), [style.md](clio/style.md) (the map table) |

## The same question type, several presenters' playbooks

Several presenters often have a playbook for the same question type (mechanism, system, concept, argument, conceptual
change and procedure all do), told in completely different ways. Only Sophie has perspectives, only Clio has narrative,
and only Theo has proof: give those to them directly. When several have one, choose by **the shape of the answer**,
asking four questions in order:

> **One (ask only for argument and concept): if all the facts were known, would the disagreement remain?**
> Yes (the disagreement is over what matters most, how a passage should be read, or where a concept's line is drawn by
> value judgment, for example moral and legal distinctions; the evidence is judgments of cases and original texts) →
> Sophie. A term with several definitions where the facts can be checked ("state": the recognition theory or the
> criteria theory) does not count. The goal of use needs a concept you can apply, and when the disagreement remains it
> is not use: judging "does it count?" is telling apart; judging "should it?" is argument or perspectives.
> No (the evidence can in principle rank the answers; a counterfactual dispute about only one event, "what if that had
> not happened?", counts too: the record can in principle rank them) → ask question two. Conceptual change does not ask
> this question, since it is settled by definition; instead ask: "Is the old intuition still in the viewer's head, and
> was it later changed by an institution or a ruling?" Yes → Sophie.
>
> **Two (ask only for argument, conceptual change and system): does the answer depend on the particular people, timing
> and chance of that one time?**
> Yes (the claim is only about the causes of one event; or the answer the viewer wants is why that group of people
> chose this road among several roads or plans, when they could have chosen another) → Clio.
> No (the answer holds in another place or another era) → ask question three.
>
> **Three (ask only for mechanism, system, argument and conceptual change): take away "several actors, each with their
> own aims, making choices and affecting each other": is the answer still there?**
> No (the answer grows out of many actors each acting on their own interests or rules and affecting each other) →
> Fabian.
> Yes (the answer lies in a structure: an equation, a machine, a program, data) → ask question four.
>
> **Four (ask only for mechanism, system, argument and conceptual change): take away "run it once" and allow only
> reasoning: does the answer still make sense?**
> No (the behaviour only shows when run, and there is no easy formula) → Mason.
> Yes → Theo; when the viewer chose the "build a small toy and run it for you" telling in the opening presenter
> probe, Mason.

Actors need not be people: a group of companies, competing genes, two sets of genes with conflicting interests inside a
cell, a spreading pathogen. As long as the explanation is "who wants what, what the rules let them do, and what happens
when everyone does it", it is Fabian's shape. Only one thing updating by a rule (a learning agent, a controller, an
optimizing program), with no several actors affecting each other, is not Fabian's shape. When both shapes make sense
(the same thing can be told as a machine, as a tug of war between groups of actors, or as a toy run for you), decide by
which telling the viewer chose in the opening presenter probe
([teaching/audience.md](../teaching/audience.md#how-to-probe)). Fabian and Sophie both put the viewer in a seat: Fabian
asks "what would the person in this seat generally do for themselves?" (a prediction with an answer, known once the
world has run); Sophie asks "is it right, should it be done, how should this text be read?" (no world will run out the
answer for you); Clio asks "how would this one person have chosen at the time?" (that one time happened only once, and
the answer includes chance).

| Question type | Theo's playbook | Fabian's playbook | Mason's playbook | Sophie's playbook | Clio's playbook | How to choose |
|---|---|---|---|---|---|---|
| Mechanism | Explain a mechanism: rebuild a structure, each link done once on screen | Explain a mechanism: each link is one step an actor takes by the rules; change only one condition and play a new round | Explain a mechanism: build a toy, and run each link as it is attached; or turn a knob, lay out all the cases, then step down | none | none | By questions three and four |
| System | Walk through a system: a faint division-of-labour diagram, grown block by block from a version that almost works, each block patching one hole; finally remove a block to see who gets hurt | Walk through a system: follow a ballot or a tax payment past actors with their own interests; change one rule and see how everyone changes what they do (exploiting loopholes included) | Walk through a system: all the components run together, pointing at one piece of data as it passes every station; change one component and see who changes with it | none | One part, one crossroads: the finished system drawn faintly first, each part filled in solid at its crossroads of the time, the options not chosen left as dashed versions | By questions two, three and four. The parts are actors who make choices (how the three branches check each other) → Fabian; the viewer wants why it was designed this way back then (which plans those framers chose between) → Clio |
| Argument | Test an argument: the claim built on an example, the rival stated in full, data and studies read item by item | Test an argument: the claim and the rival are each a small world, each running from the same starting point to a prediction; what really happened is the reveal | Test an argument: the claim and the strongest objection written as predictions of the same number, each run once, the rival running on its strongest ground | Try a claim: each piece of evidence is a variation of the same set of cases (or a passage of original text), and the viewer judges first; the strongest objection put at its heaviest | Walk the same road twice: the two accounts circled at the same crossroads, evidence pinned to that day item by item, two dashed lines side by side | By questions one and two, then by what the evidence looks like: judgments of cases and original texts → Sophie; the record of one event → Clio; a causal account of how actors behave that applies to many cases, with outcomes that really happened as evidence → Fabian; the same direction can be run out on a small toy → Mason; data, experiments, studies that must be read and understood → Theo |
| Perspectives | none | none | none | A seminar: each view in its strongest version, tested on the same set of cases; the last seat is left for the viewer | none | Sophie |
| Procedure | Reinvent a procedure: each step answers the question the previous step left, so a forgotten step can be worked back out | none | Show it once: from blank to running, each step running out its value; then another input, done again | none | none | Ask: is this procedure's most common mistake thinking wrong (a step of reasoning goes wrong, for example getting wrong what to multiply) or one that only shows when run (an infinite loop, off by one, clicking the wrong control)? Thinking wrong → Theo; shows when run, or the steps are conventions or interfaces → Mason; both, by the presenter probe. No presenter has a playbook for a skill that needs watching a real person's body move: see [draft playbooks](#draft-playbooks) |
| Concept | Enclose a concept: examples and non-examples in the same picture, and the definition is the line between them | Separate a concept: the same scene run twice, flipping only one condition to get the non-example that looks most alike | Turn a knob to sort the kinds: runs of the same toy at different knob values, and the definition is a measurable check | Draw a line: the viewer gives a definition first, cases differing in one place test it, and it is repaired from where the judgments differ | none | By question one, then by what the concept is (questions three and four are not asked): a structure (a probability, a kind of mathematical object) → Theo; the situation of actors (an institution, a kind of competition) → Fabian; a behaviour of a system whose kinds only show when run (convergence and divergence, overfitting) → Mason; a distinction whose line is drawn by value judgment (deserving versus being entitled) → Sophie. When both make sense (a repeated game is a mathematical structure and also a situation of actors), by the presenter probe. When the goal is use ([teaching/question-types.md](../teaching/question-types.md#concept-the-other-goal-use)), look at what the tool is: a structure that can be computed (expected value, compound interest, opportunity cost) → Theo; several groups of actors affecting each other (disruptive innovation) → Fabian; a system regularity that only shows when run (queueing, feedback loops) → Mason; Sophie has no playbook for use |
| Conceptual change | How an idea changed | none | Run the old method until it breaks: the old method built and running right, then run until it breaks; the new method first produces the same answer, then pays its bill | How an intuition was overruled: the viewer judges a case by the old intuition, one change and it no longer holds, then say who changed it and in which year | Same question, two tables: the time the old idea was chosen and the time it was replaced, compared on the same seat chart | The old intuition is still in the viewer's head and was later changed by an institution or a ruling → Sophie; by question two (the change of idea falls on two dated decisions) → Clio; when both Sophie and Clio make sense (an intuition changed by a law or a ruling), by how the question is asked: "on what grounds does the old intuition fail?" → Sophie, "why that year, and why not before?" → Clio; the old idea is an old method that can be built → Theo or Mason, by the presenter probe; anything else (a worldview, how a discipline's ideas changed) → Theo |
| Proof | Find the proof: believe it first, then find the key idea and where it comes from, saying why at every step | none | none | none | none | Theo |
| Narrative | none | none | none | none | Walk the crossroads: three or four crossroads on the big-picture map, each side's goal cards side by side, a guess first, the roads not taken left as dashed lines | Clio |

## Precedents

"How to compute it, how to do it" is procedure; "why it works" is mechanism; "why it must hold" is proof. "By the
presenter probe" means: decide by which telling the viewer chose in the opening presenter probe.

| Topic | Question type | Who | Why |
|---|---|---|---|
| What the attention mechanism does | Mechanism | Theo (Mason if the presenter probe chose his telling) | Remove the actors and the answer remains; reasoning alone makes sense of it: it is a computation |
| Why the commons get used up | Mechanism | Fabian | The answer is exactly what results from everyone acting on their own interests |
| How the electoral college works, and whom abolishing winner-takes-all would affect | System | Fabian | The parts are voters, states and candidates; change the rule, and candidates go to campaign in other states |
| How a program handles a request | System | Theo (Mason if the presenter probe chose his telling) | The components work as designed and do not exploit loopholes; why each station is designed this way can be reasoned out |
| How Bitcoin makes everyone trust the same ledger without a bank | System | Theo (Fabian when the viewer wants why miners are willing to be honest and how the incentives are designed) | Each block patches one hole in the previous version, explainable by reasoning; the incentives are another question |
| How a cell turns the energy in food into ATP | Mechanism | Theo | The answer is in the structure of a molecular machine, explainable by reasoning |
| Why there are two sexes | Mechanism | By the presenter probe (Theo / Fabian) | It can be told as a structural constraint of cells, or as a conflict of interest between two sets of genes |
| How raising interest rates brings prices down | Mechanism | By the presenter probe (Theo / Fabian) | It can be told as an equation, or as the separate reactions of banks, firms and households |
| What a p-value is, and how it differs from the probability that the hypothesis is true | Concept | Theo | The answer is in the structure of a conditional probability |
| How backpropagation is computed cell by cell | Procedure | Mason | Every step has a numerical answer to check against; the viewer wants to be able to compute it themselves |
| Why language models cannot count the letters in a word | Mechanism | Theo (Mason if the presenter probe chose his telling) | Reasoning makes sense of it: the model sees tokens, not letters; building a tokenizer and running it for you is Mason's telling |
| Why a steering rule gets through this bend and not that one | Mechanism | Mason | The rule is simple, the behaviour only shows when run, and there is no easy formula |
| Why training diverges when the learning rate is too large | Mechanism | Theo (Mason if the presenter probe chose his telling) | It can be derived from a parabola; running it once to watch it blow up is Mason's telling |
| Why weather forecasts fail beyond two weeks | Mechanism | Mason | No easy formula gives the two weeks; two starting points a hair apart running and drifting apart only shows when run |
| How a reinforcement learning agent learns a maze | Mechanism | Mason | Only one agent updating by a learning rule, not several actors affecting each other; what it learns only shows when run |
| How to build a Huffman tree | Procedure | Theo | The most common mistake is thinking wrong (which two to merge each time), and every step can be worked out |
| How to write binary search so it never loops forever | Procedure | Mason | The most common mistake only shows when run (off by one, never stopping) |
| Why Huffman coding is always the shortest | Proof | Theo | It asks "why must it hold" |
| Should rich countries open their borders? | Perspectives | Sophie | Once the facts are checked, people who weigh compatriots and people who weigh all humanity still disagree |
| Does Rawls's difference principle hold up? | Argument | Sophie | The claim is normative; the evidence is judgments of cases and original texts |
| Are poor countries poor because of geography or institutions? | Argument | Fabian (Theo when the evidence needs data read and understood) | Both sides are causal accounts, and the evidence is outcomes that really happened, not judgments |
| How deserving differs from being entitled | Concept | Sophie | A moral distinction; the viewer must judge the boundary cases themselves |
| Would open borders lower wages in rich countries? | Argument | Theo (Fabian when told as the separate reactions of employers, migrants and workers; by the presenter probe) | If all the facts were known, the disagreement would disappear: the evidence is research data |
| Should the death penalty be abolished? | Perspectives | Sophie | With all the facts known, the disagreement between retribution and consequences remains; "does the death penalty deter crime?" is an argument inside it, told as a short version that meets argument's must-haves |
| Why Japan attacked Pearl Harbor | Narrative | Clio | It only makes sense with the people, timing and chance of those years (the oil embargo, the breakdown of negotiations, the codes) |
| Why a resource-poor empire overextends | Mechanism | Fabian | Remove the country's name and the years, and the chain still holds elsewhere |
| Did Hitler attack the Soviet Union mainly because of a long-held ideological plan, or because the resource squeeze of 1940 forced him? | Argument | Clio | Both accounts explain the same crossroads of the same event, and the evidence is the record of that time; the shape fits only Clio |
| How the three branches check each other | System | Fabian | The parts are actors who make choices; change the rules and everyone changes what they do |
| Why the US Constitution was designed this way | System | Clio | What is wanted is which options those framers chose between back then, and what might have happened instead |
| Why the UN Security Council's five permanent members have a veto | System | Clio | Each part (who has it, how far it reaches, how it can be changed) was a crossroads at the negotiating table of 1944–45 |
| Why the British Army lifted its ban on gay service members in 2000, and why not in 1967 | Conceptual change | Clio | It asks why that year: two dated decisions (in 1967 the ban was deliberately kept, in 2000 it was replaced) |
| On what grounds did the court say the military's ban on gay service members violates human rights? | Argument (normative) | Sophie | The evidence is judgments of cases and statutes; the same history, asked differently |
| Why TSMC won | Narrative | Clio (when the viewer wants the generalization "why the foundry model wins", it is mechanism, for Fabian) | It depends on those few people, the timing of those years and chance |
| A historians' debate: was partition the result of British divide and rule? | Perspectives or argument | Clio tells the narrative first, then Sophie the debate; when the dispute is over the causes of one event with the record of that time as evidence, it is argument, for Clio | The viewer can judge only once they have the course of events being debated |
| Why the chain rule holds | Proof | Theo | Running it correctly does not mean it must hold |
| Why people stopped believing heat is a fluid | Conceptual change | Theo | The old idea is a worldview; the viewer does not hold it, and it cannot be made into a toy that runs |
| Why criminal law widened the bounds of self-defence | Conceptual change | Sophie | The old intuition ("hitting back is just a brawl") is still in the viewer's head, and was later changed by rulings and guidance |
| From counting word frequencies by hand to neural networks: why language models switched to neural networks | Conceptual change | By the presenter probe (Theo / Mason) | The old idea is an old method that can be built: you can rebuild why it was not enough, or run it until it breaks |
| Do residual connections really make deep networks easier to train? | Argument | By the presenter probe (Theo / Mason) | The viewer needs to read the paper's figures and data → Theo; wants to see it really run in the same direction on a small toy → Mason |
| What a repeated game is | Concept | By the presenter probe (Theo / Fabian) | It is a mathematical structure, and also a situation of actors |
| Disruptive innovation: use it to see whether a company not in the video will be beaten | Concept (use) | Fabian | The tool is about several groups of actors affecting each other: a big company rational at every step, a low-end newcomer, two groups of customers |
| Expected value: from now on, use it to work out whether a choice is worth it | Concept (use) | Theo | A probability structure that can be computed |
| Queueing: use it to see where things will jam | Concept (use) | Mason (Theo if the presenter probe chose Theo's telling) | Customers arriving at random and bunching up is most visible when run; there is also a short formula to derive |
| The harm principle: use it to judge new cases | Judging "does it count as harm?" is concept (telling apart); judging "should it be regulated?" splits by argument versus perspectives | Sophie | A line of value; Sophie has no playbook for use |

---

## Choosing a presenter for each episode

The plan is already laid out: each episode has one main question, and its question type decides which playbook the
episode uses (the episode's `question_type`). For each episode:

1. List the presenters with a playbook for this question type.
2. Rank them for this episode's sources and this viewer. First the shape of the answer (the four questions and the
   precedents above, and the "use it for" of each presenter's playbook). When two shapes both make sense, decide by the
   viewer's reaction to the tellings in the presenter probe ([teaching/audience.md](../teaching/audience.md)).
3. When they fit equally well, choose the one who can present the most episodes: the same presenter across a series
   keeps the voice, the visual style, the colours and the characters consistent.

Record the choice as each episode's `presenter_name` in `plan.yaml`. Why this presenter's way suits this viewer, and
which episodes' question types they cover, goes in the research notes, and in the plan's `rationale` when it matters to
the user.

## Draft playbooks

When an episode's presenter has no playbook for its question type, the episode uses a draft playbook, written for that
episode. Nothing in the plan marks it: the missing playbook decides it, and the plan shows it.

- **When to choose a presenter without a playbook:** when the shape of the answer fits only a presenter without a
  playbook for this question type (and the question type is not in their "not a fit" list), choose them, even if other
  presenters have a playbook. (Today each of a presenter's nine question types either has a playbook or is "not a fit",
  so this rule waits for "could be tried" question types added later.)
- **When no presenter has a playbook for the episode's question type, or none fits its shape:** choose, by the shape of
  the answer, the presenter whose way comes closest to meeting the question type's must-haves; prefer the series'
  presenter when they fit equally. There are no presenters outside this roster. Record the gap with
  `explainer-studio gap add --kind presenter --episode <episode> --need "..." --workaround "..."`. This includes skills
  that need watching a real person's body move: no presenter's way shows that, so adapt the closest procedure playbook
  and record the gap. When the chosen presenter has no playbook for the question type, the episode uses a draft
  playbook.
- **Writing the draft playbook:** write it in the episode's `design.md` before the script: using the presenter's own
  way, style and script craft, answer the items a playbook covers (the question it answers, how it meets the must-haves,
  how it differs from other presenters' playbooks, the skeleton, the short version, the quality bar, the self-check),
  meeting that question type's must-haves. Say why no presenter with a playbook fits.
- An episode with a draft playbook follows the shared rules like any other episode.

## These files belong to Explainer Studio

Presenters, their playbooks and styles, and the shared rules change only with a new version of Explainer Studio. Never
edit these files for a series. A series' own choices go into its series bible, `decisions.md` or the episode's
`design.md`.
