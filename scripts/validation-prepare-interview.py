#!/usr/bin/env python3
"""Prepare an intentionally incomplete private interview record from a target."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_OUT = Path("validation/private/customer-validation-interview-next.json")
DEFAULT_REQUIRED_STATUSES = ("call_booked",)
SCORE_FIELDS = (
    "pain_score",
    "urgency_score",
    "status_quo_weakness_score",
    "buyer_access_score",
    "data_feasibility_score",
    "pilot_pull_score",
)


class ValidationPrepareInterviewError(ValueError):
    """Raised when an interview starter cannot be prepared safely."""


def prepare_interview_template(
    value: dict[str, Any],
    *,
    target_label: str,
    require_current_status: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scorecard_module = _load_targets_scorecard_module()
    _validate_target_list(scorecard_module, value)
    target = _find_target(value.get("targets") or [], target_label)
    required_statuses = require_current_status or list(DEFAULT_REQUIRED_STATUSES)
    for required_status in required_statuses:
        if required_status not in scorecard_module.ALLOWED_STATUSES:
            raise ValidationPrepareInterviewError(
                f"unsupported required current status: {required_status}"
            )
    current_status = str(target["status"])
    if current_status not in set(required_statuses):
        allowed = ", ".join(sorted(required_statuses))
        raise ValidationPrepareInterviewError(
            f"target current status must be one of [{allowed}], got {current_status}"
        )
    interview = {
        "account_label": target["target_label"],
        "segment": target["segment"],
        "persona": target["persona"],
        "qualified": False,
        "current_workflow": "",
        "recent_painful_event": "",
        "existing_tools": [],
        "status_quo_gap": "",
        "desired_output": "",
        "workflow_pain_theme": "",
        "pain_score": 0,
        "urgency_score": 0,
        "status_quo_weakness_score": 0,
        "buyer_access_score": 0,
        "data_feasibility_score": 0,
        "pilot_pull_score": 0,
        "budget_signal": "",
        "pilot_signal": "",
        "objections": [],
        "next_step": "",
        "safe_artifact_offer": "",
    }
    summary = {
        "ok": True,
        "target_label": target_label,
        "target_status": current_status,
        "required_statuses": required_statuses,
        "prepopulated_fields": ["account_label", "segment", "persona", "qualified"],
        "fields_to_fill": [
            "current_workflow",
            "recent_painful_event",
            "existing_tools",
            "status_quo_gap",
            "desired_output",
            "workflow_pain_theme",
            *SCORE_FIELDS,
            "budget_signal",
            "pilot_signal",
            "objections",
            "next_step",
            "safe_artifact_offer",
        ],
        "note": "This starter is intentionally incomplete and should fail validation until real sanitized call outcomes are filled.",
    }
    return interview, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one incomplete private interview JSON starter from a booked target."
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON.",
    )
    parser.add_argument("--target-label", required=True)
    parser.add_argument(
        "--require-current-status",
        action="append",
        help="Require the target to currently have this status. Defaults to call_booked.",
    )
    parser.add_argument(
        "--date",
        help="Date for the suggested validation-log command in YYYY-MM-DD form.",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Path for the private interview starter JSON.",
    )
    args = parser.parse_args(argv)
    try:
        run_date = args.date or date.today().isoformat()
        _validate_date("date", run_date)
        targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
        if not isinstance(targets, dict):
            raise ValidationPrepareInterviewError("target list must be a JSON object")
        interview, summary = prepare_interview_template(
            targets,
            target_label=args.target_label,
            require_current_status=args.require_current_status,
        )
    except (OSError, json.JSONDecodeError, ValidationPrepareInterviewError) as exc:
        print(f"validation interview preparation failed: {exc}", file=sys.stderr)
        return 1
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(interview, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary["out"] = str(out_path)
    summary["log_dry_run_command"] = f"make validation-log-interview DATE={run_date}"
    summary["log_confirm_command"] = (
        f"make validation-log-interview DATE={run_date} CONFIRM_LOG=1"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _validate_target_list(scorecard_module: Any, value: dict[str, Any]) -> None:
    errors = scorecard_module.validate_targets(value)
    if errors:
        raise ValidationPrepareInterviewError("; ".join(errors))


def _find_target(targets: list[dict[str, Any]], target_label: str) -> dict[str, Any]:
    for target in targets:
        if target.get("target_label") == target_label:
            return target
    raise ValidationPrepareInterviewError(f"target not found: {target_label}")


def _validate_date(field: str, value: str | None) -> None:
    if value in (None, ""):
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationPrepareInterviewError(f"{field} must be YYYY-MM-DD") from exc


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise ValidationPrepareInterviewError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
