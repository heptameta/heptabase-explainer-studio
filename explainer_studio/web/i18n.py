"""Page text in the user's language (the plan's `user_language_code`, else its `language_code`):
`locales/<language_code>.json` and `translate()`.

zh-TW and zh-Hant (any case, any suffix) read Traditional Chinese, everything else English. Both locale files carry
the same keys; `{name}` placeholders are filled by `translate()` here and in the pages' JS.
"""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path

LOCALES_DIR_PATH = Path(__file__).resolve().parent / "locales"
PAGE_LANGUAGE_CODES = ("en", "zh-TW")


def resolve_page_language_code(language_code: str | None) -> str:
    lowered = (language_code or "").lower()
    return "zh-TW" if lowered.startswith(("zh-tw", "zh-hant")) else "en"


@functools.cache
def read_locale_strings(language_code: str) -> dict[str, str]:
    return json.loads((LOCALES_DIR_PATH / f"{language_code}.json").read_text(encoding="utf-8"))


def translate(language_code: str, key: str, **params: object) -> str:
    text = read_locale_strings(language_code).get(key, key)
    return re.sub(r"\{(\w+)\}", lambda match: str(params.get(match.group(1), match.group(0))), text)
