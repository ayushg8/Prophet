#!/usr/bin/env python3
"""Validate and score Prophet's production readiness backlog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


BACKLOG_SCHEMA_VERSION = "prophet_production_readiness_backlog.v0.1"
SCORECARD_SCHEMA_VERSION = "prophet_production_readiness_scorecard.v0.1"
ALLOWED_STATUSES = {"done", "in_progress", "planned", "blocked"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_RISK_TAGS = {
    "buyer",
    "compliance",
    "console",
    "data",
    "docs",
    "identity",
    "infra",
    "integrations",
    "ops",
    "release",
    "safety",
    "sandbox",
    "security",
}
ID_RE = re.compile(r"^M[0-9]+(?:-[0-9]{2})?$")


class ProductionReadinessError(ValueError):
    """Raised when the production readiness backlog is invalid."""


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProductionReadinessError("backlog must be a JSON object")
    return value


def validate_backlog(backlog: dict[str, Any], *, root: str | Path = ".") -> list[str]:
    errors: list[str] = []
    repo_root = Path(root)
    if backlog.get("schema_version") != BACKLOG_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BACKLOG_SCHEMA_VERSION}")
    if not _non_empty_str(backlog.get("updated_at")):
        errors.append("updated_at is required")
    if not _non_empty_str(backlog.get("target_definition")):
        errors.append("target_definition is required")

    milestones = backlog.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        errors.append("milestones must be a non-empty list")
        return errors

    seen_milestone_ids: set[str] = set()
    seen_work_item_ids: set[str] = set()
    for milestone_index, milestone in enumerate(milestones, start=1):
        context = f"milestones[{milestone_index}]"
        if not isinstance(milestone, dict):
            errors.append(f"{context} must be object")
            continue
        milestone_id = str(milestone.get("id", ""))
        _validate_record_common(
            milestone,
            context=context,
            errors=errors,
            require_priority=False,
        )
        if not ID_RE.fullmatch(milestone_id) or "-" in milestone_id:
            errors.append(f"{context}.id must look like M0, M1, ...")
        if milestone_id in seen_milestone_ids:
            errors.append(f"{context}.id duplicates {milestone_id}")
        seen_milestone_ids.add(milestone_id)

        work_items = milestone.get("work_items")
        if not isinstance(work_items, list) or not work_items:
            errors.append(f"{context}.work_items must be a non-empty list")
            continue
        for item_index, item in enumerate(work_items, start=1):
            item_context = f"{context}.work_items[{item_index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_context} must be object")
                continue
            item_id = str(item.get("id", ""))
            _validate_record_common(
                item,
                context=item_context,
                errors=errors,
                require_priority=True,
            )
            if not ID_RE.fullmatch(item_id) or "-" not in item_id:
                errors.append(f"{item_context}.id must look like M0-01")
            elif milestone_id and not item_id.startswith(f"{milestone_id}-"):
                errors.append(f"{item_context}.id must use parent milestone prefix {milestone_id}")
            if item_id in seen_work_item_ids:
                errors.append(f"{item_context}.id duplicates {item_id}")
            seen_work_item_ids.add(item_id)
            if item.get("status") == "done":
                evidence_paths = item.get("evidence_paths")
                if not isinstance(evidence_paths, list) or not evidence_paths:
                    errors.append(f"{item_context}.evidence_paths is required for done items")
                else:
                    for evidence_path in evidence_paths:
                        if not _non_empty_str(evidence_path):
                            errors.append(f"{item_context}.evidence_paths contains non-string path")
                            continue
                        if str(evidence_path).startswith(("http://", "https://")):
                            continue
                        if not (repo_root / str(evidence_path)).exists():
                            errors.append(f"{item_context}.evidence_paths missing file: {evidence_path}")
            if item.get("status") == "blocked" and not _non_empty_str(item.get("blocker")):
                errors.append(f"{item_context}.blocker is required for blocked items")
    return errors


def build_scorecard(backlog: dict[str, Any], *, root: str | Path = ".") -> dict[str, Any]:
    errors = validate_backlog(backlog, root=root)
    if errors:
        raise ProductionReadinessError("; ".join(errors))

    milestones = backlog["milestones"]
    milestone_statuses = Counter(str(milestone["status"]) for milestone in milestones)
    work_items = list(_iter_work_items(backlog))
    work_item_statuses = Counter(str(item["status"]) for item in work_items)
    priority_statuses: dict[str, dict[str, int]] = {}
    for priority in sorted(ALLOWED_PRIORITIES):
        priority_items = [item for item in work_items if item["priority"] == priority]
        priority_statuses[priority] = dict(sorted(Counter(item["status"] for item in priority_items).items()))

    done_count = work_item_statuses.get("done", 0)
    total_count = len(work_items)
    readiness_percent = round((done_count / total_count) * 100, 1) if total_count else 0.0
    critical_open = [
        {
            "id": item["id"],
            "title": item["title"],
            "priority": item["priority"],
            "status": item["status"],
            "target_version": item["target_version"],
            "risk_tags": item["risk_tags"],
        }
        for item in work_items
        if item["priority"] in {"P0", "P1"} and item["status"] != "done"
    ]
    return {
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "backlog_schema_version": backlog["schema_version"],
        "updated_at": backlog["updated_at"],
        "target_definition": backlog["target_definition"],
        "milestone_count": len(milestones),
        "work_item_count": total_count,
        "readiness_percent": readiness_percent,
        "milestone_statuses": dict(sorted(milestone_statuses.items())),
        "work_item_statuses": dict(sorted(work_item_statuses.items())),
        "priority_statuses": priority_statuses,
        "critical_open_count": len(critical_open),
        "critical_open": critical_open,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and score Prophet production readiness backlog."
    )
    parser.add_argument(
        "--backlog",
        default="docs/production-readiness-backlog.json",
        help="Path to prophet_production_readiness_backlog.v0.1 JSON",
    )
    parser.add_argument("--out-json", help="Optional path to write scorecard JSON")
    args = parser.parse_args(argv)

    try:
        backlog_path = Path(args.backlog)
        scorecard = build_scorecard(load_json(backlog_path), root=backlog_path.resolve().parents[1])
    except (OSError, json.JSONDecodeError, ProductionReadinessError) as exc:
        print(f"production readiness scorecard failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(scorecard, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


def _validate_record_common(
    record: dict[str, Any],
    *,
    context: str,
    errors: list[str],
    require_priority: bool,
) -> None:
    for key in ("id", "name" if not require_priority else "title", "owner", "target_version", "status"):
        if not _non_empty_str(record.get(key)):
            errors.append(f"{context}.{key} is required")
    status = record.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"{context}.status must be one of {sorted(ALLOWED_STATUSES)}")
    if require_priority and record.get("priority") not in ALLOWED_PRIORITIES:
        errors.append(f"{context}.priority must be one of {sorted(ALLOWED_PRIORITIES)}")
    risk_tags = record.get("risk_tags")
    if not isinstance(risk_tags, list) or not risk_tags:
        errors.append(f"{context}.risk_tags must be a non-empty list")
    else:
        unknown = sorted({tag for tag in risk_tags if tag not in ALLOWED_RISK_TAGS})
        if unknown:
            errors.append(f"{context}.risk_tags contains unknown tags: {unknown}")
    gates = record.get("acceptance_gates")
    if not isinstance(gates, list) or not all(_non_empty_str(gate) for gate in gates):
        errors.append(f"{context}.acceptance_gates must be non-empty list[str]")


def _iter_work_items(backlog: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for milestone in backlog.get("milestones", []):
        if not isinstance(milestone, dict):
            continue
        for item in milestone.get("work_items", []):
            if isinstance(item, dict):
                yield item


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    raise SystemExit(main())
