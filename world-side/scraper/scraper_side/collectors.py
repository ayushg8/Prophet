"""Collectors for official/local JSON feeds that emit sanitized records."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET
import zipfile

from .catalog import CatalogEntry, DEFAULT_CISA_KEV_URL, normalize_collector
from .records import RecordValidationError, SanitizedRecord, make_source_ref, stable_id, utc_now


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
    "sanctionslistservice.ofac.treas.gov",
    "api.github.com",
    "api.msrc.microsoft.com",
    "www.openwall.com",
    "www.reddit.com",
    "reddit.com",
    "api.reliefweb.int",
    "api.gdeltproject.org",
    "earthquake.usgs.gov",
    "www.gdacs.org",
    "unit42.paloaltonetworks.com",
    "blog.talosintelligence.com",
    "cloud.google.com",
    "docs.cloud.google.com",
    "www.cert.europa.eu",
    "cert.europa.eu",
    "raw.githubusercontent.com",
    "github.com",
    "www.cve.org",
    "cve.org",
    "api.osv.dev",
    "osv-vulnerabilities.storage.googleapis.com",
    "access.redhat.com",
    "cwe.mitre.org",
    "capec.mitre.org",
    "attack.mitre.org",
    "d3fend.mitre.org",
}

JSON_COLLECTORS = {
    "cisa_kev",
    "nvd_cve",
    "first_epss",
    "doj_press_releases",
    "federal_register_documents",
    "github_advisories",
    "github_commits",
    "reddit_listing",
    "reliefweb_disasters",
    "gdelt_articles",
    "geojson_features",
    "microsoft_msrc_updates",
    "cve_delta_log",
    "cve_record_v5",
    "cisa_vulnrichment",
    "osv_vulnerabilities",
    "redhat_security_data",
    "attack_stix",
    "d3fend_ontology",
    "sanitized_json",
}

TEXT_COLLECTORS = {
    "official_rss",
    "ofac_sdn_csv",
    "html_link_index",
    "cwe_catalog",
    "capec_catalog",
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
    elif collector == "ofac_sdn_csv":
        records = collect_ofac_sdn_csv(data, entry)
    elif collector == "github_advisories":
        records = collect_github_advisories(data, entry)
    elif collector == "github_commits":
        records = collect_github_commits(data, entry)
    elif collector == "microsoft_msrc_updates":
        records = collect_microsoft_msrc_updates(data, entry)
    elif collector == "cve_delta_log":
        records = collect_cve_delta_log(data, entry)
    elif collector == "cve_record_v5":
        records = collect_cve_record_v5(data, entry)
    elif collector == "cisa_vulnrichment":
        records = collect_cisa_vulnrichment(data, entry)
    elif collector == "osv_vulnerabilities":
        records = collect_osv_vulnerabilities(data, entry)
    elif collector == "redhat_security_data":
        records = collect_redhat_security_data(data, entry)
    elif collector == "attack_stix":
        records = collect_attack_stix(data, entry)
    elif collector == "cwe_catalog":
        records = collect_cwe_catalog(data, entry)
    elif collector == "capec_catalog":
        records = collect_capec_catalog(data, entry)
    elif collector == "d3fend_ontology":
        records = collect_d3fend_ontology(data, entry)
    elif collector == "reddit_listing":
        records = collect_reddit_listing(data, entry)
    elif collector == "reliefweb_disasters":
        records = collect_reliefweb_disasters(data, entry)
    elif collector == "gdelt_articles":
        records = collect_gdelt_articles(data, entry)
    elif collector == "geojson_features":
        records = collect_geojson_features(data, entry)
    elif collector == "html_link_index":
        records = collect_html_link_index(data, entry)
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


def collect_ofac_sdn_csv(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect aggregate-only OFAC sanctions metadata from the public SDN CSV."""

    if not isinstance(data, str):
        raise ValueError(f"{entry.name}: OFAC CSV payload must be text")

    counts: dict[tuple[str, str], int] = {}
    for row in _csv_records(data):
        program = _safe_label(row.get("program"), fallback="unspecified sanctions program")
        entity_type = _safe_label(row.get("entity_type"), fallback="listed entity")
        key = (program, entity_type)
        counts[key] = counts.get(key, 0) + 1

    date_value = _today()
    records: list[SanitizedRecord] = []
    for (program, entity_type), count in sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    ):
        summary = (
            f"OFAC SDN public sanctions metadata includes {count} {entity_type} "
            f"record(s) under {program} as of {date_value}. Individual names, "
            "addresses, identifiers, and raw CSV rows are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("ofac_sdn", program, entity_type, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "sanctions-linked actors",
                "region_hint": "US / global",
                "target_sector": "sanctions, export-control, and cyber-policy watchers",
                "vector_class": "sanctions-pressure timing signal",
                "motive_hint": "sanctions or legal-pressure context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="OFAC Sanctions List Service",
                    url=entry.url,
                    date_value=date_value,
                    supports=f"aggregate OFAC SDN program/type count for {program}",
                ),
                "tags": _record_tags(["ofac", "sanctions", "legal_pressure", program, entity_type]),
            },
            source_name=f"{entry.name}:{program}:{entity_type}",
        )
    return records


