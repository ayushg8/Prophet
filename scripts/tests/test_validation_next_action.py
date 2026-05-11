from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation-next-action.py"
EXAMPLE_LOG = ROOT / "docs" / "customer-validation-log.example.json"
EXAMPLE_TARGETS = ROOT / "docs" / "validation-targets.example.json"
SPEC = importlib.util.spec_from_file_location("validation_next_action", SCRIPT)
assert SPEC and SPEC.loader
validation_next_action = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validation_next_action
SPEC.loader.exec_module(validation_next_action)


class ValidationNextActionTests(unittest.TestCase):
    def test_render_names_current_gate_and_send_boundary(self) -> None:
        dashboard = _example_dashboard()

        rendered = validation_next_action.render_next_action(
            dashboard,
            run_date="2026-05-11",
            git_head="abc1234",
            git_worktree_state="clean",
            github_ci_summary="`success` (`completed`, `ci`): https://example.invalid/run",
        )

        self.assertIn(
            "make validation-pre-send-check TARGET=target-dib-platform-001 DATE=2026-05-11",
            rendered,
        )
        self.assertIn("If sending the full block, run the full-batch dry-run gate too", rendered)
        self.assertIn("make validation-pre-send-check-all DATE=2026-05-11", rendered)
        self.assertIn("refuses all `CONFIRM_*` write", rendered)
        self.assertIn("make validation-dashboard DATE=2026-05-11", rendered)
        self.assertIn("make validation-send-copy-check DATE=2026-05-11", rendered)
        self.assertIn("copy_files_outbound_safe: true", rendered)
        self.assertIn("readme_matches_manifest: true", rendered)
        self.assertIn("checklist_matches_manifest: true", rendered)
        self.assertIn("copy_index_matches_manifest: true", rendered)
        self.assertIn("subject_order_matches_manifest: true", rendered)
        self.assertIn("do_not_send_matches_manifest: true", rendered)
        self.assertIn("operator_metadata_outbound_safe: false", rendered)
        self.assertIn("DO_NOT_SEND guard", rendered)
        self.assertIn("private operator", rendered)
        self.assertIn("make validation-prune-private DATE=2026-05-11", rendered)
        self.assertIn(
            "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11",
            rendered,
        )
        self.assertIn("validation/private/today-send-copy.txt", rendered)
        self.assertIn("validation/private/send-copy-2026-05-11", rendered)
        self.assertIn("does not store recipient names", rendered)
        self.assertIn("external outreach channel", rendered)
        self.assertIn("real contact selected outside the repo", rendered)
        self.assertIn("Only after the outbound message is confirmed sent", rendered)
        self.assertIn("CONFIRM_SENT=1", rendered)
        self.assertIn("Validation verdict: insufficient_data", rendered)
        self.assertIn("Build gate: closed", rendered)
        self.assertIn("Local git head: `abc1234`", rendered)
        self.assertIn("Local git worktree: `clean`", rendered)
        self.assertIn("GitHub CI for local head: `success`", rendered)
        self.assertIn("https://example.invalid/run", rendered)
        self.assertIn("Do not use PR readiness as buyer-demand evidence", rendered)

    def test_render_send_copy_fallback_stays_copy_only(self) -> None:
        dashboard = _example_dashboard()
        dashboard["outreach_execution"].pop("send_copy_path")

        rendered = validation_next_action.render_next_action(
            dashboard,
            run_date="2026-05-11",
            git_head="abc1234",
            git_worktree_state="dirty",
            github_ci_summary="`unavailable`; run `gh run list` before release decisions.",
        )

        self.assertIn("validation/private/today-send-copy.txt", rendered)
        self.assertIn("If dirty, rerun the dashboard and send-copy checks", rendered)
        self.assertIn("GitHub CI for local head: `unavailable`", rendered)
        self.assertNotIn("validation/private/today-message-pack.json", rendered)

    def test_cli_writes_private_handoff_without_mutating_trackers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp)
            log_path = private_dir / "customer-validation-log.json"
            targets_path = private_dir / "validation-targets.json"
            block_path = private_dir / "today-outreach-block.json"
            pack_path = private_dir / "today-message-pack.json"
            out_path = private_dir / "NEXT_ACTION.md"
            log_path.write_text(EXAMPLE_LOG.read_text(encoding="utf-8"), encoding="utf-8")
            targets_path.write_text(EXAMPLE_TARGETS.read_text(encoding="utf-8"), encoding="utf-8")
            before_targets = targets_path.read_text(encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-outreach-block.py",
                    "--targets",
                    str(targets_path),
                    "--date",
                    "2026-05-11",
                    "--format",
                    "json",
                    "--out",
                    str(block_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-message-pack.py",
                    "--block",
                    str(block_path),
                    "--format",
                    "json",
                    "--out",
                    str(pack_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-next-action.py",
                    "--log",
                    str(log_path),
                    "--targets",
                    str(targets_path),
                    "--message-pack",
                    str(pack_path),
                    "--date",
                    "2026-05-11",
                    "--out",
                    str(out_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(out_path.exists())
            self.assertEqual(targets_path.read_text(encoding="utf-8"), before_targets)
            rendered = out_path.read_text(encoding="utf-8")
            self.assertIn("Next Validation Action", rendered)
            self.assertIn("target-dib-platform-001", rendered)
            self.assertIn("Build gate: closed", rendered)

    def test_cli_rejects_stale_message_pack_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp)
            log_path = private_dir / "customer-validation-log.json"
            targets_path = private_dir / "validation-targets.json"
            block_path = private_dir / "today-outreach-block.json"
            pack_path = private_dir / "today-message-pack.json"
            log_path.write_text(EXAMPLE_LOG.read_text(encoding="utf-8"), encoding="utf-8")
            targets_path.write_text(EXAMPLE_TARGETS.read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-outreach-block.py",
                    "--targets",
                    str(targets_path),
                    "--date",
                    "2026-05-10",
                    "--format",
                    "json",
                    "--out",
                    str(block_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-message-pack.py",
                    "--block",
                    str(block_path),
                    "--format",
                    "json",
                    "--out",
                    str(pack_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/validation-next-action.py",
                    "--log",
                    str(log_path),
                    "--targets",
                    str(targets_path),
                    "--message-pack",
                    str(pack_path),
                    "--date",
                    "2026-05-11",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("message pack generated_for 2026-05-10 does not match", completed.stderr)


def _example_dashboard() -> dict[str, object]:
    return {
        "customer_validation": {
            "verdict": "insufficient_data",
            "effective_validation_counts": {
                "qualified_count": 0,
                "high_pain_count": 0,
                "repeated_workflow_pain_count": 0,
                "pilot_pull_count": 0,
                "paid_or_sponsored_count": 0,
            },
            "gaps_to_verdicts": {
                "build_next_slice": {
                    "qualified_count": 15,
                    "high_pain_count": 8,
                    "repeated_workflow_pain_count": 5,
                    "pilot_pull_count": 3,
                    "paid_or_sponsored_count": 1,
                }
            },
        },
        "build_gate": {
            "allowed_to_build_next_slice": False,
            "reason": "real buyer validation has not proven enough pull",
        },
        "outreach_execution": {
            "counts": {
                "pending_send_or_update": 8,
                "needs_attention": 0,
            },
            "dry_run_verified_count": 8,
            "send_copy_state": "ready",
            "send_copy_matches_next_pending": True,
            "send_copy_path": "validation/private/today-send-copy.txt",
            "send_copy_batch_state": "ready",
            "send_copy_batch_matches_current_pack": True,
            "send_copy_batch_dir": "validation/private/send-copy-2026-05-11",
            "send_copy_batch_copy_file_count": 8,
            "next_pending_target_label": "target-dib-platform-001",
            "next_pending_group": "targeted_ask",
            "next_pending_dry_run_apply_command": (
                "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11"
            ),
            "next_pending_confirmed_apply_command": (
                "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11 CONFIRM_SENT=1"
            ),
            "status_command": "make validation-status DATE=2026-05-11",
        },
    }


if __name__ == "__main__":
    unittest.main()
