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
APPLY_SCRIPT = ROOT / "scripts" / "validation-apply-draft-update.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


outreach_block = _load_module("validation_outreach_block_for_apply", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_apply", MESSAGE_SCRIPT)
apply_update = _load_module("validation_apply_draft_update", APPLY_SCRIPT)


class ValidationApplyDraftUpdateTests(unittest.TestCase):
    def test_dry_run_summary_does_not_require_confirmed_send(self) -> None:
        targets, pack = _targets_and_pack()

        summary, updated = apply_update.build_update_summary(
            pack,
            targets,
            target_label="target-dib-platform-001",
            require_date="2026-05-10",
        )

        self.assertTrue(summary["ok"])
        self.assertFalse(summary["confirmed_sent"])
        self.assertFalse(summary["would_write"])
        self.assertEqual(
            summary["dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            summary["confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertEqual(summary["status_command"], "make validation-status DATE=2026-05-10")
        self.assertEqual(
            summary["dashboard_command"],
            "make validation-dashboard DATE=2026-05-10",
        )
        self.assertEqual(summary["tracker_update"]["after"]["status"], "outreach_sent")
        self.assertIn(
            "make validation-status DATE=2026-05-10",
            "\n".join(summary["operator_notes"]),
        )
        self.assertEqual(updated["targets"][0]["status"], "outreach_sent")
        self.assertEqual(targets["targets"][0]["status"], "identified")
        self.assertEqual(targets["targets"][0]["follow_up_due"], "")

    def test_confirmed_summary_returns_updated_copy_without_mutating_input(self) -> None:
        targets, pack = _targets_and_pack()

        summary, updated = apply_update.build_update_summary(
            pack,
            targets,
            target_label="target-dib-platform-001",
            confirm_sent=True,
            require_date="2026-05-10",
        )

        self.assertTrue(summary["confirmed_sent"])
        self.assertTrue(summary["would_write"])
        self.assertEqual(
            summary["confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertEqual(updated["targets"][0]["status"], "outreach_sent")
        self.assertEqual(targets["targets"][0]["status"], "identified")

    def test_confirmed_send_cli_requires_copy_artifact_guard(self) -> None:
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
                    str(APPLY_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--require-date",
                    "2026-05-10",
                    "--confirm-sent",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("require --require-copy-artifact", completed.stderr)
            written = json.loads(targets_path.read_text(encoding="utf-8"))

        self.assertEqual(written["targets"][0]["status"], "identified")
        self.assertEqual(written["targets"][0]["follow_up_due"], "")

    def test_confirmed_send_cli_can_require_matching_copy_artifact(self) -> None:
        targets, pack = _targets_and_pack()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_path = tmp_path / "pack.json"
            targets_path = tmp_path / "targets.json"
            send_copy_path = tmp_path / "send-copy.txt"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            send_copy_path.write_text(
                message_pack.render_send_text(
                    message_pack.filter_pack_by_target_label(
                        pack,
                        "target-dib-platform-001",
                    )
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(APPLY_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--require-date",
                    "2026-05-10",
                    "--require-copy-artifact",
                    "--send-copy",
                    str(send_copy_path),
                    "--confirm-sent",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            written = json.loads(targets_path.read_text(encoding="utf-8"))

        self.assertTrue(summary["copy_artifact_verification"]["ok"])
        self.assertEqual(summary["copy_artifact_verification"]["kind"], "send_copy")
        self.assertEqual(written["targets"][0]["status"], "outreach_sent")

    def test_confirmed_send_cli_rejects_missing_required_copy_artifact(self) -> None:
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
                    str(APPLY_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--require-date",
                    "2026-05-10",
                    "--require-copy-artifact",
                    "--send-copy",
                    str(tmp_path / "missing-send-copy.txt"),
                    "--confirm-sent",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("copy-only send artifact is not ready", completed.stderr)
            written = json.loads(targets_path.read_text(encoding="utf-8"))

        self.assertEqual(written["targets"][0]["status"], "identified")

    def test_cli_without_confirmed_send_does_not_write(self) -> None:
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
                    str(APPLY_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--target-label",
                    "target-dib-platform-001",
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
            written = json.loads(targets_path.read_text(encoding="utf-8"))

        self.assertEqual(written["targets"][0]["status"], "identified")

    def test_refuses_stale_target_state(self) -> None:
        targets, pack = _targets_and_pack()
        targets["targets"][0]["status"] = "completed"

        with self.assertRaisesRegex(apply_update.ApplyDraftUpdateError, "advanced"):
            apply_update.build_update_summary(
                pack,
                targets,
                target_label="target-dib-platform-001",
            )

    def test_refuses_date_mismatch(self) -> None:
        targets, pack = _targets_and_pack()

        with self.assertRaisesRegex(apply_update.ApplyDraftUpdateError, "required date"):
            apply_update.build_update_summary(
                pack,
                targets,
                target_label="target-dib-platform-001",
                require_date="2026-05-11",
            )

    def test_refuses_unknown_target_label(self) -> None:
        targets, pack = _targets_and_pack()

        with self.assertRaisesRegex(apply_update.ApplyDraftUpdateError, "not found"):
            apply_update.build_update_summary(
                pack,
                targets,
                target_label="target-missing",
            )


def _targets_and_pack():
    targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
    block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
    pack = message_pack.build_message_pack(block)
    return targets, pack


if __name__ == "__main__":
    unittest.main()
