"""The page server of one series: the plan page, the video page, their JSON API and the delivered media.

It listens on 127.0.0.1 only and answers only requests whose path starts with its random token and whose Host is a
local address, so another website cannot drive it through the browser. Every response carries
`Referrer-Policy: no-referrer`, so the token never leaves through a link. It stops after `--idle-seconds` without a
request (the pages' page digest polling does not count) and is started by `web.launcher`:

    python -m explainer_studio.web.server --series <series folder> --runtime-file <path>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import secrets
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from .. import __version__
from ..errors import StudioError
from ..feedback import add_comment, delete_comment, edit_comment, load_feedback, set_survey_answer
from ..feedback_bundle import resolve_unshared_items, share_feedback
from ..file_io import get_current_time, write_text_atomic
from ..gaps import load_gaps
from ..paths import Series
from ..schemas.feedback import CommentAnchor, EpisodeAnchor, MomentAnchor
from . import pages
from .i18n import translate
from .launcher import read_runtime_info
from .plan_edits import InvalidEditError, PlanConflictError, compute_plan_version, write_plan_field

IDLE_SECONDS = 2 * 60 * 60
MAX_BODY_BYTES = 1_000_000
CHUNK_BYTES = 256 * 1024
CONTENT_TYPE_BY_SUFFIX_MAP = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                              ".woff2": "font/woff2", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8",
                              ".png": "image/png", ".mp4": "video/mp4", ".vtt": "text/vtt; charset=utf-8"}
SECURITY_HEADER_VALUE_BY_NAME_MAP = {
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' "
                               "'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'self'; "
                               "frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
}
# the delivered subtitles in one language, served as WebVTT from the delivered SRT
SUBTITLES_MEDIA_NAME_PATTERN = re.compile(r"subtitles\.([A-Za-z0-9-]+)\.vtt")


def convert_srt_to_vtt(srt_text: str) -> str:
    """WebVTT for the page's player from the delivered SRT (the delivered file stays SRT)."""
    vtt_body = srt_text.lstrip("﻿").replace("\r\n", "\n")
    vtt_body = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", vtt_body)
    return "WEBVTT\n\n" + vtt_body.strip() + "\n"


def _parse_comment_anchor(raw_anchor: Any) -> CommentAnchor:
    """The comment anchor in a page request: {kind: "moment", timeSeconds} or {kind: "episode"}."""
    kind = raw_anchor.get("kind") if isinstance(raw_anchor, dict) else None
    if kind == "episode":
        return EpisodeAnchor(kind="episode")
    time_seconds = raw_anchor.get("timeSeconds") if kind == "moment" else None
    if isinstance(time_seconds, int | float) and not isinstance(time_seconds, bool) and math.isfinite(time_seconds) \
            and time_seconds >= 0:
        return MomentAnchor(kind="moment", time_seconds=float(time_seconds))
    raise InvalidEditError("invalid")


class PageServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"  # on Windows it would let a second server share the port

    def __init__(self, series: Series, token: str, port: int, idle_seconds: float):
        try:
            super().__init__(("127.0.0.1", port), PageRequestHandler)
        except OSError:
            super().__init__(("127.0.0.1", 0), PageRequestHandler)
        self.series = series
        self.token = token
        self.idle_seconds = idle_seconds
        self.last_activity_monotonic_seconds = time.monotonic()
        self.stop_event = threading.Event()

    @property
    def port(self) -> int:
        return self.server_address[1]

    def record_activity(self) -> None:
        self.last_activity_monotonic_seconds = time.monotonic()

    def watch_idle(self) -> None:
        interval_seconds = max(0.1, min(30.0, self.idle_seconds / 10))
        while not self.stop_event.wait(interval_seconds):
            if time.monotonic() - self.last_activity_monotonic_seconds > self.idle_seconds:
                self.stop()
                return

    def stop(self) -> None:
        if not self.stop_event.is_set():
            self.stop_event.set()
            threading.Thread(target=self.shutdown, daemon=True).start()


