"""Deterministic feature extraction and analogy matching for World Side.

This module intentionally stays dependency-free and defensive. It accepts
plain dictionaries produced by whatever loader owns the source file and
returns ranked, high-level matches. It does not emit exploit steps, named
targets, payload instructions, or credential paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import re
from typing import Any, Iterable, Mapping, Sequence


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]*")
DATE_RE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")


ADVERSARY_KEYWORDS: dict[str, set[str]] = {
    "PRC": {
        "china",
        "chinese",
        "prc",
        "mss",
        "mps",
        "taiwan",
        "volt",
        "flax",
        "salt",
        "ivanti",
        "hafnium",
        "silk",
        "unc5221",
        "i-soon",
        "isoon",
        "anxun",
        "apt27",
        "apt10",
    },
    "Russia": {
        "russia",
        "russian",
        "gru",
        "svr",
        "fsb",
        "sandworm",
        "apt28",
        "apt29",
        "ukraine",
        "nato",
        "cl0p",
        "clop",
        "lockbit",
        "phobos",
        "noname057",
        "carr",
    },
    "Iran": {
        "iran",
        "iranian",
        "irgc",
        "mois",
        "emennet",
        "shamoon",
        "hormuz",
        "gulf",
        "aramco",
        "oil",
        "cbI".lower(),
    },
    "DPRK": {
        "dprk",
        "north",
        "korea",
        "korean",
        "lazarus",
        "apt38",
        "bluenoroff",
        "rgb",
        "swift",
        "crypto",
        "bybit",
    },
    "criminal-proxy": {
        "ransomware",
        "extortion",
        "cl0p",
        "clop",
        "lockbit",
        "phobos",
        "blacksuit",
        "royal",
        "ta505",
        "fin11",
        "scattered",
        "spider",
    },
}


SECTOR_KEYWORDS: dict[str, set[str]] = {
    "federal-defense-edge": {
        "federal",
        "government",
        "agency",
        "defense",
        "dib",
        "contractor",
        "edge",
        "vpn",
        "gateway",
        "firewall",
        "router",
        "soho",
        "perimeter",
    },
    "critical-infrastructure": {
        "critical",
        "infrastructure",
        "water",
        "wastewater",
        "energy",
        "power",
        "grid",
        "transportation",
        "telecom",
        "communications",
        "port",
        "hospital",
        "healthcare",
        "utility",
    },
    "industrial-control": {
        "ics",
        "ot",
        "scada",
        "plc",
        "sis",
        "triconex",
        "siemens",
        "electric",
        "substation",
        "petrochemical",
        "refinery",
        "pipeline",
        "nuclear",
    },
    "financial": {
        "financial",
        "bank",
        "swift",
        "crypto",
        "exchange",
        "defi",
        "treasury",
        "fed",
        "payment",
        "custody",
        "fomc",
    },
    "election-political": {
        "election",
        "campaign",
        "party",
        "voter",
        "ballot",
        "certification",
        "midterm",
        "primary",
        "parliament",
        "presidential",
    },
    "supply-chain-saas": {
        "supply",
        "chain",
        "software",
        "update",
        "orion",
        "solarwinds",
        "mft",
        "moveit",
        "goanywhere",
        "accellion",
        "saas",
        "managed",
        "transfer",
    },
    "diplomatic": {
        "summit",
        "g7",
        "nato",
        "asean",
        "apec",
        "unga",
        "brics",
        "cop",
        "minister",
        "delegation",
        "embassy",
        "mfa",
    },
}


VECTOR_KEYWORDS: dict[str, set[str]] = {
    "edge-appliance initial access": {
        "edge",
        "vpn",
        "gateway",
        "firewall",
        "router",
        "soho",
        "perimeter",
        "ivanti",
        "fortinet",
        "citrix",
        "netscaler",
        "sonicwall",
        "auth",
        "bypass",
        "rce",
    },
    "living-off-the-land pre-positioning": {
        "pre-position",
        "prepositioning",
        "lotl",
        "living",
        "persistence",
        "stealth",
        "dwell",
        "critical",
        "infrastructure",
    },
    "credential phishing and information operation": {
        "phishing",
        "credential",
        "mail",
        "email",
        "campaign",
        "leak",
        "persona",
        "influence",
        "disinformation",
        "election",
    },
    "software supply-chain compromise": {
        "supply",
        "chain",
        "software",
        "update",
        "build",
        "orion",
        "solarwinds",
        "m.e.doc",
        "medoc",
        "managed",
    },
    "wiper or destructive malware": {
        "wiper",
        "destructive",
        "destroy",
        "wipe",
        "notpetya",
        "shamoon",
        "hermeticwiper",
        "whispergate",
    },
    "financial theft or sanctions-evasion operation": {
        "financial",
        "theft",
        "swift",
        "crypto",
        "exchange",
        "defi",
        "wallet",
        "sanctions",
        "revenue",
        "launder",
    },
    "industrial-control disruption": {
        "ics",
        "ot",
        "scada",
        "plc",
        "sis",
        "grid",
        "substation",
        "electric",
        "water",
        "pipeline",
        "petrochemical",
        "triconex",
    },
    "mass extortion against enterprise services": {
        "ransomware",
        "extortion",
        "mft",
        "moveit",
        "goanywhere",
        "accellion",
        "data",
        "theft",
        "holiday",
        "weekend",
    },
    "collection against diplomatic or policy targets": {
        "summit",
        "diplomatic",
        "mfa",
        "delegation",
        "policy",
        "transition",
        "espionage",
        "collection",
        "think",
        "tank",
    },
}


OBJECTIVE_KEYWORDS: dict[str, set[str]] = {
    "control": {"control", "admin", "administrative", "takeover", "access"},
    "shutdown": {"shutdown", "disable", "offline", "outage"},
    "disruption": {"disruption", "disrupt", "ddos", "wiper", "wipe", "destructive"},
    "data_theft": {"data", "theft", "steal", "exfil", "leak", "extortion"},
    "persistence": {"persistence", "pre-position", "prepositioning", "dwell", "stealth"},
    "financial_theft": {"financial", "swift", "crypto", "heist", "revenue", "launder"},
    "espionage": {"espionage", "collection", "intelligence", "mfa", "diplomatic"},
}


TRIGGER_KEYWORDS: dict[str, set[str]] = {
    "sanctions": {"sanction", "ofac", "sddn", "sdn", "eu", "uk", "treasury", "embargo"},
    "indictment": {"indictment", "charged", "extradited", "sentenced", "trial", "seizure"},
    "election": {"election", "primary", "midterm", "vote", "certification", "campaign"},
    "diplomatic": {"summit", "g7", "nato", "asean", "apec", "unga", "brics", "cop"},
    "anniversary": {"anniversary", "independence", "founding", "national", "day"},
    "holiday": {"holiday", "weekend", "black", "friday", "cyber", "monday", "memorial"},
    "kinetic": {"kinetic", "invasion", "military", "mobilization", "blockade", "strike"},
    "financial": {"fomc", "fed", "market", "rate", "financial", "crypto", "bank"},
    "critical-infra-stress": {"hurricane", "season", "landfall", "heat", "winter", "world", "cup"},
}


@dataclass(frozen=True)
class FeatureVector:
    """Normalized, explainable features used by matcher and scorer."""

    tokens: frozenset[str] = field(default_factory=frozenset)
    adversaries: frozenset[str] = field(default_factory=frozenset)
    sectors: frozenset[str] = field(default_factory=frozenset)
    vectors: frozenset[str] = field(default_factory=frozenset)
    objectives: frozenset[str] = field(default_factory=frozenset)
    trigger_classes: frozenset[str] = field(default_factory=frozenset)
    cve_ids: frozenset[str] = field(default_factory=frozenset)
    cwe_ids: frozenset[str] = field(default_factory=frozenset)
    dates: tuple[date, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "tokens": sorted(self.tokens),
            "adversaries": sorted(self.adversaries),
            "sectors": sorted(self.sectors),
            "vectors": sorted(self.vectors),
            "objectives": sorted(self.objectives),
            "trigger_classes": sorted(self.trigger_classes),
            "cve_ids": sorted(self.cve_ids),
            "cwe_ids": sorted(self.cwe_ids),
            "dates": [d.isoformat() for d in self.dates],
        }


def tokenize(text: str) -> frozenset[str]:
    """Return lowercase word-ish tokens with a few normalized composites."""

    raw = [token.lower() for token in TOKEN_RE.findall(text or "")]
    tokens: set[str] = set(raw)
    joined = " ".join(raw)
    composites = {
        "zero-day": ("zero", "day"),
        "auth-bypass": ("auth", "bypass"),
        "edge-device": ("edge", "device"),
        "supply-chain": ("supply", "chain"),
        "living-off-the-land": ("living", "off", "the", "land"),
        "critical-infrastructure": ("critical", "infrastructure"),
        "defense-industrial-base": ("defense", "industrial", "base"),
    }
    for composite, parts in composites.items():
        if all(part in tokens for part in parts):
            tokens.add(composite)
    if "0" in tokens and "day" in tokens:
        tokens.add("zero-day")
    return frozenset(tokens)


def textify(value: Any) -> str:
    """Flatten strings, mappings, sequences, and dataclasses into text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return textify(value.to_dict())
        except TypeError:
            pass
    if isinstance(value, Mapping):
        return " ".join(textify(v) for v in value.values())
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return " ".join(textify(v) for v in value)
    return str(value)


