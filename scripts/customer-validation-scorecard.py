#!/usr/bin/env python3
"""Score anonymized Prophet customer discovery logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "prophet_customer_validation_log.v0.1"
SCORECARD_SCHEMA_VERSION = "prophet_customer_validation_scorecard.v0.1"
SCORE_FIELDS = (
    "pain_score",
    "urgency_score",
    "status_quo_weakness_score",
    "buyer_access_score",
    "data_feasibility_score",
    "pilot_pull_score",
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?[2-9][0-9]{2}\)?[-.\s]?)?[2-9][0-9]{2}[-.\s]?[0-9]{4}")
IP_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
PRIVATE_HOST_RE = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9-]{0,62}\."
    r"(?:internal|corp|lan|localdomain|intranet|private|svc|prod|dev|test)\b",
    re.IGNORECASE,
)
ALLOWED_BUDGET_SIGNALS = {
    "none",
    "unknown",
    "influencer_only",
    "budget_owner_named",
    "could_sponsor_design_partner",
    "paid_pilot_discussed",
    "paid_pilot_committed",
}
ALLOWED_PILOT_SIGNALS = {
    "none",
    "send_deck",
    "asked_for_demo",
    "introduced_stakeholder",
    "offered_safe_artifact",
    "asked_for_scoped_pilot",
    "pilot_committed",
}


class CustomerValidationError(ValueError):
    """Raised when a validation log is unsafe or invalid."""


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CustomerValidationError("validation log must be a JSON object")
    return value


def validate_log(log: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if log.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    interviews = log.get("interviews")
    if not isinstance(interviews, list):
        errors.append("interviews must be a list")
        return errors
    for index, interview in enumerate(interviews, start=1):
        context = f"interviews[{index}]"
        if not isinstance(interview, dict):
            errors.append(f"{context} must be object")
            continue
        _scan_for_sensitive_values(interview, context, errors)
        for field in (
            "account_label",
            "segment",
            "persona",
            "current_workflow",
            "recent_painful_event",
            "status_quo_gap",
            "desired_output",
            "budget_signal",
            "pilot_signal",
            "next_step",
        ):
            if not _non_empty_str(interview.get(field)):
                errors.append(f"{context}.{field} is required")
        if not isinstance(interview.get("qualified"), bool):
            errors.append(f"{context}.qualified must be boolean")
        existing_tools = interview.get("existing_tools")
        if not isinstance(existing_tools, list) or not all(_non_empty_str(tool) for tool in existing_tools):
            errors.append(f"{context}.existing_tools must be non-empty list[str]")
        objections = interview.get("objections")
        if not isinstance(objections, list) or not all(isinstance(item, str) for item in objections):
            errors.append(f"{context}.objections must be list[str]")
        if interview.get("budget_signal") not in ALLOWED_BUDGET_SIGNALS:
            errors.append(f"{context}.budget_signal is unsupported")
        if interview.get("pilot_signal") not in ALLOWED_PILOT_SIGNALS:
            errors.append(f"{context}.pilot_signal is unsupported")
        for field in SCORE_FIELDS:
            score = interview.get(field)
            if not isinstance(score, int) or score < 1 or score > 5:
                errors.append(f"{context}.{field} must be integer 1-5")
    return errors


def build_scorecard(log: dict[str, Any]) -> dict[str, Any]:
    errors = validate_log(log)
    if errors:
        raise CustomerValidationError("; ".join(errors))
    interviews = log.get("interviews") or []
    qualified = [interview for interview in interviews if interview.get("qualified") is True]
    high_pain = [
        interview
        for interview in qualified
        if interview["pain_score"] >= 4
        and interview["urgency_score"] >= 4
        and interview["status_quo_weakness_score"] >= 4
    ]
    pilot_pull = [
        interview
        for interview in qualified
        if interview["pilot_signal"] in {
            "introduced_stakeholder",
            "offered_safe_artifact",
            "asked_for_scoped_pilot",
            "pilot_committed",
        }
        or interview["pilot_pull_score"] >= 4
    ]
    paid_or_sponsored = [
        interview
        for interview in qualified
        if interview["budget_signal"] in {
            "could_sponsor_design_partner",
            "paid_pilot_discussed",
            "paid_pilot_committed",
        }
    ]
    segment_counts = Counter(str(interview["segment"]) for interview in qualified)
    persona_counts = Counter(str(interview["persona"]) for interview in qualified)
    average_scores = {
        field: _average([interview[field] for interview in qualified])
        for field in SCORE_FIELDS
    }
    verdict = _verdict(
        qualified_count=len(qualified),
        high_pain_count=len(high_pain),
        pilot_pull_count=len(pilot_pull),
        paid_or_sponsored_count=len(paid_or_sponsored),
    )
    return {
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "log_schema_version": log["schema_version"],
        "updated_at": log.get("updated_at"),
        "interview_count": len(interviews),
        "qualified_count": len(qualified),
        "high_pain_count": len(high_pain),
        "pilot_pull_count": len(pilot_pull),
        "paid_or_sponsored_count": len(paid_or_sponsored),
        "average_scores": average_scores,
        "segment_counts": dict(sorted(segment_counts.items())),
        "persona_counts": dict(sorted(persona_counts.items())),
        "verdict": verdict,
        "next_action": _next_action(verdict),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score an anonymized Prophet customer validation log."
    )
    parser.add_argument(
        "--log",
        default="docs/customer-validation-log.example.json",
        help="Path to prophet_customer_validation_log.v0.1 JSON",
    )
    parser.add_argument("--out-json", help="Optional path to write scorecard JSON")
    args = parser.parse_args(argv)
    try:
        scorecard = build_scorecard(load_json(args.log))
    except (OSError, json.JSONDecodeError, CustomerValidationError) as exc:
        print(f"customer validation scorecard failed: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(scorecard, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


def _verdict(
    *,
    qualified_count: int,
    high_pain_count: int,
    pilot_pull_count: int,
    paid_or_sponsored_count: int,
) -> str:
    if qualified_count < 5:
        return "insufficient_data"
    if high_pain_count < 3:
        return "do_not_build_yet"
    if qualified_count < 15:
        return "keep_discovering"
    if high_pain_count >= 8 and pilot_pull_count >= 3 and paid_or_sponsored_count >= 1:
        return "build_next_slice"
    if high_pain_count >= 5 and pilot_pull_count >= 2:
        return "pilot_pull_detected"
    return "keep_discovering"


def _next_action(verdict: str) -> str:
    return {
        "insufficient_data": "Book more qualified discovery calls before changing product direction.",
        "do_not_build_yet": "Stop platform work; revise ICP or positioning because pain is not strong enough.",
        "keep_discovering": "Keep running calls and ask high-pain accounts for a scoped pilot.",
        "pilot_pull_detected": "Convert interested accounts into a paid or sponsored design partner pilot.",
        "build_next_slice": "Build only the smallest production slice required by the committed pilot.",
    }[verdict]


def _scan_for_sensitive_values(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_for_sensitive_values(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_for_sensitive_values(item, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            errors.append(f"{path} contains email-like text")
        if PHONE_RE.search(value):
            errors.append(f"{path} contains phone-like text")
        if IP_RE.search(value):
            errors.append(f"{path} contains IP-like text")
        if PRIVATE_HOST_RE.search(value):
            errors.append(f"{path} contains private hostname-like text")


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    raise SystemExit(main())
