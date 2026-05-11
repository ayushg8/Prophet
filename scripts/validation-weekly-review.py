#!/usr/bin/env python3
"""Build a read-only weekly review for the Prophet validation sprint."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


WEEKLY_REVIEW_SCHEMA_VERSION = "prophet_validation_weekly_review.v0.1"
DEFAULT_PRIVATE_DIR = Path("validation/private")
DEFAULT_TARGETS = DEFAULT_PRIVATE_DIR / "validation-targets.json"
DEFAULT_LOG = DEFAULT_PRIVATE_DIR / "customer-validation-log.json"
DEFAULT_MESSAGE_PACK = DEFAULT_PRIVATE_DIR / "today-message-pack.json"
DEFAULT_STALE_DAYS = 7


class WeeklyReviewError(ValueError):
    """Raised when a weekly review cannot be built safely."""


def build_weekly_review(
    *,
    private_dir: Path,
    targets_path: Path,
    log_path: Path,
    message_pack_path: Path,
    review_date: str | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> dict[str, Any]:
    run_date = _parse_date(review_date or date.today().isoformat(), "review-date")
    if stale_days < 1:
        raise WeeklyReviewError("stale-days must be positive")

    targets_value = _load_json_object(targets_path, "target tracker")
    log_value = _load_json_object(log_path, "validation log")
    target_scorecard_module = _load_script_module("validation_targets_scorecard")
    customer_scorecard_module = _load_script_module("customer_validation_scorecard")
    target_errors = target_scorecard_module.validate_targets(targets_value)
    if target_errors:
        raise WeeklyReviewError("; ".join(target_errors))
    log_errors = customer_scorecard_module.validate_log(log_value)
    if log_errors:
        raise WeeklyReviewError("; ".join(log_errors))

    target_scorecard = target_scorecard_module.build_scorecard(targets_value)
    customer_scorecard = customer_scorecard_module.build_scorecard(log_value)
    dashboard_module = _load_script_module("validation_sprint_dashboard")
    target_backed_validation = dashboard_module._target_backed_validation(
        customer_value=log_value,
        target_value=targets_value,
        customer_module=customer_scorecard_module,
    )
    build_allowed = (
        customer_scorecard["verdict"] == "build_next_slice"
        and target_backed_validation["verdict"] == "build_next_slice"
        and not customer_scorecard["example_seed_log"]
    )
    pack_summary = _message_pack_summary(message_pack_path, run_date)
    outreach_execution = _outreach_execution_summary(
        log_path=log_path,
        targets_path=targets_path,
        message_pack_path=message_pack_path,
        require_date=run_date.isoformat(),
    )
    private_files = _private_file_summary(private_dir, run_date, stale_days)
    pruning = _pruning_candidates(targets_value.get("targets", []), run_date)
    return {
        "schema_version": WEEKLY_REVIEW_SCHEMA_VERSION,
        "review_date": run_date.isoformat(),
        "generated_for": run_date.isoformat(),
        "private_dir": str(private_dir),
        "validation_gate": {
            "verdict": customer_scorecard["verdict"],
            "target_backed_verdict": target_backed_validation["verdict"],
            "example_seed_log": customer_scorecard["example_seed_log"],
            "allowed_to_build_next_slice": build_allowed,
            "reason": dashboard_module._build_gate_reason(
                customer_scorecard["verdict"],
                example_seed_log=bool(customer_scorecard["example_seed_log"]),
                target_backed_validation=target_backed_validation,
            ),
            "effective_validation_counts": customer_scorecard["effective_validation_counts"],
            "gaps_to_verdicts": customer_scorecard["gaps_to_verdicts"],
            "target_backed_validation": target_backed_validation,
            "next_action": customer_scorecard["next_action"],
        },
        "target_pipeline": {
            "active_target_count": target_scorecard["active_target_count"],
            "follow_up_due_count": target_scorecard["follow_up_due_count"],
            "status_counts": target_scorecard["status_counts"],
            "next_action": target_scorecard["next_action"],
        },
        "message_pack": pack_summary,
        "outreach_execution": outreach_execution,
        "private_artifacts": private_files,
        "pruning_candidates": pruning,
        "operator_notes": [
            "Read-only review: no files, targets, or logs were changed.",
            "Do not run CONFIRM_SENT=1, CONFIRM_TARGET=1, or CONFIRM_LOG=1 unless the real external action happened.",
            "Dry-run every pruning or status-update command before any confirmed write.",
            "Keep production build work closed unless the validation dashboard reaches build_next_slice.",
        ],
    }


def render_markdown(review: dict[str, Any]) -> str:
    gate = review["validation_gate"]
    pack = review["message_pack"]
    outreach = review["outreach_execution"]
    artifacts = review["private_artifacts"]
    pruning = review["pruning_candidates"]
    lines = [
        f"# Prophet Weekly Validation Review - {review['generated_for']}",
        "",
        "This is a read-only private operator report. It does not send messages,",
        "delete artifacts, or mutate validation trackers.",
        "",
        "## Validation Gate",
        "",
        f"- Verdict: {gate['verdict']}",
        f"- Target-backed verdict: {gate['target_backed_verdict']}",
        f"- Target-backed qualified calls: {gate['target_backed_validation']['qualified_count']}",
        f"- Target-backed build-gate interviews: {gate['target_backed_validation']['target_backed_interview_count']}",
        f"- Example seed log: {str(gate['example_seed_log']).lower()}",
        f"- Build gate open: {str(gate['allowed_to_build_next_slice']).lower()}",
        f"- Build gate reason: {gate['reason']}",
        f"- Next action: {gate['next_action']}",
        "",
        "## Target Pipeline",
        "",
        f"- Active targets: {review['target_pipeline']['active_target_count']}",
        f"- Follow-ups due: {review['target_pipeline']['follow_up_due_count']}",
        f"- Status counts: {_format_counts(review['target_pipeline']['status_counts'])}",
        "",
        "## Message Pack",
        "",
        f"- Exists: {str(pack['exists']).lower()}",
    ]
    if pack["exists"]:
        lines.extend(
            [
                f"- Generated for: {pack['generated_for']}",
                f"- Draft count: {pack['draft_count']}",
                f"- Age days: {pack['age_days']}",
                f"- Date matches review: {str(pack['date_matches_review']).lower()}",
                f"- Stale for review: {str(pack['stale_for_review']).lower()}",
                f"- Future for review: {str(pack['future_for_review']).lower()}",
            ]
        )
    else:
        lines.append(f"- Missing path: {pack['path']}")
    lines.extend(
        [
            "",
            "## Outreach Execution",
            "",
            f"- Available: {str(outreach['available']).lower()}",
            f"- State: {outreach['state']}",
        ]
    )
    if outreach["available"]:
        counts = outreach["counts"]
        lines.extend(
            [
                f"- Pending send/update: {counts['pending_send_or_update']}",
                f"- Needs attention: {counts['needs_attention']}",
                f"- Dry-run verified: {outreach['dry_run_verified_count']}",
                f"- Send-copy state: {outreach['send_copy_state']}",
                f"- Send-copy matches next draft: {str(outreach['send_copy_matches_next_pending']).lower()}",
                f"- Batch state: {outreach['send_copy_batch_state']}",
                f"- Batch README exists: {str(outreach['send_copy_batch_readme_exists']).lower()}",
                f"- Batch checklist exists: {str(outreach['send_copy_batch_checklist_exists']).lower()}",
                f"- Batch copy index exists: {str(outreach['send_copy_batch_copy_index_exists']).lower()}",
                f"- Batch subject order exists: {str(outreach['send_copy_batch_subject_order_exists']).lower()}",
                f"- Batch matches current pack: {str(outreach['send_copy_batch_matches_current_pack']).lower()}",
            ]
        )
    elif outreach.get("reason"):
        lines.append(f"- Reason: {outreach['reason']}")
    lines.extend(
        [
            "",
            "## Private Artifacts",
            "",
            f"- validation/private ignored: {str(artifacts['private_dir_ignored']).lower()}",
            f"- File count: {artifacts['file_count']}",
            f"- Stale file count: {artifacts['stale_file_count']}",
            f"- Send-copy warning count: {artifacts['send_copy_warning_count']}",
        ]
    )
    if artifacts["stale_files"]:
        lines.extend(["", "Stale ignored private files:"])
        for item in artifacts["stale_files"]:
            lines.append(f"- {item['path']} ({item['age_days']} day(s) old)")
    if artifacts["send_copy_warnings"]:
        lines.extend(["", "Private send-copy warnings:"])
        for item in artifacts["send_copy_warnings"]:
            lines.append(f"- {item['path']}: {', '.join(item['reasons'])}")
    lines.extend(
        [
            "",
            "## Pruning Candidates",
            "",
            f"- Overdue follow-ups: {len(pruning['overdue_follow_ups'])}",
            f"- Outreach sent without follow-up date: {len(pruning['outreach_sent_without_follow_up_due'])}",
            f"- Booked calls awaiting sanitized log: {len(pruning['booked_calls'])}",
            f"- Completed targets: {len(pruning['completed_targets'])}",
            f"- Disqualified targets: {len(pruning['disqualified_targets'])}",
        ]
    )
    for title, key in (
        ("Overdue follow-ups", "overdue_follow_ups"),
        ("Outreach sent without follow-up date", "outreach_sent_without_follow_up_due"),
        ("Booked calls awaiting sanitized log", "booked_calls"),
    ):
        if pruning[key]:
            lines.extend(["", title + ":"])
            for item in pruning[key]:
                lines.append(f"- {item['target_label']}: {item['recommended_dry_run']}")
    lines.extend(["", "## Operator Notes"])
    for note in review["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a read-only weekly Prophet validation sprint review."
    )
    parser.add_argument("--private-dir", default=str(DEFAULT_PRIVATE_DIR))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--message-pack", default=str(DEFAULT_MESSAGE_PACK))
    parser.add_argument("--review-date", help="Review date in YYYY-MM-DD form.")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--out", help="Optional path to write the rendered review.")
    args = parser.parse_args(argv)
    try:
        review = build_weekly_review(
            private_dir=Path(args.private_dir),
            targets_path=Path(args.targets),
            log_path=Path(args.log),
            message_pack_path=Path(args.message_pack),
            review_date=args.review_date,
            stale_days=args.stale_days,
        )
    except (OSError, json.JSONDecodeError, WeeklyReviewError) as exc:
        print(f"validation weekly review failed: {exc}", file=sys.stderr)
        return 1
    rendered = (
        render_markdown(review)
        if args.format == "markdown"
        else json.dumps(review, indent=2, sort_keys=True) + "\n"
    )
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _message_pack_summary(path: Path, run_date: date) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "generated_for": None,
            "draft_count": 0,
            "age_days": None,
            "date_matches_review": False,
            "stale_for_review": False,
            "future_for_review": False,
        }
    value = _load_json_object(path, "message pack")
    generated_for = value.get("generated_for")
    generated_date = _parse_date(generated_for, "message_pack.generated_for")
    draft_count = len(value.get("drafts") or [])
    age_days = (run_date - generated_date).days
    return {
        "exists": True,
        "path": str(path),
        "generated_for": generated_date.isoformat(),
        "draft_count": draft_count,
        "age_days": age_days,
        "date_matches_review": age_days == 0,
        "stale_for_review": age_days > 0,
        "future_for_review": age_days < 0,
    }


def _outreach_execution_summary(
    *,
    log_path: Path,
    targets_path: Path,
    message_pack_path: Path,
    require_date: str,
) -> dict[str, Any]:
    if not message_pack_path.exists():
        return {
            "available": False,
            "state": "missing",
            "reason": f"message pack is missing: {message_pack_path}",
            "counts": {
                "pending_send_or_update": 0,
                "needs_attention": 0,
            },
            "dry_run_verified_count": 0,
            "send_copy_state": "missing",
            "send_copy_matches_next_pending": False,
            "send_copy_batch_state": "missing",
            "send_copy_batch_readme_exists": False,
            "send_copy_batch_checklist_exists": False,
            "send_copy_batch_copy_index_exists": False,
            "send_copy_batch_subject_order_exists": False,
            "send_copy_batch_matches_current_pack": False,
        }
    dashboard_module = _load_script_module("validation_sprint_dashboard")
    try:
        dashboard = dashboard_module.build_dashboard(
            log_path=log_path,
            targets_path=targets_path,
            message_pack_path=message_pack_path,
            require_date=require_date,
            scripts_dir=Path(__file__).parent,
        )
    except Exception as exc:
        return {
            "available": False,
            "state": "error",
            "reason": str(exc),
            "counts": {
                "pending_send_or_update": 0,
                "needs_attention": 0,
            },
            "dry_run_verified_count": 0,
            "send_copy_state": "unknown",
            "send_copy_matches_next_pending": False,
            "send_copy_batch_state": "unknown",
            "send_copy_batch_readme_exists": False,
            "send_copy_batch_checklist_exists": False,
            "send_copy_batch_copy_index_exists": False,
            "send_copy_batch_subject_order_exists": False,
            "send_copy_batch_matches_current_pack": False,
        }
    outreach = dashboard["outreach_execution"]
    return {
        "available": True,
        "state": "ready"
        if outreach.get("send_copy_batch_state") == "ready"
        and outreach.get("send_copy_batch_matches_current_pack") is True
        else "not_ready",
        "counts": outreach["counts"],
        "dry_run_verified_count": outreach["dry_run_verified_count"],
        "send_copy_state": outreach["send_copy_state"],
        "send_copy_matches_next_pending": outreach["send_copy_matches_next_pending"],
        "send_copy_batch_state": outreach["send_copy_batch_state"],
        "send_copy_batch_readme_exists": outreach["send_copy_batch_readme_exists"],
        "send_copy_batch_checklist_exists": outreach["send_copy_batch_checklist_exists"],
        "send_copy_batch_copy_index_exists": outreach["send_copy_batch_copy_index_exists"],
        "send_copy_batch_subject_order_exists": outreach["send_copy_batch_subject_order_exists"],
        "send_copy_batch_matches_current_pack": outreach["send_copy_batch_matches_current_pack"],
    }


def _private_file_summary(
    private_dir: Path,
    run_date: date,
    stale_days: int,
) -> dict[str, Any]:
    files = sorted(
        path
        for path in private_dir.rglob("*")
        if path.is_file() and not _is_atomic_temp_file(path)
    )
    stale_files: list[dict[str, Any]] = []
    for path in files:
        mtime_date = date.fromtimestamp(path.stat().st_mtime)
        age_days = (run_date - mtime_date).days
        if age_days >= stale_days:
            stale_files.append({"path": str(path), "age_days": age_days})
    send_copy_warnings = _send_copy_file_warnings(private_dir, run_date)
    return {
        "private_dir_ignored": _is_ignored(private_dir),
        "file_count": len(files),
        "stale_file_count": len(stale_files),
        "stale_files": stale_files,
        "send_copy_warning_count": len(send_copy_warnings),
        "send_copy_warnings": send_copy_warnings,
    }


def _send_copy_file_warnings(private_dir: Path, run_date: date) -> list[dict[str, Any]]:
    copy_paths = sorted(
        {
            *(private_dir.glob("send-copy-*/*.txt")),
            private_dir / "today-send-copy.txt",
        }
    )
    warnings: list[dict[str, Any]] = []
    for path in copy_paths:
        if not path.is_file():
            continue
        reasons = _send_copy_warning_reasons(path, run_date)
        if reasons:
            warnings.append({"path": str(path), "reasons": reasons})
    return warnings


def _send_copy_warning_reasons(path: Path, run_date: date) -> list[str]:
    reasons: list[str] = []
    batch_date = _send_copy_batch_date(path)
    if batch_date is not None and batch_date != run_date:
        reasons.append("date_mismatch")
    text = path.read_text(encoding="utf-8")
    if re.search(r"<[^>\n]+>", text):
        reasons.append("placeholder_text")
    blocked_literals = (
        "make validation-",
        "python3 scripts/validation-",
        "CONFIRM_SENT",
        "target-",
        "validation/private",
        "manifest.json",
        "CHECKLIST.md",
        "COPY_ONLY_INDEX.md",
        "Tracker update command",
        "Safe dry-run",
        "Confirmed-send",
        "Dry-run command",
        "Confirmed-send command",
    )
    if any(literal in text for literal in blocked_literals):
        reasons.append("tracker_metadata")
    if sum(1 for line in text.splitlines() if line.startswith("Subject: ")) != 1:
        reasons.append("subject_count")
    return reasons


def _send_copy_batch_date(path: Path) -> date | None:
    match = re.fullmatch(r"send-copy-([0-9]{4}-[0-9]{2}-[0-9]{2})", path.parent.name)
    if match is None:
        return None
    return _parse_date(match.group(1), f"{path.parent.name}.date")


def _is_atomic_temp_file(path: Path) -> bool:
    return ".tmp." in path.name


def _pruning_candidates(targets: list[dict[str, Any]], run_date: date) -> dict[str, Any]:
    overdue_follow_ups: list[dict[str, Any]] = []
    sent_without_due: list[dict[str, Any]] = []
    booked_calls: list[dict[str, Any]] = []
    completed_targets: list[dict[str, Any]] = []
    disqualified_targets: list[dict[str, Any]] = []
    for target in targets:
        status = target["status"]
        label = target["target_label"]
        if status == "follow_up_due":
            due = _parse_date(target["follow_up_due"], f"{label}.follow_up_due")
            if due <= run_date:
                overdue_follow_ups.append(
                    {
                        "target_label": label,
                        "follow_up_due": due.isoformat(),
                        "recommended_dry_run": f"make validation-draft-copy TARGET={label} DATE={run_date.isoformat()}",
                    }
                )
        elif status == "outreach_sent":
            follow_up_due = str(target.get("follow_up_due", "")).strip()
            if not follow_up_due:
                sent_without_due.append(
                    {
                        "target_label": label,
                        "recommended_dry_run": f"make validation-status DATE={run_date.isoformat()}",
                    }
                )
            else:
                due = _parse_date(follow_up_due, f"{label}.follow_up_due")
                if due <= run_date:
                    overdue_follow_ups.append(
                        {
                            "target_label": label,
                            "follow_up_due": due.isoformat(),
                            "recommended_dry_run": f"make validation-draft-copy TARGET={label} DATE={run_date.isoformat()}",
                        }
                    )
        elif status == "call_booked":
            booked_calls.append(
                {
                    "target_label": label,
                    "recommended_dry_run": f"make validation-prepare-interview TARGET={label} DATE={run_date.isoformat()}",
                }
            )
        elif status == "completed":
            completed_targets.append({"target_label": label})
        elif status == "disqualified":
            disqualified_targets.append({"target_label": label})
    return {
        "overdue_follow_ups": overdue_follow_ups,
        "outreach_sent_without_follow_up_due": sent_without_due,
        "booked_calls": booked_calls,
        "completed_targets": completed_targets,
        "disqualified_targets": disqualified_targets,
    }


def _load_json_object(path: Path, name: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WeeklyReviewError(f"{name} must be a JSON object")
    return value


def _parse_date(value: object, name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise WeeklyReviewError(f"{name} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise WeeklyReviewError(f"{name} must be YYYY-MM-DD") from exc


def _is_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _load_script_module(module_name: str) -> Any:
    script_path = Path(__file__).with_name(module_name.replace("_", "-") + ".py")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise WeeklyReviewError(f"could not load {script_path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
