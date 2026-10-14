"""Loading and checking episodes/<episode>/script.yaml."""

from __future__ import annotations

from . import languages
from .file_io import load_yaml_model
from .narration_providers import NarrationProviderName
from .paths import Series
from .plan import load_plan
from .schemas.script import Beat, Script

# A short estimate usually means reasoning steps were squeezed into single beats.
MIN_ESTIMATE_TO_PLAN_RATIO = 0.8
SCENE_TRANSITION_SECONDS = 1.0
DEFAULT_PAUSE_DURATION_SECONDS = 0.3


def load_script(series: Series, episode_id: str) -> Script:
    load_plan(series).find_episode(episode_id)
    return load_yaml_model(Script, series.get_episode_paths(episode_id).script_file_path, f"{episode_id}/script.yaml")


def resolve_pause_duration_seconds(beat: Beat) -> float:
    """The silence after a beat's line: its pause_duration_seconds, or the default."""
    return beat.pause_duration_seconds if beat.pause_duration_seconds is not None else DEFAULT_PAUSE_DURATION_SECONDS


def estimate_episode_duration_seconds(script: Script, language_code: str,
                                      provider_name: NarrationProviderName | None = None) -> float:
    language = languages.resolve_language(language_code)
    total_seconds = 1.0  # the cover
    for scene in script.scenes:
        total_seconds += SCENE_TRANSITION_SECONDS
        for beat in scene.beats:
            total_seconds += language.estimate_speech_seconds(beat.narration_text, provider_name)
            total_seconds += resolve_pause_duration_seconds(beat)
    return total_seconds


def find_script_warnings(series: Series, episode_id: str, script: Script) -> list[str]:
    plan = load_plan(series)
    episode = plan.find_episode(episode_id)
    language_code = plan.resolve_episode_language_code(episode_id)
    language = languages.resolve_language(language_code)
    narration_settings = plan.resolve_episode_narration_settings(episode_id)
    warnings = []
    for beat in script.list_beats():
        unit_count = language.count_units(beat.narration_text)
        if unit_count > language.max_units_per_beat:
            warnings.append(f"beat {beat.id}: {unit_count} {language.unit}, over the {language.max_units_per_beat} a "
                            "viewer can follow in one line; split it")
    episode_unit_count = sum(language.count_units(beat.narration_text) for beat in script.list_beats())
    if episode_unit_count > language.max_units_per_episode:
        warnings.append(f"the episode has {episode_unit_count} {language.unit} of narration, over the "
                        f"{language.max_units_per_episode} an episode can carry")
    provider_name = narration_settings.provider_name if narration_settings else None
    estimated_seconds = estimate_episode_duration_seconds(script, language_code, provider_name)
    if estimated_seconds < episode.estimated_duration_seconds * MIN_ESTIMATE_TO_PLAN_RATIO:
        warnings.append(f"the episode will run about {estimated_seconds / 60:.1f} min, under 80% of the planned "
                        f"{episode.estimated_duration_seconds / 60:.1f} min; reasoning steps may be squeezed into "
                        "single beats")
    warnings += languages.find_misreading_warnings(language_code,
                                                   [(beat.id, beat.spoken_text_override or beat.narration_text)
                                                    for beat in script.list_beats()])
    return warnings
