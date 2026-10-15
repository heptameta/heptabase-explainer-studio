# Getting to know the viewer

Contents: [Probe with the sources themselves](#1-probe-with-the-sources-themselves) ([who will watch](#who-will-watch),
[how many questions](#how-many-questions), [for a teacher](#for-a-teacher)) ·
[The audience description](#2-the-audience-description-after-deep-reading) ·
[The first paragraph and the goal](#3-the-first-paragraph-and-the-goal)

Every presenter shares this. The aim is to grasp the viewer clearly and truly before spending any effort. Knowing what
they know, where they get stuck and how they like to be taught tells you what can go fast and what needs to be
unfolded in full. Everything the user gives comes at the start, and it is only their reactions: did they understand it,
did they like it. Never make them write long texts or describe their own level and expectations. Users usually do not
know what they want; they only know whether they understand and whether they like it.

## 1. Probe with the sources themselves

Do this before any deep work. Finding out after the script is written that the audience was wrong is the most wasteful
failure, and the most discouraging one for the user.

### Who will watch

Two kinds of users ask for videos, and they are asked different things:

- **A learner** wants to understand the sources themselves: they are the viewer. Probe them as below.
- **A teacher** has the knowledge and wants videos for other people: an author with their own paper, a teacher with a
  textbook, a team with its codebase. The viewer is someone else, and the user knows the sources better than you do.
  Never test their understanding of their own material: ask about their viewers ([for a teacher](#for-a-teacher)).

Tell which one from the request ("help me understand this paper", "for my students"). When it does not say, the first
question asks only that: are the videos for you, or for people you teach or share them with? Ask it on its own, so the
next question can say which kind of questions follow. Record it in the research note. Either way, the plan's audience
is the viewer.

### How many questions

Next (first, when the request already said who will watch), let the user choose how many questions to answer. The
question must make sense on its own, to someone who skips the message above it. In the question itself, say what the
questions will be like (a few real sentences or passages from the sources, asking which ones they follow, or a quick
guess; for a teacher, questions about their viewers, not about them), what the answers decide (what the videos pass
over quickly and what they explain from scratch), and only then ask how many. Never ask a bare "How many questions do
you want to answer?". For example: "Before I read the whole paper, may I ask you a few quick questions about it? I'll
show you some of its sentences and ask which ones you follow, or ask you to guess something. Your answers decide what
the video passes over quickly and what it explains from scratch. How many would you like to answer?" Offer four
options, each with its number of questions and what they cover (never minutes):

- **Start now:** no questions. Infer the viewer from the request and the sources, conservatively (when unsure, assume
  they forgot), and mark every judgment in the research note as a guess.
- **A few (2 questions):** round one only.
- **The usual (4 to 6 questions; recommended):** two or three rounds, as below.
- **More (up to 9 questions):** the usual, plus the way of telling, familiar worlds and vocabulary.

This asks how many questions, not how deep or how long the videos are: those stay your recommendation after deep
reading. Whatever they choose, the plan review is where they can still say it does not sound like them. Record the
choice in the research note.

### Lessons from calibrating viewers

From real production: one video's audience had to be changed three times before it was right.

- **Having watched it is not remembering it.** Someone who "watched 3b1b's Transformer video" has usually forgotten what
  QKV, softmax and layers are. Choosing the audience by what they watched overestimates them; look at what they still
  understand. When unsure, assume they forgot.
- **Calibrate with the sources, not with labels.** "Engineer", "graduate student" and "general public" are too coarse;
  the real answer often falls between two options.
- **Never let the user assess themselves, and never ask first how deep or how long they want it.** Users want deep,
  complete understanding by default, and avoid options that look shallow. Whether their current level can get there in
  one or two videos is for you to judge. Depth, purpose, number of episodes and length are your recommendations after
  deep reading, not constraints set at the start.
- **What they say counts only after it is checked.** Choosing "which passage felt just right" or ticking "which words
  need teaching again" is also self-assessment. People overestimate how fast they can follow (feeling they understand),
  and sometimes underestimate. So every such choice is followed by a check question that shows what they can actually
  do. Estimate capacity from the check, not from what they chose.
- **The most common viewer has seen popular science and forgotten the details.** They are not slow; they forgot. Do not
  use the terms directly, and do not start from typing on a phone. How to handle them:
  [teaching/rules.md](rules.md#the-viewer-who-has-seen-it-and-forgotten).

### How to probe

1. **Skim the sources** (title, abstract, table of contents, section openings, figure captions; no deep reading), just
   enough to pick the probes. When the sources are large and the user chose a part, pick the probes from that part. For
   a paper, first look for a web version ([sources/paper.md](../sources/paper.md)).
2. **Show the user real things from the sources and ask how they react**, in the user's language: the question, the
   option titles and descriptions, and every sentence quoted from the sources, translated faithfully when the sources
   are in another language (keep a term in the original, in brackets, only when the exact word matters). Each question
   has at most four options, and some allow several answers. Ask one or two questions per round, and choose each round
   from the reactions to the last. **Stop at the number of questions they chose** (the usual: two or three rounds).
   - **Original-sentence probe:** pick 3 or 4 sentences from the sources, from easy to hard (short, and faithful to
     the sources: translated into the user's language when they are in another one; a one-line plain paraphrase may
     be added). Ask "Which of these do you understand when you read them?" Several
     answers allowed.
   - **Paraphrase choice** (on the most important sentence): give 3 or 4 plain-language versions: one correct, one or
     two common misunderstandings, and one "I can't really tell". Ask "Which is closest to what went through your mind
     when you read this? There's no right answer; I want your first instinct." People feel they understand when they
     see familiar words. Only this question shows whether they really understand, never learned it, or **think they
     understand but have it wrong** (they chose a misunderstanding).
   - **Intuition guess:** one concrete question about the topic, with options built from common wrong intuitions, plus
     "no idea". Example: "A small model with only attention and no MLP: do you think it can learn 'after seeing A B …
     A, say B next'?" Pick a question that **the hardest step of the video will resolve**: it is a diagnosis. The same
     question can later be a guess beat in the video ([teaching/rules.md](rules.md#guess-beats)), but there it is asked
     afresh to every viewer, and the video never mentions what anyone answered before. The video will be shown to
     others; the opening questions only estimate this user's level.
   - **Depth probe:** write 2 or 3 passages you might really say in the video, on the same key concept and in the
     same tone, differing only in depth (mentioned in passing; one reminder plus an example; from scratch). Ask "Which
     one felt just right?" This tests level.
   - **Check after listening** (right after the depth probe; always do it): take the passage they chose and ask a
     question only someone who really understood that passage can answer, for example "From that passage, why does X
     cause Y?" The options: one correct, one or two common wrong ideas, one "not sure". Wrap it as a guess, never say it
     is a test. They chose the fast passage but answered wrong: overestimated. They chose the slow passage but can also
     answer the fast version: underestimated.
   - **Way of telling** (when needed): one more question tests the preferred way of telling: the same depth, told two
     ways (for example an analogy first and then the formula, versus starting from real numbers). Never mix depth and
     way of telling in one question, or you cannot tell which one they chose.
   - **A reasoning chain** (when the sources are mainly reasoning): write, at narration speed, 3 or 4 steps of reasoning
     the sources really make, and ask the reason for the middle step or for the conclusion. How many steps they can
     answer is how many steps they can follow in one go.
   - **Presenter probe** (when two or more presenters have a playbook for the question type of the sources' main
     question): at the same depth, on the same concept, each presenter whose shape still fits the answer (usually two)
     writes a passage in their own way of making people understand. For example: drawing the idea and rebuilding it
     step by step; shrinking it into a small world where you take a seat and play a round; building a small toy and
     running it for you. Ask "Which one would you rather keep listening to?" The presenter choice follows it
     ([presenters/README.md](../presenters/README.md)).
   - **Surprising facts** (when needed): list 3 or 4 true facts about the topic, one or two of which run against a
     common misconception. Ask "Which of these surprise you?" Being surprised by a true fact means they believed the
     opposite. Such a fact is often also the opening hook.
   - **Familiar worlds** (when you plan to use analogies): "Which of these do you know well?", with the things you plan
     to use as analogy sources as options (spreadsheets, search engines, a band...). The source of an analogy must be
     something they know well.
   - **Vocabulary** (when needed): split the sources' key words into at most four groups, from easy to hard. Ask
     "When you hear which groups would you need a reminder, or a lesson from scratch? (Tick the ones you've seen but
     forgotten too.)"
   - Suggested order. Round one: the original-sentence probe and the intuition guess. Round two: a paraphrase choice on
     a sentence near their level and a depth probe, followed by the check after listening. Round three (when
     needed): whichever of surprising facts, way of telling, familiar worlds and vocabulary best removes your remaining
     uncertainty.
   - If they understand everything, go deeper; if they do not understand even the easy ones, go more basic. Never put
     "What is your level?" or "How deep do you want it?" in a question.
   - Keep option titles short ("Line 2", "Version B"), and put the full sentence or narration in the option's
     description. The original-sentence probe allows several answers.
3. End with one sentence inviting anything else, and say it is fine to add nothing, for example "Anything else you'd
   like me to know? If not, I'll go and read the whole material."
4. **Record what you learned** in a research note about the viewer (for example `research/audience.md`):
   - **Vocabulary** (always): each key word as *known*, *refresh* (heard it, forgot it), *teach* (never learned it) or
     *misconceived* (thinks they know it, but has it wrong).
   - **Probes:** what you showed them and how they reacted. This is the evidence for every later judgment.
   - **The intuition guess:** the question, the options, the correct answer and their first choice.
   - **Checks:** every self-assessment that was checked: what they claimed, the check question and its answer, what they
     answered, the result (matched, overestimated or underestimated) and how it changed your capacity estimate.

   When you write the plan (after deep reading), these become its audience fields. Words marked refresh or teach go
   into `audience.unfamiliar_terms`: the script audience reviewer reads them as words the viewer does not know yet.
   Each misconceived belief, with the evidence for it, goes into `audience.misconceptions`.
5. **Estimate their capacity:** how much new content they can take in per episode. Base it on the checks, not only on
   which passage they chose: which depth they chose in the depth probe (in passing; a reminder plus an example; from
   scratch), how they did on the check after it, how many steps of the reasoning chain they followed, how many words
   they ticked for teaching again. Overestimated: one level down (an example for each piece of reasoning, fewer steps).
   Underestimated: one level up. Write it as amounts anyone can read, for example "per episode at most 4 new terms,
   3 new people, 5 reasoning steps", with its evidence, in the research note, and say it in plain words in a later
   paragraph of the audience description (not the first). The plan cuts episodes by it
   ([teaching/plan.md](plan.md)). The user feels the load from each episode's length and outline. If it is too much or
   too little, they will say so; then change the capacity and plan again.

### For a teacher

A teacher knows the material and their viewers better than you do. Ask for reactions they can give at a glance, still
never long texts. Skim the sources the same way, then ask, in this order, as many as they chose:

- **Who watches:** 2 to 4 concrete descriptions of viewers, built from the sources (for example "first-year students
  who have had calculus but not linear algebra"); several allowed. Never labels like "beginner".
- **Which they would follow:** the depth probe, 2 or 3 passages on the same key concept at different depths: "Which one
  would your viewers follow?" No check question after it: they judge others, not themselves.
- **Where they go wrong:** 3 or 4 common misconceptions on the topic: "Which do your viewers usually hold?" They go into
  `audience.misconceptions`, with the teacher's answer as the evidence.
- **What must not be lost:** 3 or 4 key results or points of the sources: "Which must every viewer take away?" They
  are the plan's endpoints.
- **Their way of telling** (when more questions were chosen, or two presenters fit): the presenter probe, "Which one
  would your viewers rather keep listening to?"
- **Their words** (when needed): when the field names one thing two ways, which one they use.

The vocabulary and the capacity come from these answers; note in the research note that they are the teacher's
estimate.

## 2. The audience description (after deep reading)

After reading the sources, write the audience description: `audience.description` in the plan. It is the basis of
every later judgment: planning, picking the hardest step, handling misconceptions, and the script audience review (the
audience reviewer is given it as "who you are"). The key question: **have you really understood the viewer?**

It is **not** a restatement of the probe answers ("you know A, you don't know B"). It should:

- **Say the picture in the viewer's head:** roughly what their mental model of the topic looks like now, and which
  version it stopped at. Example: "Your picture of the Transformer probably still stops at that diagram: a stack of
  blocks, with data flowing up through layer after layer of attention."
- **Say where they may be thinking wrong now**, gently and with evidence: "In the second question you chose 'attention
  means finding the most relevant word'. That's reasonable; most popular videos say so. But the attention heads in the
  paper are often doing something quite different: they move information rather than pick out what matters. This is
  where the video will spend the most time." Seeing their own idea is the first step of changing their understanding,
  and the video handles it from there. Each of these goes into `audience.misconceptions` (the belief and the evidence);
  write the better version in the research note.
- **Say the difficulties they will not have:** "You don't need me to explain matrix multiplication." Then the video does
  not waste their time there.
- **Say where they will get stuck, and why.** Not "you don't know softmax", but "When the paper multiplies two matrices
  and treats the result as a table, you'll need to stop and think, because you remember a matrix as a grid of numbers,
  but not that it can stand for a correspondence."
- **Say what can go fast and what needs full treatment**, with reasons.
- **Say how they like to be taught** (from the depth probe and the way of telling): for example concrete examples
  before formulas, no childish analogies, real numbers.
- **Say what they really want**: for example "You don't want the popular-science version; you want to be able to read
  this paper on your own afterwards."
- **Back every judgment with evidence** ("because you said line 2 made sense and line 3 didn't"), so later steps can
  check why you judged that way. Mark guesses as not yet confirmed.
- Use the second person, be concrete, write short paragraphs, and do not pile up jargon.

## 3. The first paragraph and the goal

The user should see at a glance whether you overestimated or underestimated them. So the description opens with what
they know now, and the plan's `goal` says what they want. The rest of the description, the capacity, the vocabulary and
your assumptions are your basis for planning, not something they need to read first.

- **What you know now** (the first paragraph of the description): two to four concrete things, some they know and some
  that are new to them, one per line. Say them with things from the sources, not with labels like "beginner" or
  "intermediate". Example:

  ```text
  - Economics at news level: you've heard of rate rises and inflation, but couldn't say who decides or how prices change
  - You know the US has a president, a Congress and a Senate; the early history of its central bank is new to you
  - Permissions and how work is divided in an organization are very familiar
  ```

- **What you want** (the plan's `goal`): one sentence, the purpose of this learning, in their words. Example: "When I
  read news about the Fed, understand who made the decision and how."
- No evidence here (it is in the rest of the description), and no jargon, file names or field names.
- For a teacher, both are about their viewers ("Your students know…"), and the goal is what the viewers should be able
  to do, in the teacher's words.
- When they say it doesn't sound like them: fix the description first, then the goal, and plan again when needed.
