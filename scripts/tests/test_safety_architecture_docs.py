from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SAFETY_ARCHITECTURE = ROOT / "docs" / "SAFETY_ARCHITECTURE.md"
DATA_INVENTORY = ROOT / "docs" / "DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md"


class SafetyArchitectureDocsTests(unittest.TestCase):
    def test_raw_to_sanitized_boundary_is_documented(self) -> None:
        text = SAFETY_ARCHITECTURE.read_text(encoding="utf-8")

        required_phrases = [
            "## Raw-To-Sanitized Boundary",
            "Raw collection zone",
            "Sanitization gate",
            "Product zone",
            "source_ref metadata",
            "Raw source body or scraper output fields",
            "Live target URLs",
            "evidence/bundle.py",
            "scripts/check-default-output-safety.py",
            "scripts/check-release-safety.py",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_private_outreach_send_copy_boundary_is_documented(self) -> None:
        text = DATA_INVENTORY.read_text(encoding="utf-8")

        self.assertIn("Outreach/message packs and status", text)
        self.assertIn("today-send-copy.txt", text)
        self.assertIn("one subject line plus the message body", text)
        self.assertIn("omits target labels, tracker commands, alternate subject options", text)
        self.assertIn("matching ready states for the next draft and send-copy file", text)
        self.assertIn("send-copy readiness", text)
        self.assertIn("Export aggregate counts only", text)

    def test_pilot_mode_threat_model_is_documented(self) -> None:
        text = SAFETY_ARCHITECTURE.read_text(encoding="utf-8")

        required_phrases = [
            "## Pilot Mode Threat Model",
            "fixture-backed, localhost-only",
            "validation/private/",
            "Copy-only outreach text to private tracker/audit metadata",
            "dashboard-first recovery",
            "exact `CONFIRM_SENT=1`",
            "Localhost console actions",
            "example validation seed data",
            "ignores atomic `.tmp.` files",
            "production build gate closed until real validation reaches `build_next_slice`",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
