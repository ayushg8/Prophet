# Prophet Operational TODO

Last updated: 2026-05-11

For the full backlog, production roadmap, and long-horizon commercial work, use
`docs/PROPHET_MASTER_TODO.md` as the source of truth. This file is the short
operator board for the next buyer-pilot cycles.

## Operating Boundary

- Default mode stays fixture-backed, seeded-OSINT-backed, policy-bound, and
  localhost-only.
- Runtime outputs stay under ignored `*/outputs/runtime/` directories.
- Public demos use safe fixtures, deterministic sandbox artifacts, and review
  templates only.
- Do not add live collection, target-control workflows, credentials, private
  hostnames, raw scraper text, or offensive automation to this repo.
- Do not mark a TODO complete unless the code, docs, tests, and smoke output
  actually support it.

## Current Ground Truth

- [x] One-command buyer smoke path exists:
  `./scripts/run-pilot-demo-smoke.sh`.
- [x] Smoke output hashes are deterministic and policy-drift checked.
- [x] Evidence JSON and Markdown include policy hash, approval hash, artifact
  hashes, source freshness, source failures, validation failure/timeout
  evidence, safety attestation, and redaction report.
- [x] Customer-safe CSV asset imports emit a hash-only import manifest for raw
  input and sanitized inventory/report/seedset outputs.
- [x] Integration handoffs are review templates, not auto-deploying controls.
- [x] Root README points evaluators to the 3-minute smoke path and generated
  evidence outputs.
- [x] Console has readiness, policy, evidence, integration, freshness, failure,
  fixture-mode proof, non-blocking missing-runtime warning states, asset/SBOM
  context drilldown, and policy-blocked states.
- [x] Release safety checks cover unsafe text, runtime artifacts, policy hashes,
  source-catalog allowlists, and console live-action gates.
- [x] Buyer positioning has been refreshed against May 2026 market pressure:
  CISA KEV/BOD, EPSS, CMMC/DFARS, exposure-management incumbents, and
  SIEM/ticketing workflows.
- [x] Product management decisions are explicit in commercial readiness:
  personas, first paid wedge, positioning, paid-pilot conversion, 90-day
  non-goals, competitive set, success metrics, and feedback form:
  `docs/COMMERCIAL_READINESS.md`.
- [x] Buyer follow-up package exists for qualified post-demo reviews:
  `docs/BUYER_FOLLOW_UP_PACKAGE.md`; it includes a procurement/security
  questionnaire draft and export-control review placeholder for qualified
  buyers, plus data processing addendum scoping notes.
- [x] Design partner pilot offer includes SOW-lite, success criteria, and a
  post-pilot conversion plan gated on `build_next_slice`:
  `docs/DESIGN_PARTNER_PILOT_OFFER.md`.
- [x] Design partner pilot offer includes a pricing and packaging memo that
  keeps custom work paid and scope narrow until validation reaches
  `build_next_slice`: `docs/DESIGN_PARTNER_PILOT_OFFER.md`.
- [x] Design partner pilot offer includes a pilot support model and pilot issue
  communication template without production SLA or incident-response claims:
  `docs/DESIGN_PARTNER_PILOT_OFFER.md`.
- [x] Design partner pilot offer includes onboarding/offboarding steps for
  approved metadata, retention, closeout, and local artifact cleanup:
  `docs/DESIGN_PARTNER_PILOT_OFFER.md`.
- [x] Evaluator worksheet includes CISO/executive review questions and
  go/no-go outcomes: `docs/EVALUATOR_WORKSHEET.md`.
- [x] Daily outreach block generator exists for private validation targets:
  `scripts/validation-outreach-block.py`; when no follow-ups are due, it
  provides safe first-touch backfill asks rather than fake follow-ups.
