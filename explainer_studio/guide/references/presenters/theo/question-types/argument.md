# Theo's argument playbook: Test an argument

Contents: [Skeleton](#skeleton) ·
[Short version](#short-version-6-minutes-or-less-or-a-short-passage-inside-another-episode) ·
[When the goal is far from the viewer](#when-the-goal-is-far-from-the-viewer) ·
[Keeping the viewer with the argument](#keeping-the-viewer-with-the-argument) ·
[Working with the paper](#working-with-the-paper) · [Self-check](#self-check)

**The question it answers:** argument, "Why should we believe this claim?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can state the claim, the
strongest evidence and the strongest objection, and judge its credibility themselves.

**How it meets the must-haves:** the claim is first built on one concrete example, saying clearly what it asserts and
what it does not (the core idea). The naive approach is one of the strongest rivals: state it fairly in full, then show
where it fails. Each piece of evidence is read until the viewer understands what it supports. The limits and what is
still unknown are never left out.

**Use it for:** empirical and technical claims: the finding of a study, the core argument of a book. For example
explaining a machine learning paper to engineers who have not read it, or a researcher presenting their results to
colleagues in another field.

**Not this one:** when what the viewer really wants is "how does this new method work", the main question is mechanism
([mechanism.md](mechanism.md)) and the evidence is only a short passage. Several views side by side with no verdict
for the viewer is perspectives, which Theo has no playbook for ([presenter.md](../presenter.md)). A page-by-page guided
reading of a whole paper is not a video; neither is a news-style summary that reports results without the idea.

When a paper has several core ideas, the plan arranges them as several questions
([teaching/plan.md](../../../teaching/plan.md#planning-how-many-episodes-each-answering-what)); one episode covers only
one.

Basis: Simon Peyton Jones, "How to give a great research talk" (one idea per video, the example before the
generalization, no literature review, motivate with a question); 3Blue1Brown's GPT and Transformer series (behaviour
first, then the mechanism, finally the evidence); the "phenomenon first, mechanism after" structure common in research
explainer channels.

---

**Versus other presenters' argument playbooks:** Fabian tests causal accounts of how actors behave that apply to
many cases, and his evidence is outcomes that really happened. Sophie tests normative and interpretive claims, and her
evidence is judgments of cases and original texts. Mason tests claims about how something buildable behaves: the claim
and its rival each run once on a small toy. A dispute about the causes of one event goes to Clio
([presenters/clio/question-types/argument.md](../../clio/question-types/argument.md)). Theo fits claims whose evidence
must be read and understood (data, experiments, a study's figures). When a technical claim would also show the same
direction on a small toy, decide by the presenter probe ([presenters/README.md](../../README.md)).

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | Phenomenon or question | The first 5 seconds give something concrete the viewer wants answered: a surprising result, a question that looks simple yet nobody can answer, the paper's most representative figure. Not a title card of the paper. **It must mean something to the viewer**, not only be interesting to researchers: keep the paper's odd details until the viewer understands |
| 8–18% | Why it matters | Whom this problem blocks, what solving it makes possible, what it has to do with the viewer. In the viewer's language, not the field's jargon |
| 18–30% | The naive approach and why it is not enough | The approach the viewer would think of (the foil), stated fairly in full, then where it fails. This step makes the core idea "have to appear" |
| 30–65% | The core idea, on one concrete example | The paper's key insight, shown step by step on a spine object that can be operated on; example first, generalization after, the paper's formal notation last. This is the centre of the video |
| 65–82% | Evidence | The paper's one or two most important experiments or figures: first say "if the idea is right, what should we see", then give the paper's figure (text as object: whole first, then a box around the part, then extract it), read item by item |
| 82–92% | Limits and what is still unknown | What the paper does not claim, the limits of the experimental conditions, the gaps the authors admit, the controversy in the field. This is the honesty floor of a research explainer and can never be left out |
| 92–100% | Close | A one-sentence takeaway (a reframe, not a summary); which section of the paper to read to go deeper |

## Short version (6 minutes or less, or a short passage inside another episode)

| Share | Section |
|---|---|
| 0–8% | Phenomenon or question (a surprising result or a representative figure) |
| 8–20% | Why it matters + why the naive approach is not enough (together, at most 45 seconds) |
| 20–70% | The core idea, on one concrete example |
| 70–85% | One key piece of evidence (one figure, read item by item) |
| 85–100% | One sentence of limits + one sentence of takeaway |

Word count from the language reference's speaking rate.

## When the goal is far from the viewer

When the viewer needs many terms filled in and the goal is to understand the paper's formulas, the load exceeds their
capacity. The plan splits it by prerequisites
([teaching/plan.md](../../../teaching/plan.md#planning-how-many-episodes-each-answering-what)). A common split: first an
episode without formulas that tells the core finding as a complete story, which stands on its own; the next episode
takes those who want more through the paper's figures and equations.

## Keeping the viewer with the argument

An argument is one line: claim → the rival account → one or two pieces of evidence → limits. A viewer who gets lost
nearly always does so because two lines are running at once, or because a step has no reason.

- **The guess asks exactly the claim this episode tests.** The guess, the title, every piece of evidence and the close
  answer the same question. Do not have the viewer guess one question ("Why did this happen so late?") and then test
  another with the evidence ("Did this happen only once?"). The closing reframe may sharpen the question; it may not
  say "the question was not really the one you guessed".
- **The guess's options must be distinct.** Each option names a different cause. When two options share a key word
  (for example one says "resources increased" and another says "resources ran short"), say clearly how they differ
  before the guess, or the viewer will think it is the same answer reworded.
- **The rival answers the same question.** It is another answer to this episode's claim (the claim says "one source";
  the rival says "many sources"). When the rival named in the sources answers a different question, choose another
  rival, or keep it for the episode that answers that question. Check this especially after a question was split.
- **Tell only one version of the rival's account,** matching what the guess card says, with its time and conditions
  clear. Then say "let's test it by its own prediction". Do not say "we won't refute it" and then knock it down at once.
- **Before every "if X, we should see Y", act out why X leads to Y,** ideally once each with one concrete example on
  the spine object. The reason may not wait until the close.
- **Only the one or two strongest pieces of evidence.** Each one, once told, first answers the question it opened with
  (a new piece of evidence says in its first line what it is there to answer; principle 11 in
  [teaching/rules.md](../../../teaching/rules.md#principles-every-presenter-follows)), with no other topic inserted in
  the middle (for example stopping halfway to explain who another character is). Other evidence and rebuttals go to
  the episode that needs them; what has no place gets one sentence, for completeness.
- **Answer the strongest objection only once,** with the single most powerful reason, saying clearly why it holds the
  objection off. Do not first give weaker reasons and then say "this only shows it is unlikely". Rivals already handled,
  or another kind of "defeat", do not appear here either: the viewer would think there are several answers and could
  not tell which one holds. When the sources list several reasons, pick the strongest; put the others, for
  completeness, where they serve, or in the plan's `excluded_topics`.
- **Put the transfer where the rule has just been established:** try the new rule once on a new example, or make it a
  guess the viewer judges themselves. No new example after the conclusion and before the close.
- **What the opening asks, this episode answers.** When the opening "why" takes several episodes to answer, this
  episode first gives the skeleton of the answer (one sentence and one picture), saying which later episodes prove
  which part. A viewer who finishes an episode must not hold only an IOU. The skeleton comes after this episode's
  conclusion: first say which opening question it answers ("The why we started with: the author's answer is…"), then
  whose answer it is and that it is not proven yet. Otherwise it sounds like another topic, or like something already
  proven.
- **The close hands off only one thing:** say the one question the next episode answers. Several "later" previews at
  the end leave the viewer holding several IOUs.
- **The script's steps follow the plan's outline.** One outline step is one step in the script; no new sub-argument
  grows under a step. To add one, change the plan's outline first and record why in `decisions.md`
  ([teaching/plan.md](../../../teaching/plan.md#when-the-script-departs-from-the-plan)).

## Working with the paper

- **Rebuild; do not guide through it in order.** The paper's section order serves peer review, not understanding.
  Reorder it by the skeleton above.
- **Keep three kinds of statement apart:** what the paper claims ("the authors found…"), what the paper has evidence
  for, and your interpretation or simplification ("another way to think about it…"). The narration lets the viewer
  hear the difference.
- **Check every number and conclusion against the original,** citing down to the section, figure or page (for example
  §3.2, Fig. 4, p. 12) in the beat's `citation`.
- **The paper's figures** can be quoted directly (crop them with `explainer-studio asset pdf crop`), with the source
  marked on screen. When the figure needs animating, redraw it with the engine and say it is redrawn from the original.

## Self-check

- [ ] The opening phenomenon means something to the viewer, and why they should care is said within 30 seconds?
- [ ] The whole video covers only one core idea, and it can be said in one sentence?
- [ ] The naive approach is stated in full and shown to be not enough before the core idea appears?
- [ ] The core idea is shown on a concrete example before the paper's formal notation?
- [ ] At least one key experiment or figure is read item by item, after saying "if the idea is right, what we should
      see"?
- [ ] There is a passage on limits and what is still unknown?
- [ ] The title, the evidence and the close (and the question put to the viewer, if any) answer the same question? The
      rival's account has only one version?
- [ ] For every "if X, we should see Y", was the reason acted out before the prediction? Only one or two pieces of
      evidence, each opening by saying which question it answers?
- [ ] The strongest objection is answered with one reason only? The transfer comes right where the rule is
      established? The opening "why" has an answer, or the skeleton of one, in this episode? The close has no new facts,
      examples or names?
- [ ] Every number, conclusion and quoted figure cites the paper (section, figure, page) and was checked against the
      original?
