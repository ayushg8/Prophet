#!/usr/bin/env python3
"""Summarize execution state for today's Prophet validation outreach pack."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shlex
import sys
from datetime import date
from pathlib import Path
from typing import Any


MESSAGE_PACK_SCHEMA_VERSION = "prophet_validation_message_pack.v0.1"
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")


class OutreachStatusError(ValueError):
    """Raised when outreach status cannot be summarized safely."""


def build_status(
    pack: dict[str, Any],
    targets_value: dict[str, Any],
    *,
    verify_dry_run_commands: bool = False,
    require_date: str | None = None,
) -> dict[str, Any]:
    _validate_message_pack(pack)
    _validate_required_date(require_date)
    if require_date is not None and pack["generated_for"] != require_date:
        raise OutreachStatusError(
            f"message pack generated_for {pack['generated_for']} does not match required date {require_date}"
        )
    scorecard_module = _load_targets_scorecard_module()
    target_errors = scorecard_module.validate_targets(targets_value)
    if target_errors:
        raise OutreachStatusError("; ".join(target_errors))

    targets_by_label = {
        target["target_label"]: target
        for target in targets_value.get("targets", [])
    }
    items = []
    for draft in pack["drafts"]:
        expected = _parse_tracker_command(draft["tracker_update_command"])
        label = draft["target_label"]
        if expected["target_label"] != label:
            raise OutreachStatusError(f"{label} tracker command updates a different target")
        target = targets_by_label.get(label)
        if target is None:
            items.append(_missing_target_item(draft, expected))
            continue
        items.append(_status_item(draft, target, expected))

    if verify_dry_run_commands:
        _verify_dry_run_commands(items, targets_value)

    counts = _count_states(items)
    dry_run_counts = _count_dry_run_verifications(items)
    next_pending = _next_pending_item(items)
    return {
        "schema_version": "prophet_validation_outreach_status.v0.1",
        "message_pack_schema_version": pack["schema_version"],
        "generated_for": pack["generated_for"],
        "target_tracker_updated_at": targets_value.get("updated_at"),
        "draft_count": len(items),
        "counts": counts,
        "dry_run_verified_count": dry_run_counts["verified"],
        "dry_run_failed_count": dry_run_counts["failed"],
        "dry_run_skipped_count": dry_run_counts["skipped"],
        "complete": counts["updated_after_send"] + counts["advanced"] == len(items),
        "next_pending_target_label": (
            next_pending["target_label"] if next_pending is not None else None
        ),
        "next_pending_group": next_pending["group"] if next_pending is not None else None,
        "next_pending_dry_run_apply_command": (
            next_pending.get("dry_run_apply_command") if next_pending is not None else None
        ),
        "next_pending_confirmed_apply_command": (
            next_pending.get("confirmed_apply_command") if next_pending is not None else None
        ),
        "status_command": f"make validation-status DATE={pack['generated_for']}",
        "items": items,
        "operator_notes": [
            "Send messages before applying non-dry-run tracker updates.",
            "Use --require-date YYYY-MM-DD after restored sessions to reject stale message packs.",
            "Run each Make dry-run command first and inspect the summary.",
            "Run each CONFIRM_SENT=1 command only after the message was actually sent.",
            "Use --verify-dry-run-commands to check pending generated commands before sending.",
            f"Rerun make validation-dashboard DATE={pack['generated_for']} after tracker updates.",
        ],
    }


def render_markdown(status: dict[str, Any]) -> str:
    lines = [
        f"# Prophet Outreach Execution Status - {status['generated_for']}",
        "",
        f"- Draft count: {status['draft_count']}",
        f"- Pending send/update: {status['counts']['pending_send_or_update']}",
        f"- Updated after send: {status['counts']['updated_after_send']}",
        f"- Advanced beyond outreach: {status['counts']['advanced']}",
        f"- Needs attention: {status['counts']['needs_attention']}",
        f"- Dry-run verified: {status['dry_run_verified_count']}",
        f"- Dry-run failed: {status['dry_run_failed_count']}",
        f"- Dry-run skipped: {status['dry_run_skipped_count']}",
        f"- Complete: {str(status['complete']).lower()}",
    ]
    lines.extend(
        [
            f"- Next pending target: {status.get('next_pending_target_label') or 'none'}",
            f"- Next pending group: {status.get('next_pending_group') or 'none'}",
        ]
    )
    if status.get("next_pending_dry_run_apply_command"):
        lines.append(
            f"- Next safe dry-run apply command: `{status['next_pending_dry_run_apply_command']}`"
        )
    if status.get("next_pending_confirmed_apply_command"):
        lines.append(
            f"- Next confirmed-send apply command: `{status['next_pending_confirmed_apply_command']}`"
        )
    lines.extend(["", "## Targets"])
    for item in status["items"]:
        lines.extend(
            [
                "",
                f"### {item['target_label']} - {item['state']}",
                "",
                f"- Group: {item['group']}",
                f"- Current status: {item.get('current_status', 'missing')}",
                f"- Expected status: {item['expected']['status']}",
                f"- Expected follow-up due: {item['expected']['follow_up_due']}",
                f"- Required current status: {_format_required_statuses(item['expected']['require_current_status'])}",
                f"- Action: {item['action']}",
            ]
        )
        if item.get("mismatches"):
            lines.append(f"- Mismatches: {', '.join(item['mismatches'])}")
        if item.get("dry_run_verification"):
            verification = item["dry_run_verification"]
            if verification["ok"] is True:
                lines.append("- Dry-run verification: passed")
            elif verification["ok"] is False:
                lines.append(f"- Dry-run verification: failed ({verification['error']})")
            else:
                lines.append(f"- Dry-run verification: skipped ({verification['reason']})")
        if item.get("dry_run_apply_command"):
            lines.append(f"- Safe dry-run apply command: `{item['dry_run_apply_command']}`")
        if item.get("confirmed_apply_command"):
            lines.append(f"- Confirmed-send apply command: `{item['confirmed_apply_command']}`")
        lines.append(f"- Dry-run command: `{item['tracker_update_command']}`")
    lines.extend(["", "## Operator Notes"])
    for note in status["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report which validation outreach drafts still need send/update work."
    )
    parser.add_argument(
        "--message-pack",
        default=str(DEFAULT_MESSAGE_PACK),
        help="Path to prophet_validation_message_pack.v0.1 JSON.",
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--verify-dry-run-commands",
        action="store_true",
        help="Validate pending generated tracker commands against the current tracker without writing.",
    )
    parser.add_argument(
        "--require-date",
        help="Fail unless the message pack generated_for date matches this YYYY-MM-DD value.",
    )
    parser.add_argument("--out", help="Optional path to write the rendered status.")
    args = parser.parse_args(argv)

    try:
        pack = _load_json_object(Path(args.message_pack), "message pack")
        targets = _load_json_object(Path(args.targets), "target tracker")
        status = build_status(
            pack,
            targets,
            verify_dry_run_commands=args.verify_dry_run_commands,
            require_date=args.require_date,
        )
    except (OSError, json.JSONDecodeError, OutreachStatusError) as exc:
        print(f"validation outreach status failed: {exc}", file=sys.stderr)
        return 1

    rendered = (
        render_markdown(status)
        if args.format == "markdown"
        else json.dumps(status, indent=2, sort_keys=True) + "\n"
    )
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _validate_message_pack(pack: dict[str, Any]) -> None:
    if pack.get("schema_version") != MESSAGE_PACK_SCHEMA_VERSION:
        raise OutreachStatusError(f"schema_version must be {MESSAGE_PACK_SCHEMA_VERSION}")
    if not isinstance(pack.get("generated_for"), str) or not pack["generated_for"].strip():
        raise OutreachStatusError("generated_for is required")
    drafts = pack.get("drafts")
    if not isinstance(drafts, list):
        raise OutreachStatusError("drafts must be a list")
    seen_labels: set[str] = set()
    for index, draft in enumerate(drafts, start=1):
        context = f"drafts[{index}]"
        if not isinstance(draft, dict):
            raise OutreachStatusError(f"{context} must be an object")
        for field in ("target_label", "group", "tracker_update_command"):
            if not isinstance(draft.get(field), str) or not draft[field].strip():
                raise OutreachStatusError(f"{context}.{field} is required")
        label = draft["target_label"]
        if label in seen_labels:
            raise OutreachStatusError(f"{context}.target_label duplicates {label}")
        seen_labels.add(label)


def _validate_required_date(require_date: str | None) -> None:
    if require_date is None:
        return
    try:
        date.fromisoformat(require_date)
    except ValueError as exc:
        raise OutreachStatusError("require-date must be YYYY-MM-DD") from exc


def _status_item(
    draft: dict[str, Any],
    target: dict[str, Any],
    expected: dict[str, str],
) -> dict[str, Any]:
    mismatches = [
        field
        for field in ("status", "last_touch", "follow_up_due", "next_action")
        if str(target.get(field, "")) != expected[field]
    ]
    current_status = str(target["status"])
    if not mismatches:
        state = "updated_after_send"
        action = "No tracker update needed for this draft."
    elif current_status in {"call_booked", "completed"}:
        state = "advanced"
        action = "Target advanced beyond outreach; confirm the private call log is updated."
    elif current_status == "disqualified":
        state = "advanced"
        action = "Target disqualified; confirm the reason is reflected in private notes."
    elif current_status in {"identified", "intro_requested", "outreach_sent", "follow_up_due"}:
        state = "pending_send_or_update"
        action = (
            "Run the Make dry-run command. If it passes, generate the copy-only "
            "send text with make validation-send-copy, send that text outside "
            "the repo, then apply the tracker update only after the actual send "
            "is confirmed."
        )
    else:
        state = "needs_attention"
        action = "Unexpected target status; inspect the private target tracker."
    if state == "pending_send_or_update" and current_status == expected["status"]:
        action = "Tracker status is partly updated; verify dates and next_action before continuing."
    return {
        "target_label": draft["target_label"],
        "group": draft["group"],
        "state": state,
        "current_status": current_status,
        "expected": expected,
        "mismatches": mismatches,
        "action": action,
        "dry_run_apply_command": draft.get("dry_run_apply_command"),
        "confirmed_apply_command": draft.get("confirmed_apply_command"),
        "tracker_update_command": draft["tracker_update_command"],
    }


def _missing_target_item(draft: dict[str, Any], expected: dict[str, str]) -> dict[str, Any]:
    return {
        "target_label": draft["target_label"],
        "group": draft["group"],
        "state": "needs_attention",
        "expected": expected,
        "mismatches": ["target_label"],
        "action": "Draft target is missing from the private target tracker.",
        "dry_run_apply_command": draft.get("dry_run_apply_command"),
        "confirmed_apply_command": draft.get("confirmed_apply_command"),
        "tracker_update_command": draft["tracker_update_command"],
    }


def _parse_tracker_command(command: str) -> dict[str, Any]:
    parts = shlex.split(command)
    if parts[:2] != ["python3", "scripts/validation-target-update.py"]:
        raise OutreachStatusError("tracker command must call scripts/validation-target-update.py")
    if "--dry-run" not in parts:
        raise OutreachStatusError("tracker command must include --dry-run")
    return {
        "target_label": _arg_value(parts, "--target-label"),
        "status": _arg_value(parts, "--status"),
        "last_touch": _arg_value(parts, "--last-touch"),
        "follow_up_due": _arg_value(parts, "--follow-up-due"),
        "next_action": _arg_value(parts, "--next-action"),
        "require_current_status": _arg_values(parts, "--require-current-status"),
    }


def _verify_dry_run_commands(
    items: list[dict[str, Any]],
    targets_value: dict[str, Any],
) -> None:
    target_update_module = _load_target_update_module()
    for item in items:
        if item["state"] != "pending_send_or_update":
            item["dry_run_verification"] = {
                "ok": None,
                "reason": f"state is {item['state']}",
            }
            continue
        expected = item["expected"]
        try:
            target_update_module.update_target(
                copy.deepcopy(targets_value),
                target_label=expected["target_label"],
                status=expected["status"],
                last_touch=expected["last_touch"],
                follow_up_due=expected["follow_up_due"],
                next_action=expected["next_action"],
                updated_at=expected["last_touch"],
                require_current_status=expected["require_current_status"],
            )
        except target_update_module.ValidationTargetUpdateError as exc:
            item["state"] = "needs_attention"
            item["action"] = (
                "Dry-run command failed; regenerate the pack or inspect the target tracker before sending."
            )
            item["dry_run_verification"] = {
                "ok": False,
                "error": str(exc),
            }
        else:
            item["dry_run_verification"] = {"ok": True}


def _arg_value(parts: list[str], flag: str) -> str:
    try:
        index = parts.index(flag)
        value = parts[index + 1]
    except (ValueError, IndexError) as exc:
        raise OutreachStatusError(f"tracker command missing {flag}") from exc
    if not value.strip():
        raise OutreachStatusError(f"tracker command has empty {flag}")
    return value


def _arg_values(parts: list[str], flag: str) -> list[str]:
    values: list[str] = []
    for index, part in enumerate(parts):
        if part != flag:
            continue
        try:
            value = parts[index + 1]
        except IndexError as exc:
            raise OutreachStatusError(f"tracker command missing {flag}") from exc
        if not value.strip():
            raise OutreachStatusError(f"tracker command has empty {flag}")
        values.append(value)
    return values


def _format_required_statuses(statuses: list[str]) -> str:
    if not statuses:
        return "not specified"
    return ", ".join(statuses)


def _count_states(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "pending_send_or_update": 0,
        "updated_after_send": 0,
        "advanced": 0,
        "needs_attention": 0,
    }
    for item in items:
        counts[item["state"]] += 1
    return counts


def _count_dry_run_verifications(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "verified": 0,
        "failed": 0,
        "skipped": 0,
    }
    for item in items:
        verification = item.get("dry_run_verification")
        if not verification:
            continue
        if verification.get("ok") is True:
            counts["verified"] += 1
        elif verification.get("ok") is False:
            counts["failed"] += 1
        else:
            counts["skipped"] += 1
    return counts


def _next_pending_item(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in items:
        if item["state"] != "pending_send_or_update":
            continue
        verification = item.get("dry_run_verification")
        if verification is None or verification.get("ok") is True:
            return item
    return None


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OutreachStatusError(f"{label} must be a JSON object")
    return value


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise OutreachStatusError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_target_update_module() -> Any:
    script_path = Path(__file__).with_name("validation-target-update.py")
    spec = importlib.util.spec_from_file_location("validation_target_update", script_path)
    if spec is None or spec.loader is None:
        raise OutreachStatusError("could not load validation target updater")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