- [x] Daily safe message pack generator exists for private outreach blocks:
  `scripts/validation-message-pack.py`; it can render the full pack or one
  source-aware draft with `--target-label`, and generated tracker commands use
  `--require-current-status` guards. It supports `--require-date`, and root
  `make validation-draft TARGET=... DATE=YYYY-MM-DD` renders one clean draft
  for send-by-send execution while rejecting stale packs.
- [x] Copy-only send batch generator exists for all verified pending outreach
  drafts: `scripts/validation-send-copy-batch.py`; root
  `make validation-send-copy-batch DATE=YYYY-MM-DD` writes one private `.txt`
  file per draft plus a private manifest with copy-file SHA-256 values and
  outbound-boundary fields, checklist, and README, after verifying generated dry-run commands still
  apply.
- [x] Next-draft helper renders the first verified pending private outreach
  draft and refuses stale target-state or date-mismatched packs:
  `scripts/validation-next-draft.py`; root `make validation-next-draft` wraps
  it, writes `validation/private/today-next-draft.md`, and
  enforces today's date by default unless `DATE=YYYY-MM-DD` is supplied.
  The tracker/audit Markdown warns operators not to paste it to buyers and
  points them to the copy-only send artifact.
- [x] CLI reference exists for the safe local pilot and validation command
  surface: `docs/CLI_REFERENCE.md`.
- [x] CLI reference help commands are covered by a docs test:
  `scripts/tests/test_cli_reference_docs.py`.
- [x] CLI safety matrix includes validation sprint CLIs and guardrails:
  `docs/CLI_SAFETY_MATRIX.md`; docs coverage lives in
  `scripts/tests/test_cli_safety_matrix_docs.py`.
- [x] Local environment checker exists for the root pilot and strict console
  path: `scripts/check-local-env.sh`.
- [x] First successful evaluator run is verified under three minutes:
  `./scripts/run-pilot-demo-smoke.sh` passed in 2s on 2026-05-10.
- [x] Integration handoff bundles include a customer review checklist:
  `integrations/outputs/runtime/*/review_checklist.md`.
- [x] Integration handoff checklist requires SOC/customer sign-off fields in
  validation: reviewer role, evidence/policy hash checks, placeholder and
  telemetry mapping, customer owner approval, and deployment decision.
- [x] Integration handoff manifest validates customer placeholder inventory:
  `manifest.customer_placeholder_validation`.
- [x] Integration handoff artifacts can be packaged as deterministic review
  ZIPs under ignored runtime output paths.
- [x] README includes the current safe pilot architecture diagram and module
  ownership map.
- [x] Optional Python virtualenv setup is documented in
  `docs/PILOT_TROUBLESHOOTING.md`.
- [x] Daily outreach execution status checker exists for comparing message
  packs with the private target tracker and verifying pending dry-run commands:
  `scripts/validation-outreach-status.py`. It supports `--require-date`, and
  root `make validation-status DATE=YYYY-MM-DD` rejects stale packs.
- [x] No-write reply triage helper exists for sanitized post-reply actions:
  `scripts/validation-reply-triage.py` emits safe dry-run and
  `CONFIRM_TARGET=1` commands without accepting reply text or writing files.
  Root `make validation-reply-triage TARGET=... REPLY=... DATE=YYYY-MM-DD`
  wraps the helper for normal outreach.
- [x] Validation sprint dashboard surfaces private outreach execution status
  when today's message pack exists, and it detects whether an already-rendered
  `today-next-draft.md` still matches the current next pending
  target/date/status before restored sessions proceed to the send boundary.
- [x] Validation sprint dashboard supports sanitized aggregate-only team
  updates through `--format team` and `make validation-team-update`, omitting
  target labels, commands, message bodies, and private validation paths.
- [x] Saved aggregate validation team updates use an atomic temp-file write:
  `make validation-team-update-save DATE=YYYY-MM-DD` preserves the previous
  `validation/private/today-team-update.md` if rendering fails.
- [x] `make validation-pack` refreshes outreach block, message pack, and paired
  outreach status JSON/Markdown so private status files do not go stale.
