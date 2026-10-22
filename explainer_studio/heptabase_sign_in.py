"""The user's sign-in to Heptabase, through which the video page saves the series' whiteboard.

The series' whiteboard is the one place the package talks to Heptabase's product. It signs in with
Heptabase's OAuth server: the authorization code flow with PKCE, the browser sent back to the page server on a
loopback address and from there to the page that started the sign-in. The sign-in belongs to this computer, for every
series: credentials.toml (mode 0600) keeps the client registration, the account, its email and the refresh token
under `[heptabase."<issuer>"]`, the issuer being the OAuth server's own name for itself; access tokens stay in the page
server's memory. Signing out revokes the refresh token and deletes that table. Token values are never printed or
logged.

EXPLAINER_STUDIO_HEPTABASE_APP_URL and EXPLAINER_STUDIO_HEPTABASE_API_URL point it at another Heptabase (a local web
app and backend while developing).
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlencode, urlsplit

import httpx

from . import __version__
from .credentials import hold_credentials_lock, read_credentials, write_credentials
from .errors import StudioError

HEPTABASE_APP_URL = "https://app.heptabase.com"
HEPTABASE_API_URL = "https://api.heptabase.com"
HEPTABASE_APP_URL_ENV = "EXPLAINER_STUDIO_HEPTABASE_APP_URL"
HEPTABASE_API_URL_ENV = "EXPLAINER_STUDIO_HEPTABASE_API_URL"
CALLBACK_PATH = "/heptabase-callback"
OAUTH_SCOPE = "openid email offline_access space:read space:write"
CLIENT_DISPLAY_NAME = "Explainer Studio"
CREDENTIALS_TABLE_NAME = "heptabase"
# An access token is refreshed this long before it expires, so a page never gets one about to stop working.
ACCESS_TOKEN_MARGIN_SECONDS = 5 * 60
SIGN_IN_ATTEMPT_LIFETIME_SECONDS = 15 * 60
REQUEST_TIMEOUT_SECONDS = 60
# the hosts a Heptabase may answer on over plain HTTP: a local backend while developing
LOOPBACK_HOST_NAMES = ("localhost", "127.0.0.1", "::1")

# upgradeRequired: Heptabase answered that this Studio is too old for it (UPGRADE_REQUIRED_CODE)
SignInStatus = Literal["pending", "signedIn", "canceled", "failed", "upgradeRequired"]
# signed_out: this computer has no sign-in; sign_in_expired: Heptabase no longer accepts the one it has
SignInRequiredCode = Literal["signed_out", "sign_in_expired"]
# Reserved for Heptabase to answer, with any HTTP status, when this version of Studio must be updated to keep working:
# a change it could not make by addition. Heptabase tells which version asks by the User-Agent.
UPGRADE_REQUIRED_CODE = "upgrade_required"


class HeptabaseSignInRequiredError(StudioError):
    """There is no sign-in, or Heptabase no longer accepts it; `code` says which."""

    def __init__(self, why: str, code: SignInRequiredCode):
        super().__init__("not signed in to Heptabase", why, "sign in again from the video page")
        self.code = code


class HeptabaseRequestError(StudioError):
    """Heptabase refused a request with HTTP `status_code`; `code` is its error code, when it gave one."""

    def __init__(self, what: str, status_code: int, code: str | None = None):
        super().__init__(what, f"HTTP {status_code}" + (f" ({code})" if code else ""),
                         "update Explainer Studio, then try again" if code == UPGRADE_REQUIRED_CODE
                         else "try again; if it keeps failing, tell the Heptabase team")
        self.status_code = status_code
        self.code = code


def resolve_heptabase_app_url() -> str:
    return (os.environ.get(HEPTABASE_APP_URL_ENV, "").strip() or HEPTABASE_APP_URL).rstrip("/")


def resolve_heptabase_api_url() -> str:
    return (os.environ.get(HEPTABASE_API_URL_ENV, "").strip() or HEPTABASE_API_URL).rstrip("/")


def resolve_rest_api_url(base_url: str) -> str:
    """The REST API under a Heptabase base URL."""
    return f"{base_url}/v1"


@dataclass(frozen=True)
class AuthorizationServer:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    revocation_endpoint: str

    @property
    def resource_url(self) -> str:
        """The resource an access token is requested for: the REST API on the OAuth server's own address, which a
        backend reached on another address expects too."""
        return resolve_rest_api_url(self.issuer)


@dataclass
class SignInAttempt:
    api_url: str
    issuer: str
    redirect_uri: str
    return_path: str  # the page the browser goes back to once Heptabase is done
    client_id: str
    state: str
    code_verifier: str
    created_at_monotonic_seconds: float = field(default_factory=time.monotonic)
    status: SignInStatus = "pending"


@dataclass
class AccessToken:
    value: str
    expires_at_monotonic_seconds: float
    client_id: str  # the stored sign-in it was given for
    account_id: str

    def __repr__(self) -> str:  # never show the value in a traceback or debugger
        return f"AccessToken(client_id={self.client_id!r})"


_authorization_server_by_api_url_map: dict[str, AuthorizationServer] = {}
# one client for every request to Heptabase, so requests reuse its connections (a save uploads many pictures)
_http_client = httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True,
                            headers={"User-Agent": f"explainer-studio/{__version__}"})
_access_token_by_issuer_map: dict[str, AccessToken] = {}
_access_token_lock = threading.Lock()


# HTTP -----------------------------------------------------------------------------------------------------------------
def send_request(method: str, url: str, **request_options: Any) -> httpx.Response:
    """A request to Heptabase, or anywhere it points Studio (a picture's upload URL)."""
    return _http_client.request(method, url, **request_options)


def _fetch_json(method: str, url: str, **request_options: Any) -> tuple[int, Any]:
    try:
        response = send_request(method, url, **request_options)
    except httpx.HTTPError as error:
        raise StudioError("Heptabase could not be reached", f"{type(error).__name__}: {error}",
                          "check the network and try again") from None
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, None


def _read_error_code(response_body: Any) -> str | None:
    return response_body.get("code") if isinstance(response_body, dict) else None


def _resolve_origin(url: Any) -> str | None:
    """`scheme://host[:port]` of an HTTPS URL, or an HTTP one on a loopback host; None for any other value (another
    scheme such as `javascript:`, credentials in the URL, not a string)."""
    if not isinstance(url, str):
        return None
    try:
        parts = urlsplit(url)
    except ValueError:  # such as an unclosed `[` around the host
        return None
    is_secure = parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in LOOPBACK_HOST_NAMES)
    if not is_secure or not parts.hostname or parts.username is not None or parts.password is not None:
        return None
    return f"{parts.scheme}://{parts.netloc.lower()}"


