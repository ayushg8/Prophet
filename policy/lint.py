"""Lint Prophet pilot policy files for buyer-pilot safety.

The evidence bundle validates the policy contract at runtime. This module adds
standalone checks that are useful before a customer-specific policy is handed to
the console or smoke script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from evidence.bundle import (
    EvidenceBundleError,
    POLICY_ALLOWED_MODES,
    POLICY_BLOCKED_CONTROLS,
    POLICY_REQUIRED_ATTESTATIONS,
    POLICY_SCHEMA_VERSION,
    load_json,
    validate_pilot_policy,
)


RUNTIME_OUTPUT_PREFIXES = (
    "assets/outputs/runtime/",
    "world-side/outputs/runtime/",
    "cyber-side/outputs/runtime/",
    "evidence/outputs/runtime/",
    "integrations/outputs/runtime/",
)

OPTIONAL_ID_LISTS = (
    "allowed_source_ids",
    "allowed_sandbox_profiles",
)

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,120}$")

ALLOWED_INTEGRATION_EXPORTS = {
    "splunk_saved_search",
    "elastic_detection_rule",
    "sentinel_analytic_rule",
    "jira_ticket",
    "servicenow_task",
    "operator_audit_event",
}

DEFAULT_SCHEMA_PATH = Path(__file__).with_name("prophet-pilot-policy.schema.json")

RUNTIME_POLICY_HASH_SCHEMAS: dict[str, tuple[str, tuple[tuple[str, ...], ...]]] = {
    "prophet_evidence_bundle.v0.1": (
        "evidence bundle",
        (("policy", "policy_sha256"), ("hashes", "policy_sha256")),
    ),
    "prophet.osint_snapshot_manifest.v0.1": (
        "OSINT manifest",
        (("policy", "policy_sha256"),),
    ),
    "exploit_engine_artifact.v0.1": (
        "sandbox artifact",
        (("audit", "policy_sha256"),),
    ),
    "prophet.sandbox_run_manifest.v0.1": (
        "sandbox run manifest",
        (("policy", "policy_sha256"),),
    ),
    "prophet_integration_export.v0.1": (
        "integration manifest",
        (("evidence_refs", "policy_sha256"),),
    ),
    "prophet_operator_audit_event.v0.1": (
        "operator audit event",
        (("policy", "policy_sha256"),),
    ),
    "prophet_operator_audit_export.v0.1": (
        "operator audit export",
        (("policy_sha256s",),),
    ),
    "prophet_operator_audit_retention.v0.1": (
        "operator audit retention report",
        (("policy", "policy_sha256"),),
    ),
    "prophet_runtime_retention_report.v0.1": (
        "runtime retention report",
        (("policy", "policy_sha256"),),
    ),
}


class PolicyLintError(ValueError):
    """Raised when a policy file is valid JSON but unsafe for pilot use."""


class PolicySchemaError(PolicyLintError):
    """Raised when a policy file fails the public JSON Schema contract."""


def lint_policy_file(
    path: str | Path,
    *,
    schema_path: str | Path | None = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    policy_path = Path(path)
    policy = load_json(policy_path)
    validate_pilot_policy(policy)
    if schema_path is not None:
        _validate_policy_json_schema(policy, schema_path)
    _lint_default_outputs(policy)
    _lint_optional_id_lists(policy)
    _lint_allowed_integration_exports(policy)

    allowed_modes = {
        category: list(policy["allowed_modes"][category])
        for category in sorted(POLICY_ALLOWED_MODES)
    }
    controls = {
        control: policy["controls"][control]
        for control in sorted(POLICY_BLOCKED_CONTROLS)
    }
    default_outputs = {
        key: value
        for key, value in sorted(_object(policy.get("default_outputs")).items())
        if isinstance(value, str)
    }
    return {
        "ok": True,
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_id": policy["policy_id"],
        "policy_sha256": _sha256_normalized(policy),
        "path": str(policy_path),
        "schema_path": str(schema_path) if schema_path is not None else None,
        "allowed_modes": allowed_modes,
        "blocked_controls": controls,
        "required_attestations": list(policy["required_attestations"]),
        "default_outputs": default_outputs,
        "allowed_source_ids": list(policy.get("allowed_source_ids") or []),
        "allowed_sandbox_profiles": list(policy.get("allowed_sandbox_profiles") or []),
        "allowed_integration_exports": list(policy.get("allowed_integration_exports") or []),
        "retention": dict(sorted(_object(policy.get("retention")).items())),
    }


def compare_policy_files(candidate_path: str | Path, baseline_path: str | Path) -> dict[str, Any]:
    """Return buyer-review differences between a candidate and baseline policy."""

    candidate = lint_policy_file(candidate_path)
    baseline = lint_policy_file(baseline_path)
    return compare_policy_summaries(candidate=candidate, baseline=baseline)


def compare_policy_summaries(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    differences: list[dict[str, Any]] = []

    _append_value_difference(differences, "schema_version", baseline, candidate)
    _append_value_difference(differences, "policy_id", baseline, candidate)

    _append_mapping_set_differences(
        differences,
        field_prefix="allowed_modes",
        baseline_mapping=_object(baseline.get("allowed_modes")),
        candidate_mapping=_object(candidate.get("allowed_modes")),
    )
    _append_mapping_value_differences(
        differences,
        field_prefix="blocked_controls",
        baseline_mapping=_object(baseline.get("blocked_controls")),
        candidate_mapping=_object(candidate.get("blocked_controls")),
    )
    _append_set_difference(
        differences,
        "required_attestations",
        baseline.get("required_attestations") or [],
        candidate.get("required_attestations") or [],
    )
    _append_set_difference(
        differences,
        "allowed_source_ids",
        baseline.get("allowed_source_ids") or [],
        candidate.get("allowed_source_ids") or [],
    )
    _append_set_difference(
        differences,
        "allowed_sandbox_profiles",
        baseline.get("allowed_sandbox_profiles") or [],
        candidate.get("allowed_sandbox_profiles") or [],
    )
    _append_set_difference(
        differences,
        "allowed_integration_exports",
        baseline.get("allowed_integration_exports") or [],
        candidate.get("allowed_integration_exports") or [],
    )
    _append_mapping_value_differences(
        differences,
        field_prefix="retention",
        baseline_mapping=_object(baseline.get("retention")),
        candidate_mapping=_object(candidate.get("retention")),
    )
    _append_mapping_value_differences(
        differences,
        field_prefix="default_outputs",
        baseline_mapping=_object(baseline.get("default_outputs")),
        candidate_mapping=_object(candidate.get("default_outputs")),
    )

    return {
        "baseline_policy_id": baseline.get("policy_id"),
        "baseline_policy_sha256": baseline.get("policy_sha256"),
        "candidate_policy_id": candidate.get("policy_id"),
        "candidate_policy_sha256": candidate.get("policy_sha256"),
        "changed": bool(differences),
        "difference_count": len(differences),
        "differences": differences,
    }


def verify_runtime_policy_artifacts(
    policy_path: str | Path,
    artifact_paths: list[str | Path] | tuple[str | Path, ...],
    *,
    schema_path: str | Path | None = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Verify known runtime artifacts were generated under the given policy."""

    policy_summary = lint_policy_file(policy_path, schema_path=schema_path)
    return verify_runtime_policy_artifacts_for_summary(
        policy_summary=policy_summary,
        artifact_paths=artifact_paths,
    )


