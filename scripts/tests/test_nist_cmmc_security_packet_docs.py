from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "NIST_CMMC_SECURITY_PACKET.md"
BACKLOG = ROOT / "docs" / "production-readiness-backlog.json"
TODO = ROOT / "docs" / "PROPHET_TODO.md"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"
GAP_MAP = ROOT / "docs" / "COMPLIANCE_GAP_MAP.md"


class NistCmmcSecurityPacketDocsTests(unittest.TestCase):
    def test_packet_contains_required_review_sections(self) -> None:
        text = PACKET.read_text(encoding="utf-8")

        for required in (
            "SSP Draft",
            "CMMC/NIST Control Matrix",
            "Data Flows",
            "Asset Inventory",
            "Access Controls",
            "Incident Response",
            "POA&M",
        ):
            self.assertIn(required, text)

        self.assertIn("NIST SP 800-171 Rev. 3", text)
        self.assertIn("NIST SP 800-171A Rev. 3", text)
        self.assertIn("CMMC Phase 1 implementation began on 2025-11-10", text)
        self.assertIn("docs/INCIDENT_RESPONSE_PLAYBOOK.md", text)
        self.assertIn("docs/SOFTWARE_SUPPLY_CHAIN_PACKET.md", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)

    def test_packet_keeps_cmmc_non_claims_explicit(self) -> None:
        text = PACKET.read_text(encoding="utf-8")

        self.assertIn("It is not a certification claim", text)
        self.assertIn("Prophet is not authorized for CUI/FCI handling", text)
        self.assertIn('"Prophet is CMMC-ready."', text)
        self.assertIn('"Prophet is NIST 800-171 compliant."', text)
        self.assertIn("Production build scope remains gated", text)
        self.assertIn("`build_next_slice`", text)

    def test_backlog_marks_security_packet_done_with_evidence(self) -> None:
        backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
        item = next(
            work_item
            for milestone in backlog["milestones"]
            for work_item in milestone["work_items"]
            if work_item["id"] == "M8-01"
        )

        self.assertEqual(item["status"], "done")
        self.assertEqual(item["evidence_paths"], ["docs/NIST_CMMC_SECURITY_PACKET.md"])

    def test_operator_boards_reference_packet_without_cmmc_ready_claim(self) -> None:
        todo = TODO.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")
        gap_map = GAP_MAP.read_text(encoding="utf-8")

        self.assertIn("docs/NIST_CMMC_SECURITY_PACKET.md", todo)
        self.assertIn("[x] Add NIST/CMMC-oriented security packet.", master_todo)
        self.assertIn("docs/NIST_CMMC_SECURITY_PACKET.md", gap_map)
        self.assertIn("Do not represent the current local pilot as CMMC-ready", gap_map)


if __name__ == "__main__":
    unittest.main()
