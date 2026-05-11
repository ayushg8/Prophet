"""Generate and validate Prophet evidence bundles.

The bundle wraps existing Direction B, prediction portfolio, and Direction C
artifacts. It does not replace those contracts and intentionally avoids raw
payload strings, raw validation traffic, credentials, hostnames, or live IPs.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "prophet_evidence_bundle.v0.1"
DEFAULT_EVIDENCE_SCHEMA_PATH = Path(__file__).with_name(
    "prophet-evidence-bundle.schema.json"
)
NO_LIVE_TARGET_DATA_ASSERTION = (
    "No live target data is included; evidence contains only fixture, "
    "seeded-OSINT, product-family, and localhost sandbox metadata."
)
ASSET_SCHEMA_VERSION = "asset_inventory.v0.1"
POLICY_SCHEMA_VERSION = "prophet_pilot_policy.v0.1"

REPO_ROOT = Path(__file__).resolve().parents[1]
for rel_path in ("cyber-side", "world-side"):
    module_path = str(REPO_ROOT / rel_path)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

try:
    from predictor import (  # type: ignore
        BANNED_KEYS as PORTFOLIO_BANNED_KEYS,
        PAYLOAD_TOKENS as PORTFOLIO_PAYLOAD_TOKENS,
        PROCEDURAL_PHRASES as PORTFOLIO_PROCEDURAL_PHRASES,
        validate_prediction_portfolio,
    )
    from validator import (  # type: ignore
        BANNED_KEYS as ARTIFACT_BANNED_KEYS,
        PROCEDURAL_PHRASES as ARTIFACT_PROCEDURAL_PHRASES,
        validate_exploit_engine_artifact,
    )
    from forecaster.models import (  # type: ignore
        BANNED_VECTOR_KEYS,
        validate_world_forecast,
    )
except ImportError as exc:  # pragma: no cover - environment issue
    raise RuntimeError(
        "evidence.bundle requires PYTHONPATH=.:cyber-side:world-side"
    ) from exc

try:
    from assets.inventory import (  # type: ignore
        summarize_asset_seedset,
        validate_asset_seedset,
    )
except ImportError:  # pragma: no cover - asset enrichment is optional.
    summarize_asset_seedset = None  # type: ignore
    validate_asset_seedset = None  # type: ignore

try:
    from sandbox_runner.schema import validate_sandbox_run_manifest_schema  # type: ignore
except ImportError:  # pragma: no cover - sandbox provenance is optional.
    validate_sandbox_run_manifest_schema = None  # type: ignore


RAW_SOURCE_BANNED_KEYS = {
    "message_text",
    "raw_body",
    "raw_content",
    "raw_html",
    "raw_scrape_output",
    "raw_scraper_text",
    "raw_source_text",
    "raw_text",
    "scraper_output",
    "source_text",
}

BANNED_KEYS = (
    set(PORTFOLIO_BANNED_KEYS)
    | set(ARTIFACT_BANNED_KEYS)
    | set(BANNED_VECTOR_KEYS)
    | RAW_SOURCE_BANNED_KEYS
)
PROCEDURAL_PHRASES = tuple(
    sorted(set(PORTFOLIO_PROCEDURAL_PHRASES) | set(ARTIFACT_PROCEDURAL_PHRASES))
)
PAYLOAD_TOKENS = tuple(
    sorted(
        set(PORTFOLIO_PAYLOAD_TOKENS)
        | {
            "${jndi:",
            "${${",
            "ldap://",
            "rmi://",
            "dns://",
            "runtime.getruntime",
            "cmd.exe",
        }
    )
)
RAW_SOURCE_TEXT_MARKERS = (
    "message_text:",
    "raw scraper artifact:",
    "raw source body:",
    "raw_body:",
    "raw_html:",
    "unredacted source text:",
)

REQUIRED_SECTIONS = (
    "schema_version",
    "bundle_id",
    "generated_at",
    "input_refs",
    "operator_approval",
    "forecast_summary",
    "open_source_summary",
    "prediction_summary",
    "defense_summary",
    "validation_summary",
    "safety_attestation",
    "redaction_report",
    "source_refs",
    "hashes",
    "bundle_sha256",
)

MARKDOWN_SECTIONS = (
    "Executive Summary",
    "CISO Review Summary",
    "Forecast",
    "Open Source Basis",
    "Source Freshness And Failures",
    "Exploit-Class Portfolio",
    "Defense Artifact",
    "Validation",
    "Operator Approval",
    "Safety Attestation",
    "Redaction Report",
    "Policy Controls",
    "Asset/SBOM Seeds",
    "Source References",
    "Hashes",
)

POLICY_BLOCKED_CONTROLS = (
    "live_targets_allowed",
    "live_vm_scraper_allowed",
    "arbitrary_target_input_allowed",
    "payload_generation_allowed",
    "raw_scraper_text_allowed",
    "private_hostnames_allowed",
    "credentials_allowed",
)

POLICY_ALLOWED_MODES = {
    "asset_context": {"fixture", "customer_owned_metadata"},
    "osint_collection": {"fixture", "seeded_osint"},
    "forecast_generation": {"fixture", "seeded_osint"},
    "validation": {"fixture", "localhost_sandbox"},
    "evidence_generation": {"fixture", "localhost_sandbox"},
}

POLICY_REQUIRED_ATTESTATIONS = (
    "no_live_targets",
    "no_live_target_data_included",
    "no_payloads",
    "no_credentials",
    "no_raw_scraper_text",
    "no_private_hostnames",
)

POLICY_RETENTION_LIMITS = {
    "runtime_outputs_max_days": 90,
    "audit_log_max_days": 365,
    "customer_metadata_max_days": 90,
}

EVIDENCE_RUNTIME_OUTPUT_PREFIX = "evidence/outputs/runtime/"


class EvidenceBundleError(ValueError):
    """Raised when an evidence bundle or input violates the product contract."""


class EvidenceBundleSchemaError(EvidenceBundleError):
    """Raised when an evidence bundle drifts from the public JSON Schema."""


def load_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise EvidenceBundleError(f"{file_path} must decode to a JSON object")
    return data


def load_policy(path: str | Path) -> dict[str, Any]:
    """Load and validate a pilot policy file."""

    policy = load_json(path)
    validate_pilot_policy(policy)
    return policy


def build_evidence_bundle(
    *,
    forecast: dict[str, Any],
    portfolio: dict[str, Any],
    artifact: dict[str, Any],
    operator_label: str,
    approval_decision: str,
    generated_at: str | None = None,
    run_id: str | None = None,
    asset_inventory: dict[str, Any] | None = None,
    asset_seedset: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
    approval_record: dict[str, Any] | None = None,
    sandbox_run_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build, hash, and validate an evidence bundle from validated artifacts."""

    validate_world_forecast(forecast)
    validate_prediction_portfolio(portfolio)
    validate_exploit_engine_artifact(artifact)
    if asset_inventory is not None:
        validate_asset_inventory(asset_inventory)
    if asset_seedset is not None:
        _validate_asset_seedset(asset_seedset)
    policy_summary: dict[str, Any] | None = None
    if policy is not None:
        validate_pilot_policy(policy)
        _enforce_pilot_policy(policy, forecast=forecast, artifact=artifact)
        policy_summary = _policy_summary(policy)
    approval_record_summary: dict[str, Any] | None = None
    if approval_record is not None:
        approval_record_summary = _approval_record_summary(
            approval_record,
            operator_label=operator_label,
            approval_decision=approval_decision,
            policy_summary=policy_summary,
        )
    sandbox_provenance: dict[str, Any] | None = None
    if sandbox_run_manifest is not None:
        sandbox_provenance = _build_sandbox_provenance(
            sandbox_run_manifest,
            artifact=artifact,
            policy_summary=policy_summary,
        )

    emitted_at = _ensure_generated_at(generated_at)
    top_window = _first_ranked(forecast.get("strike_windows"))
    top_vector = _first_ranked(forecast.get("strike_vectors"))
    top_zero_day = _first_ranked(portfolio.get("zero_day_predictions"))
    top_one_day = _first_ranked(portfolio.get("one_day_predictions"))
    artifact_refs = _object(artifact.get("input_refs"))
    validation = _object(artifact.get("validation"))
    operator_notes = _object(artifact.get("operator_notes"))
    defense = _object(artifact.get("defense"))
    patch = _object(defense.get("patch"))
    sigma = _object(defense.get("sigma_rule"))

    forecast_id = _string(forecast.get("forecast_id"), "unknown-forecast")
    artifact_id = _string(artifact.get("artifact_id"), "unknown-artifact")
    bundle_seed = run_id or f"{forecast_id}:{artifact_id}:{emitted_at}"
    bundle_id = f"peb-{hashlib.sha256(bundle_seed.encode('utf-8')).hexdigest()[:16]}"

    approval_mode = (
        "fixture_bypass"
        if approval_decision == "bypassed_for_fixture" or operator_label == "fixture"
        else "human_gate"
    )
    source_refs = _collect_source_refs(forecast, portfolio, artifact)
    open_source_summary = _build_open_source_summary(forecast)

    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "generated_at": emitted_at,
        "input_refs": {
            "forecast_id": forecast_id,
            "candidate_id": _string(
                artifact_refs.get("candidate_id"),
                _string(forecast.get("input_candidate_id"), "unknown-candidate"),
            ),
            "portfolio_id": _string(portfolio.get("portfolio_id"), "unknown-portfolio"),
            "portfolio_forecast_id": _string(
                _object(portfolio.get("input_refs")).get("forecast_id"),
                "unknown-portfolio-forecast",
            ),
            "artifact_id": artifact_id,
            "vector_id": _string(
                artifact_refs.get("vector_id"),
                _string(top_vector.get("vector_id"), "unknown-vector"),
            ),
            "run_id": run_id or _string(_object(artifact.get("audit")).get("run_id"), bundle_id),
        },
        "operator_approval": {
            "decision": approval_decision,
            "operator_label": operator_label,
            "approval_mode": approval_mode,
            "timestamp": _string(artifact.get("generated_at"), emitted_at),
            "caveats": list(operator_notes.get("post_run_caveats") or []),
        },
        "forecast_summary": {
            "strike_window": {
                "start_date": _string(top_window.get("start_date"), "unknown"),
                "end_date": _string(top_window.get("end_date"), "unknown"),
                "confidence": _string(top_window.get("confidence"), "unknown"),
                "confidence_score": top_window.get("confidence_score"),
                "why_this_window": _sanitize_text(
                    _string(top_window.get("why_this_window"), "No rationale supplied.")
                ),
            },
            "vector": {
                "vector_id": _string(top_vector.get("vector_id"), "unknown-vector"),
                "vector_class": _sanitize_text(
                    _string(top_vector.get("vector_class"), "Unknown vector")
                ),
                "target_sector": _sanitize_text(
                    _string(top_vector.get("target_sector"), "Sector-level scope")
                ),
                "likely_objective": _string(top_vector.get("likely_objective"), "unknown"),
                "confidence": _string(top_vector.get("confidence"), "unknown"),
                "confidence_score": top_vector.get("confidence_score"),
                "why_this_vector": _sanitize_text(
                    _string(top_vector.get("why_this_vector"), "No rationale supplied.")
                ),
                "defensive_implication": _sanitize_text(
                    _string(top_vector.get("defensive_implication"), "Not supplied.")
                ),
            },
            "strategic_frame": {
                "adversary_class": _sanitize_text(
                    _string(_object(forecast.get("strategic_frame")).get("adversary_class"), "unknown")
                ),
                "target_scope": _sanitize_text(
                    _string(_object(forecast.get("strategic_frame")).get("target_scope"), "unknown")
                ),
                "geographic_scope": _sanitize_text(
                    _string(_object(forecast.get("strategic_frame")).get("geographic_scope"), "unknown")
                ),
            },
            "source_ref_ids": _source_ids_for(top_window, top_vector),
        },
        "open_source_summary": open_source_summary,
        "prediction_summary": {
            "top_zero_day_class": _sanitize_text(
                _string(top_zero_day.get("exploit_class_label"), "Unknown zero-day class")
            ),
            "top_one_day_class": _sanitize_text(
                _string(top_one_day.get("exploit_class_label"), "Unknown one-day class")
            ),
            "zero_day_count": len(portfolio.get("zero_day_predictions") or []),
            "one_day_count": len(portfolio.get("one_day_predictions") or []),
            "source_ref_ids": sorted(
                {
                    ref.get("id")
                    for ref in (top_zero_day.get("source_refs") or [])
                    + (top_one_day.get("source_refs") or [])
                    if isinstance(ref, dict) and isinstance(ref.get("id"), str)
                }
            ),
        },
        "defense_summary": {
            "patch_summary": _sanitize_text(_string(patch.get("summary"), "No patch summary.")),
            "patch_format": _string(patch.get("patch_format"), "unknown"),
            "sigma": {
                "title": _sanitize_text(_string(sigma.get("title"), "Untitled Sigma rule")),
                "rule_id": _string(sigma.get("rule_id"), "unknown-rule"),
                "level": _string(sigma.get("level"), "unknown"),
                "logsources": list(sigma.get("logsources") or []),
            },
        },
        "validation_summary": {
            "pre_patch_status": _string(validation.get("pre_patch_status"), "unknown"),
            "post_patch_status": _string(validation.get("post_patch_status"), "unknown"),
            "sandbox_scope": _sanitize_text(_string(validation.get("scope"), "unknown")),
            "sandbox_id": _sanitize_text(_string(validation.get("sandbox_id"), "fixture")),
            "validation_tool": _sanitize_text(
                _string(validation.get("validation_tool"), "fixture validation")
            ),
            "wall_time_seconds": validation.get("wall_time_seconds"),
            "sanitized_excerpts": {
                "pre_patch": _sanitize_text(
                    _string(validation.get("pre_patch_excerpt"), "No excerpt.")
                ),
                "post_patch": _sanitize_text(
                    _string(validation.get("post_patch_excerpt"), "No excerpt.")
                ),
            },
            "failure_evidence": _build_validation_failure_evidence(validation),
        },
        "safety_attestation": {
            "scope": "fixture_or_localhost_sandbox",
            "fixture_backed": approval_mode == "fixture_bypass",
            "no_live_targets": True,
            "no_live_target_data_included": True,
            "no_payloads": True,
            "no_credentials": True,
            "no_raw_scraper_text": True,
            "no_private_hostnames": True,
            "data_boundary_statement": NO_LIVE_TARGET_DATA_ASSERTION,
            "validation_scope": _sanitize_text(_string(validation.get("scope"), "unknown")),
            "attested_at": emitted_at,
        },
        "source_refs": source_refs,
        "hashes": {
            "forecast_sha256": _sha256_normalized(forecast),
            "portfolio_sha256": _sha256_normalized(portfolio),
            "artifact_sha256": _sha256_normalized(artifact),
            "bundle_body_sha256": "",
        },
    }

    if policy_summary is not None:
        bundle["policy"] = policy_summary
        bundle["hashes"]["policy_sha256"] = policy_summary["policy_sha256"]

    if approval_record_summary is not None:
        bundle["operator_approval"]["approval_record_hash"] = approval_record_summary[
            "approval_record_hash"
        ]
        bundle["operator_approval"]["approval_event_id"] = approval_record_summary[
            "approval_event_id"
        ]
        bundle["operator_approval"]["approval_chain"] = approval_record_summary[
            "approval_chain"
        ]
        bundle["hashes"]["approval_record_sha256"] = approval_record_summary[
            "approval_record_hash"
        ]

    if sandbox_provenance is not None:
        bundle["sandbox_provenance"] = sandbox_provenance
        bundle["hashes"]["sandbox_run_manifest_sha256"] = sandbox_provenance[
            "manifest_sha256"
        ]

    if open_source_summary["integrated"]:
        bundle["hashes"]["osint_snapshot_hashes"] = open_source_summary["hashes"]

    if asset_inventory is not None:
        bundle["asset_context"] = summarize_asset_context(asset_inventory, top_vector)
        bundle["hashes"]["asset_inventory_sha256"] = _sha256_normalized(asset_inventory)
    if asset_seedset is not None:
        bundle["asset_seed_summary"] = _build_asset_seed_summary(asset_seedset)
        bundle["hashes"]["asset_seedset_sha256"] = _sha256_normalized(asset_seedset)
        bundle["input_refs"]["asset_seedset_id"] = _string(
            asset_seedset.get("seedset_id"),
            "unknown-asset-seedset",
        )

    bundle["redaction_report"] = _build_evidence_redaction_report(bundle)

    digest = _bundle_body_sha256(bundle)
    bundle["hashes"]["bundle_body_sha256"] = digest
    bundle["bundle_sha256"] = digest
    validate_evidence_bundle(bundle)
    return bundle


