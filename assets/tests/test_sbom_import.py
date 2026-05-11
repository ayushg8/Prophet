from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from assets.inventory import build_asset_seedset, load_json, validate_asset_inventory, validate_asset_seedset
from assets.sbom_import import AssetSbomImportError, import_asset_inventory_sbom, main


ROOT = Path(__file__).resolve().parents[2]
CYCLONEDX_FIXTURE = ROOT / "assets/fixtures/dib-edge-appliance-sbom.cyclonedx.json"
SPDX_FIXTURE = ROOT / "assets/fixtures/financial-workflow-sbom.spdx.json"
FIXED_TIME = "2026-05-11T08:00:00Z"


class AssetSbomImportTests(unittest.TestCase):
    def test_cyclonedx_imports_to_valid_inventory_and_seedset(self) -> None:
        inventory, report = import_asset_inventory_sbom(
            CYCLONEDX_FIXTURE,
            inventory_id="asset-sbom-dib-edge-001",
            product_family="secure edge appliance family",
            exposure_class="edge_appliance",
            owner_group="product security",
            environment="customer approved metadata",
            business_criticality="high",
            generated_at=FIXED_TIME,
            fixture=True,
        )
        validate_asset_inventory(inventory)
        self.assertEqual(inventory["source_format"], "cyclonedx-json")
        self.assertEqual(report["component_count"], 3)
        self.assertEqual(report["deduplicated_component_count"], 1)
        self.assertEqual(report["known_cve_overlap_count"], 2)
        self.assertIn("java-library", report["package_type_counts"])
        seedset = build_asset_seedset(inventory, generated_at=FIXED_TIME, run_id="sbom-dib-edge")
        validate_asset_seedset(seedset)
        self.assertEqual(len(seedset["package_seeds"]), 3)
        self.assertEqual(len(seedset["cve_seeds"]), 2)

    def test_spdx_imports_to_valid_inventory_and_maps_package_ecosystems(self) -> None:
        inventory, report = import_asset_inventory_sbom(
            SPDX_FIXTURE,
            inventory_id="asset-sbom-financial-workflow-001",
            product_family="financial workflow service",
            exposure_class="workflow_application",
            owner_group="application security",
            environment="customer approved metadata",
            business_criticality="high",
            generated_at=FIXED_TIME,
            fixture=True,
        )
        validate_asset_inventory(inventory)
        self.assertEqual(inventory["source_format"], "spdx-json")
        package_types = {component["package_type"] for component in inventory["assets"][0]["sbom_components"]}
        self.assertEqual(package_types, {"java-library", "npm-package", "python-package"})
        self.assertEqual(report["known_cve_overlaps"], ["CVE-2023-46604"])
        seedset = build_asset_seedset(inventory, generated_at=FIXED_TIME, run_id="sbom-financial")
        validate_asset_seedset(seedset)
        self.assertEqual(len(seedset["package_seeds"]), 3)
        self.assertEqual(len(seedset["cve_seeds"]), 1)

    def test_cli_writes_inventory_report_and_seedset_without_raw_sbom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory_out = Path(tmp) / "inventory.json"
            report_out = Path(tmp) / "report.json"
            seedset_out = Path(tmp) / "seedset.json"
            exit_code = main(
                [
                    "--sbom",
                    str(CYCLONEDX_FIXTURE),
                    "--inventory-id",
                    "asset-sbom-cli",
                    "--product-family",
                    "secure edge appliance family",
                    "--exposure-class",
                    "edge_appliance",
                    "--owner-group",
                    "product security",
                    "--environment",
                    "customer approved metadata",
                    "--business-criticality",
                    "high",
                    "--generated-at",
                    FIXED_TIME,
                    "--fixture",
                    "--out",
                    str(inventory_out),
                    "--report-out",
                    str(report_out),
                    "--seedset-out",
                    str(seedset_out),
                    "--seedset-run-id",
                    "sbom-cli-seedset",
                ]
            )
            self.assertEqual(exit_code, 0)
            validate_asset_inventory(load_json(inventory_out))
            validate_asset_seedset(load_json(seedset_out))
            report = load_json(report_out)
            self.assertFalse(report["raw_sbom_embedded"])
            self.assertFalse(report["raw_component_values_embedded"])
            self.assertNotIn("serialNumber", json.dumps(report))
            self.assertEqual(len(report["source_sbom_sha256"]), 64)

    def test_rejects_unsafe_sbom_without_echoing_raw_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-sbom.json"
            path.write_text(
                json.dumps(
                    {
                        "bomFormat": "CycloneDX",
                        "specVersion": "1.5",
                        "components": [
                            {
                                "name": "safe-component",
                                "version": "1.2.3",
                                "type": "library",
                                "purl": "pkg:npm/safe-component@1.2.3",
                            }
                        ],
                        "metadata": {"note": "review prod-edge.example.com before import"},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(AssetSbomImportError) as raised:
                import_asset_inventory_sbom(
                    path,
                    inventory_id="asset-sbom-bad",
                    product_family="secure edge appliance family",
                    exposure_class="edge_appliance",
                    owner_group="product security",
                    environment="customer approved metadata",
                    business_criticality="high",
                    generated_at=FIXED_TIME,
                    fixture=True,
                )
            self.assertIn("hostname-like", str(raised.exception))
            self.assertNotIn("prod-edge.example.com", str(raised.exception))

    def test_cli_rejects_unsafe_sbom_without_echoing_raw_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-sbom.json"
            path.write_text(
                json.dumps(
                    {
                        "spdxVersion": "SPDX-2.3",
                        "packages": [
                            {
                                "name": "safe-component",
                                "versionInfo": "1.2.3",
                                "downloadLocation": "NOASSERTION",
                                "externalRefs": [
                                    {
                                        "referenceCategory": "PACKAGE-MANAGER",
                                        "referenceLocator": "pkg:npm/safe-component@1.2.3",
                                        "referenceType": "purl",
                                    }
                                ],
                            }
                        ],
                        "annotations": [{"comment": "operator note includes https://customer.example.com"}],
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--sbom",
                        str(path),
                        "--inventory-id",
                        "asset-sbom-bad-cli",
                        "--product-family",
                        "secure edge appliance family",
                        "--exposure-class",
                        "edge_appliance",
                        "--owner-group",
                        "product security",
                        "--environment",
                        "customer approved metadata",
                        "--business-criticality",
                        "high",
                        "--generated-at",
                        FIXED_TIME,
                        "--fixture",
                        "--out",
                        str(Path(tmp) / "inventory.json"),
                        "--report-out",
                        str(Path(tmp) / "report.json"),
                    ]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("URL-like", stderr.getvalue())
            self.assertNotIn("customer.example.com", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