- [x] Makefile validation wrappers have focused tests for overridden private
  validation directories: `scripts/tests/test_make_validation_targets.py`.
- [x] Safe target status updater exists for anonymized outreach tracking:
  `scripts/validation-target-update.py`; booked calls and disqualifications can
  clear follow-up dates with `--clear-follow-up-due`, and completed calls can
  be marked only after sanitized interview logging with `--require-current-status`
  guards and a matching validation-log `account_label`. The raw CLI blocks
  confirmed send-derived `intro_requested` / `outreach_sent` writes so
  post-send updates must go through
  `scripts/validation-apply-draft-update.py` with copy-only artifact
  verification; non-send raw writes require `--confirm-target`; root wrappers
  `make validation-book-call`, `make validation-disqualify-target`, and
  `make validation-complete-call` dry-run by default and write only with
  `CONFIRM_TARGET=1`.
- [x] Target tracker validation rejects malformed top-level/target dates, due
  follow-up statuses without due dates, and advanced statuses that still carry
  stale follow-up dates: `scripts/validation-targets-scorecard.py`.
- [x] Guarded draft-update applier exists for post-send tracker updates:
  `scripts/validation-apply-draft-update.py`; root
  `make validation-apply-draft TARGET=... DATE=YYYY-MM-DD` dry-runs before
  sending or writing, rejects stale packs, writes only with `CONFIRM_SENT=1`
  after a confirmed send and matching copy-only send artifact, and tells the
  operator to rerun dated status verification after tracker writes. Make
  confirmation wrappers now require exact `=1` values so `CONFIRM_SENT=0`,
  `CONFIRM_TARGET=false`, and similar
  values fail closed.
- [x] Safe customer validation log appender exists for sanitized interview
  notes and writes only with `--confirm-log`:
  `scripts/customer-validation-log-add.py`.
- [x] Safe interview starter helper exists for booked anonymized targets:
  `scripts/validation-prepare-interview.py`. It writes an intentionally
  incomplete private record so fake/sample data cannot be logged without
  filling real sanitized call outcomes.
- [x] Root `make validation-log-interview DATE=YYYY-MM-DD` validates sanitized
  interview log appends against a matching `call_booked` anonymized target
  and matching segment/persona metadata without writing and writes only with
  `CONFIRM_LOG=1`; normal raw confirmed writes require
  `--require-target-status call_booked` with matching target metadata or
  explicit `--allow-untracked-interview`, while first-interview seed replacement
  requires the booked-target guard and rejects the untracked bypass.
- [x] Sanitized interview JSON template exists for private validation logging:
  `docs/customer-validation-interview.template.json`.
- [x] Example validation dashboard verdict is `insufficient_data`; production
  build gate remains closed until real private validation shows
  `build_next_slice`. `pilot_pull_detected` means convert design partners first.
- [x] Customer validation scorecard reports `gaps_to_verdicts` so remaining
  counts to `pilot_pull_detected` and `build_next_slice` are explicit.
- [x] Production build gate also requires `target_backed_validation`:
  interviews counted toward build scope must match anonymized targets in
  `call_booked` or `completed` with matching segment/persona metadata.
- [x] Local smoke has been verified on macOS after the handoff checklist,
  customer-placeholder validation, and review-ZIP packaging updates: default
  smoke passed with 26 hashes on 2026-05-10.
- [x] Default output safety checker scans policy-listed runtime outputs for
  live-target URL fields while allowing public source citations:
  `scripts/check-default-output-safety.py`.
- [x] Safety architecture documents the raw-to-sanitized source boundary and
  the enforcement points that keep raw source text out of buyer-pilot outputs:
  `docs/SAFETY_ARCHITECTURE.md`.
- [x] Asset import guide documents how to generate customer-safe fictional
  fixture examples without importing customer target data:
  `docs/ASSET_IMPORT_GUIDE.md`.