def parse_dates(value: Any) -> tuple[date, ...]:
    """Extract ISO dates from a record while ignoring malformed values."""

    dates: list[date] = []
    for year, month, day in DATE_RE.findall(textify(value)):
        try:
            dates.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    return tuple(sorted(set(dates)))


def _matches_profile(tokens: set[str], profiles: Mapping[str, set[str]]) -> frozenset[str]:
    matches: set[str] = set()
    for label, keywords in profiles.items():
        if tokens & keywords:
            matches.add(label)
    return frozenset(matches)


def _extract_ids(tokens: Iterable[str], prefix: str) -> frozenset[str]:
    ids = {token.upper() for token in tokens if token.upper().startswith(prefix)}
    return frozenset(ids)


def extract_features(value: Any) -> FeatureVector:
    """Extract feature buckets from arbitrary candidate or context data."""

    text = textify(value)
    tokens = set(tokenize(text))
    return FeatureVector(
        tokens=frozenset(tokens),
        adversaries=_matches_profile(tokens, ADVERSARY_KEYWORDS),
        sectors=_matches_profile(tokens, SECTOR_KEYWORDS),
        vectors=_matches_profile(tokens, VECTOR_KEYWORDS),
        objectives=_matches_profile(tokens, OBJECTIVE_KEYWORDS),
        trigger_classes=_matches_profile(tokens, TRIGGER_KEYWORDS),
        cve_ids=_extract_ids(tokens, "CVE-"),
        cwe_ids=_extract_ids(tokens, "CWE-"),
        dates=parse_dates(value),
    )