def _require_endpoints_on_issuer_origin(api_url: str, metadata: dict[str, Any]) -> None:
    """Refuse metadata whose endpoints are not on the issuer's own origin over HTTPS: the stored sign-in is kept under
    the issuer, so its refresh token only ever goes to that origin, and the browser is only ever sent there."""
    issuer_origin = _resolve_origin(metadata.get("issuer"))
    for field_name in ("issuer", "authorization_endpoint", "token_endpoint", "registration_endpoint",
                       "revocation_endpoint"):
        if issuer_origin is None or _resolve_origin(metadata.get(field_name)) != issuer_origin:
            raise StudioError("Heptabase's sign-in is not available",
                              f"the metadata at {api_url} gives {field_name} {metadata.get(field_name)!r}, which is "
                              "not on the issuer's own HTTPS origin",
                              "check EXPLAINER_STUDIO_HEPTABASE_API_URL if it is set; otherwise try again later, and "
                              "if it keeps failing, tell the Heptabase team")


def fetch_authorization_server(api_url: str) -> AuthorizationServer:
    """Heptabase's OAuth server as its metadata describes it, asked once per process."""
    if api_url in _authorization_server_by_api_url_map:
        return _authorization_server_by_api_url_map[api_url]
    status_code, metadata = _fetch_json("GET", f"{api_url}/.well-known/oauth-authorization-server")
    if status_code != 200 or not isinstance(metadata, dict):
        raise StudioError("Heptabase's sign-in is not available", f"its metadata answered HTTP {status_code}",
                          "try again later")
    _require_endpoints_on_issuer_origin(api_url, metadata)
    authorization_server = AuthorizationServer(
        issuer=metadata["issuer"].rstrip("/"), authorization_endpoint=metadata["authorization_endpoint"],
        token_endpoint=metadata["token_endpoint"], registration_endpoint=metadata["registration_endpoint"],
        revocation_endpoint=metadata["revocation_endpoint"])
    _authorization_server_by_api_url_map[api_url] = authorization_server
    return authorization_server


