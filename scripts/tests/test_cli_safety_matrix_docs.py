from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs" / "CLI_SAFETY_MATRIX.md"


VALIDATION_CLIS = [
    "scripts/init-validation-sprint.py",
    "scripts/validation-outreach-block.py",
    "scripts/validation-message-pack.py",
    "scripts/validation-next-draft.py",
    "scripts/validation-send-copy-batch.py",
    "scripts/validation-apply-draft-update.py",
    "scripts/validation-outreach-status.py",
    "scripts/validation-reply-triage.py",
    "scripts/validation-target-update.py",
    "scripts/validation-prepare-interview.py",
    "scripts/customer-validation-log-add.py",
    "scripts/customer-validation-scorecard.py",
    "scripts/validation-targets-scorecard.py",
    "scripts/validation-sprint-dashboard.py",
    "scripts/validation-next-action.py",
    "scripts/validation-weekly-review.py",
    "scripts/validation-prune-private.py",
]


class CliSafetyMatrixDocsTests(unittest.TestCase):
    def test_validation_sprint_clis_are_listed(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")

        self.assertIn("Last updated: 2026-05-10", text)
        self.assertIn("Covered Validation Sprint CLIs", text)
        for cli in VALIDATION_CLIS:
            with self.subTest(cli=cli):
                self.assertIn(cli, text)

    def test_validation_sprint_guardrails_are_named(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")

        required_phrases = [
            "validation/private/",
            "--confirm-sent",
            "--confirm-log",
            "--confirm-target",
            "CONFIRM_TARGET=1",
            "CONFIRM_LOG=1",
            "REFRESH_README=1",
            "exactly `1`",
            "--require-date",
            "--refresh-readme",
            "--require-current-status",
            "gaps_to_verdicts",
            "target_backed_validation",
            "needs_attention",
            "next_pending_target_label",
            "build_next_slice",
            "--format team",
            "sanitized aggregate-only",
            "aggregate send-copy readiness",
            "make validation-team-update",
            "make validation-team-update-save",
            "make validation-next-action-save",
            "make validation-weekly-review",
            "make validation-prune-private",
            "make validation-reply-triage",
            "make validation-resume",
            "make goal-resume",
            "today-next-draft.md",
            "today-send-copy.txt",
            "send-copy-YYYY-MM-DD",
            "send_copy_batch_state",
            "send_copy_batch_matches_current_pack",
            "send_copy_batch_readme_exists",
            "send_copy_batch_checklist_exists",
            "--format send-text",
            "--target-label ... --format send-text",
            "temporary file",
            "preserves the previous saved",
            "if rendering fails",
            "NEXT_ACTION.md",
            "does not send, delete, or mutate trackers/logs",
            "matching sanitized validation-log interview",
            "--allow-untracked-interview",
            "--replace-example-seed",
            "no `--allow-untracked-interview`",
            "--require-target-status call_booked",
            "read-only private weekly review",
            "does not delete files or mutate trackers/logs",
            "--confirm-prune",
            "CONFIRM_PRUNE=1",
            "generated ignored private validation artifacts only",
            "protects validation trackers/logs/templates/README files",
            "accepts only a sanitized classification",
            "never reply text",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_dashboard_row_names_date_mismatch_guard(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        dashboard_line = next(
            line for line in text.splitlines() if "scripts/validation-sprint-dashboard.py" in line
        )

        self.assertIn("--require-date", dashboard_line)
        self.assertIn("date-mismatched", dashboard_line)
        self.assertIn("next_draft_state", dashboard_line)
        self.assertIn("next_draft_matches_next_pending", dashboard_line)
        self.assertIn("send_copy_state", dashboard_line)
        self.assertIn("send_copy_matches_next_pending", dashboard_line)
        self.assertIn("send_copy_batch_state", dashboard_line)
        self.assertIn("send_copy_batch_matches_current_pack", dashboard_line)
        self.assertIn("send_copy_batch_readme_exists", dashboard_line)
        self.assertIn("send_copy_batch_checklist_exists", dashboard_line)
        self.assertIn("target/date/status", dashboard_line)
        self.assertIn("build_next_slice", dashboard_line)
        self.assertIn("target_backed_validation", dashboard_line)
        self.assertIn("call_booked", dashboard_line)
        self.assertIn("completed", dashboard_line)
        self.assertIn("matching segment/persona metadata", dashboard_line)
        self.assertIn("CONFIRM_SENT=1", dashboard_line)

    def test_apply_draft_row_names_echoed_recovery_commands(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        apply_line = next(
            line for line in text.splitlines() if "scripts/validation-apply-draft-update.py" in line
        )

        self.assertIn("--require-date", apply_line)
        self.assertIn("CONFIRM_SENT=1", apply_line)
        self.assertIn("status/dashboard commands", apply_line)
        self.assertIn("--confirm-sent", apply_line)

    def test_target_update_row_blocks_direct_confirmed_send_writes(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        target_line = next(
            line for line in text.splitlines() if "scripts/validation-target-update.py" in line
        )

        self.assertIn("dry-run send-derived `intro_requested` / `outreach_sent`", target_line)
        self.assertIn("confirmed send-derived writes are blocked", target_line)
        self.assertIn("scripts/validation-apply-draft-update.py", target_line)
        self.assertIn("copy-only artifact verification", target_line)

    def test_outreach_status_row_names_date_mismatch_guard(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        status_line = next(
            line for line in text.splitlines() if "scripts/validation-outreach-status.py" in line
        )

        self.assertIn("--require-date", status_line)
        self.assertIn("date-mismatched", status_line)
        self.assertIn("next_pending_target_label", status_line)
        self.assertIn("CONFIRM_SENT=1", status_line)
        self.assertIn("needs_attention", status_line)


if __name__ == "__main__":
    unittest.main()