def extract_candidate_features(candidate: Mapping[str, Any]) -> FeatureVector:
    """Extract features from Direction A candidate JSON."""

    identity = candidate.get("identity", {})
    attack = candidate.get("attack_hypothesis", {})
    rationale = candidate.get("rationale", {})
    weaponization = candidate.get("weaponization", {})
    focused = {
        "identity": identity,
        "attack_hypothesis": attack,
        "rationale": rationale,
        "weaponization": weaponization,
        "source_refs": candidate.get("source_refs", []),
    }
    return extract_features(focused)


def record_id(record: Any, default_prefix: str = "rec") -> str:
    if isinstance(record, Mapping):
        for key in ("case_id", "id", "event_id", "source_id", "cveID", "cve_id", "window_id"):
            value = record.get(key)
            if value:
                return str(value)
    for attr in ("case_id", "source_id", "cve_id", "context_type"):
        value = getattr(record, attr, None)
        if value:
            if attr == "context_type":
                title = getattr(record, "title", "")
                slug = re.sub(r"[^a-z0-9]+", "_", str(title).lower()).strip("_")
                return f"{value}_{slug}" if slug else str(value)
            return str(value)
    text = textify(record)
    cve_match = re.search(r"CVE-\d{4}-\d{4,}", text, re.IGNORECASE)
    if cve_match:
        return cve_match.group(0).upper()
    return default_prefix


