# Prophet Gstack Worklog

Historical context: this worklog records earlier gstack cycles and recovered
planning context. Use `docs/CODEX_CEO_FINISH_BRIEF.md`,
`docs/PROPHET_COMPLETION_AUDIT.md`, `docs/PROPHET_TODO.md`, and the validation
dashboard as the current source of truth. Do not treat old worklog entries as
permission to build production scope while customer validation remains
`insufficient_data`.

## 2026-05-05 Overnight Loop

### Buyer Operator Docs Cycle

Intent:

- Make the buyer review easier to run without changing the fixture-backed pilot
  behavior or widening the safety boundary.

Completed:

- Added `docs/DEMO_OPERATOR_CHECKLIST.md` with preflight commands, pass
  conditions, console setup, talk track, artifact checkpoints, stop gates, and
  after-review handling.
- Added `docs/GLOSSARY.md` with buyer-facing definitions for Prophet terms and
  preferred language.
- Linked both docs from the root README, evaluator start page, and pilot demo
  guide.
- Marked only the matching demo-operator-checklist and non-cyber-glossary TODOs
  complete in the operational and master TODO boards.

Verification:

- `python3 scripts/check-release-safety.py --paths README.md docs/EVALUATOR_START_HERE.md docs/PILOT_DEMO.md docs/DEMO_OPERATOR_CHECKLIST.md docs/GLOSSARY.md docs/PROPHET_TODO.md docs/PROPHET_MASTER_TODO.md`:
  pass.
- `git diff --check`: pass.
- Touched-file trailing whitespace scan: pass.

### Root Evaluator README Cycle

Intent:

- Give buyer evaluators a direct root-level path from clone to policy-bound
  evidence without requiring them to find the deeper pilot docs first.

Completed:

- Tightened the root `README.md` quickstart into an explicit 3-minute
  evaluator path with prerequisites, expected pass conditions, safety boundary,
  and exact generated evidence/audit/integration files to inspect.
- Updated the operational TODO ground truth to call out the root README
  evaluator path.
- Marked only the matching master backlog README/documentation-map items
  complete.

Verification:

- `python3 scripts/check-release-safety.py --paths README.md docs/PROPHET_MASTER_TODO.md docs/PROPHET_TODO.md`:
  pass.
- Touched-file trailing whitespace scan: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 23 pilot demo hashes and
  passed runtime policy-hash drift verification.

### Runtime Retention Enforcement Cycle

Intent:

- Extend retention enforcement beyond the hash-chained audit log so buyer
  reviewers can verify runtime-output and customer-metadata cleanup posture.

Completed:

- Added `policy.retention` to report policy-bound retention for known
  `*/outputs/runtime/` artifacts without embedding raw artifact bodies.
- Classified `assets/outputs/runtime/` artifacts as customer metadata so they
  use `retention.customer_metadata_max_days`; other managed runtime files use
  `retention.runtime_outputs_max_days`.
- Kept operator audit-log deletion delegated to `evidence.audit retention` to
  avoid partial hash-chain pruning.
- Added explicit confirmation-gated deletion for expired managed runtime files,
  validation for the retention report, policy-drift support for the new report
  schema, focused unit tests, and policy-review docs.
- Marked only the matching runtime/customer metadata retention TODO complete.

Verification:

- `python3 -m py_compile policy/retention.py policy/lint.py`: pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest policy.tests.test_policy_retention -v`:
  pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest policy.tests.test_policy_lint -v`:
  pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v`:
  pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m policy.retention --policy policy/prophet-pilot-policy.json --generated-at 2026-05-05T00:00:00Z --out-json evidence/outputs/runtime/pilot-demo-runtime-retention.json`:
  pass; report validated 232 runtime files, with 5 customer-metadata artifacts
  and 6 audit logs delegated to audit retention.
- `PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint --policy policy/prophet-pilot-policy.json --verify-runtime-artifacts evidence/outputs/runtime/pilot-demo-runtime-retention.json`:
  pass.
- `python3 scripts/check-release-safety.py --paths ...`: pass.

### Operational TODO Cleanup Cycle

Intent:

