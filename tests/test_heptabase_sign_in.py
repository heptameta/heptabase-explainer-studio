"""The Heptabase sign-in every series' page server shares through credentials.toml."""

from __future__ import annotations

from typing import Any

import pytest

from explainer_studio import heptabase_sign_in
from explainer_studio.credentials import hold_credentials_lock

ISSUER = "https://heptabase.test"
API_URL = "https://api.heptabase.test"


@pytest.fixture
def token_responses(tmp_path, monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, Any]]:
    """What Heptabase's token endpoint answers, in order; a signed-in computer to begin with."""
    monkeypatch.setattr("explainer_studio.user_dirs.get_config_dir_path", lambda: tmp_path / "config")
    authorization_server = heptabase_sign_in.AuthorizationServer(
        ISSUER, f"{ISSUER}/auth", f"{ISSUER}/token", f"{ISSUER}/register", f"{ISSUER}/token/revocation")
    monkeypatch.setattr(heptabase_sign_in, "fetch_authorization_server", lambda api_url: authorization_server)
    monkeypatch.setattr(heptabase_sign_in, "_access_token_by_issuer_map", {})
    responses: list[tuple[int, Any]] = []
    monkeypatch.setattr(heptabase_sign_in, "_request_tokens", lambda api_url, form: responses.pop(0))
    with hold_credentials_lock():
        heptabase_sign_in._write_sign_in(ISSUER, {"client_id": "client", "account_id": "account",
                                                  "email": "reader@heptabase.test", "refresh_token": "refresh-1"})
    return responses


def test_a_sign_out_by_another_series_ends_the_access_token_in_memory(token_responses) -> None:
    token_responses.append((200, {"access_token": "access-1", "refresh_token": "refresh-2", "expires_in": 3600}))
    assert heptabase_sign_in.fetch_access_token(API_URL).value == "access-1"
    # another series' page server signs out: it deletes the stored sign-in this process gave the token for
    with hold_credentials_lock():
        heptabase_sign_in._delete_sign_in(ISSUER)
    with pytest.raises(heptabase_sign_in.HeptabaseSignInRequiredError) as error:
        heptabase_sign_in.fetch_access_token(API_URL)
    assert error.value.code == "signed_out"


def test_a_sign_in_heptabase_refuses_stays_expired_rather_than_signed_out(token_responses) -> None:
    token_responses.append((400, {"error": "invalid_grant"}))
    with pytest.raises(heptabase_sign_in.HeptabaseSignInRequiredError) as error:
        heptabase_sign_in.fetch_access_token(API_URL)
    assert error.value.code == "sign_in_expired"
    # every later read, from any series, says the same, and nothing shows the account as signed in
    with pytest.raises(heptabase_sign_in.HeptabaseSignInRequiredError) as error:
        heptabase_sign_in.require_signed_in_account_id(ISSUER)
    assert error.value.code == "sign_in_expired"
    assert heptabase_sign_in.find_signed_in_email(ISSUER) is None
