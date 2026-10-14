"""`doctor [--json]`."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

import click

from .common import print_result


def format_check_summary_lines(checks) -> list[str]:
    name_width_characters = max(len(check.name) for check in checks)
    lines = []
    for check in checks:
        status = "ok" if check.is_ok else ("MISSING" if check.is_required else "optional")
        lines.append(f"{status:<8} {check.name:<{name_width_characters}}  {check.detail}")
        if not check.is_ok and check.fix:
            lines.append(f"{'':<8} {'':<{name_width_characters}}  fix: {check.fix}")
    return lines


@click.command()
@click.option("--json", "should_print_json", is_flag=True, help="Print the checks as JSON.")
def doctor(should_print_json: bool) -> None:
    """Check what making videos needs, without installing anything. Exits 1 when something required is missing."""
    from .. import __version__
    from ..environment import run_checks

    checks = run_checks()
    is_ready = all(check.is_ok for check in checks if check.is_required)
    if should_print_json:
        print_result(json.dumps({"is_ready": is_ready, "explainer_studio_version": __version__,
                                 "checks": [asdict(check) for check in checks]}, ensure_ascii=False, indent=2))
    else:
        print_result(f"explainer-studio {__version__}")
        for line in format_check_summary_lines(checks):
            print_result(line)
        failing_check_names = [check.name for check in checks if check.is_required and not check.is_ok]
        print_result("ready: everything required is installed" if is_ready else
                     f"not ready: fix {', '.join(failing_check_names)} (see the fix lines)")
    if not is_ready:
        sys.exit(1)
