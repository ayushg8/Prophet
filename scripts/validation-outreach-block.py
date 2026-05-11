#!/usr/bin/env python3
"""Build today's Prophet validation outreach block from safe target metadata."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


OUTREACH_BLOCK_SCHEMA_VERSION = "prophet_validation_outreach_block.v0.1"
DEFAULT_TARGETS = Path("validation/private/validation-targets.json")
DEFAULT_TARGETED_ASKS = 5
DEFAULT_FOLLOW_UPS = 2
DEFAULT_REFERRAL_ASKS = 1
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
TARGETED_STATUSES = {"identified", "intro_requested"}
FOLLOW_UP_STATUS = "follow_up_due"
DISQUALIFIED_STATUSES = {"completed", "disqualified"}


class OutreachBlockError(ValueError):
    """Raised when an outreach block cannot be generated safely."""


def build_outreach_block(
    value: dict[str, Any],
    *,
    run_date: str | None = None,
    targeted_ask_count: int = DEFAULT_TARGETED_ASKS,
    follow_up_count: int = DEFAULT_FOLLOW_UPS,
    referral_ask_count: int = DEFAULT_REFERRAL_ASKS,
) -> dict[str, Any]:
    generated_for = _validated_run_date(run_date)
    scorecard_module = _load_targets_scorecard_module()
    errors = scorecard_module.validate_targets(value)
    if errors:
        raise OutreachBlockError("; ".join(errors))
    targets = list(value.get("targets") or [])
    targeted_asks = _select_targeted_asks(targets, targeted_ask_count)
    follow_ups = _select_follow_ups(targets, follow_up_count)
    referral_asks = _select_referral_asks(
        targets,
        referral_ask_count,
        excluded_labels={target["target_label"] for target in targeted_asks},
    )
    follow_up_gap_count = max(0, follow_up_count - len(follow_ups))
    excluded_for_backfill = {
        target["target_label"]
        for target in [*targeted_asks, *follow_ups, *referral_asks]
    }
    follow_up_backfill_asks = _select_targeted_asks(
        targets,
        follow_up_gap_count,
        excluded_labels=excluded_for_backfill,
    )
    return {
        "schema_version": OUTREACH_BLOCK_SCHEMA_VERSION,
        "target_schema_version": value["schema_version"],
        "generated_for": generated_for,
        "source_updated_at": value.get("updated_at"),
        "daily_minimum": {
            "targeted_asks": targeted_ask_count,
            "follow_ups": follow_up_count,
            "referral_asks": referral_ask_count,
        },
        "targeted_asks": [_compact_target(target) for target in targeted_asks],
        "follow_ups": [_compact_target(target) for target in follow_ups],
        "referral_asks": [_compact_target(target) for target in referral_asks],
        "follow_up_backfill_asks": [
            _compact_target(target) for target in follow_up_backfill_asks
        ],
        "gaps": {
            "targeted_ask_gap_count": max(0, targeted_ask_count - len(targeted_asks)),
            "follow_up_gap_count": follow_up_gap_count,
            "follow_up_backfill_count": len(follow_up_backfill_asks),
            "referral_ask_gap_count": max(0, referral_ask_count - len(referral_asks)),
        },
        "operator_notes": [
            "Use docs/OUTREACH_PLAYBOOK.md for message templates.",
            "Use docs/CUSTOMER_DISCOVERY_GUIDE.md once a buyer accepts a call.",
            "After each ask, use make validation-apply-draft to dry-run and then confirm the tracker update.",
            "If no follow-ups are due, use the follow-up gap backfill asks as extra first-touch asks.",
            "Log outcomes only in validation/private/customer-validation-log.json.",
            "Do not add names, emails, phone numbers, URLs, private hostnames, IPs, or raw customer notes.",
        ],
    }


def render_markdown(block: dict[str, Any]) -> str:
    lines = [
        f"# Prophet Outreach Block - {block['generated_for']}",
        "",
        "## Targeted Asks",
    ]
    lines.extend(_render_target_list(block["targeted_asks"], empty="No targeted asks available."))
    lines.extend(["", "## Follow-Ups"])
    lines.extend(_render_target_list(block["follow_ups"], empty="No follow-ups are currently due."))
    lines.extend(["", "## Follow-Up Gap Backfill"])
    lines.extend(
        _render_target_list(
            block["follow_up_backfill_asks"],
            empty="No extra first-touch asks available to backfill missing follow-ups.",
        )
    )
    lines.extend(["", "## Referral Asks"])
    lines.extend(_render_target_list(block["referral_asks"], empty="No referral asks available."))
    lines.extend(["", "## Gaps"])
    for key, value in block["gaps"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Operator Notes"])
    for note in block["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build today's safe Prophet validation outreach block."
    )
    parser.add_argument(
        "--targets",
        default=str(DEFAULT_TARGETS),
        help="Path to prophet_validation_targets.v0.1 JSON.",
    )
    parser.add_argument("--date", help="Outreach date in YYYY-MM-DD form.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument("--out", help="Optional path to write the rendered block.")
    args = parser.parse_args(argv)
    try:
        targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
        if not isinstance(targets, dict):
            raise OutreachBlockError("target list must be a JSON object")
        block = build_outreach_block(targets, run_date=args.date)
    except (OSError, json.JSONDecodeError, OutreachBlockError) as exc:
        print(f"validation outreach block failed: {exc}", file=sys.stderr)
        return 1
    rendered = (
        render_markdown(block)
        if args.format == "markdown"
        else json.dumps(block, indent=2, sort_keys=True) + "\n"
    )
    print(rendered, end="")
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    return 0


def _select_targeted_asks(
    targets: list[dict[str, Any]],
    count: int,
    *,
    excluded_labels: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded_labels = excluded_labels or set()
    candidates = [
        target
        for target in targets
        if target["status"] in TARGETED_STATUSES
        and target["target_label"] not in excluded_labels
    ]
    return sorted(candidates, key=_target_sort_key)[:count]


def _validated_run_date(run_date: str | None) -> str:
    if run_date is None:
        return date.today().isoformat()
    try:
        return date.fromisoformat(run_date).isoformat()
    except ValueError as exc:
        raise OutreachBlockError("date must be YYYY-MM-DD") from exc


def _select_follow_ups(targets: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    candidates = [target for target in targets if target["status"] == FOLLOW_UP_STATUS]
    return sorted(candidates, key=_target_sort_key)[:count]


def _select_referral_asks(
    targets: list[dict[str, Any]],
    count: int,
    *,
    excluded_labels: set[str],
) -> list[dict[str, Any]]:
    candidates = [
        target
        for target in targets
        if target["status"] not in DISQUALIFIED_STATUSES
        and target["target_label"] not in excluded_labels
        and target["source"] == "warm_intro_needed"
    ]
    return sorted(candidates, key=_target_sort_key)[:count]


def _target_sort_key(target: dict[str, Any]) -> tuple[int, int, str]:
    status_rank = 0 if target["status"] == "intro_requested" else 1
    return (
        PRIORITY_RANK.get(str(target["priority"]), 99),
        status_rank,
        str(target["target_label"]),
    )


def _compact_target(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_label": target["target_label"],
        "segment": target["segment"],
        "persona": target["persona"],
        "priority": target["priority"],
        "source": target["source"],
        "status": target["status"],
        "planned_ask": target["planned_ask"],
        "next_action": target["next_action"],
    }


def _render_target_list(targets: list[dict[str, Any]], *, empty: str) -> list[str]:
    if not targets:
        return [f"- {empty}"]
    lines: list[str] = []
    for target in targets:
        lines.append(
            "- "
            f"{target['target_label']} ({target['priority']}, {target['segment']}, "
            f"{target['persona']}): {target['planned_ask']} Next: {target['next_action']}"
        )
    return lines


def _load_targets_scorecard_module() -> Any:
    script_path = Path(__file__).with_name("validation-targets-scorecard.py")
    spec = importlib.util.spec_from_file_location("validation_targets_scorecard", script_path)
    if spec is None or spec.loader is None:
        raise OutreachBlockError("could not load validation target validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
