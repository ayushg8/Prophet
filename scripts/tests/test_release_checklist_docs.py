from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_CHECKLIST = ROOT / "docs/RELEASE_CHECKLIST.md"
PRE_COMMIT_HOOK = ROOT / ".githooks" / "pre-commit"


class ReleaseChecklistDocsTests(unittest.TestCase):
    def test_validation_gate_is_release_checklist_item(self) -> None:
        text = RELEASE_CHECKLIST.read_text(encoding="utf-8")

        self.assertIn("## Validation Gate", text)
        self.assertIn("make validation-dashboard DATE=YYYY-MM-DD", text)
        self.assertIn("insufficient_data", text)
        self.assertIn("build gate closed", text)
        self.assertIn("pilot_pull_detected", text)
        self.assertIn("convert the design", text)
        self.assertIn("build_next_slice", text)
        self.assertIn("real anonymized buyer validation", text)
        self.assertIn("make goal-resume DATE=YYYY-MM-DD", text)

    def test_console_demo_is_release_checklist_item(self) -> None:
        text = RELEASE_CHECKLIST.read_text(encoding="utf-8")

        self.assertIn("make console-demo", text)
        self.assertIn("make console-live-check", text)
        self.assertIn("localhost-only control API", text)
        self.assertIn("evaluator", text)
        self.assertIn("stops both", text)
        self.assertIn("evidence and integration demo endpoints", text)
        self.assertIn("runtime audit log", text)

    def test_python_tests_wrapper_is_release_checklist_item(self) -> None:
        text = RELEASE_CHECKLIST.read_text(encoding="utf-8")

        self.assertIn("make python-tests", text)
        self.assertIn("python3 scripts/check-doc-links.py", text)
        self.assertIn("make secrets-archaeology", text)
        self.assertIn("historical findings", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)
        self.assertIn("npm run capture:screenshots", text)
        self.assertIn("make console-screenshot-check", text)
        self.assertIn("console-screenshots/manifest.json", text)
        self.assertIn("scripts", text)
        self.assertIn("cyber-side", text)
        self.assertIn("world-side", text)
        self.assertIn("sandbox runner", text)
        self.assertIn("evidence", text)
        self.assertIn("integrations", text)

    def test_release_tag_gate_blocks_unresolved_secret_history(self) -> None:
        text = RELEASE_CHECKLIST.read_text(encoding="utf-8")

        self.assertIn("## Release Tag Gate", text)
        self.assertIn("Do not create or push a public pilot release tag", text)
        self.assertIn("make secrets-archaeology", text)
        self.assertIn("LOG4SHELL_INSTRUCTIONS.md", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)
        self.assertIn("without pasting the matched line or", text)
        self.assertIn("rotate/revoke", text)
        self.assertIn("false-positive exception", text)
        self.assertIn("ownership is unknown", text)
        self.assertIn("validation verdict", text)
        self.assertIn("build-gate state", text)

    def test_documented_pre_commit_hook_exists_and_scans_staged_paths(self) -> None:
        text = RELEASE_CHECKLIST.read_text(encoding="utf-8")
        hook = PRE_COMMIT_HOOK.read_text(encoding="utf-8")

        self.assertIn("git config core.hooksPath .githooks", text)
        self.assertIn("check-release-safety.py --staged", hook)
        self.assertTrue(PRE_COMMIT_HOOK.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
