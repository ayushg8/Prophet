from __future__ import annotations

import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI_REFERENCE = ROOT / "docs" / "CLI_REFERENCE.md"
README = ROOT / "README.md"


class CliReferenceDocsTests(unittest.TestCase):
    def test_readme_documents_validation_status_machine_readable_output(self) -> None:
        text = README.read_text(encoding="utf-8")

        self.assertIn("make validation-status", text)
        self.assertIn("make validation-team-update", text)
        self.assertIn("make validation-team-update-save", text)
        self.assertIn("make validation-next-action-save", text)
        self.assertIn("validation-next-action.py", text)
        self.assertIn("make validation-weekly-review", text)
        self.assertIn("make validation-prune-private", text)
        self.assertIn("validation-reply-triage.py", text)
        self.assertIn("make validation-reply-triage", text)
        self.assertIn("make validation-send-copy", text)
        self.assertIn("make validation-send-copy-batch", text)
        self.assertIn("make validation-draft-copy", text)
        self.assertIn("make validation-resume", text)
        self.assertIn("make goal-resume", text)
        self.assertIn("make python-tests", text)
        self.assertIn("sanitized aggregate-only", text)
        self.assertIn("aggregate send-copy readiness", text)
        self.assertIn("prints the Markdown status report", text)
        self.assertIn("validation/private/today-outreach-status.json", text)
        self.assertIn("validation/private/today-team-update.md", text)
        self.assertIn("validation/private/NEXT_ACTION.md", text)
        self.assertIn("validation/private/today-send-copy.txt", text)
        self.assertIn("validation/private/send-copy-YYYY-MM-DD/", text)
        self.assertIn("next_pending_target_label", text)
        self.assertIn("CONFIRM_SENT=1", text)
        self.assertIn("Confirmed", text)
        self.assertIn("send-derived `intro_requested` / `outreach_sent` writes are blocked", text)
        self.assertIn("exact write guards", text)
        self.assertIn("CONFIRM_TARGET=1", text)
        self.assertIn("CONFIRM_LOG=1", text)
        self.assertIn("CONFIRM_PRUNE=1", text)
        self.assertIn("--require-target-status call_booked", text)
        self.assertIn("--allow-untracked-interview", text)
        self.assertIn("Do not use", text)
        self.assertIn("REPLACE_EXAMPLE_SEED=1", text)
        self.assertIn("CLI rejects that combination", text)
        self.assertIn("fail closed", text)
        self.assertIn("--refresh-readme", text)
        self.assertIn("private tracker or log files", text)
        self.assertIn("read-only private weekly review", text)
        self.assertIn("sanitized classification", text)

    def test_validation_status_documents_machine_readable_output(self) -> None:
        text = CLI_REFERENCE.read_text(encoding="utf-8")

        self.assertIn("make validation-status", text)
        self.assertIn("make validation-team-update", text)
        self.assertIn("make validation-team-update-save", text)
        self.assertIn("make validation-next-action-save", text)
        self.assertIn("validation-next-action.py", text)
        self.assertIn("make validation-weekly-review", text)
        self.assertIn("make validation-prune-private", text)
        self.assertIn("validation-prune-private.py", text)
        self.assertIn("validation-reply-triage.py", text)
        self.assertIn("make validation-reply-triage", text)
        self.assertIn("make validation-send-copy", text)
        self.assertIn("make validation-send-copy-batch", text)
        self.assertIn("make validation-draft-copy", text)
        self.assertIn("make validation-resume", text)
        self.assertIn("make goal-resume", text)
        self.assertIn("make python-tests", text)
        self.assertIn("make secrets-archaeology", text)
        self.assertIn("git-history secret scan", text)
        self.assertIn("--format team", text)
        self.assertIn("aggregate send-copy readiness", text)
        self.assertIn("prints the Markdown status report", text)
        self.assertIn("validation/private/today-outreach-status.json", text)
        self.assertIn("validation/private/today-team-update.md", text)
        self.assertIn("validation/private/NEXT_ACTION.md", text)
        self.assertIn("validation/private/today-send-copy.txt", text)
        self.assertIn("validation/private/send-copy-YYYY-MM-DD/", text)
        self.assertIn("next_pending_target_label", text)
        self.assertIn("CONFIRM_SENT=1", text)
        self.assertIn("Confirmed", text)
        self.assertIn("send-derived `intro_requested` / `outreach_sent` writes are blocked", text)
        self.assertIn("exact write guards", text)
        self.assertIn("CONFIRM_TARGET=1", text)
        self.assertIn("CONFIRM_LOG=1", text)
        self.assertIn("CONFIRM_PRUNE=1", text)
        self.assertIn("--require-target-status call_booked", text)
        self.assertIn("--allow-untracked-interview", text)
        self.assertIn("--replace-example-seed", text)
        self.assertIn("Do not combine --replace-example-seed with --allow-untracked-interview", text)
        self.assertIn("rejects `--allow-untracked-interview`", text)
        self.assertIn("fail closed", text)
        self.assertIn("--refresh-readme", text)
        self.assertIn("tracker/log files", text)
        self.assertIn("does not delete", text)
        self.assertIn("never reply text", text)
        self.assertIn("copy the generated subject/body as-is", text)
        self.assertIn("personalize only in the outreach channel", text)
        self.assertIn("Do not store recipient names", text)
        self.assertNotIn("replace only the recipient name", text)

    def test_console_demo_docs_name_dependency_and_port_override(self) -> None:
        readme = README.read_text(encoding="utf-8")
        reference = CLI_REFERENCE.read_text(encoding="utf-8")
        troubleshooting = (ROOT / "docs" / "PILOT_TROUBLESHOOTING.md").read_text(
            encoding="utf-8"
        )

        for text in (readme, reference, troubleshooting):
            with self.subTest(document=text[:40]):
                self.assertIn("make console-demo", text)
                self.assertIn("make console-live-check", text)
                self.assertIn("PROPHET_CONTROL_PORT=8877", text)
                self.assertIn("PROPHET_CONSOLE_PORT=5273", text)
                self.assertIn("localhost", text)
        self.assertIn("npm ci", reference)
        self.assertIn("npm run capture:screenshots", reference)
        self.assertIn("make console-screenshot-check", reference)
        self.assertIn("console-screenshots/manifest.json", reference)
        self.assertIn("Policy-Blocked Evaluator Action Runbook", troubleshooting)
        self.assertIn("Evidence Generation Failure Runbook", troubleshooting)
        self.assertIn("Sandbox Validation Failure Runbook", troubleshooting)
        self.assertIn("Dependency audit fails", troubleshooting)
        self.assertIn("policy_blocked", troubleshooting)
        self.assertIn("./scripts/run-policy-blocked-demo.sh", troubleshooting)
        self.assertIn("evidence/tests", troubleshooting)
        self.assertIn("sandbox_runner/tests", troubleshooting)
        self.assertIn("npm audit --audit-level=moderate", troubleshooting)
        self.assertIn("do not mark validation progress", troubleshooting)
        self.assertIn("build_next_slice", troubleshooting)

    def test_visual_handoff_docs_name_screenshot_verifier(self) -> None:
        documents = [
            README,
            ROOT / "docs" / "EVALUATOR_START_HERE.md",
            ROOT / "docs" / "PILOT_DEMO.md",
            ROOT / "docs" / "DEMO_OPERATOR_CHECKLIST.md",
            ROOT / "docs" / "CONSOLE_EXPECTED_SCREENSHOTS.md",
            CLI_REFERENCE,
        ]

        for path in documents:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("npm run capture:screenshots", text)
                self.assertIn("make console-screenshot-check", text)
                self.assertIn("redacted", text)

    def test_validation_dashboard_documents_next_draft_exists(self) -> None:
        readme = README.read_text(encoding="utf-8")
        reference = CLI_REFERENCE.read_text(encoding="utf-8")

        for text in (readme, reference):
            with self.subTest(document=text[:40]):
                self.assertIn("outreach_execution.next_draft_exists", text)
                self.assertIn("outreach_execution.next_draft_state", text)
                self.assertIn("outreach_execution.next_draft_matches_next_pending", text)
                self.assertIn("outreach_execution.send_copy_state", text)
                self.assertIn("outreach_execution.send_copy_matches_next_pending", text)
                self.assertIn("outreach_execution.send_copy_batch_state", text)
                self.assertIn("outreach_execution.send_copy_batch_matches_current_pack", text)
                self.assertIn("outreach_execution.send_copy_batch_readme_exists", text)
                self.assertIn("outreach_execution.send_copy_batch_checklist_exists", text)
                self.assertIn("outreach_execution.send_copy_batch_copy_index_exists", text)
                self.assertIn("outreach_execution.send_copy_batch_subject_order_exists", text)
                self.assertIn("target/date/status", text)
                self.assertIn("already-rendered", text)
                self.assertIn("validation/private/today-next-draft.md", text)
                self.assertIn("neutral copy-index body", text)
                self.assertIn("subject-order body", text)
                self.assertIn("private manifest, checklist, copy index", text)
                self.assertIn("subject-order helper", text)
                self.assertIn("batch README", text)
                self.assertIn("make validation-resume", text)
                self.assertIn("make goal-resume", text)
                self.assertIn("--format text", text)
                self.assertIn("--format team", text)

    def test_documented_help_commands_execute(self) -> None:
        commands = _help_commands()
        self.assertGreaterEqual(len(commands), 20)

        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(
                    _argv_for(command),
                    cwd=ROOT,
                    env=_env_for(command),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                    check=False,
                )

                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                lowered = output.lower()
                self.assertTrue(
                    any(
                        marker in lowered
                        for marker in ("usage:", "optional arguments", "prophet operator targets")
                    ),
                    output,
                )


def _help_commands() -> list[str]:
    text = CLI_REFERENCE.read_text(encoding="utf-8")
    marker = "The docs test suite executes these help commands directly:"
    start = text.index(marker)
    fenced_start = text.index("```text", start)
    body_start = text.index("\n", fenced_start) + 1
    fenced_end = text.index("```", body_start)
    return [
        line.strip()
        for line in text[body_start:fenced_end].splitlines()
        if line.strip()
    ]


def _argv_for(command: str) -> list[str]:
    parts = shlex.split(command)
    if parts[0].startswith("PYTHONPATH="):
        parts = parts[1:]
    if parts and parts[0] == "python3":
        parts[0] = sys.executable
    return parts


def _env_for(command: str) -> dict[str, str]:
    env = os.environ.copy()
    first = shlex.split(command)[0]
    if first.startswith("PYTHONPATH="):
        key, value = first.split("=", 1)
        env[key] = value
    return env


if __name__ == "__main__":
    unittest.main()
