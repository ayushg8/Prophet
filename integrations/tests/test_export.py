from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from evidence.bundle import build_evidence_bundle, load_json, load_policy
from integrations.export import (
    IntegrationExportError,
    build_integration_export,
    main,
    validate_integration_export,
    write_integration_export,
)


ROOT = Path(__file__).resolve().parents[2]
FORECAST_PATH = ROOT / "world-side/outputs/golden-forecast-edge-appliance.json"
PORTFOLIO_PATH = ROOT / "cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json"
ARTIFACT_PATH = ROOT / "cyber-side/fixtures/exploit-engine-output-edge-appliance.json"
ASSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-inventory.json"
ASSET_SEEDSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-seedset.json"
POLICY_PATH = ROOT / "policy/prophet-pilot-policy.json"
FIXED_TIME = "2026-05-04T20:40:00Z"


class IntegrationExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = build_evidence_bundle(
            forecast=load_json(FORECAST_PATH),
            portfolio=load_json(PORTFOLIO_PATH),
            artifact=load_json(ARTIFACT_PATH),
            asset_inventory=load_json(ASSET_PATH),
            asset_seedset=load_json(ASSET_SEEDSET_PATH),
            policy=load_policy(POLICY_PATH),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="integration-export-test-evidence",
        )

    def test_builds_valid_siem_ticket_and_audit_handoff(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-test",
            policy=load_policy(POLICY_PATH),
        )
        validate_integration_export(export)
        self.assertEqual(export["schema_version"], "prophet_integration_export.v0.1")
        self.assertEqual(export["mode"], "review_template_only")
        self.assertIn("splunk_saved_search", export["siem"])
        self.assertIn("elastic_detection_rule", export["siem"])
        self.assertIn("sentinel_analytic_rule", export["siem"])
        self.assertIn("jira_ticket", export["tickets"])
        self.assertIn("servicenow_task", export["tickets"])
        self.assertEqual(
            export["operator_audit_event"]["event_type"],
            "integration_handoff_exported",
        )
        self.assertEqual(
            export["operator_audit_event"]["schema_version"],
            "prophet.operator_audit_event.v0.1",
        )
        self.assertEqual(
            export["operator_audit_event"]["policy"]["policy_sha256"],
            export["evidence_refs"]["policy_sha256"],
        )
        self.assertEqual(export["evidence_refs"]["policy_id"], "prophet-pilot-fixture-localhost-v0.1")
        self.assertTrue(export["policy_restrictions"]["enforced"])
        self.assertTrue(export["safety_attestation"]["no_live_target_data_included"])
        self.assertIn(
            "No live target data is included",
            export["safety_attestation"]["data_boundary_statement"],
        )
        self.assertIn("export_body_sha256", export["hashes"])

    def test_deterministic_hash_stability_with_fixed_inputs(self) -> None:
        first = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-test",
        )
        second = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-test",
        )
        self.assertEqual(first["hashes"], second["hashes"])

    def test_cli_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp) / "bundle.json"
            out_dir = Path(tmp) / "handoff"
            bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--bundle",
                        str(bundle_path),
                        "--policy",
                        str(POLICY_PATH),
                        "--generated-at",
                        FIXED_TIME,
                        "--export-id",
                        "integration-export-cli-test",
                        "--out-dir",
                        str(out_dir),
                    ]
                )
            self.assertEqual(exit_code, 0)
            for rel_path in (
                "manifest.json",
                "siem/splunk_saved_search.json",
                "siem/elastic_detection_rule.ndjson",
                "siem/sentinel_analytic_rule.json",
                "tickets/jira_remediation_ticket.json",
                "tickets/servicenow_remediation_task.json",
                "audit/operator_approval_event.json",
            ):
                self.assertTrue((out_dir / rel_path).exists(), rel_path)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            validate_integration_export(manifest)

    def test_writer_returns_hashes_for_all_files(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-write-test",
        )
        with tempfile.TemporaryDirectory() as tmp:
            hashes = write_integration_export(export, tmp)
            self.assertEqual(len(hashes), 7)
            self.assertIn("manifest.json", hashes)

    def test_policy_rejects_disallowed_export_kind(self) -> None:
        policy = load_policy(POLICY_PATH)
        policy["allowed_integration_exports"] = [
            item for item in policy["allowed_integration_exports"] if item != "jira_ticket"
        ]
        with self.assertRaises(IntegrationExportError):
            build_integration_export(
                copy.deepcopy(self.bundle),
                generated_at=FIXED_TIME,
                export_id="integration-export-policy-test",
                policy=policy,
            )

    def test_validator_rejects_payload_like_export_text(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-bad-test",
        )
        export["tickets"]["jira_ticket"]["description"] += " ${jndi:blocked}"
        with self.assertRaises(IntegrationExportError):
            validate_integration_export(export)

    def test_validator_rejects_missing_no_live_target_data_assertion(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-bad-attestation",
        )
        export["safety_attestation"]["no_live_target_data_included"] = False
        with self.assertRaisesRegex(
            IntegrationExportError,
            "safety_attestation.no_live_target_data_included must be true",
        ):
            validate_integration_export(export)


if __name__ == "__main__":
    unittest.main()
