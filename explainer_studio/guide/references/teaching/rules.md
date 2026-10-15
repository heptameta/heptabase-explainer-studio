# Teaching rules

Contents: [Two kinds of rule](#two-kinds-of-rule) · [Enforced by the tools](#enforced-by-the-tools) ·
[Principles every presenter follows](#principles-every-presenter-follows) ·
[The viewer who has seen it and forgotten](#the-viewer-who-has-seen-it-and-forgotten) ·
[Misconceptions, guesses and takeaways](#misconceptions-guesses-and-takeaways) · [Visuals](#visuals) ·
[Fixing after an audience review](#fixing-after-an-audience-review) · [Common failures](#common-failures)

Every presenter follows these rules.

## Two kinds of rule

Each rule says who checks it:

- **Enforced by the tools:** things that make any viewer stuck, whatever the sources or the audience. Where a program
  can get it right (subtitle timing, loudness), the program does it. Where it cannot, the tools refuse narration or
  delivery.
- **Followed by the presenter:** principles. The presenter follows them; the tools do not block them. How well they
  were followed shows in the viewer's comments on the video ([teaching/feedback-analysis.md](feedback-analysis.md)).

How many names and years an episode carries, and whether it follows the original book's order, depend on the sources
and the viewer. They are not rules. They are numbers you estimate while planning and judge against the viewer's
capacity ([teaching/plan.md](plan.md)).

## Enforced by the tools

| Rule | Why | What the tools do |
|---|---|---|
| Text on screen too small to read | Text a viewer cannot read always causes trouble | The automatic check reports `text_too_small`; `deliver` refuses while any remains |
| Other layout a viewer cannot read: text on text, content outside its card or off the frame | A viewer cannot read what is covered or cut off | The automatic checks report `text_overlap`, `outside_container` and `text_outside_frame` in `preview` and `render`; fix every one ([teaching/visual.md](visual.md)) |
| Subtitles out of step with the voice | Subtitles that drift always distract | Nobody times them by hand: `render` makes the subtitles and the narration from the same beat timeline, and when the cover is added at the start, the subtitles move with it |
| Sound too quiet or clipping | Sound that is hard to hear or harsh always causes trouble | `render` normalizes the mix to −16 LUFS with true peak ≤ −1.5 dBTP (it measures first, then adjusts) |
| Narration made before a fresh audience reviewer has read every scene | A scene a reviewer got lost in will lose viewers | `narrate` refuses until every scene has been read and every scene lost in its latest read has been read again ([below](#the-script-audience-review)) |

Two rules are not checked by a program. You follow them:

- **Unfamiliar terms are handled before they are used.** A term the viewer said they do not know, used without being
  handled, always makes them stuck. The plan's `audience.unfamiliar_terms` go to the script audience reviewer, which
  flags any term used before it is explained. Handle each one as described in
  [the viewer who has seen it and forgotten](#the-viewer-who-has-seen-it-and-forgotten).
- **The video follows the plan the user agreed to.** The user agreed to the plan; a video that does not follow it makes
  that agreement meaningless. Scenes follow the episode's `outline`: no step missing, no change of order, no content
  the plan does not have. When the script must depart from it, record what and why in `decisions.md`, and update the
  plan's `outline`, `takeaway` and `taught_terms` if they changed (later episodes' reviews read them). The user hears
  of every departure when the episode is delivered.

## Principles every presenter follows

Basis: about 80 teaching examples across subjects and audiences, and research on learning. Tone, pace, how much
humour, length, the form of the close and when to name things belong to the presenter's style and playbook, and the
presenter decides them. **A presenter uses one style; never average different teachers' ways together.**

1. **Aim at this viewer's starting point.** Whether something is easy to teach is not absolute. The same explanation
   is just right for one person and too fast or too slow for another. Example: a tensor lecture with no animation,
   spoken very slowly, was the only one online that physics students "who thought they understood vectors" could
   follow. Every judgment rests on the audience description ([teaching/audience.md](audience.md)).
2. **Start from the model already in the viewer's head, including what is wrong in it.** Say how they probably think
   now (usually reasonably), let it fail on a concrete case, then give the new one. If you only make the correct
   version clear, the viewer finds it "very clear" and learns nothing. Physics education research: stating and
   overturning students' wrong ideas works far better than a clear explanation. When the viewer has no wrong idea, only
   an incomplete one, organize and respect their intuitions, then let them collide.
3. **Make the viewer want it before giving the answer.** Every new concept needs a reason it has to appear (Grant: "a
   reason to be there"). The question must be felt before the answer comes.
4. **Concrete before abstract, and back to concrete after.** First one concrete example (real numbers, objects,
   cases), then name it, then generalize, and finally verify on one concrete point. "The best teaching order is often
   very different from the logical order." Never open with a definition.
5. **Let the viewer think, when they really want to know.** A good question is one the viewer would come up with at
   this point: what they just saw made them curious or provoked their intuition, and the answer is not obvious at a
   glance. Then stop and let them think (guess, judge, recall), leave time, then reveal. A wrong guess itself teaches.
   Do not ask a question just to make them do something, one with an obvious answer, or one they do not care about:
   that tests them like a student, and over time it annoys them. A rhetorical "you might think..." speaks for the
   viewer and does not count.
6. **One core idea carries one video.** Its most common form is an aha moment (the view shifts and the pieces fall into
   place by themselves). It can also be a tool to take away (a name, a picture and a sentence), a sharpened question,
   or a new way of seeing. If you cannot find one, do not start. The playbook decides which form.
7. **One spine object runs through an act.** Choose one concrete object that can be operated on, cut and deformed, and
   let the whole act turn around it. The subject reference defines what counts as an object (a number line in
   mathematics, a primary text in intellectual history, a data-flow diagram in engineering).
8. **Name after understanding.** Terms, symbols and people's names become tools only after the viewer has grasped the
   thing, and the video says why it has that name. By default the label comes after understanding. A concept episode
   whose goal is use ([teaching/question-types.md](question-types.md)) may give the name earlier as a container, but
   before the name is used it is already filled with concrete content. Metaphors and figurative phrases ("that door",
   "a way out") are names too: first build them on screen with a concrete thing, then reuse them. What carries a whole
   episode is a concrete thing you can see, not a metaphor. The same holds for the author's terms and own words: use
   the author's wording only after the viewer has seen, in this episode, the thing it refers to happen. Never let a
   sentence from the book stand in for acting the thing out.
9. **Rebuild, do not relay: show how we know.** Do not be a second-hand commentator. Every episode does at least one
   passage of the subject's core work step by step on screen. In mathematics it is a derivation (the goal is to make
   the result look almost inevitable, which Grant calls an unsolved expository problem). In biology and medicine it is
   a chain of evidence. In history it keeps "it might not have gone this way". In literature it is close reading. In
   law and medicine it is reasoning through a case. In engineering it is one complete request flow. The subject
   references give the details. **Do not lose the subject itself.**
10. **Hand over something to take away, and show it works elsewhere.** After digging into one case, use it at least
    once, quickly, in another situation, ideally one the viewer did not expect (one deep, several quick). A viewer who
    has seen only one case learns that case, not the idea. What they take away is the episode's
    [takeaway card](#the-takeaway-card).
11. **Narration is written for the picture, the picture is made for the narration, and every element has a job.**
    Every line of narration can point at "this" on screen. Every movement and every element on screen is deliberate
    ("Every movement on the screen should be deliberate"). Jokes, anecdotes and asides too: keep one only if you can
    say which link it makes clearer or more memorable (interesting but irrelevant details make people learn worse).
    When a new example or piece of evidence enters, its first line says what it is there to answer. When you return to
    something from earlier, or from a previous episode, call it back with one sentence and its original picture, in or
    before the line that relies on it: a viewer who cannot follow that line does not wait for the next one to explain
    it. A recap uses the same sentence and the same picture as when it was taught: a new wording in a recap makes the
    viewer think they missed something. A label keeps its meaning in a new example.
12. **Be honest, including about limits and stance.** Say when you simplify, say where an analogy stops working,
    discount legends, state controversies, separate the author's argument from the consensus. For every named idea,
    say **what it is not and where it fails**. When there is a value judgment, let the viewer know where the presenter
    stands. Each field's honesty rules are in its subject reference.
13. **Neither completeness nor clarity is compromised; only how much goes into each episode can change.** Every key
    argument, example, person, number and quotation in this scope (the part the user chose, when they chose only a
    part) has a place on the coverage map, and the video really teaches the "complete" the user expects. Do not drop
    content to be clear, and do not become hard to follow to fit content in. Covering is not equal time: the main line
    gets depth; side lines get one clear sentence and one picture. An item mentioned in one sentence sits in the act it
    serves. An item with no place in this episode goes to the episode that needs it, or to the plan's
    `excluded_topics`; do not pile items into the close just so each has a place. One-sentence mentions are only for
    items the viewer does not reason about: facts, examples, people. A rival view, a piece of evidence or a rebuttal is
    a line the viewer has to follow, even when said in one sentence. When it does not fit this episode, it goes to the
    episode that answers it, or to `excluded_topics` (the user sees them with the plan and can ask for an episode). The
    viewer's level decides how much goes into each episode, and the number of episodes follows. With no sources, only
    a topic, cover the list of learning goals the user gave instead.
14. **Feeling you understand is not learning.** Following smoothly and finding it very clear often has nothing to do
    with real learning, and can even be the opposite (what Grant calls the "Feynman effect"). So the self-check before
    production asks whether the viewer can **use** it: answer a question the video did not directly cover, with what
    the video gave ([the transfer check](#the-transfer-check)). A comment from a viewer who got lost is a real person's
    answer.
15. **One link, one beat; wait for the viewer to finish thinking.** Every link of reasoning (because A, so B; what this
    evidence means; if X, then Y) gets its own beat: give the premise, do it once on screen, then say the conclusion in
    one sentence, the last step included. The premise is best something the viewer already knows, or something this
    episode has already built on screen. When you use an earlier episode's point, rebuild that link on screen; do not
    just say "episode 2 showed it". After the conclusion beat, pause (`pause_duration_seconds`, about 1 to 1.5
    seconds) and keep the conclusion on screen ([teaching/visual.md](visual.md), text). The next new thing waits for
    it. Pace follows difficulty: a turn told at the speed of common knowledge gets skipped, and the viewer has to pause
    or rewatch. Difficulty is how far a link is from what the picture can show. A link the picture shows at once (one
    curve through the planets and the falling apple) can go quickly. A link only words can carry (that two activities
    have become the same kind of knowing, what a method amounts to) gets more room, in a recap and the close too: first
    a concrete case on screen where it happens, then its steps one beat each, then the conclusion. Never ask the viewer
    to accept it in one sentence. So an episode's load is counted in links, and the plan's length is the time those
    links need. When the script is much shorter than the plan, first look for links squeezed into one beat and
    conclusions not said aloud; do not shorten the plan.
16. **At every seam, say two things: what is now established, and why we go on.** A seam is a new scene, a switch to
    another example or place, going on after the main question is answered, a turn in the argument, or leaving the
    picture used so far. At each one the viewer hears what the previous part established (one sentence, the same as the
    conclusion on screen), and which part of the main question the next part answers and why we look at it now.
    - At a turn in the argument, first say what we believe now, then turn, then say the revised claim and pause.
    - When several things that look different are really the same, say so when the second one appears, not at the
      close.
    - When you leave the picture used so far to look at another case, say where we are and what corresponds to what in
      the picture.
    - Say these two sentences aloud: written only on screen, a listener cannot connect them.
    - The main question and the main picture are used from start to finish; never swap them for another card midway.

    **The viewer should know where they are in the big picture, without one more thing added for it.** The big picture
    comes from three things the viewer can already read: the two sentences at each seam; the main-question line (small,
    faint, in the same place for the whole episode); and the presenter's own picture the viewer has already seen
    (Theo's home picture, Fabian's scene and conclusion board, Mason's scoreboard, Sophie's position board, Clio's
    big-picture map, the division-of-labour diagram in Theo's system episodes). At a seam, return to that picture, point
    at where we are and what was just established, and let it leave after the two sentences. While a detail is being
    explained, only that detail and the main-question line are on screen. Never list the names of parts not yet reached
    (an outline bar at the bottom, a table-of-contents strip): the viewer has not seen those parts and cannot read those
    words, so they are one more thing to read, competing with what is being said. This matters most in mathematics and
    derivations.

## The viewer who has seen it and forgotten

This is the most common viewer. Most people who watch explainer videos have met the topic in a popular-science video
or a class, but have forgotten the details. They are not slow; they forgot. Two ways of writing fail them: using the
terms directly (they cannot follow), and starting from zero (they feel treated like children).

Handle each word by its level in the vocabulary in the research notes ([teaching/audience.md](audience.md)):

- **Known (use it directly):** no explanation, no apology.
- **Refresh (heard it, forgot it):** at the moment it is needed, wake it up with **one sentence and one picture**,
  about 3 seconds, then keep going. Example: "Each word first becomes a list of numbers", while a word turns into a row
  of numbers on screen; afterwards you can say "that list of numbers". Those who remember do not feel taught; those who
  forgot catch up just in time.
- **Teach (never learned it):** name after understanding (technique 20 in
  [presenters/theo/craft.md](../presenters/theo/craft.md)): first show on the spine object what it does, then give the
  name.
- **Misconceived (thinks they know it, but has it wrong):** the four steps of
  [handling a misconception](#handling-a-misconception).

Do not:

- Say "Do you remember...?" or "You have probably seen this in such-and-such video." It tests the viewer, and those who
  forgot feel it is their fault. **But "guess first" or "think for a moment about what happens next" is good:** recall
  and guessing as practice, with the answer two or three seconds later, not as a test. A wrong guess itself teaches
  ([guess beats](#guess-beats)).
- Say a paper's names when the viewer does not want the symbols. Put them only as small labels on screen: the original
  plus one line in the narration language (for example "QK circuit: where to look"). The narration
  keeps the viewer's words ("that where-to-look table") and never reads the abbreviation. Note in `design.md` that the
  term is on screen only. When they later read the paper, the label is their bridge.
- Name other channels or videos, unless the user asks. Implementers and viewers of the series are the exception: "this
  needs X first, which episode 2 covered" is efficient.
- Fill in a large block of prerequisites at once (against the just-in-time vocabulary aside, technique 25 in
  [presenters/theo/craft.md](../presenters/theo/craft.md)). Fill each one in when it is needed, one at a time.
- Use overly basic analogies (starting from typing on a phone, or primary-school arithmetic). This viewer needs
  reminders, not first lessons.
- Put two new, unhandled words in one sentence.

## Misconceptions, guesses and takeaways

These hold in every subject.

### Handling a misconception

The input is the plan's `audience.misconceptions` and the words marked misconceived in the research notes. In
`design.md`, write for each one the beat that handles it and how. A series spreads its misconceptions across episodes:
for one that belongs to another episode, note which episode handles it; do not force it into this one.

1. **Say it**, in the viewer's own words: "You might think attention means finding the most relevant word." Best if it
   is an answer the viewer actually chose in the probes.
2. **Grant that it is reasonable:** "That's reasonable. Many popular videos say so, and in some cases it's right."
   Never let anyone feel mocked. In the humanities an intuition is often not wrong, only incomplete.
3. **Let it fail on a concrete case:** act it out on the spine object; do not just say it.
4. **Give the new version**, and go back to say at which step the old idea went wrong and which part of it was right.

For an advanced viewer the four steps can shrink to one or two sentences. When you are unsure whether the viewer holds
the misconception, handle it anyway: those who do not hold it only hear a short confirmation; for those who do, it helps
a lot.

### Guess beats

- **Ask only when the viewer really wants to know at this moment** (principle 5): the question is one they would come up
  with here, and their intuition may be wrong in an interesting way (a misconception in the audience description, the
  opening guess, a counter-intuitive result). Otherwise just tell them, or say it and pause to let them think. Not
  every episode needs one; an episode usually has zero to two. Too many, or too formulaic, and the viewer feels tested
  like a student and treated as stupid.
- **Where a playbook skeleton mentions a guess or a bet, it means "you may ask here"**, not "you must ask". If the
  question fails the previous point, pause instead.
- **Ask like a person talking:** "Do you think it can come up with Frühstück?" Never open with "Bet:", "Guess first:"
  or "Place a bet": those are commands.
- **Use multiple choice only when the options themselves are interesting:** 2 to 4 options, one of them a wrong answer
  many people would choose. Otherwise ask one open question. After asking, **pause 2 to 3 seconds**
  (`pause_duration_seconds: 2.5` on that beat, with the options left on screen), then reveal.
- The best places: just before the first transfer (the viewer's first chance to predict with the new idea), or just
  before a misconception fails (let them bet wrong first).
- The intuition guess from the probes ([teaching/audience.md](audience.md)) is a question the viewer answered and cares
  about. It is often the best opening question.
- When revealing, you can say what the common answer is ("most people pick B"), so those who guessed wrong do not feel
  embarrassed.

### The takeaway card

One per episode, written in `design.md`. Its one-sentence version is the plan's `takeaway`.

- **Name:** short, fits in a sentence (for example "aggregator", "SUB NN17").
- **Standard picture:** one, in the same style throughout. Each later appearance changes only one thing, and an
  animation draws attention to the change.
- **One sentence:** can be quoted word for word.
- **When to take it out:** the phenomenon that should bring it to mind.
- **What it is not:** an example that looks like it but is not (a near miss).
- **Where it fails:** its limits and costs.
- **A question handed to the viewer** (optional).

A mathematical aha or a new view of history gets this card too; some fields (for example the standard picture) can stay
empty.

### Transfer: one deep, several quick

After digging into one spine case, use it at least once, quickly, in another situation: the same standard picture, the
same sentence pattern, only one thing changed. Ideally one comes from a field the viewer did not expect (Christensen:
disk drives → steel → Intel → your life; Bi Dao, a Chinese science creator: self-reference → Escher's drawing hands,
Bach's crab canon, a program that prints itself). In a concept episode whose goal is use, the climax is often the "oh,
this works here too" moment. Put a transfer right after the rule or idea is established, and say what it is testing.
Put after the conclusion, it leaves the viewer wondering why the topic suddenly changed.

### The transfer check

Part of the self-check before production. After writing the script, pick a case that does not appear in the video and
analyse it using only the names, pictures and questions the video gave. If you cannot, the idea has not been handed
over yet: go back and add a transfer, or make the takeaway card clearer. Write the check in `design.md`; it helps when
analysing comments ([teaching/feedback-analysis.md](feedback-analysis.md)).

## Visuals

Visual principles that hold in every style are in [teaching/visual.md](visual.md). The presenter follows them.

## Fixing after an audience review

In an audience review, a fresh subagent (the audience reviewer) plays the plan's viewer and lists problems. The reviewer
lists problems only; never ask it for a score. A model playing a viewer who half understands overestimates how much it
understands: it is good at finding problems and bad at judging quality.

### The script audience review

It comes once the script is written, before any scene code. The reviewer has never seen the script. It reads only the
audience and the script (narration and the written visual descriptions); it needs no pictures. Reading early means its
findings change the script while there is no scene code to redo.

Before it, read the script once yourself as the viewer in the audience description. Is every word handled before it is
used? Does the opening say why they should care? Can they follow the hardest part?

The reviewer goes through the episode as this viewer and lists problems beat by beat, each marked `lost`, `wrong` or
`minor`: words used before they are explained, skipped causal steps, misconceptions from the audience description left
unhandled, sentences that distract or cannot be followed by ear, claims stronger than the evidence, and the rest of the
list its prompt carries. After the whole episode it also sums up (`reviewer_summary`): the question the episode answers,
what it takes away, which terms were explained, where it first got lost (the main line), and the line that most made it
want to keep watching (`most_engaging_beat_id`). Keep that line when fixing; cut elsewhere. Compare the summary with the plan's
`question`, `takeaway` and `taught_terms`; a mismatch is a finding too.

**Fix by cutting and reordering first, not only by adding.**

- Fix the main line and the `lost` and `wrong` findings first.
- `wrong`: correct or soften the original sentence. Do not add a denial somewhere else. A detail that does not affect
  what the viewer takes away may stay, with the correction in the finding's resolution note.
- A side question the reviewer raises ("what about X?"): answer it in the episode that needs it. Do not add it to this
  one.
- The reviewer cannot see how a passage relates to the main question: the passage is usually a detour off the main line.
  Cut it or reduce it to one sentence; do not keep a shortened version.
- Where the reviewer thought something wrong, fix it starting from what it thought at that moment.
- `minor`: fix only by deleting words or moving words already in the script. Add no sentence, and do not replace a
  sentence with a new one (a new summary is also a new sentence). If it cannot be fixed that way, keep it
  (`action: kept`). This is for wording and polish. A finding that says the reasoning is missing something is a
  missing link, however it is marked: a premise the viewer was never given, what a piece of evidence is there to
  answer, a reminder, or one case of what a claim means, worked on what the episode already shows. Fix it as the next
  item says, with its own beat. Never keep it because a `minor` fix may not add a sentence.
- The reviewer got lost, or a link was missing: give the missing link its own beat (say the premise or the conclusion,
  then pause). Do not squeeze it into the existing sentence. A missing reminder of something earlier goes before the
  line that relies on it, not after (principle 11). Do not answer it with a denial, an abstract summary or a new
  example: viewers' comments on finished videos land mostly on lines fixed that way. The script may grow, as long as
  it stays within the plan's length.
- Give every finding a resolution: `fixed`, or `kept` with the reason. Keep earlier rounds.

**Read again until the main line holds, at most twice.** The first round reads the whole episode. After fixing where
the reviewer got lost, another fresh audience reviewer reads only those scenes again, until it can say what each scene
answers and no longer gets lost there: at most two more rounds. A scene added or heavily changed later is also read
before narration. `narrate` refuses until every scene has been read and every scene lost in its latest read has been
read again, or the rules below settle it.

**Lost twice in the same place: rewording does not help.** Write that step as sentences the viewer could repeat back
(premise, prediction, what we see, conclusion). Find the missing sentence, or a word that points at two different
things, and give the missing sentence its own line. If the chain is longer than the viewer's capacity, switch to a more
direct piece of evidence. If a derivation is longer than their capacity, say what the result looks like and confirm
it with one number or one picture instead ([teaching/plan.md](plan.md), links).

**Reviews always stop; when they stop, move on.**

- Count losses per step of the episode, not per scene name: a scene you split or renamed is still the same step. The
  gate counts per scene id, so a renamed scene starts again from zero; never rename a scene to escape the count.
- Lost twice at the same step: write it a different way, as above (confirm the result with one number or picture, cut
  the detour, give each missing link its own beat). Record in `decisions.md` what the plan's outline says, what the
  script now does and why. Then read it again.
- Three rounds in one episode (the whole episode once, then two rounds on the scenes where reviewers got lost): every
  scene is settled. A scene added afterwards and never read is still read. A round costs about $1.
- The user is told, after delivery, about every scene where reviewers were still getting lost when it was settled.
- Reviewers often contradict each other (one wants the derivation, the next finds it too crowded). Fix toward what most
  reviewers ask for, or let the scene settle by the rules above. It is not a question for the user.

## Common failures

When one appears, go back and fix it.

- Opening with a definition, a timeline, background or a biography.
- The picture turns into slides: bullet points, a full-screen quotation, a photo slowly zooming in.
- Colour used as decoration; the same concept in different colours; more than 3 accent colours in one frame.
- The questioner replaces the derivation. The questioner may ask, react and voice a wrong guess, but the narration and
  the picture complete the derivation.
- Only the correct version is made clear, and the wrong ideas in the viewer's head are never handled; the viewer is
  never asked to guess or judge anything from start to finish.
- The whole video has one case: the viewer learns that case, not the idea.
- No passage of real subject content is completed on screen; satisfaction replaces understanding (the "Feynman
  effect").
- A promised preview is never delivered; a set-up is never paid off.
- Claiming a scene is done without looking at its rendered frames.

Each presenter's playbooks and each subject reference list their own failures (for example, Theo on the history of
ideas: too many people, judging the past by the present, philosophy with no object).
