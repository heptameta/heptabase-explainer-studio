from __future__ import annotations

from pathlib import Path

import pytest

from explainer_studio import releases

UPGRADING_TEXT = """# Upgrading

Introduction.

## Unreleased

- If a series has X, do Y.

## 0.4.0

- If `plan.yaml` has `lang`, rename it to `language_code`.

## 0.3.0

- If a scene calls `LabeledArrow(text=...)`, rename the argument to `label=`.

## 0.2.0

- Never shown after 0.2.0.
"""


def test_upgrading_sections_are_the_releases_skipped_over(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    upgrading_file_path = tmp_path / "UPGRADING.md"
    upgrading_file_path.write_text(UPGRADING_TEXT, encoding="utf-8")
    monkeypatch.setattr(releases, "UPGRADING_FILE_PATH", upgrading_file_path)

    sections = releases.read_upgrading_sections("0.2.0", "0.4.0")
    assert [section.version for section in sections] == ["0.3.0", "0.4.0"]
    assert sections[1].text == "- If `plan.yaml` has `lang`, rename it to `language_code`."
    assert releases.read_upgrading_sections("0.4.0", "0.4.0") == []
    assert releases.read_upgrading_sections("0.3.1.dev2+gabc1234", "0.4.0") == []


def test_latest_release_is_the_highest_version_tag() -> None:
    ls_remote_text = ("a\trefs/tags/v0.9.9\nb\trefs/tags/v0.10.2\nc\trefs/tags/v1.0.0-rc1\nd\trefs/tags/v0.1.0\n")
    assert releases.parse_latest_release_version(ls_remote_text) == "0.10.2"
    assert releases.parse_latest_release_version("") is None
