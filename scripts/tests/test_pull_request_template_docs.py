from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PR_TEMPLATE = ROOT / ".github" / "pull_request_template.md"


class PullRequestTemplateDocsTests(unittest.TestCase):
    def test_pr_template_keeps_validation_gate_closed_by_default(self) -> None:
        text = PR_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("## Validation Gate", text)
        self.assertIn("make validation-dashboard DATE=YYYY-MM-DD", text)
        self.assertIn("allowed_to_build_next_slice", text)
        self.assertIn("build_next_slice", text)
        self.assertIn("pilot_pull_detected", text)
        self.assertIn("design-partner conversion", text)

    def test_pr_template_blocks_private_artifact_staging(self) -> None:
        text = PR_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("validation/private/", text)
        self.assertIn("runtime output", text)
        self.assertIn("private buyer note", text)
        self.assertIn("send-copy file", text)
        self.assertIn("raw outreach artifact", text)

    def test_pr_template_names_current_release_wrappers(self) -> None:
        text = PR_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("docs/PROPHET_FINISH_CHANGE_INVENTORY.md", text)
        self.assertIn("make python-tests", text)
        self.assertIn("make release-hygiene", text)
        self.assertIn("make worktree-smoke", text)
        self.assertIn("make console-screenshot-check", text)
        self.assertIn("visual handoff artifacts", text)
        self.assertIn("check-release-safety.py --staged", text)
        self.assertIn("/api/readiness", text)


if __name__ == "__main__":
    unittest.main()
