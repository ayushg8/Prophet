from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "customer-validation-log-add.py"
EXAMPLE = ROOT / "docs" / "customer-validation-log.example.json"
EXAMPLE_TARGETS = ROOT / "docs" / "validation-targets.example.json"
SPEC = importlib.util.spec_from_file_location("customer_validation_log_add", SCRIPT)
assert SPEC and SPEC.loader
log_add = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = log_add
SPEC.loader.exec_module(log_add)


class CustomerValidationLogAddTests(unittest.TestCase):
    def test_appends_safe_interview_and_reports_scorecard(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        interview = _interview("example-dib-platform-002")

        summary = log_add.append_interview(log, interview, updated_at="2026-05-10")

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["interview_count"], 2)
        self.assertEqual(summary["qualified_count"], 2)
        self.assertEqual(summary["repeated_workflow_pain_count"], 2)
        self.assertEqual(summary["top_workflow_pain_theme"], "evidence_packet_gap")
        self.assertEqual(summary["gaps_to_verdicts"]["pilot_pull_detected"]["qualified_count"], 15)
        self.assertEqual(summary["gaps_to_verdicts"]["build_next_slice"]["high_pain_count"], 8)
        self.assertEqual(summary["verdict"], "insufficient_data")
        self.assertEqual(log["updated_at"], "2026-05-10")
        self.assertEqual(log["interviews"][1]["account_label"], "example-dib-platform-002")

    def test_replace_example_seed_starts_real_private_log(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        interview = _interview("target-dib-platform-001")

        summary = log_add.append_interview(
            log,
            interview,
            updated_at="2026-05-10",
            replace_example_seed=True,
        )

        self.assertTrue(summary["ok"])
        self.assertTrue(summary["replaced_example_seed"])
        self.assertEqual(summary["removed_example_seed_count"], 1)
        self.assertFalse(summary["example_seed_log"])
        self.assertEqual(summary["interview_count"], 1)
        self.assertEqual(summary["qualified_count"], 1)
        self.assertEqual(summary["effective_validation_counts"]["qualified_count"], 1)
        self.assertEqual(summary["gaps_to_verdicts"]["build_next_slice"]["qualified_count"], 14)
        self.assertEqual(log["interviews"][0]["account_label"], "target-dib-platform-001")
        self.assertNotIn("Example only", log["notes"])

    def test_replace_example_seed_requires_seed_marker(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        log["notes"] = "Private anonymized buyer validation log."
        interview = _interview("target-dib-platform-001")

        with self.assertRaisesRegex(log_add.CustomerValidationLogAddError, "example-only"):
            log_add.append_interview(
                log,
                interview,
                updated_at="2026-05-10",
                replace_example_seed=True,
            )

    def test_replace_example_seed_refuses_mixed_logs(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        log["interviews"].append(_interview("target-dib-platform-001"))
        interview = _interview("target-dib-platform-002")

        with self.assertRaisesRegex(log_add.CustomerValidationLogAddError, "mixed logs"):
            log_add.append_interview(
                log,
                interview,
                updated_at="2026-05-10",
                replace_example_seed=True,
            )

    def test_rejects_duplicate_account_label(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        interview = _interview("example-dib-platform-001")

        with self.assertRaisesRegex(log_add.CustomerValidationLogAddError, "already exists"):
            log_add.append_interview(log, interview, updated_at="2026-05-10")

    def test_rejects_sensitive_interview_text(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        interview = _interview("example-dib-platform-002")
        interview["next_step"] = "Email buyer@example.com"

        with self.assertRaisesRegex(log_add.CustomerValidationLogAddError, "email-like"):
            log_add.append_interview(log, interview, updated_at="2026-05-10")

    def test_rejects_bad_updated_at_date(self) -> None:
        log = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        interview = _interview("example-dib-platform-002")

        with self.assertRaisesRegex(log_add.CustomerValidationLogAddError, "YYYY-MM-DD"):
            log_add.append_interview(log, interview, updated_at="05/10/2026")

    def test_cli_dry_run_does_not_write_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--account-label",
                    "example-dib-platform-002",
                    "--segment",
                    "dib_platform_security",
                    "--persona",
                    "director_product_security",
                    "--qualified",
                    "true",
                    "--current-workflow",
                    "Scanner, SBOM review, ticket queue, manual briefing.",
                    "--recent-painful-event",
                    "Had to justify edge appliance remediation order.",
                    "--existing-tool",
                    "scanner",
                    "--existing-tool",
                    "ticketing",
                    "--status-quo-gap",
                    "No audit-ready packet for why this first.",
                    "--desired-output",
                    "Evidence packet with source basis and SOC review handoff.",
                    "--workflow-pain-theme",
                    "evidence_packet_gap",
                    "--pain-score",
                    "5",
                    "--urgency-score",
                    "4",
                    "--status-quo-weakness-score",
                    "4",
                    "--buyer-access-score",
                    "3",
                    "--data-feasibility-score",
                    "4",
                    "--pilot-pull-score",
                    "3",
                    "--budget-signal",
                    "could_sponsor_design_partner",
                    "--pilot-signal",
                    "asked_for_scoped_pilot",
                    "--objection",
                    "Needs security review.",
                    "--next-step",
                    "Send pilot scope.",
                    "--updated-at",
                    "2026-05-10",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertEqual(summary["interview_count"], 2)
            self.assertFalse(summary["confirmed_log"])
            self.assertFalse(summary["would_write"])
            self.assertIn("gaps_to_verdicts", summary)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_without_confirm_log_does_not_write_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertEqual(summary["interview_count"], 2)
            self.assertFalse(summary["confirmed_log"])
            self.assertFalse(summary["would_write"])
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_confirm_log_writes_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path = Path(tmp) / "validation-targets.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            _write_booked_target(target_path, "example-dib-platform-002")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--targets",
                    str(target_path),
                    "--interview-json",
                    str(interview_path),
                    "--require-target-status",
                    "call_booked",
                    "--updated-at",
                    "2026-05-10",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertEqual(summary["interview_count"], 2)
            self.assertTrue(summary["confirmed_log"])
            self.assertTrue(summary["would_write"])
            updated = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(updated["interviews"]), 2)
            self.assertEqual(updated["updated_at"], "2026-05-10")

    def test_cli_confirm_log_requires_target_guard_or_explicit_bypass(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--confirm-log requires --require-target-status", completed.stderr)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_confirm_log_allows_explicit_untracked_interview_bypass(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--allow-untracked-interview",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            updated = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["confirmed_log"])
            self.assertEqual(len(updated["interviews"]), 2)

    def test_cli_replace_example_seed_rejects_untracked_bypass(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("target-dib-platform-001")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--allow-untracked-interview",
                    "--replace-example-seed",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--replace-example-seed requires --require-target-status", completed.stderr)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged, original)

    def test_cli_replace_example_seed_requires_target_status_guard(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("target-dib-platform-001")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--replace-example-seed",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(
                "--replace-example-seed requires --require-target-status call_booked",
                completed.stderr,
            )
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged, original)

    def test_cli_accepts_booked_target_when_guarded(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path = Path(tmp) / "validation-targets.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            _write_booked_target(target_path, "example-dib-platform-002")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--targets",
                    str(target_path),
                    "--interview-json",
                    str(interview_path),
                    "--require-target-status",
                    "call_booked",
                    "--updated-at",
                    "2026-05-10",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertEqual(summary["account_label"], "example-dib-platform-002")
            self.assertFalse(summary["would_write"])

    def test_cli_rejects_guarded_interview_with_target_metadata_mismatch(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path = Path(tmp) / "validation-targets.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            _write_booked_target(target_path, "example-dib-platform-002")
            interview = _interview("example-dib-platform-002")
            interview["persona"] = "mismatched_persona"
            interview_path.write_text(json.dumps(interview), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--targets",
                    str(target_path),
                    "--interview-json",
                    str(interview_path),
                    "--require-target-status",
                    "call_booked",
                    "--updated-at",
                    "2026-05-10",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("interview persona must match validation target persona", completed.stderr)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_replace_example_seed_dry_run_does_not_write(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path = Path(tmp) / "validation-targets.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            _write_booked_target(target_path, "target-dib-platform-001")
            interview_path.write_text(
                json.dumps(_interview("target-dib-platform-001")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--targets",
                    str(target_path),
                    "--interview-json",
                    str(interview_path),
                    "--require-target-status",
                    "call_booked",
                    "--updated-at",
                    "2026-05-10",
                    "--replace-example-seed",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertTrue(summary["replaced_example_seed"])
            self.assertFalse(summary["example_seed_log"])
            self.assertFalse(summary["would_write"])
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged, original)

    def test_cli_rejects_unbooked_target_when_guarded(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path = Path(tmp) / "validation-targets.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            _write_booked_target(target_path, "example-dib-platform-002", status="identified")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--targets",
                    str(target_path),
                    "--interview-json",
                    str(interview_path),
                    "--require-target-status",
                    "call_booked",
                    "--updated-at",
                    "2026-05-10",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("target current status", completed.stderr)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_rejects_dry_run_and_confirm_log_together(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(
                json.dumps(_interview("example-dib-platform-002")),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--dry-run",
                    "--confirm-log",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("cannot be combined", completed.stderr)
            unchanged = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["interviews"]), len(original["interviews"]))

    def test_cli_help_names_target_metadata_guard(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("account_label, segment, and persona", completed.stdout)

    def test_cli_accepts_interview_json(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            interview_path = Path(tmp) / "interview.json"
            log_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            interview_path.write_text(json.dumps(_interview("example-dib-platform-002")), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--log",
                    str(log_path),
                    "--interview-json",
                    str(interview_path),
                    "--updated-at",
                    "2026-05-10",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertEqual(summary["account_label"], "example-dib-platform-002")
            self.assertEqual(summary["interview_count"], 2)
            self.assertFalse(summary["would_write"])


def _interview(account_label: str) -> dict[str, object]:
    return {
        "account_label": account_label,
        "segment": "dib_platform_security",
        "persona": "director_product_security",
        "qualified": True,
        "current_workflow": "Scanner, SBOM review, ticket queue, manual briefing.",
        "recent_painful_event": "Had to justify edge appliance remediation order.",
        "existing_tools": ["scanner", "ticketing"],
        "status_quo_gap": "No audit-ready packet for why this first.",
        "desired_output": "Evidence packet with source basis and SOC review handoff.",
        "workflow_pain_theme": "evidence_packet_gap",
        "pain_score": 5,
        "urgency_score": 4,
        "status_quo_weakness_score": 4,
        "buyer_access_score": 3,
        "data_feasibility_score": 4,
        "pilot_pull_score": 3,
        "budget_signal": "could_sponsor_design_partner",
        "pilot_signal": "asked_for_scoped_pilot",
        "objections": ["Needs security review."],
        "next_step": "Send pilot scope.",
        "safe_artifact_offer": "Sanitized SBOM family export.",
    }


def _write_booked_target(path: Path, target_label: str, *, status: str = "call_booked") -> None:
    targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
    targets["targets"][0]["target_label"] = target_label
    targets["targets"][0]["status"] = status
    targets["targets"][0]["last_touch"] = "2026-05-10"
    targets["targets"][0]["follow_up_due"] = ""
    targets["targets"][0]["next_action"] = "Prepare discovery call."
    path.write_text(json.dumps(targets), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
