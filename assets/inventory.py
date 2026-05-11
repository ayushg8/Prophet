"""Validate asset inventories and derive safe OSINT seedsets.

Asset inventories are customer-owned or fictional context. The seedset derived
from them is intentionally metadata-only: CVE IDs, package families, product
families, exposure classes, and owner queues. It does not perform collection and
does not contain addresses, hostnames, secrets, or target names.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ASSET_SCHEMA_VERSION = "asset_inventory.v0.1"
SEEDSET_SCHEMA_VERSION = "asset_osint_seedset.v0.1"

RECOMMENDED_SOURCE_IDS = (
    "cveproject_cvelistv5_delta_log",
    "cisa_vulnrichment_cve_record_seed",
    "osv_query_api_seed",
    "redhat_security_data_cve_api",
)

REQUIRED_INVENTORY_ASSET_FIELDS = (
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

REQUIRED_COMPONENT_FIELDS = ("name", "version_family", "package_type")

SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./+-]{0,120}$")
CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOSTNAME_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|mil|gov|edu|io|dev|local|lan|internal|corp)\b",
    re.IGNORECASE,
)
SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|token)\s*[:=])",
    re.IGNORECASE,
)
LIVE_NAME_RE = re.compile(
    r"\b(?:prod-[a-z0-9-]+|corp-[a-z0-9-]+|dc\d+|srv\d+|host\d+)\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"\b(?:https?|ssh|ftp)://", re.IGNORECASE)
UNSAFE_KEYS = {
    "hostname",
    "hostnames",
    "ip",
    "ip_address",
    "credential",
    "credentials",
    "username",
    "password",
    "payload",
    "payloads",
    "procedure",
    "procedures",
    "command",
    "commands",
}


class AssetInventoryError(ValueError):
    """Raised when an asset inventory or seedset violates the safe contract."""


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssetInventoryError(f"{file_path} must decode to a JSON object")
    return value


def validate_asset_inventory(inventory: dict[str, Any] | str) -> None:
    """Validate an asset inventory fixture/customer context file."""

    value = json.loads(inventory) if isinstance(inventory, str) else inventory
    if not isinstance(value, dict):
        raise AssetInventoryError("asset inventory must be an object")
    _scan_safe(value, "asset_inventory")
    if value.get("schema_version") != ASSET_SCHEMA_VERSION:
        raise AssetInventoryError(f"schema_version must be {ASSET_SCHEMA_VERSION}")
    _required_str(value, "inventory_id", "asset_inventory")
    _validate_iso(_required_str(value, "generated_at", "asset_inventory"), "generated_at")
    _required_str(value, "scope", "asset_inventory")
    if not isinstance(value.get("fixture"), bool):
        raise AssetInventoryError("asset_inventory.fixture must be boolean")

    assets = value.get("assets")
    if not isinstance(assets, list) or not assets:
        raise AssetInventoryError("asset_inventory.assets must be a non-empty list")
    seen_assets: set[str] = set()
    for idx, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise AssetInventoryError(f"assets[{idx}] must be object")
        for field in REQUIRED_INVENTORY_ASSET_FIELDS:
            if field not in asset:
                raise AssetInventoryError(f"assets[{idx}] missing {field}")
        asset_id = _required_str(asset, "asset_id", f"assets[{idx}]")
        if asset_id in seen_assets:
            raise AssetInventoryError(f"duplicate asset_id: {asset_id}")
        seen_assets.add(asset_id)
        for field in ("product_family", "exposure_class", "owner_group", "environment", "business_criticality"):
            _safe_label(_required_str(asset, field, f"assets[{idx}]"), f"assets[{idx}].{field}")
        _validate_components(asset["sbom_components"], f"assets[{idx}].sbom_components")
        _validate_cve_list(asset["known_cve_overlaps"], f"assets[{idx}].known_cve_overlaps")
        _validate_string_list(
            asset["compensating_controls"],
            f"assets[{idx}].compensating_controls",
            allow_empty=True,
        )


def build_asset_seedset(
    inventory: dict[str, Any],
    *,
    generated_at: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic safe OSINT seedset from an asset inventory."""

    validate_asset_inventory(inventory)
    emitted_at = _ensure_timestamp(generated_at)
    assets = [asset for asset in inventory["assets"] if isinstance(asset, dict)]
    inventory_id = _str(inventory.get("inventory_id"), "unknown-inventory")
    seed = run_id or f"{inventory_id}:{emitted_at}"
    seedset_id = f"asset-seedset-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    exposure_seeds = _build_exposure_seeds(assets)
    product_family_seeds = _build_product_family_seeds(assets)
    package_seeds = _build_package_seeds(assets)
    cve_seeds = _build_cve_seeds(assets)
    owner_queues = _build_owner_queues(assets)

    seedset: dict[str, Any] = {
        "schema_version": SEEDSET_SCHEMA_VERSION,
        "seedset_id": seedset_id,
        "generated_at": emitted_at,
        "input_refs": {
            "inventory_id": inventory_id,
            "inventory_schema_version": _str(inventory.get("schema_version"), ASSET_SCHEMA_VERSION),
            "asset_count": len(assets),
            "run_id": run_id or seedset_id,
        },
        "fixture_context": bool(inventory.get("fixture", True)),
        "scope_statement": _str(
            inventory.get("scope"),
            "Fixture/customer-owned asset context only; no live systems named.",
        ),
        "exposure_class_seeds": exposure_seeds,
        "product_family_seeds": product_family_seeds,
        "package_seeds": package_seeds,
        "cve_seeds": cve_seeds,
        "owner_queues": owner_queues,
        "recommended_source_ids": list(RECOMMENDED_SOURCE_IDS),
        "query_hints": {
            "cve_ids": [item["cve_id"] for item in cve_seeds],
            "package_names": [item["package_name"] for item in package_seeds],
            "product_families": [item["product_family"] for item in product_family_seeds],
            "exposure_classes": [item["exposure_class"] for item in exposure_seeds],
        },
        "safety_attestation": {
            "fixture_or_customer_owned": True,
            "sector_level_only": True,
            "no_ips": True,
            "no_hostnames": True,
            "no_secret_material": True,
            "no_live_target_names": True,
            "no_collection_performed": True,
        },
        "hashes": {
            "asset_inventory_sha256": _sha256_normalized(inventory),
            "seedset_body_sha256": "",
        },
    }
    digest = _seedset_body_sha256(seedset)
    seedset["hashes"]["seedset_body_sha256"] = digest
    seedset["seedset_sha256"] = digest
    validate_asset_seedset(seedset)
    return seedset


