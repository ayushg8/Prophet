from __future__ import annotations

import importlib.util
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPLETION_AUDIT = ROOT / "docs/PROPHET_COMPLETION_AUDIT.md"
FINISH_INVENTORY = ROOT / "docs/PROPHET_FINISH_CHANGE_INVENTORY.md"
EXAMPLE_LOG = ROOT / "docs/customer-validation-log.example.json"
EXAMPLE_TARGETS = ROOT / "docs/validation-targets.example.json"
READINESS_BACKLOG = ROOT / "docs/production-readiness-backlog.json"
READINESS_SCRIPT = ROOT / "scripts/production-readiness-scorecard.py"
DASHBOARD_SCRIPT = ROOT / "scripts/validation-sprint-dashboard.py"
READINESS_SPEC = importlib.util.spec_from_file_location(
    "production_readiness_scorecard", READINESS_SCRIPT
)
assert READINESS_SPEC and READINESS_SPEC.loader
readiness_scorecard = importlib.util.module_from_spec(READINESS_SPEC)
READINESS_SPEC.loader.exec_module(readiness_scorecard)
DASHBOARD_SPEC = importlib.util.spec_from_file_location(
    "validation_sprint_dashboard", DASHBOARD_SCRIPT
)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
validation_dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
DASHBOARD_SPEC.loader.exec_module(validation_dashboard)


