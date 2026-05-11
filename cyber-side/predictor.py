"""Deterministic exploit-class portfolio generator for Prophet.

The predictor consumes a Forecaster output (Direction B) and an optional
candidate (Direction A), then emits Alex's requested portfolio:

* 5 hypothesized zero-day exploit classes
* 5 known one-day / KEV replay classes

The output is intentionally non-actionable. It contains class-level forecasts,
defensive primitives, and source citations. It does not generate payloads,
procedures, live targets, credentials, or exploit code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "exploit_prediction_portfolio.v0.1"

BANNED_KEYS = {
    "payload",
    "payloads",
    "procedure",
    "procedures",
    "steps",
    "exploit_steps",
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

PAYLOAD_TOKENS = (
    "${jndi:",
    "${${",
    "marshalsec",
    "ysoserial",
    "mimikatz",
)


class PortfolioValidationError(ValueError):
    """Raised when a generated portfolio violates the safe output contract."""


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise PortfolioValidationError(f"{path} must decode to a JSON object")
    return value


def generate_prediction_portfolio(
    forecast: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic safe prediction portfolio from forecast context."""
    top_vector = _first(forecast.get("strike_vectors"))
    top_window = _first(forecast.get("strike_windows"))
    frame = _object(forecast.get("strategic_frame"))
    candidate_identity = _object((candidate or {}).get("identity"))

    forecast_id = _str(forecast.get("forecast_id"), "unknown-forecast")
    candidate_id = _str(
        (candidate or {}).get("candidate_id"),
        _str(forecast.get("input_candidate_id"), "unknown-candidate"),
    )
    vector_id = _str(top_vector.get("vector_id"), "vec_1")
    portfolio_id = _portfolio_id(forecast_id, candidate_id, vector_id)
    emitted_at = generated_at or _str(
        forecast.get("generated_at"),
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    source_refs = _build_source_pool(forecast, candidate)
    context_sources = _top_context_sources(source_refs, top_vector, top_window)

    strike_context = {
        "adversary_class": _readable(_str(frame.get("adversary_class"), "unknown")),
        "target_scope": _str(frame.get("target_scope"), "sector-level target scope"),
        "geographic_scope": _str(frame.get("geographic_scope"), "sector-level geography"),
        "strike_vector": _str(top_vector.get("vector_class"), "unknown vector"),
        "strike_window": {
            "start_date": _str(top_window.get("start_date"), "unknown"),
            "end_date": _str(top_window.get("end_date"), "unknown"),
            "confidence": _str(top_window.get("confidence"), "unknown"),
        },
        "candidate_class": _str(
            candidate_identity.get("cve_class_label"),
            _str(forecast.get("input_candidate_id"), "representative exploit class"),
        ),
    }

    portfolio = {
        "portfolio_id": portfolio_id,
        "generated_at": emitted_at,
        "schema_version": SCHEMA_VERSION,
        "input_refs": {
            "candidate_id": candidate_id,
            "forecast_id": forecast_id,
            "vector_id": vector_id,
        },
        "policy": {
            "mode": "deterministic_fixture_safe",
            "exclusions": [
                "No exploit payloads",
                "No target-control instructions",
                "No named live targets",
                "No credentials or operational infrastructure",
            ],
        },
        "strike_context": strike_context,
        "zero_day_predictions": _zero_day_predictions(strike_context, context_sources),
        "one_day_predictions": _one_day_predictions(strike_context, context_sources),
    }
    validate_prediction_portfolio(portfolio)
    return portfolio


def validate_prediction_portfolio(portfolio: dict[str, Any] | str) -> None:
    """Validate the safe portfolio shape and content constraints."""
    value = json.loads(portfolio) if isinstance(portfolio, str) else portfolio
    if not isinstance(value, dict):
        raise PortfolioValidationError("portfolio must be an object")
    _scan_for_banned_keys(value, "portfolio")
    _scan_text_safety(value, "portfolio")

    if value.get("schema_version") != SCHEMA_VERSION:
        raise PortfolioValidationError(f"schema_version must be {SCHEMA_VERSION}")
    _required(value, "portfolio_id", str)
    _validate_iso(_required(value, "generated_at", str), "generated_at")

    input_refs = _required(value, "input_refs", dict)
    for key in ("candidate_id", "forecast_id", "vector_id"):
        _required(input_refs, key, str)

    zero_days = _required(value, "zero_day_predictions", list)
    one_days = _required(value, "one_day_predictions", list)
    if len(zero_days) != 5:
        raise PortfolioValidationError("zero_day_predictions must contain exactly 5 entries")
    if len(one_days) != 5:
        raise PortfolioValidationError("one_day_predictions must contain exactly 5 entries")

    for expected_type, predictions in (
        ("hypothesized_zero_day", zero_days),
        ("known_one_day", one_days),
    ):
        seen_ids: set[str] = set()
        for idx, prediction in enumerate(predictions, start=1):
            if not isinstance(prediction, dict):
                raise PortfolioValidationError(f"{expected_type}[{idx}] must be object")
            pred_id = _required(prediction, "prediction_id", str)
            if pred_id in seen_ids:
                raise PortfolioValidationError(f"duplicate prediction_id: {pred_id}")
            seen_ids.add(pred_id)
            if prediction.get("prediction_type") != expected_type:
                raise PortfolioValidationError(
                    f"{pred_id} prediction_type must be {expected_type}"
                )
            if prediction.get("rank") != idx:
                raise PortfolioValidationError(f"{pred_id} rank must be {idx}")
            _required(prediction, "exploit_class_label", str)
            _required(prediction, "affected_surface", str)
            _required(prediction, "mapped_strike_vector", str)
            _required(prediction, "likely_objective", str)
            _required(prediction, "non_actionable_rationale", str)
            sources = _required(prediction, "source_refs", list)
            if not 2 <= len(sources) <= 3:
                raise PortfolioValidationError(f"{pred_id} must carry 2-3 source_refs")
            for source in sources:
                _validate_source(source, pred_id)
            defense = _required(prediction, "defense_primitive", dict)
            _required(defense, "patch_focus", str)
            _required(defense, "detection_focus", str)
            _required(defense, "sandbox_note", str)
            if "localhost" not in defense["sandbox_note"].lower():
                raise PortfolioValidationError(f"{pred_id} sandbox_note must be localhost scoped")


def _zero_day_predictions(
    context: dict[str, Any],
    sources: list[dict[str, str]],
) -> list[dict[str, Any]]:
    vector = context["strike_vector"]
    window = context["strike_window"]
    objective = _objective_from_vector(vector)
    target_scope = context["target_scope"]

    templates = _financial_zero_day_templates() if _is_financial_context(context) else [
        {
            "label": "edge appliance authentication-state bypass",
            "surface": "enterprise VPN and secure edge administrative access plane",
            "cwes": ["CWE-287", "CWE-306"],
            "rationale": (
                "Because the forecast favors edge-appliance access during the lead window, "
                "a state actor would get high value from a class that bypasses authentication "
                "state on exposed perimeter management surfaces without requiring commodity malware."
            ),
            "patch": "Strengthen authentication-state validation, invalidate ambiguous sessions, and require explicit administrative re-authentication for sensitive flows.",
            "detection": "Alert on anomalous administrative session creation, unusual token reuse, and management-plane access outside expected maintenance windows.",
        },
        {
            "label": "perimeter device request-parser memory safety flaw",
            "surface": "gateway request parsing and appliance control-plane services",
            "cwes": ["CWE-787", "CWE-119"],
            "rationale": (
                "The historical edge-appliance analogies make parser flaws a plausible burn class "
                "because they can turn internet-facing traffic into durable access while staying "
                "sector-level and product-family agnostic."
            ),
            "patch": "Add strict bounds checks, reject malformed control-plane requests, and isolate parser failures from privileged appliance services.",
            "detection": "Track parser error spikes, appliance worker crashes, and management-service restarts correlated with external request volume.",
        },
        {
            "label": "federated identity token validation weakness",
            "surface": "SSO, federation, and appliance identity broker components",
            "cwes": ["CWE-347", "CWE-287"],
            "rationale": (
                "If the objective is persistence, identity-bound access is more valuable than a "
                "single crash primitive; the strike window therefore elevates token validation "
                "weaknesses tied to perimeter access."
            ),
            "patch": "Require strict signature, issuer, audience, expiry, and replay checks across all federation paths.",
            "detection": "Correlate impossible-travel admin logins, unusual token lifetimes, and authentication successes missing normal identity-provider context.",
        },
        {
            "label": "management API authorization confusion",
            "surface": "appliance REST APIs, role checks, and configuration endpoints",
            "cwes": ["CWE-863", "CWE-862"],
            "rationale": (
                "The forecasted vector points at administrative control planes, so a zero-day "
                "class involving authorization confusion would fit pre-positioning without "
                "requiring destructive effects."
            ),
            "patch": "Centralize authorization checks, deny-by-default sensitive API routes, and regression-test role boundaries for configuration changes.",
            "detection": "Flag low-frequency configuration reads, privilege-boundary anomalies, and changes made by principals without matching role history.",
        },
        {
            "label": "appliance update-channel trust validation gap",
            "surface": "firmware update, plugin distribution, and package verification logic",
            "cwes": ["CWE-347", "CWE-494"],
            "rationale": (
                "Pre-positioning campaigns reward durable access, and update-channel trust gaps "
                "can persist across normal maintenance cycles when defenders focus only on endpoint telemetry."
            ),
            "patch": "Enforce signed-update verification, certificate pinning for update metadata, and rollback protection for appliance packages.",
            "detection": "Monitor unexpected update metadata fetches, package verification failures, and post-update configuration drift.",
        },
    ]

    return [
        _prediction(
            prediction_id=f"zp-{idx:03d}",
            rank=idx,
            prediction_type="hypothesized_zero_day",
            label=item["label"],
            affected_surface=item["surface"],
            cwe_ids=item["cwes"],
            vector=vector,
            window=window,
            objective=objective,
            rationale=_with_window(item["rationale"], window, target_scope),
            patch_focus=item["patch"],
            detection_focus=item["detection"],
            sources=_rotate_sources(sources, idx),
        )
        for idx, item in enumerate(templates, start=1)
    ]


def _financial_zero_day_templates() -> list[dict[str, Any]]:
    return [
        {
            "label": "financial workflow authorization-state bypass",
            "surface": "transaction approval and settlement workflow policy checks",
            "cwes": ["CWE-862", "CWE-863"],
            "rationale": (
                "The forecast favors financial workflow abuse during a revenue-pressure window, "
                "so ambiguous approval state is a high-value defensive review area without "
                "describing institution-specific transfer behavior."
            ),
            "patch": "Centralize approval-state enforcement, deny inconsistent transitions, and require independent review for high-risk workflow changes.",
            "detection": "Alert on high-risk approvals missing expected policy context, reviewer separation, or normal business-event correlation.",
        },
        {
            "label": "custody policy-engine assertion validation gap",
            "surface": "digital-asset custody policy evaluation and identity assertions",
            "cwes": ["CWE-287", "CWE-347"],
            "rationale": (
                "Custody workflows depend on strict identity and policy assertions; the strike "
                "window elevates validation gaps because they can affect approval integrity "
                "while remaining defensible in synthetic fixture data."
            ),
            "patch": "Require strict assertion issuer, audience, expiry, replay, and policy-binding checks before approving privileged custody actions.",
            "detection": "Correlate assertion anomalies, unusual policy-engine decisions, and privileged workflow activity outside expected approval patterns.",
        },
        {
            "label": "financial workflow event-parser trust-boundary flaw",
            "surface": "payment operations event parsing, reconciliation, and audit pipelines",
            "cwes": ["CWE-20", "CWE-116"],
            "rationale": (
                "Payment operations depend on trusted event normalization; parser trust-boundary "
                "errors are plausible burn classes for defenders to test with synthetic logs."
            ),
            "patch": "Validate event schemas before enrichment, reject ambiguous fields, and preserve immutable audit records for reconciliation.",
            "detection": "Flag schema drift, reconciliation gaps, and high-risk workflow events whose normalized form differs from immutable audit evidence.",
        },
        {
            "label": "privileged action queue replay-control weakness",
            "surface": "approval queues, privileged action tickets, and workflow deduplication logic",
            "cwes": ["CWE-294", "CWE-345"],
            "rationale": (
                "Revenue-driven activity benefits from confusing repeated privileged actions, so "
                "defenders should test replay controls without modeling financial instructions."
            ),
            "patch": "Bind approvals to single-use workflow intents, enforce deduplication keys, and expire stale privileged-action requests.",
            "detection": "Watch for repeated approval identifiers, stale queue items becoming active, and privileged actions without matching fresh intent.",
        },
        {
            "label": "settlement report integrity-control gap",
            "surface": "settlement reporting, audit export, and exception-review workflows",
            "cwes": ["CWE-345", "CWE-353"],
            "rationale": (
                "Financial defenders need confidence that review evidence cannot drift from "
                "business events; integrity-control gaps are a useful prediction class for "
                "evidence-focused pilots."
            ),
            "patch": "Hash-chain settlement reports, require signed export metadata, and block report updates that cannot be tied to source events.",
            "detection": "Detect report hash mismatches, missing export provenance, and exception-review decisions without matching source evidence.",
        },
    ]


def _one_day_predictions(
    context: dict[str, Any],
    sources: list[dict[str, str]],
) -> list[dict[str, Any]]:
    vector = context["strike_vector"]
    window = context["strike_window"]
    objective = _objective_from_vector(vector)
    target_scope = context["target_scope"]

    templates = _financial_one_day_templates() if _is_financial_context(context) else [
        {
            "label": "Log4Shell-class Java logging framework remote code execution",
            "surface": "Java services and logging paths exposed through perimeter applications",
            "cves": ["CVE-2021-44228"],
            "cwes": ["CWE-917", "CWE-20"],
            "rationale": "A Log4Shell replay remains a strong one-day analog for edge-facing services because it ties exposed request handling to high-impact application compromise.",
            "patch": "Upgrade the vulnerable library family, disable unsafe lookup behavior, and enforce dependency inventory checks.",
            "detection": "Detect suspicious lookup strings in web and application logs and correlate with Java service exposure.",
            "sources": [
                _static_source("src_cisa_log4shell", "CISA Log4j advisory", "https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a", "authoritative mitigation context for CVE-2021-44228"),
            ],
        },
        {
            "label": "Pulse Secure / Ivanti VPN arbitrary file read class",
            "surface": "VPN gateway web components and credential-adjacent appliance files",
            "cves": ["CVE-2019-11510"],
            "cwes": ["CWE-22"],
            "rationale": "VPN gateway file-read flaws map cleanly to the forecast because perimeter appliances have historically served as durable initial-access points.",
            "patch": "Apply vendor-fixed gateway versions, remove exposed legacy paths, and rotate secrets that could have been exposed in the sandbox scenario.",
            "detection": "Alert on unusual VPN web-path access, configuration reads, and authentication activity following gateway errors.",
            "sources": [
                _static_source("src_cisa_kev_pulse", "CISA KEV: CVE-2019-11510", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited VPN gateway vulnerability used as a one-day replay analog"),
            ],
        },
        {
            "label": "Citrix NetScaler gateway code-execution class",
            "surface": "ADC/Gateway perimeter services and appliance web management paths",
            "cves": ["CVE-2023-3519"],
            "cwes": ["CWE-787"],
            "rationale": "NetScaler exploitation is a close historical match for the edge-appliance vector and shows why perimeter services deserve priority during diplomatic collection windows.",
            "patch": "Update affected gateway builds, restrict management exposure, and add compensating controls around appliance administrative interfaces.",
            "detection": "Watch for gateway process instability, anomalous session creation, and post-update persistence indicators.",
            "sources": [
                _static_source("src_cisa_kev_netscaler", "CISA KEV: CVE-2023-3519", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited NetScaler gateway vulnerability for one-day replay planning"),
            ],
        },
        {
            "label": "Palo Alto GlobalProtect management-plane compromise class",
            "surface": "firewall edge services and device telemetry/control paths",
            "cves": ["CVE-2024-3400"],
            "cwes": ["CWE-20", "CWE-78"],
            "rationale": "Firewall and VPN edge services are directly aligned with the forecasted perimeter-access vector and provide a relevant one-day defense rehearsal path.",
            "patch": "Apply the fixed vendor release, reduce management exposure, and verify telemetry paths cannot mutate privileged state.",
            "detection": "Correlate firewall telemetry anomalies, unexpected file artifacts, and edge-device administrative activity.",
            "sources": [
                _static_source("src_cisa_kev_globalprotect", "CISA KEV: CVE-2024-3400", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited firewall edge vulnerability for one-day replay planning"),
            ],
        },
        {
            "label": "Ivanti Connect Secure auth-bypass and gateway-control class",
            "surface": "secure access gateway authentication and command-adjacent control paths",
            "cves": ["CVE-2023-46805", "CVE-2024-21887"],
            "cwes": ["CWE-287", "CWE-78"],
            "rationale": "The Ivanti campaign is the strongest one-day analog because it combines PRC-nexus reporting, edge-appliance targeting, and pre-positioning behavior that mirrors this forecast.",
            "patch": "Apply the vendor remediation, import clean configuration baselines, and rebuild trust for exposed secure-access gateways.",
            "detection": "Hunt for unexpected gateway configuration changes, administrative session anomalies, and appliance integrity drift.",
            "sources": [
                _static_source("src_mandiant_ivanti", "Mandiant Ivanti zero-day analysis", "https://cloud.google.com/blog/topics/threat-intelligence/ivanti-connect-secure-vpn-zero-day", "public reporting on PRC-nexus edge-appliance exploitation"),
            ],
        },
    ]

    return [
        _prediction(
            prediction_id=f"op-{idx:03d}",
            rank=idx,
            prediction_type="known_one_day",
            label=item["label"],
            affected_surface=item["surface"],
            cwe_ids=item["cwes"],
            vector=vector,
            window=window,
            objective=objective,
            rationale=_with_window(item["rationale"], window, target_scope),
            patch_focus=item["patch"],
            detection_focus=item["detection"],
            sources=_merge_sources(item["sources"], _rotate_sources(sources, idx))[:3],
            known_cve_ids=item["cves"],
        )
        for idx, item in enumerate(templates, start=1)
    ]


def _financial_one_day_templates() -> list[dict[str, Any]]:
    return [
        {
            "label": "Log4Shell-class Java logging framework compromise",
            "surface": "Java-backed financial workflow services and application logging paths",
            "cves": ["CVE-2021-44228"],
            "cwes": ["CWE-917", "CWE-20"],
            "rationale": "Log4Shell remains a useful one-day analog for financial workflow services because application logging often sits near approval and audit paths.",
            "patch": "Upgrade the vulnerable library family, disable unsafe lookup behavior, and require dependency inventory checks for workflow services.",
            "detection": "Detect suspicious lookup strings in application logs and correlate with abnormal approval or reconciliation events.",
            "sources": [
                _static_source("src_cisa_log4shell", "CISA Log4j advisory", "https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a", "authoritative mitigation context for CVE-2021-44228"),
            ],
        },
        {
            "label": "secure-access gateway authentication bypass class",
            "surface": "financial operations remote-access gateways and identity broker paths",
            "cves": ["CVE-2023-46805", "CVE-2024-21887"],
            "cwes": ["CWE-287", "CWE-78"],
            "rationale": "Secure-access gateway one-days are relevant because financial workflow operators often depend on remote administration and vendor support paths.",
            "patch": "Apply vendor remediation, rebuild clean access baselines, and require fresh approval for privileged workflow access after gateway exposure.",
            "detection": "Hunt for anomalous access sessions, configuration integrity drift, and privileged workflow activity following gateway errors.",
            "sources": [
                _static_source("src_cisa_kev_ivanti", "CISA KEV: Ivanti secure access CVEs", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited secure-access gateway vulnerabilities for one-day replay planning"),
            ],
        },
        {
            "label": "managed file-transfer data-exposure class",
            "surface": "statement exchange, reconciliation files, and managed file-transfer workflows",
            "cves": ["CVE-2023-34362"],
            "cwes": ["CWE-89"],
            "rationale": "Financial institutions rely on managed file-transfer workflows, making data-exposure one-days a practical defensive rehearsal class.",
            "patch": "Update affected file-transfer components, isolate exchange workflows, and validate downstream reconciliation evidence.",
            "detection": "Track unusual file-export volume, unexpected partner exchange patterns, and reconciliation gaps after file-transfer service errors.",
            "sources": [
                _static_source("src_cisa_kev_moveit", "CISA KEV: MOVEit Transfer CVE-2023-34362", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited file-transfer vulnerability used as a defensive analog"),
            ],
        },
        {
            "label": "legacy file-transfer appliance compromise class",
            "surface": "legacy exchange appliances and financial document handoff paths",
            "cves": ["CVE-2021-27101", "CVE-2021-27104"],
            "cwes": ["CWE-22", "CWE-78"],
            "rationale": "Older file-transfer appliances are a useful one-day analog for financial-sector evidence review because they concentrate sensitive document workflows.",
            "patch": "Retire or isolate legacy exchange appliances, apply fixed versions, and require hash-based review of exported documents.",
            "detection": "Alert on abnormal export volume, appliance integrity drift, and document handoff events missing expected approval context.",
            "sources": [
                _static_source("src_cisa_kev_accellion", "CISA KEV: Accellion FTA CVEs", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited legacy file-transfer vulnerabilities for one-day replay planning"),
            ],
        },
        {
            "label": "collaboration platform privilege-boundary class",
            "surface": "operations runbooks, approval evidence stores, and collaboration-backed workflow notes",
            "cves": ["CVE-2023-22518"],
            "cwes": ["CWE-287", "CWE-863"],
            "rationale": "Financial workflow evidence often depends on collaboration systems, so privilege-boundary one-days can affect approval records and review artifacts.",
            "patch": "Apply fixed collaboration-platform versions, restrict administrative paths, and review evidence-store permissions.",
            "detection": "Monitor unusual evidence-page changes, unexpected administrator activity, and approval-note edits without matching workflow events.",
            "sources": [
                _static_source("src_cisa_kev_confluence", "CISA KEV: Atlassian Confluence CVE-2023-22518", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known exploited collaboration platform vulnerability for evidence-store review"),
            ],
        },
    ]


def _prediction(
    *,
    prediction_id: str,
    rank: int,
    prediction_type: str,
    label: str,
    affected_surface: str,
    cwe_ids: list[str],
    vector: str,
    window: dict[str, str],
    objective: str,
    rationale: str,
    patch_focus: str,
    detection_focus: str,
    sources: list[dict[str, str]],
    known_cve_ids: list[str] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "prediction_id": prediction_id,
        "rank": rank,
        "prediction_type": prediction_type,
        "exploit_class_label": label,
        "affected_surface": affected_surface,
        "cwe_ids": cwe_ids,
        "known_cve_ids": known_cve_ids or [],
        "mapped_strike_vector": vector,
        "mapped_strike_window": window,
        "likely_objective": objective,
        "non_actionable_rationale": rationale,
        "defense_primitive": {
            "patch_focus": patch_focus,
            "detection_focus": detection_focus,
            "sandbox_note": "Validate only in a localhost vulnerable-by-design sandbox or fixture replay; do not target live infrastructure.",
        },
        "source_refs": sources[:3],
    }
    return value


def _with_window(rationale: str, window: dict[str, str], target_scope: str) -> str:
    start = window.get("start_date", "unknown")
    end = window.get("end_date", "unknown")
    return (
        f"{rationale} It is prioritized for {start} to {end} because the "
        f"Forecaster maps the pressure window to {target_scope}."
    )


def _build_source_pool(
    forecast: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> dict[str, dict[str, str]]:
    pool: dict[str, dict[str, str]] = {}
    for idx, ref in enumerate(forecast.get("source_refs") or [], start=1):
        if not isinstance(ref, dict):
            continue
        ref_id = _str(ref.get("id"), f"forecast_src_{idx}")
        pool[ref_id] = {
            "id": ref_id,
            "label": _str(ref.get("label"), ref_id),
            "url": _str(ref.get("url"), "unknown"),
            "supports": _str(ref.get("supports"), "forecast source context"),
        }

    for idx, ref in enumerate((candidate or {}).get("source_refs") or [], start=1):
        if not isinstance(ref, dict):
            continue
        slug = _slug(_str(ref.get("label"), f"candidate source {idx}"))
        ref_id = f"candidate_{idx}_{slug}"[:80]
        pool.setdefault(
            ref_id,
            {
                "id": ref_id,
                "label": _str(ref.get("label"), ref_id),
                "url": _str(ref.get("url"), "unknown"),
                "supports": _str(ref.get("supports"), "candidate source context"),
            },
        )
    return pool


def _top_context_sources(
    source_pool: dict[str, dict[str, str]],
    top_vector: dict[str, Any],
    top_window: dict[str, Any],
) -> list[dict[str, str]]:
    ids: list[str] = []
    for ref_id in top_vector.get("source_ref_ids") or []:
        if isinstance(ref_id, str):
            ids.append(ref_id)
    for ref_id in top_window.get("source_ref_ids") or []:
        if isinstance(ref_id, str):
            ids.append(ref_id)
    ids.extend(source_pool.keys())

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for ref_id in ids:
        ref = source_pool.get(ref_id)
        if not ref or ref["id"] in seen:
            continue
        seen.add(ref["id"])
        out.append(ref)

    if not out:
        out.append(
            _static_source(
                "src_world_forecast",
                "Prophet Forecaster output",
                "world-side/outputs/",
                "forecast context used to rank strike vector and strike window",
            )
        )
    return out


def _rotate_sources(sources: list[dict[str, str]], rank: int) -> list[dict[str, str]]:
    if len(sources) <= 3:
        return sources
    start = (rank - 1) % len(sources)
    rotated = sources[start:] + sources[:start]
    return rotated[:3]


def _merge_sources(
    primary: list[dict[str, str]],
    context: list[dict[str, str]],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for ref in primary + context:
        ref_id = ref["id"]
        if ref_id in seen:
            continue
        seen.add(ref_id)
        out.append(ref)
    return out


def _static_source(ref_id: str, label: str, url: str, supports: str) -> dict[str, str]:
    return {"id": ref_id, "label": label, "url": url, "supports": supports}


def _portfolio_id(forecast_id: str, candidate_id: str, vector_id: str) -> str:
    digest = hashlib.sha256(f"{forecast_id}:{candidate_id}:{vector_id}".encode()).hexdigest()[:10]
    return f"ep-{digest}"


def _objective_from_vector(vector: str) -> str:
    lowered = vector.lower()
    if "shutdown" in lowered or "wiper" in lowered:
        return "shutdown"
    if "financial" in lowered or "theft" in lowered:
        return "data_theft"
    if "disruption" in lowered:
        return "disruption"
    return "persistence"


def _is_financial_context(context: dict[str, Any]) -> bool:
    haystack = " ".join(
        _str(context.get(key), "")
        for key in ("target_scope", "strike_vector", "candidate_class", "adversary_class")
    ).lower()
    return any(token in haystack for token in ("financial", "payment", "custody", "settlement"))


def _first(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _readable(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "source"


def _scan_for_banned_keys(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in BANNED_KEYS:
                raise PortfolioValidationError(f"{path} contains banned key: {key}")
            _scan_for_banned_keys(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_for_banned_keys(item, f"{path}[{idx}]")


def _scan_text_safety(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            _scan_text_safety(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_text_safety(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in PROCEDURAL_PHRASES:
            if phrase in lowered:
                raise PortfolioValidationError(f"{path} contains procedural phrase: {phrase!r}")
        for token in PAYLOAD_TOKENS:
            if token in lowered:
                raise PortfolioValidationError(f"{path} contains payload-like token: {token!r}")


def _required(value: dict[str, Any], key: str, typ: type) -> Any:
    inner = value.get(key)
    if not isinstance(inner, typ):
        raise PortfolioValidationError(f"missing or invalid {key}")
    if typ is str and not inner.strip():
        raise PortfolioValidationError(f"missing or invalid {key}")
    if typ is list and not inner:
        raise PortfolioValidationError(f"missing or invalid {key}")
    return inner


def _validate_source(source: Any, prediction_id: str) -> None:
    if not isinstance(source, dict):
        raise PortfolioValidationError(f"{prediction_id} source_refs must be objects")
    for key in ("id", "label", "url", "supports"):
        _required(source, key, str)


def _validate_iso(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PortfolioValidationError(f"{label} must be ISO 8601") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a safe exploit-class prediction portfolio from Prophet forecasts."
    )
    parser.add_argument("--forecast", required=True, help="Path to Direction B forecast JSON")
    parser.add_argument("--candidate", help="Path to Direction A candidate JSON")
    parser.add_argument("--out", help="Output JSON path; stdout when omitted")
    parser.add_argument(
        "--generated-at",
        help="Override generated_at for deterministic fixtures",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate an existing portfolio at --forecast instead of generating one",
    )
    args = parser.parse_args(argv)

    if args.validate_only:
        validate_prediction_portfolio(load_json(args.forecast))
        return 0

    forecast = load_json(args.forecast)
    candidate = load_json(args.candidate) if args.candidate else None
    portfolio = generate_prediction_portfolio(
        forecast,
        candidate,
        generated_at=args.generated_at,
    )
    output = json.dumps(portfolio, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
