"""Shared by every test. The check-code job runs the tests not marked `render` on a machine without ffmpeg or ManimGL,
so a test that runs them, even through a helper such as `delivered_series.create_series`, must be marked `render`.
One that is not fails here at once, on any computer, instead of only in CI."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys

import pytest

RENDER_PROGRAM_NAMES = {"ffmpeg", "ffprobe"}
RENDER_MODULE_NAMES = {"manimlib", "explainer_studio.scene_kit.render_process"}


def _find_render_program(args: object) -> str | None:
    """The program a subprocess's arguments run, when it is ffmpeg, ffprobe or ManimGL."""
    if isinstance(args, str):
        argv = shlex.split(args)
    elif isinstance(args, (list, tuple)):
        argv = [os.fsdecode(arg) for arg in args]
    else:
        argv = [os.fsdecode(args)]
    if not argv:
        return None
    program_name = os.path.splitext(os.path.basename(argv[0]))[0]
    if program_name in RENDER_PROGRAM_NAMES:
        return program_name
    if argv[0] == sys.executable and len(argv) > 2 and argv[1] == "-m" and argv[2] in RENDER_MODULE_NAMES:
        return argv[2]
    return None


@pytest.fixture(autouse=True)
def refuse_render_programs_outside_render_tests(request: pytest.FixtureRequest,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("render"):
        return

    class RenderGuardPopen(subprocess.Popen):
        def __init__(self, args, *rest, **kwargs) -> None:
            program = _find_render_program(args)
            if program:
                pytest.fail(f"this test runs {program}: mark it @pytest.mark.render (check-code runs the other tests "
                            f"without ffmpeg or ManimGL)", pytrace=False)
            super().__init__(args, *rest, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", RenderGuardPopen)
