#!/usr/bin/env python3
"""Validate the latest scraper-side sanitized JSONL and export it.

The preceding collector already emits minimized records. This final boundary
step revalidates the allowlisted schema, writes the reviewed JSONL export, and
records an audit manifest that says no raw content crossed.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any


APP_DIR = Path(os.environ.get("SCRAPER_APP_DIR", Path(__file__).resolve().parents[1]))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from scraper_side.records import SanitizedRecord  # noqa: E402


def main() -> int:
    run_id = os.environ.get("SCRAPER_RUN_ID") or _stamp()
    state_dir = Path(os.environ.get("SCRAPER_STATE_DIR", "/srv/scraper/state"))
    output_dir = Path(os.environ.get("SCRAPER_OUTPUT_DIR", "/srv/scraper/output"))
    pending_path = Path(
        os.environ.get(
            "SCRAPER_PENDING_JSONL",
            state_dir / "latest-collected-sanitized.jsonl",
        )
    )

    if not pending_path.exists():
        raise FileNotFoundError(f"pending sanitized JSONL not found: {pending_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    records = _read_valid_records(pending_path)

    output_path = output_dir / f"sanitized-{run_id}.jsonl"
    latest_output = output_dir / "latest-sanitized.jsonl"
    payload = "".join(record.to_json_line() + "\n" for record in records)
    output_path.write_text(payload, encoding="utf-8")
    latest_output.write_text(payload, encoding="utf-8")

    manifest = {
        "schema_version": "prophet.scraper.sanitization_manifest.v0.1",
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": _now(),
        "input_path": str(pending_path),
        "sanitized_output_path": str(output_path),
        "records_validated": len(records),
        "raw_content_written": False,
        "boundary": "sanitized_jsonl_only",
    }
    manifest_path = output_dir / f"sanitization-manifest-{run_id}.json"
    latest_manifest = output_dir / "latest-sanitization-manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    latest_manifest.write_text(manifest_text, encoding="utf-8")

    print(f"sanitized_output={output_path}")
    print(f"sanitization_manifest={manifest_path}")
    return 0


def _read_valid_records(path: Path) -> list[SanitizedRecord]:
    records: list[SanitizedRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parsed: Any = json.loads(line)
            records.append(SanitizedRecord.from_mapping(parsed, source_name=f"{path}:{line_no}"))
    return records


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
