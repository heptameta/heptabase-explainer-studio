"""Claude Code's transcripts.

A conversation is `<projects>/<slug>/<session>.jsonl`, where `<projects>` is `~/.claude/projects` (or
`$CLAUDE_CONFIG_DIR/projects`) and `<slug>` is the folder Claude Code started in with every character other than a
letter or digit replaced by `-`. Its subagents are `<session>/subagents/agent-<id>.jsonl`, each with a
`agent-<id>.meta.json` naming the tool use that started it. One line per message; a
model call's output can span several lines with the same message id, the last of which carries its final token counts,
and each carries the reasoning effort (`effort`) the call asked for.

The conversations read are those that started in the series folder or a folder above it, plus the one running this
command (`CLAUDE_CODE_SESSION_ID`), when they mention the series folder.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schemas.cost import TokenUsage
from . import Conversation, ConversationEvent, ModelCall, ToolUse

SESSION_ENV = "CLAUDE_CODE_SESSION_ID"
PATH_PARAMETER_BY_FILE_TOOL_MAP = {"Read": "file_path", "Write": "file_path", "Edit": "file_path",
                                   "MultiEdit": "file_path", "NotebookEdit": "notebook_path", "Glob": "path",
                                   "Grep": "path"}
FILE_WRITING_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SUBAGENT_TOOLS = {"Agent", "Task"}
# tools that only wait: for a background task's output, for a monitored condition, or until a set time
WAITING_TOOLS = {"TaskOutput", "BashOutput", "Monitor", "ScheduleWakeup"}
CHUNK_BYTES = 8 << 20


def get_projects_dir_path() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"


def _convert_path_to_project_slug(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def _check_does_mention(path: Path, needles: list[bytes]) -> bool:
    """Whether the file contains one of `needles`, read in chunks so a large conversation is never loaded whole."""
    overlap = max(len(needle) for needle in needles)
    tail = b""
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_BYTES):
                window = tail + chunk
                if any(needle in window for needle in needles):
                    return True
                tail = window[-overlap:]
    except OSError:
        return False
    return False


def find_conversation_file_paths(series_root_dir_path: Path) -> list[Path]:
    projects_dir_path = get_projects_dir_path()
    if not projects_dir_path.is_dir():
        return []
    candidates: set[Path] = set()
    for candidate_dir_path in [series_root_dir_path, *series_root_dir_path.parents]:
        candidates.update((projects_dir_path / _convert_path_to_project_slug(candidate_dir_path)).glob("*.jsonl"))
    session_id = os.environ.get(SESSION_ENV, "").strip()
    if re.fullmatch(r"[0-9a-fA-F-]{8,}", session_id):
        candidates.update(projects_dir_path.glob(f"*/{session_id}.jsonl"))
    series_root_text = str(series_root_dir_path)
    needles = list({series_root_text.encode(), json.dumps(series_root_text)[1:-1].encode()})
    return sorted(path for path in candidates if _check_does_mention(path, needles))


def read_conversations(series_root_dir_path: Path) -> list[Conversation]:
    conversations = []
    for conversation_file_path in find_conversation_file_paths(series_root_dir_path):
        conversations.append(read_conversation(conversation_file_path))
        for subagent_file_path in sorted((conversation_file_path.parent / conversation_file_path.stem / "subagents")
                                         .glob("agent-*.jsonl")):
            conversations.append(read_conversation(subagent_file_path,
                                                   _read_started_by_tool_use_id(subagent_file_path)))
    return [conversation for conversation in conversations if conversation.calls]


def _read_started_by_tool_use_id(subagent_file_path: Path) -> str | None:
    """The tool use that started a subagent."""
    try:
        metadata_file_path = subagent_file_path.with_name(subagent_file_path.stem + ".meta.json")
        metadata = json.loads(metadata_file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    tool_use_id = metadata.get("toolUseId") if isinstance(metadata, dict) else None
    return tool_use_id if isinstance(tool_use_id, str) else None


def _parse_timestamp_seconds(timestamp: str) -> float | None:
    try:
        return datetime.fromisoformat(timestamp).timestamp()
    except (ValueError, AttributeError):
        return None


def _parse_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(block.get("text", "")) for block in content
                         if isinstance(block, dict) and block.get("type") == "text")
    return ""


def _convert_usage_to_token_usage(usage: dict[str, Any]) -> TokenUsage:
    """A call's token usage. Some lines give it only per iteration, with zeros at the top level."""
    iterations = usage.get("iterations")
    if isinstance(iterations, list) and not any(usage.get(key) for key in (
            "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")):
        iteration_usages = [_convert_usage_to_token_usage(iteration) for iteration in iterations
                            if isinstance(iteration, dict)]
        return TokenUsage(**{name: sum(getattr(iteration_usage, name) for iteration_usage in iteration_usages)
                             for name in TokenUsage.model_fields})
    cache_creation = usage.get("cache_creation") or {}
    if cache_creation:
        five_minute_cache_write_tokens = cache_creation.get("ephemeral_5m_input_tokens") or 0
        one_hour_cache_write_tokens = cache_creation.get("ephemeral_1h_input_tokens") or 0
    else:
        five_minute_cache_write_tokens, one_hour_cache_write_tokens = usage.get("cache_creation_input_tokens") or 0, 0
    return TokenUsage(non_cached_input_tokens=usage.get("input_tokens") or 0,
                      cache_read_tokens=usage.get("cache_read_input_tokens") or 0,
                      five_minute_cache_write_tokens=five_minute_cache_write_tokens,
                      one_hour_cache_write_tokens=one_hour_cache_write_tokens,
                      output_tokens=usage.get("output_tokens") or 0)


