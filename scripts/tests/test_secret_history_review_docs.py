from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs" / "SECRET_HISTORY_REVIEW.md"
SCRIPT = ROOT / "scripts" / "check-secrets-archaeology.sh"


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


if __name__ == "__main__":
    unittest.main()
