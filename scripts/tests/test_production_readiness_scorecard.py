from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "production-readiness-scorecard.py"
BACKLOG = ROOT / "docs" / "production-readiness-backlog.json"
SPEC = importlib.util.spec_from_file_location("production_readiness_scorecard", SCRIPT)
assert SPEC and SPEC.loader
scorecard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scorecard
SPEC.loader.exec_module(scorecard)


class ProductionReadinessScorecardTests(unittest.TestCase):
    def test_default_backlog_validates_and_scores(self) -> None:
        backlog = scorecard.load_json(BACKLOG)
        summary = scorecard.build_scorecard(backlog, root=ROOT)

        self.assertEqual(
            summary["schema_version"],
            scorecard.SCORECARD_SCHEMA_VERSION,
        )
        self.assertEqual(summary["milestone_count"], 9)
        self.assertGreaterEqual(summary["work_item_count"], 40)
        self.assertGreater(summary["critical_open_count"], 0)
        self.assertIn("P0", summary["priority_statuses"])

    def test_done_work_items_require_existing_evidence_paths(self) -> None:
        backlog = scorecard.load_json(BACKLOG)
        item = copy.deepcopy(backlog["milestones"][0]["work_items"][0])
        item["id"] = "M0-99"
        item["evidence_paths"] = []
        backlog["milestones"][0]["work_items"].append(item)

        errors = scorecard.validate_backlog(backlog, root=ROOT)

        self.assertTrue(any("evidence_paths is required" in error for error in errors))

    def test_unknown_risk_tag_is_rejected(self) -> None:
        backlog = scorecard.load_json(BACKLOG)
        backlog["milestones"][0]["work_items"][0]["risk_tags"].append("magic")

        errors = scorecard.validate_backlog(backlog, root=ROOT)

        self.assertTrue(any("unknown tags" in error for error in errors))

    def test_blocked_work_items_require_blocker(self) -> None:
        backlog = scorecard.load_json(BACKLOG)
        blocked = backlog["milestones"][4]["work_items"][4]
        self.assertEqual(blocked["status"], "blocked")
        del blocked["blocker"]

        errors = scorecard.validate_backlog(backlog, root=ROOT)

        self.assertTrue(any("blocker is required" in error for error in errors))

    def test_public_release_review_is_blocked_on_secret_history_decision(self) -> None:
        backlog = scorecard.load_json(BACKLOG)
        item = next(
            work_item
            for milestone in backlog["milestones"]
            for work_item in milestone["work_items"]
            if work_item["id"] == "M8-03"
        )

        self.assertEqual(item["status"], "blocked")
        self.assertIn("LOG4SHELL_INSTRUCTIONS.md", item["blocker"])
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", item["blocker"])


if __name__ == "__main__":
    unittest.main()
