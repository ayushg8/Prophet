from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/PRODUCT_VALIDATION_PLAN.md"
GUIDE = ROOT / "docs/CUSTOMER_DISCOVERY_GUIDE.md"
OUTREACH = ROOT / "docs/OUTREACH_PLAYBOOK.md"
DAILY = ROOT / "docs/VALIDATION_DAILY_BRIEF.md"


class ProductValidationPlanDocsTests(unittest.TestCase):
    def test_plan_distinguishes_pilot_pull_from_build_gate(self) -> None:
        text = PLAN.read_text(encoding="utf-8")

        self.assertIn("Only `build_next_slice` opens the production build gate.", text)
        self.assertIn("`pilot_pull_detected` is a design-partner conversion signal", text)
        self.assertIn("`target_backed_validation`", text)
        self.assertIn("`call_booked` or `completed`", text)
        self.assertIn("segment/persona metadata matches", text)
        self.assertIn("not permission to", text)
        self.assertIn("private validation dashboard reaches `build_next_slice`", text)

        guide = GUIDE.read_text(encoding="utf-8")
        for required_field in [
            "Qualified/not-qualified call flag",
            "Status quo gap",
            "`workflow_pain_theme`",
            "`pain_score`",
            "`urgency_score`",
            "`status_quo_weakness_score`",
            "`buyer_access_score`",
            "`data_feasibility_score`",
            "`pilot_pull_score`",
            "Budget signal",
            "Pilot signal",
        ]:
            with self.subTest(required_field=required_field):
                self.assertIn(required_field, guide)

    def test_reply_triage_keeps_private_details_out_of_tracker(self) -> None:
        for path in (OUTREACH, DAILY):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("book_call", text)
                self.assertIn("disqualify", text)
                self.assertIn("keep_pending", text)
                self.assertIn("manual_review", text)
                self.assertIn("Never paste reply text", text)
                self.assertIn("names, emails, phone numbers, URLs, hostnames, IPs", text)
                self.assertIn("validation-reply-triage.py", text)
                self.assertIn("make validation-reply-triage", text)
                self.assertIn("sanitized classification", text)
                self.assertIn("make validation-book-call", text)
                self.assertIn("make validation-disqualify-target", text)

    def test_outreach_copy_guidance_is_placeholder_free(self) -> None:
        for path in (OUTREACH, DAILY):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("copy the generated subject/body as-is", text)
                self.assertIn("personalize only in the outreach channel", text)
                self.assertIn("Do not store recipient", text)
                self.assertNotIn("replace only the recipient name", text)
                self.assertNotIn("<first name>", text)


if __name__ == "__main__":
    unittest.main()
