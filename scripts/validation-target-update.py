#!/usr/bin/env python3
"""Safely update one Prophet validation target after outreach."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_LOG = Path("validation/private/customer-validation-log.json")
DATE_FIELDS = ("last_touch", "follow_up_due")
SEND_DERIVED_STATUSES = {"intro_requested", "outreach_sent"}


class ValidationTargetUpdateError(ValueError):
    """Raised when a validation target update is unsafe or invalid."""


def update_target(
    value: dict[str, Any],
    *,
    target_label: str,
    status: str,
    last_touch: str | None = None,
    follow_up_due: str | None = None,
    clear_follow_up_due: bool = False,
    next_action: str | None = None,
    updated_at: str | None = None,
    require_current_status: list[str] | None = None,
) -> dict[str, Any]:
    scorecard_module = _load_targets_scorecard_module()
    _validate_target_list(scorecard_module, value)
    if clear_follow_up_due and follow_up_due is not None:
        raise ValidationTargetUpdateError(
            "--clear-follow-up-due cannot be combined with --follow-up-due"
        )
    if clear_follow_up_due:
        follow_up_due = ""
    _validate_date("last_touch", last_touch)
    _validate_date("follow_up_due", follow_up_due)
    _validate_date("updated_at", updated_at)
    if status not in scorecard_module.ALLOWED_STATUSES:
        raise ValidationTargetUpdateError(f"unsupported status: {status}")
    required_statuses = require_current_status or []
    for required_status in required_statuses:
        if required_status not in scorecard_module.ALLOWED_STATUSES:
            raise ValidationTargetUpdateError(
                f"unsupported required current status: {required_status}"
            )
    targets = value.get("targets") or []
    target = _find_target(targets, target_label)
    current_status = str(target["status"])
    if required_statuses and current_status not in set(required_statuses):
        allowed = ", ".join(sorted(required_statuses))
        raise ValidationTargetUpdateError(
            f"target current status must be one of [{allowed}], got {current_status}"
        )
    before = {
        "status": current_status,
        "last_touch": target.get("last_touch", ""),
        "follow_up_due": target.get("follow_up_due", ""),
        "next_action": target["next_action"],
    }
    target["status"] = status
    if last_touch is not None:
        target["last_touch"] = last_touch
    if follow_up_due is not None:
        target["follow_up_due"] = follow_up_due
    if next_action is not None:
        target["next_action"] = next_action
    value["updated_at"] = updated_at or last_touch or date.today().isoformat()
    _validate_target_list(scorecard_module, value)
    return {
        "ok": True,
        "target_label": target_label,
        "before": before,
        "after": {
            "status": target["status"],
            "last_touch": target.get("last_touch", ""),
            "follow_up_due": target.get("follow_up_due", ""),
            "next_action": target["next_action"],
        },
        "updated_at": value["updated_at"],
        "status_command": f"make validation-status DATE={value['updated_at']}",
        "dashboard_command": f"make validation-dashboard DATE={value['updated_at']}",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update one safe anonymized validation target."
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON.",
    )
    parser.add_argument("--target-label", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--last-touch")
    parser.add_argument("--follow-up-due")
    parser.add_argument(
        "--clear-follow-up-due",
        action="store_true",
        help="Clear the target follow_up_due field after a reply, booked call, or disqualification.",
    )
    parser.add_argument("--next-action")
    parser.add_argument("--updated-at")
    parser.add_argument(
        "--require-current-status",
        action="append",
        help="Require the target to currently have this status before updating. Repeat for alternatives. Required for CLI updates.",
    )
    parser.add_argument(
        "--out",
        help="Optional output path. Defaults to updating --targets in place when --confirm-target is supplied.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the update summary without writing. This is the default when --confirm-target is omitted.",
    )
    parser.add_argument(
        "--confirm-target",
        action="store_true",
        help="Write the anonymized target update after reviewing the validation summary.",
    )
    parser.add_argument(
        "--validation-log",
        default=str(DEFAULT_LOG),
        help="Path to prophet_customer_validation_log.v0.1 JSON for completion guards.",
    )
    parser.add_argument(
        "--require-validation-log-account",
        action="store_true",
        help="Require a sanitized validation-log interview with account_label matching --target-label.",
    )
    args = parser.parse_args(argv)
    targets_path = Path(args.targets)
    try:
        if args.dry_run and args.confirm_target:
            raise ValidationTargetUpdateError(
                "--dry-run cannot be combined with --confirm-target"
            )
        if not args.require_current_status:
            raise ValidationTargetUpdateError(
                "at least one --require-current-status is required for CLI updates"
            )
        if args.confirm_target and args.status in SEND_DERIVED_STATUSES:
            raise ValidationTargetUpdateError(
                f"confirmed {args.status} writes must use "
                "scripts/validation-apply-draft-update.py after a real send and "
                "matching copy-only send artifact verification"
            )
        if (
            args.confirm_target
            and args.status == "completed"
            and not args.require_validation_log_account
        ):
            raise ValidationTargetUpdateError(
                "confirmed completed writes require "
                "--require-validation-log-account with a matching sanitized "
                "validation log interview"
            )
        if args.require_validation_log_account:
            _validate_logged_interview(args.validation_log, args.target_label)
        targets = json.loads(targets_path.read_text(encoding="utf-8"))
        if not isinstance(targets, dict):
            raise ValidationTargetUpdateError("target list must be a JSON object")
        summary = update_target(
            targets,
            target_label=args.target_label,
            status=args.status,
            last_touch=args.last_touch,
            follow_up_due=args.follow_up_due,
            clear_follow_up_due=args.clear_follow_up_due,
            next_action=args.next_action,
            updated_at=args.updated_at,
            require_current_status=args.require_current_status,
        )
        summary["confirmed_target"] = args.confirm_target
        summary["would_write"] = args.confirm_target
    except (OSError, json.JSONDecodeError, ValidationTargetUpdateError) as exc:
        print(f"validation target update failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.confirm_target:
        out_path = Path(args.out) if args.out else targets_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(targets, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _validate_logged_interview(log_path: str, target_label: str) -> None:
    scorecard_module = _load_customer_scorecard_module()
    try:
        log = json.loads(Path(log_path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationTargetUpdateError(
            f"validation log is required before completing target: {log_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValidationTargetUpdateError("validation log must be valid JSON") from exc
    if not isinstance(log, dict):
        raise ValidationTargetUpdateError("validation log must be a JSON object")
    errors = scorecard_module.validate_log(log)
    if errors:
        raise ValidationTargetUpdateError("; ".join(errors))
    if not any(
        interview.get("account_label") == target_label
        for interview in log.get("interviews", [])
        if isinstance(interview, dict)
    ):
        raise ValidationTargetUpdateError(
            f"validation log has no sanitized interview for target: {target_label}"
        )


def _validate_target_list(scorecard_module: Any, value: dict[str, Any]) -> None:
    errors = scorecard_module.validate_targets(value)
    if errors:
        raise ValidationTargetUpdateError("; ".join(errors))


def _find_target(targets: list[dict[str, Any]], target_label: str) -> dict[str, Any]:
    for target in targets:
        if target.get("target_label") == target_label:
            return target
    raise ValidationTargetUpdateError(f"target not found: {target_label}")


def _validate_date(field: str, value: str | None) -> None:
    if value in (None, ""):
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationTargetUpdateError(f"{field} must be YYYY-MM-DD") from exc


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise ValidationTargetUpdateError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_customer_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("customer-validation-scorecard.py")
    spec = importlib.util.spec_from_file_location("customer_validation_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise ValidationTargetUpdateError("could not load customer validation validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
