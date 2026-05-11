from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_TARGETS = ROOT / "docs" / "validation-targets.example.json"
EXAMPLE_LOG = ROOT / "docs" / "customer-validation-log.example.json"


class MakeValidationTargetsTests(unittest.TestCase):
    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_make_help_describes_validation_status_outputs(self) -> None:
        completed = subprocess.run(
            ["make", "help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("make pilot-ready-check", completed.stdout)
        self.assertIn("Run env, smoke, validation dashboard, readiness, and release-safety", completed.stdout)
        self.assertIn("make pilot-ready-check-full", completed.stdout)
        self.assertIn("Run pilot-ready-check plus console acceptance and audit", completed.stdout)
        self.assertIn("make worktree-smoke", completed.stdout)
        self.assertIn("overlay dirty non-ignored files", completed.stdout)
        self.assertIn("make console-control", completed.stdout)
        self.assertIn("Run the local console control server", completed.stdout)
        self.assertIn("make console-ui", completed.stdout)
        self.assertIn("Run the evaluator console UI", completed.stdout)
        self.assertIn("make console-demo", completed.stdout)
        self.assertIn("Start control server and evaluator UI in one local terminal", completed.stdout)
        self.assertIn("make console-live-check", completed.stdout)
        self.assertIn("Check running local console readiness, evidence, integration", completed.stdout)
        self.assertIn("make console-screenshot-check", completed.stdout)
        self.assertIn("Verify generated console screenshot manifest", completed.stdout)
        self.assertIn("make validation-status", completed.stdout)
        self.assertIn("REFRESH_README=1", completed.stdout)
        self.assertIn(
            "optional DATE=YYYY-MM-DD, CONFIRM_SENT=1 after actual send",
            completed.stdout,
        )
        self.assertIn("optional DATE=YYYY-MM-DD, CONFIRM_TARGET=1", completed.stdout)
        self.assertIn(
            "optional INTERVIEW=path, DATE=YYYY-MM-DD, REPLACE_EXAMPLE_SEED=1",
            completed.stdout,
        )
        self.assertIn("CONFIRM_LOG=1", completed.stdout)
        self.assertIn("Print Markdown status and write next-target JSON", completed.stdout)
        self.assertIn("make validation-team-update", completed.stdout)
        self.assertIn("make validation-team-update-save", completed.stdout)
        self.assertIn("sanitized aggregate-only validation update", completed.stdout)
        self.assertIn("make validation-next-action-save", completed.stdout)
        self.assertIn("regenerated private NEXT_ACTION.md handoff", completed.stdout)
        self.assertIn("make validation-weekly-review", completed.stdout)
        self.assertIn("read-only private weekly review report", completed.stdout)
        self.assertIn("make validation-prune-private", completed.stdout)
        self.assertIn("Dry-run pruning of generated ignored private artifacts", completed.stdout)
        self.assertIn("CONFIRM_PRUNE=1", completed.stdout)
        self.assertIn(
            "use today-send-copy.txt for outbound text only after today-next-draft.md matches the next pending target/date/status/body",
            completed.stdout,
        )
        self.assertIn("make validation-send-copy", completed.stdout)
        self.assertIn("copy-only next draft text without tracker metadata", completed.stdout)
        self.assertIn("make validation-send-copy-check", completed.stdout)
        self.assertIn("Verify existing batch copy files are outbound-only", completed.stdout)
        self.assertIn("make validation-send-copy-batch", completed.stdout)
        self.assertIn("copy-only text files for all verified pending drafts", completed.stdout)
        self.assertIn("make validation-reply-triage", completed.stdout)
        self.assertIn("No-write reply triage", completed.stdout)
        self.assertIn("make validation-resume", completed.stdout)
        self.assertIn("make goal-resume", completed.stdout)
        self.assertIn("matching sanitized interview log", completed.stdout)
        self.assertIn("make python-tests", completed.stdout)
        self.assertIn(
            "Run all Python unit suites for pilot/release verification",
            completed.stdout,
        )
        self.assertIn("make release-hygiene", completed.stdout)
        self.assertIn("read-only whitespace, safety, current-secret", completed.stdout)
        self.assertIn("make secrets-archaeology", completed.stdout)
        self.assertIn("current + git-history secret scan", completed.stdout)

    def test_python_tests_target_runs_all_unit_suites(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn(".PHONY: python-tests", makefile)
        self.assertIn("python3 -m unittest discover -s scripts/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s cyber-side/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s world-side/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s assets/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s sandbox_runner/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s policy/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s evidence/tests -v", makefile)
        self.assertIn("python3 -m unittest discover -s integrations/tests -v", makefile)

    def test_console_demo_help_documents_safe_local_scope(self) -> None:
        completed = subprocess.run(
            ["./scripts/run-console-demo.sh", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Start the safe local Prophet evaluator console", completed.stdout)
        self.assertIn("http://127.0.0.1:8787", completed.stdout)
        self.assertIn("http://127.0.0.1:5173", completed.stdout)
        self.assertIn("must be 127.0.0.1 or localhost", completed.stdout)
        self.assertIn("Press Ctrl-C to stop both processes", completed.stdout)
        self.assertIn("npm ci", completed.stdout)
        self.assertIn("does not enable live collection", completed.stdout)
        self.assertIn("offensive workflows", completed.stdout)

    def test_console_demo_script_has_fresh_checkout_dependency_hint(self) -> None:
        script = (ROOT / "scripts" / "run-console-demo.sh").read_text(encoding="utf-8")

        self.assertIn("node_modules/.bin/vite", script)
        self.assertIn("console dependencies are not installed", script)
        self.assertIn("cd prophet-console && npm ci", script)

    def test_console_live_check_help_documents_local_runtime_scope(self) -> None:
        completed = subprocess.run(
            ["./scripts/check-console-live-demo.sh", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Check an already-running local Prophet evaluator console", completed.stdout)
        self.assertIn("make console-demo", completed.stdout)
        self.assertIn("demo-bundle", completed.stdout)
        self.assertIn("demo-export", completed.stdout)
        self.assertIn("ignored runtime outputs", completed.stdout)
        self.assertIn("does not enable live collection", completed.stdout)
        self.assertIn("offensive workflows", completed.stdout)

    def test_console_live_check_posts_safe_local_demo_endpoints(self) -> None:
        script = (ROOT / "scripts" / "check-console-live-demo.sh").read_text(encoding="utf-8")

        self.assertIn("/api/readiness", script)
        self.assertIn("/api/evidence/demo-bundle", script)
        self.assertIn("/api/integrations/demo-export", script)
        self.assertIn("no_live_target_data_included", script)
        self.assertIn("review_template_only", script)
        self.assertIn("evidence.audit validate", script)
        self.assertIn("127.0.0.1|localhost", script)

    def test_console_screenshot_check_help_documents_manifest_scope(self) -> None:
        completed = subprocess.run(
            ["python3", "scripts/check-console-screenshots.py", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Verify console screenshot manifest", completed.stdout)
        self.assertIn("hashes", completed.stdout)
        self.assertIn("dimensions", completed.stdout)
        self.assertIn("sharing boundary", completed.stdout)

    def test_console_screenshot_check_is_make_target(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn(".PHONY: console-screenshot-check", makefile)
        self.assertIn("python3 scripts/check-console-screenshots.py --format text", makefile)

    def test_worktree_smoke_script_overlays_non_ignored_dirty_files(self) -> None:
        script = (ROOT / "scripts" / "run-worktree-smoke.sh").read_text(encoding="utf-8")

        self.assertIn("git clone --local", script)
        self.assertIn("git diff --name-only -z", script)
        self.assertIn("git ls-files --others --exclude-standard -z", script)
        self.assertIn("Ignored files such as validation/private/ are not copied", script)
        self.assertIn("./scripts/check-local-env.sh", script)
        self.assertIn("./scripts/run-pilot-demo-smoke.sh", script)

    def test_worktree_smoke_help_documents_no_commit_or_private_copy(self) -> None:
        completed = subprocess.run(
            ["./scripts/run-worktree-smoke.sh", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("non-ignored dirty worktree files", completed.stdout)
        self.assertIn("does not stage, commit, push, tag", completed.stdout)
        self.assertIn("copy ignored private validation files", completed.stdout)

    def test_release_hygiene_help_documents_read_only_checks(self) -> None:
        completed = subprocess.run(
            ["./scripts/check-release-hygiene.sh", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("read-only release hygiene checks", completed.stdout)
        self.assertIn("untracked non-ignored file whitespace", completed.stdout)
        self.assertIn("tracked path policy-hash coverage", completed.stdout)
        self.assertIn("current-worktree secrets scan", completed.stdout)
        self.assertIn("default output URL/provenance safety", completed.stdout)
        self.assertIn("does not stage, commit, push, tag", completed.stdout)

    def test_release_hygiene_script_runs_expected_safety_checks(self) -> None:
        script = (ROOT / "scripts" / "check-release-hygiene.sh").read_text(encoding="utf-8")

        self.assertIn("git diff --check", script)
        self.assertIn("git diff --no-index --check /dev/null", script)
        self.assertIn("check-release-safety.py --diff", script)
        self.assertIn("check-release-safety.py --tracked --paths-only", script)
        self.assertIn("check-release-safety.py --staged", script)
        self.assertIn("check-secrets-archaeology.sh --current-only", script)
        self.assertIn("policy.lint --policy policy/prophet-pilot-policy.json", script)
        self.assertIn("check-default-output-safety.py", script)

    def test_secrets_archaeology_help_documents_history_scan(self) -> None:
        completed = subprocess.run(
            ["./scripts/check-secrets-archaeology.sh", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("read-only secrets archaeology", completed.stdout)
        self.assertIn("tracked and untracked non-ignored files", completed.stdout)
        self.assertIn("git history", completed.stdout)
        self.assertIn("does not print matched secret values", completed.stdout)

    def test_console_demo_rejects_non_localhost_ui_host_before_starting(self) -> None:
        env = os.environ.copy()
        env["PROPHET_CONSOLE_HOST"] = "0.0.0.0"

        completed = subprocess.run(
            ["./scripts/run-console-demo.sh"],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        output = completed.stdout + completed.stderr
        self.assertIn("console host must be localhost-only", output)
        self.assertIn("PROPHET_CONSOLE_HOST", output)
        self.assertNotIn("console dependencies are not installed", output)
        self.assertNotIn("Starting Prophet local evaluator console", output)

    def test_console_demo_script_checks_port_conflicts_before_starting(self) -> None:
        script = (ROOT / "scripts" / "run-console-demo.sh").read_text(encoding="utf-8")

        self.assertIn("require_port_available", script)
        self.assertIn("require_localhost_host", script)
        self.assertIn("console host must be localhost-only", script)
        self.assertIn("port $port is already in use", script)
        self.assertIn("make console-live-check", script)
        self.assertIn("PROPHET_${label}_PORT", script)
        self.assertIn('require_port_available "127.0.0.1" "$CONTROL_PORT" "CONTROL"', script)
        self.assertIn('require_port_available "$UI_HOST" "$UI_PORT" "CONSOLE"', script)

    def test_console_demo_fails_cleanly_when_control_port_is_occupied(self) -> None:
        if not (ROOT / "prophet-console" / "node_modules" / ".bin" / "vite").exists():
            self.skipTest("console dependencies are not installed")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            occupied_port = occupied.getsockname()[1]
            env = os.environ.copy()
            env["PROPHET_CONTROL_PORT"] = str(occupied_port)
            env["PROPHET_CONSOLE_PORT"] = "5273"

            completed = subprocess.run(
                ["./scripts/run-console-demo.sh"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        output = completed.stdout + completed.stderr
        self.assertIn(f"CONTROL port {occupied_port} is already in use", output)
        self.assertIn("make console-live-check", output)
        self.assertIn("PROPHET_CONTROL_PORT", output)
        self.assertNotIn("Starting Prophet local evaluator console", output)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_init_refresh_readme_uses_overridden_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"

            initial = subprocess.run(
                [
                    "make",
                    "validation-init",
                    "DATE=2026-05-20",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(initial.returncode, 0, initial.stderr)
            self.assertTrue((private_dir / "customer-validation-log.json").exists())
            self.assertTrue((private_dir / "validation-targets.json").exists())
            self.assertTrue((private_dir / "customer-validation-interview.template.json").exists())
            self.assertTrue((private_dir / "README.md").exists())
            (private_dir / "customer-validation-log.json").write_text(
                '{"changed": true}\n',
                encoding="utf-8",
            )
            (private_dir / "README.md").write_text("old private readme\n", encoding="utf-8")

            refreshed = subprocess.run(
                [
                    "make",
                    "validation-init",
                    "DATE=2026-05-21",
                    "REFRESH_README=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            summary = json.loads(refreshed.stdout)
            self.assertEqual(
                (private_dir / "customer-validation-log.json").read_text(encoding="utf-8"),
                '{"changed": true}\n',
            )
            readme = (private_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("make goal-resume DATE=2026-05-21", readme)
            self.assertIn(
                "Send the copy-only text outside the repo only after that dry-run is clean",
                readme,
            )
            self.assertNotIn("old private readme", readme)
            self.assertEqual(summary["written"], [str(private_dir / "README.md")])
            self.assertEqual(len(summary["skipped_existing"]), 3)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_init_rejects_non_one_refresh_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"

            completed = subprocess.run(
                [
                    "make",
                    "validation-init",
                    "DATE=2026-05-20",
                    "REFRESH_README=0",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("REFRESH_README must be 1", completed.stderr)
            self.assertFalse(private_dir.exists())

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_pack_uses_overridden_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Wrote validation pack and status files", completed.stdout)
            self.assertNotIn('"drafts"', completed.stdout)
            expected_files = [
                "today-outreach-block.json",
                "today-outreach-block.md",
                "today-message-pack.json",
                "today-message-pack.md",
                "today-outreach-status.json",
                "today-outreach-status.md",
            ]
            for filename in expected_files:
                self.assertTrue((private_dir / filename).exists(), filename)

            pack = json.loads((private_dir / "today-message-pack.json").read_text())
            status = json.loads((private_dir / "today-outreach-status.json").read_text())
            status_md = (private_dir / "today-outreach-status.md").read_text()

            self.assertEqual(pack["generated_for"], "2026-05-10")
            self.assertEqual(pack["draft_count"], 8)
            self.assertEqual(status["generated_for"], "2026-05-10")
        self.assertEqual(status["draft_count"], 8)
        self.assertEqual(status["counts"]["pending_send_or_update"], 8)
        self.assertEqual(status["counts"]["needs_attention"], 0)
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
        self.assertIn("Prophet Outreach Execution Status - 2026-05-10", status_md)
        self.assertIn("Next pending target: target-dib-platform-001", status_md)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_status_uses_overridden_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            (private_dir / "today-outreach-status.json").unlink()
            (private_dir / "today-outreach-status.md").unlink()

            completed = subprocess.run(
                [
                    "make",
                    "validation-status",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Prophet Outreach Execution Status - 2026-05-10", completed.stdout)
            self.assertTrue((private_dir / "today-outreach-status.json").exists())
            self.assertTrue((private_dir / "today-outreach-status.md").exists())
            status = json.loads((private_dir / "today-outreach-status.json").read_text())
            self.assertEqual(status["counts"]["pending_send_or_update"], 8)
            self.assertEqual(status["next_pending_target_label"], "target-dib-platform-001")
            self.assertEqual(
                status["next_pending_dry_run_apply_command"],
                "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-10",
            )

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_status_rejects_stale_pack_without_date_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=1900-01-01",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                ["make", "validation-status", f"VALIDATION_DIR={private_dir}"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match required date", completed.stderr)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_reply_triage_uses_overridden_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-reply-triage",
                    "TARGET=target-dib-platform-001",
                    "REPLY=disqualify",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Prophet Reply Triage - 2026-05-10", completed.stdout)
            self.assertIn("Classification: disqualify", completed.stdout)
            self.assertIn(
                "make validation-disqualify-target TARGET=target-dib-platform-001 DATE=2026-05-10",
                completed.stdout,
            )
            self.assertIn("CONFIRM_TARGET=1", completed.stdout)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_reply_triage_requires_reply_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-reply-triage",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Usage: make validation-reply-triage", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_weekly_review_uses_overridden_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-weekly-review",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Prophet Weekly Validation Review - 2026-05-10", completed.stdout)
            self.assertTrue((private_dir / "today-weekly-review.json").exists())
            self.assertTrue((private_dir / "today-weekly-review.md").exists())
            report = json.loads((private_dir / "today-weekly-review.json").read_text())
            self.assertEqual(report["review_date"], "2026-05-10")
            self.assertEqual(report["validation_gate"]["verdict"], "insufficient_data")
            self.assertFalse(report["validation_gate"]["allowed_to_build_next_slice"])
            self.assertTrue(report["message_pack"]["exists"])

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_next_draft_uses_overridden_private_directory_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-send-copy",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)

            completed = subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Next Prophet Validation Draft - 2026-05-10", completed.stdout)
            self.assertIn("target-dib-platform-001", completed.stdout)
            next_draft_path = private_dir / "today-next-draft.md"
            self.assertTrue(next_draft_path.exists())
            self.assertIn(
                "target-dib-platform-001",
                next_draft_path.read_text(encoding="utf-8"),
            )

            send_copy = subprocess.run(
                [
                    "make",
                    "validation-send-copy",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(send_copy.returncode, 0, send_copy.stderr)
            self.assertTrue(send_copy.stdout.startswith("Subject: Intro to someone"))
            self.assertIn("Hi,", send_copy.stdout)
            self.assertNotIn("<first name>", send_copy.stdout)
            self.assertNotRegex(send_copy.stdout, r"<[^>\n]+>")
            self.assertNotIn("Prophet Validation Draft - 2026-05-10", send_copy.stdout)
            self.assertNotIn("Subject options:", send_copy.stdout)
            self.assertNotIn("Message:", send_copy.stdout)
            self.assertNotIn("target-dib-platform-001", send_copy.stdout)
            self.assertNotIn("make validation-apply-draft", send_copy.stdout)
            send_copy_path = private_dir / "today-send-copy.txt"
            self.assertTrue(send_copy_path.exists())
            send_copy_text = send_copy_path.read_text(encoding="utf-8")
            self.assertTrue(send_copy_text.startswith("Subject: Intro to someone"))
            self.assertNotIn("Subject options:", send_copy_text)
            self.assertNotIn("CONFIRM_SENT", send_copy_text)

            batch = subprocess.run(
                [
                    "make",
                    "validation-send-copy-batch",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(batch.returncode, 0, batch.stderr)
            batch_manifest = json.loads(batch.stdout)
            self.assertEqual(batch_manifest["copy_file_count"], 8)
            batch_dir = private_dir / "send-copy-2026-05-10"
            first_copy = batch_dir / "01.txt"
            self.assertTrue(first_copy.exists())
            self.assertFalse((batch_dir / "01-targeted_ask-target-dib-platform-001.txt").exists())
            self.assertTrue((batch_dir / "manifest.json").exists())
            first_copy_text = first_copy.read_text(encoding="utf-8")
            self.assertTrue(first_copy_text.startswith("Subject: Intro to someone"))
            self.assertNotIn("target-dib-platform-001", first_copy_text)
            self.assertNotIn("make validation-apply-draft", first_copy_text)

            mismatch = subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-11",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("required date 2026-05-11", mismatch.stderr)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_next_draft_rejects_stale_pack_without_date_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=1900-01-01",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match required date", completed.stderr)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_resume_prints_existing_next_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-resume",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Next draft exists: true", completed.stdout)
            self.assertIn("Build gate open: false", completed.stdout)
            self.assertIn("Copy-only send text is missing or stale", completed.stdout)
            self.assertIn("make validation-send-copy DATE=2026-05-10", completed.stdout)
            self.assertIn("DO NOT SEND BELOW THIS LINE", completed.stdout)
            self.assertIn("Already-rendered next draft with tracker metadata:", completed.stdout)
            self.assertLess(
                completed.stdout.index("Copy-only send text"),
                completed.stdout.index("Already-rendered next draft with tracker metadata:"),
            )
            self.assertIn("Next Prophet Validation Draft - 2026-05-10", completed.stdout)
            self.assertIn("target-dib-platform-001", completed.stdout)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            first_target = targets["targets"][0]
            self.assertEqual(first_target["status"], "identified")
            self.assertEqual(first_target["last_touch"], "")
            self.assertEqual(first_target["follow_up_due"], "")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_resume_does_not_print_stale_send_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            (private_dir / "today-send-copy.txt").write_text(
                "stale outbound text\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-resume",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Send-copy state: stale", completed.stdout)
            self.assertIn("Copy-only send text is missing or stale", completed.stdout)
            self.assertIn("make validation-send-copy DATE=2026-05-10", completed.stdout)
            self.assertNotIn("stale outbound text", completed.stdout)
            self.assertIn("DO NOT SEND BELOW THIS LINE", completed.stdout)
            self.assertIn("Already-rendered next draft with tracker metadata:", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_resume_marks_copy_only_boundary_when_send_copy_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)
            subprocess.run(
                [
                    "make",
                    "validation-send-copy",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)

            completed = subprocess.run(
                [
                    "make",
                    "validation-resume",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("BEGIN COPY-ONLY SEND TEXT:", completed.stdout)
        self.assertIn("END COPY-ONLY SEND TEXT", completed.stdout)
        self.assertIn("DO NOT SEND BELOW THIS LINE", completed.stdout)
        self.assertIn("Already-rendered next draft with tracker metadata:", completed.stdout)
        self.assertLess(
            completed.stdout.index("BEGIN COPY-ONLY SEND TEXT:"),
            completed.stdout.index("END COPY-ONLY SEND TEXT"),
        )
        self.assertLess(
            completed.stdout.index("END COPY-ONLY SEND TEXT"),
            completed.stdout.index("DO NOT SEND BELOW THIS LINE"),
        )
        send_block = completed.stdout.split("BEGIN COPY-ONLY SEND TEXT:", 1)[1].split(
            "END COPY-ONLY SEND TEXT", 1
        )[0]
        self.assertIn("Subject: Intro to someone", send_block)
        self.assertIn("Hi,", send_block)
        self.assertNotIn("<first name>", send_block)
        self.assertNotRegex(send_block, r"<[^>\n]+>")
        self.assertNotIn("target-dib-platform-001", send_block)
        self.assertNotIn("make validation-apply-draft", send_block)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_goal_resume_alias_prints_existing_next_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "goal-resume",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Next draft matches target/date/status/body: true", completed.stdout)
            self.assertIn("Copy-only send text is missing or stale", completed.stdout)
            self.assertIn("DO NOT SEND BELOW THIS LINE", completed.stdout)
            self.assertIn("Already-rendered next draft with tracker metadata:", completed.stdout)
            self.assertIn("Next Prophet Validation Draft - 2026-05-10", completed.stdout)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_resume_refuses_stale_existing_next_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)

            completed = subprocess.run(
                [
                    "make",
                    "validation-resume",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Next target: target-dib-platform-002", completed.stdout)
            self.assertIn("Next draft matches target/date/status/body: false", completed.stdout)
            self.assertIn("stale for the current tracker", completed.stdout)
            self.assertIn("Existing next draft is stale or unreadable", completed.stdout)
            self.assertIn("Run: make validation-next-draft DATE=2026-05-10", completed.stdout)
            self.assertNotIn("Already-rendered next draft:", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_next_draft_overwrites_stale_file_after_confirmed_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)
            subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-next-draft",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            dashboard = subprocess.run(
                [
                    "make",
                    "validation-dashboard",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            next_draft = (private_dir / "today-next-draft.md").read_text(encoding="utf-8")
            summary = json.loads(dashboard.stdout)

        self.assertIn("Next Prophet Validation Draft - 2026-05-10", completed.stdout)
        self.assertIn("- Target: target-dib-platform-002", completed.stdout)
        self.assertIn("- Target: target-dib-platform-002", next_draft)
        self.assertNotIn("- Target: target-dib-platform-001", next_draft)
        self.assertEqual(
            summary["outreach_execution"]["next_pending_target_label"],
            "target-dib-platform-002",
        )
        self.assertEqual(
            summary["outreach_execution"]["next_draft_target_label"],
            "target-dib-platform-002",
        )
        self.assertEqual(summary["outreach_execution"]["next_draft_state"], "ready")
        self.assertTrue(summary["outreach_execution"]["next_draft_matches_next_pending"])

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_draft_uses_overridden_private_directory_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-draft",
                    "TARGET=target-dib-platform-004",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Prophet Validation Message Pack - 2026-05-10", completed.stdout)
            self.assertIn("target-dib-platform-004 - targeted_ask", completed.stdout)
            self.assertNotIn("target-dib-platform-001 - targeted_ask", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_draft_copy_prints_copy_only_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-draft-copy",
                    "TARGET=target-dib-platform-004",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(completed.stdout.startswith("Subject: "))
            self.assertIn("Is that a real pain", completed.stdout)
            self.assertNotIn("target-dib-platform-004", completed.stdout)
            self.assertNotIn("make validation-apply-draft", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_draft_rejects_stale_pack_without_date_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=1900-01-01",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-draft",
                    "TARGET=target-dib-platform-004",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match required date", completed.stderr)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_dashboard_uses_overridden_private_directory_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-dashboard",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            dashboard = json.loads(completed.stdout)
            self.assertFalse(dashboard["build_gate"]["allowed_to_build_next_slice"])
            self.assertEqual(dashboard["customer_validation"]["verdict"], "insufficient_data")
            self.assertEqual(dashboard["outreach_execution"]["generated_for"], "2026-05-10")
            self.assertEqual(
                dashboard["outreach_execution"]["next_pending_target_label"],
                "target-dib-platform-001",
            )

            mismatch = subprocess.run(
                [
                    "make",
                    "validation-dashboard",
                    "DATE=2026-05-11",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("required date 2026-05-11", mismatch.stderr)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_team_update_uses_aggregate_only_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-team-update",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Prophet Validation Team Update", completed.stdout)
            self.assertIn("Customer validation verdict: insufficient_data", completed.stdout)
            self.assertIn("Pending send/update: 8", completed.stdout)
            self.assertIn("Send-copy state:", completed.stdout)
            self.assertIn("Send-copy matches next draft:", completed.stdout)
            self.assertNotIn("target-dib-", completed.stdout)
            self.assertNotIn("make validation-apply-draft", completed.stdout)
            self.assertNotIn("validation/private", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_team_update_save_writes_aggregate_only_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-team-update-save",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            output_path = private_dir / "today-team-update.md"
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(str(output_path), completed.stdout)
            text = output_path.read_text(encoding="utf-8")
            self.assertIn("Prophet Validation Team Update", text)
            self.assertIn("Customer validation verdict: insufficient_data", text)
            self.assertIn("Pending send/update: 8", text)
            self.assertIn("Send-copy state:", text)
            self.assertIn("Send-copy matches next draft:", text)
            self.assertNotIn("target-dib-", text)
            self.assertNotIn("make validation-apply-draft", text)
            self.assertNotIn("validation/private", text)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_team_update_save_does_not_clobber_existing_file_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            (private_dir / "customer-validation-log.json").write_text(
                "{not valid json\n",
                encoding="utf-8",
            )
            output_path = private_dir / "today-team-update.md"
            output_path.write_text("previous aggregate update\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "make",
                    "validation-team-update-save",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("validation sprint dashboard failed", completed.stderr)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "previous aggregate update\n",
            )
            self.assertEqual(list(private_dir.glob("today-team-update.md.tmp.*")), [])

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_apply_draft_defaults_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertFalse(summary["would_write"])
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_apply_draft_rejects_stale_pack_without_date_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=1900-01-01",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match required date", completed.stderr)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_apply_draft_can_write_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            _run_make_send_copy(private_dir)

            completed = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertTrue(summary["would_write"])
            self.assertEqual(targets["targets"][0]["status"], "outreach_sent")
            self.assertEqual(targets["targets"][0]["follow_up_due"], "2026-05-13")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_apply_draft_confirm_requires_copy_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("copy-only send artifact is not ready", completed.stderr)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_apply_draft_rejects_non_exact_one_confirm_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")
            subprocess.run(
                [
                    "make",
                    "validation-pack",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=0",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("CONFIRM_SENT must be 1", completed.stderr)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

            multi_value = subprocess.run(
                [
                    "make",
                    "validation-apply-draft",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-10",
                    "CONFIRM_SENT=1 0",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(multi_value.returncode, 0)
            self.assertIn("CONFIRM_SENT must be 1", multi_value.stderr)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_defaults_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_booked_target(
                private_dir / "validation-targets.json",
                "example-dib-platform-002",
            )
            interview_path = private_dir / "customer-validation-interview-next.json"
            interview_path.write_text(
                json.dumps(
                    {
                        "account_label": "example-dib-platform-002",
                        "segment": "dib_platform_security",
                        "persona": "director_product_security",
                        "qualified": True,
                        "current_workflow": "Scanner, SBOM review, ticket queue, manual briefing.",
                        "recent_painful_event": "Had to justify edge appliance remediation order.",
                        "existing_tools": ["scanner", "ticketing"],
                        "status_quo_gap": "No audit-ready packet for why this first.",
                        "desired_output": "Evidence packet with source basis and SOC review handoff.",
                        "workflow_pain_theme": "evidence_packet_gap",
                        "pain_score": 5,
                        "urgency_score": 4,
                        "status_quo_weakness_score": 4,
                        "buyer_access_score": 3,
                        "data_feasibility_score": 4,
                        "pilot_pull_score": 3,
                        "budget_signal": "could_sponsor_design_partner",
                        "pilot_signal": "asked_for_scoped_pilot",
                        "objections": ["Needs security review."],
                        "next_step": "Send pilot scope.",
                        "safe_artifact_offer": "Sanitized SBOM family export.",
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertEqual(summary["interview_count"], 2)
            self.assertFalse(summary["confirmed_log"])
            self.assertFalse(summary["would_write"])
            self.assertEqual(len(log["interviews"]), 1)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_requires_booked_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_booked_target(
                private_dir / "validation-targets.json",
                "example-dib-platform-002",
                status="identified",
            )
            _write_valid_interview(private_dir / "customer-validation-interview-next.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("target current status", completed.stderr)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertEqual(len(log["interviews"]), 1)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_prepare_interview_writes_incomplete_private_starter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
            targets["targets"][0]["status"] = "call_booked"
            targets["targets"][0]["last_touch"] = "2026-05-11"
            targets["targets"][0]["follow_up_due"] = ""
            targets["targets"][0]["next_action"] = "Prepare discovery call."
            (private_dir / "validation-targets.json").write_text(
                json.dumps(targets),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "make",
                    "validation-prepare-interview",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-12",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            interview = json.loads(
                (private_dir / "customer-validation-interview-next.json").read_text()
            )
            self.assertEqual(summary["target_label"], "target-dib-platform-001")
            self.assertEqual(
                summary["log_dry_run_command"],
                "make validation-log-interview DATE=2026-05-12",
            )
            self.assertEqual(interview["account_label"], "target-dib-platform-001")
            self.assertEqual(interview["current_workflow"], "")
            self.assertEqual(interview["pain_score"], 0)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_writes_only_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_booked_target(
                private_dir / "validation-targets.json",
                "example-dib-platform-002",
            )
            interview_path = private_dir / "customer-validation-interview-next.json"
            interview_path.write_text(
                json.dumps(
                    {
                        "account_label": "example-dib-platform-002",
                        "segment": "dib_platform_security",
                        "persona": "director_product_security",
                        "qualified": True,
                        "current_workflow": "Scanner, SBOM review, ticket queue, manual briefing.",
                        "recent_painful_event": "Had to justify edge appliance remediation order.",
                        "existing_tools": ["scanner", "ticketing"],
                        "status_quo_gap": "No audit-ready packet for why this first.",
                        "desired_output": "Evidence packet with source basis and SOC review handoff.",
                        "workflow_pain_theme": "evidence_packet_gap",
                        "pain_score": 5,
                        "urgency_score": 4,
                        "status_quo_weakness_score": 4,
                        "buyer_access_score": 3,
                        "data_feasibility_score": 4,
                        "pilot_pull_score": 3,
                        "budget_signal": "could_sponsor_design_partner",
                        "pilot_signal": "asked_for_scoped_pilot",
                        "objections": ["Needs security review."],
                        "next_step": "Send pilot scope.",
                        "safe_artifact_offer": "Sanitized SBOM family export.",
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    "CONFIRM_LOG=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertEqual(summary["interview_count"], 2)
            self.assertTrue(summary["confirmed_log"])
            self.assertTrue(summary["would_write"])
            self.assertEqual(len(log["interviews"]), 2)
            self.assertEqual(log["updated_at"], "2026-05-10")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_can_replace_example_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_booked_target(
                private_dir / "validation-targets.json",
                "target-dib-platform-001",
            )
            _write_valid_interview(
                private_dir / "customer-validation-interview-next.json",
                account_label="target-dib-platform-001",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    "REPLACE_EXAMPLE_SEED=1",
                    "CONFIRM_LOG=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertTrue(summary["replaced_example_seed"])
            self.assertFalse(summary["example_seed_log"])
            self.assertEqual(summary["removed_example_seed_count"], 1)
            self.assertEqual(summary["interview_count"], 1)
            self.assertEqual(log["interviews"][0]["account_label"], "target-dib-platform-001")
            self.assertNotIn("Example only", log["notes"])

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_rejects_non_one_confirm_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_valid_interview(private_dir / "customer-validation-interview-next.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    "CONFIRM_LOG=false",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("CONFIRM_LOG must be 1", completed.stderr)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertEqual(len(log["interviews"]), 1)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_usage_mentions_seed_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("REPLACE_EXAMPLE_SEED=1", completed.stdout)
            self.assertIn("CONFIRM_LOG=1", completed.stdout)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_log_interview_rejects_non_one_replace_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")
            _write_booked_target(
                private_dir / "validation-targets.json",
                "target-dib-platform-001",
            )
            _write_valid_interview(
                private_dir / "customer-validation-interview-next.json",
                account_label="target-dib-platform-001",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-log-interview",
                    "DATE=2026-05-10",
                    "REPLACE_EXAMPLE_SEED=0",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("REPLACE_EXAMPLE_SEED must be 1", completed.stderr)
            log = json.loads((private_dir / "customer-validation-log.json").read_text())
            self.assertEqual(len(log["interviews"]), 1)

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_book_call_defaults_to_dry_run_and_can_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
            targets["targets"][0]["status"] = "outreach_sent"
            targets["targets"][0]["last_touch"] = "2026-05-10"
            targets["targets"][0]["follow_up_due"] = "2026-05-13"
            (private_dir / "validation-targets.json").write_text(
                json.dumps(targets),
                encoding="utf-8",
            )

            dry_run = subprocess.run(
                [
                    "make",
                    "validation-book-call",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-11",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            summary = json.loads(dry_run.stdout)
            unchanged = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(summary["after"]["status"], "call_booked")
            self.assertEqual(summary["status_command"], "make validation-status DATE=2026-05-11")
            self.assertEqual(unchanged["targets"][0]["status"], "outreach_sent")

            confirmed = subprocess.run(
                [
                    "make",
                    "validation-book-call",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-11",
                    "CONFIRM_TARGET=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
            written = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(written["targets"][0]["status"], "call_booked")
            self.assertEqual(written["targets"][0]["follow_up_due"], "")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_target_wrappers_reject_non_one_confirm_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-disqualify-target",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-11",
                    "CONFIRM_TARGET=0",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("CONFIRM_TARGET must be 1", completed.stderr)
            targets = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(targets["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_disqualify_target_defaults_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            shutil.copyfile(EXAMPLE_TARGETS, private_dir / "validation-targets.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-disqualify-target",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-11",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            unchanged = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(summary["after"]["status"], "disqualified")
            self.assertEqual(unchanged["targets"][0]["status"], "identified")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_complete_call_writes_only_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
            targets["targets"][0]["status"] = "call_booked"
            targets["targets"][0]["last_touch"] = "2026-05-11"
            (private_dir / "validation-targets.json").write_text(
                json.dumps(targets),
                encoding="utf-8",
            )
            _write_matching_validation_log(
                private_dir / "customer-validation-log.json",
                "target-dib-platform-001",
            )

            completed = subprocess.run(
                [
                    "make",
                    "validation-complete-call",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-12",
                    "CONFIRM_TARGET=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            written = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(summary["after"]["status"], "completed")
            self.assertEqual(written["targets"][0]["status"], "completed")
            self.assertEqual(written["targets"][0]["next_action"], "Logged sanitized discovery outcome.")

    @unittest.skipIf(shutil.which("make") is None, "make is not available")
    def test_validation_complete_call_requires_matching_logged_interview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "validation-private"
            private_dir.mkdir()
            targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
            targets["targets"][0]["status"] = "call_booked"
            targets["targets"][0]["last_touch"] = "2026-05-11"
            (private_dir / "validation-targets.json").write_text(
                json.dumps(targets),
                encoding="utf-8",
            )
            shutil.copyfile(EXAMPLE_LOG, private_dir / "customer-validation-log.json")

            completed = subprocess.run(
                [
                    "make",
                    "validation-complete-call",
                    "TARGET=target-dib-platform-001",
                    "DATE=2026-05-12",
                    "CONFIRM_TARGET=1",
                    f"VALIDATION_DIR={private_dir}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("no sanitized interview", completed.stderr)
            unchanged = json.loads((private_dir / "validation-targets.json").read_text())
            self.assertEqual(unchanged["targets"][0]["status"], "call_booked")


def _write_valid_interview(
    path: Path,
    *,
    account_label: str = "example-dib-platform-002",
) -> None:
    path.write_text(
        json.dumps(
            {
                "account_label": account_label,
                "segment": "dib_platform_security",
                "persona": "director_product_security",
                "qualified": True,
                "current_workflow": "Scanner, SBOM review, ticket queue, manual briefing.",
                "recent_painful_event": "Had to justify edge appliance remediation order.",
                "existing_tools": ["scanner", "ticketing"],
                "status_quo_gap": "No audit-ready packet for why this first.",
                "desired_output": "Evidence packet with source basis and SOC review handoff.",
                "workflow_pain_theme": "evidence_packet_gap",
                "pain_score": 5,
                "urgency_score": 4,
                "status_quo_weakness_score": 4,
                "buyer_access_score": 3,
                "data_feasibility_score": 4,
                "pilot_pull_score": 3,
                "budget_signal": "could_sponsor_design_partner",
                "pilot_signal": "asked_for_scoped_pilot",
                "objections": ["Needs security review."],
                "next_step": "Send pilot scope.",
                "safe_artifact_offer": "Sanitized SBOM family export.",
            }
        ),
        encoding="utf-8",
    )


def _run_make_send_copy(private_dir: Path) -> None:
    subprocess.run(
        [
            "make",
            "validation-send-copy",
            "DATE=2026-05-10",
            f"VALIDATION_DIR={private_dir}",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _write_matching_validation_log(path: Path, account_label: str) -> None:
    log = json.loads(EXAMPLE_LOG.read_text(encoding="utf-8"))
    log["interviews"][0]["account_label"] = account_label
    path.write_text(json.dumps(log), encoding="utf-8")


def _write_booked_target(
    path: Path,
    target_label: str,
    *,
    status: str = "call_booked",
) -> None:
    targets = json.loads(EXAMPLE_TARGETS.read_text(encoding="utf-8"))
    targets["targets"][0]["target_label"] = target_label
    targets["targets"][0]["status"] = status
    targets["targets"][0]["last_touch"] = "2026-05-10"
    targets["targets"][0]["follow_up_due"] = ""
    targets["targets"][0]["next_action"] = "Prepare discovery call."
    path.write_text(json.dumps(targets), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