- Make the near-term TODO file usable as a short operator board while keeping
  the master backlog as the complete source of truth.

Completed:

- Replaced `docs/PROPHET_TODO.md` with a concise operational view covering
  safety invariants, current ground truth, active queue, verification commands,
  and master-backlog pointers.
- Marked the matching master backlog cleanup item complete.
- Kept the cycle documentation-only and did not change runtime behavior,
  generated artifacts, or safety policy.

Verification:

- `python3 scripts/check-release-safety.py --paths docs/PROPHET_TODO.md docs/PROPHET_MASTER_TODO.md docs/PROPHET_GSTACK_WORKLOG.md`:
  pass.
- `git diff --check`: pass.
- `rg -n '[ \t]+$' docs/PROPHET_TODO.md docs/PROPHET_MASTER_TODO.md docs/PROPHET_GSTACK_WORKLOG.md`:
  pass.

### Console Source Freshness And Failure Indicator Cycle

Intent:

- Let buyer evaluators see seeded OSINT freshness and sanitized source-failure
  status directly in the Console evidence panel.

Completed:

- Rendered evidence `open_source_summary` as a compact OSINT basis card with
  freshness status, newest record age, successful source count, and failure
  count.
- Added a failure list path for sanitized source failures while keeping the
  default fixture path quiet when no failures are present.
- Extended control and browser smoke checks for the new evidence source
  indicators.
- Updated pilot docs and marked only the matching Console TODOs complete.

Verification:

- `cd prophet-console && npx --no-install tsc -b --pretty false`: pass.
- `cd prophet-console && npm run lint`: pass.
- `cd prophet-console && npm run build`: pass.
- `cd prophet-console && npm run test:control:evidence`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes and
  passed runtime policy-hash drift verification.
- `cd prophet-console && npm run test:smoke`: pass.
- `git diff --check`: pass.
- Touched-file trailing whitespace scan: pass.

### OSINT Freshness And Failure Evidence Cycle

Intent:

- Make buyer evidence show how fresh the seeded OSINT basis is and whether any
  sanitized source failed, without adding live collection or raw scraper text.

Completed:

- Added fixture-backed OSINT freshness metadata to forecaster
  `open_source_signals`.
- Added source health and sanitized source-failure summaries to evidence JSON
  and Markdown.
- Updated the published evidence JSON Schema and focused tests for the new
  evidence fields.
- Updated pilot docs and marked only the matching source freshness/evidence
  TODOs complete.

Verification:

- `python3 -m py_compile world-side/forecaster/generator.py evidence/bundle.py`:
  pass.
- `python3 -m json.tool evidence/prophet-evidence-bundle.schema.json`: pass.
- `PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest world-side/tests/test_forecaster_smoke.py -v`:
  pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest evidence/tests/test_evidence_bundle.py -v`:
  pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes and
  passed runtime policy-hash drift verification.

### Smoke Policy Drift Gate Cycle

Intent:

- Make the one-command buyer smoke path fail if generated runtime artifacts no
  longer carry the reviewed pilot policy hash.

Completed:

- Added a final `policy.lint --verify-runtime-artifacts` gate to
  `scripts/run-pilot-demo-smoke.sh` after golden smoke hash verification.
- Covered the generated OSINT manifest, sandbox artifact, sandbox run manifest,
  approval record, audit export, audit retention report, evidence bundle,
  integration manifest, and exported operator audit event.
- Updated evaluator and policy-review docs to explain that policy-hash drift is
  now release-blocking in the smoke path.
- Marked CI smoke hash verification complete because the CI workflow runs the
  smoke script, which verifies `scripts/pilot-demo-smoke.sha256`.

Verification:

- `bash -n scripts/run-pilot-demo-smoke.sh`: pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v`:
  pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes and
  passed runtime policy-hash drift verification.
- `python3 scripts/check-release-safety.py --paths scripts/run-pilot-demo-smoke.sh docs/EVALUATOR_START_HERE.md docs/PILOT_DEMO.md docs/PILOT_POLICY_REVIEW.md docs/PROPHET_MASTER_TODO.md docs/PROPHET_GSTACK_WORKLOG.md`:
  pass.
