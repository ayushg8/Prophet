"""Source-reference helpers for Prophet World Side loaders.

The forecaster has a hard rule: every surfaced claim needs a source. These
helpers keep source extraction deterministic and stdlib-only so parser,
matcher, and scoring workers can share stable reference IDs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re
from pathlib import Path
from typing import Iterable


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BARE_URL_RE = re.compile(r"https?://[^\s<>)\]]+")


@dataclass(frozen=True)
class SourceRef:
    """A citation-like reference extracted from a local artifact."""

    id: str
    label: str
    url: str
    source_path: str | None = None
    line: int | None = None
    supports: str = ""

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value not in (None, "")}


def stable_source_id(url: str, label: str = "", source_path: str | None = None) -> str:
    """Return a short deterministic ID for a source URL/label/path tuple."""

    digest_input = "\n".join([source_path or "", label.strip(), url.strip()])
    return "src_" + hashlib.sha1(digest_input.encode("utf-8")).hexdigest()[:12]


def extract_urls(text: str) -> list[str]:
    """Extract unique bare URLs from text in first-seen order."""

    seen: set[str] = set()
    urls: list[str] = []
    for match in BARE_URL_RE.finditer(text or ""):
        url = match.group(0).rstrip(".,;")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def extract_markdown_links(text: str) -> list[dict[str, str]]:
    """Extract Markdown links as ``{"label": ..., "url": ...}`` dictionaries."""

    links: list[dict[str, str]] = []
    for label, url in MARKDOWN_LINK_RE.findall(text or ""):
        links.append({"label": label.strip(), "url": url.strip().rstrip(".,;")})
    return links


def extract_source_refs(
    text: str,
    source_path: str | Path | None = None,
    default_label: str = "Source",
    supports: str = "",
) -> list[dict[str, object]]:
    """Extract Markdown and bare-URL references from text.

    Markdown links preserve their label. Bare URLs that are not already part of
    a Markdown link are included with ``default_label``.
    """

    source_path_str = str(source_path) if source_path is not None else None
    refs: list[SourceRef] = []
    seen_urls: set[str] = set()

    for line_number, line in enumerate((text or "").splitlines(), start=1):
        markdown_urls: set[str] = set()
        for link in extract_markdown_links(line):
            label = link["label"] or default_label
            url = link["url"]
            markdown_urls.add(url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                SourceRef(
                    id=stable_source_id(url, label, source_path_str),
                    label=label,
                    url=url,
                    source_path=source_path_str,
                    line=line_number,
                    supports=supports,
                )
            )

        for url in extract_urls(line):
            if url in markdown_urls or url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                SourceRef(
                    id=stable_source_id(url, default_label, source_path_str),
                    label=default_label,
                    url=url,
                    source_path=source_path_str,
                    line=line_number,
                    supports=supports,
                )
            )

    return [ref.to_dict() for ref in refs]


def refs_by_id(refs: Iterable[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Index source refs by ID, preserving the first copy of duplicates."""

    indexed: dict[str, dict[str, object]] = {}
    for ref in refs:
        ref_id = str(ref.get("id", ""))
        if ref_id and ref_id not in indexed:
            indexed[ref_id] = dict(ref)
    return indexed