def collect_github_advisories(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect safe metadata from the public GitHub Advisory Database API."""

    values = _json_items(data, entry.name, "GitHub advisories")
    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        ghsa_id = _safe_label(item.get("ghsa_id"), fallback="GitHub advisory")
        published = _date_string(item.get("published_at")) or _date_string(item.get("updated_at")) or _today()
        severity = _safe_label(item.get("severity"), fallback="unknown severity")
        title = _safe_label(item.get("summary"), fallback="public advisory metadata")
        cve_ids = _github_cve_ids(item)
        ecosystem = _github_ecosystem(item)
        link = _safe_url(item.get("html_url")) or _safe_url(item.get("url")) or entry.url
        cve_phrase = f" linked to {', '.join(cve_ids[:3])}" if cve_ids else ""
        ecosystem_phrase = f" in {ecosystem}" if ecosystem else ""
        summary = (
            f"GitHub Advisory Database metadata: {ghsa_id}{cve_phrase}, "
            f"{severity} severity{ecosystem_phrase}, published {published}. "
            "Descriptions, affected-version ranges, and exploit details are omitted."
        )
        vector_class = _vector_from_terms(" ".join([title, severity, ecosystem, *cve_ids]))
        _append_record(
            records,
            {
                "record_id": stable_id("github_advisory", ghsa_id, published),
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": ecosystem or "open-source package consumers",
                "vector_class": vector_class,
                "motive_hint": "public vulnerability disclosure timing context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="GitHub Advisory Database",
                    url=link,
                    date_value=published,
                    supports=f"public advisory metadata for {ghsa_id}",
                ),
                "tags": _record_tags(["github", "advisory", severity, ecosystem, *cve_ids, *_keyword_tags(vector_class)]),
            },
            source_name=f"{entry.name}:{ghsa_id}",
        )
    return records


def collect_github_commits(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect commit metadata only; never fetch repository file contents or diffs."""

    values = _json_items(data, entry.name, "GitHub commits")
    label = _option(entry, "display_label") or _safe_label(entry.name.replace("_", " "), fallback="GitHub repository")
    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        commit = item.get("commit", {})
        if not isinstance(commit, Mapping):
            continue
        commit_id = _safe_label(str(item.get("sha", ""))[:12], fallback="commit")
        headline = _safe_label(str(commit.get("message", "")).splitlines()[0], fallback="public repository update")
        published = _nested_date(commit, ("author", "date")) or _nested_date(commit, ("committer", "date")) or _today()
        link = _safe_url(item.get("html_url")) or entry.url
        vector_class = _vector_from_terms(headline)
        summary = (
            f"{label} public commit metadata: {headline}; dated {published}. "
            "Only commit headline, date, and source link are retained; diffs, files, "
            "template bodies, and payloads are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("github_commit", entry.name, commit_id, published),
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "defenders tracking public detection-template metadata",
                "vector_class": vector_class,
                "motive_hint": "public detection/disclosure timing context",
                "confidence": "low",
                "summary": summary,
                "source_ref": make_source_ref(
                    label=label,
                    url=link,
                    date_value=published,
                    supports=f"public commit metadata for {commit_id}",
                ),
                "tags": _record_tags([entry.name, "github", "commit_metadata", *_keyword_tags(headline)]),
            },
            source_name=f"{entry.name}:{commit_id}",
        )
    return records


def collect_microsoft_msrc_updates(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect Microsoft MSRC update-list metadata without CVRF document bodies."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: MSRC updates JSON must be an object")
    values = data.get("value", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: MSRC value must be a list")

    records: list[SanitizedRecord] = []
    for item in sorted(values, key=_msrc_sort_key, reverse=True):
        if not isinstance(item, Mapping):
            continue
        update_id = _safe_label(item.get("ID") or item.get("Alias"), fallback="MSRC update")
        title = _safe_label(item.get("DocumentTitle"), fallback="Microsoft security update")
        severity = _safe_label(item.get("Severity"), fallback="unspecified severity")
        current = _date_string(item.get("CurrentReleaseDate")) or _date_string(item.get("InitialReleaseDate")) or _today()
        initial = _date_string(item.get("InitialReleaseDate"))
        link = _safe_url(item.get("CvrfUrl")) or entry.url
        vector_class = _vector_from_terms(" ".join([update_id, title, severity]))
        initial_phrase = f"; initial release {initial}" if initial and initial != current else ""
        summary = (
            f"Microsoft MSRC public update metadata: {update_id} / {title}; "
            f"current release {current}{initial_phrase}; severity {severity}. "
            "Only update-list metadata is retained; CVRF bodies, product matrices, "
            "exploitability notes, and remediation details are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("microsoft_msrc", update_id, current),
                "observed_at": f"{current}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "organizations using Microsoft products",
                "vector_class": vector_class,
                "motive_hint": "public patch and advisory timing",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="Microsoft MSRC Security Update Guide CVRF API",
                    url=link,
                    date_value=current,
                    supports=f"public MSRC update-list metadata for {update_id}",
                ),
                "tags": _record_tags(["microsoft", "msrc", "patch_tuesday", severity, *_keyword_tags(vector_class)]),
            },
            source_name=f"{entry.name}:{update_id}",
        )
    return records


