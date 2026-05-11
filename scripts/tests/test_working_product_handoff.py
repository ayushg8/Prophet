from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "working-product-handoff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("working_product_handoff", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load working-product-handoff.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkingProductHandoffTests(unittest.TestCase):
    def test_render_handoff_names_current_ports_and_closed_build_gate(self) -> None:
        module = _load_module()
        dashboard = {
            "build_gate": {
                "allowed_to_build_next_slice": False,
                "reason": "real buyer validation has not proven enough pull",
            },
            "customer_validation": {
                "verdict": "insufficient_data",
                "gaps_to_verdicts": {
                    "build_next_slice": {
                        "qualified_count": 15,
                        "high_pain_count": 8,
                    }
                },
            },
            "target_backed_validation": {"verdict": "insufficient_data"},
            "outreach_execution": {
                "counts": {"pending_send_or_update": 8, "needs_attention": 0},
                "dry_run_verified_count": 8,
                "send_copy_state": "ready",
                "send_copy_batch_state": "ready",
                "contact_form_copy_state": "ready",
                "next_pending_target_label": "target-dib-platform-001",
                "next_pending_pre_send_check_command": (
                    "make validation-pre-send-check "
                    "TARGET=target-dib-platform-001 DATE=2026-05-11"
                ),
                "send_copy_path": "validation/private/today-send-copy.txt",
                "next_pending_confirmed_apply_command": (
                    "make validation-apply-draft "
                    "TARGET=target-dib-platform-001 DATE=2026-05-11 CONFIRM_SENT=1"
                ),
            },
        }

        rendered = module.render_handoff(
            dashboard,
            run_date="2026-05-11",
            ui_url="http://127.0.0.1:5291/",
            readiness_url="http://127.0.0.1:8891/api/readiness",
            handoff_command=(
                "PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 "
                "make validation-working-product-handoff-save DATE=2026-05-11"
            ),
            live_check_command=(
                "PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 "
                "make console-live-check"
            ),
            git_branch="main",
            git_head_short="abc1234",
            git_head_full="abc123456789",
            git_worktree_state="clean",
            readiness={"checked": True, "ok": True, "blocking_failures": 0},
        )

        self.assertIn("http://127.0.0.1:5291/", rendered)
        self.assertIn("http://127.0.0.1:8891/api/readiness", rendered)
        self.assertIn("PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291", rendered)
        self.assertIn("make validation-working-product-handoff-save DATE=2026-05-11", rendered)
        self.assertIn("Customer validation verdict: `insufficient_data`", rendered)
        self.assertIn("Target-backed validation verdict: `insufficient_data`", rendered)
        self.assertIn("`allowed_to_build_next_slice`: `false`", rendered)
        self.assertIn("Do not add production platform scope", rendered)
        self.assertIn("Do not run `CONFIRM_SENT=1`", rendered)

    def test_live_check_command_uses_default_or_explicit_ports(self) -> None:
        module = _load_module()

        self.assertEqual(module._live_check_command(8787, 5173), "make console-live-check")
        self.assertEqual(
            module._live_check_command(8891, 5291),
            "PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 make console-live-check",
        )
        self.assertEqual(
            module._handoff_command(8891, 5291, "2026-05-11"),
            "PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 "
            "make validation-working-product-handoff-save DATE=2026-05-11",
        )


if __name__ == "__main__":
    unittest.main()
