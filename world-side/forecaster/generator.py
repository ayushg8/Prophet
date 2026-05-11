"""Assemble World Side strike forecasts.

This module is intentionally stdlib-only. Other workers may add richer
loaders, matchers, or scoring helpers later; this file keeps a deterministic
fallback path so the CLI can produce a schema-compatible forecast today.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

try:
    from .chatter import chatter_records_to_events, load_sanitized_chatter
    from .models import ExploitCandidate, validate_world_forecast
except ImportError:  # pragma: no cover - direct script fallback
    try:
        from chatter import chatter_records_to_events, load_sanitized_chatter  # type: ignore
        from models import ExploitCandidate, validate_world_forecast  # type: ignore
    except ImportError:  # pragma: no cover - helpers may not exist in forked lanes.
        ExploitCandidate = None  # type: ignore
        chatter_records_to_events = None  # type: ignore
        load_sanitized_chatter = None  # type: ignore

        def validate_world_forecast(_forecast: dict[str, Any]) -> None:
            return None

try:
    from assets.inventory import (  # type: ignore
        summarize_asset_seedset,
        validate_asset_seedset,
    )
except ImportError:  # pragma: no cover - assets package may be absent in minimal lanes.
    summarize_asset_seedset = None  # type: ignore
    validate_asset_seedset = None  # type: ignore


SCHEMA_VERSION = "world_forecast.v0.1"
DEFAULT_EXCLUDED_USES = [
    "No exploit payloads",
    "No target-control instructions",
    "No named live targets",
]

_ALLOWED_OBJECTIVES = {
    "control",
    "shutdown",
    "disruption",
    "data_theft",
    "persistence",
    "unknown",
}
_CONFIDENCE_LABELS = ((0.70, "high"), (0.50, "medium"), (0.0, "low"))


def assemble_forecast(
    candidate: dict[str, Any],
    *,
    data_dir: str | Path | None = None,
    generated_at: str | None = None,
    chatter_path: str | Path | None = None,
    chatter_paths: Iterable[str | Path] | None = None,
    chatter_records: Iterable[Any] | None = None,
    osint_snapshot_paths: Iterable[str | Path] | None = None,
    osint_manifest_paths: Iterable[str | Path] | None = None,
    asset_seedset_paths: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Build a Direction B forecast from a Direction A candidate.

    Args:
        candidate: Parsed Cyber Side candidate JSON.
        data_dir: Directory containing world-side/data markdown files.
        generated_at: Optional ISO 8601 timestamp for deterministic tests.
        chatter_path: Optional sanitized JSONL chatter file.
        chatter_paths: Optional iterable of sanitized JSONL chatter files.
        chatter_records: Optional already-parsed sanitized chatter records.
        osint_snapshot_paths: Optional sanitized OSINT snapshot JSONL files.
        osint_manifest_paths: Optional OSINT snapshot manifest JSON files.
        asset_seedset_paths: Optional asset_osint_seedset.v0.1 JSON files.

    Returns:
        A dict matching the world_forecast.v0.1 shape in INTERFACE.md.
    """

    root_data_dir = Path(data_dir) if data_dir else _default_data_dir()
    generated_at = generated_at or _now_utc()
    as_of = _date_from_iso(generated_at[:10]) or _dt.date.today()

    if ExploitCandidate is not None:
        ExploitCandidate.from_mapping(candidate)

    historical_cases = _parse_historical_cases(
        _read_text(root_data_dir / "historical_pairings.md")
    )
    current_events = _parse_calendar_events(
        _read_text(root_data_dir / "calendar_events.md")
    )
    current_events.extend(
        _parse_context_table_events(
            _read_text(root_data_dir / "indictments_state.md"),
            context_type="indictment",
            motive="LEGAL",
        )
    )
    current_events.extend(
        _parse_context_table_events(
            _read_text(root_data_dir / "sanctions_state.md"),
            context_type="sanctions",
            motive="FIN / LEGAL",
        )
    )
    context_sources = _context_file_sources(root_data_dir)
    sanitized_chatter = _load_chatter_inputs(
        chatter_path=chatter_path,
        chatter_paths=chatter_paths,
        chatter_records=chatter_records,
    )
    sanitized_osint = _load_chatter_inputs(
        chatter_path=None,
        chatter_paths=osint_snapshot_paths,
        chatter_records=None,
    )
    chatter_events = _chatter_events(sanitized_chatter)
    osint_events = _osint_events(sanitized_osint)
    if chatter_events:
        current_events.extend(chatter_events)
        context_sources.append(
            _chatter_context_source(
                chatter_path=chatter_path,
                chatter_paths=chatter_paths,
                event_count=len(chatter_events),
            )
        )
    if osint_events:
        current_events.extend(osint_events)
        context_sources.append(
            _osint_context_source(
                osint_snapshot_paths=osint_snapshot_paths,
                osint_manifest_paths=osint_manifest_paths,
                event_count=len(osint_events),
            )
        )
    osint_manifests = _load_osint_manifests(osint_manifest_paths)
    asset_seedsets = _load_asset_seedsets(asset_seedset_paths)
    if asset_seedsets:
        context_sources.append(
            _asset_seedset_context_source(
                asset_seedset_paths=asset_seedset_paths,
                seedset_count=len(asset_seedsets),
            )
        )

    features = _candidate_features(candidate)
    features = _apply_asset_seed_features(features, asset_seedsets)
    analogy_matches = _rank_historical_cases(historical_cases, features)
    windows = _build_strike_windows(current_events, analogy_matches, features, as_of=as_of)
    vectors = _build_strike_vectors(
        candidate,
        analogy_matches,
        features,
        chatter_events=[*chatter_events, *osint_events],
    )

    source_refs = _SourceRegistry()
    _register_candidate_sources(source_refs, candidate)
    _register_context_sources(source_refs, context_sources)
    _register_window_sources(source_refs, windows)
    _register_vector_sources(source_refs, vectors)
    _register_osint_sources(source_refs, osint_events)
    _register_analogy_sources(source_refs, analogy_matches[:5])

    strategic_frame = _build_strategic_frame(
        candidate,
        features,
        has_chatter=bool(chatter_events),
        asset_seedset_count=len(asset_seedsets),
    )
    forecast_id = _forecast_id(candidate, generated_at)

    forecast = {
        "forecast_id": forecast_id,
        "generated_at": generated_at,
        "input_candidate_id": str(candidate.get("candidate_id") or "unknown"),
        "schema_version": SCHEMA_VERSION,
        "strategic_frame": strategic_frame,
        "strike_windows": [_window_payload(w, source_refs) for w in windows],
        "strike_vectors": [_vector_payload(v, source_refs) for v in vectors],
        "summary": _build_summary(
            candidate,
            windows,
            vectors,
            features,
            chatter_count=len(chatter_events),
            osint_count=len(osint_events),
            asset_seedset_count=len(asset_seedsets),
        ),
        "open_source_signals": _build_open_source_signals(
            records=sanitized_osint,
            events=osint_events,
            snapshot_paths=osint_snapshot_paths,
            manifest_paths=osint_manifest_paths,
            manifests=osint_manifests,
        ),
        "asset_seed_context": _build_asset_seed_context(
            seedsets=asset_seedsets,
            seedset_paths=asset_seedset_paths,
        ),
        "source_refs": source_refs.items(),
    }

    _assert_source_ref_integrity(forecast)
    validate_world_forecast(forecast)
    return forecast