def validate_evidence_bundle(bundle: dict[str, Any] | str) -> None:
    """Validate evidence bundle shape, scope, hashes, and text safety."""

    value = json.loads(bundle) if isinstance(bundle, str) else bundle
    if not isinstance(value, dict):
        raise EvidenceBundleError("evidence bundle must be an object")

    missing = [section for section in REQUIRED_SECTIONS if section not in value]
    if missing:
        raise EvidenceBundleError(f"evidence bundle missing sections: {missing}")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceBundleError(f"schema_version must be {SCHEMA_VERSION}")

    _scan_for_banned_keys(value, "bundle")
    _scan_text_safety(value, "bundle")

    for key in (
        "input_refs",
        "operator_approval",
        "forecast_summary",
        "open_source_summary",
        "prediction_summary",
        "defense_summary",
        "validation_summary",
        "safety_attestation",
        "redaction_report",
        "hashes",
    ):
        if not isinstance(value.get(key), dict):
            raise EvidenceBundleError(f"{key} must be object")
    if not isinstance(value.get("source_refs"), list) or not value["source_refs"]:
        raise EvidenceBundleError("source_refs must be a non-empty list")

    sanitized_excerpts = _object(value["validation_summary"].get("sanitized_excerpts"))
    _validate_evidence_redaction_report(
        value["redaction_report"],
        source_ref_count=len(value["source_refs"]),
        validation_excerpt_count=len(sanitized_excerpts),
    )

    validation = value["validation_summary"]
    scope = _string(validation.get("sandbox_scope"), "")
    fixture_backed = bool(value["safety_attestation"].get("fixture_backed"))
    approval_mode = _string(value["operator_approval"].get("approval_mode"), "")
    if "localhost" not in scope.lower() and not (
        fixture_backed or approval_mode == "fixture_bypass"
    ):
        raise EvidenceBundleError(
            "validation_summary.sandbox_scope must be localhost-only unless fixture-backed"
        )
    _validate_validation_failure_evidence(validation)

    for flag in (
        "no_live_targets",
        "no_live_target_data_included",
        "no_payloads",
        "no_credentials",
        "no_raw_scraper_text",
    ):
        if value["safety_attestation"].get(flag) is not True:
            raise EvidenceBundleError(f"safety_attestation.{flag} must be true")
    if not _string(value["safety_attestation"].get("data_boundary_statement"), ""):
        raise EvidenceBundleError("safety_attestation.data_boundary_statement must be non-empty")

    approval_hash = _string(value["operator_approval"].get("approval_record_hash"), "")
    if approval_hash:
        if not _is_sha256(approval_hash):
            raise EvidenceBundleError("operator_approval.approval_record_hash must be SHA-256")
        if value["hashes"].get("approval_record_sha256") != approval_hash:
            raise EvidenceBundleError(
                "hashes.approval_record_sha256 must match operator approval record hash"
            )
        approval_chain = value["operator_approval"].get("approval_chain")
        if not isinstance(approval_chain, dict):
            raise EvidenceBundleError("operator_approval.approval_chain must be object")

    validate_evidence_bundle_schema(value)

    expected = _bundle_body_sha256(value)
    if value.get("bundle_sha256") != expected:
        raise EvidenceBundleError("bundle_sha256 does not match canonical bundle body")
    if value["hashes"].get("bundle_body_sha256") != expected:
        raise EvidenceBundleError("hashes.bundle_body_sha256 does not match bundle body")

    seen_refs: set[str] = set()
    for idx, ref in enumerate(value["source_refs"]):
        if not isinstance(ref, dict):
            raise EvidenceBundleError(f"source_refs[{idx}] must be object")
        ref_id = _string(ref.get("id"), "")
        if not ref_id:
            raise EvidenceBundleError(f"source_refs[{idx}].id is required")
        if ref_id in seen_refs:
            raise EvidenceBundleError(f"duplicate source ref id: {ref_id}")
        seen_refs.add(ref_id)
        for key in ("label", "url", "supports"):
            if not _string(ref.get(key), ""):
                raise EvidenceBundleError(f"source_refs[{idx}].{key} is required")

    if "asset_context" in value and not isinstance(value["asset_context"], dict):
        raise EvidenceBundleError("asset_context must be object when present")
    if "asset_seed_summary" in value and not isinstance(value["asset_seed_summary"], dict):
        raise EvidenceBundleError("asset_seed_summary must be object when present")
    if "sandbox_provenance" in value:
        _validate_sandbox_provenance(
            value["sandbox_provenance"],
            artifact_sha256=_string(value["hashes"].get("artifact_sha256"), ""),
            policy_sha256=_string(value["hashes"].get("policy_sha256"), ""),
        )
    if "policy" in value:
        policy_summary = value["policy"]
        if not isinstance(policy_summary, dict):
            raise EvidenceBundleError("policy must be object when present")
        if not _string(policy_summary.get("policy_id"), ""):
            raise EvidenceBundleError("policy.policy_id is required")
        if policy_summary.get("schema_version") != POLICY_SCHEMA_VERSION:
            raise EvidenceBundleError(
                f"policy.schema_version must be {POLICY_SCHEMA_VERSION}"
            )
        policy_sha = _string(policy_summary.get("policy_sha256"), "")
        if not _is_sha256(policy_sha):
            raise EvidenceBundleError("policy.policy_sha256 must be SHA-256")
        if value["hashes"].get("policy_sha256") != policy_sha:
            raise EvidenceBundleError("hashes.policy_sha256 must match policy.policy_sha256")
        if not isinstance(policy_summary.get("allowed_modes"), dict):
            raise EvidenceBundleError("policy.allowed_modes must be object")
        if not isinstance(policy_summary.get("controls"), dict):
            raise EvidenceBundleError("policy.controls must be object")
        if not isinstance(policy_summary.get("retention"), dict):
            raise EvidenceBundleError("policy.retention must be object")