def find_issuer(api_url: str) -> str | None:
    """The issuer of the Heptabase at `api_url`, or None when it cannot be reached."""
    try:
        return fetch_authorization_server(api_url).issuer
    except StudioError:
        return None


# Stored sign-in -------------------------------------------------------------------------------------------------------
def _read_sign_in(issuer: str) -> dict[str, str]:
    sign_in = read_credentials().get(CREDENTIALS_TABLE_NAME, {}).get(issuer)
    return {key: value for key, value in sign_in.items() if isinstance(value, str)} \
        if isinstance(sign_in, dict) else {}


def _write_sign_in(issuer: str, sign_in: dict[str, str]) -> None:
    """Replace the stored sign-in to `issuer`, keeping everything else in credentials.toml. The caller holds the
    credentials file's lock."""
    credentials = read_credentials()
    credentials.setdefault(CREDENTIALS_TABLE_NAME, {})[issuer] = sign_in
    write_credentials(credentials)


def _delete_sign_in(issuer: str) -> None:
    """Delete the stored sign-in to `issuer`, keeping everything else in credentials.toml. The caller holds the
    credentials file's lock."""
    credentials = read_credentials()
    sign_in_by_issuer_map = credentials.get(CREDENTIALS_TABLE_NAME, {})
    if issuer not in sign_in_by_issuer_map:
        return
    del sign_in_by_issuer_map[issuer]
    if not sign_in_by_issuer_map:
        del credentials[CREDENTIALS_TABLE_NAME]
    write_credentials(credentials)


def _build_sign_in_required_error(sign_in: dict[str, str]) -> HeptabaseSignInRequiredError:
    """For a stored sign-in without a refresh token: one Heptabase refused keeps its account, and none has none."""
    if sign_in.get("account_id"):
        return HeptabaseSignInRequiredError("Heptabase no longer accepts the sign-in", "sign_in_expired")
    return HeptabaseSignInRequiredError("Studio has no Heptabase sign-in on this computer", "signed_out")


def require_signed_in_account_id(issuer: str) -> str:
    """The account this computer is signed in to at `issuer` with. Raises HeptabaseSignInRequiredError when it is
    not signed in."""
    sign_in = _read_sign_in(issuer)
    if not sign_in.get("refresh_token") or not sign_in.get("account_id"):
        raise _build_sign_in_required_error(sign_in)
    return sign_in["account_id"]


def find_signed_in_email(issuer: str) -> str | None:
    """The email of the account this computer is signed in to at `issuer` with, or None when it is not signed in."""
    sign_in = _read_sign_in(issuer)
    return sign_in.get("email") if sign_in.get("refresh_token") else None


# OAuth ----------------------------------------------------------------------------------------------------------------
def _ensure_client_id(api_url: str, authorization_server: AuthorizationServer, redirect_uri: str) -> str:
    """The client id Studio registered with Heptabase's OAuth server, registering it the first time. A loopback
    redirect URI may use any port, so one registration serves every page server."""
    with hold_credentials_lock():
        sign_in = _read_sign_in(authorization_server.issuer)
        if sign_in.get("client_id"):
            return sign_in["client_id"]
        status_code, registration = _fetch_json("POST", authorization_server.registration_endpoint, json={
            "client_name": CLIENT_DISPLAY_NAME, "application_type": "native", "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"],
            "token_endpoint_auth_method": "none", "scope": OAUTH_SCOPE})
        if status_code not in (200, 201) or not isinstance(registration, dict) or "client_id" not in registration:
            raise StudioError("Studio could not register with Heptabase", f"registration answered HTTP {status_code}",
                              "try again later")
        _write_sign_in(authorization_server.issuer, {"client_id": registration["client_id"]})
        return registration["client_id"]


