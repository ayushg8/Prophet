from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from assets.inventory import (
    AssetInventoryError,
    build_asset_seedset,
    load_json,
    main,
    summarize_asset_seedset,
    validate_asset_inventory,
    validate_asset_seedset,
)


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "assets/fixtures/dib-edge-appliance-inventory.json"
SEEDSET_PATH = ROOT / "assets/fixtures/dib-edge-appliance-seedset.json"
FINANCIAL_INVENTORY_PATH = ROOT / "assets/fixtures/financial-workflow-inventory.json"
FINANCIAL_SEEDSET_PATH = ROOT / "assets/fixtures/financial-workflow-seedset.json"
FIXED_TIME = "2026-05-04T20:10:00Z"


class AssetSeedsetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = load_json(INVENTORY_PATH)

    def test_valid_fixture_inventory_and_seedset(self) -> None:
        validate_asset_inventory(self.inventory)
        seedset = build_asset_seedset(
            copy.deepcopy(self.inventory),
            generated_at=FIXED_TIME,
            run_id="fixture-edge-appliance-seedset",
        )
        validate_asset_seedset(seedset)
        self.assertEqual(seedset["schema_version"], "asset_osint_seedset.v0.1")
        self.assertEqual(seedset["input_refs"]["asset_count"], 3)
        self.assertEqual(len(seedset["cve_seeds"]), 4)
        self.assertEqual(len(seedset["package_seeds"]), 6)
        self.assertIn("osv_query_api_seed", seedset["recommended_source_ids"])

    def test_checked_in_seedset_validates(self) -> None:
        seedset = load_json(SEEDSET_PATH)
        validate_asset_seedset(seedset)
        summary = summarize_asset_seedset(seedset)
        self.assertEqual(summary["asset_count"], 3)
        self.assertEqual(summary["cve_seed_count"], 4)
        self.assertIn("edge_appliance", summary["exposure_classes"])

    def test_second_sector_fixture_builds_safe_seedset(self) -> None:
        inventory = load_json(FINANCIAL_INVENTORY_PATH)
        validate_asset_inventory(inventory)
        seedset = build_asset_seedset(
            copy.deepcopy(inventory),
            generated_at=FIXED_TIME,
            run_id="fixture-financial-workflow-seedset",
        )
        validate_asset_seedset(seedset)
        summary = summarize_asset_seedset(seedset)
        self.assertEqual(summary["asset_count"], 3)
        self.assertEqual(summary["cve_seed_count"], 3)
        self.assertIn("financial_workflow", summary["exposure_classes"])
        self.assertIn("custody_workflow", summary["exposure_classes"])

    def test_checked_in_second_sector_seedset_validates(self) -> None:
        seedset = load_json(FINANCIAL_SEEDSET_PATH)
        validate_asset_seedset(seedset)
        summary = summarize_asset_seedset(seedset)
        self.assertEqual(summary["asset_count"], 3)
        self.assertIn("payment_operations", summary["exposure_classes"])

    def test_deterministic_hash_stability_with_fixed_time(self) -> None:
        first = build_asset_seedset(
            copy.deepcopy(self.inventory),
            generated_at=FIXED_TIME,
            run_id="fixture-edge-appliance-seedset",
        )
        second = build_asset_seedset(
            copy.deepcopy(self.inventory),
            generated_at=FIXED_TIME,
            run_id="fixture-edge-appliance-seedset",
        )
        self.assertEqual(first["seedset_id"], second["seedset_id"])
        self.assertEqual(first["seedset_sha256"], second["seedset_sha256"])

    def test_cli_writes_seedset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "seedset.json"
            exit_code = main(
                [
                    "--inventory",
                    str(INVENTORY_PATH),
                    "--generated-at",
                    FIXED_TIME,
                    "--run-id",
                    "asset-cli-test",
                    "--out",
                    str(out_path),
                ]
            )
            self.assertEqual(exit_code, 0)
            validate_asset_seedset(load_json(out_path))

    def test_rejects_ip_like_inventory_text(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["environment"] = "support enclave 192.0.2.10"
        with self.assertRaises(AssetInventoryError):
            validate_asset_inventory(inventory)

    def test_rejects_hostname_like_inventory_text(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["environment"] = "prod-edge.example.com"
        with self.assertRaises(AssetInventoryError):
            validate_asset_inventory(inventory)

    def test_rejects_secret_like_inventory_text(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["compensating_controls"].append("password=fixture")
        with self.assertRaises(AssetInventoryError):
            validate_asset_inventory(inventory)

    def test_rejects_invalid_cve_seed(self) -> None:
        seedset = build_asset_seedset(
            copy.deepcopy(self.inventory),
            generated_at=FIXED_TIME,
            run_id="bad-cve-seed",
        )
        seedset["cve_seeds"][0]["cve_id"] = "not-a-cve"
        seedset["hashes"]["seedset_body_sha256"] = seedset["seedset_sha256"]
        with self.assertRaises(AssetInventoryError):
            validate_asset_seedset(seedset)


if __name__ == "__main__":
    unittest.main()
