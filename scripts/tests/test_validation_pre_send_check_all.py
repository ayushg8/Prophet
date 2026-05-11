from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTREACH_SCRIPT = ROOT / "scripts" / "validation-outreach-block.py"
MESSAGE_SCRIPT = ROOT / "scripts" / "validation-message-pack.py"
BATCH_SCRIPT = ROOT / "scripts" / "validation-send-copy-batch.py"
CONTACT_FORM_SCRIPT = ROOT / "scripts" / "validation-contact-form-copy.py"
PRE_SEND_SCRIPT = ROOT / "scripts" / "validation-pre-send-check-all.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


outreach_block = _load_module("validation_outreach_block_for_pre_send_all", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_pre_send_all", MESSAGE_SCRIPT)
send_copy_batch = _load_module("validation_send_copy_batch_for_pre_send_all", BATCH_SCRIPT)
contact_form_copy = _load_module("validation_contact_form_copy_for_pre_send_all", CONTACT_FORM_SCRIPT)
pre_send_all = _load_module("validation_pre_send_check_all", PRE_SEND_SCRIPT)


class ValidationPreSendCheckAllTests(unittest.TestCase):
    def test_builds_full_pre_send_summary_for_verified_batch(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            contact_dir = Path(tmp) / "contact-form-copy"
            (out_dir / "manifest.json").write_text(
                json.dumps(
                    send_copy_batch.write_send_copy_batch(
                        pack,
                        targets,
                        out_dir=out_dir,
                        require_date="2026-05-10",
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            contact_manifest_path = contact_dir / "manifest.json"
            contact_manifest = contact_form_copy.write_contact_form_copy(
                pack,
                targets,
                out_dir=contact_dir,
                require_date="2026-05-10",
            )
            contact_manifest["manifest_path"] = str(contact_manifest_path)
            contact_manifest_path.write_text(
                json.dumps(contact_manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = pre_send_all.build_pre_send_all_summary(
                pack,
                targets,
                send_copy_dir=out_dir,
                contact_form_copy_dir=contact_dir,
                require_date="2026-05-10",
            )

        self.assertEqual(summary["schema_version"], pre_send_all.PRE_SEND_ALL_SCHEMA_VERSION)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["generated_for"], "2026-05-10")
        self.assertEqual(summary["send_boundary"], "copy_numbered_txt_contents_only")
        self.assertEqual(summary["copy_file_count"], 8)
        self.assertEqual(summary["contact_form_copy_state"], "checked")
        self.assertEqual(summary["contact_form_copy_file_count"], 8)
        self.assertEqual(
            summary["contact_form_copy_send_boundary"],
            "copy_contact_form_txt_contents_only",
        )
        self.assertEqual(summary["pending_send_or_update_count"], 8)
        self.assertEqual(summary["needs_attention_count"], 0)
        self.assertEqual(summary["dry_run_verified_count"], 8)
        self.assertEqual(len(summary["target_checks"]), 8)
        first = summary["target_checks"][0]
        self.assertEqual(first["target_label"], "target-dib-platform-001")
        self.assertEqual(first["copy_file"], "01.txt")
        self.assertEqual(first["contact_form_copy_file"], "01.txt")
        self.assertTrue(first["dry_run_verified"])
        self.assertFalse(first["would_write"])
        self.assertEqual(
            first["pre_send_check_command"],
            "make validation-pre-send-check TARGET=target-dib-platform-001 DATE=2026-05-10",
        )

    def test_rejects_batch_that_no_longer_matches_pending_drafts(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            (out_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            targets = copy.deepcopy(targets)
            targets["targets"][0]["status"] = "outreach_sent"

            with self.assertRaisesRegex(
                pre_send_all.PreSendAllError,
                "outreach pack needs attention",
            ):
                pre_send_all.build_pre_send_all_summary(
                    pack,
                    targets,
                    send_copy_dir=out_dir,
                    require_date="2026-05-10",
                )

    def test_rejects_stale_contact_form_copy_when_directory_exists(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            (out_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            contact_dir = Path(tmp) / "contact-form-copy"
            contact_manifest_path = contact_dir / "manifest.json"
            contact_manifest = contact_form_copy.write_contact_form_copy(
                pack,
                targets,
                out_dir=contact_dir,
                require_date="2026-05-10",
            )
            contact_manifest["manifest_path"] = str(contact_manifest_path)
            contact_manifest_path.write_text(
                json.dumps(contact_manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (contact_dir / "01.txt").write_text("stale\n", encoding="utf-8")

            with self.assertRaisesRegex(
                pre_send_all.PreSendAllError,
                "contact-form copy",
            ):
                pre_send_all.build_pre_send_all_summary(
                    pack,
                    targets,
                    send_copy_dir=out_dir,
                    contact_form_copy_dir=contact_dir,
                    require_date="2026-05-10",
                )

    def test_cli_renders_markdown(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_dir = tmp_path / "send-copy"
            contact_dir = tmp_path / "contact-form-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            (out_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            pack_path = tmp_path / "pack.json"
            targets_path = tmp_path / "targets.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            contact_manifest_path = contact_dir / "manifest.json"
            contact_manifest = contact_form_copy.write_contact_form_copy(
                pack,
                targets,
                out_dir=contact_dir,
                require_date="2026-05-10",
            )
            contact_manifest["manifest_path"] = str(contact_manifest_path)
            contact_manifest_path.write_text(
                json.dumps(contact_manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(PRE_SEND_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--send-copy-dir",
                    str(out_dir),
                    "--contact-form-copy-dir",
                    str(contact_dir),
                    "--require-date",
                    "2026-05-10",
                    "--format",
                    "markdown",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertIn("Prophet Full Pre-Send Check - 2026-05-10", completed.stdout)
        self.assertIn("Pending send/update: 8", completed.stdout)
        self.assertIn("Contact-form copy state: checked", completed.stdout)
        self.assertIn("Contact-form copy files: 8", completed.stdout)
        self.assertIn("Dry-run verified: 8", completed.stdout)
        self.assertIn("Would write during this check: false", completed.stdout)

    def test_make_wrapper_rejects_confirm_guards(self) -> None:
        completed = subprocess.run(
            [
                "make",
                "validation-pre-send-check-all",
                "CONFIRM_SENT=1",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("validation-pre-send-check-all is dry-run only", completed.stdout)


def _targets_and_pack():
    targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
    block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
    pack = message_pack.build_message_pack(block)
    return targets, pack


if __name__ == "__main__":
    unittest.main()
