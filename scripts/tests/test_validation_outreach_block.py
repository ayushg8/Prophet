from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation-outreach-block.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"
SPEC = importlib.util.spec_from_file_location("validation_outreach_block", SCRIPT)
assert SPEC and SPEC.loader
outreach_block = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = outreach_block
SPEC.loader.exec_module(outreach_block)


class ValidationOutreachBlockTests(unittest.TestCase):
    def test_example_targets_generate_daily_block(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))

        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")

        self.assertEqual(
            block["schema_version"],
            outreach_block.OUTREACH_BLOCK_SCHEMA_VERSION,
        )
        self.assertEqual(block["generated_for"], "2026-05-10")
        self.assertEqual(len(block["targeted_asks"]), 5)
        self.assertEqual(len(block["referral_asks"]), 1)
        self.assertEqual(len(block["follow_ups"]), 0)
        self.assertEqual(block["gaps"]["follow_up_gap_count"], 2)
        self.assertEqual(len(block["follow_up_backfill_asks"]), 2)
        self.assertEqual(block["gaps"]["follow_up_backfill_count"], 2)
        self.assertTrue(all(target["priority"] == "P0" for target in block["targeted_asks"]))
        selected_labels = {
            target["target_label"]
            for group in (
                block["targeted_asks"],
                block["referral_asks"],
                block["follow_up_backfill_asks"],
            )
            for target in group
        }
        self.assertEqual(
            len(selected_labels),
            len(block["targeted_asks"])
            + len(block["referral_asks"])
            + len(block["follow_up_backfill_asks"]),
        )

    def test_follow_ups_are_selected_before_gap_report(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["follow_up_due"] = "2026-05-10"
        targets["targets"][1]["status"] = "follow_up_due"
        targets["targets"][1]["follow_up_due"] = "2026-05-10"

        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")

        self.assertEqual(len(block["follow_ups"]), 2)
        self.assertEqual(block["gaps"]["follow_up_gap_count"], 0)
        self.assertEqual(block["follow_up_backfill_asks"], [])
        self.assertEqual(
            [target["target_label"] for target in block["follow_ups"]],
            ["target-dib-platform-001", "target-dib-platform-002"],
        )

    def test_outreach_sent_targets_are_selected_when_follow_up_date_arrives(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        block = outreach_block.build_outreach_block(targets, run_date="2026-05-13")

        self.assertEqual(
            [target["target_label"] for target in block["follow_ups"]],
            ["target-dib-platform-001"],
        )
        self.assertEqual(block["gaps"]["follow_up_gap_count"], 1)
        self.assertEqual(len(block["follow_up_backfill_asks"]), 1)
        selected_labels = [
            target["target_label"]
            for group in (
                block["targeted_asks"],
                block["follow_ups"],
                block["referral_asks"],
                block["follow_up_backfill_asks"],
            )
            for target in group
        ]
        self.assertEqual(len(selected_labels), len(set(selected_labels)))

    def test_outreach_sent_targets_are_not_selected_before_follow_up_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"

        block = outreach_block.build_outreach_block(targets, run_date="2026-05-12")

        self.assertEqual(block["follow_ups"], [])
        self.assertEqual(block["gaps"]["follow_up_gap_count"], 2)

    def test_rejects_sensitive_target_text(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets = copy.deepcopy(targets)
        targets["targets"][0]["next_action"] = "Email buyer@example.com"

        with self.assertRaisesRegex(outreach_block.OutreachBlockError, "email-like"):
            outreach_block.build_outreach_block(targets, run_date="2026-05-10")

    def test_rejects_bad_run_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(outreach_block.OutreachBlockError, "YYYY-MM-DD"):
            outreach_block.build_outreach_block(targets, run_date="05/10/2026")

    def test_markdown_includes_gap_without_private_data(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")

        rendered = outreach_block.render_markdown(block)

        self.assertIn("Prophet Outreach Block - 2026-05-10", rendered)
        self.assertIn("No follow-ups are currently due", rendered)
        self.assertIn("Follow-Up Gap Backfill", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)


if __name__ == "__main__":
    unittest.main()
