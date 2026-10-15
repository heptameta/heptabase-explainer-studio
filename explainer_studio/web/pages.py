"""What the two pages show: their data as JSON, a page digest that changes when their files change, and the HTML
shell.

The HTML is a fixed shell (`templates/<page_name>.html`) around the page's script; the script shows the page from the
JSON and shows it again when the page digest changes, so an edit made by the agent shows up without interrupting the
video.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path
from string import Template
from typing import Any

from .. import __version__, presenters, question_types
from ..background_music_providers import PROVIDER_BY_NAME_MAP as BACKGROUND_MUSIC_PROVIDER_BY_NAME_MAP
from ..cost import (
    build_work_totals,
    check_has_episode_work,
    compute_cost_report,
    compute_elapsed_seconds,
    filter_cost_report_to_episode,
    find_episode,
    get_step_count,
    list_steps,
)
from ..deliver import list_delivery_record_dir_paths, load_delivered_timeline, load_latest_delivery_record
from ..dev_mode import check_is_dev_mode_on
from ..errors import StudioError
from ..feedback import (
    SURVEY_ANSWER_MODEL_BY_KIND_MAP,
    check_is_about_current_video,
    load_feedback,
    resolve_current_survey_answer,
)
from ..feedback_bundle import resolve_unshared_items
from ..file_io import convert_yaml_document_to_plain_data, read_yaml_document
from ..gaps import load_gaps
from ..model_prices import load_dev_mode_model_prices
from ..narration_providers import PROVIDER_BY_NAME_MAP
from ..paths import EPISODE_ID_PATTERN, Series
from ..schemas.cost import EPISODE_STEPS, PLANNING_STEPS, CostReport, CostReportStep
from ..schemas.delivery_record import DeliveryRecord
from ..schemas.feedback import CommentAnchor, MomentAnchor
from ..schemas.model_prices import ModelPrice
from ..schemas.plan import Plan
from ..spending import compute_spent_usd
from ..user_dirs import get_model_prices_file_path
from .i18n import read_locale_strings, resolve_page_language_code, translate
from .plan_edits import compute_plan_version, validate_plan_document
from .voices import find_voice_display_name, get_voice_field, list_narration_provider_choices

WEB_DIR_PATH = Path(__file__).resolve().parent
STATIC_DIR_PATH = WEB_DIR_PATH / "static"
TEMPLATES_DIR_PATH = WEB_DIR_PATH / "templates"
HOME_URL = "https://heptabase.com?utm_content=explainer-studio"

# The Heptabase logomark: the dark "H." on its white tile, the same in both themes.
LOGO_SVG = (
    '<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect fill="#fff" height="80" '
    'rx="17.8641" width="80"/><g fill="#2e2e2e"><circle cx="58.8348" cy="56.505" r="4.85437"/><path '
    'clip-rule="evenodd" d="m20.9707 23.0906c0-2.4576 1.9923-4.4499 4.4498-4.4499 2.4576 0 4.4499 1.9923 4.4499 '
    '4.4499v26.699c0 2.4576-1.9923 4.4499-4.4499 4.4499-2.4575 0-4.4498-1.9923-4.4498-4.4499zm19.5793 7.12c0-2.4575 '
    '1.9923-4.4498 4.4498-4.4498 2.4576 0 4.4499 1.9923 4.4499 4.4498v26.6991c0 2.4576-1.9923 4.4498-4.4499 '
    '4.4498-2.4575 0-4.4498-1.9923-4.4498-4.4498v-10.2347c0-1.3431-.8197-2.5501-2.068-3.0455l-.3721-.1477c-2.0263'
    '-.8041-4.2902-.7638-6.2867.1118-1.1865.5204-1.9528 1.6933-1.9528 2.9889v-13.1644c0 1.2956.7663 2.4685 1.9528 '
    '2.9888 1.9965.8757 4.2604.9159 6.2867.1118l.3721-.1476c1.2484-.4954 2.068-1.7025 2.068-3.0456z" '
    'fill-rule="evenodd"/></g></svg>'
)
FAVICON_URL = ("data:image/svg+xml;base64,"
               + base64.b64encode(LOGO_SVG.replace(' aria-hidden="true"', "").encode()).decode())


def _compute_digest(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, default=str).encode("utf-8")).hexdigest()[:16]


def _read_stat(path: Path) -> tuple[int, int] | None:
    try:
        stat_result = path.stat()
    except OSError:
        return None
    return stat_result.st_mtime_ns, stat_result.st_size


def _read_bytes_or_empty(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _read_raw_plan(series: Series) -> tuple[dict[str, Any], list[str], str | None]:
    """The plan as written (even when it is not valid), its problems, and a parse error."""
    try:
        document = read_yaml_document(series.plan_file_path)
    except StudioError as error:
        return {}, [], f"{error.what}: {error.why}"
    except OSError as error:
        return {}, [], str(error)
    raw_plan = convert_yaml_document_to_plain_data(document)
    return (raw_plan if isinstance(raw_plan, dict) else {}), validate_plan_document(document), None


def _find_user_language_code(raw_plan: dict[str, Any]) -> Any:
    # The pages speak to the user, so they follow the language the user writes in, not the videos'.
    return raw_plan.get("user_language_code") or raw_plan.get("language_code")


def read_page_language_code(series: Series) -> str:
    return resolve_page_language_code(_find_user_language_code(_read_raw_plan(series)[0]))


def _list_episode_ids(raw_plan: dict[str, Any]) -> list[str]:
    return [raw_episode["id"] for raw_episode in raw_plan.get("episodes") or []
            if isinstance(raw_episode, dict) and isinstance(raw_episode.get("id"), str)
            and EPISODE_ID_PATTERN.match(raw_episode["id"])]


def _find_latest_delivery_record(series: Series, episode_id: str) -> DeliveryRecord | None:
    try:
        return load_latest_delivery_record(series, episode_id)
    except StudioError:
        return None


def _find_delivered_duration_seconds(series: Series, episode_id: str) -> float | None:
    """The length of the latest delivery's video, from its record's timeline."""
    record_dir_paths = list_delivery_record_dir_paths(series, episode_id)
    try:
        timeline = load_delivered_timeline(series, record_dir_paths[-1]) if record_dir_paths else None
    except StudioError:
        return None
    return timeline.duration_seconds if timeline else None


def _format_narration_label(narration_settings: Any, language_code: str) -> str | None:
    if not isinstance(narration_settings, dict) or not narration_settings.get("provider_name"):
        return None
    provider_name = str(narration_settings["provider_name"])
    voice = narration_settings.get(get_voice_field(provider_name))
    provider_display_name = (PROVIDER_BY_NAME_MAP[provider_name].display_name if provider_name in PROVIDER_BY_NAME_MAP
                             else provider_name)
    voice_display_name = find_voice_display_name(provider_name, str(voice), language_code) if voice else None
    return provider_display_name + (f" · {voice_display_name or voice}" if voice else "")


# Plan page -----------------------------------------------------------------------------------------------------------
def compute_plan_page_digest(series: Series) -> str:
    raw_plan, _, _ = _read_raw_plan(series)
    episode_ids = _list_episode_ids(raw_plan)
    latest_delivery_times = [(episode_id, record.delivered_at) for episode_id in episode_ids
                             if (record := _find_latest_delivery_record(series, episode_id))]
    scripted_episode_ids = [episode_id for episode_id in episode_ids
                            if series.get_episode_paths(episode_id).script_file_path.is_file()]
    return _compute_digest(compute_plan_version(_read_bytes_or_empty(series.plan_file_path)), latest_delivery_times,
                           scripted_episode_ids, _read_stat(series.spending_file_path))


def compute_plan_page(series: Series) -> dict[str, Any]:
    raw_plan, problems, error = _read_raw_plan(series)
    playbooks_by_presenter_name_map = presenters.list_playbooks_by_presenter_name()
    episodes = []
    for raw_episode in raw_plan.get("episodes") or []:
        raw_episode = raw_episode if isinstance(raw_episode, dict) else {}
        episode_id = raw_episode.get("id")
        presenter_name, question_type = raw_episode.get("presenter_name"), raw_episode.get("question_type")
        is_valid_id = isinstance(episode_id, str) and bool(EPISODE_ID_PATTERN.match(episode_id))
        is_known = (presenter_name in playbooks_by_presenter_name_map
                    and question_type in question_types.QUESTION_TYPE_BY_NAME_MAP)
        latest_delivery_record = _find_latest_delivery_record(series, episode_id) if is_valid_id else None
        episodes.append({
            "id": episode_id,
            "isDelivered": latest_delivery_record is not None,
            # an episode with a script that is not delivered yet is being made
            "isInProgress": (latest_delivery_record is None and is_valid_id
                             and series.get_episode_paths(episode_id).script_file_path.is_file()),
            # the delivered video's cover and real length; the delivered time makes a new cover reload
            "deliveredAt": latest_delivery_record.delivered_at.isoformat() if latest_delivery_record else None,
            "hasCover": (latest_delivery_record is not None
                         and (series.root_dir_path / latest_delivery_record.files.cover_file_name).is_file()),
            "durationSeconds": (_find_delivered_duration_seconds(series, episode_id)
                                if latest_delivery_record else None),
            "presenterDisplayName": str(presenter_name).capitalize() if presenter_name else "",
            "questionType": question_type or "",
            "questionTypeDisplayName": (question_types.QUESTION_TYPE_BY_NAME_MAP[question_type].display_name
                                        if question_type in question_types.QUESTION_TYPE_BY_NAME_MAP
                                        else (question_type or "")),
            "doesUseDraftPlaybook": is_known and not presenters.check_has_playbook(presenter_name, question_type),
            "narrationLabel": _format_narration_label(
                raw_episode.get("narration"),
                str(raw_episode.get("language_code") or raw_plan.get("language_code") or "en")),
        })
    try:
        spent_usd = compute_spent_usd(series)
    except StudioError:
        spent_usd = 0.0
    return {
        "languageCode": resolve_page_language_code(_find_user_language_code(raw_plan)),
        "planVersion": compute_plan_version(_read_bytes_or_empty(series.plan_file_path)),
        "pageDigest": compute_plan_page_digest(series),
        "plan": raw_plan,
        "problems": problems,
        "error": error,
        "episodes": episodes,
        "narrationProviders": list_narration_provider_choices(str(raw_plan.get("language_code") or "en")),
        "musicProviderNames": list(BACKGROUND_MUSIC_PROVIDER_BY_NAME_MAP),
        "spentUsd": round(spent_usd, 2),
        "defaultNarrationBudgetUsd": Plan.model_fields["narration_budget_usd"].default,  # for a plan that omits it
    }


# Video page ----------------------------------------------------------------------------------------------------------
def find_latest_delivery(series: Series, episode_id: str) -> dict[str, Any] | None:
    """The latest delivery: its record and its files at the series root, which the video page plays. None when the
    episode has not been delivered."""
    latest_delivery_record = load_latest_delivery_record(series, episode_id)
    if latest_delivery_record is None:
        return None
    delivered_files = latest_delivery_record.files
    return {"latest_delivery_record": latest_delivery_record,
            "video_file_path": series.root_dir_path / delivered_files.video_file_name,
            "subtitles_file_path_by_language_code_map": {
                subtitles.language_code: series.root_dir_path / subtitles.file_name
                for subtitles in delivered_files.subtitles},
            "cover_file_path": series.root_dir_path / delivered_files.cover_file_name}


def convert_comment_anchor_to_page_json(anchor: CommentAnchor) -> dict[str, Any]:
    """A comment's anchor as the video page reads it: {kind: "moment", timeSeconds} or {kind: "episode"}."""
    if isinstance(anchor, MomentAnchor):
        return {"kind": anchor.kind, "timeSeconds": anchor.time_seconds}
    return {"kind": anchor.kind}


