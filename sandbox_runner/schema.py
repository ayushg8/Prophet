"""Schema validation for Prophet sandbox runner artifacts and manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CYBER_SIDE = str(REPO_ROOT / "cyber-side")
if CYBER_SIDE not in sys.path:
    sys.path.insert(0, CYBER_SIDE)

from policy.lint import PolicySchemaError, validate_json_schema_value
from validator import validate_exploit_engine_artifact  # type: ignore


DEFAULT_SANDBOX_SCHEMA_PATH = Path(__file__).with_name("sandbox-artifact.schema.json")
DEFAULT_RUN_MANIFEST_SCHEMA_PATH = Path(__file__).with_name("sandbox-run-manifest.schema.json")


class SandboxArtifactSchemaError(ValueError):
    """Raised when a sandbox artifact drifts from the public schema."""


class SandboxRunManifestSchemaError(ValueError):
    """Raised when a sandbox run manifest drifts from the public schema."""


def validate_sandbox_artifact_schema(
    artifact: dict[str, Any] | str,
    *,
    schema_path: str | Path = DEFAULT_SANDBOX_SCHEMA_PATH,
) -> None:
    """Validate the Direction C contract plus sandbox-runner-specific fields."""

    value = _coerce_object(artifact)
    validate_exploit_engine_artifact(value)
    schema = _load_schema(Path(schema_path))
    try:
        validate_json_schema_value(value, schema)
    except PolicySchemaError as exc:
        raise SandboxArtifactSchemaError(f"sandbox artifact schema validation failed: {exc}") from exc


def validate_sandbox_run_manifest_schema(
    manifest: dict[str, Any] | str,
    *,
    schema_path: str | Path = DEFAULT_RUN_MANIFEST_SCHEMA_PATH,
) -> None:
    """Validate the sandbox run manifest contract."""

    value = _coerce_manifest_object(manifest)
    schema = _load_schema(Path(schema_path))
    try:
        validate_json_schema_value(value, schema)
    except PolicySchemaError as exc:
        raise SandboxRunManifestSchemaError(
            f"sandbox run manifest schema validation failed: {exc}"
        ) from exc
    log_evidence = value.get("log_evidence")
    if not isinstance(log_evidence, dict):
        raise SandboxRunManifestSchemaError("log_evidence must be object")
    if log_evidence.get("raw_logs_retained") is not False:
        raise SandboxRunManifestSchemaError("log_evidence.raw_logs_retained must be false")
    if log_evidence.get("raw_log_path") is not None:
        raise SandboxRunManifestSchemaError("log_evidence.raw_log_path must be null")


def _coerce_object(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise SandboxArtifactSchemaError("sandbox artifact JSON must decode to object")
        return parsed
    if not isinstance(value, dict):
        raise SandboxArtifactSchemaError("sandbox artifact must be object")
    return value


def _coerce_manifest_object(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise SandboxRunManifestSchemaError("sandbox run manifest JSON must decode to object")
        return parsed
    if not isinstance(value, dict):
        raise SandboxRunManifestSchemaError("sandbox run manifest must be object")
    return value


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict):
        raise SandboxArtifactSchemaError(f"{path} must decode to object")
    return schema