def record_name(record: Any) -> str:
    if isinstance(record, Mapping):
        for key in (
            "case_name",
            "name",
            "event",
            "title",
            "vulnerabilityName",
            "vulnerability_name",
            "target",
            "defendant",
        ):
            value = record.get(key)
            if value:
                return str(value)
    for attr in ("case_name", "title", "name", "event", "label"):
        value = getattr(record, attr, None)
        if value:
            return str(value)
    text = " ".join(textify(record).split())
    return text[:96] + ("..." if len(text) > 96 else "")


def source_ref_ids(record: Any, fallback_prefix: str = "src") -> list[str]:
    if isinstance(record, Mapping):
        explicit = record.get("source_ref_ids") or record.get("source_refs")
        if explicit:
            ids: list[str] = []
            for item in explicit:
                if isinstance(item, Mapping):
                    ids.append(str(item.get("id") or item.get("label") or item.get("url")))
                else:
                    ids.append(str(item))
            return [item for item in ids if item]
    object_sources = getattr(record, "sources", None)
    if object_sources:
        ids = []
        for item in object_sources:
            source_id = getattr(item, "source_id", None)
            if source_id:
                ids.append(str(source_id))
        if ids:
            return ids
    object_urls = getattr(record, "source_urls", None)
    if object_urls:
        return [f"{fallback_prefix}_{idx + 1}" for idx, _ in enumerate(object_urls)]
    rid = record_id(record, fallback_prefix)
    slug = re.sub(r"[^a-z0-9]+", "_", rid.lower()).strip("_") or fallback_prefix
    return [f"{fallback_prefix}_{slug}"]


def feature_overlap(
    left: FeatureVector,
    right: FeatureVector,
    *,
    weights: Mapping[str, float] | None = None,
) -> tuple[float, list[str]]:
    """Weighted overlap score in [0, 1] plus short reason strings."""

    weights = weights or {
        "adversaries": 0.18,
        "sectors": 0.18,
        "vectors": 0.28,
        "objectives": 0.16,
        "trigger_classes": 0.12,
        "cwe_ids": 0.05,
        "cve_ids": 0.03,
    }
    total_weight = sum(weights.values()) or 1.0
    score = 0.0
    reasons: list[str] = []
    for field_name, weight in weights.items():
        left_values = set(getattr(left, field_name))
        right_values = set(getattr(right, field_name))
        if not left_values or not right_values:
            continue
        intersection = left_values & right_values
        if not intersection:
            continue
        field_score = len(intersection) / max(len(left_values), len(right_values), 1)
        score += weight * field_score
        reasons.append(f"{field_name.replace('_', ' ')} overlap: {', '.join(sorted(intersection))}")

    # Textual overlap is intentionally low weight; it breaks ties without
    # overpowering explicit actor/vector/sector features.
    token_overlap = left.tokens & right.tokens
    if token_overlap:
        score += 0.08 * min(len(token_overlap) / 12, 1.0)
        sample = ", ".join(sorted(token_overlap)[:6])
        reasons.append(f"keyword overlap: {sample}")

    return round(min(score / total_weight, 1.0), 4), reasons


