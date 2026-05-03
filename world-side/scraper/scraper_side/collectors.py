"""Collectors for official/local JSON feeds that emit sanitized records."""

from __future__ import annotations

from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import html
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .catalog import CatalogEntry, DEFAULT_CISA_KEV_URL, normalize_collector
from .records import SanitizedRecord, make_source_ref, stable_id, utc_now


ALLOWED_LIVE_HOSTS = {
    "api.first.org",
    "www.first.org",
    "www.cisa.gov",
    "cisa.gov",
    "travel.state.gov",
    "www.justice.gov",
    "justice.gov",
    "www.federalregister.gov",
    "www.nhc.noaa.gov",
    "fortiguard.com",
    "www.fortiguard.com",
    "fortiguard.fortinet.com",
    "www.ivanti.com",
    "services.nvd.nist.gov",
    "nvd.nist.gov",
}

JSON_COLLECTORS = {
    "cisa_kev",
    "nvd_cve",
    "first_epss",
    "doj_press_releases",
    "federal_register_documents",
    "sanitized_json",
}

TEXT_COLLECTORS = {
    "official_rss",
}


def collect_records(
    entries: Iterable[CatalogEntry],
    *,
    live: bool = False,
    limit: int | None = None,
    since: date | None = None,
    timeout: float = 20.0,
) -> list[SanitizedRecord]:
    """Collect and sanitize records from catalog entries."""

    records: list[SanitizedRecord] = []
    for entry in entries:
        records.extend(
            collect_entry(
                entry,
                live=live,
                limit=_remaining(limit, records),
                since=since,
                timeout=timeout,
            )
        )
        if limit is not None and len(records) >= limit:
            return records[:limit]
    return records


def collect_entry(
    entry: CatalogEntry,
    *,
    live: bool = False,
    limit: int | None = None,
    since: date | None = None,
    timeout: float = 20.0,
) -> list[SanitizedRecord]:
    collector = normalize_collector(entry.collector)
    data = _load_entry_payload(entry, collector=collector, live=live, timeout=timeout)
    if collector == "cisa_kev":
        records = collect_cisa_kev(data, entry)
    elif collector == "nvd_cve":
        records = collect_nvd_cve(data, entry)
    elif collector == "first_epss":
        records = collect_first_epss(data, entry)
    elif collector == "official_rss":
        records = collect_official_rss(data, entry)
    elif collector == "doj_press_releases":
        records = collect_doj_press_releases(data, entry)
    elif collector == "federal_register_documents":
        records = collect_federal_register_documents(data, entry)
    elif collector == "sanitized_json":
        records = collect_sanitized_json(data)
    else:
        raise ValueError(f"{entry.name}: unsupported collector {entry.collector}")
    return _filter_records(records, limit=limit, since=since)


