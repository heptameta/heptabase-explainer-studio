"""Script audience reviews: the prompt the audience reviewer gets, and the gate that reads the recorded rounds.

The audience reviewer is a fresh subagent that reads the script as the plan's audience and lists problems. The prompt
function writes what the reviewer may see into one file outside the series, so the whole prompt never passes through
the writing agent's conversation. The gate functions only read the recorded rounds in `audience-reviews/script.yaml`;
they never judge content.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import languages, question_types, user_dirs
from .errors import StudioError
from .file_io import load_yaml_model
from .paths import Series
from .plan import load_plan
from .schemas.audience_review import ScriptReviews, ScriptRound
from .schemas.script import Script
from .script import load_script

# A scene lost this many times is written a different way before the next read: another wording will not help.
REWRITE_AFTER_LOST_COUNT = 2
# After this many rounds (the whole episode once, then two rounds of the scenes where the reviewer got lost) the
# episode is settled: no more re-reads are required for any scene. A scene never read still needs its read. No
# per-scene limit is needed: a scene is read at most once a round, so it cannot be lost more often than this.
SETTLE_AFTER_ROUND_COUNT = 3


def load_script_reviews(series: Series, episode_id: str) -> ScriptReviews:
    script_reviews_file_path = series.get_episode_paths(episode_id).script_reviews_file_path
    if not script_reviews_file_path.exists():
        return ScriptReviews()
    return load_yaml_model(ScriptReviews, script_reviews_file_path, f"{episode_id}/audience-reviews/script.yaml")


def _find_lost_scene_ids(review_round: ScriptRound) -> set[str]:
    """Scenes of this round where the reviewer got lost. Each finding names the scene it was read in, so renaming or
    moving a beat afterwards changes nothing; a finding on a scene the round did not read does not count."""
    return {finding.scene_id for finding in review_round.findings
            if finding.kind == "lost" and finding.scene_id in review_round.scene_ids}


@dataclass(frozen=True)
class SceneReviewState:
    scene_id: str
    read_count: int
    lost_count: int
    was_lost_in_latest_read: bool


def build_scene_review_states(script: Script, reviews: ScriptReviews) -> list[SceneReviewState]:
    states = []
    for scene in script.scenes:
        covering_rounds = [review_round for review_round in reviews.rounds if scene.id in review_round.scene_ids]
        lost_flags = [scene.id in _find_lost_scene_ids(review_round) for review_round in covering_rounds]
        states.append(SceneReviewState(scene.id, len(covering_rounds), sum(lost_flags),
                                       bool(lost_flags and lost_flags[-1])))
    return states


def _check_is_episode_settled(reviews: ScriptReviews) -> bool:
    return len(reviews.rounds) >= SETTLE_AFTER_ROUND_COUNT


def find_script_review_problems(script: Script, reviews: ScriptReviews) -> dict[str, str]:
    """{scene id: why it still needs a read}, in script order."""
    is_episode_settled = _check_is_episode_settled(reviews)
    problem_by_scene_id_map = {}
    for state in build_scene_review_states(script, reviews):
        if state.read_count == 0:
            problem_by_scene_id_map[state.scene_id] = (f"scene {state.scene_id} has not been read by an audience "
                                                       "reviewer")
        elif state.was_lost_in_latest_read and not is_episode_settled:
            hint = (f" (lost {state.lost_count} times: another wording will not help; write it a different way "
                    "before the next read)"
                    if state.lost_count >= REWRITE_AFTER_LOST_COUNT else "")
            problem_by_scene_id_map[state.scene_id] = (f"scene {state.scene_id}: the audience reviewer got lost in its "
                                                       f"latest read; a new round must read it again{hint}")
    return problem_by_scene_id_map


def require_script_review(series: Series, episode_id: str, script: Script) -> None:
    """The gate before narration."""
    problem_by_scene_id_map = find_script_review_problems(script, load_script_reviews(series, episode_id))
    if problem_by_scene_id_map:
        raise StudioError(
            f"{episode_id} is not ready for narration", "the script audience review is not finished",
            f"explainer-studio script prepare-audience-review-prompt {episode_id} "
            f"--scenes {','.join(problem_by_scene_id_map)}",
            list(problem_by_scene_id_map.values()))


def find_scene_ids_settled_while_lost(series: Series, episode_id: str, script: Script) -> list[str]:
    """Scenes whose reviews stopped while the reviewer was still getting lost, to tell the user after delivery."""
    reviews = load_script_reviews(series, episode_id)
    is_episode_settled = _check_is_episode_settled(reviews)
    return [state.scene_id for state in build_scene_review_states(script, reviews)
            if state.was_lost_in_latest_read and is_episode_settled]


# Prompts --------------------------------------------------------------------------------------------------------------
# What the reviewer looks for in a script: the problems that made viewers stop following in finished episodes.
SCRIPT_PROBLEM_CHECKLIST = """\
1. Words, ideas, labels or metaphors used before they are explained or built on something concrete, for THIS viewer \
(their unfamiliar words are listed above); the author's own term or a compressed sentence from the sources used \
before the viewer has seen what it refers to happen; an idiom, an allusion (a figure from scripture or legend) or a \
quotation whose meaning is never said in plain words; or a general statement that comes before the concrete example \
it is about.
2. Skipped causal steps: places where you would ask "wait, why?" or "how did we get here?"; or a new example or piece \
of evidence that starts without saying what it is there to answer.
3. A belief this viewer may hold (listed above) that is only asserted to be wrong, not broken on a concrete case; or \
broken, but the new picture is not clear.
4. Sentences hard to follow when heard once at speaking speed: too long, two new ideas at once, an unclear "it" or \
"this"; or an abstract sentence that only restates what an example just showed, or a promise of what comes later \
("we will see...") where an example could go.
5. Narration and picture pointing at different things at the same moment, or a label on screen that now means \
something other than before.
6. Anything inaccurate, or claimed more strongly than a careful expert in the subject would.
7. Analogies that mislead: where does the analogy break, and does the script say so?
8. A question the viewer is asked to guess whose answer is obvious, or that tests memory instead of thinking.
9. Two questions running at once: a guess, a title or a scene that asks something other than what the evidence is \
answering.
10. An inference stated as a conclusion ("if X, we should see Y") before you have been shown why X leads to Y.
11. Something new in a recap or in the close: a step said in other words or with a new picture than when it was \
taught (you think you missed something), or an example, fact or name not taught where it belongs.
12. A question the opening raises that the episode never answers, nor gives the shape of the answer to.
13. Something from an earlier scene or episode (a name, a place, a picture, a label) brought back without a one-line \
reminder of what it was.
14. A beat that carries more than one new link of reasoning (A, so B, so C in one line), a link whose premise you were \
never given (or were only told "an earlier episode showed it"), or a link whose conclusion is never said aloud. Count \
it even if you followed it while reading: heard once, at speaking speed, with the next thing starting right after, \
this viewer would not.
15. A seam (a new scene, a switch to another example or place, going on after the main question is answered, a turn \
in the argument, leaving the picture used so far) where you could not say in one sentence what has just been \
established and why the next part is being shown; a turn that ends without the revised claim said aloud; pieces that \
are the same thing but are not said to be when the second one appears; or the episode's main question or main \
picture swapped for another one midway. A sentence only written on screen does not count as said.
16. Anything from this episode's must-haves (above) that the scenes you read leave out or only assert."""


