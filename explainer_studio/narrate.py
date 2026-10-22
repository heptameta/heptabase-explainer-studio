"""Narration: synthesize the beats whose spoken text or voice changed, record them, and keep the budget.

A beat counts as narrated when `narration.yaml` has it with the current spoken text (the beat's `spoken_text_override`,
or the language rewrite of its narration text), the record's settings equal the episode's narration settings, and its
audio file exists. Editing the narration text without changing the spoken text keeps the audio. `narrate` uses this to
decide what to reuse; `render` uses it to refuse an episode with missing or outdated narration.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import tempfile
import wave
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from filelock import FileLock, Timeout

from . import languages, narration_providers, user_dirs
from .audience_review import require_script_review
from .credentials import find_api_key
from .environment import ProgressReporter
from .errors import StudioError
from .file_io import hold_lock, load_yaml_model, write_yaml
from .narration_providers import NarrationProviderName
from .narration_providers.base import SynthesisError
from .paths import Series
from .plan import load_plan
from .schemas.narration import NarratedBeat, NarrationRecord
from .schemas.plan import NarrationSettings, Plan
from .schemas.script import Beat, Script
from .script import load_script
from .spending import format_usd, record_spending, require_within_budget

SAMPLE_RATE_HERTZ = 48000
# speech-rate outliers: shorter than this, or faster/slower than these multiples of the episode's typical rate
MIN_BEAT_SECONDS = 0.4
MAX_RATE_TO_TYPICAL_RATIO = 1.8
MIN_RATE_TO_TYPICAL_RATIO = 0.45


def resolve_spoken_text(beat: Beat, language_code: str) -> str:
    """The text sent to the voice: the beat's override, or the language rewrite of its narration text."""
    if beat.spoken_text_override:
        return beat.spoken_text_override.strip()
    return languages.convert_narration_text_to_spoken_text(beat.narration_text.strip(), language_code)


def load_narration_record(series: Series, episode_id: str) -> NarrationRecord | None:
    record_file_path = series.get_episode_paths(episode_id).narration_record_file_path
    if not record_file_path.exists():
        return None
    return load_yaml_model(NarrationRecord, record_file_path, f"{episode_id}/narration/narration.yaml")


def find_beat_ids_needing_narration(series: Series, plan: Plan, episode_id: str, script: Script) -> list[str]:
    """Beat ids whose audio is missing or was made from different spoken text or settings, in script order."""
    record = load_narration_record(series, episode_id)
    narration_settings = plan.resolve_episode_narration_settings(episode_id)
    language_code = plan.resolve_episode_language_code(episode_id)
    episode_paths = series.get_episode_paths(episode_id)
    stale_beat_ids = []
    for beat in script.list_beats():
        made = record.find_narrated_beat(beat.id) if record is not None else None
        is_current = (made is not None and record.settings == narration_settings
                      and made.spoken_text == resolve_spoken_text(beat, language_code)
                      and episode_paths.get_narration_audio_file_path(beat.id).exists())
        if not is_current:
            stale_beat_ids.append(beat.id)
    return stale_beat_ids


# The narrate command -------------------------------------------------------------------------------------------------
@dataclass
class NarrationRun:
    episode_id: str
    provider_name: NarrationProviderName
    reused_beat_ids: list[str] = field(default_factory=list)
    made_beat_ids: list[str] = field(default_factory=list)
    failure_by_beat_id_map: dict[str, str] = field(default_factory=dict)  # why each failed beat failed
    removed_beat_ids: list[str] = field(default_factory=list)  # audio of beats the script no longer has
    cost_usd: float = 0.0
    is_cost_estimated: bool = False
    warnings: list[str] = field(default_factory=list)  # speech-rate outliers


def narrate(series: Series, episode_id: str, forced_beat_ids: list[str] | None = None,
            report_progress: ProgressReporter = lambda message: None) -> NarrationRun:
    """Synthesize the beats that need it (plus `forced_beat_ids`), keeping each beat's progress on disk as it lands."""
    narration_settings = load_plan(series).resolve_episode_narration_settings(episode_id)
    if narration_settings is None or not narration_providers.get_provider(narration_settings.provider_name).is_paid:
        return _make_narration(series, episode_id, forced_beat_ids, report_progress)
    # the plan and the script are read once the lock is held, so a run that waited pays for their latest text
    with _hold_paid_narration_lock(series, report_progress):
        return _make_narration(series, episode_id, forced_beat_ids, report_progress)


