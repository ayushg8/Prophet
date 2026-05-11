from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SIGNED_POLICY_DESIGN = ROOT / "docs" / "SIGNED_POLICY_DESIGN.md"
PILOT_POLICY_REVIEW = ROOT / "docs" / "PILOT_POLICY_REVIEW.md"
THREAT_MODEL = ROOT / "docs" / "THREAT_MODEL.md"
PRODUCTION_ARCHITECTURE = ROOT / "docs" / "PRODUCTION_ARCHITECTURE.md"
DATA_INVENTORY = ROOT / "docs" / "DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"
OPERATOR_TODO = ROOT / "docs" / "PROPHET_TODO.md"


class SignedPolicyDesignDocsTests(unittest.TestCase):
    def test_signed_policy_design_is_gated_and_non_implementing(self) -> None:
        text = SIGNED_POLICY_DESIGN.read_text(encoding="utf-8")

        required_phrases = [
            "This design describes how Prophet should make policy files tamper-evident",
            "does not implement signing, create keys",
            "prophet_signed_policy.v0.1",
            "policy.lint --verify-runtime-artifacts",
            "unsigned_design_only",
            "Private keys must never be committed",
            "Do not implement policy signing, key handling, signature verification",
            "The validation dashboard reaches `build_next_slice`",
            "Verification failure must block sharing the review bundle",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_related_docs_cross_reference_signed_policy_design(self) -> None:
        expectations = {
            PILOT_POLICY_REVIEW: "docs/SIGNED_POLICY_DESIGN.md",
            THREAT_MODEL: "Signed policy design",
            PRODUCTION_ARCHITECTURE: "signed policy implementation",
            DATA_INVENTORY: "Signed policy implementation",
            MASTER_TODO: "[x] Add policy signing design.",
            OPERATOR_TODO: "Signed policy design exists",
        }

        for path, phrase in expectations.items():
            with self.subTest(path=str(path), phrase=phrase):
                self.assertIn(phrase, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
