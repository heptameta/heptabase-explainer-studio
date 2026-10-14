from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from delivered_series import create_series

from explainer_studio.plan import load_plan
from explainer_studio.web import launcher
from explainer_studio.web.plan_edits import (
    InvalidEditError,
    PlanConflictError,
    compute_plan_version,
    write_plan_field,
)


def test_a_page_save_changes_one_setting_and_keeps_the_agents_comments(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    loaded_plan_version = compute_plan_version(series.plan_file_path.read_bytes())
    write_plan_field(series, ["narration_budget_usd"], 12.5, loaded_plan_version)
    text = series.plan_file_path.read_text(encoding="utf-8")
    assert "narration_budget_usd: 12.5" in text
    assert "# the series title" in text and "description: |" in text and "unfamiliar_terms: [向量, 線性變換]" in text

    with pytest.raises(PlanConflictError):  # the page still holds the version it loaded
        write_plan_field(series, ["narration_budget_usd"], 20, loaded_plan_version)
    with pytest.raises(InvalidEditError):
        write_plan_field(series, ["narration_budget_usd"], -1, compute_plan_version(series.plan_file_path.read_bytes()))
    with pytest.raises(InvalidEditError):  # only the production settings are editable on the page
        write_plan_field(series, ["episodes", 0, "takeaway"], "新的結論",
                         compute_plan_version(series.plan_file_path.read_bytes()))
    assert series.plan_file_path.read_text(encoding="utf-8") == text


def test_the_end_credits_switch_saves_true_or_false_and_nothing_else(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    write_plan_field(series, ["has_end_credits"], False, compute_plan_version(series.plan_file_path.read_bytes()))
    assert load_plan(series).has_end_credits is False
    with pytest.raises(InvalidEditError):
        write_plan_field(series, ["has_end_credits"], "off", compute_plan_version(series.plan_file_path.read_bytes()))


def test_switching_the_narration_provider_writes_a_complete_block(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    write_plan_field(series, ["narration", "provider_name"], "elevenlabs",
                     compute_plan_version(series.plan_file_path.read_bytes()))
    text = series.plan_file_path.read_text(encoding="utf-8")
    assert "  provider_name: elevenlabs\n  voice_id: FS8UtxyDrvYcNCxVaziq\n\naudience:" in text


def test_the_server_needs_its_token_and_stops_when_idle(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    runtime_file_path = tmp_path / "runtime.json"
    process = subprocess.Popen([sys.executable, "-m", "explainer_studio.web.server",
                                "--series", str(series.root_dir_path), "--runtime-file", str(runtime_file_path),
                                "--idle-seconds", "1.5"])
    try:
        deadline = time.monotonic() + 15
        while (not (runtime_file_path.exists() and json.loads(runtime_file_path.read_text()).get("pid"))
               and time.monotonic() < deadline):
            time.sleep(0.05)
        runtime_info = json.loads(runtime_file_path.read_text())
        base_url = f"http://127.0.0.1:{runtime_info['port']}"
        assert httpx.get(f"{base_url}/plan", trust_env=False).status_code == 403
        assert httpx.get(f"{base_url}/not-the-token/api/plan", trust_env=False).status_code == 403
        page_response = httpx.get(f"{base_url}/{runtime_info['token']}/plan", trust_env=False)
        assert page_response.status_code == 200 and page_response.headers["Referrer-Policy"] == "no-referrer"
        assert process.wait(timeout=10) == 0
        assert json.loads(runtime_file_path.read_text())["pid"] is None  # the token and port stay for the next start
    finally:
        process.kill()


def test_open_reuses_a_running_server_and_replaces_one_of_another_version(tmp_path: Path,
                                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    monkeypatch.setattr("explainer_studio.user_dirs.get_page_server_dir_path", lambda: tmp_path / "pages")
    first_runtime_info = launcher.ensure_server(series)
    try:
        assert launcher.ensure_server(series)["pid"] == first_runtime_info["pid"]
        monkeypatch.setattr(launcher, "__version__", "9.9.9")
        replaced_runtime_info = launcher.ensure_server(series)
        assert replaced_runtime_info["pid"] != first_runtime_info["pid"]
        assert replaced_runtime_info["token"] == first_runtime_info["token"]
        assert launcher.open_page(series, "plan", should_open_browser=False) == \
            f"http://127.0.0.1:{replaced_runtime_info['port']}/{replaced_runtime_info['token']}/plan"
    finally:
        runtime_info = launcher.read_runtime_info(launcher.get_runtime_file_path(series)) or {}
        if launcher.fetch_health(runtime_info):
            httpx.post(f"{launcher.build_base_url(runtime_info)}/shutdown", trust_env=False)
