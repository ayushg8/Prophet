# Prophet

Prophet is an anticipatory cyber defense system for mission owners who cannot
wait for the next CISA KEV entry to become urgent. It fuses geopolitical
pressure, historical campaign patterns, KEV/EPSS context, and safe sandbox
validation into one operator workflow:

```text
forecast the window -> rank the likely exploit class -> generate the defense -> validate the block
```

The product claim is deliberately narrow: Prophet does not discover new
zero-days and does not target live infrastructure. It predicts which
vulnerability class deserves defensive priority, then produces patch and
detection artifacts that can be reviewed, tested, and shipped by an operator.

## Why This Exists

Federal and defense networks are structurally reactive. By the time a CVE is
added to KEV, some entries were already exploited before or on disclosure day.
Prophet moves the decision point earlier: when strategic pressure rises, it
helps defenders decide which exposure class to harden first.

For defense-tech buyers, the wedge is not another scanner. The wedge is a
closed defensive loop:

- **When**: strike windows from geopolitical and historical context.
- **How**: likely strike vectors mapped to sector-level exposure.
- **What**: exploit-class portfolio, not operational payloads.
- **So what**: generated patch and Sigma rule, validated in a sandbox.

## Current Working Surfaces

| Surface | Status | Notes |
|---|---|---|
| Forecaster | Working | Deterministic Python; no runtime LLM or external API dependency. |
| Asset import | Working | Imports customer-safe CSV metadata with row-level cleanup reports and optional seedsets. |
| Asset-seeded OSINT | Working | Generates safe metadata seedsets and policy-gated fixture-backed public-source snapshots. |
| Contract validators | Working | Reject payloads, credentials, live targets, procedural instructions, and schema drift. |
| Prediction portfolio | Working | Produces safe 5+5 exploit-class portfolio for demo and analyst review. |
| Sandbox runner | Working | Deterministic localhost fixture artifact for the edge-appliance profile. |
| Evidence export | Working | Generates policy-bound JSON + Markdown evidence bundles from validated fixtures. |
| Integration handoff | Working | Exports safe SIEM and ticketing review templates from validated evidence. |
| Policy linting | Working | Validates customer pilot policies, allowed modes, source IDs, sandbox profiles, blocked controls, and runtime output paths. |
| React operator console | Working | Fixture-backed end-to-end replay with human gate, defense artifact, and validation status. |
| Local control server | Working | Serves sanitized demo refresh and fixture artifacts on localhost. |
| Live scraper VM | Disabled by default | Requires `PROPHET_ENABLE_VM_SCRAPER=1` and an approved isolated collection plan. |
| Live exploit engine | Contracted, not packaged | Public repo includes the interface and fixtures; production engine remains a gated integration. |

## Architecture

```text
             sanitized public context
                      |
                      v
          +-----------------------+
          | Forecaster            |
          | world-side/           |
          | deterministic Python  |
          +----------+------------+
                     |
                     | world_forecast.v0.1
                     v
          +-----------------------+
          | Exploit-Class Layer   |
          | cyber-side/           |
          | safe portfolio +      |
          | artifact validator    |
          +----------+------------+
                     |
                     | exploit_engine_artifact.v0.1
                     v
          +-----------------------+
          | Operator Console      |
          | prophet-console/      |
          | React + Vite          |
          +-----------------------+
```

The contracts are the product boundary:

- `world-side/INTERFACE.md`: candidate and forecast schemas.
- `cyber-side/INTERFACE.md`: defense artifact schema.
- `cyber-side/validator.py`: payload and live-target rejection.
- `world-side/forecaster/models.py`: forecast safety and schema validation.

## Quickstart

### Three-Minute Evaluator Path

Use this when an evaluator wants to prove the defensive pilot loop from a fresh
clone without reading code or enabling live collection.

Prerequisites:

- Python 3.11 or newer.
- Bash-compatible shell.
- Optional for console review: Node 24 and npm.

From the repo root:

```bash
./scripts/run-pilot-demo-smoke.sh
```

Expected result:

- The pilot policy lints successfully.
- Safe asset import, seeded OSINT, forecast refresh, sandbox validation,
  evidence export, audit export, retention reporting, and SIEM/ticketing
  handoff export all complete.
- The final hash check matches `scripts/pilot-demo-smoke.sha256`.
- Runtime policy-hash drift checks pass for the generated evidence, OSINT,
  sandbox, audit, and integration artifacts.
- Outputs stay under ignored `*/outputs/runtime/` directories.

The smoke path is fixture-backed, policy-bound, and localhost-only. It does not
contact live targets, generate payloads, read credentials, or require private
hostnames.

For a customer-facing evaluation path, start with
`docs/EVALUATOR_START_HERE.md` and record findings in
`docs/EVALUATOR_WORKSHEET.md`. Operators should use
`docs/DEMO_OPERATOR_CHECKLIST.md` before a live buyer review, and non-cyber
reviewers can use `docs/GLOSSARY.md` for terminology. For a deeper analyst
review, use `docs/ANALYST_WALKTHROUGH.md`. For local setup failures, use
`docs/PILOT_TROUBLESHOOTING.md`.

After the smoke run, inspect:

- `evidence/outputs/runtime/latest-edge-appliance.md`
- `evidence/outputs/runtime/latest-edge-appliance.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-retention.json`
- `integrations/outputs/runtime/latest-edge-appliance/manifest.json`

