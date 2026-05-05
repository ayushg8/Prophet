from __future__ import annotations

import copy
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from evidence.bundle import EvidenceBundleError, load_json
from policy.lint import (
    PolicyLintError,
    PolicySchemaError,
    compare_policy_files,
    lint_policy_file,
    main,
    verify_runtime_policy_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "policy/prophet-pilot-policy.json"
POLICY_SCHEMA = ROOT / "policy/prophet-pilot-policy.schema.json"
EXAMPLES = (
    ROOT / "policy/examples/fixture-only-policy.json",
    ROOT / "policy/examples/seeded-osint-only-policy.json",
    ROOT / "policy/examples/localhost-sandbox-policy.json",
)


class PolicyLintTests(unittest.TestCase):
    def test_default_policy_lints(self) -> None:
        summary = lint_policy_file(DEFAULT_POLICY)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["policy_id"], "prophet-pilot-fixture-localhost-v0.1")
        self.assertRegex(summary["policy_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(summary["schema_path"], str(POLICY_SCHEMA))
        self.assertIn("localhost_sandbox", summary["allowed_modes"]["validation"])
        self.assertIn("cisa_vulnrichment_cve_record_seed", summary["allowed_source_ids"])
        self.assertIn("edge-appliance-fixture", summary["allowed_sandbox_profiles"])
        self.assertIn("financial-workflow-fixture", summary["allowed_sandbox_profiles"])
        self.assertIn("jira_ticket", summary["allowed_integration_exports"])
        self.assertEqual(summary["retention"]["runtime_outputs_max_days"], 30)
        self.assertEqual(summary["retention"]["audit_log_max_days"], 90)

    def test_policy_examples_lint(self) -> None:
        for path in EXAMPLES:
            with self.subTest(path=path.name):
                summary = lint_policy_file(path)
                self.assertTrue(summary["ok"])
                self.assertRegex(summary["policy_sha256"], r"^[0-9a-f]{64}$")

    def test_policy_schema_file_is_published(self) -> None:
        schema = load_json(POLICY_SCHEMA)
        self.assertEqual(
            schema["$id"],
            "https://prophet.local/schemas/prophet-pilot-policy.v0.1.json",
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], "prophet_pilot_policy.v0.1")

    def test_json_schema_rejects_unknown_top_level_field(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["customer_live_override"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicySchemaError):
                lint_policy_file(path)

    def test_json_schema_rejects_missing_description(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        del policy["description"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicySchemaError):
                lint_policy_file(path)

    def test_lint_rejects_live_targets_enabled(self) -> None:
        policy = load_json(DEFAULT_POLICY)
        policy["controls"]["live_targets_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(EvidenceBundleError):
                lint_policy_file(path)

    def test_lint_rejects_unknown_mode(self) -> None:
        policy = load_json(DEFAULT_POLICY)
        policy["allowed_modes"]["validation"].append("external_range")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(EvidenceBundleError):
                lint_policy_file(path)

    def test_lint_rejects_non_runtime_default_output(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["default_outputs"]["evidence_json"] = "evidence/latest.json"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicyLintError):
                lint_policy_file(path)

    def test_lint_rejects_unsafe_source_id(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["allowed_source_ids"] = ["https://example.com/source"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicyLintError):
                lint_policy_file(path)

    def test_lint_rejects_duplicate_sandbox_profile(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["allowed_sandbox_profiles"] = ["edge-appliance-fixture", "edge-appliance-fixture"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicyLintError):
                lint_policy_file(path)

    def test_lint_rejects_unknown_integration_export(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["allowed_integration_exports"] = ["direct_siem_push"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(PolicyLintError):
                lint_policy_file(path)

    def test_lint_rejects_unsafe_retention(self) -> None:
        policy = copy.deepcopy(load_json(DEFAULT_POLICY))
        policy["retention"]["raw_collection_retained"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-policy.json"
            path.write_text(_json(policy), encoding="utf-8")
            with self.assertRaises(EvidenceBundleError):
                lint_policy_file(path)

    def test_cli_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "policy-summary.json"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--policy", str(DEFAULT_POLICY), "--out-json", str(out)])
            self.assertEqual(exit_code, 0)
            self.assertTrue(out.exists())
            self.assertEqual(load_json(out)["policy_id"], "prophet-pilot-fixture-localhost-v0.1")

    def test_compare_same_policy_has_no_differences(self) -> None:
        comparison = compare_policy_files(DEFAULT_POLICY, DEFAULT_POLICY)
        self.assertFalse(comparison["changed"])
        self.assertEqual(comparison["difference_count"], 0)
        self.assertEqual(comparison["differences"], [])

    def test_compare_fixture_only_policy_to_default(self) -> None:
        comparison = compare_policy_files(EXAMPLES[0], DEFAULT_POLICY)
        self.assertTrue(comparison["changed"])
        fields = {difference["field"]: difference for difference in comparison["differences"]}

        self.assertEqual(
            fields["policy_id"]["candidate"],
            "prophet-pilot-fixture-only-v0.1",
        )
        self.assertEqual(
            fields["allowed_modes.osint_collection"]["removed"],
            ["seeded_osint"],
        )
        self.assertEqual(
            fields["allowed_modes.validation"]["removed"],
            ["localhost_sandbox"],
        )
        self.assertEqual(
            fields["allowed_source_ids"]["removed"],
            [
                "cisa_vulnrichment_cve_record_seed",
                "osv_query_api_seed",
                "redhat_security_data_cve_api",
            ],
        )
        self.assertEqual(
            fields["allowed_sandbox_profiles"]["removed"],
            ["edge-appliance-fixture", "financial-workflow-fixture"],
        )
        self.assertEqual(fields["retention.runtime_outputs_max_days"]["candidate"], 7)
        self.assertEqual(fields["default_outputs.asset_seedset"]["kind"], "value_removed")

    def test_cli_writes_policy_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "policy-summary.json"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--policy",
                        str(EXAMPLES[1]),
                        "--compare-to",
                        str(DEFAULT_POLICY),
                        "--out-json",
                        str(out),
                    ]
                )
            self.assertEqual(exit_code, 0)
            summary = load_json(out)
            self.assertTrue(summary["comparison"]["changed"])
            self.assertEqual(
                summary["comparison"]["baseline_policy_id"],
                "prophet-pilot-fixture-localhost-v0.1",
            )
            self.assertEqual(
                summary["comparison"]["candidate_policy_id"],
                "prophet-pilot-seeded-osint-only-v0.1",
            )

    def test_verify_runtime_policy_artifacts_accepts_matching_hashes(self) -> None:
        policy_sha = lint_policy_file(DEFAULT_POLICY)["policy_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "evidence.json"
            artifact.write_text(
                _json(
                    {
                        "schema_version": "prophet_evidence_bundle.v0.1",
                        "policy": {"policy_sha256": policy_sha},
                        "hashes": {"policy_sha256": policy_sha},
                    }
                ),
                encoding="utf-8",
            )

            summary = verify_runtime_policy_artifacts(DEFAULT_POLICY, [artifact])

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["checked_artifact_count"], 1)
        self.assertEqual(summary["artifacts"][0]["status"], "ok")

    def test_verify_runtime_policy_artifacts_rejects_drift(self) -> None:
        drifted_sha = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "osint-manifest.json"
            artifact.write_text(
                _json(
                    {
                        "schema_version": "prophet.osint_snapshot_manifest.v0.1",
                        "policy": {"policy_sha256": drifted_sha},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PolicyLintError, "runtime policy drift"):
                verify_runtime_policy_artifacts(DEFAULT_POLICY, [artifact])

    def test_verify_runtime_policy_artifacts_checks_audit_export_hash_list(self) -> None:
        policy_sha = lint_policy_file(DEFAULT_POLICY)["policy_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "audit-export.json"
            artifact.write_text(
                _json(
                    {
                        "schema_version": "prophet_operator_audit_export.v0.1",
                        "policy_sha256s": [policy_sha],
                    }
                ),
                encoding="utf-8",
            )

            summary = verify_runtime_policy_artifacts(DEFAULT_POLICY, [artifact])

        self.assertEqual(
            summary["artifacts"][0]["observed_policy_hashes"][0]["path"],
            "policy_sha256s[0]",
        )

    def test_verify_runtime_policy_artifacts_checks_runtime_retention_report(self) -> None:
        policy_sha = lint_policy_file(DEFAULT_POLICY)["policy_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "runtime-retention.json"
            artifact.write_text(
                _json(
                    {
                        "schema_version": "prophet_runtime_retention_report.v0.1",
                        "policy": {"policy_sha256": policy_sha},
                    }
                ),
                encoding="utf-8",
            )

            summary = verify_runtime_policy_artifacts(DEFAULT_POLICY, [artifact])

        self.assertEqual(summary["artifacts"][0]["artifact_type"], "runtime retention report")

    def test_cli_writes_runtime_policy_verification(self) -> None:
        policy_sha = lint_policy_file(DEFAULT_POLICY)["policy_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "integration-manifest.json"
            out = Path(tmp) / "policy-summary.json"
            artifact.write_text(
                _json(
                    {
                        "schema_version": "prophet_integration_export.v0.1",
                        "evidence_refs": {"policy_sha256": policy_sha},
                    }
                ),
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--policy",
                        str(DEFAULT_POLICY),
                        "--verify-runtime-artifacts",
                        str(artifact),
                        "--out-json",
                        str(out),
                    ]
                )

            self.assertEqual(exit_code, 0)
            verification = load_json(out)["runtime_policy_verification"]
            self.assertEqual(verification["checked_artifact_count"], 1)
            self.assertEqual(verification["artifacts"][0]["artifact_type"], "integration manifest")


def _json(value: object) -> str:
    import json

    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    unittest.main()