def validate_evidence_bundle_schema(
    bundle: dict[str, Any] | str,
    *,
    schema_path: str | Path = DEFAULT_EVIDENCE_SCHEMA_PATH,
) -> None:
    """Validate an evidence bundle against the published JSON Schema."""

    value = json.loads(bundle) if isinstance(bundle, str) else bundle
    if not isinstance(value, dict):
        raise EvidenceBundleSchemaError("evidence bundle must be an object")

    try:
        from policy.lint import PolicySchemaError, validate_json_schema_value  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment issue
        raise EvidenceBundleSchemaError(
            "evidence bundle schema validation requires policy.lint"
        ) from exc

    schema = load_json(schema_path)
    try:
        validate_json_schema_value(value, schema)
    except PolicySchemaError as exc:
        raise EvidenceBundleSchemaError(
            f"evidence bundle schema validation failed: {exc}"
        ) from exc


def validate_pilot_policy(policy: dict[str, Any] | str) -> None:
    """Validate the small pilot policy contract used by demo evidence."""

    value = json.loads(policy) if isinstance(policy, str) else policy
    if not isinstance(value, dict):
        raise EvidenceBundleError("pilot policy must be an object")
    if value.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise EvidenceBundleError(f"policy schema_version must be {POLICY_SCHEMA_VERSION}")
    if not _string(value.get("policy_id"), ""):
        raise EvidenceBundleError("policy_id is required")

    allowed_modes = value.get("allowed_modes")
    if not isinstance(allowed_modes, dict):
        raise EvidenceBundleError("policy.allowed_modes must be object")
    unexpected_categories = sorted(set(allowed_modes) - set(POLICY_ALLOWED_MODES))
    if unexpected_categories:
        raise EvidenceBundleError(
            f"policy.allowed_modes has unknown categories: {unexpected_categories}"
        )
    for category, allowed in POLICY_ALLOWED_MODES.items():
        modes = allowed_modes.get(category)
        if not isinstance(modes, list) or not modes or not all(
            isinstance(item, str) for item in modes
        ):
            raise EvidenceBundleError(f"policy.allowed_modes.{category} must be list[str]")
        duplicate_modes = sorted({item for item in modes if modes.count(item) > 1})
        if duplicate_modes:
            raise EvidenceBundleError(
                f"policy.allowed_modes.{category} has duplicate modes: {duplicate_modes}"
            )
        unknown_modes = sorted(set(modes) - allowed)
        if unknown_modes:
            raise EvidenceBundleError(
                f"policy.allowed_modes.{category} has unknown modes: {unknown_modes}"
            )

    controls = value.get("controls")
    if not isinstance(controls, dict):
        raise EvidenceBundleError("policy.controls must be object")
    unexpected_controls = sorted(set(controls) - set(POLICY_BLOCKED_CONTROLS))
    if unexpected_controls:
        raise EvidenceBundleError(f"policy.controls has unknown controls: {unexpected_controls}")
    for control in POLICY_BLOCKED_CONTROLS:
        if controls.get(control) is not False:
            raise EvidenceBundleError(f"policy.controls.{control} must be false")

    attestations = value.get("required_attestations")
    if not isinstance(attestations, list) or not attestations:
        raise EvidenceBundleError("policy.required_attestations must be non-empty list")
    for item in attestations:
        if not isinstance(item, str) or not item.strip():
            raise EvidenceBundleError("policy.required_attestations must contain strings")
    missing_attestations = sorted(set(POLICY_REQUIRED_ATTESTATIONS) - set(attestations))
    if missing_attestations:
        raise EvidenceBundleError(
            f"policy.required_attestations missing required values: {missing_attestations}"
        )
    _validate_policy_retention(value.get("retention"))


def validate_asset_inventory(inventory: dict[str, Any] | str) -> None:
    """Validate fictional/customer-owned asset context for evidence enrichment."""

    value = json.loads(inventory) if isinstance(inventory, str) else inventory
    if not isinstance(value, dict):
        raise EvidenceBundleError("asset inventory must be an object")
    if value.get("schema_version") != ASSET_SCHEMA_VERSION:
        raise EvidenceBundleError(f"asset inventory schema_version must be {ASSET_SCHEMA_VERSION}")
    _scan_for_banned_keys(value, "asset_inventory")
    _scan_asset_text_safety(value, "asset_inventory")

    assets = value.get("assets")
    if not isinstance(assets, list) or not assets:
        raise EvidenceBundleError("asset inventory requires non-empty assets")
    for idx, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise EvidenceBundleError(f"assets[{idx}] must be object")
        for key in (
            "asset_id",
            "product_family",
            "exposure_class",
            "owner_group",
            "environment",
            "business_criticality",
            "sbom_components",
            "known_cve_overlaps",
            "compensating_controls",
        ):
            if key not in asset:
                raise EvidenceBundleError(f"assets[{idx}] missing {key}")
        if not isinstance(asset["sbom_components"], list):
            raise EvidenceBundleError(f"assets[{idx}].sbom_components must be list")
        if not isinstance(asset["known_cve_overlaps"], list):
            raise EvidenceBundleError(f"assets[{idx}].known_cve_overlaps must be list")
        if not isinstance(asset["compensating_controls"], list):
            raise EvidenceBundleError(f"assets[{idx}].compensating_controls must be list")


def summarize_asset_context(
    inventory: dict[str, Any],
    top_vector: dict[str, Any],
) -> dict[str, Any]:
    """Summarize fictional asset/SBOM context for CISO-readable evidence."""

    validate_asset_inventory(inventory)
    assets = [asset for asset in inventory.get("assets", []) if isinstance(asset, dict)]
    vector_text = json.dumps(top_vector, sort_keys=True).lower()
    matched_assets = [
        asset
        for asset in assets
        if _string(asset.get("exposure_class"), "").replace("_", " ") in vector_text
        or "edge" in _string(asset.get("exposure_class"), "").lower()
    ]
    if not matched_assets:
        matched_assets = assets

    criticality: dict[str, int] = {}
    owner_groups: list[str] = []
    cve_counts: dict[str, int] = {}
    packages: dict[str, int] = {}
    for asset in matched_assets:
        crit = _string(asset.get("business_criticality"), "unknown")
        criticality[crit] = criticality.get(crit, 0) + 1
        owner = _string(asset.get("owner_group"), "")
        if owner and owner not in owner_groups:
            owner_groups.append(owner)
        for cve in asset.get("known_cve_overlaps") or []:
            if isinstance(cve, str) and cve.strip():
                cve_counts[cve.strip()] = cve_counts.get(cve.strip(), 0) + 1
        for component in asset.get("sbom_components") or []:
            if not isinstance(component, dict):
                continue
            name = _string(component.get("name"), "")
            if name:
                packages[name] = packages.get(name, 0) + 1

    return {
        "inventory_id": _string(inventory.get("inventory_id"), "unknown-inventory"),
        "schema_version": ASSET_SCHEMA_VERSION,
        "fixture_context": bool(inventory.get("fixture", True)),
        "matched_exposure_class": _string(
            matched_assets[0].get("exposure_class") if matched_assets else None,
            "sector-level exposure",
        ),
        "affected_asset_count": len(matched_assets),
        "criticality_summary": dict(sorted(criticality.items())),
        "package_cve_overlap_summary": {
            "packages": dict(sorted(packages.items())),
            "known_cve_overlaps": dict(sorted(cve_counts.items())),
        },
        "recommended_owner_queue": owner_groups,
        "context_statement": _sanitize_text(
            _string(
                inventory.get("scope"),
                "Fixture/customer-owned context only; no live targets are named.",
            )
        ),
    }


def _validate_asset_seedset(seedset: dict[str, Any]) -> None:
    if validate_asset_seedset is not None:
        validate_asset_seedset(seedset)
        return
    if not isinstance(seedset, dict):
        raise EvidenceBundleError("asset seedset must be object")
    if seedset.get("schema_version") != "asset_osint_seedset.v0.1":
        raise EvidenceBundleError("asset seedset schema_version must be asset_osint_seedset.v0.1")
    _scan_for_banned_keys(seedset, "asset_seedset")
    _scan_asset_text_safety(seedset, "asset_seedset")


def _build_asset_seed_summary(seedset: dict[str, Any]) -> dict[str, Any]:
    _validate_asset_seedset(seedset)
    if summarize_asset_seedset is not None:
        summary = summarize_asset_seedset(seedset)
    else:
        summary = {
            "seedset_id": _string(seedset.get("seedset_id"), "unknown-asset-seedset"),
            "schema_version": _string(seedset.get("schema_version"), "asset_osint_seedset.v0.1"),
            "fixture_context": bool(seedset.get("fixture_context", True)),
            "asset_count": _int_value(_object(seedset.get("input_refs")).get("asset_count")),
            "exposure_classes": [
                _string(item.get("exposure_class"), "")
                for item in seedset.get("exposure_class_seeds", [])
                if isinstance(item, dict)
            ],
            "product_families": [
                _string(item.get("product_family"), "")
                for item in seedset.get("product_family_seeds", [])
                if isinstance(item, dict)
            ],
            "package_seed_count": len(seedset.get("package_seeds") or []),
            "cve_seed_count": len(seedset.get("cve_seeds") or []),
            "recommended_source_ids": _string_list(seedset.get("recommended_source_ids")),
            "owner_queues": [
                _string(item.get("owner_group"), "")
                for item in seedset.get("owner_queues", [])
                if isinstance(item, dict)
            ],
            "seedset_sha256": _string(seedset.get("seedset_sha256"), ""),
            "basis_statement": "Asset/SBOM seedset supplied safe open-source enrichment keys.",
        }
    return {
        "seedset_id": _sanitize_text(_string(summary.get("seedset_id"), "unknown-asset-seedset")),
        "schema_version": _string(summary.get("schema_version"), "asset_osint_seedset.v0.1"),
        "fixture_context": bool(summary.get("fixture_context", True)),
        "asset_count": _int_value(summary.get("asset_count")),
        "exposure_classes": _string_list(summary.get("exposure_classes")),
        "product_families": _string_list(summary.get("product_families")),
        "package_seed_count": _int_value(summary.get("package_seed_count")),
        "cve_seed_count": _int_value(summary.get("cve_seed_count")),
        "recommended_source_ids": _string_list(summary.get("recommended_source_ids")),
        "owner_queues": _string_list(summary.get("owner_queues")),
        "seedset_sha256": _sanitize_text(_string(summary.get("seedset_sha256"), "")),
        "basis_statement": _sanitize_text(
            _string(
                summary.get("basis_statement"),
                "Asset/SBOM seedset supplied safe open-source enrichment keys.",
            )
        ),
    }


