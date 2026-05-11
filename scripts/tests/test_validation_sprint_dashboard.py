from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation-sprint-dashboard.py"
OUTREACH_SCRIPT = ROOT / "scripts" / "validation-outreach-block.py"
MESSAGE_SCRIPT = ROOT / "scripts" / "validation-message-pack.py"
NEXT_DRAFT_SCRIPT = ROOT / "scripts" / "validation-next-draft.py"
STATUS_SCRIPT = ROOT / "scripts" / "validation-outreach-status.py"
TARGET_UPDATE_SCRIPT = ROOT / "scripts" / "validation-target-update.py"
BATCH_SCRIPT = ROOT / "scripts" / "validation-send-copy-batch.py"
SPEC = importlib.util.spec_from_file_location("validation_sprint_dashboard", SCRIPT)
assert SPEC and SPEC.loader
dashboard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dashboard
SPEC.loader.exec_module(dashboard)


class ValidationSprintDashboardTests(unittest.TestCase):
    def test_combines_example_scorecards_and_keeps_build_gate_closed(self) -> None:
        summary = dashboard.build_dashboard(
            log_path=ROOT / "docs/customer-validation-log.example.json",
            targets_path=ROOT / "docs/validation-targets.example.json",
            scripts_dir=ROOT / "scripts",
        )

        self.assertEqual(summary["schema_version"], dashboard.DASHBOARD_SCHEMA_VERSION)
        self.assertEqual(summary["customer_validation"]["verdict"], "insufficient_data")
        self.assertTrue(summary["customer_validation"]["example_seed_log"])
        self.assertFalse(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertIn("example-only", summary["build_gate"]["reason"])
        self.assertFalse(summary["outreach_execution"]["available"])
        self.assertTrue(any("Do not build" in action for action in summary["next_actions"]))
        self.assertTrue(
            any(
                "Build gate gap to build_next_slice: 15 qualified call(s)" in action
                for action in summary["next_actions"]
            )
        )
        self.assertTrue(any("3 pilot-pull signal(s)" in action for action in summary["next_actions"]))
        self.assertTrue(any("follow-up backfill" in action for action in summary["next_actions"]))
        self.assertEqual(
            len(summary["next_actions"]),
            len(set(summary["next_actions"])),
        )

    def test_private_message_pack_status_is_summarized_when_provided(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["available"])
        self.assertEqual(summary["outreach_execution"]["draft_count"], 8)
        self.assertEqual(summary["outreach_execution"]["dry_run_verified_count"], 8)
        self.assertEqual(summary["outreach_execution"]["dry_run_failed_count"], 0)
        self.assertEqual(summary["outreach_execution"]["dry_run_skipped_count"], 0)
        self.assertEqual(summary["outreach_execution"]["counts"]["needs_attention"], 0)
        self.assertEqual(
            summary["outreach_execution"]["next_draft_path"],
            str(pack_path.with_name("today-next-draft.md")),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_path"],
            str(pack_path.with_name("today-send-copy.txt")),
        )
        self.assertFalse(summary["outreach_execution"]["send_copy_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_matches_next_pending"])
        self.assertEqual(summary["outreach_execution"]["send_copy_state"], "missing")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_command"],
            "make validation-send-copy DATE=2026-05-10",
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_dir"],
            str(pack_path.with_name("send-copy-2026-05-10")),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_readme_path"],
            str(pack_path.with_name("send-copy-2026-05-10") / "README.md"),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_checklist_path"],
            str(pack_path.with_name("send-copy-2026-05-10") / "CHECKLIST.md"),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_copy_index_path"],
            str(pack_path.with_name("send-copy-2026-05-10") / "COPY_ONLY_INDEX.md"),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_subject_order_path"],
            str(pack_path.with_name("send-copy-2026-05-10") / "SUBJECT_ORDER.md"),
        )
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_command"],
            "make validation-send-copy-batch DATE=2026-05-10",
        )
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_checklist_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_copy_index_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_subject_order_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "missing")
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_copy_file_count"], 0)
        self.assertFalse(summary["outreach_execution"]["next_draft_exists"])
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "missing")
        self.assertIsNone(summary["outreach_execution"]["next_draft_target_label"])
        self.assertEqual(
            summary["outreach_execution"]["next_pending_target_label"],
            "target-dib-platform-001",
        )
        self.assertEqual(summary["outreach_execution"]["next_pending_group"], "targeted_ask")
        self.assertEqual(
            summary["outreach_execution"]["next_pending_dry_run_apply_command"],
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
        )
        self.assertEqual(
            summary["outreach_execution"]["next_pending_confirmed_apply_command"],
            (
                "make validation-apply-draft TARGET=target-dib-platform-001 "
                "DATE=2026-05-10 CONFIRM_SENT=1"
            ),
        )
        self.assertEqual(
            summary["outreach_execution"]["status_command"],
            "make validation-status DATE=2026-05-10",
        )
        self.assertIn(
            f"--message-pack {pack_path}",
            summary["outreach_execution"]["next_draft_command"],
        )
        self.assertIn(
            "--require-date 2026-05-10",
            summary["outreach_execution"]["next_draft_command"],
        )
        self.assertTrue(
            any("Render the next verified outreach draft" in action for action in summary["next_actions"])
        )
        self.assertTrue(
            any("target-dib-platform-001 (targeted_ask)" in action for action in summary["next_actions"])
        )
        self.assertTrue(
            any(
                "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10"
                in action
                for action in summary["next_actions"]
            )
        )
        self.assertTrue(
            any("before sending or writing" in action for action in summary["next_actions"])
        )
        self.assertTrue(
            any(
                "make validation-send-copy DATE=2026-05-10" in action
                for action in summary["next_actions"]
            )
        )
        self.assertFalse(any("send it, then run" in action for action in summary["next_actions"]))
        self.assertTrue(any("CONFIRM_SENT=1" in action for action in summary["next_actions"]))
        self.assertTrue(
            any(
                "make validation-status DATE=2026-05-10" in action
                for action in summary["next_actions"]
            )
        )
        self.assertTrue(any("8 verified draft(s) remain" in action for action in summary["next_actions"]))
        self.assertTrue(
            any("Build gate gap to build_next_slice" in action for action in summary["next_actions"])
        )

    def test_team_update_is_aggregate_only(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_team", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_team", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        rendered = dashboard.render_team_update(summary)

        self.assertIn("Prophet Validation Team Update", rendered)
        self.assertIn("Customer validation verdict: insufficient_data", rendered)
        self.assertIn("Build gate open: false", rendered)
        self.assertIn(
            "Validation data mode: example seed - do not treat counts as real buyer traction",
            rendered,
        )
        self.assertIn("Qualified calls counted for gate: 0", rendered)
        self.assertIn("High-pain calls counted for gate: 0", rendered)
        self.assertIn("Repeated workflow-pain matches counted for gate: 0", rendered)
        self.assertIn("Top workflow pain theme counted for gate: none", rendered)
        self.assertIn("Pilot-pull signals counted for gate: 0", rendered)
        self.assertIn("Paid/sponsored pilot signals counted for gate: 0", rendered)
        self.assertIn("Raw example qualified calls ignored for gate: 1", rendered)
        self.assertIn("Raw example high-pain calls ignored for gate: 1", rendered)
        self.assertIn("Raw example pilot-pull signals ignored for gate: 1", rendered)
        self.assertIn("Raw example paid/sponsored signals ignored for gate: 1", rendered)
        self.assertIn("Pending send/update: 8", rendered)
        self.assertIn("Needs attention: 0", rendered)
        self.assertIn("Send-copy state:", rendered)
        self.assertIn("Send-copy matches next draft:", rendered)
        self.assertIn("Send-copy batch state:", rendered)
        self.assertIn("Send-copy batch README exists:", rendered)
        self.assertIn("Send-copy batch checklist exists:", rendered)
        self.assertIn("Send-copy batch files:", rendered)
        self.assertIn("Send-copy batch matches current pack:", rendered)
        self.assertIn("Replace the example-only validation seed", rendered)
        self.assertIn("Keep the production build gate closed", rendered)
        self.assertIn("Build gate gap to build_next_slice", rendered)
        self.assertNotIn("- Qualified calls: 1", rendered)
        self.assertNotIn("- High-pain calls: 1", rendered)
        self.assertNotIn("- Pilot-pull signals: 1", rendered)
        self.assertNotIn("target-dib-", rendered)
        self.assertNotIn("make validation-apply-draft", rendered)
        self.assertNotIn("validation/private", rendered)
        self.assertNotIn("@", rendered)

    def test_existing_next_draft_changes_action_to_send_boundary(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_existing_draft", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_existing_draft", MESSAGE_SCRIPT)
        next_draft = _load_module("dashboard_next_draft_existing_draft", NEXT_DRAFT_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        selected = next_draft.build_next_draft(pack, targets, require_date="2026-05-10")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            send_copy_path = tmp_path / "today-send-copy.txt"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(next_draft.render_markdown(selected), encoding="utf-8")
            send_copy_path.write_text(next_draft.render_send_text(selected), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["next_draft_exists"])
        self.assertEqual(
            summary["outreach_execution"]["next_draft_target_label"],
            "target-dib-platform-001",
        )
        self.assertEqual(
            summary["outreach_execution"]["next_draft_generated_for"],
            "2026-05-10",
        )
        self.assertEqual(
            summary["outreach_execution"]["next_draft_status"],
            "verified pending send/update",
        )
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "ready")
        self.assertTrue(summary["outreach_execution"]["next_draft_matches_next_pending"])
        self.assertIsNone(summary["outreach_execution"]["next_draft_mismatch_reason"])
        self.assertTrue(summary["outreach_execution"]["send_copy_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_matches_next_pending"])
        self.assertEqual(summary["outreach_execution"]["send_copy_state"], "ready")
        self.assertTrue(
            any(
                "Use the copy-only send text" in action
                for action in summary["next_actions"]
            )
        )
        self.assertTrue(
            any(str(next_draft_path) in action for action in summary["next_actions"])
        )
        self.assertTrue(
            any("is currently verified" in action for action in summary["next_actions"])
        )
        self.assertTrue(
            any("today-send-copy.txt" in action for action in summary["next_actions"])
        )
        self.assertFalse(
            any(
                "Render the next verified outreach draft" in action
                for action in summary["next_actions"]
            )
        )

    def test_existing_send_copy_batch_is_verified(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_ready", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_ready", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_ready", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_checklist_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_copy_index_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_subject_order_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "ready")
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_copy_file_count"], 8)

    def test_missing_send_copy_batch_checklist_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_no_checklist", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_no_checklist", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_no_checklist", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "CHECKLIST.md").unlink()
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_checklist_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch CHECKLIST is missing",
        )

    def test_missing_send_copy_batch_readme_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_no_readme", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_no_readme", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_no_readme", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "README.md").unlink()
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch README is missing",
        )

    def test_missing_send_copy_batch_copy_index_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_no_index", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_no_index", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_no_index", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "COPY_ONLY_INDEX.md").unlink()
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_checklist_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_copy_index_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch COPY_ONLY_INDEX is missing",
        )

    def test_missing_send_copy_batch_subject_order_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_no_subject", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_no_subject", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_no_subject", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "SUBJECT_ORDER.md").unlink()
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_checklist_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_copy_index_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_subject_order_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch SUBJECT_ORDER is missing",
        )

    def test_stale_send_copy_batch_readme_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_stale_readme", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_stale_readme", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_stale_readme", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "README.md").write_text("stale guidance\n", encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_readme_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch README does not match current generator",
        )

    def test_stale_send_copy_batch_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_stale", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_stale", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_stale", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (batch_dir / "01.txt").write_text(
                "stale batch text\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch text does not match current verified drafts",
        )

    def test_stale_send_copy_batch_manifest_hash_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_stale_hash", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_stale_hash", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_stale_hash", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            manifest["files"][0]["sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch manifest does not match current verified drafts",
        )

    def test_stale_send_copy_batch_manifest_boundary_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_batch_stale_boundary", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_batch_stale_boundary", MESSAGE_SCRIPT)
        send_copy_batch = _load_module("dashboard_send_copy_batch_stale_boundary", BATCH_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            batch_dir = tmp_path / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            manifest = send_copy_batch.write_send_copy_batch(
                pack,
                targets,
                out_dir=batch_dir,
                require_date="2026-05-10",
            )
            manifest["manifest_path"] = str(manifest_path)
            del manifest["outbound_safe"]
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["send_copy_batch_exists"])
        self.assertTrue(summary["outreach_execution"]["send_copy_batch_manifest_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_batch_matches_current_pack"])
        self.assertEqual(summary["outreach_execution"]["send_copy_batch_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_batch_mismatch_reason"],
            "send-copy batch manifest does not match current verified drafts",
        )

    def test_stale_send_copy_must_be_refreshed(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_stale_send_copy", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_stale_send_copy", MESSAGE_SCRIPT)
        next_draft = _load_module("dashboard_next_draft_stale_send_copy", NEXT_DRAFT_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        selected = next_draft.build_next_draft(pack, targets, require_date="2026-05-10")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            send_copy_path = tmp_path / "today-send-copy.txt"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(next_draft.render_markdown(selected), encoding="utf-8")
            send_copy_path.write_text("stale outbound text\n", encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "ready")
        self.assertEqual(summary["outreach_execution"]["send_copy_state"], "stale")
        self.assertTrue(summary["outreach_execution"]["send_copy_exists"])
        self.assertFalse(summary["outreach_execution"]["send_copy_matches_next_pending"])
        self.assertEqual(
            summary["outreach_execution"]["send_copy_mismatch_reason"],
            "send-copy text does not match the current verified draft",
        )
        self.assertTrue(
            any(
                "Refresh the copy-only send text" in action
                and "send_copy_state" in action
                for action in summary["next_actions"]
            )
        )
        self.assertFalse(
            any(
                "Use the copy-only send text" in action
                for action in summary["next_actions"]
            )
        )

    def test_metadata_matching_next_draft_with_stale_body_must_be_rerendered(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_stale_body", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_stale_body", MESSAGE_SCRIPT)
        next_draft = _load_module("dashboard_next_draft_stale_body", NEXT_DRAFT_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        selected = next_draft.build_next_draft(pack, targets, require_date="2026-05-10")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            send_copy_path = tmp_path / "today-send-copy.txt"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(
                "# Next Prophet Validation Draft - 2026-05-10\n\n"
                "- Target: target-dib-platform-001\n"
                "- Status: verified pending send/update\n\n"
                "stale tracker metadata body\n",
                encoding="utf-8",
            )
            send_copy_path.write_text(next_draft.render_send_text(selected), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "stale")
        self.assertFalse(summary["outreach_execution"]["next_draft_matches_next_pending"])
        self.assertEqual(
            summary["outreach_execution"]["next_draft_mismatch_reason"],
            "next-draft text does not match the current verified draft",
        )
        self.assertEqual(summary["outreach_execution"]["send_copy_state"], "stale")
        self.assertEqual(
            summary["outreach_execution"]["send_copy_mismatch_reason"],
            "next draft is not ready for the current target/date/status",
        )
        self.assertTrue(
            any(
                "Rerender the next verified outreach draft" in action
                and "next-draft text does not match the current verified draft" in action
                for action in summary["next_actions"]
            )
        )

    def test_stale_existing_next_draft_must_be_rerendered(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_stale_draft", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_stale_draft", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(
                "# Next Prophet Validation Draft - 2026-05-10\n\n"
                "- Target: target-dib-platform-999\n"
                "- Status: verified pending send/update\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["next_draft_exists"])
        self.assertEqual(
            summary["outreach_execution"]["next_draft_target_label"],
            "target-dib-platform-999",
        )
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "stale")
        self.assertFalse(summary["outreach_execution"]["next_draft_matches_next_pending"])
        self.assertTrue(
            any(
                "Rerender the next verified outreach draft" in action
                and "stale for the current tracker" in action
                and "with date 2026-05-10" in action
                and "status verified pending send/update" in action
                for action in summary["next_actions"]
            )
        )
        self.assertFalse(
            any(
                "Use the copy-only send text" in action
                for action in summary["next_actions"]
            )
        )

    def test_same_target_wrong_date_next_draft_must_be_rerendered(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_wrong_date", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_wrong_date", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(
                "# Next Prophet Validation Draft - 2026-05-09\n\n"
                "- Target: target-dib-platform-001\n"
                "- Status: verified pending send/update\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["next_draft_exists"])
        self.assertEqual(
            summary["outreach_execution"]["next_draft_target_label"],
            "target-dib-platform-001",
        )
        self.assertEqual(
            summary["outreach_execution"]["next_draft_generated_for"],
            "2026-05-09",
        )
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "stale")
        self.assertFalse(summary["outreach_execution"]["next_draft_matches_next_pending"])
        self.assertTrue(
            any(
                "Rerender the next verified outreach draft" in action
                and "with date 2026-05-09" in action
                for action in summary["next_actions"]
            )
        )

    def test_existing_next_draft_is_not_needed_after_pack_complete(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_complete", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_complete", MESSAGE_SCRIPT)
        status_module = _load_module("dashboard_status_complete", STATUS_SCRIPT)
        target_update = _load_module("dashboard_target_update_complete", TARGET_UPDATE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        updated_targets = copy.deepcopy(targets)
        for draft in pack["drafts"]:
            expected = status_module._parse_tracker_command(draft["tracker_update_command"])
            target_update.update_target(
                updated_targets,
                target_label=expected["target_label"],
                status=expected["status"],
                last_touch=expected["last_touch"],
                follow_up_due=expected["follow_up_due"],
                next_action=expected["next_action"],
                updated_at="2026-05-10",
                require_current_status=expected["require_current_status"],
            )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            targets_path.write_text(json.dumps(updated_targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(
                "# Next Prophet Validation Draft - 2026-05-10\n\n"
                "- Target: target-dib-platform-001\n"
                "- Status: verified pending send/update\n",
                encoding="utf-8",
            )
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertTrue(summary["outreach_execution"]["complete"])
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "not_needed")
        self.assertFalse(summary["outreach_execution"]["next_draft_matches_next_pending"])
        self.assertIsNone(summary["outreach_execution"]["next_pending_target_label"])
        self.assertTrue(
            any(
                "Today's outreach pack is applied" in action
                for action in summary["next_actions"]
            )
        )
        self.assertFalse(
            any(
                "Rerender the next verified outreach draft" in action
                for action in summary["next_actions"]
            )
        )

    def test_text_render_includes_send_boundary_summary(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_text", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_text", MESSAGE_SCRIPT)
        next_draft = _load_module("dashboard_next_draft_text", NEXT_DRAFT_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        selected = next_draft.build_next_draft(pack, targets, require_date="2026-05-10")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            next_draft_path = tmp_path / "today-next-draft.md"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            next_draft_path.write_text(next_draft.render_markdown(selected), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        rendered = dashboard.render_text(summary)

        self.assertIn("Customer validation verdict: insufficient_data", rendered)
        self.assertIn("Build gate open: false", rendered)
        self.assertIn("Next draft exists: true", rendered)
        self.assertIn("Next draft target: target-dib-platform-001", rendered)
        self.assertIn("Next draft date: 2026-05-10", rendered)
        self.assertIn("Next draft status: verified pending send/update", rendered)
        self.assertIn("Next draft state: ready", rendered)
        self.assertIn("Next draft matches target/date/status/body: true", rendered)
        self.assertIn(f"Send-copy path: {pack_path.with_name('today-send-copy.txt')}", rendered)
        self.assertIn("Send-copy command: make validation-send-copy DATE=2026-05-10", rendered)
        self.assertIn("Send-copy exists: false", rendered)
        self.assertIn("Send-copy state: missing", rendered)
        self.assertIn("Send-copy matches current draft: false", rendered)
        self.assertIn(f"Send-copy batch README: {pack_path.with_name('send-copy-2026-05-10') / 'README.md'}", rendered)
        self.assertIn("Send-copy batch README exists: false", rendered)
        self.assertIn(f"Send-copy batch checklist: {pack_path.with_name('send-copy-2026-05-10') / 'CHECKLIST.md'}", rendered)
        self.assertIn("Send-copy batch checklist exists: false", rendered)
        self.assertIn(f"Send-copy batch copy index: {pack_path.with_name('send-copy-2026-05-10') / 'COPY_ONLY_INDEX.md'}", rendered)
        self.assertIn("Send-copy batch copy index exists: false", rendered)
        self.assertIn(f"Send-copy batch subject order: {pack_path.with_name('send-copy-2026-05-10') / 'SUBJECT_ORDER.md'}", rendered)
        self.assertIn("Send-copy batch subject order exists: false", rendered)
        self.assertIn("Next target: target-dib-platform-001", rendered)
        self.assertIn(
            "Dry-run command: make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
            rendered,
        )
        self.assertIn("Confirmed-send command:", rendered)

    def test_private_message_pack_stale_target_state_surfaces_dry_run_failure(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_stale_state", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_stale_state", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)
        targets = copy.deepcopy(targets)
        targets["targets"][0]["status"] = "outreach_sent"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=targets_path,
                message_pack_path=pack_path,
                require_date="2026-05-10",
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["outreach_execution"]["counts"]["needs_attention"], 1)
        self.assertEqual(summary["outreach_execution"]["dry_run_verified_count"], 7)
        self.assertEqual(summary["outreach_execution"]["dry_run_failed_count"], 1)
        self.assertEqual(summary["outreach_execution"]["dry_run_skipped_count"], 0)
        self.assertEqual(
            summary["outreach_execution"]["needs_attention_targets"],
            ["target-dib-platform-001"],
        )
        self.assertTrue(
            any("Fix outreach execution status before sending" in action for action in summary["next_actions"])
        )

    def test_required_date_rejects_stale_message_pack(self) -> None:
        targets = json.loads(
            (ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8")
        )
        outreach_block = _load_module("dashboard_outreach_block_stale", OUTREACH_SCRIPT)
        message_pack = _load_module("dashboard_message_pack_stale", MESSAGE_SCRIPT)
        block = outreach_block.build_outreach_block(targets, run_date="2026-05-10")
        pack = message_pack.build_message_pack(block)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            targets_path = tmp_path / "validation-targets.json"
            pack_path = tmp_path / "today-message-pack.json"
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            with self.assertRaisesRegex(
                dashboard.ValidationDashboardError,
                "does not match required date 2026-05-11",
            ):
                dashboard.build_dashboard(
                    log_path=ROOT / "docs/customer-validation-log.example.json",
                    targets_path=targets_path,
                    message_pack_path=pack_path,
                    require_date="2026-05-11",
                    scripts_dir=ROOT / "scripts",
                )

    def test_required_date_rejects_bad_date(self) -> None:
        with self.assertRaisesRegex(dashboard.ValidationDashboardError, "YYYY-MM-DD"):
            dashboard.build_dashboard(
                log_path=ROOT / "docs/customer-validation-log.example.json",
                targets_path=ROOT / "docs/validation-targets.example.json",
                require_date="05/10/2026",
                scripts_dir=ROOT / "scripts",
            )

    def test_pilot_pull_detected_does_not_open_build_gate(self) -> None:
        log = json.loads((ROOT / "docs/customer-validation-log.example.json").read_text(encoding="utf-8"))
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"example-pilot-pull-{index:03d}"
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 2 else "asked_for_demo"
            interview["budget_signal"] = "budget_owner_named"
            log["interviews"].append(interview)

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            log_path.write_text(json.dumps(log), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=log_path,
                targets_path=ROOT / "docs/validation-targets.example.json",
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["customer_validation"]["verdict"], "pilot_pull_detected")
        self.assertFalse(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertTrue(any("Do not build" in action for action in summary["next_actions"]))

    def test_build_next_slice_requires_target_tracker_backed_interviews(self) -> None:
        log = json.loads((ROOT / "docs/customer-validation-log.example.json").read_text(encoding="utf-8"))
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index in range(15):
            interview = copy.deepcopy(template)
            interview["account_label"] = f"untracked-build-signal-{index:03d}"
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "customer-validation-log.json"
            log_path.write_text(json.dumps(log), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=log_path,
                targets_path=ROOT / "docs/validation-targets.example.json",
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["customer_validation"]["verdict"], "build_next_slice")
        self.assertEqual(summary["target_backed_validation"]["verdict"], "insufficient_data")
        self.assertEqual(summary["target_backed_validation"]["unmatched_qualified_count"], 15)
        self.assertFalse(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertIn("target-backed validation has not", summary["build_gate"]["reason"])
        self.assertTrue(
            any("Target-backed build gate gap" in action for action in summary["next_actions"])
        )

    def test_build_next_slice_requires_booked_or_completed_target_status(self) -> None:
        log = json.loads((ROOT / "docs/customer-validation-log.example.json").read_text(encoding="utf-8"))
        targets = json.loads((ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8"))
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        target_labels = [target["target_label"] for target in targets["targets"][:15]]
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index, target_label in enumerate(target_labels):
            interview = copy.deepcopy(template)
            target = targets["targets"][index]
            interview["account_label"] = target_label
            interview["segment"] = target["segment"]
            interview["persona"] = target["persona"]
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "customer-validation-log.json"
            targets_path = tmp_path / "validation-targets.json"
            log_path.write_text(json.dumps(log), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=log_path,
                targets_path=targets_path,
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["customer_validation"]["verdict"], "build_next_slice")
        self.assertEqual(summary["target_backed_validation"]["matched_interview_count"], 15)
        self.assertEqual(
            summary["target_backed_validation"]["status_ineligible_qualified_count"],
            15,
        )
        self.assertEqual(summary["target_backed_validation"]["verdict"], "insufficient_data")
        self.assertFalse(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertTrue(
            any("without call_booked/completed status" in action for action in summary["next_actions"])
        )

    def test_build_next_slice_requires_target_metadata_match(self) -> None:
        log = json.loads((ROOT / "docs/customer-validation-log.example.json").read_text(encoding="utf-8"))
        targets = json.loads((ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8"))
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        target_labels = [target["target_label"] for target in targets["targets"][:15]]
        for target in targets["targets"][:15]:
            target["status"] = "call_booked"
            target["follow_up_due"] = ""
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index, target_label in enumerate(target_labels):
            interview = copy.deepcopy(template)
            interview["account_label"] = target_label
            interview["segment"] = "mismatched_segment"
            interview["persona"] = "mismatched_persona"
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "customer-validation-log.json"
            targets_path = tmp_path / "validation-targets.json"
            log_path.write_text(json.dumps(log), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=log_path,
                targets_path=targets_path,
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["customer_validation"]["verdict"], "build_next_slice")
        self.assertEqual(summary["target_backed_validation"]["matched_interview_count"], 15)
        self.assertEqual(
            summary["target_backed_validation"]["metadata_mismatched_qualified_count"],
            15,
        )
        self.assertEqual(summary["target_backed_validation"]["verdict"], "insufficient_data")
        self.assertFalse(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertTrue(
            any("not target segment/persona metadata" in action for action in summary["next_actions"])
        )

    def test_build_next_slice_opens_when_interviews_are_target_backed(self) -> None:
        log = json.loads((ROOT / "docs/customer-validation-log.example.json").read_text(encoding="utf-8"))
        targets = json.loads((ROOT / "docs/validation-targets.example.json").read_text(encoding="utf-8"))
        log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
        target_labels = [target["target_label"] for target in targets["targets"][:15]]
        for index, target in enumerate(targets["targets"][:15]):
            target["status"] = "completed" if index < 8 else "call_booked"
            target["follow_up_due"] = ""
        template = copy.deepcopy(log["interviews"][0])
        log["interviews"] = []
        for index, target_label in enumerate(target_labels):
            interview = copy.deepcopy(template)
            target = targets["targets"][index]
            interview["account_label"] = target_label
            interview["segment"] = target["segment"]
            interview["persona"] = target["persona"]
            interview["pilot_signal"] = "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
            interview["budget_signal"] = "paid_pilot_discussed" if index == 0 else "budget_owner_named"
            log["interviews"].append(interview)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "customer-validation-log.json"
            targets_path = tmp_path / "validation-targets.json"
            log_path.write_text(json.dumps(log), encoding="utf-8")
            targets_path.write_text(json.dumps(targets), encoding="utf-8")
            summary = dashboard.build_dashboard(
                log_path=log_path,
                targets_path=targets_path,
                scripts_dir=ROOT / "scripts",
            )

        self.assertEqual(summary["customer_validation"]["verdict"], "build_next_slice")
        self.assertEqual(summary["target_backed_validation"]["verdict"], "build_next_slice")
        self.assertEqual(summary["target_backed_validation"]["target_backed_interview_count"], 15)
        self.assertTrue(summary["build_gate"]["allowed_to_build_next_slice"])
        self.assertIn("enough qualified pull", summary["build_gate"]["reason"])
        self.assertFalse(any("Do not build" in action for action in summary["next_actions"]))

    def test_missing_private_files_points_to_initializer(self) -> None:
        with self.assertRaisesRegex(dashboard.ValidationDashboardError, "init-validation-sprint"):
            dashboard.build_dashboard(
                log_path=ROOT / "validation/private/missing-log.json",
                targets_path=ROOT / "validation/private/missing-targets.json",
                scripts_dir=ROOT / "scripts",
            )


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
