#!/usr/bin/env python3
"""Apply a generated outreach draft tracker update after a confirmed send."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")


class ApplyDraftUpdateError(ValueError):
    """Raised when a generated draft update cannot be applied safely."""


def build_update_summary(
    pack: dict[str, Any],
    targets_value: dict[str, Any],
    *,
    target_label: str,
    confirm_sent: bool = False,
    require_date: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if require_date is not None:
        _validate_date(require_date)
    status_module = _load_module("validation-outreach-status.py", "validation_outreach_status")
    target_update_module = _load_module("validation-target-update.py", "validation_target_update")
    status = status_module.build_status(
        pack,
        targets_value,
        verify_dry_run_commands=True,
    )
    if require_date is not None and status["generated_for"] != require_date:
        raise ApplyDraftUpdateError(
            "message pack generated_for "
            f"{status['generated_for']} does not match required date {require_date}"
        )
    if status["counts"]["needs_attention"]:
        labels = [
            item["target_label"]
            for item in status["items"]
            if item["state"] == "needs_attention"
        ]
        raise ApplyDraftUpdateError(
            "outreach pack needs attention before applying updates: "
            + ", ".join(labels)
        )
    item = _status_item_by_label(status, target_label)
    if item["state"] != "pending_send_or_update":
        raise ApplyDraftUpdateError(
            f"{target_label} is {item['state']}; no confirmed-send update should be applied"
        )
    verification = item.get("dry_run_verification") or {}
    if verification.get("ok") is not True:
        raise ApplyDraftUpdateError(f"{target_label} generated update did not verify")
    expected = item["expected"]
    updated_targets = copy.deepcopy(targets_value)
    update_summary = target_update_module.update_target(
        updated_targets,
        target_label=expected["target_label"],
        status=expected["status"],
        last_touch=expected["last_touch"],
        follow_up_due=expected["follow_up_due"],
        next_action=expected["next_action"],
        updated_at=expected["last_touch"],
        require_current_status=expected["require_current_status"],
    )
    return (
        {
            "ok": True,
            "target_label": target_label,
            "generated_for": status["generated_for"],
            "confirmed_sent": confirm_sent,
            "would_write": confirm_sent,
            "state_before_update": item["state"],
            "dry_run_apply_command": item.get("dry_run_apply_command"),
            "confirmed_apply_command": item.get("confirmed_apply_command"),
            "status_command": f"make validation-status DATE={status['generated_for']}",
            "dashboard_command": f"make validation-dashboard DATE={status['generated_for']}",
            "tracker_update": update_summary,
            "operator_notes": [
                "This helper does not send outreach.",
                "Use --confirm-sent, or CONFIRM_SENT=1 through Make, only after the message was actually sent.",
                f"Run make validation-status DATE={status['generated_for']} after writing the private tracker.",
            ],
        },
        updated_targets,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the generated validation target update for one outreach draft. "
            "Defaults to dry-run; write only with --confirm-sent."
        )
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
    parser.add_argument("--target-label", required=True)
    parser.add_argument(
        "--require-date",
        help="Require the message pack generated_for date to match YYYY-MM-DD.",
    )
    parser.add_argument(
        "--confirm-sent",
        action="store_true",
        help="Write the generated tracker update after the outreach message was actually sent.",
    )
    parser.add_argument(
        "--require-copy-artifact",
        action="store_true",
        help=(
            "Require a matching copy-only send artifact before writing. "
            "Use with --send-copy and/or --send-copy-batch-manifest."
        ),
    )
    parser.add_argument(
        "--send-copy",
        help="Optional copy-only send text path to verify for the selected target.",
    )
    parser.add_argument(
        "--send-copy-batch-manifest",
        help="Optional private send-copy batch manifest to verify for the selected target.",
    )
    parser.add_argument("--out", help="Optional target tracker output path.")
    args = parser.parse_args(argv)
    targets_path = Path(args.targets)
    try:
        pack = _load_json_object(Path(args.message_pack), "message pack")
        targets = _load_json_object(targets_path, "target tracker")
        summary, updated_targets = build_update_summary(
            pack,
            targets,
            target_label=args.target_label,
            confirm_sent=args.confirm_sent,
            require_date=args.require_date,
        )
        if args.confirm_sent and not args.require_copy_artifact:
            raise ApplyDraftUpdateError(
                "confirmed tracker writes require --require-copy-artifact "
                "with --send-copy or --send-copy-batch-manifest"
            )
        if args.require_copy_artifact:
            summary["copy_artifact_verification"] = _verify_copy_artifact(
                pack,
                target_label=args.target_label,
                generated_for=summary["generated_for"],
                send_copy_path=Path(args.send_copy) if args.send_copy else None,
                send_copy_batch_manifest=(
                    Path(args.send_copy_batch_manifest)
                    if args.send_copy_batch_manifest
                    else None
                ),
            )
    except (OSError, json.JSONDecodeError, ApplyDraftUpdateError) as exc:
        print(f"validation apply draft update failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.confirm_sent:
        out_path = Path(args.out) if args.out else targets_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(updated_targets, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


def _status_item_by_label(status: dict[str, Any], target_label: str) -> dict[str, Any]:
    for item in status["items"]:
        if item["target_label"] == target_label:
            return item
    raise ApplyDraftUpdateError(f"target_label not found in message pack: {target_label}")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ApplyDraftUpdateError(f"{label} must be a JSON object")
    return value


def _verify_copy_artifact(
    pack: dict[str, Any],
    *,
    target_label: str,
    generated_for: str,
    send_copy_path: Path | None,
    send_copy_batch_manifest: Path | None,
) -> dict[str, Any]:
    expected = _render_expected_send_text(pack, target_label)
    errors: list[str] = []
    if send_copy_path is not None:
        if send_copy_path.exists():
            actual = send_copy_path.read_text(encoding="utf-8")
            if actual == expected:
                return {
                    "ok": True,
                    "kind": "send_copy",
                    "path": str(send_copy_path),
                    "target_label": target_label,
                }
            errors.append(f"{send_copy_path} does not match {target_label}")
        else:
            errors.append(f"{send_copy_path} is missing")
    if send_copy_batch_manifest is not None:
        batch_result = _verify_copy_batch_manifest(
            send_copy_batch_manifest,
            target_label=target_label,
            generated_for=generated_for,
            expected=expected,
        )
        if batch_result.get("ok"):
            return batch_result
        errors.extend(batch_result["errors"])
    if send_copy_path is None and send_copy_batch_manifest is None:
        errors.append("no copy-only send artifact path was provided")
    raise ApplyDraftUpdateError(
        "copy-only send artifact is not ready for confirmed tracker update: "
        + "; ".join(errors)
    )


def _verify_copy_batch_manifest(
    manifest_path: Path,
    *,
    target_label: str,
    generated_for: str,
    expected: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if not manifest_path.exists():
        return {"ok": False, "errors": [f"{manifest_path} is missing"]}
    manifest = _load_json_object(manifest_path, "send-copy batch manifest")
    if manifest.get("generated_for") != generated_for:
        errors.append(
            f"{manifest_path} generated_for {manifest.get('generated_for')} "
            f"does not match {generated_for}"
        )
    matching = [
        item
        for item in manifest.get("files", [])
        if isinstance(item, dict) and item.get("target_label") == target_label
    ]
    if len(matching) != 1:
        errors.append(f"{manifest_path} does not contain exactly one file for {target_label}")
        return {"ok": False, "errors": errors}
    copy_path = Path(str(matching[0].get("path", "")))
    if not copy_path.exists():
        errors.append(f"{copy_path} from {manifest_path} is missing")
        return {"ok": False, "errors": errors}
    actual = copy_path.read_text(encoding="utf-8")
    if actual != expected:
        errors.append(f"{copy_path} from {manifest_path} does not match {target_label}")
        return {"ok": False, "errors": errors}
    if errors:
        return {"ok": False, "errors": errors}
    return {
        "ok": True,
        "kind": "send_copy_batch",
        "manifest_path": str(manifest_path),
        "path": str(copy_path),
        "target_label": target_label,
    }


def _render_expected_send_text(pack: dict[str, Any], target_label: str) -> str:
    message_module = _load_module("validation-message-pack.py", "validation_message_pack")
    filtered = message_module.filter_pack_by_target_label(pack, target_label)
    return message_module.render_send_text(filtered)


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ApplyDraftUpdateError(f"require-date must be YYYY-MM-DD: {value}") from exc


def _load_module(filename: str, module_name: str) -> Any:
    script_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ApplyDraftUpdateError(f"could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
