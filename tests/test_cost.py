from __future__ import annotations

import collections
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from delivered_series import create_series

from explainer_studio.agent_transcripts.claude_code import SESSION_ENV, _convert_path_to_project_slug
from explainer_studio.cost import compute_cost_report
from explainer_studio.deliver import format_delivery_record_dir_name
from explainer_studio.model_prices import estimate_cost_usd
from explainer_studio.schemas.cost import CostReport
from explainer_studio.schemas.model_prices import ModelPrice

START = datetime(2026, 10, 1, 10, tzinfo=UTC)


def _format_timestamp(seconds: float) -> str:
    return (START + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


class Transcript:
    """Lines of a Claude Code conversation record."""

    def __init__(self, cwd: Path):
        self.cwd = str(cwd)
        self.lines: list[dict] = []

    def add_person_message(self, seconds: float, text: str) -> Transcript:
        self.lines.append({"type": "user", "timestamp": _format_timestamp(seconds), "origin": {"kind": "human"},
                           "message": {"role": "user", "content": text}})
        return self

    def add_tool_call(self, seconds: float, call_name: str, tool_name: str, tool_input: dict, input_tokens: int = 0,
                      result_after_seconds: float | None = None, result: str = "ok") -> Transcript:
        self.lines.append({"type": "assistant", "timestamp": _format_timestamp(seconds),
                           "requestId": f"req_{call_name}", "cwd": self.cwd, "effort": "high",
                           "message": {"id": f"msg_{call_name}", "model": "claude-opus-5-5",
                                       "usage": {"input_tokens": input_tokens, "output_tokens": 100},
                                       "content": [{"type": "tool_use", "id": f"tu_{call_name}", "name": tool_name,
                                                    "input": tool_input}]}})
        if result_after_seconds is not None:
            self.lines.append({"type": "user", "timestamp": _format_timestamp(seconds + result_after_seconds),
                               "message": {"role": "user", "content": [
                                   {"type": "tool_result", "tool_use_id": f"tu_{call_name}", "content": result}]}})
        return self

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in self.lines), encoding="utf-8")


