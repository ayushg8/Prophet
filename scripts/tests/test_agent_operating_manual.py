from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"


class AgentOperatingManualTests(unittest.TestCase):
    def test_agents_manual_points_to_current_goal_and_validation_gate(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")

        self.assertIn("docs/CODEX_CEO_FINISH_BRIEF.md", text)
        self.assertIn("docs/PROPHET_COMPLETION_AUDIT.md", text)
        self.assertIn("build_next_slice", text)
        self.assertIn("insufficient_data", text)
        self.assertIn("make validation-next-draft", text)
        self.assertIn("make validation-send-copy", text)
        self.assertIn("make validation-send-copy-batch", text)
        self.assertIn("make validation-draft-copy", text)
        self.assertIn("make validation-team-update", text)
        self.assertIn("make validation-team-update-save", text)
        self.assertIn("make validation-next-action-save", text)
        self.assertIn("make validation-resume", text)
        self.assertIn("make validation-prune-private", text)
        self.assertIn("CONFIRM_PRUNE=1", text)
        self.assertIn("generated ignored private artifacts", text)
        self.assertIn("make goal-resume", text)
        self.assertIn("today-outreach-status.json", text)
        self.assertIn("today-team-update.md", text)
        self.assertIn("NEXT_ACTION.md", text)
        self.assertIn("aggregate-only", text)
        self.assertIn("outreach_execution.next_draft_exists", text)
        self.assertIn("outreach_execution.next_draft_state", text)
        self.assertIn("outreach_execution.next_draft_matches_next_pending", text)
        self.assertIn("outreach_execution.send_copy_state", text)
        self.assertIn("outreach_execution.send_copy_matches_next_pending", text)
        self.assertIn("outreach_execution.send_copy_batch_state", text)
        self.assertIn("outreach_execution.send_copy_batch_matches_current_pack", text)
        self.assertIn("outreach_execution.send_copy_batch_readme_exists", text)
        self.assertIn("outreach_execution.send_copy_batch_checklist_exists", text)
        self.assertIn("outreach_execution.send_copy_batch_copy_index_exists", text)
        self.assertIn("outreach_execution.send_copy_batch_subject_order_exists", text)
        self.assertIn("neutral copy-index body", text)
        self.assertIn("subject-order body", text)
        self.assertIn("target/date/status", text)
        self.assertIn("validation/private/today-next-draft.md", text)
        self.assertIn("copy-only send artifact", text)
        self.assertIn("copy-only subject/body text", text)
        self.assertIn(
            "make validation-apply-draft TARGET=<target-label> DATE=YYYY-MM-DD",
            text,
        )
        self.assertIn("make validation-status DATE=YYYY-MM-DD", text)
        self.assertIn("make validation-dashboard DATE=YYYY-MM-DD", text)

    def test_agents_manual_does_not_use_old_hackathon_positioning(self) -> None:
        text = AGENTS.read_text(encoding="utf-8").lower()

        stale_phrases = [
            "predicts cyber attacks before they happen",
            "zero-day exploit",
            "zero-day defense",
            "generates zero-day",
            "active hackathon",
        ]
        for phrase in stale_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
