from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_NOTES = ROOT / "docs" / "PILOT_RELEASE_NOTES.md"
CHANGELOG = ROOT / "CHANGELOG.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class PilotReleaseNotesDocsTests(unittest.TestCase):
    def test_release_notes_name_runnable_local_product_and_gate(self) -> None:
        text = RELEASE_NOTES.read_text(encoding="utf-8")

        self.assertIn("## Runnable Local Product", text)
        self.assertIn("make console-demo", text)
        self.assertIn("http://127.0.0.1:5173/", text)
        self.assertIn("http://127.0.0.1:8787/api/readiness", text)
        self.assertIn("make pilot-ready-check-full DATE=2026-05-11", text)
        self.assertIn("Playwright console smoke tests", text)
        self.assertIn("345 tests", text)
        self.assertIn("0 paths in the clean committed worktree", text)
        self.assertIn("0 untracked non-ignored files", text)
        self.assertIn("117 URLs", text)
        self.assertIn("make release-hygiene", text)
        self.assertIn("make secrets-archaeology", text)
        self.assertIn("historical `LOG4SHELL_INSTRUCTIONS.md`", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)
        self.assertIn("pre-commit hook", text)
        self.assertIn("make console-live-check", text)
        self.assertIn("make console-screenshot-check", text)
        self.assertIn("0 non-ignored dirty files", text)
        self.assertIn("Linux fresh-clone pilot smoke", text)
        self.assertIn("Customer validation remains `insufficient_data`", text)
        self.assertIn("production platform build", text)
        self.assertNotIn("331 tests", text)
        self.assertNotIn("330 tests", text)
        self.assertNotIn("322 tests", text)
        self.assertNotIn("320 tests", text)
        self.assertNotIn("315 tests", text)
        self.assertNotIn("312 tests", text)
        self.assertNotIn("316 tests", text)
        self.assertNotIn("318 tests", text)
        self.assertNotIn("337 tests", text)
        self.assertNotIn("91 paths", text)
        self.assertNotIn("92 paths", text)
        self.assertNotIn("93 paths", text)
        self.assertNotIn("66 untracked non-ignored files", text)
        self.assertNotIn("64 untracked non-ignored files", text)
        self.assertNotIn("63 untracked non-ignored files", text)
        self.assertNotIn("58 untracked non-ignored files", text)
        self.assertNotIn("59 untracked non-ignored files", text)

    def test_release_notes_keep_safety_boundary_explicit(self) -> None:
        text = RELEASE_NOTES.read_text(encoding="utf-8")

        self.assertIn("does not authorize live target validation", text)
        self.assertIn("live collection workflows", text)
        self.assertIn("payload", text)
        self.assertIn("autonomous remediation", text)
        self.assertIn("rejects non-localhost UI hosts", text)

    def test_linux_fresh_clone_smoke_is_ci_backed(self) -> None:
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("runs on `ubuntu-latest`", notes)
        self.assertIn("Linux fresh-clone pilot smoke preflight", notes)
        self.assertIn("Linux fresh-clone pilot smoke", notes)
        self.assertIn("name: Linux fresh-clone pilot smoke preflight", workflow)
        self.assertIn("run: ./scripts/check-local-env.sh", workflow)
        self.assertIn("name: Linux fresh-clone pilot smoke", workflow)
        self.assertIn("run: ./scripts/run-pilot-demo-smoke.sh", workflow)

    def test_changelog_names_current_gate_and_review_guardrails(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")

        self.assertIn("validation sprint active; production build gate closed", text)
        self.assertIn("make pilot-ready-check-full DATE=2026-05-11", text)
        self.assertIn("PR template guardrails", text)
        self.assertIn("validation dashboard verdict", text)
        self.assertIn("private-artifact boundary", text)
        self.assertIn("`insufficient_data`", text)
        self.assertIn("`build_next_slice`", text)
        self.assertIn("Linux fresh-clone smoke is covered", text)
        self.assertNotIn("make pilot-ready-check-full DATE=2026-05-10", text)
        self.assertNotIn("Linux fresh-clone smoke, and final commit split remain open", text)


if __name__ == "__main__":
    unittest.main()