- `git diff --check`: pass.

### Runtime Policy Drift Verification Cycle

Intent:

- Give evaluators a direct check that generated runtime artifacts still carry
  the reviewed pilot policy hash, not just any syntactically valid policy hash.

Completed:

- Added `policy.lint --verify-runtime-artifacts` for evidence, seeded OSINT,
  sandbox artifact, sandbox run manifest, operator audit export, operator audit
  retention, and integration manifest schemas.
- Added unit coverage for matching hashes, drifted hashes, audit export hash
  lists, and CLI JSON output.
- Documented the post-smoke drift verification command in
  `docs/PILOT_POLICY_REVIEW.md`.
- Marked the runtime policy drift TODO complete.

Verification:

- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v`:
  pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint --policy policy/prophet-pilot-policy.json --verify-runtime-artifacts ...`:
  pass for seven current runtime artifacts with zero skipped artifacts.

### Security Checklist Boundary Cycle

Intent:

- Close the remaining P0 contributor safety documentation gaps before any
  buyer pilot handoff.

Completed:

- Expanded `SECURITY.md` with an explicit allowed research boundary for the
  public Prophet repo.
- Added a safe fixture creation checklist for contributors.
- Added a customer data handling checklist for imports before any customer
  artifact enters the evidence path.
- Marked only the matching P0 safety TODO items complete.

Verification:

- `python3 scripts/check-release-safety.py --paths SECURITY.md docs/PROPHET_MASTER_TODO.md docs/PROPHET_TODO.md docs/PROPHET_GSTACK_WORKLOG.md`:
  pass.
- `python3 -m unittest discover -s scripts/tests -v`: pass.
- `git diff --check`: pass.

### Audit Export Redaction Report Cycle

Intent:

- Make the local operator audit export clearer for buyer security review by
  proving the exported artifact contains summaries only and does not embed raw
  audit-log event bodies.

Completed:

- Added a deterministic `redaction_report` block to
  `evidence.audit export`.
- Added audit export validation for summary-only behavior, no embedded source
  log, no embedded raw event bodies, and non-empty redaction allowlists.
- Added unit coverage for the report and negative validation paths.
- Updated evaluator docs and marked the audit redaction report TODO complete.

Verification:

- `python3 -m py_compile evidence/audit.py`: pass.
- `python3 -m unittest evidence.tests.test_audit -v`: pass.
- `python3 -m unittest discover -s evidence/tests -v`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes
  with the updated audit export hash.
- `python3 scripts/verify-pilot-demo-hashes.py --manifest scripts/pilot-demo-smoke.sha256`:
  pass.

### Evidence Bundle Schema Cycle

Intent:

- Publish a buyer-reviewable JSON Schema for the `prophet_evidence_bundle.v0.1`
  contract and enforce it in the local validator without weakening the existing
  safety checks.

Completed:

- Added `evidence/prophet-evidence-bundle.schema.json` for the public evidence
  bundle shape.
- Added stdlib-backed schema validation to `validate_evidence_bundle`.
- Added schema publication, positive validation, and negative drift tests.
- Marked the evidence bundle JSON Schema TODO complete.

Verification:

- `python3 -m unittest discover -s evidence/tests -v`: pass.
- `python3 -m unittest discover -s policy/tests -v`: pass.
- `PYTHONPATH=.:cyber-side:world-side python3 -c 'from evidence.bundle import load_json, validate_evidence_bundle; validate_evidence_bundle(load_json("evidence/fixtures/prophet-evidence-edge-appliance.json"))'`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes.
- `git diff --check`: pass.

### Smoke Evaluator Summary Cycle

Intent:

- Make the one-command buyer smoke path easier for non-engineer evaluators to
  read without changing deterministic runtime artifacts.

Completed:

- Added elapsed-time tracking to `scripts/run-pilot-demo-smoke.sh`.
- Added a final plain-English PASS summary that names the fixture-backed,
  localhost-only, policy-bound mode and points reviewers to evidence, audit,
  and integration handoff outputs.
- Marked the matching buyer demo-flow TODOs complete.

Verification:

