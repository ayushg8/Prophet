#!/usr/bin/env python3
"""Check local Markdown links without reaching out to the network."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse


EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "playwright-report",
    "test-results",
    "dist",
}
EXCLUDED_PREFIXES = {
    Path("validation") / "private",
}
FENCE_RE = re.compile(r"(^|\n)(```|~~~).*?(?=\n\2|\Z)(\n\2)?", re.DOTALL)
INLINE_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s+(\S+)", re.MULTILINE)


def check_doc_links(root: Path) -> list[str]:
    errors: list[str] = []
    markdown_files = _markdown_files(root)
    for markdown in markdown_files:
        rel_markdown = markdown.relative_to(root)
        text = markdown.read_text(encoding="utf-8")
        stripped = FENCE_RE.sub("", text)
        targets = [match.group(1) for match in INLINE_LINK_RE.finditer(stripped)]
        targets.extend(match.group(1) for match in REFERENCE_LINK_RE.finditer(stripped))
        for raw_target in targets:
            target = _normalize_target(raw_target)
            if not target or _is_external_or_special(target):
                continue
            link_path = _resolve_local_path(root, markdown, target)
            if link_path is None:
                continue
            if not link_path.exists():
                errors.append(f"{rel_markdown}: missing local link target: {target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check local Markdown file/image links. External URLs, mailto links, "
            "and anchors are ignored because this is a no-network release check."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    errors = check_doc_links(root)
    if errors:
        print("Prophet doc link check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    file_count = len(_markdown_files(root))
    print(f"Prophet doc link check passed ({file_count} Markdown file(s) scanned).")
    return 0


def _markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not _excluded(path.relative_to(root))
    )


def _excluded(relative_path: Path) -> bool:
    path_parts = relative_path.parts
    parts = set(path_parts)
    if parts & EXCLUDED_DIRS:
        return True
    if _contains_runtime_output(path_parts):
        return True
    return any(
        relative_path == prefix or prefix in relative_path.parents
        for prefix in EXCLUDED_PREFIXES
    )


def _contains_runtime_output(parts: tuple[str, ...]) -> bool:
    return any(
        part == "outputs" and index + 1 < len(parts) and parts[index + 1] == "runtime"
        for index, part in enumerate(parts)
    )


def _normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")].strip()
    return target.split()[0].strip()


def _is_external_or_special(target: str) -> bool:
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return True
    return target.startswith("#")


def _resolve_local_path(root: Path, markdown: Path, target: str) -> Path | None:
    without_fragment, _fragment = urldefrag(target)
    if not without_fragment:
        return None
    without_query = without_fragment.split("?", 1)[0]
    decoded = unquote(without_query)
    if decoded.startswith("/"):
        return (root / decoded.lstrip("/")).resolve()
    return (markdown.parent / decoded).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