def collect_cisa_kev(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect records from CISA Known Exploited Vulnerabilities JSON."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: CISA KEV JSON must be an object")
    vulnerabilities = data.get("vulnerabilities", [])
    if not isinstance(vulnerabilities, list):
        raise ValueError(f"{entry.name}: vulnerabilities must be a list")

    feed_url = entry.url or DEFAULT_CISA_KEV_URL
    records: list[SanitizedRecord] = []
    for item in vulnerabilities:
        if not isinstance(item, Mapping):
            continue
        cve_id = _clean_cve(item.get("cveID") or item.get("cve_id"))
        if not cve_id:
            continue
        date_added = _date_string(item.get("dateAdded")) or _date_string(data.get("dateReleased")) or _today()
        due_date = _date_string(item.get("dueDate"))
        vendor = _safe_label(item.get("vendorProject"), fallback="affected vendor")
        product = _safe_label(item.get("product"), fallback="affected product")
        cwes = _safe_cwes(item.get("cwes"))
        vector_class = _vector_from_terms(
            " ".join(
                str(part or "")
                for part in (
                    item.get("vulnerabilityName"),
                    vendor,
                    product,
                    " ".join(cwes),
                )
            )
        )
        ransomware_use = _safe_label(item.get("knownRansomwareCampaignUse"), fallback="Unknown")
        motive = (
            "ransomware campaign use reported by CISA"
            if ransomware_use.lower() == "known"
            else "official defensive prioritization signal"
        )
        summary = _cisa_summary(cve_id, vendor, product, date_added, due_date)
        record = SanitizedRecord.from_mapping(
            {
                "record_id": f"cisa_kev_{_slug(cve_id)}_{date_added.replace('-', '')}",
                "observed_at": f"{date_added}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "US / global",
                "target_sector": f"organizations using {vendor} {product}",
                "vector_class": vector_class,
                "motive_hint": motive,
                "confidence": "high",
                "summary": summary,
                "source_ref": make_source_ref(
                    source_id=f"src_cisa_kev_{_slug(cve_id)}",
                    label="CISA Known Exploited Vulnerabilities Catalog",
                    url=feed_url,
                    date_value=date_added,
                    supports=f"official CISA known-exploited status for {cve_id}",
                ),
                "tags": _record_tags(["official", "kev", "cisa", *cwes, *_keyword_tags(vector_class)]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
        records.append(record)
    return records


def collect_nvd_cve(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect records from NVD CVE API 2.0 JSON without raw descriptions."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: NVD JSON must be an object")
    vulnerabilities = data.get("vulnerabilities", [])
    if not isinstance(vulnerabilities, list):
        raise ValueError(f"{entry.name}: vulnerabilities must be a list")

    records: list[SanitizedRecord] = []
    for wrapper in vulnerabilities:
        if not isinstance(wrapper, Mapping):
            continue
        cve = wrapper.get("cve", {})
        if not isinstance(cve, Mapping):
            continue
        cve_id = _clean_cve(cve.get("id"))
        if not cve_id:
            continue
        published = _date_string(cve.get("published")) or _today()
        severity = _nvd_severity(cve)
        cwes = _nvd_cwes(cve)
        vendor_product = _nvd_vendor_product(cve)
        vector_class = _vector_from_terms(" ".join([*cwes, severity, vendor_product]))
        summary = (
            f"NVD lists {cve_id} as public vulnerability metadata"
            f"{_with_phrase('severity', severity)}; published {published}. "
            "Descriptions, references, and actionable exploit details are omitted."
        )
        record = SanitizedRecord.from_mapping(
            {
                "record_id": f"nvd_cve_{_slug(cve_id)}_{published.replace('-', '')}",
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type or "official_government",
                "collection_tier": entry.collection_tier or "technical_chatter",
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": vendor_product or "organizations using affected public software",
                "vector_class": vector_class,
                "motive_hint": "public vulnerability metadata signal",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    source_id=f"src_nvd_{_slug(cve_id)}",
                    label=f"NVD record {cve_id}",
                    url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    date_value=published,
                    supports=f"official NVD public metadata for {cve_id}",
                ),
                "tags": _record_tags(["official", "nvd", *cwes, *_keyword_tags(vector_class)]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
        records.append(record)
    return records


def collect_first_epss(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect safe FIRST EPSS probability metadata."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: FIRST EPSS JSON must be an object")
    values = data.get("data", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: FIRST EPSS data must be a list")

    feed_url = entry.url or "https://api.first.org/data/v1/epss"
    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        cve_id = _clean_cve(item.get("cve"))
        if not cve_id:
            continue
        date_value = _date_string(item.get("date")) or _today()
        epss = _float_score(item.get("epss"))
        percentile = _float_score(item.get("percentile"))
        confidence = _score_confidence(epss, percentile)
        summary = (
            f"FIRST EPSS reports {cve_id} with exploit-probability score "
            f"{epss:.4f} and percentile {percentile:.4f} on {date_value}. "
            "This is defensive prioritization metadata; exploit details are omitted."
        )
        record = SanitizedRecord.from_mapping(
            {
                "record_id": f"first_epss_{_slug(cve_id)}_{date_value.replace('-', '')}",
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "organizations affected by public CVE exposure",
                "vector_class": "exploit-likelihood scoring signal",
                "motive_hint": "public exploit-probability prioritization",
                "confidence": confidence,
                "summary": summary,
                "source_ref": make_source_ref(
                    source_id=f"src_first_epss_{_slug(cve_id)}",
                    label="FIRST EPSS API",
                    url=feed_url,
                    date_value=date_value,
                    supports=f"EPSS exploit-probability metadata for {cve_id}",
                ),
                "tags": _record_tags(["epss", "first", "cve", "exploit_probability"]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
        records.append(record)
    return records


def collect_official_rss(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect safe title/link/date metadata from an RSS or Atom feed."""

    if not isinstance(data, str):
        raise ValueError(f"{entry.name}: RSS payload must be text")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"{entry.name}: invalid RSS/Atom XML") from exc

    feed_label = _option(entry, "display_label") or _safe_label(entry.name.replace("_", " "), fallback="Public feed")
    records: list[SanitizedRecord] = []
    for idx, item in enumerate(_feed_items(root), start=1):
        title = _safe_label(_feed_text(item, "title"), fallback=f"{feed_label} item")
        link = _safe_url(_feed_link(item)) or entry.url
        date_value = _feed_date(item)
        summary = (
            f"{feed_label} public feed item: {title}. "
            "Only headline, date, and source link are retained; raw body text is omitted."
        )
        record = SanitizedRecord.from_mapping(
            {
                "record_id": stable_id("rss", entry.name, link, title, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": _option(entry, "actor_hint") or "unknown actors",
                "region_hint": _option(entry, "region_hint") or "global",
                "target_sector": _option(entry, "target_sector") or "public-sector and enterprise defenders",
                "vector_class": _option(entry, "vector_class") or "public advisory or context signal",
                "motive_hint": _option(entry, "motive_hint") or "public timing context",
                "confidence": _option(entry, "confidence") or "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label=feed_label,
                    url=link,
                    date_value=date_value,
                    supports=f"public feed metadata for {title}",
                ),
                "tags": _record_tags([entry.name, *_keyword_tags(title), *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{idx}",
        )
        records.append(record)
    return records


def collect_doj_press_releases(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect title/date/link metadata from the public DOJ press-release API."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: DOJ press-release JSON must be an object")
    values = data.get("results", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: DOJ results must be a list")

    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        title = _safe_label(item.get("title"), fallback="DOJ press release")
        date_value = _epoch_or_date(item.get("date")) or _today()
        link = _safe_url(item.get("url")) or entry.url
        summary = (
            f"DOJ public press-release metadata: {title}. "
            "Only title, date, and source link are retained; body text is omitted."
        )
        record = SanitizedRecord.from_mapping(
            {
                "record_id": stable_id("doj", title, link, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "US / global",
                "target_sector": "organizations affected by cyber-linked legal pressure",
                "vector_class": "legal-pressure timing signal",
                "motive_hint": "indictment or enforcement timing context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="U.S. Department of Justice press releases API",
                    url=link,
                    date_value=date_value,
                    supports=f"DOJ public metadata for {title}",
                ),
                "tags": _record_tags(["doj", "legal_pressure", "indictment", *_keyword_tags(title)]),
            },
            source_name=f"{entry.name}:{title}",
        )
        records.append(record)
    return records


def collect_federal_register_documents(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect metadata from Federal Register document search results."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: Federal Register JSON must be an object")
    values = data.get("results", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: Federal Register results must be a list")

    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        title = _safe_label(item.get("title"), fallback="Federal Register document")
        date_value = _date_string(item.get("publication_date")) or _today()
        link = _safe_url(item.get("html_url")) or _safe_url(item.get("json_url")) or entry.url
        agencies = _agency_labels(item)
        target = "sanctions, export-control, and federal policy watchers"
        if agencies:
            target = f"{target}; agencies: {', '.join(agencies[:3])}"
        summary = (
            f"Federal Register public document metadata: {title}. "
            "Only metadata is retained for sanctions/export-control timing context."
        )
        record = SanitizedRecord.from_mapping(
            {
                "record_id": stable_id("federal_register", title, link, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "US / global",
                "target_sector": target,
                "vector_class": "policy-pressure timing signal",
                "motive_hint": "sanctions or export-control pressure",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="Federal Register API",
                    url=link,
                    date_value=date_value,
                    supports=f"Federal Register public metadata for {title}",
                ),
                "tags": _record_tags(["federal_register", "sanctions", "policy_pressure", *_keyword_tags(title)]),
            },
            source_name=f"{entry.name}:{title}",
        )
        records.append(record)
    return records


def collect_sanitized_json(data: Any) -> list[SanitizedRecord]:
    """Validate pre-sanitized JSON or JSONL-like arrays as SanitizedRecord."""

    if isinstance(data, Mapping) and isinstance(data.get("records"), list):
        values = data["records"]
    elif isinstance(data, list):
        values = data
    else:
        values = [data]
    return [
        SanitizedRecord.from_mapping(value, source_name=f"sanitized_json:{idx}")
        for idx, value in enumerate(values, start=1)
        if isinstance(value, Mapping)
    ]


def load_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_official_json(url: str, *, timeout: float = 20.0) -> Any:
    return json.loads(fetch_public_text(url, timeout=timeout))


def fetch_public_text(url: str, *, timeout: float = 20.0) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("live collection only supports HTTPS URLs")
    if parsed.username or parsed.password:
        raise ValueError("live collection URL must not contain credentials")
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|password|secret)=", parsed.query, re.IGNORECASE):
        raise ValueError("live collection URL must not contain credential query parameters")
    host = parsed.hostname or ""
    if host.lower() not in ALLOWED_LIVE_HOSTS:
        allowed = ", ".join(sorted(ALLOWED_LIVE_HOSTS))
        raise ValueError(f"live collection host {host!r} is not allowed; allowed: {allowed}")
    request = Request(
        url,
        headers={
            "Accept": "application/json, application/rss+xml, application/xml, text/xml, text/html;q=0.5",
            "User-Agent": "ProphetScraperSide/0.1 official-json-collector",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _load_entry_payload(
    entry: CatalogEntry,
    *,
    collector: str,
    live: bool,
    timeout: float,
) -> Any:
    if entry.local_path is not None:
        if not entry.local_path.exists():
            raise FileNotFoundError(f"{entry.name}: local JSON not found: {entry.local_path}")
        if collector in TEXT_COLLECTORS or entry.format in {"rss", "xml", "csv", "html"}:
            return entry.local_path.read_text(encoding="utf-8")
        return load_json_path(entry.local_path)
    if live:
        if not entry.url:
            raise ValueError(f"{entry.name}: live collection requires a URL")
        text = fetch_public_text(entry.url, timeout=timeout)
        if collector in JSON_COLLECTORS or entry.format == "json":
            return json.loads(text)
        return text
    raise ValueError(
        f"{entry.name}: no local_path configured and live network is disabled; "
        "pass --live for official public HTTP collection"
    )


def _filter_records(
    records: list[SanitizedRecord],
    *,
    limit: int | None,
    since: date | None,
) -> list[SanitizedRecord]:
    filtered = [record for record in records if since is None or record.observed_date >= since]
    if limit is None:
        return filtered
    return filtered[:limit]


def _remaining(limit: int | None, records: list[SanitizedRecord]) -> int | None:
    if limit is None:
        return None
    return max(limit - len(records), 0)


def _feed_items(root: ET.Element) -> list[ET.Element]:
    items = root.findall(".//item")
    if items:
        return items
    atom_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    if atom_items:
        return atom_items
    return []


def _feed_text(item: ET.Element, name: str) -> str:
    child = item.find(name)
    if child is None:
        child = item.find(f"{{http://www.w3.org/2005/Atom}}{name}")
    if child is None or child.text is None:
        return ""
    return html.unescape(re.sub(r"\s+", " ", child.text)).strip()


def _feed_link(item: ET.Element) -> str:
    link = _feed_text(item, "link")
    if link:
        return link
    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None:
        href = atom_link.attrib.get("href", "")
        if href:
            return href
    return ""


def _feed_date(item: ET.Element) -> str:
    for key in ("pubDate", "published", "updated", "dc:date"):
        value = _feed_text(item, key)
        if not value:
            continue
        parsed = _rss_date(value) or _date_string(value)
        if parsed:
            return parsed
    return _today()


def _rss_date(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return ""
    if parsed.tzinfo is None:
        return parsed.date().isoformat()
    return parsed.astimezone(timezone.utc).date().isoformat()


def _epoch_or_date(value: Any) -> str:
    if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    return _date_string(value)


def _float_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(score, 1.0))


def _score_confidence(epss: float, percentile: float) -> str:
    if epss >= 0.5 or percentile >= 0.95:
        return "high"
    if epss >= 0.05 or percentile >= 0.75:
        return "medium"
    return "low"


def _safe_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    clean = value.strip()
    parsed = urlparse(clean)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return ""
    return clean


def _option(entry: CatalogEntry, key: str) -> str:
    value = entry.options.get(key)
    if isinstance(value, str):
        return _safe_label(value, fallback="")
    return ""


def _option_tags(entry: CatalogEntry) -> list[str]:
    value = entry.options.get("tags")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _agency_labels(item: Mapping[str, Any]) -> list[str]:
    agencies = item.get("agencies", [])
    if not isinstance(agencies, list):
        return []
    values: list[str] = []
    for agency in agencies:
        if not isinstance(agency, Mapping):
            continue
        name = _safe_label(agency.get("name"), fallback="")
        if name:
            values.append(name)
    return values


def _clean_cve(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    cve = value.strip().upper()
    if re.fullmatch(r"CVE-\d{4}-\d{4,}", cve):
        return cve
    return ""


def _date_string(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    text = value.strip()
    if "T" in text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return ""
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return ""


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_label(value: Any, *, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    clean = re.sub(r"\s+", " ", value).strip()
    clean = re.sub(r"[^A-Za-z0-9 .,&()/+_-]", "", clean)
    clean = clean[:100].strip()
    return clean or fallback


def _safe_cwes(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cwes: list[str] = []
    for item in value:
        if isinstance(item, str) and re.fullmatch(r"CWE-\d+", item.strip().upper()):
            cwe = item.strip().upper()
            if cwe not in cwes:
                cwes.append(cwe)
    return cwes[:5]


def _nvd_cwes(cve: Mapping[str, Any]) -> list[str]:
    cwes: list[str] = []
    for weakness in cve.get("weaknesses", []) or []:
        if not isinstance(weakness, Mapping):
            continue
        for desc in weakness.get("description", []) or []:
            if not isinstance(desc, Mapping):
                continue
            value = desc.get("value")
            if isinstance(value, str) and re.fullmatch(r"CWE-\d+", value.strip().upper()):
                cwe = value.strip().upper()
                if cwe not in cwes:
                    cwes.append(cwe)
    return cwes[:5]


def _nvd_severity(cve: Mapping[str, Any]) -> str:
    metrics = cve.get("metrics", {})
    if not isinstance(metrics, Mapping):
        return ""
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        values = metrics.get(key, [])
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, Mapping):
                continue
            cvss_data = item.get("cvssData", {})
            if not isinstance(cvss_data, Mapping):
                continue
            severity = item.get("baseSeverity") or cvss_data.get("baseSeverity")
            if isinstance(severity, str) and severity.strip():
                return severity.strip().lower()
    return ""


def _nvd_vendor_product(cve: Mapping[str, Any]) -> str:
    for configuration in cve.get("configurations", []) or []:
        if not isinstance(configuration, Mapping):
            continue
        for node in configuration.get("nodes", []) or []:
            if not isinstance(node, Mapping):
                continue
            for match in node.get("cpeMatch", []) or []:
                if not isinstance(match, Mapping):
                    continue
                criteria = match.get("criteria")
                if not isinstance(criteria, str):
                    continue
                parts = criteria.split(":")
                if len(parts) >= 6:
                    vendor = _safe_label(parts[3].replace("_", " "), fallback="")
                    product = _safe_label(parts[4].replace("_", " "), fallback="")
                    label = " ".join(part for part in (vendor, product) if part)
                    if label:
                        return f"organizations using {label}"
    return ""


def _vector_from_terms(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ("auth", "login", "cwe-287", "cwe-306")):
        return "identity or access-control vulnerability signal"
    if any(term in lower for term in ("edge", "vpn", "gateway", "firewall", "router", "appliance")):
        return "edge-appliance exposure signal"
    if any(term in lower for term in ("cwe-79", "cross-site scripting", "xss")):
        return "web application vulnerability signal"
    if any(term in lower for term in ("cwe-89", "sql")):
        return "data-layer vulnerability signal"
    if any(term in lower for term in ("cwe-78", "cwe-77", "command")):
        return "remote-action vulnerability signal"
    if any(term in lower for term in ("cwe-22", "path traversal", "directory traversal")):
        return "file-access vulnerability signal"
    return "public vulnerability signal"


def _keyword_tags(text: str) -> list[str]:
    lower = text.lower()
    tags: list[str] = []
    for tag, needles in {
        "identity": ("identity", "access-control", "auth"),
        "edge": ("edge", "appliance", "gateway", "vpn", "firewall"),
        "web": ("web", "application"),
        "data": ("data-layer",),
        "remote_action": ("remote-action",),
        "file_access": ("file-access",),
    }.items():
        if any(needle in lower for needle in needles):
            tags.append(tag)
    return tags


def _record_tags(values: Iterable[str]) -> list[str]:
    tags: list[str] = []
    for value in values:
        tag = _slug(value)
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:12]


def _cisa_summary(
    cve_id: str,
    vendor: str,
    product: str,
    date_added: str,
    due_date: str,
) -> str:
    due = f"; remediation due {due_date}" if due_date else ""
    return (
        f"CISA KEV lists {cve_id} affecting {vendor} {product} as known exploited; "
        f"added {date_added}{due}. This is an official defensive-prioritization "
        "signal and omits actionable exploit details, target names, and raw source text."
    )


def _with_phrase(label: str, value: str) -> str:
    if not value:
        return ""
    return f" with {label} {value}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
