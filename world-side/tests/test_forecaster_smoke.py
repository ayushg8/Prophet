from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forecaster.corpus import load_corpus_bundle
from forecaster.chatter import (
    ChatterValidationError,
    load_sanitized_chatter,
)
from forecaster.generator import assemble_forecast
from forecaster.loaders import load_cisa_kev, load_calendar_events
from forecaster.models import (
    ValidationError,
    validate_exploit_candidate,
    validate_world_forecast,
)


ROOT = Path(__file__).resolve().parents[2]
WORLD_SIDE = ROOT / "world-side"
FIXTURES = WORLD_SIDE / "fixtures"


class ForecasterSmokeTests(unittest.TestCase):
    def test_local_data_loads(self) -> None:
        kev = load_cisa_kev(ROOT / "kve.json")
        self.assertGreaterEqual(kev["count"], 1000)

        calendar = load_calendar_events(WORLD_SIDE / "data" / "calendar_events.md")
        self.assertGreaterEqual(len(calendar["events"]), 50)

        corpus = load_corpus_bundle(WORLD_SIDE / "data")
        self.assertEqual(len(corpus.historical_cases), 12)
        self.assertGreaterEqual(len(corpus.context_events), 100)

    def test_fixtures_validate(self) -> None:
        for path in sorted(FIXTURES.glob("exploit-candidate-*.json")):
            candidate = _load_json(path)
            validate_exploit_candidate(candidate)

    def test_generator_outputs_valid_forecasts(self) -> None:
        for path in sorted(FIXTURES.glob("exploit-candidate-*.json")):
            candidate = _load_json(path)
            forecast = assemble_forecast(
                candidate,
                generated_at="2026-05-02T23:45:00Z",
            )
            validate_world_forecast(forecast)
            self.assertEqual(forecast["schema_version"], "world_forecast.v0.1")
            self.assertGreaterEqual(len(forecast["strike_windows"]), 1)
            self.assertGreaterEqual(len(forecast["strike_vectors"]), 1)
            self.assert_source_coverage(forecast)
            self.assert_non_actionable(forecast)

    def test_sanitized_chatter_fixture_loads(self) -> None:
        records = load_sanitized_chatter(FIXTURES / "sanitized-chatter-sample.jsonl")
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].collection_tier, "public_chatter")
        self.assertIn("edge", records[0].tags)

    def test_generator_uses_sanitized_chatter(self) -> None:
        candidate = _load_json(FIXTURES / "exploit-candidate-edge-appliance.json")
        forecast = assemble_forecast(
            candidate,
            generated_at="2026-05-02T23:45:00Z",
            chatter_path=FIXTURES / "sanitized-chatter-sample.jsonl",
        )
        validate_world_forecast(forecast)
        source_ids = {source["id"] for source in forecast["source_refs"]}
        self.assertIn("src_context_chatter", source_ids)
        self.assertIn("src_chatter_fixture_001", source_ids)
        used = _used_source_ids(forecast)
        self.assertIn("src_chatter_fixture_001", used)
        self.assert_non_actionable(forecast)

    def test_chatter_validation_rejects_raw_material(self) -> None:
        bad_record = {
            "record_id": "bad_raw",
            "observed_at": "2026-05-02T22:20:00Z",
            "source_type": "telegram_public_channel",
            "collection_tier": "public_chatter",
            "confidence": "medium",
            "summary": "This record should fail.",
            "message_text": "raw post content should never cross the boundary",
            "source_ref": {
                "label": "Bad source",
                "url": "sanitized://scraper-record/bad_raw",
                "supports": "negative test",
            },
        }
        with self.assertRaises(ChatterValidationError):
            assemble_forecast(
                _load_json(FIXTURES / "exploit-candidate-edge-appliance.json"),
                generated_at="2026-05-02T23:45:00Z",
                chatter_records=[bad_record],
            )

    def test_chatter_validation_rejects_onion_addresses(self) -> None:
        bad_record = {
            "record_id": "bad_onion",
            "observed_at": "2026-05-02T22:20:00Z",
            "source_type": "onion_public_metadata",
            "collection_tier": "darkweb_metadata",
            "confidence": "low",
            "summary": "Metadata-only note with a forbidden source URL.",
            "source_ref": {
                "label": "Bad onion source",
                "url": "http://examplebadaddress.onion/path",
                "supports": "negative test",
            },
        }
        with self.assertRaises(ChatterValidationError):
            assemble_forecast(
                _load_json(FIXTURES / "exploit-candidate-edge-appliance.json"),
                generated_at="2026-05-02T23:45:00Z",
                chatter_records=[bad_record],
            )

    def test_cli_writes_forecast(self) -> None:
        candidate = FIXTURES / "exploit-candidate-edge-appliance.json"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "forecast.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "forecaster.cli",
                    "--candidate",
                    str(candidate),
                    "--generated-at",
                    "2026-05-02T23:45:00Z",
                    "--chatter",
                    str(FIXTURES / "sanitized-chatter-sample.jsonl"),
                    "--out",
                    str(out_path),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(WORLD_SIDE)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            forecast = _load_json(out_path)
            validate_world_forecast(forecast)
            self.assertEqual(forecast["input_candidate_id"], "cs-fixture-edge-appliance-001")
            self.assertIn(
                "src_context_chatter",
                {source["id"] for source in forecast["source_refs"]},
            )

    def test_vector_validation_rejects_actionable_fields(self) -> None:
        candidate = _load_json(FIXTURES / "exploit-candidate-edge-appliance.json")
        forecast = assemble_forecast(candidate, generated_at="2026-05-02T23:45:00Z")
        forecast["strike_vectors"][0]["procedure"] = ["do not allow this field"]
        with self.assertRaises(ValidationError):
            validate_world_forecast(forecast)

    def test_world_console_assets_exist_and_parse(self) -> None:
        app_dir = WORLD_SIDE / "app"
        index = app_dir / "index.html"
        script = app_dir / "app.js"
        styles = app_dir / "styles.css"
        for path in (index, script, styles):
            self.assertTrue(path.exists(), f"{path} should exist")

        html = index.read_text(encoding="utf-8")
        for element_id in (
            "statusStrip",
            "scoreRing",
            "regionGrid",
            "feedList",
            "forecastDetail",
        ):
            self.assertIn(element_id, html)

        source = script.read_text(encoding="utf-8")
        self.assertIn("Cyber Pressure Index", html)
        for phrase in (
            "worldmonitor_bootstrap_api",
            "sanitized-chatter-sample.jsonl",
            "golden-forecast-edge-appliance.json",
        ):
            self.assertIn(phrase, source)

        node = shutil.which("node")
        if node:
            proc = subprocess.run(
                [node, "--check", str(script)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def assert_source_coverage(self, forecast: dict) -> None:
        source_ids = {ref["id"] for ref in forecast["source_refs"]}
        used: set[str] = set()
        for window in forecast["strike_windows"]:
            used.update(window["source_ref_ids"])
            for analogy in window["historical_analogies"]:
                used.update(analogy["source_ref_ids"])
        for vector in forecast["strike_vectors"]:
            used.update(vector["source_ref_ids"])
        self.assertFalse(used - source_ids)

    def assert_non_actionable(self, forecast: dict) -> None:
        banned_keys = {
            "payload",
            "procedure",
            "exploit_steps",
            "target_control_steps",
            "command",
            "commands",
            "credentials",
            "ip_address",
            "named_live_targets",
        }
        for vector in forecast["strike_vectors"]:
            self.assertFalse(banned_keys & set(vector))
            mechanism = vector["non_actionable_mechanism"].lower()
            for phrase in ("curl ", "powershell", "ssh ", "password", "run "):
                self.assertNotIn(phrase, mechanism)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def _used_source_ids(forecast: dict) -> set[str]:
    used: set[str] = set()
    for window in forecast["strike_windows"]:
        used.update(window["source_ref_ids"])
        for analogy in window["historical_analogies"]:
            used.update(analogy["source_ref_ids"])
    for vector in forecast["strike_vectors"]:
        used.update(vector["source_ref_ids"])
    return used


if __name__ == "__main__":
    unittest.main()
