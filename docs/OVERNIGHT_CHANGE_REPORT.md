# Overnight Change Report

Last updated: 2026-05-05

Historical context: this report summarizes the May 2026 overnight GStack loop
and its consolidation work. For current product direction, use
`docs/CODEX_CEO_FINISH_BRIEF.md`, `docs/PROPHET_COMPLETION_AUDIT.md`,
`docs/PROPHET_TODO.md`, and the validation dashboard as the source of truth.
Do not use this report as authorization for production platform work while
customer validation remains `insufficient_data`.

This report summarizes the autonomous Prophet GStack loop and the consolidation
work required before the repo can be treated as a pilot release candidate.

## Loop Result

- Started: 2026-05-04 22:53 PDT.
- Finished: 2026-05-05 02:32 PDT.
- Configured run: `--hours 8 --sleep-seconds 60 --max-cycles 40`.
- Stop reason: reached `max_cycles=40`.
- Cycle count: 40.
- Cycle statuses: 40 exited `0`.
- Runtime logs: `evidence/outputs/runtime/gstack-overnight-loop/`.
- GStack timeline final event: `prophet-overnight-loop completed [finished]`.

## High-Level Delivery

The overnight loop moved Prophet from a single-scenario pilot package toward a
multi-scenario, policy-bound evaluator package. The biggest additions are:

- Default and customer policy schema/comparison/retention work.
- Evidence bundle schema and audit export/retention work.
- Sandbox artifact and sandbox run manifest schemas.
- Release safety checks and CLI live-target guardrail tests.
- Console policy/readiness/evidence/integration surface hardening.
- Buyer-facing evaluator docs, operator checklist, glossary, and walkthroughs.
- A second fixture-backed buyer smoke sector: `financial-workflow`.

## Changed Areas

### Safety And Release Hygiene

- Runtime output directories remain ignored.
- Release safety scanning was added under `scripts/`.
- A pre-commit hook was added under `.githooks/`.
- Lab exploit/demo files remain deleted from the public product tree.
- Documentation now emphasizes fixture-backed, non-live, defensive evaluation.

### Assets And Seedsets

- Added fictional DIB edge-appliance inventory fixtures.
- Added fictional financial-workflow inventory fixtures.
- Added CSV customer-safe import path and row-level import reporting.
- Added asset/SBOM seedset generation and tests.

### Policy

- Added default pilot policy and narrower example policies.
- Added policy linter, policy comparison, policy schema, source allowlists, and
  retention handling.
- Added policy tests for unsafe modes, duplicate values, retention, comparison,
  and schema behavior.

### Evidence And Audit

- Added evidence bundle generation and validation.
- Added evidence JSON Schema.
- Added local hash-chained audit events.
- Added audit export and retention reporting/cleanup support.
- Added validation that evidence and handoff outputs remain safe and
  policy-bound.

### Sandbox

- Added deterministic sandbox runner profile support.
- Added sandbox artifact schema.
- Added sandbox run manifest schema.
- Added negative defense-failed fixture path.
- Added financial-workflow sandbox artifact fixture.

### OSINT And Forecasting

- Added fixture-backed seeded OSINT snapshot support.
- Added source catalog entries and schema extensions.
- Added OSINT freshness/source failure evidence.
- Added forecast enrichment from asset and seeded OSINT context.

### Integrations

- Added SIEM/ticketing handoff exports.
- Added Splunk, Elastic, Sentinel, Jira, ServiceNow, and operator audit review
  templates.
- Added export validation and manifest hashing.

### Console

- Added evidence, integration, readiness, and policy status surfaces.
- Added control evidence smoke and Playwright smoke.
- Added policy-blocked action state work.
- Added safety/readiness contract checks.

### CI And Tests

- Added GitHub CI workflows for Python, console, browser smoke, and dependency
  audit.
- Added script tests for release safety, live-target guardrails, and fixture
  diffing.
- Added hash manifests for edge-appliance and financial-workflow smoke paths.

### Docs

- Added evaluator start-here guide, worksheet, demo operator checklist,
  troubleshooting, glossary, analyst walkthrough, technical validation
  walkthrough, buyer FAQ, pilot scope, commercial readiness, safety
  architecture, integration handoff guide, release checklist, and master TODO.

## Verification Performed During Consolidation

- `git diff --check`: passed.
- `bash -n scripts/run-pilot-demo-smoke.sh
  scripts/prophet-overnight-gstack-loop.sh scripts/run-policy-blocked-demo.sh`:
  passed.
