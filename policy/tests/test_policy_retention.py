from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from evidence.bundle import load_json
from policy.retention import (
    RuntimeRetentionError,
    build_runtime_retention_report,
    main,
    validate_runtime_retention_report,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "policy/prophet-pilot-policy.json"
FIXED_TIME = "2026-05-05T00:00:00Z"


class RuntimeRetentionTests(unittest.TestCase):
    def test_reports_runtime_and_customer_metadata_retention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            customer = _write_json(
                repo_root / "assets/outputs/runtime/customer-inventory.json",
                {
                    "schema_version": "asset_inventory.v0.1",
                    "generated_at": "2026-03-20T00:00:00Z",
                },
            )
            runtime = _write_json(
                repo_root / "evidence/outputs/runtime/evidence.json",
                {
                    "schema_version": "prophet_evidence_bundle.v0.1",
                    "generated_at": "2026-04-20T00:00:00Z",
                },
            )
            audit_log = repo_root / "evidence/outputs/runtime/operator-audit-log.jsonl"
            audit_log.parent.mkdir(parents=True, exist_ok=True)
            audit_log.write_text("{}\n", encoding="utf-8")

            report = build_runtime_retention_report(
                policy_path=DEFAULT_POLICY,
                repo_root=repo_root,
                roots=[
                    "assets/outputs/runtime",
                    "evidence/outputs/runtime",
                ],
                generated_at=FIXED_TIME,
            )

            validate_runtime_retention_report(report)
            artifacts = {artifact["path"]: artifact for artifact in report["artifacts"]}
            self.assertTrue(artifacts[_rel(customer)]["expired"])
            self.assertEqual(artifacts[_rel(customer)]["retention_class"], "customer_metadata")
            self.assertFalse(artifacts[_rel(runtime)]["expired"])
            self.assertEqual(artifacts[_rel(runtime)]["retention_class"], "runtime_output")
            self.assertEqual(artifacts[_rel(audit_log)]["retention_class"], "operator_audit_log")
            self.assertFalse(artifacts[_rel(audit_log)]["deletion_eligible"])
            self.assertEqual(report["summary"]["customer_metadata_artifact_count"], 1)
            self.assertEqual(report["summary"]["expired_customer_metadata_artifact_count"], 1)
            self.assertEqual(report["summary"]["skipped_audit_log_count"], 1)

    def test_delete_expired_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_json(
                repo_root / "assets/outputs/runtime/old-customer-inventory.json",
                {
                    "schema_version": "asset_inventory.v0.1",
                    "generated_at": "2026-01-01T00:00:00Z",
                },
            )

            with self.assertRaisesRegex(RuntimeRetentionError, "requires --confirm"):
                build_runtime_retention_report(
                    policy_path=DEFAULT_POLICY,
                    repo_root=repo_root,
                    roots=["assets/outputs/runtime"],
                    generated_at=FIXED_TIME,
                    delete_expired=True,
                )

    def test_confirmed_delete_removes_only_managed_expired_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            old_customer = _write_json(
                repo_root / "assets/outputs/runtime/old-customer-inventory.json",
                {
                    "schema_version": "asset_inventory.v0.1",
                    "generated_at": "2026-01-01T00:00:00Z",
                },
            )
            old_runtime = _write_json(
                repo_root / "world-side/outputs/runtime/old-forecast.json",
                {
                    "schema_version": "world_forecast.v0.1",
                    "generated_at": "2026-01-01T00:00:00Z",
                },
            )
            audit_log = repo_root / "evidence/outputs/runtime/operator-audit-log.jsonl"
            audit_log.parent.mkdir(parents=True, exist_ok=True)
            audit_log.write_text("{}\n", encoding="utf-8")

            report = build_runtime_retention_report(
                policy_path=DEFAULT_POLICY,
                repo_root=repo_root,
                roots=[
                    "assets/outputs/runtime",
                    "world-side/outputs/runtime",
                    "evidence/outputs/runtime",
                ],
                generated_at=FIXED_TIME,
                delete_expired=True,
                confirm_retention_delete=True,
            )

            validate_runtime_retention_report(report)
            self.assertFalse(old_customer.exists())
            self.assertFalse(old_runtime.exists())
            self.assertTrue(audit_log.exists())
            self.assertEqual(report["summary"]["deleted_artifact_count"], 2)

    def test_rejects_non_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeRetentionError, "must stay under"):
                build_runtime_retention_report(
                    policy_path=DEFAULT_POLICY,
                    repo_root=Path(tmp),
                    roots=["docs"],
                    generated_at=FIXED_TIME,
                )

    def test_cli_writes_report_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_json(
                repo_root / "assets/outputs/runtime/customer-inventory.json",
                {
                    "schema_version": "asset_inventory.v0.1",
                    "generated_at": "2026-04-20T00:00:00Z",
                },
            )
            out = repo_root / "evidence/outputs/runtime/runtime-retention.json"

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--policy",
                        str(DEFAULT_POLICY),
                        "--repo-root",
                        str(repo_root),
                        "--root",
                        "assets/outputs/runtime",
                        "--generated-at",
                        FIXED_TIME,
                        "--out-json",
                        "evidence/outputs/runtime/runtime-retention.json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = load_json(out)
            validate_runtime_retention_report(report)
            self.assertEqual(report["summary"]["artifact_count"], 1)


def _write_json(path: Path, value: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _rel(path: Path) -> str:
    return path.as_posix().split("/outputs/runtime/", maxsplit=1)[0].rsplit("/", maxsplit=1)[-1] + (
        "/outputs/runtime/" + path.as_posix().split("/outputs/runtime/", maxsplit=1)[1]
    )


if __name__ == "__main__":
    unittest.main()