def _get_project_dir_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    """Where Claude Code keeps the transcripts of conversations started in `root`, in a config folder of the test."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.delenv(SESSION_ENV, raising=False)
    return tmp_path / "claude" / "projects" / _convert_path_to_project_slug(root)


def _write_subagent(project_dir_path: Path, conversation_name: str, agent_id: str, started_by_call_name: str,
                    transcript: Transcript) -> None:
    subagents_dir_path = project_dir_path / conversation_name / "subagents"
    transcript.write(subagents_dir_path / f"agent-{agent_id}.jsonl")
    (subagents_dir_path / f"agent-{agent_id}.meta.json").write_text(
        json.dumps({"toolUseId": f"tu_{started_by_call_name}"}))


def test_cost_follows_the_steps_and_leaves_out_waits_copies_and_onlookers(tmp_path: Path,
                                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root, script_path = series.root_dir_path, str(series.get_episode_paths("ep01").script_file_path)
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)

    def add_planning(transcript: Transcript) -> Transcript:
        return transcript.add_person_message(0, "make the first episode").add_tool_call(
            0, "plan", "Bash", {"command": "explainer-studio plan validate"}, input_tokens=1_000_000,
            result_after_seconds=60)

    making = add_planning(Transcript(root)).add_person_message(1800, "looks good, go on")
    making.add_tool_call(1810, "guide", "Read", {"file_path": "/plugin/skills/explainer-studio/workflow/script.md"},
                result_after_seconds=5)  # shows no step: works toward the next one
    making.add_tool_call(1820, "write", "Write", {"file_path": script_path}, result_after_seconds=10)
    making.add_tool_call(1840, "review", "Bash", {"command": "explainer-studio script validate ep01 && "
                                                    "explainer-studio script prepare-audience-review-prompt ep01"},
                result_after_seconds=10)
    making.add_tool_call(1860, "reviewer", "Agent", {"prompt": "review"}, result_after_seconds=540)
    making.add_tool_call(2410, "fix", "Edit", {"file_path": script_path}, result_after_seconds=10)
    making.add_tool_call(2430, "narrate", "Bash", {"command": "explainer-studio narrate ep01"}, result_after_seconds=70)
    making.write(project_dir_path / "making.jsonl")

    reviewer = Transcript(root).add_person_message(
        1861, f"Read /scratch/audience-review-prompts/{root.name}-ep01-script-review-1.md")
    reviewer.add_tool_call(1870, "read-prompt", "Read", {"file_path": "/elsewhere/prompt.md"})
    reviewer.add_tool_call(1900, "answer", "Write", {"file_path": "/elsewhere/answer.md"})
    _write_subagent(project_dir_path, "making", "a1", "reviewer", reviewer)

    # a resumed conversation copies the calls before it, a making one among them
    add_planning(Transcript(root)).add_tool_call(1820, "write", "Write", {"file_path": script_path}).write(
        project_dir_path / "resumed.jsonl")
    # opened the page, made nothing
    Transcript(root).add_tool_call(3000, "watch", "Bash", {"command": "explainer-studio video open ep01"},
                                   result_after_seconds=1).write(project_dir_path / "onlooker.jsonl")
    series.spending_file_path.write_text(json.dumps({"kind": "narration", "spent_at": _format_timestamp(2440),
                                                     "episode_id": "ep01", "provider_name": "openai",
                                                     "character_count": 100, "cost_usd": 0.5,
                                                     "is_estimated": True}) + "\n")

    report = compute_cost_report(series)

    assert report.unavailable_reason is None
    # no viewer note and no plan.yaml saved: the planning is all deep reading
    [planning_call] = [model_call for model_call in report.model_calls if model_call.episode_id is None]
    assert (planning_call.step, planning_call.model_name, planning_call.effort,
            planning_call.token_usage.non_cached_input_tokens) == ("deep_reading", "claude-opus-5-5", "high", 1_000_000)
    assert _find_step(report, None, "deep_reading").working_duration_seconds == 60
    assert (_count_calls(report, "script"), _count_calls(report, "audience_review"), _count_calls(report, "narration")) \
        == (2, 5, 1)
    # the audience reviewer's calls are its own agent's, apart from the main agent's; the resumed copy is the same agent
    assert _count_calls_by_agent_kind(report, "audience_review") == {"main": 3, "audience_reviewer": 2}
    [main_agent, reviewer_agent] = report.agents
    assert (main_agent.kind, reviewer_agent.kind, reviewer_agent.parent_agent_id) == \
        ("main", "audience_reviewer", main_agent.id)
    assert _find_step(report, "ep01", "audience_review").round_count == 1
    # the person wrote again after the planning call
    assert {model_call.turn_number for model_call in report.model_calls
            if _find_agent_kind(report, model_call.agent_id) == "main"} == {1, 2}
    # the half hour waiting for the person is left out; the reviewer working beside the agent is not counted twice
    assert (_find_step(report, "ep01", "script").working_duration_seconds,
            _find_step(report, "ep01", "audience_review").working_duration_seconds) == (30, 590)
    [narration_call] = report.narration_calls
    assert (narration_call.step, narration_call.character_count, narration_call.cost_usd) == ("narration", 100, 0.5)
    assert report.episodes[0].first_delivery is None
    assert not any(step.step == "after_delivery" for step in report.steps)

    # dollars use the prices in effect when the work started
    prices = [ModelPrice(model_name="claude-opus-5-5", effective_date=date(2026, 1, 1),
                         non_cached_input_usd_per_million_tokens=4, cache_read_usd_per_million_tokens=0.2,
                         five_minute_cache_write_usd_per_million_tokens=5,
                         one_hour_cache_write_usd_per_million_tokens=8, output_usd_per_million_tokens=20),
              ModelPrice(model_name="claude-opus-5-5", effective_date=date(2026, 11, 1),
                         non_cached_input_usd_per_million_tokens=2, cache_read_usd_per_million_tokens=0.1,
                         five_minute_cache_write_usd_per_million_tokens=2.5,
                         one_hour_cache_write_usd_per_million_tokens=4, output_usd_per_million_tokens=10)]
    assert estimate_cost_usd([planning_call], prices).cost_usd == pytest.approx(4.002)


def _find_step(report: CostReport, episode_id: str | None, step: str):
    return next(entry for entry in report.steps if (entry.episode_id, entry.step) == (episode_id, step))


def _find_agent_kind(report: CostReport, agent_id: str) -> str:
    return next(agent.kind for agent in report.agents if agent.id == agent_id)


def _count_calls(report: CostReport, step: str, episode_id: str | None = "ep01") -> int:
    return sum((model_call.episode_id, model_call.step) == (episode_id, step) for model_call in report.model_calls)


def _count_calls_by_agent_kind(report: CostReport, step: str, episode_id: str | None = "ep01") -> dict[str, int]:
    return dict(collections.Counter(_find_agent_kind(report, model_call.agent_id) for model_call in report.model_calls
                                    if (model_call.episode_id, model_call.step) == (episode_id, step)))


def test_a_scene_writer_counts_in_scenes_and_a_wait_in_the_step_it_waits_for(tmp_path: Path,
                                                                              monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root, episode_dir_path = series.root_dir_path, series.get_episode_paths("ep01").root_dir_path
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)
    making = Transcript(root).add_tool_call(0, "review", "Bash", {
        "command": "explainer-studio script prepare-audience-review-prompt ep01"}, result_after_seconds=5)
    making.add_tool_call(10, "writer", "Agent", {"prompt": "write the hook scene"}, result_after_seconds=60)
    making.add_tool_call(100, "narrate", "Bash", {"command": "explainer-studio narrate ep01"}, result_after_seconds=5)
    # waits in the series folder, then renders: the wait is the render's
    making.add_tool_call(110, "wait", "Bash", {"command": "sleep 60"}, result_after_seconds=60)
    making.add_tool_call(180, "render", "Bash", {"command": "explainer-studio render ep01"}, result_after_seconds=5)
    making.write(project_dir_path / "making.jsonl")
    # started during the audience review, it reads what it needs to write its scene
    writer = Transcript(root).add_person_message(11, "Write the hook scene; the brief is at /scratch/brief.md")
    writer.add_tool_call(12, "read-shared", "Read", {"file_path": str(root / "production" / "shared" / "series.py")})
    writer.add_tool_call(14, "read-script", "Read", {"file_path": str(episode_dir_path / "script.yaml")})
    writer.add_tool_call(16, "write-scene", "Write", {"file_path": str(episode_dir_path / "scenes" / "hook.py")})
    _write_subagent(project_dir_path, "making", "w1", "writer", writer)

    report = compute_cost_report(series)

    assert not any(model_call.episode_id is None for model_call in report.model_calls)
    # the scene writer's calls are all in scenes, none in planning or the audience review
    assert _count_calls_by_agent_kind(report, "scenes") == {"scene_writer": 3}
    assert _count_calls_by_agent_kind(report, "audience_review") == {"main": 1}
    render_calls = [model_call for model_call in report.model_calls if model_call.step == "render"]
    assert [model_call.is_waiting for model_call in render_calls] == [True, False]  # the wait, then the render


def test_a_scene_writer_counts_in_the_episode_it_writes_not_the_template_it_reads(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root = series.root_dir_path
    ep01_dir_path = series.get_episode_paths("ep01").root_dir_path
    ep02_dir_path = series.get_episode_paths("ep02").root_dir_path
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)
    making = Transcript(root).add_tool_call(0, "narrate", "Bash", {"command": "explainer-studio narrate ep02"},
                                            result_after_seconds=5)
    making.add_tool_call(10, "writer", "Agent", {"prompt": "write the intro scene"}, result_after_seconds=60)
    making.write(project_dir_path / "making.jsonl")
    # the guide has a writer read another episode's finished scene as its template first
    writer = Transcript(root).add_person_message(11, "Write the intro scene of ep02")
    writer.add_tool_call(12, "read-bible", "Read", {"file_path": str(root / "production" / "series-bible.md")})
    writer.add_tool_call(13, "read-template", "Read", {"file_path": str(ep01_dir_path / "scenes" / "hook.py")})
    writer.add_tool_call(14, "read-script", "Read", {"file_path": str(ep02_dir_path / "script.yaml")})
    writer.add_tool_call(16, "write-scene", "Write", {"file_path": str(ep02_dir_path / "scenes" / "intro.py")})
    writer.add_tool_call(18, "preview", "Bash", {"command": "explainer-studio preview ep02 --scenes intro"})
    _write_subagent(project_dir_path, "making", "w1", "writer", writer)

    report = compute_cost_report(series)

    assert not any(model_call.episode_id in (None, "ep01") for model_call in report.model_calls)
    assert _count_calls_by_agent_kind(report, "scenes", "ep02") == {"scene_writer": 5}


def test_a_subagent_that_only_reads_scenes_is_not_a_scene_writer(tmp_path: Path,
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root, episode_dir_path = series.root_dir_path, series.get_episode_paths("ep01").root_dir_path
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)
    making = Transcript(root).add_tool_call(0, "review", "Bash", {
        "command": "explainer-studio script prepare-audience-review-prompt ep01"}, result_after_seconds=5)
    making.add_tool_call(10, "checker", "Agent", {"prompt": "check the script against the scenes"},
                         result_after_seconds=30)
    making.write(project_dir_path / "making.jsonl")
    checker = Transcript(root).add_person_message(11, "Check the script against the scenes")
    checker.add_tool_call(12, "read-script", "Read", {"file_path": str(episode_dir_path / "script.yaml")})
    checker.add_tool_call(14, "read-scene", "Read", {"file_path": str(episode_dir_path / "scenes" / "hook.py")})
    _write_subagent(project_dir_path, "making", "c1", "checker", checker)

    report = compute_cost_report(series)

    # each read counts where the file it read belongs, as any other subagent's call does
    assert _count_calls_by_agent_kind(report, "audience_review") == {"main": 2, "other_subagent": 1}
    assert _count_calls_by_agent_kind(report, "scenes") == {"other_subagent": 1}


def test_work_after_the_first_delivery_is_one_step(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root, episode_paths = series.root_dir_path, series.get_episode_paths("ep01")
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)
    for delivered_seconds in (100, 300):
        delivered_at = START + timedelta(seconds=delivered_seconds)
        record_dir_path = episode_paths.delivery_records_dir_path / format_delivery_record_dir_name(delivered_at)
        record_dir_path.mkdir(parents=True)
        (record_dir_path / "metadata.json").write_text(json.dumps({
            "delivered_at": delivered_at.isoformat(), "explainer_studio_version": "0.1.0",
            "files": {"video_file_name": "01.mp4", "cover_file_name": "01.png",
                      "subtitles": [{"language_code": "zh-TW", "file_name": "01.zh-TW.srt"}]}}))
    making = Transcript(root).add_tool_call(0, "render", "Bash", {"command": "explainer-studio render ep01"},
                                            result_after_seconds=5)
    making.add_tool_call(90, "deliver", "Bash", {"command": "explainer-studio deliver ep01"}, result_after_seconds=10)
    # a change and its delivery, then a change not delivered yet
    making.add_tool_call(200, "fix", "Edit", {"file_path": str(episode_paths.root_dir_path / "scenes" / "hook.py")},
                         result_after_seconds=5)
    making.add_tool_call(290, "deliver-again", "Bash", {"command": "explainer-studio deliver ep01"},
                         result_after_seconds=10)
    making.add_tool_call(400, "fix-again", "Edit", {"file_path": str(episode_paths.script_file_path)},
                         result_after_seconds=5)
    making.write(project_dir_path / "making.jsonl")

    report = compute_cost_report(series)

    first_delivery = next(episode.first_delivery for episode in report.episodes if episode.episode_id == "ep01")
    assert first_delivery is not None and first_delivery.delivered_at == START + timedelta(seconds=100)
    assert (_count_calls(report, "render"), _count_calls(report, "after_delivery")) == (2, 3)


def test_planning_splits_at_what_was_saved_and_a_check_alone_counts_nothing(tmp_path: Path,
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    root, research_dir_path = series.root_dir_path, series.root_dir_path / "production" / "research"
    project_dir_path = _get_project_dir_path(tmp_path, monkeypatch, root)
    # a planning conversation runs no making command: writing the series' files is what makes it count
    planning = Transcript(root).add_person_message(0, "teach me linear algebra")
    planning.add_tool_call(10, "probe", "Read", {"file_path": str(root / "sources" / "notes.pdf")})
    planning.add_tool_call(20, "viewer-note", "Write", {"file_path": str(research_dir_path / "audience.md")})
    planning.add_tool_call(30, "reading-note", "Write", {"file_path": str(research_dir_path / "notes.md")})
    planning.add_tool_call(40, "plan", "Write", {"file_path": str(series.plan_file_path)})
    planning.add_tool_call(50, "open", "Bash", {"command": "explainer-studio plan open"}, result_after_seconds=1)
    planning.add_tool_call(55, "wait-for-reply", "Read", {"file_path": str(series.plan_file_path)})
    planning.add_person_message(60, "start")
    planning.add_tool_call(70, "revise", "Edit", {"file_path": str(series.plan_file_path)})
    planning.write(project_dir_path / "planning.jsonl")
    # checking and looking make nothing
    checker = Transcript(root).add_tool_call(100, "check", "Bash", {
        "command": "explainer-studio plan validate && explainer-studio script validate ep01"})
    checker.add_tool_call(110, "look", "Read", {"file_path": str(series.plan_file_path)})
    checker.write(project_dir_path / "checker.jsonl")

    report = compute_cost_report(series)

    assert [(model_call.step, model_call.turn_number) for model_call in report.model_calls] == [
        ("audience", 1), ("audience", 1), ("deep_reading", 1), ("plan", 1), ("plan", 1), ("plan", 1),
        ("plan_review", 2)]
    assert [agent.kind for agent in report.agents] == ["main"]