def compute_video_page_digest(series: Series, episode_id: str) -> str:
    latest_delivery = find_latest_delivery(series, episode_id)
    return _compute_digest(_read_bytes_or_empty(series.get_episode_paths(episode_id).feedback_file_path),
                           compute_plan_version(_read_bytes_or_empty(series.plan_file_path)),
                           _read_stat(series.gaps_file_path),
                           latest_delivery["latest_delivery_record"].delivered_at if latest_delivery else None,
                           _read_stat(latest_delivery["video_file_path"]) if latest_delivery else None)


def compute_video_page(series: Series, episode_id: str) -> dict[str, Any]:
    raw_plan, _, _ = _read_raw_plan(series)
    raw_episode_by_id_map = {raw_episode.get("id"): raw_episode for raw_episode in raw_plan.get("episodes") or []
                             if isinstance(raw_episode, dict)}
    latest_delivery = find_latest_delivery(series, episode_id)
    if latest_delivery is None:
        raise StudioError(f"{episode_id} has not been delivered")
    feedback = load_feedback(series, episode_id)
    latest_delivery_record = latest_delivery["latest_delivery_record"]
    latest_delivery_time = latest_delivery_record.delivered_at
    comments = [{"id": comment.id, "anchor": convert_comment_anchor_to_page_json(comment.anchor), "text": comment.text,
                 "origin": comment.origin, "isResolved": comment.resolution is not None,
                 # made before the latest delivery: its moment is in an older video
                 "isOnOlderVideo": not check_is_about_current_video(comment.created_at, latest_delivery_time)}
                for comment in feedback.comments]
    current_survey_answers = [answer for kind in SURVEY_ANSWER_MODEL_BY_KIND_MAP
                              if (answer := resolve_current_survey_answer(feedback, kind, latest_delivery_time))]
    delivered_episodes = [{"id": delivered_episode_id,
                           "title": str(raw_episode_by_id_map.get(delivered_episode_id, {}).get("title")
                                        or delivered_episode_id)}
                          for delivered_episode_id in _list_episode_ids(raw_plan)
                          if _find_latest_delivery_record(series, delivered_episode_id)]
    return {
        "languageCode": resolve_page_language_code(_find_user_language_code(raw_plan)),
        "pageDigest": compute_video_page_digest(series, episode_id),
        "episode": {"id": episode_id,
                    "title": str(raw_episode_by_id_map.get(episode_id, {}).get("title") or episode_id)},
        "seriesTitle": str(raw_plan.get("title") or ""),
        "delivery": {"deliveredAt": latest_delivery_record.delivered_at.isoformat(),
                     "filePath": str(latest_delivery["video_file_path"]),
                     "hasFile": latest_delivery["video_file_path"].is_file(),
                     # the delivered subtitles whose file is at the series root
                     "subtitles": [{"languageCode": language_code} for language_code, subtitles_file_path
                                   in latest_delivery["subtitles_file_path_by_language_code_map"].items()
                                   if subtitles_file_path.is_file()],
                     "hasCover": latest_delivery["cover_file_path"].is_file(),
                     "explainerStudioVersion": latest_delivery_record.explainer_studio_version},
        "explainerStudioVersion": __version__,  # the installed version, which this page server runs
        "comments": comments,
        # the current answer of each survey question answered since the latest delivery
        "surveyAnswers": [{"kind": answer.kind, "value": answer.value} for answer in current_survey_answers],
        "isDevModeOn": check_is_dev_mode_on(),
        "hasUnsharedFeedback": resolve_unshared_items(feedback, load_gaps(series)).has_feedback,
        "episodes": delivered_episodes,
    }