def generate_forecast(
    candidate: dict[str, Any],
    *,
    data_dir: str | Path | None = None,
    generated_at: str | None = None,
    chatter_path: str | Path | None = None,
    chatter_paths: Iterable[str | Path] | None = None,
    chatter_records: Iterable[Any] | None = None,
    osint_snapshot_paths: Iterable[str | Path] | None = None,
    osint_manifest_paths: Iterable[str | Path] | None = None,
    asset_seedset_paths: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias for callers that expect generate_forecast."""

    return assemble_forecast(
        candidate,
        data_dir=data_dir,
        generated_at=generated_at,
        chatter_path=chatter_path,
        chatter_paths=chatter_paths,
        chatter_records=chatter_records,
        osint_snapshot_paths=osint_snapshot_paths,
        osint_manifest_paths=osint_manifest_paths,
        asset_seedset_paths=asset_seedset_paths,
    )


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def _now_utc() -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_chatter_inputs(
    *,
    chatter_path: str | Path | None,
    chatter_paths: Iterable[str | Path] | None,
    chatter_records: Iterable[Any] | None,
) -> list[Any]:
    records: list[Any] = []
    if chatter_records:
        records.extend(chatter_records)

    paths: list[str | Path] = []
    if chatter_path:
        paths.append(chatter_path)
    if chatter_paths:
        paths.extend(chatter_paths)

    if paths and load_sanitized_chatter is None:
        raise ValueError("sanitized chatter loader is unavailable")

    for path in paths:
        records.extend(load_sanitized_chatter(path))
    return records


def _chatter_events(records: list[Any]) -> list[dict[str, Any]]:
    if not records:
        return []
    if chatter_records_to_events is None:
        raise ValueError("sanitized chatter event converter is unavailable")
    return chatter_records_to_events(records)


def _osint_events(records: list[Any]) -> list[dict[str, Any]]:
    events = _chatter_events(records)
    for event in events:
        event["context_type"] = "osint_signal"
    return events


def _candidate_features(candidate: dict[str, Any]) -> dict[str, Any]:
    identity = _as_dict(candidate.get("identity"))
    hypothesis = _as_dict(candidate.get("attack_hypothesis"))
    rationale = _as_dict(candidate.get("rationale"))
    weaponization = _as_dict(candidate.get("weaponization"))

    text = " ".join(
        str(value)
        for value in [
            identity.get("candidate_type"),
            identity.get("candidate_label"),
            identity.get("cve_id"),
            identity.get("cve_class_label"),
            identity.get("target_product"),
            identity.get("target_component"),
            " ".join(identity.get("cwe_ids") or []),
            hypothesis.get("attack_vector"),
            hypothesis.get("intended_effect"),
            hypothesis.get("destructiveness"),
            hypothesis.get("narrative"),
            rationale.get("narrative"),
            weaponization.get("public_status"),
        ]
        if value is not None
    ).lower()

    tags: set[str] = set()
    groups = {
        "edge": ("edge", "vpn", "gateway", "perimeter", "firewall", "router"),
        "appliance": ("appliance", "fortinet", "ivanti", "citrix", "sonicwall"),
        "supply_chain": ("supply chain", "orion", "update", "vendor", "mft"),
        "financial": ("bank", "swift", "crypto", "exchange", "wallet", "defi"),
        "election": ("election", "campaign", "voter", "party", "dnc"),
        "ics": ("ics", "ot", "plc", "scada", "grid", "water", "energy"),
        "wiper": ("wiper", "destructive", "wipe", "hermetic", "notpetya"),
        "ransomware": ("ransomware", "extortion", "cl0p", "lockbit"),
        "phishing": ("phish", "credential", "email", "login"),
        "data_theft": ("data theft", "exfil", "leak", "theft", "steal"),
        "shutdown": ("shutdown", "disruption", "disable", "outage"),
        "persistence": ("persistence", "pre-position", "dwell", "access"),
        "prc": ("prc", "china", "chinese", "taiwan", "mss", "volt"),
        "russia": ("russia", "russian", "gru", "sandworm", "svr"),
        "iran": ("iran", "iranian", "irgc", "mois"),
        "dprk": ("dprk", "north korea", "lazarus", "rgb"),
        "us_gov": ("us government", "federal", "defense", "dib", "agency"),
    }
    for tag, needles in groups.items():
        if any(_contains_term(text, needle) for needle in needles):
            tags.add(tag)

    objective = str(hypothesis.get("intended_effect") or "").strip().lower()
    if objective not in _ALLOWED_OBJECTIVES:
        if "data_theft" in tags:
            objective = "data_theft"
        elif "shutdown" in tags:
            objective = "shutdown"
        elif "persistence" in tags:
            objective = "persistence"
        else:
            objective = "unknown"

    if ("edge" in tags or "appliance" in tags) and not _actor_tag_present(tags):
        tags.add("prc")
        tags.add("persistence")

    if objective in {"shutdown", "disruption"}:
        tags.add("shutdown")

    return {
        "tags": tags,
        "objective": objective,
        "text": text,
        "identity": identity,
        "hypothesis": hypothesis,
    }


def _actor_tag_present(tags: set[str]) -> bool:
    return bool({"prc", "russia", "iran", "dprk"} & tags)


def _parse_historical_cases(markdown: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+)$", markdown, re.MULTILINE))
    for index, match in enumerate(matches):
        start = match.end()
        next_heading = re.search(r"^##\s+", markdown[start:], re.MULTILINE)
        numbered_end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        any_heading_end = start + next_heading.start() if next_heading else len(markdown)
        end = min(numbered_end, any_heading_end)
        section = markdown[start:end].strip()
        number = match.group(1)
        name = match.group(2).strip()
        case = {
            "case_id": f"hist_{number}",
            "case_name": name,
            "section": section,
            "time_to_burn": _extract_labeled_paragraph(section, "Time-to-burn"),
            "pattern_signature": _extract_labeled_paragraph(section, "Pattern signature"),
            "why_anchor": _extract_labeled_paragraph(section, "Why it's a useful anchor"),
            "sources": _extract_markdown_links(_extract_sources_block(section)),
            "anchor": _slugify_heading(number, name),
        }
        case["tags"] = _tags_from_text(f"{name}\n{section}")
        cases.append(case)
    return cases


def _extract_labeled_paragraph(section: str, label: str) -> str:
    pattern = re.compile(
        r"\*\*" + re.escape(label) + r"\.\*\*\s*(.*?)(?=\n\n\*\*|\n\n---|\Z)",
        re.DOTALL,
    )
    match = pattern.search(section)
    if not match:
        return ""
    return _squash(match.group(1))


def _extract_sources_block(section: str) -> str:
    match = re.search(r"\*\*Sources\.\*\*\s*(.*?)(?=\n\n---|\Z)", section, re.DOTALL)
    return match.group(1) if match else ""


def _extract_markdown_links(text: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for label, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        links.append({"label": _squash(label), "url": url.strip()})
    return links


def _tags_from_text(text: str) -> set[str]:
    lower = text.lower()
    tags: set[str] = set()
    keyword_map = {
        "edge": ("edge", "vpn", "gateway", "perimeter", "fortinet", "ivanti"),
        "appliance": ("appliance", "connect secure", "netScaler".lower()),
        "supply_chain": ("supply-chain", "supply chain", "orion", "update server"),
        "financial": ("swift", "bank", "crypto", "financial", "defi"),
        "election": ("election", "campaign", "voter", "political"),
        "ics": ("ics", "plc", "scada", "grid", "triconex", "industrial"),
        "wiper": ("wiper", "notpetya", "hermetic", "destructive"),
        "ransomware": ("ransomware", "extortion", "cl0p", "lockbit"),
        "phishing": ("phishing", "spearphish", "credential"),
        "data_theft": ("data theft", "exfil", "leak", "theft"),
        "shutdown": ("shutdown", "disruption", "outage", "disable"),
        "persistence": ("pre-position", "preposition", "persistence", "dwell"),
        "prc": ("prc", "china", "chinese", "taiwan", "mss", "volt typhoon"),
        "russia": ("russia", "russian", "gru", "sandworm", "svr", "apt28"),
        "iran": ("iran", "iranian", "irgc", "mois"),
        "dprk": ("dprk", "north korea", "lazarus", "apt38"),
        "us_gov": ("us federal", "government", "defense", "dib", "agency"),
        "sanctions": ("sanction", "ofac", "sdn", "designation", "eu package", "cyber regime"),
        "indictment": ("indictment", "charged", "extradited", "sentenced", "trial", "prosecution"),
    }
    for tag, needles in keyword_map.items():
        if any(_contains_term(lower, needle) for needle in needles):
            tags.add(tag)
    return tags


def _contains_term(text: str, term: str) -> bool:
    term = term.lower().strip()
    if not term:
        return False
    if " " in term or "-" in term:
        return term in text
    if len(term) <= 3:
        return re.search(rf"(?<![a-z0-9_-]){re.escape(term)}(?![a-z0-9_-])", text) is not None
    return re.search(rf"(?<![a-z0-9_-]){re.escape(term)}(?![a-z0-9_-])", text) is not None


def _rank_historical_cases(
    cases: list[dict[str, Any]],
    features: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_tags: set[str] = set(features["tags"])
    actor_tags = {"prc", "russia", "iran", "dprk"}
    candidate_actors = candidate_tags & actor_tags
    scored: list[dict[str, Any]] = []
    for case in cases:
        case_tags = set(case.get("tags") or set())
        case_actors = case_tags & actor_tags
        overlap = candidate_tags & case_tags
        score = 0.24 + min(0.38, len(overlap) * 0.07)
        if candidate_actors and case_actors:
            if candidate_actors & case_actors:
                score += 0.08
            else:
                score -= 0.18
        if {"edge", "appliance"} & candidate_tags and {"edge", "appliance"} & case_tags:
            score += 0.20
        if "prc" in candidate_tags and "prc" in case_tags:
            score += 0.16
        if "russia" in candidate_tags and "russia" in case_tags:
            score += 0.16
        if "dprk" in candidate_tags and "dprk" in case_tags:
            score += 0.16
        if "iran" in candidate_tags and "iran" in case_tags:
            score += 0.16
        if features["objective"] == "shutdown" and {"shutdown", "ics", "wiper"} & case_tags:
            score += 0.12
        if features["objective"] == "data_theft" and "data_theft" in case_tags:
            score += 0.12
        if features["objective"] == "persistence" and "persistence" in case_tags:
            score += 0.12
        if "supply_chain" in candidate_tags and "supply_chain" in case_tags:
            score += 0.14
        enriched = dict(case)
        enriched["match_score"] = round(min(score, 0.94), 2)
        enriched["matched_tags"] = sorted(overlap)
        scored.append(enriched)
    scored.sort(key=lambda item: (-item["match_score"], item["case_id"]))
    return scored


def _parse_calendar_events(markdown: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Date | Event" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        date_cell, event, parties, motive, why, source = cells[:6]
        start, end = _parse_date_range(date_cell)
        if not start:
            continue
        event_id = f"ctx_cal_{len(events) + 1:02d}"
        combined = f"{event} {parties} {motive} {why}"
        events.append(
            {
                "id": event_id,
                "context_type": "calendar",
                "date_cell": _strip_markdown(date_cell),
                "event": _strip_markdown(event),
                "parties": _strip_markdown(parties),
                "motive": _strip_markdown(motive),
                "why": _strip_markdown(why),
                "source": _source_url_from_cell(source) or _strip_markdown(source),
                "start": start,
                "end": end or start,
                "tags": _tags_from_text(combined),
            }
        )
    return events


def _parse_context_table_events(
    markdown: str,
    *,
    context_type: str,
    motive: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Date "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        date_cell = cells[0]
        start, end = _parse_date_range(date_cell)
        if not start:
            continue

        if context_type == "indictment":
            title = _strip_markdown(cells[1]) if len(cells) > 1 else "Legal pressure event"
            parties = _strip_markdown(cells[2]) if len(cells) > 2 else ""
            why = _strip_markdown(cells[3]) if len(cells) > 3 else ""
        else:
            title = _strip_markdown(cells[2]) if len(cells) > 2 else _strip_markdown(cells[1])
            parties = _strip_markdown(cells[1]) if len(cells) > 1 else ""
            why = _strip_markdown(cells[3]) if len(cells) > 3 else ""

        source_cell = cells[-1]
        combined = " ".join(_strip_markdown(cell) for cell in cells)
        event_id = f"ctx_{context_type}_{len(events) + 1:02d}"
        events.append(
            {
                "id": event_id,
                "context_type": context_type,
                "date_cell": _strip_markdown(date_cell),
                "event": title,
                "parties": parties,
                "motive": motive,
                "why": why,
                "source": _source_url_from_cell(source_cell) or _repo_doc_for_context(context_type),
                "start": start,
                "end": end or start,
                "tags": _tags_from_text(combined) | {context_type},
            }
        )
    return events


def _source_url_from_cell(cell: str) -> str:
    markdown_link = re.search(r"\[[^\]]+\]\((https?://[^)]+)\)", cell)
    if markdown_link:
        return markdown_link.group(1).strip()
    bare = re.search(r"https?://[^\s<>)\]]+", cell)
    if bare:
        return bare.group(0).rstrip(".,;")
    return ""


def _repo_doc_for_context(context_type: str) -> str:
    if context_type == "indictment":
        return "world-side/data/indictments_state.md"
    if context_type == "sanctions":
        return "world-side/data/sanctions_state.md"
    return "world-side/data/calendar_events.md"


def _parse_date_range(date_cell: str) -> tuple[_dt.date | None, _dt.date | None]:
    clean = _strip_markdown(date_cell)
    dates = re.findall(r"20\d{2}-\d{2}-\d{2}", clean)
    if dates:
        start = _date_from_iso(dates[0])
        end = _date_from_iso(dates[-1])
        return start, end

    first = re.search(r"(20\d{2})-(\d{2})-(\d{2})\s+to\s+(\d{1,2})", clean)
    if first:
        year, month, day, end_day = first.groups()
        start = _date_from_parts(year, month, day)
        end = _date_from_parts(year, month, end_day)
        return start, end

    month_only = re.search(r"(20\d{2})-(\d{2})(?!-\d{2})", clean)
    if month_only:
        year, month = month_only.groups()
        start = _date_from_parts(year, month, "01")
        if start:
            end = _last_day_of_month(start)
            return start, end

    return None, None


def _date_from_iso(value: str) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        return None


def _date_from_parts(year: str, month: str, day: str) -> _dt.date | None:
    try:
        return _dt.date(int(year), int(month), int(day))
    except ValueError:
        return None


def _last_day_of_month(day: _dt.date) -> _dt.date:
    if day.month == 12:
        next_month = _dt.date(day.year + 1, 1, 1)
    else:
        next_month = _dt.date(day.year, day.month + 1, 1)
    return next_month - _dt.timedelta(days=1)


def _context_file_sources(data_dir: Path) -> list[dict[str, str]]:
    specs = [
        (
            "src_context_calendar",
            "World Side current context: calendar events",
            data_dir / "calendar_events.md",
            "scheduled geopolitical and infrastructure stress windows",
        ),
        (
            "src_context_indictments",
            "World Side current context: indictments and prosecutions",
            data_dir / "indictments_state.md",
            "legal pressure indicators that can alter actor tempo",
        ),
        (
            "src_context_sanctions",
            "World Side current context: sanctions state",
            data_dir / "sanctions_state.md",
            "sanctions pressure indicators used for motive scoring",
        ),
    ]
    return [
        {
            "id": source_id,
            "label": label,
            "url": _repo_relative(path),
            "date": "2026-05-02",
            "supports": supports,
        }
        for source_id, label, path, supports in specs
        if path.exists()
    ]


def _chatter_context_source(
    *,
    chatter_path: str | Path | None,
    chatter_paths: Iterable[str | Path] | None,
    event_count: int,
) -> dict[str, str]:
    paths: list[str] = []
    if chatter_path:
        paths.append(_repo_relative(Path(chatter_path)))
    if chatter_paths:
        paths.extend(_repo_relative(Path(path)) for path in chatter_paths)
    location = ", ".join(paths) if paths else "runtime sanitized chatter records"
    return {
        "id": "src_context_chatter",
        "label": "World Side current context: sanitized chatter",
        "url": location,
        "date": "2026-05-02",
        "supports": f"{event_count} sanitized chatter signal(s) cleared for forecast use",
    }


def _osint_context_source(
    *,
    osint_snapshot_paths: Iterable[str | Path] | None,
    osint_manifest_paths: Iterable[str | Path] | None,
    event_count: int,
) -> dict[str, str]:
    snapshot_paths = [_repo_relative(Path(path)) for path in osint_snapshot_paths or []]
    manifest_paths = [_repo_relative(Path(path)) for path in osint_manifest_paths or []]
    locations = snapshot_paths + manifest_paths
    location = ", ".join(locations) if locations else "runtime sanitized OSINT snapshot"
    return {
        "id": "src_context_osint_snapshot",
        "label": "World Side current context: open-source metadata snapshot",
        "url": location,
        "date": "2026-05-04",
        "supports": f"{event_count} sanitized open-source metadata signal(s) cleared for forecast use",
    }


def _asset_seedset_context_source(
    *,
    asset_seedset_paths: Iterable[str | Path] | None,
    seedset_count: int,
) -> dict[str, str]:
    paths = [_repo_relative(Path(path)) for path in asset_seedset_paths or []]
    location = ", ".join(paths) if paths else "runtime asset/SBOM OSINT seedset"
    return {
        "id": "src_context_asset_seedset",
        "label": "World Side current context: asset/SBOM OSINT seedset",
        "url": location,
        "date": "2026-05-04",
        "supports": f"{seedset_count} asset-derived open-source seedset(s) cleared for forecast use",
    }


def _load_osint_manifests(paths: Iterable[str | Path] | None) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path_like in paths or []:
        path = Path(path_like)
        if not path.exists():
            raise FileNotFoundError(f"OSINT snapshot manifest not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"OSINT snapshot manifest must be an object: {path}")
        manifests.append(data)
    return manifests


def _load_asset_seedsets(paths: Iterable[str | Path] | None) -> list[dict[str, Any]]:
    seedsets: list[dict[str, Any]] = []
    for path_like in paths or []:
        path = Path(path_like)
        if not path.exists():
            raise FileNotFoundError(f"asset seedset not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"asset seedset must be an object: {path}")
        if validate_asset_seedset is not None:
            validate_asset_seedset(data)
        seedsets.append(data)
    return seedsets


def _apply_asset_seed_features(
    features: dict[str, Any],
    seedsets: list[dict[str, Any]],
) -> dict[str, Any]:
    if not seedsets:
        return features
    enriched = dict(features)
    tags: set[str] = set(features.get("tags") or set())
    for seedset in seedsets:
        for item in seedset.get("exposure_class_seeds") or []:
            if not isinstance(item, dict):
                continue
            exposure = str(item.get("exposure_class") or "")
            tags.update(_tags_from_text(exposure.replace("_", " ")))
            if "edge" in exposure.lower():
                tags.update({"edge", "appliance", "us_gov"})
        for item in seedset.get("product_family_seeds") or []:
            if not isinstance(item, dict):
                continue
            tags.update(_tags_from_text(str(item.get("product_family") or "")))
        if seedset.get("cve_seeds"):
            tags.add("appliance")
    enriched["tags"] = tags
    return enriched


def _build_strike_windows(
    events: list[dict[str, Any]],
    analogies: list[dict[str, Any]],
    features: dict[str, Any],
    *,
    as_of: _dt.date,
) -> list[dict[str, Any]]:
    candidate_tags: set[str] = set(features["tags"])
    scored_events: list[dict[str, Any]] = []
    for event in events:
        score = _event_relevance(event, candidate_tags, as_of)
        if score <= 0:
            continue
        _, expanded_end = _expand_window(event)
        if expanded_end < as_of:
            continue
        enriched = dict(event)
        enriched["relevance"] = score
        scored_events.append(enriched)
    scored_events.sort(key=lambda item: (-item["relevance"], item["start"]))

    selected = scored_events[:3]
    if not selected and events:
        selected = [event for event in events if _expand_window(event)[1] >= as_of][:3]

    windows: list[dict[str, Any]] = []
    top_analogies = analogies[:2] or []
    for rank, event in enumerate(selected, start=1):
        start, end = _expand_window(event)
        base = 0.46 + min(0.22, event.get("relevance", 0) * 0.05)
        if top_analogies:
            base += min(0.14, top_analogies[0].get("match_score", 0) * 0.12)
        if rank == 1:
            base += 0.04
        score = round(min(base, 0.82), 2)
        analogy_payload = [_analogy_payload(item) for item in top_analogies]
        windows.append(
            {
                "window_id": f"win_{rank}",
                "rank": rank,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "confidence": _confidence_label(score),
                "confidence_score": score,
                "why_this_window": _window_rationale(event, analogy_payload, features),
                "trigger_signals": _trigger_signals(event, features),
                "historical_analogies": analogy_payload,
                "event": event,
            }
        )
    return windows


def _event_relevance(
    event: dict[str, Any],
    candidate_tags: set[str],
    as_of: _dt.date,
) -> int:
    event_tags = set(event.get("tags") or set())
    text = f"{event.get('event', '')} {event.get('parties', '')} {event.get('why', '')}".lower()
    score = len(candidate_tags & event_tags)
    context_type = str(event.get("context_type", "calendar"))

    if context_type == "sanctions":
        if "sanctions" in event_tags:
            score += 2
        if {"prc", "russia", "iran", "dprk"} & candidate_tags:
            score += 1
    if context_type == "indictment":
        if "indictment" in event_tags:
            score += 2
        if {"prc", "russia", "iran", "dprk"} & candidate_tags:
            score += 1
    if context_type in {"chatter", "osint_signal"}:
        score += 3
        if event_tags & candidate_tags:
            score += min(6, len(event_tags & candidate_tags) * 2)
        if event.get("confidence") == "high":
            score += 3
        elif event.get("confidence") == "medium":
            score += 2
        if event.get("collection_tier") in {"public_chatter", "darkweb_metadata"}:
            score += 1

    if "prc" in candidate_tags:
        if any(word in text for word in ("prc", "china", "chinese", "taiwan", "asean", "shangri-la", "apec", "tiananmen")):
            score += 4
        if "trump" in text and "xi" in text:
            score += 3
        if "dipl" in str(event.get("motive", "")).lower():
            score += 1
    if "russia" in candidate_tags:
        if any(word in text for word in ("russia", "nato", "ukraine", "sanction", "g7")):
            score += 4
    if "dprk" in candidate_tags:
        if any(word in text for word in ("dprk", "north korean", "crypto", "fomc", "financial")):
            score += 4
    if "iran" in candidate_tags:
        if any(word in text for word in ("iran", "irgc", "israel", "sanction", "9/11")):
            score += 4
    if {"edge", "appliance", "us_gov"} & candidate_tags:
        if any(word in text for word in ("summit", "defense", "government", "federal", "us", "five eyes")):
            score += 2
    if "shutdown" in candidate_tags and "crit-infra" in str(event.get("motive", "")).lower():
        score += 3
    if "election" in candidate_tags and "elec" in str(event.get("motive", "")).lower():
        score += 3
    days_until = (event["start"] - as_of).days
    if event["end"] >= as_of and days_until <= 30:
        score += 4
    elif 0 <= days_until <= 60:
        score += 3
    elif 61 <= days_until <= 120:
        score += 1
    elif days_until > 180:
        score -= 1
    elif event["end"] < as_of:
        score -= 3
    return score


def _expand_window(event: dict[str, Any]) -> tuple[_dt.date, _dt.date]:
    start: _dt.date = event["start"]
    end: _dt.date = event["end"]
    motive = str(event.get("motive", "")).upper()
    context_type = str(event.get("context_type", "calendar"))
    if context_type in {"chatter", "osint_signal"}:
        extra_days = 21 if event.get("confidence") == "high" else 14
        return start, end + _dt.timedelta(days=extra_days)
    if context_type == "sanctions":
        return start + _dt.timedelta(days=14), end + _dt.timedelta(days=75)
    if context_type == "indictment":
        return start, end + _dt.timedelta(days=60)
    if "DIPL" in motive:
        return start - _dt.timedelta(days=7), end
    if "ELEC" in motive:
        return start - _dt.timedelta(days=3), end + _dt.timedelta(days=3)
    if "ANNIV" in motive:
        return start - _dt.timedelta(days=2), end + _dt.timedelta(days=2)
    if "CRIT-INFRA" in motive:
        return start, end
    return start - _dt.timedelta(days=1), end + _dt.timedelta(days=1)


def _window_rationale(
    event: dict[str, Any],
    analogies: list[dict[str, Any]],
    features: dict[str, Any],
) -> str:
    event_name = event.get("event") or "the selected context event"
    motive = event.get("motive") or "current context"
    top = analogies[0] if analogies else None
    candidate_phrase = _candidate_phrase(features)
    if event.get("context_type") == "chatter":
        confidence = event.get("confidence") or "unknown"
        return (
            f"{event_name} is ranked because sanitized {confidence}-confidence "
            f"chatter overlaps the candidate's {candidate_phrase} profile and "
            f"points to {motive}. Raw collection artifacts remain outside the "
            "forecast pipeline."
        )
    if event.get("context_type") == "osint_signal":
        confidence = event.get("confidence") or "unknown"
        return (
            f"{event_name} is ranked because sanitized {confidence}-confidence "
            f"open-source metadata overlaps the candidate's {candidate_phrase} "
            "profile. Raw advisory bodies and scraper artifacts remain outside "
            "the forecast pipeline."
        )
    if top:
        return (
            f"{event_name} is ranked because its {motive} timing overlaps the "
            f"candidate's {candidate_phrase} profile. The nearest historical "
            f"anchor is {top['case_name']}, where the corpus pattern matched "
            f"{top['pattern_matched']}"
        )
    return (
        f"{event_name} is ranked because its {motive} timing overlaps the "
        f"candidate's {candidate_phrase} profile. Confidence is capped because "
        "no historical analogy was available in the local corpus."
    )


def _candidate_phrase(features: dict[str, Any]) -> str:
    identity = features.get("identity") or {}
    label = identity.get("cve_class_label") or identity.get("candidate_label")
    return str(label or "exploit-class").strip()


def _trigger_signals(event: dict[str, Any], features: dict[str, Any]) -> list[str]:
    signals = [str(event.get("motive") or "current context")]
    if event.get("context_type") in {"chatter", "osint_signal"}:
        source_type = str(event.get("source_type") or "sanitized source").replace("_", " ")
        tier = str(event.get("collection_tier") or "chatter").replace("_", " ")
        tier_label = f"{tier} context" if "signal" in tier else f"{tier} signal"
        confidence = str(event.get("confidence") or "unknown")
        source_label = "open-source metadata" if event.get("context_type") == "osint_signal" else source_type
        signals.extend(
            [
                f"sanitized {source_label}",
                tier_label,
                f"source confidence: {confidence}",
            ]
        )
    why = str(event.get("why") or "")
    tags = set(features.get("tags") or set())
    combined = f"{why} {event.get('event', '')} {event.get('parties', '')}".lower()
    for needle, label in [
        ("summit", "diplomatic collection window"),
        ("sanction", "sanctions pressure"),
        ("election", "election-cycle pressure"),
        ("critical infrastructure", "critical-infrastructure stress"),
        ("defense", "defense-ministry attention window"),
    ]:
        if needle.lower() in combined:
            signals.append(label)
    actor_signal_rules = [
        ("prc", ("prc", "china", "chinese", "taiwan"), "PRC strategic context"),
        ("dprk", ("dprk", "north korea", "korean"), "DPRK revenue pressure"),
        ("russia", ("russia", "russian", "gru", "ukraine"), "Russia-linked retaliation pressure"),
        ("iran", ("iran", "iranian", "irgc"), "Iran-linked retaliation pressure"),
    ]
    for tag, needles, label in actor_signal_rules:
        if tag in tags and any(needle in combined for needle in needles):
            signals.append(label)
    if features["objective"] in {"shutdown", "disruption"}:
        signals.append("candidate objective is disruption/shutdown")
    return _dedupe(signals)[:5]


def _analogy_payload(case: dict[str, Any]) -> dict[str, Any]:
    pattern = case.get("pattern_signature") or case.get("why_anchor") or case.get("case_name")
    return {
        "case_id": case["case_id"],
        "case_name": case["case_name"],
        "pattern_matched": _truncate(pattern, 240),
        "time_to_burn": _truncate(case.get("time_to_burn") or "not stated", 180),
        "source_ref_ids": [f"src_{case['case_id']}_corpus"],
    }


def _build_strike_vectors(
    candidate: dict[str, Any],
    analogies: list[dict[str, Any]],
    features: dict[str, Any],
    *,
    chatter_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    tags: set[str] = set(features["tags"])
    objective = features["objective"]
    chatter_events = chatter_events or []
    candidates: list[dict[str, Any]] = []

    if {"edge", "appliance"} & tags:
        candidates.append(
            _vector_template(
                "edge-appliance initial access and pre-positioning",
                "US federal and defense-industrial perimeter services",
                objective if objective != "unknown" else "persistence",
                "Adversary interest centers on exposed perimeter infrastructure as an access and staging layer; details remain at sector and technique-class level.",
                "Matches a Stage 1 candidate framed around edge-device, VPN, gateway, or perimeter-control behavior.",
                "Perimeter appliance cases in the corpus, especially Volt Typhoon and Ivanti, make this the strongest fit.",
                "Prioritize detection and blocking for perimeter-device access patterns, configuration drift, and suspicious administrative sessions.",
                {"edge", "appliance", "prc", "persistence"},
            )
        )
    if "prc" in tags or "persistence" in tags:
        candidates.append(
            _vector_template(
                "living-off-the-land pre-positioning",
                "US critical infrastructure and defense-support enterprise networks",
                "persistence",
                "Adversary value comes from maintaining low-noise access with ordinary administration tooling until a separate strategic trigger raises activation risk.",
                "Fits candidates whose effect is durable access, control, or pre-positioning rather than immediate destructive impact.",
                "Volt Typhoon and SolarWinds-style anchors show that access can sit dormant until a geopolitical trigger makes activation valuable.",
                "Prioritize behavior-based detections for administrative-tool misuse, account hygiene, and suspicious egress from critical services.",
                {"prc", "persistence", "edge"},
            )
        )
    if "ics" in tags or objective in {"shutdown", "disruption"}:
        candidates.append(
            _vector_template(
                "critical-infrastructure disruption staging",
                "US government-adjacent critical infrastructure and operational technology",
                objective if objective != "unknown" else "disruption",
                "The forecast treats shutdown effects as a defensive scenario for service disruption, not as instructions for affecting a live system.",
                "Fits candidates whose intended effect is control, shutdown, or disruption rather than data theft.",
                "Wiper and OT cases show disruption tends to activate around crisis or symbolic windows after prior access is already in place.",
                "Validate deny, detect, and rollback controls for safe sandbox services that represent the operational dependency.",
                {"ics", "shutdown", "wiper", "russia"},
            )
        )
    if "wiper" in tags or objective in {"shutdown", "disruption"}:
        candidates.append(
            _vector_template(
                "wiper or destructive-malware readiness",
                "government, critical-infrastructure, and crisis-adjacent enterprise networks",
                "disruption" if objective == "unknown" else objective,
                "The vector is modeled as availability-risk readiness for defensive validation, not as a payload or deployment procedure.",
                "Fits candidates whose intended effect is shutdown, disruption, or service denial.",
                "NotPetya, HermeticWiper, and Shamoon-style anchors show destructive or disruptive burns cluster around sanctions, holidays, anniversaries, or kinetic crisis windows.",
                "Prioritize destructive-action detections, backup isolation, privileged-access review, and rapid rollback rehearsal.",
                {"wiper", "shutdown", "russia", "iran"},
            )
        )
    if "supply_chain" in tags:
        candidates.append(
            _vector_template(
                "software or service supply-chain access",
                "federal civilian agencies and enterprise software consumers",
                objective if objective != "unknown" else "persistence",
                "Adversary value comes from trusted distribution or managed-service relationships rather than direct targeting of named organizations.",
                "Maps to candidates involving update paths, vendor trust, or managed file-transfer/service infrastructure.",
                "SolarWinds and MOVEit anchors show that supply-chain timing can be long-fuse or holiday-window driven depending on actor objective.",
                "Prioritize provenance checks, signed artifact validation, service telemetry, and detection around staged downstream access.",
                {"supply_chain", "persistence", "data_theft"},
            )
        )
    if "financial" in tags or objective == "data_theft":
        candidates.append(
            _vector_template(
                "financial or high-value data theft operation",
                "financial services, crypto custody, and sensitive data processors",
                "data_theft",
                "The forecast stays at fraud and custody-system risk level without describing theft procedures or account paths.",
                "Fits candidates tied to data access, financial systems, managed transfer, or credential reuse.",
                "DPRK and Cl0p anchors show revenue-driven actors burn access around sanctions pressure, market stress, or response gaps.",
                "Prioritize anomaly detection, transfer review, credential controls, and extortion-resilient backup and disclosure workflows.",
                {"financial", "data_theft", "dprk", "ransomware"},
            )
        )
    if "ransomware" in tags or "financial" in tags or objective == "data_theft":
        candidates.append(
            _vector_template(
                "mass extortion against enterprise services",
                "managed file transfer, SaaS, retail, logistics, healthcare, and government vendors",
                "data_theft",
                "Adversary value comes from burning a broadly useful enterprise-service weakness around a response-gap window for maximum leverage.",
                "Fits candidates involving high-value data access, managed workflows, or financial pressure.",
                "MOVEit and related managed-file-transfer anchors show mass data-theft campaigns can be timed to holidays and operational response gaps.",
                "Prioritize externally exposed service patching, data-egress monitoring, and weekend/holiday incident staffing.",
                {"ransomware", "financial", "data_theft", "supply_chain"},
            )
        )
    if "phishing" in tags or "election" in tags:
        candidates.append(
            _vector_template(
                "credential phishing and influence-support access",
                "campaign, policy, media, and civil-society organizations",
                objective if objective != "unknown" else "data_theft",
                "The vector is limited to credential-risk and influence-support classes; it excludes phishing kit details and target lists.",
                "Fits candidates involving credential access, email compromise, or politically timed disclosure risk.",
                "Election-cycle cases show timing follows news-cycle leverage more than exploit readiness.",
                "Prioritize account-hardening, suspicious-login detection, and leak-prevention workflows for the demo scenario.",
                {"phishing", "election", "russia", "iran"},
            )
        )

    if not candidates:
        candidates.append(
            _vector_template(
                "state-aligned exploit-class validation",
                "US federal and defense-industrial technology environments",
                objective,
                "The mechanism remains a high-level exploit-class forecast for defensive validation only.",
                "Maps to the candidate at class level because no narrower sector cue was present.",
                "Historical corpus match is partial; confidence should rise only after Cyber Side adds richer candidate details.",
                "Use the forecast to pick a safe representative validation path and require citations before escalation.",
                set(),
            )
        )

    vectors: list[dict[str, Any]] = []
    for vector in candidates:
        vector_tags = set(vector.pop("_tags"))
        matching_analogies = [
            case
            for case in analogies
            if vector_tags & set(case.get("tags") or set())
        ][:3]
        if not matching_analogies:
            matching_analogies = analogies[:2]
        matching_chatter = _matching_chatter_events(vector_tags, tags, chatter_events)[:2]
        base = 0.45
        if matching_analogies:
            base += min(0.24, matching_analogies[0].get("match_score", 0) * 0.20)
        if vector_tags & tags:
            base += min(0.12, len(vector_tags & tags) * 0.03)
        if matching_chatter:
            base += min(0.10, len(matching_chatter) * 0.04 + 0.02)
            vector["why_this_vector"] = (
                f"{vector['why_this_vector']} Sanitized chatter adds current, "
                "source-attributed context for this vector class."
            )
        vector["confidence_score"] = round(min(base, 0.84), 2)
        vector["confidence"] = _confidence_label(vector["confidence_score"])
        vector["analogies"] = matching_analogies
        vector["chatter_events"] = matching_chatter
        vectors.append(vector)

    vectors.sort(key=lambda item: -item["confidence_score"])
    for rank, vector in enumerate(vectors[:3], start=1):
        vector["rank"] = rank
        vector["vector_id"] = f"vec_{rank}"
    return vectors[:3]


def _matching_chatter_events(
    vector_tags: set[str],
    candidate_tags: set[str],
    chatter_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for event in chatter_events:
        event_tags = set(event.get("tags") or set())
        if vector_tags & event_tags or candidate_tags & event_tags:
            enriched = dict(event)
            enriched["_match_size"] = len((vector_tags | candidate_tags) & event_tags)
            matches.append(enriched)
    confidence_rank = {"high": 3, "medium": 2, "low": 1}
    matches.sort(
        key=lambda event: (
            -event.get("_match_size", 0),
            -confidence_rank.get(str(event.get("confidence")), 0),
            event.get("start") or _dt.date.min,
        )
    )
    return matches


def _vector_template(
    vector_class: str,
    target_sector: str,
    likely_objective: str,
    mechanism: str,
    fit: str,
    why: str,
    implication: str,
    tags: set[str],
) -> dict[str, Any]:
    return {
        "vector_class": vector_class,
        "target_sector": target_sector,
        "likely_objective": likely_objective if likely_objective in _ALLOWED_OBJECTIVES else "unknown",
        "non_actionable_mechanism": mechanism,
        "candidate_fit": fit,
        "why_this_vector": why,
        "defensive_implication": implication,
        "_tags": tags,
    }


def _build_strategic_frame(
    candidate: dict[str, Any],
    features: dict[str, Any],
    *,
    has_chatter: bool,
    asset_seedset_count: int = 0,
) -> dict[str, Any]:
    tags: set[str] = set(features["tags"])
    identity = features["identity"]

    if "prc" in tags:
        adversary = "PRC-prepositioning-class"
    elif "russia" in tags:
        adversary = "Russia-linked-disruption-or-espionage-class"
    elif "dprk" in tags:
        adversary = "DPRK-revenue-generation-class"
    elif "iran" in tags:
        adversary = "Iran-linked-retaliation-class"
    else:
        adversary = "state-aligned-opportunistic-class"

    if {"edge", "appliance"} & tags:
        target_scope = "US federal and defense-industrial edge infrastructure"
    elif "financial" in tags:
        target_scope = "financial services and crypto custody infrastructure"
    elif "ics" in tags:
        target_scope = "critical infrastructure and operational technology"
    elif "election" in tags:
        target_scope = "election, campaign, and civil-society infrastructure"
    else:
        target_scope = "US government and defense-industrial technology environments"

    candidate_label = identity.get("candidate_label") or identity.get("cve_class_label") or "candidate"
    assumptions = [
        f"Stage 1 candidate is treated as {candidate_label} for timing and vector matching.",
        "Forecast uses sector-level targets only; no named live targets are produced.",
        "Geopolitical confidence is computed separately from any Cyber Side technical priority score.",
    ]
    if has_chatter:
        assumptions.append(
            "Current chatter is sanitized JSONL only; raw scraper artifacts stay off the main box."
        )
    if asset_seedset_count:
        assumptions.append(
            f"{asset_seedset_count} asset/SBOM seedset(s) are used only for sector-level exposure matching."
        )

    return {
        "adversary_class": adversary,
        "target_scope": target_scope,
        "geographic_scope": "US federal / DIB infrastructure",
        "forecast_assumptions": assumptions,
        "excluded_uses": list(DEFAULT_EXCLUDED_USES),
    }


def _build_summary(
    candidate: dict[str, Any],
    windows: list[dict[str, Any]],
    vectors: list[dict[str, Any]],
    features: dict[str, Any],
    *,
    chatter_count: int,
    osint_count: int,
    asset_seedset_count: int,
) -> dict[str, Any]:
    top_window = windows[0] if windows else None
    top_vector = vectors[0] if vectors else None
    phrase = _candidate_phrase(features)
    if top_window and top_vector:
        one_line = (
            f"For {phrase}, rank {top_vector['vector_class']} highest and "
            f"treat {top_window['start_date']} to {top_window['end_date']} "
            "as the lead strike-window forecast."
        )
        demo = (
            f"Use {top_vector['vector_id']} inside {top_window['window_id']} "
            "as context for a safe Stage 3 validation scenario."
        )
        priority = top_vector["defensive_implication"]
    else:
        one_line = (
            f"For {phrase}, World Side produced a low-context forecast and needs "
            "more candidate detail before ranking strongly."
        )
        demo = "Use the schema output as a placeholder until richer candidate details land."
        priority = "Keep Stage 3 validation at representative, safe sandbox level."

    candidate_sources = candidate.get("source_refs") or []
    analyst_notes = [
        "Vector descriptions are intentionally non-actionable and sector-level.",
        "Every ranked window and vector includes source_ref_ids for UI citation rendering.",
    ]
    if chatter_count:
        analyst_notes.append(
            f"Included {chatter_count} sanitized chatter signal(s); raw scraper output is excluded."
        )
    if osint_count:
        analyst_notes.append(
            f"Included {osint_count} sanitized open-source metadata signal(s) from OSINT snapshot input."
        )
    if asset_seedset_count:
        analyst_notes.append(
            f"Included {asset_seedset_count} asset/SBOM seedset(s) for targeted OSINT context."
        )
    if not candidate_sources:
        analyst_notes.append(
            "Stage 1 candidate did not include source_refs; unsupported technical claims are treated as assumptions."
        )
    return {
        "one_line": one_line,
        "recommended_demo_path": demo,
        "stage3_priority": priority,
        "analyst_notes": analyst_notes,
    }


def _build_open_source_signals(
    *,
    records: list[Any],
    events: list[dict[str, Any]],
    snapshot_paths: Iterable[str | Path] | None,
    manifest_paths: Iterable[str | Path] | None,
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    source_type_counts: dict[str, int] = {}
    collection_tier_counts: dict[str, int] = {}
    for record in records:
        source_type = str(getattr(record, "source_type", "") or "unknown")
        collection_tier = str(getattr(record, "collection_tier", "") or "unknown")
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        collection_tier_counts[collection_tier] = collection_tier_counts.get(collection_tier, 0) + 1

    snapshot_list = [_repo_relative(Path(path)) for path in snapshot_paths or []]
    manifest_list = [_repo_relative(Path(path)) for path in manifest_paths or []]
    snapshot_hashes = {
        _repo_relative(Path(path)): _file_sha256(Path(path))
        for path in snapshot_paths or []
        if Path(path).exists()
    }
    manifest_hashes = {
        _repo_relative(Path(path)): _file_sha256(Path(path))
        for path in manifest_paths or []
        if Path(path).exists()
    }
    manifest_record_count = sum(
        int(manifest.get("record_count") or 0)
        for manifest in manifests
        if isinstance(manifest.get("record_count"), int)
    )
    failed_sources = sorted(
        {
            str(source)
            for manifest in manifests
            for source in manifest.get("failed_sources", [])
            if isinstance(source, str)
        }
    )
    successful_sources = sorted(
        {
            str(source)
            for manifest in manifests
            for source in manifest.get("successful_sources", [])
            if isinstance(source, str)
        }
    )
    source_failures = _osint_source_failures(manifests)

    return {
        "schema_version": "prophet.open_source_signals.v0.1",
        "integrated": bool(records),
        "record_count": len(records),
        "event_count": len(events),
        "manifest_record_count": manifest_record_count,
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "collection_tier_counts": dict(sorted(collection_tier_counts.items())),
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "freshness": _osint_freshness(records=records, manifests=manifests),
        "source_health": _osint_source_health(
            manifests=manifests,
            successful_sources=successful_sources,
            failed_sources=failed_sources,
        ),
        "source_failures": source_failures,
        "snapshot_paths": snapshot_list,
        "manifest_paths": manifest_list,
        "hashes": {
            "snapshot_jsonl_sha256": snapshot_hashes,
            "manifest_sha256": manifest_hashes,
        },
        "source_ref_ids": _dedupe(
            [
                "src_context_osint_snapshot",
                *[
                    str(getattr(record, "source_ref", {}).get("id"))
                    for record in records
                    if isinstance(getattr(record, "source_ref", {}), dict)
                    and getattr(record, "source_ref", {}).get("id")
                ],
            ]
        )
        if records
        else [],
        "basis_statement": (
            "Sanitized open-source metadata was integrated into ranked windows and vectors."
            if records
            else "No OSINT snapshot was provided for this forecast run."
        ),
    }


def _osint_freshness(
    *,
    records: list[Any],
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_times = [
        parsed
        for parsed in (
            _parse_datetime(str(manifest.get("generated_at") or ""))
            for manifest in manifests
        )
        if parsed is not None
    ]
    observed_times = [
        parsed
        for parsed in (
            _parse_datetime(str(getattr(record, "observed_at", "") or ""))
            for record in records
        )
        if parsed is not None
    ]
    snapshot_generated_at = max(generated_times) if generated_times else None
    newest_observed_at = max(observed_times) if observed_times else None
    oldest_observed_at = min(observed_times) if observed_times else None
    basis_time = snapshot_generated_at or newest_observed_at
    newest_record_age_days: float | None = None
    if basis_time is not None and newest_observed_at is not None:
        age_seconds = max(0.0, (basis_time - newest_observed_at).total_seconds())
        newest_record_age_days = round(age_seconds / 86400, 2)
    record_span_days: float | None = None
    if newest_observed_at is not None and oldest_observed_at is not None:
        span_seconds = max(0.0, (newest_observed_at - oldest_observed_at).total_seconds())
        record_span_days = round(span_seconds / 86400, 2)

    freshness_window_days = 7
    if not records:
        status = "not_provided"
    elif newest_record_age_days is None:
        status = "unknown"
    elif newest_record_age_days <= freshness_window_days:
        status = "current"
    else:
        status = "stale"

    return {
        "status": status,
        "snapshot_generated_at": _format_datetime(snapshot_generated_at),
        "oldest_record_observed_at": _format_datetime(oldest_observed_at),
        "newest_record_observed_at": _format_datetime(newest_observed_at),
        "newest_record_age_days": newest_record_age_days,
        "record_span_days": record_span_days,
        "freshness_window_days": freshness_window_days,
    }


def _osint_source_health(
    *,
    manifests: list[dict[str, Any]],
    successful_sources: list[str],
    failed_sources: list[str],
) -> dict[str, Any]:
    if not manifests:
        status = "not_provided"
    elif failed_sources:
        status = "degraded"
    else:
        status = "ok"
    return {
        "status": status,
        "manifest_count": len(manifests),
        "successful_source_count": len(successful_sources),
        "failed_source_count": len(failed_sources),
        "failure_policy": (
            "Failed sources are summarized in evidence; raw collection text remains excluded."
        ),
    }


def _osint_source_failures(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for manifest in manifests:
        for source in manifest.get("sources") or []:
            if not isinstance(source, dict):
                continue
            status = str(source.get("status") or "unknown")
            if status == "ok":
                continue
            failures.append(
                {
                    "source_id": str(source.get("source_id") or "unknown_source"),
                    "status": status,
                    "collector": str(source.get("collector") or "unknown"),
                    "source_type": str(source.get("source_type") or "unknown"),
                    "collection_tier": str(source.get("collection_tier") or "unknown"),
                    "records": int(source.get("records") or 0)
                    if not isinstance(source.get("records"), bool)
                    else 0,
                    "error": _truncate(str(source.get("error") or "not supplied"), 180),
                }
            )
    return failures


def _parse_datetime(value: str) -> _dt.datetime | None:
    if not value:
        return None
    try:
        parsed = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed.astimezone(_dt.timezone.utc)


def _format_datetime(value: _dt.datetime | None) -> str:
    if value is None:
        return "not supplied"
    return value.astimezone(_dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _build_asset_seed_context(
    *,
    seedsets: list[dict[str, Any]],
    seedset_paths: Iterable[str | Path] | None,
) -> dict[str, Any]:
    seedset_list = [_repo_relative(Path(path)) for path in seedset_paths or []]
    seedset_hashes = {
        _repo_relative(Path(path)): _file_sha256(Path(path))
        for path in seedset_paths or []
        if Path(path).exists()
    }
    if not seedsets:
        return {
            "schema_version": "prophet.asset_seed_context.v0.1",
            "integrated": False,
            "seedset_count": 0,
            "asset_count": 0,
            "fixture_context": False,
            "exposure_classes": [],
            "product_family_count": 0,
            "package_seed_count": 0,
            "cve_seed_count": 0,
            "owner_queues": [],
            "recommended_source_ids": [],
            "seedset_paths": seedset_list,
            "hashes": {"asset_seedset_sha256": seedset_hashes},
            "basis_statement": "No asset/SBOM seedset was provided for this forecast run.",
        }

    summaries: list[dict[str, Any]] = []
    for seedset in seedsets:
        if summarize_asset_seedset is not None:
            summaries.append(summarize_asset_seedset(seedset))
        else:
            summaries.append(_fallback_asset_seed_summary(seedset))

    exposure_classes = _dedupe(
        [
            exposure
            for summary in summaries
            for exposure in summary.get("exposure_classes", [])
            if isinstance(exposure, str)
        ]
    )
    product_families = _dedupe(
        [
            product
            for summary in summaries
            for product in summary.get("product_families", [])
            if isinstance(product, str)
        ]
    )
    owner_queues = _dedupe(
        [
            owner
            for summary in summaries
            for owner in summary.get("owner_queues", [])
            if isinstance(owner, str)
        ]
    )
    recommended_source_ids = _dedupe(
        [
            source_id
            for summary in summaries
            for source_id in summary.get("recommended_source_ids", [])
            if isinstance(source_id, str)
        ]
    )

    return {
        "schema_version": "prophet.asset_seed_context.v0.1",
        "integrated": True,
        "seedset_count": len(seedsets),
        "asset_count": sum(int(summary.get("asset_count") or 0) for summary in summaries),
        "fixture_context": all(bool(summary.get("fixture_context", True)) for summary in summaries),
        "exposure_classes": exposure_classes,
        "product_family_count": len(product_families),
        "product_families": product_families,
        "package_seed_count": sum(int(summary.get("package_seed_count") or 0) for summary in summaries),
        "cve_seed_count": sum(int(summary.get("cve_seed_count") or 0) for summary in summaries),
        "owner_queues": owner_queues,
        "recommended_source_ids": recommended_source_ids,
        "seedset_paths": seedset_list,
        "hashes": {
            "asset_seedset_sha256": seedset_hashes,
            "seedset_body_sha256": {
                str(seedset.get("seedset_id") or f"seedset_{idx}"): str(
                    seedset.get("seedset_sha256") or ""
                )
                for idx, seedset in enumerate(seedsets, start=1)
            },
        },
        "source_ref_ids": ["src_context_asset_seedset"],
        "basis_statement": (
            "Asset/SBOM-derived CVE, package, product-family, and exposure-class "
            "seeds narrowed open-source enrichment to customer-relevant metadata."
        ),
    }


def _fallback_asset_seed_summary(seedset: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_count": int(_as_dict(seedset.get("input_refs")).get("asset_count") or 0),
        "fixture_context": bool(seedset.get("fixture_context", True)),
        "exposure_classes": [
            str(item.get("exposure_class"))
            for item in seedset.get("exposure_class_seeds", [])
            if isinstance(item, dict) and item.get("exposure_class")
        ],
        "product_families": [
            str(item.get("product_family"))
            for item in seedset.get("product_family_seeds", [])
            if isinstance(item, dict) and item.get("product_family")
        ],
        "package_seed_count": len(seedset.get("package_seeds") or []),
        "cve_seed_count": len(seedset.get("cve_seeds") or []),
        "recommended_source_ids": [
            str(item) for item in seedset.get("recommended_source_ids", []) if isinstance(item, str)
        ],
        "owner_queues": [
            str(item.get("owner_group"))
            for item in seedset.get("owner_queues", [])
            if isinstance(item, dict) and item.get("owner_group")
        ],
    }


def _window_payload(window: dict[str, Any], sources: "_SourceRegistry") -> dict[str, Any]:
    event = window.pop("event")
    event_source_id = sources.ensure_event(event)
    source_ids = [event_source_id]
    context_source_id = _context_source_for_event(event)
    if context_source_id:
        source_ids.append(context_source_id)
    for analogy in window.get("historical_analogies", []):
        source_ids.extend(analogy.get("source_ref_ids", []))
    return {
        "window_id": window["window_id"],
        "rank": window["rank"],
        "start_date": window["start_date"],
        "end_date": window["end_date"],
        "confidence": window["confidence"],
        "confidence_score": window["confidence_score"],
        "why_this_window": window["why_this_window"],
        "trigger_signals": window["trigger_signals"],
        "historical_analogies": window["historical_analogies"],
        "source_ref_ids": _dedupe(source_ids),
    }


def _vector_payload(vector: dict[str, Any], sources: "_SourceRegistry") -> dict[str, Any]:
    analogies = vector.pop("analogies", [])
    chatter_events = vector.pop("chatter_events", [])
    source_ids: list[str] = []
    for case in analogies:
        source_ids.append(sources.ensure_case(case))
    for event in chatter_events:
        source_ids.append(sources.ensure_event(event))
    if not source_ids:
        source_ids.append("src_context_calendar")
    return {
        "vector_id": vector["vector_id"],
        "rank": vector["rank"],
        "vector_class": vector["vector_class"],
        "target_sector": vector["target_sector"],
        "likely_objective": vector["likely_objective"],
        "non_actionable_mechanism": vector["non_actionable_mechanism"],
        "candidate_fit": vector["candidate_fit"],
        "confidence": vector["confidence"],
        "confidence_score": vector["confidence_score"],
        "why_this_vector": vector["why_this_vector"],
        "defensive_implication": vector["defensive_implication"],
        "source_ref_ids": _dedupe(source_ids),
    }


def _context_source_for_event(event: dict[str, Any]) -> str:
    context_type = str(event.get("context_type") or "calendar")
    if context_type == "calendar":
        return "src_context_calendar"
    if context_type == "indictment":
        return "src_context_indictments"
    if context_type == "sanctions":
        return "src_context_sanctions"
    if context_type == "chatter":
        return "src_context_chatter"
    if context_type == "osint_signal":
        return "src_context_osint_snapshot"
    return "src_context_calendar"


class _SourceRegistry:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, str]] = {}

    def add(
        self,
        source_id: str,
        *,
        label: str,
        url: str,
        date: str,
        supports: str,
    ) -> str:
        if source_id not in self._items:
            self._items[source_id] = {
                "id": source_id,
                "label": label,
                "url": url,
                "date": _source_date(date),
                "supports": supports,
            }
        return source_id

    def ensure_case(self, case: dict[str, Any]) -> str:
        source_id = f"src_{case['case_id']}_corpus"
        self.add(
            source_id,
            label=f"Historical corpus: {case['case_name']}",
            url=f"world-side/data/historical_pairings.md#{case.get('anchor') or case['case_id']}",
            date="2026-05-02",
            supports=_truncate(
                case.get("pattern_signature")
                or case.get("why_anchor")
                or "historical analogy match",
                180,
            ),
        )
        for idx, source in enumerate((case.get("sources") or [])[:2], start=1):
            self.add(
                f"{source_id}_web_{idx}",
                label=source.get("label") or f"{case['case_name']} source {idx}",
                url=source.get("url") or "",
                date="",
                supports=f"external source for {case['case_name']}",
            )
        return source_id

    def ensure_event(self, event: dict[str, Any]) -> str:
        source_ref = event.get("source_ref")
        if isinstance(source_ref, dict):
            source_id = str(source_ref.get("id") or f"src_{event['id']}")
            return self.add(
                source_id,
                label=str(source_ref.get("label") or event.get("event") or source_id),
                url=str(source_ref.get("url") or event.get("source") or ""),
                date=str(source_ref.get("date") or event.get("date_cell") or ""),
                supports=_truncate(
                    str(source_ref.get("supports") or event.get("why") or "sanitized context"),
                    180,
                ),
            )
        return self.add(
            f"src_{event['id']}",
            label=f"{str(event.get('context_type') or 'calendar').title()} context: {event['event']}",
            url=event.get("source") or "world-side/data/calendar_events.md",
            date=event["start"].isoformat() if isinstance(event.get("start"), _dt.date) else event.get("date_cell") or "",
            supports=_truncate(event.get("why") or "scheduled context event", 180),
        )

    def items(self) -> list[dict[str, str]]:
        return [self._items[key] for key in sorted(self._items)]


def _register_candidate_sources(registry: _SourceRegistry, candidate: dict[str, Any]) -> None:
    for idx, ref in enumerate(candidate.get("source_refs") or [], start=1):
        if not isinstance(ref, dict):
            continue
        registry.add(
            f"src_stage1_{idx}",
            label=str(ref.get("label") or f"Stage 1 source {idx}"),
            url=str(ref.get("url") or ""),
            date=str(ref.get("date") or ""),
            supports=str(ref.get("supports") or "Stage 1 technical claim"),
        )


def _register_context_sources(
    registry: _SourceRegistry,
    context_sources: list[dict[str, str]],
) -> None:
    for ref in context_sources:
        registry.add(
            ref["id"],
            label=ref["label"],
            url=ref["url"],
            date=ref["date"],
            supports=ref["supports"],
        )


def _register_window_sources(
    registry: _SourceRegistry,
    windows: list[dict[str, Any]],
) -> None:
    for window in windows:
        registry.ensure_event(window["event"])


def _register_vector_sources(
    registry: _SourceRegistry,
    vectors: list[dict[str, Any]],
) -> None:
    for vector in vectors:
        for case in vector.get("analogies", []):
            registry.ensure_case(case)
        for event in vector.get("chatter_events", []):
            registry.ensure_event(event)


def _register_osint_sources(
    registry: _SourceRegistry,
    osint_events: list[dict[str, Any]],
) -> None:
    for event in osint_events:
        registry.ensure_event(event)


def _register_analogy_sources(
    registry: _SourceRegistry,
    analogies: list[dict[str, Any]],
) -> None:
    for case in analogies:
        registry.ensure_case(case)


def _assert_source_ref_integrity(forecast: dict[str, Any]) -> None:
    known = {item["id"] for item in forecast.get("source_refs", [])}
    used: set[str] = set()
    for window in forecast.get("strike_windows", []):
        used.update(window.get("source_ref_ids", []))
        for analogy in window.get("historical_analogies", []):
            used.update(analogy.get("source_ref_ids", []))
    for vector in forecast.get("strike_vectors", []):
        used.update(vector.get("source_ref_ids", []))
    missing = sorted(used - known)
    if missing:
        raise ValueError(f"forecast references missing source ids: {', '.join(missing)}")


def _forecast_id(candidate: dict[str, Any], generated_at: str) -> str:
    seed = "|".join(
        [
            str(candidate.get("candidate_id") or "unknown"),
            generated_at,
            str((_as_dict(candidate.get("identity"))).get("candidate_label") or ""),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    day = generated_at[:10].replace("-", "")
    return f"ws-{day}-{digest}"


def _confidence_label(score: float) -> str:
    for threshold, label in _CONFIDENCE_LABELS:
        if score >= threshold:
            return label
    return "low"


def _slugify_heading(number: str, heading: str) -> str:
    text = f"{number}-{heading}".lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def _repo_relative(path: Path) -> str:
    parts = path.parts
    for anchor in ("world-side", "cyber-side", "assets", "evidence", "docs"):
        if anchor in parts:
            idx = parts.index(anchor)
            return "/".join(parts[idx:])
    return str(path)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_date(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value or "")):
        return str(value)
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", str(value or ""))
    if match:
        return match.group(1)
    return "2026-05-02"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strip_markdown(value: str) -> str:
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return _squash(value)


def _squash(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _truncate(value: str, limit: int) -> str:
    value = _squash(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "."


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
