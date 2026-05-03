"""Strike-window and strike-vector scoring for Prophet World Side.

The scorer is deterministic, source-preserving, and deliberately high-level.
It ranks when a capability is plausibly spent and which defensive vector class
best matches the candidate/context. It does not produce attack procedures.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import math
import re
from typing import Any, Mapping, Sequence

try:  # Support both package imports and direct script loading.
    from .matcher import (
        FeatureVector,
        candidate_priority_score,
        extract_candidate_features,
        extract_features,
        feature_overlap,
        match_current_signals,
        match_historical_cases,
        record_name,
        source_ref_ids,
    )
except ImportError:  # pragma: no cover - used when run from this directory.
    from matcher import (  # type: ignore
        FeatureVector,
        candidate_priority_score,
        extract_candidate_features,
        extract_features,
        feature_overlap,
        match_current_signals,
        match_historical_cases,
        record_name,
        source_ref_ids,
    )


CONFIDENCE_THRESHOLDS = ((0.72, "high"), (0.23, "medium"), (0.0, "low"))
ALLOWED_OBJECTIVES = {"control", "shutdown", "disruption", "data_theft", "persistence", "unknown"}


VECTOR_PROFILES: dict[str, dict[str, str]] = {
    "edge-appliance initial access": {
        "target_sector": "federal, defense-industrial, and critical-infrastructure perimeter services",
        "likely_objective": "persistence",
        "mechanism": "Use exposed perimeter infrastructure as a foothold and selection point; keep analysis at ATT&CK/vector-class level.",
        "defensive": "Prioritize perimeter-device inventory, emergency patch validation, log review, and detection for anomalous management-plane activity.",
    },
    "living-off-the-land pre-positioning": {
        "target_sector": "critical infrastructure and defense-support enterprise networks",
        "likely_objective": "persistence",
        "mechanism": "Maintain low-noise access with ordinary administration tooling until a separate strategic trigger raises activation risk.",
        "defensive": "Prioritize behavioral detections for admin-tool misuse, account hygiene, and egress review from critical services.",
    },
    "credential phishing and information operation": {
        "target_sector": "election, diplomatic, policy, and civil-society organizations",
        "likely_objective": "data_theft",
        "mechanism": "Harvest access to politically valuable communications and use downstream disclosure or influence effects.",
        "defensive": "Prioritize phishing-resistant authentication, mailbox auditing, and monitoring for suspicious OAuth or forwarding-rule behavior.",
    },
    "software supply-chain compromise": {
        "target_sector": "federal civilian agencies, software vendors, and managed-service ecosystems",
        "likely_objective": "persistence",
        "mechanism": "Abuse trusted update or service relationships to reach many downstream organizations without naming live targets.",
        "defensive": "Prioritize build-pipeline integrity checks, vendor telemetry review, and anomalous update-channel detection.",
    },
    "wiper or destructive malware": {
        "target_sector": "government, critical infrastructure, and crisis-adjacent enterprise networks",
        "likely_objective": "disruption",
        "mechanism": "Spend pre-positioned access for availability impact during a symbolic, crisis, or kinetic window.",
        "defensive": "Prioritize backup isolation, destructive-action detections, privileged-access review, and incident-response readiness.",
    },
    "financial theft or sanctions-evasion operation": {
        "target_sector": "banks, crypto platforms, payment rails, and financial-service vendors",
        "likely_objective": "data_theft",
        "mechanism": "Convert access into revenue or liquidity during sanctions or market-pressure windows.",
        "defensive": "Prioritize transaction-monitoring controls, withdrawal throttles, privileged finance-system access review, and wallet-risk monitoring.",
    },
    "industrial-control disruption": {
        "target_sector": "water, energy, transport, petrochemical, and other OT environments",
        "likely_objective": "shutdown",
        "mechanism": "Use already-established OT/ICS access or adjacent enterprise access to create service disruption at a symbolic or stress point.",
        "defensive": "Prioritize OT segmentation, manual fallback checks, engineering-workstation monitoring, and safety-system integrity review.",
    },
    "mass extortion against enterprise services": {
        "target_sector": "managed file transfer, SaaS, retail, logistics, healthcare, and government vendors",
        "likely_objective": "data_theft",
        "mechanism": "Burn a broadly useful enterprise-service weakness around a response-gap window for maximum leverage.",
        "defensive": "Prioritize externally exposed enterprise-service patching, data-egress monitoring, and holiday/weekend incident staffing.",
    },
    "collection against diplomatic or policy targets": {
        "target_sector": "diplomatic missions, summit delegations, policy staff, and defense forums",
        "likely_objective": "data_theft",
        "mechanism": "Use credential or access collection around a summit to inform state negotiating positions.",
        "defensive": "Prioritize MFA enforcement, temporary travel-device hygiene, mailbox auditing, and summit-themed lure awareness.",
    },
}


def confidence_label(score: float) -> str:
    for threshold, label in CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


def clamp_score(score: float) -> float:
    if math.isnan(score) or math.isinf(score):
        return 0.0
    return round(max(0.0, min(score, 1.0)), 4)


def rank_strike_windows(
    candidate: Mapping[str, Any],
    historical_cases: Sequence[Any] | None = None,
    calendar_events: Sequence[Any] | None = None,
    sanctions: Sequence[Any] | None = None,
    indictments: Sequence[Any] | None = None,
    kev_signals: Sequence[Any] | None = None,
    *,
    today: date | str | None = None,
    horizon_days: int = 180,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Produce interface-shaped strike-window rankings.

    Inputs can be raw dictionaries from loaders. Each output contains ranked
    dates, confidence, trigger signals, analogy snippets, and source ids.
    """

    as_of = _coerce_date(today) or date.today()
    horizon_end = as_of + timedelta(days=horizon_days)
    candidate_features = extract_candidate_features(candidate)
    historical_matches = match_historical_cases(candidate_features, historical_cases or [], top_n=6)

    signal_matches = _collect_current_signal_matches(
        candidate_features,
        calendar_events=calendar_events,
        sanctions=sanctions,
        indictments=indictments,
        kev_signals=kev_signals,
    )

    windows: list[dict[str, Any]] = []
    for signal in signal_matches:
        projected = _project_window(signal, historical_matches, as_of, horizon_end)
        if projected is None:
            continue
        start, end, projection_note = projected
        score = score_strike_window(
            candidate,
            signal,
            historical_matches,
            start_date=start,
            end_date=end,
            today=as_of,
        )
        if score <= 0:
            continue
        source_ids = _dedupe(signal.get("source_ref_ids", []) + _top_hist_source_ids(historical_matches))
        windows.append(
            {
                "window_id": "",
                "rank": 0,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "confidence": confidence_label(score),
                "confidence_score": score,
                "why_this_window": _window_rationale(signal, historical_matches, projection_note, source_ids),
                "trigger_signals": _trigger_signal_labels(signal),
                "historical_analogies": _historical_analogies(historical_matches),
                "source_ref_ids": source_ids,
                "_sort": (score, start, end),
            }
        )

    if not windows and historical_matches:
        windows.append(_fallback_window(candidate, historical_matches, as_of))

    windows.sort(key=lambda item: (-item["_sort"][0], item["_sort"][1], item["_sort"][2]))
    windows = _dedupe_overlapping_windows(windows)
    for idx, window in enumerate(windows[:top_n], start=1):
        window["window_id"] = f"win_{idx}"
        window["rank"] = idx
        window.pop("_sort", None)
    return windows[:top_n]


