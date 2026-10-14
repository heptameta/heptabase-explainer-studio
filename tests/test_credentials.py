"""Where narration keys are read from and how they are stored."""

from __future__ import annotations

import os
import stat
import sys

import pytest

from explainer_studio import credentials


@pytest.fixture
def config(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("explainer_studio.user_dirs.get_config_dir_path", lambda: tmp_path / "config")
    for variable in ("ELEVENLABS_API_KEY", "OPENAI_API_KEY", "VOAI_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    return tmp_path / "config"


def test_the_environment_variable_comes_before_the_saved_key(config, monkeypatch) -> None:
    credentials.write_api_key("openai", "saved-key")
    assert credentials.find_api_key("openai").value == "saved-key"
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")
    found = credentials.find_api_key("openai")
    assert found.value == "environment-key" and found.source == "environment variable OPENAI_API_KEY"
    assert "environment-key" not in repr(found)
    assert credentials.find_api_key("macos-say") is None


def test_saving_a_key_keeps_the_others_and_only_the_user_can_read_the_file(config) -> None:
    credentials.write_api_key("voai", "first")
    path = credentials.write_api_key("elevenlabs", "second")
    assert credentials.find_api_key("voai").value == "first"
    assert credentials.find_api_key("elevenlabs").value == "second"
    if sys.platform != "win32":
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
