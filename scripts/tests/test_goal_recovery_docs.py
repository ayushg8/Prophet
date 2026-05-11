from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECOVERED_CONTEXT_DOCS = [
    ROOT / "docs/PROPHET_COMPLETION_PLAN.md",
    ROOT / "docs/PROPHET_FULL_FINISH_PLAN.md",
    ROOT / "docs/PROPHET_GSTACK_WORKLOG.md",
]
COMPLETION_AUDIT = ROOT / "docs/PROPHET_COMPLETION_AUDIT.md"
OPERATIONAL_TODO = ROOT / "docs/PROPHET_TODO.md"
VALIDATION_RECOVERY_DOCS = [
    ROOT / "docs/VALIDATION_DAILY_BRIEF.md",
    ROOT / "docs/VALIDATION_SPRINT_CHECKLIST.md",
]
VALIDATION_CHECKLIST = ROOT / "docs/VALIDATION_SPRINT_CHECKLIST.md"


class GoalRecoveryDocsTests(unittest.TestCase):
    def test_recovered_context_docs_point_to_current_gate(self) -> None:
        for path in RECOVERED_CONTEXT_DOCS:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")

                self.assertIn("Historical context", text)
                self.assertIn("docs/CODEX_CEO_FINISH_BRIEF.md", text)
                self.assertIn("docs/PROPHET_COMPLETION_AUDIT.md", text)
                self.assertIn("docs/PROPHET_TODO.md", text)
                self.assertIn("validation", text)
                self.assertIn("insufficient_data", text)

    def test_completion_audit_is_current_resume_source(self) -> None:
        text = COMPLETION_AUDIT.read_text(encoding="utf-8")

        self.assertIn("Recovered Goal Source / Goal Setter", text)
        self.assertIn("current resume source", text)
        self.assertIn("make validation-dashboard", text)
        self.assertIn("make goal-resume", text)
        self.assertIn("No separate project `*goal*.md` file was found", text)
        self.assertIn("https://github.com/Ayush1298567/Prophet.git", text)
        self.assertIn("20260510-132727-prophet-example-seed-guard-current.md", text)
        self.assertIn("20260510-131943-prophet-goal-recovery-current.md", text)
        self.assertIn("20260510-124000-prophet-goal-resume-github-current-232-tests.md", text)
        self.assertIn("20260510-123000-prophet-goal-resume-github-current-231-tests.md", text)
        self.assertIn("20260510-122000-prophet-goal-resume-github-current-230-tests.md", text)
        self.assertIn("20260510-120157-prophet-goal-resume-github-current-226-tests.md", text)
        self.assertIn("20260510-113358-prophet-overnight-docs-historical-225-tests.md", text)
        self.assertIn("20260510-113126-prophet-overnight-loop-validation-gate-224-tests.md", text)
        self.assertIn("20260510-112804-prophet-release-validation-gate-222-tests.md", text)
        self.assertIn("20260510-112449-prophet-private-readme-inventory-221-tests.md", text)
        self.assertIn("20260510-112146-prophet-private-send-artifact-inventory-220-tests.md", text)
        self.assertIn("20260510-111519-prophet-validation-resume-218-tests.md", text)
        self.assertIn("20260510-102301-prophet-validation-checkpoint-current.md", text)
        self.assertIn("20260510-100425-prophet-validation-send-boundary.md", text)
        self.assertIn("20260510-064650-prophet-validation-gate-recovery-current.md", text)
        self.assertIn("20260510-021855-prophet-goal-resume-current.md", text)
        self.assertIn("232-test", text)
        self.assertIn("verification snapshot", text)
        self.assertIn("GitHub remote", text)
        self.assertIn("release-safety", text)
        self.assertIn("Checkpoints", text)
        self.assertNotIn("latest saved gstack checkpoint", text)
        self.assertNotIn("213-test", text)

    def test_validation_operator_docs_name_goal_resume(self) -> None:
        for path in VALIDATION_RECOVERY_DOCS:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")

                self.assertIn("make goal-resume DATE=YYYY-MM-DD", text)
                self.assertIn("lost `/goal` session", text)
                self.assertIn("no-write", text)
                self.assertIn("--refresh-readme", text)
                self.assertIn("make validation-team-update-save DATE=YYYY-MM-DD", text)
                self.assertIn("temporary file", text)
                self.assertIn("preserv", text)
                self.assertIn("next_draft_state", text)
                self.assertIn("next_draft_matches_next_pending", text)
                self.assertIn("send_copy_state", text)
                self.assertIn("send_copy_matches_next_pending", text)

    def test_operational_todo_names_weekly_private_artifact_pruning(self) -> None:
        text = OPERATIONAL_TODO.read_text(encoding="utf-8")

        self.assertIn("Weekly validation review ritual exists", text)
        self.assertIn("stale private targets", text)
        self.assertIn("stale message packs", text)
        self.assertIn("stale private interview starters", text)
        self.assertIn("completed or stale", text)
        self.assertIn("docs/VALIDATION_SPRINT_CHECKLIST.md", text)

    def test_weekly_review_keeps_validation_progress_honest(self) -> None:
        text = VALIDATION_CHECKLIST.read_text(encoding="utf-8")

        self.assertIn("## Weekly Review", text)
        self.assertIn("Run `make validation-dashboard DATE=YYYY-MM-DD`", text)
        self.assertIn("aggregate verdict, counts, and next action", text)
        self.assertIn("make validation-team-update DATE=YYYY-MM-DD", text)
        self.assertIn("make validation-status DATE=YYYY-MM-DD", text)
        self.assertIn("Do not mark messages sent", text)
        self.assertIn("unless the real external action happened", text)
        self.assertIn("Dry-run every pruning or status-update command first", text)
        self.assertIn("CONFIRM_SENT=1", text)
        self.assertIn("CONFIRM_TARGET=1", text)
        self.assertIn("CONFIRM_LOG=1", text)
        self.assertIn("Confirm `validation/private/` remains ignored", text)
        self.assertIn("Prune stale private targets", text)
        self.assertIn("Delete or rotate stale ignored private message packs", text)
        self.assertIn("customer-validation-interview-next.json", text)
        self.assertIn("only after a real call and sanitized review", text)
        self.assertIn("Leave the production build gate closed", text)
        self.assertIn("returns `build_next_slice`", text)


if __name__ == "__main__":
    unittest.main()
