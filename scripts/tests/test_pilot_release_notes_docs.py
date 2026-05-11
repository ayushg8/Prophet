from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_NOTES = ROOT / "docs" / "PILOT_RELEASE_NOTES.md"
CHANGELOG = ROOT / "CHANGELOG.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
MASTER_TODO = ROOT / "docs" / "PROPHET_MASTER_TODO.md"


class PilotReleaseNotesDocsTests(unittest.TestCase):
    def test_release_notes_name_runnable_local_product_and_gate(self) -> None:
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")
        sandbox_tests = (ROOT / "sandbox_runner/tests/test_runner.py").read_text(encoding="utf-8")

        self.assertIn("## Runnable Local Product", text)
        self.assertIn("make console-demo", text)
        self.assertIn("http://127.0.0.1:5173/", text)
        self.assertIn("http://127.0.0.1:8787/api/readiness", text)
        self.assertIn("make pilot-ready-check-full DATE=2026-05-11", text)
        self.assertIn("Playwright console smoke tests", text)
        self.assertIn("365 tests", text)
        self.assertIn("0 paths in the clean committed worktree", text)
        self.assertIn("0 untracked non-ignored files", text)
        self.assertIn("default-output URL/provenance safety", text)
        self.assertIn("make release-hygiene", text)
        self.assertIn("make secrets-archaeology", text)
        self.assertIn("historical `LOG4SHELL_INSTRUCTIONS.md`", text)
        self.assertIn("docs/SECRET_HISTORY_REVIEW.md", text)
        self.assertIn("pre-commit hook", text)
        self.assertIn("make console-live-check", text)
        self.assertIn("make console-screenshot-check", text)
        self.assertIn("0 non-ignored dirty files", text)
        self.assertIn("Linux fresh-clone pilot smoke", text)
        self.assertIn("Customer validation remains `insufficient_data`", text)
        self.assertIn("production platform build", text)
        self.assertNotIn("331 tests", text)
        self.assertNotIn("330 tests", text)
        self.assertNotIn("322 tests", text)
        self.assertNotIn("320 tests", text)
        self.assertNotIn("315 tests", text)
        self.assertNotIn("312 tests", text)
        self.assertNotIn("316 tests", text)
        self.assertNotIn("318 tests", text)
        self.assertNotIn("337 tests", text)
        self.assertNotIn("345 tests", text)
        self.assertNotIn("348 tests", text)
        self.assertNotIn("349 tests", text)
        self.assertNotIn("352 tests", text)
        self.assertNotIn("353 tests", text)
        self.assertNotIn("354 tests", text)
        self.assertNotIn("355 tests", text)
        self.assertNotIn("91 paths", text)
        self.assertNotIn("92 paths", text)
        self.assertNotIn("93 paths", text)
        self.assertNotIn("66 untracked non-ignored files", text)
        self.assertNotIn("64 untracked non-ignored files", text)
        self.assertNotIn("63 untracked non-ignored files", text)
        self.assertNotIn("58 untracked non-ignored files", text)
        self.assertNotIn("59 untracked non-ignored files", text)
        self.assertIn("[x] Day 1: Convert this working tree into reviewable commits.", master_todo)
        self.assertIn("[x] Day 1: Run full Python and console acceptance.", master_todo)
        self.assertIn("[x] Day 1: Fix any smoke or lint regressions.", master_todo)
        self.assertIn("[x] Day 3: Add sandbox artifact schema and validation tests.", master_todo)
        self.assertIn("[~] Day 7: Run fresh clone smoke and package an internal pilot release.", master_todo)
        self.assertNotIn("[x] Day 7: Run fresh clone smoke and package an internal pilot release.", master_todo)
        self.assertTrue((ROOT / "sandbox_runner/sandbox-artifact.schema.json").is_file())
        self.assertTrue((ROOT / "sandbox_runner/sandbox-run-manifest.schema.json").is_file())
        self.assertIn("test_sandbox_artifact_schema_file_is_published", sandbox_tests)
        self.assertIn("validate_sandbox_run_manifest_schema", sandbox_tests)

    def test_release_notes_keep_safety_boundary_explicit(self) -> None:
        text = RELEASE_NOTES.read_text(encoding="utf-8")

        self.assertIn("does not authorize live target validation", text)
        self.assertIn("live collection workflows", text)
        self.assertIn("payload", text)
        self.assertIn("autonomous remediation", text)
        self.assertIn("rejects non-localhost UI hosts", text)

    def test_linux_fresh_clone_smoke_is_ci_backed(self) -> None:
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        master_todo = MASTER_TODO.read_text(encoding="utf-8")

        self.assertIn("runs on `ubuntu-latest`", notes)
        self.assertIn("Linux fresh-clone pilot smoke preflight", notes)
        self.assertIn("Linux fresh-clone pilot smoke", notes)
        self.assertIn("name: Linux fresh-clone pilot smoke preflight", workflow)
        self.assertIn("run: ./scripts/check-local-env.sh", workflow)
        self.assertIn("name: Linux fresh-clone pilot smoke", workflow)
        self.assertIn("run: ./scripts/run-pilot-demo-smoke.sh", workflow)
        self.assertIn("Release safety scan", workflow)
        self.assertIn("check-release-safety.py --tracked --paths-only", workflow)
        self.assertIn("Policy examples schema validation, lint, and compare", workflow)
        self.assertIn("python3 -m policy.lint", workflow)
        self.assertIn("[x] Fresh clone smoke on Linux.", master_todo)
        self.assertIn("[x] Day 4: Add CI jobs for smoke hashes, policy lint, and unsafe text scan.", master_todo)

    def test_changelog_names_current_gate_and_review_guardrails(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")

        self.assertIn("validation sprint active; production build gate closed", text)
        self.assertIn("make pilot-ready-check-full DATE=2026-05-11", text)
        self.assertIn("PR template guardrails", text)
        self.assertIn("validation dashboard verdict", text)
        self.assertIn("private-artifact boundary", text)
        self.assertIn("`insufficient_data`", text)
        self.assertIn("`build_next_slice`", text)
        self.assertIn("Linux fresh-clone smoke is covered", text)
        self.assertNotIn("make pilot-ready-check-full DATE=2026-05-10", text)
        self.assertNotIn("Linux fresh-clone smoke, and final commit split remain open", text)


if __name__ == "__main__":
    unittest.main()
