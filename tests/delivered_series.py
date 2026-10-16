"""A small series whose first episode is rendered, with its cards, and ready to deliver, for the deliver, feedback
and page tests.

The render is fake but consistent: a 12.5 s test-pattern MP4 with a tone, made with ffmpeg, and the timeline,
subtitles, script and script audience review that match it.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from explainer_studio.paths import Series
from explainer_studio.schemas.script import compute_narration_digest

PLAN = """\
title: 線性代數入門   # the series title
sources:
  - sources/notes.pdf
language_code: zh-TW
narration_budget_usd: 5   # the user's budget

narration:
  provider_name: openai
  voice: ash

audience:
  description: |
    剛學過高中數學、想重新理解線性代數的大學生。

    他們會算矩陣乘法，但不知道為什麼要這樣算。
  unfamiliar_terms: [向量, 線性變換]
  misconceptions:
    - id: arrows_are_positions
      belief: 向量就是一個點的位置。
      evidence: 使用者在試讀時這樣回答。

goal: 能用幾何直覺理解向量運算與線性變換。

rationale: |
  先建立加法的幾何意義，第二集才能把矩陣解釋成變換。

episodes:
  - id: ep01
    title: 為什麼向量可以相加？
    question: 兩個箭頭相加，如何表示連續兩次移動？
    question_type: mechanism
    presenter_name: theo
    estimated_duration_seconds: 300
    source_scope: 講義第 2 章。
    taught_terms: [向量加法, 首尾相接]
    takeaway: 向量相加就是把兩次移動接起來。
    outline:
      - 從地圖上的兩次移動開始。
      - 把移動表示成箭頭。
  - id: ep02
    title: 矩陣如何改變空間？
    question: 一個矩陣怎麼把整個平面搬到新的位置？
    question_type: mechanism
    presenter_name: clio
    estimated_duration_seconds: 360
    taught_terms: [線性變換]
    takeaway: 矩陣記下了兩個基底向量去了哪裡。
    outline:
      - 看基底向量去了哪裡。

excluded_topics:
  - topic: 向量空間的形式公理
    reason: 這個系列先建立幾何直覺。
