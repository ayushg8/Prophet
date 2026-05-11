"""Schemas and validation for Prophet World Side forecast artifacts.

The project intentionally avoids runtime dependencies during the hackathon.
These helpers provide a small, explicit validation layer for the Direction A
and Direction B JSON contracts in ``world-side/INTERFACE.md``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import json
import re
from typing import Any


WORLD_FORECAST_SCHEMA_VERSION = "world_forecast.v0.1"

CONFIDENCE_LABELS = {"high", "medium", "low"}
CANDIDATE_TYPES = {
    "known_cve",
    "representative_cve",
    "hypothesized_zero_day",
    "exploit_class",
}
INTENDED_EFFECTS = {
    "control",
    "shutdown",
    "disruption",
    "data_theft",
    "persistence",
    "unknown",
}
DESTRUCTIVENESS = {
    "non_destructive",
    "disruptive",
    "destructive",
    "unknown",
}
PUBLIC_STATUSES = {
    "not_found",
    "public_poc_found",
    "observed_in_wild",
    "known_cve_overlap",
    "unknown",
}

BANNED_VECTOR_KEYS = {
    "named_live_target",
    "named_live_targets",
    "live_target",
    "live_targets",
    "payload",
    "procedure",
    "procedures",
    "steps",
    "exploit_steps",
    "target_control_steps",
    "command",
    "commands",
    "shell",
    "target_host",
    "hostname",
    "ip",
    "ip_address",
    "credential",
    "credentials",
    "username",
    "password",
}

IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
HOSTNAME_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|mil|gov|edu|io|dev|local|lan|internal|corp|private)\b",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|token)\s*[:=])",
    re.IGNORECASE,
)
URL_RE = re.compile(r"\b(?:https?|ssh|ftp)://", re.IGNORECASE)
PAYLOAD_TOKENS = (
    "${jndi:",
    "${${",
    "ldap://",
    "rmi://",
    "dns://",
    "runtime.getruntime",
    "cmd.exe",
    "marshalsec",
    "ysoserial",
    "mimikatz",
)
PROCEDURAL_PHRASES = (
    "curl ",
    "powershell ",
    "bash ",
    "ssh ",
    "run the following",
    "execute the following",
    "send the request",
    "paste this",
)


class ValidationError(ValueError):
    """Raised when a candidate or forecast artifact does not match contract."""


@dataclass(frozen=True)
class SourceRef:
    id: str
    label: str
    url: str
    date: str = ""
    supports: str = ""

    @classmethod
    def from_mapping(
        cls,
        value: dict[str, Any],
        fallback_id: str = "",
        *,
        require_id: bool = False,
        require_date: bool = False,
        require_supports: bool = False,
    ) -> "SourceRef":
        if not isinstance(value, dict):
            raise ValidationError("source_ref must be object")
        raw_id = value.get("id")
        source_id = str(raw_id or fallback_id or value.get("label") or "").strip()
        label = str(value.get("label") or source_id).strip()
        url = str(value.get("url") or "").strip()
        date = str(value.get("date") or "").strip()
        supports = str(value.get("supports") or "").strip()
        if require_id and not raw_id:
            raise ValidationError("source_ref missing required id")
        if not source_id:
            raise ValidationError("source_ref missing id")
        if not label:
            raise ValidationError(f"source_ref {source_id} missing label")
        if not url:
            raise ValidationError(f"source_ref {source_id} missing url")
        if require_date and not date:
            raise ValidationError(f"source_ref {source_id} missing date")
        if date:
            _validate_date_string(date, f"source_ref {source_id} date")
        if require_supports and not supports:
            raise ValidationError(f"source_ref {source_id} missing supports")
        return cls(id=source_id, label=label, url=url, date=date, supports=supports)

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExploitCandidate:
    candidate_id: str
    generated_at: str
    identity: dict[str, Any]
    attack_hypothesis: dict[str, Any]
    rationale: dict[str, Any]
    weaponization: dict[str, Any] = field(default_factory=dict)
    source_refs: list[SourceRef] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ExploitCandidate":
        if not isinstance(value, dict):
            raise ValidationError("candidate must be a JSON object")
        _validate_candidate_safe(value, "candidate")
        candidate_id = _required_str(value, "candidate_id")
        generated_at = _required_str(value, "generated_at")
        _validate_datetime_string(generated_at, "generated_at")
        identity = _required_mapping(value, "identity")
        attack_hypothesis = _required_mapping(value, "attack_hypothesis")
        rationale = _required_mapping(value, "rationale")
        weaponization = value.get("weaponization") or {}
        if not isinstance(weaponization, dict):
            raise ValidationError("weaponization must be an object when present")

        candidate_type = _required_str(identity, "candidate_type")
        if candidate_type not in CANDIDATE_TYPES:
            raise ValidationError(f"unknown candidate_type: {candidate_type}")
        _required_str(identity, "candidate_label")
        if candidate_type == "known_cve" and not identity.get("cve_id"):
            raise ValidationError("known_cve candidates require identity.cve_id")
        if candidate_type in {"hypothesized_zero_day", "exploit_class"}:
            _required_str(identity, "cve_class_label")
        _required_str(identity, "target_product")

        intended_effect = _required_str(attack_hypothesis, "intended_effect")
        if intended_effect not in INTENDED_EFFECTS:
            raise ValidationError(f"unknown intended_effect: {intended_effect}")
        destructiveness = _required_str(attack_hypothesis, "destructiveness")
        if destructiveness not in DESTRUCTIVENESS:
            raise ValidationError(f"unknown destructiveness: {destructiveness}")
        _required_str(attack_hypothesis, "attack_vector")
        _required_str(attack_hypothesis, "narrative")

        confidence = _required_str(rationale, "confidence")
        if confidence not in CONFIDENCE_LABELS:
            raise ValidationError(f"unknown rationale confidence: {confidence}")
        _required_str(rationale, "narrative")

        if weaponization:
            public_status = weaponization.get("public_status")
            if public_status is not None and public_status not in PUBLIC_STATUSES:
                raise ValidationError(f"unknown public_status: {public_status}")

        raw_refs = value.get("source_refs")
        if not isinstance(raw_refs, list) or not raw_refs:
            raise ValidationError("candidate requires non-empty source_refs")
        refs = [
            SourceRef.from_mapping(
                item,
                fallback_id=f"candidate_src_{idx + 1}",
                require_supports=True,
            )
            for idx, item in enumerate(raw_refs)
        ]
        return cls(
            candidate_id=candidate_id,
            generated_at=generated_at,
            identity=identity,
            attack_hypothesis=attack_hypothesis,
            rationale=rationale,
            weaponization=weaponization,
            source_refs=refs,
            raw=value,
        )

    @property
    def label(self) -> str:
        return str(self.identity.get("candidate_label") or self.candidate_id)

    @property
    def cve_id(self) -> str | None:
        cve_id = self.identity.get("cve_id")
        return str(cve_id) if cve_id else None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "generated_at": self.generated_at,
            "identity": dict(self.identity),
            "attack_hypothesis": dict(self.attack_hypothesis),
            "rationale": dict(self.rationale),
            "weaponization": dict(self.weaponization),
            "source_refs": [ref.to_mapping() for ref in self.source_refs],
        }


@dataclass(frozen=True)
class StrategicFrame:
    adversary_class: str
    target_scope: str
    geographic_scope: str
    forecast_assumptions: list[str]
    excluded_uses: list[str]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "StrategicFrame":
        if not isinstance(value, dict):
            raise ValidationError("strategic_frame must be object")
        excluded_uses = _required_string_list(value, "excluded_uses")
        exclusions = " | ".join(excluded_uses).lower()
        required_terms = {
            "No exploit payloads": ("exploit", "payload"),
            "No target-control instructions": ("target", "control", "instruction"),
            "No named live targets": ("named", "live", "target"),
        }
        for label, terms in required_terms.items():
            if not all(term in exclusions for term in terms):
                raise ValidationError(f"strategic_frame.excluded_uses must include {label}")
        return cls(
            adversary_class=_required_str(value, "adversary_class"),
            target_scope=_required_str(value, "target_scope"),
            geographic_scope=_required_str(value, "geographic_scope"),
            forecast_assumptions=_required_string_list(value, "forecast_assumptions"),
            excluded_uses=excluded_uses,
        )

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalAnalogy:
    case_id: str
    case_name: str
    pattern_matched: str
    time_to_burn: str
    source_ref_ids: list[str]

    @classmethod
    def from_mapping(
        cls, value: dict[str, Any], source_ids: set[str] | None = None
    ) -> "HistoricalAnalogy":
        if not isinstance(value, dict):
            raise ValidationError("historical analogy must be object")
        ref_ids = _required_string_list(value, "source_ref_ids")
        if source_ids is not None:
            _validate_source_ids(ref_ids, source_ids)
        return cls(
            case_id=_required_str(value, "case_id"),
            case_name=_required_str(value, "case_name"),
            pattern_matched=_required_str(value, "pattern_matched"),
            time_to_burn=_required_str(value, "time_to_burn"),
            source_ref_ids=ref_ids,
        )

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrikeWindow:
    window_id: str
    rank: int
    start_date: str
    end_date: str
    confidence: str
    confidence_score: float
    why_this_window: str
    trigger_signals: list[str]
    historical_analogies: list[HistoricalAnalogy]
    source_ref_ids: list[str]

    @classmethod
    def from_mapping(
        cls, value: dict[str, Any], source_ids: set[str] | None = None
    ) -> "StrikeWindow":
        _validate_ranked_item(value, source_ids or set(), item_type="strike_window")
        start_date = _required_str(value, "start_date")
        end_date = _required_str(value, "end_date")
        _validate_date_string(start_date, "strike_window.start_date")
        _validate_date_string(end_date, "strike_window.end_date")
        if date.fromisoformat(start_date) > date.fromisoformat(end_date):
            raise ValidationError("strike_window start_date must be on or before end_date")
        analogies = [
            HistoricalAnalogy.from_mapping(item, source_ids)
            for item in _required_list(value, "historical_analogies")
        ]
        return cls(
            window_id=_required_str(value, "window_id"),
            rank=value["rank"],
            start_date=start_date,
            end_date=end_date,
            confidence=value["confidence"],
            confidence_score=float(value["confidence_score"]),
            why_this_window=_required_str(value, "why_this_window"),
            trigger_signals=_required_string_list(value, "trigger_signals"),
            historical_analogies=analogies,
            source_ref_ids=_required_string_list(value, "source_ref_ids"),
        )

    def to_mapping(self) -> dict[str, Any]:
        result = asdict(self)
        result["historical_analogies"] = [
            analogy.to_mapping() for analogy in self.historical_analogies
        ]
        return result


@dataclass(frozen=True)
class StrikeVector:
    vector_id: str
    rank: int
    vector_class: str
    target_sector: str
    likely_objective: str
    non_actionable_mechanism: str
    candidate_fit: str
    confidence: str
    confidence_score: float
    why_this_vector: str
    defensive_implication: str
    source_ref_ids: list[str]

    @classmethod
    def from_mapping(
        cls, value: dict[str, Any], source_ids: set[str] | None = None
    ) -> "StrikeVector":
        _validate_ranked_item(value, source_ids or set(), item_type="strike_vector")
        _validate_non_actionable_vector(value)
        likely_objective = _required_str(value, "likely_objective")
        if likely_objective not in INTENDED_EFFECTS:
            raise ValidationError(f"unknown likely_objective: {likely_objective}")
        return cls(
            vector_id=_required_str(value, "vector_id"),
            rank=value["rank"],
            vector_class=_required_str(value, "vector_class"),
            target_sector=_required_str(value, "target_sector"),
            likely_objective=likely_objective,
            non_actionable_mechanism=_required_str(value, "non_actionable_mechanism"),
            candidate_fit=_required_str(value, "candidate_fit"),
            confidence=value["confidence"],
            confidence_score=float(value["confidence_score"]),
            why_this_vector=_required_str(value, "why_this_vector"),
            defensive_implication=_required_str(value, "defensive_implication"),
            source_ref_ids=_required_string_list(value, "source_ref_ids"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Summary:
    one_line: str
    recommended_demo_path: str
    stage3_priority: str
    analyst_notes: list[str]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Summary":
        if not isinstance(value, dict):
            raise ValidationError("summary must be object")
        return cls(
            one_line=_required_str(value, "one_line"),
            recommended_demo_path=_required_str(value, "recommended_demo_path"),
            stage3_priority=_required_str(value, "stage3_priority"),
            analyst_notes=_required_string_list(value, "analyst_notes", allow_empty=True),
        )

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorldForecast:
    forecast_id: str
    generated_at: str
    input_candidate_id: str
    schema_version: str
    strategic_frame: StrategicFrame
    strike_windows: list[StrikeWindow]
    strike_vectors: list[StrikeVector]
    summary: Summary
    source_refs: list[SourceRef]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "WorldForecast":
        if not isinstance(value, dict):
            raise ValidationError("forecast must be a JSON object")
        for key in [
            "forecast_id",
            "generated_at",
            "input_candidate_id",
            "schema_version",
            "strategic_frame",
            "strike_windows",
            "strike_vectors",
            "summary",
            "source_refs",
        ]:
            if key not in value:
                raise ValidationError(f"forecast missing {key}")

        generated_at = _required_str(value, "generated_at")
        _validate_datetime_string(generated_at, "generated_at")
        schema_version = _required_str(value, "schema_version")
        if schema_version != WORLD_FORECAST_SCHEMA_VERSION:
            raise ValidationError(
                f"schema_version must be {WORLD_FORECAST_SCHEMA_VERSION}"
            )

        source_refs = [
            SourceRef.from_mapping(
                item,
                require_id=True,
                require_date=True,
                require_supports=True,
            )
            for item in _required_list(value, "source_refs")
        ]
        source_ids = _unique_source_ids(source_refs)
        return cls(
            forecast_id=_required_str(value, "forecast_id"),
            generated_at=generated_at,
            input_candidate_id=_required_str(value, "input_candidate_id"),
            schema_version=schema_version,
            strategic_frame=StrategicFrame.from_mapping(
                _required_mapping(value, "strategic_frame")
            ),
            strike_windows=[
                StrikeWindow.from_mapping(item, source_ids)
                for item in _required_list(value, "strike_windows")
            ],
            strike_vectors=[
                StrikeVector.from_mapping(item, source_ids)
                for item in _required_list(value, "strike_vectors")
            ],
            summary=Summary.from_mapping(_required_mapping(value, "summary")),
            source_refs=source_refs,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "generated_at": self.generated_at,
            "input_candidate_id": self.input_candidate_id,
            "schema_version": self.schema_version,
            "strategic_frame": self.strategic_frame.to_mapping(),
            "strike_windows": [window.to_mapping() for window in self.strike_windows],
            "strike_vectors": [vector.to_mapping() for vector in self.strike_vectors],
            "summary": self.summary.to_mapping(),
            "source_refs": [ref.to_mapping() for ref in self.source_refs],
        }


def validate_world_forecast(value: dict[str, Any] | str) -> None:
    """Validate a Direction B forecast object.

    This enforces shape, source-ref coverage, confidence ranges, and a coarse
    structural non-actionability check for strike vector payloads.
    """

    WorldForecast.from_mapping(_coerce_json_object(value, "forecast"))


def validate_exploit_candidate(value: dict[str, Any] | str) -> None:
    """Validate a Direction A exploit candidate object."""

    ExploitCandidate.from_mapping(_coerce_json_object(value, "candidate"))


def parse_exploit_candidate(value: dict[str, Any] | str) -> ExploitCandidate:
    """Parse and validate a Direction A exploit candidate."""

    return ExploitCandidate.from_mapping(_coerce_json_object(value, "candidate"))


def parse_world_forecast(value: dict[str, Any] | str) -> WorldForecast:
    """Parse and validate a Direction B World Side forecast."""

    return WorldForecast.from_mapping(_coerce_json_object(value, "forecast"))


def _validate_ranked_item(item: Any, source_ids: set[str], item_type: str) -> None:
    if not isinstance(item, dict):
        raise ValidationError(f"{item_type} must be object")
    rank = item.get("rank")
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
        raise ValidationError(f"{item_type} rank must be positive integer")
    confidence = _required_str(item, "confidence")
    if confidence not in CONFIDENCE_LABELS:
        raise ValidationError(f"{item_type} confidence must be high|medium|low")
    score = item.get("confidence_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
        raise ValidationError(f"{item_type} confidence_score must be 0.0-1.0")
    _validate_source_ids(item.get("source_ref_ids") or [], source_ids)


def _validate_source_ids(ref_ids: Any, source_ids: set[str]) -> None:
    if not isinstance(ref_ids, list) or not ref_ids:
        raise ValidationError("source_ref_ids must be a non-empty list")
    invalid = [ref_id for ref_id in ref_ids if not isinstance(ref_id, str) or not ref_id.strip()]
    if invalid:
        raise ValidationError("source_ref_ids must contain non-empty strings")
    missing = [ref_id for ref_id in ref_ids if ref_id not in source_ids]
    if missing:
        raise ValidationError(f"unknown source_ref_ids: {missing}")


def _validate_non_actionable_vector(vector: dict[str, Any]) -> None:
    lower_keys = {str(key).lower() for key in vector}
    blocked = sorted(
        key
        for key in lower_keys
        if key in BANNED_VECTOR_KEYS
        or "procedure" in key
        or key.startswith("named_live_target")
    )
    if blocked:
        raise ValidationError(f"strike vector contains banned actionable keys: {blocked}")
    mechanism = str(vector.get("non_actionable_mechanism") or "").lower()
    for phrase in ["run ", "execute ", "curl ", "powershell", "bash ", "ssh ", "password"]:
        if phrase in mechanism:
            raise ValidationError("non_actionable_mechanism contains procedural language")


def _validate_candidate_safe(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if (
                lowered in BANNED_VECTOR_KEYS
                or lowered.startswith("named_live_target")
                or "payload" in lowered
                or "credential" in lowered
            ):
                raise ValidationError(f"{path} contains banned candidate key: {key}")
            _validate_candidate_safe(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _validate_candidate_safe(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        _validate_candidate_text_safe(value, path)


def _validate_candidate_text_safe(value: str, path: str) -> None:
    lowered = value.lower()
    for phrase in PROCEDURAL_PHRASES:
        if phrase in lowered:
            raise ValidationError(f"{path} contains procedural phrase: {phrase!r}")
    for token in PAYLOAD_TOKENS:
        if token in lowered:
            raise ValidationError(f"{path} contains payload-like token: {token!r}")
    if EMAIL_RE.search(value):
        raise ValidationError(f"{path} contains email-like text")
    if SECRET_RE.search(value):
        raise ValidationError(f"{path} contains credential-like text")
    if _path_allows_public_source_url(path):
        return
    if URL_RE.search(value):
        raise ValidationError(f"{path} contains URL-like text outside source_refs.url")
    live_ips = [ip for ip in IP_RE.findall(value) if not _allowed_non_live_ip(ip)]
    if live_ips:
        raise ValidationError(f"{path} contains live-IP-like text")
    if HOSTNAME_RE.search(value):
        raise ValidationError(f"{path} contains hostname-like text")


def _path_allows_public_source_url(path: str) -> bool:
    return ".source_refs[" in path and path.endswith(".url")


def _allowed_non_live_ip(raw_ip: str) -> bool:
    return (
        raw_ip.startswith("127.")
        or raw_ip == "0.0.0.0"
        or raw_ip.startswith("192.0.2.")
        or raw_ip.startswith("198.51.100.")
        or raw_ip.startswith("203.0.113.")
    )


def _required_mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ValidationError(f"missing or invalid object: {key}")
    return result


def _required_list(value: dict[str, Any], key: str) -> list[Any]:
    result = value.get(key)
    if not isinstance(result, list) or not result:
        raise ValidationError(f"missing or invalid non-empty list: {key}")
    return result


def _required_string_list(
    value: dict[str, Any], key: str, *, allow_empty: bool = False
) -> list[str]:
    result = value.get(key)
    if not isinstance(result, list) or (not allow_empty and not result):
        raise ValidationError(f"missing or invalid list: {key}")
    strings: list[str] = []
    for item in result:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{key} must contain non-empty strings")
        strings.append(item.strip())
    return strings


def _required_str(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValidationError(f"missing or invalid string: {key}")
    return result.strip()


def _coerce_json_object(value: dict[str, Any] | str, label: str) -> dict[str, Any]:
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValidationError(f"{label} JSON must decode to an object")
        return parsed
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def _unique_source_ids(source_refs: list[SourceRef]) -> set[str]:
    source_ids: set[str] = set()
    duplicates: set[str] = set()
    for ref in source_refs:
        if ref.id in source_ids:
            duplicates.add(ref.id)
        source_ids.add(ref.id)
    if duplicates:
        raise ValidationError(f"duplicate source_ref ids: {sorted(duplicates)}")
    return source_ids


def _validate_datetime_string(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be ISO 8601 datetime") from exc


def _validate_date_string(value: str, label: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{label} must be YYYY-MM-DD") from exc