def _build_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def create_sign_in_attempt(redirect_uri: str, return_path: str) -> tuple[SignInAttempt, str]:
    """A new sign-in and the URL to open for it, on Heptabase's consent page."""
    api_url = resolve_heptabase_api_url()
    authorization_server = fetch_authorization_server(api_url)
    attempt = SignInAttempt(api_url=api_url, issuer=authorization_server.issuer, redirect_uri=redirect_uri,
                            return_path=return_path,
                            client_id=_ensure_client_id(api_url, authorization_server, redirect_uri),
                            state=secrets.token_urlsafe(24), code_verifier=secrets.token_urlsafe(48))
    authorization_url = authorization_server.authorization_endpoint + "?" + urlencode({
        "response_type": "code", "client_id": attempt.client_id, "redirect_uri": redirect_uri, "scope": OAUTH_SCOPE,
        "resource": authorization_server.resource_url, "state": attempt.state, "prompt": "consent",
        "code_challenge": _build_code_challenge(attempt.code_verifier), "code_challenge_method": "S256"})
    return attempt, authorization_url


def check_is_sign_in_attempt_expired(attempt: SignInAttempt) -> bool:
    return time.monotonic() - attempt.created_at_monotonic_seconds > SIGN_IN_ATTEMPT_LIFETIME_SECONDS


def _remember_access_token(issuer: str, token_response: dict[str, Any], sign_in: dict[str, str]) -> AccessToken:
    lifetime_seconds = float(token_response.get("expires_in") or 3600)
    access_token = AccessToken(token_response["access_token"], time.monotonic() + lifetime_seconds,
                               sign_in["client_id"], sign_in.get("account_id", ""))
    _access_token_by_issuer_map[issuer] = access_token
    return access_token


def _request_tokens(api_url: str, form: dict[str, str]) -> tuple[int, Any]:
    authorization_server = fetch_authorization_server(api_url)
    # a redirect would carry the code or the refresh token to wherever it points
    return _fetch_json("POST", authorization_server.token_endpoint, follow_redirects=False,
                       data={**form, "resource": authorization_server.resource_url})


def _fetch_account(api_url: str, access_token: str) -> tuple[str, str]:
    """The account an access token is for and its email: the OAuth server's user info (`sub` and `email`). Heptabase
    issues no ID token."""
    status_code, user_info = _fetch_json("GET", f"{api_url}/me", headers={"Authorization": f"Bearer {access_token}"})
    if _read_error_code(user_info) == UPGRADE_REQUIRED_CODE:
        raise HeptabaseRequestError("Heptabase did not say which account signed in", status_code, UPGRADE_REQUIRED_CODE)
    if status_code != 200 or not isinstance(user_info, dict) or not isinstance(user_info.get("sub"), str) \
            or not isinstance(user_info.get("email"), str):
        raise StudioError("Heptabase did not say which account signed in", f"/me answered HTTP {status_code}",
                          "sign in again from the video page")
    return user_info["sub"], user_info["email"]


def finish_sign_in(attempt: SignInAttempt, code: str) -> None:
    """Exchange the authorization code for tokens, learn the account, and keep the refresh token."""
    status_code, token_response = _request_tokens(attempt.api_url, {
        "grant_type": "authorization_code", "code": code, "redirect_uri": attempt.redirect_uri,
        "client_id": attempt.client_id, "code_verifier": attempt.code_verifier})
    if status_code != 200 or not isinstance(token_response, dict) or "refresh_token" not in token_response:
        raise StudioError("Heptabase did not finish the sign-in", f"its token endpoint answered HTTP {status_code}",
                          "sign in again from the video page")
    account_id, email = _fetch_account(attempt.api_url, token_response["access_token"])
    sign_in = {"client_id": attempt.client_id, "account_id": account_id, "email": email,
               "refresh_token": token_response["refresh_token"]}
    with hold_credentials_lock():
        _write_sign_in(attempt.issuer, sign_in)
    with _access_token_lock:
        _remember_access_token(attempt.issuer, token_response, sign_in)


