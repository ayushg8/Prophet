#!/usr/bin/env python3
"""Combine Prophet validation target and interview scorecards into one daily view."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


DASHBOARD_SCHEMA_VERSION = "prophet_validation_sprint_dashboard.v0.1"
SEND_COPY_BATCH_SCHEMA_VERSION = "prophet_validation_send_copy_batch.v0.1"
BUILD_VERDICTS = {"build_next_slice"}
DEFAULT_LOG = Path("validation/private/customer-validation-log.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
BUILD_GATE_TARGET_STATUSES = {"call_booked", "completed"}
BUILD_GATE_GAP_LABELS = {
    "qualified_count": "qualified call(s)",
    "high_pain_count": "high-pain call(s)",
    "repeated_workflow_pain_count": "repeated workflow-pain match(es)",
    "pilot_pull_count": "pilot-pull signal(s)",
    "paid_or_sponsored_count": "paid/sponsored pilot signal(s)",
}


class ValidationDashboardError(ValueError):
    """Raised when the validation dashboard cannot be generated."""


def build_dashboard(
    *,
    log_path: str | Path = DEFAULT_LOG,
    targets_path: str | Path = DEFAULT_TARGETS,
    message_pack_path: str | Path | None = None,
    require_date: str | None = None,
    scripts_dir: str | Path = "scripts",
) -> dict[str, Any]:
    if require_date is not None:
        _validate_date(require_date)
    log = Path(log_path)
    targets = Path(targets_path)
    if not log.exists() or not targets.exists():
        missing = [str(path) for path in (log, targets) if not path.exists()]
        raise ValidationDashboardError(
            "private validation files missing: "
            + ", ".join(missing)
            + "; run python3 scripts/init-validation-sprint.py"
        )

    scripts = Path(scripts_dir)
    customer_module = _load_module(
        scripts / "customer-validation-scorecard.py",
        "customer_validation_scorecard_module",
    )
    targets_module = _load_module(
        scripts / "validation-targets-scorecard.py",
        "validation_targets_scorecard_module",
    )
    customer_value = customer_module.load_json(log)
    target_value = targets_module.load_json(targets)
    customer_scorecard = customer_module.build_scorecard(customer_value)
    target_scorecard = targets_module.build_scorecard(target_value)
    target_backed_validation = _target_backed_validation(
        customer_value=customer_value,
        target_value=target_value,
        customer_module=customer_module,
    )
    if message_pack_path is None and log == DEFAULT_LOG and targets == DEFAULT_TARGETS:
        message_pack = DEFAULT_MESSAGE_PACK
    elif message_pack_path is None:
        message_pack = None
    else:
        message_pack = Path(message_pack_path)
    outreach_execution = _outreach_execution(
        message_pack_path=message_pack,
        target_tracker_path=targets,
        target_value=target_value,
        require_date=require_date,
        scripts_dir=scripts,
    )
    build_allowed = (
        customer_scorecard["verdict"] in BUILD_VERDICTS
        and target_backed_validation["verdict"] in BUILD_VERDICTS
        and not customer_scorecard.get("example_seed_log", False)
    )
    next_actions = _next_actions(
        customer_scorecard=customer_scorecard,
        target_scorecard=target_scorecard,
        target_backed_validation=target_backed_validation,
        outreach_execution=outreach_execution,
        build_allowed=build_allowed,
    )
    return {
        "schema_version": DASHBOARD_SCHEMA_VERSION,
        "customer_validation": customer_scorecard,
        "target_backed_validation": target_backed_validation,
        "target_pipeline": target_scorecard,
        "outreach_execution": outreach_execution,
        "build_gate": {
            "allowed_to_build_next_slice": build_allowed,
            "reason": _build_gate_reason(
                customer_scorecard["verdict"],
                example_seed_log=bool(customer_scorecard.get("example_seed_log")),
                target_backed_validation=target_backed_validation,
            ),
        },
        "daily_minimum": {
            "targeted_asks": 5,
            "follow_ups": 2,
            "referral_asks": 1,
            "private_log_update": 1,
        },
        "next_actions": next_actions,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a combined Prophet validation sprint dashboard."
    )
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Private validation log path.")
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Private validation target tracker path.",
    )
    parser.add_argument(
        "--message-pack",
        help="Optional validation message pack path. Defaults to today's private pack when using default private files.",
    )
    parser.add_argument(
        "--require-date",
        help="Require the message pack generated_for date to match YYYY-MM-DD.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text", "team"),
        default="json",
        help="Output format. Use team for sanitized aggregate-only status updates.",
    )
    parser.add_argument("--out-json", help="Optional path to write dashboard JSON.")
    args = parser.parse_args(argv)
    try:
        dashboard = build_dashboard(
            log_path=args.log,
            targets_path=args.targets,
            message_pack_path=args.message_pack,
            require_date=args.require_date,
        )
    except Exception as exc:  # scorecard modules raise their own ValueErrors
        print(f"validation sprint dashboard failed: {exc}", file=sys.stderr)
        return 1
    rendered_json = json.dumps(dashboard, indent=2, sort_keys=True)
    if args.format == "text":
        rendered = render_text(dashboard)
    elif args.format == "team":
        rendered = render_team_update(dashboard)
    else:
        rendered = rendered_json
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered_json + "\n", encoding="utf-8")
    return 0


def render_text(dashboard: dict[str, Any]) -> str:
    customer = dashboard["customer_validation"]
    build_gate = dashboard["build_gate"]
    outreach = dashboard.get("outreach_execution", {})
    lines = [
        "# Prophet Validation Sprint Dashboard",
        "",
        f"- Customer validation verdict: {customer['verdict']}",
        f"- Target-backed validation verdict: {dashboard['target_backed_validation']['verdict']}",
        f"- Target-backed qualified calls: {dashboard['target_backed_validation']['qualified_count']}",
        f"- Untracked qualified calls: {dashboard['target_backed_validation']['unmatched_qualified_count']}",
        f"- Status-ineligible qualified calls: {dashboard['target_backed_validation']['status_ineligible_qualified_count']}",
        f"- Metadata-mismatched qualified calls: {dashboard['target_backed_validation']['metadata_mismatched_qualified_count']}",
        f"- Build gate open: {str(build_gate['allowed_to_build_next_slice']).lower()}",
        f"- Build gate reason: {build_gate['reason']}",
    ]
    if outreach.get("available"):
        counts = outreach["counts"]
        lines.extend(
            [
                f"- Outreach date: {outreach['generated_for']}",
                f"- Next draft exists: {str(outreach['next_draft_exists']).lower()}",
                f"- Next draft path: {outreach['next_draft_path']}",
                f"- Next draft target: {outreach.get('next_draft_target_label') or 'none'}",
                f"- Next draft date: {outreach.get('next_draft_generated_for') or 'none'}",
                f"- Next draft status: {outreach.get('next_draft_status') or 'none'}",
                f"- Next draft state: {outreach.get('next_draft_state', 'unknown')}",
                f"- Next draft matches target/date/status/body: {str(outreach.get('next_draft_matches_next_pending', False)).lower()}",
                f"- Send-copy path: {outreach.get('send_copy_path') or 'none'}",
                f"- Send-copy command: {outreach.get('send_copy_command') or 'none'}",
                f"- Send-copy exists: {str(outreach.get('send_copy_exists', False)).lower()}",
                f"- Send-copy state: {outreach.get('send_copy_state', 'unknown')}",
                f"- Send-copy matches current draft: {str(outreach.get('send_copy_matches_next_pending', False)).lower()}",
                f"- Send-copy batch dir: {outreach.get('send_copy_batch_dir') or 'none'}",
                f"- Send-copy batch command: {outreach.get('send_copy_batch_command') or 'none'}",
                f"- Send-copy batch README: {outreach.get('send_copy_batch_readme_path') or 'none'}",
                f"- Send-copy batch README exists: {str(outreach.get('send_copy_batch_readme_exists', False)).lower()}",
                f"- Send-copy batch checklist: {outreach.get('send_copy_batch_checklist_path') or 'none'}",
                f"- Send-copy batch checklist exists: {str(outreach.get('send_copy_batch_checklist_exists', False)).lower()}",
                f"- Send-copy batch copy index: {outreach.get('send_copy_batch_copy_index_path') or 'none'}",
                f"- Send-copy batch copy index exists: {str(outreach.get('send_copy_batch_copy_index_exists', False)).lower()}",
                f"- Send-copy batch subject order: {outreach.get('send_copy_batch_subject_order_path') or 'none'}",
                f"- Send-copy batch subject order exists: {str(outreach.get('send_copy_batch_subject_order_exists', False)).lower()}",
                f"- Send-copy batch state: {outreach.get('send_copy_batch_state', 'unknown')}",
                f"- Send-copy batch files: {outreach.get('send_copy_batch_copy_file_count', 0)}",
                f"- Send-copy batch matches current pack: {str(outreach.get('send_copy_batch_matches_current_pack', False)).lower()}",
                f"- Next target: {outreach.get('next_pending_target_label') or 'none'}",
                f"- Next group: {outreach.get('next_pending_group') or 'none'}",
                f"- Pending send/update: {counts['pending_send_or_update']}",
                f"- Needs attention: {counts['needs_attention']}",
                f"- Dry-run verified: {outreach['dry_run_verified_count']}",
            ]
        )
        dry_run = outreach.get("next_pending_dry_run_apply_command")
        confirmed = outreach.get("next_pending_confirmed_apply_command")
        status_command = outreach.get("status_command")
        if dry_run:
            lines.append(f"- Dry-run command: {dry_run}")
        if confirmed:
            lines.append(f"- Confirmed-send command: {confirmed}")
        if status_command:
            lines.append(f"- Status command: {status_command}")
    else:
        lines.append(f"- Outreach execution: unavailable ({outreach.get('reason', 'not requested')})")
    lines.extend(["", "## Next Actions"])
    for action in dashboard["next_actions"]:
        lines.append(f"- {action}")
    return "\n".join(lines)


def render_team_update(dashboard: dict[str, Any]) -> str:
    """Render a sanitized aggregate update with no target labels or commands."""
    customer = dashboard["customer_validation"]
    target_backed = dashboard["target_backed_validation"]
    targets = dashboard["target_pipeline"]
    build_gate = dashboard["build_gate"]
    outreach = dashboard.get("outreach_execution", {})
    effective_counts = customer.get("effective_validation_counts") or {}
    qualified_count = effective_counts.get("qualified_count", customer["qualified_count"])
    high_pain_count = effective_counts.get("high_pain_count", customer["high_pain_count"])
    repeated_pain_count = effective_counts.get(
        "repeated_workflow_pain_count",
        customer["repeated_workflow_pain_count"],
    )
    pilot_pull_count = effective_counts.get("pilot_pull_count", customer["pilot_pull_count"])
    paid_or_sponsored_count = effective_counts.get(
        "paid_or_sponsored_count",
        customer["paid_or_sponsored_count"],
    )
    top_workflow_pain_theme = (
        customer.get("top_workflow_pain_theme") if repeated_pain_count else None
    )
    lines = [
        "# Prophet Validation Team Update",
        "",
        f"- Customer validation verdict: {customer['verdict']}",
        f"- Build gate open: {str(build_gate['allowed_to_build_next_slice']).lower()}",
        f"- Build gate reason: {build_gate['reason']}",
        f"- Validation data mode: {_validation_data_mode(customer)}",
        f"- Qualified calls counted for gate: {qualified_count}",
        f"- High-pain calls counted for gate: {high_pain_count}",
        f"- Repeated workflow-pain matches counted for gate: {repeated_pain_count}",
        f"- Top workflow pain theme counted for gate: {top_workflow_pain_theme or 'none'}",
        f"- Pilot-pull signals counted for gate: {pilot_pull_count}",
        f"- Paid/sponsored pilot signals counted for gate: {paid_or_sponsored_count}",
        f"- Target-backed validation verdict: {target_backed['verdict']}",
        f"- Target-backed qualified calls: {target_backed['qualified_count']}",
        f"- Untracked qualified calls: {target_backed['unmatched_qualified_count']}",
        f"- Status-ineligible qualified calls: {target_backed['status_ineligible_qualified_count']}",
        f"- Metadata-mismatched qualified calls: {target_backed['metadata_mismatched_qualified_count']}",
        f"- Active outreach targets: {targets['active_target_count']}",
        f"- P0 active targets: {targets['p0_active_count']}",
        f"- Follow-ups due: {targets['follow_up_due_count']}",
    ]
    if outreach.get("available"):
        counts = outreach["counts"]
        lines.extend(
            [
                f"- Outreach date: {outreach['generated_for']}",
                f"- Outreach drafts: {outreach['draft_count']}",
                f"- Pending send/update: {counts['pending_send_or_update']}",
                f"- Needs attention: {counts['needs_attention']}",
                f"- Dry-run verified: {outreach['dry_run_verified_count']}",
                f"- Dry-run failed: {outreach['dry_run_failed_count']}",
                f"- Next draft state: {outreach.get('next_draft_state', 'unknown')}",
                f"- Send-copy state: {outreach.get('send_copy_state', 'unknown')}",
                f"- Send-copy matches next draft: {str(outreach.get('send_copy_matches_next_pending', False)).lower()}",
                f"- Send-copy batch state: {outreach.get('send_copy_batch_state', 'unknown')}",
                f"- Send-copy batch README exists: {str(outreach.get('send_copy_batch_readme_exists', False)).lower()}",
                f"- Send-copy batch checklist exists: {str(outreach.get('send_copy_batch_checklist_exists', False)).lower()}",
                f"- Send-copy batch copy index exists: {str(outreach.get('send_copy_batch_copy_index_exists', False)).lower()}",
                f"- Send-copy batch subject order exists: {str(outreach.get('send_copy_batch_subject_order_exists', False)).lower()}",
                f"- Send-copy batch files: {outreach.get('send_copy_batch_copy_file_count', 0)}",
                f"- Send-copy batch matches current pack: {str(outreach.get('send_copy_batch_matches_current_pack', False)).lower()}",
            ]
        )
    else:
        lines.append(
            f"- Outreach execution: unavailable ({outreach.get('reason', 'not requested')})"
        )
    if customer.get("example_seed_log"):
        lines.extend(
            [
                f"- Raw example qualified calls ignored for gate: {customer['qualified_count']}",
                f"- Raw example high-pain calls ignored for gate: {customer['high_pain_count']}",
                f"- Raw example pilot-pull signals ignored for gate: {customer['pilot_pull_count']}",
                f"- Raw example paid/sponsored signals ignored for gate: {customer['paid_or_sponsored_count']}",
            ]
        )

    lines.extend(["", "## Shareable Next Actions"])
    for action in _shareable_next_actions(dashboard):
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "Do not include target labels, message bodies, contact details, URLs, "
            "hostnames, IPs, or private buyer notes in shared updates.",
        ]
    )
    return "\n".join(lines)


def _load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValidationDashboardError(f"could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _target_backed_validation(
    *,
    customer_value: dict[str, Any],
    target_value: dict[str, Any],
    customer_module: Any,
) -> dict[str, Any]:
    target_by_label = {
        str(target["target_label"]): target
        for target in target_value.get("targets", [])
        if isinstance(target, dict)
    }
    interviews = [
        interview
        for interview in customer_value.get("interviews", [])
        if isinstance(interview, dict)
    ]
    target_backed_interviews = [
        interview
        for interview in interviews
        if _target_supports_build_gate(interview, target_by_label)
    ]
    matched_interview_count = sum(
        1
        for interview in interviews
        if str(interview.get("account_label")) in target_by_label
    )
    unmatched_qualified = [
        str(interview.get("account_label"))
        for interview in interviews
        if interview.get("qualified") is True
        and str(interview.get("account_label")) not in target_by_label
    ]
    status_ineligible_qualified = [
        str(interview.get("account_label"))
        for interview in interviews
        if interview.get("qualified") is True
        and str(interview.get("account_label")) in target_by_label
        and str(target_by_label[str(interview.get("account_label"))]["status"])
        not in BUILD_GATE_TARGET_STATUSES
    ]
    metadata_mismatched_qualified = [
        str(interview.get("account_label"))
        for interview in interviews
        if interview.get("qualified") is True
        and str(interview.get("account_label")) in target_by_label
        and str(target_by_label[str(interview.get("account_label"))]["status"])
        in BUILD_GATE_TARGET_STATUSES
        and not _target_metadata_matches(
            interview,
            target_by_label[str(interview.get("account_label"))],
        )
    ]
    target_backed_log = dict(customer_value)
    target_backed_log["interviews"] = target_backed_interviews
    target_backed_scorecard = customer_module.build_scorecard(target_backed_log)
    return {
        "required_for_build_gate": True,
        "required_target_statuses": sorted(BUILD_GATE_TARGET_STATUSES),
        "verdict": target_backed_scorecard["verdict"],
        "interview_count": target_backed_scorecard["interview_count"],
        "qualified_count": target_backed_scorecard["qualified_count"],
        "high_pain_count": target_backed_scorecard["high_pain_count"],
        "repeated_workflow_pain_count": target_backed_scorecard[
            "repeated_workflow_pain_count"
        ],
        "pilot_pull_count": target_backed_scorecard["pilot_pull_count"],
        "paid_or_sponsored_count": target_backed_scorecard["paid_or_sponsored_count"],
        "top_workflow_pain_theme": target_backed_scorecard["top_workflow_pain_theme"],
        "gaps_to_verdicts": target_backed_scorecard["gaps_to_verdicts"],
        "target_label_count": len(target_by_label),
        "matched_interview_count": matched_interview_count,
        "target_backed_interview_count": len(target_backed_interviews),
        "unmatched_interview_count": len(interviews) - matched_interview_count,
        "unmatched_qualified_count": len(unmatched_qualified),
        "status_ineligible_qualified_count": len(status_ineligible_qualified),
        "metadata_mismatched_qualified_count": len(metadata_mismatched_qualified),
        "unmatched_qualified_account_labels": sorted(unmatched_qualified)[:10],
        "unmatched_qualified_account_label_overflow": max(
            0,
            len(unmatched_qualified) - 10,
        ),
        "status_ineligible_qualified_account_labels": sorted(
            status_ineligible_qualified
        )[:10],
        "status_ineligible_qualified_account_label_overflow": max(
            0,
            len(status_ineligible_qualified) - 10,
        ),
        "metadata_mismatched_qualified_account_labels": sorted(
            metadata_mismatched_qualified
        )[:10],
        "metadata_mismatched_qualified_account_label_overflow": max(
            0,
            len(metadata_mismatched_qualified) - 10,
        ),
    }


def _target_supports_build_gate(
    interview: dict[str, Any],
    target_by_label: dict[str, dict[str, Any]],
) -> bool:
    target = target_by_label.get(str(interview.get("account_label")))
    if target is None:
        return False
    if str(target["status"]) not in BUILD_GATE_TARGET_STATUSES:
        return False
    return _target_metadata_matches(interview, target)


def _target_metadata_matches(interview: dict[str, Any], target: dict[str, Any]) -> bool:
    return (
        str(interview.get("segment")) == str(target.get("segment"))
        and str(interview.get("persona")) == str(target.get("persona"))
    )


def _build_gate_reason(
    verdict: str,
    *,
    example_seed_log: bool = False,
    target_backed_validation: dict[str, Any] | None = None,
) -> str:
    if example_seed_log:
        return "Validation log is still marked example-only; real buyer validation has not proven enough pull for production platform work."
    if verdict == "build_next_slice":
        if (
            target_backed_validation is not None
            and target_backed_validation.get("verdict") != "build_next_slice"
        ):
            return (
                "Customer scorecard reached build_next_slice, but target-backed "
                "validation has not; interviews must match anonymized targets "
                "with call_booked or completed status before production build work."
            )
        return "Customer validation has enough qualified pull to build only the committed pilot's next required slice."
    if verdict == "pilot_pull_detected":
        return "Pilot pull exists; convert design partners before production build work."
    return "Customer validation has not proven enough buyer pull for more production platform work."


def _validation_data_mode(customer_scorecard: dict[str, Any]) -> str:
    if customer_scorecard.get("example_seed_log"):
        return "example seed - do not treat counts as real buyer traction"
    return "private anonymized buyer log"


def _outreach_execution(
    *,
    message_pack_path: Path | None,
    target_tracker_path: Path,
    target_value: dict[str, Any],
    require_date: str | None,
    scripts_dir: Path,
) -> dict[str, Any]:
    if message_pack_path is None:
        return {
            "available": False,
            "reason": "No outreach message pack was requested for this dashboard.",
        }
    if not message_pack_path.exists():
        return {
            "available": False,
            "reason": f"Message pack missing: {message_pack_path}",
            "next_command": (
                "python3 scripts/validation-message-pack.py --block "
                "validation/private/today-outreach-block.json --format markdown "
                "--out validation/private/today-message-pack.md"
            ),
        }
    status_module = _load_module(
        scripts_dir / "validation-outreach-status.py",
        "validation_outreach_status_module",
    )
    try:
        pack = json.loads(message_pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationDashboardError(f"could not read message pack: {exc}") from exc
    if not isinstance(pack, dict):
        raise ValidationDashboardError("message pack must be a JSON object")
    status = status_module.build_status(
        pack,
        target_value,
        verify_dry_run_commands=True,
    )
    if require_date is not None and status["generated_for"] != require_date:
        raise ValidationDashboardError(
            "message pack generated_for "
            f"{status['generated_for']} does not match required date {require_date}"
        )
    next_draft_path = message_pack_path.with_name("today-next-draft.md")
    send_copy_path = message_pack_path.with_name("today-send-copy.txt")
    send_copy_batch_dir = message_pack_path.with_name(f"send-copy-{status['generated_for']}")
    send_copy_batch_manifest_path = send_copy_batch_dir / "manifest.json"
    send_copy_batch_readme_path = send_copy_batch_dir / "README.md"
    send_copy_batch_checklist_path = send_copy_batch_dir / "CHECKLIST.md"
    send_copy_batch_copy_index_path = send_copy_batch_dir / "COPY_ONLY_INDEX.md"
    send_copy_batch_subject_order_path = send_copy_batch_dir / "SUBJECT_ORDER.md"
    next_pending = _next_verified_pending_item(status)
    next_pending_label = next_pending["target_label"] if next_pending is not None else None
    counts = status["counts"]
    next_draft_check = _next_draft_check(
        next_draft_path=next_draft_path,
        next_pending_label=next_pending_label,
        generated_for=status["generated_for"],
        pending_count=int(counts["pending_send_or_update"]),
        pack=pack,
        target_value=target_value,
        scripts_dir=scripts_dir,
    )
    next_draft_metadata = next_draft_check["metadata"]
    next_draft_target_label = next_draft_metadata["target_label"]
    next_draft_exists = next_draft_check["exists"]
    next_draft_matches_next_pending = next_draft_check["matches"]
    next_draft_state = next_draft_check["state"]
    send_copy_check = _send_copy_check(
        send_copy_path=send_copy_path,
        next_draft_matches_next_pending=next_draft_matches_next_pending,
        pending_count=int(counts["pending_send_or_update"]),
        pack=pack,
        target_value=target_value,
        generated_for=status["generated_for"],
        scripts_dir=scripts_dir,
    )
    send_copy_batch_check = _send_copy_batch_check(
        send_copy_batch_dir=send_copy_batch_dir,
        manifest_path=send_copy_batch_manifest_path,
        pending_count=int(counts["pending_send_or_update"]),
        status=status,
        pack=pack,
        generated_for=status["generated_for"],
        scripts_dir=scripts_dir,
    )
    return {
        "available": True,
        "message_pack_path": str(message_pack_path),
        "next_draft_path": str(next_draft_path),
        "send_copy_path": str(send_copy_path),
        "send_copy_batch_dir": str(send_copy_batch_dir),
        "send_copy_batch_manifest_path": str(send_copy_batch_manifest_path),
        "send_copy_batch_readme_path": str(send_copy_batch_readme_path),
        "send_copy_batch_checklist_path": str(send_copy_batch_checklist_path),
        "send_copy_batch_copy_index_path": str(send_copy_batch_copy_index_path),
        "send_copy_batch_subject_order_path": str(send_copy_batch_subject_order_path),
        "send_copy_exists": send_copy_check["exists"],
        "send_copy_matches_next_pending": send_copy_check["matches"],
        "send_copy_state": send_copy_check["state"],
        "send_copy_mismatch_reason": send_copy_check["mismatch_reason"],
        "send_copy_batch_exists": send_copy_batch_check["exists"],
        "send_copy_batch_manifest_exists": send_copy_batch_check["manifest_exists"],
        "send_copy_batch_readme_exists": send_copy_batch_check["readme_exists"],
        "send_copy_batch_checklist_exists": send_copy_batch_check["checklist_exists"],
        "send_copy_batch_copy_index_exists": send_copy_batch_check["copy_index_exists"],
        "send_copy_batch_subject_order_exists": send_copy_batch_check["subject_order_exists"],
        "send_copy_batch_matches_current_pack": send_copy_batch_check["matches"],
        "send_copy_batch_state": send_copy_batch_check["state"],
        "send_copy_batch_copy_file_count": send_copy_batch_check["copy_file_count"],
        "send_copy_batch_mismatch_reason": send_copy_batch_check["mismatch_reason"],
        "next_draft_exists": next_draft_exists,
        "next_draft_target_label": next_draft_target_label,
        "next_draft_generated_for": next_draft_metadata["generated_for"],
        "next_draft_status": next_draft_metadata["status"],
        "next_draft_matches_next_pending": next_draft_matches_next_pending,
        "next_draft_state": next_draft_state,
        "next_draft_mismatch_reason": next_draft_check["mismatch_reason"],
        "next_draft_command": (
            "python3 scripts/validation-next-draft.py "
            f"--message-pack {message_pack_path} "
            f"--targets {target_tracker_path} "
            f"--require-date {status['generated_for']} "
            f"--out {next_draft_path}"
        ),
        "send_copy_command": f"make validation-send-copy DATE={status['generated_for']}",
        "send_copy_batch_command": (
            f"make validation-send-copy-batch DATE={status['generated_for']}"
        ),
        "generated_for": status["generated_for"],
        "draft_count": status["draft_count"],
        "next_pending_target_label": next_pending_label,
        "next_pending_group": next_pending["group"] if next_pending is not None else None,
        "next_pending_dry_run_apply_command": (
            next_pending.get("dry_run_apply_command") if next_pending is not None else None
        ),
        "next_pending_confirmed_apply_command": (
            next_pending.get("confirmed_apply_command") if next_pending is not None else None
        ),
        "status_command": f"make validation-status DATE={status['generated_for']}",
        "counts": counts,
        "complete": status["complete"],
        "dry_run_verified_count": status["dry_run_verified_count"],
        "dry_run_failed_count": status["dry_run_failed_count"],
        "dry_run_skipped_count": status["dry_run_skipped_count"],
        "needs_attention_targets": [
            item["target_label"]
            for item in status["items"]
            if item["state"] == "needs_attention"
        ],
    }


def _next_actions(
    *,
    customer_scorecard: dict[str, Any],
    target_scorecard: dict[str, Any],
    target_backed_validation: dict[str, Any],
    outreach_execution: dict[str, Any],
    build_allowed: bool,
) -> list[str]:
    daily_outreach_action = _daily_outreach_action(
        int(target_scorecard.get("follow_up_due_count", 0))
    )
    actions = [
        target_scorecard["next_action"],
        customer_scorecard["next_action"],
    ]
    if not build_allowed:
        actions.append("Do not build more production platform scope today.")
        gap_action = _build_gate_gap_action(customer_scorecard)
        if gap_action:
            actions.append(gap_action)
        target_backed_gap_action = _target_backed_build_gate_gap_action(
            customer_scorecard,
            target_backed_validation,
        )
        if target_backed_gap_action:
            actions.append(target_backed_gap_action)
    outreach_action = _outreach_execution_action(outreach_execution)
    if outreach_action:
        actions.append(outreach_action)
    actions.append(daily_outreach_action)
    return _dedupe(actions)


def _shareable_next_actions(dashboard: dict[str, Any]) -> list[str]:
    customer = dashboard["customer_validation"]
    targets = dashboard["target_pipeline"]
    target_backed = dashboard.get("target_backed_validation", {})
    outreach = dashboard.get("outreach_execution", {})
    actions = []
    if customer.get("example_seed_log"):
        actions.append(
            "Replace the example-only validation seed with real anonymized buyer interviews before treating counts as traction."
        )
    if not dashboard["build_gate"]["allowed_to_build_next_slice"]:
        actions.append("Keep the production build gate closed.")
        gap_action = _build_gate_gap_action(customer)
        if gap_action:
            actions.append(gap_action)
        target_backed_gap_action = _target_backed_build_gate_gap_action(
            customer,
            target_backed,
        )
        if target_backed_gap_action:
            actions.append(
                "Tie enough validated interviews back to anonymized target labels "
                "with booked or completed call status before opening production scope."
            )
    if outreach.get("available"):
        counts = outreach["counts"]
        if counts["needs_attention"]:
            actions.append("Fix private outreach status before sending more asks.")
        elif counts["pending_send_or_update"]:
            actions.append(
                "Send the next verified draft outside the repo, then update the private "
                "tracker only after the send is confirmed."
            )
        elif outreach.get("complete"):
            actions.append("Log replies and calls, then regenerate the next outreach block when ready.")
    else:
        actions.append("Generate the private validation pack before sending outreach.")
    actions.append(_daily_outreach_action(int(targets.get("follow_up_due_count", 0))))
    actions.append("Log only sanitized outcomes in the private validation workspace.")
    return _dedupe(actions)


def _daily_outreach_action(follow_up_due_count: int) -> str:
    if follow_up_due_count >= 2:
        return "Run today's outreach block: 5 targeted asks, 2 due follow-ups, and 1 referral ask."
    if follow_up_due_count == 1:
        return "Run today's outreach block: 5 targeted asks, 1 due follow-up, 1 follow-up backfill ask, and 1 referral ask."
    return "Run today's outreach block: 5 targeted asks, 2 follow-up backfill asks, and 1 referral ask."


def _outreach_execution_action(outreach_execution: dict[str, Any]) -> str | None:
    if not outreach_execution.get("available"):
        next_command = outreach_execution.get("next_command")
        if next_command:
            return f"Generate today's message pack before sending outreach: {next_command}"
        return None
    counts = outreach_execution["counts"]
    if counts["needs_attention"]:
        return (
            "Fix outreach execution status before sending: "
            f"{counts['needs_attention']} item(s) need attention."
        )
    if counts["pending_send_or_update"]:
        next_draft_exists = bool(outreach_execution.get("next_draft_exists"))
        next_draft_ready = bool(outreach_execution.get("next_draft_matches_next_pending"))
        command_clause = _next_pending_apply_clause(
            outreach_execution,
            next_draft_exists=next_draft_ready,
        )
        if next_draft_ready:
            if not outreach_execution.get("send_copy_matches_next_pending"):
                return (
                    "Refresh the copy-only send text"
                    f"{_next_pending_suffix(outreach_execution)} "
                    f"with `{outreach_execution['send_copy_command']}` before sending; "
                    f"do not use {outreach_execution['send_copy_path']} until "
                    f"`send_copy_state` is `ready`; "
                    f"{command_clause}. "
                    f"{counts['pending_send_or_update']} verified draft(s) remain."
                )
            return (
                "Use the copy-only send text"
                f"{_next_pending_suffix(outreach_execution)} "
                f"from {outreach_execution['send_copy_path']}; "
                f"`{outreach_execution['send_copy_command']}` refreshes it from "
                f"the verified tracker/audit draft at {outreach_execution['next_draft_path']}; "
                f"{command_clause}. "
                f"{counts['pending_send_or_update']} verified draft(s) remain."
            )
        if next_draft_exists:
            return (
                "Rerender the next verified outreach draft"
                f"{_next_pending_suffix(outreach_execution)} "
                f"with `{outreach_execution['next_draft_command']}`; "
                f"existing {outreach_execution['next_draft_path']} targets "
                f"{outreach_execution.get('next_draft_target_label') or 'an unknown target'} "
                f"with date {outreach_execution.get('next_draft_generated_for') or 'unknown'} "
                f"and status {outreach_execution.get('next_draft_status') or 'unknown'}, "
                "which is stale for the current tracker"
                f"{_mismatch_reason_suffix(outreach_execution.get('next_draft_mismatch_reason'))}. "
                f"{counts['pending_send_or_update']} verified draft(s) remain."
            )
        return (
            "Render the next verified outreach draft"
            f"{_next_pending_suffix(outreach_execution)} "
            f"to {outreach_execution['next_draft_path']}, "
            f"then run `{outreach_execution['send_copy_command']}` for copy-only text, "
            f"{command_clause}. "
            f"{counts['pending_send_or_update']} verified draft(s) remain."
        )
    if outreach_execution.get("complete"):
        return "Today's outreach pack is applied; log replies/calls and regenerate the next block when ready."
    return None


def _build_gate_gap_action(customer_scorecard: dict[str, Any]) -> str | None:
    gaps = (
        customer_scorecard.get("gaps_to_verdicts", {})
        .get("build_next_slice", {})
    )
    if not isinstance(gaps, dict) or not gaps:
        return None
    parts = [
        f"{int(gaps[field])} {label}"
        for field, label in BUILD_GATE_GAP_LABELS.items()
        if int(gaps.get(field, 0)) > 0
    ]
    if not parts:
        return None
    return "Build gate gap to build_next_slice: " + ", ".join(parts) + "."


def _target_backed_build_gate_gap_action(
    customer_scorecard: dict[str, Any],
    target_backed_validation: dict[str, Any],
) -> str | None:
    if customer_scorecard.get("verdict") != "build_next_slice":
        return None
    if target_backed_validation.get("verdict") == "build_next_slice":
        return None
    gaps = (
        target_backed_validation.get("gaps_to_verdicts", {})
        .get("build_next_slice", {})
    )
    if not isinstance(gaps, dict):
        return None
    parts = [
        f"{int(gaps[field])} target-backed {label}"
        for field, label in BUILD_GATE_GAP_LABELS.items()
        if int(gaps.get(field, 0)) > 0
    ]
    context = []
    unmatched = int(target_backed_validation.get("unmatched_qualified_count", 0))
    status_ineligible = int(
        target_backed_validation.get("status_ineligible_qualified_count", 0)
    )
    if unmatched:
        context.append(f"{unmatched} qualified call(s) are not in the target tracker")
    if status_ineligible:
        context.append(
            f"{status_ineligible} qualified call(s) match targets without "
            "call_booked/completed status"
        )
    metadata_mismatched = int(
        target_backed_validation.get("metadata_mismatched_qualified_count", 0)
    )
    if metadata_mismatched:
        context.append(
            f"{metadata_mismatched} qualified call(s) match target labels but "
            "not target segment/persona metadata"
        )
    if not parts and not context:
        return None
    detail = ", ".join(parts) if parts else "no target-backed count gap"
    if context:
        detail += "; " + "; ".join(context)
    return "Target-backed build gate gap: " + detail + "."


def _next_verified_pending_item(status: dict[str, Any]) -> dict[str, Any] | None:
    for item in status["items"]:
        if (
            item["state"] == "pending_send_or_update"
            and item.get("dry_run_verification", {}).get("ok") is True
        ):
            return item
    return None


def _next_draft_metadata(next_draft_path: Path) -> dict[str, str | None]:
    metadata: dict[str, str | None] = {
        "generated_for": None,
        "target_label": None,
        "status": None,
    }
    if not next_draft_path.exists():
        return metadata
    try:
        for line in next_draft_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# Next Prophet Validation Draft - "):
                value = line.removeprefix("# Next Prophet Validation Draft - ").strip()
                metadata["generated_for"] = value or None
            if line.startswith("- Target: "):
                value = line.removeprefix("- Target: ").strip()
                metadata["target_label"] = value or None
            if line.startswith("- Status: "):
                value = line.removeprefix("- Status: ").strip()
                metadata["status"] = value or None
    except OSError:
        return metadata
    return metadata


def _next_draft_state(
    *,
    next_draft_exists: bool,
    next_draft_matches_next_pending: bool,
    pending_count: int,
) -> str:
    if pending_count <= 0:
        return "not_needed"
    if not next_draft_exists:
        return "missing"
    if next_draft_matches_next_pending:
        return "ready"
    return "stale"


def _next_draft_check(
    *,
    next_draft_path: Path,
    next_pending_label: str | None,
    generated_for: str,
    pending_count: int,
    pack: dict[str, Any],
    target_value: dict[str, Any],
    scripts_dir: Path,
) -> dict[str, Any]:
    exists = next_draft_path.exists()
    metadata = _next_draft_metadata(next_draft_path)
    result: dict[str, Any] = {
        "exists": exists,
        "metadata": metadata,
        "matches": False,
        "state": "missing",
        "mismatch_reason": None,
    }
    if pending_count <= 0:
        result["state"] = "not_needed"
        return result
    if not exists:
        return result
    if next_pending_label is None:
        result["state"] = "stale"
        result["mismatch_reason"] = "no verified pending draft is available"
        return result
    metadata_matches = (
        metadata["target_label"] == next_pending_label
        and metadata["generated_for"] == generated_for
        and metadata["status"] == "verified pending send/update"
    )
    if not metadata_matches:
        result["state"] = "stale"
        result["mismatch_reason"] = "next-draft metadata does not match current target/date/status"
        return result
    try:
        expected = _expected_next_draft_markdown(
            pack=pack,
            target_value=target_value,
            generated_for=generated_for,
            scripts_dir=scripts_dir,
        )
        actual = next_draft_path.read_text(encoding="utf-8")
    except Exception as exc:
        result["state"] = "stale"
        result["mismatch_reason"] = f"could not verify next-draft text: {exc}"
        return result
    if actual == expected:
        result["matches"] = True
        result["state"] = "ready"
    else:
        result["state"] = "stale"
        result["mismatch_reason"] = "next-draft text does not match the current verified draft"
    return result


def _send_copy_check(
    *,
    send_copy_path: Path,
    next_draft_matches_next_pending: bool,
    pending_count: int,
    pack: dict[str, Any],
    target_value: dict[str, Any],
    generated_for: str,
    scripts_dir: Path,
) -> dict[str, Any]:
    exists = send_copy_path.exists()
    result = {
        "exists": exists,
        "matches": False,
        "state": "missing",
        "mismatch_reason": None,
    }
    if pending_count <= 0:
        result["state"] = "not_needed"
        return result
    if not exists:
        return result
    if not next_draft_matches_next_pending:
        result["state"] = "stale"
        result["mismatch_reason"] = "next draft is not ready for the current target/date/status"
        return result
    try:
        expected = _expected_send_copy_text(
            pack=pack,
            target_value=target_value,
            generated_for=generated_for,
            scripts_dir=scripts_dir,
        )
        actual = send_copy_path.read_text(encoding="utf-8")
    except Exception as exc:
        result["state"] = "stale"
        result["mismatch_reason"] = f"could not verify send-copy text: {exc}"
        return result
    if actual == expected:
        result["matches"] = True
        result["state"] = "ready"
    else:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy text does not match the current verified draft"
    return result


def _send_copy_batch_check(
    *,
    send_copy_batch_dir: Path,
    manifest_path: Path,
    pending_count: int,
    status: dict[str, Any],
    pack: dict[str, Any],
    generated_for: str,
    scripts_dir: Path,
) -> dict[str, Any]:
    exists = send_copy_batch_dir.exists()
    manifest_exists = manifest_path.exists()
    readme_path = send_copy_batch_dir / "README.md"
    readme_exists = readme_path.exists()
    checklist_path = send_copy_batch_dir / "CHECKLIST.md"
    checklist_exists = checklist_path.exists()
    copy_index_path = send_copy_batch_dir / "COPY_ONLY_INDEX.md"
    copy_index_exists = copy_index_path.exists()
    subject_order_path = send_copy_batch_dir / "SUBJECT_ORDER.md"
    subject_order_exists = subject_order_path.exists()
    copy_file_count = len(_send_copy_batch_file_paths(send_copy_batch_dir)) if exists else 0
    result = {
        "exists": exists,
        "manifest_exists": manifest_exists,
        "readme_exists": readme_exists,
        "checklist_exists": checklist_exists,
        "copy_index_exists": copy_index_exists,
        "subject_order_exists": subject_order_exists,
        "matches": False,
        "state": "missing",
        "copy_file_count": copy_file_count,
        "mismatch_reason": None,
    }
    if pending_count <= 0:
        result["state"] = "not_needed"
        return result
    if not exists or not manifest_exists:
        return result
    if not readme_exists:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch README is missing"
        return result
    if not checklist_exists:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch CHECKLIST is missing"
        return result
    if not copy_index_exists:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch COPY_ONLY_INDEX is missing"
        return result
    if not subject_order_exists:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch SUBJECT_ORDER is missing"
        return result
    try:
        expected_files = _expected_send_copy_batch_files(
            send_copy_batch_dir=send_copy_batch_dir,
            status=status,
            pack=pack,
            scripts_dir=scripts_dir,
        )
        actual_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["state"] = "stale"
        result["mismatch_reason"] = f"could not verify send-copy batch: {exc}"
        return result
    if not isinstance(actual_manifest, dict):
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch manifest must be a JSON object"
        return result
    try:
        actual_readme = readme_path.read_text(encoding="utf-8")
        actual_checklist = checklist_path.read_text(encoding="utf-8")
        actual_copy_index = copy_index_path.read_text(encoding="utf-8")
        actual_subject_order = subject_order_path.read_text(encoding="utf-8")
    except OSError as exc:
        result["state"] = "stale"
        result["mismatch_reason"] = f"could not read send-copy batch operator files: {exc}"
        return result

    actual_names = [path.name for path in _send_copy_batch_file_paths(send_copy_batch_dir)]
    expected_names = [file["name"] for file in expected_files]
    if actual_names != expected_names:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch file list does not match current verified drafts"
        return result
    for file in expected_files:
        try:
            actual_text = Path(file["path"]).read_text(encoding="utf-8")
        except OSError as exc:
            result["state"] = "stale"
            result["mismatch_reason"] = f"could not read send-copy batch file: {exc}"
            return result
        if actual_text != file["text"]:
            result["state"] = "stale"
            result["mismatch_reason"] = (
                "send-copy batch text does not match current verified drafts"
            )
            return result

    expected_operator_notes = _expected_send_copy_batch_operator_notes(generated_for)
    expected_readme = _expected_send_copy_batch_readme(
        generated_for=generated_for,
        copy_file_count=len(expected_files),
    )
    if actual_readme != expected_readme:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch README does not match current generator"
        return result
    expected_checklist = _expected_send_copy_batch_checklist(
        generated_for=generated_for,
        files=expected_files,
    )
    if actual_checklist != expected_checklist:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch CHECKLIST does not match current generator"
        return result
    expected_copy_index = _expected_send_copy_batch_copy_index(
        generated_for=generated_for,
        files=expected_files,
    )
    if actual_copy_index != expected_copy_index:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch COPY_ONLY_INDEX does not match current generator"
        return result
    expected_subject_order = _expected_send_copy_batch_subject_order(
        generated_for=generated_for,
        files=expected_files,
    )
    if actual_subject_order != expected_subject_order:
        result["state"] = "stale"
        result["mismatch_reason"] = "send-copy batch SUBJECT_ORDER does not match current generator"
        return result

    expected_manifest_fields = {
        "schema_version": SEND_COPY_BATCH_SCHEMA_VERSION,
        "message_pack_schema_version": pack["schema_version"],
        "status_schema_version": status["schema_version"],
        "generated_for": generated_for,
        "outbound_safe": False,
        "copy_files_outbound_safe": True,
        "operator_metadata_outbound_safe": False,
        "private_metadata": True,
        "send_boundary": "copy_numbered_txt_contents_only",
        "out_dir": str(send_copy_batch_dir),
        "manifest_path": str(manifest_path),
        "readme_path": str(readme_path),
        "checklist_path": str(checklist_path),
        "copy_index_path": str(copy_index_path),
        "subject_order_path": str(subject_order_path),
        "copy_file_count": len(expected_files),
        "pending_send_or_update_count": status["counts"]["pending_send_or_update"],
        "needs_attention_count": status["counts"]["needs_attention"],
        "dry_run_verified_count": status["dry_run_verified_count"],
        "operator_notes": expected_operator_notes,
        "files": [
            {
                "ordinal": file["ordinal"],
                "target_label": file["target_label"],
                "group": file["group"],
                "path": file["path"],
                "subject": file["subject"],
                "sha256": file["sha256"],
                "dry_run_apply_command": file["dry_run_apply_command"],
                "confirmed_apply_command": file["confirmed_apply_command"],
            }
            for file in expected_files
        ],
    }
    for key, expected_value in expected_manifest_fields.items():
        if actual_manifest.get(key) != expected_value:
            result["state"] = "stale"
            result["mismatch_reason"] = (
                "send-copy batch manifest does not match current verified drafts"
            )
            return result
    result["matches"] = True
    result["state"] = "ready"
    return result


def _expected_send_copy_batch_operator_notes(generated_for: str) -> list[str]:
    return [
        "Each file contains only one subject line and body text; copy the contents, do not attach the file.",
        "Do not paste target labels, tracker commands, the manifest, the batch checklist, the copy index, the subject order helper, or the batch README to buyers.",
        "Run the matching dry-run command before sending each file's contents.",
        "Run the matching CONFIRM_SENT=1 command only after that message was actually sent.",
        f"Rerun make validation-status DATE={generated_for} after confirmed tracker updates.",
    ]


def _expected_send_copy_batch_readme(*, generated_for: str, copy_file_count: int) -> str:
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


def _expected_send_copy_batch_checklist(
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


def _expected_send_copy_batch_copy_index(
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


def _expected_send_copy_batch_subject_order(
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
        lines.append(f"| `{Path(str(file['path'])).name}` | {file['subject']} |")
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


def _expected_send_copy_batch_files(
    *,
    send_copy_batch_dir: Path,
    status: dict[str, Any],
    pack: dict[str, Any],
    scripts_dir: Path,
) -> list[dict[str, Any]]:
    message_module = _load_module(
        scripts_dir / "validation-message-pack.py",
        "validation_message_pack_dashboard_batch_module",
    )
    drafts_by_label = {
        draft["target_label"]: draft
        for draft in pack.get("drafts", [])
    }
    files: list[dict[str, Any]] = []
    pending = [
        item
        for item in status["items"]
        if item["state"] == "pending_send_or_update"
        and item.get("dry_run_verification", {}).get("ok") is True
    ]
    for ordinal, item in enumerate(pending, start=1):
        draft = drafts_by_label.get(item["target_label"])
        if draft is None:
            raise ValidationDashboardError(
                f"draft not found for target: {item['target_label']}"
            )
        filtered_pack = dict(pack)
        filtered_pack["drafts"] = [draft]
        filtered_pack["draft_count"] = 1
        name = f"{ordinal:02d}.txt"
        text = message_module.render_send_text(filtered_pack)
        subject = _subject_from_copy_text(text)
        files.append(
            {
                "ordinal": ordinal,
                "target_label": item["target_label"],
                "group": item["group"],
                "name": name,
                "path": str(send_copy_batch_dir / name),
                "text": text,
                "subject": subject,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "dry_run_apply_command": item.get("dry_run_apply_command"),
                "confirmed_apply_command": item.get("confirmed_apply_command"),
            }
        )
    return files


def _send_copy_batch_file_paths(send_copy_batch_dir: Path) -> list[Path]:
    paths = {
        *send_copy_batch_dir.glob("[0-9][0-9].txt"),
        *send_copy_batch_dir.glob("[0-9][0-9]-*.txt"),
    }
    return sorted(path for path in paths if path.is_file())


def _subject_from_copy_text(rendered: str) -> str:
    subjects = [
        line.removeprefix("Subject: ").strip()
        for line in rendered.splitlines()
        if line.startswith("Subject: ")
    ]
    if len(subjects) != 1 or not subjects[0]:
        raise ValidationDashboardError("copy-only send text must contain exactly one subject")
    return subjects[0]


def _expected_send_copy_text(
    *,
    pack: dict[str, Any],
    target_value: dict[str, Any],
    generated_for: str,
    scripts_dir: Path,
) -> str:
    next_draft_module = _load_module(
        scripts_dir / "validation-next-draft.py",
        "validation_next_draft_dashboard_module",
    )
    next_draft = next_draft_module.build_next_draft(
        pack,
        target_value,
        require_date=generated_for,
    )
    return next_draft_module.render_send_text(next_draft)


def _expected_next_draft_markdown(
    *,
    pack: dict[str, Any],
    target_value: dict[str, Any],
    generated_for: str,
    scripts_dir: Path,
) -> str:
    next_draft_module = _load_module(
        scripts_dir / "validation-next-draft.py",
        "validation_next_draft_dashboard_module",
    )
    next_draft = next_draft_module.build_next_draft(
        pack,
        target_value,
        require_date=generated_for,
    )
    return next_draft_module.render_markdown(next_draft)


def _mismatch_reason_suffix(reason: object) -> str:
    if not reason:
        return ""
    return f" ({reason})"


def _next_pending_suffix(outreach_execution: dict[str, Any]) -> str:
    target_label = outreach_execution.get("next_pending_target_label")
    group = outreach_execution.get("next_pending_group")
    if not target_label:
        return ""
    if not group:
        return f" for {target_label}"
    return f" for {target_label} ({group})"


def _next_pending_apply_clause(
    outreach_execution: dict[str, Any],
    *,
    next_draft_exists: bool,
) -> str:
    dry_run = outreach_execution.get("next_pending_dry_run_apply_command")
    confirmed = outreach_execution.get("next_pending_confirmed_apply_command")
    status_command = outreach_execution.get("status_command")
    if dry_run and confirmed:
        if next_draft_exists:
            clause = (
                f"`{dry_run}` is currently verified; rerun it before sending "
                "if the private tracker changed, then run "
                f"`{confirmed}` only after the confirmed send"
            )
        else:
            clause = (
                f"run `{dry_run}` before sending or writing, then run `{confirmed}` "
                "only after the confirmed send"
            )
        if status_command:
            clause += f", then rerun `{status_command}`"
        return clause
    return "apply its tracker update after the confirmed send"


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationDashboardError(f"require-date must be YYYY-MM-DD: {value}") from exc


def _dedupe(actions: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for action in actions:
        if action not in seen:
            unique.append(action)
            seen.add(action)
    return unique


if __name__ == "__main__":
    raise SystemExit(main())
