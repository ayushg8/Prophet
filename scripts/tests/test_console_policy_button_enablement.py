from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "prophet-console/src/App.tsx"
FORECAST_PANEL = ROOT / "prophet-console/src/components/ForecastPanel.tsx"
POLICY_PANEL = ROOT / "prophet-console/src/components/PolicyStatusPanel.tsx"
MASTER_TODO = ROOT / "docs/PROPHET_MASTER_TODO.md"


class ConsolePolicyButtonEnablementTests(unittest.TestCase):
    def test_source_refresh_button_is_bound_to_policy_gate(self) -> None:
        app = APP.read_text(encoding="utf-8")
        forecast_panel = FORECAST_PANEL.read_text(encoding="utf-8")
        policy_panel = POLICY_PANEL.read_text(encoding="utf-8")

        self.assertIn("type PolicyStatusReport", app)
        self.assertIn("sourceRefreshGateStatus(report", app)
        self.assertIn("gate.id === 'live_vm_scraper'", app)
        self.assertIn("setSourceRefreshStatus(sourceRefreshGateStatus(report))", app)
        self.assertIn("onReport={handlePolicyStatusReport}", app)
        self.assertIn("sourceRefreshGateStatus={sourceRefreshStatus}", app)

        self.assertIn("onReport?.(payload)", policy_panel)
        self.assertIn("onReport?.(null)", policy_panel)

        self.assertIn("sourceRefreshGateStatus?: 'unknown' | 'allowed' | 'blocked'", forecast_panel)
        self.assertIn("const sourceRefreshAllowed = sourceRefreshGateStatus === 'allowed'", forecast_panel)
        self.assertIn("disabled={scraperRunState === 'running' || !sourceRefreshAllowed}", forecast_panel)
        self.assertIn("Source refresh blocked", forecast_panel)
        self.assertIn("Policy blocks live source refresh", forecast_panel)

    def test_master_todo_marks_policy_bound_enablement_done(self) -> None:
        text = MASTER_TODO.read_text(encoding="utf-8")

        self.assertIn("- [x] Add policy-bound console button enablement.", text)
        self.assertIn("- [x] Add policy-blocked error states in the console.", text)


if __name__ == "__main__":
    unittest.main()
