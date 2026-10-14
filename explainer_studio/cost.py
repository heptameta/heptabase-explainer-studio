"""Cost: what making a series took, in the agent's model calls, paid narration and working time, step by step.

Nothing is recorded for it. `cost show`, `deliver` and feedback shares work it out when asked, from the harness's
transcripts of the agent's conversations (`agent_transcripts`), `spending.jsonl` and the series files, into a cost
report (`schemas/cost.py`):

- **Which conversations.** One that made something in this series, and its subagents (and theirs): it ran a making
  command (`MAKING_COMMANDS`) or wrote a file in `production/` with a file tool (feedback and delivery records
  aside). A conversation that only read the series, checked it (`plan validate`, `script validate`), opened its pages
  or recorded feedback, such as one analysing it afterwards, is not counted; work after delivery is counted when it
  happens in a conversation that made something.
- **Which step a model call belongs to.** The explainer-studio command it ran or the series file it touched (see
  `STEP_BY_COMMAND_MAP` and the part maps below). A call that shows neither, such as reading a guide or thinking,
  belongs to the next step its conversation works on.
- **Waiting.** A shell command that sleeps (`sleep 30`, a loop polling a log) is waiting for something to finish. Its
  working folder does not tie it to a step; only the commands it runs and the series files it names do (a wait that
  looks into `render/` waits for the render). A wait that names nothing shows nothing, so like thinking it belongs to
  the next step its conversation works on: what the agent does when the wait ends is what it was waiting for.
- **Subagents, by their kind.** A subagent does one kind of work, and all its calls belong to that step, whatever
  files it reads on the way. An audience reviewer, recognised by its prompt file, is the audience review of its
  episode; its calls on another series stay out. A scene writer is a subagent that writes scene files (with a file
  tool, in an episode's `scenes/`, `cover.py`, `assets/` or `preview/`) or runs `preview`; reading scene files does
  not make one. It writes for one episode: the one it wrote or previewed scenes of in the most calls (the first of
  them on a tie). Every call of it that belongs to this series is that episode's scenes step, its reads of
  `script.yaml`, `plan.yaml`, `series-bible.md`, `shared/` and another episode's template scene included: it reads
  them to write scenes, not to plan, review or fix another episode. Any other subagent follows the rules above, and
  one that shows nothing belongs where it was started.
- **Planning, by what was saved.** The series' planning is split into the flow's first four steps by moments in the
  transcripts: `audience` up to and including the first save of a research note about the viewer (named audience… or
  viewer…, such as `research/audience.md`); `deep_reading` until `plan.yaml` is first saved after another research
  note (or after the viewer note when there is none); `plan` from that save; `plan_review` from the first time the
  person writes after the plan page was first opened. Without a viewer note, its time is in `deep_reading`.
- **Then by time.** Script changes after the first audience review prompt are the review's (fixing what it found)
  until the first narration, and narration's after that; scene work after the first render is the render's (fixing
  what the whole video showed). An episode's work is split only at its first delivery: everything after it, however
  many deliveries follow, is `after_delivery`. A command that printed an `error:` line did not start
  its step.
- **Usage, not dollars.** Every model call with its step, the agent that made it, its token counts, model, effort and
  speed, counted once even when a resumed conversation repeats it; a resumed conversation is the same agent as the
  one it resumes. Dollars are worked out only to display them in dev mode, from the local price table
  (`model_prices`). Paid narration from `spending.jsonl` with its estimated cost, by when it was spent.
- **Working time.** The time between a conversation's events, except a wait for the person, and except a gap of more
  than ten minutes that no long command (narrate, preview, render, deliver) or background task explains. Work running
  at the same moment in several conversations shares that moment.
"""

from __future__ import annotations

import collections
import os
import re
import shlex
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .agent_transcripts import (
    HARNESS_DISPLAY_NAME_BY_NAME_MAP,
    Conversation,
    HarnessConversations,
    ModelCall,
    ToolUse,
    read_harness_conversations,
)
from .deliver import list_delivery_record_dir_paths, load_delivered_timeline, load_delivery_record
from .errors import StudioError
from .file_io import convert_yaml_document_to_plain_data, read_yaml_document
from .model_prices import estimate_cost_usd
from .paths import EPISODE_ID_PATTERN, PRODUCTION_DIR_NAME, Series
from .schemas.cost import (
    EPISODE_STEPS,
    PLANNING_STEPS,
    CostReport,
    CostReportAgent,
    CostReportEpisode,
    CostReportModelCall,
    CostReportNarrationCall,
    CostReportStep,
    DeliverySummary,
)
from .schemas.delivery_record import DeliveryRecord
from .schemas.model_prices import ModelPrice
from .spending import read_narration_spending_records

MAX_COUNTED_IDLE_SECONDS = 600
LABEL_BY_STEP_MAP = {"audience": "audience", "deep_reading": "deep reading", "plan": "plan",
                     "plan_review": "plan review", "script": "script", "audience_review": "audience review",
                     "narration": "narration", "scenes": "scenes", "render": "render",
                     "after_delivery": "after the first delivery"}
COUNT_FIELD_BY_STEP_MAP = {"audience_review": "round_count", "scenes": "scene_preview_count", "render": "render_count"}

COMMAND_GROUPS = {"plan", "script", "video", "feedback", "gap", "asset", "setup", "cost"}
COMMAND_FLAGS = {"cover", "dry-run", "json", "no-browser", "help", "version"}
STEP_BY_COMMAND_MAP = {"plan validate": "planning", "plan open": "planning", "script validate": "script",
                       "script prepare-audience-review-prompt": "audience_review", "narrate": "narration",
                       "preview": "scenes", "render": "render", "deliver": "render", "video open": "after_delivery",
                       "feedback add": "after_delivery", "feedback resolve": "after_delivery",
                       "feedback share": "after_delivery"}
MAKING_COMMANDS = {"script prepare-audience-review-prompt", "narrate", "preview", "render", "deliver"}
LONG_COMMANDS = {"narrate", "preview", "render", "deliver"}
# what touching a part of production/ means: a part of an episode's folder, or of the series level
STEP_BY_EPISODE_PART_MAP = {"design.md": "script", "script.yaml": "script", "audience-reviews": "audience_review",
                            "narration": "narration", "scenes": "scenes", "cover.py": "scenes", "assets": "scenes",
                            "preview": "scenes", "render": "render", "feedback.json": "after_delivery",
                            "delivery-records": "after_delivery"}
STEP_BY_SERIES_PART_MAP = {"plan.yaml": "planning", "series-bible.md": "planning", "research": "planning",
                           "sources": "planning", "shared": "scenes"}

