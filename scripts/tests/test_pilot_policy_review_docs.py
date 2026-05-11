from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_REVIEW = ROOT / "docs" / "PILOT_POLICY_REVIEW.md"


class PilotPolicyReviewDocsTests(unittest.TestCase):
    def test_source_terms_and_customer_allowlist_are_documented(self) -> None:
        text = POLICY_REVIEW.read_text(encoding="utf-8")

        required_phrases = [
            "## Source Terms And License Review",
            "is not permission to",
            "collect, store, redistribute, or automate against that source",
            "Public documentation or terms URL reviewed",
            "retention.raw_collection_retained",
            "## Customer-Approved Source Allowlist",
            "customer_approval_owner",
            "approved_collection_mode",
            "raw_collection_retained: false",
            "## Future Source Catalog Changes",
            "policy/source-catalog-allowlist.json",
            "does not grant live",
            "collection, bypass source terms, or authorize customer data handling",
            "## Future Required-Source Failure Budgets",
            "failure_action: block_forecast_and_evidence",
            "If a required source is unavailable, stale beyond the approved freshness",
            "forecast and evidence generation must fail closed",
            "Implementation remains gated on buyer/security-review demand or",
            "`build_next_slice`",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
