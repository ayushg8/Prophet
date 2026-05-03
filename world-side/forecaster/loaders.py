"""Data loaders for Prophet World Side.

This module is intentionally stdlib-only. It reads local planning/corpus
artifacts, normalizes them into plain dictionaries, and performs lightweight
source extraction. It does not scrape and does not use the network.
"""

from __future__ import annotations

import csv
from io import StringIO
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
WORLD_SIDE_DIR = ROOT / "world-side"
DATA_DIR = WORLD_SIDE_DIR / "data"
DEFAULT_KVE_PATH = ROOT / "kve.json"
DEFAULT_CALENDAR_PATH = DATA_DIR / "calendar_events.md"

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BARE_URL_RE = re.compile(r"https?://[^\s<>)\]]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def read_text(path: str | Path) -> str:
    """Read a UTF-8 text file from disk."""

    return Path(path).read_text(encoding="utf-8")


def load_json(path: str | Path) -> Any:
    """Load a JSON file from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_key(value: str) -> str:
    """Normalize a table/header key into snake_case."""

    value = re.sub(r"\*\*|`", "", value or "").strip().lower()
    value = value.replace("/", " ")
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def extract_urls(text: str) -> list[str]:
    """Extract unique URLs from text in first-seen order."""

    seen: set[str] = set()
    urls: list[str] = []
    for match in BARE_URL_RE.finditer(text or ""):
        url = match.group(0).rstrip(".,;")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def extract_markdown_links(text: str) -> list[dict[str, str]]:
    """Extract Markdown links from a text fragment."""

    return [
        {"label": label.strip(), "url": url.strip().rstrip(".,;")}
        for label, url in MARKDOWN_LINK_RE.findall(text or "")
    ]


def extract_source_refs(
    text: str,
    source_path: str | Path | None = None,
    default_label: str = "Source",
    supports: str = "",
) -> list[dict[str, object]]:
    """Extract source refs from Markdown or bare URLs.

    The returned dictionaries match the Direction B contract closely enough for
    downstream workers to reuse them directly in ``source_refs``.
    """

    source_path_str = str(source_path) if source_path is not None else None
    refs: list[dict[str, object]] = []
    seen_urls: set[str] = set()

    for line_number, line in enumerate((text or "").splitlines(), start=1):
        markdown_urls = set()
        for link in extract_markdown_links(line):
            url = link["url"]
            label = link["label"] or default_label
            markdown_urls.add(url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                {
                    "id": _source_id(url, label, source_path_str),
                    "label": label,
                    "url": url,
                    "source_path": source_path_str,
                    "line": line_number,
                    **({"supports": supports} if supports else {}),
                }
            )

        for url in extract_urls(line):
            if url in markdown_urls or url in seen_urls:
                continue
            seen_urls.add(url)
            refs.append(
                {
                    "id": _source_id(url, default_label, source_path_str),
                    "label": default_label,
                    "url": url,
                    "source_path": source_path_str,
                    "line": line_number,
                    **({"supports": supports} if supports else {}),
                }
            )

    return refs


def _source_id(url: str, label: str = "", source_path: str | None = None) -> str:
    import hashlib

    seed = "\n".join([source_path or "", label.strip(), url.strip()])
    return "src_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def load_cisa_kev(path: str | Path = DEFAULT_KVE_PATH) -> dict[str, object]:
    """Load and normalize the CISA Known Exploited Vulnerabilities catalog.

    The repo file is named ``kve.json`` in some branches, but its contents are
    the CISA KEV catalog. This function accepts either naming convention.
    """

    path_obj = Path(path)
    payload = load_json(path_obj)
    vulnerabilities = payload.get("vulnerabilities", [])
    if not isinstance(vulnerabilities, list):
        raise ValueError(f"{path_obj} does not contain a vulnerabilities list")

    normalized = [_normalize_kev_vulnerability(item, path_obj) for item in vulnerabilities]
    by_cve = {item["cve_id"]: item for item in normalized if item.get("cve_id")}

    return {
        "title": payload.get("title", ""),
        "catalog_version": payload.get("catalogVersion", ""),
        "date_released": payload.get("dateReleased", ""),
        "declared_count": payload.get("count"),
        "count": len(normalized),
        "vulnerabilities": normalized,
        "by_cve": by_cve,
        "source_refs": [
            {
                "id": "src_cisa_kev_catalog",
                "label": "CISA Known Exploited Vulnerabilities Catalog",
                "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                "source_path": str(path_obj),
                "supports": "local KEV catalog metadata and vulnerability entries",
            }
        ],
    }


def load_kev_catalog(path: str | Path = DEFAULT_KVE_PATH) -> dict[str, object]:
    """Alias for ``load_cisa_kev``."""

    return load_cisa_kev(path)


def load_kve_catalog(path: str | Path = DEFAULT_KVE_PATH) -> dict[str, object]:
    """Alias for branches/docs that refer to the KEV file as KVE."""

    return load_cisa_kev(path)


def find_kev_by_cve(catalog: dict[str, object], cve_id: str) -> dict[str, object] | None:
    """Return a normalized KEV entry by CVE ID."""

    by_cve = catalog.get("by_cve", {})
    if isinstance(by_cve, dict):
        return by_cve.get(cve_id.upper())
    return None


def search_kev(
    catalog: dict[str, object],
    query: str,
    fields: Iterable[str] = ("cve_id", "vendor_project", "product", "vulnerability_name", "short_description"),
) -> list[dict[str, object]]:
    """Case-insensitive substring search across normalized KEV entries."""

    needle = query.casefold()
    results: list[dict[str, object]] = []
    for item in catalog.get("vulnerabilities", []):
        if not isinstance(item, dict):
            continue
        if any(needle in str(item.get(field, "")).casefold() for field in fields):
            results.append(item)
    return results


def _normalize_kev_vulnerability(item: dict[str, Any], source_path: Path) -> dict[str, object]:
    cve_id = str(item.get("cveID", "")).strip().upper()
    notes = str(item.get("notes", "") or "")
    note_refs = [
        {
            "id": _source_id(url, cve_id or "KEV note", str(source_path)),
            "label": cve_id or "KEV note",
            "url": url,
            "source_path": str(source_path),
            "supports": "KEV catalog note reference",
        }
        for url in extract_urls(notes)
    ]
    return {
        "cve_id": cve_id,
        "vendor_project": str(item.get("vendorProject", "")).strip(),
        "product": str(item.get("product", "")).strip(),
        "vulnerability_name": str(item.get("vulnerabilityName", "")).strip(),
        "date_added": str(item.get("dateAdded", "")).strip(),
        "short_description": str(item.get("shortDescription", "")).strip(),
        "required_action": str(item.get("requiredAction", "")).strip(),
        "due_date": str(item.get("dueDate", "")).strip(),
        "known_ransomware_campaign_use": str(item.get("knownRansomwareCampaignUse", "")).strip(),
        "cwes": [str(cwe).strip() for cwe in item.get("cwes", []) if str(cwe).strip()],
        "notes": notes,
        "source_refs": note_refs,
        "raw": item,
    }


def parse_markdown_tables(markdown: str) -> list[dict[str, object]]:
    """Parse GitHub-flavored Markdown pipe tables into dictionaries.

    Returns all tables found in the document. Each table contains its nearest
    preceding heading, the start line, normalized headers, original headers, and
    row dictionaries. Separator/header-only rows are skipped.
    """

    lines = markdown.splitlines()
    tables: list[dict[str, object]] = []
    current_heading = ""
    current_heading_level = 0
    index = 0

    while index < len(lines):
        heading_match = HEADING_RE.match(lines[index])
        if heading_match:
            current_heading_level = len(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            index += 1
            continue

        if _is_table_header_at(lines, index):
            original_headers = _split_markdown_row(lines[index])
            headers = [_dedupe_key(normalize_key(header), position) for position, header in enumerate(original_headers)]
            table = {
                "heading": current_heading,
                "heading_level": current_heading_level,
                "start_line": index + 1,
                "headers": headers,
                "original_headers": original_headers,
                "rows": [],
            }
            index += 2
            while index < len(lines) and _looks_like_table_row(lines[index]):
                if not _is_separator_row(lines[index]):
                    values = _split_markdown_row(lines[index])
                    row = _row_from_values(headers, values)
                    row["_line"] = index + 1
                    row["_raw"] = lines[index]
                    row["_heading"] = current_heading
                    table["rows"].append(row)
                index += 1
            tables.append(table)
            continue

        index += 1

    return tables


def load_markdown_tables(path: str | Path) -> list[dict[str, object]]:
    """Load a Markdown file and parse all pipe tables."""

    return parse_markdown_tables(read_text(path))


def load_calendar_events(path: str | Path = DEFAULT_CALENDAR_PATH) -> dict[str, object]:
    """Load ``calendar_events.md`` and normalize its Markdown-table events."""

    path_obj = Path(path)
    markdown = read_text(path_obj)
    tables = parse_markdown_tables(markdown)
    events: list[dict[str, object]] = []

    for table in tables:
        for row in table["rows"]:
            if _is_calendar_month_marker(row):
                continue
            normalized = dict(row)
            normalized["source_refs"] = extract_source_refs(
                _calendar_row_source_text(row),
                source_path=path_obj,
                default_label="Calendar event source",
                supports=_calendar_row_support_label(row),
            )
            normalized["table_heading"] = table["heading"]
            events.append(normalized)

    return {
        "path": str(path_obj),
        "events": events,
        "tables": tables,
        "source_refs": extract_source_refs(markdown, source_path=path_obj, default_label="Calendar source"),
    }


def load_markdown_document(path: str | Path) -> dict[str, object]:
    """Load a Markdown document with tables and extracted source refs."""

    path_obj = Path(path)
    markdown = read_text(path_obj)
    return {
        "path": str(path_obj),
        "text": markdown,
        "tables": parse_markdown_tables(markdown),
        "source_refs": extract_source_refs(markdown, source_path=path_obj),
    }


def load_world_data(
    data_dir: str | Path = DATA_DIR,
    kve_path: str | Path = DEFAULT_KVE_PATH,
) -> dict[str, object]:
    """Load the local World Side corpus bundle and KEV catalog."""

    data_path = Path(data_dir)
    return {
        "kev": load_cisa_kev(kve_path),
        "calendar": load_calendar_events(data_path / "calendar_events.md"),
        "historical_pairings": load_markdown_document(data_path / "historical_pairings.md"),
        "indictments_state": load_markdown_document(data_path / "indictments_state.md"),
        "sanctions_state": load_markdown_document(data_path / "sanctions_state.md"),
    }


def _is_calendar_month_marker(row: dict[str, object]) -> bool:
    date_value = str(row.get("date", "")).strip()
    if not date_value.startswith("**") or not date_value.endswith("**"):
        return False
    return all(not str(value).strip() for key, value in row.items() if key not in {"date", "_line", "_raw", "_heading"})


def _calendar_row_source_text(row: dict[str, object]) -> str:
    """Return the cell text most likely to hold citations for a calendar row."""

    for key in ("source", "historic_cyber_example", "_raw"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def _calendar_row_support_label(row: dict[str, object]) -> str:
    """Return a short label describing what a row-level source supports."""

    for key in ("event", "anniversary", "date"):
        value = str(row.get(key, "")).strip()
        if value:
            return re.sub(r"\*\*", "", value)
    return "calendar row"


def _is_table_header_at(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return _looks_like_table_row(lines[index]) and _is_separator_row(lines[index + 1])


def _looks_like_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_separator_row(line: str) -> bool:
    cells = _split_markdown_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    reader = csv.reader(StringIO(stripped), delimiter="|", escapechar="\\")
    try:
        row = next(reader)
    except StopIteration:
        return []
    return [cell.strip() for cell in row]


def _row_from_values(headers: list[str], values: list[str]) -> dict[str, object]:
    row = {}
    for index, header in enumerate(headers):
        row[header] = values[index] if index < len(values) else ""
    if len(values) > len(headers):
        row["_extra_cells"] = values[len(headers) :]
    return row


def _dedupe_key(key: str, position: int) -> str:
    if key:
        return key
    return f"column_{position + 1}"
