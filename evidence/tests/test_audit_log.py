from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from evidence.audit import (
    AuditLogError,
    append_audit_event,
    build_audit_event,
    validate_audit_log,
)
from evidence.bundle import (
    EvidenceBundleError,
    build_evidence_bundle,
    load_json,
    load_policy,
    validate_evidence_bundle,
)


ROOT = Path(__file__).resolve().parents[2]
FORECAST_PATH = ROOT / "world-side/outputs/golden-forecast-edge-appliance.json"
PORTFOLIO_PATH = ROOT / "cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json"
ARTIFACT_PATH = ROOT / "cyber-side/fixtures/exploit-engine-output-edge-appliance.json"
ASSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-inventory.json"
ASSET_SEEDSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-seedset.json"
POLICY_PATH = ROOT / "policy/prophet-pilot-policy.json"
FIXED_TIME = "2026-05-05T05:00:00Z"


class AuditLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy(POLICY_PATH)

    def test_append_audit_events_hash_chains_local_runtime_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "outputs/runtime/operator-audit-log.jsonl"
            first = append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=copy.deepcopy(self.policy),
                generated_at=FIXED_TIME,
                run_id="audit-chain-test",
                reason="fixture-approved console evidence generation",
            )
            second = append_audit_event(
                log,
                event_type="integration_handoff_exported",
                operator_label="local-console",
                decision="integration_handoff_exported",
                policy=copy.deepcopy(self.policy),
                generated_at="2026-05-05T05:01:00Z",
                run_id="audit-chain-test",
                bundle_id="peb-audit-test",
                bundle_sha256="a" * 64,
                export_id="integration-export-test",
                reason="policy-approved console integration handoff export",
            )

            summary = validate_audit_log(log)
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(
                second["chain"]["previous_event_hash"],
                first["event_hash"],
            )
            self.assertEqual(summary["latest_event_hash"], second["event_hash"])

    def test_audit_event_rejects_unsafe_operator_label(self) -> None:
        with self.assertRaises(AuditLogError):
            build_audit_event(
                event_type="operator_approval",
                operator_label="operator.prod.example.com",
                decision="bypassed_for_fixture",
                policy=copy.deepcopy(self.policy),
                generated_at=FIXED_TIME,
            )

    def test_evidence_bundle_carries_approval_record_hash(self) -> None:
        approval = build_audit_event(
            event_type="operator_approval",
            operator_label="local-console",
            decision="bypassed_for_fixture",
            policy=copy.deepcopy(self.policy),
            generated_at=FIXED_TIME,
            run_id="evidence-approval-record-test",
            reason="fixture-approved console evidence generation",
        )
        bundle = build_evidence_bundle(
            forecast=load_json(FORECAST_PATH),
            portfolio=load_json(PORTFOLIO_PATH),
            artifact=load_json(ARTIFACT_PATH),
            asset_inventory=load_json(ASSET_PATH),
            asset_seedset=load_json(ASSET_SEEDSET_PATH),
            policy=copy.deepcopy(self.policy),
            approval_record=approval,
            operator_label="local-console",
            approval_decision="bypassed_for_fixture",
            generated_at=FIXED_TIME,
            run_id="evidence-approval-record-test",
        )

        validate_evidence_bundle(bundle)
        self.assertEqual(
            bundle["operator_approval"]["approval_record_hash"],
            approval["event_hash"],
        )
        self.assertEqual(
            bundle["hashes"]["approval_record_sha256"],
            approval["event_hash"],
        )

    def test_evidence_rejects_mismatched_approval_record(self) -> None:
        approval = build_audit_event(
            event_type="operator_approval",
            operator_label="local-console",
            decision="bypassed_for_fixture",
            policy=copy.deepcopy(self.policy),
            generated_at=FIXED_TIME,
        )
        with self.assertRaises(EvidenceBundleError):
            build_evidence_bundle(
                forecast=load_json(FORECAST_PATH),
                portfolio=load_json(PORTFOLIO_PATH),
                artifact=load_json(ARTIFACT_PATH),
                policy=copy.deepcopy(self.policy),
                approval_record=approval,
                operator_label="different-operator",
                approval_decision="bypassed_for_fixture",
                generated_at=FIXED_TIME,
            )


if __name__ == "__main__":
    unittest.main()