_INVOCATION_PATTERN = re.compile(r"(?:^|[\s;&|(/\"'])explainer-studio[ \t]+([^;&|\n)]*)")
_CD_PATTERN = re.compile(r"(?:^|[;&|(]|\s)cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|)]+)")
_PATH_TOKEN_PATTERN = re.compile(r"[^\s'\"`;|&()<>]+")
_FILE_SUFFIXES = (".yaml", ".yml", ".md", ".py", ".json", ".jsonl", ".wav", ".mp4", ".png", ".srt")
_ERROR_LINE_PATTERN = re.compile(r"(?m)^error: ")
# `sleep` run as a command: on its own, after `;`, `&&` or `|`, or as a loop's body
_SLEEP_PATTERN = re.compile(r"(?:^|[;&|({]|\b(?:do|then))\s*sleep\s+[\d.]", re.MULTILINE)
# a research note about the viewer (the guide suggests research/audience.md)
_VIEWER_NOTE_PATTERN = re.compile(r"^(?:audience|viewer)", re.IGNORECASE)

# (episode id or None for the series level, step); the step is planning, one of EPISODE_STEPS or after_delivery (work
# on a delivered episode, such as opening its video page)
Context = tuple[str | None, str]
OTHER_CONTEXT: Context = ("", "other")  # work on something else, such as another series


# Commands and files a model call touched ----------------------------------------------------------------------------
@dataclass(frozen=True)
class CommandRun:
    """One explainer-studio command in a shell command."""

    name: str  # narrate, script validate …
    episode_id: str | None
    series_path: str | None  # its --series
    scene_ids: tuple[str, ...] | None  # its --scenes
    has_cover_option: bool  # its --cover
    has_help_option: bool

    @property
    def is_production(self) -> bool:
        return self.name in STEP_BY_COMMAND_MAP and not self.has_help_option


def parse_command_runs(command: str) -> list[CommandRun]:
    runs = []
    for match in _INVOCATION_PATTERN.finditer(command):
        try:
            tokens = shlex.split(match.group(1))
        except ValueError:
            tokens = match.group(1).split()
        positional_arguments, option_value_by_name_map, has_help_option = [], {}, False
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token[:1] in (">", "<") or token[:2] in ("2>", "1>", "&>"):
                break
            if token in ("-h", "--help", "--version"):
                has_help_option = True
            elif token.startswith("--"):
                option_name, _, value = token[2:].partition("=")
                if not value and option_name not in COMMAND_FLAGS and index + 1 < len(tokens):
                    index += 1
                    value = tokens[index]
                option_value_by_name_map[option_name] = value
            else:
                positional_arguments.append(token)
            index += 1
        if not positional_arguments:
            continue
        command_name = positional_arguments[0]
        if command_name in COMMAND_GROUPS and len(positional_arguments) > 1:
            command_name = f"{command_name} {positional_arguments[1]}"
        episode_id = next((token for token in positional_arguments[1:] + [option_value_by_name_map.get("episode", "")]
                           if EPISODE_ID_PATTERN.match(token)), None)
        scene_ids = (tuple(scene_id.strip() for scene_id in option_value_by_name_map["scenes"].split(",")
                           if scene_id.strip())
                     if option_value_by_name_map.get("scenes") else None)
        runs.append(CommandRun(command_name, episode_id, option_value_by_name_map.get("series") or None, scene_ids,
                               "cover" in option_value_by_name_map, has_help_option))
    return runs


@dataclass(frozen=True)
class Work:
    """What one model call worked on."""

    is_this_series: bool | None  # True: this series; False: something else (another series); None: cannot tell
    episode_id: str | None = None
    step: str | None = None
    runs: tuple[tuple[CommandRun, ToolUse], ...] = ()  # explainer-studio commands it ran on this series
    # the episode whose scenes it wrote (with a file tool, in the episode's scenes/, cover.py, assets/ or preview/) or
    # previewed; reading them does not count
    scene_writing_episode_id: str | None = None


def _resolve_absolute_path(path: str, cwd: str) -> str:
    return os.path.normpath(os.path.join(cwd or "/", os.path.expanduser(path)))


def _check_is_within(path: str, root: str) -> bool:
    return path == root or path.startswith((root + os.sep, root + "/"))


def _resolve_effective_cwd(command: str, cwd: str) -> str:
    """The folder the command's work happens in: its `cd`s applied in order."""
    for match in _CD_PATTERN.finditer(command):
        cd_target = match.group(1).strip("\"'")
        if cd_target and not cd_target.startswith("$") and cd_target != "-":
            cwd = _resolve_absolute_path(cd_target, cwd)
    return cwd


def _resolve_part_context(path: str, series_root_dir_path: str) -> tuple[str | None, str | None] | None:
    """(episode id, step) of a path inside the series folder; None when it is outside."""
    if not _check_is_within(path, series_root_dir_path):
        return None
    parts = PurePosixPath(os.path.relpath(path, series_root_dir_path).replace(os.sep, "/")).parts
    if not parts or parts[0] != PRODUCTION_DIR_NAME:
        return (None, None)
    parts = parts[1:]
    if len(parts) >= 2 and parts[0] == "episodes" and EPISODE_ID_PATTERN.match(parts[1]):
        return (parts[1], STEP_BY_EPISODE_PART_MAP.get(parts[2]) if len(parts) > 2 else None)
    return (None, STEP_BY_SERIES_PART_MAP.get(parts[0]) if parts else None)


def _check_does_look_like_another_series(path: str) -> bool:
    return bool(re.search(r"/production/(plan\.yaml|episodes/ep\d{2,})", path.replace(os.sep, "/")))


def _find_scene_writing_episode_id(call: ModelCall, series_root_dir_path: str) -> str | None:
    """The episode whose scenes the call wrote with a file tool or ran `preview` on; None when it did neither."""
    for tool_use in call.tool_uses:
        if tool_use.kind == "shell" and tool_use.command:
            cwd = _resolve_effective_cwd(tool_use.command, tool_use.cwd)
            for run in parse_command_runs(tool_use.command):
                target_dir_path = _resolve_absolute_path(run.series_path, cwd) if run.series_path else cwd
                if run.name == "preview" and run.episode_id and _check_is_within(target_dir_path, series_root_dir_path):
                    return run.episode_id
        elif tool_use.kind == "file" and tool_use.path and tool_use.does_write_file:
            part_context = _resolve_part_context(_resolve_absolute_path(tool_use.path, tool_use.cwd),
                                                 series_root_dir_path)
            if part_context is not None and part_context[0] is not None and part_context[1] == "scenes":
                return part_context[0]
    return None