def rank_strike_vectors(
    candidate: Mapping[str, Any],
    historical_cases: Sequence[Any] | None = None,
    calendar_events: Sequence[Any] | None = None,
    sanctions: Sequence[Any] | None = None,
    indictments: Sequence[Any] | None = None,
    kev_signals: Sequence[Any] | None = None,
    *,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Produce interface-shaped, high-level strike-vector rankings."""

    candidate_features = extract_candidate_features(candidate)
    historical_matches = match_historical_cases(candidate_features, historical_cases or [], top_n=8)
    current_matches = _collect_current_signal_matches(
        candidate_features,
        calendar_events=calendar_events,
        sanctions=sanctions,
        indictments=indictments,
        kev_signals=kev_signals,
    )
    kev_matches = match_current_signals(candidate_features, kev_signals or [], signal_type="kev", top_n=10)

    vectors: list[dict[str, Any]] = []
    for vector_class, profile in VECTOR_PROFILES.items():
        profile_features = extract_features({"vector_class": vector_class, **profile})
        candidate_fit_score, candidate_reasons = feature_overlap(
            candidate_features,
            profile_features,
            weights={
                "adversaries": 0.08,
                "sectors": 0.22,
                "vectors": 0.34,
                "objectives": 0.24,
                "trigger_classes": 0.06,
                "cwe_ids": 0.03,
                "cve_ids": 0.03,
            },
        )
        historical_support = _profile_support(profile_features, historical_matches)
        current_support = _profile_support(profile_features, current_matches)
        kev_support = _profile_support(profile_features, kev_matches)
        objective_bonus = _objective_bonus(candidate, profile["likely_objective"])
        score = clamp_score(
            0.50 * candidate_fit_score
            + 0.25 * historical_support
            + 0.10 * current_support
            + 0.10 * kev_support
            + 0.05 * objective_bonus
        )
        if score < 0.04:
            continue
        source_ids = _dedupe(
            _top_hist_source_ids(historical_matches)
            + _top_signal_source_ids(current_matches)
            + _top_signal_source_ids(kev_matches)
        )
        likely_objective = _candidate_objective(candidate) or profile["likely_objective"]
        vectors.append(
            {
                "vector_id": "",
                "rank": 0,
                "vector_class": vector_class,
                "target_sector": _target_sector(candidate_features, profile["target_sector"]),
                "likely_objective": likely_objective,
                "non_actionable_mechanism": profile["mechanism"],
                "candidate_fit": _candidate_fit_text(vector_class, candidate_reasons),
                "confidence": confidence_label(score),
                "confidence_score": score,
                "why_this_vector": _vector_rationale(
                    vector_class,
                    candidate_fit_score,
                    historical_support,
                    current_support,
                    kev_support,
                    source_ids,
                ),
                "defensive_implication": profile["defensive"],
                "source_ref_ids": source_ids,
                "_sort": score,
            }
        )

    vectors.sort(key=lambda item: (-item["_sort"], item["vector_class"]))
    for idx, vector in enumerate(vectors[:top_n], start=1):
        vector["vector_id"] = f"vec_{idx}"
        vector["rank"] = idx
        vector.pop("_sort", None)
    return vectors[:top_n]


def score_strike_window(
    candidate: Mapping[str, Any],
    signal: Mapping[str, Any],
    historical_matches: Sequence[Mapping[str, Any]],
    *,
    start_date: date,
    end_date: date,
    today: date,
) -> float:
    """Score a projected window using context, analogies, and timing proximity."""

    signal_score = float(signal.get("score", 0.0))
    historical_support = _historical_support_for_signal(signal, historical_matches)
    timing = _timing_proximity_score(start_date, end_date, today)
    technical = _technical_pressure(candidate, signal)
    stage1 = candidate_priority_score(candidate)
    score = (
        0.42 * signal_score
        + 0.28 * historical_support
        + 0.12 * timing
        + 0.10 * technical
        + 0.08 * stage1
    )
    return clamp_score(score)


def _collect_current_signal_matches(
    candidate_features: FeatureVector,
    *,
    calendar_events: Sequence[Any] | None,
    sanctions: Sequence[Any] | None,
    indictments: Sequence[Any] | None,
    kev_signals: Sequence[Any] | None,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    signal_sets = [
        ("calendar", calendar_events or []),
        ("sanctions", sanctions or []),
        ("indictment", indictments or []),
        ("kev", kev_signals or []),
    ]
    for signal_type, records in signal_sets:
        if not records:
            continue
        signals.extend(match_current_signals(candidate_features, records, signal_type=signal_type, top_n=12))
    signals.sort(key=lambda item: (-item["score"], item["signal_type"], item["signal_id"]))
    return signals


def _project_window(
    signal: Mapping[str, Any],
    historical_matches: Sequence[Mapping[str, Any]],
    today: date,
    horizon_end: date,
) -> tuple[date, date, str] | None:
    signal_type = str(signal.get("signal_type", "context"))
    features = _features_from_match(signal)
    raw = signal.get("raw", {})
    dates = _dates_from_signal(signal)
    if not dates:
        dates = (today,)
    base_start, base_end = min(dates), max(dates)

    if signal_type == "calendar":
        motives = set(features.trigger_classes)
        if "diplomatic" in motives:
            start, end = base_start - timedelta(days=7), base_end + timedelta(days=2)
            note = "summit/diplomatic pre-window"
        elif "election" in motives:
            extension = 30 if "certification" in str(signal.get("label", "")).lower() else 3
            start, end = base_start - timedelta(days=10), base_end + timedelta(days=extension)
            note = "election pressure window"
        elif {"anniversary", "holiday"} & motives:
            start, end = base_start - timedelta(days=2), base_end + timedelta(days=2)
            note = "symbolic calendar window"
        elif "critical-infra-stress" in motives:
            start, end = base_start - timedelta(days=7), base_end + timedelta(days=7)
            note = "critical-infrastructure stress window"
        elif "financial" in motives:
            start, end = base_start - timedelta(days=3), base_end + timedelta(days=3)
            note = "market/financial stress window"
        else:
            start, end = base_start - timedelta(days=5), base_end + timedelta(days=2)
            note = "scheduled context window"
    elif signal_type == "sanctions":
        lower, upper = _burn_range_from_historical(historical_matches, preferred_triggers={"sanctions"})
        start, end = base_end + timedelta(days=lower), base_end + timedelta(days=upper)
        note = f"sanctions-retaliation projection using {lower}-{upper} day burn range"
    elif signal_type == "indictment":
        lower, upper = _burn_range_from_historical(historical_matches, preferred_triggers={"indictment"})
        if lower == 0 and upper <= 7:
            lower, upper = 30, 180
        start, end = base_end + timedelta(days=lower), base_end + timedelta(days=upper)
        note = f"legal-retaliation projection using {lower}-{upper} day burn range"
    elif signal_type == "kev":
        start = _field_date(raw, "dateAdded", "date_added") or base_start
        end = _field_date(raw, "dueDate", "due_date") or (start + timedelta(days=21))
        end = max(end, start + timedelta(days=7))
        note = "known-exploited-vulnerability operational pressure window"
    else:
        start, end = base_start, base_end + timedelta(days=14)
        note = "current-context window"

    if end < today:
        return None
    start = max(start, today)
    end = min(max(end, start), horizon_end)
    if start > horizon_end:
        return None
    return start, end, note


def _burn_range_from_historical(
    historical_matches: Sequence[Mapping[str, Any]],
    *,
    preferred_triggers: set[str],
) -> tuple[int, int]:
    ranges: list[tuple[int, int, float]] = []
    for match in historical_matches:
        triggers = set(match.get("trigger_class", []))
        if preferred_triggers and triggers and not (triggers & preferred_triggers):
            continue
        lower, upper = parse_time_to_burn_days(str(match.get("time_to_burn", "")))
        if upper > 0:
            ranges.append((lower, upper, float(match.get("score", 0.0))))
    if not ranges:
        if "sanctions" in preferred_triggers:
            return 14, 56
        if "indictment" in preferred_triggers:
            return 30, 180
        return 0, 14
    ranges.sort(key=lambda item: -item[2])
    selected = ranges[:3]
    lower = round(sum(item[0] * item[2] for item in selected) / max(sum(item[2] for item in selected), 0.01))
    upper = round(sum(item[1] * item[2] for item in selected) / max(sum(item[2] for item in selected), 0.01))
    lower = max(0, min(lower, 180))
    upper = max(lower + 1, min(upper, 180))
    return lower, upper


def parse_time_to_burn_days(text: str) -> tuple[int, int]:
    """Map corpus time-to-burn prose to a day range."""

    lower = text.lower()
    if "no burn" in lower or "no destructive deployment" in lower:
        return 90, 180
    if "hour" in lower or "h-hour" in lower:
        return 0, 3
    if "0 days" in lower or "same day" in lower or "coincident" in lower:
        return 0, 2
    if "week" in lower or "wk" in lower:
        numbers = [int(num) for num in re.findall(r"\d+", lower)]
        if numbers:
            if len(numbers) >= 2:
                return numbers[0] * 7, numbers[1] * 7
            return max(0, numbers[0] * 7 - 7), numbers[0] * 7 + 7
    if "month" in lower or "mo" in lower:
        numbers = [int(num) for num in re.findall(r"\d+", lower)]
        if numbers:
            if len(numbers) >= 2:
                return numbers[0] * 30, min(numbers[1] * 30, 720)
            return max(0, numbers[0] * 30 - 15), numbers[0] * 30 + 30
    if "day" in lower:
        numbers = [int(num) for num in re.findall(r"\d+", lower)]
        if numbers:
            if len(numbers) >= 2:
                return numbers[0], numbers[1]
            return max(0, numbers[0] - 7), numbers[0] + 10
    if "year" in lower:
        return 180, 720
    return 0, 30


def _features_from_match(match: Mapping[str, Any]) -> FeatureVector:
    features = match.get("features", {})
    if isinstance(features, FeatureVector):
        return features
    return FeatureVector(
        tokens=frozenset(features.get("tokens", [])),
        adversaries=frozenset(features.get("adversaries", [])),
        sectors=frozenset(features.get("sectors", [])),
        vectors=frozenset(features.get("vectors", [])),
        objectives=frozenset(features.get("objectives", [])),
        trigger_classes=frozenset(features.get("trigger_classes", [])),
        cve_ids=frozenset(features.get("cve_ids", [])),
        cwe_ids=frozenset(features.get("cwe_ids", [])),
        dates=tuple(_coerce_date(item) for item in features.get("dates", []) if _coerce_date(item)),
    )


def _dates_from_signal(signal: Mapping[str, Any]) -> tuple[date, ...]:
    parsed = [_coerce_date(item) for item in signal.get("dates", [])]
    dates = [item for item in parsed if item]
    raw = signal.get("raw", {})
    for key in ("date", "start_date", "end_date", "dateAdded", "dueDate", "compiled", "updated"):
        maybe = raw.get(key) if isinstance(raw, Mapping) else None
        parsed_date = _coerce_date(maybe)
        if parsed_date:
            dates.append(parsed_date)
    return tuple(sorted(set(dates)))


def _field_date(record: Any, *keys: str) -> date | None:
    if not isinstance(record, Mapping):
        return None
    lowered = {str(key).lower(): value for key, value in record.items()}
    for key in keys:
        parsed = _coerce_date(lowered.get(key.lower()))
        if parsed:
            return parsed
    return None


def _coerce_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", value)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                return None
    return None


def _historical_support_for_signal(
    signal: Mapping[str, Any],
    historical_matches: Sequence[Mapping[str, Any]],
) -> float:
    if not historical_matches:
        return 0.0
    signal_features = _features_from_match(signal)
    scores: list[float] = []
    for match in historical_matches[:5]:
        match_features = _features_from_match(match)
        overlap, _ = feature_overlap(signal_features, match_features)
        scores.append(max(overlap, float(match.get("score", 0.0)) * 0.7))
    return clamp_score(sum(scores[:3]) / max(len(scores[:3]), 1))


def _technical_pressure(candidate: Mapping[str, Any], signal: Mapping[str, Any]) -> float:
    weaponization = candidate.get("weaponization", {}) if isinstance(candidate, Mapping) else {}
    pressure = 0.0
    if weaponization.get("kev_listed"):
        pressure += 0.25
    if weaponization.get("in_the_wild_observed"):
        pressure += 0.25
    if weaponization.get("public_poc_available"):
        pressure += 0.15
    try:
        epss = weaponization.get("epss_score")
        if epss is not None:
            pressure += 0.2 * max(0.0, min(float(epss), 1.0))
    except (TypeError, ValueError):
        pass
    if signal.get("signal_type") == "kev":
        pressure += 0.25
    return clamp_score(pressure)


def _timing_proximity_score(start: date, end: date, today: date) -> float:
    if start <= today <= end:
        return 1.0
    days_until = (start - today).days
    if days_until < 0:
        return 0.25
    if days_until <= 7:
        return 0.9
    if days_until <= 30:
        return 0.75
    if days_until <= 90:
        return 0.55
    return 0.35


def _window_rationale(
    signal: Mapping[str, Any],
    historical_matches: Sequence[Mapping[str, Any]],
    projection_note: str,
    source_ids: Sequence[str],
) -> str:
    label = signal.get("label", "current context signal")
    signal_type = signal.get("signal_type", "context")
    top_case = historical_matches[0] if historical_matches else None
    if top_case:
        analogy = f"Top analogy: {top_case['case_name']} ({top_case.get('time_to_burn', 'unknown burn timing')})."
    else:
        analogy = "No historical case dominates; confidence is driven by the current signal only."
    refs = ", ".join(source_ids[:5]) if source_ids else "source refs pending"
    return (
        f"Ranked because the {signal_type} signal '{label}' aligns with candidate/context features and "
        f"projects to this {projection_note}. {analogy} Source refs: {refs}."
    )


def _trigger_signal_labels(signal: Mapping[str, Any]) -> list[str]:
    features = _features_from_match(signal)
    labels = sorted(features.trigger_classes) or [str(signal.get("signal_type", "context"))]
    return [f"{label}: {signal.get('label', 'current signal')}" for label in labels[:4]]


def _historical_analogies(historical_matches: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    analogies: list[dict[str, Any]] = []
    for match in historical_matches[:3]:
        matched = "; ".join(match.get("matched_features", [])[:3]) or "feature-level analogy"
        analogies.append(
            {
                "case_id": str(match.get("case_id", "unknown")),
                "case_name": str(match.get("case_name", "unknown")),
                "pattern_matched": matched,
                "time_to_burn": str(match.get("time_to_burn", "unknown")),
                "source_ref_ids": list(match.get("source_ref_ids", [])),
            }
        )
    return analogies


def _fallback_window(
    candidate: Mapping[str, Any],
    historical_matches: Sequence[Mapping[str, Any]],
    today: date,
) -> dict[str, Any]:
    start = today
    end = today + timedelta(days=30)
    score = clamp_score(0.25 + 0.25 * float(historical_matches[0].get("score", 0.0)) + 0.1 * candidate_priority_score(candidate))
    source_ids = _top_hist_source_ids(historical_matches)
    return {
        "window_id": "",
        "rank": 0,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "confidence": confidence_label(score),
        "confidence_score": score,
        "why_this_window": "Fallback near-term forecast based on historical analogy only; add current context signals before using in a demo artifact.",
        "trigger_signals": ["historical analogy only"],
        "historical_analogies": _historical_analogies(historical_matches),
        "source_ref_ids": source_ids,
        "_sort": (score, start, end),
    }


def _dedupe_overlapping_windows(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for window in windows:
        start = _coerce_date(window["start_date"])
        end = _coerce_date(window["end_date"])
        if not start or not end:
            continue
        overlaps = False
        for existing in kept:
            ex_start = _coerce_date(existing["start_date"])
            ex_end = _coerce_date(existing["end_date"])
            if ex_start and ex_end and start <= ex_end and ex_start <= end:
                overlaps = True
                if window["confidence_score"] > existing["confidence_score"]:
                    existing.update(window)
                break
        if not overlaps:
            kept.append(window)
    return kept


def _profile_support(profile_features: FeatureVector, matches: Sequence[Mapping[str, Any]]) -> float:
    scores: list[float] = []
    for match in matches[:8]:
        features = _features_from_match(match)
        overlap, _ = feature_overlap(profile_features, features)
        if overlap > 0:
            scores.append(overlap * float(match.get("score", 0.0) or 0.0))
    if not scores:
        return 0.0
    scores.sort(reverse=True)
    return clamp_score(sum(scores[:3]) / min(len(scores), 3))


def _candidate_objective(candidate: Mapping[str, Any]) -> str | None:
    attack = candidate.get("attack_hypothesis", {}) if isinstance(candidate, Mapping) else {}
    objective = str(attack.get("intended_effect", "")).lower()
    return objective if objective in ALLOWED_OBJECTIVES else None


def _objective_bonus(candidate: Mapping[str, Any], profile_objective: str) -> float:
    candidate_objective = _candidate_objective(candidate)
    if not candidate_objective:
        return 0.35
    if candidate_objective == profile_objective:
        return 1.0
    compatible = {
        ("shutdown", "disruption"),
        ("disruption", "shutdown"),
        ("control", "persistence"),
        ("persistence", "control"),
        ("data_theft", "persistence"),
    }
    return 0.65 if (candidate_objective, profile_objective) in compatible else 0.15


def _target_sector(candidate_features: FeatureVector, fallback: str) -> str:
    if not candidate_features.sectors:
        return fallback
    ordered = sorted(candidate_features.sectors)
    sector_map = {
        "federal-defense-edge": "US federal and defense-industrial perimeter services",
        "critical-infrastructure": "US critical infrastructure and adjacent service providers",
        "industrial-control": "OT/ICS environments in critical infrastructure sectors",
        "financial": "financial services and crypto/payment infrastructure",
        "election-political": "election, campaign, and political infrastructure",
        "supply-chain-saas": "software supply-chain and managed-service ecosystems",
        "diplomatic": "diplomatic and policy organizations",
    }
    return sector_map.get(ordered[0], fallback)


def _candidate_fit_text(vector_class: str, reasons: Sequence[str]) -> str:
    if reasons:
        return f"Stage 1 candidate aligns with {vector_class} through {('; '.join(reasons[:3]))}."
    return f"Stage 1 candidate has partial high-level alignment with {vector_class}; no procedure-level detail is inferred."


def _vector_rationale(
    vector_class: str,
    candidate_fit: float,
    historical_support: float,
    current_support: float,
    kev_support: float,
    source_ids: Sequence[str],
) -> str:
    refs = ", ".join(source_ids[:5]) if source_ids else "source refs pending"
    return (
        f"{vector_class} is ranked from candidate fit ({candidate_fit:.2f}), historical analogy support "
        f"({historical_support:.2f}), current-context support ({current_support:.2f}), and KEV/public-exposure "
        f"support ({kev_support:.2f}). Source refs: {refs}."
    )


def _top_hist_source_ids(historical_matches: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for match in historical_matches[:3]:
        refs.extend(match.get("source_ref_ids", []))
    return _dedupe(refs)


def _top_signal_source_ids(matches: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for match in matches[:5]:
        refs.extend(match.get("source_ref_ids", []))
    return _dedupe(refs)


def _dedupe(items: Sequence[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
