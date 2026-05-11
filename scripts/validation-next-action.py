#!/usr/bin/env python3
"""Render the ignored private next-action handoff from the live validation gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_LOG = Path("validation/private/customer-validation-log.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_SEND_COPY = Path("validation/private/today-send-copy.txt")
DEFAULT_OUT = Path("validation/private/NEXT_ACTION.md")


class ValidationNextActionError(ValueError):
    """Raised when the private next-action handoff cannot be rendered."""


def render_next_action(
    dashboard: dict[str, Any],
    *,
    run_date: str,
    git_head: str | None = None,
    git_worktree_state: str | None = None,
    github_ci_summary: str | None = None,
) -> str:
    customer = dashboard["customer_validation"]
    build_gate = dashboard["build_gate"]
    outreach = dashboard.get("outreach_execution", {})
    next_target = outreach.get("next_pending_target_label")
    effective_counts = customer.get("effective_validation_counts") or {}
    gaps = (customer.get("gaps_to_verdicts") or {}).get("build_next_slice") or {}
    lines = [
        "# Next Validation Action",
        "",
        f"Date: {run_date}",
        "",
        "Generated from the current validation dashboard. Do not edit committed",
        "files for this step, and do not mark outreach sent until it was actually",
        "sent outside the repo.",
        "",
        "## 1. Rerun The Read-Only Checks",
        "",
        "Before sending anything, rerun the dry-run pre-send gate:",
        "",
        "```bash",
        f"make validation-pre-send-check TARGET={next_target or 'target-label'} DATE={run_date}",
        "```",
        "",
        "If sending the full block, run the full-batch dry-run gate too:",
        "",
        "```bash",
        f"make validation-pre-send-check-all DATE={run_date}",
        "```",
        "",
        "That wrapper expands to these checks and refuses all `CONFIRM_*` write",
        "guards:",
        "",
        "```bash",
        f"make validation-dashboard DATE={run_date}",
        f"make validation-send-copy-check DATE={run_date}",
        f"make validation-prune-private DATE={run_date}",
    ]
    dry_run = outreach.get("next_pending_dry_run_apply_command")
    if dry_run:
        lines.append(str(dry_run))
    lines.extend(
        [
            "```",
            "",
            "Proceed only if the dashboard still reports:",
            "",
            f"- `send_copy_state: {outreach.get('send_copy_state', 'unavailable')}`",
            f"- `send_copy_matches_next_pending: {_lower_bool(outreach.get('send_copy_matches_next_pending'))}`",
            f"- `send_copy_batch_state: {outreach.get('send_copy_batch_state', 'unavailable')}`",
            f"- `send_copy_batch_matches_current_pack: {_lower_bool(outreach.get('send_copy_batch_matches_current_pack'))}`",
            f"- `needs_attention: {(outreach.get('counts') or {}).get('needs_attention', 'unavailable')}`",
            "",
            "Also proceed only if `make validation-send-copy-check` reports:",
            "",
            "- `copy_files_outbound_safe: true`",
            "- `readme_matches_manifest: true`",
            "- `checklist_matches_manifest: true`",
            "- `copy_index_matches_manifest: true`",
            "- `subject_order_matches_manifest: true`",
            "- `do_not_send_matches_manifest: true`",
            "",
            "`operator_metadata_outbound_safe: false` is expected because the",
            "manifest, README, checklist, copy index, subject-order helper, and",
            "DO_NOT_SEND guard are private operator metadata. Send only the",
            "numbered `.txt` file contents.",
            "",
            "The dry-run apply command must still show the target moving to",
            "`outreach_sent` without writing.",
            "",
            "The prune command is optional cleanup only. It must not delete anything",
            "unless `CONFIRM_PRUNE=1` is supplied after operator review.",
            "",
            "## 2. Send Copy-Only Text",
            "",
            "The repo intentionally does not store recipient names, emails,",
            "LinkedIn URLs, or outbound channel details. To actually send a",
            "draft, the operator must use an external outreach channel and a",
            "real contact selected outside the repo.",
            "",
        ]
    )
    if outreach.get("send_copy_state") == "ready":
        lines.extend(
            [
                "For the next single outbound message, use only this file:",
                "",
                "```text",
                str(outreach.get("send_copy_path") or DEFAULT_SEND_COPY),
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "The single-send copy file is not ready. Refresh it before sending:",
                "",
                "```bash",
                f"make validation-send-copy DATE={run_date}",
                "```",
                "",
            ]
        )
    batch_dir = outreach.get("send_copy_batch_dir")
    if outreach.get("send_copy_batch_state") == "ready" and batch_dir:
        lines.extend(
            [
                "For the full block, copy only the contents of the numbered `.txt` files in:",
                "",
                "```text",
                str(batch_dir),
                "```",
                "",
                "Do not attach files. Do not send manifests, README/checklist files, copy",
                "indexes, subject-order helpers, DO_NOT_SEND guards, target labels,",
                "tracker commands, or operator metadata.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "The full send-copy batch is not ready. Refresh it before using a block send:",
                "",
                "```bash",
                f"make validation-send-copy-batch DATE={run_date}",
                "```",
                "",
            ]
        )
    confirmed = outreach.get("next_pending_confirmed_apply_command")
    lines.extend(
        [
            "## 3. After The Message Is Actually Sent",
            "",
            "Only after the outbound message is confirmed sent outside the repo, run:",
            "",
            "```bash",
        ]
    )
    if confirmed:
        lines.append(str(confirmed))
    elif next_target:
        lines.append(f"make validation-apply-draft TARGET={next_target} DATE={run_date} CONFIRM_SENT=1")
    else:
        lines.append(f"# No pending target is available for {run_date}; do not confirm-send anything.")
    lines.extend(
        [
            f"make validation-status DATE={run_date}",
            f"make validation-dashboard DATE={run_date}",
            "```",
            "",
            "If sending the full block, use the private checklist to run each matching",
            "`CONFIRM_SENT=1` command only after that specific message has actually",
            "been sent.",
            "",
            "## 4. If A Reply Comes Back",
            "",
            "Do not paste reply text into the tracker. Classify it manually, then run one of:",
            "",
            "```bash",
        ]
    )
    reply_target = next_target or "target-label"
    for reply in ("book_call", "disqualify", "keep_pending", "manual_review"):
        lines.append(f"make validation-reply-triage TARGET={reply_target} REPLY={reply} DATE={run_date}")
    lines.extend(
        [
            "```",
            "",
            "Only run a `CONFIRM_TARGET=1` command after reviewing the dry-run output.",
            "",
            "## Current Gate",
            "",
            f"- Validation verdict: {customer.get('verdict')}",
            f"- Effective buyer evidence: {json.dumps(effective_counts, sort_keys=True)}",
            f"- Build gate: {'open' if build_gate.get('allowed_to_build_next_slice') else 'closed'}",
            f"- Build gate reason: {build_gate.get('reason')}",
            f"- Build-next-slice gaps: {json.dumps(gaps, sort_keys=True)}",
            f"- Pending send/update: {(outreach.get('counts') or {}).get('pending_send_or_update', 'unavailable')}",
            f"- Dry-run verified: {outreach.get('dry_run_verified_count', 'unavailable')}",
            f"- Needs attention: {(outreach.get('counts') or {}).get('needs_attention', 'unavailable')}",
            f"- Batch copy files: {outreach.get('send_copy_batch_copy_file_count', 'unavailable')}",
            f"- Batch state: {outreach.get('send_copy_batch_state', 'unavailable')}",
        ]
    )
    if git_head:
        lines.extend(
            [
                f"- Local git head: `{git_head}`. Recheck GitHub status before release decisions.",
            ]
        )
    if git_worktree_state:
        lines.append(
            f"- Local git worktree: `{git_worktree_state}`. If dirty, rerun the "
            "dashboard and send-copy checks after resolving local changes."
        )
    if github_ci_summary:
        lines.append(f"- GitHub CI for local head: {github_ci_summary}")
    if git_head or git_worktree_state:
        lines.append("- Do not use PR readiness as buyer-demand evidence.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the ignored private Prophet validation next-action handoff."
    )
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Private validation log path.")
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS), help="Private target tracker path.")
    parser.add_argument(
        "--message-pack",
        default=str(DEFAULT_MESSAGE_PACK),
        help="Private message pack path.",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Outreach date in YYYY-MM-DD form.")
    parser.add_argument("--out", help="Optional path to write the rendered handoff.")
    args = parser.parse_args(argv)
    try:
        dashboard_module = _load_dashboard_module()
        dashboard = dashboard_module.build_dashboard(
            log_path=args.log,
            targets_path=args.targets,
            message_pack_path=args.message_pack,
            require_date=args.date,
        )
        git_head = _git_head()
        rendered = render_next_action(
            dashboard,
            run_date=args.date,
            git_head=git_head,
            git_worktree_state=_git_worktree_state(),
            github_ci_summary=_github_ci_summary(_git_commit_sha()),
        )
    except Exception as exc:
        print(f"validation next action failed: {exc}", file=sys.stderr)
        return 1
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _lower_bool(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return "unavailable"


def _git_head() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _git_commit_sha() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _git_worktree_state() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return "dirty" if completed.stdout.strip() else "clean"


def _github_ci_summary(commit_sha: str | None) -> str | None:
    if not commit_sha:
        return None
    fallback = (
        "`unavailable`; run `gh run list --repo Ayush1298567/Prophet "
        f"--commit {commit_sha} --limit 1` before release decisions."
    )
    try:
        completed = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--repo",
                "Ayush1298567/Prophet",
                "--commit",
                commit_sha,
                "--limit",
                "1",
                "--json",
                "status,conclusion,url,name,headSha",
            ],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        runs = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return fallback
    if not isinstance(runs, list) or not runs:
        return (
            "`not_found`; run `gh run list --repo Ayush1298567/Prophet "
            f"--commit {commit_sha} --limit 1` before release decisions."
        )
    run = runs[0]
    if not isinstance(run, dict):
        return fallback
    conclusion = str(run.get("conclusion") or "pending")
    status = str(run.get("status") or "unknown")
    name = str(run.get("name") or "workflow")
    url = str(run.get("url") or "")
    summary = f"`{conclusion}` (`{status}`, `{name}`)"
    if url:
        summary = f"{summary}: {url}"
    return summary


def _load_dashboard_module() -> Any:
    script_path = Path(__file__).with_name("validation-sprint-dashboard.py")
    spec = importlib.util.spec_from_file_location("validation_sprint_dashboard", script_path)
    if spec is None or spec.loader is None:
        raise ValidationNextActionError("could not load validation sprint dashboard")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
