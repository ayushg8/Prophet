from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-default-output-safety.py"
SPEC = importlib.util.spec_from_file_location("check_default_output_safety", SCRIPT)
assert SPEC and SPEC.loader
check_default_output_safety = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_default_output_safety
SPEC.loader.exec_module(check_default_output_safety)


class DefaultOutputSafetyTests(unittest.TestCase):
    def test_allows_public_source_citations_in_default_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy(root, ["safe.json", "safe.jsonl", "safe.md"])
            (root / "safe.json").write_text(
                json.dumps(
                    {
                        "source_refs": [
                            {
                                "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                            }
                        ],
                        "defense": {
                            "sigma_rule": {
                                "yaml": "references:\n  - https://nvd.nist.gov/vuln/detail/CVE-2021-44228\n",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "safe.jsonl").write_text(
                json.dumps(
                    {
                        "record_id": "fixture-001",
                        "source_ref": {
                            "url": "https://osv.dev/vulnerability/CVE-2024-3400",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "safe.md").write_text(
                "- Source: https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a\n",
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["checked_outputs"], 3)
        self.assertEqual(summary["provenance_manifest_count"], 0)
        self.assertEqual(summary["issues"], [])
        self.assertEqual(summary["url_count"], 4)

    def test_requires_osint_snapshot_provenance_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy_map(
                root,
                {
                    "seeded_osint_snapshot": "snapshot.jsonl",
                },
            )
            (root / "snapshot.jsonl").write_text(
                json.dumps(
                    {
                        "record_id": "fixture-001",
                        "source_ref": {
                            "url": "https://osv.dev/vulnerability/CVE-2024-3400",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        self.assertEqual(summary["provenance_manifest_count"], 0)
        self.assertTrue(
            any("must have paired seeded_osint_manifest" in issue["message"] for issue in summary["issues"])
        )

    def test_validates_osint_snapshot_provenance_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy_map(
                root,
                {
                    "seeded_osint_snapshot": "snapshot.jsonl",
                    "seeded_osint_manifest": "snapshot.manifest.json",
                },
            )
            snapshot = root / "snapshot.jsonl"
            snapshot.write_text(
                json.dumps(
                    {
                        "record_id": "fixture-001",
                        "source_ref": {
                            "url": "https://osv.dev/vulnerability/CVE-2024-3400",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            _write_manifest(root / "snapshot.manifest.json", snapshot)

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["provenance_manifest_count"], 1)
        self.assertEqual(summary["issues"], [])

    def test_rejects_unsafe_osint_snapshot_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy_map(
                root,
                {
                    "seeded_osint_snapshot": "snapshot.jsonl",
                    "seeded_osint_manifest": "snapshot.manifest.json",
                },
            )
            snapshot = root / "snapshot.jsonl"
            snapshot.write_text('{"record_id": "fixture-001"}\n', encoding="utf-8")
            _write_manifest(
                root / "snapshot.manifest.json",
                snapshot,
                snapshot_jsonl_sha256="0" * 64,
                raw_content_written=True,
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        messages = [issue["message"] for issue in summary["issues"]]
        self.assertTrue(any("hash does not match" in message for message in messages))
        self.assertTrue(any("raw content was not written" in message for message in messages))

    def test_rejects_live_target_url_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy(root, ["unsafe.json"])
            (root / "unsafe.json").write_text(
                json.dumps({"target_url": "https://example.com/customer-appliance"}),
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(any("live-target URL field" in issue["message"] for issue in summary["issues"]))

    def test_rejects_nested_live_endpoint_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy(root, ["unsafe.json"])
            (root / "unsafe.json").write_text(
                json.dumps(
                    {
                        "customer": {
                            "metadata": {
                                "endpoint": "https://review.example.com/live-system",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(any("live-target URL field" in issue["message"] for issue in summary["issues"]))

    def test_rejects_private_host_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy(root, ["unsafe.json"])
            (root / "unsafe.json").write_text(
                json.dumps(
                    {
                        "source_refs": [
                            {"url": "https://review.internal/evidence"},
                            {"url": "https://10.0.0.5/evidence"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        messages = [issue["message"] for issue in summary["issues"]]
        self.assertTrue(any("private hostname" in message for message in messages))
        self.assertTrue(any("non-public URL host" in message for message in messages))

    def test_rejects_markdown_live_target_url_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_policy(root, ["unsafe.md"])
            (root / "unsafe.md").write_text(
                "Target URL: https://example.com/customer-appliance\n",
                encoding="utf-8",
            )

            summary = check_default_output_safety.check_default_outputs(
                root / "policy.json",
                root,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(
            any("live-target URL context" in issue["message"] for issue in summary["issues"])
        )


def _write_policy(root: Path, output_paths: list[str]) -> None:
    _write_policy_map(
        root,
        {
            f"output_{index}": output_path
            for index, output_path in enumerate(output_paths, 1)
        },
    )


def _write_policy_map(root: Path, default_outputs: dict[str, str]) -> None:
    (root / "policy.json").write_text(
        json.dumps(
            {
                "schema_version": "prophet_pilot_policy.v0.1",
                "default_outputs": default_outputs,
            }
        ),
        encoding="utf-8",
    )


def _write_manifest(
    path: Path,
    snapshot: Path,
    *,
    snapshot_jsonl_sha256: str | None = None,
    raw_content_written: bool = False,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "prophet.osint_snapshot_manifest.v0.1",
                "record_count": 1,
                "source_count": 1,
                "hashes": {
                    "snapshot_jsonl_sha256": snapshot_jsonl_sha256
                    or check_default_output_safety._sha256_file(snapshot),
                },
                "safety_attestation": {
                    "sanitized_records_only": True,
                    "raw_content_written": raw_content_written,
                },
                "policy": {
                    "policy_sha256": "a" * 64,
                    "retention": {"raw_collection_retained": False},
                },
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