def collect_cve_delta_log(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect CVEProject cvelistV5 delta metadata without CVE record bodies."""

    batches = data if isinstance(data, list) else [data]
    max_records = _collector_item_limit(entry)
    records: list[SanitizedRecord] = []
    for batch in batches:
        if not isinstance(batch, Mapping):
            continue
        observed = _date_string(batch.get("fetchTime")) or _today()
        for change_type in ("new", "updated"):
            changes = batch.get(change_type, [])
            if not isinstance(changes, list):
                continue
            for item in changes:
                if len(records) >= max_records:
                    return records
                if not isinstance(item, Mapping):
                    continue
                cve_id = _clean_cve(item.get("cveId") or item.get("cveID"))
                if not cve_id:
                    continue
                updated = _date_string(item.get("dateUpdated")) or observed
                link = _safe_url(item.get("cveOrgLink")) or _safe_url(item.get("githubLink")) or entry.url
                summary = (
                    f"CVEProject cvelistV5 delta metadata marks {cve_id} as {change_type} "
                    f"on {updated}. Only CVE ID, update time, and public record link are "
                    "retained; CVE record text is omitted."
                )
                _append_record(
                    records,
                    {
                        "record_id": stable_id("cvelistv5_delta", cve_id, change_type, updated),
                        "observed_at": f"{updated}T00:00:00Z",
                        "source_type": entry.source_type,
                        "collection_tier": entry.collection_tier,
                        "actor_hint": "unknown actors",
                        "region_hint": "global",
                        "target_sector": "organizations tracking newly published CVE records",
                        "vector_class": "public vulnerability disclosure timing signal",
                        "motive_hint": "official CVE publication or update timing",
                        "confidence": "medium",
                        "summary": summary,
                        "source_ref": make_source_ref(
                            label="CVEProject cvelistV5 delta log",
                            url=link,
                            date_value=updated,
                            supports=f"cvelistV5 delta metadata for {cve_id}",
                        ),
                        "tags": _record_tags(["cve", "cvelistv5", change_type, "vulnerability_metadata"]),
                    },
                    source_name=f"{entry.name}:{cve_id}:{change_type}",
                )
    return records


def collect_cve_record_v5(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect safe metadata from CVE JSON 5 records."""

    records: list[SanitizedRecord] = []
    for item in _cve_record_items(data):
        if len(records) >= _collector_item_limit(entry):
            break
        cve_meta = item.get("cveMetadata", {})
        if not isinstance(cve_meta, Mapping):
            cve_meta = {}
        cve_id = _clean_cve(cve_meta.get("cveId") or item.get("id"))
        if not cve_id:
            continue
        updated = (
            _date_string(cve_meta.get("dateUpdated"))
            or _date_string(cve_meta.get("datePublished"))
            or _today()
        )
        products = _cve_record_products(item)
        cwes = _cve_record_cwes(item)
        vector_class = _vector_from_terms(" ".join([*products, *cwes]))
        product_phrase = f"; affected product family {', '.join(products[:3])}" if products else ""
        cwe_phrase = f"; weakness tags {', '.join(cwes[:3])}" if cwes else ""
        summary = (
            f"CVE JSON 5 metadata lists {cve_id} updated {updated}{product_phrase}{cwe_phrase}. "
            "Descriptions, references, and actionable details are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("cve_json_v5", entry.name, cve_id, updated),
                "observed_at": f"{updated}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": _target_from_products(products) or "organizations using affected public software",
                "vector_class": vector_class,
                "motive_hint": "public vulnerability disclosure timing context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label=_option(entry, "display_label") or "CVE JSON 5 record",
                    url=_cve_record_url(cve_id, entry),
                    date_value=updated,
                    supports=f"CVE JSON 5 metadata for {cve_id}",
                ),
                "tags": _record_tags(["cve", "json_v5", *cwes, *products, *_keyword_tags(vector_class)]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
    return records


def collect_cisa_vulnrichment(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect CISA Vulnrichment ADP metadata without raw CVE text."""

    records: list[SanitizedRecord] = []
    for item in _cve_record_items(data):
        if len(records) >= _collector_item_limit(entry):
            break
        cve_meta = item.get("cveMetadata", {})
        if not isinstance(cve_meta, Mapping):
            cve_meta = {}
        cve_id = _clean_cve(cve_meta.get("cveId") or item.get("id"))
        if not cve_id:
            continue
        updated = _date_string(cve_meta.get("dateUpdated")) or _date_string(cve_meta.get("datePublished")) or _today()
        cwes = _cve_record_cwes(item)
        adp_labels = _cve_adp_labels(item)
        cwe_phrase = f"; CISA-linked weakness tags {', '.join(cwes[:3])}" if cwes else ""
        adp_phrase = f"; ADP containers {', '.join(adp_labels[:2])}" if adp_labels else ""
        summary = (
            f"CISA Vulnrichment metadata enriches {cve_id} with ADP/SSVC context "
            f"updated {updated}{cwe_phrase}{adp_phrase}. Descriptions, examples, and "
            "record references are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("cisa_vulnrichment", cve_id, updated),
                "observed_at": f"{updated}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "US / global",
                "target_sector": "public-sector and enterprise defenders tracking CISA-enriched CVEs",
                "vector_class": _vector_from_terms(" ".join(cwes)),
                "motive_hint": "official vulnerability enrichment and triage timing",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="CISA Vulnrichment repository",
                    url=_cve_record_url(cve_id, entry),
                    date_value=updated,
                    supports=f"CISA Vulnrichment metadata for {cve_id}",
                ),
                "tags": _record_tags(["cisa", "vulnrichment", "adp", "ssvc", *cwes]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
    return records


def collect_osv_vulnerabilities(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect OSV vulnerability metadata without details, events, or raw ranges."""

    values = [data] if isinstance(data, Mapping) and data.get("id") else _json_items(
        data,
        entry.name,
        "OSV vulnerabilities",
    )
    records: list[SanitizedRecord] = []
    for item in values:
        if len(records) >= _collector_item_limit(entry):
            break
        if not isinstance(item, Mapping):
            continue
        osv_id = _safe_label(item.get("id"), fallback="")
        if not osv_id:
            continue
        published = _date_string(item.get("published")) or _date_string(item.get("modified")) or _today()
        aliases = _osv_aliases(item)
        ecosystems = _osv_ecosystems(item)
        severity = _osv_severity(item)
        cve_phrase = f" linked to {', '.join(aliases[:3])}" if aliases else ""
        ecosystem_phrase = f" across {', '.join(ecosystems[:3])}" if ecosystems else ""
        severity_phrase = f"; severity metadata {severity}" if severity else ""
        summary = (
            f"OSV vulnerability metadata lists {osv_id}{cve_phrase}{ecosystem_phrase}; "
            f"published {published}{severity_phrase}. Details, event ranges, and references are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("osv", osv_id, published),
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "open-source package consumers",
                "vector_class": _vector_from_terms(" ".join([osv_id, *aliases, *ecosystems, severity])),
                "motive_hint": "open-source vulnerability disclosure timing",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="OSV vulnerability database",
                    url=_safe_url(item.get("url")) or entry.url,
                    date_value=published,
                    supports=f"OSV metadata for {osv_id}",
                ),
                "tags": _record_tags(["osv", "open_source", severity, *aliases, *ecosystems]),
            },
            source_name=f"{entry.name}:{osv_id}",
        )
    return records


def collect_redhat_security_data(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect Red Hat Security Data API CVE metadata."""

    values = [data] if isinstance(data, Mapping) and (data.get("CVE") or data.get("cve")) else _json_items(
        data,
        entry.name,
        "Red Hat Security Data CVEs",
    )
    records: list[SanitizedRecord] = []
    for item in values:
        if len(records) >= _collector_item_limit(entry):
            break
        if not isinstance(item, Mapping):
            continue
        cve_id = _clean_cve(item.get("CVE") or item.get("cve"))
        if not cve_id:
            continue
        published = _date_string(item.get("public_date")) or _today()
        severity = _safe_label(item.get("severity"), fallback="unspecified")
        cwe = _clean_cwe(item.get("CWE") or item.get("cwe"))
        packages = _redhat_packages(item)
        package_phrase = f"; package families {', '.join(packages[:3])}" if packages else ""
        cwe_phrase = f"; weakness tag {cwe}" if cwe else ""
        summary = (
            f"Red Hat Security Data metadata lists {cve_id} with {severity} severity; "
            f"public date {published}{cwe_phrase}{package_phrase}. Advisory bodies and "
            "scoring vectors are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("redhat_security_data", cve_id, published),
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "organizations using Red Hat product families",
                "vector_class": _vector_from_terms(" ".join([severity, cwe, *packages])),
                "motive_hint": "vendor vulnerability disclosure and patch timing",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="Red Hat Security Data API",
                    url=_safe_url(item.get("resource_url")) or entry.url,
                    date_value=published,
                    supports=f"Red Hat Security Data metadata for {cve_id}",
                ),
                "tags": _record_tags(["redhat", "vendor_advisory", severity, cwe, *packages]),
            },
            source_name=f"{entry.name}:{cve_id}",
        )
    return records


def collect_attack_stix(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect MITRE ATT&CK STIX object metadata without procedure text."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: ATT&CK STIX JSON must be an object")
    values = data.get("objects", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: ATT&CK STIX objects must be a list")

    records: list[SanitizedRecord] = []
    allowed_types = {"attack-pattern", "course-of-action", "intrusion-set", "malware", "tool"}
    for item in values:
        if len(records) >= _collector_item_limit(entry):
            break
        if not isinstance(item, Mapping) or item.get("type") not in allowed_types:
            continue
        if item.get("revoked") is True or item.get("x_mitre_deprecated") is True:
            continue
        name = _safe_label(item.get("name"), fallback="")
        if not name:
            continue
        stix_type = _safe_label(item.get("type"), fallback="stix object")
        external_id, link = _attack_external_ref(item)
        observed = _date_string(item.get("modified")) or _date_string(item.get("created")) or _today()
        tactics = _attack_tactics(item)
        tactic_phrase = f"; tactics {', '.join(tactics[:3])}" if tactics else ""
        identifier = external_id or str(item.get("id") or name)
        summary = (
            f"MITRE ATT&CK STIX metadata lists {identifier} {name} as {stix_type}"
            f"{tactic_phrase}; modified {observed}. Procedure text and relationship bodies are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("attack_stix", identifier, observed),
                "observed_at": f"{observed}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "documented adversary behavior taxonomy",
                "region_hint": "global",
                "target_sector": "defenders mapping ATT&CK behavior to defensive priorities",
                "vector_class": "adversary behavior taxonomy signal",
                "motive_hint": "public adversary-behavior knowledge-base context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="MITRE ATT&CK STIX data",
                    url=link or entry.url,
                    date_value=observed,
                    supports=f"ATT&CK STIX metadata for {identifier}",
                ),
                "tags": _record_tags(["attack", "stix", stix_type, identifier, *tactics]),
            },
            source_name=f"{entry.name}:{identifier}",
        )
    return records


def collect_cwe_catalog(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect MITRE CWE weakness taxonomy metadata from XML."""

    if not isinstance(data, str):
        raise ValueError(f"{entry.name}: CWE catalog payload must be XML text")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"{entry.name}: invalid CWE XML") from exc

    date_value = _date_string(root.attrib.get("Date")) or _today()
    records: list[SanitizedRecord] = []
    for weakness in _xml_elements(root, "Weakness"):
        if len(records) >= _collector_item_limit(entry):
            break
        if weakness.attrib.get("Status", "").lower() == "deprecated":
            continue
        cwe_id = _clean_cwe(f"CWE-{weakness.attrib.get('ID', '')}")
        name = _safe_label(weakness.attrib.get("Name"), fallback="")
        if not cwe_id or not name:
            continue
        summary = (
            f"MITRE CWE catalog lists {cwe_id} {name} as software weakness taxonomy "
            f"metadata as of {date_value}. Extended descriptions, examples, and references are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("mitre_cwe", cwe_id, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "software weakness taxonomy",
                "region_hint": "global",
                "target_sector": "defenders mapping software weakness classes",
                "vector_class": _vector_from_terms(f"{cwe_id} {name}"),
                "motive_hint": "public vulnerability-class taxonomy context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="MITRE CWE catalog",
                    url=entry.url,
                    date_value=date_value,
                    supports=f"CWE taxonomy metadata for {cwe_id}",
                ),
                "tags": _record_tags(["mitre", "cwe", cwe_id, *_keyword_tags(name)]),
            },
            source_name=f"{entry.name}:{cwe_id}",
        )
    return records


