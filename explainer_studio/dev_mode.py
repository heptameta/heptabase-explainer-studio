"""Dev mode: what people improving Explainer Studio need while they make and watch videos, on for this computer.

It adds ways to observe: how closely the user watched (watch depth), and each episode's cost report in `deliver`'s
output and on the video page, with dollars worked out from the local price table (`model_prices`). It never changes
how a video is made (the guide, the gates and the commands behave the same), so what a developer tests is what users
get. The setting lives in the user's settings file, read on every use, so pages pick up a change when they reload.
"""

from __future__ import annotations

import tomllib

import tomli_w

from .file_io import hold_lock, write_text_atomic
from .user_dirs import get_settings_file_path


def _read_settings() -> dict:
    path = get_settings_file_path()
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def check_is_dev_mode_on() -> bool:
    return _read_settings().get("is_dev_mode_on") is True


def set_dev_mode(is_on: bool) -> None:
    path = get_settings_file_path()
    with hold_lock(path):
        settings = _read_settings()
        settings["is_dev_mode_on"] = is_on
        write_text_atomic(path, tomli_w.dumps(settings))