- [x] Pilot policy review documents source terms review, future source-catalog
  allowlist review, and customer-approved source allowlist notes without
  enabling live collection: `docs/PILOT_POLICY_REVIEW.md`.
- [x] Default output safety checker verifies policy-listed OSINT snapshot
  provenance manifests, including snapshot hash, policy hash, sanitized-only
  attestation, and disabled raw collection retention:
  `scripts/check-default-output-safety.py`.
- [x] Temporary local clone with the current non-ignored worktree overlay passed
  `./scripts/check-local-env.sh` and the default smoke with 26 hashes on
  2026-05-10.
- [x] Repeatable worktree-overlay smoke wrapper exists for pre-commit local
  package checks: `make worktree-smoke` / `scripts/run-worktree-smoke.sh`.
- [x] Repeatable release hygiene wrapper exists for tracked/untracked
  whitespace, safety, current-worktree secret scanning, policy, default-output,
  and local Markdown link checks:
  `make release-hygiene` / `scripts/check-release-hygiene.sh`.
- [x] Full secrets archaeology scanner exists:
  `make secrets-archaeology` / `scripts/check-secrets-archaeology.sh`.
- [ ] Full secrets archaeology and public release review currently flag
  historical
  `LOG4SHELL_INSTRUCTIONS.md` password-like content in git history; decide
  cleanup/rotation/exception before any public release. Public release review
  stays blocked until the owner decision is recorded. Safe review path:
  `docs/SECRET_HISTORY_REVIEW.md`.
- [x] True GitHub fresh-clone smoke passed on macOS with 26 verified pilot
  hashes. Exact-head evidence belongs in the PR verification notes because
  documentation commits can move the branch head; rerun after any further
  commit before merge or release decisions.
- [x] Linux fresh-clone smoke is covered by the Ubuntu GitHub Actions `python`
  job through the named `Linux fresh-clone pilot smoke preflight` and
  `Linux fresh-clone pilot smoke` steps.
- [x] Pilot release notes identify the current smoke manifests, policy hash, and
  main generated artifact hashes, plus the runnable `make console-demo` local
  product path and `make pilot-ready-check-full DATE=2026-05-11` gate.
- [x] Console screenshot manifest verifier exists for redacted visual handoff
  review: `make console-screenshot-check` /
  `scripts/check-console-screenshots.py`.
- [x] Evidence Markdown now surfaces the selected forecast window rationale,
  vector rationale, and cited forecast source IDs so buyer reviewers can trace
  "why this first, why now" without opening raw forecast JSON.
- [x] Published evidence JSON Schema now requires the selected vector rationale
  in `forecast_summary.vector.why_this_vector`, and the checked-in evidence
  fixture validates against that contract.
- [x] Data classification and artifact inventory exists for buyer/security
  review: `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`.
- [x] Local operator identity format guidance exists for the buyer pilot:
  `docs/OPERATOR_IDENTITY_GUIDE.md`.
- [x] Signed operator approval design exists for future buyer/security review:
  `docs/SIGNED_OPERATOR_APPROVAL_DESIGN.md`.
- [x] Pilot scope includes a customer data boundary appendix for allowed inputs,
  prohibited inputs, storage/retention, and export rules:
  `docs/PILOT_SCOPE.md`.
- [x] Pilot scope includes a customer pilot reference architecture for approved
  metadata, local evidence generation, and customer review:
  `docs/PILOT_SCOPE.md`.
- [x] Signed evidence manifest design exists for future buyer/security review:
  `docs/SIGNED_EVIDENCE_MANIFEST_DESIGN.md`.
- [x] Signed policy design exists for future buyer/security review:
  `docs/SIGNED_POLICY_DESIGN.md`.
- [x] Completion audit maps the CEO finish objective to current evidence and
  remaining blockers; use its "Recovered Goal Source / Goal Setter" section
  plus `make goal-resume DATE=YYYY-MM-DD` after a lost `/goal` session:
  `docs/PROPHET_COMPLETION_AUDIT.md`.
