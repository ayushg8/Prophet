#!/usr/bin/env python3
"""Verify the whole Prophet validation send batch before outbound work."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_SEND_COPY_DIR_TEMPLATE = "validation/private/send-copy-{date}"
DEFAULT_CONTACT_FORM_COPY_DIR_TEMPLATE = "validation/private/contact-form-copy-{date}"
PRE_SEND_ALL_SCHEMA_VERSION = "prophet_validation_pre_send_all.v0.1"


class PreSendAllError(ValueError):
    """Raised when the full pre-send batch is not safe to use."""


def build_pre_send_all_summary(
    pack: dict[str, Any],
    targets_value: dict[str, Any],
    *,
    send_copy_dir: Path,
    contact_form_copy_dir: Path | None = None,
    require_date: str | None = None,
) -> dict[str, Any]:
    status_module = _load_module("validation-outreach-status.py", "validation_outreach_status")
    send_copy_module = _load_module("validation-send-copy-batch.py", "validation_send_copy_batch")
    status = status_module.build_status(
        pack,
        targets_value,
        verify_dry_run_commands=True,
        require_date=require_date,
    )
    generated_for = status["generated_for"]
    if require_date is not None and generated_for != require_date:
        raise PreSendAllError(
            f"message pack generated_for {generated_for} does not match required date {require_date}"
        )
    batch = send_copy_module.check_send_copy_directory(
        send_copy_dir,
        require_date=require_date,
    )
    if status["counts"]["needs_attention"]:
        labels = [
            item["target_label"]
            for item in status["items"]
            if item["state"] == "needs_attention"
        ]
        raise PreSendAllError(
            "outreach pack needs attention before sending: " + ", ".join(labels)
        )
    pending = [
        item
        for item in status["items"]
        if item["state"] == "pending_send_or_update"
    ]
    if batch["copy_file_count"] != len(pending):
        raise PreSendAllError(
            "send-copy batch file count does not match pending draft count: "
            f"{batch['copy_file_count']} file(s), {len(pending)} pending draft(s)"
        )
    contact_summary: dict[str, Any] | None = None
    contact_files_by_target: dict[str, Any] = {}
    if contact_form_copy_dir is not None and contact_form_copy_dir.exists():
        contact_form_module = _load_module(
            "validation-contact-form-copy.py",
            "validation_contact_form_copy",
        )
        try:
            contact_summary = contact_form_module.check_contact_form_copy_directory(
                contact_form_copy_dir,
                require_date=require_date,
            )
        except Exception as exc:
            raise PreSendAllError(f"contact-form copy check failed: {exc}") from exc
        if contact_summary["copy_file_count"] != len(pending):
            raise PreSendAllError(
                "contact-form copy file count does not match pending draft count: "
                f"{contact_summary['copy_file_count']} file(s), "
                f"{len(pending)} pending draft(s)"
            )
        contact_manifest = _load_json_object(
            contact_form_copy_dir / "manifest.json",
            "contact-form copy manifest",
        )
        contact_files_by_target = {
            str(file["target_label"]): file
            for file in contact_manifest.get("files", [])
            if isinstance(file, dict) and file.get("target_label")
        }
    manifest = _load_json_object(send_copy_dir / "manifest.json", "send-copy manifest")
    files_by_target = {
        str(file["target_label"]): file
        for file in manifest.get("files", [])
        if isinstance(file, dict) and file.get("target_label")
    }
    target_checks = []
    for item in pending:
        verification = item.get("dry_run_verification") or {}
        if verification.get("ok") is not True:
            raise PreSendAllError(
                f"{item['target_label']} dry-run verification did not pass"
            )
        file = files_by_target.get(item["target_label"])
        if file is None:
            raise PreSendAllError(
                f"send-copy manifest has no numbered file for {item['target_label']}"
            )
        contact_file = None
        if contact_summary is not None:
            contact_file = contact_files_by_target.get(item["target_label"])
            if contact_file is None:
                raise PreSendAllError(
                    "contact-form copy manifest has no numbered file for "
                    f"{item['target_label']}"
                )
        target_checks.append(
            {
                "target_label": item["target_label"],
                "group": item["group"],
                "copy_file": Path(str(file["path"])).name,
                "contact_form_copy_file": (
                    Path(str(contact_file["path"])).name
                    if contact_file is not None
                    else "not_present"
                ),
                "dry_run_apply_command": item.get("dry_run_apply_command"),
                "pre_send_check_command": file.get("pre_send_check_command"),
                "confirmed_apply_command": item.get("confirmed_apply_command"),
                "dry_run_verified": True,
                "would_write": False,
            }
        )
    return {
        "schema_version": PRE_SEND_ALL_SCHEMA_VERSION,
        "generated_for": generated_for,
        "ok": True,
        "send_boundary": "copy_numbered_txt_contents_only",
        "send_copy_dir": str(send_copy_dir),
        "copy_file_count": batch["copy_file_count"],
        "contact_form_copy_state": "checked" if contact_summary is not None else "not_present",
        "contact_form_copy_dir": (
            str(contact_form_copy_dir) if contact_form_copy_dir is not None else None
        ),
        "contact_form_copy_file_count": (
            contact_summary["copy_file_count"] if contact_summary is not None else 0
        ),
        "contact_form_copy_send_boundary": (
            contact_summary["send_boundary"] if contact_summary is not None else None
        ),
        "pending_send_or_update_count": status["counts"]["pending_send_or_update"],
        "needs_attention_count": status["counts"]["needs_attention"],
        "dry_run_verified_count": status["dry_run_verified_count"],
        "dry_run_failed_count": status["dry_run_failed_count"],
        "target_checks": target_checks,
        "operator_notes": [
            "This helper is dry-run only and does not send outreach.",
            "Send only the contents of the numbered .txt files.",
            "Run the matching CONFIRM_SENT=1 command only after each message is actually sent.",
            f"Rerun make validation-status DATE={generated_for} after confirmed tracker updates.",
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Prophet Full Pre-Send Check - {summary['generated_for']}",
        "",
        f"- OK: {str(summary['ok']).lower()}",
        f"- Send boundary: {summary['send_boundary']}",
        f"- Send-copy directory: `{summary['send_copy_dir']}`",
        f"- Copy files: {summary['copy_file_count']}",
        f"- Contact-form copy state: {summary['contact_form_copy_state']}",
        f"- Contact-form copy directory: `{summary['contact_form_copy_dir']}`",
        f"- Contact-form copy files: {summary['contact_form_copy_file_count']}",
        f"- Pending send/update: {summary['pending_send_or_update_count']}",
        f"- Needs attention: {summary['needs_attention_count']}",
        f"- Dry-run verified: {summary['dry_run_verified_count']}",
        f"- Dry-run failed: {summary['dry_run_failed_count']}",
        "",
        "## Target Checks",
    ]
    for check in summary["target_checks"]:
        lines.extend(
            [
                "",
                f"### {check['copy_file']} - {check['target_label']}",
                "",
                f"- Group: {check['group']}",
                f"- Dry-run verified: {str(check['dry_run_verified']).lower()}",
                f"- Would write during this check: {str(check['would_write']).lower()}",
                f"- Contact-form copy file: `{check['contact_form_copy_file']}`",
                f"- Dry-run command: `{check['dry_run_apply_command']}`",
                f"- Pre-send command: `{check['pre_send_check_command']}`",
                f"- Confirmed-send command: `{check['confirmed_apply_command']}`",
            ]
        )
    lines.extend(["", "## Operator Notes"])
    for note in summary["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run verify every pending copy-only outreach draft before sending."
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
        "--send-copy-dir",
        help="Path to an existing send-copy-YYYY-MM-DD directory.",
    )
    parser.add_argument(
        "--contact-form-copy-dir",
        help=(
            "Path to an existing contact-form-copy-YYYY-MM-DD directory. "
            "If the directory exists, it is validated as part of the pre-send gate."
        ),
    )
    parser.add_argument(
        "--require-date",
        help="Require the message pack and send-copy batch date to match YYYY-MM-DD.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
    )
    args = parser.parse_args(argv)
    try:
        pack = _load_json_object(Path(args.message_pack), "message pack")
        generated_for = str(args.require_date or pack.get("generated_for") or "")
        send_copy_dir = (
            Path(args.send_copy_dir)
            if args.send_copy_dir
            else Path(DEFAULT_SEND_COPY_DIR_TEMPLATE.format(date=generated_for))
        )
        contact_form_copy_dir = (
            Path(args.contact_form_copy_dir)
            if args.contact_form_copy_dir
            else Path(DEFAULT_CONTACT_FORM_COPY_DIR_TEMPLATE.format(date=generated_for))
        )
        summary = build_pre_send_all_summary(
            pack,
            _load_json_object(Path(args.targets), "target tracker"),
            send_copy_dir=send_copy_dir,
            contact_form_copy_dir=contact_form_copy_dir,
            require_date=args.require_date,
        )
    except (OSError, json.JSONDecodeError, PreSendAllError) as exc:
        print(f"validation pre-send all failed: {exc}", file=sys.stderr)
        return 1
    if args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreSendAllError(f"{label} must be a JSON object")
    return value


def _load_module(filename: str, module_name: str) -> Any:
    script_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise PreSendAllError(f"could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
