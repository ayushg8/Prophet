# Prophet Operational TODO

Last updated: 2026-05-05

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
  and policy-blocked states.
- [x] Release safety checks cover unsafe text, runtime artifacts, policy hashes,
  source-catalog allowlists, and console live-action gates.
- [ ] Fresh-clone smoke has not yet been independently verified.
- [ ] The pilot fixture/hash set has not yet been release-tagged.

## Active Queue

### P0: Release Hygiene

- [ ] Review the dirty worktree and split it into intentional commits once the
  user asks for commits.
- [ ] Confirm deleted lab/demo exploit files are intentional in the final diff.
- [ ] Run `git diff --check` before every commit.
- [ ] Run all Python unit suites before the final pilot commit.
- [ ] Run `cd prophet-console && npm run acceptance` before internal alpha demo.
- [ ] Run the top-level smoke script from a fresh checkout.
- [ ] Store smoke output hashes in release notes.
- [ ] Create a pilot release tag naming the fixture/hash set.

### P1: Buyer Pilot Hardening

- [x] Add a `--sector financial-workflow` smoke variant.
- [x] Add a second golden hash manifest for that sector.
- [x] Add a fixture diff command to explain demo-run changes.
- [x] Add a failure-mode demo showing policy-blocked live behavior.
- [ ] Add evaluator mode that hides non-demo controls.

### P1: Pilot Documentation

- [x] Add a 12-minute analyst walkthrough through console, evidence, and
  exports.
- [x] Add a 30-minute technical walkthrough through policy, tests, and
  validation.
- [x] Add a demo operator checklist.
- [x] Add troubleshooting for missing Node, Python, npm, and Playwright.
- [ ] Add redacted final-console screenshots or expected screenshot artifacts.
- [x] Add a glossary for non-cyber readers.

### P1/P2: Validation And Evidence

- [x] Add timeout/failure evidence paths for sandbox validation.
- [ ] Add signed evidence manifest design.
- [ ] Add optional detached signature support.
- [ ] Add policy migration handling.
- [x] Add explicit no-live-target enforcement tests for every buyer-pilot CLI
  that accepts mutable operator, customer, source, policy, forecast, sandbox,
  evidence, or export input.
- [x] Finish runtime-output and customer-metadata retention enforcement beyond
  the current audit-log cleanup.

### P2: Next Technical Depth

- [ ] Package `sandbox_runner` as a reproducible container.
- [ ] Add no-egress notes, resource limits, and container hash provenance.
- [x] Add a second sandbox profile for a different defensive class.
- [ ] Add CycloneDX and SPDX SBOM fixtures and parsers.
- [ ] Add production architecture, threat model, RBAC/SSO plan, and customer
  data-boundary appendix.

## Verification Commands

Run the narrowest focused tests for the touched slice, then always run:

```bash
git diff --check
```

Before calling a buyer pilot build stable, run:

```bash
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v
PYTHONPATH=.:cyber-side:world-side:world-side/scraper python3 -m unittest scripts.tests.test_cli_no_live_targets -v
./scripts/run-pilot-demo-smoke.sh
cd prophet-console && npm run acceptance
cd prophet-console && npm audit --audit-level=moderate
```

## Master Backlog Pointers

- Safety and release gates: `docs/PROPHET_MASTER_TODO.md` P0.
- Buyer pilot flow, policy, evidence, sandbox, and console: P1.
- Asset/SBOM, OSINT, forecast, integrations, audit, security, and DX: P2.
- Commercial readiness, production architecture, operations, product, UX: P3.
- Governance, compliance, research, and testing matrix: P4 and later.
