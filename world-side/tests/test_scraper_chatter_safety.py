from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[2]
WORLD_SIDE = ROOT / "world-side"
SCRAPER_ROOT = WORLD_SIDE / "scraper"
FIXTURES = WORLD_SIDE / "fixtures"

for import_root in (SCRAPER_ROOT, WORLD_SIDE):
    root_text = str(import_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


BANNED_RAW_KEYS = {
    "raw",
    "raw_text",
    "raw_html",
    "html",
    "message",
    "message_text",
    "body",
    "content",
    "dump",
    "leak",
    "credential",
    "credentials",
    "username",
    "password",
    "token",
    "session",
    "session_file",
    "onion",
    "onion_url",
    "invite_link",
    "phone",
    "email",
}

SAFE_RECORD = {
    "record_id": "chat_safety_fixture_001",
    "observed_at": "2026-05-02T22:20:00Z",
    "source_type": "telegram_public_channel",
    "collection_tier": "public_chatter",
    "actor_hint": "PRC-nexus",
    "region_hint": "US / Indo-Pacific",
    "target_sector": "US federal and defense edge infrastructure",
    "vector_class": "edge-appliance access and pre-positioning",
    "motive_hint": "summit-timed collection interest",
    "confidence": "medium",
    "summary": (
        "Sanitized public-channel chatter notes increased discussion of "
        "federal edge-access themes around a near-term diplomatic window."
    ),
    "source_ref": {
        "id": "src_chatter_safety_fixture_001",
        "label": "Sanitized chatter safety fixture",
        "url": "sanitized://scraper-record/chat_safety_fixture_001",
        "date": "2026-05-02",
        "supports": "current public chatter signal for edge-appliance timing",
    },
}

SAFE_RECORD_2 = {
    **SAFE_RECORD,
    "record_id": "chat_safety_fixture_002",
    "source_type": "official_government",
    "collection_tier": "official_signal",
    "confidence": "high",
    "summary": "Public government advisory context summarized without raw artifacts.",
    "source_ref": {
        **SAFE_RECORD["source_ref"],
        "id": "src_chatter_safety_fixture_002",
        "url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a",
    },
}


class ScraperChatterSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api = _load_scraper_api()
        if cls.api.sanitizer_missing:
            raise unittest.SkipTest(cls.api.sanitizer_missing)

    def test_sanitizer_rejects_raw_fields(self) -> None:
        candidate = {
            **SAFE_RECORD,
            "record_id": "bad_raw_fields",
            "message_text": "Raw post text must never cross to the main dev box.",
            "raw_html": "<html>raw scraper artifact</html>",
        }

        self.assert_rejected(candidate)

    def test_sanitizer_rejects_onion_urls(self) -> None:
        candidate = {
            **SAFE_RECORD,
            "record_id": "bad_onion_url",
            "source_type": "onion_public_metadata",
            "collection_tier": "darkweb_metadata",
            "source_ref": {
                **SAFE_RECORD["source_ref"],
                "url": "http://not-a-real-hidden-service.onion/path",
            },
        }

        self.assert_rejected(candidate)

    def test_sanitizer_accepts_safe_fixture(self) -> None:
        accepted = self.api.validate(SAFE_RECORD)
        accepted_record = _as_mapping(accepted, fallback=SAFE_RECORD)
        self.assert_no_unsafe_surface(accepted_record)

        fixture_path = FIXTURES / "sanitized-chatter-sample.jsonl"
        if fixture_path.exists():
            for fixture_record in _read_jsonl(fixture_path):
                accepted = self.api.validate(fixture_record)
                self.assert_no_unsafe_surface(_as_mapping(accepted, fallback=fixture_record))

    def test_collector_writes_valid_jsonl(self) -> None:
        if self.api.write_jsonl is None:
            self.skipTest(self.api.collector_missing or "scraper_side collector writer not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sanitized-chatter.jsonl"
            self.api.write_jsonl([SAFE_RECORD, SAFE_RECORD_2], output_path)

            self.assertTrue(output_path.exists(), "collector should create the JSONL file")
            records = _read_jsonl(output_path)

        self.assertEqual(len(records), 2)
        for record in records:
            accepted = self.api.validate(record)
            self.assert_no_unsafe_surface(_as_mapping(accepted, fallback=record))

    def test_source_catalog_keeps_risky_sources_disabled(self) -> None:
        from scraper_side.catalog import filter_catalog, load_source_catalog

        catalog_path = SCRAPER_ROOT / "config" / "source_catalog.json"
        entries = load_source_catalog(catalog_path)
        by_name = {entry.name: entry for entry in entries}

        for required in (
            "first_epss_api",
            "state_travel_advisories_rss",
            "doj_cyber_press_releases_api",
            "federal_register_sanctions_api",
            "noaa_nhc_atlantic_rss",
            "fortinet_psirt_rss",
            "ivanti_security_advisory_rss",
            "shodan_context_api",
            "exa_osint_search_api",
            "aishub_ais_api",
            "flightradar24_context_reference",
            "telegram_public_channel_metadata",
            "onion_public_landing_metadata",
        ):
            self.assertIn(required, by_name)

        for disabled in (
            "shodan_context_api",
            "exa_osint_search_api",
            "aishub_ais_api",
            "barentswatch_historic_ais_api",
            "marinecadastre_vessel_traffic_data",
            "kaggle_ais_dataset_reference",
            "flightradar24_context_reference",
            "telegram_public_channel_metadata",
            "onion_public_landing_metadata",
            "ofac_sanctions_list_service",
            "microsoft_msrc_cvrf_api",
        ):
            self.assertFalse(by_name[disabled].enabled, f"{disabled} must not run by default")

        ready_defaults = {entry.name for entry in filter_catalog(entries, names=None)}
        self.assertIn("first_epss_api", ready_defaults)
        self.assertIn("state_travel_advisories_rss", ready_defaults)
        self.assertIn("fortinet_psirt_rss", ready_defaults)
        self.assertNotIn("shodan_context_api", ready_defaults)
        self.assertNotIn("telegram_public_channel_metadata", ready_defaults)

    def test_catalog_has_no_enabled_auth_gated_sources(self) -> None:
        catalog_path = SCRAPER_ROOT / "config" / "source_catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for source in catalog["sources"]:
            auth_method = source["collection"]["auth_method"]
            if auth_method in {
                "api_key_required",
                "account_required",
                "commercial_or_terms_review_required",
            }:
                self.assertFalse(source["enabled"], f"{source['id']} is auth-gated")
            if source["lane"] == "high_risk_metadata_only":
                self.assertFalse(source["enabled"], f"{source['id']} is high risk")

    def test_new_collectors_emit_sanitized_records(self) -> None:
        from scraper_side.catalog import CatalogEntry
        from scraper_side.collectors import (
            collect_doj_press_releases,
            collect_federal_register_documents,
            collect_first_epss,
            collect_official_rss,
        )

        epss_records = collect_first_epss(
            {
                "data": [
                    {
                        "cve": "CVE-2026-12345",
                        "epss": "0.91",
                        "percentile": "0.99",
                        "date": "2026-05-02",
                    }
                ]
            },
            CatalogEntry(
                name="first_epss_api",
                collector="first_epss",
                source_type="threat_intel_feed",
                collection_tier="technical_chatter",
                url="https://api.first.org/data/v1/epss",
            ),
        )
        rss_records = collect_official_rss(
            """
            <rss version="2.0"><channel>
              <item>
                <title>Advisory headline CVE-2026-12345</title>
                <link>https://example.gov/advisory</link>
                <pubDate>Sat, 02 May 2026 12:00:00 GMT</pubDate>
              </item>
            </channel></rss>
            """,
            CatalogEntry(
                name="state_travel_advisories_rss",
                collector="official_rss",
                source_type="official_government",
                collection_tier="official_signal",
                url="https://travel.state.gov/_res/rss/TAsTWs.xml",
                format="rss",
            ),
        )
        doj_records = collect_doj_press_releases(
            {
                "results": [
                    {
                        "title": "Cyber indictment announced",
                        "url": "https://www.justice.gov/opa/pr/cyber-indictment",
                        "date": "1777737600",
                        "uuid": "fixture",
                    }
                ]
            },
            CatalogEntry(
                name="doj_cyber_press_releases_api",
                collector="doj_press_releases",
                source_type="official_government",
                collection_tier="official_signal",
                url="https://www.justice.gov/api/v1/press_releases.json",
            ),
        )
        federal_records = collect_federal_register_documents(
            {
                "results": [
                    {
                        "title": "Sanctions and export-control notice",
                        "publication_date": "2026-05-02",
                        "html_url": "https://www.federalregister.gov/documents/fixture",
                        "document_number": "2026-fixture",
                        "agencies": [{"name": "Office of Foreign Assets Control"}],
                    }
                ]
            },
            CatalogEntry(
                name="federal_register_sanctions_api",
                collector="federal_register_documents",
                source_type="official_government",
                collection_tier="official_signal",
                url="https://www.federalregister.gov/api/v1/documents.json",
            ),
        )

        for record in [*epss_records, *rss_records, *doj_records, *federal_records]:
            accepted = self.api.validate(record.to_dict())
            self.assert_no_unsafe_surface(_as_mapping(accepted, fallback=record.to_dict()))

    def assert_rejected(self, record: dict[str, Any]) -> None:
        try:
            result = self.api.validate(record)
        except Exception:
            return

        if result is False:
            return
        if isinstance(result, tuple) and result and result[0] is False:
            return
        self.fail("sanitized chatter validator accepted unsafe scraper material")

    def assert_no_unsafe_surface(self, record: dict[str, Any]) -> None:
        for path, key, value in _walk(record):
            if key in BANNED_RAW_KEYS:
                self.fail(f"unsafe raw field survived at {path}")
            if isinstance(value, str):
                self.assertNotRegex(value, r"\.onion\b", f"onion URL survived at {path}")


class ScraperSafetyApi:
    def __init__(
        self,
        *,
        validate: Callable[[dict[str, Any]], Any] | None,
        write_jsonl: Callable[[Iterable[dict[str, Any]], Path], Any] | None,
        sanitizer_missing: str | None = None,
        collector_missing: str | None = None,
    ) -> None:
        self._validate = validate
        self.write_jsonl = write_jsonl
        self.sanitizer_missing = sanitizer_missing
        self.collector_missing = collector_missing

    def validate(self, record: dict[str, Any]) -> Any:
        if self._validate is None:
            raise AssertionError("scraper_side sanitizer validation function not found")
        return self._validate(record)


def _load_scraper_api() -> ScraperSafetyApi:
    sanitizer = _import_first(
        [
            "scraper_side.sanitizer",
            "scraper.scraper_side.sanitizer",
        ]
    )
    if sanitizer is None:
        return ScraperSafetyApi(
            validate=None,
            write_jsonl=None,
            sanitizer_missing=(
                "scraper_side.sanitizer is not importable yet from world-side/scraper"
            ),
        )

    validate = _first_callable(
        sanitizer,
        [
            "validate_sanitized_record",
            "validate_sanitized_chatter_record",
            "assert_sanitized_record",
            "assert_safe_record",
        ],
    )
    if validate is None:
        return ScraperSafetyApi(
            validate=None,
            write_jsonl=None,
            sanitizer_missing=(
                "scraper_side.sanitizer should expose validate_sanitized_record(record)"
            ),
        )

    collector = _import_first(
        [
            "scraper_side.collector",
            "scraper.scraper_side.collector",
        ]
    )
    collector_missing = None
    write_jsonl = None
    if collector is None:
        collector_missing = "scraper_side.collector is not importable yet"
    else:
        writer = _first_callable(
            collector,
            [
                "write_sanitized_jsonl",
                "write_jsonl",
                "dump_sanitized_jsonl",
                "write_sanitized_records",
            ],
        )
        if writer is None:
            collector_missing = (
                "scraper_side.collector should expose write_sanitized_jsonl(records, path)"
            )
        else:
            write_jsonl = _wrap_jsonl_writer(writer)

    return ScraperSafetyApi(
        validate=validate,
        write_jsonl=write_jsonl,
        collector_missing=collector_missing,
    )


def _import_first(module_names: list[str]) -> Any | None:
    for module_name in module_names:
        if importlib.util.find_spec(module_name) is None:
            continue
        return importlib.import_module(module_name)
    return None


def _first_callable(module: Any, names: list[str]) -> Callable[..., Any] | None:
    for name in names:
        value = getattr(module, name, None)
        if callable(value):
            return value
    return None


def _wrap_jsonl_writer(
    writer: Callable[..., Any],
) -> Callable[[Iterable[dict[str, Any]], Path], Any]:
    def write(records: Iterable[dict[str, Any]], path: Path) -> Any:
        if _path_looks_first(writer):
            return writer(path, records)
        return writer(records, path)

    return write


def _path_looks_first(writer: Callable[..., Any]) -> bool:
    try:
        parameters = list(inspect.signature(writer).parameters.values())
    except (TypeError, ValueError):
        return False
    if not parameters:
        return False
    first_name = parameters[0].name.lower()
    return any(token in first_name for token in ("path", "file", "out", "dest"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise AssertionError(f"{path}:{line_no}: JSONL line must be an object")
            records.append(parsed)
    return records


def _as_mapping(value: Any, *, fallback: dict[str, Any]) -> dict[str, Any]:
    if value is None or value is True:
        return fallback
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    if isinstance(value, tuple) and value:
        return _as_mapping(value[0], fallback=fallback)
    return fallback


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from _walk(child, f"{path}[{idx}]")


if __name__ == "__main__":
    unittest.main()