def resolve_call_work(call: ModelCall, series_root_dir_path: str) -> Work:
    found_work: Work | None = None
    runs: list[tuple[CommandRun, ToolUse]] = []
    is_elsewhere = False
    for tool_use in call.tool_uses:
        candidates: list[tuple[str | None, str | None]] = []
        if tool_use.kind == "shell" and tool_use.command:
            cwd = _resolve_effective_cwd(tool_use.command, tool_use.cwd)
            for run in parse_command_runs(tool_use.command):
                target_dir_path = _resolve_absolute_path(run.series_path, cwd) if run.series_path else cwd
                if _check_is_within(target_dir_path, series_root_dir_path):
                    runs.append((run, tool_use))
                    if run.is_production:
                        candidates.append((run.episode_id, STEP_BY_COMMAND_MAP[run.name]))
                    elif run.episode_id:
                        candidates.append((run.episode_id, None))
                elif run.is_production:
                    is_elsewhere = True
            for token in _PATH_TOKEN_PATTERN.findall(tool_use.command):
                if "/" in token or token.endswith(_FILE_SUFFIXES):
                    path = _resolve_absolute_path(token, cwd)
                    part_context = _resolve_part_context(path, series_root_dir_path)
                    if part_context is not None:
                        candidates.append(part_context)
                    elif token.startswith("/") and _check_does_look_like_another_series(path):
                        is_elsewhere = True
            # a wait is about what it names, not about the folder it waits in
            part_context = (_resolve_part_context(cwd, series_root_dir_path)
                            if not _SLEEP_PATTERN.search(tool_use.command) else None)
            if part_context is not None:
                candidates.append(part_context)
        elif tool_use.kind == "file" and tool_use.path:
            path = _resolve_absolute_path(tool_use.path, tool_use.cwd)
            part_context = _resolve_part_context(path, series_root_dir_path)
            if part_context is not None:
                candidates.append(part_context)
            elif _check_does_look_like_another_series(path):
                is_elsewhere = True
        for episode_id, step in candidates:
            if found_work is None or (found_work.step is None and step is not None) or \
                    (found_work.episode_id is None and episode_id is not None and found_work.step == step):
                found_work = Work(True, episode_id, step)
        if found_work is not None and found_work.step is not None and found_work.episode_id is not None:
            break
    if found_work is not None:
        return Work(True, found_work.episode_id, found_work.step, tuple(runs),
                    _find_scene_writing_episode_id(call, series_root_dir_path))
    return Work(False if is_elsewhere else None)


# Which step each call belongs to ------------------------------------------------------------------------------------
# Where work is counted: (episode id or None for the series level, step); the step is a `schemas.cost.Step`.
StepKey = tuple[str | None, str]


@dataclass
class Milestones:
    """When the series and each episode reached the moments that move work from one step to the next."""

    viewer_note_saved_seconds: float | None  # the end of the audience step (inclusive)
    plan_saved_seconds: float | None  # the start of the plan step
    plan_review_start_seconds: float | None
    review_start_seconds_by_episode_id_map: dict[str, float]
    narration_start_seconds_by_episode_id_map: dict[str, float]
    render_start_seconds_by_episode_id_map: dict[str, float]
    first_delivery_seconds_by_episode_id_map: dict[str, float]

    def resolve_planning_step(self, moment_seconds: float) -> str:
        if self.plan_review_start_seconds is not None and moment_seconds >= self.plan_review_start_seconds:
            return "plan_review"
        if self.plan_saved_seconds is not None and moment_seconds >= self.plan_saved_seconds:
            return "plan"
        if self.viewer_note_saved_seconds is not None and moment_seconds <= self.viewer_note_saved_seconds:
            return "audience"
        return "deep_reading"

    def resolve_step_key(self, context: Context, moment_seconds: float) -> StepKey:
        episode_id, step = context
        if episode_id is None or step == "planning":
            return (None, self.resolve_planning_step(moment_seconds))
        if moment_seconds >= self.first_delivery_seconds_by_episode_id_map.get(episode_id, float("inf")):
            return (episode_id, "after_delivery")
        if step == "script" and moment_seconds >= self.review_start_seconds_by_episode_id_map.get(episode_id,
                                                                                                 float("inf")):
            is_narrating = moment_seconds >= self.narration_start_seconds_by_episode_id_map.get(episode_id,
                                                                                                float("inf"))
            step = "narration" if is_narrating else "audience_review"
        # scene work after the first render fixes what the whole video showed; the delivery files of an episode that
        # is not delivered yet are being delivered
        elif (step == "scenes"
              and moment_seconds >= self.render_start_seconds_by_episode_id_map.get(episode_id, float("inf"))) \
                or step == "after_delivery":
            step = "render"
        return (episode_id, step)


def _resolve_context(work: Work, current_context: Context | None, has_production_started: bool) -> Context:
    """The context of a call that touched this series, given the one before it in its conversation."""
    episode_id, step = work.episode_id, work.step
    current_episode_id = current_context[0] if current_context and current_context != OTHER_CONTEXT else None
    if episode_id is None:
        # series files touched while making an episode, and episode work that names no episode, belong to the episode
        # being made
        if current_episode_id is None or (step in (None, "planning") and not has_production_started):
            return (None, "planning")
        return (current_episode_id,
                current_context[1] if step in (None, "planning") else step)  # type: ignore[index]
    if step is None:
        return (episode_id, current_context[1] if current_episode_id == episode_id else "script")  # type: ignore[index]
    return (episode_id, step)


def _build_review_prompt_pattern(series: Series) -> re.Pattern[str]:
    """The audience review prompt files of this series (`audience_review._write_prompt_file`), capturing the
    episode id."""
    return re.compile(re.escape(f"audience-review-prompts/{series.root_dir_path.name[:40]}-")
                      + r"(ep\d{2,})-script-review-")


def _fill_gaps[Value](values: list[Value | None]) -> list[Value | None]:
    """Each None takes the next value after it; the Nones after the last value take that value."""
    filled = list(values)
    following_value: Value | None = None
    for index in range(len(filled) - 1, -1, -1):
        if filled[index] is None:
            filled[index] = following_value
        else:
            following_value = filled[index]
    previous_value: Value | None = None
    for index, value in enumerate(filled):
        if value is None:
            filled[index] = previous_value
        else:
            previous_value = value
    return filled


def _resolve_conversation_contexts(conversation: Conversation, works: list[Work], production_start_seconds: float,
                                   review_prompt_pattern: re.Pattern[str]) -> list[Context | None]:
    is_subagent = conversation.started_by_tool_use_id is not None
    contexts: list[Context | None] = [None] * len(conversation.calls)
    current_context: Context | None = None
    for index, (call, work) in enumerate(zip(conversation.calls, works)):
        if work.is_this_series is False:
            current_context = OTHER_CONTEXT
        elif work.is_this_series:
            current_context = _resolve_context(work, current_context, call.time_seconds >= production_start_seconds)
        else:
            continue
        contexts[index] = current_context
    # a call that shows nothing works toward the next step its conversation shows
    contexts = _fill_gaps(contexts)
    if not is_subagent:
        return contexts
    reviewer_match = review_prompt_pattern.search(conversation.opening)
    if reviewer_match:
        # an audience reviewer only reviews; what it does on another series stays out
        return [OTHER_CONTEXT if context == OTHER_CONTEXT else (reviewer_match.group(1), "audience_review")
                for context in contexts]
    scene_writing_episode_id_counter = collections.Counter(
        work.scene_writing_episode_id for work in works if work.scene_writing_episode_id)
    if scene_writing_episode_id_counter:
        # a scene writer writes the scenes of one episode, whatever it reads on the way (another episode's template
        # scene included): the one it wrote or previewed scenes of in the most calls, the first of them on a tie
        [(scene_writing_episode_id, _)] = scene_writing_episode_id_counter.most_common(1)
        return [context if context in (None, OTHER_CONTEXT) else (scene_writing_episode_id, "scenes")
                for context in contexts]
    return contexts