- [x] Root agent operating manual is aligned to the current validation-first
  product direction and recovered goal source: `AGENTS.md`; regression coverage
  lives in `scripts/tests/test_agent_operating_manual.py`.
- [x] Private validation workspace README can be safely refreshed without
  overwriting private tracker/log files:
  `python3 scripts/init-validation-sprint.py --date YYYY-MM-DD --refresh-readme`
  or `make validation-init DATE=YYYY-MM-DD REFRESH_README=1`.
- [x] Dirty worktree finish inventory exists for later review/commit splitting:
  `docs/PROPHET_FINISH_CHANGE_INVENTORY.md`.
- [x] Weekly validation review ritual exists for pruning stale private targets,
  stale message packs, stale private interview starters, and completed or stale
  TODOs:
  `docs/VALIDATION_SPRINT_CHECKLIST.md`.
- [x] Weekly validation review report is executable and read-only:
  `scripts/validation-weekly-review.py` and
  `make validation-weekly-review DATE=YYYY-MM-DD` report date-guarded outreach
  execution readiness, send-copy batch README/checklist/copy-index state, stale
  private artifacts, and pruning candidates without deleting files or mutating
  trackers/logs. The JSON report includes `review_date` for machine-readable
  recovered-session handoffs.
- [x] Evaluator and buyer FAQ docs explicitly say the standard pilot is not
  live attack prediction, live collection, offensive validation, production
  control push, or autonomous remediation.
- [x] Redacted pilot output snippets with packaged SHA-256 hashes exist for
  evaluator review: `docs/PILOT_OUTPUT_SNIPPETS.md`.
- [x] Current tracked diff has no deleted files; `git diff --name-status` and
  `git ls-files --deleted` show no lab/demo exploit deletions to confirm.
- [x] Release checklist includes the validation dashboard/build-gate decision
  before internal alpha or customer-pilot builds:
  `docs/RELEASE_CHECKLIST.md`.
- [x] Overnight GStack loop prompt is aligned to the current validation gate and
  recovered `/goal` path: `scripts/prophet-overnight-gstack-loop.sh`.
- [x] Historical overnight consolidation docs point to the current validation
  gate rather than authorizing production scope:
  `docs/OVERNIGHT_CHANGE_REPORT.md` and
  `docs/OVERNIGHT_CONSOLIDATION_TODO.md`.
- [ ] The pilot fixture/hash set has not yet been release-tagged; public tagging
  is blocked until the historical secret-history finding has an owner decision.

## Active Queue

### P0: Product Validation Before More Platform Work

- [x] Add customer discovery guide.
- [x] Add outreach playbook.
- [x] Add design partner pilot offer.
- [x] Add customer validation scorecard.
- [x] Add validation sprint checklist and daily brief.
- [x] Add anonymized outreach target tracker.
- [x] Add daily outreach block generator.
- [x] Add safe outreach message pack generator.
- [x] Add safe copy-only outreach send batch generator.
- [x] Add safe outreach execution status checker.
- [x] Add safe no-write reply triage helper.
- [x] Add safe target status updater.
- [x] Add safe customer validation log appender.
- [x] Add sanitized interview JSON template.
- [ ] Complete 15 qualified discovery conversations.
- [ ] Get 3 design-partner pilot discussions.
- [ ] Get 1 paid, sponsored, or procurement-sponsored pilot path.

### P0: Release Hygiene

- [x] Review the dirty worktree and split it into intentional commits for PR
  `#5`; keep `docs/PROPHET_FINISH_CHANGE_INVENTORY.md` as the review map.
- [x] Add `make release-hygiene` for the full read-only local hygiene sweep.
- [x] Confirm deleted lab/demo exploit files are intentional in the final diff:
  current tracked diff has no deleted files.
