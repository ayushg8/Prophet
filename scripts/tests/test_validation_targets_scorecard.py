from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation-targets-scorecard.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"
SPEC = importlib.util.spec_from_file_location("validation_targets_scorecard", SCRIPT)
assert SPEC and SPEC.loader
scorecard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scorecard
SPEC.loader.exec_module(scorecard)


class ValidationTargetsScorecardTests(unittest.TestCase):
    def test_example_target_list_validates(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        summary = scorecard.build_scorecard(targets)

        self.assertEqual(summary["schema_version"], scorecard.SCORECARD_SCHEMA_VERSION)
        self.assertEqual(summary["target_count"], 30)
        self.assertEqual(summary["active_target_count"], 30)
        self.assertGreaterEqual(summary["p0_active_count"], 10)
        self.assertIn("Run today's outreach block", summary["next_action"])
        self.assertIn("follow-up backfill", summary["next_action"])

    def test_duplicate_target_labels_are_rejected(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets["targets"].append(copy.deepcopy(targets["targets"][0]))

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("duplicates" in error for error in errors))

    def test_email_and_url_like_text_are_rejected(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets["targets"][0]["next_action"] = "Email buyer@example.com at https://example.com"

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("email-like" in error for error in errors))
        self.assertTrue(any("URL-like" in error for error in errors))

    def test_ready_target_list_prompts_daily_outreach(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        template = targets["targets"][0]
        targets["targets"] = []
        for index in range(30):
            target = copy.deepcopy(template)
            target["target_label"] = f"target-{index:03d}"
            target["priority"] = "P0" if index < 12 else "P1"
            target["status"] = "identified"
            targets["targets"].append(target)

        summary = scorecard.build_scorecard(targets)

        self.assertEqual(summary["target_count"], 30)
        self.assertEqual(summary["p0_active_count"], 12)
        self.assertIn("Run today's outreach block", summary["next_action"])
        self.assertIn("2 follow-up backfill asks", summary["next_action"])

    def test_one_due_follow_up_prompts_one_backfill_ask(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["follow_up_due"] = "2026-05-10"

        summary = scorecard.build_scorecard(targets)

        self.assertEqual(summary["follow_up_due_count"], 1)
        self.assertIn("1 due follow-up", summary["next_action"])
        self.assertIn("1 follow-up backfill ask", summary["next_action"])

    def test_two_due_follow_ups_prompt_due_follow_ups(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["follow_up_due"] = "2026-05-10"
        targets["targets"][1]["status"] = "follow_up_due"
        targets["targets"][1]["follow_up_due"] = "2026-05-10"

        summary = scorecard.build_scorecard(targets)

        self.assertEqual(summary["follow_up_due_count"], 2)
        self.assertIn("2 due follow-ups", summary["next_action"])
        self.assertNotIn("backfill", summary["next_action"])

    def test_malformed_target_dates_are_rejected(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["last_touch"] = "05/10/2026"
        targets["targets"][1]["follow_up_due"] = 20260510

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("last_touch must be YYYY-MM-DD" in error for error in errors))
        self.assertTrue(any("follow_up_due must be YYYY-MM-DD" in error for error in errors))

    def test_malformed_updated_at_is_rejected(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets["updated_at"] = "05/10/2026"

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("updated_at must be YYYY-MM-DD" in error for error in errors))

    def test_follow_up_due_status_requires_date(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["follow_up_due"] = ""

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("follow_up_due is required" in error for error in errors))

    def test_advanced_statuses_clear_follow_up_due(self) -> None:
        targets = scorecard.load_json(EXAMPLE)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "call_booked"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        errors = scorecard.validate_targets(targets)

        self.assertTrue(any("follow_up_due must be empty" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
