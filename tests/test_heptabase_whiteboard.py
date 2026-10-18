from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from delivered_series import create_series, write_delivery_record

from explainer_studio import heptabase_sign_in, heptabase_whiteboard, user_dirs
from explainer_studio.errors import StudioError
from explainer_studio.heptabase_whiteboard import compute_whiteboard_page, import_episodes, parse_whiteboard_layout
from explainer_studio.paths import Series

# every test here delivers the fake render, which ffmpeg makes
pytestmark = pytest.mark.render

LAYOUT = {
    "episodeIds": ["ep01"],
    "sections": [{"key": key, "color": None, "x": 0, "y": 0, "width": 100, "height": 100}
                 for key in ("ep01", "ep01/moves", "ep01/adding")],
    "cards": [{"key": key, "x": 0, "y": 0, "width": 520, "height": 200}
              for key in ("ep01/moves_add", "ep01/tip_to_tail")],
    "connections": [{"key": "ep01/moves_add->ep01/tip_to_tail", "type": "curve", "beginPos": "right",
                     "endPos": "left"}],
}


class FakeHeptabase:
    """A signed-in Heptabase: the requests sent to it, in order, whether its answer to an import gets lost, and the
    whiteboards whose import it refuses (by id, with the code)."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, dict[str, Any]]] = []
        self.should_lose_response = False
        self.refusal_code_by_whiteboard_id_map: dict[str, str] = {}

    def call_rest_api(self, api_url: str, path: str, body: dict[str, Any]) -> Any:
        self.requests.append((path, body))
        if path == heptabase_whiteboard.UPLOAD_URL_PATH:
            return {"status": "valid", "signedUrl": "https://s3.test/upload"}
        if self.should_lose_response:
            raise StudioError("Heptabase could not be reached", "ReadTimeout")
        code = self.refusal_code_by_whiteboard_id_map.get(body["whiteboard"]["id"])
        if code:
            raise heptabase_sign_in.HeptabaseRequestError("Heptabase refused it", f"HTTP 409 ({code})", code)
        return {}


@pytest.fixture
def heptabase(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeHeptabase:
    monkeypatch.setattr(user_dirs, "get_cache_dir_path", lambda: tmp_path / "cache")
    authorization_server = heptabase_sign_in.AuthorizationServer(
        "https://heptabase.test", "https://heptabase.test/auth", "https://heptabase.test/token",
        "https://heptabase.test/register", "https://heptabase.test/token/revocation")
    monkeypatch.setattr(heptabase_sign_in, "fetch_authorization_server", lambda api_url: authorization_server)
    monkeypatch.setattr(heptabase_sign_in, "find_issuer", lambda api_url: authorization_server.issuer)
    monkeypatch.setattr(heptabase_sign_in, "require_signed_in_account_id", lambda issuer: "account")
    monkeypatch.setattr(heptabase_sign_in, "send_request", lambda method, url, **options: httpx.Response(200))
    fake_heptabase = FakeHeptabase()
    monkeypatch.setattr(heptabase_sign_in, "call_rest_api", fake_heptabase.call_rest_api)
    return fake_heptabase


def deliver_series(tmp_path: Path) -> Series:
    series = create_series(tmp_path / "series")
    write_delivery_record(series, datetime.now(UTC) - timedelta(minutes=5))
    shutil.copy(series.get_episode_paths("ep01").render_video_file_path, series.root_dir_path / "01-v.mp4")
    return series


def lay_out(series: Series) -> heptabase_whiteboard.WhiteboardLayout:
    """The page's layout of the cards as the page server gives them now."""
    return parse_whiteboard_layout({**LAYOUT, "cardsVersion": compute_whiteboard_page(series)["cardsVersion"]})


