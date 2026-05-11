#!/usr/bin/env python3
"""Classify a sanitized outreach reply into the next safe validation command."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import sys
from datetime import date
from pathlib import Path
from typing import Any


REPLY_TRIAGE_SCHEMA_VERSION = "prophet_validation_reply_triage.v0.1"
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
CLASSIFICATIONS = {"book_call", "disqualify", "keep_pending", "manual_review"}
BOOK_CALL_STATUSES = {"intro_requested", "outreach_sent", "follow_up_due"}
DISQUALIFY_STATUSES = {
    "identified",
    "intro_requested",
    "outreach_sent",
    "follow_up_due",
    "call_booked",
}
PENDING_STATUSES = {"identified", "intro_requested", "outreach_sent", "follow_up_due"}
PRIVATE_DETAIL_WARNING = (
    "Never paste reply text, names, emails, phone numbers, URLs, hostnames, IPs, "
    "screenshots, raw tickets, scanner rows, or customer artifacts into the tracker."
)


class ReplyTriageError(ValueError):
    """Raised when a reply classification cannot be turned into a safe action."""


def build_reply_triage(
    value: dict[str, Any],
    *,
    target_label: str,
    classification: str,
    run_date: str | None = None,
) -> dict[str, Any]:
    _validate_date(run_date)
    if classification not in CLASSIFICATIONS:
        raise ReplyTriageError(f"unsupported classification: {classification}")
    scorecard_module = _load_targets_scorecard_module()
    errors = scorecard_module.validate_targets(value)
    if errors:
        raise ReplyTriageError("; ".join(errors))
    target = _find_target(value.get("targets") or [], target_label)
    effective_date = run_date or date.today().isoformat()
    current_status = str(target["status"])

    if classification == "book_call":
        _require_status(current_status, BOOK_CALL_STATUSES, classification)
        dry_run = _make_command("validation-book-call", target_label, effective_date)
        confirmed = _make_command(
            "validation-book-call",
            target_label,
            effective_date,
            confirm_var="CONFIRM_TARGET",
        )
        action = "Run the dry-run command, then confirm only after the call is actually booked."
        write_allowed_after_review = True
    elif classification == "disqualify":
        _require_status(current_status, DISQUALIFY_STATUSES, classification)
        dry_run = _make_command("validation-disqualify-target", target_label, effective_date)
        confirmed = _make_command(
            "validation-disqualify-target",
            target_label,
            effective_date,
            confirm_var="CONFIRM_TARGET",
        )
        action = "Run the dry-run command, then confirm only after the disqualification is safe and sanitized."
        write_allowed_after_review = True
    elif classification == "keep_pending":
        _require_status(current_status, PENDING_STATUSES, classification)
        dry_run = f"make validation-status DATE={shlex.quote(effective_date)}"
        confirmed = None
        action = (
            "Do not write a tracker update from this helper. Keep the target pending unless "
            "you have a real sanitized follow-up date to handle separately."
        )
        write_allowed_after_review = False
    else:
        dry_run = f"make validation-status DATE={shlex.quote(effective_date)}"
        confirmed = None
        action = (
            "Do not write a tracker update yet. Review privately, decide the safe action, "
            "then run the narrow dry-run command for that action."
        )
        write_allowed_after_review = False

    return {
        "schema_version": REPLY_TRIAGE_SCHEMA_VERSION,
        "target_schema_version": value["schema_version"],
        "generated_for": effective_date,
        "classification": classification,
        "target": {
            "target_label": target["target_label"],
            "segment": target["segment"],
            "persona": target["persona"],
            "priority": target["priority"],
            "source": target["source"],
            "current_status": current_status,
            "last_touch": target.get("last_touch", ""),
            "follow_up_due": target.get("follow_up_due", ""),
        },
        "write_allowed_after_review": write_allowed_after_review,
        "dry_run_commands": [dry_run],
        "confirmed_write_commands": [confirmed] if confirmed else [],
        "recommended_next_step": action,
        "operator_notes": [
            "This helper does not read reply text and does not write files.",
            "Use only the sanitized classification, not the buyer's message body.",
            PRIVATE_DETAIL_WARNING,
            f"Rerun make validation-dashboard DATE={effective_date} after any confirmed tracker update.",
        ],
    }


def render_markdown(triage: dict[str, Any]) -> str:
    target = triage["target"]
    lines = [
        f"# Prophet Reply Triage - {triage['generated_for']}",
        "",
        f"- Target: {target['target_label']}",
        f"- Classification: {triage['classification']}",
        f"- Current status: {target['current_status']}",
        f"- Write allowed after review: {str(triage['write_allowed_after_review']).lower()}",
        f"- Recommended next step: {triage['recommended_next_step']}",
        "",
        "## Dry-Run Commands",
    ]
    for command in triage["dry_run_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Confirmed Write Commands"])
    if triage["confirmed_write_commands"]:
        for command in triage["confirmed_write_commands"]:
            lines.append(f"- `{command}`")
    else:
        lines.append("- None. Do not write a tracker update for this classification.")
    lines.extend(["", "## Operator Notes"])
    for note in triage["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Turn a sanitized outreach reply classification into the next safe "
            "validation command. Does not accept reply text and does not write files."
        )
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON.",
    )
    parser.add_argument("--target-label", required=True)
    parser.add_argument(
        "--classification",
        choices=sorted(CLASSIFICATIONS),
        required=True,
        help="Sanitized reply classification. Do not pass reply text.",
    )
    parser.add_argument("--date", help="Reply triage date in YYYY-MM-DD form.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    args = parser.parse_args(argv)
    try:
        targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
        if not isinstance(targets, dict):
            raise ReplyTriageError("target tracker must be a JSON object")
        triage = build_reply_triage(
            targets,
            target_label=args.target_label,
            classification=args.classification,
            run_date=args.date,
        )
    except (OSError, json.JSONDecodeError, ReplyTriageError) as exc:
        print(f"validation reply triage failed: {exc}", file=sys.stderr)
        return 1
    rendered = (
        render_markdown(triage)
        if args.format == "markdown"
        else json.dumps(triage, indent=2, sort_keys=True) + "\n"
    )
    print(rendered, end="")
    return 0


def _require_status(
    current_status: str,
    allowed_statuses: set[str],
    classification: str,
) -> None:
    if current_status in allowed_statuses:
        return
    allowed = ", ".join(sorted(allowed_statuses))
    raise ReplyTriageError(
        f"{classification} requires current status in [{allowed}], got {current_status}"
    )


def _make_command(
    make_target: str,
    target_label: str,
    run_date: str,
    *,
    confirm_var: str | None = None,
) -> str:
    parts = [
        "make",
        make_target,
        f"TARGET={target_label}",
        f"DATE={run_date}",
    ]
    if confirm_var is not None:
        parts.append(f"{confirm_var}=1")
    return " ".join(shlex.quote(part) for part in parts)


def _find_target(targets: list[dict[str, Any]], target_label: str) -> dict[str, Any]:
    for target in targets:
        if target.get("target_label") == target_label:
            return target
    raise ReplyTriageError(f"target not found: {target_label}")


def _validate_date(value: str | None) -> None:
    if value is None:
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ReplyTriageError("date must be YYYY-MM-DD") from exc


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise ReplyTriageError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