def verify_runtime_policy_artifacts_for_summary(
    *,
    policy_summary: dict[str, Any],
    artifact_paths: list[str | Path] | tuple[str | Path, ...],
) -> dict[str, Any]:
    expected_policy_sha256 = policy_summary.get("policy_sha256")
    if not _is_sha256(expected_policy_sha256):
        raise PolicyLintError("policy summary must include a SHA-256 policy hash")

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    checked_count = 0

    for artifact_path in artifact_paths:
        path = Path(artifact_path)
        artifact = load_json(path)
        schema_version = artifact.get("schema_version")
        contract = RUNTIME_POLICY_HASH_SCHEMAS.get(str(schema_version))
        if contract is None:
            results.append(
                {
                    "path": str(path),
                    "schema_version": schema_version,
                    "status": "skipped",
                    "reason": "no runtime policy-hash contract for schema",
                }
            )
            continue

        artifact_label, hash_paths = contract
        observed_hashes: list[dict[str, Any]] = []
        artifact_failures: list[str] = []
        for hash_path in hash_paths:
            values = _nested_policy_hash_values(artifact, hash_path)
            if not values:
                artifact_failures.append(f"{_dotted(hash_path)} is missing")
                continue
            for dotted_path, observed_hash in values:
                observed_hashes.append(
                    {
                        "path": dotted_path,
                        "policy_sha256": observed_hash,
                    }
                )
                if not _is_sha256(observed_hash):
                    artifact_failures.append(f"{dotted_path} is not a SHA-256 hash")
                    continue
                if observed_hash != expected_policy_sha256:
                    artifact_failures.append(
                        f"{dotted_path} has {observed_hash}, expected {expected_policy_sha256}"
                    )

        checked_count += 1
        status = "ok" if not artifact_failures else "drift"
        results.append(
            {
                "path": str(path),
                "schema_version": schema_version,
                "artifact_type": artifact_label,
                "status": status,
                "observed_policy_hashes": observed_hashes,
            }
        )
        for failure in artifact_failures:
            failures.append(f"{path}: {failure}")

    if failures:
        raise PolicyLintError("runtime policy drift detected: " + "; ".join(failures))

    return {
        "ok": True,
        "policy_id": policy_summary.get("policy_id"),
        "policy_sha256": expected_policy_sha256,
        "artifact_count": len(artifact_paths),
        "checked_artifact_count": checked_count,
        "skipped_artifact_count": len(artifact_paths) - checked_count,
        "artifacts": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a Prophet pilot policy JSON file and print its canonical hash."
    )
    parser.add_argument("--policy", required=True, help="Path to prophet_pilot_policy.v0.1 JSON")
    parser.add_argument(
        "--compare-to",
        help="Optional baseline policy path. Prints semantic differences after linting both files.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to the Prophet pilot policy JSON Schema used for structural validation.",
    )
    parser.add_argument(
        "--verify-runtime-artifacts",
        nargs="*",
        default=[],
        metavar="PATH",
        help=(
            "Optional runtime JSON artifacts to verify against the policy hash. "
            "Known Prophet schemas fail on missing or drifted policy hashes."
        ),
    )
    parser.add_argument("--out-json", help="Optional path for a lint summary JSON")
    args = parser.parse_args(argv)

    try:
        summary = lint_policy_file(args.policy, schema_path=args.schema)
        if args.compare_to:
            baseline = lint_policy_file(args.compare_to, schema_path=args.schema)
            summary["comparison"] = compare_policy_summaries(
                candidate=summary,
                baseline=baseline,
            )
        if args.verify_runtime_artifacts:
            summary["runtime_policy_verification"] = (
                verify_runtime_policy_artifacts_for_summary(
                    policy_summary=summary,
                    artifact_paths=args.verify_runtime_artifacts,
                )
            )
    except (OSError, json.JSONDecodeError, EvidenceBundleError, PolicyLintError) as exc:
        print(f"policy lint failed: {exc}", file=sys.stderr)
        return 1

    rendered = _pretty_json(summary)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


