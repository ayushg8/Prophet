"""Policy-bound retention checks for Prophet runtime outputs.

This module covers generated runtime artifacts that are not the hash-chained
operator audit log. Audit logs keep their stricter whole-log cleanup path in
``evidence.audit retention`` so the chain is never partially pruned.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from evidence.bundle import load_policy
from policy.lint import RUNTIME_OUTPUT_PREFIXES, lint_policy_file


RUNTIME_RETENTION_SCHEMA_VERSION = "prophet_runtime_retention_report.v0.1"
DEFAULT_RUNTIME_ROOTS = tuple(prefix.rstrip("/") for prefix in RUNTIME_OUTPUT_PREFIXES)


class RuntimeRetentionError(ValueError):
    """Raised when runtime retention cannot be evaluated safely."""


def build_runtime_retention_report(
    *,
    policy_path: str | Path,
    roots: list[str | Path] | tuple[str | Path, ...] = DEFAULT_RUNTIME_ROOTS,
    repo_root: str | Path = ".",
    generated_at: str | None = None,
    delete_expired: bool = False,
    confirm_retention_delete: bool = False,
) -> dict[str, Any]:
    """Report retention status for known ignored runtime-output artifacts."""

    if delete_expired and not confirm_retention_delete:
        raise RuntimeRetentionError("runtime retention deletion requires --confirm-retention-delete")

    repo_root_path = Path(repo_root).resolve()
    policy = load_policy(policy_path)
    policy_summary = lint_policy_file(policy_path)
    emitted_at = _format_timestamp(_parse_timestamp(_ensure_timestamp(generated_at)))
    emitted_dt = _parse_timestamp(emitted_at)
    retention = _policy_retention(policy)

    scanned_roots = [_resolve_repo_path(root, repo_root_path) for root in roots]
    artifacts: list[dict[str, Any]] = []
    deleted_count = 0

    for artifact_path, rel_path in _iter_runtime_files(scanned_roots, repo_root_path):
        artifact = _artifact_retention_entry(
            artifact_path=artifact_path,
            rel_path=rel_path,
            generated_at=emitted_dt,
            retention=retention,
        )
        if (
            delete_expired
            and artifact["expired"]
            and artifact["deletion_eligible"]
            and artifact_path.exists()
        ):
            artifact_path.unlink()
            artifact["deleted"] = True
            deleted_count += 1
        artifacts.append(artifact)

    managed_artifacts = [item for item in artifacts if item["deletion_eligible"]]
    expired_managed = [item for item in managed_artifacts if item["expired"]]
    customer_metadata = [item for item in artifacts if item["retention_class"] == "customer_metadata"]
    report = {
        "schema_version": RUNTIME_RETENTION_SCHEMA_VERSION,
        "generated_at": emitted_at,
        "policy": {
            "policy_id": policy_summary["policy_id"],
            "policy_sha256": policy_summary["policy_sha256"],
        },
        "retention": {
            "runtime_outputs_max_days": retention["runtime_outputs_max_days"],
            "customer_metadata_max_days": retention["customer_metadata_max_days"],
            "audit_log_max_days": retention["audit_log_max_days"],
            "runtime_cutoff_generated_before": _format_timestamp(
                emitted_dt - timedelta(days=retention["runtime_outputs_max_days"])
            ),
            "customer_metadata_cutoff_generated_before": _format_timestamp(
                emitted_dt - timedelta(days=retention["customer_metadata_max_days"])
            ),
        },
        "scanned_roots": [rel_path for _, rel_path in scanned_roots],
        "summary": {
            "artifact_count": len(artifacts),
            "runtime_managed_artifact_count": len(managed_artifacts),
            "expired_runtime_managed_artifact_count": len(expired_managed),
            "retained_runtime_managed_artifact_count": len(managed_artifacts) - len(expired_managed),
            "customer_metadata_artifact_count": len(customer_metadata),
            "expired_customer_metadata_artifact_count": len(
                [item for item in customer_metadata if item["expired"]]
            ),
            "skipped_audit_log_count": len(
                [item for item in artifacts if item["retention_class"] == "operator_audit_log"]
            ),
            "deleted_artifact_count": deleted_count,
        },
        "cleanup": {
            "requested": delete_expired,
            "confirmed": confirm_retention_delete,
            "deleted_artifact_count": deleted_count,
            "mode": "expired runtime files only",
            "reason": (
                "expired managed artifacts removed"
                if deleted_count
                else "no expired managed artifacts removed"
            ),
        },
        "artifacts": artifacts,
        "safety_attestation": {
            "repo_runtime_paths_only": True,
            "policy_bound_retention": True,
            "customer_metadata_uses_customer_window": True,
            "audit_log_cleanup_delegated": True,
            "no_raw_artifact_bodies_embedded": True,
            "no_credentials": True,
            "no_private_hostnames": True,
            "no_live_targets": True,
            "no_live_target_data_included": True,
            "no_payloads": True,
        },
        "retention_body_sha256": "",
    }
    report["retention_body_sha256"] = runtime_retention_body_hash(report)
    validate_runtime_retention_report(report)
    return report


def validate_runtime_retention_report(report: dict[str, Any] | str) -> None:
    value = json.loads(report) if isinstance(report, str) else report
    if not isinstance(value, dict):
        raise RuntimeRetentionError("runtime retention report must be object")
    if value.get("schema_version") != RUNTIME_RETENTION_SCHEMA_VERSION:
        raise RuntimeRetentionError(
            f"runtime retention schema_version must be {RUNTIME_RETENTION_SCHEMA_VERSION}"
        )
    policy = _object(value.get("policy"))
    if not _str(policy.get("policy_id"), ""):
        raise RuntimeRetentionError("runtime retention policy.policy_id is required")
    if not _is_sha256(_str(policy.get("policy_sha256"), "")):
        raise RuntimeRetentionError("runtime retention policy.policy_sha256 must be SHA-256")

    summary = _object(value.get("summary"))
    for field in (
        "artifact_count",
        "runtime_managed_artifact_count",
        "expired_runtime_managed_artifact_count",
        "retained_runtime_managed_artifact_count",
        "customer_metadata_artifact_count",
        "expired_customer_metadata_artifact_count",
        "skipped_audit_log_count",
        "deleted_artifact_count",
    ):
        count = summary.get(field)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RuntimeRetentionError(f"runtime retention summary.{field} must be non-negative integer")
    if (
        summary["expired_runtime_managed_artifact_count"]
        + summary["retained_runtime_managed_artifact_count"]
        != summary["runtime_managed_artifact_count"]
    ):
        raise RuntimeRetentionError("runtime retention managed counts do not add up")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, list):
        raise RuntimeRetentionError("runtime retention artifacts must be list")
    if summary["artifact_count"] != len(artifacts):
        raise RuntimeRetentionError("runtime retention artifact_count does not match artifacts")
    for index, artifact in enumerate(artifacts):
        _validate_artifact_entry(_object(artifact), index)

    cleanup = _object(value.get("cleanup"))
    for field in ("requested", "confirmed"):
        if not isinstance(cleanup.get(field), bool):
            raise RuntimeRetentionError(f"runtime retention cleanup.{field} must be boolean")
    if cleanup.get("deleted_artifact_count") != summary["deleted_artifact_count"]:
        raise RuntimeRetentionError("runtime retention cleanup deleted count mismatch")

    safety = _object(value.get("safety_attestation"))
    for flag in (
        "repo_runtime_paths_only",
        "policy_bound_retention",
        "audit_log_cleanup_delegated",
        "no_raw_artifact_bodies_embedded",
        "no_credentials",
        "no_private_hostnames",
        "no_live_targets",
        "no_live_target_data_included",
        "no_payloads",
    ):
        if safety.get(flag) is not True:
            raise RuntimeRetentionError(f"runtime retention safety_attestation.{flag} must be true")

    if value.get("retention_body_sha256") != runtime_retention_body_hash(value):
        raise RuntimeRetentionError("runtime retention body hash does not match")


def runtime_retention_body_hash(report: dict[str, Any]) -> str:
    body = json.loads(_canonical_json(report))
    body["retention_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m policy.retention",
        description="Report and optionally clean policy-bound Prophet runtime outputs.",
    )
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Runtime root to scan. Defaults to all known */outputs/runtime roots.",
    )
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--generated-at", help="ISO 8601 timestamp for deterministic output")
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--delete-expired", action="store_true")
    parser.add_argument("--confirm-retention-delete", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = build_runtime_retention_report(
            policy_path=args.policy,
            roots=tuple(args.roots) if args.roots else DEFAULT_RUNTIME_ROOTS,
            repo_root=args.repo_root,
            generated_at=args.generated_at,
            delete_expired=args.delete_expired,
            confirm_retention_delete=args.confirm_retention_delete,
        )
        rendered = _pretty_json(report)
        print(rendered)
        if args.out_json:
            out_path, _ = _resolve_repo_path(args.out_json, Path(args.repo_root).resolve())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered + "\n", encoding="utf-8")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"policy retention failed: {_safe_error(exc)}", file=sys.stderr)
        return 1


def _iter_runtime_files(
    roots: list[tuple[Path, str]],
    repo_root: Path,
) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for root_path, _ in roots:
        if root_path.is_file():
            candidates = [root_path]
        elif root_path.is_dir():
            candidates = [path for path in root_path.rglob("*") if path.is_file()]
        else:
            candidates = []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            rel_path = _repo_relative_label(resolved, repo_root)
            _assert_runtime_rel_path(rel_path)
            seen.add(resolved)
            files.append((resolved, rel_path))
    return sorted(files, key=lambda item: item[1])


def _artifact_retention_entry(
    *,
    artifact_path: Path,
    rel_path: str,
    generated_at: datetime,
    retention: dict[str, int],
) -> dict[str, Any]:
    metadata = _read_artifact_metadata(artifact_path)
    retention_class = _retention_class(rel_path, metadata["schema_version"])
    max_days = retention[_retention_days_key(retention_class)]
    cutoff_dt = generated_at - timedelta(days=max_days)
    artifact_dt = metadata["artifact_generated_at"]
    expired = artifact_dt < cutoff_dt
    deletion_eligible = retention_class != "operator_audit_log"
    return {
        "path": rel_path,
        "schema_version": metadata["schema_version"],
        "file_sha256": _file_sha256(artifact_path),
        "artifact_generated_at": _format_timestamp(artifact_dt),
        "timestamp_source": metadata["timestamp_source"],
        "retention_class": retention_class,
        "retention_max_days": max_days,
        "cutoff_generated_before": _format_timestamp(cutoff_dt),
        "expired": expired,
        "deletion_eligible": deletion_eligible,
        "deleted": False,
        "cleanup_note": (
            "managed by evidence.audit retention"
            if retention_class == "operator_audit_log"
            else "managed by policy.retention"
        ),
    }


def _read_artifact_metadata(path: Path) -> dict[str, Any]:
    schema_version = ""
    artifact_generated_at: datetime | None = None
    timestamp_source = "file_mtime"
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            value = None
        if isinstance(value, dict):
            schema_version = _str(value.get("schema_version"), "")
            generated = value.get("generated_at")
            if isinstance(generated, str) and generated.strip():
                artifact_generated_at = _parse_timestamp(generated)
                timestamp_source = "artifact_generated_at"
    if artifact_generated_at is None:
        artifact_generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return {
        "schema_version": schema_version,
        "artifact_generated_at": artifact_generated_at,
        "timestamp_source": timestamp_source,
    }


def _retention_class(rel_path: str, schema_version: str) -> str:
    if rel_path.endswith(".jsonl") and "audit" in rel_path:
        return "operator_audit_log"
    if rel_path.startswith("assets/outputs/runtime/") or schema_version in {
        "asset_inventory.v0.1",
        "asset_osint_seedset.v0.1",
        "asset_csv_import_report.v0.1",
        "asset_csv_import_manifest.v0.1",
    }:
        return "customer_metadata"
    return "runtime_output"


def _retention_days_key(retention_class: str) -> str:
    if retention_class == "customer_metadata":
        return "customer_metadata_max_days"
    if retention_class == "operator_audit_log":
        return "audit_log_max_days"
    return "runtime_outputs_max_days"


def _policy_retention(policy: dict[str, Any]) -> dict[str, int]:
    value = _object(policy.get("retention"))
    out: dict[str, int] = {}
    limits = {
        "runtime_outputs_max_days": 90,
        "customer_metadata_max_days": 90,
        "audit_log_max_days": 365,
    }
    for field, max_days in limits.items():
        days = value.get(field)
        if isinstance(days, bool) or not isinstance(days, int) or days < 1 or days > max_days:
            raise RuntimeRetentionError(f"policy.retention.{field} must be integer days between 1 and {max_days}")
        out[field] = days
    return out


def _resolve_repo_path(path: str | Path, repo_root: Path) -> tuple[Path, str]:
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()
    rel_path = _repo_relative_label(resolved, repo_root)
    _assert_runtime_rel_path(rel_path)
    return resolved, rel_path


def _repo_relative_label(path: Path, repo_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise RuntimeRetentionError(f"runtime path must stay under repo root: {path}") from exc
    if ".." in rel.parts:
        raise RuntimeRetentionError(f"runtime path must not contain '..': {path}")
    return rel.as_posix()


def _assert_runtime_rel_path(rel_path: str) -> None:
    if rel_path in DEFAULT_RUNTIME_ROOTS:
        return
    if any(rel_path.startswith(prefix) for prefix in RUNTIME_OUTPUT_PREFIXES):
        return
    allowed = ", ".join(RUNTIME_OUTPUT_PREFIXES)
    raise RuntimeRetentionError(f"runtime retention path must stay under: {allowed}")


def _validate_artifact_entry(artifact: dict[str, Any], index: int) -> None:
    path = _str(artifact.get("path"), "")
    if not path:
        raise RuntimeRetentionError(f"runtime retention artifacts[{index}].path is required")
    _assert_runtime_rel_path(path)
    if not _is_sha256(_str(artifact.get("file_sha256"), "")):
        raise RuntimeRetentionError(f"runtime retention artifacts[{index}].file_sha256 must be SHA-256")
    if artifact.get("retention_class") not in {
        "runtime_output",
        "customer_metadata",
        "operator_audit_log",
    }:
        raise RuntimeRetentionError(f"runtime retention artifacts[{index}].retention_class is unsupported")
    for field in ("expired", "deletion_eligible", "deleted"):
        if not isinstance(artifact.get(field), bool):
            raise RuntimeRetentionError(f"runtime retention artifacts[{index}].{field} must be boolean")
    max_days = artifact.get("retention_max_days")
    if isinstance(max_days, bool) or not isinstance(max_days, int) or max_days < 1:
        raise RuntimeRetentionError(f"runtime retention artifacts[{index}].retention_max_days must be positive integer")
    _parse_timestamp(_str(artifact.get("artifact_generated_at"), ""))
    _parse_timestamp(_str(artifact.get("cutoff_generated_before"), ""))


def _ensure_timestamp(value: str | None) -> str:
    if value:
        _parse_timestamp(value)
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    if not value:
        raise RuntimeRetentionError("timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


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


if __name__ == "__main__":
    raise SystemExit(main())