class PageRequestHandler(BaseHTTPRequestHandler):
    server: PageServer
    protocol_version = "HTTP/1.1"

    def version_string(self) -> str:
        return "ExplainerStudio"

    def log_message(self, format: str, *args: Any) -> None:
        pass  # request paths carry the token: never log them

    # responses ------------------------------------------------------------------------------------------------------
    def _send_headers(self, status: int, content_type: str, length_bytes: int,
                      extra_header_value_by_name_map: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length_bytes))
        header_value_by_name_map = {**SECURITY_HEADER_VALUE_BY_NAME_MAP, "Cache-Control": "no-store",
                                    **(extra_header_value_by_name_map or {})}
        for name, value in header_value_by_name_map.items():
            self.send_header(name, value)
        self.end_headers()

    def _send(self, status: int, body: bytes, content_type: str,
              extra_header_value_by_name_map: dict[str, str] | None = None) -> None:
        self._send_headers(status, content_type, len(body), extra_header_value_by_name_map)
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: int, value: Any) -> None:
        self._send(status, json.dumps(value, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _send_html(self, text: str) -> None:
        self._send(200, text.encode("utf-8"), "text/html; charset=utf-8")

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        """A file, honouring a Range request so the video can seek."""
        size_bytes = path.stat().st_size
        content_type = content_type or CONTENT_TYPE_BY_SUFFIX_MAP.get(path.suffix.lower(), "application/octet-stream")
        start_byte, end_byte, status = 0, size_bytes - 1, 200
        range_match = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "").split(",")[0].strip())
        if range_match and (range_match.group(1) or range_match.group(2)):
            if range_match.group(1):
                start_byte = int(range_match.group(1))
                end_byte = min(int(range_match.group(2)), size_bytes - 1) if range_match.group(2) else size_bytes - 1
            else:
                start_byte = max(0, size_bytes - int(range_match.group(2)))
            if start_byte > end_byte or start_byte >= size_bytes:
                return self._send(416, b"", "text/plain", {"Content-Range": f"bytes */{size_bytes}"})
            status = 206
        extra_header_value_by_name_map = {"Accept-Ranges": "bytes", "Cache-Control": "no-cache"}
        if status == 206:
            extra_header_value_by_name_map["Content-Range"] = f"bytes {start_byte}-{end_byte}/{size_bytes}"
        self._send_headers(status, content_type, end_byte - start_byte + 1, extra_header_value_by_name_map)
        if self.command == "HEAD":
            return
        with path.open("rb") as handle:
            handle.seek(start_byte)
            remaining_bytes = end_byte - start_byte + 1
            while remaining_bytes > 0:
                chunk = handle.read(min(CHUNK_BYTES, remaining_bytes))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining_bytes -= len(chunk)

    def _read_json_body(self) -> Any:
        length_bytes = int(self.headers.get("Content-Length") or 0)
        if length_bytes > MAX_BODY_BYTES:
            self.close_connection = True  # the unread body would spoil the next request on this connection
            raise InvalidEditError("invalid")
        raw_body = self.rfile.read(length_bytes)
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            raise InvalidEditError("invalid")  # also keeps plain cross-site form posts out
        try:
            return json.loads(raw_body or b"null")
        except ValueError:
            raise InvalidEditError("invalid") from None

    # routing --------------------------------------------------------------------------------------------------------
    def _check_is_local_host(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in ("127.0.0.1", "localhost", "::1")

    def _handle_request(self, method: str) -> None:
        try:
            url = urlsplit(self.path)
            path_parts = [unquote(part) for part in url.path.split("/") if part]
            if (not self._check_is_local_host() or not path_parts
                    or not secrets.compare_digest(path_parts[0], self.server.token)):
                self.close_connection = True
                return self._send(403, b"forbidden", "text/plain; charset=utf-8")
            route = path_parts[1:]
            if route[:2] != ["api", "page-digest"]:
                self.server.record_activity()
            self._route_request(method, route, parse_qs(url.query))
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser dropped a range request while seeking
        except PlanConflictError:
            self._send_json(409, {"code": "conflict",
                                 "planVersion": compute_plan_version(self.server.series.plan_file_path.read_bytes())})
        except InvalidEditError as error:
            self._send_json(422, {"code": error.code, "details": error.details})
        except StudioError as error:
            self._send_json(400, {"code": "studio", "message": error.what, "details": [error.why, *error.details]})
        except Exception:  # noqa: BLE001 - keep serving; the log has the traceback
            traceback.print_exc(file=sys.stderr)
            try:
                self._send_json(500, {"code": "server"})
            except OSError:
                pass

    def _route_request(self, method: str, route: list[str], query: dict[str, list[str]]) -> None:
        series = self.server.series
        base_url = f"/{self.server.token}"
        match method, route:
            case ("GET" | "HEAD"), ([] | ["plan"]):
                language_code = pages.read_page_language_code(series)
                title = f"{pages.read_series_title(series)} · {translate(language_code, 'plan.eyebrow')}"
                self._send_html(pages.format_page_html("plan", language_code, title, base_url, {"pageName": "plan"}))
            case ("GET" | "HEAD"), ["video", episode_id]:
                series.get_episode_paths(episode_id)
                language_code = pages.read_page_language_code(series)
                self._send_html(pages.format_page_html("video", language_code, pages.read_series_title(series),
                                                       base_url, {"pageName": "video", "episodeId": episode_id}))
            case "GET", ["health"]:
                self._send_json(200, {"explainer_studio_version": __version__,
                                      "series_path": str(series.root_dir_path)})
            case "POST", ["shutdown"]:
                self._send_json(200, {"isStopping": True})
                self.server.stop()
            case ("GET" | "HEAD"), ["static", *path_parts]:
                static_file_path = (pages.STATIC_DIR_PATH / "/".join(path_parts)).resolve()
                if not static_file_path.is_relative_to(pages.STATIC_DIR_PATH) or not static_file_path.is_file():
                    return self._send(404, b"not found", "text/plain")
                self._send_file(static_file_path)
            case "GET", ["api", "page-digest"]:
                episode_id = (query.get("episodeId") or [""])[0]
                self._send_json(200, {"pageDigest": pages.compute_video_page_digest(series, episode_id) if episode_id
                                      else pages.compute_plan_page_digest(series)})
            case "GET", ["api", "plan"]:
                self._send_json(200, pages.compute_plan_page(series))
            case "POST", ["api", "plan"]:
                body = self._read_json_body()
                if not isinstance(body, dict) or not isinstance(body.get("fieldPath"), list):
                    raise InvalidEditError("invalid")
                plan_version = write_plan_field(series, body["fieldPath"], body.get("value"),
                                                str(body.get("planVersion")))
                self._send_json(200, {"planVersion": plan_version,
                                      "pageDigest": pages.compute_plan_page_digest(series)})
            case "GET", ["api", "video", episode_id]:
                self._send_json(200, pages.compute_video_page(series, episode_id))
            case "POST", ["api", "video", episode_id, "comments"]:
                body = self._read_json_body()
                if pages.find_latest_delivery(series, episode_id) is None or not isinstance(body, dict):
                    raise InvalidEditError("invalid")
                comment = add_comment(series, episode_id, str(body.get("text") or ""),
                                      _parse_comment_anchor(body.get("anchor")), "page")
                self._send_json(200, {"id": comment.id})
            case "PATCH", ["api", "video", episode_id, "comments", comment_id]:
                body = self._read_json_body()
                if not isinstance(body, dict):
                    raise InvalidEditError("invalid")
                comment_changes: dict[str, Any] = {}
                if "text" in body:
                    comment_changes["text"] = str(body["text"])
                if "anchor" in body:
                    comment_changes["anchor"] = _parse_comment_anchor(body["anchor"])
                edit_comment(series, episode_id, comment_id, **comment_changes)
                self._send_json(200, {"id": comment_id})
            case "DELETE", ["api", "video", episode_id, "comments", comment_id]:
                delete_comment(series, episode_id, comment_id)
                self._send_json(200, {"id": comment_id})
            case "PUT", ["api", "video", episode_id, "survey-answers", kind]:
                # the current answer to one survey question; a null value removes it
                body = self._read_json_body()
                value = body.get("value") if isinstance(body, dict) else None
                if pages.find_latest_delivery(series, episode_id) is None or not isinstance(body, dict) \
                        or not (value is None or isinstance(value, str)):
                    raise InvalidEditError("invalid")
                try:
                    set_survey_answer(series, episode_id, kind, value)
                except StudioError:  # a question the survey does not ask or an answer it does not offer
                    raise InvalidEditError("invalid") from None
                self._send_json(200, {"kind": kind, "value": value})
            case "GET", ["api", "video", episode_id, "cost-report"]:
                self._send_json(200, pages.compute_video_cost_report(series, episode_id))
            case "GET", ["api", "video", episode_id, "share"]:
                # the confirm dialog's list: the new feedback, what the user wrote that no bundle has carried yet
                unshared_items = resolve_unshared_items(load_feedback(series, episode_id), load_gaps(series))
                self._send_json(200, {"isEmpty": not unshared_items.has_feedback,
                                      "comments": [{"id": comment.id,
                                                    "anchor": pages.convert_comment_anchor_to_page_json(comment.anchor),
                                                    "text": comment.text} for comment in unshared_items.comments],
                                      "surveyAnswers": [{"kind": answer.kind, "value": answer.value}
                                                        for answer in unshared_items.survey_answers]})
            case "POST", ["api", "video", episode_id, "share"]:
                try:
                    shared_items = share_feedback(series, episode_id)
                except StudioError as error:
                    return self._send_json(502, {"code": "not_sent", "message": error.why})
                self._send_json(200, {"isSent": bool(shared_items)})
            case ("GET" | "HEAD"), ["media", episode_id, media_name]:
                # video.mp4, cover.png or subtitles.<language code>.vtt of the latest delivery
                latest_delivery = pages.find_latest_delivery(series, episode_id)
                subtitles_match = SUBTITLES_MEDIA_NAME_PATTERN.fullmatch(media_name)
                delivered_file_key = {"video.mp4": "video_file_path", "cover.png": "cover_file_path"}.get(media_name)
                if latest_delivery is None:
                    media_file_path = None
                elif subtitles_match:
                    language_code = subtitles_match.group(1)
                    media_file_path = latest_delivery["subtitles_file_path_by_language_code_map"].get(language_code)
                else:
                    media_file_path = latest_delivery[delivered_file_key] if delivered_file_key else None
                if media_file_path is None or not media_file_path.is_file():
                    return self._send(404, b"not found", "text/plain")
                if subtitles_match:
                    vtt_text = convert_srt_to_vtt(media_file_path.read_text(encoding="utf-8-sig"))
                    return self._send(200, vtt_text.encode("utf-8"), CONTENT_TYPE_BY_SUFFIX_MAP[".vtt"])
                self._send_file(media_file_path)
            case _:
                self._send(404, b"not found", "text/plain")

    def do_GET(self) -> None:
        self._handle_request("GET")

    def do_HEAD(self) -> None:
        self._handle_request("HEAD")

    def do_POST(self) -> None:
        self._handle_request("POST")

    def do_PUT(self) -> None:
        self._handle_request("PUT")

    def do_PATCH(self) -> None:
        self._handle_request("PATCH")

    def do_DELETE(self) -> None:
        self._handle_request("DELETE")


def _write_runtime_info(runtime_file_path: Path, runtime_info: dict[str, Any]) -> None:
    write_text_atomic(runtime_file_path, json.dumps(runtime_info), is_private=True)


def serve(series: Series, runtime_file_path: Path, idle_seconds: float = IDLE_SECONDS) -> None:
    """Serve until idle. A previous server's port and token are reused when possible, so open tabs keep working."""
    previous_runtime_info = read_runtime_info(runtime_file_path) or {}
    token = previous_runtime_info.get("token") or secrets.token_urlsafe(24)
    server = PageServer(series, token, int(previous_runtime_info.get("port") or 0), idle_seconds)
    runtime_info = {"pid": os.getpid(), "port": server.port, "token": token,
                    "explainer_studio_version": __version__, "series_path": str(series.root_dir_path),
                    "started_at": get_current_time().isoformat()}
    _write_runtime_info(runtime_file_path, runtime_info)
    threading.Thread(target=server.watch_idle, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        current_runtime_info = read_runtime_info(runtime_file_path) or {}
        if current_runtime_info.get("pid") == os.getpid():
            _write_runtime_info(runtime_file_path, {**runtime_info, "pid": None})


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="explainer_studio.web.server")
    parser.add_argument("--series", required=True, type=Path)
    parser.add_argument("--runtime-file", dest="runtime_file_path", required=True, type=Path)
    parser.add_argument("--idle-seconds", type=float, default=IDLE_SECONDS)
    arguments = parser.parse_args(argv)
    serve(Series.find(arguments.series), arguments.runtime_file_path, arguments.idle_seconds)


if __name__ == "__main__":
    main()
