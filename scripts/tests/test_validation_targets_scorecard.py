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
        self.assertEqual(summary["target_count"], 2)
        self.assertEqual(summary["active_target_count"], 2)
        self.assertIn("Add more anonymized targets", summary["next_action"])

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


if __name__ == "__main__":
    unittest.main()
