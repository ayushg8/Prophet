# Overnight Consolidation TODO

Last updated: 2026-05-05

The overnight GStack loop completed 40 cycles and left a large uncommitted
worktree. This checklist is the execution plan for turning that work into a
reviewable Prophet pilot release candidate.

## Status Key

- `[x]` Done during this consolidation pass.
- `[~]` In progress.
- `[ ]` Not done yet.
- `[BLOCKED]` Needs a failing check fixed or a human release decision.

## P0: Stop The Loop And Preserve Evidence

- [x] Confirm `prophet-overnight-loop` stopped normally after 40 cycles.
- [x] Confirm every overnight cycle exited with status `0`.
- [x] Confirm the stop reason was `max_cycles=40`, not sleep or crash.
- [x] Confirm `git diff --check` passes before consolidation.
- [x] Keep overnight logs under ignored runtime output:
  `evidence/outputs/runtime/gstack-overnight-loop/`.
- [~] Keep the machine caffeinated only as long as needed for validation.

## P0: Change Report

- [x] Add `docs/OVERNIGHT_CHANGE_REPORT.md`.
- [x] Fill in final full-suite validation results.
- [ ] Fill in commit hashes after local commits are created.
- [x] Record any failing checks and exact remediation.
- [x] Record residual risk after all validation.

## P0: Full Validation

- [x] Run `git diff --check`.
- [x] Run cyber-side tests:
  `PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v`.
- [x] Run world-side tests:
  `PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v`.
- [x] Run asset tests:
  `PYTHONPATH=. python3 -m unittest discover -s assets/tests -v`.
- [x] Run sandbox runner tests:
  `PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v`.
- [x] Run policy tests:
  `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v`.
- [x] Run evidence tests:
  `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v`.
- [x] Run integration export tests:
  `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v`.
- [x] Run script safety tests:
  `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s scripts/tests -v`.
- [x] Run edge-appliance smoke:
  `./scripts/run-pilot-demo-smoke.sh`.
- [x] Run financial-workflow smoke:
  `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`.
- [x] Run console lint:
  `cd prophet-console && npm run lint`.
- [x] Run console build:
  `cd prophet-console && npm run build`.
- [x] Run control evidence smoke:
  `cd prophet-console && npm run test:control:evidence`.
- [x] Run browser smoke:
  `cd prophet-console && npm run test:smoke`.
- [x] Run console acceptance:
  `cd prophet-console && npm run acceptance`.
- [x] Run dependency audit:
  `cd prophet-console && npm audit --audit-level=moderate`.
- [x] Run release safety check on tracked files:
  `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --tracked`.
- [x] Run release safety check on changed and untracked files:
  `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py $( { git diff --name-only --diff-filter=ACMR; git ls-files --others --exclude-standard; } | sort -u )`.

## P0: Safety Review

- [x] Confirm no runtime output is staged.
- [x] Confirm lab exploit material remains deleted from the public tree.
- [x] Confirm policies still block live targets, VM scraping, arbitrary target
  input, payload generation, raw scraper text, private hostnames, and
  credentials.
- [x] Confirm seeded OSINT remains fixture-backed unless `--live` is explicit
  and policy-approved.
- [x] Confirm integration outputs remain review templates, not production pushes.
- [x] Confirm smoke artifacts contain policy hash and pass policy drift checks.
- [x] Confirm no generated runtime artifacts appear in `git status`.

## P1: Commit Groups

Create local commits only after the full validation pass is green or the failure
is documented and isolated.

- [ ] Commit 1: safety cleanup and deleted lab/demo exploit material.
- [ ] Commit 2: asset/SBOM fixtures, CSV import, seedset generation, and tests.
- [ ] Commit 3: seeded OSINT snapshotting, source catalog safety, freshness, and
  forecaster enrichment.
- [ ] Commit 4: policy schema, linter, comparison, allowlists, retention, and
  policy tests.
- [ ] Commit 5: evidence bundle, audit log, audit export, retention evidence,
  JSON Schema, and evidence tests.
- [ ] Commit 6: sandbox runner profiles, artifacts, manifests, negative
  fixtures, schemas, and tests.
- [ ] Commit 7: integration handoff exports, validation, docs, and tests.
- [ ] Commit 8: console evidence, integration, policy, readiness, and browser
  smoke work.
- [ ] Commit 9: CI, release safety checks, pre-commit hook, and script tests.
- [ ] Commit 10: buyer/evaluator docs, worksheets, walkthroughs, glossary, and
  troubleshooting.
- [ ] Commit 11: second-sector financial-workflow smoke path and hashes.
- [ ] Commit 12: overnight supervisor script and consolidation docs.

## P1: Post-Commit Review

- [ ] Run `git log --oneline --decorate -12` and verify commit order is legible.
- [ ] Run `git status --short --untracked-files=all` and confirm only ignored
  runtime outputs remain unstaged.
- [ ] Re-run `git diff --check`.
- [ ] Run the full Python matrix.
- [ ] Run both smoke sectors.
- [ ] Run `cd prophet-console && npm run acceptance`.
- [ ] Run `cd prophet-console && npm audit --audit-level=moderate`.
- [ ] Run a GStack review/timeline log for the consolidation pass.

## P2: Fresh Clone Gate

- [ ] Create a fresh clone or fresh worktree after local commits exist.
- [ ] Run `./scripts/run-pilot-demo-smoke.sh`.
- [ ] Run `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`.
- [ ] Run `cd prophet-console && npm ci && npm run acceptance`.
- [ ] Confirm no private context, live target, credential, raw scraper text, or
  generated runtime artifact is required.

## P2: Release Candidate

- [ ] Add release note with policy hash, evidence hashes, smoke manifests, and
  known gaps.
- [ ] Tag an internal alpha only after fresh-clone validation passes.
- [ ] Do not push until the user explicitly asks.

## Current Residual Risks

- [~] The diff is large and needs human-readable commit boundaries.
- [ ] Console sector selector/evaluator mode remains open after the financial
  workflow smoke path.
- [ ] Production SaaS features remain out of scope: RBAC, SSO, tenant isolation,
  production secrets, deployment runbooks, and production retention.
