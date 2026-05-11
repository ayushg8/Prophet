#!/usr/bin/env python3
"""Dry-run or prune generated private validation artifacts after review."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


PRUNE_SCHEMA_VERSION = "prophet_validation_private_prune.v0.1"
DEFAULT_PRIVATE_DIR = Path("validation/private")
DEFAULT_WEEKLY_REVIEW = DEFAULT_PRIVATE_DIR / "today-weekly-review.json"
PROTECTED_FILENAMES = {
    "README.md",
    "customer-validation-interview.template.json",
    "customer-validation-log.json",
    "validation-targets.json",
}


class ValidationPruneError(ValueError):
    """Raised when private validation artifacts cannot be pruned safely."""


def build_prune_plan(
    review: dict[str, Any],
    *,
    private_dir: Path,
    review_date: str | None = None,
) -> dict[str, Any]:
    if review.get("schema_version") != "prophet_validation_weekly_review.v0.1":
        raise ValidationPruneError("weekly review schema_version is unsupported")
    run_date = _parse_date(review_date or str(review.get("review_date") or ""), "review-date")
    if review.get("review_date") != run_date.isoformat():
        raise ValidationPruneError("weekly review date does not match requested review-date")
    artifacts = review.get("private_artifacts")
    if not isinstance(artifacts, dict):
        raise ValidationPruneError("weekly review private_artifacts must be object")

    private_dir = private_dir.resolve()
    batch_dirs: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    blocked: list[dict[str, Any]] = []

    for warning in artifacts.get("send_copy_warnings") or []:
        if not isinstance(warning, dict):
            continue
        raw_path = str(warning.get("path") or "")
        reasons = [str(reason) for reason in (warning.get("reasons") or [])]
        path = _candidate_path(raw_path, private_dir)
        issue = _candidate_issue(path, private_dir)
        if issue:
            blocked.append({"path": raw_path, "reason": issue})
            continue
        batch_date = _send_copy_batch_date(path)
        if batch_date is not None and batch_date != run_date:
            batch_dirs[str(path.parent)] = {
                "path": str(path.parent),
                "kind": "outdated_send_copy_batch",
                "reasons": sorted(set(reasons + ["date_mismatch"])),
            }
        else:
            files[str(path)] = {
                "path": str(path),
                "kind": "unsafe_send_copy_file",
                "reasons": sorted(set(reasons)),
            }

    for stale in artifacts.get("stale_files") or []:
        if not isinstance(stale, dict):
            continue
        raw_path = str(stale.get("path") or "")
        path = _candidate_path(raw_path, private_dir)
        issue = _candidate_issue(path, private_dir)
        if issue:
            blocked.append({"path": raw_path, "reason": issue})
            continue
        if path.name in PROTECTED_FILENAMES:
            blocked.append({"path": str(path), "reason": "protected_private_state_file"})
            continue
        if not _is_generated_private_artifact(path, private_dir):
            blocked.append({"path": str(path), "reason": "not_a_generated_private_artifact"})
            continue
        files.setdefault(
            str(path),
            {
                "path": str(path),
                "kind": "stale_generated_private_file",
                "reasons": ["stale_file"],
            },
        )

    candidates = sorted(batch_dirs.values(), key=lambda item: item["path"]) + sorted(
        files.values(), key=lambda item: item["path"]
    )
    return {
        "schema_version": PRUNE_SCHEMA_VERSION,
        "review_date": run_date.isoformat(),
        "private_dir": str(private_dir),
        "dry_run": True,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "blocked_count": len(blocked),
        "blocked": blocked,
        "operator_notes": [
            "Dry-run only by default; no files are removed unless --confirm-prune is supplied.",
            "Only generated ignored private validation artifacts are eligible.",
            "Validation trackers, logs, templates, and README files are protected.",
        ],
    }


def apply_prune_plan(plan: dict[str, Any], *, private_dir: Path) -> dict[str, Any]:
    private_dir = private_dir.resolve()
    if not _is_ignored(private_dir):
        raise ValidationPruneError(f"{private_dir} is not ignored by git")
    removed: list[str] = []
    for candidate in plan.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        path = Path(str(candidate.get("path") or "")).resolve()
        issue = _candidate_issue(path, private_dir)
        if issue:
            raise ValidationPruneError(f"{path}: {issue}")
        if path.is_symlink():
            raise ValidationPruneError(f"{path}: symlink pruning is not allowed")
        if path.is_dir():
            if not _is_outdated_send_copy_batch_dir(path, plan["review_date"]):
                raise ValidationPruneError(f"{path}: directory is not an outdated send-copy batch")
            shutil.rmtree(path)
            removed.append(str(path))
        elif path.is_file():
            if path.name in PROTECTED_FILENAMES:
                raise ValidationPruneError(f"{path}: protected private state file")
            if not _is_generated_private_artifact(path, private_dir):
                raise ValidationPruneError(f"{path}: not a generated private artifact")
            path.unlink()
            removed.append(str(path))
    result = dict(plan)
    result["dry_run"] = False
    result["removed_count"] = len(removed)
    result["removed"] = removed
    return result


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# Prophet Private Validation Prune Plan - {plan['review_date']}",
        "",
        f"- Dry run: {str(plan['dry_run']).lower()}",
        f"- Candidate count: {plan['candidate_count']}",
        f"- Blocked count: {plan['blocked_count']}",
        "",
        "## Candidates",
    ]
    if plan["candidates"]:
        for candidate in plan["candidates"]:
            lines.append(
                f"- {candidate['path']} ({candidate['kind']}): "
                + ", ".join(candidate["reasons"])
            )
    else:
        lines.append("- No generated private artifacts are eligible for pruning.")
    if plan["blocked"]:
        lines.extend(["", "## Blocked"])
        for item in plan["blocked"]:
            lines.append(f"- {item['path']}: {item['reason']}")
    if not plan["dry_run"]:
        lines.extend(["", "## Removed"])
        for path in plan.get("removed", []):
            lines.append(f"- {path}")
    lines.extend(["", "## Operator Notes"])
    for note in plan["operator_notes"]:
        lines.append(f"- {note}")
    lines.append("- Rerun the weekly review after confirmed pruning.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan or prune generated ignored private validation artifacts."
    )
    parser.add_argument("--weekly-review", default=str(DEFAULT_WEEKLY_REVIEW))
    parser.add_argument("--private-dir", default=str(DEFAULT_PRIVATE_DIR))
    parser.add_argument("--review-date", help="Required review date in YYYY-MM-DD form.")
    parser.add_argument("--confirm-prune", action="store_true")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        review = _load_json_object(Path(args.weekly_review))
        plan = build_prune_plan(
            review,
            private_dir=Path(args.private_dir),
            review_date=args.review_date,
        )
        if args.confirm_prune:
            plan = apply_prune_plan(plan, private_dir=Path(args.private_dir))
    except (OSError, json.JSONDecodeError, ValidationPruneError) as exc:
        print(f"validation private prune failed: {exc}", file=sys.stderr)
        return 1
    rendered = (
        render_markdown(plan)
        if args.format == "markdown"
        else json.dumps(plan, indent=2, sort_keys=True) + "\n"
    )
    print(rendered, end="")
    return 0


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationPruneError(f"{path} must decode to object")
    return value


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationPruneError(f"{field} must be YYYY-MM-DD") from exc


def _candidate_path(raw_path: str, private_dir: Path) -> Path:
    if not raw_path:
        raise ValidationPruneError("candidate path is empty")
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (Path.cwd() / path).resolve() if not private_dir.is_absolute() else path.resolve()


def _candidate_issue(path: Path, private_dir: Path) -> str | None:
    if not _is_relative_to(path, private_dir):
        return "outside_private_dir"
    parts = path.relative_to(private_dir).parts
    if any(part in {"", ".", ".."} for part in parts):
        return "unsafe_relative_path"
    if path.name.startswith("."):
        return "hidden_file_not_pruned"
    return None


def _is_generated_private_artifact(path: Path, private_dir: Path) -> bool:
    if path.parent.name.startswith("send-copy-"):
        return path.suffix in {".txt", ".md", ".json"}
    if path.parent != private_dir:
        return False
    if path.name.startswith("today-") and path.suffix in {".json", ".md", ".txt"}:
        return True
    if path.name == "NEXT_ACTION.md":
        return True
    return False


def _send_copy_batch_date(path: Path) -> date | None:
    if path.parent.name.startswith("send-copy-"):
        return _batch_dir_date(path.parent.name)
    return None


def _is_outdated_send_copy_batch_dir(path: Path, review_date: str) -> bool:
    batch_date = _batch_dir_date(path.name)
    return batch_date is not None and batch_date.isoformat() != review_date


def _batch_dir_date(name: str) -> date | None:
    prefix = "send-copy-"
    if not name.startswith(prefix):
        return None
    try:
        return date.fromisoformat(name[len(prefix) :])
    except ValueError:
        return None


def _is_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