def validate_asset_seedset(seedset: dict[str, Any] | str) -> None:
    """Validate a safe, metadata-only OSINT seedset."""

    value = json.loads(seedset) if isinstance(seedset, str) else seedset
    if not isinstance(value, dict):
        raise AssetInventoryError("asset seedset must be an object")
    _scan_safe(value, "asset_seedset")
    for field in (
        "schema_version",
        "seedset_id",
        "generated_at",
        "input_refs",
        "fixture_context",
        "scope_statement",
        "exposure_class_seeds",
        "product_family_seeds",
        "package_seeds",
        "cve_seeds",
        "owner_queues",
        "recommended_source_ids",
        "query_hints",
        "safety_attestation",
        "hashes",
        "seedset_sha256",
    ):
        if field not in value:
            raise AssetInventoryError(f"asset seedset missing {field}")
    if value["schema_version"] != SEEDSET_SCHEMA_VERSION:
        raise AssetInventoryError(f"schema_version must be {SEEDSET_SCHEMA_VERSION}")
    _validate_iso(_required_str(value, "generated_at", "asset_seedset"), "generated_at")
    if not isinstance(value["input_refs"], dict):
        raise AssetInventoryError("asset_seedset.input_refs must be object")
    asset_count = value["input_refs"].get("asset_count")
    if isinstance(asset_count, bool) or not isinstance(asset_count, int) or asset_count < 1:
        raise AssetInventoryError("asset_seedset.input_refs.asset_count must be positive integer")
    if not isinstance(value["fixture_context"], bool):
        raise AssetInventoryError("asset_seedset.fixture_context must be boolean")

    _validate_seed_list(value["exposure_class_seeds"], "exposure_class_seeds", "exposure_class")
    _validate_seed_list(value["product_family_seeds"], "product_family_seeds", "product_family")
    _validate_seed_list(value["package_seeds"], "package_seeds", "package_name")
    for idx, item in enumerate(_required_list(value["cve_seeds"], "cve_seeds")):
        if not isinstance(item, dict):
            raise AssetInventoryError(f"cve_seeds[{idx}] must be object")
        cve_id = _required_str(item, "cve_id", f"cve_seeds[{idx}]")
        if not CVE_RE.fullmatch(cve_id):
            raise AssetInventoryError(f"cve_seeds[{idx}].cve_id must be CVE-yyyy-nnnn")
    _validate_seed_list(value["owner_queues"], "owner_queues", "owner_group")
    _validate_string_list(value["recommended_source_ids"], "recommended_source_ids", allow_empty=False)

    safety = value["safety_attestation"]
    if not isinstance(safety, dict):
        raise AssetInventoryError("asset_seedset.safety_attestation must be object")
    for flag in (
        "fixture_or_customer_owned",
        "sector_level_only",
        "no_ips",
        "no_hostnames",
        "no_secret_material",
        "no_live_target_names",
        "no_collection_performed",
    ):
        if safety.get(flag) is not True:
            raise AssetInventoryError(f"asset_seedset.safety_attestation.{flag} must be true")

    hashes = value["hashes"]
    if not isinstance(hashes, dict):
        raise AssetInventoryError("asset_seedset.hashes must be object")
    if not _is_sha256(_str(hashes.get("asset_inventory_sha256"), "")):
        raise AssetInventoryError("asset_seedset.hashes.asset_inventory_sha256 must be SHA-256")
    expected = _seedset_body_sha256(value)
    if value["seedset_sha256"] != expected:
        raise AssetInventoryError("asset_seedset.seedset_sha256 does not match body")
    if hashes.get("seedset_body_sha256") != expected:
        raise AssetInventoryError("asset_seedset.hashes.seedset_body_sha256 does not match body")


