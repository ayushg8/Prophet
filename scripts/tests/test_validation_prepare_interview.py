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
SCRIPT = ROOT / "scripts" / "validation-prepare-interview.py"
TARGETS_EXAMPLE = ROOT / "docs" / "validation-targets.example.json"
LOG_EXAMPLE = ROOT / "docs" / "customer-validation-log.example.json"
SPEC = importlib.util.spec_from_file_location("validation_prepare_interview", SCRIPT)
assert SPEC and SPEC.loader
prepare_interview = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_interview
SPEC.loader.exec_module(prepare_interview)

SCORECARD_SPEC = importlib.util.spec_from_file_location(
    "customer_validation_scorecard",
    ROOT / "scripts" / "customer-validation-scorecard.py",
)
assert SCORECARD_SPEC and SCORECARD_SPEC.loader
scorecard = importlib.util.module_from_spec(SCORECARD_SPEC)
sys.modules[SCORECARD_SPEC.name] = scorecard
SCORECARD_SPEC.loader.exec_module(scorecard)


class ValidationPrepareInterviewTests(unittest.TestCase):
    def test_prepares_incomplete_interview_from_booked_target(self) -> None:
        targets = _booked_targets()

        interview, summary = prepare_interview.prepare_interview_template(
            targets,
            target_label="target-dib-platform-001",
        )

        self.assertTrue(summary["ok"])
        self.assertEqual(interview["account_label"], "target-dib-platform-001")
        self.assertEqual(interview["segment"], "dib_platform_security")
        self.assertEqual(interview["persona"], "director_product_security")
        self.assertEqual(interview["qualified"], False)
        self.assertEqual(interview["current_workflow"], "")
        self.assertEqual(interview["existing_tools"], [])
        self.assertEqual(interview["pain_score"], 0)
        self.assertIn("workflow_pain_theme", summary["fields_to_fill"])
        self.assertIn("intentionally incomplete", summary["note"])

    def test_starter_fails_log_validation_until_filled(self) -> None:
        targets = _booked_targets()
        interview, _summary = prepare_interview.prepare_interview_template(
            targets,
            target_label="target-dib-platform-001",
        )
        log = json.loads(LOG_EXAMPLE.read_text(encoding="utf-8"))
        log = copy.deepcopy(log)
        log["interviews"] = [interview]

        errors = scorecard.validate_log(log)

        self.assertTrue(any("current_workflow is required" in error for error in errors))
        self.assertTrue(any("existing_tools must be non-empty list" in error for error in errors))
        self.assertTrue(any("pain_score must be integer 1-5" in error for error in errors))

    def test_rejects_unbooked_target_by_default(self) -> None:
        targets = json.loads(TARGETS_EXAMPLE.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(
            prepare_interview.ValidationPrepareInterviewError,
            "current status",
        ):
            prepare_interview.prepare_interview_template(
                targets,
                target_label="target-dib-platform-001",
            )

    def test_cli_writes_private_starter_and_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            targets_path = Path(tmp) / "targets.json"
            out_path = Path(tmp) / "customer-validation-interview-next.json"
            targets_path.write_text(json.dumps(_booked_targets()), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--targets",
                    str(targets_path),
                    "--target-label",
                    "target-dib-platform-001",
                    "--date",
                    "2026-05-12",
                    "--out",
                    str(out_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(completed.stdout)
            written = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["out"], str(out_path))
            self.assertEqual(
                summary["log_dry_run_command"],
                "make validation-log-interview DATE=2026-05-12",
            )
            self.assertEqual(written["account_label"], "target-dib-platform-001")
            self.assertEqual(written["status_quo_gap"], "")


def _booked_targets() -> dict[str, object]:
    targets = json.loads(TARGETS_EXAMPLE.read_text(encoding="utf-8"))
    targets = copy.deepcopy(targets)
    targets["targets"][0]["status"] = "call_booked"
    targets["targets"][0]["last_touch"] = "2026-05-11"
    targets["targets"][0]["follow_up_due"] = ""
    targets["targets"][0]["next_action"] = "Prepare discovery call."
    return targets


if __name__ == "__main__":
    unittest.main()
