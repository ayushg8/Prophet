"""Optional source-catalog loading for scraper-side collectors."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


@dataclass(frozen=True)
class CatalogEntry:
    """One official or local JSON source the CLI can collect from."""

    name: str
    collector: str
    source_type: str = "official_government"
    collection_tier: str = "official_signal"
    url: str = ""
    format: str = "json"
    local_path: Path | None = None
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)


CATALOG_SOURCE_TYPE_MAP = {
    "gov_feed": "official_government",
    "technical_index": "threat_intel_feed",
    "technical_api": "threat_intel_feed",
    "public_social": "public_social",
    "high_risk_metadata": "onion_public_metadata",
    "vendor_advisory": "vendor_advisory",
    "osint_context": "manual_analyst_note",
}

CATALOG_LANE_TIER_MAP = {
    "official_gov_feeds": "official_signal",
    "public_technical_chatter": "technical_chatter",
    "public_social_chatter": "public_chatter",
    "high_risk_metadata_only": "darkweb_metadata",
    "osint_context_feeds": "analyst_context",
    "analysis_tooling_references": "analyst_context",
}

CATALOG_COLLECTOR_MAP = {
    "cisa_kev_json": "cisa_kev",
    "nvd_cve_api_recent": "nvd_cve",
    "first_epss_api": "first_epss",
    "state_travel_advisories_rss": "official_rss",
    "doj_cyber_press_releases_api": "doj_press_releases",
    "federal_register_sanctions_api": "federal_register_documents",
    "ofac_sanctions_list_service": "ofac_sdn_csv",
    "noaa_nhc_atlantic_rss": "official_rss",
    "noaa_nhc_eastern_pacific_rss": "official_rss",
    "cisa_cybersecurity_advisories": "html_link_index",
    "cisa_ics_advisories": "html_link_index",
    "github_advisory_database": "github_advisories",
    "nuclei_templates_cve_commits": "github_commits",
    "openwall_oss_security_index": "html_link_index",
    "fortinet_psirt_rss": "official_rss",
    "ivanti_security_advisory_rss": "official_rss",
    "reddit_security_public_new": "reddit_listing",
    "reliefweb_active_disasters_api": "reliefweb_disasters",
    "gdelt_cyber_geopolitics_articles": "gdelt_articles",
    "usgs_significant_earthquakes_day_geojson": "geojson_features",
    "gdacs_alerts_rss": "official_rss",
    "worldmonitor_bootstrap_api": "sanitized_json",
    "telegram_public_channel_metadata": "sanitized_json",
    "onion_public_landing_metadata": "sanitized_json",
    "high_risk_forum_topic_metadata": "sanitized_json",
    "high_risk_leak_claim_metadata": "sanitized_json",
    "high_risk_paste_index_metadata": "sanitized_json",
}

READY_COLLECTORS = {
    "cisa_kev",
    "nvd_cve",
    "first_epss",
    "official_rss",
    "doj_press_releases",
    "federal_register_documents",
    "ofac_sdn_csv",
    "github_advisories",
    "github_commits",
    "reddit_listing",
    "reliefweb_disasters",
    "gdelt_articles",
    "geojson_features",
    "html_link_index",
}

def load_source_catalog(path: str | Path | None = None) -> list[CatalogEntry]:
    """Load source catalog entries if a config exists, else return safe defaults.

    Supported JSON shape is either ``{"sources": [...]}`` or a top-level list.
    Relative ``local_path`` values are resolved against the catalog file's
    directory. No config file is created by this loader.
    """

    catalog_path = _resolve_catalog_path(path)
    if catalog_path is None:
        return default_catalog()
    if path is not None and not catalog_path.exists():
        raise FileNotFoundError(f"source catalog not found: {catalog_path}")
    if not catalog_path.exists():
        return default_catalog()

    with catalog_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, Mapping):
        sources = data.get("sources", [])
    else:
        sources = data
    if not isinstance(sources, list):
        raise ValueError(f"{catalog_path}: sources must be a list")

    entries: list[CatalogEntry] = []
    for idx, item in enumerate(sources, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"{catalog_path}: source {idx} must be an object")
        entries.append(_entry_from_mapping(item, catalog_path.parent, idx))
    return entries


def default_catalog() -> list[CatalogEntry]:
    return [
        CatalogEntry(
            name="cisa_kev",
            collector="cisa_kev",
            source_type="official_government",
            collection_tier="official_signal",
            url=DEFAULT_CISA_KEV_URL,
            enabled=True,
        )
    ]


def filter_catalog(
    entries: Iterable[CatalogEntry],
    names: Iterable[str] | None,
) -> list[CatalogEntry]:
    requested = {name for name in names or [] if name}
    entries_list = list(entries)
    if requested:
        selected = [entry for entry in entries_list if entry.name in requested]
    else:
        selected = [entry for entry in entries_list if entry.enabled and _collector_ready(entry)]
    missing = requested.difference({entry.name for entry in entries_list})
    if missing:
        raise ValueError(f"source(s) not found in catalog: {', '.join(sorted(missing))}")
    return selected


def _collector_ready(entry: CatalogEntry) -> bool:
    if entry.collector == "sanitized_json":
        return entry.local_path is not None
    if entry.collector in READY_COLLECTORS:
        return True
    return entry.local_path is not None


def _resolve_catalog_path(path: str | Path | None) -> Path | None:
    if path is not None:
        return Path(path)

    env_path = os.environ.get("PROPHET_SCRAPER_CATALOG")
    if env_path:
        return Path(env_path)

    scraper_dir = Path(__file__).resolve().parents[1]
    for name in ("source_catalog.json", "sources.json", "catalog.json"):
        for candidate in (scraper_dir / name, scraper_dir / "config" / name):
            if candidate.exists():
                return candidate
    return None


def _entry_from_mapping(
    value: Mapping[str, Any],
    base_dir: Path,
    idx: int,
) -> CatalogEntry:
    name = _str_value(value, "name") or f"source_{idx}"
    source_id = _str_value(value, "id")
    if source_id and name == f"source_{idx}":
        name = source_id
    collector = (
        _str_value(value, "collector")
        or _str_value(value, "type")
        or CATALOG_COLLECTOR_MAP.get(source_id, "sanitized_json")
    )

    collection = value.get("collection")
    if collection is not None and not isinstance(collection, Mapping):
        raise ValueError(f"catalog source {name}: collection must be an object")
    collection = collection if isinstance(collection, Mapping) else {}

    local_path_value = _str_value(value, "local_path") or _str_value(value, "path")
    local_path = None
    if local_path_value:
        local_path = Path(local_path_value)
        if not local_path.is_absolute():
            local_path = base_dir / local_path

    options = value.get("options", {})
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError(f"catalog source {name}: options must be an object")
    display_name = _str_value(value, "display_name")
    if display_name and "display_label" not in options:
        options = {**options, "display_label": display_name}

    raw_source_type = _str_value(value, "source_type") or "official_government"
    source_type = CATALOG_SOURCE_TYPE_MAP.get(raw_source_type, raw_source_type)
    lane = _str_value(value, "lane")
    collection_tier = (
        _str_value(value, "collection_tier")
        or CATALOG_LANE_TIER_MAP.get(lane, "official_signal")
    )
    url = _str_value(value, "url") or _str_value(collection, "url")
    feed_format = _str_value(collection, "format") or "json"

    return CatalogEntry(
        name=name,
        collector=normalize_collector(collector),
        source_type=source_type,
        collection_tier=collection_tier,
        url=url,
        format=feed_format,
        local_path=local_path,
        enabled=bool(value.get("enabled", True)),
        options=dict(options),
    )


def normalize_collector(value: str) -> str:
    clean = value.strip().lower().replace("-", "_")
    aliases = {
        "cisa": "cisa_kev",
        "kev": "cisa_kev",
        "cisa_known_exploited": "cisa_kev",
        "nvd": "nvd_cve",
        "nvd_cves": "nvd_cve",
        "epss": "first_epss",
        "first": "first_epss",
        "rss": "official_rss",
        "atom": "official_rss",
        "doj": "doj_press_releases",
        "federal_register": "federal_register_documents",
        "ofac": "ofac_sdn_csv",
        "ofac_sdn": "ofac_sdn_csv",
        "github_advisory": "github_advisories",
        "github_advisories_api": "github_advisories",
        "github_commit": "github_commits",
        "github_commits_api": "github_commits",
        "reddit": "reddit_listing",
        "reliefweb": "reliefweb_disasters",
        "gdelt": "gdelt_articles",
        "geojson": "geojson_features",
        "html": "html_link_index",
        "html_index": "html_link_index",
        "sanitized": "sanitized_json",
        "sanitized_records": "sanitized_json",
        "metadata_jsonl": "sanitized_json",
    }
    return aliases.get(clean, clean)


def _str_value(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if result is None:
        return ""
    if not isinstance(result, str):
        raise ValueError(f"catalog field {key} must be a string")
    return result.strip()
