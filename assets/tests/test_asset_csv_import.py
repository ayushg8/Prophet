from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from assets.import_csv import import_asset_csv, main
from assets.inventory import load_json, validate_asset_inventory, validate_asset_seedset
from assets.inventory import build_asset_seedset


ROOT = Path(__file__).resolve().parents[2]
CSV_FIXTURE = ROOT / "assets/fixtures/customer-asset-import.csv"
FIXED_TIME = "2026-05-05T04:40:00Z"


class AssetCsvImportTests(unittest.TestCase):
    def test_imports_safe_customer_csv(self) -> None:
        result = import_asset_csv(
            CSV_FIXTURE,
            inventory_id="customer-csv-import-test",
            generated_at=FIXED_TIME,
            fixture=True,
        )
        inventory = result["inventory"]
        report = result["report"]
        validate_asset_inventory(inventory)
        self.assertEqual(report["accepted_count"], 2)
        self.assertEqual(report["rejected_count"], 0)
        seedset = build_asset_seedset(
            inventory,
            generated_at=FIXED_TIME,
            run_id="customer-csv-seedset-test",
        )
        validate_asset_seedset(seedset)

    def test_rejects_unsafe_rows_without_rejecting_safe_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assets.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "asset_id",
                        "product_family",
                        "exposure_class",
                        "owner_group",
                        "environment",
                        "business_criticality",
                        "sbom_components",
                        "known_cve_overlaps",
                        "compensating_controls",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "asset_id": "asset-safe-001",
                        "product_family": "secure edge appliance family",
                        "exposure_class": "edge_appliance",
                        "owner_group": "Edge Platform Security",
                        "environment": "mission partner enclave",
                        "business_criticality": "high",
                        "sbom_components": "log4j-core@2.x legacy:java-library",
                        "known_cve_overlaps": "CVE-2021-44228",
                        "compensating_controls": "centralized web log collection",
                    }
                )
                writer.writerow(
                    {
                        "asset_id": "asset-bad-001",
                        "product_family": "secure edge appliance family",
                        "exposure_class": "edge_appliance",
                        "owner_group": "Edge Platform Security",
                        "environment": "prod-edge.example.com",
                        "business_criticality": "high",
                        "sbom_components": "log4j-core@2.x legacy:java-library",
                        "known_cve_overlaps": "CVE-2021-44228",
                        "compensating_controls": "password=fixture",
                    }
                )

            result = import_asset_csv(
                path,
                inventory_id="customer-csv-reject-test",
                generated_at=FIXED_TIME,
            )
            self.assertEqual(result["report"]["accepted_count"], 1)
            self.assertEqual(result["report"]["rejected_count"], 1)
            self.assertEqual(result["report"]["rejected_rows"][0]["row_number"], 3)
            validate_asset_inventory(result["inventory"])

    def test_cli_writes_inventory_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory_out = Path(tmp) / "inventory.json"
            report_out = Path(tmp) / "report.json"
            exit_code = main(
                [
                    "--csv",
                    str(CSV_FIXTURE),
                    "--inventory-id",
                    "customer-csv-cli-test",
                    "--generated-at",
                    FIXED_TIME,
                    "--fixture",
                    "--out-inventory",
                    str(inventory_out),
                    "--out-report",
                    str(report_out),
                ]
            )
            self.assertEqual(exit_code, 0)
            validate_asset_inventory(load_json(inventory_out))
            report = load_json(report_out)
            self.assertEqual(report["accepted_count"], 2)
            self.assertEqual(report["rejected_count"], 0)


if __name__ == "__main__":
    unittest.main()