def _write_prompt_file(series: Series, episode_id: str, text: str) -> Path:
    prompt_dir_path = user_dirs.ensure_scratch_dir("audience-review-prompts")
    timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
    prefix = f"{series.root_dir_path.name[:40]}-{episode_id}-script-review-{timestamp}-"
    file_descriptor, prompt_path_text = tempfile.mkstemp(prefix=prefix, suffix=".md", dir=prompt_dir_path, text=True)
    with open(file_descriptor, "w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    return Path(prompt_path_text)


def _format_terms(terms: list[str]) -> str:
    return ", ".join(terms) if terms else "(none listed)"


def _format_viewer_section(plan) -> str:
    audience = plan.audience
    lines = ["## Who you are", "", audience.description.strip(), "",
             f"Words you do not know yet: {_format_terms(audience.unfamiliar_terms)}"]
    if audience.misconceptions:
        lines += ["", "What you may believe going in:"]
        lines += [f"- {misconception.belief.strip()}" for misconception in audience.misconceptions]
    return "\n".join(lines)


def _format_earlier_episodes_section(plan, episode_id: str) -> str:
    earlier_episode_lines = []
    for earlier_episode in plan.episodes:
        if earlier_episode.id == episode_id:
            break
        earlier_episode_lines.append(
            f"- {earlier_episode.id}, \"{earlier_episode.title}\": it answered \"{earlier_episode.question.strip()}\"; "
            f"you took away: {earlier_episode.takeaway.strip()}; "
            f"it taught: {_format_terms(earlier_episode.taught_terms)}")
    if not earlier_episode_lines:
        return ""
    return "\n".join(["## Earlier episodes you have watched", "",
                      "You watched these earlier episodes of the series and know what they taught:",
                      *earlier_episode_lines])


def _format_this_episode_section(episode) -> str:
    question_type = question_types.resolve_question_type(episode.question_type, episode.concept_goal)
    lines = ["## This episode", "", f"It answers one question: {episode.question.strip()}"]
    if question_type is not None:
        lines += [f"Kind of question: {question_type.display_name} ({question_type.question})",
                  f"Afterwards you should be able to: {question_type.outcome}",
                  f"Whoever presents it, the episode must have: {question_type.must_haves}"]
    return "\n".join(lines)


def _format_scene_section(scene, is_read: bool) -> str:
    label = "READ" if is_read else "CONTEXT ONLY"
    lines = [f"### Scene `{scene.id}` ({label})", "", f"Purpose: {scene.purpose.strip()}", ""]
    for beat in scene.beats:
        lines.append(f"- beat `{beat.id}`")
        lines.append(f"  Narration (heard): {beat.narration_text.strip()}")
        if is_read:
            lines.append(f"  Picture (seen at the same time): {beat.visual.strip()}")
        if beat.pause_duration_seconds:
            lines.append(f"  Then a pause of {beat.pause_duration_seconds:g} s")
    return "\n".join(lines)


SCRIPT_REPLY_TEMPLATE = """\
reviewer_summary:
  question: "<the question this episode answers, in one sentence, as you understood it>"
  takeaway: "<what you take away from it, in one sentence>"
  explained_terms: ["<a term the scenes explained clearly enough for you>", ...]
  lost_beat_id: <the first beat id after which you were holding too many things or no longer knew why you were being told \
this; null if nowhere>
  most_engaging_beat_id: <the beat id that made you most want to keep watching; null if none>
findings:
  - scene_id: <scene id>
    beat_id: <beat id>
    kind: <lost, wrong or minor>
    problem: "<the problem, and why this viewer stumbles there: what you thought it meant>\""""


def prepare_audience_review_prompt(series: Series, episode_id: str,
                                   scene_ids: list[str] | None = None) -> tuple[Path, str]:
    """Write the script audience review prompt for `scene_ids` (default: all) and return its path and the round
    header."""
    plan = load_plan(series)
    episode = plan.find_episode(episode_id)
    script = load_script(series, episode_id)
    known_scene_ids = [scene.id for scene in script.scenes]
    chosen_scene_ids = scene_ids or known_scene_ids
    unknown_scene_ids = [scene_id for scene_id in chosen_scene_ids if scene_id not in known_scene_ids]
    if unknown_scene_ids:
        raise StudioError(f"{episode_id}/script.yaml has no scene {', '.join(unknown_scene_ids)}",
                          f"its scenes are {', '.join(known_scene_ids)}",
                          "pass --scenes with scene ids from the script, or omit it to review every scene")
    chosen_scene_ids = [scene_id for scene_id in known_scene_ids if scene_id in chosen_scene_ids]  # script order
    is_partial = len(chosen_scene_ids) < len(known_scene_ids)
    language_name = languages.format_language_name(plan.resolve_episode_language_code(episode_id))
    reading_instruction = (
        "Read the scenes marked READ, in order, as if hearing them once at speaking speed. Scenes marked "
        "CONTEXT ONLY were read by earlier reviewers; they are here so you know what comes before and after. "
        "Report problems only in the READ scenes." if is_partial else
        "Read every scene, in order, as if hearing it once at speaking speed.")
    sections = [
        f"# Script audience review: {episode_id}, \"{episode.title}\"",
        ("You are one specific viewer, described below, about to read part of the script of an explainer video. "
         f"Write your whole reply in {language_name}, except the YAML keys, the kinds and the beat ids, which stay as "
         "they are."),
        ("Read only this file. Do not open any other file (no plan, notes, code or earlier reviews) and do not "
         "search the web. Do not rewrite the script and do not score it."),
        _format_viewer_section(plan),
        _format_earlier_episodes_section(plan, episode_id),
        _format_this_episode_section(episode),
        "## The script\n\nEach beat is one line of narration, which you hear, and the picture on screen at the same "
        "time. A pause means the narration stops for that long; the picture says what plays then, if anything.\n\n"
        + reading_instruction + " You hear each line once and cannot read ahead: a word, label, figure of speech, "
        "quotation or reminder whose meaning only comes later (after a colon, in the next clause or the next line) is "
        "unexplained where you hear it, and you are lost there, even if what follows explains it.",
        "\n\n".join(_format_scene_section(scene, scene.id in chosen_scene_ids) for scene in script.scenes
                    if scene.id in chosen_scene_ids or is_partial),
        "## What to look for\n\nAs this viewer, go beat by beat and list only problems:\n\n" + SCRIPT_PROBLEM_CHECKLIST,
        "## Your reply\n\nReply with only this YAML, nothing before or after it:\n\n```yaml\n" + SCRIPT_REPLY_TEMPLATE
        + "\n```\n\n"
        "Kinds:\n"
        "- `lost`: you lost the thread or stopped following there; or it is a problem of type 14 or 15; or it is a "
        "problem of type 1 that the reasoning depends on.\n"
        "- `wrong`: it is inaccurate or overclaimed (type 6).\n"
        "- `minor`: anything else.\n\n"
        "At most 15 findings, most serious first. Use scene and beat ids exactly as written above. Put every "
        "sentence in double quotes. If you found nothing, write `findings: []`. Under 800 words in all.",
    ]
    prompt_file_path = _write_prompt_file(series, episode_id, "\n\n".join(part for part in sections if part) + "\n")
    rounds_header = "" if series.get_episode_paths(episode_id).script_reviews_file_path.exists() else "rounds:\n"
    return prompt_file_path, f"{rounds_header}  - scene_ids: [{', '.join(chosen_scene_ids)}]"