def _build_cost_row(report: CostReport, steps: list[CostReportStep], prices: list[ModelPrice] | None) -> dict[str, Any]:
    totals = build_work_totals(report, steps, prices)
    return {"workingDurationSeconds": totals.working_duration_seconds, "callCount": totals.call_count,
            "tokenCount": totals.token_count, "narrationCostUsd": round(totals.narration_cost_usd, 2),
            "agentCostUsd": round(totals.agent_cost_usd, 2) if totals.agent_cost_usd is not None else None,
            "unpricedModelNames": list(totals.unpriced_model_names)}


def _build_cost_group(report: CostReport, steps: list[CostReportStep],
                      prices: list[ModelPrice] | None) -> dict[str, Any]:
    return {"total": _build_cost_row(report, steps, prices),
            "steps": [{"step": step.step, "count": get_step_count(step), **_build_cost_row(report, [step], prices)}
                      for step in steps]}


def compute_video_cost_report(series: Series, episode_id: str) -> dict[str, Any]:
    """The episode's cost report as dev mode's section of the video page shows it (worked out on request, not stored):
    the series' planning step by step, then the episode's steps up to its first delivery.

    Dollars for the agent's usage are worked out here, from the local price table, when it exists."""
    report = filter_cost_report_to_episode(compute_cost_report(series), episode_id)
    episode = find_episode(report, episode_id)
    if report.unavailable_reason is not None or episode is None or not check_has_episode_work(report, episode_id):
        return {"unavailableReason": report.unavailable_reason or "no work on this episode is in the agent's "
                                                                  "transcripts"}
    prices, price_table_problem = load_dev_mode_model_prices()
    first_delivery = episode.first_delivery
    has_planning = any(step.episode_id is None for step in report.steps)
    return {
        "unavailableReason": None,
        "priceTablePath": str(get_model_prices_file_path()),  # read when it exists: the rows then have agentCostUsd
        "priceTableProblem": price_table_problem,
        "firstDelivery": {"deliveredAt": first_delivery.delivered_at.isoformat(),
                          "durationSeconds": first_delivery.duration_seconds,
                          "sceneCount": first_delivery.scene_count} if first_delivery else None,
        "elapsedSeconds": compute_elapsed_seconds(report, episode_id),
        "planning": _build_cost_group(report, list_steps(report, None, PLANNING_STEPS), prices) if has_planning
        else None,
        "episode": _build_cost_group(report, list_steps(report, episode_id, EPISODE_STEPS), prices),
    }