def summarize_asset_seedset(seedset: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary safe for forecasts, evidence, and UI surfaces."""

    validate_asset_seedset(seedset)
    exposure_classes = [
        _str(item.get("exposure_class"), "")
        for item in seedset.get("exposure_class_seeds", [])
        if isinstance(item, dict)
    ]
    product_families = [
        _str(item.get("product_family"), "")
        for item in seedset.get("product_family_seeds", [])
        if isinstance(item, dict)
    ]
    owner_groups = [
        _str(item.get("owner_group"), "")
        for item in seedset.get("owner_queues", [])
        if isinstance(item, dict)
    ]
    return {
        "seedset_id": _str(seedset.get("seedset_id"), "unknown-seedset"),
        "schema_version": SEEDSET_SCHEMA_VERSION,
        "fixture_context": bool(seedset.get("fixture_context", True)),
        "asset_count": _int(_object(seedset.get("input_refs")).get("asset_count")),
        "exposure_classes": [item for item in exposure_classes if item],
        "product_families": [item for item in product_families if item],
        "package_seed_count": len(seedset.get("package_seeds") or []),
        "cve_seed_count": len(seedset.get("cve_seeds") or []),
        "recommended_source_ids": list(seedset.get("recommended_source_ids") or []),
        "owner_queues": [item for item in owner_groups if item],
        "seedset_sha256": _str(seedset.get("seedset_sha256"), ""),
        "basis_statement": (
            "Asset/SBOM-derived seeds identify CVE, package, product-family, "
            "and exposure-class metadata for targeted open-source enrichment."
        ),
    }


def write_seedset(seedset: dict[str, Any], out_path: str | Path) -> None:
    """Write a seedset JSON file."""

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_pretty_json(seedset) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        inventory = load_json(args.inventory)
        seedset = build_asset_seedset(
            inventory,
            generated_at=args.generated_at,
            run_id=args.run_id,
        )
        if args.out:
            write_seedset(seedset, args.out)
        else:
            print(_pretty_json(seedset))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"assets.inventory: {_safe_error(exc)}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m assets.inventory",
        description="Validate an asset inventory and emit a safe OSINT seedset.",
    )
    parser.add_argument("--inventory", required=True, type=Path, help="asset_inventory.v0.1 JSON")
    parser.add_argument("--generated-at", help="ISO 8601 timestamp for deterministic output")
    parser.add_argument("--run-id", help="Explicit seedset run id")
    parser.add_argument("--out", type=Path, help="Output asset_osint_seedset.v0.1 JSON path")
    return parser


def _build_exposure_seeds(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        grouped.setdefault(_str(asset.get("exposure_class"), "unknown"), []).append(asset)
    out: list[dict[str, Any]] = []
    for exposure_class, group in sorted(grouped.items()):
        out.append(
            {
                "exposure_class": exposure_class,
                "asset_count": len(group),
                "owner_groups": _unique(_str(asset.get("owner_group"), "") for asset in group),
                "business_criticality_counts": _count_values(
                    _str(asset.get("business_criticality"), "unknown") for asset in group
                ),
            }
        )
    return out


def _build_product_family_seeds(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        grouped.setdefault(_str(asset.get("product_family"), "unknown"), []).append(asset)
    out: list[dict[str, Any]] = []
    for product_family, group in sorted(grouped.items()):
        out.append(
            {
                "product_family": product_family,
                "asset_count": len(group),
                "exposure_classes": _unique(_str(asset.get("exposure_class"), "") for asset in group),
                "owner_groups": _unique(_str(asset.get("owner_group"), "") for asset in group),
            }
        )
    return out


def _build_package_seeds(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for asset in assets:
        for component in asset.get("sbom_components") or []:
            if not isinstance(component, dict):
                continue
            key = (
                _str(component.get("name"), "unknown"),
                _str(component.get("version_family"), "unknown"),
                _str(component.get("package_type"), "unknown"),
            )
            item = grouped.setdefault(
                key,
                {
                    "package_name": key[0],
                    "version_family": key[1],
                    "package_type": key[2],
                    "asset_count": 0,
                    "owner_groups": set(),
                    "known_cve_overlaps": set(),
                },
            )
            item["asset_count"] += 1
            item["owner_groups"].add(_str(asset.get("owner_group"), ""))
            for cve_id in asset.get("known_cve_overlaps") or []:
                item["known_cve_overlaps"].add(str(cve_id))
    out: list[dict[str, Any]] = []
    for item in grouped.values():
        out.append(
            {
                "package_name": item["package_name"],
                "version_family": item["version_family"],
                "package_type": item["package_type"],
                "asset_count": item["asset_count"],
                "owner_groups": sorted(owner for owner in item["owner_groups"] if owner),
                "known_cve_overlaps": sorted(item["known_cve_overlaps"]),
            }
        )
    return sorted(out, key=lambda item: (item["package_name"], item["version_family"]))


def _build_cve_seeds(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for asset in assets:
        components = [
            _str(component.get("name"), "")
            for component in asset.get("sbom_components") or []
            if isinstance(component, dict)
        ]
        for cve_id in asset.get("known_cve_overlaps") or []:
            cve = str(cve_id).strip().upper()
            item = grouped.setdefault(
                cve,
                {
                    "cve_id": cve,
                    "affected_asset_count": 0,
                    "product_families": set(),
                    "package_names": set(),
                    "owner_groups": set(),
                    "exposure_classes": set(),
                },
            )
            item["affected_asset_count"] += 1
            item["product_families"].add(_str(asset.get("product_family"), ""))
            item["owner_groups"].add(_str(asset.get("owner_group"), ""))
            item["exposure_classes"].add(_str(asset.get("exposure_class"), ""))
            item["package_names"].update(component for component in components if component)
    out: list[dict[str, Any]] = []
    for item in grouped.values():
        out.append(
            {
                "cve_id": item["cve_id"],
                "affected_asset_count": item["affected_asset_count"],
                "product_families": sorted(value for value in item["product_families"] if value),
                "package_names": sorted(value for value in item["package_names"] if value),
                "owner_groups": sorted(value for value in item["owner_groups"] if value),
                "exposure_classes": sorted(value for value in item["exposure_classes"] if value),
            }
        )
    return sorted(out, key=lambda item: item["cve_id"])


def _build_owner_queues(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        grouped.setdefault(_str(asset.get("owner_group"), "unknown"), []).append(asset)
    out: list[dict[str, Any]] = []
    for owner_group, group in sorted(grouped.items()):
        cve_ids: list[str] = []
        package_names: list[str] = []
        for asset in group:
            cve_ids.extend(str(cve) for cve in asset.get("known_cve_overlaps") or [])
            package_names.extend(
                _str(component.get("name"), "")
                for component in asset.get("sbom_components") or []
                if isinstance(component, dict)
            )
        out.append(
            {
                "owner_group": owner_group,
                "asset_count": len(group),
                "criticality_counts": _count_values(
                    _str(asset.get("business_criticality"), "unknown") for asset in group
                ),
                "cve_ids": sorted(set(cve_ids)),
                "package_names": sorted({name for name in package_names if name}),
                "recommended_source_ids": list(RECOMMENDED_SOURCE_IDS),
            }
        )
    return out


def _validate_components(value: Any, path: str) -> None:
    components = _required_list(value, path)
    if not components:
        raise AssetInventoryError(f"{path} must be non-empty")
    for idx, component in enumerate(components):
        if not isinstance(component, dict):
            raise AssetInventoryError(f"{path}[{idx}] must be object")
        for field in REQUIRED_COMPONENT_FIELDS:
            _safe_label(_required_str(component, field, f"{path}[{idx}]"), f"{path}[{idx}].{field}")


def _validate_cve_list(value: Any, path: str) -> None:
    items = _validate_string_list(value, path, allow_empty=True)
    for item in items:
        if not CVE_RE.fullmatch(item):
            raise AssetInventoryError(f"{path} contains invalid CVE id: {item}")


def _validate_string_list(value: Any, path: str, *, allow_empty: bool) -> list[str]:
    items = _required_list(value, path)
    if not allow_empty and not items:
        raise AssetInventoryError(f"{path} must be non-empty")
    out: list[str] = []
    for idx, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise AssetInventoryError(f"{path}[{idx}] must be non-empty string")
        _safe_label(item.strip(), f"{path}[{idx}]")
        out.append(item.strip())
    return out


def _validate_seed_list(value: Any, path: str, label_key: str) -> None:
    items = _required_list(value, path)
    if not items:
        raise AssetInventoryError(f"{path} must be non-empty")
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise AssetInventoryError(f"{path}[{idx}] must be object")
        _safe_label(_required_str(item, label_key, f"{path}[{idx}]"), f"{path}[{idx}].{label_key}")
        asset_count = item.get("asset_count") or item.get("affected_asset_count")
        if isinstance(asset_count, bool) or not isinstance(asset_count, int) or asset_count < 1:
            raise AssetInventoryError(f"{path}[{idx}] asset count must be positive integer")


def _scan_safe(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in UNSAFE_KEYS:
                raise AssetInventoryError(f"{path} contains unsafe key: {key}")
            _scan_safe(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_safe(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        _scan_safe_text(value, path)


def _scan_safe_text(value: str, path: str) -> None:
    if IP_RE.search(value):
        raise AssetInventoryError(f"{path} contains IP-like text")
    if EMAIL_RE.search(value):
        raise AssetInventoryError(f"{path} contains email-like text")
    if HOSTNAME_RE.search(value):
        raise AssetInventoryError(f"{path} contains hostname-like text")
    if SECRET_RE.search(value):
        raise AssetInventoryError(f"{path} contains secret-like text")
    if URL_RE.search(value):
        raise AssetInventoryError(f"{path} contains URL-like text")
    if LIVE_NAME_RE.search(value):
        raise AssetInventoryError(f"{path} contains live-target-like name")


def _safe_label(value: str, path: str) -> None:
    if len(value) > 160:
        raise AssetInventoryError(f"{path} must stay under 160 characters")
    if not SAFE_LABEL_RE.fullmatch(value):
        raise AssetInventoryError(f"{path} contains unsupported characters")
    _scan_safe_text(value, path)


def _required_str(value: dict[str, Any], key: str, path: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise AssetInventoryError(f"{path}.{key} must be non-empty string")
    return item.strip()


def _required_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise AssetInventoryError(f"{path} must be list")
    return value


def _validate_iso(value: str, path: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AssetInventoryError(f"{path} must be ISO 8601") from exc


def _ensure_timestamp(value: str | None) -> str:
    if value:
        _validate_iso(value, "generated_at")
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _seedset_body_sha256(seedset: dict[str, Any]) -> str:
    body = copy.deepcopy(seedset)
    body.pop("seedset_sha256", None)
    if isinstance(body.get("hashes"), dict):
        body["hashes"].pop("seedset_body_sha256", None)
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _sha256_normalized(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        label = str(value or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def _unique(values: Any) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    return value if isinstance(value, int) else 0


def _str(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[a-f0-9]{64}", value))


def _safe_error(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:800]


if __name__ == "__main__":
    raise SystemExit(main())
