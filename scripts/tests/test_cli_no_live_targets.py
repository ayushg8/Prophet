from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "policy/prophet-pilot-policy.json"
FORECAST = ROOT / "world-side/outputs/golden-forecast-edge-appliance.json"
CANDIDATE = ROOT / "world-side/fixtures/exploit-candidate-edge-appliance.json"
PORTFOLIO = ROOT / "cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json"
ARTIFACT = ROOT / "cyber-side/fixtures/exploit-engine-output-edge-appliance.json"
ASSET_INVENTORY = ROOT / "assets/fixtures/dib-edge-appliance-inventory.json"
SOURCE_CATALOG = ROOT / "world-side/scraper/config/source_catalog.json"


class CliNoLiveTargetTests(unittest.TestCase):
    def test_assets_import_csv_rejects_hostname_like_asset_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "unsafe-assets.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        ",".join(
                            [
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
                        ),
                        (
                            "prod-gateway.customer.com,edge_gateway,"
                            "internet_edge,network_ops,prod,high,"
                            "openssl|3.x|rpm,CVE-2024-0001,mfa"
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = _run_cli(
                [
                    "-m",
                    "assets.import_csv",
                    "--csv",
                    str(csv_path),
                    "--inventory-id",
                    "cli-safety-import",
                    "--out",
                    str(root / "assets/outputs/runtime/inventory.json"),
                    "--report-out",
                    str(root / "assets/outputs/runtime/report.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no safe asset rows", result.stderr)

    def test_assets_inventory_rejects_live_ip_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = json.loads(ASSET_INVENTORY.read_text(encoding="utf-8"))
            unsafe["assets"][0]["owner_group"] = "network 8.8.8.8"
            unsafe_path = root / "unsafe-inventory.json"
            _write_json(unsafe_path, unsafe)

            result = _run_cli(
                [
                    "-m",
                    "assets.inventory",
                    "--inventory",
                    str(unsafe_path),
                    "--out",
                    str(root / "assets/outputs/runtime/seedset.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("IP-like", result.stderr)

    def test_assets_sbom_import_rejects_url_like_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sbom_path = root / "unsafe-sbom.json"
            _write_json(
                sbom_path,
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
                    "metadata": {"note": "review https://customer.example.com before import"},
                },
            )

            result = _run_cli(
                [
                    "-m",
                    "assets.sbom_import",
                    "--sbom",
                    str(sbom_path),
                    "--inventory-id",
                    "cli-safety-sbom",
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
                    "--out",
                    str(root / "assets/outputs/runtime/inventory.json"),
                    "--report-out",
                    str(root / "assets/outputs/runtime/report.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("URL-like", result.stderr)
        self.assertNotIn("customer.example.com", result.stderr)

    def test_forecaster_cli_rejects_direction_a_live_target_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = json.loads(CANDIDATE.read_text(encoding="utf-8"))
            unsafe["attack_hypothesis"]["target_host"] = "prod-gateway.customer.com"
            unsafe_path = root / "unsafe-candidate.json"
            _write_json(unsafe_path, unsafe)

            result = _run_cli(
                [
                    "-m",
                    "forecaster.cli",
                    "--candidate",
                    str(unsafe_path),
                    "--data-dir",
                    str(ROOT / "world-side/data"),
                    "--out",
                    str(root / "world-side/outputs/runtime/forecast.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("banned candidate key", result.stderr)

    def test_scraper_cli_rejects_live_collection_for_unapproved_host(self) -> None:
        result = _run_cli(
            [
                "-m",
                "scraper_side.cli",
                "--collector",
                "cisa-kev",
                "--live",
                "--feed-url",
                "https://prod-gateway.customer.com/kev.json",
                "--limit",
                "1",
            ]
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed", result.stderr)

    def test_snapshot_cli_rejects_policy_blocked_live_collection(self) -> None:
        result = _run_cli(
            [
                "-m",
                "scraper_side.snapshot",
                "--catalog",
                str(SOURCE_CATALOG),
                "--source",
                "cisa_vulnrichment_cve_record_seed",
                "--policy",
                str(DEFAULT_POLICY),
                "--live",
                "--max-records",
                "0",
            ]
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not allow --live", result.stderr)

    def test_predictor_cli_validate_only_rejects_live_target_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
            unsafe["strike_context"]["target_host"] = "prod-gateway.customer.com"
            unsafe_path = Path(tmp) / "unsafe-portfolio.json"
            _write_json(unsafe_path, unsafe)

            result = _run_cli(["-m", "predictor", "--forecast", str(unsafe_path), "--validate-only"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target_host", result.stderr)

    def test_sandbox_runner_cli_rejects_non_fixture_mode_by_default(self) -> None:
        result = _run_cli(
            [
                "-m",
                "sandbox_runner",
                "run",
                "--profile",
                "edge-appliance-fixture",
                "--mode",
                "container",
                "--policy",
                str(DEFAULT_POLICY),
            ],
            env_overrides={"PROPHET_ENABLE_SANDBOX_RUNNER": ""},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("customer approval record is required", result.stderr)

    def test_evidence_audit_cli_rejects_email_like_operator_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_cli(
                [
                    "-m",
                    "evidence.audit",
                    "append",
                    "--log",
                    str(root / "evidence/outputs/runtime/operator-audit-log.jsonl"),
                    "--policy",
                    str(DEFAULT_POLICY),
                    "--event-type",
                    "operator_approval",
                    "--operator-label",
                    "analyst@customer.com",
                    "--decision",
                    "bypassed_for_fixture",
                    "--generated-at",
                    "2026-05-05T00:00:00Z",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("operator_label", result.stderr)

    def test_evidence_audit_cli_keeps_out_event_under_runtime_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_cli(
                [
                    "-m",
                    "evidence.audit",
                    "append",
                    "--log",
                    str(root / "evidence/outputs/runtime/operator-audit-log.jsonl"),
                    "--policy",
                    str(DEFAULT_POLICY),
                    "--event-type",
                    "operator_approval",
                    "--operator-label",
                    "cli-safety",
                    "--decision",
                    "bypassed_for_fixture",
                    "--generated-at",
                    "2026-05-05T00:00:00Z",
                    "--out-event",
                    str(root / "approval-record.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outputs/runtime", result.stderr)

    def test_evidence_bundle_cli_rejects_non_runtime_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_cli(
                [
                    "-m",
                    "evidence.bundle",
                    "--forecast",
                    str(FORECAST),
                    "--portfolio",
                    str(PORTFOLIO),
                    "--artifact",
                    str(ARTIFACT),
                    "--asset-inventory",
                    str(ASSET_INVENTORY),
                    "--policy",
                    str(DEFAULT_POLICY),
                    "--operator-label",
                    "cli-safety",
                    "--approval-decision",
                    "bypassed_for_fixture",
                    "--generated-at",
                    "2026-05-05T00:00:00Z",
                    "--out-json",
                    str(Path(tmp) / "evidence.json"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence/outputs/runtime", result.stderr)

    def test_integration_export_cli_rejects_policy_disallowed_handoff_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
            policy["allowed_integration_exports"] = [
                item for item in policy["allowed_integration_exports"] if item != "jira_ticket"
            ]
            policy_path = root / "policy.json"
            _write_json(policy_path, policy)

            result = _run_cli(
                [
                    "-m",
                    "integrations.export",
                    "--bundle",
                    str(ROOT / "evidence/fixtures/prophet-evidence-edge-appliance.json"),
                    "--policy",
                    str(policy_path),
                    "--out-dir",
                    str(root / "integrations/outputs/runtime/handoff"),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not allow integration exports", result.stderr)

    def test_policy_lint_cli_rejects_live_targets_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _unsafe_live_policy(Path(tmp))
            result = _run_cli(["-m", "policy.lint", "--policy", str(path)])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live_targets_allowed", result.stderr)

    def test_policy_retention_cli_rejects_live_targets_enabled_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = _unsafe_live_policy(root)
            result = _run_cli(
                [
                    "-m",
                    "policy.retention",
                    "--policy",
                    str(policy_path),
                    "--repo-root",
                    str(root),
                    "--root",
                    "evidence/outputs/runtime",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live_targets_allowed", result.stderr)


def _run_cli(
    args: list[str],
    *,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = [
        str(ROOT),
        str(ROOT / "cyber-side"),
        str(ROOT / "world-side"),
        str(ROOT / "world-side/scraper"),
    ]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    if env_overrides:
        for key, value in env_overrides.items():
            if value:
                env[key] = value
            else:
                env.pop(key, None)
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _unsafe_live_policy(root: Path) -> Path:
    policy = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
    policy["controls"]["live_targets_allowed"] = True
    path = root / "unsafe-live-policy.json"
    _write_json(path, policy)
    return path


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