def _build_sandbox_provenance(
    manifest: dict[str, Any],
    *,
    artifact: dict[str, Any],
    policy_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if validate_sandbox_run_manifest_schema is not None:
        validate_sandbox_run_manifest_schema(manifest)
    elif manifest.get("schema_version") != "prophet.sandbox_run_manifest.v0.1":
        raise EvidenceBundleError(
            "sandbox_run_manifest.schema_version must be prophet.sandbox_run_manifest.v0.1"
        )

    artifact_summary = _object(manifest.get("artifact"))
    log_evidence = _object(manifest.get("log_evidence"))
    policy = _object(manifest.get("policy"))
    safety = _object(manifest.get("safety"))
    artifact_sha256 = _sha256_normalized(artifact)
    manifest_artifact_sha256 = _string(artifact_summary.get("content_sha256"), "")
    if manifest_artifact_sha256 != artifact_sha256:
        raise EvidenceBundleError(
            "sandbox run manifest artifact.content_sha256 must match evidence artifact"
        )
    artifact_id = _string(artifact.get("artifact_id"), "")
    if _string(artifact_summary.get("artifact_id"), "") != artifact_id:
        raise EvidenceBundleError(
            "sandbox run manifest artifact.artifact_id must match evidence artifact"
        )
    if policy_summary is not None:
        manifest_policy_sha = _string(policy.get("policy_sha256"), "")
        if manifest_policy_sha and manifest_policy_sha != policy_summary["policy_sha256"]:
            raise EvidenceBundleError(
                "sandbox run manifest policy hash must match evidence policy"
            )
    for key in (
        "localhost_only",
        "fixture_backed",
        "no_network_egress",
        "no_live_targets",
        "no_payloads",
        "no_credentials",
        "no_raw_logs",
    ):
        if safety.get(key) is not True:
            raise EvidenceBundleError(f"sandbox run manifest safety.{key} must be true")
    if log_evidence.get("raw_logs_retained") is not False:
        raise EvidenceBundleError("sandbox run manifest must not retain raw logs")
    if log_evidence.get("raw_log_path") is not None:
        raise EvidenceBundleError("sandbox run manifest raw_log_path must be null")

    return {
        "schema_version": _string(manifest.get("schema_version"), ""),
        "manifest_id": _string(manifest.get("manifest_id"), ""),
        "run_id": _string(manifest.get("run_id"), ""),
        "profile": _string(manifest.get("profile"), ""),
        "mode": _string(manifest.get("mode"), ""),
        "artifact_id": artifact_id,
        "artifact_schema_version": _string(artifact_summary.get("schema_version"), ""),
        "artifact_content_sha256": manifest_artifact_sha256,
        "artifact_file_sha256": artifact_summary.get("file_sha256"),
        "artifact_path": _sanitize_text(_string(artifact_summary.get("path"), "")),
        "manifest_sha256": _sha256_normalized(manifest),
        "sanitized_logs_sha256": _string(log_evidence.get("sanitized_logs_sha256"), ""),
        "raw_logs_retained": False,
        "stored_raw_log_bytes": _int_value(log_evidence.get("stored_raw_log_bytes")),
        "stored_log_excerpt_count": _int_value(log_evidence.get("stored_log_excerpt_count")),
        "policy_id": _string(policy.get("policy_id"), "not-supplied"),
        "policy_sha256": policy.get("policy_sha256"),
        "localhost_only": True,
        "fixture_backed": True,
        "no_network_egress": True,
        "no_live_targets": True,
        "no_payloads": True,
        "no_credentials": True,
        "no_raw_logs": True,
    }


def _validate_sandbox_provenance(
    provenance: Any,
    *,
    artifact_sha256: str,
    policy_sha256: str,
) -> None:
    if not isinstance(provenance, dict):
        raise EvidenceBundleError("sandbox_provenance must be object")
    for field in (
        "schema_version",
        "manifest_id",
        "run_id",
        "profile",
        "mode",
        "artifact_id",
        "artifact_schema_version",
        "artifact_content_sha256",
        "artifact_path",
        "manifest_sha256",
        "sanitized_logs_sha256",
        "policy_id",
    ):
        if not _string(provenance.get(field), ""):
            raise EvidenceBundleError(f"sandbox_provenance.{field} must be non-empty")
    if provenance["schema_version"] != "prophet.sandbox_run_manifest.v0.1":
        raise EvidenceBundleError(
            "sandbox_provenance.schema_version must be prophet.sandbox_run_manifest.v0.1"
        )
    for field in ("artifact_content_sha256", "manifest_sha256", "sanitized_logs_sha256"):
        if not _is_sha256(_string(provenance.get(field), "")):
            raise EvidenceBundleError(f"sandbox_provenance.{field} must be SHA-256")
    artifact_file_sha = provenance.get("artifact_file_sha256")
    if artifact_file_sha is not None and not _is_sha256(_string(artifact_file_sha, "")):
        raise EvidenceBundleError("sandbox_provenance.artifact_file_sha256 must be SHA-256 or null")
    policy_sha = provenance.get("policy_sha256")
    if policy_sha is not None and not _is_sha256(_string(policy_sha, "")):
        raise EvidenceBundleError("sandbox_provenance.policy_sha256 must be SHA-256 or null")
    if artifact_sha256 and provenance["artifact_content_sha256"] != artifact_sha256:
        raise EvidenceBundleError(
            "sandbox_provenance.artifact_content_sha256 must match hashes.artifact_sha256"
        )
    if policy_sha256 and provenance.get("policy_sha256") != policy_sha256:
        raise EvidenceBundleError(
            "sandbox_provenance.policy_sha256 must match hashes.policy_sha256"
        )
    for key in (
        "raw_logs_retained",
        "localhost_only",
        "fixture_backed",
        "no_network_egress",
        "no_live_targets",
        "no_payloads",
        "no_credentials",
        "no_raw_logs",
    ):
        if not isinstance(provenance.get(key), bool):
            raise EvidenceBundleError(f"sandbox_provenance.{key} must be boolean")
    if provenance["raw_logs_retained"] is not False:
        raise EvidenceBundleError("sandbox_provenance.raw_logs_retained must be false")
    for key in (
        "localhost_only",
        "fixture_backed",
        "no_network_egress",
        "no_live_targets",
        "no_payloads",
        "no_credentials",
        "no_raw_logs",
    ):
        if provenance[key] is not True:
            raise EvidenceBundleError(f"sandbox_provenance.{key} must be true")
    for field in ("stored_raw_log_bytes", "stored_log_excerpt_count"):
        value = provenance.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise EvidenceBundleError(f"sandbox_provenance.{field} must be non-negative integer")


def _build_validation_failure_evidence(validation: dict[str, Any]) -> dict[str, Any]:
    pre_status = _string(validation.get("pre_patch_status"), "unknown")
    post_status = _string(validation.get("post_patch_status"), "unknown")
    pre_excerpt = _string(validation.get("pre_patch_excerpt"), "")
    post_excerpt = _string(validation.get("post_patch_excerpt"), "")
    combined = f"{pre_status} {post_status} {pre_excerpt} {post_excerpt}".lower()
    timeout_observed = "timeout" in combined or "timed out" in combined
    timeout_seconds = validation.get("timeout_seconds")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        timeout_seconds = None

    passed = post_status in {"blocked", "not_vulnerable"}
    if timeout_observed:
        result = "timeout"
        failure_kind = "timeout"
        summary = (
            "Validation reported a timeout in the localhost sandbox; evidence keeps only "
            "sanitized status and excerpts."
        )
        operator_action = (
            "Treat as inconclusive and rerun approved localhost fixture validation before "
            "buyer handoff."
        )
    elif passed:
        result = "passed"
        failure_kind = "none"
        summary = (
            "Post-patch validation reported a blocked or not-vulnerable outcome in the "
            "localhost sandbox."
        )
        operator_action = "No failure action required for the fixture-backed pilot path."
    elif "error" in {pre_status, post_status}:
        result = "failed"
        failure_kind = "validation_error"
        summary = (
            "Validation reported an error in the localhost sandbox; evidence keeps only "
            "sanitized status and excerpts."
        )
        operator_action = (
            "Treat as inconclusive, inspect the sanitized sandbox run manifest, and rerun "
            "approved fixture validation."
        )
    else:
        result = "failed"
        failure_kind = "defense_not_blocked"
        summary = (
            "Post-patch validation did not report a blocked or not-vulnerable outcome in "
            "the localhost sandbox."
        )
        operator_action = (
            "Do not present the defense as effective; revise the defense candidate and "
            "regenerate evidence."
        )

    return {
        "result": result,
        "failure_detected": result != "passed",
        "failure_kind": failure_kind,
        "timeout_observed": timeout_observed,
        "timeout_seconds": timeout_seconds,
        "summary": _sanitize_text(summary),
        "operator_action": _sanitize_text(operator_action),
    }


def _validate_validation_failure_evidence(validation: dict[str, Any]) -> None:
    post_status = _string(validation.get("post_patch_status"), "")
    passed = post_status in {"blocked", "not_vulnerable"}
    evidence = validation.get("failure_evidence")
    if evidence is None:
        if passed:
            return
        raise EvidenceBundleError(
            "validation_summary.failure_evidence is required for failed validation"
        )
    if not isinstance(evidence, dict):
        raise EvidenceBundleError("validation_summary.failure_evidence must be object")

    result = _string(evidence.get("result"), "")
    failure_kind = _string(evidence.get("failure_kind"), "")
    if result not in {"passed", "failed", "timeout"}:
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.result must be passed, failed, or timeout"
        )
    if failure_kind not in {"none", "defense_not_blocked", "validation_error", "timeout"}:
        raise EvidenceBundleError("validation_summary.failure_evidence.failure_kind is invalid")
    if not isinstance(evidence.get("failure_detected"), bool):
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.failure_detected must be boolean"
        )
    if not isinstance(evidence.get("timeout_observed"), bool):
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.timeout_observed must be boolean"
        )
    timeout_seconds = evidence.get("timeout_seconds")
    if timeout_seconds is not None and (
        not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
        or timeout_seconds < 0
    ):
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.timeout_seconds must be non-negative or null"
        )
    for field in ("summary", "operator_action"):
        if not _string(evidence.get(field), ""):
            raise EvidenceBundleError(
                f"validation_summary.failure_evidence.{field} must be non-empty"
            )
    if evidence["failure_detected"] != (result != "passed"):
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.failure_detected does not match result"
        )
    if passed and result != "passed":
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.result conflicts with post_patch_status"
        )
    if not passed and result == "passed":
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.result conflicts with failed validation"
        )
    if evidence["timeout_observed"] != (failure_kind == "timeout"):
        raise EvidenceBundleError(
            "validation_summary.failure_evidence.timeout_observed conflicts with failure_kind"
        )


