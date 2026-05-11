from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from evidence.bundle import build_evidence_bundle, load_json, load_policy
from integrations.export import (
    IntegrationExportError,
    build_integration_export,
    main,
    validate_integration_export,
    write_integration_export,
    write_integration_export_zip,
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
        self.assertIn("review_checklist", export)
        self.assertIn("customer_placeholder_validation", export)
        self.assertIn(
            "Confirm manifest mode is review_template_only.",
            export["review_checklist"]["checks"],
        )
        for field in (
            "reviewer_role",
            "evidence_hash_checked",
            "policy_hash_checked",
            "placeholders_mapped",
            "telemetry_mapping_reviewed",
            "customer_owner_approved",
            "deployment_decision",
        ):
            self.assertIn(field, export["review_checklist"]["signoff_fields"])
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
        placeholder_validation = export["customer_placeholder_validation"]
        self.assertEqual(
            placeholder_validation["schema_version"],
            "prophet.customer_placeholder_validation.v0.1",
        )
        self.assertEqual(placeholder_validation["status"], "customer_mapping_required")
        self.assertTrue(placeholder_validation["review_template_only"])
        placeholder_items = {
            item["file"]: item["placeholders"] for item in placeholder_validation["items"]
        }
        self.assertEqual(
            placeholder_items["siem/splunk_saved_search.json"],
            [
                "<approved_owner_queue>",
                "<customer_security_index>",
                "<edge_or_identity_logs>",
            ],
        )
        self.assertEqual(
            placeholder_items["tickets/jira_remediation_ticket.json"],
            ["<CUSTOMER_PROJECT>"],
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
            zip_path = Path(tmp) / "handoff.zip"
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
                        "--zip-out",
                        str(zip_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            result = json.loads(stdout.getvalue())
            self.assertTrue(result["ok"])
            self.assertIn("zip_sha256", result)
            for rel_path in (
                "manifest.json",
                "siem/splunk_saved_search.json",
                "siem/elastic_detection_rule.ndjson",
                "siem/sentinel_analytic_rule.json",
                "tickets/jira_remediation_ticket.json",
                "tickets/servicenow_remediation_task.json",
                "audit/operator_approval_event.json",
                "review_checklist.md",
            ):
                self.assertTrue((out_dir / rel_path).exists(), rel_path)
            checklist = (out_dir / "review_checklist.md").read_text(encoding="utf-8")
            self.assertIn("Prophet Handoff Review Checklist", checklist)
            self.assertIn("review_template_only", checklist)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            validate_integration_export(manifest)
            with zipfile.ZipFile(zip_path) as archive:
                self.assertIn("prophet-handoff-review-bundle/manifest.json", archive.namelist())
                zipped_manifest = json.loads(
                    archive.read("prophet-handoff-review-bundle/manifest.json")
                )
            validate_integration_export(zipped_manifest)

    def test_writer_returns_hashes_for_all_files(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-write-test",
        )
        with tempfile.TemporaryDirectory() as tmp:
            hashes = write_integration_export(export, tmp)
            self.assertEqual(len(hashes), 8)
            self.assertIn("manifest.json", hashes)
            self.assertIn("review_checklist.md", hashes)

    def test_zip_writer_is_deterministic_and_review_only(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-zip-test",
        )
        with tempfile.TemporaryDirectory() as tmp:
            first_zip = Path(tmp) / "first.zip"
            second_zip = Path(tmp) / "second.zip"
            first_hashes = write_integration_export_zip(export, first_zip)
            second_hashes = write_integration_export_zip(export, second_zip)
            self.assertEqual(first_hashes, second_hashes)
            self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())
            self.assertEqual(len(first_hashes), 8)
            with zipfile.ZipFile(first_zip) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), 8)
                self.assertTrue(
                    all(name.startswith("prophet-handoff-review-bundle/") for name in names)
                )
                self.assertFalse(any("/../" in name or name.startswith("/") for name in names))
                manifest = json.loads(archive.read("prophet-handoff-review-bundle/manifest.json"))
                checklist = archive.read(
                    "prophet-handoff-review-bundle/review_checklist.md"
                ).decode("utf-8")
            validate_integration_export(manifest)
            self.assertEqual(manifest["mode"], "review_template_only")
            self.assertIn("Prophet Handoff Review Checklist", checklist)

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

    def test_validator_rejects_missing_required_review_signoff_field(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-bad-checklist",
        )
        export["review_checklist"]["signoff_fields"].remove("deployment_decision")
        export["hashes"] = {}
        with self.assertRaisesRegex(
            IntegrationExportError,
            "review_checklist.signoff_fields missing required fields",
        ):
            validate_integration_export(export)

    def test_validator_rejects_unlisted_customer_placeholder(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-bad-placeholder",
        )
        export["tickets"]["jira_ticket"]["summary"] += " <customer_change_window>"
        export["hashes"] = {}
        with self.assertRaisesRegex(
            IntegrationExportError,
            "customer_placeholder_validation does not match discovered customer placeholders",
        ):
            validate_integration_export(export)

    def test_validator_rejects_placeholder_inventory_without_customer_action(self) -> None:
        export = build_integration_export(
            copy.deepcopy(self.bundle),
            generated_at=FIXED_TIME,
            export_id="integration-export-bad-placeholder-action",
        )
        export["customer_placeholder_validation"]["items"][0]["required_customer_action"] = ""
        export["hashes"] = {}
        with self.assertRaisesRegex(
            IntegrationExportError,
            "required_customer_action is required",
        ):
            validate_integration_export(export)


if __name__ == "__main__":
    unittest.main()