def _record_earliest(moment_seconds_by_episode_id_map: dict[str, float], episode_id: str,
                     moment_seconds: float) -> None:
    moment_seconds_by_episode_id_map[episode_id] = min(moment_seconds_by_episode_id_map.get(episode_id, moment_seconds),
                                                       moment_seconds)


def _check_has_failed(tool_use: ToolUse) -> bool:
    return bool(tool_use.result and _ERROR_LINE_PATTERN.search(tool_use.result))


def _check_was_run_in_background(tool_use: ToolUse) -> bool:
    """Whether the harness ran the command in the background, so its output, and whether it failed, is unknown."""
    return bool(tool_use.result and "running in background" in tool_use.result)


def _parse_timestamp_seconds(timestamp: str) -> float | None:
    try:
        return datetime.fromisoformat(timestamp).timestamp()
    except (ValueError, AttributeError):
        return None


def _convert_seconds_to_local_time(moment_seconds: float) -> datetime:
    """A moment as seconds since the epoch, in local time with its UTC offset, to the second."""
    return datetime.fromtimestamp(moment_seconds).astimezone().replace(microsecond=0)


def _parse_number(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _check_is_waiting(call: ModelCall) -> bool:
    """Every tool the call used only waited: a waiting tool, or a shell command that sleeps and runs no
    explainer-studio command that makes something."""
    def check_does_only_wait(tool_use: ToolUse) -> bool:
        if tool_use.kind == "wait":
            return True
        command = tool_use.command or ""
        return (tool_use.kind == "shell" and bool(_SLEEP_PATTERN.search(command))
                and not any(run.is_production for run in parse_command_runs(command)))

    return bool(call.tool_uses) and all(check_does_only_wait(tool_use) for tool_use in call.tool_uses)


def _resolve_turn_numbers(conversation: Conversation) -> list[int]:
    """Each call's turn: 1 before the person first writes to the agent again after its first call, 2 after that … What
    the person writes between two calls is one turn, however many messages it takes (a slash command and its output
    are two)."""
    turn_numbers: list[int | None] = [None] * len(conversation.calls)
    turn_number, has_model_spoken_since_turn = 1, False
    for event in conversation.events:
        if event.kind == "model" and event.call_index is not None:
            if turn_numbers[event.call_index] is None:
                turn_numbers[event.call_index] = turn_number
            has_model_spoken_since_turn = True
        elif event.kind == "person" and has_model_spoken_since_turn:
            turn_number += 1
            has_model_spoken_since_turn = False
    return [number or 1 for number in turn_numbers]


def _resolve_agent_kind(conversation: Conversation, conversation_works: list[Work],
                        review_prompt_pattern: re.Pattern[str]) -> str:
    if conversation.started_by_tool_use_id is None:
        return "main"
    if review_prompt_pattern.search(conversation.opening):
        return "audience_reviewer"
    if any(work.scene_writing_episode_id for work in conversation_works):
        return "scene_writer"
    return "other_subagent"


def _check_does_make_file(tool_use: ToolUse, series_root_dir_path: str) -> bool:
    """A file tool that wrote a file in production/, feedback and delivery records aside."""
    if tool_use.kind != "file" or not tool_use.does_write_file or not tool_use.path:
        return False
    path = _resolve_absolute_path(tool_use.path, tool_use.cwd)
    if not _check_is_within(path, os.path.join(series_root_dir_path, PRODUCTION_DIR_NAME)):
        return False
    part_context = _resolve_part_context(path, series_root_dir_path)
    return part_context is None or part_context[1] != "after_delivery"


def _check_does_make(conversation: Conversation, conversation_works: list[Work], series_root_dir_path: str) -> bool:
    """Whether the conversation made something in the series: ran a making command or wrote a production file."""
    return (any(run.name in MAKING_COMMANDS and not run.has_help_option
                for work in conversation_works for run, _ in work.runs)
            or any(_check_does_make_file(tool_use, series_root_dir_path)
                   for call in conversation.calls for tool_use in call.tool_uses))


def _find_planning_boundaries(series: Series, conversations: list[Conversation], works: list[list[Work]],
                              conversation_indices: list[int]) -> tuple[float | None, float | None, float | None]:
    """When the viewer note was first saved, when plan.yaml was first saved after a deep-reading note (or after the
    viewer note when there is none), and when the person first wrote after the plan page was first opened."""
    research_dir_path = os.path.normpath(os.path.join(str(series.root_dir_path), PRODUCTION_DIR_NAME, "research"))
    plan_file_path = os.path.normpath(str(series.plan_file_path))
    viewer_note_moments, reading_note_moments, plan_save_moments = [], [], []
    plan_opens: list[tuple[float, int]] = []
    for index in conversation_indices:
        for call, work in zip(conversations[index].calls, works[index]):
            for tool_use in call.tool_uses:
                if tool_use.kind != "file" or not tool_use.does_write_file or not tool_use.path:
                    continue
                path = _resolve_absolute_path(tool_use.path, tool_use.cwd)
                if path == plan_file_path:
                    plan_save_moments.append(call.time_seconds)
                elif _check_is_within(path, research_dir_path) and path != research_dir_path:
                    (viewer_note_moments if _VIEWER_NOTE_PATTERN.search(os.path.basename(path))
                     else reading_note_moments).append(call.time_seconds)
            plan_opens += [(call.time_seconds, index) for run, tool_use in work.runs
                           if run.name == "plan open" and not run.has_help_option and not _check_has_failed(tool_use)]
    viewer_note_saved_seconds = min(viewer_note_moments, default=None)
    # notes saved before the viewer note are step 1's probes, not deep reading
    reading_start_seconds = min((moment_seconds for moment_seconds in reading_note_moments
                                 if viewer_note_saved_seconds is None or moment_seconds > viewer_note_saved_seconds),
                                default=None) or viewer_note_saved_seconds
    plan_saved_seconds = min((moment_seconds for moment_seconds in plan_save_moments
                              if reading_start_seconds is None or moment_seconds > reading_start_seconds), default=None)
    plan_review_start_seconds = None
    if plan_opens:
        plan_open_seconds, index = min(plan_opens)
        plan_review_start_seconds = min((event.time_seconds for event in conversations[index].events
                                         if event.kind == "person" and event.time_seconds > plan_open_seconds),
                                        default=None)
    return viewer_note_saved_seconds, plan_saved_seconds, plan_review_start_seconds


def _compute_working_seconds(intervals: list[tuple[float, float, StepKey]]) -> dict[StepKey, float]:
    """Seconds per step; a moment covered by several conversations is shared between them."""
    boundaries = []
    for start_seconds, end_seconds, key in set(intervals):  # a resumed conversation repeats the events it copied
        boundaries += [(start_seconds, 1, key), (end_seconds, -1, key)]
    boundaries.sort(key=lambda boundary: (boundary[0], boundary[1]))
    open_count_by_step_key_map: collections.Counter = collections.Counter()
    working_seconds_by_step_key_map: dict[StepKey, float] = collections.defaultdict(float)
    last_moment_seconds = None
    for moment_seconds, change, key in boundaries:
        running_count = sum(open_count_by_step_key_map.values())
        if last_moment_seconds is not None and moment_seconds > last_moment_seconds and running_count:
            for open_key, count in open_count_by_step_key_map.items():
                if count:
                    working_seconds_by_step_key_map[open_key] += (
                        (moment_seconds - last_moment_seconds) * count / running_count)
        open_count_by_step_key_map[key] += change
        last_moment_seconds = moment_seconds
    return working_seconds_by_step_key_map


def _read_raw_yaml(path: Path) -> Any:
    try:
        return convert_yaml_document_to_plain_data(read_yaml_document(path)) if path.exists() else None
    except (StudioError, OSError, ValueError):  # a file the agent is halfway through editing
        return None


# The report ---------------------------------------------------------------------------------------------------------
def compute_cost_report(series: Series) -> CostReport:
    """Never raises for what it cannot read: the report says what is missing instead."""
    try:
        harness_conversations = read_harness_conversations(series.root_dir_path)
    except OSError as error:
        # the reason travels in feedback bundles, so it names the error without the path it was about
        return CostReport(unavailable_reason=(
            f"could not read the agent's transcripts: {error.strerror or type(error).__name__}"))
    if harness_conversations is None:
        return CostReport(unavailable_reason=(
            "no Claude Code conversation that worked on this series was found on this computer (only Claude Code's "
            "transcripts can be read so far, and Claude Code deletes them after 30 days by default)"))
    return _compute_cost_report_from_conversations(series, harness_conversations)


def _compute_cost_report_from_conversations(series: Series,
                                            harness_conversations: HarnessConversations) -> CostReport:
    series_root_dir_path = str(series.root_dir_path)
    conversations = harness_conversations.conversations
    works = [[resolve_call_work(call, series_root_dir_path) for call in conversation.calls]
             for conversation in conversations]

    # conversations that made something in this series, and the subagents they started (and theirs)
    conversation_index_by_tool_use_id_map = {tool_use.id: index for index, conversation in enumerate(conversations)
                                             for call in conversation.calls for tool_use in call.tool_uses}
    depth_by_conversation_index_map = {
        index: 0 for index, conversation_works in enumerate(works)
        if conversations[index].started_by_tool_use_id is None
        and _check_does_make(conversations[index], conversation_works, series_root_dir_path)}
    if not depth_by_conversation_index_map:
        return CostReport(unavailable_reason=(
            "no conversation on this computer made something in this series (ran explainer-studio making commands or "
            "wrote its production files)"))
    while True:
        depth_by_started_conversation_index_map = {
            index: depth_by_conversation_index_map[
                conversation_index_by_tool_use_id_map[conversation.started_by_tool_use_id]] + 1  # type: ignore[index]
            for index, conversation in enumerate(conversations)
            if index not in depth_by_conversation_index_map
            and conversation_index_by_tool_use_id_map.get(conversation.started_by_tool_use_id or "")
            in depth_by_conversation_index_map}
        if not depth_by_started_conversation_index_map:
            break
        depth_by_conversation_index_map.update(depth_by_started_conversation_index_map)
    # each subagent after the conversation that started it
    included_conversation_indices = sorted(depth_by_conversation_index_map,
                                           key=lambda index: depth_by_conversation_index_map[index])

    review_prompt_pattern = _build_review_prompt_pattern(series)
    episode_call_moments_seconds = [call.time_seconds for index in included_conversation_indices
                                    for call, work in zip(conversations[index].calls, works[index])
                                    if work.episode_id]
    production_start_seconds = min(episode_call_moments_seconds, default=float("inf"))
    # when each episode first reached a step; a command that printed an error did not reach it
    review_start_seconds_by_episode_id_map: dict[str, float] = {}
    narration_start_seconds_by_episode_id_map: dict[str, float] = {}
    render_start_seconds_by_episode_id_map: dict[str, float] = {}
    milestone_map_by_command_map = {"script prepare-audience-review-prompt": review_start_seconds_by_episode_id_map,
                                    "narrate": narration_start_seconds_by_episode_id_map,
                                    "render": render_start_seconds_by_episode_id_map}
    runs_by_episode_id_map: dict[str, list[tuple[float, CommandRun, bool]]] = collections.defaultdict(list)
    counted_call_ids: set[str] = set()
    for index in included_conversation_indices:
        for call, work in zip(conversations[index].calls, works[index]):
            if call.id in counted_call_ids:  # a resumed conversation repeats the calls it copied
                continue
            counted_call_ids.add(call.id)
            for run, tool_use in work.runs:
                if not run.is_production or not run.episode_id:
                    continue
                has_failed = _check_has_failed(tool_use)
                runs_by_episode_id_map[run.episode_id].append((call.time_seconds, run, has_failed))
                # narrate in the background may still be refused: then the first paid call below says it started
                if run.name in milestone_map_by_command_map and not has_failed \
                        and not (run.name == "narrate" and _check_was_run_in_background(tool_use)):
                    _record_earliest(milestone_map_by_command_map[run.name], run.episode_id, call.time_seconds)
        reviewer_match = review_prompt_pattern.search(conversations[index].opening)
        if reviewer_match and conversations[index].calls:
            _record_earliest(review_start_seconds_by_episode_id_map, reviewer_match.group(1),
                             conversations[index].calls[0].time_seconds)
    spending_records = _read_narration_spending_records(series)
    for record in spending_records:
        moment_seconds = _parse_timestamp_seconds(str(record.get("spent_at") or ""))
        if isinstance(record.get("episode_id"), str) and moment_seconds is not None:
            _record_earliest(narration_start_seconds_by_episode_id_map, record["episode_id"], moment_seconds)

    episode_ids = sorted({work.episode_id for index in included_conversation_indices for work in works[index]
                          if work.episode_id}
                         | {episode_id for episode_id, _ in _read_plan_episodes(series)}
                         | {str(record["episode_id"]) for record in spending_records
                            if EPISODE_ID_PATTERN.match(str(record.get("episode_id") or ""))},
                         key=lambda episode_id: int(
                             EPISODE_ID_PATTERN.match(episode_id).group(1)))  # type: ignore[union-attr]
    first_delivery_by_episode_id_map = {episode_id: first_delivery for episode_id in episode_ids
                                        if (first_delivery := _find_first_delivery(series, episode_id))}
    milestones = Milestones(*_find_planning_boundaries(series, conversations, works, included_conversation_indices),
                            review_start_seconds_by_episode_id_map, narration_start_seconds_by_episode_id_map,
                            render_start_seconds_by_episode_id_map,
                            {episode_id: moment_seconds
                             for episode_id, (moment_seconds, _, _) in first_delivery_by_episode_id_map.items()})

    contexts_by_conversation_index_map: dict[int, list[Context | None]] = {}
    call_position_by_tool_use_id_map: dict[str, tuple[int, int]] = {}
    for index in included_conversation_indices:
        conversation = conversations[index]
        conversation_contexts = _resolve_conversation_contexts(conversation, works[index], production_start_seconds,
                                                               review_prompt_pattern)
        if conversation.started_by_tool_use_id is not None \
                and all(context is None for context in conversation_contexts):
            parent_call_position = call_position_by_tool_use_id_map.get(conversation.started_by_tool_use_id)
            inherited_context = (contexts_by_conversation_index_map[parent_call_position[0]][parent_call_position[1]]
                                 if parent_call_position else None)
            conversation_contexts = [inherited_context] * len(conversation_contexts)
        contexts_by_conversation_index_map[index] = conversation_contexts
        for call_index, call in enumerate(conversation.calls):
            for tool_use in call.tool_uses:
                call_position_by_tool_use_id_map[tool_use.id] = (index, call_index)

    # every counted call once, with its step and turn, in time order; the agents in the order of their first call
    counted_calls: list[tuple[ModelCall, int, StepKey, int]] = []
    seen_call_ids: set[str] = set()
    for index in included_conversation_indices:
        conversation = conversations[index]
        turn_numbers = _resolve_turn_numbers(conversation)
        for call_index, (call, context) in enumerate(zip(conversation.calls, contexts_by_conversation_index_map[index])):
            if context is None or context == OTHER_CONTEXT or call.id in seen_call_ids \
                    or call.model_name == "<synthetic>":
                continue
            seen_call_ids.add(call.id)
            counted_calls.append((call, index, milestones.resolve_step_key(context, call.time_seconds),
                                  turn_numbers[call_index]))
    counted_calls.sort(key=lambda counted_call: counted_call[0].time_seconds)
    # a resumed conversation repeats the calls of the one it resumes: they are one agent, known by their first call
    def get_agent_key(index: int) -> str | None:
        return conversations[index].calls[0].id if conversations[index].calls else None

    agent_id_by_agent_key_map: dict[str | None, str] = {}
    conversation_index_by_agent_key_map: dict[str | None, int] = {}
    model_calls = []
    for call, index, (episode_id, step), turn_number in counted_calls:
        agent_id = agent_id_by_agent_key_map.setdefault(get_agent_key(index),
                                                        f"agent-{len(agent_id_by_agent_key_map) + 1}")
        conversation_index_by_agent_key_map.setdefault(get_agent_key(index), index)
        model_calls.append(CostReportModelCall(
            called_at=_convert_seconds_to_local_time(call.time_seconds), agent_id=agent_id, episode_id=episode_id,
            step=step, turn_number=turn_number, model_name=call.model_name, effort=call.effort, speed=call.speed,
            is_waiting=_check_is_waiting(call), token_usage=call.token_usage))
    agents = []
    for agent_key, agent_id in agent_id_by_agent_key_map.items():
        index = conversation_index_by_agent_key_map[agent_key]
        # the agent that started it: the nearest ancestor with counted calls of its own
        parent_index = conversation_index_by_tool_use_id_map.get(conversations[index].started_by_tool_use_id or "")
        while parent_index is not None and get_agent_key(parent_index) not in agent_id_by_agent_key_map:
            parent_index = conversation_index_by_tool_use_id_map.get(
                conversations[parent_index].started_by_tool_use_id or "")
        agents.append(CostReportAgent(
            id=agent_id, harness_name=harness_conversations.harness_name,
            kind=_resolve_agent_kind(conversations[index], works[index], review_prompt_pattern),
            parent_agent_id=agent_id_by_agent_key_map[get_agent_key(parent_index)] if parent_index is not None
            else None))

    intervals = []
    long_command_tool_use_ids = {tool_use.id for index in included_conversation_indices for work in works[index]
                                 for run, tool_use in work.runs if run.name in LONG_COMMANDS}
    for index in included_conversation_indices:
        conversation, conversation_contexts = conversations[index], contexts_by_conversation_index_map[index]
        previous_moment_seconds, last_call_index = None, None
        for event in conversation.events:
            if event.kind == "model":
                last_call_index = event.call_index
            call_index = event.call_index if event.call_index is not None else last_call_index
            context = conversation_contexts[call_index] if call_index is not None else None
            if previous_moment_seconds is not None and event.kind != "person" and context not in (None, OTHER_CONTEXT):
                interval_seconds = event.time_seconds - previous_moment_seconds
                is_explained = event.kind == "notification" or event.tool_use_id in long_command_tool_use_ids
                if interval_seconds > 0 and (interval_seconds <= MAX_COUNTED_IDLE_SECONDS or is_explained):
                    # counted where its model call is: the time deliver runs is delivering, not work after it
                    moment_seconds = conversation.calls[call_index].time_seconds  # type: ignore[index]
                    step_key = milestones.resolve_step_key(context, moment_seconds)  # type: ignore[arg-type]
                    intervals.append((previous_moment_seconds, event.time_seconds, step_key))
            previous_moment_seconds = event.time_seconds
    working_seconds_by_step_key_map = _compute_working_seconds(intervals)

    narration_calls = []
    for record in spending_records:
        episode_id = record.get("episode_id")
        moment_seconds = _parse_timestamp_seconds(str(record.get("spent_at") or ""))
        if not isinstance(episode_id, str) or moment_seconds is None:
            continue
        narration_calls.append((moment_seconds, CostReportNarrationCall(
            called_at=_convert_seconds_to_local_time(moment_seconds), episode_id=episode_id,
            step=milestones.resolve_step_key((episode_id, "narration"), moment_seconds)[1],
            provider_name=str(record.get("provider_name") or ""),
            character_count=int(_parse_number(record.get("character_count"))),
            cost_usd=_parse_number(record.get("cost_usd")), is_estimated=record.get("is_estimated") is not False)))
    narration_calls.sort(key=lambda entry: entry[0])

    step_keys = ({(model_call.episode_id, model_call.step) for model_call in model_calls}
                    | {(narration_call.episode_id, narration_call.step) for _, narration_call in narration_calls}
                    | set(working_seconds_by_step_key_map))
    steps = [CostReportStep(step=step, working_duration_seconds=round(working_seconds_by_step_key_map.get(
        (None, step), 0))) for step in PLANNING_STEPS if (None, step) in step_keys]
    for episode_id in episode_ids:
        first_delivery = first_delivery_by_episode_id_map.get(episode_id)
        # the commands that made the episode up to its first delivery
        runs = [run for moment_seconds, run, has_failed in runs_by_episode_id_map[episode_id]
                if not has_failed and (first_delivery is None or moment_seconds < first_delivery[0])]
        count_by_field_map_by_step_map = {
            "audience_review": {"round_count": sum(run.name == "script prepare-audience-review-prompt"
                                                   for run in runs)},
            "scenes": {"scene_preview_count": _count_scene_previews(series, episode_id, runs)},
            "render": {"render_count": sum(run.name == "render" for run in runs)}}
        steps += [CostReportStep(episode_id=episode_id, step=step,
                                 working_duration_seconds=round(working_seconds_by_step_key_map.get(
                                     (episode_id, step), 0)),
                                 **count_by_field_map_by_step_map.get(step, {}))
                  for step in (*EPISODE_STEPS, "after_delivery") if (episode_id, step) in step_keys]
    episodes = [CostReportEpisode(episode_id=episode_id, first_delivery=_load_delivery_summary(
        series, *first_delivery_by_episode_id_map[episode_id][1:]) if episode_id in first_delivery_by_episode_id_map
        else None) for episode_id in episode_ids]
    return CostReport(episodes=episodes, agents=agents, steps=steps, model_calls=model_calls,
                      narration_calls=[narration_call for _, narration_call in narration_calls])


def _read_plan_episodes(series: Series) -> list[tuple[str, str]]:
    plan = _read_raw_yaml(series.plan_file_path)
    episode_entries = plan.get("episodes") if isinstance(plan, dict) else None
    return [(str(entry.get("id")), str(entry.get("title") or "")) for entry in episode_entries or []
            if isinstance(entry, dict) and EPISODE_ID_PATTERN.match(str(entry.get("id") or ""))]


def _read_narration_spending_records(series: Series) -> list[dict[str, Any]]:
    """The narration records in spending.jsonl, unvalidated; none when the file cannot be read."""
    try:
        return read_narration_spending_records(series)
    except (StudioError, OSError):
        return []


def _find_first_delivery(series: Series, episode_id: str) -> tuple[float, DeliveryRecord, Path] | None:
    """The episode's first delivery with when it was made and its record folder; None when it has none. A damaged
    record is left out."""
    try:
        record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
    except OSError:
        return None
    for record_dir_path in record_dir_paths:
        try:
            record = load_delivery_record(series, record_dir_path)
        except (StudioError, OSError, ValueError):
            continue
        return (record.delivered_at.timestamp(), record, record_dir_path)
    return None


def _load_delivery_summary(series: Series, record: DeliveryRecord, record_dir_path: Path) -> DeliverySummary:
    try:
        timeline = load_delivered_timeline(series, record_dir_path)
    except (StudioError, OSError):
        timeline = None
    return DeliverySummary(delivered_at=record.delivered_at, explainer_studio_version=record.explainer_studio_version,
                           duration_seconds=timeline.duration_seconds if timeline else None,
                           scene_count=len(timeline.scenes) if timeline else None)


def _count_scene_previews(series: Series, episode_id: str, runs: list[CommandRun]) -> int:
    script = _read_raw_yaml(series.get_episode_paths(episode_id).script_file_path)
    scenes = script.get("scenes") if isinstance(script, dict) else None
    scene_count = sum(isinstance(scene, dict) for scene in scenes) if isinstance(scenes, list) else 0
    # previewing only the cover (`--cover` without `--scenes`) renders no scene
    return sum(len(run.scene_ids) if run.scene_ids is not None else 0 if run.has_cover_option else scene_count
               for run in runs if run.name == "preview")


# Output ---------------------------------------------------------------------------------------------------------------
def filter_cost_report_to_episode(report: CostReport, episode_id: str) -> CostReport:
    """The series' planning and this episode, with the agents that worked on them: what a feedback bundle carries."""
    def check_is_kept(owner_episode_id: str | None) -> bool:
        return owner_episode_id in (None, episode_id)

    model_calls = [model_call for model_call in report.model_calls if check_is_kept(model_call.episode_id)]
    agent_by_id_map = {agent.id: agent for agent in report.agents}
    kept_agent_ids: set[str] = set()
    for model_call in model_calls:
        agent_id: str | None = model_call.agent_id
        while agent_id is not None and agent_id not in kept_agent_ids:
            kept_agent_ids.add(agent_id)
            agent_id = agent_by_id_map[agent_id].parent_agent_id
    return report.model_copy(update={
        "episodes": [episode for episode in report.episodes if episode.episode_id == episode_id],
        "agents": [agent for agent in report.agents if agent.id in kept_agent_ids],
        "steps": [step for step in report.steps if check_is_kept(step.episode_id)],
        "model_calls": model_calls,
        "narration_calls": [narration_call for narration_call in report.narration_calls
                            if check_is_kept(narration_call.episode_id)]})


def list_steps(report: CostReport, episode_id: str | None, step_names: tuple[str, ...]) -> list[CostReportStep]:
    """The named steps of the series (`episode_id` None) or of an episode, in order; a step without work is empty."""
    step_by_name_map = {step.step: step for step in report.steps if step.episode_id == episode_id}
    return [step_by_name_map.get(step_name) or CostReportStep(episode_id=episode_id, step=step_name)  # type: ignore[arg-type]
            for step_name in step_names]


def find_episode(report: CostReport, episode_id: str) -> CostReportEpisode | None:
    return next((episode for episode in report.episodes if episode.episode_id == episode_id), None)


def check_has_episode_work(report: CostReport, episode_id: str) -> bool:
    """Whether the transcripts hold any work on the episode (another computer may have made it)."""
    return any(step.episode_id == episode_id for step in report.steps)


def get_step_count(step: CostReportStep) -> int | None:
    """What the step counts (audience review rounds, scene previews, renders); None for a step that counts nothing."""
    return getattr(step, COUNT_FIELD_BY_STEP_MAP[step.step]) if step.step in COUNT_FIELD_BY_STEP_MAP else None


def compute_elapsed_seconds(report: CostReport, episode_id: str) -> float | None:
    """From the episode's first model call to its first delivery."""
    episode = find_episode(report, episode_id)
    delivered_seconds = (episode.first_delivery.delivered_at.timestamp()
                         if episode and episode.first_delivery else None)
    start_moments_seconds = [model_call.called_at.timestamp() for model_call in report.model_calls
                             if model_call.episode_id == episode_id and model_call.step != "after_delivery"]
    if delivered_seconds is None or not start_moments_seconds:
        return None
    return delivered_seconds - min(start_moments_seconds)


@dataclass(frozen=True)
class WorkTotals:
    """One or more steps added up, as they are shown."""

    working_duration_seconds: int
    call_count: int
    token_count: int
    narration_character_count: int
    narration_cost_usd: float
    agent_cost_usd: float | None  # the model calls at the price table's prices; None without a price table
    unpriced_model_names: tuple[str, ...]  # names of the models without a price, left out of agent_cost_usd


def build_work_totals(report: CostReport, steps: list[CostReportStep], prices: list[ModelPrice] | None) -> WorkTotals:
    """The steps' working time, and the sum of the model and narration calls that belong to them."""
    step_keys = {(step.episode_id, step.step) for step in steps}
    model_calls = [model_call for model_call in report.model_calls
                   if (model_call.episode_id, model_call.step) in step_keys]
    narration_calls = [narration_call for narration_call in report.narration_calls
                       if (narration_call.episode_id, narration_call.step) in step_keys]
    estimate = estimate_cost_usd(model_calls, prices) if prices is not None else None
    return WorkTotals(
        working_duration_seconds=sum(step.working_duration_seconds for step in steps),
        call_count=len(model_calls),
        token_count=sum(sum(model_call.token_usage.model_dump().values()) for model_call in model_calls),
        narration_character_count=sum(narration_call.character_count for narration_call in narration_calls),
        narration_cost_usd=sum(narration_call.cost_usd for narration_call in narration_calls),
        agent_cost_usd=estimate.cost_usd if estimate is not None else None,
        unpriced_model_names=estimate.unpriced_model_names if estimate is not None else ())


def _format_minutes(seconds: float) -> str:
    minutes = seconds / 60
    return f"{minutes:.0f} min" if minutes >= 10 else f"{minutes:.1f} min"


def _format_token_count(token_count: int) -> str:
    if token_count >= 1_000_000:
        return f"{token_count / 1_000_000:.1f}M"
    return f"{token_count / 1000:.0f}K" if token_count >= 1000 else str(token_count)


def format_work_totals(totals: WorkTotals) -> str:
    text = (f"{_format_minutes(totals.working_duration_seconds)} of work, {totals.call_count} model calls, "
            f"{_format_token_count(totals.token_count)} tokens")
    if totals.narration_cost_usd or totals.narration_character_count:
        text += (f", narration ${totals.narration_cost_usd:.2f} for {totals.narration_character_count:,} "
                 "characters")
    if totals.agent_cost_usd is not None:
        text += f"; agent ≈ ${totals.agent_cost_usd:.2f}"
    return text


def format_episode_cost(report: CostReport, episode_id: str, prices: list[ModelPrice] | None = None) -> str:
    """One line: what making the episode took up to its first delivery, or so far while it is being made."""
    episode = find_episode(report, episode_id)
    totals = build_work_totals(report, list_steps(report, episode_id, EPISODE_STEPS), prices)
    elapsed_seconds = compute_elapsed_seconds(report, episode_id)
    span = f" ({_format_minutes(elapsed_seconds)} from start to delivery)" if elapsed_seconds else ""
    text = (f"{'up to the first delivery' if episode and episode.first_delivery else 'so far'}{span}: "
            f"{format_work_totals(totals)}")
    if totals.agent_cost_usd is not None:
        text += f", ≈ ${totals.agent_cost_usd + totals.narration_cost_usd:.2f} in all"
    return text


def _format_model_calls(report: CostReport, steps: list[CostReportStep]) -> str:
    step_keys = {(step.episode_id, step.step) for step in steps}
    kind_by_agent_id_map = {agent.id: agent.kind for agent in report.agents}
    call_count_by_settings_map_by_who_map: dict[str, collections.Counter] = {
        "main agent": collections.Counter(), "subagents": collections.Counter()}
    for model_call in report.model_calls:
        if (model_call.episode_id, model_call.step) not in step_keys:
            continue
        who = "main agent" if kind_by_agent_id_map.get(model_call.agent_id) == "main" else "subagents"
        settings = " ".join(part for part in (model_call.model_name, model_call.effort,
                                              model_call.speed if model_call.speed not in (None, "standard") else None)
                            if part)
        call_count_by_settings_map_by_who_map[who][settings] += 1
    parts = [f"{who} " + ", ".join(f"{settings} × {count}" for settings, count in counts.items())
             for who, counts in call_count_by_settings_map_by_who_map.items() if counts]
    return "; ".join(parts) or "none"


def format_cost_report(report: CostReport, series: Series, prices: list[ModelPrice] | None = None) -> list[str]:
    if report.unavailable_reason is not None:
        return [f"cost: not available ({report.unavailable_reason})"]
    harness_display_names = list(dict.fromkeys(
        HARNESS_DISPLAY_NAME_BY_NAME_MAP.get(agent.harness_name, agent.harness_name) for agent in report.agents))
    lines = [f"cost of {series.root_dir_path.name}, from {' and '.join(harness_display_names) or 'the harness'}'s "
             "transcripts and spending.jsonl"
             + ("; agent dollars at the local price table's prices (an estimate: on a subscription the usage counts "
                "toward the plan instead)" if prices is not None else "")]
    unpriced_model_names: dict[str, None] = {}

    def format_totals(steps: list[CostReportStep]) -> str:
        totals = build_work_totals(report, steps, prices)
        unpriced_model_names.update(dict.fromkeys(totals.unpriced_model_names))
        return format_work_totals(totals)

    if any(step.episode_id is None for step in report.steps):
        planning_steps = list_steps(report, None, PLANNING_STEPS)
        lines.append(f"planning: {format_totals(planning_steps)}")
        lines += [f"  {LABEL_BY_STEP_MAP[step.step]}: {format_totals([step])}" for step in planning_steps]
    title_by_episode_id_map = dict(_read_plan_episodes(series))
    count_unit_by_step_map = {"audience_review": "round(s)", "scenes": "scene preview(s)", "render": "render(s)"}
    for episode in report.episodes:
        if not check_has_episode_work(report, episode.episode_id):
            continue
        title = (f" \"{title_by_episode_id_map[episode.episode_id]}\""
                 if title_by_episode_id_map.get(episode.episode_id) else "")
        first_delivery = episode.first_delivery
        if first_delivery is None:
            lines.append(f"{episode.episode_id}{title} (not delivered yet)")
        else:
            video_note = (f"; a {first_delivery.duration_seconds / 60:.1f} min video in {first_delivery.scene_count} "
                          "scenes" if first_delivery.duration_seconds is not None else "")
            lines.append(f"{episode.episode_id}{title} (first delivered {first_delivery.delivered_at.isoformat()} with "
                         f"Explainer Studio {first_delivery.explainer_studio_version}{video_note})")
        lines.append(f"  {format_episode_cost(report, episode.episode_id, prices)}")
        episode_steps = list_steps(report, episode.episode_id, EPISODE_STEPS)
        for step in episode_steps:
            count = get_step_count(step)
            note = f" ({count} {count_unit_by_step_map[step.step]})" if count is not None else ""
            lines.append(f"    {LABEL_BY_STEP_MAP[step.step]}{note}: {format_totals([step])}")
        [after_delivery] = list_steps(report, episode.episode_id, ("after_delivery",))
        if any(step.episode_id == episode.episode_id and step.step == "after_delivery" for step in report.steps):
            lines.append(f"  {LABEL_BY_STEP_MAP['after_delivery']}: {format_totals([after_delivery])}")
        lines.append(f"  model calls up to the first delivery: {_format_model_calls(report, episode_steps)}")
    if unpriced_model_names:
        lines.append(f"no price in the price table for {', '.join(unpriced_model_names)}: left out of the dollars")
    return lines