- `bash -n scripts/run-pilot-demo-smoke.sh`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes and
  printed the evaluator summary.
- `git diff --check`: pass.

### Sandbox Run Manifest Cycle

Intent:

- Prove each deterministic sandbox run has a reviewable manifest with artifact
  hashes, sanitized log evidence, policy hash, and no retained raw logs.

Completed:

- Added `sandbox_runner/sandbox-run-manifest.schema.json` and stdlib schema
  validation for sandbox run manifests.
- Added `sandbox_runner run --manifest-out` to emit a policy-bound manifest
  next to the Direction C sandbox artifact.
- Added release safety coverage so tracked sandbox run manifests must include a
  policy SHA-256.
- Added the run manifest to the buyer smoke path and deterministic hash
  manifest.
- Updated pilot docs and TODO status.

Verification:

- `PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v`: pass.
- `python3 -m unittest discover -s scripts/tests -v`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 22 pilot demo hashes.

### Main Buyer Pilot Hardening

Intent:

- Use gstack-style product, engineering, CSO, QA, and DX review.
- Do not ask the user for decisions.
- Finish a concrete alpha slice, update the finish plan, and test it strictly.

Completed:

- Added policy-bound `POST /api/integrations/demo-export` to the localhost
  control server.
- Added console Handoff panel for SIEM, ticketing, and audit review-template
  export.
- Extended control smoke to prove the handoff endpoint emits
  `review_template_only`, no-external-API-call artifacts.
- Extended Playwright smoke to generate evidence, export handoff templates, and
  refresh readiness.
- Added `docs/PROPHET_FULL_FINISH_PLAN.md`.
- Added `docs/INTEGRATION_HANDOFF_GUIDE.md`.
- Added safe customer asset CSV import with row-level rejection report.
- Added `docs/ASSET_IMPORT_GUIDE.md`.
- Added policy source allowlists and sandbox-profile allowlists to the default
  and example pilot policies.
- Enforced `allowed_source_ids` in `scraper_side.snapshot --policy`.
- Enforced `allowed_sandbox_profiles` in `sandbox_runner run --policy`.
- Enforced `allowed_integration_exports` in `integrations.export --policy`.
- Added local operator identity and hash-chained audit events for approval,
  denial, and integration handoff export.
- Evidence bundles now include the local approval record hash; integration
  manifests carry that hash forward.
- Added a denial endpoint that records operator denial without generating an
  evidence bundle.
- Readiness now validates the local operator audit log when it exists.
- Added `docs/RELEASE_CHECKLIST.md` and a GitHub PR template with explicit
  safety, policy, audit, and acceptance gates.
- Confirmed the pilot smoke script verifies 21 deterministic artifact hashes
  against `scripts/pilot-demo-smoke.sha256`.
- Added `npm audit --audit-level=moderate` to the console CI job.
- Added dependency audit workflow and Playwright failure artifact upload.
- Added a second customer-safe financial workflow asset fixture, CSV fixture,
  and checked-in seedset to prove asset intake is not edge-appliance-only.
- Removed legacy live-demo candidate instructions from presentation/research
  docs and replaced them with the fixture-only pilot contract.
- Added policy retention hints for runtime outputs, audit logs, customer
  metadata, raw collection retention, and deletion review.
- Added policy ID/hash/retention context to the seeded-OSINT manifest and
  sandbox runtime artifact so downstream runtime manifests carry policy basis.
- Added policy-bound audit retention reporting with a confirmation-gated cleanup
  path for fully expired runtime audit logs.
- Added audit export and retention report generation to the deterministic pilot
  smoke path.
- Added `policy/prophet-pilot-policy.schema.json` and made `policy.lint`
  validate policies against the schema by default.
- Updated README, console README, alpha review, and TODO status.

Verification:

- Policy tests: pass.
- Asset tests: pass.
- Cyber-side tests: pass.
- World-side tests: pass.
- Sandbox runner tests: pass.
- Evidence bundle tests: pass.
- Audit retention tests: pass.
- Integration export tests: pass.
- `npm run acceptance`: pass.
- `git diff --check`: pass.
- `npm audit --audit-level=moderate`: pass with 0 vulnerabilities.