def _validation_failure_evidence_for_markdown(validation: dict[str, Any]) -> dict[str, Any]:
    evidence = validation.get("failure_evidence")
    if isinstance(evidence, dict):
        return {
            "result": _string(evidence.get("result"), "passed"),
            "failure_detected": bool(evidence.get("failure_detected")),
            "failure_kind": _string(evidence.get("failure_kind"), "none"),
            "timeout_observed": bool(evidence.get("timeout_observed")),
            "timeout_seconds": evidence.get("timeout_seconds"),
            "summary": _string(evidence.get("summary"), "No failure evidence recorded."),
            "operator_action": _string(
                evidence.get("operator_action"),
                "Review validation status before buyer handoff.",
            ),
        }
    return _build_validation_failure_evidence(
        {
            "pre_patch_status": validation.get("pre_patch_status"),
            "post_patch_status": validation.get("post_patch_status"),
            "pre_patch_excerpt": _object(validation.get("sanitized_excerpts")).get("pre_patch"),
            "post_patch_excerpt": _object(validation.get("sanitized_excerpts")).get("post_patch"),
            "timeout_seconds": None,
        }
    )


def _build_evidence_redaction_report(bundle: dict[str, Any]) -> dict[str, Any]:
    validation = _object(bundle.get("validation_summary"))
    sanitized_excerpts = _object(validation.get("sanitized_excerpts"))
    return {
        "summary_fields_only": True,
        "source_documents_embedded": False,
        "raw_forecast_embedded": False,
        "raw_prediction_portfolio_embedded": False,
        "raw_defense_artifact_embedded": False,
        "raw_validation_logs_embedded": False,
        "raw_osint_records_embedded": False,
        "raw_asset_inventory_embedded": False,
        "sandbox_run_manifest_embedded": "sandbox_provenance" in bundle,
        "source_refs_emitted": len(bundle.get("source_refs") or []),
        "sanitized_validation_excerpts_emitted": len(sanitized_excerpts),
        "field_allowlist": [
            "asset_context summary",
            "asset_seed_summary summary",
            "bundle_id",
            "defense_summary",
            "forecast_summary",
            "hashes",
            "input_refs",
            "open_source_summary",
            "operator_approval",
            "policy",
            "prediction_summary",
            "safety_attestation",
            "source_refs",
            "sandbox_provenance summary",
            "validation_summary.failure_evidence",
            "validation_summary.sanitized_excerpts",
        ],
        "redacted_fields": [
            "raw forecast artifact body",
            "raw prediction portfolio body",
            "raw defense artifact body",
            "raw validation logs and traffic",
            "raw OSINT snapshot records",
            "raw customer asset rows",
            "exploit payload strings",
            "credentials and secrets",
            "private hostnames and live IPs",
        ],
        "blocked_text_classes": [
            "credential-like text",
            "hostname-like text",
            "IP-like text",
            "payload-like tokens",
            "procedural exploit text",
            "raw scraper text",
        ],
        "operator_review_required": True,
    }


