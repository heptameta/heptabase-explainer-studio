from __future__ import annotations

from explainer_studio.audience_review import find_script_review_problems
from explainer_studio.schemas.audience_review import ScriptFinding, ScriptReviews, ScriptRound
from explainer_studio.schemas.script import Script


def build_script() -> Script:
    return Script.model_validate({"scenes": [
        {"id": "hook", "purpose": "p", "beats": [{"id": "a", "narration_text": "n", "visual": "v"}]},
        {"id": "dam", "purpose": "p", "beats": [{"id": "b", "narration_text": "n", "visual": "v"},
                                                 {"id": "c", "narration_text": "n", "visual": "v"}]},
    ]})


def build_lost_finding(scene_id: str, beat_id: str) -> ScriptFinding:
    return ScriptFinding(scene_id=scene_id, beat_id=beat_id, kind="lost", problem="lost here")


def test_every_scene_must_be_read() -> None:
    reviews = ScriptReviews(rounds=[ScriptRound(scene_ids=["hook"])])
    assert list(find_script_review_problems(build_script(), reviews)) == ["dam"]


def test_a_scene_lost_in_its_latest_read_needs_another_read() -> None:
    reviews = ScriptReviews(rounds=[ScriptRound(scene_ids=["hook", "dam"], findings=[build_lost_finding("dam", "b")])])
    assert list(find_script_review_problems(build_script(), reviews)) == ["dam"]
    reviews.rounds.append(ScriptRound(scene_ids=["dam"]))
    assert find_script_review_problems(build_script(), reviews) == {}


def test_a_lost_finding_counts_in_the_scene_it_was_read_in_whatever_the_beat_is_called_now() -> None:
    # the beat was renamed while fixing; only the scene it was read in needs another read
    reviews = ScriptReviews(rounds=[ScriptRound(scene_ids=["hook", "dam"],
                                                findings=[build_lost_finding("dam", "old_beat")])])
    assert list(find_script_review_problems(build_script(), reviews)) == ["dam"]


def test_a_scene_lost_twice_is_written_a_different_way() -> None:
    rounds = [ScriptRound(scene_ids=["hook", "dam"], findings=[build_lost_finding("dam", "b")])]
    assert "different way" not in find_script_review_problems(build_script(), ScriptReviews(rounds=rounds))["dam"]
    rounds.append(ScriptRound(scene_ids=["dam"], findings=[build_lost_finding("dam", "c")]))
    assert "different way" in find_script_review_problems(build_script(), ScriptReviews(rounds=rounds))["dam"]


def test_three_rounds_settle_the_episode_but_unread_scenes_still_block() -> None:
    rounds = [ScriptRound(scene_ids=["dam"], findings=[build_lost_finding("dam", "b")]) for _ in range(3)]
    assert list(find_script_review_problems(build_script(), ScriptReviews(rounds=rounds))) == ["hook"]
    assert list(find_script_review_problems(build_script(), ScriptReviews(rounds=rounds[:2]))) == ["hook", "dam"]
