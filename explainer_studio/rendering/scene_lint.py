"""Refuse scene code that cannot work before ManimGL runs it.

Models often mix Manim Community Edition into ManimGL scenes, and the render then fails late or silently draws the
wrong thing. Each pattern below is a mistake seen in real episodes, with the fix in its message.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..errors import StudioError

PATTERNS = [
    (r"^\s*from manim import", "this is Manim Community; start the file with `from explainer_studio.scene_kit import *`"),
    (r"^\s*import manim\b", "this is Manim Community; start the file with `from explainer_studio.scene_kit import *`"),
    (r"\bMathTex\(", "ManimGL has no MathTex; use Tex(...)"),
    (r"(?<![\w.])Create\(", "ManimGL has no Create; use ShowCreation(...)"),
    (r"\bconfig\.\w+\s*=", "ManimGL has no global config object; preview and render choose the resolution"),
    (r"self\.camera\.frame", "ManimGL scenes move the camera with self.frame"),
    (r"\b(MovingCameraScene|ThreeDScene|ZoomedScene)\b",
     "subclass NarratedScene and move self.frame instead (3D works in any scene)"),
    (r"\b[xy]_length\s*=", "ManimGL Axes take width= and height=, not x_length/y_length"),
    (r"\bCircumscribe\(", "ManimGL has no Circumscribe; use FlashAround(...) or get_highlight_rectangle(...)"),
    (r"(?<![\w.])Table\(", "ManimGL has no Table; use get_table(...)"),
    (r"(?<![\w.])Star\(", "ManimGL has no Star class; draw it with RegularPolygram or a VMobject"),
    (r"\bAddTextLetterByLetter\(", "ManimGL has no AddTextLetterByLetter; use Write(...)"),
    (r"\bVGroup\([^#]*(ImageMobject|get_image|get_clip|get_paper_figure|get_portrait_card)",
     "images are not vector mobjects: use Group(...) around anything holding a picture"),
    (r"\.set_fill\([^#]*\bfamily\s*=", "set_fill has no family=; it recurses by default (recurse=False to limit it)"),
    (r"(?i)(arc|curve)\w*(\[[^\]]*\])?\.(animate\.)?set_opacity\(",
     ("set_opacity also sets the fill, so an arc or curved arrow turns into a filled blob; use "
      "set_stroke(opacity=...) or dim(...)")),
    (r"\.add_updater\(\s*lambda\s+\w+\s*,\s*\w+\s*=",
     "a two-argument lambda updater receives dt as its second argument; bind loop variables with functools.partial"),
    (r"\bCurvedArrow\([^#]*fill", "CurvedArrow with a fill turns into a blob; use get_curved_arrow(...)"),
    (r"\\;\s*\\;|\\!", r"ManimGL Tex fails on \;\; and \! (\UseTextAccent / Missing delimiter); use \quad or \,"),
    (r"self\.add_sound\(", "use self.play_sound(...), which records the sound for the mix and timeline.json"),
    (r"self\.sfx\(", "use self.play_sound(...)"),
]


PLAY_PATH_ARC_FIX = ("path_arc belongs to the animation, not to play: Transform(a, b, path_arc=PI/2) or "
                     "a.animate(path_arc=PI/2)")


def _parse_play_arguments(text: str):
    """(offset, text) of each self.play(...) call's own arguments, with nested brackets, strings and comments blanked
    out, so a keyword passed to an animation inside the call is not mistaken for one passed to play."""
    for match in re.finditer(r"self\.play\(", text):
        if "#" in text[text.rfind("\n", 0, match.start()) + 1:match.start()]:
            continue  # commented out
        kept, depth, i = [], 1, match.end()
        while i < len(text) and depth:
            character = text[i]
            if character == "#":
                end = text.find("\n", i)
                end = len(text) if end < 0 else end
                kept.append(" " * (end - i))
                i = end
                continue
            if character in "\"'":
                quote = character * 3 if text.startswith(character * 3, i) else character
                j = i + len(quote)
                while j < len(text) and not text.startswith(quote, j):
                    j += 2 if text[j] == "\\" else 1
                kept.append(" " * (j + len(quote) - i))
                i = j + len(quote)
                continue
            depth += character in "([{"
            depth -= character in ")]}"
            kept.append(character if depth == 1 or (depth == 2 and character in "([{") else " ")
            i += 1
        yield match.end(), "".join(kept)


def lint_text(text: str) -> list[tuple[int, str, str]]:
    """(line number, fix, line) for every problem in a scene file's text."""
    problems = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        for pattern, fix in PATTERNS:
            if re.search(pattern, line):
                problems.append((line_number, fix, line.strip()))
    for offset, arguments in _parse_play_arguments(text):
        for keyword_match in re.finditer(r"\bpath_arc\s*=(?!=)", arguments):
            line_number = text.count("\n", 0, offset + keyword_match.start()) + 1
            problems.append((line_number, PLAY_PATH_ARC_FIX, lines[line_number - 1].strip()))
    return sorted(problems, key=lambda problem: problem[0])


def require_clean_scene_code(file_paths: list[Path], base_dir_path: Path) -> None:
    """Raise StudioError listing every problem in these files (paths shown relative to `base_dir_path`)."""
    detail_lines = []
    for path in file_paths:
        label = path.relative_to(base_dir_path).as_posix() if path.is_relative_to(base_dir_path) else str(path)
        detail_lines += [f"{label}:{line_number}: {fix}\n      {line[:110]}"
                         for line_number, fix, line in lint_text(path.read_text(encoding="utf-8"))]
    if detail_lines:
        raise StudioError("scene code uses Manim Community syntax or a known ManimGL pitfall",
                          f"{len(detail_lines)} line(s) would fail or draw the wrong thing",
                          "fix each line as described, then run the command again", detail_lines[:30])
