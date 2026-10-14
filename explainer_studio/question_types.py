"""The nine question types an episode can answer.

This is the source of truth: `plan validate` checks `question_type` against it, the script audience review prompt
uses each type's outcome and must-haves, and the guide's `references/teaching/question-types.md` table is generated
from it by `scripts/release.py`. A question type defines only what the viewer can do afterwards and what the episode
must contain; how to teach it is each presenter's playbook.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionType:
    name: str
    display_name: str
    question: str
    outcome: str
    must_haves: str


QUESTION_TYPE_BY_NAME_MAP: dict[str, QuestionType] = {
    question_type.name: question_type
    for question_type in [
        QuestionType(
            "mechanism", "Mechanism", "Why does this happen? How does it work?",
            "Explain the causal chain in their own words and predict what changes when one condition changes.",
            "Every link of the causal chain is visible, with no skipped link; at least once the viewer predicts "
            "what happens when one condition changes."),
        QuestionType(
            "proof", "Proof", "Why must this be true?",
            "State the key idea of the proof and follow each step, confirming that it holds.",
            "The claim is first made clear with examples; the key idea is stated on its own; every step says why "
            "it is allowed; the episode says what the result buys us."),
        QuestionType(
            "concept", "Concept", "What is it, and how does it differ from things that look like it?",
            "Tell examples from non-examples and produce an example of their own.",
            "At least two examples and one close non-example; the definition comes out of their difference; one "
            "boundary case the viewer judges for themselves."),
        QuestionType(
            "system", "System", "How do the parts of this system work together?",
            "Given any part, say what it is responsible for and what a change to it would affect.",
            "The whole picture comes first; one concrete thing is followed through every part; the episode says "
            "what changing one part would affect."),
        QuestionType(
            "procedure", "Procedure", "How is it done?",
            "Do it once on their own in a new situation.",
            "One complete run; the judgment at each step is said out loud; a second run in a different situation; "
            "the common mistakes."),
        QuestionType(
            "narrative", "Narrative", "What happened, and why did it happen that way?",
            "Tell the main line, the turning points and their causes, and where things could have gone otherwise.",
            "One main-line question; every turning point has its cause; the places where it could have gone "
            "otherwise are pointed out."),
        QuestionType(
            "conceptual-change", "Conceptual change",
            "How did people come to think this way, and where did the old idea fall short?",
            "Say why the old idea was reasonable, where it broke down, and what the new idea gains and costs.",
            "The old idea is presented as reasonable; where it breaks down is concrete; the cost of the new idea "
            "is stated too."),
        QuestionType(
            "argument", "Argument", "Why should we believe this claim?",
            "State the claim, the strongest evidence and the strongest objection, and judge its credibility "
            "themselves.",
            "The claim says clearly what it does and does not assert; each piece of evidence says what it "
            "supports; the strongest objection is presented; what is still unknown is said."),
        QuestionType(
            "perspectives", "Perspectives", "On an open question, what are the views, and what does each rest on?",
            "State the strongest version of each position and its cost, and know where they stand and why.",
            "Each position in its strongest version; the same case tests all of them; no verdict for the viewer "
            "(a presenter who holds a position says so)."),
    ]
}

# A concept episode can instead aim for the viewer to *use* a named thinking tool on new situations
# (plan: `concept_goal: use`). It replaces the concept row's outcome and must-haves.
CONCEPT_GOAL_BY_NAME_MAP: dict[str, QuestionType] = {
    "use": QuestionType(
        "use", "Concept (use)", "What is it, and how do I apply it?",
        "Apply the tool to a situation they have not seen and say, using its name, what will happen.",
        "One case dug into deeply builds the tool: a picture whose shape never changes afterwards, labelled with the "
        "tool's parts and the conditions it needs, and the name given once the case is done, then used every time "
        "it is applied; at least two quick applications that change only labels and numbers, not the picture's "
        "shape, with a guess before the first, one of them from a field the viewer would not expect; a fence: a "
        "situation where the tool looks usable but gives the wrong answer, naming the condition that fails; your "
        "turn: a case not seen before, the viewer applies the tool, pause, reveal."),
}


def resolve_question_type(question_type: str, concept_goal: str | None = None) -> QuestionType | None:
    base = QUESTION_TYPE_BY_NAME_MAP.get(question_type)
    if base is not None and question_type == "concept" and concept_goal:
        return CONCEPT_GOAL_BY_NAME_MAP.get(concept_goal)
    return base
