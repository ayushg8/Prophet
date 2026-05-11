from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTREACH_SCRIPT = ROOT / "scripts" / "validation-outreach-block.py"
MESSAGE_SCRIPT = ROOT / "scripts" / "validation-message-pack.py"
STATUS_SCRIPT = ROOT / "scripts" / "validation-outreach-status.py"
TARGET_UPDATE_SCRIPT = ROOT / "scripts" / "validation-target-update.py"
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


outreach_block = _load_module("validation_outreach_block_for_status", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_status", MESSAGE_SCRIPT)
outreach_status = _load_module("validation_outreach_status", STATUS_SCRIPT)
target_update = _load_module("validation_target_update_for_status", TARGET_UPDATE_SCRIPT)


class ValidationOutreachStatusTests(unittest.TestCase):
    def test_current_example_pack_is_pending_before_tracker_updates(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)

        status = outreach_status.build_status(
            pack,
            targets,
            verify_dry_run_commands=True,
            require_date="2026-05-10",
        )

        self.assertFalse(status["complete"])
        self.assertEqual(status["counts"]["pending_send_or_update"], 8)
        self.assertEqual(status["counts"]["updated_after_send"], 0)
        self.assertEqual(status["counts"]["needs_attention"], 0)
        self.assertEqual(status["dry_run_verified_count"], 8)
        self.assertEqual(status["dry_run_failed_count"], 0)
        self.assertEqual(status["dry_run_skipped_count"], 0)
        self.assertEqual(status["next_pending_target_label"], "target-dib-platform-001")
        self.assertEqual(status["next_pending_group"], "targeted_ask")
        self.assertEqual(
            status["next_pending_dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            status["next_pending_confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertEqual(status["status_command"], "make validation-status DATE=2026-05-10")
        self.assertTrue(
            all(
                item["dry_run_verification"]["ok"] is True
                for item in status["items"]
            )
        )
        self.assertEqual(
            status["items"][0]["expected"]["require_current_status"],
            ["identified", "intro_requested"],
        )
        self.assertEqual(
            status["items"][0]["dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            status["items"][0]["confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertIn("Run the Make dry-run command", status["items"][0]["action"])
        self.assertIn("make validation-send-copy", status["items"][0]["action"])
        self.assertIn("send that text outside the repo", status["items"][0]["action"])
        self.assertIn("actual send is confirmed", status["items"][0]["action"])

    def test_required_date_must_match_message_pack_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)

        with self.assertRaisesRegex(
            outreach_status.OutreachStatusError,
            "does not match required date 2026-05-11",
        ):
            outreach_status.build_status(pack, targets, require_date="2026-05-11")

    def test_required_date_must_be_iso_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)

        with self.assertRaisesRegex(
            outreach_status.OutreachStatusError,
            "require-date must be YYYY-MM-DD",
        ):
            outreach_status.build_status(pack, targets, require_date="05/10/2026")

    def test_updated_targets_are_marked_complete(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)
        targets = copy.deepcopy(targets)
        for draft in pack["drafts"]:
            expected = outreach_status._parse_tracker_command(draft["tracker_update_command"])
            target_update.update_target(
                targets,
                target_label=expected["target_label"],
                status=expected["status"],
                last_touch=expected["last_touch"],
                follow_up_due=expected["follow_up_due"],
                next_action=expected["next_action"],
                updated_at="2026-05-10",
            )

        status = outreach_status.build_status(
            pack,
            targets,
            verify_dry_run_commands=True,
        )

        self.assertTrue(status["complete"])
        self.assertEqual(status["counts"]["updated_after_send"], 8)
        self.assertEqual(status["counts"]["pending_send_or_update"], 0)
        self.assertEqual(status["dry_run_verified_count"], 0)
        self.assertEqual(status["dry_run_skipped_count"], 8)
        self.assertIsNone(status["next_pending_target_label"])
        self.assertIsNone(status["next_pending_group"])
        self.assertIsNone(status["next_pending_dry_run_apply_command"])
        self.assertIsNone(status["next_pending_confirmed_apply_command"])

    def test_stale_pending_command_needs_attention(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"

        status = outreach_status.build_status(
            pack,
            targets,
            verify_dry_run_commands=True,
        )

        self.assertEqual(status["counts"]["needs_attention"], 1)
        self.assertEqual(status["dry_run_failed_count"], 1)
        self.assertEqual(status["items"][0]["state"], "needs_attention")
        self.assertFalse(status["items"][0]["dry_run_verification"]["ok"])
        self.assertIn(
            "target current status must be one of",
            status["items"][0]["dry_run_verification"]["error"],
        )

    def test_missing_target_needs_attention(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)
        targets = copy.deepcopy(targets)
        targets["targets"] = [
            target
            for target in targets["targets"]
            if target["target_label"] != pack["drafts"][0]["target_label"]
        ]

        status = outreach_status.build_status(
            pack,
            targets,
            verify_dry_run_commands=True,
        )

        self.assertEqual(status["counts"]["needs_attention"], 1)
        self.assertEqual(status["items"][0]["mismatches"], ["target_label"])

    def test_rejects_tracker_command_without_dry_run(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)
        pack = copy.deepcopy(pack)
        pack["drafts"][0]["tracker_update_command"] = pack["drafts"][0][
            "tracker_update_command"
        ].replace(" --dry-run", "")

        with self.assertRaisesRegex(outreach_status.OutreachStatusError, "dry-run"):
            outreach_status.build_status(pack, targets)

    def test_markdown_includes_operator_actions(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        pack = _message_pack_from_targets(targets)
        status = outreach_status.build_status(
            pack,
            targets,
            verify_dry_run_commands=True,
        )

        rendered = outreach_status.render_markdown(status)

        self.assertIn("Prophet Outreach Execution Status - 2026-05-10", rendered)
        self.assertIn("Pending send/update: 8", rendered)
        self.assertIn("Dry-run verified: 8", rendered)
        self.assertIn("Dry-run failed: 0", rendered)
        self.assertIn("Next pending target: target-dib-platform-001", rendered)
        self.assertIn("Next pending group: targeted_ask", rendered)
        self.assertIn(
            "Next safe dry-run apply command: `make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10`",
            rendered,
        )
        self.assertIn(
            "Next confirmed-send apply command: `make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10 CONFIRM_SENT=1`",
            rendered,
        )
        self.assertIn("Required current status: identified, intro_requested", rendered)
        self.assertIn("make validation-send-copy", rendered)
        self.assertIn("send that text outside the repo", rendered)
        self.assertIn("Dry-run verification: passed", rendered)
        self.assertIn("Safe dry-run apply command:", rendered)
        self.assertIn("Confirmed-send apply command:", rendered)
        self.assertIn("Dry-run command:", rendered)
        self.assertIn("Rerun make validation-dashboard DATE=2026-05-10", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)


def _message_pack_from_targets(targets):
    block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
    return message_pack.build_message_pack(block)


if __name__ == "__main__":
    unittest.main()
