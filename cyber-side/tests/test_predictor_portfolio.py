from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from predictor import (
    PortfolioValidationError,
    generate_prediction_portfolio,
    main,
    validate_prediction_portfolio,
)


ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "world-side" / "outputs" / "generated-forecast-edge-appliance-with-chatter.json"
FINANCIAL_FORECAST = ROOT / "world-side" / "outputs" / "golden-forecast-financial-theft.json"
CANDIDATE = ROOT / "world-side" / "fixtures" / "exploit-candidate-edge-appliance.json"
FINANCIAL_CANDIDATE = ROOT / "world-side" / "fixtures" / "exploit-candidate-financial-theft.json"
FIXTURE = ROOT / "cyber-side" / "fixtures" / "predicted-exploit-portfolio-edge-appliance.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


class PredictorPortfolioTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        validate_prediction_portfolio(_load(FIXTURE))

    def test_generates_five_zero_day_and_five_one_day_predictions(self) -> None:
        portfolio = generate_prediction_portfolio(
            _load(FORECAST),
            _load(CANDIDATE),
            generated_at="2026-05-03T06:15:00Z",
        )

        self.assertEqual(len(portfolio["zero_day_predictions"]), 5)
        self.assertEqual(len(portfolio["one_day_predictions"]), 5)
        self.assertEqual(
            portfolio["strike_context"]["strike_vector"],
            "edge-appliance initial access and pre-positioning",
        )

    def test_generates_financial_workflow_predictions(self) -> None:
        portfolio = generate_prediction_portfolio(
            _load(FINANCIAL_FORECAST),
            _load(FINANCIAL_CANDIDATE),
            generated_at="2026-05-04T20:30:00Z",
        )

        validate_prediction_portfolio(portfolio)
        self.assertEqual(len(portfolio["zero_day_predictions"]), 5)
        self.assertEqual(len(portfolio["one_day_predictions"]), 5)
        self.assertIn(
            "financial workflow",
            portfolio["zero_day_predictions"][0]["exploit_class_label"],
        )
        self.assertEqual(
            portfolio["strike_context"]["strike_vector"],
            "financial-messaging or custody workflow compromise",
        )

    def test_each_prediction_has_sources_and_defense_primitive(self) -> None:
        portfolio = _load(FIXTURE)
        predictions = portfolio["zero_day_predictions"] + portfolio["one_day_predictions"]

        for prediction in predictions:
            with self.subTest(prediction=prediction["prediction_id"]):
                self.assertGreaterEqual(len(prediction["source_refs"]), 2)
                self.assertLessEqual(len(prediction["source_refs"]), 3)
                self.assertIn("patch_focus", prediction["defense_primitive"])
                self.assertIn("detection_focus", prediction["defense_primitive"])
                self.assertIn("localhost", prediction["defense_primitive"]["sandbox_note"].lower())

    def test_rejects_banned_keys(self) -> None:
        portfolio = _load(FIXTURE)
        portfolio["zero_day_predictions"][0]["payload"] = "blocked"

        with self.assertRaises(PortfolioValidationError):
            validate_prediction_portfolio(portfolio)

    def test_rejects_payload_like_text(self) -> None:
        portfolio = _load(FIXTURE)
        portfolio["zero_day_predictions"][0]["non_actionable_rationale"] += " ${jndi:x}"

        with self.assertRaises(PortfolioValidationError):
            validate_prediction_portfolio(portfolio)

    def test_cli_writes_valid_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "portfolio.json"
            code = main(
                [
                    "--forecast",
                    str(FORECAST),
                    "--candidate",
                    str(CANDIDATE),
                    "--generated-at",
                    "2026-05-03T06:15:00Z",
                    "--out",
                    str(out),
                ]
            )

            self.assertEqual(code, 0)
            validate_prediction_portfolio(_load(out))


if __name__ == "__main__":
    unittest.main()
