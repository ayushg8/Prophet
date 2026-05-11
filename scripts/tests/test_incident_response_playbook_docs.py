from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = ROOT / "docs" / "INCIDENT_RESPONSE_PLAYBOOK.md"
BACKLOG = ROOT / "docs" / "production-readiness-backlog.json"
TODO = ROOT / "docs" / "PROPHET_TODO.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"
GAP_MAP = ROOT / "docs" / "COMPLIANCE_GAP_MAP.md"


class IncidentResponsePlaybookDocsTests(unittest.TestCase):
    def test_playbook_covers_required_incident_classes(self) -> None:
        text = PLAYBOOK.read_text(encoding="utf-8")

        for required in (
            "Data Spill",
            "Credential Exposure",
            "Policy Bypass",
            "Integration Misfire",
            "Sandbox Escape",
            "Customer Notification",
        ):
            self.assertIn(required, text)

        self.assertIn("Do not include raw customer data", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)
        self.assertIn("make release-hygiene", text)

    def test_readiness_backlog_marks_only_incident_playbook_done(self) -> None:
        backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
        item = next(
            work_item
            for milestone in backlog["milestones"]
            for work_item in milestone["work_items"]
            if work_item["id"] == "M8-04"
        )

        self.assertEqual(item["status"], "done")
        self.assertEqual(item["evidence_paths"], ["docs/INCIDENT_RESPONSE_PLAYBOOK.md"])

    def test_operator_boards_reference_playbook_without_claiming_cmmc_ready(self) -> None:
        todo = TODO.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")
        gap_map = GAP_MAP.read_text(encoding="utf-8")

        self.assertIn("docs/INCIDENT_RESPONSE_PLAYBOOK.md", todo)
        self.assertIn("[x] Add incident response playbook.", master_todo)
        self.assertIn("Run a tabletop exercise", gap_map)
        self.assertIn("Do not represent the current local pilot as CMMC-ready", gap_map)


if __name__ == "__main__":
    unittest.main()
