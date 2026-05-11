from __future__ import annotations

import copy
import hashlib
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
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


outreach_block = _load_module("validation_outreach_block_for_send_copy_batch", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_send_copy_batch", MESSAGE_SCRIPT)
send_copy_batch = _load_module("validation_send_copy_batch", BATCH_SCRIPT)


class ValidationSendCopyBatchTests(unittest.TestCase):
    def test_writes_copy_only_files_for_verified_pending_drafts(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"

            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )

            self.assertEqual(
                manifest["schema_version"],
                send_copy_batch.SEND_COPY_BATCH_SCHEMA_VERSION,
            )
            self.assertEqual(manifest["generated_for"], "2026-05-10")
            self.assertFalse(manifest["outbound_safe"])
            self.assertTrue(manifest["copy_files_outbound_safe"])
            self.assertFalse(manifest["operator_metadata_outbound_safe"])
            self.assertTrue(manifest["private_metadata"])
            self.assertEqual(
                manifest["send_boundary"],
                "copy_numbered_txt_contents_only",
            )
            self.assertEqual(manifest["copy_file_count"], 8)
            self.assertEqual(manifest["dry_run_verified_count"], 8)
            first = manifest["files"][0]
            self.assertEqual(first["target_label"], "target-dib-platform-001")
            self.assertIn("subject", first)
            self.assertEqual(
                first["path"],
                str(out_dir / "01.txt"),
            )
            rendered = Path(first["path"]).read_text(encoding="utf-8")
            self.assertEqual(
                first["sha256"],
                hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
            )
            self.assertTrue(rendered.startswith("Subject: "))
            self.assertIn("Hi,", rendered)
            self.assertNotIn("<first name>", rendered)
            self.assertNotRegex(rendered, r"<[^>\n]+>")
            self.assertIn("No live data ask", rendered)
            self.assertNotIn("target-dib-platform-001", rendered)
            self.assertNotIn("make validation-apply-draft", rendered)
            self.assertNotIn("Tracker update command", rendered)
            self.assertNotIn("CONFIRM_SENT", rendered)
            self.assertNotIn("@", rendered)
            self.assertNotIn("http://", rendered)
            self.assertNotIn("https://", rendered)
            readme = Path(manifest["readme_path"]).read_text(encoding="utf-8")
            self.assertIn("copy only its contents", readme)
            self.assertIn("Do not attach the `.txt` files", readme)
            self.assertIn("COPY_ONLY_INDEX.md", readme)
            self.assertIn("SUBJECT_ORDER.md", readme)
            self.assertIn(
                "Do not send `manifest.json`, `CHECKLIST.md`, `COPY_ONLY_INDEX.md`, `SUBJECT_ORDER.md`, or this README",
                readme,
            )
            self.assertIn("SHA-256", readme)
            self.assertIn("make validation-send-copy-check DATE=2026-05-10", readme)
            self.assertIn("make validation-status DATE=2026-05-10", readme)
            self.assertIn("personalize only in the outreach channel", readme)
            self.assertIn("Do not store recipient names", readme)
            self.assertNotIn("target-dib-platform-001", readme)
            self.assertNotIn("@", readme)
            self.assertNotIn("http://", readme)
            self.assertNotIn("https://", readme)
            checklist = Path(manifest["checklist_path"]).read_text(encoding="utf-8")
            self.assertIn("Prophet Send-Copy Batch Checklist", checklist)
            self.assertIn("make validation-send-copy-check DATE=2026-05-10", checklist)
            self.assertIn("Do not send this checklist", checklist)
            self.assertIn("`01.txt`", checklist)
            self.assertIn("`target-dib-platform-001`", checklist)
            self.assertIn(
                "`make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10`",
                checklist,
            )
            self.assertIn(
                "`make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10 CONFIRM_SENT=1`",
                checklist,
            )
            copy_index = Path(manifest["copy_index_path"]).read_text(encoding="utf-8")
            self.assertIn("Prophet Copy-Only Send Index", copy_index)
            self.assertIn("`01.txt`", copy_index)
            self.assertNotIn("target-dib-platform-001", copy_index)
            self.assertNotIn("make validation-", copy_index)
            self.assertNotIn("CONFIRM_SENT", copy_index)
            copy_index = Path(manifest["copy_index_path"]).read_text(encoding="utf-8")
            self.assertIn("Prophet Copy-Only Send Index", copy_index)
            self.assertIn("intentionally omits target labels", copy_index)
            self.assertIn("`01.txt`", copy_index)
            self.assertIn("`targeted_ask`", copy_index)
            self.assertNotIn("target-dib-platform-001", copy_index)
            self.assertNotIn("make validation-apply-draft", copy_index)
            self.assertNotIn("CONFIRM_SENT", copy_index)
            self.assertNotIn("@", copy_index)
            self.assertNotIn("http://", copy_index)
            self.assertNotIn("https://", copy_index)
            subject_order = Path(manifest["subject_order_path"]).read_text(encoding="utf-8")
            self.assertIn("Prophet Copy-Only Subject Order", subject_order)
            self.assertIn("`01.txt`", subject_order)
            self.assertIn("Intro to someone", subject_order)
            self.assertNotIn("target-dib-platform-001", subject_order)
            self.assertNotIn("make validation-apply-draft", subject_order)
            self.assertNotIn("@", subject_order)
            self.assertNotIn("http://", subject_order)
            self.assertNotIn("https://", subject_order)

    def test_removes_old_generated_copy_files_before_writing(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            out_dir.mkdir()
            stale = out_dir / "01-stale-target.txt"
            stale_neutral = out_dir / "99.txt"
            keep = out_dir / "operator-note.md"
            stale.write_text("stale\n", encoding="utf-8")
            stale_neutral.write_text("stale\n", encoding="utf-8")
            keep.write_text("keep\n", encoding="utf-8")

            send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )

            self.assertFalse(stale.exists())
            self.assertFalse(stale_neutral.exists())
            self.assertTrue(keep.exists())
            self.assertTrue((out_dir / "01.txt").exists())

    def test_refuses_needs_attention_pack(self) -> None:
        targets, pack = _targets_and_pack()
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(send_copy_batch.SendCopyBatchError, "needs attention"):
                send_copy_batch.write_send_copy_batch(
                    pack,
                    targets,
                    out_dir=Path(tmp),
                    require_date="2026-05-10",
                )

    def test_cli_writes_manifest_and_files(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_path = tmp_path / "pack.json"
            targets_path = tmp_path / "targets.json"
            out_dir = tmp_path / "send-copy"
            manifest_path = out_dir / "manifest.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(BATCH_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--require-date",
                    "2026-05-10",
                    "--out-dir",
                    str(out_dir),
                    "--manifest-out",
                    str(manifest_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(completed.stdout)
            self.assertEqual(manifest["copy_file_count"], 8)
            self.assertEqual(manifest["readme_path"], str(out_dir / "README.md"))
            self.assertEqual(manifest["checklist_path"], str(out_dir / "CHECKLIST.md"))
            self.assertEqual(manifest["copy_index_path"], str(out_dir / "COPY_ONLY_INDEX.md"))
            self.assertEqual(manifest["subject_order_path"], str(out_dir / "SUBJECT_ORDER.md"))
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), manifest)
            self.assertTrue((out_dir / "08.txt").exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "CHECKLIST.md").exists())
            self.assertTrue((out_dir / "COPY_ONLY_INDEX.md").exists())
            self.assertTrue((out_dir / "SUBJECT_ORDER.md").exists())

    def test_check_send_copy_directory_validates_existing_batch(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            manifest_path = out_dir / "manifest.json"
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            summary = send_copy_batch.check_send_copy_directory(
                out_dir,
                require_date="2026-05-10",
            )

            self.assertEqual(summary["copy_file_count"], 8)
            self.assertTrue(summary["copy_files_outbound_safe"])
            self.assertFalse(summary["operator_metadata_outbound_safe"])
            self.assertTrue(summary["operator_metadata_private_by_design"])
            self.assertEqual(summary["operator_metadata_send_boundary"], "private_do_not_send")
            self.assertEqual(
                summary["send_boundary"],
                "copy_numbered_txt_contents_only",
            )
            self.assertTrue(summary["readme_exists"])
            self.assertTrue(summary["readme_matches_manifest"])
            self.assertTrue(summary["checklist_exists"])
            self.assertTrue(summary["checklist_matches_manifest"])
            self.assertTrue(summary["copy_index_exists"])
            self.assertTrue(summary["copy_index_matches_manifest"])
            self.assertTrue(summary["subject_order_exists"])
            self.assertTrue(summary["subject_order_matches_manifest"])
            self.assertTrue(all(file["subject_count"] == 1 for file in summary["checked_files"]))

    def test_cli_check_dir_validates_existing_batch_without_writing(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            manifest_path = out_dir / "manifest.json"
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(BATCH_SCRIPT),
                    "--check-dir",
                    str(out_dir),
                    "--require-date",
                    "2026-05-10",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["copy_file_count"], 8)
            self.assertTrue(summary["copy_files_outbound_safe"])
            self.assertTrue(summary["readme_matches_manifest"])
            self.assertTrue(summary["checklist_matches_manifest"])
            self.assertTrue(summary["copy_index_matches_manifest"])
            self.assertTrue(summary["subject_order_matches_manifest"])

    def test_check_send_copy_directory_rejects_stale_metadata(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            manifest_path = out_dir / "manifest.json"
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (out_dir / "COPY_ONLY_INDEX.md").write_text("stale\n", encoding="utf-8")

            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "metadata file is stale",
            ):
                send_copy_batch.check_send_copy_directory(
                    out_dir,
                    require_date="2026-05-10",
                )

    def test_check_send_copy_directory_rejects_stale_subject_order(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            manifest_path = out_dir / "manifest.json"
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (out_dir / "SUBJECT_ORDER.md").write_text("stale\n", encoding="utf-8")

            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "metadata file is stale",
            ):
                send_copy_batch.check_send_copy_directory(
                    out_dir,
                    require_date="2026-05-10",
                )

    def test_check_send_copy_directory_rejects_tracker_metadata_leak(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "send-copy"
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=out_dir,
                require_date="2026-05-10",
            )
            manifest_path = out_dir / "manifest.json"
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (out_dir / "01.txt").write_text(
                "Subject: bad\n\nmake validation-status DATE=2026-05-10\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "contains tracker metadata",
            ):
                send_copy_batch.check_send_copy_directory(
                    out_dir,
                    require_date="2026-05-10",
                )

    def test_rejects_copy_text_with_target_label_leak(self) -> None:
        targets, pack = _targets_and_pack()
        pack = copy.deepcopy(pack)
        pack["drafts"][0]["body"] += "\n\ntarget-dib-platform-001"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "contains target label",
            ):
                send_copy_batch.write_send_copy_batch(
                    pack,
                    targets,
                    out_dir=Path(tmp),
                    require_date="2026-05-10",
                )

    def test_rejects_copy_text_with_tracker_command_leak(self) -> None:
        targets, pack = _targets_and_pack()
        pack = copy.deepcopy(pack)
        pack["drafts"][0]["body"] += "\n\nmake validation-status DATE=2026-05-10"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "contains tracker metadata",
            ):
                send_copy_batch.write_send_copy_batch(
                    pack,
                    targets,
                    out_dir=Path(tmp),
                    require_date="2026-05-10",
                )

    def test_rejects_copy_text_with_placeholder(self) -> None:
        targets, pack = _targets_and_pack()
        pack = copy.deepcopy(pack)
        pack["drafts"][0]["body"] = pack["drafts"][0]["body"].replace(
            "Hi,",
            "Hi <first name>,",
            1,
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                send_copy_batch.SendCopyBatchError,
                "contains placeholder text",
            ):
                send_copy_batch.write_send_copy_batch(
                    pack,
                    targets,
                    out_dir=Path(tmp),
                    require_date="2026-05-10",
                )

    def test_cli_rejects_required_date_mismatch(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_path = tmp_path / "pack.json"
            targets_path = tmp_path / "targets.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(BATCH_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--require-date",
                    "2026-05-11",
                    "--out-dir",
                    str(tmp_path / "send-copy"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match required date", completed.stderr)


def _targets_and_pack():
    targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
    block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
    pack = message_pack.build_message_pack(block)
    return targets, pack


if __name__ == "__main__":
    unittest.main()
