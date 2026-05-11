"""Build sanitized OSINT snapshot artifacts from scraper catalog sources."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

from .catalog import CatalogEntry, filter_catalog, load_source_catalog
from .collectors import collect_entry
from .records import SanitizedRecord


SNAPSHOT_SCHEMA_VERSION = "prophet.osint_snapshot.v0.1"
MANIFEST_SCHEMA_VERSION = "prophet.osint_snapshot_manifest.v0.1"
SEEDSET_SCHEMA_VERSION = "asset_osint_seedset.v0.1"
SEEDABLE_COLLECTORS = {
    "cve_record_v5",
    "cisa_vulnrichment",
    "osv_vulnerabilities",
    "redhat_security_data",
}


def build_osint_snapshot(
    entries: Iterable[CatalogEntry],
    *,
    live: bool = False,
    limit_per_source: int = 25,
    max_records: int = 1000,
    generated_at: str | None = None,
    timeout: float = 20.0,
    continue_on_error: bool = True,
    asset_seedsets: Iterable[dict[str, Any]] | None = None,
    seed_fixture_dir: str | Path | None = None,
    max_seeds_per_source: int = 25,
) -> tuple[list[SanitizedRecord], dict[str, Any]]:
    """Collect catalog entries and return sanitized records plus a manifest."""

    if limit_per_source < 0:
        raise ValueError("limit_per_source must be non-negative")
    if max_records < 0:
        raise ValueError("max_records must be non-negative")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_seeds_per_source < 0:
        raise ValueError("max_seeds_per_source must be non-negative")

    emitted_at = _ensure_timestamp(generated_at)
    records: list[SanitizedRecord] = []
    source_results: list[dict[str, Any]] = []
    seed_context = _build_seed_context(asset_seedsets, max_seeds_per_source=max_seeds_per_source)
    expanded_entries = expand_seeded_entries(
        list(entries),
        seed_context=seed_context,
        seed_fixture_dir=seed_fixture_dir,
    )

    for entry in expanded_entries:
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
                    "source_id": entry.name,
                    "collector": entry.collector,
                    "source_type": entry.source_type,
                    "collection_tier": entry.collection_tier,
                    "enabled": entry.enabled,
                    "status": "ok",
                    "records": len(records) - before,
                    "seed_key": str(entry.options.get("seed_key") or ""),
                }
            )
        except Exception as exc:  # noqa: BLE001 - manifest must record source failure.
            source_results.append(
                {
                    "source_id": entry.name,
                    "collector": entry.collector,
                    "source_type": entry.source_type,
                    "collection_tier": entry.collection_tier,
                    "enabled": entry.enabled,
                    "status": "error",
                    "records": 0,
                    "seed_key": str(entry.options.get("seed_key") or ""),
                    "error": _safe_error(exc),
                }
            )
            if not continue_on_error:
                raise

    jsonl_payload = records_to_jsonl(records)
    source_type_counts = _count_by(source_results, "source_type")
    collection_tier_counts = _count_by(source_results, "collection_tier")
    successful_sources = [item["source_id"] for item in source_results if item["status"] == "ok"]
    failed_sources = [item["source_id"] for item in source_results if item["status"] == "error"]

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "generated_at": emitted_at,
        "live": live,
        "record_count": len(records),
        "source_count": len(source_results),
        "seed_context": seed_context["manifest"],
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "source_type_counts": source_type_counts,
        "collection_tier_counts": collection_tier_counts,
        "sources": source_results,
        "hashes": {
            "snapshot_jsonl_sha256": hashlib.sha256(jsonl_payload.encode("utf-8")).hexdigest(),
            "manifest_body_sha256": "",
        },
        "safety_attestation": {
            "sanitized_records_only": True,
            "raw_content_written": False,
            "no_credentials": True,
            "no_payloads": True,
            "no_target_lists": True,
        },
    }
    manifest["hashes"]["manifest_body_sha256"] = _manifest_body_sha256(manifest)
    return records, manifest


def expand_seeded_entries(
    entries: Iterable[CatalogEntry],
    *,
    seed_context: dict[str, Any],
    seed_fixture_dir: str | Path | None = None,
) -> list[CatalogEntry]:
    """Expand seedable catalog entries into per-CVE metadata collection entries."""

    cve_ids = list(seed_context.get("cve_ids") or [])
    if not cve_ids:
        return list(entries)

    fixture_root = Path(seed_fixture_dir) if seed_fixture_dir else None
    expanded: list[CatalogEntry] = []
    for entry in entries:
        if entry.collector not in SEEDABLE_COLLECTORS:
            expanded.append(entry)
            continue
        for cve_id in cve_ids:
            expanded.append(_seeded_entry(entry, cve_id, fixture_root))
    return expanded


def records_to_jsonl(records: Iterable[SanitizedRecord]) -> str:
    return "".join(record.to_json_line() + "\n" for record in records)


def write_osint_snapshot(
    records: list[SanitizedRecord],
    manifest: dict[str, Any],
    *,
    out_jsonl: str | Path,
    out_manifest: str | Path,
) -> None:
    jsonl_path = Path(out_jsonl)
    manifest_path = Path(out_manifest)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text(records_to_jsonl(records), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        entries = filter_catalog(load_source_catalog(args.catalog), args.source)
        seedsets = [load_asset_seedset(path) for path in args.asset_seedset]
        policy_context = _load_policy(args.policy) if args.policy else None
        if args.policy:
            enforce_snapshot_policy(
                args.policy,
                entries=entries,
                live=args.live,
                seeded=bool(seedsets),
            )
        records, manifest = build_osint_snapshot(
            entries,
            live=args.live,
            limit_per_source=args.limit_per_source,
            max_records=args.max_records,
            generated_at=args.generated_at,
            timeout=args.timeout,
            continue_on_error=not args.fail_fast,
            asset_seedsets=seedsets,
            seed_fixture_dir=args.seed_fixture_dir,
            max_seeds_per_source=args.max_seeds_per_source,
        )
        if policy_context is not None:
            manifest["policy"] = _policy_manifest_context(policy_context)
            manifest["hashes"]["manifest_body_sha256"] = _manifest_body_sha256(manifest)
        if args.out_jsonl and args.out_manifest:
            write_osint_snapshot(
                records,
                manifest,
                out_jsonl=args.out_jsonl,
                out_manifest=args.out_manifest,
            )
            print(
                f"wrote {len(records)} sanitized OSINT record(s) to {args.out_jsonl}",
                file=sys.stderr,
            )
        else:
            print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0 if records or not args.require_records else 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"osint.snapshot: {_safe_error(exc)}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m scraper_side.snapshot",
        description="Collect safe scraper sources into a sanitized OSINT snapshot JSONL and manifest.",
    )
    parser.add_argument("--catalog", type=Path, help="Source catalog JSON")
    parser.add_argument("--source", action="append", default=[], help="Catalog source id to include")
    parser.add_argument(
        "--asset-seedset",
        action="append",
        type=Path,
        default=[],
        help=(
            "Optional asset_osint_seedset.v0.1 JSON. Seedable sources are expanded "
            "into per-CVE metadata lookups."
        ),
    )
    parser.add_argument(
        "--seed-fixture-dir",
        type=Path,
        help=(
            "Optional local fixture directory for seeded sources. Expected shape: "
            "<dir>/<source_id>/<CVE-id>.json. Useful for offline demos/tests."
        ),
    )
    parser.add_argument("--max-seeds-per-source", type=int, default=25)
    parser.add_argument("--live", action="store_true", help="Enable official public HTTPS collection")
    parser.add_argument("--limit-per-source", type=int, default=25)
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--generated-at", help="ISO 8601 timestamp for deterministic output")
    parser.add_argument("--policy", type=Path, help="Optional prophet_pilot_policy.v0.1 gate")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first source failure")
    parser.add_argument("--require-records", action="store_true", help="Return non-zero if no records were produced")
    parser.add_argument("--out-jsonl", type=Path, help="Output sanitized JSONL snapshot path")
    parser.add_argument("--out-manifest", type=Path, help="Output snapshot manifest JSON path")
    return parser


def load_asset_seedset(path: str | Path) -> dict[str, Any]:
    seedset_path = Path(path)
    data = json.loads(seedset_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"asset seedset must be an object: {seedset_path}")
    if data.get("schema_version") != SEEDSET_SCHEMA_VERSION:
        raise ValueError(f"asset seedset schema_version must be {SEEDSET_SCHEMA_VERSION}")
    _assert_seedset_safe(data, str(seedset_path))
    return data


def enforce_snapshot_policy(
    policy_path: str | Path,
    *,
    entries: Iterable[CatalogEntry],
    live: bool,
    seeded: bool,
) -> None:
    """Fail closed when a policy does not permit the requested snapshot mode."""

    policy = _load_policy(policy_path)
    allowed_modes = _object(policy.get("allowed_modes"))
    osint_modes = _string_list(allowed_modes.get("osint_collection"))
    forecast_modes = _string_list(allowed_modes.get("forecast_generation"))
    mode = "seeded_osint" if seeded else "fixture"
    if live:
        raise ValueError("policy does not allow --live OSINT collection for pilot snapshots")
    if mode not in osint_modes:
        raise ValueError(f"policy does not allow OSINT collection mode: {mode}")
    if mode not in forecast_modes:
        raise ValueError(f"policy does not allow forecast generation mode: {mode}")

    allowed_sources = _string_list(policy.get("allowed_source_ids"))
    if allowed_sources:
        requested_sources = [entry.name for entry in entries]
        blocked = sorted(source for source in requested_sources if source not in allowed_sources)
        if blocked:
            raise ValueError(f"policy does not allow source ids: {', '.join(blocked)}")


def _count_by(source_results: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in source_results:
        if item.get("status") != "ok":
            continue
        label = str(item.get(key) or "unknown")
        counts[label] = counts.get(label, 0) + int(item.get("records") or 0)
    return dict(sorted(counts.items()))


def _manifest_body_sha256(manifest: dict[str, Any]) -> str:
    body = json.loads(json.dumps(manifest, sort_keys=True))
    if isinstance(body.get("hashes"), dict):
        body["hashes"]["manifest_body_sha256"] = ""
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _build_seed_context(
    seedsets: Iterable[dict[str, Any]] | None,
    *,
    max_seeds_per_source: int,
) -> dict[str, Any]:
    seedset_list = list(seedsets or [])
    cve_ids = _dedupe(
        [
            str(item.get("cve_id") or "").strip().upper()
            for seedset in seedset_list
            for item in seedset.get("cve_seeds", [])
            if isinstance(item, dict)
        ]
    )
    cve_ids = [cve_id for cve_id in cve_ids if re.fullmatch(r"CVE-\d{4}-\d{4,}", cve_id)]
    if max_seeds_per_source:
        cve_ids = cve_ids[:max_seeds_per_source]
    seedset_refs = [
        {
            "seedset_id": str(seedset.get("seedset_id") or "unknown-seedset"),
            "asset_count": int((seedset.get("input_refs") or {}).get("asset_count") or 0)
            if isinstance(seedset.get("input_refs"), dict)
            else 0,
            "cve_seed_count": len(seedset.get("cve_seeds") or []),
            "fixture_context": bool(seedset.get("fixture_context", True)),
            "seedset_sha256": str(seedset.get("seedset_sha256") or ""),
        }
        for seedset in seedset_list
    ]
    manifest = {
        "integrated": bool(seedset_list),
        "seedset_count": len(seedset_list),
        "cve_seed_count": len(cve_ids),
        "max_seeds_per_source": max_seeds_per_source,
        "seedsets": seedset_refs,
        "cve_ids": cve_ids,
        "safety_attestation": {
            "metadata_seeds_only": True,
            "no_live_targets": True,
            "no_payloads": True,
            "no_credentials": True,
            "no_collection_without_explicit_source": True,
        },
    }
    return {"cve_ids": cve_ids, "manifest": manifest}


def _seeded_entry(
    entry: CatalogEntry,
    cve_id: str,
    fixture_root: Path | None,
) -> CatalogEntry:
    url = _seeded_url(entry, cve_id)
    local_path = _seed_fixture_path(fixture_root, entry.name, cve_id)
    options = {
        **entry.options,
        "seed_key": cve_id,
        "max_records": str(min(int(str(entry.options.get("max_records", "100"))), 1))
        if str(entry.options.get("max_records", "100")).isdigit()
        else "1",
    }
    return CatalogEntry(
        name=f"{entry.name}_{_slug(cve_id)}",
        collector=entry.collector,
        source_type=entry.source_type,
        collection_tier=entry.collection_tier,
        url=url,
        url_template=entry.url_template,
        format=entry.format,
        local_path=local_path,
        enabled=entry.enabled,
        options=options,
    )


def _seeded_url(entry: CatalogEntry, cve_id: str) -> str:
    template = entry.url_template or entry.url
    if not template:
        return entry.url
    year, number = _split_cve(cve_id)
    bucket = _cve_bucket(number)
    return template.format(
        cve_id=cve_id,
        osv_id=cve_id,
        year=year,
        bucket=bucket,
        id=number,
    )


def _seed_fixture_path(root: Path | None, source_id: str, cve_id: str) -> Path | None:
    if root is None:
        return None
    candidates = [
        root / source_id / f"{cve_id}.json",
        root / source_id / f"{_slug(cve_id)}.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _split_cve(cve_id: str) -> tuple[str, str]:
    match = re.fullmatch(r"CVE-(\d{4})-(\d{4,})", cve_id)
    if not match:
        return "0000", "0"
    return match.group(1), match.group(2)


def _cve_bucket(number: str) -> str:
    try:
        value = int(number)
    except ValueError:
        return "0xxx"
    return f"{value // 1000}xxx"


def _assert_seedset_safe(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in {"payload", "credentials", "password", "hostname", "ip_address"}:
                raise ValueError(f"{path}: unsafe seedset key {key}")
            _assert_seedset_safe(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _assert_seedset_safe(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        if re.search(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b", value):
            raise ValueError(f"{path}: seedset contains IP-like text")
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
            raise ValueError(f"{path}: seedset contains email-like text")
        if re.search(r"\b(?:password|secret|api[_-]?key|access[_-]?token)\b", value, re.I):
            raise ValueError(f"{path}: seedset contains credential-like text")


def _load_policy(path: str | Path) -> dict[str, Any]:
    try:
        from evidence.bundle import load_policy  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment issue.
        raise ValueError("policy enforcement requires PYTHONPATH=.:cyber-side:world-side") from exc

    return load_policy(path)


def _policy_manifest_context(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_id": str(policy.get("policy_id") or "unknown-policy"),
        "policy_sha256": _sha256_normalized(policy),
        "retention": _object(policy.get("retention")),
    }


def _sha256_normalized(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _ensure_timestamp(value: str | None) -> str:
    if value:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_error(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:500]


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


if __name__ == "__main__":
    raise SystemExit(main())