"""

SCRIPT = {
    "scenes": [
        {"id": "hook", "purpose": "從地圖上的兩次移動開始。", "beats": [
            {"id": "two_moves", "narration_text": "先往東走三步，再往北走兩步。", "visual": "地圖上兩段箭頭。"},
            {"id": "one_arrow", "narration_text": "兩次移動合起來，等於一支斜的箭頭。",
             "visual": "斜箭頭從起點連到終點。", "pause_duration_seconds": 1},
        ]},
        {"id": "tip_to_tail", "purpose": "把移動表示成首尾相接的箭頭。", "beats": [
            {"id": "tail", "narration_text": "第二支箭頭的尾巴，接在第一支的頭上。", "visual": "第二支箭頭平移過去。"},
            {"id": "sum", "narration_text": "這就是向量加法。", "visual": "標上 a + b。"},
        ]},
    ],
}
# (beat id, start, end) in video time; the cover holds the first second
BEATS = [("two_moves", 1.0, 4.0), ("one_arrow", 4.0, 7.0), ("tail", 7.0, 10.0), ("sum", 10.0, 12.0)]
DURATION_SECONDS = 12.5


def _format_srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    return (f"{milliseconds // 3_600_000:02d}:{milliseconds // 60_000 % 60:02d}:{milliseconds // 1000 % 60:02d},"
            f"{milliseconds % 1000:03d}")


def _build_timeline(script: dict) -> dict:
    narration_text_by_beat_id_map = {beat["id"]: beat["narration_text"] for scene in script["scenes"]
                                     for beat in scene["beats"]}
    scenes = []
    for scene in script["scenes"]:
        scene_beat_ids = {beat["id"] for beat in scene["beats"]}
        beats = [{"beat_id": beat_id, "start_seconds": start_seconds,
                  "duration_seconds": round(end_seconds - start_seconds, 3)}
                 for beat_id, start_seconds, end_seconds in BEATS if beat_id in scene_beat_ids]
        scenes.append({"scene_id": scene["id"], "start_seconds": beats[0]["start_seconds"],
                       "duration_seconds": round(sum(beat["duration_seconds"] for beat in beats), 3),
                       "beats": beats})
    narration_digest = compute_narration_digest([narration_text_by_beat_id_map[beat_id] for beat_id, _, _ in BEATS])
    return {"narration_digest": narration_digest,
            "duration_seconds": DURATION_SECONDS, "scenes": scenes, "sounds": []}


def write_delivery_record(series: Series, delivered_at: datetime, script: dict = SCRIPT,
                          episode_id: str = "ep01") -> Path:
    """A delivery record as deliver keeps it, without a render or a video at the series root."""
    import yaml

    from explainer_studio.deliver import format_delivery_record_dir_name

    delivery_records_dir_path = series.get_episode_paths(episode_id).delivery_records_dir_path
    record_dir_path = delivery_records_dir_path / format_delivery_record_dir_name(delivered_at)
    record_dir_path.mkdir(parents=True)
    (record_dir_path / "script.yaml").write_text(yaml.safe_dump(script, allow_unicode=True, sort_keys=False),
                                                 encoding="utf-8")
    (record_dir_path / "timeline.json").write_text(json.dumps(_build_timeline(script), ensure_ascii=False),
                                                   encoding="utf-8")
    (record_dir_path / "metadata.json").write_text(json.dumps({
        "delivered_at": delivered_at.isoformat(), "explainer_studio_version": "0.1.0",
        "files": {"video_file_name": "01-v.mp4", "cover_file_name": "01-v.png",
                  "subtitles": [{"language_code": "zh-TW", "file_name": "01-v.zh-TW.srt"}]}}),
        encoding="utf-8")
    return record_dir_path


def write_render(series: Series, episode_id: str = "ep01", tone_hertz: int = 440) -> None:
    """A fresh render/ for the episode, matching its current script."""
    import yaml

    episode_paths = series.get_episode_paths(episode_id)
    script = yaml.safe_load(episode_paths.script_file_path.read_text(encoding="utf-8"))
    narration_text_by_beat_id_map = {beat["id"]: beat["narration_text"] for scene in script["scenes"]
                                     for beat in scene["beats"]}
    render_dir_path = episode_paths.render_dir_path
    render_dir_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"testsrc2=size=640x360:rate=25:duration={DURATION_SECONDS}",
                    "-f", "lavfi", "-i", f"sine=frequency={tone_hertz}:duration={DURATION_SECONDS}", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart",
                    str(render_dir_path / "video.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", str(render_dir_path / "video.mp4"),
                    "-frames:v", "1", str(render_dir_path / "cover.png")], check=True)
    cues = [f"{number}\n{_format_srt_time(start_seconds)} --> {_format_srt_time(end_seconds)}\n"
            f"{narration_text_by_beat_id_map[beat_id]}\n"
            for number, (beat_id, start_seconds, end_seconds) in enumerate(BEATS, start=1)]
    (render_dir_path / "subtitles.srt").write_text("\n".join(cues), encoding="utf-8")
    (render_dir_path / "timeline.json").write_text(json.dumps(_build_timeline(script), ensure_ascii=False),
                                                   encoding="utf-8")
    (render_dir_path / "automatic-checks.json").write_text('{"issues": []}', encoding="utf-8")


def write_script_review(series: Series, episode_id: str = "ep01") -> None:
    episode_paths = series.get_episode_paths(episode_id)
    episode_paths.audience_reviews_dir_path.mkdir(parents=True, exist_ok=True)
    episode_paths.script_reviews_file_path.write_text(
        "rounds:\n"
        "  - scene_ids: [hook, tip_to_tail]\n"
        "    findings: []\n", encoding="utf-8")


# cards that fit the render: deliver checks them
NOTES = {
    "parts": [{"title": "兩次移動等於一支箭頭", "segments": ["hook"]},
              {"title": "首尾相接就是加法", "segments": ["tip_to_tail"]}],
    "segments": {
        "hook": {"title": "兩次移動", "summary": "往東三步再往北兩步，合起來是一支斜箭頭。", "key_frame": "one_arrow",
                 "cards": [{"id": "moves_add", "title": "兩次移動合起來，等於從起點直接走到終點。",
                            "points": ["往東三步再往北兩步，==終點只跟兩次移動有關==。",
                                       {"text": "合起來的移動是一支斜箭頭。", "frame": "one_arrow",
                                        "caption": "斜的箭頭連起點和終點"}],
                            "leads_to": ["tip_to_tail"]}]},
        "tip_to_tail": {"title": "首尾相接", "summary": "第二支箭頭的尾巴接上第一支的頭。", "key_frame": "sum",
                        "cards": [{"id": "tip_to_tail", "title": "**向量加法**就是把箭頭首尾相接。", "color": "green",
                                   "points": [{"text": "畫法有兩步：", "points": ["尾巴接頭", "從第一支的尾畫到第二支的頭"]}]}]},
    },
}


def write_notes(series: Series, notes: dict = NOTES, episode_id: str = "ep01") -> None:
    import yaml

    series.get_episode_paths(episode_id).notes_file_path.write_text(yaml.safe_dump(notes, allow_unicode=True),
                                                                    encoding="utf-8")


def create_series(root: Path, should_render: bool = True) -> Series:
    """The series at `root`, with ep01 written, reviewed and (unless `should_render` is False) rendered."""
    import yaml

    production_dir_path = root / "production"
    production_dir_path.mkdir(parents=True)
    (production_dir_path / "plan.yaml").write_text(PLAN, encoding="utf-8")
    series = Series.find(root)
    episode_paths = series.get_episode_paths("ep01")
    episode_paths.root_dir_path.mkdir(parents=True)
    episode_paths.script_file_path.write_text(yaml.safe_dump(SCRIPT, allow_unicode=True, sort_keys=False),
                                              encoding="utf-8")
    if should_render:
        write_render(series)
        write_script_review(series)
        write_notes(series)
    return series