def collect_capec_catalog(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect MITRE CAPEC attack-pattern taxonomy metadata from XML."""

    if not isinstance(data, str):
        raise ValueError(f"{entry.name}: CAPEC catalog payload must be XML text")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"{entry.name}: invalid CAPEC XML") from exc

    date_value = _date_string(root.attrib.get("Date")) or _today()
    records: list[SanitizedRecord] = []
    for pattern in _xml_elements(root, "Attack_Pattern"):
        if len(records) >= _collector_item_limit(entry):
            break
        capec_id = _safe_label(f"CAPEC-{pattern.attrib.get('ID', '')}", fallback="")
        name = _safe_label(pattern.attrib.get("Name"), fallback="")
        abstraction = _safe_label(pattern.attrib.get("Abstraction"), fallback="pattern")
        if not capec_id or not name:
            continue
        summary = (
            f"MITRE CAPEC catalog lists {capec_id} {name} as {abstraction} "
            f"attack-pattern taxonomy metadata as of {date_value}. Execution flows and examples are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("mitre_capec", capec_id, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "attack-pattern taxonomy",
                "region_hint": "global",
                "target_sector": "defenders mapping attack-pattern classes",
                "vector_class": "attack-pattern taxonomy signal",
                "motive_hint": "public attack-pattern taxonomy context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="MITRE CAPEC catalog",
                    url=entry.url,
                    date_value=date_value,
                    supports=f"CAPEC taxonomy metadata for {capec_id}",
                ),
                "tags": _record_tags(["mitre", "capec", capec_id, abstraction]),
            },
            source_name=f"{entry.name}:{capec_id}",
        )
    return records


def collect_d3fend_ontology(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect MITRE D3FEND defensive taxonomy metadata from JSON-LD."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: D3FEND JSON-LD must be an object")
    values = data.get("@graph", [])
    if not isinstance(values, list):
        raise ValueError(f"{entry.name}: D3FEND @graph must be a list")

    date_value = _today()
    records: list[SanitizedRecord] = []
    for item in values:
        if len(records) >= _collector_item_limit(entry):
            break
        if not isinstance(item, Mapping):
            continue
        d3fend_id = _safe_label(_jsonld_text(item.get("d3f:d3fend-id")), fallback="")
        label = _safe_label(_jsonld_text(item.get("rdfs:label")), fallback="")
        if not d3fend_id or not label:
            continue
        summary = (
            f"MITRE D3FEND ontology lists {label} ({d3fend_id}) as defensive taxonomy "
            "metadata. Definitions and inferred relationships are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("mitre_d3fend", d3fend_id, label),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "defensive technique taxonomy",
                "region_hint": "global",
                "target_sector": "defenders mapping countermeasure options",
                "vector_class": "defensive taxonomy signal",
                "motive_hint": "public countermeasure taxonomy context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="MITRE D3FEND ontology",
                    url=entry.url,
                    date_value=date_value,
                    supports=f"D3FEND taxonomy metadata for {d3fend_id}",
                ),
                "tags": _record_tags(["mitre", "d3fend", d3fend_id, label]),
            },
            source_name=f"{entry.name}:{d3fend_id}",
        )
    return records


def collect_reddit_listing(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect public Reddit listing metadata without authors, comments, or bodies."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: Reddit listing JSON must be an object")
    listing = data.get("data", {})
    if not isinstance(listing, Mapping):
        raise ValueError(f"{entry.name}: Reddit listing data must be an object")
    children = listing.get("children", [])
    if not isinstance(children, list):
        raise ValueError(f"{entry.name}: Reddit listing children must be a list")

    records: list[SanitizedRecord] = []
    for child in children:
        if not isinstance(child, Mapping):
            continue
        item = child.get("data", {})
        if not isinstance(item, Mapping):
            continue
        post_id = _safe_label(item.get("id"), fallback=stable_id("reddit", str(item.get("permalink", ""))))
        title = _safe_label(item.get("title"), fallback="public security-community post")
        published = _epoch_or_date(item.get("created_utc")) or _today()
        permalink = item.get("permalink")
        link = ""
        if isinstance(permalink, str) and permalink.startswith("/"):
            link = _safe_url(urljoin("https://www.reddit.com", permalink))
        link = link or _safe_url(item.get("url")) or entry.url
        vector_class = _vector_from_terms(title)
        summary = (
            f"Reddit public security-community listing metadata: {title}; posted {published}. "
            "Only title, public link, and timestamp are retained; authors, comments, "
            "self text, and raw thread exports are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("reddit_public", post_id, published),
                "observed_at": f"{published}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "unknown actors",
                "region_hint": "global",
                "target_sector": "public-sector and enterprise defenders",
                "vector_class": vector_class,
                "motive_hint": "public community chatter timing context",
                "confidence": "low",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="Reddit public security-community listing",
                    url=link,
                    date_value=published,
                    supports=f"public listing metadata for post {post_id}",
                ),
                "tags": _record_tags(["reddit", "public_chatter", *_keyword_tags(title), *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{post_id}",
        )
    return records


def collect_reliefweb_disasters(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect public ReliefWeb disaster metadata as coarse instability context."""

    values = _json_items(data, entry.name, "ReliefWeb disasters")
    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        fields = item.get("fields", item)
        if not isinstance(fields, Mapping):
            continue
        disaster_id = _safe_label(str(item.get("id") or fields.get("id") or ""), fallback=stable_id("reliefweb", json.dumps(fields, sort_keys=True, default=str)))
        name = _safe_label(fields.get("name"), fallback="ReliefWeb disaster")
        date_value = _reliefweb_date(fields.get("date")) or _today()
        countries = _label_list(fields.get("country"), "name")
        disaster_types = _label_list(fields.get("type"), "name")
        status = _safe_label(fields.get("status"), fallback="active or recently updated")
        link = _safe_url(fields.get("url")) or _safe_url(item.get("href")) or entry.url
        region = " / ".join(countries[:3]) if countries else "global"
        sector = "critical infrastructure and continuity planners"
        type_phrase = ", ".join(disaster_types[:3]) if disaster_types else "crisis"
        summary = (
            f"ReliefWeb public disaster metadata: {name}; {type_phrase}; "
            f"status {status}; updated {date_value}. Only crisis metadata is retained; "
            "reports, attachments, and personal data are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("reliefweb_disaster", disaster_id, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "environmental or civil-contingency pressure",
                "region_hint": region,
                "target_sector": sector,
                "vector_class": "infrastructure-stress context signal",
                "motive_hint": "crisis-window timing context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="ReliefWeb disasters API",
                    url=link,
                    date_value=date_value,
                    supports=f"public disaster metadata for {name}",
                ),
                "tags": _record_tags(["reliefweb", "disaster", "infrastructure_stress", *countries, *disaster_types, *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{disaster_id}",
        )
    return records


def collect_gdelt_articles(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect public GDELT article-list metadata without article bodies."""

    values = _json_items(data, entry.name, "GDELT articles")
    records: list[SanitizedRecord] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        title = _safe_label(item.get("title"), fallback="GDELT article metadata")
        date_value = _date_string(item.get("seendate")) or _date_string(item.get("date")) or _today()
        link = _safe_url(item.get("url")) or entry.url
        country = _safe_label(item.get("sourcecountry") or item.get("sourceCountry"), fallback="global")
        domain = _safe_label(item.get("domain"), fallback="public news source")
        language = _safe_label(item.get("language"), fallback="unknown language")
        vector_class = _vector_from_terms(title)
        summary = (
            f"GDELT public news metadata: {title}; source country {country}; "
            f"domain {domain}; seen {date_value}. Only title/date/source metadata is "
            "retained; article bodies and images are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("gdelt_article", link, title, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "public news-cycle pressure",
                "region_hint": country,
                "target_sector": "government, critical infrastructure, and enterprise defenders",
                "vector_class": _option(entry, "vector_class") or vector_class,
                "motive_hint": "news-cycle and geopolitical timing context",
                "confidence": "low",
                "summary": summary,
                "source_ref": make_source_ref(
                    label="GDELT DOC API article list",
                    url=link,
                    date_value=date_value,
                    supports=f"public GDELT article metadata from {domain}",
                ),
                "tags": _record_tags(["gdelt", "news", country, language, *_keyword_tags(title), *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{title}",
        )
    return records


def collect_geojson_features(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect public GeoJSON feature metadata for infrastructure-stress signals."""

    if not isinstance(data, Mapping):
        raise ValueError(f"{entry.name}: GeoJSON payload must be an object")
    features = data.get("features", [])
    if not isinstance(features, list):
        raise ValueError(f"{entry.name}: GeoJSON features must be a list")

    records: list[SanitizedRecord] = []
    for idx, feature in enumerate(features, start=1):
        if not isinstance(feature, Mapping):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, Mapping):
            continue
        event_id = _safe_label(str(feature.get("id") or properties.get("code") or idx), fallback=f"feature {idx}")
        title = _safe_label(properties.get("title") or properties.get("place"), fallback="GeoJSON public event")
        date_value = _millis_or_date(properties.get("time")) or _date_string(properties.get("updated")) or _today()
        magnitude = _safe_label(str(properties.get("mag") or ""), fallback="")
        alert = _safe_label(str(properties.get("alert") or ""), fallback="")
        link = _safe_url(properties.get("url")) or entry.url
        mag_phrase = f"; magnitude {magnitude}" if magnitude else ""
        alert_phrase = f"; alert {alert}" if alert else ""
        summary = (
            f"USGS public GeoJSON event metadata: {title}{mag_phrase}{alert_phrase}; "
            f"observed {date_value}. Only event metadata is retained."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("geojson_feature", entry.name, event_id, date_value),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": "environmental infrastructure stress",
                "region_hint": _safe_label(properties.get("place"), fallback="global"),
                "target_sector": "critical infrastructure and continuity planners",
                "vector_class": "natural-hazard infrastructure-stress signal",
                "motive_hint": "disaster-response and continuity pressure context",
                "confidence": "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label=_option(entry, "display_label") or "USGS GeoJSON feed",
                    url=link,
                    date_value=date_value,
                    supports=f"public GeoJSON metadata for {title}",
                ),
                "tags": _record_tags([entry.name, "usgs", "natural_hazard", "infrastructure_stress", alert, *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{event_id}",
        )
    return records


def collect_html_link_index(data: Any, entry: CatalogEntry) -> list[SanitizedRecord]:
    """Collect headline/link metadata from a public HTML index page."""

    if not isinstance(data, str):
        raise ValueError(f"{entry.name}: HTML index payload must be text")
    parser = _LinkIndexParser()
    parser.feed(data)
    label = _option(entry, "display_label") or _safe_label(entry.name.replace("_", " "), fallback="Public HTML index")

    records: list[SanitizedRecord] = []
    seen: set[str] = set()
    for href, text in parser.links:
        link = _safe_url(urljoin(entry.url, href))
        if not link or link in seen or link == entry.url:
            continue
        if not _link_matches_entry(entry, link):
            continue
        seen.add(link)
        title = _safe_label(text, fallback=f"{label} item")
        if len(title) < 4:
            continue
        date_value = _date_from_url(link) or _today()
        vector_class = _vector_from_terms(title)
        summary = (
            f"{label} public index metadata: {title}. Only headline, link, and "
            "derived/public date are retained; page body and raw HTML are omitted."
        )
        _append_record(
            records,
            {
                "record_id": stable_id("html_index", entry.name, link, title),
                "observed_at": f"{date_value}T00:00:00Z",
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "actor_hint": _option(entry, "actor_hint") or "unknown actors",
                "region_hint": _option(entry, "region_hint") or "global",
                "target_sector": _option(entry, "target_sector") or "public-sector and enterprise defenders",
                "vector_class": _option(entry, "vector_class") or vector_class,
                "motive_hint": _option(entry, "motive_hint") or "public advisory or research timing context",
                "confidence": _option(entry, "confidence") or "medium",
                "summary": summary,
                "source_ref": make_source_ref(
                    label=label,
                    url=link,
                    date_value=date_value,
                    supports=f"public index metadata for {title}",
                ),
                "tags": _record_tags([entry.name, *_keyword_tags(title), *_option_tags(entry)]),
            },
            source_name=f"{entry.name}:{title}",
        )
    return records


def collect_sanitized_json(data: Any) -> list[SanitizedRecord]:
    """Validate pre-sanitized JSON or JSONL-like arrays as SanitizedRecord."""

    if isinstance(data, str):
        values = _jsonl_values(data)
    elif isinstance(data, Mapping) and isinstance(data.get("records"), list):
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


class _LinkIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str = ""
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href" and value:
                href = value
                break
        self._href = href
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href:
            return
        text = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
        self.links.append((self._href, html.unescape(text)))
        self._href = ""
        self._parts = []


def _append_record(
    records: list[SanitizedRecord],
    payload: Mapping[str, Any],
    *,
    source_name: str,
) -> None:
    try:
        records.append(SanitizedRecord.from_mapping(payload, source_name=source_name))
    except RecordValidationError:
        return


def _csv_records(data: str) -> Iterable[dict[str, str]]:
    reader = csv.reader(io.StringIO(data))
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue
        first = row[0].strip().lower()
        if first in {"ent_num", "uid", "id"}:
            continue
        yield {
            "entity_type": row[2].strip() if len(row) > 2 else "",
            "program": row[3].strip() if len(row) > 3 else "",
        }


def _json_items(data: Any, source_name: str, label: str) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, Mapping):
        for key in ("items", "results", "data", "advisories", "articles", "vulns"):
            values = data.get(key)
            if isinstance(values, list):
                return values
    raise ValueError(f"{source_name}: {label} JSON must be an array or object with item list")


def _collector_item_limit(entry: CatalogEntry, default: int = 250) -> int:
    value = entry.options.get("max_records")
    if isinstance(value, str) and value.strip().isdigit():
        return max(1, min(int(value.strip()), 5000))
    return default


def _cve_record_items(data: Any) -> list[Mapping[str, Any]]:
    values: list[Any]
    if isinstance(data, list):
        values = data
    elif isinstance(data, Mapping) and isinstance(data.get("records"), list):
        values = data["records"]
    elif isinstance(data, Mapping) and isinstance(data.get("containers"), Mapping):
        values = [data]
    elif isinstance(data, Mapping) and isinstance(data.get("cveMetadata"), Mapping):
        values = [data]
    else:
        values = []
    return [item for item in values if isinstance(item, Mapping)]


def _cve_record_products(item: Mapping[str, Any]) -> list[str]:
    products: list[str] = []
    containers = item.get("containers", {})
    if not isinstance(containers, Mapping):
        return products
    for container in _cve_containers(containers):
        affected = container.get("affected", [])
        if not isinstance(affected, list):
            continue
        for value in affected:
            if not isinstance(value, Mapping):
                continue
            vendor = _safe_label(value.get("vendor"), fallback="")
            product = _safe_label(value.get("product"), fallback="")
            label = " ".join(part for part in (vendor, product) if part)
            if label and label not in products:
                products.append(label)
    return products[:6]


def _cve_record_cwes(item: Mapping[str, Any]) -> list[str]:
    cwes: list[str] = []
    containers = item.get("containers", {})
    if not isinstance(containers, Mapping):
        return cwes
    for container in _cve_containers(containers):
        problem_types = container.get("problemTypes", [])
        if not isinstance(problem_types, list):
            continue
        for problem_type in problem_types:
            if not isinstance(problem_type, Mapping):
                continue
            descriptions = problem_type.get("descriptions", [])
            if not isinstance(descriptions, list):
                continue
            for description in descriptions:
                if not isinstance(description, Mapping):
                    continue
                cwe = _clean_cwe(description.get("cweId") or description.get("description"))
                if cwe and cwe not in cwes:
                    cwes.append(cwe)
    return cwes[:6]


def _cve_adp_labels(item: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    containers = item.get("containers", {})
    if not isinstance(containers, Mapping):
        return labels
    adp = containers.get("adp", [])
    if not isinstance(adp, list):
        return labels
    for container in adp:
        if not isinstance(container, Mapping):
            continue
        provider = container.get("providerMetadata", {})
        if isinstance(provider, Mapping):
            label = _safe_label(provider.get("shortName") or provider.get("orgId"), fallback="")
            if label and label not in labels:
                labels.append(label)
        title = _safe_label(container.get("title"), fallback="")
        if title and title not in labels:
            labels.append(title)
    return labels[:4]


def _cve_containers(containers: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    cna = containers.get("cna")
    if isinstance(cna, Mapping):
        yield cna
    adp = containers.get("adp")
    if isinstance(adp, list):
        for item in adp:
            if isinstance(item, Mapping):
                yield item


def _target_from_products(products: list[str]) -> str:
    if not products:
        return ""
    return "organizations using " + ", ".join(products[:3])


def _cve_record_url(cve_id: str, entry: CatalogEntry) -> str:
    if entry.url:
        return entry.url
    return f"https://www.cve.org/CVERecord?id={cve_id}"


def _osv_aliases(item: Mapping[str, Any]) -> list[str]:
    aliases: list[str] = []
    values = item.get("aliases", [])
    if not isinstance(values, list):
        return aliases
    for alias in values:
        cve = _clean_cve(alias)
        if cve and cve not in aliases:
            aliases.append(cve)
    return aliases[:6]


def _osv_ecosystems(item: Mapping[str, Any]) -> list[str]:
    ecosystems: list[str] = []
    values = item.get("affected", [])
    if not isinstance(values, list):
        return ecosystems
    for affected in values:
        if not isinstance(affected, Mapping):
            continue
        package = affected.get("package", {})
        if not isinstance(package, Mapping):
            continue
        ecosystem = _safe_label(package.get("ecosystem"), fallback="")
        name = _safe_label(package.get("name"), fallback="")
        label = ecosystem or name
        if ecosystem and name:
            label = f"{ecosystem} {name}"
        if label and label not in ecosystems:
            ecosystems.append(label)
    return ecosystems[:6]


def _osv_severity(item: Mapping[str, Any]) -> str:
    severity = item.get("severity", [])
    if isinstance(severity, list):
        for value in severity:
            if not isinstance(value, Mapping):
                continue
            score_type = _safe_label(value.get("type"), fallback="")
            score = _safe_label(value.get("score"), fallback="")
            if score_type or score:
                return " ".join(part for part in (score_type, score[:12]) if part)
    database_specific = item.get("database_specific", {})
    if isinstance(database_specific, Mapping):
        return _safe_label(database_specific.get("severity"), fallback="")
    return ""


def _redhat_packages(item: Mapping[str, Any]) -> list[str]:
    packages: list[str] = []
    affected = item.get("affected_packages", [])
    if isinstance(affected, list):
        for value in affected:
            label = _safe_label(value, fallback="")
            if label and label not in packages:
                packages.append(label)
    package_state = item.get("package_state", [])
    if isinstance(package_state, list):
        for value in package_state:
            if not isinstance(value, Mapping):
                continue
            label = _safe_label(value.get("package_name"), fallback="")
            if label and label not in packages:
                packages.append(label)
    return packages[:6]


def _attack_external_ref(item: Mapping[str, Any]) -> tuple[str, str]:
    values = item.get("external_references", [])
    if not isinstance(values, list):
        return "", ""
    for value in values:
        if not isinstance(value, Mapping):
            continue
        source = _safe_label(value.get("source_name"), fallback="")
        if source != "mitre-attack":
            continue
        external_id = _safe_label(value.get("external_id"), fallback="")
        link = _safe_url(value.get("url"))
        return external_id, link
    return "", ""


def _attack_tactics(item: Mapping[str, Any]) -> list[str]:
    values = item.get("kill_chain_phases", [])
    if not isinstance(values, list):
        return []
    tactics: list[str] = []
    for value in values:
        if not isinstance(value, Mapping):
            continue
        label = _safe_label(value.get("phase_name"), fallback="")
        if label and label not in tactics:
            tactics.append(label)
    return tactics[:6]


def _xml_elements(root: ET.Element, local_name: str) -> Iterable[ET.Element]:
    for element in root.iter():
        if _xml_local_name(element.tag) == local_name:
            yield element


def _xml_local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _jsonld_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        inner = value.get("@value") or value.get("value") or value.get("@id")
        return inner if isinstance(inner, str) else ""
    if isinstance(value, list):
        for item in value:
            text = _jsonld_text(item)
            if text:
                return text
    return ""


def _jsonl_values(data: str) -> list[Any]:
    values: list[Any] = []
    for line_no, raw_line in enumerate(data.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"metadata JSONL line {line_no} is not valid JSON") from exc
    return values


def _github_cve_ids(item: Mapping[str, Any]) -> list[str]:
    cve_ids: list[str] = []
    cve = _clean_cve(item.get("cve_id"))
    if cve:
        cve_ids.append(cve)
    identifiers = item.get("identifiers", [])
    if isinstance(identifiers, list):
        for identifier in identifiers:
            if not isinstance(identifier, Mapping):
                continue
            value = _clean_cve(identifier.get("value"))
            if value and value not in cve_ids:
                cve_ids.append(value)
    return cve_ids[:5]


def _github_ecosystem(item: Mapping[str, Any]) -> str:
    ecosystems: list[str] = []
    values = item.get("vulnerabilities", [])
    if isinstance(values, list):
        for vulnerability in values:
            if not isinstance(vulnerability, Mapping):
                continue
            package = vulnerability.get("package", {})
            if not isinstance(package, Mapping):
                continue
            ecosystem = _safe_label(package.get("ecosystem"), fallback="")
            if ecosystem and ecosystem not in ecosystems:
                ecosystems.append(ecosystem)
    if not ecosystems:
        return ""
    return " / ".join(ecosystems[:3])


def _label_list(value: Any, key: str) -> list[str]:
    values: list[str] = []
    raw_items = value if isinstance(value, list) else [value]
    for item in raw_items:
        if isinstance(item, Mapping):
            label = _safe_label(item.get(key), fallback="")
        else:
            label = _safe_label(item, fallback="")
        if label and label not in values:
            values.append(label)
    return values[:6]


def _reliefweb_date(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("changed", "created", "original"):
            parsed = _date_string(value.get(key))
            if parsed:
                return parsed
    return _date_string(value)


def _nested_date(value: Mapping[str, Any], path: tuple[str, str]) -> str:
    parent = value.get(path[0])
    if not isinstance(parent, Mapping):
        return ""
    return _date_string(parent.get(path[1]))


def _millis_or_date(value: Any) -> str:
    if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
        try:
            numeric = int(value)
            if numeric > 10_000_000_000:
                numeric = numeric // 1000
            return datetime.fromtimestamp(numeric, tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    return _date_string(value)


def _msrc_sort_key(item: Any) -> str:
    if not isinstance(item, Mapping):
        return ""
    return _date_string(item.get("CurrentReleaseDate")) or _date_string(item.get("InitialReleaseDate"))


def _link_matches_entry(entry: CatalogEntry, link: str) -> bool:
    parsed = urlparse(link)
    path = parsed.path
    if entry.name == "cisa_cybersecurity_advisories":
        return "/news-events/cybersecurity-advisories/" in path
    if entry.name == "cisa_ics_advisories":
        return "/news-events/ics-advisories/" in path
    if entry.name == "openwall_oss_security_index":
        return "/lists/oss-security/" in path and bool(re.search(r"/20\d{2}/", path))
    if entry.name == "google_cloud_security_bulletins":
        return "/support/bulletins" in path or "security-bulletins" in path
    if entry.name == "cert_eu_security_advisories":
        return "/publications/security-advisories/" in path
    return parsed.netloc == (urlparse(entry.url).netloc if entry.url else parsed.netloc)


def _date_from_url(link: str) -> str:
    path = urlparse(link).path
    match = re.search(r"/(20\d{2})/(\d{2})/(\d{2})(?:/|$)", path)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return ""


def load_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_zip_text_path(path: Path) -> str:
    return _first_zip_text(path.read_bytes(), source_name=str(path))


def fetch_official_json(url: str, *, timeout: float = 20.0) -> Any:
    return _loads_json_text(fetch_public_text(url, timeout=timeout))


def fetch_public_text(url: str, *, timeout: float = 20.0) -> str:
    with _open_public_request(url, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_public_bytes(url: str, *, timeout: float = 20.0) -> bytes:
    with _open_public_request(url, timeout=timeout) as response:
        return response.read()


class _AllowlistedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        redirected_url = urljoin(req.full_url, newurl)
        _assert_allowed_live_url(redirected_url, context="live collection redirect")
        return super().redirect_request(req, fp, code, msg, headers, redirected_url)


def _assert_allowed_live_url(url: str, *, context: str = "live collection") -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"{context} only supports HTTPS URLs")
    if parsed.username or parsed.password:
        raise ValueError(f"{context} URL must not contain credentials")
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|password|secret)=", parsed.query, re.IGNORECASE):
        raise ValueError(f"{context} URL must not contain credential query parameters")
    host = parsed.hostname or ""
    if host.lower() not in ALLOWED_LIVE_HOSTS:
        allowed = ", ".join(sorted(ALLOWED_LIVE_HOSTS))
        raise ValueError(f"{context} host {host!r} is not allowed; allowed: {allowed}")


def _open_public_request(url: str, *, timeout: float = 20.0) -> Any:
    _assert_allowed_live_url(url)
    request = Request(
        url,
        headers={
            "Accept": "application/json, application/rss+xml, application/xml, application/zip, text/xml, text/html;q=0.5",
            "User-Agent": "ProphetScraperSide/0.1 official-json-collector",
        },
    )
    opener = build_opener(_AllowlistedRedirectHandler)
    response = opener.open(request, timeout=timeout)
    _assert_allowed_live_url(response.geturl(), context="live collection final URL")
    return response


def _first_zip_text(data: bytes, *, source_name: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.lower().endswith((".xml", ".json", ".csv", ".txt"))
                and not name.endswith("/")
            ]
            if not names:
                raise ValueError(f"{source_name}: ZIP archive has no supported text member")
            with archive.open(sorted(names)[0]) as handle:
                return handle.read().decode("utf-8", errors="replace")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{source_name}: invalid ZIP archive") from exc


def _resolved_live_url(entry: CatalogEntry, collector: str) -> str:
    if collector == "nvd_cve":
        end = datetime.now(timezone.utc).replace(microsecond=0)
        start = end - timedelta(days=7)
        params = {
            "resultsPerPage": "100",
            "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "pubEndDate": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "noRejected": "",
        }
        return "https://services.nvd.nist.gov/rest/json/cves/2.0?" + urlencode(params)
    if collector == "redhat_security_data":
        if entry.options.get("seed_key"):
            return entry.url
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=30)
        separator = "&" if "?" in entry.url else "?"
        return f"{entry.url}{separator}after={start.isoformat()}"
    return entry.url


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
        if entry.format == "xml_zip" or entry.local_path.suffix.lower() == ".zip":
            return load_zip_text_path(entry.local_path)
        if (
            collector in TEXT_COLLECTORS
            or entry.format in {"rss", "xml", "csv", "html", "metadata_jsonl"}
            or entry.local_path.suffix.lower() == ".jsonl"
        ):
            return entry.local_path.read_text(encoding="utf-8")
        return load_json_path(entry.local_path)
    if live:
        url = _resolved_live_url(entry, collector)
        if not url:
            raise ValueError(f"{entry.name}: live collection requires a URL")
        if entry.format == "xml_zip":
            return _first_zip_text(fetch_public_bytes(url, timeout=timeout), source_name=entry.name)
        text = fetch_public_text(url, timeout=timeout)
        if collector in JSON_COLLECTORS or entry.format == "json":
            return _loads_json_text(text)
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


def _loads_json_text(text: str) -> Any:
    data = json.loads(text)
    if isinstance(data, str):
        clean = data.strip()
        if clean.startswith("{") or clean.startswith("["):
            return json.loads(clean)
    return data


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


def _clean_cwe(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    match = re.search(r"CWE-\d+", value.strip(), re.IGNORECASE)
    if not match:
        return ""
    return match.group(0).upper()


def _date_string(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    text = value.strip()
    basic = re.match(r"^(20\d{2})(\d{2})(\d{2})T", text)
    if basic:
        return f"{basic.group(1)}-{basic.group(2)}-{basic.group(3)}"
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
