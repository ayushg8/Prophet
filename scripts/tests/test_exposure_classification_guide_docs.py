from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs" / "EXPOSURE_CLASSIFICATION_GUIDE.md"
ASSET_GUIDE = ROOT / "docs" / "ASSET_IMPORT_GUIDE.md"
PILOT_SCOPE = ROOT / "docs" / "PILOT_SCOPE.md"
WORKSHEET = ROOT / "docs" / "EVALUATOR_WORKSHEET.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"


class ExposureClassificationGuideDocsTests(unittest.TestCase):
    def test_guide_defines_safe_exposure_classification(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")

        required_phrases = [
            "An exposure class is a broad defensive category",
            "hostname, IP address, URL",
            "`edge_appliance`",
            "`financial_workflow`",
            "`custody_workflow`",
            "`payment_operations`",
            "Start with the buyer's painful prioritization event",
            "Reject the class if the buyer must provide targetable details",
            "known_cve_overlaps",
            "check-release-safety.py",
            "target-backed interviews",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_related_docs_link_the_guide(self) -> None:
        for path in (ASSET_GUIDE, PILOT_SCOPE, WORKSHEET):
            with self.subTest(path=path.name):
                self.assertIn(
                    "docs/EXPOSURE_CLASSIFICATION_GUIDE.md",
                    path.read_text(encoding="utf-8"),
                )

    def test_master_todo_marks_guide_complete(self) -> None:
        text = MASTER_TODO.read_text(encoding="utf-8")

        self.assertIn("[x] Add exposure classification guide.", text)

    def test_master_todo_marks_evaluator_worksheet_complete(self) -> None:
        text = MASTER_TODO.read_text(encoding="utf-8")
        worksheet = WORKSHEET.read_text(encoding="utf-8")

        self.assertIn("[x] A customer-facing evaluator worksheet exists.", text)
        self.assertIn("[x] Add CISO evaluator checklist.", text)
        self.assertIn("[x] Day 6: Add customer evaluator worksheet and CISO checklist.", text)
        self.assertIn("## CISO / Executive Review", worksheet)
        self.assertIn("Executive go/no-go", worksheet)
        self.assertIn("Build next slice", worksheet)


if __name__ == "__main__":
    unittest.main()