def _lint_default_outputs(policy: dict[str, Any]) -> None:
    outputs = policy.get("default_outputs")
    if outputs is None:
        return
    if not isinstance(outputs, dict):
        raise PolicyLintError("policy.default_outputs must be object when present")
    for key, value in outputs.items():
        if not isinstance(key, str) or not key.strip():
            raise PolicyLintError("policy.default_outputs keys must be non-empty strings")
        if not isinstance(value, str) or not value.strip():
            raise PolicyLintError(f"policy.default_outputs.{key} must be a non-empty string")
        output_path = Path(value)
        if output_path.is_absolute():
            raise PolicyLintError(f"policy.default_outputs.{key} must be repo-relative")
        if ".." in output_path.parts:
            raise PolicyLintError(f"policy.default_outputs.{key} must not contain '..'")
        normalized = value.replace("\\", "/")
        if not any(normalized.startswith(prefix) for prefix in RUNTIME_OUTPUT_PREFIXES):
            allowed = ", ".join(RUNTIME_OUTPUT_PREFIXES)
            raise PolicyLintError(
                f"policy.default_outputs.{key} must stay under ignored runtime outputs: {allowed}"
            )


def _lint_optional_id_lists(policy: dict[str, Any]) -> None:
    for key in OPTIONAL_ID_LISTS:
        value = policy.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise PolicyLintError(f"policy.{key} must be list[str] when present")
        duplicates = sorted({item for item in value if value.count(item) > 1})
        if duplicates:
            raise PolicyLintError(f"policy.{key} has duplicate values: {duplicates}")
        for item in value:
            if not SAFE_ID_RE.fullmatch(item):
                raise PolicyLintError(f"policy.{key} contains unsafe id: {item}")


