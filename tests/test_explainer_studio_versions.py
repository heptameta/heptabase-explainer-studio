from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner
from delivered_series import create_series, write_delivery_record
from packaging.version import Version

from explainer_studio import releases
from explainer_studio.cli.main import cli
from explainer_studio.explainer_studio_versions import convert_git_description_to_dev_build_version, record_version_use


def test_a_dev_build_version_is_the_next_release_the_commits_since_the_tag_and_the_commit() -> None:
    assert convert_git_description_to_dev_build_version("v0.1.0-13-g9b0e2d4") == "0.1.1.dev13+g9b0e2d4"
    # an all-digit commit starting with 0 must come through Python's version normalization unchanged, since the
    # installed CLI reports the normalized version and the version records compare it as a string
    version = convert_git_description_to_dev_build_version("v0.1.9-0-g0123456")
    assert version == "0.1.10.dev0+g0123456"
    assert str(Version(version)) == version


def test_feedback_on_an_episode_does_not_count_as_making_it(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    write_delivery_record(series, datetime.now(UTC) - timedelta(hours=1))
    versions_file_path = series.get_episode_paths("ep01").explainer_studio_versions_file_path
    earlier = "0.1.1.dev13+g9b0e2d4"  # the version the episode was made with
    versions_text = json.dumps({"last_used_version": earlier, "versions_since_last_delivery": []})
    versions_file_path.write_text(versions_text, encoding="utf-8")

    run = CliRunner().invoke(cli, ["feedback", "add", "ep01", "整集太快", "--series", str(series.root_dir_path)],
                             catch_exceptions=False)

    assert run.exit_code == 0, run.output
    assert versions_file_path.read_text(encoding="utf-8") == versions_text and "changed from" not in run.stderr


def test_a_new_episode_learns_what_the_series_needs_from_its_last_version(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    series.get_episode_paths("ep01").explainer_studio_versions_file_path.write_text(
        json.dumps({"last_used_version": "0.1.0", "versions_since_last_delivery": []}), encoding="utf-8")
    series.get_episode_paths("ep02").root_dir_path.mkdir()
    upgrading_file_path = tmp_path / "UPGRADING.md"
    upgrading_file_path.write_text("# Upgrading\n\n## 0.2.0\n\n- If `plan.yaml` has `lang`, rename it.\n",
                                   encoding="utf-8")
    monkeypatch.setattr(releases, "UPGRADING_FILE_PATH", upgrading_file_path)

    notice = record_version_use(series, "ep02", "0.2.0")

    assert notice is not None and "from 0.1.0 to 0.2.0" in notice and "rename it" in notice
    assert record_version_use(series, "ep02", "0.2.0") is None
