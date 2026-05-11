from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "init-validation-sprint.py"
SPEC = importlib.util.spec_from_file_location("init_validation_sprint", SCRIPT)
assert SPEC and SPEC.loader
init_validation_sprint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = init_validation_sprint
SPEC.loader.exec_module(init_validation_sprint)


class InitValidationSprintTests(unittest.TestCase):
    def test_initializes_private_workspace_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "customer-validation-log.example.json").write_text('{"interviews": []}\n')
            (docs / "validation-targets.example.json").write_text('{"targets": []}\n')
            (docs / "customer-validation-interview.template.json").write_text('{"account_label": "example"}\n')

            summary = init_validation_sprint.initialize_workspace(
                repo_root=root,
                run_date="2026-05-20",
            )

            private_dir = root / "validation/private"
            self.assertTrue((private_dir / "customer-validation-log.json").exists())
            self.assertTrue((private_dir / "validation-targets.json").exists())
            self.assertTrue((private_dir / "customer-validation-interview.template.json").exists())
            self.assertTrue((private_dir / "README.md").exists())
            self.assertEqual(len(summary["written"]), 4)
            self.assertTrue(
                any("validation-message-pack.py" in command for command in summary["next_commands"])
            )
            self.assertTrue(
                any(
                    "validation-outreach-block.py --date 2026-05-20" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    "validation-message-pack.py" in command
                    and "--require-date 2026-05-20" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    command == "make validation-next-draft DATE=2026-05-20"
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    command == "make validation-send-copy DATE=2026-05-20"
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    command == (
                        "make validation-draft-copy "
                        "TARGET=target-dib-platform-004 DATE=2026-05-20"
                    )
                    for command in summary["next_commands"]
                )
            )
            self.assertLess(
                summary["next_commands"].index("make validation-dashboard DATE=2026-05-20"),
                summary["next_commands"].index("make validation-next-draft DATE=2026-05-20"),
            )
            self.assertTrue(
                any(
                    command == (
                        "make validation-apply-draft "
                        "TARGET=target-dib-platform-001 DATE=2026-05-20"
                    )
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    "validation-outreach-status.py" in command
                    and "--require-date 2026-05-20" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    command == "make validation-team-update-save DATE=2026-05-20"
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    command == "make validation-weekly-review DATE=2026-05-20"
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    "validation-sprint-dashboard.py --require-date 2026-05-20" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    "customer-validation-log-add.py" in command
                    and "--interview-json validation/private/customer-validation-interview-next.json" in command
                    and "--require-target-status call_booked" in command
                    and "--replace-example-seed" not in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any(
                    "customer-validation-log-add.py" in command
                    and "--replace-example-seed" in command
                    and "--require-target-status call_booked" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertTrue(
                any("today-message-pack.json" in command for command in summary["next_commands"])
            )
            self.assertTrue(
                any(
                    "--status outreach_sent --require-current-status identified "
                    "--require-current-status intro_requested" in command
                    and "--last-touch 2026-05-20" in command
                    and "--follow-up-due 2026-05-23" in command
                    and "--next-action 'Send follow-up if no reply.'" in command
                    for command in summary["next_commands"]
                )
            )
            self.assertIn(
                "validation-message-pack.py",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "do not force-overwrite private tracker/log files",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "validation-outreach-block.py --date 2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "--require-date 2026-05-20 --format json",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "--status outreach_sent --require-current-status identified "
                "--require-current-status intro_requested",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "--last-touch 2026-05-20 --follow-up-due 2026-05-23",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "today-outreach-status.json",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "machine-readable checks",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Normal outreach order",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-dashboard DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "If it reports `next_draft_exists: true`",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "next_draft_state: ready",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "next_draft_matches_next_pending: true",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-next-draft DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-send-copy DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-send-copy-batch DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-draft-copy TARGET=target-dib-platform-004 DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "writing `today-send-copy.txt`",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "validation/private/today-send-copy.txt",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "send_copy_state: ready",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "send_copy_matches_next_pending: true",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "send_copy_batch_state: ready",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "send_copy_batch_matches_current_pack: true",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make goal-resume DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "BEGIN COPY-ONLY SEND TEXT",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "DO NOT SEND BELOW THIS LINE",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-team-update-save DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "validation/private/today-team-update.md",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-weekly-review DATE=2026-05-20",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "not delete files or mutate trackers/logs",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Send the copy-only text outside the repo only after that dry-run is clean",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "Optional: run `make validation-send-copy",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "actual send is confirmed",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "same dated Make command with `CONFIRM_SENT=1`",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "example_seed_log: true",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "seed counts are not real buyer traction",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "REPLACE_EXAMPLE_SEED=1",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "prefer the Make wrappers during normal outreach",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Normal confirmed raw writes require `--require-target-status",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "`--allow-untracked-interview` bypass",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "interview seed replacement is stricter",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "`--replace-example-seed --require-target-status call_booked`",
                (private_dir / "README.md").read_text(encoding="utf-8"),
            )

            second = init_validation_sprint.initialize_workspace(repo_root=root)
            self.assertEqual(second["written"], [])
            self.assertEqual(len(second["skipped_existing"]), 4)

    def test_refresh_readme_without_overwriting_private_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "customer-validation-log.example.json").write_text('{"interviews": []}\n')
            (docs / "validation-targets.example.json").write_text('{"targets": []}\n')
            (docs / "customer-validation-interview.template.json").write_text('{"account_label": "example"}\n')
            init_validation_sprint.initialize_workspace(repo_root=root, run_date="2026-05-20")
            private_dir = root / "validation/private"
            log = private_dir / "customer-validation-log.json"
            readme = private_dir / "README.md"
            log.write_text('{"changed": true}\n')
            readme.write_text("old private readme\n")

            summary = init_validation_sprint.initialize_workspace(
                repo_root=root,
                refresh_readme=True,
                run_date="2026-05-21",
            )

            self.assertEqual(log.read_text(), '{"changed": true}\n')
            self.assertIn("make goal-resume DATE=2026-05-21", readme.read_text(encoding="utf-8"))
            self.assertIn(
                "BEGIN COPY-ONLY SEND TEXT",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "DO NOT SEND BELOW THIS LINE",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-team-update-save DATE=2026-05-21",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-send-copy DATE=2026-05-21",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "example_seed_log: true",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "seed counts are not real buyer traction",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "REPLACE_EXAMPLE_SEED=1",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Use `DATE` as the actual sanitized interview/log date.",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "a logged interview on 2026-05-23",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "make validation-draft-copy TARGET=target-dib-platform-004 DATE=2026-05-21",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "send_copy_state: ready",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "next_draft_matches_next_pending: true",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Send the copy-only text outside the repo only after that dry-run is clean",
                readme.read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "Optional: run `make validation-send-copy",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "same dated Make command with `CONFIRM_SENT=1`",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Normal confirmed raw writes require `--require-target-status",
                readme.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "interview seed replacement is stricter",
                readme.read_text(encoding="utf-8"),
            )
            self.assertNotIn("old private readme", readme.read_text(encoding="utf-8"))
            self.assertEqual(summary["written"], [str(readme)])
            self.assertEqual(len(summary["skipped_existing"]), 3)

    def test_force_overwrites_private_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "customer-validation-log.example.json").write_text('{"interviews": []}\n')
            (docs / "validation-targets.example.json").write_text('{"targets": []}\n')
            (docs / "customer-validation-interview.template.json").write_text('{"account_label": "example"}\n')
            init_validation_sprint.initialize_workspace(repo_root=root)
            target = root / "validation/private/customer-validation-log.json"
            target.write_text('{"changed": true}\n')

            init_validation_sprint.initialize_workspace(repo_root=root, force=True)

            self.assertEqual(target.read_text(), '{"interviews": []}\n')

    def test_rejects_bad_run_date(self) -> None:
        with self.assertRaisesRegex(
            init_validation_sprint.ValidationSprintInitError,
            "--date must be in YYYY-MM-DD form",
        ):
            init_validation_sprint.initialize_workspace(run_date="May 20")


if __name__ == "__main__":
    unittest.main()
