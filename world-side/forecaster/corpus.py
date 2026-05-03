"""Markdown corpus parsers for Prophet World Side.

Worker 3 owns this module. It keeps the current research corpus usable by
downstream matchers and scorers without requiring non-stdlib dependencies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Iterable

try:  # Allow both package imports and direct `sys.path` imports in scripts/tests.
    from .features import FeatureSet, extract_features, merge_feature_sets
except ImportError:  # pragma: no cover - exercised only when imported as a script module.
    from features import FeatureSet, extract_features, merge_feature_sets


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"

CASE_HEADING_RE = re.compile(r"^##\s+(?P<number>\d+)\.\s+(?P<title>.+?)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^\*\*(?P<name>[^*]+?)\.\*\*\s*(?P<lead>.*)$", re.MULTILINE)
SOURCE_RE = re.compile(r"-\s+\[(?P<label>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
URL_RE = re.compile(r"https?://[^\s)|]+")
TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")


@dataclass(frozen=True)
class SourceRef:
    """A cited source extracted from corpus markdown."""

    label: str
    url: str
    source_id: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalCase:
    """One numbered historical analogy anchor."""

    case_id: int
    title: str
    slug: str
    geopolitical_context: str
    cyber_event: str
    time_to_burn: str
    pattern_signature: str
    why_anchor: str
    sources: tuple[SourceRef, ...]
    features: FeatureSet
    summary_actor: str = ""
    summary_trigger_class: str = ""
    summary_time_to_burn: str = ""
    summary_burn_class: str = ""
    source_path: str = ""
    raw_markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["features"] = self.features.to_dict()
        data["sources"] = [source.to_dict() for source in self.sources]
        return data


@dataclass(frozen=True)
class ContextEvent:
    """A current-context signal from calendar, indictment, or sanctions docs."""

    context_type: str
    title: str
    date: str = ""
    parties: str = ""
    motive_classes: tuple[str, ...] = ()
    why_it_matters: str = ""
    source_urls: tuple[str, ...] = ()
    features: FeatureSet = FeatureSet()
    source_path: str = ""
    raw_markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["features"] = self.features.to_dict()
        return data


@dataclass(frozen=True)
class CorpusBundle:
    """Convenience wrapper containing all parsed World Side corpus inputs."""

    historical_cases: tuple[HistoricalCase, ...]
    context_events: tuple[ContextEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "historical_cases": [case.to_dict() for case in self.historical_cases],
            "context_events": [event.to_dict() for event in self.context_events],
        }


def load_corpus_bundle(data_dir: str | Path = DEFAULT_DATA_DIR) -> CorpusBundle:
    """Load historical cases plus current-context events from a data directory."""

    data_path = Path(data_dir)
    return CorpusBundle(
        historical_cases=tuple(load_historical_cases(data_path / "historical_pairings.md")),
        context_events=tuple(load_context_events(data_path)),
    )


def load_historical_cases(path: str | Path = DEFAULT_DATA_DIR / "historical_pairings.md") -> list[HistoricalCase]:
    """Read and parse `historical_pairings.md`."""

    source_path = Path(path)
    return parse_historical_pairings(source_path.read_text(encoding="utf-8"), source_path=str(source_path))


def parse_historical_pairings(markdown: str, *, source_path: str = "") -> list[HistoricalCase]:
    """Parse numbered historical cases from the analogy corpus markdown."""

    summary_rows = _parse_engine_summary(markdown)
    case_matches = list(CASE_HEADING_RE.finditer(markdown))
    cases: list[HistoricalCase] = []

    for index, match in enumerate(case_matches):
        case_id = int(match.group("number"))
        title = match.group("title").strip()
        next_start = case_matches[index + 1].start() if index + 1 < len(case_matches) else len(markdown)
        body = _trim_engine_summary(markdown[match.end() : next_start].strip())
        fields = _parse_case_fields(body)
        sources = _parse_sources(body, case_id)
        summary = summary_rows.get(case_id, {})

        feature_text = "\n\n".join(
            value
            for value in (
                title,
                fields.get("geopolitical context window", ""),
                fields.get("cyber event", ""),
                fields.get("time-to-burn", ""),
                fields.get("pattern signature", ""),
                fields.get("why it's a useful anchor", ""),
                summary.get("actor", ""),
                summary.get("trigger_class", ""),
                summary.get("burn_class", ""),
            )
            if value
        )
        source_features = extract_features("\n".join(source.url for source in sources))

        cases.append(
            HistoricalCase(
                case_id=case_id,
                title=title,
                slug=_slugify(title),
                geopolitical_context=fields.get("geopolitical context window", ""),
                cyber_event=fields.get("cyber event", ""),
                time_to_burn=fields.get("time-to-burn", ""),
                pattern_signature=fields.get("pattern signature", ""),
                why_anchor=fields.get("why it's a useful anchor", ""),
                sources=sources,
                features=merge_feature_sets(extract_features(feature_text), source_features),
                summary_actor=summary.get("actor", ""),
                summary_trigger_class=summary.get("trigger_class", ""),
                summary_time_to_burn=summary.get("time_to_burn", ""),
                summary_burn_class=summary.get("burn_class", ""),
                source_path=source_path,
                raw_markdown=body,
            )
        )

    return cases


def load_context_events(data_dir: str | Path = DEFAULT_DATA_DIR) -> list[ContextEvent]:
    """Load current-context docs from the World Side data directory."""

    data_path = Path(data_dir)
    events: list[ContextEvent] = []
    file_parsers = (
        ("calendar_events.md", parse_calendar_events),
        ("indictments_state.md", parse_indictment_events),
        ("sanctions_state.md", parse_sanctions_events),
    )
    for filename, parser in file_parsers:
        path = data_path / filename
        if path.exists():
            events.extend(parser(path.read_text(encoding="utf-8"), source_path=str(path)))
    return events


def parse_calendar_events(markdown: str, *, source_path: str = "") -> list[ContextEvent]:
    """Parse the master chronological calendar table into context events."""

    rows = _parse_markdown_tables(markdown)
    events: list[ContextEvent] = []
    for row in rows:
        if len(row) < 6:
            continue
        date, event, parties, motive_class, why, source = row[:6]
        if not _looks_like_date_cell(date):
            continue
        title = _strip_markdown(event)
        motives = _split_motive_classes(_strip_markdown(motive_class))
        raw = " | ".join(row[:6])
        events.append(
            ContextEvent(
                context_type="calendar",
                date=_strip_markdown(date),
                title=title,
                parties=_strip_markdown(parties),
                motive_classes=motives,
                why_it_matters=_strip_markdown(why),
                source_urls=_extract_urls(source),
                features=_context_features(raw, motives),
                source_path=source_path,
                raw_markdown=raw,
            )
        )
    return events


def parse_indictment_events(markdown: str, *, source_path: str = "") -> list[ContextEvent]:
    """Parse indictment/prosecution headings and the pending-status table."""

    events: list[ContextEvent] = []

    for section in _iter_numbered_subsections(markdown):
        title = _strip_markdown(section["title"])
        body = section["body"]
        date = _extract_first_date(title) or _extract_labeled_value(body, "Trial dates") or _extract_first_date(body)
        affiliation = _extract_labeled_value(body, "Affiliation")
        campaign = _extract_labeled_value(body, "Underlying campaigns")
        raw = f"{title}\n{body}"
        events.append(
            ContextEvent(
                context_type="indictment",
                date=date,
                title=title,
                parties=affiliation,
                motive_classes=("LEGAL",),
                why_it_matters=_first_nonempty(campaign, _extract_labeled_value(body, "Charges"), _preview(body)),
                source_urls=_extract_urls(body),
                features=_context_features(raw, ("LEGAL",)),
                source_path=source_path,
                raw_markdown=body,
            )
        )

    for row in _parse_markdown_tables(markdown):
        if len(row) < 5:
            continue
        date, defendant, group, status, source = row[:5]
        if not _looks_like_date_cell(date):
            continue
        raw = " | ".join(row[:5])
        events.append(
            ContextEvent(
                context_type="legal_status",
                date=_strip_markdown(date),
                title=_strip_markdown(defendant),
                parties=_strip_markdown(group),
                motive_classes=("LEGAL",),
                why_it_matters=_strip_markdown(status),
                source_urls=_extract_urls(source),
                features=_context_features(raw, ("LEGAL",)),
                source_path=source_path,
                raw_markdown=raw,
            )
        )

    return _dedupe_context_events(events)


def parse_sanctions_events(markdown: str, *, source_path: str = "") -> list[ContextEvent]:
    """Parse sanctions tables and regime profiles into context events."""

    events: list[ContextEvent] = []

    for row in _parse_markdown_tables(markdown):
        if len(row) < 4:
            continue
        date = _strip_markdown(row[0])
        if not _looks_like_date_cell(date) and not date.lower().startswith(("pending", "outstanding", "mid-")):
            continue

        title = _strip_markdown(row[2] if len(row) >= 5 else row[1])
        parties = _strip_markdown(row[1])
        why = _strip_markdown(row[3] if len(row) >= 5 else row[2])
        source = row[4] if len(row) >= 5 else row[-1]
        raw = " | ".join(row)
        events.append(
            ContextEvent(
                context_type="sanctions",
                date=date,
                title=title,
                parties=parties,
                motive_classes=("FIN", "LEGAL"),
                why_it_matters=why,
                source_urls=_extract_urls(source),
                features=_context_features(raw, ("FIN", "LEGAL")),
                source_path=source_path,
                raw_markdown=raw,
            )
        )

    for section in _iter_regime_profiles(markdown):
        title = _strip_markdown(section["title"])
        body = section["body"]
        raw = f"{title}\n{body}"
        events.append(
            ContextEvent(
                context_type="sanctions_profile",
                title=title,
                motive_classes=("FIN", "LEGAL"),
                why_it_matters=_preview(body, limit=700),
                source_urls=_extract_urls(body),
                features=_context_features(raw, ("FIN", "LEGAL")),
                source_path=source_path,
                raw_markdown=body,
            )
        )

    return _dedupe_context_events(events)


def cases_by_actor(cases: Iterable[HistoricalCase]) -> dict[str, list[HistoricalCase]]:
    """Group historical cases by extracted actor country."""

    grouped: dict[str, list[HistoricalCase]] = {}
    for case in cases:
        for country in case.features.actor_countries or ("Unknown",):
            grouped.setdefault(country, []).append(case)
    return grouped


def cases_by_feature(cases: Iterable[HistoricalCase], feature_field: str) -> dict[str, list[HistoricalCase]]:
    """Group historical cases by a named FeatureSet tuple field."""

    if feature_field not in FeatureSet.__dataclass_fields__:
        raise ValueError(f"unknown feature field: {feature_field}")
    grouped: dict[str, list[HistoricalCase]] = {}
    for case in cases:
        for value in getattr(case.features, feature_field):
            grouped.setdefault(value, []).append(case)
    return grouped


def _parse_case_fields(body: str) -> dict[str, str]:
    matches = list(FIELD_RE.finditer(body))
    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = _canonical_field_name(match.group("name"))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        lead = match.group("lead").strip()
        continuation = body[start:end].strip()
        fields[name] = _strip_markdown("\n".join(part for part in (lead, continuation) if part))
    return fields


def _parse_sources(body: str, case_id: int) -> tuple[SourceRef, ...]:
    sources: list[SourceRef] = []
    for index, match in enumerate(SOURCE_RE.finditer(body), start=1):
        sources.append(
            SourceRef(
                label=_strip_markdown(match.group("label")),
                url=match.group("url").strip(),
                source_id=f"historical:{case_id}:source:{index}",
            )
        )
    return tuple(sources)


def _parse_engine_summary(markdown: str) -> dict[int, dict[str, str]]:
    marker = "## Engine-facing summary table"
    if marker not in markdown:
        return {}
    summary: dict[int, dict[str, str]] = {}
    for row in _parse_markdown_tables(markdown.split(marker, 1)[1]):
        if len(row) < 6 or not row[0].strip().isdigit():
            continue
        summary[int(row[0])] = {
            "case": _strip_markdown(row[1]),
            "actor": _strip_markdown(row[2]),
            "trigger_class": _strip_markdown(row[3]),
            "time_to_burn": _strip_markdown(row[4]),
            "burn_class": _strip_markdown(row[5]),
        }
    return summary


def _parse_markdown_tables(markdown: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        match = TABLE_ROW_RE.match(line.strip())
        if not match:
            continue
        cells = [_strip_markdown(cell.strip()) for cell in match.group(1).split("|")]
        if not cells or _is_table_header_or_rule(cells):
            continue
        rows.append(cells)
    return rows


def _iter_numbered_subsections(markdown: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"^###\s+(?P<num>\d+\.\d+)\s+(?P<title>.+?)\s*$", markdown, re.MULTILINE))
    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections.append({"title": match.group("title"), "body": markdown[start:end].strip()})
    return sections


def _iter_regime_profiles(markdown: str) -> list[dict[str, str]]:
    marker = "## 4. Currently sanctioned regimes"
    if marker not in markdown:
        return []
    tail = markdown.split(marker, 1)[1]
    stop = tail.find("\n## 5.")
    if stop != -1:
        tail = tail[:stop]
    matches = list(re.finditer(r"^###\s+(?P<num>4\.\d+)\s+(?P<title>.+?)\s*$", tail, re.MULTILINE))
    profiles: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tail)
        profiles.append({"title": match.group("title"), "body": tail[start:end].strip()})
    return profiles


def _context_features(raw: str, motive_classes: Iterable[str]) -> FeatureSet:
    motive_text = " ".join(motive_classes)
    return extract_features(f"{raw}\n{motive_text}", extra_terms=motive_classes)


def _dedupe_context_events(events: Iterable[ContextEvent]) -> list[ContextEvent]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[ContextEvent] = []
    for event in events:
        key = (event.context_type, event.date, event.title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def _trim_engine_summary(body: str) -> str:
    marker = "\n## Engine-facing summary table"
    if marker in body:
        return body.split(marker, 1)[0].strip()
    return body


def _canonical_field_name(name: str) -> str:
    return _strip_markdown(name).lower().rstrip(".")


def _split_motive_classes(value: str) -> tuple[str, ...]:
    parts = re.split(r"[/,]|\s+\+\s+", value)
    return tuple(part.strip().upper() for part in parts if part.strip())


def _extract_urls(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(url.rstrip(".,") for url in URL_RE.findall(text)))


def _extract_first_date(text: str) -> str:
    patterns = (
        r"\b\d{4}-\d{2}-\d{2}(?:\s+to\s+\d{2})?\b",
        r"\b\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\b",
        r"\b[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}\b",
        r"\b[A-Z][a-z]+\s+\d{4}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def _extract_labeled_value(text: str, label: str) -> str:
    match = re.search(rf"^\s*-\s+\*\*{re.escape(label)}:\*\*\s*(.+)$", text, re.MULTILINE)
    return _strip_markdown(match.group(1)) if match else ""


def _first_nonempty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _preview(text: str, *, limit: int = 400) -> str:
    cleaned = _strip_markdown(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def _looks_like_date_cell(value: str) -> bool:
    value = _strip_markdown(value)
    if not value or value.startswith("---"):
        return False
    if value.upper() in {"MAY 2026", "JUNE 2026", "JULY 2026", "AUGUST 2026", "SEPTEMBER 2026", "OCTOBER 2026", "NOVEMBER 2026"}:
        return False
    if re.search(r"\b\d{4}(?:-\d{2})?(?:-\d{2})?\b", value):
        return True
    if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b", value, re.IGNORECASE):
        return True
    return False


def _is_table_header_or_rule(cells: list[str]) -> bool:
    lowered = [cell.lower() for cell in cells]
    if all(set(cell) <= {"-", ":"} for cell in cells):
        return True
    header_words = {"date", "event", "source", "#", "case", "actor", "target", "defendant", "status", "section"}
    return bool(lowered and lowered[0] in header_words)


def _strip_markdown(value: str) -> str:
    value = value.replace("**", "").replace("`", "")
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 \2", value)
    value = re.sub(r"<([^>]+)>", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