class FinishInventoryDocsTests(unittest.TestCase):
    def test_verification_snapshots_share_current_script_test_count(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")

        audit_count = _script_test_count(audit)
        inventory_count = _script_test_count(inventory)
        discovered_count = _discovered_script_test_count()

        self.assertGreaterEqual(audit_count, 190)
        self.assertEqual(audit_count, discovered_count)
        self.assertEqual(audit_count, inventory_count)

    def test_untracked_file_count_matches_current_worktree(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        completed = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        actual_count = len([line for line in completed.stdout.splitlines() if line])

        self.assertEqual(_untracked_count(audit), actual_count)
        self.assertEqual(_untracked_count(inventory), actual_count)

    def test_finish_inventory_lists_every_dirty_non_ignored_path(self) -> None:
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        missing = [path for path in _dirty_worktree_paths() if path not in inventory]

        self.assertEqual(missing, [])

    def test_recovery_docs_do_not_pin_historical_checkpoint_test_counts(self) -> None:
        combined = (
            COMPLETION_AUDIT.read_text(encoding="utf-8")
            + "\n"
            + FINISH_INVENTORY.read_text(encoding="utf-8")
        )

        self.assertNotIn("186-test", combined)
        self.assertNotIn("191 tests", combined)
        self.assertIn("verification snapshot", combined)

    def test_private_validation_output_scans_are_recorded(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        self.assertIn(
            "ignored private validation output safety scan passes over the generated ignored private validation output paths",
            audit,
        )
        self.assertIn("ignored private validation output whitespace checks pass", audit)
        self.assertIn("Ignored private validation outputs passed release-safety scanning", inventory)
        self.assertIn("copy-only send text", inventory)
        self.assertIn("no-index whitespace checks", inventory)

    def test_release_hygiene_checks_are_recorded(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        tracked_count = len(
            subprocess.run(
                ["git", "ls-files"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )

        for text in (audit, inventory):
            with self.subTest(document=("audit" if text == audit else "inventory")):
                self.assertIn("check-release-safety.py --tracked --paths-only", text)
                self.assertIn(f"{tracked_count} tracked", text)
                self.assertIn("policy.lint --policy policy/prophet-pilot-policy.json", text)
                self.assertIn("check-default-output-safety.py", text)
                self.assertRegex(text, r"7 (?:policy-listed )?default outputs")
                self.assertIn("1 OSINT provenance manifest", text)
                self.assertIn("check-doc-links.py", text)
                self.assertIn("86 Markdown", text)

    def test_inventory_lists_copy_only_private_send_artifact(self) -> None:
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")

        self.assertIn("`validation/private/today-send-copy.txt`", inventory)
        self.assertIn("`validation/private/today-next-draft.md`", inventory)
        self.assertIn("`validation/private/today-message-pack.json`", inventory)
        self.assertIn("`validation/private/send-copy-2026-05-11/`", inventory)
        self.assertIn("`validation/private/send-copy-2026-05-11/README.md`", inventory)
        self.assertIn("`validation/private/send-copy-2026-05-11/CHECKLIST.md`", inventory)
        self.assertIn("send_copy_batch_state: ready", inventory)
        self.assertIn("send_copy_batch_matches_current_pack", inventory)

    def test_completion_audit_lists_current_copy_only_batch_boundary(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")

        self.assertIn("`validation/private/send-copy-2026-05-11/`", audit)
        self.assertIn("send_copy_batch_state: ready", audit)
        self.assertIn("send_copy_batch_matches_current_pack: true", audit)
        self.assertIn("manifest.json` as tracker/audit metadata", audit)
        self.assertIn("CHECKLIST.md` as tracker/audit metadata", audit)
        self.assertIn("README.md` as tracker/audit metadata", audit)

    def test_inventory_lists_private_workspace_readme(self) -> None:
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")

        self.assertIn("`validation/private/README.md`", inventory)
        self.assertIn("make goal-resume DATE=YYYY-MM-DD", inventory)
        self.assertIn("Ignored Private Validation Outputs", inventory)

    def test_inventory_describes_same_date_init_recovery_commands(self) -> None:
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")

        self.assertIn("`scripts/init-validation-sprint.py --date YYYY-MM-DD`", inventory)
        self.assertIn("same-date `make validation-dashboard DATE=YYYY-MM-DD`", inventory)
        self.assertIn("same-date `make validation-next-draft DATE=YYYY-MM-DD`", inventory)
        self.assertNotIn("`scripts/init-validation-sprint.py --date 2026-05-10` now prints", inventory)
        self.assertNotIn("`make validation-dashboard DATE=2026-05-11` before", inventory)

    def test_weekly_review_json_handoff_is_recorded(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")

        for text in (audit, inventory):
            with self.subTest(document=("audit" if text == audit else "inventory")):
                self.assertIn("validation/private/today-weekly-review.json", text)
                self.assertIn("review_date: 2026-05-11", text)
                self.assertIn("outreach_execution.state: ready", text)

    def test_inventory_lists_doc_guard_tests_for_commit_splitting(self) -> None:
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        required_tests = [
            "scripts/tests/test_asset_import_guide_docs.py",
            "scripts/tests/test_finish_inventory_docs.py",
            "scripts/tests/test_goal_recovery_docs.py",
            "scripts/tests/test_product_validation_plan_docs.py",
            "scripts/tests/test_exposure_classification_guide_docs.py",
        ]

        for test_path in required_tests:
            with self.subTest(test_path=test_path):
                self.assertIn(f"`{test_path}`", inventory)
        self.assertIn("## PR Handoff Draft", inventory)
        self.assertIn("allowed_to_build_next_slice", inventory)
        self.assertIn("`pilot_pull_detected` remains", inventory)
        self.assertIn("Do not stage `validation/private/`", inventory)
        self.assertIn("make pilot-ready-check-full DATE=2026-05-11", inventory)
        self.assertIn("make python-tests", inventory)
        self.assertIn("make release-hygiene", inventory)
        self.assertIn("make secrets-archaeology", inventory)
        self.assertIn("LOG4SHELL_INSTRUCTIONS.md", inventory)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", inventory)
        self.assertIn("make worktree-smoke", inventory)

    def test_completion_audit_readiness_numbers_match_scorecard(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        scorecard = readiness_scorecard.build_scorecard(
            readiness_scorecard.load_json(READINESS_BACKLOG),
            root=ROOT,
        )

        readiness = str(scorecard["readiness_percent"])
        critical = str(scorecard["critical_open_count"])

        self.assertIn(f"readiness_percent: {readiness}", audit)
        self.assertIn(f"Critical open production-readiness items: `{critical}`", audit)
        self.assertIn(f"Production readiness: `{readiness}%`", inventory)
        self.assertIn(f"Critical open readiness items: `{critical}`", inventory)

    def test_completion_audit_gate_numbers_match_example_dashboard(self) -> None:
        audit = COMPLETION_AUDIT.read_text(encoding="utf-8")
        inventory = FINISH_INVENTORY.read_text(encoding="utf-8")
        dashboard = validation_dashboard.build_dashboard(
            log_path=EXAMPLE_LOG,
            targets_path=EXAMPLE_TARGETS,
            message_pack_path=None,
            scripts_dir=ROOT / "scripts",
        )

        customer = dashboard["customer_validation"]
        gate = dashboard["build_gate"]
        gate_word = "open" if gate["allowed_to_build_next_slice"] else "closed"

        self.assertIn(f"Customer validation verdict: `{customer['verdict']}`", audit)
        self.assertIn(f"Customer validation verdict: `{customer['verdict']}`", inventory)
        self.assertIn(f"Build gate: {gate_word}", audit)
        self.assertIn(f"Production build gate: {gate_word}", inventory)
        self.assertIn(f"Qualified private/example interviews: `{customer['qualified_count']}`", audit)
        self.assertIn(
            f"Repeated workflow pain count: `{customer['repeated_workflow_pain_count']}`",
            audit,
        )
        target_backed = dashboard["target_backed_validation"]
        self.assertIn(
            f"Target-backed validation verdict: `{target_backed['verdict']}`",
            audit,
        )
        self.assertIn(
            f"Target-backed qualified calls: `{target_backed['qualified_count']}`",
            audit,
        )
        gaps = customer["gaps_to_verdicts"]["build_next_slice"]
        self.assertIn(
            (
                f"`{gaps['qualified_count']}` qualified call(s), "
                f"`{gaps['high_pain_count']}` high-pain call(s), "
                f"`{gaps['repeated_workflow_pain_count']}` repeated workflow-pain "
                f"match(es), `{gaps['pilot_pull_count']}` pilot-pull signal(s), "
                "and "
                f"`{gaps['paid_or_sponsored_count']}` additional paid/sponsored "
                "pilot signal(s)"
            ),
            audit,
        )


def _script_test_count(text: str) -> int:
    match = re.search(
        r"`python3 -m unittest discover -s scripts/tests -v`[^\n]*?"
        r"(?:passes with ([0-9]+) tests?|([0-9]+) tests? passed)",
        text,
    )
    if match is None:
        raise AssertionError("missing scripts test verification count")
    return int(next(group for group in match.groups() if group is not None))


def _untracked_count(text: str) -> int:
    match = re.search(r"over(?: the)? ([0-9]+)\s+untracked non-ignored files", text)
    if match is None:
        raise AssertionError("missing untracked non-ignored file count")
    return int(match.group(1))


def _discovered_script_test_count() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "scripts/tests"))
    return suite.countTestCases()


def _dirty_worktree_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    paths = []
    for line in completed.stdout.splitlines():
        if not line or line.startswith("## "):
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", maxsplit=1)[-1]
        paths.append(path)
    return paths


if __name__ == "__main__":
    unittest.main()
