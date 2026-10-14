from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_DIR_PATH = Path(__file__).resolve().parent.parent


def run_script(script_name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(REPOSITORY_DIR_PATH / "scripts" / script_name), *arguments],
                          capture_output=True, text=True, check=False)


def test_generated_files_are_up_to_date() -> None:
    result = run_script("release.py", "--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_guide_follows_its_conventions() -> None:
    result = run_script("check_guide.py")
    assert result.returncode == 0, result.stdout