### Internal Acceptance

Run the full internal-alpha acceptance path from the console package:

```bash
cd prophet-console
npm run acceptance
```

The acceptance command runs the root pilot smoke, console lint/build,
control-server evidence/readiness smoke, and Playwright browser smoke.

### Focused Contract Checks

Run the contract slices directly:

```bash
PYTHONPATH=. python3 -m unittest discover -s policy/tests -v
PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v
PYTHONPATH=cyber-side python3 -m predictor --validate-only \
  --forecast cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json
```

Import a safe customer-owned asset CSV fixture:

```bash
PYTHONPATH=. python3 -m assets.import_csv \
  --csv assets/fixtures/dib-edge-appliance-inventory.csv \
  --inventory-id customer-safe-import \
  --scope "Customer-owned product-family metadata; no live targets named." \
  --generated-at 2026-05-05T08:00:00Z \
  --fixture \
  --out assets/outputs/runtime/customer-safe-inventory.json \
  --report-out assets/outputs/runtime/customer-safe-import-report.json \
  --seedset-out assets/outputs/runtime/customer-safe-seedset.json
```

Lint the packaged pilot policy or a customer-specific policy before a demo:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
```

See `docs/ASSET_IMPORT_GUIDE.md` and `docs/PILOT_POLICY_REVIEW.md` for the
customer CSV and policy review contracts.

Generate the pilot evidence bundle:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.bundle \
  --forecast world-side/outputs/golden-forecast-edge-appliance.json \
  --portfolio cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json \
  --artifact cyber-side/fixtures/exploit-engine-output-edge-appliance.json \
  --asset-inventory assets/fixtures/dib-edge-appliance-inventory.json \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --policy policy/prophet-pilot-policy.json \
  --operator-label fixture \
  --approval-decision bypassed_for_fixture \
  --out-json evidence/outputs/runtime/latest-edge-appliance.json \
  --out-md evidence/outputs/runtime/latest-edge-appliance.md
```

Run the operator console:

```bash
cd prophet-console
npm ci
npm run dev
```

Optional local-only control server for fixture refresh and artifact loading:

```bash
cd prophet-console
npm run dev:control
```

Read-only readiness probe:

```bash
curl http://127.0.0.1:8787/api/readiness
```

Open `http://127.0.0.1:5173`, enter the console, use **Refresh demo**, load the
defense fixture, generate the evidence bundle, export the handoff templates, and
check **Alpha Readiness**.

## Safety Model

Prophet should be sold and evaluated as a defensive decision and validation
system, not an exploit-delivery system.

- No live infrastructure testing from the public console.
- No raw scraper output crosses into the main app.
- No credentials, IPs, or operational hostnames in committed artifacts.
- No payload bytes in accepted JSON contracts.
- Policy-gated OSINT snapshots can use only approved source IDs, and
  `sandbox_runner` can use only approved profiles.
- VM scraping is disabled unless explicitly enabled with
  `PROPHET_ENABLE_VM_SCRAPER=1`.
- Production validation must run only in approved, isolated, vulnerable-by-design
  sandboxes.

See `SECURITY.md` for operating rules.

## Commercial Path

The credible first product is a **Defensive Exposure Prioritization Copilot**:

1. Ingest approved public and customer-owned context.
2. Forecast pressure windows and likely exposure classes.
3. Generate a reviewable defense package: patch guidance, Sigma/YARA/SIEM logic,
   test plan, and audit record.
4. Validate only in a customer-approved sandbox or digital twin.
5. Export an evidence bundle for security leadership, mission owners, and
   compliance teams.

Near-term integrations should focus on defensive systems: SBOM/asset inventory,
SIEM, ticketing, vulnerability management, and sandbox orchestration. Offensive
or live-target integrations should stay out of the default product.

Production-readiness planning is tracked in:

- `docs/PRODUCTION_EXECUTION_PLAN.md`
- `docs/PRODUCTION_ARCHITECTURE.md`
- `docs/THREAT_MODEL.md`
- `docs/COMPLIANCE_GAP_MAP.md`
- `docs/production-readiness-backlog.json`

Generate the current production readiness scorecard with:

```bash
python3 scripts/production-readiness-scorecard.py
```

Before adding more production-platform scope, run the product validation track:

- `docs/PRODUCT_VALIDATION_PLAN.md`
- `docs/CUSTOMER_DISCOVERY_GUIDE.md`
- `docs/OUTREACH_PLAYBOOK.md`
- `docs/DESIGN_PARTNER_PILOT_OFFER.md`

Score anonymized discovery evidence with:

```bash
python3 scripts/customer-validation-scorecard.py --log docs/customer-validation-log.example.json
```

## Repository Map

```text
world-side/       Forecaster, source sanitization, deterministic outputs
cyber-side/       Safe exploit-class portfolio, artifact contract, validators
evidence/         JSON + Markdown evidence bundle generator and validator
integrations/     SIEM, ticketing, and audit handoff exporters
assets/           Fictional asset/SBOM inventory fixtures
sandbox_runner/   Deterministic local sandbox simulation runner
prophet-console/  React operator console and localhost control server
intel/            KEV seed data
research/         Demo candidate notes
docs/             Productization and safety notes
```

Lab-only exploit validation scaffolding is not part of the public product tree.
It belongs in a private research repo or local archive outside this repository;
see `docs/RESEARCH_LAB_POLICY.md`.
