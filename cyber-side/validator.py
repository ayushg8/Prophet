"""Validator for the Prophet Exploit Engine output artifact (Direction C).

This module mirrors the validation style used in
``world-side/forecaster/models.py``: stdlib only, raises ``ValidationError``
with a concrete reason when an artifact drifts from the contract.

The schema is defined in ``cyber-side/INTERFACE.md``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


SCHEMA_VERSION = "exploit_engine_artifact.v0.1"

CONFIDENCE_LABELS = {"high", "medium", "low"}
PATCH_FORMATS = {"unified_diff", "config_snippet", "jvm_flag_set"}
PRE_STATUSES = {"vulnerable", "not_vulnerable", "error"}
POST_STATUSES = {"vulnerable", "not_vulnerable", "blocked", "error"}
SIGMA_LEVELS = {"low", "medium", "high", "critical"}
GATE_DECISIONS = {"approved", "denied", "bypassed_for_fixture"}

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

# Phrases that should never appear in non-actionable narrative fields.
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
    """Raised when a Direction C artifact does not match the contract."""


def validate_exploit_engine_artifact(value: dict[str, Any] | str) -> None:
    """Validate a Direction C artifact. Raises ValidationError on drift."""
    artifact = _coerce_object(value, "artifact")
    _check_no_banned_keys(artifact, "artifact")

    _required_str(artifact, "artifact_id")
    generated_at = _required_str(artifact, "generated_at")
    _validate_iso_datetime(generated_at, "generated_at")
    schema_version = _required_str(artifact, "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ValidationError(
            f"schema_version must be {SCHEMA_VERSION}, got {schema_version}"
        )

    _validate_input_refs(_required_object(artifact, "input_refs"))
    _validate_predicted_exploit(_required_object(artifact, "predicted_exploit"))
    _validate_defense(_required_object(artifact, "defense"))
    _validate_validation_block(_required_object(artifact, "validation"))
    _validate_operator_notes(_required_object(artifact, "operator_notes"))
    _validate_audit(_required_object(artifact, "audit"))
    _validate_source_refs(_required_list(artifact, "source_refs"))


# ── section validators ────────────────────────────────────────────────────────


def _validate_input_refs(refs: dict[str, Any]) -> None:
    _required_str(refs, "candidate_id")
    _required_str(refs, "forecast_id")
    _required_str(refs, "vector_id")


def _validate_predicted_exploit(value: dict[str, Any]) -> None:
    _check_no_banned_keys(value, "predicted_exploit")
    label = _required_str(value, "exploit_class_label")
    _check_non_actionable(label, "predicted_exploit.exploit_class_label")
    _required_string_list(value, "cwe_ids", allow_empty=True)
    cve_id = value.get("cve_id")
    if cve_id is not None and not (isinstance(cve_id, str) and cve_id.strip()):
        raise ValidationError("predicted_exploit.cve_id must be string or null")
    if not isinstance(value.get("kev_listed"), bool):
        raise ValidationError("predicted_exploit.kev_listed must be boolean")
    epss = value.get("epss_score")
    if epss is not None and not _is_unit_float(epss):
        raise ValidationError("predicted_exploit.epss_score must be 0.0–1.0 or null")
    technique = value.get("attack_technique")
    if technique is not None and not (isinstance(technique, str) and technique.strip()):
        raise ValidationError("predicted_exploit.attack_technique must be string or null")
    rationale = _required_str(value, "non_actionable_rationale")
    _check_non_actionable(rationale, "predicted_exploit.non_actionable_rationale")
    confidence = _required_str(value, "confidence")
    if confidence not in CONFIDENCE_LABELS:
        raise ValidationError(f"predicted_exploit.confidence must be one of {CONFIDENCE_LABELS}")
    score = value.get("confidence_score")
    if not _is_unit_float(score):
        raise ValidationError("predicted_exploit.confidence_score must be 0.0–1.0")


def _validate_defense(value: dict[str, Any]) -> None:
    _check_no_banned_keys(value, "defense")
    patch = _required_object(value, "patch")
    _check_no_banned_keys(patch, "defense.patch")
    _required_str(patch, "summary")
    patch_format = _required_str(patch, "patch_format")
    if patch_format not in PATCH_FORMATS:
        raise ValidationError(f"defense.patch.patch_format must be one of {PATCH_FORMATS}")
    diff = _required_str(patch, "diff")
    _check_diff_is_defensive(diff)
    _required_str(patch, "applies_to")
    _required_str(patch, "rollback_note")

    sigma = _required_object(value, "sigma_rule")
    _check_no_banned_keys(sigma, "defense.sigma_rule")
    rule_id = _required_str(sigma, "rule_id")
    _required_str(sigma, "title")
    yaml_text = _required_str(sigma, "yaml")
    _check_sigma_yaml(yaml_text, rule_id)
    level = _required_str(sigma, "level")
    if level not in SIGMA_LEVELS:
        raise ValidationError(f"defense.sigma_rule.level must be one of {SIGMA_LEVELS}")
    _required_string_list(sigma, "logsources")


def _validate_validation_block(value: dict[str, Any]) -> None:
    _check_no_banned_keys(value, "validation")
    _required_str(value, "sandbox_id")
    scope = _required_str(value, "scope")
    if "localhost" not in scope.lower():
        raise ValidationError("validation.scope must declare a localhost-only scope")
    pre = _required_str(value, "pre_patch_status")
    if pre not in PRE_STATUSES:
        raise ValidationError(f"validation.pre_patch_status must be one of {PRE_STATUSES}")
    _required_str(value, "pre_patch_excerpt")
    post = _required_str(value, "post_patch_status")
    if post not in POST_STATUSES:
        raise ValidationError(f"validation.post_patch_status must be one of {POST_STATUSES}")
    _required_str(value, "post_patch_excerpt")
    _required_str(value, "validation_tool")
    template = value.get("validation_template")
    if template is not None and not (isinstance(template, str) and template.strip()):
        raise ValidationError("validation.validation_template must be string or null")
    wall = value.get("wall_time_seconds")
    if not isinstance(wall, (int, float)) or isinstance(wall, bool) or wall < 0:
        raise ValidationError("validation.wall_time_seconds must be a non-negative number")


def _validate_operator_notes(value: dict[str, Any]) -> None:
    _check_no_banned_keys(value, "operator_notes")
    decision = _required_str(value, "human_gate_decision")
    if decision not in GATE_DECISIONS:
        raise ValidationError(f"operator_notes.human_gate_decision must be one of {GATE_DECISIONS}")
    _required_str(value, "operator_label")
    _required_string_list(value, "post_run_caveats", allow_empty=True)


def _validate_audit(value: dict[str, Any]) -> None:
    _check_no_banned_keys(value, "audit")
    _required_str(value, "run_id")
    sha = value.get("signed_sha256")
    if sha is not None and not (isinstance(sha, str) and sha.strip()):
        raise ValidationError("audit.signed_sha256 must be string or null")
    _required_str(value, "emitted_by")


def _validate_source_refs(refs: list[Any]) -> None:
    if not refs:
        raise ValidationError("source_refs must be a non-empty list")
    seen_ids: set[str] = set()
    for idx, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise ValidationError(f"source_refs[{idx}] must be object")
        ref_id = _required_str(ref, "id")
        if ref_id in seen_ids:
            raise ValidationError(f"duplicate source_ref id: {ref_id}")
        seen_ids.add(ref_id)
        _required_str(ref, "label")
        _required_str(ref, "url")
        _required_str(ref, "supports")


# ── content-safety helpers ────────────────────────────────────────────────────


def _check_no_banned_keys(value: dict[str, Any], path: str) -> None:
    lowered = {str(k).lower() for k in value.keys()}
    blocked = sorted(k for k in lowered if k in BANNED_KEYS)
    if blocked:
        raise ValidationError(f"{path} contains banned keys: {blocked}")


def _check_non_actionable(text: str, path: str) -> None:
    lowered = text.lower()
    for phrase in PROCEDURAL_PHRASES:
        if phrase in lowered:
            raise ValidationError(f"{path} contains procedural phrase: {phrase!r}")


def _check_diff_is_defensive(diff: str) -> None:
    """Reject diffs that look like they ADD an exploit primitive.

    The contract allows defensive diffs against vulnerable-by-design code, so we
    do not block strings like ``jndi:`` outright (the Sigma rule references them
    as detection patterns). We block diffs that *add* lines containing common
    payload tokens via the unified-diff ``+`` prefix.
    """
    payload_tokens = ("${jndi:", "${${", "marshalsec.jndi.LDAPRefServer")
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        lowered_added = line.lower()
        for token in payload_tokens:
            if token.lower() in lowered_added:
                raise ValidationError(
                    f"defense.patch.diff adds payload-like content: {token!r}"
                )


_SIGMA_REQUIRED = ("title:", "id:", "logsource:", "detection:", "level:")


def _check_sigma_yaml(yaml_text: str, expected_id: str) -> None:
    if not all(needle in yaml_text for needle in _SIGMA_REQUIRED):
        missing = [n for n in _SIGMA_REQUIRED if n not in yaml_text]
        raise ValidationError(f"defense.sigma_rule.yaml missing fields: {missing}")
    match = re.search(r"^id:\s*(\S+)", yaml_text, flags=re.MULTILINE)
    if not match:
        raise ValidationError("defense.sigma_rule.yaml has no parseable id")
    if match.group(1).strip() != expected_id:
        raise ValidationError(
            "defense.sigma_rule.yaml id does not match defense.sigma_rule.rule_id"
        )


# ── primitive helpers ─────────────────────────────────────────────────────────


def _coerce_object(value: dict[str, Any] | str, label: str) -> dict[str, Any]:
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValidationError(f"{label} JSON must decode to an object")
        return parsed
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def _required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    inner = value.get(key)
    if not isinstance(inner, dict):
        raise ValidationError(f"missing or invalid object: {key}")
    return inner


def _required_list(value: dict[str, Any], key: str) -> list[Any]:
    inner = value.get(key)
    if not isinstance(inner, list) or not inner:
        raise ValidationError(f"missing or invalid non-empty list: {key}")
    return inner


def _required_string_list(
    value: dict[str, Any], key: str, *, allow_empty: bool = False
) -> list[str]:
    inner = value.get(key)
    if not isinstance(inner, list) or (not allow_empty and not inner):
        raise ValidationError(f"missing or invalid list: {key}")
    out: list[str] = []
    for item in inner:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{key} must contain non-empty strings")
        out.append(item.strip())
    return out


def _required_str(value: dict[str, Any], key: str) -> str:
    inner = value.get(key)
    if not isinstance(inner, str) or not inner.strip():
        raise ValidationError(f"missing or invalid string: {key}")
    return inner.strip()


def _validate_iso_datetime(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be ISO 8601 datetime") from exc


def _is_unit_float(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0.0 <= float(value) <= 1.0
    )
