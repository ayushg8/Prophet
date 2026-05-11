from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs" / "SECRET_HISTORY_REVIEW.md"
SCRIPT = ROOT / "scripts" / "check-secrets-archaeology.sh"
RELEASE_TAG_PREFLIGHT = ROOT / "scripts" / "check-release-tag-preflight.sh"
OPERATIONAL_TODO = ROOT / "docs" / "PROPHET_TODO.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"


class SecretHistoryReviewDocsTests(unittest.TestCase):
    def test_review_matches_current_full_history_findings(self) -> None:
        completed = subprocess.run(
            [str(SCRIPT)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        review = REVIEW.read_text(encoding="utf-8")
        findings = sorted(
            set(
                re.findall(
                    r"suspicious historical content: ([0-9a-f]{40}):LOG4SHELL_INSTRUCTIONS\.md",
                    completed.stderr,
                )
            )
        )

        self.assertEqual(completed.returncode, 1)
        self.assertGreaterEqual(len(findings), 1)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", completed.stderr)
        self.assertIn("do not paste matched values", completed.stderr)
        for commit in findings:
            self.assertIn(f"`{commit}`", review)
        self.assertIn("LOG4SHELL_INSTRUCTIONS.md", review)

    def test_current_only_scan_still_passes(self) -> None:
        completed = subprocess.run(
            [str(SCRIPT), "--current-only"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Prophet secrets archaeology passed", completed.stdout)

    def test_review_keeps_values_out_of_docs(self) -> None:
        review = REVIEW.read_text(encoding="utf-8")

        self.assertIn("without printing matched secret-like values", review)
        self.assertIn("Do not paste the matched line or value", review)
        self.assertIn("Owner Decision Template", review)
        self.assertIn("Rationale without matched value", review)
        self.assertIn("Unknown ownership or uncertainty", review)
        self.assertIn("git show --no-ext-diff <commit>:LOG4SHELL_INSTRUCTIONS.md", review)
        self.assertNotIn("Password:", review)
        self.assertNotIn("s3cr", review.lower())

    def test_todos_block_public_release_review_on_owner_decision(self) -> None:
        for path in (OPERATIONAL_TODO, MASTER_TODO):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("LOG4SHELL_INSTRUCTIONS.md", text)
                self.assertIn("public release review", text)
                self.assertIn("blocked until the owner decision", text)
                self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)

    def test_release_tag_preflight_requires_full_history_before_build_gate(self) -> None:
        script = RELEASE_TAG_PREFLIGHT.read_text(encoding="utf-8")

        full_history_check = "./scripts/check-secrets-archaeology.sh"
        build_gate_check = "scripts/validation-sprint-dashboard.py"

        self.assertIn(full_history_check, script)
        self.assertIn(build_gate_check, script)
        self.assertNotIn("check-secrets-archaeology.sh --current-only", script)
        self.assertLess(script.index(full_history_check), script.index(build_gate_check))
        self.assertIn("full secrets archaeology", script)
        self.assertIn("build_next_slice", script)
        self.assertIn("does not stage, commit, push, tag", script)

    def test_release_tag_preflight_reports_secret_and_validation_blockers(self) -> None:
        script = RELEASE_TAG_PREFLIGHT.read_text(encoding="utf-8")

        self.assertIn("preflight_failed=0", script)
        self.assertIn("release tag preflight blocker: full secrets archaeology failed", script)
        self.assertIn("release tag preflight failed: build gate is closed", script)
        self.assertIn("Prophet release tag preflight failed.", script)
        self.assertIn("both the full secrets archaeology result", script)
        self.assertLess(
            script.index("release tag preflight blocker: full secrets archaeology failed"),
            script.index("Checking real-validation build gate"),
        )


if __name__ == "__main__":
    unittest.main()
