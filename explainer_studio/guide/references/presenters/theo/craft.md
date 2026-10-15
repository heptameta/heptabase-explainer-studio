# Theo's script craft

Contents: [A. Targets while writing](#a-targets-while-writing) · [B. 38 script techniques](#b-38-script-techniques) ·
[C. Principles Grant has stated](#c-principles-grant-has-stated) ·
[D. Writing procedure (12 steps)](#d-writing-procedure-12-steps) · [E. Self-check](#e-self-check)

Basis: close study of 3Blue1Brown's public videos, plus the principles Grant Sanderson has talked about in
public. The example lines are our own, written to show what a technique sounds like; write the episode's own lines.

---

## A. Targets while writing

3b1b's measurements (speaking rate, length, sentence length, density of "you", number of questions, number of key
points, number of recaps, how often a joke comes, when the first question appears) are in the style
([style.md](style.md#measurements)). Converted into targets for the narration language (for example the speaking rate
and the length of one sentence), they are in the language reference (`languages/<language>.md`). **These
numbers are style.** Another style can have completely different numbers.

Targets that do not depend on style or language (per episode):

- Every misconception in the audience description has a place
  ([teaching/rules.md](../../teaching/rules.md#handling-a-misconception)).
- A question to the viewer is asked only where they would really want to ask it at that moment
  ([teaching/rules.md](../../teaching/rules.md#guess-beats)). When you ask, really stop, then reveal.
- At least one transfer: the core idea used in a second situation
  ([teaching/rules.md](../../teaching/rules.md#transfer-one-deep-several-quick)).
- Recaps: in a long video, one between each act (as a causal chain, or as another walk over the standard picture).

Long-video targets with the blackboard style (15 minutes or more):

- Questions to the viewer: mostly embedded "you might be thinking…", voicing the doubt in their head. The viewer stops
  and really answers only where they would really want to know the answer.
- Key-point labels: at most 3.
- Causal recap: one between each act.
- Humour: a low-key joke every 3 to 5 minutes, growing out of the sources themselves, never in the middle of an
  argument.
- The first question appears within 60 seconds; the foil is finished within 3 minutes.

Those are the targets for a long video (15 minutes or more). For a short video of 6 minutes or less: the first question
within 10 seconds, the foil within 30 seconds, at least 2 questions to the viewer, 1 key-point label, no recaps between
acts (the skeleton is in each playbook's short version).

**What humour is** (in any style): a joke can be the argument itself (an absurd case, irony, a recurring fictional
character), but for every joke you can say which point it makes clearer or easier to remember. How often and how loud
is the style's decision.

---

## B. 38 script techniques

Grouped by what they do.

### I. Motivation

1. **The confession hook:** "For years I could say why ice floats without actually understanding it." Suits a topic
   that everyone thinks they understand.
2. **The concrete input and output hook:** "A drop of ink in a still glass of water; an hour later the whole glass is
   blue, and nobody stirred it." Suits a surprising phenomenon.
3. **State the standard account fairly, then prosecute it:** "None of this is false, but none of it says why"; or:
   "It works, and that is what is unsatisfying." Use it when the viewer already has a ready-made explanation in their
   head. The foil itself counts as content. The other kind of foil is **the viewer's own wrong intuition**, which is
   stronger evidence ([teaching/rules.md](../../teaching/rules.md#handling-a-misconception)). Business, social and
   humanities topics often have no textbook account, only the common sense in everyone's head; use that kind there.

   3a. **Shake the viewer's belief about themselves:** "You are sure you would notice if one of your memories were
   false. Would you?" It attacks not a textbook but an assumption in the viewer's head.
4. **A volley of questions:** 3 to 4 questions, escalating step by step, landing on "Is this a coincidence or a
   necessity?"
5. **State the standard for the explanation:** "By the end, I want this rule to feel like something you could have
   worked out yourself." Say it once in the whole video, near the start.
6. **The sceptic as client:** the π video makes the friend from the Wigner anecdote its "client", who comes back at
   the start, in the middle and at the end to check the progress. Suits a "why" chased layer by layer.
7. **A strange promised preview:** "Later, this will explain why the shower turns cold when someone flushes; stay with
   me", paid off later in the video. One per video.
8. **Behaviour first, mechanism after:** first show what attention "does", then how it is computed.
9. **Stakes before abstraction ("who cares?"):** Newton's fractal first talks about fonts and Pixar; Monster first talks
   about symmetry. **The stakes must be in the viewer's own world.** The detail in the sources that excites the author
   most (for example a strange bug in a paper) is often "so what does this have to do with me" for the viewer. The
   opening first answers why the viewer should care, then comes the detail.

### II. Order and concreteness

10. **Restate the question:** "Why do colds spread more in winter?" → "What changes in winter that lets a virus pass
    from one person to the next more easily?" (picture: the old question turns grey → the new question). Write both
    versions.
11. **A toy model with stated assumptions:** "This town of 100 people is made up, to keep the numbers small"; "For
    now, pretend there is no friction." Pair it with technique 34.
12. **Exaggerate, then take the limit:** interest paid once a year → twice a year at half the rate → every instant: the
    limit is continuous growth.
13. **Numbers before symbols** (the STEM version; in general "the concrete case before abstract symbols or terms", for
    example in the humanities read a concrete passage before discussing the concept; details in
    [subjects/mathematics.md](../../subjects/mathematics.md)): a loan of 1,000 at 5% before the formula; ten coin flips
    before n; a real table's three rows before a matrix.
14. **Show or simulate first, derive after:** "Before any formula, let's just run it and watch."
15. **Read a formula term by term, then push it to the extremes** (mathematics and STEM; in general "take the core rule
    apart term by term, then test extreme cases"; details in [subjects/mathematics.md](../../subjects/mathematics.md)):
    in the pull between two masses, the top grows with either mass; the bottom: twice as far, a quarter of the pull;
    and when one mass is tiny, or the two are very far apart…
16. **The cousin problem (and admit it is a trick)** (the example is mathematics, but "solve a related problem first,
    then come back" works in any subject): the π video suddenly jumps to two dimensions, admits the jump looks
    arbitrary, and only near the end explains why it was necessary.
17. **The same logic in another field:** "The rule doesn't care whether the things are atoms, people or packets"; the
    averaging that blurs an image also smooths a noisy price chart.
18. **A ladder of characters:** a character living in two dimensions and one living in three make a ladder: "by the
    end, you'll see this the way she does."
19. **A thread through the series:** a timeline of what is known gains one entry in every episode, reaching the
    present in the last.

### III. Naming

20. **Name after understanding:** "This is called the half-life" comes after watching the pile halve twice;
    "opportunity cost" comes after the viewer has felt the choice.
21. **Explain the name, pay it off later:** the opening asks "Why is it called the greenhouse effect, when a greenhouse
    works differently?", and a later episode answers it.
22. **The picture first, the paper's formula after** (STEM; in general "the intuitive presentation first, the formal
    statement after"): draw the two populations rising and falling completely, then show the paper's pair of
    equations.
23. **Flag non-standard notation or terms, and align with the literature:** "I'll call this the gap; most textbooks
    call it the spread"; "Careful: the paper uses the same letter for two things."
24. **Wink at the jargon:** "Despite the grand name, it's a weighted average"; "Economists call this elasticity, a
    stretchy word for a simple ratio."
25. **The just-in-time vocabulary aside:** add a term only when it is needed (amplitude, angular frequency), instead of
    a big block of "prerequisites" at the start.

### IV. Pacing

26. **Key-point labels:** at most 3 per video, and only for ideas the episode has already shown to matter. Each label
    says its idea in concrete words the viewer can repeat ("Key idea two: a vaccine trains the body on a harmless
    copy"), never the number alone. Say how many there are at the first one, and at each later one recall the earlier
    ones in a phrase: minutes apart, "the second key idea" alone leaves the viewer wondering what the first was. The
    same goes for any numbered set (three escapes, two rules): say how many and what each one is, and keep them on
    screen as a list that fills in.
27. **The step-back causal recap:** "So far we know: … because … so … What's still missing is …". Recap the
    because-chain, not a list of topics.
28. **Compress into one slogan first, then apply it:** first say "the price is where the two lines cross", then apply
    it case by case. The slogan names the concrete things it compresses (the two lines, the price). A line that works
    only by wordplay, with nothing in it the viewer could point at ("it's not about speed, it's about rhythm"), sounds
    like a summary and says nothing: say the concrete version, rhythm and parallels included.
29. **Milestones and reassurance:** "If you stop here, you already have the main idea"; "The next part trips most
    people up; that's normal."
30. **The contract:** the roadmap is presented as a promise; a deferred payoff says "I'll explain in a moment"; skipping
    is allowed ("you can jump straight to…", "if the edge case doesn't interest you, skip ahead"). **Every promise is
    kept.**

**The close holds only five things:** the recap, one sentence on limits, the punchline, the reframe and the hand-off.
New facts, examples and names go into the act they serve, or into the next episode. How to write a recap: principle 11
in [teaching/rules.md](../../teaching/rules.md#principles-every-presenter-follows).

**Pace preferences apply only to what the viewer already understands.** When the audience description says the viewer
likes "one sentence and move on" and a fast pace, that means reminding them of old words and passing quickly over what
they already know. A step of reasoning (why X leads to Y) is never passed over in one sentence: before using it to
predict or to conclude, say the reason, ideally acting it out once on the spine object.

### V. Honesty

31. **Name the omission:** "I'm leaving out air resistance: it matters for a feather, not for a stone"; "To keep
    focus, set taxes aside for now."
32. **Correct yourself on the spot:** "Actually, that's not quite right."; "Well, mostly."
33. **The imagined student with a raised hand → an honest referral:** "Some of you are wondering what happens at the
    edges. The full answer is long; the book's appendix has it."
34. **Interrogate your own toy model:** "You might fairly ask whether a town of 100 people tells us anything about a
    country of millions."
35. **Admit uncertainty and open questions:** "Nobody knows yet why…; here is what we do know"; an honest account of
    where research stands.

### VI. Talking with the viewer

36. **Voice the viewer's objection, boredom or guess:** "You might be thinking: fine, so it all comes down to supply
    and demand."; "A reasonable first guess might be…"
37. **Layered invitations:** "If you've done some algebra, try finishing this line yourself"; "Take a second to check
    this"; "For the curious".

### VII. Analogies and representations

38. **Give the analogy, then correct it:** the heart as a pump → "A better picture is actually two pumps side by side";
    the common picture of electricity as water in pipes explains the current but misleads about where the energy
    travels. **Say where every analogy fails.**

Related devices:

- **When the picture gets crowded, change the representation:** turn a 2D vector field into colour on the wave crests
  only; switch to phasors; look at the same matrix multiplication first by rows, then by columns.
- **Physical evidence:** the Millennium Bridge, calcite, the helical antenna: "And this really happens."
- **Analogy with a familiar abstraction:** "An average is to a list of numbers as a centre of mass is to a set of
  weights."

### VIII. Closing

- **The causal-chain punchline:** "So this is the real reason ___", plus a claim of inevitability.
- **A reframing reflection:** what looked like a detail turns out to be the whole story; the question we started with
  was not quite the right one, and here is the better one; an old idea still hides questions nobody has asked yet.
- The punchline and the reframe name the episode's concrete things: the objects, numbers and people the viewer saw.
  "The question was never X but Y" says nothing until Y is something the viewer has watched happen.
- **Structural rhyme:** close with a challenge problem of your own, echoing a challenge from the story the video
  told.
- **The hand-off:** preview the next chapter; split one step off into another video.
- **Thanks inside the narration:** the sources, the people who helped and the viewers who asked questions are named in
  the body.
- People entering, legends, anachronism, "imagine you lived then", explaining why the textbook looks the way it does:
  see [question-types/conceptual-change.md](question-types/conceptual-change.md#people-and-the-historians-techniques).

### IX. Tone

- Second person dominates; "you and I", "together" as company.
- Long cumulative sentences with short punches between them ("Strange." "But true."). A short punch follows a concrete
  sentence; it never stands in for the conclusion.
- A moderate amount of softeners ("a little", "to some extent").
- Signposts that tell the viewer where they are: what this part is for, a step back to the whole picture, what is set
  aside for now, a short wrap-up before moving on.
- Wonder is earned before it is said.
- Humility: admit what confused you too, and do not claim a framing as your own invention.
- **Avoid "obviously", "clearly", "it is easy to see"** (Grant explicitly opposes them).

---

## C. Principles Grant has stated

- **Audience:** be empathetic to beginners and explain the jargon. There is no "good explanation for the general
  public": target a specific audience. His model of the audience is himself before he understood. Do not dilute:
  people want to learn. You should know ten times more than you say.
- **Motivation:** within 30 seconds people know why they should care. Do not open with big philosophy; leave the big
  theme for the end. Every formula should put into symbols something already in the viewer's head. Start from a
  naive, flawed attempt and correct it step by step, showing the wrong turns. No aha, no start. Mathematics is like a
  detective novel. Tension and release, like a tritone resolving to a fifth. Axiomatic textbooks leave out the
  question that motivated each idea.
- **Concreteness and order:** from concrete to abstract (his own first drafts are often the other way round). Levels of
  abstraction: give an example from one level down. Put one or two examples at the centre and play with them
  repeatedly. Never open with a definition; the best teaching order often differs from the logical order. Say what
  else the definition could have been. A proof should feel rediscoverable.
- **Process:** script first, Manim is only a tool for making the pieces; yet he often writes while animating, and the
  animating is part of the writing. Choosing the topic and angle takes 1% of the time but decides most of the
  value; test them with sample lessons. First walk through the unintuitive derivation yourself, then ask where it can
  be visualized. Cut a script that is not engaging enough. Questions from early Patreon viewers are written into the
  final version.
- **Rigour and honesty:** rigour is a Midas curse, so keep a separate teaching checklist: every definition has a
  motivating example, proofs are rediscoverable, there is a personal voice, there are pictures, the concrete comes
  first. Be honest where you hand-wave. Beware the "Feynman effect": enjoying the explanation is not long-term
  learning. A proof that shows why something is true is worth more than one you can only check.
- **History:** Grant's views on history and "discovery fiction" are in
  [question-types/conceptual-change.md](question-types/conceptual-change.md#grant-on-history).

---

## D. Writing procedure (12 steps)

0. **Audience and standard:** write three sentences: who the viewer is; what they believe now (the standard account,
   and the misconceptions in the audience description); what must "feel discovered or forced" by the end, and what the
   viewer takes away ([the takeaway card](../../teaching/rules.md#the-takeaway-card)).
1. **Main question:** write it as the why or how a smart layperson would ask. Write both the naive version and the
   restated one.
2. **Foil:** state the standard account fairly in 60 to 150 seconds, then list 3 or 4 questions that show it "falls
   out of the sky".
3. **Spine object:** choose one concrete object or toy, and write down its assumptions.
4. **Work the causal chain backwards:** from the punchline ("so this is the real reason…") list every "because" link
   back to the start. That gives 3 to 5 acts. Mark the first key point.
5. **Order each act by desire:** a question, or an objection voiced for the viewer → exploration on the spine object
   (show or simulate) → naming → generalization → interpretation and testing of extreme cases.
6. **Place the contract:** the roadmap promise (with one strange preview), a causal recap between acts, a milestone
   after the hardest act, a pointer with every deferral. Finally check that every promise is kept.

   6a. **Misconceptions, guesses, transfer:** place each misconception from the audience description in the script
   ([handling a misconception](../../teaching/rules.md#handling-a-misconception)). Look for a place where the viewer
   would really want to ask at that moment; ask only if there is one
   ([guess beats](../../teaching/rules.md#guess-beats), ideally before the first transfer). Write the takeaway card and
   plan the transfer ([the takeaway card](../../teaching/rules.md#the-takeaway-card),
   [transfer](../../teaching/rules.md#transfer-one-deep-several-quick)).
7. **Honesty check:** every simplification has a named omission or a self-correction; the toy is interrogated; the
   unknowns are marked; every named idea says what it is not and where it fails. Add the honesty rules of the subject
   guide in use (for example, the history of ideas: discount legends, warn about anachronism, separate the author's
   argument from the consensus).
8. **Analogy check:** for each analogy, write where it is right, where it breaks and a better alternative.
9. **Write the narration for the picture:** every passage directs the viewer's eye; a colour convention is announced
   only once; every change of representation has a reason; cut pure description.

   **Term check:** list every technical term in the narration (abbreviations and symbol names included), grade it by
   the vocabulary in the research notes, and write in `design.md` where it first appears and which sentence and which
   picture make the viewer understand it. A term the vocabulary does not list counts as one to teach. If a term appears
   before it is handled, rewrite that sentence. How to handle each grade:
   [the viewer who has seen it and forgotten](../../teaching/rules.md#the-viewer-who-has-seen-it-and-forgotten). The
   script audience reviewer flags any of the plan's unfamiliar terms used before it is explained.
10. **Close:** hand over the thing the viewer takes away: a causal punchline, a reframing reflection, a structural
    rhyme, a question handed to the viewer, or a list of at most three items, each verified in the video (the playbook
    decides the default); the hand-off; worthwhile notes; thanks.
11. **Read aloud:** read it at the language reference's target rate. If the causal chain has more than 5 links, split
    the episode.
12. **Reviewer feedback:** turn the reviewer's confusion into an objection voiced for the viewer, or leave it for a Q&A
    follow-up episode (ordered by how much prior knowledge it needs). The fixing rules for the script audience review
    are in [teaching/rules.md](../../teaching/rules.md#the-script-audience-review).

---

## E. Self-check

Tick every item after writing each episode.

**Viewer** (adjust to the level in the audience description: the recaps, analogies and milestones a beginner needs are
a burden to an expert; keep the expert version short)

- [ ] Every misconception in the audience description has a place in the script, handled with the four steps of
      [handling a misconception](../../teaching/rules.md#handling-a-misconception)?
- [ ] Is every question to the viewer one they would really want to ask at that point? No asking for the sake of
      asking, no "place your bet first"?
- [ ] The core idea is used in a second situation at least once? The takeaway card is written?
- [ ] Transfer check: using only the names, pictures and questions the video gives, can a case not in the video be
      analysed correctly?
- [ ] For every joke, anecdote and aside, can you say which link it serves?

**Motivation**

- [ ] Within the first 30 seconds the opening answers why the viewer should care, with something from their own world?
- [ ] Can the main question be said in one sentence?
- [ ] Is the question felt before any answer?
- [ ] Is the standard for the explanation stated?
- [ ] Is there a sceptic or client, and does he come back?

**Order**

- [ ] Term check done: before its first appearance, every technical term was handled according to its grade in the
      viewer's vocabulary (the term list in `design.md` is complete)?
- [ ] There is a spine object, and its assumptions are stated?
- [ ] Every claim is first shown on a concrete case (real numbers, objects or text)?
- [ ] For every inference ("if X, we will see Y"), was its reason given before it is used, rather than skimmed in one
      sentence because of a pace preference?
- [ ] Every name comes after understanding, with its reason?
- [ ] Every formula or core rule is read term by term and tested at the extremes? (The mathematics guide asks for more.)
- [ ] Every derivation is preceded by a demonstration?

**Structure**

- [ ] 3 to 5 acts, each opened by a question?
- [ ] At most 3 key-point labels, each saying its idea in concrete words, the first saying how many?
- [ ] Every recap, slogan, label and the close, heard alone, names something concrete the viewer could repeat?
- [ ] The recaps are causal?
- [ ] Every promise is listed and kept?
- [ ] A milestone after the hardest part?
- [ ] At least one set-up paid off?

**Honesty**

- [ ] Every simplification is flagged?
- [ ] The toy model is interrogated?
- [ ] The unknowns are marked?
- [ ] The limits of each analogy are said?
- [ ] The honesty items of the subject reference in use are all met? (For example, the history of ideas: legends
      discounted, anachronism warned about, argument and consensus separated, sources thanked aloud.)

**Conversation**

- [ ] The number of questions fits the style (blackboard: at least 6 per 20 minutes)?
- [ ] Skipped proofs are offered as layered exercises?
- [ ] Second person dominates?

**Picture**

- [ ] Is the eye guided?
- [ ] Is the colour convention announced and kept?
- [ ] Does every change of representation have a reason?
- [ ] Are rendering artefacts explained?

**Tone**

- [ ] Long sentences mixed with short ones?
- [ ] Humour fits the style (blackboard: low-key humour every 3 to 5 minutes, never in the middle of an argument)?
- [ ] Wonder is earned before it is said?
- [ ] The jargon is demystified?
- [ ] Can it be read at the language reference's target rate?

**Close**

- [ ] It hands over something to take away, not a topic-list summary? (Explain a mechanism: a reframe, not a summary?)
- [ ] There is a clear hand-off?

**Coverage**

- [ ] Every item on the coverage map appears in the script, at the depth the map gives it?
