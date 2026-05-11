from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation-reply-triage.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"
SPEC = importlib.util.spec_from_file_location("validation_reply_triage", SCRIPT)
assert SPEC and SPEC.loader
reply_triage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reply_triage
SPEC.loader.exec_module(reply_triage)


class ValidationReplyTriageTests(unittest.TestCase):
    def test_book_call_emits_dry_run_and_confirmed_commands_without_writing(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        triage = reply_triage.build_reply_triage(
            targets,
            target_label="target-dib-platform-001",
            classification="book_call",
            run_date="2026-05-10",
        )

        self.assertEqual(triage["schema_version"], reply_triage.REPLY_TRIAGE_SCHEMA_VERSION)
        self.assertEqual(triage["classification"], "book_call")
        self.assertTrue(triage["write_allowed_after_review"])
        self.assertEqual(
            triage["dry_run_commands"],
            ["make validation-book-call TARGET=target-dib-platform-001 DATE=2026-05-10"],
        )
        self.assertEqual(
            triage["confirmed_write_commands"],
            [
                "make validation-book-call TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_TARGET=1"
            ],
        )
        self.assertEqual(targets["targets"][0]["status"], "outreach_sent")

    def test_disqualify_allows_identified_target(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        triage = reply_triage.build_reply_triage(
            targets,
            target_label="target-dib-platform-001",
            classification="disqualify",
            run_date="2026-05-10",
        )

        self.assertTrue(triage["write_allowed_after_review"])
        self.assertEqual(
            triage["dry_run_commands"],
            [
                "make validation-disqualify-target "
                "TARGET=target-dib-platform-001 DATE=2026-05-10"
            ],
        )
        self.assertIn("CONFIRM_TARGET=1", triage["confirmed_write_commands"][0])

    def test_keep_pending_never_emits_confirmed_write_command(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        triage = reply_triage.build_reply_triage(
            targets,
            target_label="target-dib-platform-001",
            classification="keep_pending",
            run_date="2026-05-10",
        )

        self.assertFalse(triage["write_allowed_after_review"])
        self.assertEqual(triage["confirmed_write_commands"], [])
        self.assertEqual(triage["dry_run_commands"], ["make validation-status DATE=2026-05-10"])

    def test_manual_review_markdown_warns_not_to_paste_private_reply_text(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        triage = reply_triage.build_reply_triage(
            targets,
            target_label="target-dib-platform-001",
            classification="manual_review",
            run_date="2026-05-10",
        )

        rendered = reply_triage.render_markdown(triage)

        self.assertIn("None. Do not write a tracker update", rendered)
        self.assertIn("Never paste reply text", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_book_call_rejects_unsent_target(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(reply_triage.ReplyTriageError, "requires current status"):
            reply_triage.build_reply_triage(
                targets,
                target_label="target-dib-platform-001",
                classification="book_call",
                run_date="2026-05-10",
            )

    def test_rejects_bad_date(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(reply_triage.ReplyTriageError, "YYYY-MM-DD"):
            reply_triage.build_reply_triage(
                targets,
                target_label="target-dib-platform-001",
                classification="manual_review",
                run_date="05/10/2026",
            )

    def test_rejects_unknown_target(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(reply_triage.ReplyTriageError, "target not found"):
            reply_triage.build_reply_triage(
                targets,
                target_label="missing-target",
                classification="manual_review",
                run_date="2026-05-10",
            )

    def test_rejects_sensitive_target_text_from_tracker_validation(self) -> None:
        targets = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["next_action"] = "Email buyer@example.com"

        with self.assertRaisesRegex(reply_triage.ReplyTriageError, "email-like"):
            reply_triage.build_reply_triage(
                targets,
                target_label="target-dib-platform-001",
                classification="manual_review",
                run_date="2026-05-10",
            )

    def test_cli_outputs_json_and_does_not_require_reply_text(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--targets",
                str(EXAMPLE),
                "--target-label",
                "target-dib-platform-001",
                "--classification",
                "disqualify",
                "--date",
                "2026-05-10",
                "--format",
                "json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        triage = json.loads(completed.stdout)
        self.assertEqual(triage["classification"], "disqualify")
        self.assertIn("confirmed_write_commands", triage)
        self.assertNotIn("reply_text", completed.stdout)


if __name__ == "__main__":
    unittest.main()