@contextlib.contextmanager
def _hold_paid_narration_lock(series: Series, report_progress: ProgressReporter) -> Iterator[None]:
    """One paid narrate run per series at a time, from reading the script to the last paid call: a run checks the
    budget against everything earlier runs spent, and two runs of an episode never pay for the same beat. The lock
    goes with the process, also when it is killed."""
    lock = FileLock(str(series.paid_narration_lock_file_path))
    try:
        lock.acquire(timeout=0)
    except Timeout:
        report_progress("waiting for another narrate run in this series, which pays for its narration, to finish")
        lock.acquire()
    try:
        yield
    finally:
        lock.release()


def _make_narration(series: Series, episode_id: str, forced_beat_ids: list[str] | None,
                    report_progress: ProgressReporter) -> NarrationRun:
    plan = load_plan(series)
    script = load_script(series, episode_id)
    narration_settings = plan.resolve_episode_narration_settings(episode_id)
    if narration_settings is None:
        raise StudioError(f"{episode_id} has no narration settings",
                          "plan.yaml sets no `narration` (series level, or episodes[].narration for this episode)",
                          "add a narration block to production/plan.yaml, for example `narration: {provider_name: "
                          "openai, voice: ash}` (providers: elevenlabs, openai, voai, macos-say)")
    provider = narration_providers.get_provider(narration_settings.provider_name)
    provider.require_available()
    require_script_review(series, episode_id, script)
    beats = script.list_beats()
    current_beat_ids = {beat.id for beat in beats}
    forced_beat_ids = list(dict.fromkeys(forced_beat_ids or []))
    unknown_beat_ids = [beat_id for beat_id in forced_beat_ids if beat_id not in current_beat_ids]
    if unknown_beat_ids:
        raise StudioError(f"--beats names beats that are not in {episode_id}/script.yaml", ", ".join(unknown_beat_ids),
                          "use beat ids from the script")
    language_code = plan.resolve_episode_language_code(episode_id)
    stale_beat_ids = set(find_beat_ids_needing_narration(series, plan, episode_id, script)) | set(forced_beat_ids)
    beats_to_make = [beat for beat in beats if beat.id in stale_beat_ids]
    run = NarrationRun(episode_id, provider.name,
                       reused_beat_ids=[beat.id for beat in beats if beat.id not in stale_beat_ids])
    api_key = None
    if provider.api_key_env and beats_to_make:
        found = find_api_key(provider.name)
        if found is None:
            raise StudioError(f"no {provider.name} API key",
                              f"plan.yaml narration uses {provider.name}, and neither {provider.api_key_env} nor "
                              "credentials.toml has a key",
                              f"ask the user to run `explainer-studio setup narration {provider.name}` in their own "
                              "terminal (the agent never handles the key), then run narrate again")
        api_key = found.value

    if provider.is_paid:
        estimated_cost_usd = sum(provider.estimate_cost_usd(resolve_spoken_text(beat, language_code),
                                                            narration_settings) for beat in beats_to_make)
        require_within_budget(series, plan, estimated_cost_usd)
    ffmpeg_path = user_dirs.find_tool("ffmpeg")
    if beats_to_make and ffmpeg_path is None:
        raise StudioError("ffmpeg is not installed", "narrate converts every voice to 48 kHz WAV with ffmpeg",
                          "run `explainer-studio setup`")

    episode_paths = series.get_episode_paths(episode_id)
    episode_paths.narration_dir_path.mkdir(parents=True, exist_ok=True)
    record = load_narration_record(series, episode_id)
    is_same_voice = record is None or record.settings == narration_settings
    narrated_beat_by_beat_id_map = ({narrated_beat.beat_id: narrated_beat for narrated_beat in record.beats
                                     if narrated_beat.beat_id in current_beat_ids}
                                    if record is not None and is_same_voice else {})
    for audio_file_path in sorted(episode_paths.narration_dir_path.glob("*.wav")):
        if audio_file_path.stem not in current_beat_ids and not audio_file_path.name.startswith("."):
            audio_file_path.unlink()
            run.removed_beat_ids.append(audio_file_path.stem)
    is_record_switched = False

    def switch_record() -> None:
        # With another voice, the old record keeps describing the old audio until a new-voice file is about to
        # replace an old one (or the run finishes): a run that stops before then leaves the old narration usable, and
        # one interrupted after it never passes old-voice audio off as current.
        nonlocal is_record_switched
        if not is_record_switched:
            _write_narration_record(series, episode_id, narration_settings, narrated_beat_by_beat_id_map, beats)
            is_record_switched = True

    if is_same_voice:
        switch_record()  # drops the entries of removed beats now

    spoken_texts = [resolve_spoken_text(beat, language_code) for beat in beats]
    beat_index_by_beat_id_map = {beat.id: beat_index for beat_index, beat in enumerate(beats)}
    for beat_number, beat in enumerate(beats_to_make, start=1):
        beat_index = beat_index_by_beat_id_map[beat.id]
        spoken_text = spoken_texts[beat_index]
        # the neighbors in the script, whether or not they are redone in this run
        previous_spoken_text = spoken_texts[beat_index - 1] if beat_index > 0 else None
        next_spoken_text = spoken_texts[beat_index + 1] if beat_index + 1 < len(beats) else None
        report_progress(f"[{beat_number}/{len(beats_to_make)}] {beat.id}: {len(spoken_text)} characters")
        try:
            duration_seconds = _make_beat_audio(series, episode_id, provider, narration_settings, beat.id, spoken_text,
                                                previous_spoken_text, next_spoken_text, api_key, language_code,
                                                ffmpeg_path, run, switch_record)
        except SynthesisError as error:
            failure = str(error)
            if error.was_possibly_charged and provider.is_paid:
                # counted as spent, so the budget never leaves out a charge the service may have made
                cost_usd = provider.estimate_cost_usd(spoken_text, narration_settings)
                record_spending(series, episode_id, provider.name, len(spoken_text), cost_usd, is_estimated=True)
                run.cost_usd += cost_usd
                run.is_cost_estimated = True
                failure += f"; its estimated {format_usd(cost_usd)} is counted as spent"
            run.failure_by_beat_id_map[beat.id] = failure
            report_progress(f"  failed: {failure}")
            continue
        except StudioError as error:
            if not run.made_beat_ids:
                progress_note = "no beat was made"
            elif is_record_switched:
                progress_note = (f"made {len(run.made_beat_ids)} beat(s) before stopping; they are saved and will be "
                                 "reused")
            else:
                progress_note = (f"made {len(run.made_beat_ids)} beat(s) in the new voice before stopping; the "
                                 "previous narration stays in use until the new voice replaces it")
            raise StudioError(error.what, error.why, error.next_step, [*error.details, progress_note]) from None
        narrated_beat_by_beat_id_map[beat.id] = NarratedBeat(beat_id=beat.id, spoken_text=spoken_text,
                                                             duration_seconds=duration_seconds)
        if is_record_switched:
            _write_narration_record(series, episode_id, narration_settings, narrated_beat_by_beat_id_map, beats)
        run.made_beat_ids.append(beat.id)
    switch_record()
    run.warnings = find_speech_rate_warnings(narrated_beat_by_beat_id_map.values(), language_code, provider.name)
    return run


