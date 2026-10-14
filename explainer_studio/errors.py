"""The one error type commands raise for an expected failure.

Every message says what failed, why, and what to run next, because the reader is usually a coding agent that will act
on it without asking anyone.
"""

from __future__ import annotations


class StudioError(Exception):
    """An expected failure: bad input, a failed gate, a missing tool or a provider that refused the request."""

    def __init__(self, what: str, why: str = "", next_step: str = "", details: list[str] | None = None):
        self.what = what
        self.why = why
        self.next_step = next_step
        self.details = details or []
        super().__init__(self.format())

    def format(self) -> str:
        lines = [f"error: {self.what}"]
        if self.why:
            lines.append(f"why: {self.why}")
        lines.extend(f"  - {detail}" for detail in self.details)
        if self.next_step:
            lines.append(f"next: {self.next_step}")
        return "\n".join(lines)
