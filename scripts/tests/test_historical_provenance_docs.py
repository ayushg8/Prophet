from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_DOCS = [
    ROOT / "HACKATHON.md",
    ROOT / "PROPHET_TECHNICAL_WRITEUP.md",
]


class HistoricalProvenanceDocsTests(unittest.TestCase):
    def test_old_hackathon_docs_are_marked_historical(self) -> None:
        for path in HISTORICAL_DOCS:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                compact = " ".join(text.replace("> ", "").split())

                self.assertIn("Historical context", text)
                self.assertIn("not the current product direction", text)
                self.assertIn("docs/CODEX_CEO_FINISH_BRIEF.md", text)
                self.assertIn("docs/PROPHET_COMPLETION_AUDIT.md", text)
                self.assertIn("policy-bound defensive exposure evidence workflow", compact)
                self.assertIn("not zero-day prediction", compact)


if __name__ == "__main__":
    unittest.main()
