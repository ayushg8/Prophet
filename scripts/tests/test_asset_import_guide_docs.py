from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs" / "ASSET_IMPORT_GUIDE.md"


class AssetImportGuideDocsTests(unittest.TestCase):
    def test_customer_safe_fixture_generation_is_documented(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")

        required_phrases = [
            "## Generating Customer-Safe Fixture Examples",
            "workflow class, not a named customer environment",
            "synthetic `asset_id` values",
            "queue-style `owner_group` values",
            "public CVE IDs only",
            "check-release-safety.py",
            "Runtime inventory, report, and",
            "Live IPs, private hostnames, URLs, or target endpoints",
            "Raw scanner exports, raw telemetry, raw logs, raw scraper text",
            "## SBOM JSON Imports",
            "assets.sbom_import",
            "dib-edge-appliance-sbom.cyclonedx.json",
            "financial-workflow-sbom.spdx.json",
            "It does not embed",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
