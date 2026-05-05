# Prophet CLI Safety Matrix

Last updated: 2026-05-05

This matrix defines the no-live-target guardrail for local buyer-pilot CLIs.
It covers command surfaces that accept mutable operator, customer, policy,
source, forecast, sandbox, evidence, or export input.

Run the guard suite with:

```bash
PYTHONPATH=.:cyber-side:world-side:world-side/scraper python3 -m unittest scripts.tests.test_cli_no_live_targets -v
```

## Covered Buyer-Pilot CLIs

| CLI | Guard exercised |
|---|---|
| `python3 -m assets.import_csv` | Rejects hostname-like customer asset rows before sanitized inventory output. |
| `python3 -m assets.inventory` | Rejects live-IP-like text in inventory JSON before seedset generation. |
| `python3 -m forecaster.cli` | Rejects Direction A candidate files with live-target keys before forecast generation. |
| `python3 -m scraper_side.cli` | Rejects live collection for unapproved hosts before any network request. |
| `python3 -m scraper_side.snapshot` | Rejects `--live` when the pilot policy is supplied. |
| `python3 -m predictor` | Rejects portfolio validation input containing live-target keys. |
| `python3 -m sandbox_runner` | Rejects non-fixture sandbox mode unless explicitly gated, and still has no packaged public container mode. |
| `python3 -m evidence.audit` | Rejects unsafe operator labels and keeps approval event outputs under ignored `outputs/runtime` paths. |
| `python3 -m evidence.bundle` | Rejects evidence output paths outside `evidence/outputs/runtime/`. |
| `python3 -m integrations.export` | Rejects handoff exports that the supplied policy does not allow. |
| `python3 -m policy.lint` | Rejects policies with `live_targets_allowed` enabled. |
| `python3 -m policy.retention` | Rejects retention runs under policies with `live_targets_allowed` enabled. |

## Related Release Utilities

`scripts/check-release-safety.py` is covered by
`scripts/tests/test_check_release_safety.py`, including unsafe IP, secret,
runtime artifact, source-catalog allowlist, and console live-action policy-gate
checks.

`scripts/diff-pilot-demo-fixtures.py` and
`scripts/verify-pilot-demo-hashes.py` read deterministic fixture/hash inputs and
do not accept target-control, live host, credential, or network collection
parameters.
