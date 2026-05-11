from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evidence.audit import (
    AuditLogError,
    append_audit_event,
    audit_event_body_hash,
    audit_export_body_hash,
    audit_retention_report,
    audit_retention_body_hash,
    build_audit_event,
    export_audit_log,
    validate_audit_event,
    validate_audit_export,
    validate_audit_log,
    validate_audit_retention_report,
)
from evidence.bundle import load_policy


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy/prophet-pilot-policy.json"
FIXED_TIME = "2026-05-05T05:00:00Z"


class AuditLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy(POLICY_PATH)

    def test_builds_safe_hash_chained_audit_event(self) -> None:
        event = build_audit_event(
            event_type="operator_approval",
            operator_label="local-console",
            decision="bypassed_for_fixture",
            policy=self.policy,
            generated_at=FIXED_TIME,
            run_id="audit-unit-test",
            reason="fixture-approved pilot workflow",
        )
        validate_audit_event(event)
        self.assertRegex(event["event_hash"], r"^[0-9a-f]{64}$")
        self.assertIsNone(event["chain"]["previous_event_hash"])
        self.assertTrue(event["safety_attestation"]["no_live_target_data_included"])

    def test_audit_event_rejects_missing_no_live_target_data_assertion(self) -> None:
        event = build_audit_event(
            event_type="operator_approval",
            operator_label="local-console",
            decision="bypassed_for_fixture",
            policy=self.policy,
            generated_at=FIXED_TIME,
            run_id="audit-unit-test",
            reason="fixture-approved pilot workflow",
        )
        event["safety_attestation"]["no_live_target_data_included"] = False
        event["chain"]["event_body_sha256"] = audit_event_body_hash(event)
        event["event_hash"] = audit_event_body_hash(event)
        with self.assertRaisesRegex(
            AuditLogError,
            "safety_attestation.no_live_target_data_included must be true",
        ):
            validate_audit_event(event)

    def test_append_validates_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            first = append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-unit-test-1",
            )
            second = append_audit_event(
                log,
                event_type="integration_handoff_exported",
                operator_label="local-console",
                decision="integration_handoff_exported",
                policy=self.policy,
                generated_at="2026-05-05T05:01:00Z",
                run_id="audit-unit-test-2",
                export_id="integration-export-test",
            )
            summary = validate_audit_log(log)
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(second["chain"]["previous_event_hash"], first["event_hash"])

    def test_rejects_unsafe_operator_label(self) -> None:
        with self.assertRaises(AuditLogError):
            build_audit_event(
                event_type="operator_approval",
                operator_label="prod-edge.example.com",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
            )

    def test_rejects_email_shaped_operator_label(self) -> None:
        with self.assertRaises(AuditLogError):
            build_audit_event(
                event_type="operator_approval",
                operator_label="analyst@example.com",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
            )

    def test_cli_append_writes_event_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            event_path = Path(tmp) / "evidence/outputs/runtime/event.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "evidence.audit",
                    "append",
                    "--log",
                    str(log),
                    "--policy",
                    str(POLICY_PATH),
                    "--event-type",
                    "operator_approval",
                    "--operator-label",
                    "local-console",
                    "--decision",
                    "bypassed_for_fixture",
                    "--generated-at",
                    FIXED_TIME,
                    "--run-id",
                    "audit-cli-test",
                    "--out-event",
                    str(event_path),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": f"{ROOT}:{ROOT / 'cyber-side'}:{ROOT / 'world-side'}"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            validate_audit_event(json.loads(event_path.read_text(encoding="utf-8")))
            self.assertEqual(validate_audit_log(log)["event_count"], 1)

    def test_export_audit_log_summarizes_safe_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            first = append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-export-test-1",
            )
            second = append_audit_event(
                log,
                event_type="integration_handoff_exported",
                operator_label="local-console",
                decision="integration_handoff_exported",
                policy=self.policy,
                generated_at="2026-05-05T05:01:00Z",
                run_id="audit-export-test-2",
                export_id="integration-export-test",
            )

            exported = export_audit_log(log, generated_at="2026-05-05T05:02:00Z")
            validate_audit_export(exported)
            self.assertEqual(exported["event_count"], 2)
            self.assertEqual(exported["first_event_hash"], first["event_hash"])
            self.assertEqual(exported["latest_event_hash"], second["event_hash"])
            self.assertEqual(exported["event_type_counts"]["operator_approval"], 1)
            self.assertEqual(exported["decision_counts"]["integration_handoff_exported"], 1)
            self.assertEqual(exported["operator_labels"], ["local-console"])
            self.assertEqual(exported["policy_ids"], ["prophet-pilot-fixture-localhost-v0.1"])
            self.assertTrue(exported["redaction_report"]["summary_fields_only"])
            self.assertFalse(exported["redaction_report"]["source_log_embedded"])
            self.assertFalse(exported["redaction_report"]["raw_event_bodies_embedded"])
            self.assertEqual(exported["redaction_report"]["event_summaries_emitted"], 2)
            self.assertIn("event_hash", exported["redaction_report"]["field_allowlist"])
            self.assertIn("raw collection text", exported["redaction_report"]["redacted_fields"])
            self.assertIn(
                "secret-like text",
                exported["redaction_report"]["blocked_text_classes"],
            )
            self.assertRegex(exported["source_log_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(exported["export_body_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(exported["safety_attestation"]["no_live_target_data_included"])

    def test_audit_export_requires_redaction_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-export-redaction-required-test",
            )
            exported = export_audit_log(log, generated_at="2026-05-05T05:02:00Z")
            exported.pop("redaction_report")
            exported["export_body_sha256"] = audit_export_body_hash(exported)
            with self.assertRaisesRegex(
                AuditLogError,
                "audit export redaction_report is required",
            ):
                validate_audit_export(exported)

    def test_audit_export_rejects_raw_event_body_embedding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-export-raw-event-body-test",
            )
            exported = export_audit_log(log, generated_at="2026-05-05T05:02:00Z")
            exported["redaction_report"]["raw_event_bodies_embedded"] = True
            exported["export_body_sha256"] = audit_export_body_hash(exported)
            with self.assertRaisesRegex(
                AuditLogError,
                "audit export redaction_report.raw_event_bodies_embedded must be false",
            ):
                validate_audit_export(exported)

    def test_audit_export_rejects_missing_no_live_target_data_assertion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-export-bad-attestation-test",
            )
            exported = export_audit_log(log, generated_at="2026-05-05T05:02:00Z")
            exported["safety_attestation"]["no_live_target_data_included"] = False
            exported["export_body_sha256"] = audit_export_body_hash(exported)
            with self.assertRaisesRegex(
                AuditLogError,
                "safety_attestation.no_live_target_data_included must be true",
            ):
                validate_audit_export(exported)

    def test_cli_export_writes_summary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            out = Path(tmp) / "evidence/outputs/runtime/audit-export.json"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-export-cli-test",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "evidence.audit",
                    "export",
                    "--log",
                    str(log),
                    "--generated-at",
                    "2026-05-05T05:03:00Z",
                    "--out-json",
                    str(out),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": f"{ROOT}:{ROOT / 'cyber-side'}:{ROOT / 'world-side'}"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            exported = json.loads(out.read_text(encoding="utf-8"))
            validate_audit_export(exported)
            self.assertEqual(exported["event_count"], 1)

    def test_retention_report_keeps_active_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-retention-active-test",
            )

            report = audit_retention_report(
                log,
                policy=self.policy,
                generated_at="2026-05-05T06:00:00Z",
            )
            validate_audit_retention_report(report)
            self.assertEqual(report["retention"]["event_count"], 1)
            self.assertEqual(report["retention"]["expired_event_count"], 0)
            self.assertFalse(report["cleanup"]["eligible"])
            self.assertFalse(report["cleanup"]["deleted"])
            self.assertTrue(report["safety_attestation"]["no_live_target_data_included"])
            self.assertTrue(log.exists())

    def test_audit_retention_rejects_missing_no_live_target_data_assertion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-retention-bad-attestation-test",
            )
            report = audit_retention_report(
                log,
                policy=self.policy,
                generated_at="2026-05-05T06:00:00Z",
            )
            report["safety_attestation"]["no_live_target_data_included"] = False
            report["retention_body_sha256"] = audit_retention_body_hash(report)
            with self.assertRaisesRegex(
                AuditLogError,
                "safety_attestation.no_live_target_data_included must be true",
            ):
                validate_audit_retention_report(report)

    def test_retention_cleanup_deletes_only_confirmed_expired_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at="2026-01-01T00:00:00Z",
                run_id="audit-retention-expired-test",
            )

            with self.assertRaises(AuditLogError):
                audit_retention_report(
                    log,
                    policy=self.policy,
                    generated_at="2026-05-05T06:00:00Z",
                    delete_expired_log=True,
                )

            report = audit_retention_report(
                log,
                policy=self.policy,
                generated_at="2026-05-05T06:00:00Z",
                delete_expired_log=True,
                confirm_retention_delete=True,
            )
            validate_audit_retention_report(report)
            self.assertEqual(report["retention"]["expired_event_count"], 1)
            self.assertTrue(report["cleanup"]["eligible"])
            self.assertTrue(report["cleanup"]["deleted"])
            self.assertFalse(log.exists())

    def test_cli_retention_writes_report_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "evidence/outputs/runtime/audit.jsonl"
            out = Path(tmp) / "evidence/outputs/runtime/audit-retention.json"
            append_audit_event(
                log,
                event_type="operator_approval",
                operator_label="local-console",
                decision="bypassed_for_fixture",
                policy=self.policy,
                generated_at=FIXED_TIME,
                run_id="audit-retention-cli-test",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "evidence.audit",
                    "retention",
                    "--log",
                    str(log),
                    "--policy",
                    str(POLICY_PATH),
                    "--generated-at",
                    "2026-05-05T06:00:00Z",
                    "--out-json",
                    str(out),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": f"{ROOT}:{ROOT / 'cyber-side'}:{ROOT / 'world-side'}"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            validate_audit_retention_report(report)
            self.assertEqual(report["retention"]["event_count"], 1)


if __name__ == "__main__":
    unittest.main()
