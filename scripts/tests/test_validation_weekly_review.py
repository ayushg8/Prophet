from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEEKLY_SCRIPT = ROOT / "scripts" / "validation-weekly-review.py"
PRUNE_SCRIPT = ROOT / "scripts" / "validation-prune-private.py"
OUTREACH_SCRIPT = ROOT / "scripts" / "validation-outreach-block.py"
MESSAGE_SCRIPT = ROOT / "scripts" / "validation-message-pack.py"
BATCH_SCRIPT = ROOT / "scripts" / "validation-send-copy-batch.py"
EXAMPLE_TARGETS = ROOT / "docs" / "validation-targets.example.json"
EXAMPLE_LOG = ROOT / "docs" / "customer-validation-log.example.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


weekly_review = _load_module("validation_weekly_review", WEEKLY_SCRIPT)
validation_prune = _load_module("validation_prune_private_for_weekly_review", PRUNE_SCRIPT)
outreach_block = _load_module("validation_outreach_block_for_weekly_review", OUTREACH_SCRIPT)
message_pack = _load_module("validation_message_pack_for_weekly_review", MESSAGE_SCRIPT)
send_copy_batch = _load_module("validation_send_copy_batch_for_weekly_review", BATCH_SCRIPT)


class ValidationWeeklyReviewTests(unittest.TestCase):
    def test_builds_read_only_weekly_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            self.assertEqual(
                review["schema_version"],
                weekly_review.WEEKLY_REVIEW_SCHEMA_VERSION,
            )
            self.assertEqual(review["review_date"], "2026-05-10")
            self.assertEqual(review["generated_for"], "2026-05-10")
            self.assertEqual(review["validation_gate"]["verdict"], "insufficient_data")
            self.assertTrue(review["validation_gate"]["example_seed_log"])
            self.assertFalse(review["validation_gate"]["allowed_to_build_next_slice"])
            self.assertEqual(review["target_pipeline"]["active_target_count"], 30)
            self.assertTrue(review["message_pack"]["exists"])
            self.assertEqual(review["message_pack"]["draft_count"], 8)
            self.assertEqual(review["message_pack"]["age_days"], 0)
            self.assertTrue(review["message_pack"]["date_matches_review"])
            self.assertFalse(review["message_pack"]["stale_for_review"])
            self.assertFalse(review["message_pack"]["future_for_review"])
            self.assertTrue(review["outreach_execution"]["available"])
            self.assertEqual(review["outreach_execution"]["state"], "not_ready")
            self.assertEqual(review["outreach_execution"]["send_copy_batch_state"], "missing")
            self.assertFalse(review["outreach_execution"]["send_copy_batch_copy_index_exists"])
            self.assertFalse(review["outreach_execution"]["send_copy_batch_subject_order_exists"])
            self.assertEqual(review["private_artifacts"]["send_copy_warning_count"], 0)
            self.assertEqual(review["private_artifacts"]["send_copy_warnings"], [])
            self.assertEqual(review["pruning_candidates"]["overdue_follow_ups"], [])
            self.assertTrue(
                any("Read-only review" in note for note in review["operator_notes"])
            )

    def test_reports_send_copy_batch_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            targets = json.loads(targets_path.read_text(encoding="utf-8"))
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
            batch_dir = private_dir / "send-copy-2026-05-10"
            manifest_path = batch_dir / "manifest.json"
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

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            outreach = review["outreach_execution"]
            self.assertTrue(outreach["available"])
            self.assertEqual(outreach["state"], "ready")
            self.assertEqual(outreach["counts"]["pending_send_or_update"], 8)
            self.assertEqual(outreach["dry_run_verified_count"], 8)
            self.assertEqual(outreach["send_copy_batch_state"], "ready")
            self.assertTrue(outreach["send_copy_batch_readme_exists"])
            self.assertTrue(outreach["send_copy_batch_checklist_exists"])
            self.assertTrue(outreach["send_copy_batch_copy_index_exists"])
            self.assertTrue(outreach["send_copy_batch_subject_order_exists"])
            self.assertTrue(outreach["send_copy_batch_matches_current_pack"])
            self.assertEqual(review["private_artifacts"]["send_copy_warning_count"], 0)

    def test_flags_unsafe_or_outdated_private_send_copy_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            old_dir = private_dir / "send-copy-2026-05-09"
            old_dir.mkdir()
            old_copy = old_dir / "01.txt"
            old_copy.write_text(
                "Subject: stale\n\nHi <first name>,\n\nOld placeholder body.\n",
                encoding="utf-8",
            )

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            self.assertEqual(review["private_artifacts"]["send_copy_warning_count"], 1)
            warning = review["private_artifacts"]["send_copy_warnings"][0]
            self.assertEqual(warning["path"], str(old_copy))
            self.assertIn("date_mismatch", warning["reasons"])
            self.assertIn("placeholder_text", warning["reasons"])

            rendered = weekly_review.render_markdown(review)
            self.assertIn("Send-copy warning count: 1", rendered)
            self.assertIn("Private send-copy warnings:", rendered)
            self.assertIn("placeholder_text", rendered)

            plan = validation_prune.build_prune_plan(
                review,
                private_dir=private_dir,
                review_date="2026-05-10",
            )
            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["candidate_count"], 1)
            self.assertEqual(Path(plan["candidates"][0]["path"]).resolve(), old_dir.resolve())
            self.assertEqual(plan["candidates"][0]["kind"], "outdated_send_copy_batch")
            self.assertIn("--confirm-prune", validation_prune.render_markdown(plan))
            original_is_ignored = validation_prune._is_ignored
            try:
                validation_prune._is_ignored = lambda _path: True
                applied = validation_prune.apply_prune_plan(plan, private_dir=private_dir)
            finally:
                validation_prune._is_ignored = original_is_ignored
            self.assertFalse(old_dir.exists())
            self.assertFalse(applied["dry_run"])
            self.assertEqual(applied["removed_count"], 1)

    def test_build_gate_requires_target_backed_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            log = json.loads(log_path.read_text(encoding="utf-8"))
            log["notes"] = "Synthetic threshold test with anonymized non-example interviews."
            template = copy.deepcopy(log["interviews"][0])
            log["interviews"] = []
            for index in range(15):
                interview = copy.deepcopy(template)
                interview["account_label"] = f"untracked-build-signal-{index:03d}"
                interview["pilot_signal"] = (
                    "asked_for_scoped_pilot" if index < 3 else "asked_for_demo"
                )
                interview["budget_signal"] = (
                    "paid_pilot_discussed" if index == 0 else "budget_owner_named"
                )
                log["interviews"].append(interview)
            log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            gate = review["validation_gate"]
            self.assertEqual(gate["verdict"], "build_next_slice")
            self.assertEqual(gate["target_backed_verdict"], "insufficient_data")
            self.assertEqual(
                gate["target_backed_validation"]["unmatched_qualified_count"],
                15,
            )
            self.assertFalse(gate["allowed_to_build_next_slice"])
            self.assertIn("target-backed validation has not", gate["reason"])

    def test_flags_stale_pack_artifacts_and_pruning_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(
                private_dir,
                message_date="2026-05-09",
            )
            targets = json.loads(targets_path.read_text(encoding="utf-8"))
            targets_path.write_text(
                json.dumps(_make_stale_targets(targets), indent=2) + "\n",
                encoding="utf-8",
            )
            old_file = private_dir / "old-message-pack.md"
            old_file.write_text("stale private artifact\n", encoding="utf-8")
            old_timestamp = datetime(2026, 4, 30).timestamp()
            os.utime(old_file, (old_timestamp, old_timestamp))

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
                stale_days=7,
            )

            self.assertTrue(review["message_pack"]["stale_for_review"])
            self.assertEqual(review["message_pack"]["age_days"], 1)
            self.assertFalse(review["message_pack"]["date_matches_review"])
            self.assertFalse(review["message_pack"]["future_for_review"])
            self.assertFalse(review["outreach_execution"]["available"])
            self.assertEqual(review["outreach_execution"]["state"], "error")
            self.assertIn(
                "does not match required date",
                review["outreach_execution"]["reason"],
            )
            self.assertEqual(review["private_artifacts"]["stale_file_count"], 1)
            self.assertEqual(
                review["private_artifacts"]["stale_files"][0]["path"],
                str(old_file),
            )
            self.assertEqual(
                review["pruning_candidates"]["overdue_follow_ups"][0]["target_label"],
                "target-dib-platform-001",
            )
            self.assertEqual(
                review["pruning_candidates"]["overdue_follow_ups"][1]["target_label"],
                "target-dib-platform-004",
            )
            self.assertEqual(
                review["pruning_candidates"]["booked_calls"][0]["target_label"],
                "target-dib-platform-002",
            )
            self.assertEqual(
                review["pruning_candidates"]["outreach_sent_without_follow_up_due"][0][
                    "target_label"
                ],
                "target-dib-platform-003",
            )

    def test_private_file_summary_ignores_atomic_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            tmp_path = private_dir / "today-team-update.md.tmp.ABCDEF"
            tmp_path.write_text("partial aggregate update\n", encoding="utf-8")

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            self.assertEqual(review["private_artifacts"]["file_count"], 3)
            self.assertEqual(review["private_artifacts"]["stale_files"], [])

    def test_flags_future_pack_date_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(
                private_dir,
                message_date="2026-05-11",
            )

            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            self.assertEqual(review["message_pack"]["age_days"], -1)
            self.assertFalse(review["message_pack"]["date_matches_review"])
            self.assertFalse(review["message_pack"]["stale_for_review"])
            self.assertTrue(review["message_pack"]["future_for_review"])
            self.assertFalse(review["outreach_execution"]["available"])
            self.assertEqual(review["outreach_execution"]["state"], "error")
            self.assertIn(
                "does not match required date",
                review["outreach_execution"]["reason"],
            )

    def test_markdown_names_no_write_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            review = weekly_review.build_weekly_review(
                private_dir=private_dir,
                targets_path=targets_path,
                log_path=log_path,
                message_pack_path=pack_path,
                review_date="2026-05-10",
            )

            rendered = weekly_review.render_markdown(review)

            self.assertIn("Prophet Weekly Validation Review - 2026-05-10", rendered)
            self.assertIn("This is a read-only private operator report", rendered)
            self.assertIn("Build gate open: false", rendered)
            self.assertIn("Date matches review: true", rendered)
            self.assertIn("## Outreach Execution", rendered)
            self.assertIn("Batch checklist exists: false", rendered)
            self.assertIn("Batch copy index exists: false", rendered)
            self.assertIn("Batch subject order exists: false", rendered)
            self.assertIn("Do not run CONFIRM_SENT=1", rendered)

    def test_rejects_sensitive_target_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets_path, log_path, pack_path = _write_private_inputs(private_dir)
            targets = json.loads(targets_path.read_text(encoding="utf-8"))
            targets = _make_sensitive_targets(targets)
            targets_path.write_text(json.dumps(targets, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(weekly_review.WeeklyReviewError, "email-like"):
                weekly_review.build_weekly_review(
                    private_dir=private_dir,
                    targets_path=targets_path,
                    log_path=log_path,
                    message_pack_path=pack_path,
                    review_date="2026-05-10",
                )

    def test_cli_writes_markdown_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            _write_private_inputs(private_dir)
            out_path = private_dir / "today-weekly-review.md"

            with contextlib.redirect_stdout(io.StringIO()):
                result = weekly_review.main(
                    [
                        "--private-dir",
                        str(private_dir),
                        "--targets",
                        str(private_dir / "validation-targets.json"),
                        "--log",
                        str(private_dir / "customer-validation-log.json"),
                        "--message-pack",
                        str(private_dir / "today-message-pack.json"),
                        "--review-date",
                        "2026-05-10",
                        "--format",
                        "markdown",
                        "--out",
                        str(out_path),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue(out_path.exists())
            self.assertIn(
                "Prophet Weekly Validation Review - 2026-05-10",
                out_path.read_text(encoding="utf-8"),
            )


def _write_private_inputs(
    private_dir: Path,
    *,
    message_date: str = "2026-05-10",
    targets_transform=None,
) -> tuple[Path, Path, Path]:
    targets = outreach_block.json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
    if targets_transform is not None:
        targets = targets_transform(targets)
    block = outreach_block.build_outreach_block(targets, run_date=message_date)
    pack = message_pack.build_message_pack(block)
    targets_path = private_dir / "validation-targets.json"
    log_path = private_dir / "customer-validation-log.json"
    pack_path = private_dir / "today-message-pack.json"
    targets_path.write_text(json.dumps(targets, indent=2) + "\n", encoding="utf-8")
    log_path.write_text(EXAMPLE_LOG.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    return targets_path, log_path, pack_path


def _make_stale_targets(targets: dict) -> dict:
    targets = copy.deepcopy(targets)
    targets["targets"][0]["status"] = "follow_up_due"
    targets["targets"][0]["last_touch"] = "2026-05-06"
    targets["targets"][0]["follow_up_due"] = "2026-05-09"
    targets["targets"][1]["status"] = "call_booked"
    targets["targets"][1]["last_touch"] = "2026-05-09"
    targets["targets"][1]["follow_up_due"] = ""
    targets["targets"][2]["status"] = "outreach_sent"
    targets["targets"][2]["last_touch"] = "2026-05-09"
    targets["targets"][2]["follow_up_due"] = ""
    targets["targets"][3]["status"] = "outreach_sent"
    targets["targets"][3]["last_touch"] = "2026-05-07"
    targets["targets"][3]["follow_up_due"] = "2026-05-09"
    return targets


def _make_sensitive_targets(targets: dict) -> dict:
    targets = copy.deepcopy(targets)
    targets["targets"][0]["next_action"] = "Email buyer@example.com"
    return targets


if __name__ == "__main__":
    unittest.main()
