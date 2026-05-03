"""CLI for emitting sanitized scraper-side JSONL records."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

from .catalog import CatalogEntry, filter_catalog, load_source_catalog, normalize_collector
from .collectors import collect_entry
from .records import RecordValidationError


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        entries = _entries_from_args(args)
        if args.list_sources:
            _write_catalog(entries)
            return 0

        since = _parse_date(args.since) if args.since else None
        records = []
        for entry in entries:
            remaining = None if args.limit is None else max(args.limit - len(records), 0)
            if remaining == 0:
                break
            records.extend(
                collect_entry(
                    entry,
                    live=args.live,
                    limit=remaining,
                    since=since,
                    timeout=args.timeout,
                )
            )

        _write_jsonl(records, args.out)
    except (OSError, json.JSONDecodeError, ValueError, RecordValidationError) as exc:
        print(f"scraper_side: {exc}", file=sys.stderr)
        return 1

    if args.out:
        print(f"wrote {len(records)} sanitized record(s) to {args.out}", file=sys.stderr)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m scraper_side.cli",
        description="Collect official/local JSON feeds and emit sanitized Prophet JSONL.",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        help="Optional source catalog JSON. If omitted, scraper/source_catalog.json is used only when it exists.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Catalog source name to collect. May be repeated. Defaults to all enabled sources.",
    )
    parser.add_argument(
        "--collector",
        choices=(
            "cisa-kev",
            "nvd-cve",
            "first-epss",
            "official-rss",
            "doj-press-releases",
            "federal-register-documents",
            "ofac-sdn-csv",
            "github-advisories",
            "github-commits",
            "reddit-listing",
            "reliefweb-disasters",
            "gdelt-articles",
            "geojson-features",
            "html-link-index",
            "sanitized-json",
            "metadata-jsonl",
        ),
        help="Collector to run without a catalog entry.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Local/sample/public JSON file for the selected collector.",
    )
    parser.add_argument(
        "--feed-url",
        help="Official public JSON feed URL. Only used with --live.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable official public HTTPS collection. Off by default.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum records to emit.",
    )
    parser.add_argument(
        "--since",
        help="Only emit records observed on or after YYYY-MM-DD.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds for --live official feed collection.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write JSONL to this path. Defaults to stdout.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Print the loaded catalog entries as JSON and exit.",
    )
    return parser


def _entries_from_args(args: argparse.Namespace) -> list[CatalogEntry]:
    if args.limit is not None and args.limit < 0:
        raise ValueError("--limit must be non-negative")
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")

    if args.collector:
        return [_entry_from_direct_args(args)]

    catalog = load_source_catalog(args.catalog)
    return filter_catalog(catalog, args.source)


def _entry_from_direct_args(args: argparse.Namespace) -> CatalogEntry:
    collector = normalize_collector(args.collector or "")
    if args.input is None and not args.live:
        raise ValueError("--collector requires --input unless --live is set")
    if args.live and not args.feed_url and collector not in {"cisa_kev", "first_epss"}:
        raise ValueError("--feed-url is required for live non-CISA collectors")

    source_type = (
        "official_government"
        if collector in {"cisa_kev", "nvd_cve", "doj_press_releases", "federal_register_documents", "ofac_sdn_csv"}
        else "public_social"
        if collector == "reddit_listing"
        else "manual_analyst_note"
        if collector in {"reliefweb_disasters", "gdelt_articles"}
        else "threat_intel_feed"
    )
    collection_tier = (
        "official_signal"
        if collector in {"cisa_kev", "nvd_cve", "doj_press_releases", "federal_register_documents", "ofac_sdn_csv"}
        else "public_chatter"
        if collector == "reddit_listing"
        else "analyst_context"
        if collector in {"reliefweb_disasters", "gdelt_articles"}
        else "technical_chatter"
    )
    url = args.feed_url or ""
    if collector == "cisa_kev" and args.live and not url:
        from .catalog import DEFAULT_CISA_KEV_URL

        url = DEFAULT_CISA_KEV_URL
    if collector == "first_epss" and args.live and not url:
        url = "https://api.first.org/data/v1/epss?limit=100&order=!epss"
    if collector == "official_rss":
        feed_format = "rss"
    elif collector == "ofac_sdn_csv":
        feed_format = "csv"
    elif collector == "html_link_index":
        feed_format = "html"
    elif collector == "geojson_features":
        feed_format = "json"
    elif collector == "sanitized_json":
        feed_format = "metadata_jsonl" if args.input and args.input.suffix == ".jsonl" else "json"
    else:
        feed_format = "json"

    return CatalogEntry(
        name=collector,
        collector=collector,
        source_type=source_type,
        collection_tier=collection_tier,
        url=url,
        format=feed_format,
        local_path=args.input,
        enabled=True,
    )


def _write_jsonl(records: list[object], out_path: Path | None) -> None:
    payload = "".join(record.to_json_line() + "\n" for record in records)
    if out_path is None:
        sys.stdout.write(payload)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")


def _write_catalog(entries: list[CatalogEntry]) -> None:
    payload = []
    for entry in entries:
        payload.append(
            {
                "name": entry.name,
                "collector": entry.collector,
                "source_type": entry.source_type,
                "collection_tier": entry.collection_tier,
                "url": entry.url,
                "local_path": str(entry.local_path) if entry.local_path else "",
                "enabled": entry.enabled,
            }
        )
    sys.stdout.write(json.dumps({"sources": payload}, indent=2) + "\n")


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("--since must be YYYY-MM-DD") from exc


if __name__ == "__main__":
    raise SystemExit(main())