def _validate_evidence_redaction_report(
    report: dict[str, Any],
    *,
    source_ref_count: int,
    validation_excerpt_count: int,
) -> None:
    bool_fields = (
        "summary_fields_only",
        "source_documents_embedded",
        "raw_forecast_embedded",
        "raw_prediction_portfolio_embedded",
        "raw_defense_artifact_embedded",
        "raw_validation_logs_embedded",
        "raw_osint_records_embedded",
        "raw_asset_inventory_embedded",
        "sandbox_run_manifest_embedded",
        "operator_review_required",
    )
    for field in bool_fields:
        if not isinstance(report.get(field), bool):
            raise EvidenceBundleError(f"redaction_report.{field} must be boolean")
    if report.get("summary_fields_only") is not True:
        raise EvidenceBundleError("redaction_report.summary_fields_only must be true")
    for field in (
        "source_documents_embedded",
        "raw_forecast_embedded",
        "raw_prediction_portfolio_embedded",
        "raw_defense_artifact_embedded",
        "raw_validation_logs_embedded",
        "raw_osint_records_embedded",
        "raw_asset_inventory_embedded",
    ):
        if report.get(field) is not False:
            raise EvidenceBundleError(f"redaction_report.{field} must be false")
    if report.get("operator_review_required") is not True:
        raise EvidenceBundleError("redaction_report.operator_review_required must be true")
    if report.get("source_refs_emitted") != source_ref_count:
        raise EvidenceBundleError("redaction_report.source_refs_emitted does not match source_refs")
    if report.get("sanitized_validation_excerpts_emitted") != validation_excerpt_count:
        raise EvidenceBundleError(
            "redaction_report.sanitized_validation_excerpts_emitted does not match validation"
        )
    for field in ("field_allowlist", "redacted_fields", "blocked_text_classes"):
        items = report.get(field)
        if not isinstance(items, list) or not items:
            raise EvidenceBundleError(f"redaction_report.{field} must be non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in items):
            raise EvidenceBundleError(
                f"redaction_report.{field} must contain non-empty strings"
            )


def render_markdown(bundle: dict[str, Any]) -> str:
    """Render a CISO-readable Markdown evidence report."""

    validate_evidence_bundle(bundle)
    input_refs = bundle["input_refs"]
    forecast = bundle["forecast_summary"]
    vector = forecast["vector"]
    window = forecast["strike_window"]
    prediction = bundle["prediction_summary"]
    open_source = bundle["open_source_summary"]
    freshness = open_source["freshness"]
    source_health = open_source["source_health"]
    defense = bundle["defense_summary"]
    validation = bundle["validation_summary"]
    failure_evidence = _validation_failure_evidence_for_markdown(validation)
    approval = bundle["operator_approval"]
    safety = bundle["safety_attestation"]
    redaction = bundle["redaction_report"]
    policy = bundle.get("policy")
    hashes = bundle["hashes"]
    asset_context = bundle.get("asset_context")
    asset_seed_summary = bundle.get("asset_seed_summary")
    sandbox_provenance = bundle.get("sandbox_provenance")
    policy_label = policy["policy_id"] if policy else "not supplied"
    approval_hash = approval.get("approval_record_hash", "not supplied")
    asset_summary = (
        f"{asset_context['affected_asset_count']} affected fixture asset(s), "
        f"criticality {_inline_json(asset_context['criticality_summary'])}"
        if asset_context
        else "no asset context supplied"
    )
    duplicate_source_summary = _object(open_source.get("duplicate_source_summary"))
    duplicate_source_lines: list[str] = []
    if duplicate_source_summary:
        duplicate_ids = duplicate_source_summary.get("duplicate_source_ids") or []
        duplicate_label = ", ".join(duplicate_ids) if duplicate_ids else "path-only duplicates"
        duplicate_source_lines.append(
            "- Duplicate source collapse: "
            f"{duplicate_source_summary['collapsed_duplicate_count']} duplicate mention(s) "
            f"collapsed ({duplicate_label})"
        )

    lines = [
        "# Prophet Evidence Bundle",
        "",
        "## Executive Summary",
        "",
        (
            f"Bundle `{bundle['bundle_id']}` records a validated Prophet fixture run "
            f"for forecast `{input_refs['forecast_id']}` and defense artifact "
            f"`{input_refs['artifact_id']}`. The prioritized vector is "
            f"{vector['vector_class']} for the {window['start_date']} to "
            f"{window['end_date']} strike window. Validation finished with "
            f"`{validation['post_patch_status']}`."
        ),
        "",
        "## CISO Review Summary",
        "",
        "| Review area | Evidence in this bundle |",
        "|---|---|",
        (
            f"| Strike window | {_markdown_cell(window['start_date'])} to "
            f"{_markdown_cell(window['end_date'])}; "
            f"{_markdown_cell(window['confidence'])} confidence |"
        ),
        f"| Priority vector | {_markdown_cell(vector['vector_class'])} |",
        f"| Business scope | {_markdown_cell(forecast['strategic_frame']['target_scope'])} |",
        f"| Asset context | {_markdown_cell(asset_summary)} |",
        (
            f"| Defensive result | Pre-patch `{_markdown_cell(validation['pre_patch_status'])}`; "
            f"post-patch `{_markdown_cell(validation['post_patch_status'])}` |"
        ),
        (
            f"| Validation evidence | Result `{_markdown_cell(failure_evidence['result'])}`; "
            f"failure kind `{_markdown_cell(failure_evidence['failure_kind'])}` |"
        ),
        (
            f"| Safety boundary | No live targets: `{str(safety['no_live_targets']).lower()}`; "
            f"no live target data included: "
            f"`{str(safety['no_live_target_data_included']).lower()}` |"
        ),
        (
            f"| Policy and approval | Policy `{_markdown_cell(policy_label)}`; "
            f"approval record `{_markdown_cell(approval_hash)}` |"
        ),
        (
            f"| Redaction | Summary fields only: "
            f"`{str(redaction['summary_fields_only']).lower()}`; "
            f"raw source documents embedded: "
            f"`{str(redaction['source_documents_embedded']).lower()}` |"
        ),
        f"| Integrity proof | Bundle SHA-256 `{_markdown_cell(bundle['bundle_sha256'])}` |",
        "",
        "## Forecast",
        "",
        f"- Strike window: {window['start_date']} to {window['end_date']} ({window['confidence']} confidence)",
        f"- Vector: {vector['vector_class']} ({vector['confidence']} confidence)",
        f"- Target scope: {forecast['strategic_frame']['target_scope']}",
        f"- Why this window: {window['why_this_window']}",
        f"- Why this vector: {vector['why_this_vector']}",
        f"- Defensive implication: {vector['defensive_implication']}",
        f"- Cited forecast source IDs: {', '.join(forecast['source_ref_ids'])}",
        "",
        "## Open Source Basis",
        "",
        f"- Integrated: `{str(open_source['integrated']).lower()}`",
        f"- Sanitized record count: {open_source['record_count']}",
        f"- Source types: {_inline_json(open_source['source_type_counts'])}",
        f"- Successful sources: {', '.join(open_source['successful_sources']) if open_source['successful_sources'] else 'none recorded'}",
        f"- Failed sources: {', '.join(open_source['failed_sources']) if open_source['failed_sources'] else 'none'}",
        (
            f"- Freshness: {freshness['status']}; newest record "
            f"{freshness['newest_record_observed_at']}; newest age "
            f"{freshness['newest_record_age_days'] if freshness['newest_record_age_days'] is not None else 'unknown'} days"
        ),
        (
            f"- Source health: {source_health['status']}; "
            f"{source_health['successful_source_count']} successful / "
            f"{source_health['failed_source_count']} failed"
        ),
        f"- Snapshot hashes: {_inline_json(open_source['hashes'])}",
        f"- Basis: {open_source['basis_statement']}",
        *duplicate_source_lines,
        "",
        "## Source Freshness And Failures",
        "",
        f"- Snapshot generated: {freshness['snapshot_generated_at']}",
        f"- Oldest source record: {freshness['oldest_record_observed_at']}",
        f"- Newest source record: {freshness['newest_record_observed_at']}",
        (
            f"- Newest record age: "
            f"{freshness['newest_record_age_days'] if freshness['newest_record_age_days'] is not None else 'unknown'} days"
        ),
        (
            f"- Record span: "
            f"{freshness['record_span_days'] if freshness['record_span_days'] is not None else 'unknown'} days"
        ),
        f"- Freshness window: {freshness['freshness_window_days']} days",
        f"- Health status: {source_health['status']}",
        f"- Failure policy: {source_health['failure_policy']}",
        (
            "- Source failures: "
            + (
                "; ".join(
                    f"{item['source_id']} ({item['status']}): {item['error']}"
                    for item in open_source["source_failures"]
                )
                if open_source["source_failures"]
                else "none"
            )
        ),
        "",
        "## Exploit-Class Portfolio",
        "",
        f"- Top hypothesized zero-day class: {prediction['top_zero_day_class']}",
        f"- Top one-day replay class: {prediction['top_one_day_class']}",
        f"- Portfolio size: {prediction['zero_day_count']} zero-day classes and {prediction['one_day_count']} one-day classes",
        "",
        "## Defense Artifact",
        "",
        f"- Patch summary: {defense['patch_summary']}",
        f"- Patch format: {defense['patch_format']}",
        f"- Sigma: {defense['sigma']['title']} (`{defense['sigma']['rule_id']}`), level `{defense['sigma']['level']}`",
        f"- Log sources: {', '.join(defense['sigma']['logsources'])}",
        "",
        "## Validation",
        "",
        f"- Pre-patch status: `{validation['pre_patch_status']}`",
        f"- Post-patch status: `{validation['post_patch_status']}`",
        f"- Scope: {validation['sandbox_scope']}",
        f"- Tool: {validation['validation_tool']}",
        f"- Wall time: {validation['wall_time_seconds']} seconds",
        f"- Result: `{failure_evidence['result']}`",
        f"- Failure detected: `{str(failure_evidence['failure_detected']).lower()}`",
        f"- Failure kind: `{failure_evidence['failure_kind']}`",
        f"- Timeout observed: `{str(failure_evidence['timeout_observed']).lower()}`",
        f"- Timeout seconds: {failure_evidence['timeout_seconds'] if failure_evidence['timeout_seconds'] is not None else 'not recorded'}",
        f"- Failure summary: {failure_evidence['summary']}",
        f"- Operator action: {failure_evidence['operator_action']}",
        f"- Pre excerpt: {validation['sanitized_excerpts']['pre_patch']}",
        f"- Post excerpt: {validation['sanitized_excerpts']['post_patch']}",
        "",
    ]

    if isinstance(sandbox_provenance, dict):
        lines.extend(
            [
                "## Sandbox Provenance",
                "",
                f"- Manifest: `{sandbox_provenance['manifest_id']}`",
                f"- Profile: `{sandbox_provenance['profile']}`",
                f"- Mode: `{sandbox_provenance['mode']}`",
                f"- Artifact ID: `{sandbox_provenance['artifact_id']}`",
                f"- Artifact content SHA-256: `{sandbox_provenance['artifact_content_sha256']}`",
                f"- Manifest SHA-256: `{sandbox_provenance['manifest_sha256']}`",
                f"- Sanitized logs SHA-256: `{sandbox_provenance['sanitized_logs_sha256']}`",
                f"- Raw logs retained: `{str(sandbox_provenance['raw_logs_retained']).lower()}`",
                f"- No network egress: `{str(sandbox_provenance['no_network_egress']).lower()}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Operator Approval",
            "",
            f"- Decision: `{approval['decision']}`",
            f"- Operator label: `{approval['operator_label']}`",
            f"- Approval mode: `{approval['approval_mode']}`",
            f"- Timestamp: {approval['timestamp']}",
            f"- Approval record hash: `{approval.get('approval_record_hash', 'not supplied')}`",
            "",
            "## Safety Attestation",
            "",
            f"- No live targets: `{str(safety['no_live_targets']).lower()}`",
            f"- No live target data included: `{str(safety['no_live_target_data_included']).lower()}`",
            f"- Data boundary: {safety['data_boundary_statement']}",
            f"- No payloads: `{str(safety['no_payloads']).lower()}`",
            f"- No credentials: `{str(safety['no_credentials']).lower()}`",
            f"- Fixture backed: `{str(safety['fixture_backed']).lower()}`",
            f"- Validation scope: {safety['validation_scope']}",
            "",
            "## Redaction Report",
            "",
            f"- Summary fields only: `{str(redaction['summary_fields_only']).lower()}`",
            f"- Source documents embedded: `{str(redaction['source_documents_embedded']).lower()}`",
            f"- Raw forecast embedded: `{str(redaction['raw_forecast_embedded']).lower()}`",
            f"- Raw prediction portfolio embedded: `{str(redaction['raw_prediction_portfolio_embedded']).lower()}`",
            f"- Raw defense artifact embedded: `{str(redaction['raw_defense_artifact_embedded']).lower()}`",
            f"- Raw validation logs embedded: `{str(redaction['raw_validation_logs_embedded']).lower()}`",
            f"- Raw OSINT records embedded: `{str(redaction['raw_osint_records_embedded']).lower()}`",
            f"- Raw asset inventory embedded: `{str(redaction['raw_asset_inventory_embedded']).lower()}`",
            f"- Source references emitted: {redaction['source_refs_emitted']}",
            f"- Sanitized validation excerpts emitted: {redaction['sanitized_validation_excerpts_emitted']}",
            f"- Field allowlist: {', '.join(redaction['field_allowlist'])}",
            f"- Redacted fields: {', '.join(redaction['redacted_fields'])}",
            f"- Blocked text classes: {', '.join(redaction['blocked_text_classes'])}",
            f"- Operator review required: `{str(redaction['operator_review_required']).lower()}`",
            "",
        ]
    )

    if policy:
        lines.extend(
            [
                "## Policy Controls",
                "",
                f"- Policy ID: `{policy['policy_id']}`",
                f"- Policy SHA-256: `{policy['policy_sha256']}`",
                f"- Allowed validation modes: {', '.join(policy['allowed_modes'].get('validation', []))}",
                f"- Allowed OSINT modes: {', '.join(policy['allowed_modes'].get('osint_collection', []))}",
                f"- Live targets allowed: `{str(policy['controls'].get('live_targets_allowed')).lower()}`",
                f"- Live VM scraper allowed: `{str(policy['controls'].get('live_vm_scraper_allowed')).lower()}`",
                f"- Runtime retention: `{policy['retention'].get('runtime_outputs_max_days')}` days",
                f"- Audit retention: `{policy['retention'].get('audit_log_max_days')}` days",
                "",
            ]
        )

    if asset_context:
        lines.extend(
            [
                "## Asset Context",
                "",
                f"- Inventory: `{asset_context['inventory_id']}`",
                f"- Matched exposure class: {asset_context['matched_exposure_class']}",
                f"- Affected asset count: {asset_context['affected_asset_count']}",
                f"- Criticality summary: {_inline_json(asset_context['criticality_summary'])}",
                f"- Package/CVE overlap: {_inline_json(asset_context['package_cve_overlap_summary'])}",
                f"- Owner queue: {', '.join(asset_context['recommended_owner_queue'])}",
                f"- Context: {asset_context['context_statement']}",
                "",
            ]
        )

    if asset_seed_summary:
        lines.extend(
            [
                "## Asset/SBOM Seeds",
                "",
                f"- Seedset: `{asset_seed_summary['seedset_id']}`",
                f"- Fixture context: `{str(asset_seed_summary['fixture_context']).lower()}`",
                f"- Asset count: {asset_seed_summary['asset_count']}",
                f"- Exposure classes: {', '.join(asset_seed_summary['exposure_classes'])}",
                f"- Product families: {', '.join(asset_seed_summary['product_families'])}",
                f"- Package seeds: {asset_seed_summary['package_seed_count']}",
                f"- CVE seeds: {asset_seed_summary['cve_seed_count']}",
                f"- Recommended open-source sources: {', '.join(asset_seed_summary['recommended_source_ids'])}",
                f"- Owner queues: {', '.join(asset_seed_summary['owner_queues'])}",
                f"- Basis: {asset_seed_summary['basis_statement']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Source References",
            "",
        ]
    )
    for ref in bundle["source_refs"]:
        lines.append(f"- `{ref['id']}`: {ref['label']} - {ref['supports']} ({ref['url']})")
    lines.extend(
        [
            "",
            "## Hashes",
            "",
            f"- Forecast SHA-256: `{hashes['forecast_sha256']}`",
            f"- Portfolio SHA-256: `{hashes['portfolio_sha256']}`",
            f"- Artifact SHA-256: `{hashes['artifact_sha256']}`",
        ]
    )
    if "asset_inventory_sha256" in hashes:
        lines.append(f"- Asset inventory SHA-256: `{hashes['asset_inventory_sha256']}`")
    if "asset_seedset_sha256" in hashes:
        lines.append(f"- Asset seedset SHA-256: `{hashes['asset_seedset_sha256']}`")
    if "policy_sha256" in hashes:
        lines.append(f"- Policy SHA-256: `{hashes['policy_sha256']}`")
    if "sandbox_run_manifest_sha256" in hashes:
        lines.append(f"- Sandbox run manifest SHA-256: `{hashes['sandbox_run_manifest_sha256']}`")
    lines.extend(
        [
            f"- Bundle SHA-256: `{bundle['bundle_sha256']}`",
            "",
        ]
    )

    markdown = "\n".join(lines)
    _scan_text_safety(markdown, "markdown")
    return markdown


def write_bundle(
    bundle: dict[str, Any],
    *,
    out_json: str | Path | None = None,
    out_md: str | Path | None = None,
) -> None:
    if out_json:
        json_path = Path(out_json)
        _assert_evidence_runtime_output_path(json_path, label="evidence JSON", suffix=".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(_pretty_json(bundle) + "\n", encoding="utf-8")
    if out_md:
        md_path = Path(out_md)
        _assert_evidence_runtime_output_path(md_path, label="evidence Markdown", suffix=".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(bundle), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        forecast = load_json(args.forecast)
        portfolio = load_json(args.portfolio)
        artifact = load_json(args.artifact)
        asset_inventory = load_json(args.asset_inventory) if args.asset_inventory else None
        asset_seedset = load_json(args.asset_seedset) if args.asset_seedset else None
        policy = load_policy(args.policy) if args.policy else None
        approval_record = load_json(args.approval_record) if args.approval_record else None
        sandbox_run_manifest = (
            load_json(args.sandbox_run_manifest) if args.sandbox_run_manifest else None
        )
        bundle = build_evidence_bundle(
            forecast=forecast,
            portfolio=portfolio,
            artifact=artifact,
            asset_inventory=asset_inventory,
            asset_seedset=asset_seedset,
            policy=policy,
            approval_record=approval_record,
            sandbox_run_manifest=sandbox_run_manifest,
            operator_label=args.operator_label,
            approval_decision=args.approval_decision,
            generated_at=args.generated_at,
            run_id=args.run_id,
        )
        write_bundle(bundle, out_json=args.out_json, out_md=args.out_md)
        if not args.out_json:
            print(_pretty_json(bundle))
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"evidence.bundle: {_sanitize_error(str(exc))}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m evidence.bundle",
        description="Generate a Prophet JSON and Markdown evidence bundle.",
    )
    parser.add_argument("--forecast", required=True, help="Direction B forecast JSON")
    parser.add_argument("--portfolio", required=True, help="Prediction portfolio JSON")
    parser.add_argument("--artifact", required=True, help="Direction C artifact JSON")
    parser.add_argument("--asset-inventory", help="Optional asset inventory fixture JSON")
    parser.add_argument("--asset-seedset", help="Optional asset/SBOM OSINT seedset JSON")
    parser.add_argument("--policy", help="Optional prophet_pilot_policy.v0.1 JSON")
    parser.add_argument("--approval-record", help="Optional local operator audit event JSON")
    parser.add_argument(
        "--sandbox-run-manifest",
        help="Optional prophet.sandbox_run_manifest.v0.1 JSON for provenance summary",
    )
    parser.add_argument("--operator-label", required=True, help="Operator label for audit")
    parser.add_argument("--approval-decision", required=True, help="Operator approval decision")
    parser.add_argument("--generated-at", help="Override generated_at for deterministic output")
    parser.add_argument("--run-id", help="Explicit evidence run id")
    parser.add_argument("--out-json", help="Output evidence JSON path")
    parser.add_argument("--out-md", help="Output evidence Markdown path")
    return parser


def _collect_source_refs(
    forecast: dict[str, Any],
    portfolio: dict[str, Any],
    artifact: dict[str, Any],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(ref: Any, fallback: str) -> None:
        if not isinstance(ref, dict):
            return
        source = _normalize_source_ref(ref, fallback)
        if source["id"] in seen:
            return
        seen.add(source["id"])
        out.append(source)

    for idx, ref in enumerate(forecast.get("source_refs") or [], start=1):
        add(ref, f"forecast_source_{idx}")
    for section in ("zero_day_predictions", "one_day_predictions"):
        for prediction in portfolio.get(section) or []:
            if not isinstance(prediction, dict):
                continue
            pred_id = _string(prediction.get("prediction_id"), section)
            for idx, ref in enumerate(prediction.get("source_refs") or [], start=1):
                add(ref, f"{pred_id}_source_{idx}")
    for idx, ref in enumerate(artifact.get("source_refs") or [], start=1):
        add(ref, f"artifact_source_{idx}")
    return out


def _normalize_source_ref(ref: dict[str, Any], fallback: str) -> dict[str, str]:
    source = {
        "id": _string(ref.get("id"), fallback),
        "label": _sanitize_text(_string(ref.get("label"), fallback)),
        "url": _sanitize_text(_string(ref.get("url"), "unknown")),
        "supports": _sanitize_text(_string(ref.get("supports"), "supporting source")),
    }
    date = _string(ref.get("date"), "")
    if date:
        source["date"] = date
    return source


def _source_ids_for(*values: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for value in values:
        for ref_id in value.get("source_ref_ids") or []:
            if isinstance(ref_id, str) and ref_id not in ids:
                ids.append(ref_id)
    return ids


def _build_open_source_summary(forecast: dict[str, Any]) -> dict[str, Any]:
    signals = forecast.get("open_source_signals")
    if not isinstance(signals, dict):
        return {
            "integrated": False,
            "record_count": 0,
            "event_count": 0,
            "source_type_counts": {},
            "collection_tier_counts": {},
            "successful_sources": [],
            "failed_sources": [],
            "freshness": _open_source_freshness_summary(None),
            "source_health": _open_source_health_summary(None),
            "source_failures": [],
            "snapshot_paths": [],
            "manifest_paths": [],
            "hashes": {},
            "source_ref_ids": [],
            "basis_statement": "No OSINT snapshot was provided for this forecast run.",
        }

    successful_sources, successful_duplicates = _string_list_with_duplicates(
        signals.get("successful_sources")
    )
    failed_sources, failed_duplicates = _string_list_with_duplicates(
        signals.get("failed_sources")
    )
    source_ref_ids, source_ref_duplicates = _string_list_with_duplicates(
        signals.get("source_ref_ids")
    )
    snapshot_paths, snapshot_duplicates = _string_list_with_duplicates(
        signals.get("snapshot_paths")
    )
    manifest_paths, manifest_duplicates = _string_list_with_duplicates(
        signals.get("manifest_paths")
    )
    source_failures, failure_duplicates = _open_source_failure_summaries_with_duplicates(
        signals.get("source_failures")
    )
    summary = {
        "integrated": bool(signals.get("integrated")),
        "record_count": _int_value(signals.get("record_count")),
        "event_count": _int_value(signals.get("event_count")),
        "source_type_counts": _string_int_dict(signals.get("source_type_counts")),
        "collection_tier_counts": _string_int_dict(signals.get("collection_tier_counts")),
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "freshness": _open_source_freshness_summary(signals.get("freshness")),
        "source_health": _open_source_health_summary(signals.get("source_health")),
        "source_failures": source_failures,
        "snapshot_paths": snapshot_paths,
        "manifest_paths": manifest_paths,
        "hashes": _sanitize_hash_map(signals.get("hashes")),
        "source_ref_ids": source_ref_ids,
        "basis_statement": _sanitize_text(
            _string(
                signals.get("basis_statement"),
                "Sanitized open-source metadata basis was not supplied.",
            )
        ),
    }
    duplicate_summary = _duplicate_source_summary(
        source_duplicates=[
            successful_duplicates,
            failed_duplicates,
            source_ref_duplicates,
            failure_duplicates,
        ],
        path_duplicates=[snapshot_duplicates, manifest_duplicates],
    )
    if duplicate_summary:
        summary["duplicate_source_summary"] = duplicate_summary
    return summary


def _policy_summary(policy: dict[str, Any]) -> dict[str, Any]:
    validate_pilot_policy(policy)
    allowed_modes = {
        key: _string_list(value)
        for key, value in _object(policy.get("allowed_modes")).items()
        if isinstance(value, list)
    }
    controls = {
        key: bool(value)
        for key, value in _object(policy.get("controls")).items()
        if isinstance(value, bool)
    }
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_id": _sanitize_text(_string(policy.get("policy_id"), "unknown-policy")),
        "policy_sha256": _sha256_normalized(policy),
        "enforced": True,
        "allowed_modes": dict(sorted(allowed_modes.items())),
        "controls": dict(sorted(controls.items())),
        "retention": dict(sorted(_object(policy.get("retention")).items())),
    }


def _validate_policy_retention(retention: Any) -> None:
    if not isinstance(retention, dict):
        raise EvidenceBundleError("policy.retention must be object")
    unexpected = sorted(
        set(retention)
        - set(POLICY_RETENTION_LIMITS)
        - {"raw_collection_retained", "deletion_review_required"}
    )
    if unexpected:
        raise EvidenceBundleError(f"policy.retention has unknown fields: {unexpected}")
    for field, max_days in POLICY_RETENTION_LIMITS.items():
        value = retention.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not (1 <= value <= max_days):
            raise EvidenceBundleError(
                f"policy.retention.{field} must be integer days between 1 and {max_days}"
            )
    if retention.get("raw_collection_retained") is not False:
        raise EvidenceBundleError("policy.retention.raw_collection_retained must be false")
    if retention.get("deletion_review_required") is not True:
        raise EvidenceBundleError("policy.retention.deletion_review_required must be true")


def _approval_record_summary(
    approval_record: dict[str, Any],
    *,
    operator_label: str,
    approval_decision: str,
    policy_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(approval_record, dict):
        raise EvidenceBundleError("approval_record must be object")
    if approval_record.get("schema_version") != "prophet_operator_audit_event.v0.1":
        raise EvidenceBundleError("approval_record schema_version is unsupported")
    if approval_record.get("event_type") != "operator_approval":
        raise EvidenceBundleError("approval_record event_type must be operator_approval")
    if _string(approval_record.get("decision"), "") != approval_decision:
        raise EvidenceBundleError("approval_record decision must match approval decision")
    operator = _object(approval_record.get("operator"))
    if _string(operator.get("label"), "") != operator_label:
        raise EvidenceBundleError("approval_record operator label must match evidence operator")
    if policy_summary is not None:
        policy = _object(approval_record.get("policy"))
        if _string(policy.get("policy_id"), "") != policy_summary["policy_id"]:
            raise EvidenceBundleError("approval_record policy_id must match evidence policy")
        if _string(policy.get("policy_sha256"), "") != policy_summary["policy_sha256"]:
            raise EvidenceBundleError("approval_record policy_sha256 must match evidence policy")
    event_hash = _string(approval_record.get("event_hash"), "")
    if not _is_sha256(event_hash):
        raise EvidenceBundleError("approval_record.event_hash must be SHA-256")
    expected = _audit_event_body_sha256(approval_record)
    if event_hash != expected:
        raise EvidenceBundleError("approval_record.event_hash does not match body")
    chain = _object(approval_record.get("chain"))
    if chain.get("event_body_sha256") != expected:
        raise EvidenceBundleError("approval_record chain event hash does not match body")
    previous = chain.get("previous_event_hash")
    if previous is not None and not _is_sha256(_string(previous, "")):
        raise EvidenceBundleError("approval_record previous_event_hash must be SHA-256 or null")
    return {
        "approval_event_id": _sanitize_text(_string(approval_record.get("event_id"), "")),
        "approval_record_hash": event_hash,
        "approval_chain": {
            "log_schema_version": _sanitize_text(
                _string(chain.get("log_schema_version"), "prophet_operator_audit_log.v0.1")
            ),
            "previous_event_hash": previous,
            "event_body_sha256": expected,
        },
    }


def _enforce_pilot_policy(
    policy: dict[str, Any],
    *,
    forecast: dict[str, Any],
    artifact: dict[str, Any],
) -> None:
    validate_pilot_policy(policy)
    allowed_modes = _object(policy.get("allowed_modes"))
    controls = _object(policy.get("controls"))
    for control in POLICY_BLOCKED_CONTROLS:
        if controls.get(control) is not False:
            raise EvidenceBundleError(f"policy blocks evidence because {control} is not false")

    validation = _object(artifact.get("validation"))
    scope = _string(validation.get("scope"), "")
    operator_notes = _object(artifact.get("operator_notes"))
    decision = _string(operator_notes.get("human_gate_decision"), "")
    validation_mode = _artifact_validation_mode(artifact, scope=scope, decision=decision)
    if validation_mode is None:
        raise EvidenceBundleError(
            "policy allows only fixture or localhost sandbox validation for pilot evidence"
        )
    if not _policy_allows(allowed_modes, "validation", validation_mode):
        raise EvidenceBundleError(f"policy does not allow validation mode: {validation_mode}")
    if not _policy_allows(allowed_modes, "evidence_generation", validation_mode):
        raise EvidenceBundleError(
            f"policy does not allow evidence generation mode: {validation_mode}"
        )

    open_source = _object(forecast.get("open_source_signals"))
    asset_seed_context = _object(forecast.get("asset_seed_context"))
    osint_mode = "fixture"
    if open_source.get("integrated") is True:
        osint_mode = (
            "seeded_osint" if asset_seed_context.get("integrated") is True else "fixture"
        )
    if not _policy_allows(allowed_modes, "osint_collection", osint_mode):
        raise EvidenceBundleError(f"policy does not allow OSINT mode: {osint_mode}")
    if not _policy_allows(allowed_modes, "forecast_generation", osint_mode):
        raise EvidenceBundleError(f"policy does not allow forecast mode: {osint_mode}")


def _artifact_validation_mode(
    artifact: dict[str, Any],
    *,
    scope: str,
    decision: str,
) -> str | None:
    audit = _object(artifact.get("audit"))
    validation = _object(artifact.get("validation"))
    emitted_by = _string(audit.get("emitted_by"), "")
    validation_tool = _string(validation.get("validation_tool"), "")
    scope_lower = scope.lower()
    if (
        emitted_by.startswith("sandbox_runner.")
        or validation_tool == "prophet deterministic sandbox runner"
    ) and "localhost" in scope_lower:
        return "localhost_sandbox"
    if (decision == "bypassed_for_fixture" or emitted_by == "fixture") and (
        "localhost" in scope_lower or "fixture" in scope_lower or "sandbox" in scope_lower
    ):
        return "fixture"
    if "localhost" in scope_lower:
        return "localhost_sandbox"
    return None


def _policy_allows(
    allowed_modes: dict[str, Any],
    category: str,
    mode: str,
) -> bool:
    modes = allowed_modes.get(category)
    return isinstance(modes, list) and mode in modes


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    return 0


def _string_int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, count in value.items():
        label = _sanitize_text(str(key).strip())
        if label:
            out[label] = _int_value(count)
    return dict(sorted(out.items()))


def _open_source_freshness_summary(value: Any) -> dict[str, Any]:
    freshness = _object(value)
    return {
        "status": _sanitize_text(_string(freshness.get("status"), "not_provided")),
        "snapshot_generated_at": _sanitize_text(
            _string(freshness.get("snapshot_generated_at"), "not supplied")
        ),
        "oldest_record_observed_at": _sanitize_text(
            _string(freshness.get("oldest_record_observed_at"), "not supplied")
        ),
        "newest_record_observed_at": _sanitize_text(
            _string(freshness.get("newest_record_observed_at"), "not supplied")
        ),
        "newest_record_age_days": _number_or_none(freshness.get("newest_record_age_days")),
        "record_span_days": _number_or_none(freshness.get("record_span_days")),
        "freshness_window_days": _int_value(freshness.get("freshness_window_days")) or 7,
    }


def _open_source_health_summary(value: Any) -> dict[str, Any]:
    health = _object(value)
    return {
        "status": _sanitize_text(_string(health.get("status"), "not_provided")),
        "manifest_count": _int_value(health.get("manifest_count")),
        "successful_source_count": _int_value(health.get("successful_source_count")),
        "failed_source_count": _int_value(health.get("failed_source_count")),
        "failure_policy": _sanitize_text(
            _string(
                health.get("failure_policy"),
                "Failed sources are summarized in evidence; raw collection text remains excluded.",
            )
        ),
    }


def _open_source_failure_summaries(value: Any) -> list[dict[str, Any]]:
    failures, _duplicates = _open_source_failure_summaries_with_duplicates(value)
    return failures


def _open_source_failure_summaries_with_duplicates(
    value: Any,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if not isinstance(value, list):
        return [], {}
    failures_by_source: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    source_counts: dict[str, int] = {}
    for item in value:
        source = _object(item)
        if not source:
            continue
        failure = {
            "source_id": _sanitize_text(_string(source.get("source_id"), "unknown_source")),
            "status": _sanitize_text(_string(source.get("status"), "unknown")),
            "collector": _sanitize_text(_string(source.get("collector"), "unknown")),
            "source_type": _sanitize_text(_string(source.get("source_type"), "unknown")),
            "collection_tier": _sanitize_text(
                _string(source.get("collection_tier"), "unknown")
            ),
            "records": _int_value(source.get("records")),
            "error": _sanitize_text(_string(source.get("error"), "not supplied")),
        }
        source_id = failure["source_id"]
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
        if source_id not in failures_by_source:
            failures_by_source[source_id] = failure
            order.append(source_id)
            continue
        existing = failures_by_source[source_id]
        existing["records"] = max(existing["records"], failure["records"])
    failures = [failures_by_source[source_id] for source_id in order]
    duplicates = {
        source_id: count for source_id, count in sorted(source_counts.items()) if count > 1
    }
    return failures, duplicates


def _duplicate_source_summary(
    *,
    source_duplicates: list[dict[str, int]],
    path_duplicates: list[dict[str, int]],
) -> dict[str, Any] | None:
    duplicate_source_ids = sorted(
        {source_id for duplicates in source_duplicates for source_id in duplicates}
    )
    duplicate_source_count = sum(
        count - 1 for duplicates in source_duplicates for count in duplicates.values()
    )
    duplicate_path_count = sum(
        count - 1 for duplicates in path_duplicates for count in duplicates.values()
    )
    collapsed_count = duplicate_source_count + duplicate_path_count
    if collapsed_count == 0:
        return None
    return {
        "collapsed_duplicate_count": collapsed_count,
        "duplicate_source_ids": duplicate_source_ids,
        "duplicate_path_count": duplicate_path_count,
        "dedupe_policy": (
            "Duplicate source IDs and repeated snapshot or manifest paths are "
            "collapsed in evidence summaries; raw source documents remain excluded."
        ),
    }


def _number_or_none(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value if value >= 0 else None
    return None


def _string_list(value: Any) -> list[str]:
    strings, _duplicates = _string_list_with_duplicates(value)
    return strings


def _string_list_with_duplicates(value: Any) -> tuple[list[str], dict[str, int]]:
    if not isinstance(value, list):
        return [], {}
    out: list[str] = []
    counts: dict[str, int] = {}
    for item in value:
        if not isinstance(item, str):
            continue
        clean = _sanitize_text(item.strip())
        if not clean:
            continue
        counts[clean] = counts.get(clean, 0) + 1
        if clean not in out:
            out.append(clean)
    duplicates = {item: count for item, count in sorted(counts.items()) if count > 1}
    return out, duplicates


def _sanitize_hash_map(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, Any] = {}
    for key, inner in value.items():
        clean_key = _sanitize_text(str(key).strip())
        if not clean_key:
            continue
        if isinstance(inner, dict):
            out[clean_key] = _sanitize_hash_map(inner)
        elif isinstance(inner, str):
            out[clean_key] = _sanitize_text(inner.strip())
    return dict(sorted(out.items()))


def _scan_for_banned_keys(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if lowered in BANNED_KEYS:
                raise EvidenceBundleError(f"{path} contains banned key: {key}")
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
        for marker in RAW_SOURCE_TEXT_MARKERS:
            if marker in lowered:
                raise EvidenceBundleError(f"{path} contains raw source marker: {marker!r}")
        for phrase in PROCEDURAL_PHRASES:
            if phrase in lowered:
                raise EvidenceBundleError(f"{path} contains procedural phrase: {phrase!r}")
        for token in PAYLOAD_TOKENS:
            if token in lowered:
                raise EvidenceBundleError(f"{path} contains payload-like token: {token!r}")


def _scan_asset_text_safety(value: Any, path: str) -> None:
    _scan_text_safety(value, path)
    if isinstance(value, dict):
        for key, inner in value.items():
            _scan_asset_text_safety(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_asset_text_safety(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        if _looks_like_ip(value):
            raise EvidenceBundleError(f"{path} contains IP-like text")
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
            raise EvidenceBundleError(f"{path} contains email-like text")
        if re.search(r"\b(?:password|secret|token|private key)\b", value, flags=re.I):
            raise EvidenceBundleError(f"{path} contains credential-like text")


def _assert_evidence_runtime_output_path(path: Path, *, label: str, suffix: str) -> None:
    if path.suffix.lower() != suffix:
        raise EvidenceBundleError(f"{label} output path must end with {suffix}")
    try:
        rel_path = path.expanduser().resolve(strict=False).relative_to(REPO_ROOT)
    except ValueError as exc:
        raise EvidenceBundleError(
            f"{label} output path must stay under {EVIDENCE_RUNTIME_OUTPUT_PREFIX}"
        ) from exc
    normalized = rel_path.as_posix()
    if not normalized.startswith(EVIDENCE_RUNTIME_OUTPUT_PREFIX):
        raise EvidenceBundleError(
            f"{label} output path must stay under {EVIDENCE_RUNTIME_OUTPUT_PREFIX}"
        )
    if "/../" in f"/{normalized}/" or normalized.endswith("/.."):
        raise EvidenceBundleError(f"{label} output path must not contain parent traversal")


def _sanitize_text(value: str) -> str:
    replacements: tuple[tuple[str | re.Pattern[str], str], ...] = (
        (re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"), "[INTERNAL-IP]"),
        (re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"), "[IP-REDACTED]"),
        (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL-REDACTED]"),
        (re.compile(r"ldap://[^\s)]+", re.I), "[REDACTED-ENDPOINT]"),
        (re.compile(r"rmi://[^\s)]+", re.I), "[REDACTED-ENDPOINT]"),
        (re.compile(r"runtime\.getruntime\(\)\.exec\([^)]*\)", re.I), "[REDACTED-EXEC]"),
    )
    out = value
    for pattern, replacement in replacements:
        out = pattern.sub(replacement, out) if hasattr(pattern, "sub") else out.replace(pattern, replacement)
    return out


def _sanitize_error(value: str) -> str:
    return _sanitize_text(value).replace("\n", " ").strip()[:800]


def _looks_like_ip(value: str) -> bool:
    return bool(re.search(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b", value))


def _is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _bundle_body_sha256(bundle: dict[str, Any]) -> str:
    body = copy.deepcopy(bundle)
    body.pop("bundle_sha256", None)
    if isinstance(body.get("hashes"), dict):
        body["hashes"].pop("bundle_body_sha256", None)
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _audit_event_body_sha256(event: dict[str, Any]) -> str:
    body = copy.deepcopy(event)
    body.pop("event_hash", None)
    if isinstance(body.get("chain"), dict):
        body["chain"]["event_body_sha256"] = ""
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _sha256_normalized(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


def _inline_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _markdown_cell(value: Any) -> str:
    return _sanitize_text(str(value)).replace("|", "\\|").replace("\n", " ").strip()


def _ensure_generated_at(value: str | None) -> str:
    if value:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceBundleError("generated_at must be ISO 8601") from exc
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _first_ranked(value: Any) -> dict[str, Any]:
    if not isinstance(value, list):
        return {}
    ranked = [item for item in value if isinstance(item, dict)]
    if not ranked:
        return {}
    return sorted(ranked, key=lambda item: item.get("rank", 999))[0]


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


if __name__ == "__main__":
    raise SystemExit(main())