def _lint_allowed_integration_exports(policy: dict[str, Any]) -> None:
    value = policy.get("allowed_integration_exports")
    if value is None:
        return
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise PolicyLintError("policy.allowed_integration_exports must be list[str] when present")
    duplicates = sorted({item for item in value if value.count(item) > 1})
    if duplicates:
        raise PolicyLintError(
            f"policy.allowed_integration_exports has duplicate values: {duplicates}"
        )
    unknown = sorted(set(value) - ALLOWED_INTEGRATION_EXPORTS)
    if unknown:
        raise PolicyLintError(
            f"policy.allowed_integration_exports has unknown values: {unknown}"
        )


def _validate_policy_json_schema(policy: dict[str, Any], schema_path: str | Path) -> None:
    schema = load_json(schema_path)
    try:
        validate_json_schema_value(policy, schema)
    except PolicySchemaError as exc:
        raise PolicySchemaError(f"policy JSON Schema validation failed: {exc}") from exc


def validate_json_schema_value(value: Any, schema: dict[str, Any]) -> None:
    """Validate a small, stdlib-supported JSON Schema subset."""

    if not isinstance(schema, dict):
        raise PolicySchemaError("schema must be object")
    _validate_schema_value(value, schema, "$", schema)


def _validate_schema_value(
    value: Any,
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> None:
    if "$ref" in schema:
        schema = _resolve_schema_ref(schema["$ref"], root_schema)

    for sub_schema in _schema_list(schema.get("allOf"), "allOf"):
        _validate_schema_value(value, sub_schema, path, root_schema)

    if "anyOf" in schema:
        candidates = _schema_list(schema.get("anyOf"), "anyOf")
        if not any(_schema_matches(value, candidate, root_schema) for candidate in candidates):
            raise PolicySchemaError(f"{path} must match at least one allowed schema")

    if "const" in schema and value != schema["const"]:
        raise PolicySchemaError(f"{path} must equal {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise PolicySchemaError(f"{path} must be one of {schema['enum']!r}")

    if "type" in schema:
        expected_types = schema["type"]
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not isinstance(expected_types, list) or not all(
            isinstance(item, str) for item in expected_types
        ):
            raise PolicySchemaError(f"{path} schema has invalid type declaration")
        if not any(_schema_type_matches(value, expected) for expected in expected_types):
            expected = " or ".join(expected_types)
            raise PolicySchemaError(f"{path} must be {expected}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise PolicySchemaError(f"{path} must have length at least {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise PolicySchemaError(f"{path} must match pattern {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise PolicySchemaError(f"{path} must be >= {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise PolicySchemaError(f"{path} must be <= {maximum}")

    if isinstance(value, dict):
        property_name_schema = schema.get("propertyNames")
        if isinstance(property_name_schema, dict):
            for key in value:
                _validate_schema_value(
                    key,
                    property_name_schema,
                    f"{path} property name {key!r}",
                    root_schema,
                )

        properties = _object(schema.get("properties"))
        required = schema.get("required")
        if required is not None:
            if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
                raise PolicySchemaError(f"{path} schema has invalid required list")
            missing = sorted(item for item in required if item not in value)
            if missing:
                raise PolicySchemaError(f"{path} missing required fields: {missing}")

        for key, sub_schema in properties.items():
            if key in value:
                _validate_schema_value(value[key], sub_schema, _join_schema_path(path, key), root_schema)

        additional = schema.get("additionalProperties", True)
        additional_keys = sorted(set(value) - set(properties))
        if additional is False and additional_keys:
            raise PolicySchemaError(f"{path} has unknown fields: {additional_keys}")
        if isinstance(additional, dict):
            for key in additional_keys:
                _validate_schema_value(
                    value[key],
                    additional,
                    _join_schema_path(path, key),
                    root_schema,
                )

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise PolicySchemaError(f"{path} must contain at least {min_items} items")

        if schema.get("uniqueItems") is True:
            seen: set[str] = set()
            duplicates: list[Any] = []
            for item in value:
                key = _canonical_json(item)
                if key in seen:
                    duplicates.append(item)
                seen.add(key)
            if duplicates:
                raise PolicySchemaError(f"{path} has duplicate items: {duplicates!r}")

        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, f"{path}[{index}]", root_schema)

        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict) and not any(
            _schema_matches(item, contains_schema, root_schema) for item in value
        ):
            raise PolicySchemaError(f"{path} must contain an item matching schema")


def _schema_matches(value: Any, schema: dict[str, Any], root_schema: dict[str, Any]) -> bool:
    try:
        _validate_schema_value(value, schema, "$", root_schema)
    except PolicySchemaError:
        return False
    return True


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise PolicySchemaError(f"unsupported JSON Schema type: {expected}")


def _schema_list(value: Any, field: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise PolicySchemaError(f"schema field {field} must be list[object]")
    return value


def _resolve_schema_ref(ref: Any, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
        raise PolicySchemaError(f"unsupported JSON Schema ref: {ref!r}")
    target: Any = root_schema
    for part in ref.lstrip("#/").split("/"):
        if not isinstance(target, dict) or part not in target:
            raise PolicySchemaError(f"unresolved JSON Schema ref: {ref!r}")
        target = target[part]
    if not isinstance(target, dict):
        raise PolicySchemaError(f"JSON Schema ref does not resolve to object: {ref!r}")
    return target


def _join_schema_path(path: str, key: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"{path}.{key}"
    return f"{path}[{key!r}]"


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _append_value_difference(
    differences: list[dict[str, Any]],
    field: str,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> None:
    baseline_value = baseline.get(field)
    candidate_value = candidate.get(field)
    if baseline_value == candidate_value:
        return
    differences.append(
        {
            "field": field,
            "kind": "value_changed",
            "baseline": baseline_value,
            "candidate": candidate_value,
        }
    )


def _append_mapping_set_differences(
    differences: list[dict[str, Any]],
    *,
    field_prefix: str,
    baseline_mapping: dict[str, Any],
    candidate_mapping: dict[str, Any],
) -> None:
    for key in sorted(set(baseline_mapping) | set(candidate_mapping)):
        _append_set_difference(
            differences,
            f"{field_prefix}.{key}",
            baseline_mapping.get(key) or [],
            candidate_mapping.get(key) or [],
        )


def _append_mapping_value_differences(
    differences: list[dict[str, Any]],
    *,
    field_prefix: str,
    baseline_mapping: dict[str, Any],
    candidate_mapping: dict[str, Any],
) -> None:
    for key in sorted(set(baseline_mapping) | set(candidate_mapping)):
        field = f"{field_prefix}.{key}"
        baseline_missing = key not in baseline_mapping
        candidate_missing = key not in candidate_mapping
        if baseline_missing and not candidate_missing:
            differences.append(
                {
                    "field": field,
                    "kind": "value_added",
                    "baseline": None,
                    "candidate": candidate_mapping[key],
                }
            )
            continue
        if candidate_missing and not baseline_missing:
            differences.append(
                {
                    "field": field,
                    "kind": "value_removed",
                    "baseline": baseline_mapping[key],
                    "candidate": None,
                }
            )
            continue
        if baseline_mapping[key] != candidate_mapping[key]:
            differences.append(
                {
                    "field": field,
                    "kind": "value_changed",
                    "baseline": baseline_mapping[key],
                    "candidate": candidate_mapping[key],
                }
            )


def _append_set_difference(
    differences: list[dict[str, Any]],
    field: str,
    baseline_values: Any,
    candidate_values: Any,
) -> None:
    baseline_list = _sorted_strings(baseline_values)
    candidate_list = _sorted_strings(candidate_values)
    if baseline_list == candidate_list:
        return
    baseline_set = set(baseline_list)
    candidate_set = set(candidate_list)
    differences.append(
        {
            "field": field,
            "kind": "set_changed",
            "added": sorted(candidate_set - baseline_set),
            "removed": sorted(baseline_set - candidate_set),
            "baseline": baseline_list,
            "candidate": candidate_list,
        }
    )


def _sorted_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(item for item in value if isinstance(item, str))


def _nested_policy_hash_values(
    value: dict[str, Any],
    path: tuple[str, ...],
) -> list[tuple[str, Any]]:
    current: Any = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return []
        current = current[key]

    dotted_path = _dotted(path)
    if isinstance(current, list):
        return [(f"{dotted_path}[{index}]", item) for index, item in enumerate(current)]
    return [(dotted_path, current)]


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _dotted(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _sha256_normalized(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
