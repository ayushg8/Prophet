#!/usr/bin/env python3
"""Verify generated console screenshot artifacts before sharing."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("evidence/outputs/runtime/console-screenshots/manifest.json")
EXPECTED_SCHEMA_VERSION = "prophet_console_screenshot_manifest.v0.1"
REQUIRED_BOUNDARY_FLAGS = {
    "fixture_backed",
    "browser_chrome_excluded",
    "no_customer_systems",
    "no_live_targets",
    "no_payloads",
    "no_credentials",
    "review_required_before_sharing",
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def verify_console_screenshots(manifest_path: Path, *, root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = _resolve_under_root(manifest_path, root)
    manifest = _load_json(manifest_path)
    issues: list[str] = []

    if manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        issues.append("manifest.schema_version is unsupported")
    output_dir = manifest.get("output_dir")
    if output_dir != "evidence/outputs/runtime/console-screenshots":
        issues.append("manifest.output_dir must be evidence/outputs/runtime/console-screenshots")

    boundary = manifest.get("data_boundary")
    if not isinstance(boundary, dict):
        issues.append("manifest.data_boundary must be an object")
    else:
        for flag in sorted(REQUIRED_BOUNDARY_FLAGS):
            if boundary.get(flag) is not True:
                issues.append(f"manifest.data_boundary.{flag} must be true")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        issues.append("manifest.artifacts must be a non-empty list")
        artifacts = []

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    checked_artifacts = 0
    for index, artifact in enumerate(artifacts):
        context = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            issues.append(f"{context} must be an object")
            continue
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            issues.append(f"{context}.id must be a non-empty string")
        elif artifact_id in seen_ids:
            issues.append(f"{context}.id is duplicated")
        else:
            seen_ids.add(artifact_id)

        label = artifact.get("path")
        if not isinstance(label, str) or not label:
            issues.append(f"{context}.path must be a non-empty string")
            continue
        if label in seen_paths:
            issues.append(f"{context}.path is duplicated")
            continue
        seen_paths.add(label)
        if not label.startswith("evidence/outputs/runtime/console-screenshots/"):
            issues.append(f"{context}.path must stay under ignored console screenshot runtime output")
            continue
        if not label.endswith(".png"):
            issues.append(f"{context}.path must point to a PNG file")
            continue
        try:
            artifact_path = _resolve_under_root(Path(label), root)
        except ValueError as exc:
            issues.append(f"{context}.path {exc}")
            continue
        if not artifact_path.exists():
            issues.append(f"{context}.path is missing")
            continue
        if not _is_git_ignored(artifact_path, root):
            issues.append(f"{context}.path is not ignored by git")

        expected_sha = artifact.get("sha256")
        actual_sha = _sha256(artifact_path)
        if expected_sha != actual_sha:
            issues.append(f"{context}.sha256 does not match file contents")

        viewport = artifact.get("viewport")
        if not isinstance(viewport, dict):
            issues.append(f"{context}.viewport must be an object")
            continue
        expected_width = viewport.get("width")
        expected_height = viewport.get("height")
        try:
            actual_width, actual_height = _png_dimensions(artifact_path)
        except ValueError as exc:
            issues.append(f"{context}.path {exc}")
            continue
        if expected_width != actual_width or expected_height != actual_height:
            issues.append(
                f"{context}.viewport does not match PNG dimensions "
                f"({actual_width}x{actual_height})"
            )
        checked_artifacts += 1

    if not _is_git_ignored(manifest_path, root):
        issues.append("manifest path is not ignored by git")

    return {
        "ok": not issues,
        "artifact_count": len(artifacts),
        "checked_artifacts": checked_artifacts,
        "issues": issues,
        "manifest": str(manifest_path.relative_to(root)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify console screenshot manifest hashes, dimensions, ignored paths, and sharing boundary."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--root", default=".")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    try:
        summary = verify_console_screenshots(Path(args.manifest), root=Path(args.root))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"console screenshot check failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["ok"]:
        print(
            "Console screenshot check passed "
            f"({summary['checked_artifacts']} artifact(s) checked)."
        )
    else:
        print("Console screenshot check failed:", file=sys.stderr)
        for issue in summary["issues"]:
            print(f"- {issue}", file=sys.stderr)
    return 0 if summary["ok"] else 1


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be a JSON object")
    return value


def _resolve_under_root(path: Path, root: Path) -> Path:
    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("escapes repository root") from exc
    return resolved


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or not data.startswith(PNG_SIGNATURE):
        raise ValueError("is not a PNG file")
    if data[12:16] != b"IHDR":
        raise ValueError("does not have an IHDR chunk")
    return struct.unpack(">II", data[16:24])


def _is_git_ignored(path: Path, root: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", str(path.relative_to(root))],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return completed.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
