from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET_DOC = ROOT / "docs/CONSOLE_ACCESSIBILITY_AND_BROWSER_TARGET.md"
MASTER_TODO = ROOT / "docs/PROPHET_MASTER_TODO.md"
OPERATOR_TODO = ROOT / "docs/PROPHET_TODO.md"
CONSOLE_SMOKE = ROOT / "prophet-console/tests/console.smoke.ts"


class ConsoleAccessibilityBrowserDocsTests(unittest.TestCase):
    def test_console_accessibility_and_browser_target_matches_smoke_coverage(self) -> None:
        target = TARGET_DOC.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")
        operator_todo = OPERATOR_TODO.read_text(encoding="utf-8")
        console_smoke = CONSOLE_SMOKE.read_text(encoding="utf-8")

        for required in (
            "does not claim production WCAG certification",
            "Chromium through\nPlaywright",
            "localhost-only control\nAPI",
            "No Safari support claim",
            "No Firefox support claim",
            "No mobile browser support claim",
            "Do not describe the console as broadly accessible",
            "cross-browser supported",
        ):
            with self.subTest(required=required):
                self.assertIn(required, target)

        smoke_tests = (
            "console supports keyboard navigation for the evaluator runbook path",
            "console accessibility smoke keeps controls named and hidden drawers out of tab order",
        )
        for test_name in smoke_tests:
            with self.subTest(test_name=test_name):
                self.assertIn(test_name, target)
                self.assertIn(test_name, console_smoke)

        self.assertIn("- [x] Add accessibility target and test plan.", master_todo)
        self.assertIn("- [x] Add browser compatibility target.", master_todo)
        self.assertIn("docs/CONSOLE_ACCESSIBILITY_AND_BROWSER_TARGET.md", operator_todo)


if __name__ == "__main__":
    unittest.main()
