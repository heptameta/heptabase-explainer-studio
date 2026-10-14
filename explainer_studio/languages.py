"""What the tools need to know about a narration language.

One table drives the length warnings in `script validate`, the time estimate for beats without narration in
`preview`, the cost estimate in `narrate`, and the rewrite from a beat's narration text to the spoken text a voice
provider reads.
Languages are looked up by prefix: zh-TW and zh-Hant use "zh", en-US uses "en". Any other language works with the
English counting rules and no rewrite. `format_language_name` gives the English name of any language code, for prompts.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .narration_providers import NarrationProviderName


@dataclass(frozen=True)
class Language:
    code: str
    is_counted_in_characters: bool  # Chinese is counted in characters, English in words
    max_units_per_beat: int
    max_units_per_episode: int
    units_per_minute: int  # typical speaking rate of a paid voice
    # measured rates that differ from the default
    units_per_minute_by_provider_name_map: dict[NarrationProviderName, int] = field(default_factory=dict)
    known_misreadings: tuple[tuple[str, str], ...] = ()  # (pattern, what goes wrong and how to rewrite it)

    @property
    def unit(self) -> str:
        return "characters" if self.is_counted_in_characters else "words"

    def count_units(self, text: str) -> int:
        if self.is_counted_in_characters:
            return len(re.sub(r"[\s\W_]+", "", text))
        return len(re.findall(r"[\w'’-]+", text))

    def resolve_units_per_minute(self, provider_name: NarrationProviderName | None = None) -> int:
        return self.units_per_minute_by_provider_name_map.get(provider_name, self.units_per_minute)

    def estimate_speech_seconds(self, text: str, provider_name: NarrationProviderName | None = None) -> float:
        return max(1.0, self.count_units(text) / self.resolve_units_per_minute(provider_name) * 60)


LANGUAGE_BY_CODE_MAP = {
    "zh": Language(
        "zh", True, max_units_per_beat=60, max_units_per_episode=7200, units_per_minute=300,
        units_per_minute_by_provider_name_map={"voai": 312, "macos-say": 250},
        known_misreadings=(
            (r"多種(?=的|出|了|一)",
             ("「種」in 多種的 (to plant) is read as 種類: rewrite as 多收的, or set `spoken_text_override` with a "
              "homophone (多眾的)")),
            (r"(?<![數份能重質容總流變向產大少適音力雨熱電劑測丈衡打估])量(?=的是|出|到|一下|看看|得)",
             ("the verb 量 (to measure) is read as the noun 量 (amount): rewrite as 測的是 or 代表, or set "
              "`spoken_text_override` with a homophone (良)")),
        ),
    ),
    "en": Language("en", False, max_units_per_beat=32, max_units_per_episode=3400, units_per_minute=165,
                   units_per_minute_by_provider_name_map={"openai": 170, "macos-say": 175}),
}


def resolve_language(language_code: str | None) -> Language:
    return LANGUAGE_BY_CODE_MAP.get((language_code or "en").split("-")[0].lower(), LANGUAGE_BY_CODE_MAP["en"])


# English names, by language tag and then by its first part
LANGUAGE_NAME_BY_CODE_MAP = {
    "zh-tw": "Traditional Chinese", "zh-hant": "Traditional Chinese", "zh-hans": "Simplified Chinese",
    "zh-cn": "Simplified Chinese", "zh": "Chinese", "en": "English", "ja": "Japanese", "ko": "Korean",
    "fr": "French", "de": "German", "es": "Spanish", "pt": "Portuguese", "it": "Italian",
}


def format_language_name(language_code: str) -> str:
    lowered = language_code.lower()
    english_name = (LANGUAGE_NAME_BY_CODE_MAP.get(lowered)
                    or LANGUAGE_NAME_BY_CODE_MAP.get(lowered.split("-")[0]))
    return f"{english_name} ({language_code})" if english_name else f"the language with code {language_code}"


def find_misreading_warnings(language_code: str, beat_texts: list[tuple[str, str]]) -> list[str]:
    language = resolve_language(language_code)
    return [f"beat {beat_id}: {why}" for beat_id, text in beat_texts for pattern, why in language.known_misreadings
            if re.search(pattern, text)]


# Narration text -> the spoken text a voice provider reads -------------------------------------------------------
CHINESE_DIGITS = "〇一二三四五六七八九"

# Paid voices drop symbols they cannot read: σ, μ and σ² came out as silence. Taiwanese classrooms read Greek
# letters by their English names.
GREEK_LETTER_TO_NAME_MAP = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "ϵ": "epsilon", "ζ": "zeta",
    "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi",
    "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon", "φ": "phi", "ϕ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega", "Γ": "gamma", "Δ": "delta", "Θ": "theta", "Λ": "lambda", "Π": "pi", "Σ": "sigma",
    "Φ": "phi", "Ψ": "psi", "Ω": "omega", "ℵ": "aleph",
}
SUPERSCRIPT_TO_CHINESE_WORD_MAP = {"²": "平方", "³": "立方"}
SUPERSCRIPT_TO_ENGLISH_WORD_MAP = {"²": " squared", "³": " cubed"}


def _check_does_need_space(neighbor: str) -> bool:
    return bool(neighbor) and not neighbor.isspace() and not unicodedata.category(neighbor).startswith("P")


def _convert_symbol_to_chinese_word(match: re.Match, text: str) -> str:
    symbol = match.group()
    word = GREEK_LETTER_TO_NAME_MAP.get(symbol) or SUPERSCRIPT_TO_CHINESE_WORD_MAP.get(symbol) or "減"
    before, after = text[match.start() - 1:match.start()], text[match.end():match.end() + 1]
    space_before = " " if _check_does_need_space(before) else ""
    space_after = " " if _check_does_need_space(after) and symbol not in SUPERSCRIPT_TO_CHINESE_WORD_MAP else ""
    return space_before + word + space_after


def convert_narration_text_to_spoken_text(text: str, language_code: str | None) -> str:
    """What the voice reads for a beat's narration text. Only symbols and punctuation change; the words stay."""
    base_language_code = resolve_language(language_code).code
    result = text
    if base_language_code == "zh":
        # standalone years are read digit by digit in Taiwan: 1872 年 -> 一八七二年
        result = re.sub(r"(?<![\d,.])\s*(1[5-9]\d\d|20\d\d)(?![\d,.])\s*",
                        lambda match: "".join(CHINESE_DIGITS[int(digit)] for digit in match.group(1)), result)
        result = result.replace("——", "，").replace("—", "，").replace("……", "，").replace("…", "，")
        # a minus sign before a number is 負 (−9), anywhere else 減 (x − μ)
        result = re.sub(r"(?:^|(?<=[\s、，,（(：:=]))−\s*(?=\d)", "負", result)
        source = result
        result = re.sub("[−" + "".join(GREEK_LETTER_TO_NAME_MAP) + "".join(SUPERSCRIPT_TO_CHINESE_WORD_MAP) + "]",
                        lambda match: _convert_symbol_to_chinese_word(match, source), source)
        result = re.sub(r"[「」『』《》]", "", result)
    else:
        result = re.sub("[" + "".join(SUPERSCRIPT_TO_ENGLISH_WORD_MAP) + "]",
                        lambda match: SUPERSCRIPT_TO_ENGLISH_WORD_MAP[match.group()], result)
        result = re.sub("[" + "".join(GREEK_LETTER_TO_NAME_MAP) + "]",
                        lambda match: f" {GREEK_LETTER_TO_NAME_MAP[match.group()]} ", result)
        result = re.sub(r"(?:^|(?<=[\s(]))−\s*(?=\d)", "minus ", result)
        result = result.replace("−", " minus ")
    return re.sub(r"\s+", " ", result).strip()
