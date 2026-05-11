from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diff-pilot-demo-fixtures.py"
SPEC = importlib.util.spec_from_file_location("diff_pilot_demo_fixtures", SCRIPT)
assert SPEC and SPEC.loader
diff_pilot_demo_fixtures = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = diff_pilot_demo_fixtures
SPEC.loader.exec_module(diff_pilot_demo_fixtures)


class PilotDemoFixtureDiffTests(unittest.TestCase):
    def test_current_artifacts_with_matching_hashes_have_no_differences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence/outputs/runtime/latest-edge-appliance.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"safe": true}\n', encoding="utf-8")
            baseline = _write_manifest(
                root / "baseline.sha256",
                {"evidence/outputs/runtime/latest-edge-appliance.json": artifact.read_bytes()},
            )

            baseline_hashes = diff_pilot_demo_fixtures.read_hash_manifest(baseline)
            candidate_hashes = diff_pilot_demo_fixtures.hash_candidate_files(
                root,
                baseline_hashes.keys(),
            )
            result = diff_pilot_demo_fixtures.compare_hashes(
                baseline_hashes,
                candidate_hashes,
            )

        self.assertFalse(result.has_differences)
        self.assertEqual(result.summary(), {"unchanged": 1, "changed": 0, "missing": 0, "added": 0})

    def test_current_artifacts_report_changed_and_missing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changed_path = root / "assets/outputs/runtime/inventory.json"
            changed_path.parent.mkdir(parents=True)
            changed_path.write_text("candidate\n", encoding="utf-8")
            baseline = _write_manifest(
                root / "baseline.sha256",
                {
                    "assets/outputs/runtime/inventory.json": b"baseline\n",
                    "evidence/outputs/runtime/latest-edge-appliance.md": b"missing\n",
                },
            )

            baseline_hashes = diff_pilot_demo_fixtures.read_hash_manifest(baseline)
            candidate_hashes = diff_pilot_demo_fixtures.hash_candidate_files(
                root,
                baseline_hashes.keys(),
            )
            result = diff_pilot_demo_fixtures.compare_hashes(
                baseline_hashes,
                candidate_hashes,
            )

        self.assertTrue(result.has_differences)
        self.assertEqual(result.summary(), {"unchanged": 0, "changed": 1, "missing": 1, "added": 0})
        self.assertEqual(result.changed[0]["path"], "assets/outputs/runtime/inventory.json")
        self.assertEqual(result.missing[0]["path"], "evidence/outputs/runtime/latest-edge-appliance.md")

    def test_candidate_manifest_reports_added_paths(self) -> None:
        baseline = {
            "evidence/outputs/runtime/latest-edge-appliance.json": _sha256(b"one"),
        }
        candidate = {
            "evidence/outputs/runtime/latest-edge-appliance.json": _sha256(b"one"),
            "integrations/outputs/runtime/latest-edge-appliance/manifest.json": _sha256(b"two"),
        }

        result = diff_pilot_demo_fixtures.compare_hashes(baseline, candidate)

        self.assertTrue(result.has_differences)
        self.assertEqual(result.summary(), {"unchanged": 1, "changed": 0, "missing": 0, "added": 1})
        self.assertEqual(
            result.added[0]["path"],
            "integrations/outputs/runtime/latest-edge-appliance/manifest.json",
        )

    def test_manifest_rejects_paths_that_escape_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "bad.sha256"
            manifest.write_text(f"{_sha256(b'data')}  ../outside.json\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "repo-relative"):
                diff_pilot_demo_fixtures.read_hash_manifest(manifest)

    def test_cli_json_output_is_hash_only_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "cyber-side/outputs/runtime/artifact.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"safe_field": "SECRET_RAW_BODY"}\n', encoding="utf-8")
            baseline = _write_manifest(
                root / "baseline.sha256",
                {"cyber-side/outputs/runtime/artifact.json": artifact.read_bytes()},
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--baseline",
                    str(baseline),
                    "--root",
                    str(root),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)

        self.assertEqual(payload["schema_version"], "prophet_pilot_fixture_diff.v0.1")
        self.assertEqual(payload["result"], "no_differences")
        self.assertFalse(payload["safety"]["artifact_contents_printed"])
        self.assertNotIn("SECRET_RAW_BODY", completed.stdout)


def _write_manifest(path: Path, entries: dict[str, bytes]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{_sha256(body)}  {rel_path}" for rel_path, body in entries.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


if __name__ == "__main__":
    unittest.main()
