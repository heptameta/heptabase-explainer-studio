"""Narration for the render fixture made directly with macOS `say` (no narrate gate, no provider code), so render
tests can run without the audience review records a real `narrate` needs."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from explainer_studio.file_io import write_yaml
from explainer_studio.narrate import measure_wav_duration_seconds, resolve_spoken_text
from explainer_studio.paths import Series
from explainer_studio.plan import load_plan
from explainer_studio.script import load_script

VOICE_BY_LANGUAGE_CODE_MAP = {"zh": "Meijia", "en": "Samantha"}


def check_is_say_available() -> bool:
    return shutil.which("say") is not None and shutil.which("ffmpeg") is not None


def write_say_narration(series: Series, episode_id: str) -> None:
    plan = load_plan(series)
    script = load_script(series, episode_id)
    language_code = plan.resolve_episode_language_code(episode_id)
    voice = VOICE_BY_LANGUAGE_CODE_MAP.get(language_code.split("-")[0], "Samantha")
    episode_paths = series.get_episode_paths(episode_id)
    episode_paths.narration_dir_path.mkdir(parents=True, exist_ok=True)
    narrated_beats = []
    with tempfile.TemporaryDirectory() as temporary_dir_path:
        for beat in script.list_beats():
            spoken_text = resolve_spoken_text(beat, language_code)
            aiff_file_path = Path(temporary_dir_path) / f"{beat.id}.aiff"
            subprocess.run(["say", "-v", voice, "-o", str(aiff_file_path), spoken_text], check=True)
            wav_file_path = episode_paths.get_narration_audio_file_path(beat.id)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(aiff_file_path), "-ac", "1", "-ar", "48000",
                            "-c:a", "pcm_s16le", str(wav_file_path)], check=True)
            narrated_beats.append({"beat_id": beat.id, "spoken_text": spoken_text,
                                   "duration_seconds": round(measure_wav_duration_seconds(wav_file_path), 3)})
    narration_settings = plan.resolve_episode_narration_settings(episode_id)
    write_yaml(episode_paths.narration_record_file_path,
               {"settings": narration_settings.model_dump(mode="json", exclude_unset=True, exclude_none=True),
                "beats": narrated_beats})
