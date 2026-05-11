from __future__ import annotations

import importlib.util
import json
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-console-screenshots.py"
SPEC = importlib.util.spec_from_file_location("check_console_screenshots", SCRIPT)
assert SPEC and SPEC.loader
check_console_screenshots = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_console_screenshots
SPEC.loader.exec_module(check_console_screenshots)


class CheckConsoleScreenshotsTests(unittest.TestCase):
    def test_current_generated_manifest_verifies(self) -> None:
        manifest = ROOT / "evidence/outputs/runtime/console-screenshots/manifest.json"
        if not manifest.exists():
            self.skipTest("run npm run capture:screenshots before this check")

        summary = check_console_screenshots.verify_console_screenshots(
            manifest,
            root=ROOT,
        )

        self.assertTrue(summary["ok"], summary["issues"])
        self.assertEqual(summary["artifact_count"], 6)
        self.assertEqual(summary["checked_artifacts"], 6)

    def test_rejects_manifest_without_required_boundary(self) -> None:
        with _temp_screenshot_dir() as base_dir:
            manifest = _write_manifest(base_dir, boundary_overrides={"no_live_targets": False})

            summary = check_console_screenshots.verify_console_screenshots(
                manifest,
                root=ROOT,
            )

        self.assertFalse(summary["ok"])
        self.assertIn("manifest.data_boundary.no_live_targets must be true", summary["issues"])

    def test_rejects_hash_mismatch(self) -> None:
        with _temp_screenshot_dir() as base_dir:
            manifest = _write_manifest(base_dir, sha256="0" * 64)

            summary = check_console_screenshots.verify_console_screenshots(
                manifest,
                root=ROOT,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(any("sha256 does not match" in issue for issue in summary["issues"]))

    def test_rejects_dimension_mismatch(self) -> None:
        with _temp_screenshot_dir() as base_dir:
            manifest = _write_manifest(base_dir, width=390, height=844, declared_width=1440)

            summary = check_console_screenshots.verify_console_screenshots(
                manifest,
                root=ROOT,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(any("viewport does not match" in issue for issue in summary["issues"]))

    def test_rejects_non_png_artifact_paths(self) -> None:
        with _temp_screenshot_dir() as base_dir:
            outside_path = str((Path(base_dir) / "unsafe.txt").relative_to(ROOT))
            manifest = _write_manifest(base_dir, artifact_path=outside_path)

            summary = check_console_screenshots.verify_console_screenshots(
                manifest,
                root=ROOT,
            )

        self.assertFalse(summary["ok"])
        self.assertTrue(any("must point to a PNG file" in issue for issue in summary["issues"]))

    def test_cli_help_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Verify console screenshot manifest", result.stdout)


def _temp_screenshot_dir() -> tempfile.TemporaryDirectory[str]:
    base = ROOT / "evidence/outputs/runtime/console-screenshots"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base)


def _write_manifest(
    base_dir: Path | str,
    *,
    artifact_path: str | None = None,
    width: int = 24,
    height: int = 16,
    declared_width: int | None = None,
    declared_height: int | None = None,
    sha256: str | None = None,
    boundary_overrides: dict[str, bool] | None = None,
) -> Path:
    base_dir = Path(base_dir)
    if artifact_path is None:
        artifact_path = str((base_dir / "test.png").relative_to(ROOT))
    image_path = ROOT / artifact_path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    _write_png(image_path, width, height)
    boundary = {
        "fixture_backed": True,
        "browser_chrome_excluded": True,
        "no_customer_systems": True,
        "no_live_targets": True,
        "no_payloads": True,
        "no_credentials": True,
        "review_required_before_sharing": True,
    }
    boundary.update(boundary_overrides or {})
    manifest_path = base_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": check_console_screenshots.EXPECTED_SCHEMA_VERSION,
                "output_dir": "evidence/outputs/runtime/console-screenshots",
                "data_boundary": boundary,
                "artifacts": [
                    {
                        "id": "test",
                        "path": artifact_path,
                        "sha256": sha256 or check_console_screenshots._sha256(image_path),
                        "viewport": {
                            "width": declared_width or width,
                            "height": declared_height or height,
                        },
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _write_png(path: Path, width: int, height: int) -> None:
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    payload = _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(raw))
    payload += _chunk(b"IEND", b"")
    path.write_bytes(check_console_screenshots.PNG_SIGNATURE + payload)


def _chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


if __name__ == "__main__":
    unittest.main()
