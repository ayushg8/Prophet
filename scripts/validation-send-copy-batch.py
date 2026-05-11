#!/usr/bin/env python3
"""Write copy-only send files for verified Prophet validation outreach drafts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


SEND_COPY_BATCH_SCHEMA_VERSION = "prophet_validation_send_copy_batch.v0.1"
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")


class SendCopyBatchError(ValueError):
    """Raised when copy-only send files cannot be written safely."""


def write_send_copy_batch(
    pack: dict[str, Any],
    targets_value: dict[str, Any],
    *,
    out_dir: Path,
    require_date: str | None = None,
) -> dict[str, Any]:
    if require_date is not None:
        _validate_date(require_date)
    status_module = _load_module("validation-outreach-status.py", "validation_outreach_status")
    message_module = _load_module("validation-message-pack.py", "validation_message_pack")
    status = status_module.build_status(
        pack,
        targets_value,
        verify_dry_run_commands=True,
        require_date=require_date,
    )
    if status["counts"]["needs_attention"]:
        labels = [
            item["target_label"]
            for item in status["items"]
            if item["state"] == "needs_attention"
        ]
        raise SendCopyBatchError(
            "outreach pack needs attention before copy files can be written: "
            + ", ".join(labels)
        )

    pending = [
        item
        for item in status["items"]
        if item["state"] == "pending_send_or_update"
        and item.get("dry_run_verification", {}).get("ok") is True
    ]
    drafts_by_label = {
        draft["target_label"]: draft
        for draft in pack.get("drafts", [])
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _remove_generated_copy_files(out_dir)

    files = []
    for ordinal, item in enumerate(pending, start=1):
        draft = drafts_by_label.get(item["target_label"])
        if draft is None:
            raise SendCopyBatchError(f"draft not found for target: {item['target_label']}")
        filtered_pack = dict(pack)
        filtered_pack["drafts"] = [draft]
        filtered_pack["draft_count"] = 1
        try:
            rendered = message_module.render_send_text(filtered_pack)
        except ValueError as exc:
            raise SendCopyBatchError(str(exc)) from exc
        _validate_copy_text(
            rendered,
            target_labels=set(drafts_by_label),
            message_module=message_module,
        )
        path = out_dir / f"{ordinal:02d}.txt"
        path.write_text(rendered, encoding="utf-8")
        files.append(
            {
                "ordinal": ordinal,
                "target_label": item["target_label"],
                "group": item["group"],
                "path": str(path),
                "subject": _subject_from_copy_text(rendered),
                "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                "dry_run_apply_command": item.get("dry_run_apply_command"),
                "confirmed_apply_command": item.get("confirmed_apply_command"),
            }
        )

    readme_path = out_dir / "README.md"
    readme_path.write_text(
        _render_operator_readme(
            generated_for=status["generated_for"],
            copy_file_count=len(files),
        ),
        encoding="utf-8",
    )
    checklist_path = out_dir / "CHECKLIST.md"
    checklist_path.write_text(
        _render_operator_checklist(
            generated_for=status["generated_for"],
            files=files,
        ),
        encoding="utf-8",
    )
    copy_index_path = out_dir / "COPY_ONLY_INDEX.md"
    copy_index_path.write_text(
        _render_copy_only_index(
            generated_for=status["generated_for"],
            files=files,
        ),
        encoding="utf-8",
    )
    subject_order_path = out_dir / "SUBJECT_ORDER.md"
    subject_order_path.write_text(
        _render_subject_order(
            generated_for=status["generated_for"],
            files=files,
        ),
        encoding="utf-8",
    )

    return {
        "schema_version": SEND_COPY_BATCH_SCHEMA_VERSION,
        "message_pack_schema_version": pack["schema_version"],
        "status_schema_version": status["schema_version"],
        "generated_for": status["generated_for"],
        "outbound_safe": False,
        "copy_files_outbound_safe": True,
        "operator_metadata_outbound_safe": False,
        "private_metadata": True,
        "send_boundary": "copy_numbered_txt_contents_only",
        "out_dir": str(out_dir),
        "readme_path": str(readme_path),
        "checklist_path": str(checklist_path),
        "copy_index_path": str(copy_index_path),
        "subject_order_path": str(subject_order_path),
        "copy_file_count": len(files),
        "pending_send_or_update_count": status["counts"]["pending_send_or_update"],
        "needs_attention_count": status["counts"]["needs_attention"],
        "dry_run_verified_count": status["dry_run_verified_count"],
        "files": files,
        "operator_notes": [
            "Each file contains only one subject line and body text; copy the contents, do not attach the file.",
            "Do not paste target labels, tracker commands, the manifest, the batch checklist, the copy index, the subject order helper, or the batch README to buyers.",
            "Run the matching dry-run command before sending each file's contents.",
            "Run the matching CONFIRM_SENT=1 command only after that message was actually sent.",
            f"Rerun make validation-status DATE={status['generated_for']} after confirmed tracker updates.",
        ],
    }


def check_send_copy_directory(
    out_dir: Path,
    *,
    require_date: str | None = None,
) -> dict[str, Any]:
    if require_date is not None:
        _validate_date(require_date)
    if not out_dir.is_dir():
        raise SendCopyBatchError(f"send-copy directory not found: {out_dir}")
    message_module = _load_module("validation-message-pack.py", "validation_message_pack")
    manifest_path = out_dir / "manifest.json"
    manifest = _load_json_object(manifest_path, "send-copy manifest")
    if manifest.get("schema_version") != SEND_COPY_BATCH_SCHEMA_VERSION:
        raise SendCopyBatchError("send-copy manifest schema_version is unsupported")
    generated_for = str(manifest.get("generated_for") or "")
    if require_date is not None and generated_for != require_date:
        raise SendCopyBatchError(
            f"send-copy batch date {generated_for} does not match required date {require_date}"
        )
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise SendCopyBatchError("send-copy manifest must list copy files")
    target_labels = {
        str(file.get("target_label"))
        for file in files
        if isinstance(file, dict) and file.get("target_label")
    }
    checked_files = []
    for file in files:
        if not isinstance(file, dict):
            raise SendCopyBatchError("send-copy manifest file entries must be objects")
        path = Path(str(file.get("path") or ""))
        if not path.is_absolute():
            path = out_dir / path.name
        if path.parent.resolve() != out_dir.resolve():
            raise SendCopyBatchError(f"copy file must stay inside send-copy directory: {path}")
        if not re.fullmatch(r"[0-9][0-9]\.txt", path.name):
            raise SendCopyBatchError(f"copy file name must be neutral and numbered: {path.name}")
        rendered = path.read_text(encoding="utf-8")
        _validate_copy_text(
            rendered,
            target_labels=target_labels,
            message_module=message_module,
        )
        subject_count = sum(1 for line in rendered.splitlines() if line.startswith("Subject: "))
        if subject_count != 1:
            raise SendCopyBatchError(
                f"copy file must contain exactly one Subject line: {path.name}"
            )
        expected_sha = str(file.get("sha256") or "")
        actual_sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if expected_sha != actual_sha:
            raise SendCopyBatchError(f"copy file sha256 mismatch: {path.name}")
        checked_files.append(
            {
                "path": str(path),
                "sha256": actual_sha,
                "subject_count": subject_count,
            }
        )
    actual_names = sorted(path.name for path in out_dir.glob("[0-9][0-9].txt"))
    manifest_names = sorted(Path(str(file["path"])).name for file in files)
    if actual_names != manifest_names:
        raise SendCopyBatchError("send-copy directory file list does not match manifest")
    readme_path = _metadata_path(
        manifest.get("readme_path"),
        out_dir=out_dir,
        expected_name="README.md",
    )
    checklist_path = _metadata_path(
        manifest.get("checklist_path"),
        out_dir=out_dir,
        expected_name="CHECKLIST.md",
    )
    copy_index_path = _metadata_path(
        manifest.get("copy_index_path"),
        out_dir=out_dir,
        expected_name="COPY_ONLY_INDEX.md",
    )
    subject_order_path = _metadata_path(
        manifest.get("subject_order_path"),
        out_dir=out_dir,
        expected_name="SUBJECT_ORDER.md",
    )
    _assert_metadata_body(
        readme_path,
        _render_operator_readme(
            generated_for=generated_for,
            copy_file_count=len(files),
        ),
    )
    _assert_metadata_body(
        checklist_path,
        _render_operator_checklist(
            generated_for=generated_for,
            files=files,
        ),
    )
    _assert_metadata_body(
        copy_index_path,
        _render_copy_only_index(
            generated_for=generated_for,
            files=files,
        ),
    )
    _assert_metadata_body(
        subject_order_path,
        _render_subject_order(
            generated_for=generated_for,
            files=files,
        ),
    )
    return {
        "schema_version": "prophet_validation_send_copy_batch_check.v0.1",
        "generated_for": generated_for,
        "out_dir": str(out_dir),
        "copy_file_count": len(checked_files),
        "copy_files_outbound_safe": True,
        "operator_metadata_outbound_safe": False,
        "operator_metadata_private_by_design": True,
        "operator_metadata_send_boundary": "private_do_not_send",
        "send_boundary": "copy_numbered_txt_contents_only",
        "readme_exists": True,
        "readme_matches_manifest": True,
        "checklist_exists": True,
        "checklist_matches_manifest": True,
        "copy_index_exists": True,
        "copy_index_matches_manifest": True,
        "subject_order_exists": True,
        "subject_order_matches_manifest": True,
        "checked_files": checked_files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write copy-only text files for verified validation outreach drafts."
    )
    parser.add_argument(
        "--check-dir",
        help="Validate an existing send-copy directory without writing files.",
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
        "--require-date",
        help="Require the message pack generated_for date to match YYYY-MM-DD.",
    )
    parser.add_argument(
        "--out-dir",
        help="Directory for copy-only send text files. Defaults to validation/private/send-copy-YYYY-MM-DD.",
    )
    parser.add_argument(
        "--manifest-out",
        help="Optional path for the private JSON manifest. Defaults to OUT_DIR/manifest.json.",
    )
    args = parser.parse_args(argv)

    try:
        if args.check_dir:
            summary = check_send_copy_directory(
                Path(args.check_dir),
                require_date=args.require_date,
            )
            print(json.dumps(summary, indent=2, sort_keys=True))
            return 0
        pack = _load_json_object(Path(args.message_pack), "message pack")
        targets = _load_json_object(Path(args.targets), "target tracker")
        run_date = args.require_date or str(pack.get("generated_for", ""))
        _validate_date(run_date)
        out_dir = Path(args.out_dir) if args.out_dir else Path(
            f"validation/private/send-copy-{run_date}"
        )
        manifest = write_send_copy_batch(
            pack,
            targets,
            out_dir=out_dir,
            require_date=args.require_date,
        )
        manifest_out = Path(args.manifest_out) if args.manifest_out else out_dir / "manifest.json"
        manifest["manifest_path"] = str(manifest_out)
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, SendCopyBatchError) as exc:
        print(f"validation send-copy batch failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _remove_generated_copy_files(out_dir: Path) -> None:
    generated = {
        *out_dir.glob("[0-9][0-9].txt"),
        *out_dir.glob("[0-9][0-9]-*.txt"),
    }
    for path in generated:
        if path.is_file():
            path.unlink()


def _render_operator_readme(*, generated_for: str, copy_file_count: int) -> str:
    return "\n".join(
        [
            "# Prophet Send-Copy Batch",
            "",
            f"Date: {generated_for}",
            f"Copy files: {copy_file_count}",
            "",
            "## Outbound Boundary",
            "",
            "- Open each numbered `.txt` file and copy only its contents into the outreach channel.",
            "- Do not attach the `.txt` files; filenames and this directory are private operator workflow.",
            "- `COPY_ONLY_INDEX.md` is a neutral operator aid for send order, not buyer collateral.",
            "- `SUBJECT_ORDER.md` is a private subject/file-order helper, not buyer collateral.",
            "- Do not send `manifest.json`, `CHECKLIST.md`, `COPY_ONLY_INDEX.md`, `SUBJECT_ORDER.md`, or this README.",
            "- Each `.txt` file should contain only one `Subject:` line and the message body.",
            "- Copy the generated subject/body as-is, or personalize only in the outreach channel after pasting.",
            "- Do not store recipient names or private contact details in repo files.",
            "",
            "## Tracker Boundary",
            "",
            "- Use `manifest.json`, `CHECKLIST.md`, `COPY_ONLY_INDEX.md`, and `SUBJECT_ORDER.md` only as private tracker/operator metadata.",
            f"- Before using an existing batch, run `make validation-send-copy-check DATE={generated_for}`.",
            "- The manifest records a SHA-256 for each copy-only `.txt` file.",
            "- Run each matching dry-run command from the manifest before sending.",
            "- Run each matching confirmed command only after that message was actually sent.",
            f"- Rerun `make validation-status DATE={generated_for}` after confirmed tracker updates.",
            "",
        ]
    )


def _render_operator_checklist(
    *,
    generated_for: str,
    files: list[dict[str, Any]],
) -> str:
    lines = [
        "# Prophet Send-Copy Batch Checklist",
        "",
        f"Date: {generated_for}",
        "",
        "This is private tracker/audit metadata. Do not send this checklist, target labels, or commands to buyers.",
        "",
        f"Before sending, run `make validation-send-copy-check DATE={generated_for}` and proceed only if it passes.",
        "",
        "For each row:",
        "",
        "1. Run the dry-run command.",
        "2. Open the numbered `.txt` file and send only its contents.",
        "3. Run the confirmed command only after the message was actually sent.",
        "",
        "| Sent | File | Group | Target | Dry-run command | Confirmed-send command |",
        "|---|---|---|---|---|---|",
    ]
    for file in files:
        lines.append(
            "| [ ] "
            f"| `{Path(str(file['path'])).name}` "
            f"| `{file['group']}` "
            f"| `{file['target_label']}` "
            f"| `{file['dry_run_apply_command']}` "
            f"| `{file['confirmed_apply_command']}` |"
        )
    lines.extend(
        [
            "",
            "## After Confirmed Sends",
            "",
            f"- Rerun `make validation-status DATE={generated_for}`.",
            f"- Rerun `make validation-dashboard DATE={generated_for}`.",
            "- Log only sanitized buyer outcomes in `validation/private/`.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_copy_only_index(
    *,
    generated_for: str,
    files: list[dict[str, Any]],
) -> str:
    lines = [
        "# Prophet Copy-Only Send Index",
        "",
        f"Date: {generated_for}",
        "",
        "This index intentionally omits target labels and tracker commands.",
        "Use it only to step through the numbered copy-only files.",
        "",
        "| File | Draft group | Outbound contents |",
        "|---|---|---|",
    ]
    for file in files:
        lines.append(
            f"| `{Path(str(file['path'])).name}` "
            f"| `{file['group']}` "
            "| Copy the file contents only. |"
        )
    lines.extend(
        [
            "",
            "Do not attach this index, the manifest, checklist, README, or the `.txt` files.",
            "After real sends, use the private status workflow to verify tracker state.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_subject_order(
    *,
    generated_for: str,
    files: list[dict[str, Any]],
) -> str:
    lines = [
        "# Prophet Copy-Only Subject Order",
        "",
        f"Date: {generated_for}",
        "",
        "Use this private helper to send the numbered copy-only `.txt` files in order.",
        "Do not attach this file, the manifest, checklist, README, or copy index.",
        "Send only the contents of each numbered `.txt` file.",
        "",
        "| File | Subject |",
        "|---|---|",
    ]
    for file in files:
        lines.append(
            f"| `{Path(str(file['path'])).name}` | {file['subject']} |"
        )
    lines.extend(
        [
            "",
            "After each real send, use the matching row in `CHECKLIST.md` to run the",
            "corresponding confirmed tracker update. Do not run `CONFIRM_SENT=1` before the",
            "message is actually sent.",
            "",
        ]
    )
    return "\n".join(lines)


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
        "target-",
        "validation/private",
        "manifest.json",
        "CHECKLIST.md",
        "COPY_ONLY_INDEX.md",
        "SUBJECT_ORDER.md",
        "Tracker update command",
        "Safe dry-run",
        "Confirmed-send",
        "Dry-run command",
        "Confirmed-send command",
    )
    for label in target_labels:
        if label in rendered:
            raise SendCopyBatchError(f"copy-only send text contains target label: {label}")
    for literal in blocked_literals:
        if literal in rendered:
            raise SendCopyBatchError(
                f"copy-only send text contains tracker metadata: {literal}"
            )
    if re.search(r"<[^>\n]+>", rendered):
        raise SendCopyBatchError("copy-only send text contains placeholder text")
    for regex_name, label in (
        ("EMAIL_RE", "email-like text"),
        ("URL_RE", "URL-like text"),
        ("PHONE_RE", "phone-like text"),
        ("PRIVATE_HOST_RE", "private hostname-like text"),
    ):
        regex = getattr(message_module, regex_name, None)
        if regex is not None and regex.search(rendered):
            raise SendCopyBatchError(f"copy-only send text contains {label}")
    if re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", rendered):
        raise SendCopyBatchError("copy-only send text contains IP-like text")


def _subject_from_copy_text(rendered: str) -> str:
    subjects = [
        line.removeprefix("Subject: ").strip()
        for line in rendered.splitlines()
        if line.startswith("Subject: ")
    ]
    if len(subjects) != 1 or not subjects[0]:
        raise SendCopyBatchError("copy-only send text must contain exactly one subject")
    return subjects[0]


def _metadata_path(raw_path: object, *, out_dir: Path, expected_name: str) -> Path:
    path = Path(str(raw_path or expected_name))
    if not path.is_absolute():
        path = out_dir / path.name
    if path.parent.resolve() != out_dir.resolve():
        raise SendCopyBatchError(
            f"send-copy metadata must stay inside send-copy directory: {path}"
        )
    if path.name != expected_name:
        raise SendCopyBatchError(
            f"send-copy metadata path must be {expected_name}: {path.name}"
        )
    if not path.is_file():
        raise SendCopyBatchError(f"send-copy metadata file is missing: {expected_name}")
    return path


def _assert_metadata_body(path: Path, expected: str) -> None:
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        raise SendCopyBatchError(f"send-copy metadata file is stale: {path.name}")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SendCopyBatchError(f"{label} must be a JSON object")
    return value


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise SendCopyBatchError(f"require-date must be YYYY-MM-DD: {value}") from exc


def _load_module(filename: str, module_name: str) -> Any:
    script_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise SendCopyBatchError(f"could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
