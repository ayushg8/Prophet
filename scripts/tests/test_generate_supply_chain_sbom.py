from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-supply-chain-sbom.py"
SPEC = importlib.util.spec_from_file_location("generate_supply_chain_sbom", SCRIPT)
assert SPEC and SPEC.loader
sbom_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sbom_script)


class GenerateSupplyChainSbomTests(unittest.TestCase):
    def test_builds_current_supply_chain_inventory(self) -> None:
        sbom = sbom_script.build_supply_chain_sbom(
            root=ROOT,
            generated_at="2026-05-11",
        )

        self.assertEqual(sbom["schema_version"], sbom_script.SCHEMA_VERSION)
        self.assertEqual(sbom["generated_at"], "2026-05-11")
        self.assertEqual(sbom["summary"]["direct_runtime_dependency_count"], 5)
        self.assertEqual(sbom["summary"]["direct_development_dependency_count"], 15)
        self.assertEqual(sbom["summary"]["scraper_requirement_count"], 0)
        self.assertGreaterEqual(sbom["summary"]["npm_component_count"], 190)
        names = {component["name"] for component in sbom["components"]}
        self.assertIn("Prophet", names)
        self.assertIn("react", names)
        self.assertIn("three", names)
        self.assertIn("vite", names)
        self.assertTrue(
            any(
                component["name"] == "react"
                and component["scope"] == "direct_runtime"
                and component["ecosystem"] == "npm"
                for component in sbom["components"]
            )
        )
        self.assertTrue(
            any(
                source["path"] == "prophet-console/package-lock.json"
                and len(source["sha256"]) == 64
                for source in sbom["generated_from"]["source_paths"]
            )
        )
        self.assertIn("not a CMMC certification artifact", sbom["review_boundary"]["non_claims"])

    def test_cli_writes_only_under_ignored_runtime_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence/outputs/runtime") as tmp:
            out_path = Path(tmp) / "supply-chain-sbom.json"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--date",
                    "2026-05-11",
                    "--out",
                    str(out_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            written = json.loads(out_path.read_text(encoding="utf-8"))
            printed = json.loads(completed.stdout)
            self.assertEqual(written, printed)
            self.assertEqual(written["generated_at"], "2026-05-11")

    def test_cli_rejects_committed_output_path(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--root",
                str(ROOT),
                "--date",
                "2026-05-11",
                "--out",
                "docs/unsafe-sbom.json",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("outputs/runtime", completed.stderr)

    def test_rejects_credential_or_index_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            requirements = Path(tmp) / "requirements.txt"
            requirements.write_text(
                "--extra-index-url https://token@example.invalid/simple\n",
                encoding="utf-8",
            )

            with self.assertRaises(sbom_script.SupplyChainSbomError):
                sbom_script._parse_requirements(requirements)


if __name__ == "__main__":
    unittest.main()
