"""Append and validate local Prophet operator audit events.

The audit log is intentionally local, append-only, and hash-chained. It is not a
replacement for production signing or SIEM retention, but it gives paid-pilot
evaluators a concrete approval trail without introducing auth complexity.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from evidence.bundle import load_policy


AUDIT_SCHEMA_VERSION = "prophet_operator_audit_event.v0.1"
LOG_SCHEMA_VERSION = "prophet_operator_audit_log.v0.1"
AUDIT_EXPORT_SCHEMA_VERSION = "prophet_operator_audit_export.v0.1"
AUDIT_RETENTION_SCHEMA_VERSION = "prophet_operator_audit_retention.v0.1"
NO_LIVE_TARGET_DATA_ASSERTION = (
    "No live target data is included; audit artifacts contain only local "
    "operator labels, policy hashes, artifact IDs, and output hashes."
)

ALLOWED_EVENT_TYPES = {
    "operator_approval",
    "operator_denial",
    "integration_handoff_exported",
    "sandbox_artifact_generated",
}
ALLOWED_DECISIONS = {
    "approved",
    "denied",
    "bypassed_for_fixture",
    "integration_handoff_exported",
    "sandbox_artifact_generated",
}
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./+-]{0,120}$")
IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
HOSTNAME_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|mil|gov|edu|io|dev|local|lan|internal|corp)\b",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|token)\s*[:=])",
    re.IGNORECASE,
)


class AuditLogError(ValueError):
    """Raised when an audit event or log violates the local audit contract."""


def build_audit_event(
    *,
    event_type: str,
    operator_label: str,
    decision: str,
    policy: dict[str, Any],
    generated_at: str | None = None,
    run_id: str | None = None,
    artifact_id: str | None = None,
    bundle_id: str | None = None,
    bundle_sha256: str | None = None,
    export_id: str | None = None,
    previous_event_hash: str | None = None,
    reason: str = "fixture-approved pilot workflow",
) -> dict[str, Any]:
    """Build a hash-chained local audit event."""

    if event_type not in ALLOWED_EVENT_TYPES:
        raise AuditLogError(f"unsupported audit event_type: {event_type}")
    if decision not in ALLOWED_DECISIONS:
        raise AuditLogError(f"unsupported audit decision: {decision}")
    _safe_label(operator_label, "operator_label")
    _safe_label(reason, "reason")
    if previous_event_hash is not None and not _is_sha256(previous_event_hash):
        raise AuditLogError("previous_event_hash must be SHA-256 or null")
    emitted_at = _ensure_timestamp(generated_at)
    policy_id = _safe_policy_id(policy)
    policy_sha256 = _sha256_normalized(policy)
    event_seed = "\n".join(
        [
            event_type,
            operator_label,
            decision,
            policy_id,
            previous_event_hash or "",
            run_id or "",
            emitted_at,
        ]
    )
    event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_id": f"pae-{hashlib.sha256(event_seed.encode('utf-8')).hexdigest()[:16]}",
        "event_type": event_type,
        "generated_at": emitted_at,
        "operator": {
            "label": operator_label,
            "identity_mode": "local_label",
            "identity_provider": "prophet-local-control",
        },
        "decision": decision,
        "reason": reason,
        "policy": {
            "policy_id": policy_id,
            "policy_sha256": policy_sha256,
        },
        "refs": {
            "run_id": run_id or "",
            "artifact_id": artifact_id or "",
            "bundle_id": bundle_id or "",
            "bundle_sha256": bundle_sha256 or "",
            "export_id": export_id or "",
        },
        "chain": {
            "log_schema_version": LOG_SCHEMA_VERSION,
            "previous_event_hash": previous_event_hash,
            "event_body_sha256": "",
        },
        "safety_attestation": {
            "local_runtime_log_only": True,
            "no_credentials": True,
            "no_private_hostnames": True,
            "no_live_targets": True,
            "no_live_target_data_included": True,
            "no_payloads": True,
            "data_boundary_statement": NO_LIVE_TARGET_DATA_ASSERTION,
        },
    }
    event["chain"]["event_body_sha256"] = audit_event_body_hash(event)
    event["event_hash"] = audit_event_body_hash(event)
    validate_audit_event(event)
    return event


def append_audit_event(
    log_path: str | Path,
    *,
    event_type: str,
    operator_label: str,
    decision: str,
    policy: dict[str, Any],
    generated_at: str | None = None,
    run_id: str | None = None,
    artifact_id: str | None = None,
    bundle_id: str | None = None,
    bundle_sha256: str | None = None,
    export_id: str | None = None,
    reason: str = "fixture-approved pilot workflow",
    reset_log: bool = False,
) -> dict[str, Any]:
    """Append an event to a local JSONL audit log and return the event."""

    path = Path(log_path)
    _assert_runtime_log_path(path)
    if reset_log and path.exists():
        path.unlink()
    previous_hash = _last_event_hash(path)
    event = build_audit_event(
        event_type=event_type,
        operator_label=operator_label,
        decision=decision,
        policy=policy,
        generated_at=generated_at,
        run_id=run_id,
        artifact_id=artifact_id,
        bundle_id=bundle_id,
        bundle_sha256=bundle_sha256,
        export_id=export_id,
        previous_event_hash=previous_hash,
        reason=reason,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(event) + "\n")
    validate_audit_log(path)
    return event


def validate_audit_event(event: dict[str, Any] | str) -> None:
    value = json.loads(event) if isinstance(event, str) else event
    if not isinstance(value, dict):
        raise AuditLogError("audit event must be object")
    _scan_safe(value, "audit_event")
    if value.get("schema_version") != AUDIT_SCHEMA_VERSION:
        raise AuditLogError(f"schema_version must be {AUDIT_SCHEMA_VERSION}")
    if value.get("event_type") not in ALLOWED_EVENT_TYPES:
        raise AuditLogError("audit event_type is unsupported")
    if value.get("decision") not in ALLOWED_DECISIONS:
        raise AuditLogError("audit decision is unsupported")
    operator = _object(value.get("operator"))
    _safe_label(_str(operator.get("label"), ""), "operator.label")
    policy = _object(value.get("policy"))
    if not _str(policy.get("policy_id"), ""):
        raise AuditLogError("audit policy.policy_id is required")
    if not _is_sha256(_str(policy.get("policy_sha256"), "")):
        raise AuditLogError("audit policy.policy_sha256 must be SHA-256")
    refs = _object(value.get("refs"))
    bundle_sha = _str(refs.get("bundle_sha256"), "")
    if bundle_sha and not _is_sha256(bundle_sha):
        raise AuditLogError("audit refs.bundle_sha256 must be SHA-256 when present")
    chain = _object(value.get("chain"))
    previous = chain.get("previous_event_hash")
    if previous is not None and not _is_sha256(_str(previous, "")):
        raise AuditLogError("audit chain.previous_event_hash must be SHA-256 or null")
    expected = audit_event_body_hash(value)
    if chain.get("event_body_sha256") != expected:
        raise AuditLogError("audit chain.event_body_sha256 does not match event body")
    if value.get("event_hash") != expected:
        raise AuditLogError("audit event_hash does not match event body")
    _validate_safety_attestation(value, "audit event")


def validate_audit_log(log_path: str | Path) -> dict[str, Any]:
    path = Path(log_path)
    events = _read_events(path)
    previous: str | None = None
    for index, event in enumerate(events):
        validate_audit_event(event)
        actual_previous = _object(event.get("chain")).get("previous_event_hash")
        if actual_previous != previous:
            raise AuditLogError(f"audit log chain break at event {index + 1}")
        previous = _str(event.get("event_hash"), "")
    return {
        "ok": True,
        "schema_version": LOG_SCHEMA_VERSION,
        "path": str(path),
        "event_count": len(events),
        "latest_event_hash": previous,
    }


def export_audit_log(
    log_path: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a safe security-review summary for a local audit log."""

    path = Path(log_path)
    _assert_runtime_log_path(path)
    log_summary = validate_audit_log(path)
    events = _read_events(path)
    event_summaries = [_audit_event_summary(event) for event in events]
    event_type_counts = Counter(_str(event.get("event_type"), "") for event in events)
    decision_counts = Counter(_str(event.get("decision"), "") for event in events)
    policies = [_object(event.get("policy")) for event in events]
    export = {
        "schema_version": AUDIT_EXPORT_SCHEMA_VERSION,
        "generated_at": _ensure_timestamp(generated_at),
        "source_log_path": str(path),
        "source_log_sha256": _file_sha256(path),
        "log_schema_version": LOG_SCHEMA_VERSION,
        "event_count": log_summary["event_count"],
        "first_event_hash": event_summaries[0]["event_hash"] if event_summaries else None,
        "latest_event_hash": log_summary["latest_event_hash"],
        "event_type_counts": dict(sorted(event_type_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "policy_ids": sorted({_str(policy.get("policy_id"), "") for policy in policies if policy}),
        "policy_sha256s": sorted({_str(policy.get("policy_sha256"), "") for policy in policies if policy}),
        "operator_labels": sorted(
            {
                _str(_object(event.get("operator")).get("label"), "")
                for event in events
                if _object(event.get("operator")).get("label")
            }
        ),
        "redaction_report": _audit_redaction_report(event_summaries),
        "events": event_summaries,
        "safety_attestation": {
            "local_runtime_log_only": True,
            "summary_export_only": True,
            "no_credentials": True,
            "no_private_hostnames": True,
            "no_live_targets": True,
            "no_live_target_data_included": True,
            "no_payloads": True,
            "data_boundary_statement": NO_LIVE_TARGET_DATA_ASSERTION,
        },
        "export_body_sha256": "",
    }
    export["export_body_sha256"] = audit_export_body_hash(export)
    validate_audit_export(export)
    return export


def audit_retention_report(
    log_path: str | Path,
    *,
    policy: dict[str, Any],
    generated_at: str | None = None,
    delete_expired_log: bool = False,
    confirm_retention_delete: bool = False,
) -> dict[str, Any]:
    """Report audit-log retention status and optionally delete a fully expired log."""

    path = Path(log_path)
    _assert_runtime_log_path(path)
    if delete_expired_log and not confirm_retention_delete:
        raise AuditLogError("retention deletion requires --confirm-retention-delete")

    events = _read_events(path)
    log_summary = validate_audit_log(path)
    source_log_sha256 = _file_sha256(path)
    generated_at_value = _format_timestamp(_parse_timestamp(_ensure_timestamp(generated_at)))
    generated_at_dt = _parse_timestamp(generated_at_value)
    max_days = _audit_log_max_days(policy)
    cutoff_dt = generated_at_dt - timedelta(days=max_days)
    event_datetimes = [_parse_timestamp(_str(event.get("generated_at"), "")) for event in events]
    expired_events = [dt for dt in event_datetimes if dt < cutoff_dt]
    retained_events = [dt for dt in event_datetimes if dt >= cutoff_dt]
    latest_event_dt = max(event_datetimes) if event_datetimes else None
    latest_event_expired = latest_event_dt is not None and latest_event_dt < cutoff_dt

    if not events:
        cleanup_reason = "audit log has no events"
    elif latest_event_expired:
        cleanup_reason = "latest audit event is older than policy retention window"
    elif expired_events:
        cleanup_reason = "some events are expired, but the active hash chain is still retained"
    else:
        cleanup_reason = "audit log is within policy retention window"

    deleted = False
    if delete_expired_log and latest_event_expired and path.exists():
        path.unlink()
        deleted = True

    report = {
        "schema_version": AUDIT_RETENTION_SCHEMA_VERSION,
        "generated_at": generated_at_value,
        "source_log_path": str(path),
        "source_log_sha256": source_log_sha256,
        "log_schema_version": LOG_SCHEMA_VERSION,
        "policy": {
            "policy_id": _safe_policy_id(policy),
            "policy_sha256": _sha256_normalized(policy),
        },
        "retention": {
            "audit_log_max_days": max_days,
            "cutoff_generated_before": _format_timestamp(cutoff_dt),
            "event_count": log_summary["event_count"],
            "expired_event_count": len(expired_events),
            "retained_event_count": len(retained_events),
            "oldest_event_at": _format_timestamp(min(event_datetimes)) if event_datetimes else None,
            "latest_event_at": _format_timestamp(latest_event_dt) if latest_event_dt else None,
            "latest_event_expired": latest_event_expired,
        },
        "cleanup": {
            "eligible": latest_event_expired,
            "requested": delete_expired_log,
            "confirmed": confirm_retention_delete,
            "deleted": deleted,
            "reason": cleanup_reason,
        },
        "safety_attestation": {
            "local_runtime_log_only": True,
            "policy_bound_retention": True,
            "whole_log_cleanup_only": True,
            "no_credentials": True,
            "no_private_hostnames": True,
            "no_live_targets": True,
            "no_live_target_data_included": True,
            "no_payloads": True,
            "data_boundary_statement": NO_LIVE_TARGET_DATA_ASSERTION,
        },
        "retention_body_sha256": "",
    }
    report["retention_body_sha256"] = audit_retention_body_hash(report)
    validate_audit_retention_report(report)
    return report


def validate_audit_export(export: dict[str, Any] | str) -> None:
    value = json.loads(export) if isinstance(export, str) else export
    if not isinstance(value, dict):
        raise AuditLogError("audit export must be object")
    _scan_safe(value, "audit_export")
    if value.get("schema_version") != AUDIT_EXPORT_SCHEMA_VERSION:
        raise AuditLogError(f"audit export schema_version must be {AUDIT_EXPORT_SCHEMA_VERSION}")
    if not _is_sha256(_str(value.get("source_log_sha256"), "")):
        raise AuditLogError("audit export source_log_sha256 must be SHA-256")
    latest = value.get("latest_event_hash")
    if latest is not None and not _is_sha256(_str(latest, "")):
        raise AuditLogError("audit export latest_event_hash must be SHA-256 or null")
    first = value.get("first_event_hash")
    if first is not None and not _is_sha256(_str(first, "")):
        raise AuditLogError("audit export first_event_hash must be SHA-256 or null")
    events = value.get("events")
    if not isinstance(events, list):
        raise AuditLogError("audit export events must be list")
    if value.get("event_count") != len(events):
        raise AuditLogError("audit export event_count does not match events")
    redaction = _object(value.get("redaction_report"))
    if not redaction:
        raise AuditLogError("audit export redaction_report is required")
    for field in (
        "summary_fields_only",
        "source_log_embedded",
        "raw_event_bodies_embedded",
        "operator_review_required",
    ):
        if not isinstance(redaction.get(field), bool):
            raise AuditLogError(f"audit export redaction_report.{field} must be boolean")
    if redaction.get("summary_fields_only") is not True:
        raise AuditLogError("audit export redaction_report.summary_fields_only must be true")
    if redaction.get("source_log_embedded") is not False:
        raise AuditLogError("audit export redaction_report.source_log_embedded must be false")
    if redaction.get("raw_event_bodies_embedded") is not False:
        raise AuditLogError(
            "audit export redaction_report.raw_event_bodies_embedded must be false"
        )
    if redaction.get("operator_review_required") is not True:
        raise AuditLogError(
            "audit export redaction_report.operator_review_required must be true"
        )
    if redaction.get("event_summaries_emitted") != len(events):
        raise AuditLogError(
            "audit export redaction_report.event_summaries_emitted does not match events"
        )
    for field in ("field_allowlist", "redacted_fields", "blocked_text_classes"):
        items = redaction.get(field)
        if not isinstance(items, list) or not items:
            raise AuditLogError(f"audit export redaction_report.{field} must be non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in items):
            raise AuditLogError(
                f"audit export redaction_report.{field} must contain non-empty strings"
            )
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise AuditLogError(f"audit export events[{index}] must be object")
        if not _is_sha256(_str(event.get("event_hash"), "")):
            raise AuditLogError(f"audit export events[{index}].event_hash must be SHA-256")
        previous = event.get("previous_event_hash")
        if previous is not None and not _is_sha256(_str(previous, "")):
            raise AuditLogError(
                f"audit export events[{index}].previous_event_hash must be SHA-256 or null"
            )
    expected = audit_export_body_hash(value)
    if value.get("export_body_sha256") != expected:
        raise AuditLogError("audit export_body_sha256 does not match export body")
    _validate_safety_attestation(value, "audit export")


def validate_audit_retention_report(report: dict[str, Any] | str) -> None:
    value = json.loads(report) if isinstance(report, str) else report
    if not isinstance(value, dict):
        raise AuditLogError("audit retention report must be object")
    _scan_safe(value, "audit_retention")
    if value.get("schema_version") != AUDIT_RETENTION_SCHEMA_VERSION:
        raise AuditLogError(
            f"audit retention schema_version must be {AUDIT_RETENTION_SCHEMA_VERSION}"
        )
    if not _is_sha256(_str(value.get("source_log_sha256"), "")):
        raise AuditLogError("audit retention source_log_sha256 must be SHA-256")
    policy = _object(value.get("policy"))
    _safe_label(_str(policy.get("policy_id"), ""), "audit_retention.policy.policy_id")
    if not _is_sha256(_str(policy.get("policy_sha256"), "")):
        raise AuditLogError("audit retention policy.policy_sha256 must be SHA-256")
    retention = _object(value.get("retention"))
    for field in (
        "audit_log_max_days",
        "event_count",
        "expired_event_count",
        "retained_event_count",
    ):
        item = retention.get(field)
        if not isinstance(item, int) or item < 0:
            raise AuditLogError(f"audit retention.{field} must be non-negative integer")
    if retention["expired_event_count"] + retention["retained_event_count"] != retention["event_count"]:
        raise AuditLogError("audit retention counts do not add up")
    cleanup = _object(value.get("cleanup"))
    for field in ("eligible", "requested", "confirmed", "deleted"):
        if not isinstance(cleanup.get(field), bool):
            raise AuditLogError(f"audit retention cleanup.{field} must be boolean")
    expected = audit_retention_body_hash(value)
    if value.get("retention_body_sha256") != expected:
        raise AuditLogError("audit retention_body_sha256 does not match report body")
    _validate_safety_attestation(value, "audit retention")


def audit_export_body_hash(export: dict[str, Any]) -> str:
    body = json.loads(_canonical_json(export))
    body["export_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def audit_retention_body_hash(report: dict[str, Any]) -> str:
    body = json.loads(_canonical_json(report))
    body["retention_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def audit_event_body_hash(event: dict[str, Any]) -> str:
    body = json.loads(_canonical_json(event))
    body.pop("event_hash", None)
    if isinstance(body.get("chain"), dict):
        body["chain"]["event_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m evidence.audit",
        description="Append or validate local Prophet operator audit events.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    append_parser = subparsers.add_parser("append", help="Append a local audit event")
    append_parser.add_argument("--log", required=True, type=Path)
    append_parser.add_argument("--policy", required=True, type=Path)
    append_parser.add_argument("--event-type", required=True, choices=sorted(ALLOWED_EVENT_TYPES))
    append_parser.add_argument("--operator-label", required=True)
    append_parser.add_argument("--decision", required=True, choices=sorted(ALLOWED_DECISIONS))
    append_parser.add_argument("--generated-at")
    append_parser.add_argument("--run-id")
    append_parser.add_argument("--artifact-id")
    append_parser.add_argument("--bundle-id")
    append_parser.add_argument("--bundle-sha256")
    append_parser.add_argument("--export-id")
    append_parser.add_argument("--reason", default="fixture-approved pilot workflow")
    append_parser.add_argument("--out-event", type=Path)
    append_parser.add_argument("--reset-log", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate a local audit log")
    validate_parser.add_argument("--log", required=True, type=Path)

    export_parser = subparsers.add_parser("export", help="Export a safe audit log summary")
    export_parser.add_argument("--log", required=True, type=Path)
    export_parser.add_argument("--generated-at")
    export_parser.add_argument("--out-json", type=Path)

    retention_parser = subparsers.add_parser(
        "retention",
        help="Report policy-bound audit retention status and optionally delete expired logs",
    )
    retention_parser.add_argument("--log", required=True, type=Path)
    retention_parser.add_argument("--policy", required=True, type=Path)
    retention_parser.add_argument("--generated-at")
    retention_parser.add_argument("--out-json", type=Path)
    retention_parser.add_argument("--delete-expired-log", action="store_true")
    retention_parser.add_argument("--confirm-retention-delete", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "append":
            event = append_audit_event(
                args.log,
                event_type=args.event_type,
                operator_label=args.operator_label,
                decision=args.decision,
                policy=load_policy(args.policy),
                generated_at=args.generated_at,
                run_id=args.run_id,
                artifact_id=args.artifact_id,
                bundle_id=args.bundle_id,
                bundle_sha256=args.bundle_sha256,
                export_id=args.export_id,
                reason=args.reason,
                reset_log=args.reset_log,
            )
            if args.out_event:
                _assert_runtime_output_path(args.out_event, "audit event")
                args.out_event.parent.mkdir(parents=True, exist_ok=True)
                args.out_event.write_text(_pretty_json(event) + "\n", encoding="utf-8")
            print(_pretty_json(event))
            return 0
        if args.command == "export":
            exported = export_audit_log(args.log, generated_at=args.generated_at)
            if args.out_json:
                _assert_runtime_output_path(args.out_json, "audit export")
                args.out_json.parent.mkdir(parents=True, exist_ok=True)
                args.out_json.write_text(_pretty_json(exported) + "\n", encoding="utf-8")
            print(_pretty_json(exported))
            return 0
        if args.command == "retention":
            report = audit_retention_report(
                args.log,
                policy=load_policy(args.policy),
                generated_at=args.generated_at,
                delete_expired_log=args.delete_expired_log,
                confirm_retention_delete=args.confirm_retention_delete,
            )
            if args.out_json:
                _assert_runtime_output_path(args.out_json, "audit retention report")
                args.out_json.parent.mkdir(parents=True, exist_ok=True)
                args.out_json.write_text(_pretty_json(report) + "\n", encoding="utf-8")
            print(_pretty_json(report))
            return 0
        print(_pretty_json(validate_audit_log(args.log)))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"evidence.audit: {_safe_error(exc)}", file=sys.stderr)
        return 1


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AuditLogError(f"{path}:{line_no} must decode to object")
        events.append(value)
    return events


def _last_event_hash(path: Path) -> str | None:
    events = _read_events(path)
    if not events:
        return None
    validate_audit_log(path)
    return _str(events[-1].get("event_hash"), "")


def _assert_runtime_log_path(path: Path) -> None:
    _assert_runtime_output_path(path, "audit log")


def _assert_runtime_output_path(path: Path, label: str) -> None:
    normalized = str(path).replace("\\", "/")
    if "/outputs/runtime/" not in f"/{normalized}" and not normalized.startswith("outputs/runtime/"):
        raise AuditLogError(f"{label} must stay under an ignored outputs/runtime directory")


def _audit_event_summary(event: dict[str, Any]) -> dict[str, Any]:
    operator = _object(event.get("operator"))
    policy = _object(event.get("policy"))
    chain = _object(event.get("chain"))
    refs = {
        key: value
        for key, value in sorted(_object(event.get("refs")).items())
        if isinstance(value, str) and value
    }
    return {
        "event_id": _str(event.get("event_id"), ""),
        "event_type": _str(event.get("event_type"), ""),
        "generated_at": _str(event.get("generated_at"), ""),
        "operator_label": _str(operator.get("label"), ""),
        "decision": _str(event.get("decision"), ""),
        "reason": _str(event.get("reason"), ""),
        "policy_id": _str(policy.get("policy_id"), ""),
        "policy_sha256": _str(policy.get("policy_sha256"), ""),
        "refs": refs,
        "previous_event_hash": chain.get("previous_event_hash"),
        "event_hash": _str(event.get("event_hash"), ""),
    }


def _audit_redaction_report(event_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "summary_fields_only": True,
        "source_log_embedded": False,
        "raw_event_bodies_embedded": False,
        "event_summaries_emitted": len(event_summaries),
        "field_allowlist": [
            "decision",
            "event_hash",
            "event_id",
            "event_type",
            "generated_at",
            "operator_label",
            "policy_id",
            "policy_sha256",
            "previous_event_hash",
            "reason",
            "refs",
        ],
        "redacted_fields": [
            "full hash-chained event body",
            "per-event safety attestation block",
            "empty reference fields",
            "raw collection text",
            "runtime-local source details",
        ],
        "blocked_text_classes": [
            "email-like operator labels",
            "hostname-like text",
            "IP-like text",
            "secret-like text",
            "URL-like text",
        ],
        "operator_review_required": True,
    }


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_policy_id(policy: dict[str, Any]) -> str:
    policy_id = _str(policy.get("policy_id"), "")
    _safe_label(policy_id, "policy_id")
    return policy_id


def _audit_log_max_days(policy: dict[str, Any]) -> int:
    retention = _object(policy.get("retention"))
    value = retention.get("audit_log_max_days")
    if not isinstance(value, int) or value < 1 or value > 365:
        raise AuditLogError("policy.retention.audit_log_max_days must be integer days between 1 and 365")
    return value


def _validate_safety_attestation(value: dict[str, Any], label: str) -> None:
    safety = _object(value.get("safety_attestation"))
    for flag in (
        "no_live_targets",
        "no_live_target_data_included",
        "no_payloads",
        "no_credentials",
    ):
        if safety.get(flag) is not True:
            raise AuditLogError(f"{label} safety_attestation.{flag} must be true")
    if not _str(safety.get("data_boundary_statement"), ""):
        raise AuditLogError(f"{label} safety_attestation.data_boundary_statement must be non-empty")


def _scan_safe(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in {"credential", "credentials", "password", "payload", "payloads", "hostname", "ip"}:
                raise AuditLogError(f"{path} contains unsafe key: {key}")
            _scan_safe(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_safe(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        _safe_text(value, path)


def _safe_label(value: str, path: str) -> None:
    if not value or not SAFE_LABEL_RE.fullmatch(value):
        raise AuditLogError(f"{path} must be a safe label")
    _safe_text(value, path)


def _safe_text(value: str, path: str) -> None:
    if len(value) > 600:
        raise AuditLogError(f"{path} must stay under 600 characters")
    if IP_RE.search(value):
        raise AuditLogError(f"{path} contains IP-like text")
    if HOSTNAME_RE.search(value):
        raise AuditLogError(f"{path} contains hostname-like text")
    if EMAIL_RE.search(value):
        raise AuditLogError(f"{path} contains email-like text")
    if SECRET_RE.search(value):
        raise AuditLogError(f"{path} contains secret-like text")
    if re.search(r"\b(?:https?|ssh|ftp)://", value, re.I):
        raise AuditLogError(f"{path} contains URL-like text")


def _ensure_timestamp(value: str | None) -> str:
    if value:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    if not value:
        raise AuditLogError("timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_normalized(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


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
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _safe_error(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:800]


if __name__ == "__main__":
    raise SystemExit(main())
