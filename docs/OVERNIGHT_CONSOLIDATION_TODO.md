# Overnight Consolidation TODO

Last updated: 2026-05-05

Historical context: this checklist records the May 2026 overnight consolidation
pass. For current product direction, use `docs/CODEX_CEO_FINISH_BRIEF.md`,
`docs/PROPHET_COMPLETION_AUDIT.md`, `docs/PROPHET_TODO.md`, and the validation
dashboard as the source of truth. Do not use this checklist as authorization
for production platform work while customer validation remains
`insufficient_data`.

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
- [x] Fill in commit hashes after local commits are created.
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

- [x] Commit 1: `13f16a8` safety cleanup and deleted lab/demo exploit material.
- [x] Commit 2: `347d1f0` asset/SBOM fixtures, CSV import, seedset generation,
  and tests.
- [x] Commit 3: `3263e82` seeded OSINT snapshotting, source catalog safety,
  freshness, and forecaster enrichment.
- [x] Commit 4: `4fa99dc` policy schema, linter, comparison, allowlists,
  retention, and policy tests.
- [x] Commit 5: `cdd8e34` sandbox runner profiles, artifacts, manifests,
  negative fixtures, schemas, and tests.
- [x] Commit 6: `4987893` evidence bundle, audit log, audit export, retention
  evidence, JSON Schema, and evidence tests.
- [x] Commit 7: `17952de` integration handoff exports, validation, docs, and
  tests.
- [x] Commit 8: `d00e619` console evidence, integration, policy, readiness, and
  browser smoke work.
- [x] Commit 9: `e1b1551` CI, release safety checks, pre-commit hook, smoke
  scripts, second-sector hashes, and script tests.
- [x] Commit 10: `0357cc0` buyer/evaluator docs, worksheets, walkthroughs,
  glossary, troubleshooting, and consolidation report.

## P1: Post-Commit Review

- [x] Run `git log --oneline --decorate -12` and verify commit order is legible.
- [x] Run `git status --short --untracked-files=all` and confirm only ignored
  runtime outputs remain unstaged.
- [x] Re-run `git diff --check`.
- [x] Run the full Python matrix.
- [x] Run both smoke sectors.
- [x] Run `cd prophet-console && npm run acceptance`.
- [x] Run `cd prophet-console && npm audit --audit-level=moderate`.
- [x] Run a GStack review/timeline log for the consolidation pass.

## P2: Fresh Clone Gate

- [x] Create a fresh clone or fresh worktree after local commits exist.
- [x] Run `./scripts/run-pilot-demo-smoke.sh`.
- [x] Run `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`.
- [x] Run `cd prophet-console && npm ci && npm run acceptance`.
- [x] Confirm no private context, live target, credential, raw scraper text, or
  generated runtime artifact is required.

## P2: Release Candidate

- [ ] Add release note with policy hash, evidence hashes, smoke manifests, and
  known gaps.
- [~] Tag an internal alpha only after fresh-clone validation passes.
- [ ] Do not push until the user explicitly asks.

## Current Residual Risks

- [x] The diff is large and needs human-readable commit boundaries.
- [ ] Console sector selector/evaluator mode remains open after the financial
  workflow smoke path.
- [ ] Production SaaS features remain out of scope: RBAC, SSO, tenant isolation,
  production secrets, deployment runbooks, and production retention.