def test_an_unconfirmed_save_goes_again_with_the_same_ids(tmp_path: Path, heptabase: FakeHeptabase) -> None:
    series = deliver_series(tmp_path)
    assert [episode["id"] for episode in compute_whiteboard_page(series)["episodesToAdd"]] == ["ep01"]
    layout = lay_out(series)

    heptabase.should_lose_response = True  # Heptabase may have added it, but Studio never heard back
    with pytest.raises(StudioError):
        import_episodes(series, layout)
    first_body = heptabase.requests[-1][1]
    whiteboard = heptabase_whiteboard.load_heptabase_whiteboard(series)
    assert whiteboard.episodes["ep01"].imported_at is None
    assert compute_whiteboard_page(series)["savedWhiteboard"] is None  # still a preview, saved again by the user

    heptabase.should_lose_response = False
    import_episodes(series, layout)
    second_body = heptabase.requests[-1][1]
    assert second_body == first_body  # the same ids, which Heptabase does not add twice
    assert first_body["files"][0]["id"] == whiteboard.files["frame:ep01/one_arrow"]
    assert f"hepta-image-ref:{whiteboard.files['frame:ep01/one_arrow']}" in first_body["cards"][0]["content"]
    assert heptabase_whiteboard.load_heptabase_whiteboard(series).episodes["ep01"].imported_at is not None
    whiteboard_page = compute_whiteboard_page(series)
    assert whiteboard_page["savedWhiteboard"]["importedEpisodeIds"] == ["ep01"]
    assert whiteboard_page["episodesToAdd"] == []


def test_a_layout_of_cards_that_changed_since_is_refused(tmp_path: Path, heptabase: FakeHeptabase) -> None:
    series = deliver_series(tmp_path)
    layout = lay_out(series)
    notes_file_path = series.get_episode_paths("ep01").notes_file_path
    notes_file_path.write_text(notes_file_path.read_text(encoding="utf-8").replace("首尾相接", "頭尾相接"),
                               encoding="utf-8")
    with pytest.raises(heptabase_whiteboard.WhiteboardImportRefusedError) as error:
        import_episodes(series, layout)
    assert error.value.code == "cards_changed"
    assert heptabase.requests == [] and heptabase_whiteboard.load_heptabase_whiteboard(series) is None
    import_episodes(series, lay_out(series))
    assert compute_whiteboard_page(series)["savedWhiteboard"]["importedEpisodeIds"] == ["ep01"]


def test_a_layout_measured_with_an_earlier_frame_is_refused(tmp_path: Path, heptabase: FakeHeptabase) -> None:
    series = deliver_series(tmp_path)
    layout = lay_out(series)
    write_delivery_record(series, datetime.now(UTC))
    with pytest.raises(heptabase_whiteboard.WhiteboardImportRefusedError) as error:
        import_episodes(series, layout)
    assert error.value.code == "cards_changed" and heptabase.requests == []


def test_a_first_save_whose_whiteboard_heptabase_refuses_goes_to_a_new_whiteboard(
        tmp_path: Path, heptabase: FakeHeptabase) -> None:
    series = deliver_series(tmp_path)
    heptabase.should_lose_response = True  # Heptabase made the whiteboard, but its objects did not go through
    with pytest.raises(StudioError):
        import_episodes(series, lay_out(series))
    first_whiteboard_id = heptabase_whiteboard.load_heptabase_whiteboard(series).whiteboard_id
    heptabase.should_lose_response = False
    heptabase.refusal_code_by_whiteboard_id_map[first_whiteboard_id] = "whiteboard_trashed"  # the user trashed it

    import_episodes(series, lay_out(series))
    whiteboard = heptabase_whiteboard.load_heptabase_whiteboard(series)
    assert whiteboard.whiteboard_id != first_whiteboard_id and whiteboard.episodes["ep01"].imported_at is not None


def test_a_saved_whiteboard_is_not_added_to_from_another_account(
        tmp_path: Path, heptabase: FakeHeptabase, monkeypatch: pytest.MonkeyPatch) -> None:
    series = deliver_series(tmp_path)
    import_episodes(series, lay_out(series))
    saved_whiteboard = heptabase_whiteboard.load_heptabase_whiteboard(series)
    request_count = len(heptabase.requests)

    monkeypatch.setattr(heptabase_sign_in, "require_signed_in_account_id", lambda issuer: "another account")
    with pytest.raises(heptabase_whiteboard.WhiteboardImportRefusedError) as error:
        import_episodes(series, lay_out(series))
    assert error.value.code == "other_account"
    assert len(heptabase.requests) == request_count
    assert heptabase_whiteboard.load_heptabase_whiteboard(series) == saved_whiteboard
