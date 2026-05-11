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
        self.assertEqual(summary["repeated_workflow_pain_count"], 1)
        self.assertEqual(summary["top_workflow_pain_theme"], "evidence_packet_gap")
        self.assertTrue(summary["example_seed_log"])
        self.assertEqual(summary["raw_verdict"], "insufficient_data")
        self.assertEqual(
            summary["effective_validation_counts"],
            {
                "qualified_count": 0,
                "high_pain_count": 0,
                "repeated_workflow_pain_count": 0,
                "pilot_pull_count": 0,
                "paid_or_sponsored_count": 0,
            },
        )
        self.assertEqual(
            summary["gaps_to_verdicts"]["pilot_pull_detected"],
            {
                "qualified_count": 15,
                "high_pain_count": 5,
                "repeated_workflow_pain_count": 5,
                "pilot_pull_count": 2,
            },
        )
        self.assertEqual(
            summary["gaps_to_verdicts"]["build_next_slice"],
            {
                "qualified_count": 15,
                "high_pain_count": 8,
                "repeated_workflow_pain_count": 5,
                "pilot_pull_count": 3,
                "paid_or_sponsored_count": 1,
            },
        )
        self.assertEqual(summary["verdict"], "insufficient_data")
        self.assertIn("example-only validation seed", summary["next_action"])

    def test_build_next_slice_requires_paid_or_sponsored_pilot_signal(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
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
        self.assertEqual(summary["repeated_workflow_pain_count"], 15)
        self.assertEqual(summary["pilot_pull_count"], 3)
        self.assertEqual(summary["paid_or_sponsored_count"], 1)
        self.assertFalse(summary["example_seed_log"])
        self.assertEqual(summary["raw_verdict"], "build_next_slice")
        self.assertTrue(
            all(value == 0 for value in summary["gaps_to_verdicts"]["build_next_slice"].values())
        )
        self.assertEqual(summary["verdict"], "build_next_slice")

    def test_example_seed_log_cannot_open_build_gate_verdict(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-seed-gate-{index:03d}"
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        summary = scorecard.build_scorecard(log)

        self.assertTrue(summary["example_seed_log"])
        self.assertEqual(summary["raw_verdict"], "build_next_slice")
        self.assertEqual(summary["verdict"], "insufficient_data")
        self.assertEqual(
            summary["effective_validation_counts"],
            {
                "qualified_count": 0,
                "high_pain_count": 0,
                "repeated_workflow_pain_count": 0,
                "pilot_pull_count": 0,
                "paid_or_sponsored_count": 0,
            },
        )
        self.assertEqual(
            summary["gaps_to_verdicts"]["build_next_slice"],
            {
                "qualified_count": 15,
                "high_pain_count": 8,
                "repeated_workflow_pain_count": 5,
                "pilot_pull_count": 3,
                "paid_or_sponsored_count": 1,
            },
        )
        self.assertIn("example-only validation seed", summary["next_action"])

    def test_build_next_slice_requires_repeated_workflow_pain(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        template = copy.deepcopy(log["interviews"][0])
        themes = [
            "evidence_packet_gap",
            "leadership_briefing_gap",
            "soc_ticket_handoff_gap",
            "asset_sbom_context_gap",
        ]
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-scattered-pain-{index:03d}"
            interview["workflow_pain_theme"] = themes[index % len(themes)]
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        summary = scorecard.build_scorecard(log)

        self.assertEqual(summary["qualified_count"], 15)
        self.assertEqual(summary["high_pain_count"], 15)
        self.assertEqual(summary["pilot_pull_count"], 3)
        self.assertEqual(summary["paid_or_sponsored_count"], 1)
        self.assertLess(summary["repeated_workflow_pain_count"], 5)
        self.assertEqual(summary["verdict"], "keep_discovering")

    def test_pilot_pull_detected_requires_repeated_workflow_pain(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        template = copy.deepcopy(log["interviews"][0])
        themes = [
            "evidence_packet_gap",
            "leadership_briefing_gap",
            "soc_ticket_handoff_gap",
            "asset_sbom_context_gap",
        ]
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-pilot-pull-{index:03d}"
            interview["workflow_pain_theme"] = (
                "evidence_packet_gap" if index < 5 else themes[index % len(themes)]
            )
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 2 else "asked_for_demo"
            interview["budget_signal"] = "budget_owner_named"
            log["interviews"].append(interview)

        summary = scorecard.build_scorecard(log)

        self.assertEqual(summary["repeated_workflow_pain_count"], 7)
        self.assertEqual(summary["pilot_pull_count"], 2)
        self.assertEqual(summary["paid_or_sponsored_count"], 0)
        self.assertEqual(summary["verdict"], "pilot_pull_detected")

    def test_low_pain_after_five_calls_is_do_not_build_yet(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
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

    def test_rejects_unknown_workflow_pain_theme(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["interviews"][0]["workflow_pain_theme"] = "interesting_chat"

        errors = scorecard.validate_log(log)

        self.assertTrue(any("workflow_pain_theme is unsupported" in error for error in errors))

    def test_rejects_empty_existing_tools(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["interviews"][0]["existing_tools"] = []

        errors = scorecard.validate_log(log)

        self.assertTrue(any("existing_tools must be non-empty" in error for error in errors))

    def test_rejects_malformed_updated_at(self) -> None:
        log = scorecard.load_json(EXAMPLE)
        log["updated_at"] = "05/10/2026"

        errors = scorecard.validate_log(log)

        self.assertTrue(any("updated_at must be YYYY-MM-DD" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