def _make_beat_audio(series: Series, episode_id: str, provider, narration_settings, beat_id: str, spoken_text: str,
                     previous_spoken_text: str | None, next_spoken_text: str | None, api_key: str | None,
                     language_code: str, ffmpeg_path: str | None, run: NarrationRun,
                     before_replacing: Callable[[], None]) -> float:
    """Synthesize one beat, convert it to 48 kHz mono 16-bit WAV and put it in place. Returns its duration."""
    audio_file_path = series.get_episode_paths(episode_id).get_narration_audio_file_path(beat_id)
    with tempfile.TemporaryDirectory(prefix="explainer-studio-narrate-") as temporary_dir_path:
        provider_audio_file_path = Path(temporary_dir_path) / "provider.wav"
        synthesis = provider.synthesize(spoken_text, narration_settings, provider_audio_file_path, api_key,
                                        language_code, previous_spoken_text, next_spoken_text)
        if provider.is_paid:
            record_spending(series, episode_id, provider.name, synthesis.character_count, synthesis.cost_usd,
                            synthesis.is_estimated)
        run.cost_usd += synthesis.cost_usd
        run.is_cost_estimated = run.is_cost_estimated or synthesis.is_estimated
        # convert next to the target so the final rename never crosses file systems
        file_descriptor, converted_name = tempfile.mkstemp(prefix=f".{beat_id}.", suffix=".wav",
                                                           dir=audio_file_path.parent)
        os.close(file_descriptor)
        converted_file_path = Path(converted_name)
        try:
            conversion = subprocess.run([ffmpeg_path, "-v", "error", "-y", "-i", str(provider_audio_file_path), "-ar",
                                         str(SAMPLE_RATE_HERTZ), "-ac", "1", "-c:a", "pcm_s16le",
                                         str(converted_file_path)],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                                        timeout=300, check=False)
            duration_seconds = measure_wav_duration_seconds(converted_file_path) if conversion.returncode == 0 else 0.0
            if duration_seconds <= 0:
                raise SynthesisError(f"could not convert the provider's audio: {conversion.stderr.strip()[-300:]}")
            if audio_file_path.exists():
                before_replacing()
            os.replace(converted_file_path, audio_file_path)
            os.chmod(audio_file_path, 0o644)
        finally:
            converted_file_path.unlink(missing_ok=True)
    return round(duration_seconds, 3)


