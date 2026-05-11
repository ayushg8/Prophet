#!/usr/bin/env python3
"""Validate an anonymized Prophet validation target list."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "prophet_validation_targets.v0.1"
SCORECARD_SCHEMA_VERSION = "prophet_validation_targets_scorecard.v0.1"
DAILY_FOLLOW_UP_TARGET = 2
ALLOWED_PRIORITIES = {"P0", "P1", "P2"}
ALLOWED_STATUSES = {
    "identified",
    "intro_requested",
    "outreach_sent",
    "follow_up_due",
    "call_booked",
    "completed",
    "disqualified",
}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?[2-9][0-9]{2}\)?[-.\s]?)?[2-9][0-9]{2}[-.\s]?[0-9]{4}")
URL_RE = re.compile(r"https?://", re.IGNORECASE)


class ValidationTargetsError(ValueError):
    """Raised when the target list is unsafe or invalid."""


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationTargetsError("target list must be a JSON object")
    return value


def validate_targets(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    _validate_optional_date(value.get("updated_at"), "updated_at", errors)
    targets = value.get("targets")
    if not isinstance(targets, list):
        errors.append("targets must be a list")
        return errors
    seen_labels: set[str] = set()
    for index, target in enumerate(targets, start=1):
        context = f"targets[{index}]"
        if not isinstance(target, dict):
            errors.append(f"{context} must be object")
            continue
        _scan_sensitive(target, context, errors)
        for field in (
            "target_label",
            "segment",
            "persona",
            "priority",
            "source",
            "status",
            "hypothesized_pain",
            "planned_ask",
            "next_action",
        ):
            if not _non_empty_str(target.get(field)):
                errors.append(f"{context}.{field} is required")
        label = str(target.get("target_label", ""))
        if label in seen_labels:
            errors.append(f"{context}.target_label duplicates {label}")
        seen_labels.add(label)
        if target.get("priority") not in ALLOWED_PRIORITIES:
            errors.append(f"{context}.priority is unsupported")
        if target.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{context}.status is unsupported")
        _validate_optional_date(target.get("last_touch"), f"{context}.last_touch", errors)
        _validate_optional_date(target.get("follow_up_due"), f"{context}.follow_up_due", errors)
        if target.get("status") == "follow_up_due" and not _non_empty_str(target.get("follow_up_due")):
            errors.append(f"{context}.follow_up_due is required when status is follow_up_due")
        if target.get("status") in {"call_booked", "completed", "disqualified"} and _non_empty_str(target.get("follow_up_due")):
            errors.append(f"{context}.follow_up_due must be empty when status is {target.get('status')}")
    return errors


def build_scorecard(value: dict[str, Any]) -> dict[str, Any]:
    errors = validate_targets(value)
    if errors:
        raise ValidationTargetsError("; ".join(errors))
    targets = value.get("targets") or []
    status_counts = Counter(str(target["status"]) for target in targets)
    priority_counts = Counter(str(target["priority"]) for target in targets)
    segment_counts = Counter(str(target["segment"]) for target in targets)
    active_targets = [
        target
        for target in targets
        if target["status"] not in {"completed", "disqualified"}
    ]
    due_count = sum(1 for target in targets if target["status"] == "follow_up_due")
    p0_active_count = sum(1 for target in active_targets if target["priority"] == "P0")
    return {
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "target_schema_version": value["schema_version"],
        "updated_at": value.get("updated_at"),
        "target_count": len(targets),
        "active_target_count": len(active_targets),
        "p0_active_count": p0_active_count,
        "follow_up_due_count": due_count,
        "status_counts": dict(sorted(status_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "segment_counts": dict(sorted(segment_counts.items())),
        "next_action": _next_action(
            target_count=len(targets),
            active_target_count=len(active_targets),
            p0_active_count=p0_active_count,
            due_count=due_count,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and summarize an anonymized Prophet validation target list."
    )
    parser.add_argument(
        "--targets",
        default="docs/validation-targets.example.json",
        help="Path to prophet_validation_targets.v0.1 JSON",
    )
    parser.add_argument("--out-json", help="Optional path to write scorecard JSON")
    args = parser.parse_args(argv)
    try:
        scorecard = build_scorecard(load_json(args.targets))
    except (OSError, json.JSONDecodeError, ValidationTargetsError) as exc:
        print(f"validation targets scorecard failed: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(scorecard, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


def _next_action(
    *,
    target_count: int,
    active_target_count: int,
    p0_active_count: int,
    due_count: int,
) -> str:
    if target_count < 30:
        return "Add more anonymized targets until the sprint has at least 30 candidates."
    if p0_active_count < 10:
        return "Add more P0 DIB/platform-security targets."
    if active_target_count < 15:
        return "Replenish the active target list before the next outreach block."
    if due_count >= DAILY_FOLLOW_UP_TARGET:
        return "Run today's outreach block: 5 targeted asks, 2 due follow-ups, and 1 referral ask."
    if due_count == 1:
        return "Run today's outreach block: 5 targeted asks, 1 due follow-up, 1 follow-up backfill ask, and 1 referral ask."
    return "Run today's outreach block: 5 targeted asks, 2 follow-up backfill asks, and 1 referral ask."


def _scan_sensitive(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_sensitive(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_sensitive(item, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            errors.append(f"{path} contains email-like text")
        if PHONE_RE.search(value):
            errors.append(f"{path} contains phone-like text")
        if URL_RE.search(value):
            errors.append(f"{path} contains URL-like text")


def _validate_optional_date(value: object, path: str, errors: list[str]) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str):
        errors.append(f"{path} must be YYYY-MM-DD")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be YYYY-MM-DD")


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    raise SystemExit(main())
