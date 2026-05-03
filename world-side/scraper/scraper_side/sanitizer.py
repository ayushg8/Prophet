"""Public sanitizer API for scraper-side tests and wrappers."""

from __future__ import annotations

from typing import Any, Mapping

from .records import SanitizedRecord, validate_sanitized_record


def validate_sanitized_chatter_record(value: Mapping[str, Any]) -> SanitizedRecord:
    """Alias matching the main-box chatter vocabulary."""

    return validate_sanitized_record(value)


def assert_sanitized_record(value: Mapping[str, Any]) -> SanitizedRecord:
    """Validate and return a normalized record, raising on unsafe input."""

    return validate_sanitized_record(value)


def assert_safe_record(value: Mapping[str, Any]) -> SanitizedRecord:
    """Compatibility alias for safety tests."""

    return validate_sanitized_record(value)
