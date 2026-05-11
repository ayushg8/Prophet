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
EXAMPLE = ROOT / "docs" / "validation-targets.example.json"

OUTREACH_SPEC = importlib.util.spec_from_file_location(
    "validation_outreach_block_for_messages", OUTREACH_SCRIPT
)
assert OUTREACH_SPEC and OUTREACH_SPEC.loader
outreach_block = importlib.util.module_from_spec(OUTREACH_SPEC)
sys.modules[OUTREACH_SPEC.name] = outreach_block
OUTREACH_SPEC.loader.exec_module(outreach_block)

MESSAGE_SPEC = importlib.util.spec_from_file_location("validation_message_pack", MESSAGE_SCRIPT)
assert MESSAGE_SPEC and MESSAGE_SPEC.loader
message_pack = importlib.util.module_from_spec(MESSAGE_SPEC)
sys.modules[MESSAGE_SPEC.name] = message_pack
MESSAGE_SPEC.loader.exec_module(message_pack)


class ValidationMessagePackTests(unittest.TestCase):
    def test_builds_message_pack_from_outreach_block(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")

        pack = message_pack.build_message_pack(block)

        self.assertEqual(pack["schema_version"], message_pack.MESSAGE_PACK_SCHEMA_VERSION)
        self.assertEqual(pack["generated_for"], "2026-05-10")
        self.assertEqual(pack["draft_count"], 8)
        groups = [draft["group"] for draft in pack["drafts"]]
        self.assertEqual(groups.count("targeted_ask"), 5)
        self.assertEqual(groups.count("follow_up_backfill"), 2)
        self.assertEqual(groups.count("referral_ask"), 1)
        self.assertTrue(
            all("No live data ask" in draft["body"] for draft in pack["drafts"])
        )
        self.assertTrue(any("CMMC" in draft["body"] for draft in pack["drafts"]))
        first_draft = pack["drafts"][0]
        self.assertIn("tracker_update_command", first_draft)
        self.assertEqual(
            first_draft["dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            first_draft["pre_send_check_command"],
            "make validation-pre-send-check TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            first_draft["confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertIn("--last-touch 2026-05-10", first_draft["tracker_update_command"])
        self.assertIn("--follow-up-due 2026-05-13", first_draft["tracker_update_command"])
        self.assertIn("--require-current-status identified", first_draft["tracker_update_command"])
        self.assertIn("--require-current-status intro_requested", first_draft["tracker_update_command"])
        self.assertTrue(first_draft["tracker_update_command"].endswith("--dry-run"))
        self.assertIn(
            "make validation-status DATE=2026-05-10",
            "\n".join(pack["operator_notes"]),
        )
        self.assertIn(
            "Run the pre-send check command immediately before sending.",
            "\n".join(pack["operator_notes"]),
        )
        self.assertEqual(first_draft["source"], "warm_intro_needed")
        self.assertIn("Do you know someone", first_draft["body"])
        cold_draft = next(
            draft for draft in pack["drafts"] if draft["target_label"] == "target-dib-platform-004"
        )
        self.assertEqual(cold_draft["source"], "cold_outreach")
        self.assertIn("Is that a real pain", cold_draft["body"])
        referral_draft = pack["drafts"][-1]
        self.assertIn("--status intro_requested", referral_draft["tracker_update_command"])
        self.assertIn("--require-current-status identified", referral_draft["tracker_update_command"])

    def test_follow_up_tracker_command_requires_due_status(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets["targets"][0]["status"] = "follow_up_due"
        targets["targets"][0]["follow_up_due"] = "2026-05-10"
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")

        pack = message_pack.build_message_pack(block)

        follow_up_draft = next(draft for draft in pack["drafts"] if draft["group"] == "follow_up")
        self.assertIn("--status outreach_sent", follow_up_draft["tracker_update_command"])
        self.assertIn(
            "--require-current-status follow_up_due",
            follow_up_draft["tracker_update_command"],
        )
        self.assertIn(
            "--require-current-status outreach_sent",
            follow_up_draft["tracker_update_command"],
        )

    def test_due_outreach_sent_target_gets_follow_up_draft(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        targets["targets"][0]["status"] = "outreach_sent"
        targets["targets"][0]["last_touch"] = "2026-05-10"
        targets["targets"][0]["follow_up_due"] = "2026-05-13"
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-13")

        pack = message_pack.build_message_pack(block)

        follow_up_draft = next(draft for draft in pack["drafts"] if draft["group"] == "follow_up")
        self.assertEqual(follow_up_draft["target_label"], "target-dib-platform-001")
        self.assertIn("Following up on the narrow workflow question", follow_up_draft["body"])
        self.assertIn(
            "--require-current-status outreach_sent",
            follow_up_draft["tracker_update_command"],
        )

    def test_markdown_is_safe_and_send_ready(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        rendered = message_pack.render_markdown(pack)

        self.assertIn("Prophet Validation Message Pack - 2026-05-10", rendered)
        self.assertIn("Execution Checklist", rendered)
        self.assertIn("- [ ] target-dib-platform-001", rendered)
        self.assertIn("run `make validation-apply-draft", rendered)
        self.assertIn("run `make validation-pre-send-check", rendered)
        self.assertIn(
            "` immediately before sending, send copy-only text, then run `make validation-apply-draft",
            rendered,
        )
        self.assertIn("confirming the message was sent", rendered)
        self.assertIn(
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
            rendered,
        )
        self.assertIn(
            "make validation-pre-send-check TARGET=target-dib-platform-001 DATE=2026-05-10",
            rendered,
        )
        self.assertIn("DATE=2026-05-10 CONFIRM_SENT=1", rendered)
        self.assertIn("Source: warm intro needed", rendered)
        self.assertIn("Safe dry-run apply command:", rendered)
        self.assertIn("Pre-send check command:", rendered)
        self.assertIn("Confirmed-send apply command:", rendered)
        self.assertIn("Subject options:", rendered)
        self.assertIn("Tracker update command:", rendered)
        self.assertIn("Hi,", rendered)
        self.assertNotIn("<first name>", rendered)
        self.assertIn("No live data ask, no exploit tooling, no sales deck.", rendered)
        self.assertIn("make validation-status DATE=2026-05-10", rendered)
        self.assertIn("before sending and before writing tracker changes", rendered)
        self.assertNotIn("@", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_filter_pack_by_target_label_renders_one_draft(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        filtered = message_pack.filter_pack_by_target_label(pack, "target-dib-platform-004")
        rendered = message_pack.render_markdown(filtered)

        self.assertEqual(filtered["draft_count"], 1)
        self.assertEqual(filtered["drafts"][0]["target_label"], "target-dib-platform-004")
        self.assertIn("target-dib-platform-004 - targeted_ask", rendered)
        self.assertNotIn("target-dib-platform-001 - targeted_ask", rendered)

    def test_send_text_requires_one_filtered_draft(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        filtered = message_pack.filter_pack_by_target_label(pack, "target-dib-platform-004")

        rendered = message_pack.render_send_text(filtered)

        self.assertIn("target-dib-platform-001", filtered["target_labels"])
        self.assertTrue(rendered.startswith("Subject: "))
        self.assertIn("Hi,", rendered)
        self.assertNotIn("<first name>", rendered)
        self.assertNotRegex(rendered, r"<[^>\n]+>")
        self.assertIn("No live data ask, no exploit tooling, no sales deck.", rendered)
        self.assertNotIn("target-dib-platform-004", rendered)
        self.assertNotIn("make validation-apply-draft", rendered)
        self.assertNotIn("Tracker update command", rendered)
        with self.assertRaisesRegex(message_pack.MessagePackError, "requires exactly one draft"):
            message_pack.render_send_text(pack)

    def test_send_text_rejects_target_label_leak(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        for target_label in ("target-dib-platform-001", "target-dib-platform-004"):
            with self.subTest(target_label=target_label):
                filtered = message_pack.filter_pack_by_target_label(
                    pack,
                    "target-dib-platform-004",
                )
                filtered = copy.deepcopy(filtered)
                filtered["drafts"][0]["body"] += f"\n\n{target_label}"

                with self.assertRaisesRegex(message_pack.MessagePackError, "contains target label"):
                    message_pack.render_send_text(filtered)

    def test_send_text_rejects_tracker_command_leak(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        filtered = message_pack.filter_pack_by_target_label(pack, "target-dib-platform-004")
        filtered = copy.deepcopy(filtered)
        filtered["drafts"][0]["body"] += "\n\nmake validation-status DATE=2026-05-10"

        with self.assertRaisesRegex(message_pack.MessagePackError, "contains tracker metadata"):
            message_pack.render_send_text(filtered)

    def test_cli_target_label_filter_outputs_one_json_draft(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.json"
            block_path.write_text(json.dumps(block), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MESSAGE_SCRIPT),
                    "--block",
                    str(block_path),
                    "--target-label",
                    "target-dib-platform-004",
                    "--require-date",
                    "2026-05-10",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

        rendered = json.loads(completed.stdout)
        self.assertEqual(rendered["draft_count"], 1)
        self.assertEqual(rendered["drafts"][0]["target_label"], "target-dib-platform-004")

    def test_cli_target_label_outputs_send_text_without_tracker_metadata(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.json"
            block_path.write_text(json.dumps(block), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MESSAGE_SCRIPT),
                    "--block",
                    str(block_path),
                    "--target-label",
                    "target-dib-platform-004",
                    "--require-date",
                    "2026-05-10",
                    "--format",
                    "send-text",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertTrue(completed.stdout.startswith("Subject: "))
        self.assertIn("Is that a real pain", completed.stdout)
        self.assertIn("Hi,", completed.stdout)
        self.assertNotIn("<first name>", completed.stdout)
        self.assertNotRegex(completed.stdout, r"<[^>\n]+>")
        self.assertNotIn("target-dib-platform-004", completed.stdout)
        self.assertNotIn("make validation-apply-draft", completed.stdout)

    def test_send_text_rejects_placeholder_text(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        filtered = message_pack.filter_pack_by_target_label(pack, "target-dib-platform-004")
        filtered = copy.deepcopy(filtered)
        filtered["drafts"][0]["body"] = filtered["drafts"][0]["body"].replace(
            "Hi,",
            "Hi <first name>,",
            1,
        )

        with self.assertRaisesRegex(message_pack.MessagePackError, "placeholder text"):
            message_pack.render_send_text(filtered)

    def test_cli_send_text_requires_target_label_when_pack_has_multiple_drafts(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.json"
            block_path.write_text(json.dumps(block), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MESSAGE_SCRIPT),
                    "--block",
                    str(block_path),
                    "--require-date",
                    "2026-05-10",
                    "--format",
                    "send-text",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("send-text format requires exactly one draft", completed.stderr)

    def test_cli_rejects_required_date_mismatch(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.json"
            block_path.write_text(json.dumps(block), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MESSAGE_SCRIPT),
                    "--block",
                    str(block_path),
                    "--target-label",
                    "target-dib-platform-004",
                    "--require-date",
                    "2026-05-11",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("does not match required date 2026-05-11", completed.stderr)

    def test_cli_rejects_bad_required_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.json"
            block_path.write_text(json.dumps(block), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MESSAGE_SCRIPT),
                    "--block",
                    str(block_path),
                    "--require-date",
                    "05/10/2026",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("require-date must be YYYY-MM-DD", completed.stderr)

    def test_filter_rejects_unknown_target_label(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with self.assertRaisesRegex(message_pack.MessagePackError, "target_label not found"):
            message_pack.filter_pack_by_target_label(pack, "missing-target")

    def test_rejects_sensitive_block_text(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        block = copy.deepcopy(block)
        block["targeted_asks"][0]["next_action"] = "Send to buyer@example.com"

        with self.assertRaisesRegex(message_pack.MessagePackError, "email-like"):
            message_pack.build_message_pack(block)

    def test_rejects_bad_schema(self) -> None:
        with self.assertRaisesRegex(message_pack.MessagePackError, "schema_version"):
            message_pack.build_message_pack({"schema_version": "wrong", "generated_for": "2026-05-10"})

    def test_rejects_bad_generated_for_date(self) -> None:
        targets = outreach_block.json.loads(EXAMPLE.read_text(encoding="utf-8"))
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        block["generated_for"] = "2026/05/10"

        with self.assertRaisesRegex(message_pack.MessagePackError, "generated_for"):
            message_pack.build_message_pack(block)


if __name__ == "__main__":
    unittest.main()
