from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "SOFTWARE_SUPPLY_CHAIN_PACKET.md"
BACKLOG = ROOT / "docs" / "production-readiness-backlog.json"
TODO = ROOT / "docs" / "PROPHET_TODO.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"


class SoftwareSupplyChainPacketDocsTests(unittest.TestCase):
    def test_packet_contains_required_review_sections(self) -> None:
        text = PACKET.read_text(encoding="utf-8")

        for required in (
            "Dependency Inventory",
            "SBOM Summary",
            "Provenance Target",
            "Vulnerability Process",
            "Update Cadence",
        ):
            self.assertIn(required, text)

        self.assertIn("prophet-console/package-lock.json", text)
        self.assertIn("world-side/scraper/requirements.txt", text)
        self.assertIn("make supply-chain-sbom DATE=YYYY-MM-DD", text)
        self.assertIn("evidence/outputs/runtime/supply-chain/prophet-supply-chain-sbom.json", text)
        self.assertIn("not a CycloneDX/SPDX release asset", text)
        self.assertIn("npm audit --audit-level=moderate", text)
        self.assertIn("docs/INCIDENT_RESPONSE_PLAYBOOK.md", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)

    def test_backlog_marks_supply_chain_packet_done_with_evidence(self) -> None:
        backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
        item = next(
            work_item
            for milestone in backlog["milestones"]
            for work_item in milestone["work_items"]
            if work_item["id"] == "M8-02"
        )

        self.assertEqual(item["status"], "done")
        self.assertEqual(item["evidence_paths"], ["docs/SOFTWARE_SUPPLY_CHAIN_PACKET.md"])

    def test_operator_boards_reference_supply_chain_packet(self) -> None:
        todo = TODO.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")

        self.assertIn("docs/SOFTWARE_SUPPLY_CHAIN_PACKET.md", todo)
        self.assertIn("make supply-chain-sbom DATE=YYYY-MM-DD", todo)
        self.assertIn("[x] Add software supply-chain risk register.", master_todo)
        self.assertIn("[x] Add SBOM for Prophet itself.", master_todo)


if __name__ == "__main__":
    unittest.main()
