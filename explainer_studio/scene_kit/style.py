"""Fonts, font sizes and semantic colours shared by every scene, and the CJK-capable LaTeX builder.

Video text uses Noto Sans TC (CJK and Latin) and JetBrains Mono for code; `explainer-studio setup` installs both.
When they are missing, an installed CJK font stands in and the scene reports it once.
"""

from __future__ import annotations

import manimpango
from manimlib import BLACK, GREEN, GREY_A, GREY_B, RED, TEAL, WHITE, YELLOW, TexText
from manimlib.config import manim_config

__all__ = [
    "AFFIRMATION_COLOR",
    "BACKGROUND_COLOR",
    "BODY_FONT_SIZE",
    "CONTRADICTION_COLOR",
    "DIM_OPACITY",
    "FONT",
    "FONT_WARNINGS",
    "FUNCTION_COLOR",
    "HEADING_FONT_SIZE",
    "HIGHLIGHT_COLOR",
    "HIGHLIGHT_RECTANGLE_COLOR",
    "LABEL_FONT_SIZE",
    "META_BACKGROUND_COLOR",
    "MONO_FONT",
    "NAME_COLOR",
    "QUOTE_COLOR",
    "SMALL_FONT_SIZE",
    "TEX_TO_COLOR_MAP",
    "TITLE_FONT_SIZE",
    "YEAR_COLOR",
    "choose_local_text",
    "get_cjk_tex",
]

PREFERRED_FONT = "Noto Sans TC"
PREFERRED_MONO_FONT = "JetBrains Mono"
# Stand-ins when setup has not installed the fonts yet. Heiti TC is left out: Chinese text rendered wrongly in it.
FALLBACK_FONTS = ("PingFang TC", "Noto Sans CJK TC", "Microsoft JhengHei", "Source Han Sans TC")
FALLBACK_MONO_FONTS = ("Menlo", "DejaVu Sans Mono", "Consolas", "Courier New")

FONT_WARNINGS: list[str] = []


def _choose_font(preferred_font: str, fallback_fonts: tuple[str, ...], purpose: str) -> str:
    installed_fonts = set(manimpango.list_fonts())
    if preferred_font in installed_fonts:
        return preferred_font
    chosen = next((name for name in fallback_fonts if name in installed_fonts), preferred_font)
    FONT_WARNINGS.append(f"{preferred_font} is not installed; {purpose} uses {chosen} instead "
                         "(run `explainer-studio setup` to install the video fonts)")
    return chosen


FONT = _choose_font(PREFERRED_FONT, FALLBACK_FONTS, "video text")
MONO_FONT = _choose_font(PREFERRED_MONO_FONT, FALLBACK_MONO_FONTS, "code")
# Text(...) without font= uses the video font, so CJK and Latin text need no helper.
manim_config.text.font = FONT

# Font sizes (Tex/Text font_size; 48 is the ManimGL default)
TITLE_FONT_SIZE = 72
HEADING_FONT_SIZE = 60
BODY_FONT_SIZE = 48
LABEL_FONT_SIZE = 36
SMALL_FONT_SIZE = 24

# Semantic colour roles. A series' concept colours live in its series bible and production/shared/ code.
BACKGROUND_COLOR = BLACK
HIGHLIGHT_COLOR = YELLOW  # "look here" / the key term
HIGHLIGHT_RECTANGLE_COLOR = YELLOW  # get_highlight_rectangle stroke
CONTRADICTION_COLOR = RED  # false, paradox, counterexample
AFFIRMATION_COLOR = GREEN  # true, proven, consistent
DIM_OPACITY = 0.35  # de-emphasised material
META_BACKGROUND_COLOR = "#1A1A1A"  # the dark-grey commentary layer
FUNCTION_COLOR = TEAL  # graphs
YEAR_COLOR = GREY_B
NAME_COLOR = WHITE
QUOTE_COLOR = GREY_A

# Reusable Tex colouring. Wrap variables in braces, e.g. "{x}", so a key only matches intended occurrences.
TEX_TO_COLOR_MAP = {"{x}": "#58C4DD", "{y}": YELLOW}


def get_cjk_tex(text: str, font_size: float = BODY_FONT_SIZE, **kwargs) -> TexText:
    """CJK text with inline LaTeX math, e.g. get_cjk_tex(R"戴德金分割 $(A \\mid B)$"). Compiled with xelatex and ctex,
    so it is slower than Text; use it only when math sits inside the sentence."""
    return TexText(text, font_size=font_size, template="basic_ctex",
                   additional_preamble=Rf"\setCJKmainfont{{{FONT}}}", **kwargs)


def choose_local_text(chinese: str, english: str) -> str:
    """A default word shown on screen, in the episode's language (Chinese for zh*, English otherwise)."""
    from .context import get_scene_context

    return chinese if get_scene_context().language_code.lower().startswith("zh") else english
