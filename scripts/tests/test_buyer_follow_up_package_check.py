from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-buyer-follow-up-package.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_buyer_follow_up_package", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuyerFollowUpPackageCheckTests(unittest.TestCase):
    def test_accepts_safe_follow_up_package_fixture(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture(root, module)

            summary = module.check_package(root=root, check_git=False)

        self.assertTrue(summary["ok"], summary["issues"])
        self.assertEqual(summary["doc_count"], len(module.DEFAULT_DOCS))
        self.assertEqual(summary["runtime_artifact_count"], len(module.DEFAULT_RUNTIME_ARTIFACTS))
        self.assertTrue(all(item["hash_matches_expected"] for item in summary["runtime_artifacts"]))
        self.assertTrue(summary["evidence"]["safety_flags_ok"])
        self.assertTrue(summary["handoff_manifest"]["review_template_only"])
        self.assertTrue(summary["handoff_manifest"]["customer_mapping_required"])

    def test_rejects_stale_runtime_hash(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture(root, module)
            evidence_md = root / "evidence/outputs/runtime/latest-edge-appliance.md"
            evidence_md.write_text("# changed after smoke\n", encoding="utf-8")

            summary = module.check_package(root=root, check_git=False)

        self.assertFalse(summary["ok"])
        self.assertTrue(
            any("hash does not match smoke manifest" in issue["message"] for issue in summary["issues"])
        )

    def test_rejects_follow_up_doc_missing_boundary_phrase(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture(root, module)
            package = root / "docs/BUYER_FOLLOW_UP_PACKAGE.md"
            package.write_text("# Buyer Follow-Up Package\n", encoding="utf-8")

            summary = module.check_package(root=root, check_git=False)

        self.assertFalse(summary["ok"])
        self.assertTrue(
            any(
                issue["path"] == "docs/BUYER_FOLLOW_UP_PACKAGE.md"
                and "missing required buyer-boundary phrase" in issue["message"]
                for issue in summary["issues"]
            )
        )


def _write_fixture(root: Path, module) -> None:
    for doc in module.DEFAULT_DOCS:
        required = "\n".join(module.REQUIRED_DOC_PHRASES.get(doc, ()))
        _write(root / doc, f"# safe doc\n\n{required}\n")
    _write_json(
        root / "evidence/outputs/runtime/latest-edge-appliance.json",
        {
            "schema_version": "prophet_evidence_bundle.v0.1",
            "bundle_id": "peb-test",
            "policy": {"policy_id": "prophet-pilot-fixture-localhost-v0.1"},
            "safety_attestation": {
                "no_credentials": True,
                "no_live_target_data_included": True,
                "no_live_targets": True,
                "no_payloads": True,
                "no_private_hostnames": True,
                "no_raw_scraper_text": True,
            },
            "redaction_report": {
                "raw_asset_inventory_embedded": False,
                "raw_defense_artifact_embedded": False,
                "raw_forecast_embedded": False,
                "raw_osint_records_embedded": False,
                "raw_prediction_portfolio_embedded": False,
                "raw_validation_logs_embedded": False,
                "summary_fields_only": True,
            },
        },
    )
    _write(root / "evidence/outputs/runtime/latest-edge-appliance.md", "# evidence\n")
    _write_json(
        root / "integrations/outputs/runtime/latest-edge-appliance/manifest.json",
        {
            "schema_version": "prophet_integration_export.v0.1",
            "export_id": "export-test",
            "mode": "review_template_only",
            "policy_restrictions": {"policy_id": "prophet-pilot-fixture-localhost-v0.1"},
            "files": {"review_checklist": "review_checklist.md"},
            "safety_attestation": {
                "no_credentials": True,
                "no_external_api_calls": True,
                "no_live_target_data_included": True,
                "no_live_targets": True,
                "no_payloads": True,
                "no_private_hostnames": True,
                "review_templates_only": True,
            },
            "customer_placeholder_validation": {
                "review_template_only": True,
                "status": "customer_mapping_required",
            },
        },
    )
    _write(
        root / "integrations/outputs/runtime/latest-edge-appliance/review_checklist.md",
        "# checklist\n",
    )
    zip_path = root / "integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("prophet-handoff-review-bundle/manifest.json", "{}\n")
    smoke_lines = []
    for path in module.DEFAULT_RUNTIME_ARTIFACTS:
        smoke_lines.append(f"{_sha256(root / path)}  {path}\n")
    _write(root / "scripts/pilot-demo-smoke.sha256", "".join(smoke_lines))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, value: dict) -> None:
    _write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
