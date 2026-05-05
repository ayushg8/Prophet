from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from assets.import_csv import (
    IMPORT_MANIFEST_SCHEMA_VERSION,
    import_asset_inventory_csv,
    main,
    validate_import_manifest,
)
from assets.inventory import (
    AssetInventoryError,
    build_asset_seedset,
    load_json,
    validate_asset_inventory,
    validate_asset_seedset,
)


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "assets/fixtures/dib-edge-appliance-inventory.csv"
FINANCIAL_CSV_PATH = ROOT / "assets/fixtures/financial-workflow-inventory.csv"
FIXED_TIME = "2026-05-05T08:00:00Z"


class AssetCsvImportTests(unittest.TestCase):
    def test_fixture_csv_imports_to_valid_inventory_and_seedset(self) -> None:
        inventory, report = import_asset_inventory_csv(
            CSV_PATH,
            inventory_id="asset-csv-dib-edge-001",
            scope="Fictional defense-industrial CSV inventory; product-family metadata only.",
            generated_at=FIXED_TIME,
            fixture=True,
        )
        validate_asset_inventory(inventory)
        self.assertEqual(len(inventory["assets"]), 3)
        self.assertEqual(report["accepted_row_count"], 3)
        self.assertEqual(report["rejected_row_count"], 0)
        seedset = build_asset_seedset(
            inventory,
            generated_at=FIXED_TIME,
            run_id="csv-import-seedset",
        )
        validate_asset_seedset(seedset)
        self.assertEqual(len(seedset["cve_seeds"]), 4)
        self.assertEqual(len(seedset["package_seeds"]), 6)

    def test_second_sector_csv_imports_to_valid_seedset(self) -> None:
        inventory, report = import_asset_inventory_csv(
            FINANCIAL_CSV_PATH,
            inventory_id="asset-csv-financial-workflow-001",
            scope="Fictional financial workflow CSV inventory; workflow metadata only.",
            generated_at=FIXED_TIME,
            fixture=True,
        )
        validate_asset_inventory(inventory)
        self.assertEqual(len(inventory["assets"]), 3)
        self.assertEqual(report["accepted_row_count"], 3)
        self.assertEqual(report["rejected_row_count"], 0)
        seedset = build_asset_seedset(
            inventory,
            generated_at=FIXED_TIME,
            run_id="financial-csv-import-seedset",
        )
        validate_asset_seedset(seedset)
        self.assertEqual(len(seedset["cve_seeds"]), 3)
        self.assertEqual(len(seedset["package_seeds"]), 6)

    def test_csv_import_rejects_unsafe_rows_without_echoing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "inventory.csv"
            _write_csv(
                csv_path,
                [
                    {
                        "asset_id": "safe-row-001",
                        "product_family": "secure edge appliance family",
                        "exposure_class": "edge_appliance",
                        "owner_group": "Edge Platform Security",
                        "environment": "mission partner enclave",
                        "business_criticality": "high",
                        "sbom_components": "log4j-core|2.x legacy|java-library",
                        "known_cve_overlaps": "CVE-2021-44228",
                        "compensating_controls": "centralized web log collection",
                    },
                    {
                        "asset_id": "bad-row-001",
                        "product_family": "secure edge appliance family",
                        "exposure_class": "edge_appliance",
                        "owner_group": "Edge Platform Security",
                        "environment": "prod-edge.example.com",
                        "business_criticality": "high",
                        "sbom_components": "log4j-core|2.x legacy|java-library",
                        "known_cve_overlaps": "CVE-2021-44228",
                        "compensating_controls": "centralized web log collection",
                    },
                ],
            )
            inventory, report = import_asset_inventory_csv(
                csv_path,
                inventory_id="asset-csv-row-rejection",
                scope="Fictional CSV import fixture.",
                generated_at=FIXED_TIME,
                fixture=True,
            )
            self.assertEqual(len(inventory["assets"]), 1)
            self.assertEqual(report["accepted_row_count"], 1)
            self.assertEqual(report["rejected_row_count"], 1)
            rendered_report = str(report)
            self.assertIn("hostname-like", rendered_report)
            self.assertNotIn("prod-edge.example.com", rendered_report)

    def test_csv_import_rejects_unsupported_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "inventory.csv"
            csv_path.write_text(
                "asset_id,product_family,exposure_class,owner_group,environment,"
                "business_criticality,sbom_components,known_cve_overlaps,"
                "compensating_controls,hostname\n",
                encoding="utf-8",
            )
            with self.assertRaises(AssetInventoryError):
                import_asset_inventory_csv(
                    csv_path,
                    inventory_id="asset-csv-bad-columns",
                    scope="Fictional CSV import fixture.",
                    generated_at=FIXED_TIME,
                    fixture=True,
                )

    def test_cli_writes_inventory_report_and_seedset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "inventory.json"
            report = Path(tmp) / "report.json"
            seedset = Path(tmp) / "seedset.json"
            manifest = Path(tmp) / "import-manifest.json"
            exit_code = main(
                [
                    "--csv",
                    str(CSV_PATH),
                    "--inventory-id",
                    "asset-csv-cli",
                    "--scope",
                    "Fictional defense-industrial CSV inventory; product-family metadata only.",
                    "--generated-at",
                    FIXED_TIME,
                    "--fixture",
                    "--out",
                    str(out),
                    "--report-out",
                    str(report),
                    "--seedset-out",
                    str(seedset),
                    "--seedset-run-id",
                    "csv-cli-seedset",
                    "--manifest-out",
                    str(manifest),
                ]
            )
            self.assertEqual(exit_code, 0)
            validate_asset_inventory(load_json(out))
            validate_asset_seedset(load_json(seedset))
            self.assertEqual(load_json(report)["accepted_row_count"], 3)
            import_manifest = load_json(manifest)
            validate_import_manifest(import_manifest)
            self.assertEqual(import_manifest["schema_version"], IMPORT_MANIFEST_SCHEMA_VERSION)
            self.assertFalse(import_manifest["source"]["raw_csv_embedded"])
            self.assertFalse(import_manifest["source"]["raw_row_values_embedded"])
            self.assertIn("inventory", import_manifest["sanitized_outputs"])
            self.assertIn("report", import_manifest["sanitized_outputs"])
            self.assertIn("seedset", import_manifest["sanitized_outputs"])
            rendered_manifest = str(import_manifest)
            self.assertNotIn("secure edge appliance family", rendered_manifest)
            self.assertNotIn("centralized web log collection", rendered_manifest)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    columns = [
        "asset_id",
        "product_family",
        "exposure_class",
        "owner_group",
        "environment",
        "business_criticality",
        "sbom_components",
        "known_cve_overlaps",
        "compensating_controls",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