# HTML ----------------------------------------------------------------------------------------------------------------
def _format_header_html(language_code: str) -> str:
    version_text = html.escape(translate(language_code, "common.version", version=__version__))
    return (f'<header class="hb-bar"><a class="hb-brand" href="{HOME_URL}" target="_blank" rel="noreferrer noopener">'
            f'{LOGO_SVG}<span>Heptabase</span></a>'
            f'<span class="hb-product">{translate(language_code, "app.product")}</span>'
            f'<span class="hb-version hb-meta">{version_text}</span>'
            '</header>')


def _serialize_json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028") \
        .replace("\u2029", "\\u2029")


def format_page_html(page_name: str, language_code: str, title: str, base_url: str, boot: dict[str, Any]) -> str:
    """The page's HTML shell with everything its script needs to show the page."""
    template = Template((TEMPLATES_DIR_PATH / f"{page_name}.html").read_text(encoding="utf-8"))
    boot = {**boot, "baseUrl": base_url, "languageCode": language_code,
            "strings": read_locale_strings(language_code)}
    return template.substitute(lang=language_code, title=html.escape(title),
                               favicon=FAVICON_URL, static=f"{base_url}/static",
                               header=_format_header_html(language_code), boot=_serialize_json_for_script(boot))


def read_series_title(series: Series) -> str:
    return str(_read_raw_plan(series)[0].get("title") or series.root_dir_path.name)
