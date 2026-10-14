from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from delivered_series import SCRIPT, create_series

from explainer_studio.audience_review import prepare_audience_review_prompt
from explainer_studio.errors import StudioError


def test_script_prompt_gives_the_reviewer_the_viewer_and_the_series_so_far_but_not_the_answer(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    series.plan_file_path.write_text(series.plan_file_path.read_text(encoding="utf-8").replace("taught_terms: [線性變換]",
                                                                           "taught_terms: [基底變換]"), encoding="utf-8")
    episode_paths = series.get_episode_paths("ep02")
    episode_paths.root_dir_path.mkdir(parents=True)
    episode_paths.script_file_path.write_text(yaml.safe_dump(SCRIPT, allow_unicode=True), encoding="utf-8")

    path, header = prepare_audience_review_prompt(series, "ep02", ["tip_to_tail"])
    prompt = path.read_text(encoding="utf-8")

    assert not path.is_relative_to(series.root_dir_path)
    assert "剛學過高中數學" in prompt and "向量, 線性變換" in prompt and "向量就是一個點的位置" in prompt
    assert "兩個箭頭相加，如何表示連續兩次移動？" in prompt and "向量相加就是把兩次移動接起來" in prompt
    assert "向量加法, 首尾相接" in prompt  # what ep01 taught
    assert "一個矩陣怎麼把整個平面搬到新的位置？" in prompt and "Every link of the causal chain" in prompt
    assert "Kind of question: Mechanism (" in prompt  # the question type's display name, not its name
    assert "矩陣記下了兩個基底向量去了哪裡" not in prompt and "基底變換" not in prompt  # ep02's own answer
    assert "### Scene `tip_to_tail` (READ)" in prompt and "### Scene `hook` (CONTEXT ONLY)" in prompt
    assert "Traditional Chinese" in prompt
    assert header == "rounds:\n  - scene_ids: [tip_to_tail]"


def test_script_prompt_refuses_an_unknown_scene(tmp_path: Path) -> None:
    series = create_series(tmp_path / "series", should_render=False)
    with pytest.raises(StudioError, match="no scene"):
        prepare_audience_review_prompt(series, "ep01", ["missing"])