def match_historical_cases(
    candidate: Mapping[str, Any] | FeatureVector,
    historical_cases: Sequence[Any],
    *,
    top_n: int = 5,
    min_score: float = 0.05,
) -> list[dict[str, Any]]:
    """Rank historical analogy anchors against a Direction A candidate."""

    candidate_features = (
        candidate if isinstance(candidate, FeatureVector) else extract_candidate_features(candidate)
    )
    matches: list[dict[str, Any]] = []
    for idx, case in enumerate(historical_cases, start=1):
        case_features = extract_features(case)
        score, reasons = feature_overlap(candidate_features, case_features)
        if score < min_score:
            continue
        case_id = record_id(case, f"hist_{idx}") or f"hist_{idx}"
        matches.append(
            {
                "case_id": case_id,
                "case_name": record_name(case),
                "score": score,
                "features": case_features.as_dict(),
                "matched_features": reasons,
                "time_to_burn": _field(case, "time_to_burn", "time-to-burn", default="unknown"),
                "burn_class": _field(case, "burn_class", "burn class", default="unknown"),
                "trigger_class": sorted(case_features.trigger_classes),
                "source_ref_ids": source_ref_ids(case, "src_hist"),
                "raw": case,
            }
        )
    matches.sort(key=lambda item: (-item["score"], item["case_id"]))
    return matches[:top_n]


def match_current_signals(
    candidate: Mapping[str, Any] | FeatureVector,
    records: Sequence[Any],
    *,
    signal_type: str,
    top_n: int = 10,
    min_score: float = 0.02,
) -> list[dict[str, Any]]:
    """Rank calendar, sanctions, indictment, chatter, or KEV records."""

    candidate_features = (
        candidate if isinstance(candidate, FeatureVector) else extract_candidate_features(candidate)
    )
    matches: list[dict[str, Any]] = []
    for idx, record in enumerate(records, start=1):
        features = extract_features(record)
        score, reasons = feature_overlap(
            candidate_features,
            features,
            weights={
                "adversaries": 0.24,
                "sectors": 0.18,
                "vectors": 0.18,
                "objectives": 0.12,
                "trigger_classes": 0.22,
                "cwe_ids": 0.03,
                "cve_ids": 0.03,
            },
        )
        if signal_type == "kev":
            score = max(score, _kev_fit_boost(candidate_features, record, features))
        if score < min_score:
            continue
        rid = record_id(record, f"{signal_type}_{idx}") or f"{signal_type}_{idx}"
        matches.append(
            {
                "signal_id": rid,
                "signal_type": signal_type,
                "label": record_name(record),
                "score": round(min(score, 1.0), 4),
                "features": features.as_dict(),
                "matched_features": reasons,
                "dates": [d.isoformat() for d in features.dates],
                "source_ref_ids": source_ref_ids(record, f"src_{signal_type}"),
                "raw": record,
            }
        )
    matches.sort(key=lambda item: (-item["score"], item["signal_id"]))
    return matches[:top_n]


def _field(record: Any, *keys: str, default: str = "") -> str:
    if isinstance(record, Mapping):
        lowered = {str(key).lower(): value for key, value in record.items()}
        for key in keys:
            value = lowered.get(key.lower())
            if value:
                return str(value)
    for key in keys:
        attr = key.lower().replace("-", "_").replace(" ", "_")
        value = getattr(record, attr, None)
        if value:
            return str(value)
    return default


def _kev_fit_boost(
    candidate_features: FeatureVector,
    record: Any,
    kev_features: FeatureVector,
) -> float:
    """Boost KEV matches when CVE/CWE/product or ransomware fields align."""

    boost = 0.0
    if candidate_features.cve_ids & kev_features.cve_ids:
        boost += 0.55
    if candidate_features.cwe_ids & kev_features.cwe_ids:
        boost += 0.25
    if candidate_features.sectors & kev_features.sectors:
        boost += 0.12
    if candidate_features.vectors & kev_features.vectors:
        boost += 0.12
    if isinstance(record, Mapping):
        ransomware_use = str(record.get("knownRansomwareCampaignUse", "")).lower()
        if ransomware_use == "known":
            boost += 0.08
    return round(min(boost, 1.0), 4)


def candidate_priority_score(candidate: Mapping[str, Any]) -> float:
    """Cyber-side technical score normalized into [0, 1]."""

    rationale = candidate.get("rationale", {}) if isinstance(candidate, Mapping) else {}
    value = rationale.get("stage1_priority_score")
    try:
        if value is not None:
            return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        pass
    confidence = str(rationale.get("confidence", "")).lower()
    return {"high": 0.82, "medium": 0.58, "low": 0.34}.get(confidence, 0.45)
