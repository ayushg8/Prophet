from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from evidence.bundle import (
    DEFAULT_EVIDENCE_SCHEMA_PATH,
    REQUIRED_SECTIONS,
    RAW_SOURCE_BANNED_KEYS,
    SCHEMA_VERSION,
    EvidenceBundleError,
    EvidenceBundleSchemaError,
    build_evidence_bundle,
    load_json,
    load_policy,
    render_markdown,
    validate_evidence_bundle,
    validate_evidence_bundle_schema,
    validate_pilot_policy,
    write_bundle,
)
from evidence.audit import build_audit_event
from forecaster.generator import assemble_forecast
from sandbox_runner.runner import build_run_manifest, run_profile


ROOT = Path(__file__).resolve().parents[2]
FORECAST_PATH = ROOT / "world-side/outputs/golden-forecast-edge-appliance.json"
FIXTURE_FORECAST_PATH = ROOT / "world-side/outputs/generated-forecast-edge-appliance.json"
PORTFOLIO_PATH = ROOT / "cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json"
ARTIFACT_PATH = ROOT / "cyber-side/fixtures/exploit-engine-output-edge-appliance.json"
DEFENSE_FAILED_ARTIFACT_PATH = (
    ROOT / "cyber-side/fixtures/exploit-engine-output-edge-appliance-defense-failed.json"
)
ASSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-inventory.json"
ASSET_SEEDSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-seedset.json"
EVIDENCE_FIXTURE_PATH = ROOT / "evidence/fixtures/prophet-evidence-edge-appliance.json"
POLICY_PATH = ROOT / "policy/prophet-pilot-policy.json"
FIXTURE_ONLY_POLICY_PATH = ROOT / "policy/examples/fixture-only-policy.json"
LOCALHOST_POLICY_PATH = ROOT / "policy/examples/localhost-sandbox-policy.json"
FIXED_TIME = "2026-05-04T20:00:00Z"


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.forecast = load_json(FORECAST_PATH)
        self.portfolio = load_json(PORTFOLIO_PATH)
        self.artifact = load_json(ARTIFACT_PATH)
        self.asset_inventory = load_json(ASSET_PATH)
        self.asset_seedset = load_json(ASSET_SEEDSET_PATH)
        self.policy = load_policy(POLICY_PATH)

    def build_bundle(self) -> dict:
        return build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-001",
        )

    def test_valid_fixture_bundle_generation(self) -> None:
        bundle = self.build_bundle()
        validate_evidence_bundle(bundle)
        validate_evidence_bundle_schema(bundle)
        self.assertEqual(bundle["schema_version"], "prophet_evidence_bundle.v0.1")
        self.assertEqual(bundle["input_refs"]["forecast_id"], "ws-golden-edge-appliance-001")
        self.assertEqual(bundle["validation_summary"]["post_patch_status"], "blocked")
        self.assertTrue(bundle["safety_attestation"]["no_live_target_data_included"])
        self.assertIn("No live target data is included", bundle["safety_attestation"]["data_boundary_statement"])
        self.assertIn("asset_context", bundle)
        self.assertIn("asset_seed_summary", bundle)
        self.assertIn("open_source_summary", bundle)
        self.assertEqual(bundle["policy"]["policy_id"], "prophet-pilot-fixture-localhost-v0.1")
        self.assertIn("policy_sha256", bundle["hashes"])
        self.assertTrue(bundle["redaction_report"]["summary_fields_only"])
        self.assertFalse(bundle["redaction_report"]["raw_osint_records_embedded"])
        self.assertEqual(
            bundle["redaction_report"]["source_refs_emitted"],
            len(bundle["source_refs"]),
        )

    def test_bundle_includes_local_approval_record_hash(self) -> None:
        approval_record = build_audit_event(
            event_type="operator_approval",
            operator_label="fixture",
            decision="bypassed_for_fixture",
            policy=copy.deepcopy(self.policy),
            generated_at=FIXED_TIME,
            run_id="test-run",
            reason="fixture-approved pilot workflow",
        )
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=copy.deepcopy(self.policy),
            approval_record=approval_record,
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run",
        )
        validate_evidence_bundle(bundle)
        self.assertEqual(
            bundle["operator_approval"]["approval_record_hash"],
            approval_record["event_hash"],
        )
        self.assertEqual(bundle["hashes"]["approval_record_sha256"], approval_record["event_hash"])
        self.assertEqual(bundle["asset_seed_summary"]["cve_seed_count"], 4)

    def test_policy_fixture_validates(self) -> None:
        validate_pilot_policy(self.policy)
        self.assertEqual(self.policy["retention"]["runtime_outputs_max_days"], 30)

    def test_evidence_schema_file_is_published(self) -> None:
        schema = load_json(DEFAULT_EVIDENCE_SCHEMA_PATH)
        self.assertEqual(
            schema["$id"],
            "https://prophet.local/schemas/prophet-evidence-bundle.v0.1.json",
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)

    def test_evidence_schema_version_contract_matches_runtime_validator(self) -> None:
        schema = load_json(DEFAULT_EVIDENCE_SCHEMA_PATH)
        self.assertEqual(SCHEMA_VERSION, "prophet_evidence_bundle.v0.1")
        self.assertEqual(schema["required"], list(REQUIRED_SECTIONS))
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, schema["properties"])
        vector_schema = schema["properties"]["forecast_summary"]["properties"]["vector"]
        self.assertIn("why_this_vector", vector_schema["required"])
        self.assertIn("why_this_vector", vector_schema["properties"])

        bundle = self.build_bundle()
        self.assertEqual(bundle["schema_version"], SCHEMA_VERSION)
        validate_evidence_bundle_schema(bundle)

    def test_evidence_schema_requires_vector_rationale(self) -> None:
        bundle = self.build_bundle()
        del bundle["forecast_summary"]["vector"]["why_this_vector"]

        with self.assertRaisesRegex(
            EvidenceBundleSchemaError,
            "missing required.*why_this_vector",
        ):
            validate_evidence_bundle_schema(bundle)

    def test_published_evidence_fixture_validates_current_schema_version(self) -> None:
        bundle = load_json(EVIDENCE_FIXTURE_PATH)
        self.assertEqual(bundle["schema_version"], SCHEMA_VERSION)
        validate_evidence_bundle_schema(bundle)
        validate_evidence_bundle(bundle)

    def test_evidence_schema_rejects_unsupported_schema_versions(self) -> None:
        for unsupported_version in (
            "prophet_evidence_bundle.v0.0",
            "prophet_evidence_bundle.v0.2",
            "prophet_evidence_bundle.v1.0",
        ):
            with self.subTest(schema_version=unsupported_version):
                bundle = self.build_bundle()
                bundle["schema_version"] = unsupported_version

                with self.assertRaisesRegex(
                    EvidenceBundleSchemaError,
                    "must equal 'prophet_evidence_bundle.v0.1'",
                ):
                    validate_evidence_bundle_schema(bundle)

                with self.assertRaisesRegex(
                    EvidenceBundleError,
                    "schema_version must be prophet_evidence_bundle.v0.1",
                ):
                    validate_evidence_bundle(bundle)

    def test_evidence_schema_rejects_unknown_top_level_field(self) -> None:
        bundle = self.build_bundle()
        bundle["unexpected_runtime_blob"] = {"raw": "not part of the public contract"}
        with self.assertRaisesRegex(EvidenceBundleSchemaError, "unknown fields"):
            validate_evidence_bundle_schema(bundle)

    def test_evidence_schema_rejects_missing_required_attestation(self) -> None:
        bundle = self.build_bundle()
        del bundle["safety_attestation"]["no_private_hostnames"]
        with self.assertRaisesRegex(EvidenceBundleSchemaError, "missing required"):
            validate_evidence_bundle_schema(bundle)

    def test_policy_examples_support_narrow_modes(self) -> None:
        validate_pilot_policy(load_policy(FIXTURE_ONLY_POLICY_PATH))
        validate_pilot_policy(load_policy(LOCALHOST_POLICY_PATH))

    def test_fixture_only_policy_allows_fixture_forecast_and_artifact(self) -> None:
        fixture_only_policy = load_policy(FIXTURE_ONLY_POLICY_PATH)
        bundle = build_evidence_bundle(
            forecast=load_json(FIXTURE_FORECAST_PATH),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            policy=fixture_only_policy,
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-fixture-only-policy",
        )
        self.assertEqual(bundle["policy"]["policy_id"], "prophet-pilot-fixture-only-v0.1")
        self.assertEqual(bundle["policy"]["retention"]["runtime_outputs_max_days"], 7)

    def test_fixture_only_policy_rejects_seeded_osint_forecast(self) -> None:
        fixture_only_policy = load_policy(FIXTURE_ONLY_POLICY_PATH)
        with self.assertRaisesRegex(EvidenceBundleError, "seeded_osint"):
            build_evidence_bundle(
                forecast=copy.deepcopy(self.forecast),
                portfolio=copy.deepcopy(self.portfolio),
                artifact=copy.deepcopy(self.artifact),
                policy=fixture_only_policy,
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
                run_id="test-run-seeded-rejected",
            )

    def test_localhost_policy_allows_sandbox_runner_artifact(self) -> None:
        localhost_policy = load_policy(LOCALHOST_POLICY_PATH)
        sandbox_artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="test-localhost-policy",
            policy=LOCALHOST_POLICY_PATH,
        )
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=sandbox_artifact,
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=localhost_policy,
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-localhost-policy",
        )
        self.assertEqual(bundle["policy"]["policy_id"], "prophet-pilot-localhost-sandbox-v0.1")

    def test_bundle_includes_sandbox_run_manifest_provenance(self) -> None:
        localhost_policy = load_policy(LOCALHOST_POLICY_PATH)
        sandbox_artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="test-sandbox-provenance",
            policy=LOCALHOST_POLICY_PATH,
        )
        manifest = build_run_manifest(
            artifact=sandbox_artifact,
            profile="edge-appliance-fixture",
            artifact_path="cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json",
        )
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=sandbox_artifact,
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=localhost_policy,
            sandbox_run_manifest=manifest,
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-sandbox-provenance",
        )

        validate_evidence_bundle(bundle)
        validate_evidence_bundle_schema(bundle)
        provenance = bundle["sandbox_provenance"]
        self.assertEqual(provenance["profile"], "edge-appliance-fixture")
        self.assertEqual(provenance["mode"], "fixture")
        self.assertEqual(provenance["artifact_id"], sandbox_artifact["artifact_id"])
        self.assertEqual(
            provenance["artifact_content_sha256"],
            manifest["artifact"]["content_sha256"],
        )
        self.assertEqual(
            bundle["hashes"]["sandbox_run_manifest_sha256"],
            provenance["manifest_sha256"],
        )
        self.assertFalse(provenance["raw_logs_retained"])
        self.assertTrue(provenance["no_network_egress"])
        self.assertTrue(bundle["redaction_report"]["sandbox_run_manifest_embedded"])
        markdown = render_markdown(bundle)
        self.assertIn("## Sandbox Provenance", markdown)
        self.assertIn("No network egress: `true`", markdown)
        self.assertIn("Sandbox run manifest SHA-256", markdown)

    def test_bundle_rejects_mismatched_sandbox_run_manifest(self) -> None:
        localhost_policy = load_policy(LOCALHOST_POLICY_PATH)
        sandbox_artifact = run_profile(
            profile="edge-appliance-fixture",
            generated_at=FIXED_TIME,
            run_id="test-sandbox-provenance-mismatch",
            policy=LOCALHOST_POLICY_PATH,
        )
        manifest = build_run_manifest(
            artifact=sandbox_artifact,
            profile="edge-appliance-fixture",
            artifact_path="cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json",
        )
        manifest["artifact"]["content_sha256"] = "0" * 64

        with self.assertRaisesRegex(EvidenceBundleError, "content_sha256"):
            build_evidence_bundle(
                forecast=copy.deepcopy(self.forecast),
                portfolio=copy.deepcopy(self.portfolio),
                artifact=sandbox_artifact,
                asset_inventory=copy.deepcopy(self.asset_inventory),
                asset_seedset=copy.deepcopy(self.asset_seedset),
                policy=localhost_policy,
                sandbox_run_manifest=manifest,
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
                run_id="test-run-sandbox-provenance-mismatch",
            )

    def test_failed_sandbox_validation_is_explicit_in_evidence(self) -> None:
        failed_artifact = load_json(DEFENSE_FAILED_ARTIFACT_PATH)
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=failed_artifact,
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-defense-failed",
        )
        failure = bundle["validation_summary"]["failure_evidence"]
        self.assertEqual(bundle["validation_summary"]["post_patch_status"], "vulnerable")
        self.assertEqual(failure["result"], "failed")
        self.assertEqual(failure["failure_kind"], "defense_not_blocked")
        self.assertTrue(failure["failure_detected"])
        self.assertFalse(failure["timeout_observed"])
        validate_evidence_bundle_schema(bundle)
        markdown = render_markdown(bundle)
        self.assertIn("Failure kind: `defense_not_blocked`", markdown)
        self.assertIn("Do not present the defense as effective", markdown)

    def test_timeout_sandbox_validation_is_explicit_in_evidence(self) -> None:
        timeout_artifact = copy.deepcopy(self.artifact)
        timeout_artifact["validation"]["post_patch_status"] = "error"
        timeout_artifact["validation"][
            "post_patch_excerpt"
        ] = "deterministic fixture validation timed out before post-patch verdict"
        timeout_artifact["validation"]["timeout_seconds"] = 30
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=timeout_artifact,
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-validation-timeout",
        )
        failure = bundle["validation_summary"]["failure_evidence"]
        self.assertEqual(failure["result"], "timeout")
        self.assertEqual(failure["failure_kind"], "timeout")
        self.assertTrue(failure["failure_detected"])
        self.assertTrue(failure["timeout_observed"])
        self.assertEqual(failure["timeout_seconds"], 30)
        validate_evidence_bundle_schema(bundle)
        markdown = render_markdown(bundle)
        self.assertIn("Result: `timeout`", markdown)
        self.assertIn("Timeout seconds: 30", markdown)

    def test_cli_writes_json_and_markdown(self) -> None:
        from evidence.bundle import main

        runtime_root = ROOT / "evidence/outputs/runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="bundle-cli-test-", dir=runtime_root) as tmp:
            out_json = Path(tmp) / "bundle.json"
            out_md = Path(tmp) / "bundle.md"
            exit_code = main(
                [
                    "--forecast",
                    str(FORECAST_PATH),
                    "--portfolio",
                    str(PORTFOLIO_PATH),
                    "--artifact",
                    str(ARTIFACT_PATH),
                    "--asset-inventory",
                    str(ASSET_PATH),
                    "--asset-seedset",
                    str(ASSET_SEEDSET_PATH),
                    "--policy",
                    str(POLICY_PATH),
                    "--operator-label",
                    "fixture",
                    "--approval-decision",
                    "bypassed_for_fixture",
                    "--generated-at",
                    FIXED_TIME,
                    "--run-id",
                    "cli-test-run",
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

    def test_write_bundle_rejects_non_runtime_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "bundle.json"
            with self.assertRaisesRegex(EvidenceBundleError, "evidence/outputs/runtime"):
                write_bundle(self.build_bundle(), out_json=out_json)

    def test_write_bundle_rejects_unexpected_output_suffix(self) -> None:
        runtime_root = ROOT / "evidence/outputs/runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="bundle-suffix-test-", dir=runtime_root) as tmp:
            out_json = Path(tmp) / "bundle.txt"
            with self.assertRaisesRegex(EvidenceBundleError, r"\.json"):
                write_bundle(self.build_bundle(), out_json=out_json)

    def test_deterministic_hash_stability_with_fixed_time(self) -> None:
        first = self.build_bundle()
        second = self.build_bundle()
        self.assertEqual(first["bundle_id"], second["bundle_id"])
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])

    def test_markdown_contains_required_sections(self) -> None:
        bundle = self.build_bundle()
        markdown = render_markdown(bundle)
        for section in (
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
        ):
            self.assertIn(f"## {section}", markdown)
        self.assertIn("why_this_vector", bundle["forecast_summary"]["vector"])
        self.assertIn("- Why this window:", markdown)
        self.assertIn("- Why this vector:", markdown)
        self.assertIn("- Cited forecast source IDs:", markdown)

    def test_open_source_snapshot_summary_in_evidence(self) -> None:
        candidate = load_json(ROOT / "world-side/fixtures/exploit-candidate-edge-appliance.json")
        forecast = assemble_forecast(
            candidate,
            generated_at="2026-05-02T23:45:00Z",
            osint_snapshot_paths=[ROOT / "world-side/fixtures/osint-snapshot-sample.jsonl"],
            osint_manifest_paths=[ROOT / "world-side/fixtures/osint-snapshot-sample.manifest.json"],
            asset_seedset_paths=[ASSET_SEEDSET_PATH],
        )
        bundle = build_evidence_bundle(
            forecast=forecast,
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-osint-001",
        )
        self.assertTrue(bundle["open_source_summary"]["integrated"])
        self.assertEqual(bundle["open_source_summary"]["record_count"], 4)
        self.assertEqual(bundle["open_source_summary"]["freshness"]["status"], "current")
        self.assertEqual(bundle["open_source_summary"]["freshness"]["newest_record_age_days"], 2.32)
        self.assertEqual(bundle["open_source_summary"]["freshness"]["record_span_days"], 0.01)
        self.assertEqual(bundle["open_source_summary"]["source_health"]["status"], "ok")
        self.assertEqual(bundle["open_source_summary"]["source_health"]["failed_source_count"], 0)
        self.assertEqual(bundle["open_source_summary"]["source_failures"], [])
        self.assertIn("osint_snapshot_hashes", bundle["hashes"])
        self.assertIn("asset_seedset_sha256", bundle["hashes"])
        self.assertEqual(bundle["asset_seed_summary"]["package_seed_count"], 6)
        markdown = render_markdown(bundle)
        self.assertIn("## Open Source Basis", markdown)
        self.assertIn("## Policy Controls", markdown)
        self.assertIn("## Asset/SBOM Seeds", markdown)
        self.assertIn("Sanitized record count: 4", markdown)
        self.assertIn("## Source Freshness And Failures", markdown)
        self.assertIn("Source failures: none", markdown)

    def test_open_source_failure_summary_in_evidence(self) -> None:
        forecast = copy.deepcopy(self.forecast)
        forecast["open_source_signals"]["source_health"] = {
            "status": "degraded",
            "manifest_count": 1,
            "successful_source_count": 1,
            "failed_source_count": 1,
            "failure_policy": "Failed sources are summarized; raw collection text remains excluded.",
        }
        forecast["open_source_signals"]["source_failures"] = [
            {
                "source_id": "seeded_fixture_missing",
                "status": "error",
                "collector": "sanitized_json",
                "source_type": "threat_intel_feed",
                "collection_tier": "technical_chatter",
                "records": 0,
                "error": "fixture metadata unavailable",
            }
        ]
        forecast["open_source_signals"]["failed_sources"] = ["seeded_fixture_missing"]
        bundle = build_evidence_bundle(
            forecast=forecast,
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-osint-failure-001",
        )
        self.assertEqual(bundle["open_source_summary"]["source_health"]["status"], "degraded")
        self.assertEqual(len(bundle["open_source_summary"]["source_failures"]), 1)
        markdown = render_markdown(bundle)
        self.assertIn("seeded_fixture_missing (error): fixture metadata unavailable", markdown)

    def test_open_source_duplicate_sources_are_collapsed_in_evidence(self) -> None:
        forecast = copy.deepcopy(self.forecast)
        signals = forecast["open_source_signals"]
        signals["successful_sources"] = [
            "osint_snapshot_fixture_input",
            "osint_snapshot_fixture_input",
            "cisa_vulnrichment_cve_record_seed",
        ]
        signals["failed_sources"] = ["osv_query_api_seed", "osv_query_api_seed"]
        signals["source_ref_ids"] = [
            "src_context_osint_snapshot",
            "src_context_osint_snapshot",
            "src_osint_cvelistv5_delta_fixture",
        ]
        signals["snapshot_paths"] = [
            "world-side/fixtures/osint-snapshot-sample.jsonl",
            "world-side/fixtures/osint-snapshot-sample.jsonl",
        ]
        signals["manifest_paths"] = [
            "world-side/fixtures/osint-snapshot-sample.manifest.json",
            "world-side/fixtures/osint-snapshot-sample.manifest.json",
        ]
        signals["source_failures"] = [
            {
                "source_id": "osv_query_api_seed",
                "status": "error",
                "collector": "sanitized_json",
                "source_type": "threat_intel_feed",
                "collection_tier": "technical_chatter",
                "records": 0,
                "error": "fixture metadata unavailable",
            },
            {
                "source_id": "osv_query_api_seed",
                "status": "error",
                "collector": "sanitized_json",
                "source_type": "threat_intel_feed",
                "collection_tier": "technical_chatter",
                "records": 0,
                "error": "fixture metadata unavailable",
            },
        ]
        bundle = build_evidence_bundle(
            forecast=forecast,
            portfolio=copy.deepcopy(self.portfolio),
            artifact=copy.deepcopy(self.artifact),
            asset_inventory=copy.deepcopy(self.asset_inventory),
            asset_seedset=copy.deepcopy(self.asset_seedset),
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-osint-duplicates-001",
        )
        summary = bundle["open_source_summary"]
        self.assertEqual(
            summary["successful_sources"],
            ["osint_snapshot_fixture_input", "cisa_vulnrichment_cve_record_seed"],
        )
        self.assertEqual(summary["failed_sources"], ["osv_query_api_seed"])
        self.assertEqual(
            summary["source_ref_ids"],
            ["src_context_osint_snapshot", "src_osint_cvelistv5_delta_fixture"],
        )
        self.assertEqual(len(summary["source_failures"]), 1)
        self.assertEqual(summary["duplicate_source_summary"]["collapsed_duplicate_count"], 6)
        self.assertEqual(summary["duplicate_source_summary"]["duplicate_path_count"], 2)
        self.assertEqual(
            summary["duplicate_source_summary"]["duplicate_source_ids"],
            [
                "osint_snapshot_fixture_input",
                "osv_query_api_seed",
                "src_context_osint_snapshot",
            ],
        )
        validate_evidence_bundle_schema(bundle)
        markdown = render_markdown(bundle)
        self.assertIn("Duplicate source collapse: 6 duplicate mention(s) collapsed", markdown)

    def test_policy_blocks_live_validation_scope(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["validation"]["scope"] = "approved external range"
        with self.assertRaises(Exception):
            build_evidence_bundle(
                forecast=self.forecast,
                portfolio=self.portfolio,
                artifact=artifact,
                policy=copy.deepcopy(self.policy),
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
            )

    def test_validator_rejects_missing_validation_section(self) -> None:
        bundle = self.build_bundle()
        del bundle["validation_summary"]
        with self.assertRaises(EvidenceBundleError):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_non_localhost_scope_without_fixture(self) -> None:
        bundle = self.build_bundle()
        bundle["validation_summary"]["sandbox_scope"] = "approved external range"
        bundle["safety_attestation"]["validation_scope"] = "approved external range"
        bundle["safety_attestation"]["fixture_backed"] = False
        bundle["operator_approval"]["approval_mode"] = "human_gate"
        bundle["hashes"]["bundle_body_sha256"] = ""
        with self.assertRaises(EvidenceBundleError):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_failed_validation_without_failure_evidence(self) -> None:
        bundle = build_evidence_bundle(
            forecast=copy.deepcopy(self.forecast),
            portfolio=copy.deepcopy(self.portfolio),
            artifact=load_json(DEFENSE_FAILED_ARTIFACT_PATH),
            policy=copy.deepcopy(self.policy),
            operator_label="fixture",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="test-run-missing-failure-evidence",
        )
        del bundle["validation_summary"]["failure_evidence"]
        with self.assertRaisesRegex(EvidenceBundleError, "failure_evidence"):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_banned_payload_key(self) -> None:
        bundle = self.build_bundle()
        bundle["payload"] = "not allowed"
        with self.assertRaises(EvidenceBundleError):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_raw_scraper_text_key(self) -> None:
        for key in sorted(RAW_SOURCE_BANNED_KEYS):
            with self.subTest(key=key):
                bundle = self.build_bundle()
                bundle["open_source_summary"][key] = "unredacted scraper content"

                with self.assertRaisesRegex(EvidenceBundleError, "banned key"):
                    validate_evidence_bundle(bundle)

    def test_validator_rejects_raw_scraper_text_marker(self) -> None:
        bundle = self.build_bundle()
        bundle["open_source_summary"][
            "basis_statement"
        ] = "RAW SCRAPER ARTIFACT: unredacted post body copied from collection."

        with self.assertRaisesRegex(EvidenceBundleError, "raw source marker"):
            validate_evidence_bundle(bundle)

    def test_generated_bundle_contains_no_raw_scraper_text_fields(self) -> None:
        bundle = self.build_bundle()
        validate_evidence_bundle(bundle)
        self.assertFalse(_contains_any_key(bundle, RAW_SOURCE_BANNED_KEYS))
        self.assertFalse(bundle["redaction_report"]["raw_osint_records_embedded"])
        self.assertFalse(bundle["redaction_report"]["source_documents_embedded"])
        self.assertTrue(bundle["safety_attestation"]["no_raw_scraper_text"])

        markdown = render_markdown(bundle)
        self.assertNotIn("RAW SCRAPER ARTIFACT:", markdown)
        self.assertIn("Blocked text classes:", markdown)
        self.assertIn("raw scraper text", markdown)

    def test_validator_rejects_missing_no_live_target_data_assertion(self) -> None:
        bundle = self.build_bundle()
        bundle["safety_attestation"]["no_live_target_data_included"] = False
        with self.assertRaisesRegex(
            EvidenceBundleError,
            "safety_attestation.no_live_target_data_included must be true",
        ):
            validate_evidence_bundle(bundle)

    def test_markdown_renders_no_live_target_data_assertion(self) -> None:
        markdown = render_markdown(self.build_bundle())
        self.assertIn("No live target data included: `true`", markdown)
        self.assertIn("No live target data is included", markdown)

    def test_markdown_contains_ciso_review_summary_table(self) -> None:
        markdown = render_markdown(self.build_bundle())
        self.assertIn("| Review area | Evidence in this bundle |", markdown)
        self.assertIn("| Defensive result | Pre-patch `vulnerable`; post-patch `blocked` |", markdown)
        self.assertIn("| Safety boundary | No live targets: `true`; no live target data included: `true` |", markdown)
        self.assertIn("| Policy and approval | Policy `prophet-pilot-fixture-localhost-v0.1`;", markdown)
        self.assertIn("| Redaction | Summary fields only: `true`;", markdown)
        self.assertIn("| Integrity proof | Bundle SHA-256 `", markdown)

    def test_validator_requires_evidence_redaction_report(self) -> None:
        bundle = self.build_bundle()
        del bundle["redaction_report"]
        with self.assertRaisesRegex(EvidenceBundleError, "missing sections"):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_evidence_redaction_raw_embedded_flag(self) -> None:
        bundle = self.build_bundle()
        bundle["redaction_report"]["raw_validation_logs_embedded"] = True
        bundle["hashes"]["bundle_body_sha256"] = ""
        with self.assertRaisesRegex(
            EvidenceBundleError,
            "redaction_report.raw_validation_logs_embedded must be false",
        ):
            validate_evidence_bundle(bundle)

    def test_validator_rejects_redaction_source_ref_count_drift(self) -> None:
        bundle = self.build_bundle()
        bundle["redaction_report"]["source_refs_emitted"] = 999
        bundle["hashes"]["bundle_body_sha256"] = ""
        with self.assertRaisesRegex(
            EvidenceBundleError,
            "redaction_report.source_refs_emitted does not match source_refs",
        ):
            validate_evidence_bundle(bundle)

    def test_direction_c_artifact_must_pass_existing_validator(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        del artifact["validation"]
        with self.assertRaises(Exception):
            build_evidence_bundle(
                forecast=self.forecast,
                portfolio=self.portfolio,
                artifact=artifact,
                policy=copy.deepcopy(self.policy),
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
            )

    def test_portfolio_rejects_payload_like_text(self) -> None:
        portfolio = copy.deepcopy(self.portfolio)
        portfolio["zero_day_predictions"][0]["non_actionable_rationale"] += " ${jndi:blocked}"
        with self.assertRaises(Exception):
            build_evidence_bundle(
                forecast=self.forecast,
                portfolio=portfolio,
                artifact=self.artifact,
                policy=copy.deepcopy(self.policy),
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
            )

    def test_asset_seedset_rejects_live_hostname_text(self) -> None:
        seedset = copy.deepcopy(self.asset_seedset)
        seedset["scope_statement"] = "prod-edge.example.com"
        with self.assertRaises(Exception):
            build_evidence_bundle(
                forecast=self.forecast,
                portfolio=self.portfolio,
                artifact=self.artifact,
                asset_seedset=seedset,
                policy=copy.deepcopy(self.policy),
                operator_label="fixture",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
            )

def _contains_any_key(value: object, keys: set[str]) -> bool:
    if isinstance(value, dict):
        for key, inner in value.items():
            if str(key).lower() in keys or _contains_any_key(inner, keys):
                return True
    if isinstance(value, list):
        return any(_contains_any_key(item, keys) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
