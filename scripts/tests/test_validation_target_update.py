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
SCRIPT = ROOT / "scripts" / "validation-target-update.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"
EXAMPLE_LOG = ROOT / "docs" / "customer-validation-log.example.json"
SPEC = importlib.util.spec_from_file_location("validation_target_update", SCRIPT)
assert SPEC and SPEC.loader
target_update = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = target_update
SPEC.loader.exec_module(target_update)


class ValidationTargetUpdateTests(unittest.TestCase):
    def test_updates_one_target_and_preserves_safe_schema(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        summary = target_update.update_target(
            targets,
            target_label="target-dib-platform-001",
            status="outreach_sent",
            last_touch="2026-05-10",
            follow_up_due="2026-05-13",
            next_action="Send follow-up if no reply.",
            updated_at="2026-05-10",
        )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["before"]["status"], "identified")
        self.assertEqual(summary["after"]["status"], "outreach_sent")
        self.assertEqual(targets["updated_at"], "2026-05-10")
        self.assertEqual(targets["targets"][0]["follow_up_due"], "2026-05-13")
        self.assertEqual(summary["status_command"], "make validation-status DATE=2026-05-10")
        self.assertEqual(
            summary["dashboard_command"],
            "make validation-dashboard DATE=2026-05-10",
        )

    def test_can_mark_call_booked_and_clear_follow_up_due(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets["targets"][0]["status"] = "outreach_sent"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        summary = target_update.update_target(
            targets,
            target_label="target-dib-platform-001",
            status="call_booked",
            last_touch="2026-05-11",
            clear_follow_up_due=True,
            next_action="Prepare discovery call.",
            updated_at="2026-05-11",
        )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["before"]["follow_up_due"], "2026-05-13")
        self.assertEqual(summary["after"]["status"], "call_booked")
        self.assertEqual(summary["after"]["follow_up_due"], "")
        self.assertEqual(targets["targets"][0]["next_action"], "Prepare discovery call.")

    def test_can_mark_completed_after_logged_call(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets["targets"][0]["status"] = "call_booked"
        targets["targets"][0]["last_touch"] = "2026-05-11"

        summary = target_update.update_target(
            targets,
            target_label="target-dib-platform-001",
            status="completed",
            last_touch="2026-05-12",
            clear_follow_up_due=True,
            next_action="Logged sanitized discovery outcome.",
            updated_at="2026-05-12",
            require_current_status=["call_booked"],
        )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["after"]["status"], "completed")
        self.assertEqual(summary["after"]["last_touch"], "2026-05-12")
        self.assertEqual(summary["after"]["follow_up_due"], "")
        self.assertEqual(summary["after"]["next_action"], "Logged sanitized discovery outcome.")

    def test_required_current_status_rejects_out_of_sequence_update(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "current status"):
            target_update.update_target(
                targets,
                target_label="target-dib-platform-001",
                status="completed",
                last_touch="2026-05-12",
                clear_follow_up_due=True,
                next_action="Logged sanitized discovery outcome.",
                require_current_status=["call_booked"],
            )

    def test_required_current_status_rejects_unknown_status(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "unsupported"):
            target_update.update_target(
                targets,
                target_label="target-dib-platform-001",
                status="completed",
                require_current_status=["meeting_done"],
            )

    def test_rejects_clear_and_set_follow_up_due_together(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "cannot be combined"):
            target_update.update_target(
                targets,
                target_label="target-dib-platform-001",
                status="call_booked",
                follow_up_due="2026-05-13",
                clear_follow_up_due=True,
            )

    def test_rejects_sensitive_next_action(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "email-like"):
            target_update.update_target(
                targets,
                target_label="target-dib-platform-001",
                status="outreach_sent",
                next_action="Email buyer@example.com",
            )

    def test_rejects_bad_date(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "YYYY-MM-DD"):
            target_update.update_target(
                targets,
                target_label="target-dib-platform-001",
                status="outreach_sent",
                last_touch="05/10/2026",
            )

    def test_rejects_unknown_target(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(target_update.ValidationTargetUpdateError, "target not found"):
            target_update.update_target(
                targets,
                target_label="missing-target",
                status="outreach_sent",
            )

    def test_cli_dry_run_does_not_write_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "outreach_sent",
                    "--require-current-status",
                    "identified",
                    "--last-touch",
                    "2026-05-10",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            self.assertTrue(summary["ok"])
            self.assertFalse(summary["confirmed_target"])
            self.assertFalse(summary["would_write"])
            self.assertEqual(summary["updated_at"], "2026-05-10")
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], original["targets"][0]["status"])

    def test_cli_without_confirm_target_does_not_write_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "outreach_sent",
                    "--require-current-status",
                    "identified",
                    "--last-touch",
                    "2026-05-10",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertFalse(summary["would_write"])
            self.assertEqual(unchanged["targets"][0]["status"], original["targets"][0]["status"])

    def test_cli_confirm_target_writes_non_send_file(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        original["targets"][0]["status"] = "outreach_sent"
        original["targets"][0]["last_touch"] = "2026-05-10"
        original["targets"][0]["follow_up_due"] = "2026-05-13"
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "call_booked",
                    "--require-current-status",
                    "outreach_sent",
                    "--last-touch",
                    "2026-05-11",
                    "--clear-follow-up-due",
                    "--next-action",
                    "Prepare discovery call.",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            written = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["confirmed_target"])
            self.assertTrue(summary["would_write"])
            self.assertEqual(written["targets"][0]["status"], "call_booked")
            self.assertEqual(written["targets"][0]["follow_up_due"], "")

    def test_cli_confirm_target_rejects_direct_outreach_sent_write(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "outreach_sent",
                    "--require-current-status",
                    "identified",
                    "--last-touch",
                    "2026-05-10",
                    "--follow-up-due",
                    "2026-05-13",
                    "--next-action",
                    "Send follow-up if no reply.",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("validation-apply-draft-update.py", completed.stderr)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], original["targets"][0]["status"])

    def test_cli_confirm_target_rejects_direct_intro_requested_write(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "intro_requested",
                    "--require-current-status",
                    "identified",
                    "--last-touch",
                    "2026-05-10",
                    "--follow-up-due",
                    "2026-05-13",
                    "--next-action",
                    "Follow up on intro request if no reply.",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("validation-apply-draft-update.py", completed.stderr)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], original["targets"][0]["status"])

    def test_cli_rejects_dry_run_and_confirm_target_together(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "outreach_sent",
                    "--require-current-status",
                    "identified",
                    "--last-touch",
                    "2026-05-10",
                    "--dry-run",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("cannot be combined", completed.stderr)

    def test_cli_rejects_missing_required_current_status_guard(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "outreach_sent",
                    "--last-touch",
                    "2026-05-10",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--require-current-status is required", completed.stderr)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], original["targets"][0]["status"])

    def test_cli_requires_matching_validation_log_for_completion(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        original["targets"][0]["status"] = "call_booked"
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            log_path.write_text(EXAMPLE_LOG.read_text(encoding="utf-8"), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--validation-log",
                    str(log_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "completed",
                    "--require-current-status",
                    "call_booked",
                    "--require-validation-log-account",
                    "--last-touch",
                    "2026-05-12",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("no sanitized interview", completed.stderr)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], "call_booked")

    def test_cli_confirm_completed_requires_validation_log_guard(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        original["targets"][0]["status"] = "call_booked"
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "completed",
                    "--require-current-status",
                    "call_booked",
                    "--last-touch",
                    "2026-05-12",
                    "--clear-follow-up-due",
                    "--next-action",
                    "Logged sanitized discovery outcome.",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--require-validation-log-account", completed.stderr)
            unchanged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["targets"][0]["status"], "call_booked")

    def test_cli_accepts_matching_validation_log_for_completion(self) -> None:
        original = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        original["targets"][0]["status"] = "call_booked"
        log = json.loads(EXAMPLE_LOG.read_text(encoding="utf-8"))
        log["interviews"][0]["account_label"] = "target-dib-platform-001"
        with tempfile.TemporaryDirectory() as tmp:
            target_path = Path(tmp) / "targets.json"
            log_path = Path(tmp) / "customer-validation-log.json"
            target_path.write_text(json.dumps(copy.deepcopy(original)), encoding="utf-8")
            log_path.write_text(json.dumps(log), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(target_path),
                    "--validation-log",
                    str(log_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--status",
                    "completed",
                    "--require-current-status",
                    "call_booked",
                    "--require-validation-log-account",
                    "--last-touch",
                    "2026-05-12",
                    "--confirm-target",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            written = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["confirmed_target"])
            self.assertEqual(written["targets"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
