from __future__ import annotations

import json
import re

from explainer_studio.web.i18n import LOCALES_DIR_PATH, PAGE_LANGUAGE_CODES, resolve_page_language_code


def test_every_locale_has_the_same_keys_and_placeholders() -> None:
    strings_by_language_code_map = {
        language_code: json.loads((LOCALES_DIR_PATH / f"{language_code}.json").read_text(encoding="utf-8"))
        for language_code in PAGE_LANGUAGE_CODES}
    english_strings = strings_by_language_code_map["en"]
    for language_code, strings in strings_by_language_code_map.items():
        assert strings.keys() == english_strings.keys(), language_code
        for key, text in strings.items():
            assert (set(re.findall(r"\{(\w+)\}", text))
                    == set(re.findall(r"\{(\w+)\}", english_strings[key]))), (language_code, key)


def test_page_language_code_follows_the_plan_language() -> None:
    assert [resolve_page_language_code(code) for code in ("zh-TW", "zh-Hant-HK", "zh-tw", "zh-CN", "ja", None)] == \
        ["zh-TW", "zh-TW", "zh-TW", "en", "en", "en"]


def test_the_pages_speak_the_users_language_when_it_differs_from_the_videos(tmp_path) -> None:
    from delivered_series import create_series

    from explainer_studio.web.pages import compute_plan_page, read_page_language_code

    series = create_series(tmp_path / "series", should_render=False)
    assert read_page_language_code(series) == "zh-TW"  # no user language: the videos' language
    text = series.plan_file_path.read_text(encoding="utf-8")
    text = text.replace("language_code: zh-TW\n", "language_code: zh-TW\nuser_language_code: en\n", 1)
    series.plan_file_path.write_text(text, encoding="utf-8")
    assert read_page_language_code(series) == "en"  # the video page reads it too
    assert compute_plan_page(series)["languageCode"] == "en"
