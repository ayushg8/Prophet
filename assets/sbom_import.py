"""Import sanitized SBOM JSON into Prophet's safe asset inventory shape.

The importer accepts fixture/customer-approved CycloneDX and SPDX JSON only. It
extracts package-family metadata, CVE IDs, and hash-only source provenance. It
does not ingest raw telemetry, resolve package URLs, collect data, or preserve
targetable customer identifiers.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import sys
from typing import Any

from assets.inventory import (
    ASSET_SCHEMA_VERSION,
    AssetInventoryError,
    build_asset_seedset,
    validate_asset_inventory,
    write_seedset,
)


REPORT_SCHEMA_VERSION = "asset_sbom_import_report.v0.1"
CYCLONEDX_FORMAT = "cyclonedx-json"
SPDX_FORMAT = "spdx-json"
SUPPORTED_FORMATS = {CYCLONEDX_FORMAT, SPDX_FORMAT}

CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./+-]{0,120}$")
PURL_RE = re.compile(r"^pkg:([A-Za-z0-9.+_-]+)/(.+)$")
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
URL_RE = re.compile(r"\b(?:https?|ssh|ftp)://", re.IGNORECASE)
SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|token)\s*[:=])",
    re.IGNORECASE,
)
LIVE_NAME_RE = re.compile(
    r"\b(?:prod-[a-z0-9-]+|corp-[a-z0-9-]+|dc\d+|srv\d+|host\d+)\b",
    re.IGNORECASE,
)
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

PURL_PACKAGE_TYPE = {
    "apk": "linux-package",
    "cargo": "rust-crate",
    "deb": "linux-package",
    "gem": "ruby-gem",
    "golang": "go-module",
    "maven": "java-library",
    "npm": "npm-package",
    "nuget": "dotnet-package",
    "pypi": "python-package",
    "rpm": "linux-package",
}


class AssetSbomImportError(ValueError):
    """Raised when an SBOM cannot be parsed into safe asset metadata."""


def import_asset_inventory_sbom(
    sbom_path: str | Path,
    *,
    inventory_id: str,
    product_family: str,
    exposure_class: str,
    owner_group: str,
    environment: str,
    business_criticality: str,
    asset_id: str | None = None,
    generated_at: str | None = None,
    scope: str = "Customer-approved sanitized SBOM metadata; no live targets named.",
    fixture: bool = False,
    sbom_format: str = "auto",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a safe inventory and import report for a sanitized SBOM JSON file."""

    emitted_at = _ensure_timestamp(generated_at)
    path = Path(sbom_path)
    source_sha256 = _sha256_file(path)
    sbom = _load_safe_sbom_json(path)
    detected_format = _detect_format(sbom, sbom_format)
    parsed = _parse_sbom(sbom, detected_format)

    if not parsed["components"]:
        raise AssetSbomImportError("SBOM import produced no safe components")

    asset = {
        "asset_id": asset_id or f"{inventory_id}-asset-001",
        "product_family": product_family,
        "exposure_class": exposure_class,
        "owner_group": owner_group,
        "environment": environment,
        "business_criticality": business_criticality,
        "sbom_components": parsed["components"],
        "known_cve_overlaps": parsed["known_cve_overlaps"],
        "compensating_controls": [
            "customer-approved metadata review",
            "policy-bound evidence packet review",
        ],
    }
    inventory = {
        "schema_version": ASSET_SCHEMA_VERSION,
        "inventory_id": inventory_id,
        "generated_at": emitted_at,
        "fixture": fixture,
        "scope": scope,
        "source_format": detected_format,
        "source_sbom_sha256": source_sha256,
        "import_summary": {
            "component_count": len(parsed["components"]),
            "deduplicated_component_count": parsed["deduplicated_component_count"],
            "known_cve_overlap_count": len(parsed["known_cve_overlaps"]),
        },
        "assets": [asset],
    }
    validate_asset_inventory(inventory)

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": emitted_at,
        "inventory_id": inventory_id,
        "source_format": detected_format,
        "source_sbom_sha256": source_sha256,
        "raw_sbom_embedded": False,
        "raw_component_values_embedded": False,
        "component_count": len(parsed["components"]),
        "deduplicated_component_count": parsed["deduplicated_component_count"],
        "known_cve_overlap_count": len(parsed["known_cve_overlaps"]),
        "package_type_counts": _count_values(component["package_type"] for component in parsed["components"]),
        "accepted_package_names": [component["name"] for component in parsed["components"]],
        "known_cve_overlaps": parsed["known_cve_overlaps"],
        "safety_attestation": {
            "customer_approved_sanitized_sbom_only": True,
            "hash_only_raw_sbom_provenance": True,
            "raw_sbom_embedded": False,
            "raw_component_values_embedded": False,
            "no_collection_performed": True,
            "no_ips": True,
            "no_hostnames": True,
            "no_credentials": True,
            "no_urls": True,
            "no_payloads": True,
        },
    }
    return inventory, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m assets.sbom_import",
        description="Import sanitized CycloneDX/SPDX SBOM JSON into Prophet inventory JSON.",
    )
    parser.add_argument("--sbom", required=True, type=Path, help="Input sanitized SBOM JSON")
    parser.add_argument("--inventory-id", required=True, help="Output inventory ID")
    parser.add_argument("--asset-id", help="Optional output asset ID")
    parser.add_argument("--format", default="auto", choices=("auto", "cyclonedx", "spdx"), help="Input SBOM format")
    parser.add_argument("--product-family", required=True, help="Safe product-family label")
    parser.add_argument("--exposure-class", required=True, help="Safe exposure-class label")
    parser.add_argument("--owner-group", required=True, help="Safe owner queue label")
    parser.add_argument("--environment", required=True, help="Safe environment class label")
    parser.add_argument("--business-criticality", required=True, help="Safe criticality label")
    parser.add_argument("--generated-at", help="ISO 8601 timestamp for deterministic output")
    parser.add_argument(
        "--scope",
        default="Customer-approved sanitized SBOM metadata; no live targets named.",
        help="Inventory scope statement",
    )
    parser.add_argument("--fixture", action="store_true", help="Mark output as a fixture inventory")
    parser.add_argument("--out", "--out-inventory", dest="out_inventory", type=Path, help="Output inventory JSON")
    parser.add_argument("--report-out", "--out-report", dest="out_report", type=Path, help="Output report JSON")
    parser.add_argument("--seedset-out", type=Path, help="Optional output asset_osint_seedset.v0.1 JSON")
    parser.add_argument("--seedset-run-id", help="Optional run ID for derived seedset")
    args = parser.parse_args(argv)

    if not args.out_inventory:
        parser.error("--out is required")
    if not args.out_report:
        parser.error("--report-out is required")

    try:
        inventory, report = import_asset_inventory_sbom(
            args.sbom,
            inventory_id=args.inventory_id,
            asset_id=args.asset_id,
            product_family=args.product_family,
            exposure_class=args.exposure_class,
            owner_group=args.owner_group,
            environment=args.environment,
            business_criticality=args.business_criticality,
            generated_at=args.generated_at,
            scope=args.scope,
            fixture=args.fixture,
            sbom_format=args.format,
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
    except (OSError, json.JSONDecodeError, AssetSbomImportError, AssetInventoryError) as exc:
        print(f"asset sbom import failed: {_safe_error(exc)}", file=sys.stderr)
        return 1

    print(_pretty_json(report))
    return 0


def _parse_sbom(sbom: dict[str, Any], sbom_format: str) -> dict[str, Any]:
    if sbom_format == CYCLONEDX_FORMAT:
        components = _parse_cyclonedx_components(sbom)
        cves = _parse_cyclonedx_cves(sbom)
    elif sbom_format == SPDX_FORMAT:
        components = _parse_spdx_components(sbom)
        cves = _parse_spdx_cves(sbom)
    else:
        raise AssetSbomImportError("unsupported SBOM format")
    deduped = _dedupe_components(components)
    return {
        "components": deduped,
        "deduplicated_component_count": len(components) - len(deduped),
        "known_cve_overlaps": sorted(set(cves)),
    }


def _parse_cyclonedx_components(sbom: dict[str, Any]) -> list[dict[str, str]]:
    raw_components = sbom.get("components")
    if not isinstance(raw_components, list):
        raise AssetSbomImportError("CycloneDX SBOM components must be a list")
    components: list[dict[str, str]] = []
    for idx, item in enumerate(raw_components):
        if not isinstance(item, dict):
            raise AssetSbomImportError(f"CycloneDX components[{idx}] must be object")
        components.append(_component_from_fields(item.get("name"), item.get("version"), item.get("type"), item.get("purl")))
    return components


def _parse_cyclonedx_cves(sbom: dict[str, Any]) -> list[str]:
    out: list[str] = []
    vulnerabilities = sbom.get("vulnerabilities") or []
    if not isinstance(vulnerabilities, list):
        raise AssetSbomImportError("CycloneDX vulnerabilities must be a list when present")
    for item in vulnerabilities:
        if not isinstance(item, dict):
            continue
        out.extend(_extract_cves(item.get("id")))
        out.extend(_extract_cves(item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else None))
    return out


def _parse_spdx_components(sbom: dict[str, Any]) -> list[dict[str, str]]:
    raw_packages = sbom.get("packages")
    if not isinstance(raw_packages, list):
        raise AssetSbomImportError("SPDX SBOM packages must be a list")
    components: list[dict[str, str]] = []
    for idx, item in enumerate(raw_packages):
        if not isinstance(item, dict):
            raise AssetSbomImportError(f"SPDX packages[{idx}] must be object")
        purl = _spdx_package_purl(item)
        components.append(_component_from_fields(item.get("name"), item.get("versionInfo"), "library", purl))
    return components


def _parse_spdx_cves(sbom: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for package in sbom.get("packages") or []:
        if isinstance(package, dict):
            out.extend(_extract_cves(package.get("comment")))
            for ref in package.get("externalRefs") or []:
                if isinstance(ref, dict):
                    out.extend(_extract_cves(ref.get("referenceLocator")))
    for annotation in sbom.get("annotations") or []:
        if isinstance(annotation, dict):
            out.extend(_extract_cves(annotation.get("comment")))
    return out


def _component_from_fields(name: Any, version: Any, package_type: Any, purl: Any) -> dict[str, str]:
    purl_text = _str_or_empty(purl)
    purl_data = _parse_purl(purl_text) if purl_text else {}
    component_name = _safe_component_label(_str_or_empty(name) or _str_or_empty(purl_data.get("name")), "component.name")
    version_family = _safe_component_label(
        _version_family(_str_or_empty(version) or _str_or_empty(purl_data.get("version"))),
        "component.version_family",
    )
    package_label = _safe_component_label(
        _package_type(_str_or_empty(package_type), _str_or_empty(purl_data.get("type"))),
        "component.package_type",
    )
    return {
        "name": component_name,
        "version_family": version_family,
        "package_type": package_label,
    }


def _spdx_package_purl(package: dict[str, Any]) -> str:
    refs = package.get("externalRefs") or []
    if not isinstance(refs, list):
        return ""
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        locator = _str_or_empty(ref.get("referenceLocator"))
        if locator.startswith("pkg:"):
            return locator
    return ""


def _parse_purl(value: str) -> dict[str, str]:
    match = PURL_RE.fullmatch(value.strip())
    if not match:
        return {}
    purl_type = match.group(1).lower()
    body = match.group(2).split("?", 1)[0].split("#", 1)[0]
    path_part, _, version = body.rpartition("@")
    if not path_part:
        path_part = body
        version = ""
    name = path_part.rstrip("/").rsplit("/", 1)[-1]
    return {"type": purl_type, "name": name, "version": version}


def _package_type(raw_type: str, purl_type: str) -> str:
    normalized_purl = purl_type.lower().strip()
    if normalized_purl in PURL_PACKAGE_TYPE:
        return PURL_PACKAGE_TYPE[normalized_purl]
    raw = raw_type.lower().strip()
    if raw in {"application", "framework"}:
        return raw
    if raw in {"library", "container", "operating-system"}:
        return raw
    return "library"


def _version_family(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or cleaned.upper() in {"NOASSERTION", "NONE", "UNKNOWN"}:
        return "unknown"
    lowered = cleaned.lower()
    if "x" in lowered or "family" in lowered or "legacy" in lowered or "lts" in lowered:
        return _labelize(cleaned)
    match = re.match(r"^v?(\d+)(?:[._-]\d+.*)?$", cleaned)
    if match:
        return f"{match.group(1)}.x"
    return _labelize(cleaned)


def _dedupe_components(components: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for component in components:
        key = (component["name"], component["version_family"], component["package_type"])
        if key in seen:
            continue
        seen.add(key)
        out.append(component)
    return sorted(out, key=lambda item: (item["name"], item["version_family"], item["package_type"]))


def _detect_format(sbom: dict[str, Any], requested: str) -> str:
    if requested == "cyclonedx":
        _require_cyclonedx(sbom)
        return CYCLONEDX_FORMAT
    if requested == "spdx":
        _require_spdx(sbom)
        return SPDX_FORMAT
    if requested != "auto":
        raise AssetSbomImportError("unsupported SBOM format request")
    if sbom.get("bomFormat") == "CycloneDX":
        _require_cyclonedx(sbom)
        return CYCLONEDX_FORMAT
    if _str_or_empty(sbom.get("spdxVersion")).startswith("SPDX-2."):
        _require_spdx(sbom)
        return SPDX_FORMAT
    raise AssetSbomImportError("SBOM format must be CycloneDX JSON or SPDX 2.x JSON")


def _require_cyclonedx(sbom: dict[str, Any]) -> None:
    if sbom.get("bomFormat") != "CycloneDX":
        raise AssetSbomImportError("CycloneDX SBOM must set bomFormat to CycloneDX")
    spec = _str_or_empty(sbom.get("specVersion"))
    if not spec:
        raise AssetSbomImportError("CycloneDX SBOM must include specVersion")


def _require_spdx(sbom: dict[str, Any]) -> None:
    if not _str_or_empty(sbom.get("spdxVersion")).startswith("SPDX-2."):
        raise AssetSbomImportError("SPDX SBOM must use SPDX-2.x")


def _load_safe_sbom_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    _scan_raw_sbom(raw)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise AssetSbomImportError("SBOM JSON must decode to an object")
    _scan_safe_value(value, "sbom")
    return value


def _scan_raw_sbom(raw: str) -> None:
    if IP_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains IP-like text")
    if EMAIL_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains email-like text")
    if URL_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains URL-like text")
    if HOSTNAME_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains hostname-like text")
    if SECRET_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains secret-like text")
    if LIVE_NAME_RE.search(raw):
        raise AssetSbomImportError("SBOM input contains live-target-like text")


def _scan_safe_value(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in UNSAFE_KEYS:
                raise AssetSbomImportError(f"{path} contains unsafe key: {key}")
            _scan_safe_value(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_safe_value(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        _scan_raw_sbom(value)


def _safe_component_label(value: str, path: str) -> str:
    cleaned = _labelize(value)
    if not cleaned:
        raise AssetSbomImportError(f"{path} must be non-empty")
    if len(cleaned) > 120:
        raise AssetSbomImportError(f"{path} must stay under 120 characters")
    if not SAFE_LABEL_RE.fullmatch(cleaned):
        raise AssetSbomImportError(f"{path} contains unsupported characters")
    _scan_raw_sbom(cleaned)
    return cleaned


def _extract_cves(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [match.group(0).upper() for match in CVE_RE.finditer(value)]


def _count_values(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        if isinstance(value, str) and value:
            out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def _labelize(value: str) -> str:
    cleaned = value.strip().replace("|", "-").replace(":", "-").replace("@", "-")
    return re.sub(r"\s+", " ", cleaned)


def _ensure_timestamp(value: str | None) -> str:
    if value:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _str_or_empty(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_error(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:800]


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
