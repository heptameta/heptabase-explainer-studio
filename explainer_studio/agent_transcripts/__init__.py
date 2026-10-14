"""The transcripts a harness keeps of the agent's conversations, read to work out the cost of a series.

A harness is the program the agent runs in, such as Claude Code or Codex. Each keeps transcripts in its own format;
one module per harness turns them into the small model below: the conversations that worked on a series (subagents
included), each model call with its model settings, token counts and the tool uses it made, and the moments that tell
working time from waiting for the user. Only commands, file paths, times, model settings and token counts are kept,
never what was said. The formats are not public specifications, so a reader that finds
nothing it understands returns no conversations instead of failing.

Only Claude Code is read for now.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ..schemas.cost import HarnessName, TokenUsage

HARNESS_DISPLAY_NAME_BY_NAME_MAP: dict[HarnessName, str] = {"claude-code": "Claude Code"}


@dataclass
class ToolUse:
    id: str
    kind: Literal["shell", "file", "subagent", "wait", "other"]  # wait: a tool that only waits
    cwd: str  # the working directory when the tool ran
    command: str | None = None  # a shell command
    path: str | None = None  # the file or folder a file tool used
    does_write_file: bool = False  # a file tool that changed the file (wrote or edited it), not one that read it
    result: str | None = None  # the output of a shell command that ran explainer-studio (only those are kept)


@dataclass
class ModelCall:
    id: str  # the same across conversations: a resumed conversation repeats the calls it copied
    time_seconds: float  # seconds since the epoch
    model_name: str
    effort: str | None  # the reasoning effort the harness asked for, as it names it (high, xhigh …)
    speed: str | None  # standard or fast
    token_usage: TokenUsage
    tool_uses: list[ToolUse] = field(default_factory=list)


@dataclass(frozen=True)
class ConversationEvent:
    time_seconds: float  # seconds since the epoch
    # person: someone wrote to the agent (waiting for them is not work); model: a model call produced output;
    # tool_result: a tool finished; notification: a background task or subagent reported back
    kind: Literal["person", "model", "tool_result", "notification"]
    call_index: int | None = None  # model: that call; tool_result: the call that made the tool use
    tool_use_id: str | None = None  # tool_result: the tool use it answers


@dataclass
class Conversation:
    id: str
    opening: str  # the first message: for a subagent, the task it was given
    started_by_tool_use_id: str | None  # for a subagent, the tool use (in its parent conversation) that started it
    calls: list[ModelCall]
    events: list[ConversationEvent]


@dataclass
class HarnessConversations:
    harness_name: HarnessName
    conversations: list[Conversation]


def read_harness_conversations(series_root_dir_path: Path) -> HarnessConversations | None:
    """The conversations on this computer that may have worked on the series, or None when no reader found any."""
    from . import claude_code

    conversations = claude_code.read_conversations(series_root_dir_path)
    return HarnessConversations("claude-code", conversations) if conversations else None