def _write_narration_record(series: Series, episode_id: str, narration_settings: NarrationSettings,
                            narrated_beat_by_beat_id_map: dict[str, NarratedBeat], beats: list[Beat]) -> None:
    record_file_path = series.get_episode_paths(episode_id).narration_record_file_path
    ordered_narrated_beats = [narrated_beat_by_beat_id_map[beat.id] for beat in beats
                              if beat.id in narrated_beat_by_beat_id_map]
    record = NarrationRecord(settings=narration_settings, beats=ordered_narrated_beats)
    with hold_lock(record_file_path):
        # only the settings fields the plan wrote, so a release that adds a setting or changes a default leaves the
        # recorded settings equal to the plan's and charges for nothing
        write_yaml(record_file_path, record.model_dump(mode="json", exclude_unset=True, exclude_none=True))


def measure_wav_duration_seconds(wav_file_path: Path) -> float:
    try:
        with wave.open(str(wav_file_path), "rb") as handle:
            return handle.getnframes() / handle.getframerate()
    except (wave.Error, EOFError, OSError):
        return 0.0


def find_speech_rate_warnings(narrated_beats: Iterable[NarratedBeat], language_code: str,
                              provider_name: NarrationProviderName) -> list[str]:
    """Beats whose audio is implausibly short or long for their text: usually a voice that skipped or mangled words."""
    language = languages.resolve_language(language_code)
    unit_count_and_seconds_by_beat_id_map = {
        narrated_beat.beat_id: (language.count_units(narrated_beat.spoken_text), narrated_beat.duration_seconds)
        for narrated_beat in narrated_beats}
    speech_rates_units_per_second = sorted(unit_count / duration_seconds for unit_count, duration_seconds
                                           in unit_count_and_seconds_by_beat_id_map.values()
                                           if unit_count and duration_seconds > 0)
    if len(speech_rates_units_per_second) >= 3:
        typical_units_per_second = speech_rates_units_per_second[len(speech_rates_units_per_second) // 2]
    else:
        typical_units_per_second = language.resolve_units_per_minute(provider_name) / 60
    warnings = []
    for beat_id, (unit_count, duration_seconds) in unit_count_and_seconds_by_beat_id_map.items():
        units_per_second = unit_count / duration_seconds if duration_seconds > 0 else 0
        if duration_seconds < MIN_BEAT_SECONDS or (unit_count and (
                units_per_second > MAX_RATE_TO_TYPICAL_RATIO * typical_units_per_second
                or units_per_second < MIN_RATE_TO_TYPICAL_RATIO * typical_units_per_second)):
            warnings.append(f"beat {beat_id}: {duration_seconds:.1f} s for {unit_count} {language.unit} "
                            f"({units_per_second:.1f}/s, typical {typical_units_per_second:.1f}/s); listen to it and "
                            f"redo it with --beats {beat_id} if it is wrong")
    return warnings