Latest acceptance timestamp:

- `2026-05-05T05:58:16Z` audit retention loop.
- Packaged smoke policy hash:
  `fd7fc162a324c926e02aca0c1093798f1ec94e4d76daedbe7dc0acb480783163`.
- Packaged smoke evidence hash:
  `556767244c4adc70332e2466ba0e13d461cfc02834aea1e34a265fb4a279fcf2`.
- Packaged smoke integration manifest hash:
  `c52e4389130194280ba92c338ec96627053edbf0bee70ea5fd14c75f3f0042fc`.
- Evidence and integration exports now carry a policy-required
  no-live-target-data assertion.
- `git diff --check`: pass.
- `npm run acceptance`: pass, including Playwright browser smoke.
- Runtime output ignore check: pass for world-side, cyber-side, evidence,
  assets, and integrations.

Next strict loop:

1. Audit retention cleanup/export workflow.
2. Second sandbox profile and container design.
3. Policy comparison output for customer-specific policy review.
4. Production deployment architecture, RBAC/SSO plan, and threat model.

## 2026-05-05 Console Artifact Source Badge Cycle

Intent:

- Make the buyer console show whether evidence used a validated sandbox runtime
  artifact or the checked-in defensive fixture.

Completed:

- Added artifact source label and mode to the evidence control-server response.
- Carried artifact source metadata through React state into the evidence panel.
- Added a compact evidence-panel badge for runtime sandbox vs checked-in fixture
  source, including the relative artifact path.
- Extended control and browser smoke checks for the new source signal.
- Marked the matching console TODO complete.

Verification:

- `cd prophet-console && npm run lint`: pass.
- `cd prophet-console && npm run build`: pass.
- `cd prophet-console && npm run test:control:evidence`: pass.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 21 pilot demo hashes.
- `cd prophet-console && npm run test:smoke`: pass.

## 2026-05-05 Console Live-Action Policy Gate Cycle

Intent:

- Make the release safety scanner fail closed if a console live-collection
  action is wired without an explicit policy gate in the localhost control
  server.

Completed:

- Added static scanning for console API endpoints that look like live
  collection, target, raw, or VM actions.
- Required the existing `POST /api/scraper/run` surface to have a
  `policy.controls.live_vm_scraper_allowed` check and a `policy_blocked`
  denial path.
- Added positive and negative scanner tests for policy-gated and ungated
  console live actions.
- Marked the matching P0 safety TODO complete.

Verification:

- `python3 -m unittest discover -s scripts/tests -v`: pass.
- `python3 scripts/check-release-safety.py --paths prophet-console/src/App.tsx prophet-console/control-server.mjs --paths-only`: pass.
- `python3 -m py_compile scripts/check-release-safety.py`: pass.
- `python3 scripts/check-release-safety.py --tracked --paths-only`: pass.

## 2026-05-05 CLI No-Live-Target Guard Cycle

Intent:

- Turn the buyer-pilot no-live-target boundary into executable CLI checks for
  mutable local inputs.

Completed:

- Added Direction A candidate input safety scanning to the forecaster.
- Added subprocess-based CLI guard tests for asset import, asset seedset,
  forecaster, scraper, OSINT snapshot, predictor, sandbox runner, audit,
  evidence bundle, integration export, policy lint, and policy retention.
- Closed the audit CLI gap where `--out-event` could write outside ignored
  runtime output directories.
- Added `docs/CLI_SAFETY_MATRIX.md` and marked the scoped CLI safety TODOs
  complete.

Verification:

- `PYTHONPATH=.:cyber-side:world-side:world-side/scraper python3 -m unittest scripts.tests.test_cli_no_live_targets -v`: pass, 13 tests.
- `PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v`: pass, 24 tests.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v`: pass, 56 tests.
- `PYTHONPATH=.:cyber-side:world-side:world-side/scraper python3 -m unittest discover -s scripts/tests -v`: pass, 33 tests.
- `./scripts/run-pilot-demo-smoke.sh`: pass, verified 23 pilot demo hashes.
- `git diff --check`: pass.
