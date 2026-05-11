#!/usr/bin/env python3
"""Generate a machine-readable Prophet supply-chain review artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


SCHEMA_VERSION = "prophet_supply_chain_sbom.v0.1"
CHECK_SCHEMA_VERSION = "prophet_supply_chain_sbom_check.v0.1"
DEFAULT_OUTPUT = Path("evidence/outputs/runtime/supply-chain/prophet-supply-chain-sbom.json")
PACKAGE_JSON = Path("prophet-console/package.json")
PACKAGE_LOCK = Path("prophet-console/package-lock.json")
SCRAPER_REQUIREMENTS = Path("world-side/scraper/requirements.txt")
ALLOWED_RUNTIME_ROOTS = {
    ("assets", "outputs", "runtime"),
    ("cyber-side", "outputs", "runtime"),
    ("evidence", "outputs", "runtime"),
    ("integrations", "outputs", "runtime"),
    ("world-side", "outputs", "runtime"),
}
PROHIBITED_REQUIREMENT_TOKENS = (
    "://",
    "--index-url",
    "--extra-index-url",
    "--find-links",
    "--trusted-host",
    "--client-cert",
    "--cert",
)


class SupplyChainSbomError(ValueError):
    """Raised when the SBOM review artifact cannot be generated safely."""


def build_supply_chain_sbom(
    *,
    root: Path,
    generated_at: str | None = None,
    package_json_path: Path = PACKAGE_JSON,
    package_lock_path: Path = PACKAGE_LOCK,
    scraper_requirements_path: Path = SCRAPER_REQUIREMENTS,
) -> dict[str, Any]:
    package_json_abs = root / package_json_path
    package_lock_abs = root / package_lock_path
    scraper_requirements_abs = root / scraper_requirements_path
    package_json = _load_json(package_json_abs)
    package_lock = _load_json(package_lock_abs)
    requirements = _parse_requirements(scraper_requirements_abs)
    source_paths = [
        _source_hash(root, package_json_path),
        _source_hash(root, package_lock_path),
        _source_hash(root, scraper_requirements_path),
    ]
    direct_runtime = dict(package_json.get("dependencies") or {})
    direct_development = dict(package_json.get("devDependencies") or {})
    npm_components = _npm_components(
        package_lock=package_lock,
        direct_runtime=direct_runtime,
        direct_development=direct_development,
    )
    requirement_components = [
        _python_requirement_component(requirement)
        for requirement in requirements
    ]
    components = [
        _first_party_component(root),
        _python_stdlib_component(),
        *npm_components,
        *requirement_components,
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_from": {
            "git_commit": _git(["rev-parse", "HEAD"], root=root),
            "git_branch": _git(["branch", "--show-current"], root=root),
            "dirty_worktree": bool(_git(["status", "--short", "--untracked-files=no"], root=root)),
            "source_paths": source_paths,
        },
        "review_boundary": {
            "purpose": "buyer/security review for the local Prophet buyer pilot",
            "output_policy": "generated artifact should stay under ignored outputs/runtime/ paths unless a release owner explicitly publishes it",
            "non_claims": [
                "not a SLSA attestation",
                "not a FedRAMP artifact",
                "not a SOC 2 report",
                "not a CMMC certification artifact",
                "not evidence of production SaaS readiness",
            ],
        },
        "summary": {
            "component_count": len(components),
            "npm_component_count": len(npm_components),
            "direct_runtime_dependency_count": len(direct_runtime),
            "direct_development_dependency_count": len(direct_development),
            "scraper_requirement_count": len(requirements),
            "python_product_dependency_model": "stdlib plus checked-in first-party modules",
        },
        "components": components,
        "limitations": [
            "No committed CycloneDX or SPDX release artifact is produced by this script.",
            "The isolated scraper requirements file is intentionally empty until scraper code lands.",
            "Generated output is a review inventory for the local buyer pilot, not a production provenance attestation.",
            "Public release tagging remains blocked until the historical secret-history owner decision is recorded.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a safe machine-readable supply-chain review artifact."
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="Output path under an ignored */outputs/runtime/ directory.",
    )
    parser.add_argument(
        "--check",
        help="Validate an existing generated artifact under an ignored */outputs/runtime/ directory instead of writing one.",
    )
    parser.add_argument(
        "--require-date",
        help="Require the existing artifact's generated_at field to match this date or timestamp.",
    )
    parser.add_argument(
        "--date",
        help="Generation timestamp/date to record. Use YYYY-MM-DD or an ISO timestamp.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.check:
            require_date = _normalize_generated_at(args.require_date)
            summary = check_supply_chain_sbom(
                root=root,
                artifact_path=Path(args.check),
                require_date=require_date,
            )
            rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        else:
            generated_at = _normalize_generated_at(args.date)
            sbom = build_supply_chain_sbom(root=root, generated_at=generated_at)
            out_path = _safe_output_path(root, Path(args.out))
            rendered = json.dumps(sbom, indent=2, sort_keys=True) + "\n"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
    except (OSError, json.JSONDecodeError, SupplyChainSbomError) as exc:
        action = "check" if args.check else "generation"
        print(f"supply-chain SBOM {action} failed: {exc}", file=sys.stderr)
        return 1
    print(rendered, end="")
    return 0


def check_supply_chain_sbom(
    *,
    root: Path,
    artifact_path: Path,
    require_date: str | None = None,
) -> dict[str, Any]:
    safe_path = _safe_output_path(root, artifact_path)
    artifact = _load_json(safe_path)
    _require_equal(artifact.get("schema_version"), SCHEMA_VERSION, "schema_version")
    generated_at = artifact.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        raise SupplyChainSbomError("generated_at must be a non-empty string")
    if require_date is not None and generated_at != require_date:
        raise SupplyChainSbomError(
            f"generated_at {generated_at!r} does not match required date {require_date!r}"
        )

    generated_from = _require_object(artifact.get("generated_from"), "generated_from")
    source_paths = _require_list(generated_from.get("source_paths"), "generated_from.source_paths")
    checked_sources = _check_source_hashes(root, source_paths)

    components = _require_list(artifact.get("components"), "components")
    summary = _require_object(artifact.get("summary"), "summary")
    review_boundary = _require_object(artifact.get("review_boundary"), "review_boundary")
    non_claims = _require_list(review_boundary.get("non_claims"), "review_boundary.non_claims")
    limitations = _require_list(artifact.get("limitations"), "limitations")

    component_count = len(components)
    npm_count = sum(1 for component in components if _component_field(component, "ecosystem") == "npm")
    direct_runtime_count = sum(
        1 for component in components if _component_field(component, "scope") == "direct_runtime"
    )
    direct_development_count = sum(
        1 for component in components if _component_field(component, "scope") == "direct_development"
    )
    _require_equal(summary.get("component_count"), component_count, "summary.component_count")
    _require_equal(summary.get("npm_component_count"), npm_count, "summary.npm_component_count")
    _require_equal(
        summary.get("direct_runtime_dependency_count"),
        direct_runtime_count,
        "summary.direct_runtime_dependency_count",
    )
    _require_equal(
        summary.get("direct_development_dependency_count"),
        direct_development_count,
        "summary.direct_development_dependency_count",
    )
    _require_contains(non_claims, "not a CMMC certification artifact", "review_boundary.non_claims")
    _require_contains(non_claims, "not evidence of production SaaS readiness", "review_boundary.non_claims")
    _require_contains(
        limitations,
        "Public release tagging remains blocked until the historical secret-history owner decision is recorded.",
        "limitations",
    )

    return {
        "schema_version": CHECK_SCHEMA_VERSION,
        "ok": True,
        "artifact_path": safe_path.relative_to(root).as_posix(),
        "generated_at": generated_at,
        "recorded_git_commit": generated_from.get("git_commit"),
        "current_git_commit": _git(["rev-parse", "HEAD"], root=root),
        "recorded_dirty_worktree": bool(generated_from.get("dirty_worktree")),
        "component_count": component_count,
        "npm_component_count": npm_count,
        "source_path_count": len(checked_sources),
        "source_hashes_match": True,
        "review_boundary": review_boundary,
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SupplyChainSbomError(f"{path} must contain a JSON object")
    return value


def _source_hash(root: Path, rel_path: Path) -> dict[str, str]:
    path = root / rel_path
    return {
        "path": rel_path.as_posix(),
        "sha256": _sha256(path),
    }


def _check_source_hashes(root: Path, source_paths: list[Any]) -> list[dict[str, str]]:
    checked: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for index, source in enumerate(source_paths):
        if not isinstance(source, dict):
            raise SupplyChainSbomError(f"generated_from.source_paths[{index}] must be an object")
        rel_path = source.get("path")
        recorded_hash = source.get("sha256")
        if not isinstance(rel_path, str) or not rel_path:
            raise SupplyChainSbomError(f"generated_from.source_paths[{index}].path must be a non-empty string")
        if not isinstance(recorded_hash, str) or len(recorded_hash) != 64:
            raise SupplyChainSbomError(f"generated_from.source_paths[{index}].sha256 must be a SHA-256 hex string")
        if rel_path.startswith("/") or ".." in Path(rel_path).parts:
            raise SupplyChainSbomError(f"generated_from.source_paths[{index}].path must stay inside the repository")
        actual_hash = _sha256(root / rel_path)
        if actual_hash != recorded_hash:
            raise SupplyChainSbomError(
                f"source hash mismatch for {rel_path}: artifact is stale for the current source file"
            )
        checked.append({"path": rel_path, "sha256": recorded_hash})
        seen_paths.add(rel_path)
    expected_paths = {
        PACKAGE_JSON.as_posix(),
        PACKAGE_LOCK.as_posix(),
        SCRAPER_REQUIREMENTS.as_posix(),
    }
    missing = sorted(expected_paths - seen_paths)
    if missing:
        raise SupplyChainSbomError(f"generated_from.source_paths is missing required source path(s): {', '.join(missing)}")
    return checked


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _npm_components(
    *,
    package_lock: dict[str, Any],
    direct_runtime: dict[str, str],
    direct_development: dict[str, str],
) -> list[dict[str, Any]]:
    packages = package_lock.get("packages")
    if not isinstance(packages, dict):
        raise SupplyChainSbomError("package-lock packages must be an object")
    components: list[dict[str, Any]] = []
    for path, metadata in sorted(packages.items()):
        if not path.startswith("node_modules/"):
            continue
        if not isinstance(metadata, dict):
            raise SupplyChainSbomError(f"package-lock metadata for {path} must be an object")
        name = _npm_name(path, metadata)
        version = metadata.get("version")
        if not isinstance(version, str) or not version:
            continue
        component: dict[str, Any] = {
            "type": "library",
            "ecosystem": "npm",
            "name": name,
            "version": version,
            "scope": _npm_scope(name, direct_runtime, direct_development),
            "path": path,
            "purl": f"pkg:npm/{quote(name, safe='@/')}@{quote(version, safe='')}",
        }
        license_value = metadata.get("license")
        if isinstance(license_value, str) and license_value:
            component["license"] = license_value
        integrity = metadata.get("integrity")
        if isinstance(integrity, str) and integrity:
            component["integrity"] = integrity
        components.append(component)
    return components


def _npm_name(path: str, metadata: dict[str, Any]) -> str:
    name = metadata.get("name")
    if isinstance(name, str) and name:
        return name
    return path.rsplit("node_modules/", maxsplit=1)[-1]


def _npm_scope(name: str, direct_runtime: dict[str, str], direct_development: dict[str, str]) -> str:
    if name in direct_runtime:
        return "direct_runtime"
    if name in direct_development:
        return "direct_development"
    return "transitive"


def _parse_requirements(path: Path) -> list[str]:
    requirements: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lowered = line.lower()
        if any(token in lowered for token in PROHIBITED_REQUIREMENT_TOKENS):
            raise SupplyChainSbomError(
                f"{path}:{line_number} contains a prohibited index, URL, or credential-bearing requirement"
            )
        requirements.append(line)
    return requirements


def _python_requirement_component(requirement: str) -> dict[str, str]:
    name = requirement
    version_spec = ""
    for delimiter in ("==", ">=", "<=", "~=", "!=", ">", "<"):
        if delimiter in requirement:
            name, version_spec = requirement.split(delimiter, maxsplit=1)
            version_spec = delimiter + version_spec
            break
    name = name.strip()
    return {
        "type": "library",
        "ecosystem": "python",
        "name": name,
        "version_spec": version_spec.strip(),
        "scope": "isolated_scraper",
        "path": SCRAPER_REQUIREMENTS.as_posix(),
        "purl": f"pkg:pypi/{quote(name.lower(), safe='._-')}",
    }


def _first_party_component(root: Path) -> dict[str, str]:
    commit = _git(["rev-parse", "HEAD"], root=root)
    return {
        "type": "application",
        "ecosystem": "first-party",
        "name": "Prophet",
        "version": commit[:12] if commit else "unknown",
        "scope": "local_buyer_pilot",
        "path": ".",
    }


def _python_stdlib_component() -> dict[str, str]:
    return {
        "type": "platform",
        "ecosystem": "python",
        "name": "python-stdlib",
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "scope": "product_python_path",
        "path": "stdlib",
    }


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SupplyChainSbomError(f"{field_name} must be an object")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise SupplyChainSbomError(f"{field_name} must be a list")
    return value


def _require_equal(actual: Any, expected: Any, field_name: str) -> None:
    if actual != expected:
        raise SupplyChainSbomError(f"{field_name} mismatch: expected {expected!r}, got {actual!r}")


def _require_contains(values: list[Any], expected: str, field_name: str) -> None:
    if expected not in values:
        raise SupplyChainSbomError(f"{field_name} must include {expected!r}")


def _component_field(component: Any, field_name: str) -> Any:
    if not isinstance(component, dict):
        raise SupplyChainSbomError("components must contain only objects")
    return component.get(field_name)


def _git(args: list[str], *, root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def _normalize_generated_at(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        raise SupplyChainSbomError("--date must not be empty")
    if len(value) == 10:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise SupplyChainSbomError("--date must be YYYY-MM-DD or an ISO timestamp") from exc
        return value
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SupplyChainSbomError("--date must be YYYY-MM-DD or an ISO timestamp") from exc
    return value


def _safe_output_path(root: Path, raw_path: Path) -> Path:
    path = raw_path if raw_path.is_absolute() else root / raw_path
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SupplyChainSbomError("--out must stay inside the repository") from exc
    parts = relative.parts
    if len(parts) < 3 or tuple(parts[:3]) not in ALLOWED_RUNTIME_ROOTS:
        raise SupplyChainSbomError("--out must be under an ignored */outputs/runtime/ directory")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
