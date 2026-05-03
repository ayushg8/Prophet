"""Sanitized record model and safety validation.

The scraper machine may observe raw collection data, but records emitted from
this package must not carry raw posts, credential material, onion addresses, or
exploit payload details. The shape mirrors the forecaster's sanitized chatter
JSONL contract so records can be consumed directly by ``forecaster.chatter``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping
from urllib.parse import urlparse


ALLOWED_SOURCE_TYPES = {
    "telegram_public_channel",
    "public_forum",
    "public_social",
    "onion_public_metadata",
    "official_government",
    "threat_intel_feed",
    "vendor_advisory",
    "manual_analyst_note",
}

ALLOWED_COLLECTION_TIERS = {
    "official_signal",
    "public_chatter",
    "technical_chatter",
    "darkweb_metadata",
    "analyst_context",
}

ALLOWED_CONFIDENCE = {"high", "medium", "low"}

ALLOWED_RECORD_KEYS = {
    "record_id",
    "observed_at",
    "source_type",
    "collection_tier",
    "actor_hint",
    "region_hint",
    "target_sector",
    "vector_class",
    "motive_hint",
    "confidence",
    "summary",
    "source_ref",
    "tags",
}

ALLOWED_SOURCE_REF_KEYS = {
    "id",
    "label",
    "url",
    "date",
    "supports",
}

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
    "passwd",
    "token",
    "api_key",
    "apikey",
    "secret",
    "session",
    "session_file",
    "onion",
    "onion_url",
    "invite_link",
    "phone",
    "email",
    "payload",
    "poc",
    "proof_of_concept",
    "exploit_code",
    "shellcode",
}

BANNED_VALUE_PATTERNS = [
    (re.compile(r"\.onion\b", re.IGNORECASE), "onion address"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|token)\s*[:=]", re.IGNORECASE), "credential material"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "raw IP address"),
    (re.compile(r"\b(?:reverse shell|shellcode|metasploit|exploit payload|proof[- ]of[- ]concept)\b", re.IGNORECASE), "exploit payload detail"),
    (re.compile(r"\b(?:cmd\.exe|powershell|/bin/sh|/bin/bash)\b", re.IGNORECASE), "command execution detail"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "email address"),
    (re.compile(r"\b(?:t\.me|telegram\.me|discord\.gg|joinchat)\b", re.IGNORECASE), "private or invite link"),
    (re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{3,}"), "social handle"),
]

SAFE_URL_SCHEMES = {"https", "sanitized"}


class RecordValidationError(ValueError):
    """Raised when a record is unsafe or does not match the sanitized schema."""


@dataclass(frozen=True)
class SanitizedRecord:
    """A safe, forecast-ready signal from an official feed or sanitized source."""

    record_id: str
    observed_at: str
    source_type: str
    collection_tier: str
    actor_hint: str
    region_hint: str
    target_sector: str
    vector_class: str
    motive_hint: str
    confidence: str
    summary: str
    source_ref: dict[str, str]
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        source_name: str = "sanitized record",
    ) -> "SanitizedRecord":
        if not isinstance(value, Mapping):
            raise RecordValidationError(f"{source_name}: record must be an object")

        _assert_allowed_keys(value, ALLOWED_RECORD_KEYS, source_name)
        _assert_no_raw_material(value, source_name)

        record_id = _required_str(value, "record_id", source_name)
        observed_at = _required_str(value, "observed_at", source_name)
        _parse_datetime(observed_at, f"{source_name} {record_id}.observed_at")

        source_type = _required_str(value, "source_type", source_name)
        if source_type not in ALLOWED_SOURCE_TYPES:
            raise RecordValidationError(
                f"{source_name} {record_id}: unsupported source_type {source_type}"
            )

        collection_tier = _required_str(value, "collection_tier", source_name)
        if collection_tier not in ALLOWED_COLLECTION_TIERS:
            raise RecordValidationError(
                f"{source_name} {record_id}: unsupported collection_tier {collection_tier}"
            )

        confidence = _required_str(value, "confidence", source_name)
        if confidence not in ALLOWED_CONFIDENCE:
            raise RecordValidationError(
                f"{source_name} {record_id}: confidence must be high|medium|low"
            )

        summary = _required_str(value, "summary", source_name)
        if len(summary) > 500:
            raise RecordValidationError(
                f"{source_name} {record_id}: summary must stay under 500 chars"
            )

        source_ref = _source_ref(value.get("source_ref"), record_id, observed_at, summary)
        tags = _safe_tags(value.get("tags", []), record_id)

        record = cls(
            record_id=record_id,
            observed_at=observed_at,
            source_type=source_type,
            collection_tier=collection_tier,
            actor_hint=_optional_str(value, "actor_hint"),
            region_hint=_optional_str(value, "region_hint"),
            target_sector=_optional_str(value, "target_sector"),
            vector_class=_optional_str(value, "vector_class"),
            motive_hint=_optional_str(value, "motive_hint"),
            confidence=confidence,
            summary=summary,
            source_ref=source_ref,
            tags=tags,
        )
        record.validate(source_name=source_name)
        return record

    @property
    def observed_date(self) -> date:
        return _parse_datetime(self.observed_at, f"{self.record_id}.observed_at").date()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not self.tags:
            payload.pop("tags", None)
        return payload

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=False)

    def validate(self, *, source_name: str = "sanitized record") -> None:
        _assert_no_raw_material(self.to_dict(), source_name)
        _source_ref(self.source_ref, self.record_id, self.observed_at, self.summary)


def make_source_ref(
    *,
    label: str,
    url: str,
    date_value: str,
    supports: str,
    source_id: str | None = None,
) -> dict[str, str]:
    """Build a source reference after applying URL and text safety checks."""

    ref = {
        "id": source_id or stable_id("src", url, label),
        "label": label.strip(),
        "url": url.strip(),
        "date": date_value.strip(),
        "supports": supports.strip(),
    }
    return _source_ref(ref, ref["id"], _date_to_datetime(date_value), supports)


def stable_id(prefix: str, *parts: str) -> str:
    digest_input = "\n".join(part.strip() for part in parts if part)
    digest = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_ref(
    value: Any,
    record_id: str,
    observed_at: str,
    summary: str,
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise RecordValidationError(f"{record_id}: source_ref must be an object")
    _assert_allowed_keys(value, ALLOWED_SOURCE_REF_KEYS, f"{record_id}.source_ref")
    source_id = _optional_str(value, "id") or stable_id("src", record_id)
    label = _required_str(value, "label", record_id)
    url = _required_str(value, "url", record_id)
    date_value = _optional_str(value, "date") or _parse_datetime(
        observed_at,
        f"{record_id}.observed_at",
    ).date().isoformat()
    supports = _optional_str(value, "supports") or _truncate(summary, 180)

    _assert_safe_string(source_id, f"{record_id}.source_ref.id")
    _assert_safe_string(label, f"{record_id}.source_ref.label")
    _assert_safe_url(url, f"{record_id}.source_ref.url")
    _assert_safe_string(date_value, f"{record_id}.source_ref.date")
    _assert_safe_string(supports, f"{record_id}.source_ref.supports")

    return {
        "id": source_id,
        "label": label,
        "url": url,
        "date": date_value,
        "supports": supports,
    }


def validate_sanitized_record(value: Mapping[str, Any]) -> SanitizedRecord:
    """Validate one sanitized record and return its normalized dataclass."""

    return SanitizedRecord.from_mapping(value)


def _safe_tags(value: Any, record_id: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise RecordValidationError(f"{record_id}: tags must be a list when present")
    tags: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise RecordValidationError(f"{record_id}: tags[{idx}] must be a string")
        tag = _slug(item)
        _assert_safe_string(tag, f"{record_id}.tags[{idx}]")
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _assert_no_raw_material(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).strip().lower()
            if key_text in BANNED_RAW_KEYS:
                raise RecordValidationError(f"{path}: banned raw field {key}")
            _assert_no_raw_material(nested, f"{path}.{key}")
        return
    if isinstance(value, list):
        for idx, nested in enumerate(value):
            _assert_no_raw_material(nested, f"{path}[{idx}]")
        return
    if isinstance(value, str):
        _assert_safe_string(value, path)


def _assert_allowed_keys(
    value: Mapping[str, Any],
    allowed: set[str],
    path: str,
) -> None:
    unknown = sorted(str(key) for key in value if str(key) not in allowed)
    if unknown:
        raise RecordValidationError(f"{path}: unsupported field(s): {', '.join(unknown)}")


def _assert_safe_string(value: str, path: str) -> None:
    for pattern, label in BANNED_VALUE_PATTERNS:
        if pattern.search(value):
            raise RecordValidationError(f"{path}: contains {label}")


def _assert_safe_url(value: str, path: str) -> None:
    _assert_safe_string(value, path)
    parsed = urlparse(value)
    if parsed.scheme not in SAFE_URL_SCHEMES:
        raise RecordValidationError(f"{path}: URL scheme must be https or sanitized")
    if parsed.username or parsed.password:
        raise RecordValidationError(f"{path}: URL must not contain credentials")


def _required_str(value: Mapping[str, Any], key: str, source_name: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise RecordValidationError(f"{source_name}: missing or invalid {key}")
    clean = re.sub(r"\s+", " ", result).strip()
    _assert_safe_string(clean, f"{source_name}.{key}")
    return clean


def _optional_str(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if result is None:
        return ""
    if not isinstance(result, str):
        raise RecordValidationError(f"{key} must be a string when present")
    clean = re.sub(r"\s+", " ", result).strip()
    _assert_safe_string(clean, key)
    return clean


def _parse_datetime(value: str, label: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordValidationError(f"{label} must be ISO 8601 datetime") from exc


def _date_to_datetime(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return utc_now()
    return f"{parsed.isoformat()}T00:00:00Z"


def _truncate(value: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", value).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "."


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
