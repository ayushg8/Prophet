"""Scraper-side sanitization package for Prophet World Side.

This package is intentionally stdlib-only and emits analyst-safe JSONL records
that can be handed to the World Side forecaster. Network collection is opt-in
through the CLI and limited to official public JSON feeds.
"""

from .catalog import CatalogEntry, load_source_catalog
from .collectors import collect_records
from .records import RecordValidationError, SanitizedRecord

__all__ = [
    "CatalogEntry",
    "RecordValidationError",
    "SanitizedRecord",
    "collect_records",
    "load_source_catalog",
]
