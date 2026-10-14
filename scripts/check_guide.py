"""Check the conventions of the guide (`.claude/skills/guide-convention/SKILL.md`).

- The guide is written in English: text in another script appears only in `references/languages/<language>.md`.
- The guide's `references/` holds judgment; the steps that run the pages, feedback and setup commands are in
  `workflow/`, so `references/` does not name those commands.

    uv run python scripts/check_guide.py
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

REPOSITORY_DIR_PATH = Path(__file__).resolve().parent.parent
GUIDE_DIR_PATH = REPOSITORY_DIR_PATH / "explainer_studio" / "guide"
REFERENCES_DIR_PATH = GUIDE_DIR_PATH / "references"
LANGUAGES_DIR_PATH = REFERENCES_DIR_PATH / "languages"

# Letters that are notation rather than another language: Latin, Greek and the mathematical forms (ℝ, ᵀ)
NOTATION_LETTER_NAME_PREFIXES = ("LATIN", "GREEK", "MATHEMATICAL", "DOUBLE-STRUCK", "SCRIPT", "BLACK-LETTER",
                                 "MODIFIER LETTER", "SUPERSCRIPT", "SUBSCRIPT")
# CJK punctuation, ideographs, kana, hangul and full-width forms
OTHER_SCRIPT_RANGES = ((0x3000, 0x9FFF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF), (0xFE30, 0xFE4F), (0xFF00, 0xFFEF),
                       (0x20000, 0x3FFFF))

WORKFLOW_COMMAND_PATTERN_TO_REASON_MAP = {
    r"\bplan open\b": "opening the plan page is a workflow step; describe the plan instead",
    r"\bvideo open\b": "opening the video page is a workflow step",
    r"\bfeedback (add|resolve|share)\b": "feedback commands are workflow steps; see workflow/feedback.md",
    r"\bexplainer-studio (setup|doctor)\b": "installation is a workflow step; see workflow/setup.md",
}


def check_is_other_script(character: str) -> bool:
    code_point = ord(character)
    if any(start <= code_point <= end for start, end in OTHER_SCRIPT_RANGES):
        return True
    return unicodedata.category(character).startswith("L") and not character.isascii() \
        and not unicodedata.name(character, "").startswith(NOTATION_LETTER_NAME_PREFIXES)


def validate_guide() -> list[str]:
    problems = []
    for path in sorted(GUIDE_DIR_PATH.rglob("*")):
        if not path.is_file() or path.is_relative_to(LANGUAGES_DIR_PATH):
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(check_is_other_script(character) for character in line):
                problems.append(f"{path.relative_to(REPOSITORY_DIR_PATH)}:{line_number}: not English; move it to "
                                f"references/languages/<language>.md: {line.strip()[:100]}")
            if path.is_relative_to(REFERENCES_DIR_PATH) and path.suffix == ".md":
                problems += [f"{path.relative_to(REPOSITORY_DIR_PATH)}:{line_number}: {reason}: {line.strip()[:100]}"
                             for pattern, reason in WORKFLOW_COMMAND_PATTERN_TO_REASON_MAP.items()
                             if re.search(pattern, line)]
    return problems


def main() -> None:
    problems = validate_guide()
    for problem in problems:
        print(problem)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
