"""Saving one production setting from the plan page.

The plan page is read-only except for the production settings: the narration provider, its voice, the narration
budget, the background music and the end credits.
Everything else the user asks the agent to change. The page sends the path of the setting it changed, the new value,
and the version of plan.yaml it showed. The save happens under the file's lock on the round-trip YAML document, so the
agent's comments, key order and block styles survive; it is refused when the file changed since the page loaded it,
and when the result would not be a valid plan.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import ValidationError
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken

from ..background_music_providers import PROVIDER_BY_NAME_MAP as BACKGROUND_MUSIC_PROVIDER_BY_NAME_MAP
from ..file_io import (
    convert_yaml_document_to_plain_data,
    format_validation_error,
    hold_lock,
    read_yaml_document,
    write_yaml,
)
from ..paths import Series
from ..schemas.plan import Plan
from .voices import build_default_narration_settings, get_voice_field


class PlanConflictError(Exception):
    """plan.yaml changed after the page loaded it."""


class InvalidEditError(Exception):
    def __init__(self, code: str, details: list[str] | None = None):
        super().__init__(code)
        self.code = code  # a locale key suffix the page shows: plan.error.<code>
        self.details = details or []


def compute_plan_version(plan_bytes: bytes) -> str:
    return hashlib.sha256(plan_bytes).hexdigest()[:16]


def _put(mapping: CommentedMap, key: str, value: Any, after_keys: tuple[str, ...] = ()) -> None:
    """Set `key`, removing it for None; a new key goes after the first of `after_keys` that exists. The blank line or
    comment that ends a mapping stays at its end."""
    keys = list(mapping)
    if value is None:
        if key in mapping:
            trailing = mapping.ca.items.pop(key, None) if keys[-1] == key else None
            del mapping[key]
            if trailing and mapping:
                mapping.ca.items[list(mapping)[-1]] = trailing
    elif key in mapping:
        mapping[key] = value
    else:
        anchor = next((keys.index(name) + 1 for name in after_keys if name in mapping), len(keys))
        mapping.insert(anchor, key, value)
        if anchor == len(keys) and keys and keys[-1] in mapping.ca.items and not isinstance(value, dict):
            mapping.ca.items[key] = mapping.ca.items.pop(keys[-1])


def _apply_edit(document: CommentedMap, field_path: list[Any], value: Any) -> None:
    match field_path:
        case ["narration_budget_usd"]:
            if value is not None and (isinstance(value, bool) or not isinstance(value, int | float)):
                raise InvalidEditError("not_a_number")
            if value is not None and value < 0:
                raise InvalidEditError("negative")
            if "narration_budget_usd" in document:
                document["narration_budget_usd"] = value  # keeps the agent's comment on it
            else:  # null is written too: it means no limit, while an omitted budget means the default
                keys = list(document)
                document.insert(keys.index("language_code") + 1 if "language_code" in document else 0,
                                "narration_budget_usd", value)
        case ["narration", "provider_name"]:
            if value is not None and not isinstance(value, str):
                raise InvalidEditError("invalid")
            language_code = str(document.get("language_code") or "en")
            block = CommentedMap(build_default_narration_settings(value, language_code)) if value else None
            old_block = document.get("narration")
            if (block is not None and isinstance(old_block, CommentedMap) and old_block
                    and old_block.ca.items.get(list(old_block)[-1])):
                # the blank line or comment after the old block belongs after the new one
                block.ca.items[list(block)[-1]] = old_block.ca.items[list(old_block)[-1]]
            elif block is not None and old_block is None:  # a new block gets a blank line after it, like the others
                block.ca.items[list(block)[-1]] = [None, None, CommentToken("\n\n", CommentMark(0), None), None]
            _put(document, "narration", block, ("narration_budget_usd", "language_code"))
        case ["background_music", "provider_name"]:
            if value not in BACKGROUND_MUSIC_PROVIDER_BY_NAME_MAP:
                raise InvalidEditError("invalid")
            _put(document, "background_music", CommentedMap({"provider_name": value}),
                 ("narration", "narration_budget_usd"))
        case ["has_end_credits"]:
            if not isinstance(value, bool):
                raise InvalidEditError("invalid")
            _put(document, "has_end_credits", value, ("background_music", "narration", "narration_budget_usd"))
        case ["narration", "voice"]:
            block = document.get("narration")
            if not isinstance(block, dict) or value is not None and not isinstance(value, str):
                raise InvalidEditError("not_editable")
            _put(block, get_voice_field(block.get("provider_name", "")), value.strip() if value else None,
                 ("provider_name",))
        case _:
            raise InvalidEditError("not_editable")


def validate_plan_document(document: Any) -> list[str]:
    try:
        Plan.model_validate(convert_yaml_document_to_plain_data(document) or {})
    except ValidationError as error:
        return format_validation_error("plan.yaml", error)
    return []


def write_plan_field(series: Series, field_path: list[Any], value: Any, shown_plan_version: str) -> str:
    """Save one field; returns the new version of plan.yaml."""
    with hold_lock(series.plan_file_path):
        if compute_plan_version(series.plan_file_path.read_bytes()) != shown_plan_version:
            raise PlanConflictError()
        document = read_yaml_document(series.plan_file_path)
        if not isinstance(document, CommentedMap) or validate_plan_document(document):
            raise InvalidEditError("plan_invalid", validate_plan_document(document))
        try:
            _apply_edit(document, field_path, value)
        except (KeyError, TypeError, AttributeError):
            raise InvalidEditError("not_editable") from None
        problems = validate_plan_document(document)
        if problems:
            raise InvalidEditError("invalid", problems)
        write_yaml(series.plan_file_path, document)
        return compute_plan_version(series.plan_file_path.read_bytes())
