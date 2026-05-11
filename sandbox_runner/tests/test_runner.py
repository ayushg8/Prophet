from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sandbox_runner.runner import (
    CUSTOMER_APPROVAL_SCHEMA_VERSION,
    NON_FIXTURE_SANDBOX_APPROVAL,
    SandboxRunnerError,
    build_run_manifest,
    run_profile,
)
from sandbox_runner.schema import (
    DEFAULT_SANDBOX_SCHEMA_PATH,
    SandboxArtifactSchemaError,
    SandboxRunManifestSchemaError,
    validate_sandbox_artifact_schema,
    validate_sandbox_run_manifest_schema,
)
from validator import validate_exploit_engine_artifact


ROOT = Path(__file__).resolve().parents[2]
FIXED_TIME = "2026-05-04T20:20:00Z"
DEFAULT_POLICY = ROOT / "policy/prophet-pilot-policy.json"
FIXTURE_ONLY_POLICY = ROOT / "policy/examples/fixture-only-policy.json"


class SandboxRunnerTests(unittest.TestCase):
    def test_fixture_profile_emits_valid_direction_c_artifact(self) -> None:
        artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-unit-test",
        )
        validate_exploit_engine_artifact(artifact)
        self.assertEqual(artifact["schema_version"], "exploit_engine_artifact.v0.1")
        self.assertTrue(artifact["artifact_id"].startswith("ee-sandbox-edge-appliance-"))
        self.assertEqual(artifact["validation"]["post_patch_status"], "blocked")
        self.assertIn("localhost", artifact["validation"]["scope"].lower())

    def test_financial_fixture_profile_emits_valid_direction_c_artifact(self) -> None:
        artifact = run_profile(
            profile="financial-workflow-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-financial-unit-test",
            policy=DEFAULT_POLICY,
        )
        validate_exploit_engine_artifact(artifact)
        validate_sandbox_artifact_schema(artifact)
        self.assertTrue(artifact["artifact_id"].startswith("ee-sandbox-financial-workflow-"))
        self.assertEqual(artifact["input_refs"]["candidate_id"], "cs-fixture-financial-theft-001")
        self.assertEqual(artifact["validation"]["post_patch_status"], "blocked")
        self.assertEqual(
            artifact["validation"]["validation_template"],
            "financial-workflow-fixture-profile",
        )

    def test_sandbox_artifact_schema_file_is_published(self) -> None:
        schema = json.loads(DEFAULT_SANDBOX_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$id"],
            "https://prophet.local/schemas/sandbox-artifact.v0.1.json",
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], "exploit_engine_artifact.v0.1")

    def test_run_manifest_records_hashes_without_raw_logs(self) -> None:
        artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-manifest-test",
            policy=DEFAULT_POLICY,
        )
        manifest = build_run_manifest(
            artifact=artifact,
            profile="edge-appliance-fixture",
        )
        validate_sandbox_run_manifest_schema(manifest)
        self.assertEqual(manifest["schema_version"], "prophet.sandbox_run_manifest.v0.1")
        self.assertRegex(manifest["artifact"]["content_sha256"], r"^[0-9a-f]{64}$")
        self.assertIsNone(manifest["artifact"]["file_sha256"])
        self.assertFalse(manifest["log_evidence"]["raw_logs_retained"])
        self.assertIsNone(manifest["log_evidence"]["raw_log_path"])
        self.assertEqual(manifest["log_evidence"]["stored_raw_log_bytes"], 0)
        self.assertEqual(manifest["log_evidence"]["stored_log_excerpt_count"], 0)
        self.assertEqual(
            manifest["policy"]["policy_id"],
            "prophet-pilot-fixture-localhost-v0.1",
        )
        self.assertRegex(manifest["policy"]["policy_sha256"], r"^[0-9a-f]{64}$")

    def test_policy_bound_artifact_passes_sandbox_schema(self) -> None:
        artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-schema-test",
            policy=DEFAULT_POLICY,
        )
        validate_sandbox_artifact_schema(artifact)
        self.assertEqual(artifact["audit"]["policy_id"], "prophet-pilot-fixture-localhost-v0.1")
        self.assertRegex(artifact["audit"]["policy_sha256"], r"^[0-9a-f]{64}$")

    def test_sandbox_schema_rejects_non_fixture_harness_id(self) -> None:
        artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-schema-negative-test",
        )
        artifact["validation"]["sandbox_id"] = "remote-validation-harness"
        with self.assertRaises(SandboxArtifactSchemaError):
            validate_sandbox_artifact_schema(artifact)

    def test_run_manifest_schema_rejects_raw_log_retention(self) -> None:
        artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="sandbox-manifest-negative-test",
            policy=DEFAULT_POLICY,
        )
        manifest = build_run_manifest(
            artifact=artifact,
            profile="edge-appliance-fixture",
        )
        manifest["log_evidence"]["raw_logs_retained"] = True
        with self.assertRaises(SandboxRunManifestSchemaError):
            validate_sandbox_run_manifest_schema(manifest)

    def test_module_cli_writes_valid_artifact_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "sandbox-artifact.json"
            manifest_path = Path(tmp) / "sandbox-run-manifest.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sandbox_runner",
                    "run",
                    "--profile",
                    "edge-appliance-fixture",
                    "--policy",
                    str(DEFAULT_POLICY),
                    "--generated-at",
                    FIXED_TIME,
                    "--run-id",
                    "sandbox-cli-test",
                    "--out",
                    str(out_path),
                    "--manifest-out",
                    str(manifest_path),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": f"{ROOT}:{ROOT / 'cyber-side'}"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            artifact = json.loads(out_path.read_text(encoding="utf-8"))
            validate_exploit_engine_artifact(artifact)
            validate_sandbox_artifact_schema(artifact)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_sandbox_run_manifest_schema(manifest)
            self.assertEqual(
                artifact["audit"]["policy_id"],
                "prophet-pilot-fixture-localhost-v0.1",
            )
            self.assertRegex(artifact["audit"]["policy_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(manifest["artifact"]["artifact_id"], artifact["artifact_id"])
            self.assertRegex(manifest["artifact"]["file_sha256"], r"^[0-9a-f]{64}$")

    def test_policy_rejects_disallowed_sandbox_mode(self) -> None:
        with self.assertRaises(SandboxRunnerError):
            run_profile(
                profile="edge-appliance-fixture",
                generated_at=FIXED_TIME,
                run_id="sandbox-policy-reject-test",
                policy=FIXTURE_ONLY_POLICY,
            )

    def test_container_mode_is_disabled_by_default(self) -> None:
        with self.assertRaisesRegex(SandboxRunnerError, "customer approval record is required"):
            run_profile(profile="edge-appliance-fixture", mode="container")

    def test_container_mode_requires_sanitized_customer_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            approval_path = Path(tmp) / "approval.json"
            approval_path.write_text(
                json.dumps(
                    {
                        "schema_version": CUSTOMER_APPROVAL_SCHEMA_VERSION,
                        "approval_id": "approval-edge-container-001",
                        "profile": "edge-appliance-fixture",
                        "mode": "container",
                        "decision": "approved",
                        "approved_for": [NON_FIXTURE_SANDBOX_APPROVAL],
                        "safety_attestation": {
                            "no_live_targets": True,
                            "no_payloads": True,
                            "no_credentials": True,
                            "customer_boundary_reviewed": True,
                            "policy_reviewed": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SandboxRunnerError, "disabled after customer approval"):
                run_profile(
                    profile="edge-appliance-fixture",
                    mode="container",
                    customer_approval_record=approval_path,
                )

    def test_container_mode_still_has_no_public_packaged_profile_after_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            approval_path = Path(tmp) / "approval.json"
            approval_path.write_text(
                json.dumps(
                    {
                        "schema_version": CUSTOMER_APPROVAL_SCHEMA_VERSION,
                        "approval_id": "approval-edge-container-001",
                        "profile": "edge-appliance-fixture",
                        "mode": "container",
                        "decision": "approved",
                        "approved_for": [NON_FIXTURE_SANDBOX_APPROVAL],
                        "safety_attestation": {
                            "no_live_targets": True,
                            "no_payloads": True,
                            "no_credentials": True,
                            "customer_boundary_reviewed": True,
                            "policy_reviewed": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            env = {**os.environ, "PROPHET_ENABLE_SANDBOX_RUNNER": "1"}
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(SandboxRunnerError, "no container profiles are packaged"):
                    run_profile(
                        profile="edge-appliance-fixture",
                        mode="container",
                        customer_approval_record=approval_path,
                    )

    def test_customer_approval_record_rejects_sensitive_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            approval_path = Path(tmp) / "approval.json"
            approval_path.write_text(
                json.dumps(
                    {
                        "schema_version": CUSTOMER_APPROVAL_SCHEMA_VERSION,
                        "approval_id": "approval-edge-container-001",
                        "profile": "edge-appliance-fixture",
                        "mode": "container",
                        "decision": "approved",
                        "approved_for": [NON_FIXTURE_SANDBOX_APPROVAL],
                        "review_note": "Contact buyer@example.com for approval.",
                        "safety_attestation": {
                            "no_live_targets": True,
                            "no_payloads": True,
                            "no_credentials": True,
                            "customer_boundary_reviewed": True,
                            "policy_reviewed": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SandboxRunnerError, "email-like"):
                run_profile(
                    profile="edge-appliance-fixture",
                    mode="container",
                    customer_approval_record=approval_path,
                )


if __name__ == "__main__":
    unittest.main()
