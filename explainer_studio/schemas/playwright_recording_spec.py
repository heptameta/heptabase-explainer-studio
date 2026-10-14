"""The spec `asset playwright record <spec>` reads (YAML or JSON), written by the agent.

    name: signup_flow                 # optional: the output name (default: the spec file's name)
    url: https://example.com          # or html: a page file, relative to the spec's folder or to production/
    viewport: [1280, 720]
    steps:
      - click: "text=Sign up"         # selectors are Playwright's (css=, text=, role=...)
      - type: ["#email", "ada@example.com"]
      - press: Enter
      - scroll: 600                   # pixels down
      - hover: "#menu"
      - highlight: "css=.price"       # glide the cursor there and hold, without clicking
      - wait: 1.5                     # seconds
      - goto: https://example.com/pricing

Never type real passwords or personal data into a recording; typing into a password field is refused.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ACTIONS = ("click", "hover", "highlight", "type", "press", "scroll", "wait", "goto")


class PlaywrightRecordingSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    url: str | None = None
    html: str | None = None
    viewport: tuple[int, int] = (1280, 720)
    steps: list[dict[str, Any]] = Field(min_length=1)

    @model_validator(mode="after")
    def one_page(self) -> PlaywrightRecordingSpec:
        if (self.url is None) == (self.html is None):
            raise ValueError("give exactly one of url or html")
        return self

    @field_validator("steps")
    @classmethod
    def known_steps(cls, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for number, step in enumerate(steps, start=1):
            if len(step) != 1 or next(iter(step)) not in ACTIONS:
                raise ValueError(f"step {number} must be one of {', '.join(ACTIONS)} with its argument, got {step}")
            action, argument = next(iter(step.items()))
            if action == "type" and not (isinstance(argument, list) and len(argument) == 2):
                raise ValueError(f"step {number}: type takes [selector, text]")
            if action in ("scroll", "wait") and not isinstance(argument, (int, float)):
                raise ValueError(f"step {number}: {action} takes a number")
        return steps
