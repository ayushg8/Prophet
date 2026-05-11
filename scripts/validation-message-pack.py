#!/usr/bin/env python3
"""Build safe outreach message drafts from a Prophet validation outreach block."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


MESSAGE_PACK_SCHEMA_VERSION = "prophet_validation_message_pack.v0.1"
OUTREACH_BLOCK_SCHEMA_VERSION = "prophet_validation_outreach_block.v0.1"
DEFAULT_BLOCK = Path("validation/private/today-outreach-block.json")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?(?:\(?[2-9][0-9]{2}\)?[-.\s]?)?[2-9][0-9]{2}[-.\s]?[0-9]{4}"
)
URL_RE = re.compile(r"https?://", re.IGNORECASE)
PRIVATE_HOST_RE = re.compile(
    r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:corp|internal|local|lan|private)\b",
    re.IGNORECASE,
)


class MessagePackError(ValueError):
    """Raised when message drafts cannot be generated safely."""


def build_message_pack(block: dict[str, Any]) -> dict[str, Any]:
    errors = validate_block(block)
    if errors:
        raise MessagePackError("; ".join(errors))

    run_date = block["generated_for"]
    follow_up_due = _follow_up_due(run_date)
    drafts: list[dict[str, Any]] = []
    for group_key, group_label, kind in (
        ("targeted_asks", "targeted_ask", "first_touch"),
        ("follow_up_backfill_asks", "follow_up_backfill", "first_touch"),
        ("follow_ups", "follow_up", "follow_up"),
        ("referral_asks", "referral_ask", "referral"),
    ):
        for target in block.get(group_key, []):
            drafts.append(
                _draft_for_target(
                    target,
                    group_label=group_label,
                    kind=kind,
                    run_date=run_date,
                    follow_up_due=follow_up_due,
                )
            )

    return {
        "schema_version": MESSAGE_PACK_SCHEMA_VERSION,
        "outreach_block_schema_version": block["schema_version"],
        "generated_for": block["generated_for"],
        "source_updated_at": block.get("source_updated_at"),
        "target_labels": sorted(str(draft["target_label"]) for draft in drafts),
        "draft_count": len(drafts),
        "drafts": drafts,
        "operator_notes": [
            "Replace only the recipient name and channel-specific greeting before sending.",
            "Do not add customer names, emails, URLs, hostnames, IPs, screenshots, or raw artifacts.",
            "Use the Make dry-run command before sending and before writing tracker changes.",
            "Use the CONFIRM_SENT=1 command only after the message was actually sent.",
            f"Rerun make validation-status DATE={run_date} after confirmed tracker updates.",
            "If a buyer asks for live testing or offensive capability, disqualify rather than promise it.",
        ],
    }


def validate_block(block: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if block.get("schema_version") != OUTREACH_BLOCK_SCHEMA_VERSION:
        errors.append(f"schema_version must be {OUTREACH_BLOCK_SCHEMA_VERSION}")
    if not _non_empty_str(block.get("generated_for")):
        errors.append("generated_for is required")
    _scan_sensitive(block, "block", errors)
    for key in ("targeted_asks", "follow_up_backfill_asks", "follow_ups", "referral_asks"):
        value = block.get(key, [])
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            continue
        for index, target in enumerate(value, start=1):
            context = f"{key}[{index}]"
            if not isinstance(target, dict):
                errors.append(f"{context} must be an object")
                continue
            for field in (
                "target_label",
                "segment",
                "persona",
                "priority",
                "source",
                "status",
                "planned_ask",
                "next_action",
            ):
                if not _non_empty_str(target.get(field)):
                    errors.append(f"{context}.{field} is required")
    return errors


def render_markdown(pack: dict[str, Any]) -> str:
    lines = [
        f"# Prophet Validation Message Pack - {pack['generated_for']}",
        "",
        f"Draft count: {pack['draft_count']}",
        "",
        "## Execution Checklist",
        "",
    ]
    for draft in pack["drafts"]:
        lines.append(
            "- [ ] "
            f"{draft['target_label']} ({draft['group']}): run "
            f"`{draft['dry_run_apply_command']}`, send copy-only text, then run "
            f"`{draft['confirmed_apply_command']}` only after confirming the "
            "message was sent."
        )
    lines.extend(
        [
            "",
            "## Drafts",
            "",
        ]
    )
    for draft in pack["drafts"]:
        lines.extend(
            [
                f"## {draft['target_label']} - {draft['group']}",
                "",
                f"- Persona: {draft['persona_label']}",
                f"- Segment: {draft['segment_label']}",
                f"- Source: {draft['source_label']}",
                f"- Operator angle: {draft['operator_angle']}",
                f"- Next tracker action: {draft['next_action']}",
                f"- Safe dry-run apply command: `{draft['dry_run_apply_command']}`",
                f"- Confirmed-send apply command: `{draft['confirmed_apply_command']}`",
                f"- Tracker update command: `{draft['tracker_update_command']}`",
                "",
                "Subject options:",
            ]
        )
        for subject in draft["subject_options"]:
            lines.append(f"- {subject}")
        lines.extend(["", "Message:", "", "```text", draft["body"], "```", ""])
    lines.append("## Operator Notes")
    for note in pack["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def render_send_text(pack: dict[str, Any]) -> str:
    """Render copy-ready subject and body for one selected draft."""
    if pack["draft_count"] != 1:
        raise MessagePackError("send-text format requires exactly one draft; use --target-label")
    draft = pack["drafts"][0]
    subject = draft["subject_options"][0]
    rendered = "\n".join([f"Subject: {subject}", "", draft["body"], ""])
    _validate_send_text(
        rendered,
        target_labels=set(pack.get("target_labels") or [draft["target_label"]]),
    )
    return rendered


def filter_pack_by_target_label(pack: dict[str, Any], target_label: str) -> dict[str, Any]:
    drafts = [
        draft
        for draft in pack["drafts"]
        if draft["target_label"] == target_label
    ]
    if not drafts:
        raise MessagePackError(f"target_label not found in message pack: {target_label}")
    filtered = dict(pack)
    filtered["drafts"] = drafts
    filtered["draft_count"] = len(drafts)
    return filtered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build safe outreach message drafts from today's validation block."
    )
    parser.add_argument(
        "--block",
        default=str(DEFAULT_BLOCK),
        help="Path to prophet_validation_outreach_block.v0.1 JSON.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "send-text"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--target-label",
        help="Render only one draft for the given anonymized target label.",
    )
    parser.add_argument(
        "--require-date",
        help="Require the message pack generated_for date to match YYYY-MM-DD.",
    )
    parser.add_argument("--out", help="Optional path to write the rendered pack.")
    args = parser.parse_args(argv)
    try:
        block = json.loads(Path(args.block).read_text(encoding="utf-8"))
        if not isinstance(block, dict):
            raise MessagePackError("outreach block must be a JSON object")
        pack = build_message_pack(block)
        if args.require_date:
            _require_generated_for(pack, args.require_date)
        if args.target_label:
            pack = filter_pack_by_target_label(pack, args.target_label)
    except (OSError, json.JSONDecodeError, MessagePackError) as exc:
        print(f"validation message pack failed: {exc}", file=sys.stderr)
        return 1

    try:
        if args.format == "markdown":
            rendered = render_markdown(pack)
        elif args.format == "send-text":
            rendered = render_send_text(pack)
        else:
            rendered = json.dumps(pack, indent=2, sort_keys=True) + "\n"
    except MessagePackError as exc:
        print(f"validation message pack failed: {exc}", file=sys.stderr)
        return 1
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _draft_for_target(
    target: dict[str, Any],
    *,
    group_label: str,
    kind: str,
    run_date: str,
    follow_up_due: str,
) -> dict[str, Any]:
    persona = _humanize(target["persona"])
    segment = _humanize(target["segment"])
    source = target["source"]
    body = _message_body(target, persona=persona, segment=segment, kind=kind, source=source)
    tracker_update = _tracker_update_command(
        target["target_label"],
        kind=kind,
        run_date=run_date,
        follow_up_due=follow_up_due,
    )
    return {
        "target_label": target["target_label"],
        "group": group_label,
        "kind": kind,
        "source": source,
        "source_label": _humanize(source),
        "persona_label": persona,
        "segment_label": segment,
        "operator_angle": target["planned_ask"],
        "next_action": target["next_action"],
        "subject_options": _subject_options(kind, source=source),
        "body": body,
        "dry_run_apply_command": (
            "make validation-apply-draft "
            f"TARGET={target['target_label']} DATE={run_date}"
        ),
        "confirmed_apply_command": (
            "make validation-apply-draft "
            f"TARGET={target['target_label']} DATE={run_date} CONFIRM_SENT=1"
        ),
        "tracker_update_command": tracker_update,
    }


def _subject_options(kind: str, *, source: str) -> list[str]:
    if kind == "referral":
        return [
            "Intro to a security leader with prioritization pain?",
            "Who owns vulnerability prioritization evidence?",
        ]
    if kind == "follow_up":
        return [
            "Following up on prioritization evidence",
            "Quick follow-up on hardening decisions",
        ]
    if source == "warm_intro_needed":
        return [
            "Intro to someone who owns prioritization evidence?",
            "Who should I learn from on hardening priorities?",
        ]
    return [
        "Quick question on vulnerability prioritization evidence",
        "How do you prove what to harden first?",
    ]


def _message_body(
    target: dict[str, Any],
    *,
    persona: str,
    segment: str,
    kind: str,
    source: str,
) -> str:
    if kind == "referral":
        return (
            "Hi <first name>,\n\n"
            "I'm looking for one operationally honest intro, not broad feedback.\n\n"
            "The person I need to learn from owns vulnerability prioritization, "
            "product security, platform security, CTI, or mission assurance and has "
            "personally had to answer: why are we hardening this exposure class first?\n\n"
            f"The current learning target is someone in a {persona} role across {segment}. "
            "Do you know someone who has had to build that evidence for leadership, "
            "a customer, CMMC, or a government requirement?\n\n"
            "No live data ask, no offensive work, no sales deck."
        )
    if kind == "follow_up":
        return (
            "Hi <first name>,\n\n"
            "Following up on the narrow workflow question: when KEV, CMMC, customer, "
            "or mission pressure hits, how do you prove what exposure class should "
            "be hardened first and what SOC or platform handoff should follow?\n\n"
            f"I'm trying to learn from people in {persona} roles across {segment}, especially "
            "where scanner, exposure-management, SIEM, SBOM, and ticketing outputs "
            "still require manual evidence assembly.\n\n"
            "If this is real in your world, could I ask 20 minutes of workflow "
            "questions? If your current stack already solves it, that answer is "
            "equally useful.\n\n"
            "No live data ask, no exploit tooling, no sales deck."
        )
    if source == "warm_intro_needed":
        return (
            "Hi <first name>,\n\n"
            f"I'm trying to find one operationally honest conversation with someone in a {persona} "
            f"role across {segment}.\n\n"
            "The workflow question is whether KEV, CMMC, customer, mission, or audit "
            "pressure still leaves a manual gap between scanner/exposure-management output "
            "and the evidence packet leadership or SOC teams actually trust.\n\n"
            "Do you know someone who has personally had to answer: what should we harden "
            "first, and why? I'm not looking for a sales intro first; I want 20 minutes "
            "of workflow discovery.\n\n"
            "No live data ask, no exploit tooling, no sales deck."
        )
    return (
        "Hi <first name>,\n\n"
        "I'm testing a narrow defensive workflow: evidence-backed vulnerability "
        "prioritization for teams that need to prove what exposure class gets "
        "hardened first and why.\n\n"
        f"I'm trying to learn from people in {persona} roles across {segment}. The specific "
        "question is whether KEV, CMMC, customer, mission, or audit pressure still "
        "leaves a manual gap between scanner/exposure-management output and the "
        "evidence packet leadership or SOC teams actually trust.\n\n"
        "Is that a real pain in your world, or does your current stack already "
        "solve it? If you have dealt with this recently, could I ask 20 minutes of "
        "workflow questions?\n\n"
        "No live data ask, no exploit tooling, no sales deck."
    )


def _humanize(value: str) -> str:
    text = value.replace("_", " ").strip()
    for acronym in ("cti", "dib", "sbom", "siem", "soc", "vp", "ciso"):
        text = re.sub(rf"\b{acronym}\b", acronym.upper(), text)
    return text


def _validate_send_text(rendered: str, *, target_labels: set[str]) -> None:
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
            raise MessagePackError(f"copy-only send text contains target label: {target_label}")
    for literal in blocked_literals:
        if literal in rendered:
            raise MessagePackError(
                f"copy-only send text contains tracker metadata: {literal}"
            )
    for regex, label in (
        (EMAIL_RE, "email-like text"),
        (URL_RE, "URL-like text"),
        (PHONE_RE, "phone-like text"),
        (PRIVATE_HOST_RE, "private hostname-like text"),
    ):
        if regex.search(rendered):
            raise MessagePackError(f"copy-only send text contains {label}")
    if re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", rendered):
        raise MessagePackError("copy-only send text contains IP-like text")


def _follow_up_due(run_date: str) -> str:
    try:
        parsed = date.fromisoformat(run_date)
    except ValueError as exc:
        raise MessagePackError("generated_for must be YYYY-MM-DD") from exc
    return (parsed + timedelta(days=3)).isoformat()


def _require_generated_for(pack: dict[str, Any], required_date: str) -> None:
    try:
        date.fromisoformat(required_date)
    except ValueError as exc:
        raise MessagePackError(f"require-date must be YYYY-MM-DD: {required_date}") from exc
    if pack["generated_for"] != required_date:
        raise MessagePackError(
            "message pack generated_for "
            f"{pack['generated_for']} does not match required date {required_date}"
        )


def _tracker_update_command(
    target_label: str,
    *,
    kind: str,
    run_date: str,
    follow_up_due: str,
) -> str:
    if kind == "referral":
        status = "intro_requested"
        next_action = "Follow up on intro request if no reply."
        required_statuses = ["identified", "intro_requested"]
    elif kind == "follow_up":
        status = "outreach_sent"
        next_action = "Send second follow-up or disqualify if no reply."
        required_statuses = ["follow_up_due"]
    else:
        status = "outreach_sent"
        next_action = "Send follow-up if no reply."
        required_statuses = ["identified", "intro_requested"]
    args = [
        "python3",
        "scripts/validation-target-update.py",
        "--target-label",
        target_label,
        "--status",
        status,
    ]
    for required_status in required_statuses:
        args.extend(["--require-current-status", required_status])
    args.extend(
        [
        "--last-touch",
        run_date,
        "--follow-up-due",
        follow_up_due,
        "--next-action",
        next_action,
        "--dry-run",
        ]
    )
    return " ".join(shlex.quote(arg) for arg in args)


def _scan_sensitive(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_sensitive(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_sensitive(item, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            errors.append(f"{path} contains email-like text")
        if PHONE_RE.search(value):
            errors.append(f"{path} contains phone-like text")
        if URL_RE.search(value):
            errors.append(f"{path} contains URL-like text")
        if PRIVATE_HOST_RE.search(value):
            errors.append(f"{path} contains private-hostname-like text")


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    raise SystemExit(main())