def fetch_access_token(api_url: str) -> AccessToken:
    """A current access token for the REST API, refreshed when needed.

    Heptabase gives a new refresh token on every refresh and refuses a used one, so the refresh holds the credentials
    file's lock and re-reads the token inside it: page servers of other series may refresh at the same time. They may
    also sign out, or in with another account, so the token in memory serves only while the stored sign-in is still the
    one it was given for.
    """
    issuer = fetch_authorization_server(api_url).issuer
    with _access_token_lock:
        access_token = _access_token_by_issuer_map.get(issuer)
        sign_in = _read_sign_in(issuer)
        if access_token and sign_in.get("refresh_token") and sign_in.get("client_id") == access_token.client_id \
                and sign_in.get("account_id") == access_token.account_id \
                and access_token.expires_at_monotonic_seconds - time.monotonic() > ACCESS_TOKEN_MARGIN_SECONDS:
            return access_token
        with hold_credentials_lock():
            sign_in = _read_sign_in(issuer)
            if not sign_in.get("refresh_token"):
                _access_token_by_issuer_map.pop(issuer, None)
                raise _build_sign_in_required_error(sign_in)
            status_code, token_response = _request_tokens(api_url, {
                "grant_type": "refresh_token", "refresh_token": sign_in["refresh_token"],
                "client_id": sign_in["client_id"]})
            if status_code in (400, 401) and isinstance(token_response, dict) \
                    and token_response.get("error") == "invalid_grant":
                # the account stays, so every page tells an expired sign-in from a sign-out
                expired_sign_in = {key: value for key, value in sign_in.items() if key != "refresh_token"}
                _write_sign_in(issuer, expired_sign_in)
                raise _build_sign_in_required_error(expired_sign_in)
            if status_code != 200 or not isinstance(token_response, dict):
                raise StudioError("Heptabase did not give an access token",
                                  f"its token endpoint answered HTTP {status_code}", "try again later")
            _write_sign_in(issuer, {**sign_in, "refresh_token": token_response.get("refresh_token")
                                    or sign_in["refresh_token"]})
        return _remember_access_token(issuer, token_response, sign_in)


def sign_out(api_url: str) -> None:
    """Sign this computer out of Heptabase: revoke the refresh token, which ends the access tokens given with it, and
    delete the stored sign-in, client registration included, so the next sign-in registers again. The stored sign-in
    goes even when Heptabase cannot be reached to revoke it: nothing on this computer can use the token after."""
    authorization_server = fetch_authorization_server(api_url)
    issuer = authorization_server.issuer
    with _access_token_lock:
        _access_token_by_issuer_map.pop(issuer, None)
        with hold_credentials_lock():
            sign_in = _read_sign_in(issuer)
            if sign_in.get("refresh_token") and sign_in.get("client_id"):
                try:
                    _fetch_json("POST", authorization_server.revocation_endpoint, follow_redirects=False, data={
                        "token": sign_in["refresh_token"], "token_type_hint": "refresh_token",
                        "client_id": sign_in["client_id"]})
                except StudioError:
                    pass
            _delete_sign_in(issuer)


def forget_access_token(api_url: str) -> None:
    """Drop the access token in memory, so the next request refreshes it (Heptabase refused it early)."""
    issuer = fetch_authorization_server(api_url).issuer
    with _access_token_lock:
        _access_token_by_issuer_map.pop(issuer, None)


def call_rest_api(api_url: str, path: str, body: dict[str, Any]) -> Any:
    """POST `body` to the REST API with the user's access token; the parsed JSON answer (None for a plain one).
    Raises HeptabaseSignInRequiredError when Heptabase refuses the sign-in, HeptabaseRequestError for any other
    refusal."""
    for attempt_number in (1, 2):
        access_token = fetch_access_token(api_url)
        status_code, response_body = _fetch_json(
            "POST", f"{resolve_rest_api_url(api_url)}{path}", json=body,
            headers={"Authorization": f"Bearer {access_token.value}"})
        code = _read_error_code(response_body)
        if code == UPGRADE_REQUIRED_CODE:  # whatever the status: a new sign-in would not help
            raise HeptabaseRequestError(f"Heptabase refused {path}", status_code, code)
        if status_code == 401 and attempt_number == 1:
            forget_access_token(api_url)  # revoked or expired early: refresh once
            continue
        if status_code == 401:
            raise HeptabaseSignInRequiredError("Heptabase refused the access token", "sign_in_expired")
        if not 200 <= status_code < 300:
            raise HeptabaseRequestError(f"Heptabase refused {path}", status_code, code)
        return response_body
    raise AssertionError("unreachable")
