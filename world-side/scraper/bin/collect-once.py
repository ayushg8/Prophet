#!/usr/bin/env python3
"""Run one sanitized collection pass on the isolated scraper host.

This script is intentionally scraper-side only. It never writes raw feed bodies
to disk; collectors parse in memory and emit the sanitized JSONL contract that
``sanitize-once.py`` validates before export.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any


APP_DIR = Path(os.environ.get("SCRAPER_APP_DIR", Path(__file__).resolve().parents[1]))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from scraper_side.catalog import filter_catalog, load_source_catalog  # noqa: E402
from scraper_side.collectors import collect_entry  # noqa: E402


def main() -> int:
    run_id = os.environ.get("SCRAPER_RUN_ID") or _stamp()
    state_dir = Path(os.environ.get("SCRAPER_STATE_DIR", "/srv/scraper/state"))
    output_dir = Path(os.environ.get("SCRAPER_OUTPUT_DIR", "/srv/scraper/output"))
    catalog_path = Path(os.environ.get("SCRAPER_CATALOG", APP_DIR / "config" / "source_catalog.json"))
    live = _truthy(os.environ.get("SCRAPER_LIVE", "1"))
    limit_per_source = _int_env("SCRAPER_LIMIT", 25)
    max_records = _int_env("SCRAPER_MAX_RECORDS", 1000)
    timeout = float(os.environ.get("SCRAPER_TIMEOUT", "20"))
    continue_on_error = _truthy(os.environ.get("SCRAPER_CONTINUE_ON_ERROR", "1"))
    requested_sources = _split_env("SCRAPER_SOURCE")

    state_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = filter_catalog(load_source_catalog(catalog_path), requested_sources)
    started_at = _now()
    records = []
    source_results: list[dict[str, Any]] = []

    for entry in entries:
        before = len(records)
        try:
            remaining = max(max_records - len(records), 0)
            if remaining == 0:
                break
            collected = collect_entry(
                entry,
                live=live,
                limit=min(limit_per_source, remaining),
                timeout=timeout,
            )
            records.extend(collected)
            source_results.append(
                {
                    "source": entry.name,
                    "collector": entry.collector,
                    "enabled": entry.enabled,
                    "status": "ok",
                    "records": len(records) - before,
                }
            )
        except Exception as exc:  # noqa: BLE001 - manifest needs the per-source failure.
            source_results.append(
                {
                    "source": entry.name,
                    "collector": entry.collector,
                    "enabled": entry.enabled,
                    "status": "error",
                    "records": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            if not continue_on_error:
                raise

    pending_path = state_dir / f"collected-sanitized-{run_id}.jsonl"
    latest_pending = state_dir / "latest-collected-sanitized.jsonl"
    manifest_path = state_dir / f"collection-manifest-{run_id}.json"
    latest_manifest = state_dir / "latest-collection-manifest.json"

    payload = "".join(record.to_json_line() + "\n" for record in records)
    pending_path.write_text(payload, encoding="utf-8")
    latest_pending.write_text(payload, encoding="utf-8")

    manifest = {
        "schema_version": "prophet.scraper.collection_manifest.v0.1",
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": _now(),
        "live": live,
        "catalog_path": str(catalog_path),
        "pending_sanitized_jsonl": str(pending_path),
        "limit_per_source": limit_per_source,
        "max_records": max_records,
        "records_collected": len(records),
        "sources": source_results,
        "raw_content_written": False,
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    latest_manifest.write_text(manifest_text, encoding="utf-8")

    print(f"pending_sanitized_jsonl={pending_path}")
    print(f"collection_manifest={manifest_path}")

    any_success = any(item["status"] == "ok" for item in source_results)
    return 0 if any_success else 1


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")
    return parsed


def _split_env(name: str) -> list[str]:
    value = os.environ.get(name, "")
    return [part.strip() for part in value.split(",") if part.strip()]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # noqa: BLE001 - CLI should surface trace in isolated host logs.
        traceback.print_exc()
        raise
