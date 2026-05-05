#!/usr/bin/env python3
"""Explain Prophet pilot fixture hash changes without printing artifact contents."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


DEFAULT_BASELINE_MANIFEST = Path("scripts/pilot-demo-smoke.sha256")
LINE_RE = re.compile(r"^([0-9a-f]{64})\s+(.+?)\s*$")
SCHEMA_VERSION = "prophet_pilot_fixture_diff.v0.1"


@dataclass(frozen=True)
class FixtureDiff:
    unchanged: list[str]
    changed: list[dict[str, str]]
    missing: list[dict[str, str]]
    added: list[dict[str, str]]

    @property
    def has_differences(self) -> bool:
        return bool(self.changed or self.missing or self.added)

    def summary(self) -> dict[str, int]:
        return {
            "unchanged": len(self.unchanged),
            "changed": len(self.changed),
            "missing": len(self.missing),
            "added": len(self.added),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Prophet pilot demo fixture hashes and explain changes "
            "without printing artifact contents."
        )
    )
    parser.add_argument(
        "--baseline",
        default=DEFAULT_BASELINE_MANIFEST,
        type=Path,
        help="Baseline hash manifest in '<sha256>  <repo-relative-path>' format.",
    )
    parser.add_argument(
        "--candidate-manifest",
        type=Path,
        help="Optional second hash manifest to compare against the baseline.",
    )
    parser.add_argument(
        "--candidate-root",
        type=Path,
        help=(
            "Optional root directory containing candidate artifacts. Defaults to "
            "--root when --candidate-manifest is omitted."
        ),
    )
    parser.add_argument(
        "--root",
        default=Path.cwd(),
        type=Path,
        help="Repository root used to resolve the baseline manifest and paths.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Return exit code 1 when differences are found.",
    )
    args = parser.parse_args()

    if args.candidate_manifest and args.candidate_root:
        parser.error("--candidate-manifest and --candidate-root are mutually exclusive")

    try:
        root = args.root.resolve()
        baseline_path = _resolve_under_root(root, args.baseline)
        baseline = read_hash_manifest(baseline_path)

        if args.candidate_manifest:
            candidate_path = _resolve_under_root(root, args.candidate_manifest)
            candidate = read_hash_manifest(candidate_path)
            candidate_label = str(_display_path(root, candidate_path))
        else:
            candidate_root = args.candidate_root.resolve() if args.candidate_root else root
            candidate = hash_candidate_files(candidate_root, baseline.keys())
            candidate_label = f"current files under {_display_path(root, candidate_root)}"

        diff = compare_hashes(baseline, candidate)
        payload = diff_payload(
            diff,
            baseline_label=str(_display_path(root, baseline_path)),
            candidate_label=candidate_label,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload))

    if args.fail_on_diff and diff.has_differences:
        return 1
    return 0


def read_hash_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    if not path.exists():
        raise ValueError(f"manifest not found: {path}")

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"{path}:{line_no}: invalid hash manifest line")
        sha256, rel_path = match.groups()
        _validate_repo_relative_path(rel_path, f"{path}:{line_no}")
        if rel_path in entries:
            raise ValueError(f"{path}:{line_no}: duplicate manifest path: {rel_path}")
        entries[rel_path] = sha256

    if not entries:
        raise ValueError(f"{path}: no hash entries")
    return entries


def hash_candidate_files(root: Path, rel_paths: Any) -> dict[str, str]:
    resolved_root = root.resolve()
    entries: dict[str, str] = {}
    for rel_path in sorted(rel_paths):
        _validate_repo_relative_path(rel_path, "candidate path")
        path = resolved_root / rel_path
        if not _is_under_root(resolved_root, path):
            raise ValueError(f"candidate path escapes root: {rel_path}")
        if not path.is_file():
            continue
        entries[rel_path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return entries


def compare_hashes(baseline: dict[str, str], candidate: dict[str, str]) -> FixtureDiff:
    unchanged: list[str] = []
    changed: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    added: list[dict[str, str]] = []

    for rel_path in sorted(baseline):
        baseline_sha256 = baseline[rel_path]
        candidate_sha256 = candidate.get(rel_path)
        if candidate_sha256 is None:
            missing.append({"path": rel_path, "baseline_sha256": baseline_sha256})
        elif candidate_sha256 == baseline_sha256:
            unchanged.append(rel_path)
        else:
            changed.append(
                {
                    "path": rel_path,
                    "baseline_sha256": baseline_sha256,
                    "candidate_sha256": candidate_sha256,
                }
            )

    for rel_path in sorted(set(candidate) - set(baseline)):
        added.append({"path": rel_path, "candidate_sha256": candidate[rel_path]})

    return FixtureDiff(
        unchanged=unchanged,
        changed=changed,
        missing=missing,
        added=added,
    )


def diff_payload(
    diff: FixtureDiff,
    *,
    baseline_label: str,
    candidate_label: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline": baseline_label,
        "candidate": candidate_label,
        "result": "differences_found" if diff.has_differences else "no_differences",
        "summary": diff.summary(),
        "unchanged_paths": diff.unchanged,
        "changed": diff.changed,
        "missing": diff.missing,
        "added": diff.added,
        "safety": {
            "artifact_contents_printed": False,
            "comparison_material": "repo-relative paths and SHA-256 hashes only",
        },
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        "Pilot demo fixture diff",
        f"Baseline: {payload['baseline']}",
        f"Candidate: {payload['candidate']}",
        f"Result: {payload['result'].replace('_', ' ')}",
        "",
        "Summary:",
    ]
    summary = payload["summary"]
    for key in ("unchanged", "changed", "missing", "added"):
        lines.append(f"- {key}: {summary[key]}")

    _append_section(lines, "Changed", payload["changed"], ("baseline_sha256", "candidate_sha256"))
    _append_section(lines, "Missing", payload["missing"], ("baseline_sha256",))
    _append_section(lines, "Added", payload["added"], ("candidate_sha256",))

    lines.extend(
        [
            "",
            "Safety: output includes only repo-relative paths and SHA-256 hashes.",
        ]
    )
    return "\n".join(lines)


def _append_section(
    lines: list[str],
    title: str,
    rows: list[dict[str, str]],
    hash_keys: tuple[str, ...],
) -> None:
    if not rows:
        return
    lines.extend(["", f"{title}:"])
    for row in rows:
        lines.append(f"- {row['path']}")
        for key in hash_keys:
            label = key.replace("_sha256", "")
            lines.append(f"  {label}: {row[key]}")


def _resolve_under_root(root: Path, path: Path) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    if not _is_under_root(root, resolved):
        raise ValueError(f"path escapes repository root: {path}")
    return resolved


def _display_path(root: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return path


def _validate_repo_relative_path(rel_path: str, context: str) -> None:
    path = Path(rel_path)
    if rel_path in {"", "."} or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{context}: path must be repo-relative and stay in repo")


def _is_under_root(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
