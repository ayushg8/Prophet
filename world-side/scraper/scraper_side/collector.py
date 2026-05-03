"""Public collector API for writing validated sanitized JSONL."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from .records import SanitizedRecord, validate_sanitized_record


def write_sanitized_jsonl(
    records: Iterable[Mapping[str, Any] | SanitizedRecord],
    path: str | Path,
) -> None:
    """Validate records, then atomically write newline-delimited JSON."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for record in records:
            normalized = (
                record if isinstance(record, SanitizedRecord) else validate_sanitized_record(record)
            )
            handle.write(normalized.to_json_line())
            handle.write("\n")
    tmp_path.replace(out_path)


def write_jsonl(
    records: Iterable[Mapping[str, Any] | SanitizedRecord],
    path: str | Path,
) -> None:
    """Compatibility alias."""

    write_sanitized_jsonl(records, path)


def dump_sanitized_jsonl(
    records: Iterable[Mapping[str, Any] | SanitizedRecord],
    path: str | Path,
) -> None:
    """Compatibility alias."""

    write_sanitized_jsonl(records, path)


def write_sanitized_records(
    records: Iterable[Mapping[str, Any] | SanitizedRecord],
    path: str | Path,
) -> None:
    """Compatibility alias."""

    write_sanitized_jsonl(records, path)
