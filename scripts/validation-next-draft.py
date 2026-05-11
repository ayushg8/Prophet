#!/usr/bin/env python3
"""Render the next safe pending Prophet validation outreach draft."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


NEXT_DRAFT_SCHEMA_VERSION = "prophet_validation_next_draft.v0.1"
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")


class NextDraftError(ValueError):
    """Raised when a safe next draft cannot be selected."""


def build_next_draft(
    pack: dict[str, Any],
    targets_value: dict[str, Any],
    *,
    require_date: str | None = None,
) -> dict[str, Any]:
    if require_date is not None:
        _validate_date(require_date)
    status_module = _load_module("validation-outreach-status.py", "validation_outreach_status")
    status = status_module.build_status(
        pack,
        targets_value,
        verify_dry_run_commands=True,
    )
    if require_date is not None and status["generated_for"] != require_date:
        raise NextDraftError(
            "message pack generated_for "
            f"{status['generated_for']} does not match required date {require_date}"
        )
    if status["counts"]["needs_attention"]:
        labels = [
            item["target_label"]
            for item in status["items"]
            if item["state"] == "needs_attention"
        ]
        raise NextDraftError(
            "outreach pack needs attention before sending: " + ", ".join(labels)
        )
    pending = [
        item
        for item in status["items"]
        if item["state"] == "pending_send_or_update"
        and item.get("dry_run_verification", {}).get("ok") is True
    ]
    if not pending:
        raise NextDraftError("no pending verified outreach drafts")
    selected = pending[0]
    draft = _draft_by_label(pack, selected["target_label"])
    target_labels = sorted(
        str(draft["target_label"])
        for draft in pack.get("drafts", [])
        if isinstance(draft, dict) and draft.get("target_label")
    )
    return {
        "schema_version": NEXT_DRAFT_SCHEMA_VERSION,
        "message_pack_schema_version": pack["schema_version"],
        "status_schema_version": status["schema_version"],
        "generated_for": status["generated_for"],
        "target_label": selected["target_label"],
        "target_labels": target_labels,
        "group": selected["group"],
        "remaining_pending_count": len(pending),
        "dry_run_apply_command": (
            "make validation-apply-draft "
            f"TARGET={selected['target_label']} DATE={status['generated_for']}"
        ),
        "confirmed_apply_command": (
            "make validation-apply-draft "
            f"TARGET={selected['target_label']} DATE={status['generated_for']} "
            "CONFIRM_SENT=1"
        ),
        "draft": draft,
        "status_item": selected,
        "operator_notes": [
            "Replace only the recipient name and channel-specific greeting before sending.",
            "Run the Make dry-run command before sending or writing tracker changes.",
            "Send the copy-only text before applying the confirmed tracker update.",
            "Run the CONFIRM_SENT=1 command only after the message was actually sent.",
            f"Rerun make validation-status DATE={status['generated_for']} after updating the private tracker.",
        ],
    }


def render_markdown(next_draft: dict[str, Any]) -> str:
    message_module = _load_module("validation-message-pack.py", "validation_message_pack")
    filtered_pack = {
        "schema_version": next_draft["message_pack_schema_version"],
        "generated_for": next_draft["generated_for"],
        "draft_count": 1,
        "drafts": [next_draft["draft"]],
        "operator_notes": next_draft["operator_notes"],
    }
    rendered_draft = message_module.render_markdown(filtered_pack)
    lines = [
        f"# Next Prophet Validation Draft - {next_draft['generated_for']}",
        "",
        "This file is tracker/audit metadata. Do not paste it to a buyer.",
        "Use `make validation-send-copy DATE="
        f"{next_draft['generated_for']}` and send only "
        "`validation/private/today-send-copy.txt` after the dashboard says the "
        "send copy is ready and matches the next pending target.",
        "",
        f"- Target: {next_draft['target_label']}",
        f"- Group: {next_draft['group']}",
        f"- Remaining pending drafts: {next_draft['remaining_pending_count']}",
        "- Status: verified pending send/update",
        "",
        "## Safe Tracker Commands",
        "",
        "Dry-run before sending or writing:",
        "",
        "```bash",
        next_draft["dry_run_apply_command"],
        "```",
        "",
        "After the message has actually been sent:",
        "",
        "```bash",
        next_draft["confirmed_apply_command"],
        "```",
        "",
        rendered_draft.rstrip(),
        "",
    ]
    return "\n".join(lines)


def render_send_text(next_draft: dict[str, Any]) -> str:
    """Render copy-ready subject and body, without tracker metadata."""
    message_module = _load_module("validation-message-pack.py", "validation_message_pack")
    draft = next_draft["draft"]
    subject = draft["subject_options"][0]
    rendered = "\n".join([f"Subject: {subject}", "", draft["body"], ""])
    _validate_copy_text(
        rendered,
        target_labels=set(next_draft.get("target_labels") or [next_draft["target_label"]]),
        message_module=message_module,
    )
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the next verified pending validation outreach draft."
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
        choices=("json", "markdown", "send-text"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--require-date",
        help="Require the message pack generated_for date to match YYYY-MM-DD.",
    )
    parser.add_argument("--out", help="Optional path to write the rendered draft.")
    args = parser.parse_args(argv)
    try:
        pack = _load_json_object(Path(args.message_pack), "message pack")
        targets = _load_json_object(Path(args.targets), "target tracker")
        next_draft = build_next_draft(pack, targets, require_date=args.require_date)
    except (OSError, json.JSONDecodeError, NextDraftError) as exc:
        print(f"validation next draft failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        rendered = render_markdown(next_draft)
    elif args.format == "send-text":
        rendered = render_send_text(next_draft)
    else:
        rendered = json.dumps(next_draft, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _draft_by_label(pack: dict[str, Any], target_label: str) -> dict[str, Any]:
    for draft in pack.get("drafts", []):
        if draft.get("target_label") == target_label:
            return draft
    raise NextDraftError(f"draft not found for target: {target_label}")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NextDraftError(f"{label} must be a JSON object")
    return value


def _validate_copy_text(
    rendered: str,
    *,
    target_labels: set[str],
    message_module: Any,
) -> None:
    blocked_literals = (
        "make validation-",
        "python3 scripts/validation-",
        "CONFIRM_SENT",
        "Tracker update command",
        "Safe dry-run",
        "Confirmed-send",
    )
    for target_label in target_labels:
        if target_label in rendered:
            raise NextDraftError(f"copy-only send text contains target label: {target_label}")
    for literal in blocked_literals:
        if literal in rendered:
            raise NextDraftError(
                f"copy-only send text contains tracker metadata: {literal}"
            )
    for regex_name, label in (
        ("EMAIL_RE", "email-like text"),
        ("URL_RE", "URL-like text"),
        ("PHONE_RE", "phone-like text"),
        ("PRIVATE_HOST_RE", "private hostname-like text"),
    ):
        regex = getattr(message_module, regex_name, None)
        if regex is not None and regex.search(rendered):
            raise NextDraftError(f"copy-only send text contains {label}")
    if re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", rendered):
        raise NextDraftError("copy-only send text contains IP-like text")


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise NextDraftError(f"require-date must be YYYY-MM-DD: {value}") from exc


def _load_module(filename: str, module_name: str) -> Any:
    script_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise NextDraftError(f"could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
