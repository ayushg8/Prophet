#!/usr/bin/env python3
"""Verify the deterministic pilot demo artifact hash manifest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys


LINE_RE = re.compile(r"^([0-9a-f]{64})\s+(.+?)\s*$")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify SHA-256 hashes for the Prophet pilot demo smoke artifacts."
    )
    parser.add_argument(
        "--manifest",
        default="scripts/pilot-demo-smoke.sha256",
        type=Path,
        help="Expected hash manifest in '<sha256>  <repo-relative-path>' format.",
    )
    parser.add_argument(
        "--root",
        default=Path.cwd(),
        type=Path,
        help="Repository root used to resolve manifest paths.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    entries = _read_manifest(manifest)
    failures: list[str] = []
    for expected, rel_path in entries:
        path = root / rel_path
        if not _is_safe_repo_path(root, path):
            failures.append(f"{rel_path}: path escapes repository root")
            continue
        if not path.exists():
            failures.append(f"{rel_path}: missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{actual}  {rel_path}")
        if actual != expected:
            failures.append(f"{rel_path}: expected {expected}, got {actual}")

    if failures:
        for failure in failures:
            print(f"pilot hash mismatch: {failure}", file=sys.stderr)
        return 1
    print(f"verified {len(entries)} pilot demo hash(es) against {manifest.relative_to(root)}")
    return 0


def _read_manifest(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = LINE_RE.fullmatch(line)
        if not match:
            raise SystemExit(f"{path}:{line_no}: invalid hash manifest line")
        rel_path = match.group(2).strip()
        if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
            raise SystemExit(f"{path}:{line_no}: path must be repo-relative and stay in repo")
        entries.append((match.group(1), rel_path))
    if not entries:
        raise SystemExit(f"{path}: no hash entries")
    return entries


def _is_safe_repo_path(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
