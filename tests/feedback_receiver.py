"""A minimal local receiver for feedback bundles, standing in for the Heptabase backend's endpoint.

Tests start it in a thread; by hand: `python tests/feedback_receiver.py --port 8799 --store <folder>` and point
EXPLAINER_STUDIO_FEEDBACK_URL at the printed URL. It checks the content type, the feedback id header (a UUID) and the
Explainer Studio version header, and answers 201 with the bundle's id; `failure_status_code`
makes every request fail with that status.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import threading
import zipfile
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FEEDBACK_ID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


@dataclass(frozen=True)
class ReceivedBundle:
    feedback_id: str
    explainer_studio_version: str
    path_to_content_map: dict[str, bytes]

    def read_json(self, path: str) -> dict:
        return json.loads(self.path_to_content_map[path])


class Receiver(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int = 0, store_dir_path: Path | None = None):
        super().__init__(("127.0.0.1", port), _Handler)
        self.bundles: list[ReceivedBundle] = []
        self.store_dir_path = store_dir_path
        self.failure_status_code: int | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}/v1/explainerStudio/submitFeedbackBundle"

    def start(self) -> Receiver:
        threading.Thread(target=self.serve_forever, daemon=True).start()
        return self


class _Handler(BaseHTTPRequestHandler):
    server: Receiver

    def log_message(self, *args: object) -> None:
        pass

    def _reply(self, status: int, body: dict) -> None:
        encoded_body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.server.failure_status_code:
            return self._reply(self.server.failure_status_code, {"error": "failing on purpose"})
        feedback_id = self.headers.get("X-Explainer-Studio-Feedback-Id") or ""
        explainer_studio_version = self.headers.get("X-Explainer-Studio-Version") or ""
        if self.headers.get("Content-Type") != "application/zip" or not FEEDBACK_ID_PATTERN.fullmatch(feedback_id) \
                or not explainer_studio_version or not body:
            return self._reply(400, {"code": "invalid_request_body"})
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            path_to_content_map = {name: archive.read(name) for name in archive.namelist()}
        self.server.bundles.append(ReceivedBundle(feedback_id, explainer_studio_version, path_to_content_map))
        if self.server.store_dir_path is not None:
            bundle_dir_path = self.server.store_dir_path / feedback_id
            bundle_dir_path.mkdir(parents=True, exist_ok=True)
            (bundle_dir_path / f"{len(self.server.bundles):03d}.zip").write_bytes(body)
        self._reply(201, {"id": str(len(self.server.bundles))})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8799)
    parser.add_argument("--store", dest="store_dir_path", type=Path, default=None)
    arguments = parser.parse_args()
    receiver = Receiver(arguments.port, arguments.store_dir_path)
    print(receiver.url, flush=True)
    receiver.serve_forever()
