#!/usr/bin/env python3
"""Safely append one anonymized Prophet customer validation interview."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_LOG = Path("validation/private/customer-validation-log.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
PRIVATE_LOG_NOTES = (
    "Private anonymized buyer validation log. Keep real validation logs private; "
    "do not commit names, emails, phone numbers, private hostnames, IPs, raw "
    "screenshots, transcripts, or customer-owned artifacts."
)


class CustomerValidationLogAddError(ValueError):
    """Raised when an interview cannot be appended safely."""


def append_interview(
    log: dict[str, Any],
    interview: dict[str, Any],
    *,
    updated_at: str | None = None,
    replace_example_seed: bool = False,
) -> dict[str, Any]:
    scorecard_module = _load_scorecard_module()
    _validate_log(scorecard_module, log)
    account_label = str(interview.get("account_label", ""))
    updated = copy.deepcopy(log)
    original_scorecard = scorecard_module.build_scorecard(updated)
    removed_example_seed_count = 0
    if replace_example_seed:
        if not original_scorecard["example_seed_log"]:
            raise CustomerValidationLogAddError(
                "--replace-example-seed requires a log marked example-only"
            )
        removed_example_seed_count = _replace_example_seed_interviews(updated)
    if any(existing.get("account_label") == account_label for existing in updated.get("interviews", [])):
        raise CustomerValidationLogAddError(f"account_label already exists: {account_label}")
    updated.setdefault("interviews", []).append(copy.deepcopy(interview))
    updated["updated_at"] = updated_at or date.today().isoformat()
    _validate_date("updated_at", updated["updated_at"])
    _validate_log(scorecard_module, updated)
    scorecard = scorecard_module.build_scorecard(updated)
    log.clear()
    log.update(updated)
    return {
        "ok": True,
        "account_label": account_label,
        "interview_count": scorecard["interview_count"],
        "qualified_count": scorecard["qualified_count"],
        "high_pain_count": scorecard["high_pain_count"],
        "repeated_workflow_pain_count": scorecard["repeated_workflow_pain_count"],
        "top_workflow_pain_theme": scorecard["top_workflow_pain_theme"],
        "pilot_pull_count": scorecard["pilot_pull_count"],
        "paid_or_sponsored_count": scorecard["paid_or_sponsored_count"],
        "gaps_to_verdicts": scorecard["gaps_to_verdicts"],
        "example_seed_log": scorecard["example_seed_log"],
        "raw_verdict": scorecard["raw_verdict"],
        "effective_validation_counts": scorecard["effective_validation_counts"],
        "replaced_example_seed": replace_example_seed,
        "removed_example_seed_count": removed_example_seed_count,
        "verdict": scorecard["verdict"],
        "pilot_conversion_signal": scorecard["verdict"] in {"pilot_pull_detected", "build_next_slice"},
        "build_gate_should_open": scorecard["verdict"] == "build_next_slice",
        "updated_at": updated["updated_at"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append one safe anonymized customer validation interview."
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG),
        help="Path to prophet_customer_validation_log.v0.1 JSON.",
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON for target-status guards.",
    )
    parser.add_argument(
        "--interview-json",
        help="Path to one sanitized interview object. If supplied, field flags are not required.",
    )
    parser.add_argument("--account-label")
    parser.add_argument("--segment")
    parser.add_argument("--persona")
    parser.add_argument("--qualified", choices=("true", "false"))
    parser.add_argument("--current-workflow")
    parser.add_argument("--recent-painful-event")
    parser.add_argument("--existing-tool", action="append")
    parser.add_argument("--status-quo-gap")
    parser.add_argument("--desired-output")
    parser.add_argument("--workflow-pain-theme")
    parser.add_argument("--pain-score", type=int)
    parser.add_argument("--urgency-score", type=int)
    parser.add_argument("--status-quo-weakness-score", type=int)
    parser.add_argument("--buyer-access-score", type=int)
    parser.add_argument("--data-feasibility-score", type=int)
    parser.add_argument("--pilot-pull-score", type=int)
    parser.add_argument("--budget-signal")
    parser.add_argument("--pilot-signal")
    parser.add_argument("--objection", action="append", default=[])
    parser.add_argument("--next-step")
    parser.add_argument("--safe-artifact-offer", default="")
    parser.add_argument("--updated-at")
    parser.add_argument(
        "--out",
        help="Optional output path. Defaults to updating --log in place.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the append summary without writing. This is the default.",
    )
    parser.add_argument(
        "--confirm-log",
        action="store_true",
        help="Write the sanitized interview append after validation.",
    )
    parser.add_argument(
        "--require-target-status",
        action="append",
        help=(
            "Require interview account_label, segment, and persona to match a "
            "target currently in this status. Repeat for alternatives."
        ),
    )
    parser.add_argument(
        "--allow-untracked-interview",
        action="store_true",
        help="Permit a confirmed log write without matching a validation target. Do not use for normal private validation sprint logging.",
    )
    parser.add_argument(
        "--replace-example-seed",
        action="store_true",
        help="Replace the initialized example-only seed with this first real anonymized interview.",
    )
    args = parser.parse_args(argv)
    if args.dry_run and args.confirm_log:
        print(
            "customer validation log append failed: --dry-run cannot be combined with --confirm-log",
            file=sys.stderr,
        )
        return 1
    log_path = Path(args.log)
    try:
        if args.replace_example_seed and args.allow_untracked_interview:
            raise CustomerValidationLogAddError(
                "--replace-example-seed requires --require-target-status; "
                "do not use --allow-untracked-interview for the first real validation log"
            )
        if args.replace_example_seed and not args.require_target_status:
            raise CustomerValidationLogAddError(
                "--replace-example-seed requires --require-target-status call_booked"
            )
        if args.require_target_status and args.allow_untracked_interview:
            raise CustomerValidationLogAddError(
                "--allow-untracked-interview cannot be combined with --require-target-status"
            )
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(log, dict):
            raise CustomerValidationLogAddError("validation log must be a JSON object")
        interview = _load_interview(args)
        if args.require_target_status:
            _validate_matching_target_status(
                args.targets,
                interview,
                args.require_target_status,
            )
        elif args.confirm_log and not args.allow_untracked_interview:
            raise CustomerValidationLogAddError(
                "--confirm-log requires --require-target-status or --allow-untracked-interview"
            )
        summary = append_interview(
            log,
            interview,
            updated_at=args.updated_at,
            replace_example_seed=args.replace_example_seed,
        )
    except (OSError, json.JSONDecodeError, CustomerValidationLogAddError) as exc:
        print(f"customer validation log append failed: {exc}", file=sys.stderr)
        return 1
    should_write = args.confirm_log
    summary["confirmed_log"] = args.confirm_log
    summary["would_write"] = should_write
    print(json.dumps(summary, indent=2, sort_keys=True))
    if should_write:
        out_path = Path(args.out) if args.out else log_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _validate_matching_target_status(
    targets_path: str,
    interview: dict[str, Any],
    required_statuses: list[str],
) -> None:
    account_label = str(interview.get("account_label", ""))
    scorecard_module = _load_targets_scorecard_module()
    for required_status in required_statuses:
        if required_status not in scorecard_module.ALLOWED_STATUSES:
            raise CustomerValidationLogAddError(
                f"unsupported required target status: {required_status}"
            )
    try:
        targets = json.loads(Path(targets_path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise CustomerValidationLogAddError(
            f"validation targets are required before logging interview: {targets_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise CustomerValidationLogAddError("validation targets must be valid JSON") from exc
    if not isinstance(targets, dict):
        raise CustomerValidationLogAddError("validation targets must be a JSON object")
    errors = scorecard_module.validate_targets(targets)
    if errors:
        raise CustomerValidationLogAddError("; ".join(errors))
    target = next(
        (
            target
            for target in targets.get("targets", [])
            if isinstance(target, dict) and target.get("target_label") == account_label
        ),
        None,
    )
    if target is None:
        raise CustomerValidationLogAddError(
            f"validation target not found for account_label: {account_label}"
        )
    current_status = str(target["status"])
    if current_status not in set(required_statuses):
        allowed = ", ".join(sorted(required_statuses))
        raise CustomerValidationLogAddError(
            f"target current status must be one of [{allowed}], got {current_status}"
        )
    for field in ("segment", "persona"):
        interview_value = str(interview.get(field, ""))
        target_value = str(target.get(field, ""))
        if interview_value != target_value:
            raise CustomerValidationLogAddError(
                f"interview {field} must match validation target {field}: "
                f"{target_value}"
            )


def _load_interview(args: argparse.Namespace) -> dict[str, Any]:
    if args.interview_json:
        value = json.loads(Path(args.interview_json).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise CustomerValidationLogAddError("interview JSON must be an object")
        return value
    missing = [
        flag
        for flag, value in (
            ("--account-label", args.account_label),
            ("--segment", args.segment),
            ("--persona", args.persona),
            ("--qualified", args.qualified),
            ("--current-workflow", args.current_workflow),
            ("--recent-painful-event", args.recent_painful_event),
            ("--existing-tool", args.existing_tool),
            ("--status-quo-gap", args.status_quo_gap),
            ("--desired-output", args.desired_output),
            ("--workflow-pain-theme", args.workflow_pain_theme),
            ("--pain-score", args.pain_score),
            ("--urgency-score", args.urgency_score),
            ("--status-quo-weakness-score", args.status_quo_weakness_score),
            ("--buyer-access-score", args.buyer_access_score),
            ("--data-feasibility-score", args.data_feasibility_score),
            ("--pilot-pull-score", args.pilot_pull_score),
            ("--budget-signal", args.budget_signal),
            ("--pilot-signal", args.pilot_signal),
            ("--next-step", args.next_step),
        )
        if value in (None, [])
    ]
    if missing:
        raise CustomerValidationLogAddError(
            "missing required interview fields: " + ", ".join(missing)
        )
    return {
        "account_label": args.account_label,
        "segment": args.segment,
        "persona": args.persona,
        "qualified": args.qualified == "true",
        "current_workflow": args.current_workflow,
        "recent_painful_event": args.recent_painful_event,
        "existing_tools": args.existing_tool,
        "status_quo_gap": args.status_quo_gap,
        "desired_output": args.desired_output,
        "workflow_pain_theme": args.workflow_pain_theme,
        "pain_score": args.pain_score,
        "urgency_score": args.urgency_score,
        "status_quo_weakness_score": args.status_quo_weakness_score,
        "buyer_access_score": args.buyer_access_score,
        "data_feasibility_score": args.data_feasibility_score,
        "pilot_pull_score": args.pilot_pull_score,
        "budget_signal": args.budget_signal,
        "pilot_signal": args.pilot_signal,
        "objections": args.objection,
        "next_step": args.next_step,
        "safe_artifact_offer": args.safe_artifact_offer,
    }


def _replace_example_seed_interviews(log: dict[str, Any]) -> int:
    interviews = log.get("interviews")
    if not isinstance(interviews, list):
        raise CustomerValidationLogAddError("interviews must be a list")
    unsafe_labels = [
        str(interview.get("account_label", ""))
        for interview in interviews
        if isinstance(interview, dict)
        and not str(interview.get("account_label", "")).startswith("example-")
    ]
    if unsafe_labels:
        raise CustomerValidationLogAddError(
            "--replace-example-seed refuses mixed logs with non-example interviews: "
            + ", ".join(sorted(unsafe_labels))
        )
    removed_count = len(interviews)
    log["interviews"] = []
    log["notes"] = PRIVATE_LOG_NOTES
    return removed_count


def _validate_log(scorecard_module: Any, log: dict[str, Any]) -> None:
    errors = scorecard_module.validate_log(log)
    if errors:
        raise CustomerValidationLogAddError("; ".join(errors))


def _validate_date(field: str, value: str | None) -> None:
    if value in (None, ""):
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CustomerValidationLogAddError(f"{field} must be YYYY-MM-DD") from exc


def _load_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("customer-validation-scorecard.py")
    spec = importlib.util.spec_from_file_location("customer_validation_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise CustomerValidationLogAddError("could not load customer validation validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise CustomerValidationLogAddError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
