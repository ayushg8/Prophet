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
NEXT_DRAFT_SCRIPT = ROOT / "scripts" / "validation-next-draft.py"
TARGET_UPDATE_SCRIPT = ROOT / "scripts" / "validation-target-update.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


outreach_block = _load_module("validation_outreach_block_for_next", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_next", MESSAGE_SCRIPT)
next_draft = _load_module("validation_next_draft", NEXT_DRAFT_SCRIPT)
target_update = _load_module("validation_target_update_for_next", TARGET_UPDATE_SCRIPT)


class ValidationNextDraftTests(unittest.TestCase):
    def test_selects_first_verified_pending_draft(self) -> None:
        targets, pack = _targets_and_pack()

        selected = next_draft.build_next_draft(pack, targets)

        self.assertEqual(selected["schema_version"], next_draft.NEXT_DRAFT_SCHEMA_VERSION)
        self.assertEqual(selected["generated_for"], "2026-05-10")
        self.assertEqual(selected["target_label"], "target-dib-platform-001")
        self.assertIn("target-dib-platform-002", selected["target_labels"])
        self.assertEqual(selected["remaining_pending_count"], 8)
        self.assertEqual(
            selected["dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            selected["confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertEqual(selected["status_item"]["state"], "pending_send_or_update")
        self.assertTrue(selected["status_item"]["dry_run_verification"]["ok"])
        self.assertIn(
            "make validation-status DATE=2026-05-10",
            "\n".join(selected["operator_notes"]),
        )
        self.assertIn(
            "Replace only the recipient name",
            "\n".join(selected["operator_notes"]),
        )
        self.assertIn(
            "before sending or writing tracker changes",
            "\n".join(selected["operator_notes"]),
        )
        self.assertIn(
            "Send the copy-only text before applying the confirmed tracker update.",
            "\n".join(selected["operator_notes"]),
        )
        self.assertNotIn("Send this draft", "\n".join(selected["operator_notes"]))

    def test_markdown_renders_only_selected_draft(self) -> None:
        targets, pack = _targets_and_pack()
        selected = next_draft.build_next_draft(pack, targets)

        rendered = next_draft.render_markdown(selected)

        self.assertIn("Next Prophet Validation Draft - 2026-05-10", rendered)
        self.assertIn("This file is tracker/audit metadata. Do not paste it to a buyer.", rendered)
        self.assertIn("make validation-send-copy DATE=2026-05-10", rendered)
        self.assertIn("validation/private/today-send-copy.txt", rendered)
        self.assertIn("send copy is ready and matches the next pending target", rendered)
        self.assertIn("target-dib-platform-001", rendered)
        self.assertNotIn("target-dib-platform-002 - targeted_ask", rendered)
        self.assertIn("Safe Tracker Commands", rendered)
        self.assertIn("Dry-run before sending or writing", rendered)
        self.assertIn(
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
            rendered,
        )
        self.assertIn("CONFIRM_SENT=1", rendered)
        self.assertIn("Tracker update command:", rendered)
        self.assertIn("Replace only the recipient name", rendered)
        self.assertIn("Rerun make validation-status DATE=2026-05-10", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_send_text_excludes_tracker_metadata(self) -> None:
        targets, pack = _targets_and_pack()
        selected = next_draft.build_next_draft(pack, targets)

        rendered = next_draft.render_send_text(selected)

        self.assertTrue(rendered.startswith("Subject: Intro to someone"))
        self.assertNotIn("Subject options:", rendered)
        self.assertNotIn("Message:", rendered)
        self.assertIn("Hi <first name>", rendered)
        self.assertIn("No live data ask", rendered)
        self.assertNotIn("Who should I learn from", rendered)
        self.assertNotIn("Prophet Validation Draft", rendered)
        self.assertNotIn("target-", rendered)
        self.assertNotIn("target-dib-platform-001", rendered)
        self.assertNotIn("make validation-apply-draft", rendered)
        self.assertNotIn("Tracker update command", rendered)
        self.assertNotIn("CONFIRM_SENT", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_send_text_rejects_target_label_leak(self) -> None:
        targets, pack = _targets_and_pack()
        for target_label in ("target-dib-platform-001", "target-dib-platform-002"):
            with self.subTest(target_label=target_label):
                selected = next_draft.build_next_draft(pack, targets)
                selected = copy.deepcopy(selected)
                selected["draft"]["body"] += f"\n\n{target_label}"

                with self.assertRaisesRegex(next_draft.NextDraftError, "contains target label"):
                    next_draft.render_send_text(selected)

    def test_send_text_rejects_tracker_command_leak(self) -> None:
        targets, pack = _targets_and_pack()
        selected = next_draft.build_next_draft(pack, targets)
        selected = copy.deepcopy(selected)
        selected["draft"]["body"] += "\n\nmake validation-status DATE=2026-05-10"

        with self.assertRaisesRegex(next_draft.NextDraftError, "contains tracker metadata"):
            next_draft.render_send_text(selected)

    def test_refuses_when_status_needs_attention(self) -> None:
        targets, pack = _targets_and_pack()
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"

        with self.assertRaisesRegex(next_draft.NextDraftError, "needs attention"):
            next_draft.build_next_draft(pack, targets)

    def test_refuses_required_date_mismatch(self) -> None:
        targets, pack = _targets_and_pack()

        with self.assertRaisesRegex(next_draft.NextDraftError, "required date"):
            next_draft.build_next_draft(pack, targets, require_date="2026-05-11")

    def test_rejects_bad_required_date(self) -> None:
        targets, pack = _targets_and_pack()

        with self.assertRaisesRegex(next_draft.NextDraftError, "YYYY-MM-DD"):
            next_draft.build_next_draft(pack, targets, require_date="05/10/2026")

    def test_refuses_when_no_pending_drafts_remain(self) -> None:
        targets, pack = _targets_and_pack()
        targets = copy.deepcopy(targets)
        for draft in pack["drafts"]:
            parts = _tracker_command_parts(draft["tracker_update_command"])
            target_update.update_target(
                targets,
                target_label=parts["target_label"],
                status=parts["status"],
                last_touch=parts["last_touch"],
                follow_up_due=parts["follow_up_due"],
                next_action=parts["next_action"],
                updated_at="2026-05-10",
            )

        with self.assertRaisesRegex(next_draft.NextDraftError, "no pending"):
            next_draft.build_next_draft(pack, targets)

    def test_cli_outputs_one_json_draft(self) -> None:
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
                    str(NEXT_DRAFT_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--format",
                    "json",
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
        rendered = json.loads(completed.stdout)
        self.assertEqual(rendered["target_label"], "target-dib-platform-001")
        self.assertEqual(rendered["draft"]["target_label"], "target-dib-platform-001")

    def test_cli_send_text_outputs_copy_only_draft(self) -> None:
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
                    str(NEXT_DRAFT_SCRIPT),
                    "--message-pack",
                    str(pack_path),
                    "--targets",
                    str(targets_path),
                    "--format",
                    "send-text",
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
        self.assertTrue(completed.stdout.startswith("Subject: Intro to someone"))
        self.assertNotIn("Subject options:", completed.stdout)
        self.assertNotIn("Message:", completed.stdout)
        self.assertIn("Hi <first name>", completed.stdout)
        self.assertNotIn("target-", completed.stdout)
        self.assertNotIn("make validation-apply-draft", completed.stdout)
        self.assertNotIn("Tracker update command", completed.stdout)
        self.assertNotIn("CONFIRM_SENT", completed.stdout)


def _targets_and_pack():
    targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
    block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
    pack = message_pack.build_message_pack(block)
    return targets, pack


def _tracker_command_parts(command: str) -> dict[str, str]:
    status_module = _load_module("validation_outreach_status_for_next", ROOT / "scripts" / "validation-outreach-status.py")
    return status_module._parse_tracker_command(command)


if __name__ == "__main__":
    unittest.main()