- `PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v`:
  19 tests passed.
- `PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s
  world-side/tests -v`: 24 tests passed.
- `PYTHONPATH=. python3 -m unittest discover -s assets/tests -v`: 18 tests
  passed.
- `PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests
  -v`: 10 tests passed.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s
  policy/tests -v`: 26 tests passed.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s
  evidence/tests -v`: 56 tests passed.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s
  integrations/tests -v`: 7 tests passed.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s
  scripts/tests -v`: 34 tests passed.
- `./scripts/run-pilot-demo-smoke.sh`: passed.
- `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`: passed.
- `cd prophet-console && npm run lint`: passed.
- `cd prophet-console && npm run build`: passed with Vite's existing chunk-size
  warning for the main bundle.
- `cd prophet-console && npm run test:control:evidence`: passed.
- `cd prophet-console && npm run test:smoke`: 2 Playwright tests passed.
- `cd prophet-console && npm run acceptance`: passed, including edge smoke,
  lint, build, control evidence smoke, and Playwright smoke.
- `cd prophet-console && npm audit --audit-level=moderate`: passed with 0
  vulnerabilities.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py
  --tracked`: passed across 131 tracked paths.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py
  $( { git diff --name-only --diff-filter=ACMR; git ls-files --others
  --exclude-standard; } | sort -u )`: passed across 151 changed/untracked paths.

## Post-Commit Validation

After commit shaping on branch `prophet-pilot-consolidation-2026-05-05`:

- `git status --short --untracked-files=all`: clean.
- `git diff --check`: passed.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py
  --tracked`: passed across 245 tracked paths.
- Full Python matrix passed: 19 cyber, 24 world-side, 18 assets, 10 sandbox,
  26 policy, 56 evidence, 7 integrations, and 34 scripts tests.
- `./scripts/run-pilot-demo-smoke.sh`: passed.
- `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`: passed.
- `cd prophet-console && npm run acceptance`: passed.
- `cd prophet-console && npm audit --audit-level=moderate`: passed with 0
  vulnerabilities.
- GStack timeline event was logged for consolidation completion.

## Fresh-Clone Validation

Fresh-clone validation was run on 2026-05-05 in
`/tmp/prophet-fresh-7W5S0V/Prophet` at commit
`bddce65fd02403461609c7f6076848526aeb728b`.

- `./scripts/run-pilot-demo-smoke.sh`: passed.
- `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`: passed.
- `cd prophet-console && npm ci`: passed from the lockfile.
- `cd prophet-console && npm run acceptance`: passed, including Playwright
  browser smoke with 2 tests passed.
- `cd prophet-console && npm audit --audit-level=moderate`: passed with 0
  vulnerabilities.
- `git diff --check`: passed.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py
  --tracked`: passed across 245 tracked paths.
- Fresh-clone `git status --short --untracked-files=all`: clean after generated
  runtime outputs, Playwright reports, and console build artifacts were ignored.
- GStack devex-review timeline event was logged for the fresh-clone pass.

## Remediation During Consolidation

- Added missing policy provenance to
  `world-side/fixtures/osint-snapshot-sample.manifest.json` after the changed-file
  safety scan caught a missing `policy.policy_sha256`.
- Removed private lab IP literals from `prophet-console/src/lib/sanitize.ts`;
  the generic IP redaction rules still cover those values without checking in
  the values themselves.
- Excluded the checked-in public CISA KEV feed `kve.json` from unsafe text
  scanning because version strings in that public catalog are expected to look
  like IPv4 literals.

## Local Commit Map

1. `13f16a8` - Remove lab exploit scaffolding from public tree.
2. `347d1f0` - Add safe asset inventory seedsets.
3. `3263e82` - Add seeded OSINT forecast context.
4. `4fa99dc` - Add pilot policy controls.
5. `cdd8e34` - Add deterministic sandbox runner workflow.
6. `4987893` - Add policy-bound evidence bundles.
7. `17952de` - Add safe integration handoff exports.
8. `d00e619` - Harden console evidence workflow.
9. `e1b1551` - Add pilot CI and smoke gates.
10. `0357cc0` - Document buyer pilot package.

## Known Open Gaps

- Console does not yet expose a full sector selector for `financial-workflow`.
- Production SaaS gaps remain: RBAC, SSO, tenant isolation, production secrets,
  deployment runbooks, and production retention automation.
- No push has been made yet for the overnight work.
