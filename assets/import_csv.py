"""Import customer-owned asset CSV metadata into Prophet's safe inventory shape.

The importer is deliberately conservative. It accepts product-family and SBOM
metadata only, rejects unsafe row text, and emits a row-level cleanup report.
It does not perform collection and does not accept hostnames, IPs, credentials,
URLs, or raw target names.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from assets.inventory import (
    ASSET_SCHEMA_VERSION,
    SEEDSET_SCHEMA_VERSION,
    AssetInventoryError,
    build_asset_seedset,
    validate_asset_inventory,
    write_seedset,
)


REPORT_SCHEMA_VERSION = "asset_csv_import_report.v0.1"
CSV_SCHEMA_VERSION = "asset_inventory_csv.v0.1"
IMPORT_MANIFEST_SCHEMA_VERSION = "asset_csv_import_manifest.v0.1"

REQUIRED_COLUMNS = (
    "asset_id",
    "product_family",
    "exposure_class",
    "owner_group",
    "environment",
    "business_criticality",
    "sbom_components",
    "known_cve_overlaps",
    "compensating_controls",
)


class AssetCsvImportError(ValueError):
    """Raised when a CSV row cannot be parsed into safe asset metadata."""


def import_asset_inventory_csv(
    csv_path: str | Path,
    *,
    inventory_id: str,
    generated_at: str | None = None,
    scope: str = "Customer-owned metadata import; no live targets named.",
    fixture: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a safe inventory and row-level import report for a CSV file."""

    emitted_at = _ensure_timestamp(generated_at)
    path = Path(csv_path)
    source_sha256 = _sha256_file(path)
    rows = _read_rows(path)
    accepted_assets: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    seen_assets: set[str] = set()

    for row_number, row in rows:
        try:
            asset = _asset_from_row(row)
            if asset["asset_id"] in seen_assets:
                raise AssetCsvImportError("duplicate asset_id")
            validate_asset_inventory(
                {
                    "schema_version": ASSET_SCHEMA_VERSION,
                    "inventory_id": f"{inventory_id}-row-{row_number}",
                    "generated_at": emitted_at,
                    "fixture": fixture,
                    "scope": scope,
                    "assets": [asset],
                }
            )
            accepted_assets.append(asset)
            seen_assets.add(asset["asset_id"])
        except (AssetCsvImportError, AssetInventoryError) as exc:
            rejected_rows.append(
                {
                    "row_number": row_number,
                    "status": "rejected",
                    "errors": [_safe_error(exc)],
                }
            )

    if not accepted_assets:
        raise AssetInventoryError("CSV import produced no safe asset rows")

    inventory = {
        "schema_version": ASSET_SCHEMA_VERSION,
        "inventory_id": inventory_id,
        "generated_at": emitted_at,
        "fixture": fixture,
        "scope": scope,
        "source_format": CSV_SCHEMA_VERSION,
        "source_csv_sha256": source_sha256,
        "import_summary": {
            "accepted_row_count": len(accepted_assets),
            "rejected_row_count": len(rejected_rows),
            "total_row_count": len(rows),
        },
        "assets": accepted_assets,
    }
    validate_asset_inventory(inventory)

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": emitted_at,
        "inventory_id": inventory_id,
        "source_format": CSV_SCHEMA_VERSION,
        "source_csv_sha256": source_sha256,
        "accepted_count": len(accepted_assets),
        "rejected_count": len(rejected_rows),
        "accepted_row_count": len(accepted_assets),
        "rejected_row_count": len(rejected_rows),
        "total_row_count": len(rows),
        "accepted_asset_ids": [asset["asset_id"] for asset in accepted_assets],
        "rejected_rows": rejected_rows,
        "safety_attestation": {
            "customer_owned_metadata_only": True,
            "no_collection_performed": True,
            "no_ips": True,
            "no_hostnames": True,
            "no_credentials": True,
            "no_urls": True,
            "no_payloads": True,
            "no_raw_unsafe_values_in_rejection_report": True,
        },
    }
    return inventory, report


def import_asset_csv(
    csv_path: str | Path,
    *,
    inventory_id: str,
    generated_at: str | None = None,
    scope: str = "Customer-owned metadata import; no live targets named.",
    fixture: bool = False,
) -> dict[str, Any]:
    """Backward-compatible wrapper returning the old mapping shape."""

    inventory, report = import_asset_inventory_csv(
        csv_path,
        inventory_id=inventory_id,
        generated_at=generated_at,
        scope=scope,
        fixture=fixture,
    )
    return {"inventory": inventory, "report": report}