def _convert_content_block_to_tool_use(block: dict[str, Any], cwd: str) -> ToolUse:
    tool_name, tool_input = block.get("name", ""), block.get("input") or {}
    tool_use_id = str(block.get("id") or "")
    if tool_name == "Bash":
        return ToolUse(tool_use_id, "shell", cwd, command=str(tool_input.get("command") or ""))
    if tool_name in PATH_PARAMETER_BY_FILE_TOOL_MAP:
        return ToolUse(tool_use_id, "file", cwd,
                       path=str(tool_input.get(PATH_PARAMETER_BY_FILE_TOOL_MAP[tool_name]) or "") or None,
                       does_write_file=tool_name in FILE_WRITING_TOOLS)
    if tool_name in SUBAGENT_TOOLS:
        return ToolUse(tool_use_id, "subagent", cwd)
    if tool_name in WAITING_TOOLS:
        return ToolUse(tool_use_id, "wait", cwd)
    return ToolUse(tool_use_id, "other", cwd)


def _resolve_user_kind(line: dict[str, Any], content: Any) -> str:
    """person, tool_result or notification. A peer message from another session counts as a person: the agent did
    not cause it. So does a slash command and its output. A subagent handing back its report counts as a
    notification."""
    if isinstance(content, list) and any(isinstance(block, dict) and block.get("type") == "tool_result"
                                         for block in content):
        return "tool_result"
    if _parse_content_text(content).lstrip().startswith(("<command-name>", "<command-message>", "<local-command-")):
        return "person"
    origin = line.get("origin") or {}
    if origin:
        kind = origin.get("kind")
        if kind == "peer":
            return "notification" if origin.get("senderTaskId") else "person"
        return "person" if kind == "human" else "notification"
    if line.get("isMeta") or line.get("isCompactSummary"):
        return "notification"
    return "notification" if _parse_content_text(content).lstrip().startswith("<") else "person"


def _parse_optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def read_conversation(conversation_file_path: Path, started_by_tool_use_id: str | None = None) -> Conversation:
    calls: list[ModelCall] = []
    events: list[ConversationEvent] = []
    call_index_by_call_id_map: dict[str, int] = {}
    call_index_and_tool_use_by_tool_use_id_map: dict[str, tuple[int, ToolUse]] = {}
    opening: str | None = None
    try:
        handle = conversation_file_path.open(encoding="utf-8")
    except OSError:
        return Conversation(conversation_file_path.stem, "", started_by_tool_use_id, [], [])
    with handle:
        for raw_line in handle:
            try:
                line = json.loads(raw_line)
            except ValueError:
                continue
            if not isinstance(line, dict) or line.get("type") not in ("assistant", "user"):
                continue
            moment_seconds = _parse_timestamp_seconds(str(line.get("timestamp") or ""))
            message = line.get("message") or {}
            if moment_seconds is None or not isinstance(message, dict):
                continue
            if line["type"] == "assistant":
                call_id = f"{message.get('id')}/{line.get('requestId')}"
                if call_id not in call_index_by_call_id_map:
                    call_index_by_call_id_map[call_id] = len(calls)
                    calls.append(ModelCall(call_id, moment_seconds, str(message.get("model") or ""),
                                           _parse_optional_text(line.get("effort")), None, TokenUsage()))
                call_index = call_index_by_call_id_map[call_id]
                call = calls[call_index]
                usage = message.get("usage")
                if isinstance(usage, dict) and usage:
                    call.token_usage = _convert_usage_to_token_usage(usage)
                    call.speed = _parse_optional_text(usage.get("speed")) or call.speed
                for block in message.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_use = _convert_content_block_to_tool_use(block, str(line.get("cwd") or ""))
                        call.tool_uses.append(tool_use)
                        call_index_and_tool_use_by_tool_use_id_map[tool_use.id] = (call_index, tool_use)
                events.append(ConversationEvent(moment_seconds, "model", call_index))
                continue
            content = message.get("content")
            if opening is None:
                opening = _parse_content_text(content)
            kind = _resolve_user_kind(line, content)
            if kind != "tool_result":
                events.append(ConversationEvent(moment_seconds, kind))  # type: ignore[arg-type]
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                answered = call_index_and_tool_use_by_tool_use_id_map.get(str(block.get("tool_use_id") or ""))
                if answered is None:
                    events.append(ConversationEvent(moment_seconds, "tool_result"))
                    continue
                call_index, tool_use = answered
                if tool_use.kind == "shell" and tool_use.command and "explainer-studio" in tool_use.command:
                    tool_use.result = _parse_content_text(block.get("content"))
                events.append(ConversationEvent(moment_seconds, "tool_result", call_index, tool_use.id))
    return Conversation(conversation_file_path.stem, opening or "", started_by_tool_use_id, calls, events)
