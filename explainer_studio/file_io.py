"""Reading and writing series files safely.

Several processes can write the same file: the agent's commands, parallel subagents and the page server. Every write
goes through `hold_lock` (a lock file next to the target) and lands with an atomic replace, so a reader never sees half
a file and two writers never lose each other's entries. YAML is read and written round-trip, so comments and key order
the agent wrote survive a save from the plan page.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from filelock import FileLock
from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from .errors import StudioError


def _create_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


@contextlib.contextmanager
def hold_lock(path: Path, timeout_seconds: float = 30) -> Iterator[None]:
    """Hold the lock for `path` while a read-modify-write happens."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(path) + ".lock", timeout=timeout_seconds)
    with lock:
        yield


def _get_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


def _publish(temporary_path: str, path: Path, is_private: bool = False) -> None:
    """Set the final permissions on the temp file (mkstemp makes it 0600), then move it into place."""
    os.chmod(temporary_path, 0o600 if is_private else 0o666 & ~_get_umask())
    os.replace(temporary_path, path)


def write_bytes_atomic(path: Path, content: bytes, is_private: bool = False) -> None:
    """`is_private` keeps the file readable by its owner only, from the moment it exists (for keys)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
        _publish(temporary_path, path, is_private)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_path)
        raise


def write_text_atomic(path: Path, text: str, is_private: bool = False) -> None:
    """UTF-8 with \\n line endings on every platform."""
    write_bytes_atomic(path, text.encode("utf-8"), is_private)


def get_current_time() -> datetime:
    """The time written into series records: local time with its UTC offset, to the second."""
    return datetime.now().astimezone().replace(microsecond=0)


# YAML ---------------------------------------------------------------------------------------------------------------
def read_yaml_document(path: Path) -> Any:
    """The YAML document with its comments (ruamel CommentedMap); None for an empty file."""
    try:
        return _create_yaml().load(path.read_text(encoding="utf-8"))
    except YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise StudioError(f"{path.name} is not valid YAML{where}", str(getattr(error, "problem", error)),
                          f"fix the YAML syntax in {path}") from None


def serialize_yaml(document: Any) -> str:
    stream = io.StringIO()
    _create_yaml().dump(document, stream)
    return stream.getvalue()


def write_yaml(path: Path, document: Any) -> None:
    write_text_atomic(path, serialize_yaml(document))


def convert_yaml_document_to_plain_data(document: Any) -> Any:
    """A ruamel document as plain dicts and lists, for validation."""
    if isinstance(document, dict):
        return {str(key): convert_yaml_document_to_plain_data(value) for key, value in document.items()}
    if isinstance(document, list):
        return [convert_yaml_document_to_plain_data(entry) for entry in document]
    return document


# JSON ---------------------------------------------------------------------------------------------------------------
def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StudioError(f"{path.name} is not valid JSON", f"{error.msg} at line {error.lineno}",
                          f"fix or remove {path}") from None


def serialize_json(document: Any) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def write_json(path: Path, document: Any) -> None:
    write_text_atomic(path, serialize_json(document))


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with hold_lock(path), path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            raise StudioError(f"{path.name} line {line_number} is not valid JSON", "the file is append-only JSON lines",
                              f"fix or remove line {line_number} of {path}") from None
    return records


# Models -------------------------------------------------------------------------------------------------------------
def format_validation_error(file_label: str, error: ValidationError) -> list[str]:
    details = []
    for problem in error.errors():
        location = ".".join(str(part) for part in problem["loc"]) or "(top level)"
        details.append(f"{file_label}: {location}: {problem['msg']}")
    return details


def validate_model[Model: BaseModel](model_class: type[Model], document: Any, path: Path,
                                      file_label: str | None = None) -> Model:
    try:
        return model_class.model_validate(document if document is not None else {})
    except ValidationError as error:
        file_label = file_label or path.name
        raise StudioError(f"{file_label} does not match its format", f"{error.error_count()} problem(s)",
                          f"fix {path} (the format is in `explainer-studio guide references/file-formats.md`)",
                          format_validation_error(file_label, error)) from None


def load_yaml_model[Model: BaseModel](model_class: type[Model], path: Path, file_label: str | None = None) -> Model:
    if not path.exists():
        raise StudioError(f"{file_label or path.name} is missing", f"expected {path}")
    return validate_model(model_class, convert_yaml_document_to_plain_data(read_yaml_document(path)), path,
                          file_label)


def load_json_model[Model: BaseModel](model_class: type[Model], path: Path, file_label: str | None = None) -> Model:
    if not path.exists():
        raise StudioError(f"{file_label or path.name} is missing", f"expected {path}")
    return validate_model(model_class, read_json(path), path, file_label)


def write_json_model(path: Path, model: BaseModel) -> None:
    write_json(path, model.model_dump(mode="json", exclude_none=False))