def build_import_manifest(
    csv_path: str | Path,
    *,
    inventory: dict[str, Any],
    report: dict[str, Any],
    inventory_path: str | Path | None = None,
    report_path: str | Path | None = None,
    seedset: dict[str, Any] | None = None,
    seedset_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a hash-only provenance manifest for a sanitized CSV import."""

    validate_asset_inventory(inventory)
    source_sha256 = _sha256_file(Path(csv_path))
    if report.get("source_csv_sha256") != source_sha256:
        raise AssetCsvImportError("report source_csv_sha256 does not match CSV input")
    emitted_at = _ensure_timestamp(
        generated_at
        or str(report.get("generated_at") or "")
        or str(inventory.get("generated_at") or "")
    )

    sanitized_outputs = {
        "inventory": _manifest_output(
            payload=inventory,
            schema_version=ASSET_SCHEMA_VERSION,
            path=inventory_path,
        ),
        "report": _manifest_output(
            payload=report,
            schema_version=REPORT_SCHEMA_VERSION,
            path=report_path,
        ),
    }
    if seedset is not None:
        sanitized_outputs["seedset"] = _manifest_output(
            payload=seedset,
            schema_version=SEEDSET_SCHEMA_VERSION,
            path=seedset_path,
        )

    manifest = {
        "schema_version": IMPORT_MANIFEST_SCHEMA_VERSION,
        "generated_at": emitted_at,
        "inventory_id": inventory["inventory_id"],
        "source": {
            "format": CSV_SCHEMA_VERSION,
            "raw_csv_sha256": source_sha256,
            "raw_csv_embedded": False,
            "raw_row_values_embedded": False,
        },
        "import_summary": {
            "accepted_row_count": report["accepted_row_count"],
            "rejected_row_count": report["rejected_row_count"],
            "total_row_count": report["total_row_count"],
        },
        "sanitized_outputs": sanitized_outputs,
        "safety_attestation": {
            "customer_owned_metadata_only": True,
            "manifest_contains_hashes_only_for_raw_input": True,
            "raw_csv_embedded": False,
            "raw_row_values_embedded": False,
            "no_collection_performed": True,
            "no_ips": True,
            "no_hostnames": True,
            "no_credentials": True,
            "no_urls": True,
            "no_payloads": True,
        },
        "manifest_body_sha256": "",
    }
    manifest["manifest_body_sha256"] = import_manifest_body_hash(manifest)
    validate_import_manifest(manifest)
    return manifest


def validate_import_manifest(manifest: dict[str, Any] | str) -> None:
    value = json.loads(manifest) if isinstance(manifest, str) else manifest
    if not isinstance(value, dict):
        raise AssetCsvImportError("asset CSV import manifest must be object")
    if value.get("schema_version") != IMPORT_MANIFEST_SCHEMA_VERSION:
        raise AssetCsvImportError(
            f"asset CSV import manifest schema_version must be {IMPORT_MANIFEST_SCHEMA_VERSION}"
        )
    _ensure_timestamp(_required_str(value, "generated_at", "asset_csv_import_manifest"))
    _required_str(value, "inventory_id", "asset_csv_import_manifest")
    source = _object(value.get("source"))
    if source.get("format") != CSV_SCHEMA_VERSION:
        raise AssetCsvImportError("asset CSV import manifest source.format is unsupported")
    if not _is_sha256(_str(source.get("raw_csv_sha256"), "")):
        raise AssetCsvImportError("asset CSV import manifest source.raw_csv_sha256 must be SHA-256")
    if source.get("raw_csv_embedded") is not False:
        raise AssetCsvImportError("asset CSV import manifest must not embed raw CSV")
    if source.get("raw_row_values_embedded") is not False:
        raise AssetCsvImportError("asset CSV import manifest must not embed raw row values")

    summary = _object(value.get("import_summary"))
    for field in ("accepted_row_count", "rejected_row_count", "total_row_count"):
        count = summary.get(field)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise AssetCsvImportError(f"asset CSV import manifest import_summary.{field} must be non-negative integer")
    if summary["accepted_row_count"] + summary["rejected_row_count"] != summary["total_row_count"]:
        raise AssetCsvImportError("asset CSV import manifest import summary counts do not add up")

    outputs = _object(value.get("sanitized_outputs"))
    for required in ("inventory", "report"):
        if required not in outputs:
            raise AssetCsvImportError(f"asset CSV import manifest missing sanitized output: {required}")
    for label, output in outputs.items():
        _validate_manifest_output(_object(output), str(label))

    safety = _object(value.get("safety_attestation"))
    for flag in (
        "customer_owned_metadata_only",
        "manifest_contains_hashes_only_for_raw_input",
        "no_collection_performed",
        "no_ips",
        "no_hostnames",
        "no_credentials",
        "no_urls",
        "no_payloads",
    ):
        if safety.get(flag) is not True:
            raise AssetCsvImportError(f"asset CSV import manifest safety_attestation.{flag} must be true")
    for flag in ("raw_csv_embedded", "raw_row_values_embedded"):
        if safety.get(flag) is not False:
            raise AssetCsvImportError(f"asset CSV import manifest safety_attestation.{flag} must be false")
    if value.get("manifest_body_sha256") != import_manifest_body_hash(value):
        raise AssetCsvImportError("asset CSV import manifest body hash does not match")


def import_manifest_body_hash(manifest: dict[str, Any]) -> str:
    body = json.loads(_canonical_json(manifest))
    body["manifest_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m assets.import_csv",
        description="Import safe customer-owned asset CSV metadata into Prophet inventory JSON.",
    )
    parser.add_argument("--csv", required=True, type=Path, help="Input asset metadata CSV")
    parser.add_argument("--inventory-id", required=True, help="Output inventory ID")
    parser.add_argument("--generated-at", help="ISO 8601 timestamp for deterministic output")
    parser.add_argument(
        "--scope",
        default="Customer-owned metadata import; no live targets named.",
        help="Inventory scope statement",
    )
    parser.add_argument("--fixture", action="store_true", help="Mark output as a fixture inventory")
    parser.add_argument("--out", "--out-inventory", dest="out_inventory", type=Path, help="Output inventory JSON")
    parser.add_argument("--report-out", "--out-report", dest="out_report", type=Path, help="Output row report JSON")
    parser.add_argument("--seedset-out", type=Path, help="Optional output asset_osint_seedset.v0.1 JSON")
    parser.add_argument("--seedset-run-id", help="Optional run ID for derived seedset")
    parser.add_argument("--manifest-out", type=Path, help="Optional output asset_csv_import_manifest.v0.1 JSON")
    args = parser.parse_args(argv)

    if not args.out_inventory:
        parser.error("--out is required")
    if not args.out_report:
        parser.error("--report-out is required")

    try:
        inventory, report = import_asset_inventory_csv(
            args.csv,
            inventory_id=args.inventory_id,
            generated_at=args.generated_at,
            scope=args.scope,
            fixture=args.fixture,
        )
        seedset: dict[str, Any] | None = None
        if args.seedset_out:
            seedset = build_asset_seedset(
                inventory,
                generated_at=args.generated_at,
                run_id=args.seedset_run_id,
            )

        args.out_inventory.parent.mkdir(parents=True, exist_ok=True)
        args.out_report.parent.mkdir(parents=True, exist_ok=True)
        args.out_inventory.write_text(_pretty_json(inventory) + "\n", encoding="utf-8")
        args.out_report.write_text(_pretty_json(report) + "\n", encoding="utf-8")
        if args.seedset_out and seedset is not None:
            write_seedset(seedset, args.seedset_out)
        if args.manifest_out:
            manifest = build_import_manifest(
                args.csv,
                inventory=inventory,
                report=report,
                inventory_path=args.out_inventory,
                report_path=args.out_report,
                seedset=seedset,
                seedset_path=args.seedset_out,
                generated_at=args.generated_at,
            )
            args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
            args.manifest_out.write_text(_pretty_json(manifest) + "\n", encoding="utf-8")
    except (OSError, csv.Error, AssetCsvImportError, AssetInventoryError) as exc:
        print(f"asset csv import failed: {_safe_error(exc)}", file=sys.stderr)
        return 1

    print(_pretty_json(report))
    return 0


def _read_rows(csv_path: Path) -> list[tuple[int, dict[str, str]]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        extra = [column for column in fieldnames if column not in REQUIRED_COLUMNS]
        if missing or extra:
            parts: list[str] = []
            if missing:
                parts.append(f"missing required columns: {', '.join(missing)}")
            if extra:
                parts.append(f"unsupported columns: {', '.join(extra)}")
            raise AssetInventoryError("CSV schema mismatch; " + "; ".join(parts))
        return [
            (index, {key: value or "" for key, value in row.items()})
            for index, row in enumerate(reader, start=2)
        ]


def _asset_from_row(row: dict[str, str]) -> dict[str, Any]:
    missing = [column for column in REQUIRED_COLUMNS if not _cell(row, column)]
    if missing:
        raise AssetCsvImportError(f"missing required values: {', '.join(missing)}")
    return {
        "asset_id": _cell(row, "asset_id"),
        "product_family": _cell(row, "product_family"),
        "exposure_class": _cell(row, "exposure_class"),
        "owner_group": _cell(row, "owner_group"),
        "environment": _cell(row, "environment"),
        "business_criticality": _cell(row, "business_criticality"),
        "sbom_components": _parse_components(_cell(row, "sbom_components")),
        "known_cve_overlaps": _split_list(_cell(row, "known_cve_overlaps")),
        "compensating_controls": _split_list(_cell(row, "compensating_controls")),
    }


def _parse_components(value: str) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    for item in _split_csv_cell(value, prefer_semicolon=True):
        if "@" in item and ":" in item:
            name_part, sep, rest = item.partition("@")
            version_part, type_sep, package_type = rest.partition(":")
            parts = [name_part.strip(), version_part.strip(), package_type.strip()]
            if not sep or not type_sep or any(not part for part in parts):
                raise AssetCsvImportError(
                    "sbom_components must use name|version_family|package_type or name@version_family:package_type entries"
                )
        else:
            parts = [part.strip() for part in item.split("|")]
        if len(parts) != 3 or any(not part for part in parts):
            raise AssetCsvImportError(
                "sbom_components must use name|version_family|package_type entries separated by semicolons"
            )
        components.append(
            {
                "name": parts[0],
                "version_family": parts[1],
                "package_type": parts[2],
            }
        )
    return components


def _split_list(value: str) -> list[str]:
    return _split_csv_cell(value)


def _split_csv_cell(value: str, *, prefer_semicolon: bool = False) -> list[str]:
    delimiter = ";"
    if ";" not in value and (not prefer_semicolon or "@" in value):
        delimiter = "|"
    return [item.strip() for item in value.split(delimiter) if item.strip()]


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _ensure_timestamp(value: str | None) -> str:
    if value:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_normalized(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _manifest_output(
    *,
    payload: dict[str, Any],
    schema_version: str,
    path: str | Path | None,
) -> dict[str, Any]:
    output = {
        "schema_version": schema_version,
        "file_sha256": _sha256_file(Path(path)) if path else "",
        "body_sha256": _sha256_normalized(payload),
    }
    if path:
        output["path"] = _safe_path_label(Path(path))
    return output


def _validate_manifest_output(output: dict[str, Any], label: str) -> None:
    if not _str(output.get("schema_version"), ""):
        raise AssetCsvImportError(f"asset CSV import manifest output {label} missing schema_version")
    file_sha256 = _str(output.get("file_sha256"), "")
    if file_sha256 and not _is_sha256(file_sha256):
        raise AssetCsvImportError(f"asset CSV import manifest output {label} file_sha256 must be SHA-256")
    if not _is_sha256(_str(output.get("body_sha256"), "")):
        raise AssetCsvImportError(f"asset CSV import manifest output {label} body_sha256 must be SHA-256")
    path = output.get("path")
    if path is not None and not isinstance(path, str):
        raise AssetCsvImportError(f"asset CSV import manifest output {label} path must be string")


def _safe_path_label(path: Path) -> str:
    normalized = str(path).replace("\\", "/").lstrip("./")
    if "/outputs/runtime/" in f"/{normalized}":
        return normalized
    return path.name or "output"


def _required_str(value: dict[str, Any], key: str, path: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise AssetCsvImportError(f"{path}.{key} must be non-empty string")
    return item.strip()


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _safe_error(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:800]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
