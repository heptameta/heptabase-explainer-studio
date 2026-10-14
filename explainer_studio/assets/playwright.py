"""Scripted screen recordings of a web page in headless Chromium: a visible cursor glides to each element before it
is clicked, and every step's time and element box are written to <name>.steps.json for callouts drawn in ManimGL.

steps.json: {"viewport": [w, h], "steps": [{"index", "action", "argument", "start_seconds", "end_seconds", "box"}]},
with times in seconds into the video and the box as [x0, y0, x1, y1] fractions of the viewport from the top-left (null
when the step has no element).
"""

from __future__ import annotations

import json
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from ..errors import StudioError
from ..paths import Series
from ..schemas.playwright_recording_spec import PlaywrightRecordingSpec
from .common import (
    choose_output_file_path,
    find_spec_input,
    load_spec,
    run_ffmpeg,
    sanitize_file_stem,
    write_asset_text,
)

CURSOR_SCRIPT = """
(() => {
  if (window.__cursor) return;
  const cursor = document.createElement('div');
  cursor.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;border-radius:50%;' +
    'background:rgba(255,220,0,.9);border:2px solid #222;box-shadow:0 0 0 6px rgba(255,220,0,.25);' +
    'z-index:2147483647;pointer-events:none;' +
    'transform:translate(-50%,-50%);transition:left .6s ease, top .6s ease, transform .15s ease';
  document.documentElement.appendChild(cursor);
  window.__cursor = cursor;
  window.__moveCursor = (x, y) => { cursor.style.left = x + 'px'; cursor.style.top = y + 'px'; };
  window.__pressCursor = () => { cursor.style.transform = 'translate(-50%,-50%) scale(.7)';
                                 setTimeout(() => cursor.style.transform = 'translate(-50%,-50%)', 180); };
  cursor.style.left = (innerWidth / 2) + 'px'; cursor.style.top = (innerHeight / 2) + 'px';
})();
"""


def _record(spec: PlaywrightRecordingSpec, target_url: str, work_dir_path: Path) -> tuple[Path, list[dict]]:
    from playwright.sync_api import Error, sync_playwright

    width_pixels, height_pixels = spec.viewport
    step_records = []
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Error as error:
            raise StudioError("Playwright's Chromium does not start", str(error).splitlines()[0][:300],
                              "run `explainer-studio setup playwright`") from None
        viewport = {"width": width_pixels, "height": height_pixels}
        context = browser.new_context(viewport=viewport, record_video_dir=str(work_dir_path),
                                      record_video_size=viewport, device_scale_factor=1)
        page = context.new_page()
        started_monotonic_seconds = time.monotonic()

        def measure_elapsed_seconds() -> float:
            return round(time.monotonic() - started_monotonic_seconds, 3)

        def locate(selector: str):
            element = page.locator(selector).first
            element.scroll_into_view_if_needed(timeout=15000)
            box = element.bounding_box()
            box_fractions = None if box is None else [box["x"] / width_pixels, box["y"] / height_pixels,
                                                      (box["x"] + box["width"]) / width_pixels,
                                                      (box["y"] + box["height"]) / height_pixels]
            return element, box_fractions

        def glide(box) -> None:
            if box:
                page.evaluate(CURSOR_SCRIPT)
                center_x, center_y = (box[0] + box[2]) / 2 * width_pixels, (box[1] + box[3]) / 2 * height_pixels
                page.evaluate(f"window.__moveCursor({center_x}, {center_y})")
                page.wait_for_timeout(700)

        try:
            page.goto(target_url, wait_until="networkidle")
            page.evaluate(CURSOR_SCRIPT)
            page.wait_for_timeout(800)
            for step_index, step in enumerate(spec.steps):
                action, argument = next(iter(step.items()))
                step_record = {"index": step_index, "action": action, "argument": argument,
                               "start_seconds": measure_elapsed_seconds(), "box": None}
                if action in ("click", "hover", "highlight"):
                    element, step_record["box"] = locate(argument)
                    glide(step_record["box"])
                    if action == "click":
                        page.evaluate("window.__pressCursor && window.__pressCursor()")
                        element.click()
                    elif action == "hover":
                        element.hover()
                    page.wait_for_timeout(1200 if action == "highlight" else 600)
                elif action == "type":
                    selector, text = argument
                    element, step_record["box"] = locate(selector)
                    if (element.get_attribute("type") or "").lower() == "password":
                        raise StudioError("the recording would type into a password field",
                                          f"step {step_index + 1} types into {selector}",
                                          "never record real credentials; show a filled demo page instead")
                    glide(step_record["box"])
                    element.click()
                    page.keyboard.type(str(text), delay=70)
                    page.wait_for_timeout(400)
                elif action == "press":
                    page.keyboard.press(str(argument))
                    page.wait_for_timeout(700)
                elif action == "scroll":
                    page.mouse.wheel(0, float(argument))
                    page.wait_for_timeout(900)
                elif action == "wait":
                    page.wait_for_timeout(int(float(argument) * 1000))
                elif action == "goto":
                    page.goto(str(argument), wait_until="networkidle")
                    page.evaluate(CURSOR_SCRIPT)
                    page.wait_for_timeout(600)
                step_record["end_seconds"] = measure_elapsed_seconds()
                step_records.append(step_record)
            page.wait_for_timeout(800)
        except Error as error:
            raise StudioError("the recording stopped at a step", str(error).splitlines()[0][:300],
                              "fix the selector or URL in the spec and run again") from None
        finally:
            video_file_path = page.video.path() if page.video else None
            context.close()
            browser.close()
    return Path(video_file_path), step_records


def record(series: Series, spec_path: Path, destination_path: Path | None,
           report_progress: Callable[[str], None]) -> dict[str, Path]:
    spec = load_spec(spec_path, PlaywrightRecordingSpec)
    file_stem = sanitize_file_stem(spec.name or spec_path.stem)
    target_url = spec.url or find_spec_input(spec.html, spec_path.resolve().parent, series).as_uri()
    video_file_path = choose_output_file_path(series, "video", f"{file_stem}.mp4", destination_path)
    with tempfile.TemporaryDirectory(prefix="explainer-studio-recording-") as temporary_dir_path:
        report_progress(f"recording {len(spec.steps)} step(s) of {spec.url or spec.html}")
        webm_file_path, step_records = _record(spec, target_url, Path(temporary_dir_path))
        video_file_path.parent.mkdir(parents=True, exist_ok=True)
        run_ffmpeg(["-i", str(webm_file_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", "30",
                    "-movflags", "+faststart", str(video_file_path)], "encode the recording")
    steps_file_path = video_file_path.with_suffix(".steps.json")
    write_asset_text(steps_file_path, json.dumps({"viewport": list(spec.viewport), "steps": step_records},
                                                 ensure_ascii=False, indent=1) + "\n")
    return {"video": video_file_path, "steps": steps_file_path}
