from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERNIGHT_LOOP = ROOT / "scripts/prophet-overnight-gstack-loop.sh"
OVERNIGHT_CHANGE_REPORT = ROOT / "docs/OVERNIGHT_CHANGE_REPORT.md"
OVERNIGHT_CONSOLIDATION_TODO = ROOT / "docs/OVERNIGHT_CONSOLIDATION_TODO.md"


class OvernightLoopPromptTests(unittest.TestCase):
    def test_prompt_preserves_validation_first_gate(self) -> None:
        text = OVERNIGHT_LOOP.read_text(encoding="utf-8")

        self.assertIn("production build gate remains closed", text)
        self.assertIn("customer validation is `insufficient_data`", text)
        self.assertIn("Only `build_next_slice` opens production platform work", text)
        self.assertIn("`pilot_pull_detected` means convert design partners first", text)
        self.assertIn("make validation-dashboard DATE=YYYY-MM-DD", text)
        self.assertIn("make goal-resume DATE=YYYY-MM-DD", text)
        self.assertIn("Do not pick production platform work", text)
        self.assertIn("Do not mark messages sent", text)
        self.assertIn("Do not commit anything under `validation/private/`", text)
        self.assertIn("Copy-only outreach/send-boundary safety", text)

    def test_prompt_no_longer_recommends_old_platform_slices_first(self) -> None:
        text = OVERNIGHT_LOOP.read_text(encoding="utf-8")

        self.assertNotIn("Policy JSON Schema and CLI validation", text)
        self.assertNotIn("Sandbox artifact schema and negative validation fixture", text)
        self.assertNotIn("Console policy status/error states", text)

    def test_overnight_docs_are_marked_historical_context(self) -> None:
        for path in [OVERNIGHT_CHANGE_REPORT, OVERNIGHT_CONSOLIDATION_TODO]:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                compact = " ".join(text.split())

                self.assertIn("Historical context", text)
                self.assertIn("docs/CODEX_CEO_FINISH_BRIEF.md", text)
                self.assertIn("docs/PROPHET_COMPLETION_AUDIT.md", text)
                self.assertIn("docs/PROPHET_TODO.md", text)
                self.assertIn("validation dashboard", compact)
                self.assertIn("customer validation remains `insufficient_data`", compact)
                self.assertIn("Do not use", text)


if __name__ == "__main__":
    unittest.main()