- [ ] Run `git diff --check` before every commit.
- [x] Add `make python-tests` for all Python unit suites before the final pilot
  commit.
- [x] Run `make python-tests` for the current pre-commit review; rerun after
  staging the exact final commit set.
- [x] Run `cd prophet-console && npm run acceptance` before internal alpha demo.
- [x] Run the top-level smoke script from a temporary worktree-overlay clone.
- [x] Add `make worktree-smoke` so the worktree-overlay clone smoke is
  repeatable before commit/PR review.
- [x] Harden PR template with validation-dashboard, closed build-gate,
  private-artifact, and current local wrapper checks.
- [x] Store smoke output hashes in release notes.
- [ ] Create a pilot release tag naming the fixture/hash set after the
  secret-history owner decision and final release checks.

### P1: Buyer Pilot Hardening

- [x] Add a `--sector financial-workflow` smoke variant.
- [x] Add a second golden hash manifest for that sector.
- [x] Add a fixture diff command to explain demo-run changes.
- [x] Add a failure-mode demo showing policy-blocked live behavior.
- [x] Add evaluator mode that hides non-demo controls.

### P1: Pilot Documentation

- [x] Add a 12-minute analyst walkthrough through console, evidence, and
  exports.
- [x] Add a 30-minute technical walkthrough through policy, tests, and
  validation.
- [x] Add a demo operator checklist.
- [x] Add troubleshooting for missing Node, Python, npm, and Playwright.
- [x] Add redacted final-console screenshots or expected screenshot artifacts,
  plus ignored responsive desktop/mobile capture:
  `cd prophet-console && npm run capture:screenshots`.
- [x] Add a glossary for non-cyber readers.

### P1/P2: Validation And Evidence

- [x] Add timeout/failure evidence paths for sandbox validation.
- [x] Add signed evidence manifest design.
- [ ] Add optional detached signature support.
- [ ] Add policy migration handling.
- [x] Add explicit no-live-target enforcement tests for every buyer-pilot CLI
  that accepts mutable operator, customer, source, policy, forecast, sandbox,
  evidence, or export input.
- [x] Add evidence-bundle regression tests that raw scraper/source fields and
  pasted raw-source markers are rejected:
  `evidence/tests/test_evidence_bundle.py`.
- [x] Finish runtime-output and customer-metadata retention enforcement beyond
  the current audit-log cleanup.

### P2: Next Technical Depth

- [ ] Package `sandbox_runner` as a reproducible container.
- [ ] Add no-egress notes, resource limits, and container hash provenance.
- [x] Add a second sandbox profile for a different defensive class.
- [ ] Add CycloneDX and SPDX SBOM fixtures and parsers.
- [x] Add production architecture, threat model, production execution plan, and
  compliance gap map.
- [x] Add pilot-mode threat model to the safety architecture.
- [~] Add RBAC roles and tenant isolation decision primitive.
- [ ] Add SSO plan, customer data-boundary appendix, and database-backed tenant
  isolation test design.
- [x] Add machine-readable production readiness backlog and scorecard.

## Verification Commands

Run the narrowest focused tests for the touched slice, then always run:

```bash
git diff --check
```

Before calling a buyer pilot build stable, run:

```bash
make python-tests
./scripts/run-pilot-demo-smoke.sh
cd prophet-console && npm run acceptance
cd prophet-console && npm audit --audit-level=moderate
```

Use the individual suite commands in `README.md` only when debugging a narrower
test failure.

## Master Backlog Pointers

- Safety and release gates: `docs/PROPHET_MASTER_TODO.md` P0.
- Buyer pilot flow, policy, evidence, sandbox, and console: P1.
- Asset/SBOM, OSINT, forecast, integrations, audit, security, and DX: P2.
- Commercial readiness, production architecture, operations, product, UX: P3.
- Governance, compliance, research, and testing matrix: P4 and later.
- Production readiness source of truth:
  `docs/production-readiness-backlog.json`.
