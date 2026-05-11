#!/usr/bin/env python3
"""Render the ignored private working-product handoff for restored sessions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_LOG = Path("validation/private/customer-validation-log.json")
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_MESSAGE_PACK = Path("validation/private/today-message-pack.json")
DEFAULT_OUT = Path("validation/private/WORKING_PRODUCT_HANDOFF.md")
DEFAULT_CONTROL_HOST = "127.0.0.1"
DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_CONTROL_PORT = 8787
DEFAULT_UI_PORT = 5173


class WorkingProductHandoffError(ValueError):
    """Raised when the working-product handoff cannot be rendered."""


def render_handoff(
    dashboard: dict[str, Any],
    *,
    run_date: str,
    ui_url: str,
    readiness_url: str,
    handoff_command: str,
    live_check_command: str,
    git_branch: str | None,
    git_head_short: str | None,
    git_head_full: str | None,
    git_worktree_state: str | None,
    readiness: dict[str, Any],
) -> str:
    build_gate = dashboard["build_gate"]
    customer = dashboard["customer_validation"]
    target_backed = dashboard.get("target_backed_validation", {})
    outreach = dashboard.get("outreach_execution", {})
    counts = outreach.get("counts") or {}
    gaps = (customer.get("gaps_to_verdicts") or {}).get("build_next_slice") or {}
    readiness_text = _format_readiness(readiness)
    lines = [
        "# Prophet Working Product Handoff",
        "",
        f"Date: {run_date}",
        "",
        "This is a private local operator note. It is ignored by git and must not be",
        "committed, attached to buyers, or treated as proof of buyer demand.",
        "",
        "## Current Repo State",
        "",
        f"- Branch: `{git_branch or 'unknown'}`",
        f"- Head: `{git_head_short or 'unknown'}`"
        + (f" (`{git_head_full}`)" if git_head_full else ""),
        f"- Worktree: `{git_worktree_state or 'unknown'}`",
        "",
        "## Working Product Path",
        "",
        f"- Evaluator UI: `{ui_url}`",
        f"- Readiness API: `{readiness_url}`",
        f"- Last readiness check: {readiness_text}",
        "",
        "Refresh this handoff with:",
        "",
        "```bash",
        handoff_command,
        "```",
        "",
        "Verify the running local product with:",
        "",
        "```bash",
        live_check_command,
        "```",
        "",
        "Use the default pilot readiness gate before sharing the local buyer pilot:",
        "",
        "```bash",
        f"make pilot-ready-check-full DATE={run_date}",
        "```",
        "",
        "## Build Gate",
        "",
        f"- Customer validation verdict: `{customer.get('verdict')}`",
        f"- Target-backed validation verdict: `{target_backed.get('verdict')}`",
        f"- `allowed_to_build_next_slice`: `{str(build_gate.get('allowed_to_build_next_slice')).lower()}`",
        f"- Build gate reason: {build_gate.get('reason')}",
        f"- Build-next-slice gaps: {json.dumps(gaps, sort_keys=True)}",
        "",
        "Do not add production platform scope until real target-backed validation",
        "reaches `build_next_slice`.",
        "",
        "## Validation Sprint State",
        "",
        f"- Pending send/update: `{counts.get('pending_send_or_update', 'unavailable')}`",
        f"- Needs attention: `{counts.get('needs_attention', 'unavailable')}`",
        f"- Dry-run verified: `{outreach.get('dry_run_verified_count', 'unavailable')}`",
        f"- Send-copy state: `{outreach.get('send_copy_state', 'unavailable')}`",
        f"- Send-copy batch state: `{outreach.get('send_copy_batch_state', 'unavailable')}`",
        f"- Contact-form copy state: `{outreach.get('contact_form_copy_state', 'unavailable')}`",
        f"- Next pending target: `{outreach.get('next_pending_target_label', 'unavailable')}`",
        "",
        "The repo intentionally does not store recipient names, emails, LinkedIn URLs,",
        "or outbound channel details. To actually send a draft, the operator must use",
        "an external outreach channel and a real contact selected outside the repo.",
        "",
        "## Next External Action",
        "",
        "Before outreach, run:",
        "",
        "```bash",
        str(outreach.get("next_pending_pre_send_check_command") or f"make validation-pre-send-check TARGET=target-label DATE={run_date}"),
        "```",
        "",
        "If it passes, send only the copy-only text from:",
        "",
        "```text",
        str(outreach.get("send_copy_path") or "validation/private/today-send-copy.txt"),
        "```",
        "",
        "After the message is actually sent, update the private tracker:",
        "",
        "```bash",
        str(outreach.get("next_pending_confirmed_apply_command") or f"make validation-apply-draft TARGET=target-label DATE={run_date} CONFIRM_SENT=1"),
        f"make validation-status DATE={run_date}",
        f"make validation-dashboard DATE={run_date}",
        "```",
        "",
        "## Boundaries",
        "",
        "- Do not send tracker metadata, target labels, manifests, checklists, or private",
        "  validation paths to buyers.",
        "- Do not run `CONFIRM_SENT=1` until the message has actually been sent.",
        "- Do not run `CONFIRM_TARGET=1`, `CONFIRM_LOG=1`, or `CONFIRM_PRUNE=1` without",
        "  the corresponding real reviewed action.",
        "- Do not treat example-seed validation counts as buyer traction.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render ignored private working-product handoff from current local state."
    )
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Private validation log path.")
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS), help="Private target tracker path.")
    parser.add_argument(
        "--message-pack",
        default=str(DEFAULT_MESSAGE_PACK),
        help="Private message pack path.",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Run date in YYYY-MM-DD form.")
    parser.add_argument("--control-host", default=DEFAULT_CONTROL_HOST, help="Control API host.")
    parser.add_argument("--ui-host", default=DEFAULT_UI_HOST, help="Evaluator UI host.")
    parser.add_argument("--control-port", type=int, default=DEFAULT_CONTROL_PORT, help="Control API port.")
    parser.add_argument("--ui-port", type=int, default=DEFAULT_UI_PORT, help="Evaluator UI port.")
    parser.add_argument(
        "--skip-readiness-check",
        action="store_true",
        help="Do not call the local readiness API while rendering.",
    )
    parser.add_argument(
        "--require-readiness-ok",
        action="store_true",
        help="Fail if the local readiness API is unreachable or reports blocking failures.",
    )
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
        ui_url = f"http://{args.ui_host}:{args.ui_port}/"
        readiness_url = f"http://{args.control_host}:{args.control_port}/api/readiness"
        readiness = (
            {"checked": False, "ok": None, "blocking_failures": None, "error": "skipped"}
            if args.skip_readiness_check
            else _readiness_summary(readiness_url)
        )
        if args.require_readiness_ok and not readiness.get("ok"):
            raise WorkingProductHandoffError(_format_readiness(readiness))
        rendered = render_handoff(
            dashboard,
            run_date=args.date,
            ui_url=ui_url,
            readiness_url=readiness_url,
            handoff_command=_handoff_command(args.control_port, args.ui_port, args.date),
            live_check_command=_live_check_command(args.control_port, args.ui_port),
            git_branch=_git_output(["git", "branch", "--show-current"]),
            git_head_short=_git_output(["git", "rev-parse", "--short", "HEAD"]),
            git_head_full=_git_output(["git", "rev-parse", "HEAD"]),
            git_worktree_state=_git_worktree_state(),
            readiness=readiness,
        )
    except Exception as exc:
        print(f"working product handoff failed: {exc}", file=sys.stderr)
        return 1
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _format_readiness(readiness: dict[str, Any]) -> str:
    if not readiness.get("checked"):
        return "not checked"
    if readiness.get("ok"):
        return f"`ok: true`, `{readiness.get('blocking_failures', 0)}` blocking failures"
    return f"`ok: false` ({readiness.get('error') or 'readiness API reported failure'})"


def _readiness_summary(readiness_url: str) -> dict[str, Any]:
    try:
        with urlopen(readiness_url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return {"checked": True, "ok": False, "blocking_failures": None, "error": str(exc)}
    if not isinstance(payload, dict):
        return {"checked": True, "ok": False, "blocking_failures": None, "error": "unexpected payload"}
    blocking_failures = payload.get("blockingFailures")
    if blocking_failures is None:
        blocking_failures = sum(
            1
            for check in payload.get("checks", [])
            if isinstance(check, dict)
            and check.get("blocking") is True
            and check.get("status") not in {"pass", "warning"}
        )
    ok = payload.get("ok") is True and int(blocking_failures or 0) == 0
    return {
        "checked": True,
        "ok": ok,
        "blocking_failures": int(blocking_failures or 0),
        "error": None if ok else "blocking readiness failure",
    }


def _live_check_command(control_port: int, ui_port: int) -> str:
    if control_port == DEFAULT_CONTROL_PORT and ui_port == DEFAULT_UI_PORT:
        return "make console-live-check"
    return f"PROPHET_CONTROL_PORT={control_port} PROPHET_CONSOLE_PORT={ui_port} make console-live-check"


def _handoff_command(control_port: int, ui_port: int, run_date: str) -> str:
    command = f"make validation-working-product-handoff-save DATE={run_date}"
    if control_port == DEFAULT_CONTROL_PORT and ui_port == DEFAULT_UI_PORT:
        return command
    return f"PROPHET_CONTROL_PORT={control_port} PROPHET_CONSOLE_PORT={ui_port} {command}"


def _git_worktree_state() -> str | None:
    output = _git_output(["git", "status", "--short", "--untracked-files=all"])
    if output is None:
        return None
    return "dirty" if output else "clean"


def _git_output(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _load_dashboard_module() -> Any:
    script_path = Path(__file__).with_name("validation-sprint-dashboard.py")
    spec = importlib.util.spec_from_file_location("validation_sprint_dashboard", script_path)
    if spec is None or spec.loader is None:
        raise WorkingProductHandoffError("could not load validation sprint dashboard")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
