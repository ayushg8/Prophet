from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "customer-validation-scorecard.py"
EXAMPLE = ROOT / "docs" / "customer-validation-log.example.json"
SPEC = importlib.util.spec_from_file_location("customer_validation_scorecard", SCRIPT)
assert SPEC and SPEC.loader
scorecard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scorecard
SPEC.loader.exec_module(scorecard)


class CustomerValidationScorecardTests(unittest.TestCase):
    def test_example_log_scores_as_insufficient_data(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        summary = scorecard.build_scorecard(log)

        self.assertEqual(summary["schema_version"], scorecard.SCORECARD_SCHEMA_VERSION)
        self.assertEqual(summary["interview_count"], 1)
        self.assertEqual(summary["qualified_count"], 1)
        self.assertEqual(summary["verdict"], "insufficient_data")

    def test_build_next_slice_requires_paid_or_sponsored_pilot_signal(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-account-{index:03d}"
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        summary = scorecard.build_scorecard(log)

        self.assertEqual(summary["qualified_count"], 15)
        self.assertEqual(summary["high_pain_count"], 15)
        self.assertEqual(summary["pilot_pull_count"], 3)
        self.assertEqual(summary["paid_or_sponsored_count"], 1)
        self.assertEqual(summary["verdict"], "build_next_slice")

    def test_low_pain_after_five_calls_is_do_not_build_yet(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        template = copy.deepcopy(log["interviews"][0])
        template["pain_score"] = 2
        template["urgency_score"] = 2
        template["status_quo_weakness_score"] = 2
        log["interviews"] = []
        for index in range(5):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-low-pain-{index:03d}"
            interview["budget_signal"] = "none"
            interview["pilot_signal"] = "none"
            log["interviews"].append(interview)

        summary = scorecard.build_scorecard(log)

        self.assertEqual(summary["verdict"], "do_not_build_yet")

    def test_rejects_committed_sensitive_contact_data(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["interviews"][0]["next_step"] = "Email buyer@example.com"

        errors = scorecard.validate_log(log)

        self.assertTrue(any("email-like" in error for error in errors))

    def test_rejects_private_hostname_text(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["interviews"][0]["current_workflow"] = "Review scanner for app.prod"

        errors = scorecard.validate_log(log)

        self.assertTrue(any("private hostname-like" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
