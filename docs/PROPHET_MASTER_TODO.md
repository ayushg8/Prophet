# Prophet Master TODO

Last updated: 2026-05-05

This is the full-system backlog for Prophet. It separates what is already real
in the buyer pilot from what still needs to be designed, built, verified, and
approved. The default posture stays defensive, fixture-backed, policy-bound, and
non-live unless a future customer policy explicitly authorizes a narrower mode.

## Status Key

- `[x]` Done in the current pilot package.
- `[~]` Started, usable for demos, but not production complete.
- `[ ]` Not started or not yet verified.
- `[BLOCKED]` Requires customer, legal, safety, or architecture decision first.
- `[DO NOT BUILD]` Outside the approved safety boundary for this repo.

## Current Ground Truth

- [x] Prophet has a repeatable local buyer pilot flow.
- [x] The pilot can generate asset seedsets, fixture-backed OSINT, forecasts,
  deterministic sandbox artifacts, evidence bundles, validation results, and
  integration handoff files.
- [x] The default pilot path is non-live and fixture-backed.
- [x] Lab exploit material has been removed from the public product tree.
- [x] Runtime outputs are ignored under `world-side/outputs/runtime/`,
  `cyber-side/outputs/runtime/`, `evidence/outputs/runtime/`,
  `assets/outputs/runtime/`, and `integrations/outputs/runtime/`.
- [~] The console has evidence, integration, readiness, and smoke-test coverage.
- [~] The policy system exists and is enforced in core pilot flows.
- [~] The audit trail exists for local pilot approvals and denials.
- [ ] Prophet is not production SaaS yet.
- [ ] Prophet does not yet have RBAC, SSO, tenant isolation, production secrets,
  customer retention automation, or deployment runbooks.
- [DO NOT BUILD] Do not add target-control, exploitation, or weaponization to
  this repo.

## Definition Of Done For The Current Pilot

- [x] One command runs the demo smoke path:
  `./scripts/run-pilot-demo-smoke.sh`.
- [x] Smoke output hashes are deterministic and verified.
- [x] Evidence includes forecast, seeded OSINT basis, asset seed summary,
  defense artifact, validation pass/failure/timeout evidence, safety
  attestation, policy ID/hash, approval record hash, and SHA-256 hashes.
- [x] Console acceptance can run with `npm run acceptance`.
- [x] Python unit suites cover cyber, world, assets, policy, sandbox, evidence,
  and integrations.
- [x] Playwright smoke checks the buyer console path.
- [x] Integration exports are review templates, not auto-deploying controls.
- [ ] A clean clone has been independently tested by a second operator.
- [ ] A packaged release tag has been created with the expected fixture hashes.
- [x] A customer-facing evaluator worksheet exists.
- [x] A customer-facing 3-minute walkthrough script exists.

## P0: Preserve The Safety Boundary

- [x] Keep live collection disabled by default.
- [x] Keep fixture-backed seeded OSINT as the default source mode.
- [x] Keep sandbox validation deterministic by default.
- [x] Keep VM scraping disabled by default.
- [x] Keep runtime outputs out of git.
- [x] Keep lab exploit files deleted from the public product tree.
- [x] Add a pre-commit safety check for unsafe terms, credentials, live IPs,
  private hostnames, and generated runtime files.
- [x] Add a release check that fails if runtime artifacts are staged.
- [x] Add a release check that fails if policy hash is missing from evidence,
  OSINT manifests, sandbox artifacts, or integration manifests.
- [x] Add a release check that fails if any console button triggers live
  collection without an explicit policy.
- [x] Add a release check that fails if a source catalog entry is enabled
  without policy allowlist coverage.
- [x] Add a short `SECURITY.md` section that defines the allowed research
  boundary for contributors.
- [x] Add a contributor checklist for safe fixture creation.
- [x] Add a customer data handling checklist before importing any customer
  artifact.

## P0: Commit And Release Hygiene

- [x] Split the current dirty worktree into intentional commits:
  safety cleanup, pilot CLI, policy, evidence, sandbox, console, docs, and CI.
- [x] Confirm deleted lab/demo exploit files are intentional in the final diff:
  current tracked diff has no deleted files.
- [ ] Run `git diff --check` before each commit.
- [ ] Run all Python unit suites before the final pilot commit.
- [x] Run `cd prophet-console && npm run acceptance`.
- [x] Run `cd prophet-console && npm audit --audit-level=moderate`.
- [x] Run the top-level smoke script from a temporary worktree-overlay clone.
- [x] Store smoke output hashes in a release note.
- [ ] Create a pilot release tag after the secret-history owner decision and
  final release checks.
- [x] Add a changelog entry for the buyer pilot package.
- [x] Add a rollback note for restoring the previous local demo state if needed.
- [x] Add a `make` or `just` wrapper if scripts keep multiplying.
- [x] Add a repo map explaining each top-level directory.

## P0: Massive Backlog Tracking

- [x] Add this master TODO.
- [x] Make `docs/PROPHET_TODO.md` a shorter operational view that points here.
- [x] Add owner and target version columns for each production milestone.
- [x] Add risk tags: `safety`, `security`, `buyer`, `infra`, `console`,
  `data`, `docs`.
- [x] Add a weekly review ritual for pruning completed or stale items.
- [x] Add a release readiness scorecard generated from this backlog.
- [x] Add a machine-readable backlog file if this needs to sync to GitHub
  Issues or Linear later.

## P1: Buyer Pilot Demo Flow

- [x] Asset seedset generation works from safe fixtures.
- [x] Seeded OSINT snapshot generation works from fixture files.
- [x] Forecast refresh works from the seedset and OSINT basis.
- [x] Evidence bundle generation works.
- [x] Evidence validation works.
- [x] Integration handoff export works.
- [x] Policy hash propagation works through the main pilot artifacts.
- [x] Runtime artifact hashes are covered by smoke verification.
- [x] Add a `--clean-runtime` option that removes only ignored runtime outputs
  after a confirmation gate.
- [x] Add a dry-run output that lists files that would be generated.
- [x] Add a plain-English final smoke summary for non-engineer evaluators.
- [x] Add demo duration timing to the smoke output.
- [x] Add a `--sector financial-workflow` smoke variant.
- [x] Add a second golden hash manifest for the second sector.
- [x] Add a fixture diff command to explain what changed between demo runs.
- [x] Add a failure-mode demo showing policy-blocked live behavior.
- [x] Add an evaluator mode that hides non-demo controls.

## P1: Pilot Documentation

- [x] `docs/PILOT_DEMO.md` documents the main evaluator path.
- [x] `docs/PILOT_SCOPE.md` defines what is and is not included.
- [x] `docs/BUYER_FAQ.md` answers buyer questions.
- [x] `docs/COMMERCIAL_READINESS.md` explains readiness and gaps.
- [x] `docs/DEFENSE_TECH_READINESS_REVIEW.md` gives a defense-tech view.
- [x] `docs/SAFETY_ARCHITECTURE.md` documents safety posture.
- [x] `docs/ASSET_IMPORT_GUIDE.md` documents customer-safe imports.
- [x] `docs/INTEGRATION_HANDOFF_GUIDE.md` documents SIEM/ticket exports.
- [x] Add a one-page "start here" README for evaluators.
- [x] Add a 3-minute buyer path from clone to evidence bundle.
- [x] Add a 12-minute analyst path through console, evidence, and exports.
- [x] Add a 30-minute technical path through policy, tests, and validation.
- [x] Add a demo operator checklist.
- [x] Add a troubleshooting guide for missing Node, Python, npm, or Playwright.
- [x] Add expected screenshot artifacts for the final console state.
- [x] Add redacted example output snippets with hashes.
- [x] Add a glossary for non-cyber readers.
- [x] Add "what this is not" language for live attack and live collection
  misunderstandings.

## P1: Evidence Bundle

- [x] Evidence JSON export exists.
- [x] Evidence Markdown export exists.
- [x] Policy ID/hash are included.
- [x] Approval record hash is included.
- [x] Forecast hash coverage is included.
- [x] Defense artifact hash coverage is included.
- [x] Safety attestation is included.
- [x] Integration export manifest references generated artifacts.
- [x] Add evidence schema version compatibility tests.
- [x] Add evidence bundle JSON Schema.
- [x] Add signed evidence manifest design.
- [ ] Add optional detached signature support.
- [x] Add validation of all evidence paths before export.
- [x] Add a summary table optimized for CISO review.
- [x] Add duplicate-source collapse in evidence summaries.
- [x] Add source freshness and source failure sections.
- [x] Add timeout/failure evidence paths for sandbox validation.
- [x] Add "no live target data included" assertion to each export.
- [x] Add a redaction report for each generated evidence bundle.

## P1: Policy System

- [x] Default pilot policy exists.
- [x] Policy examples exist for fixture-only, seeded OSINT, and localhost
  sandbox.
- [x] Policy linter exists.
- [x] OSINT source IDs are policy-bound.
- [x] Sandbox profiles are policy-bound.
- [x] Integration export restrictions are policy-bound.
- [x] Retention hints exist in policy.
- [x] Add a policy JSON Schema.
- [ ] Add policy migration handling.
- [x] Add policy comparison output.
- [x] Add customer policy review checklist.
- [x] Add policy signing design.
- [x] Add an allowlist review for every future source catalog entry.
- [x] Add explicit "no live targets" enforcement tests for every buyer-pilot
  CLI that accepts mutable operator, customer, source, policy, forecast,
  sandbox, evidence, or export input.
- [x] Add policy-bound console button enablement.
- [x] Add policy-blocked error states in the console.
- [x] Add policy drift detection between runtime outputs and the policy file.
- [x] Add policy retention enforcement, not only retention metadata.

## P1: Sandbox Runner

- [x] `sandbox_runner` runs a deterministic edge-appliance fixture profile.
- [x] The generated Direction C artifact passes `cyber-side/validator.py`.
- [x] Console evidence generation can prefer a valid latest runtime sandbox
  artifact.
- [x] Sandbox output includes policy metadata.
- [ ] Package sandbox runner as a reproducible container.
- [ ] Add container image hash to sandbox artifacts.
- [ ] Add no-egress runtime notes and tests for container mode.
- [ ] Add CPU, memory, disk, and timeout limits.
- [x] Add a second sandbox profile for another defensive class.
- [x] Add a negative validation fixture where the defense fails.
- [x] Add sandbox artifact schema.
- [x] Add sandbox run manifest with logs hash and no raw logs.
- [x] Add customer approval gate before non-fixture sandbox modes.
- [ ] Add ephemeral VM design, but keep disabled until approved.
- [x] Add artifact provenance chain from profile to evidence bundle.

## P1: Console

- [x] Forecast panel exists.
- [x] Preflight checklist exists.
- [x] Evidence panel exists.
- [x] Integration panel exists.
- [x] Readiness panel exists.
- [x] Browser smoke test exists.
- [x] Control evidence smoke test exists.
- [x] Add policy status panel.
- [x] Add sandbox artifact source badge: runtime artifact vs checked-in fixture.
- [x] Add source freshness indicators.
- [x] Add source failure indicators.
- [x] Add asset seed summary drilldown.
- [x] Add safer empty states for missing runtime outputs.
- [x] Add error states for policy-blocked actions.
- [x] Add export download controls for each SIEM/ticket artifact.
- [x] Add "fixture mode" visual proof in the console.
- [x] Add evaluator mode to hide experimental controls.
- [x] Add keyboard navigation checks.
- [x] Add accessibility smoke checks.
- [x] Add responsive screenshots for desktop and mobile.
- [ ] Add visual regression baseline if the console becomes buyer-facing.

## P1: CI And Local QA

- [x] Python tests run in CI.
- [x] Console lint/build run in CI.
- [x] Control evidence smoke runs in CI.
- [x] Optional Playwright smoke exists.
- [x] Dependency audit workflow exists.
- [x] Browser smoke uploads failure artifacts.
- [x] Add CI job for `git diff --check`.
- [x] Add CI job for policy lint against every policy example.
- [x] Add CI job for smoke hash verification.
- [x] Add CI job for unsafe text scanning.
- [x] Add CI job for generated runtime artifact detection.
- [x] Add CI job for docs link checking.
- [x] Add CI job for JSON Schema validation once schemas exist.
- [ ] Add CI matrix for supported Python and Node versions.
- [ ] Add coverage reporting for validator-heavy modules.
- [ ] Add CI status badge after the repository is hosted.

## P2: Asset And SBOM Inputs

- [x] CSV asset import exists.
- [x] Product-family, package, owner, exposure, and known-CVE fields are
  validated.
- [x] Unsafe hostnames, live IPs, credentials, URLs, and raw target names are
  rejected.
- [x] Import summaries include accepted and rejected rows.
- [x] Per-row errors are reported for customer cleanup.
- [x] A second sector fixture exists.
- [ ] Add CycloneDX fixture and parser.
- [ ] Add SPDX fixture and parser.
- [ ] Add purl normalization.
- [ ] Add CPE normalization.
- [ ] Add package ecosystem mapping.
- [ ] Add SBOM component deduplication.
- [ ] Add customer asset grouping by business function.
- [x] Add exposure classification guide.
- [ ] Add "unknown owner" safe fallback behavior.
- [ ] Add import preview before writing runtime outputs.
- [x] Add import manifest with raw input hash and sanitized output hash.
- [x] Add fixture generation docs for customer-safe examples.

## P2: Data And OSINT

- [x] Fixture-backed seeded OSINT source files exist.
- [x] Snapshot manifests exist.
- [x] Source catalog safety tests exist.
- [ ] Add official-source live collection policy gates.
- [x] Add source freshness metadata to forecasts.
- [x] Add source freshness metadata to evidence.
- [ ] Add source failure budget and fail-closed behavior. Design notes exist in
  `docs/PILOT_POLICY_REVIEW.md`; implementation remains gated on
  buyer/security-review demand or `build_next_slice`.
- [x] Add source license and terms notes.
- [ ] Add official vendor advisory source fixtures.
- [ ] Add CISA KEV fixture integration if license and policy allow.
- [ ] Add NVD/Vulnrichment freshness review if policy allows.
- [x] Add customer-approved source allowlist docs.
- [x] Add raw-to-sanitized boundary diagram.
- [x] Add source provenance manifest check for policy-listed default OSINT
  runtime outputs.
- [x] Add tests that raw scraper text never appears in evidence.
- [x] Add tests that live target URL fields never appear in default outputs.

## P2: Forecasting

- [x] Golden edge-appliance forecast exists.
- [x] Forecast uses asset and seeded OSINT context.
- [x] Forecast remains exploit-class oriented, not target-control oriented.
- [ ] Add forecast schema versioning.
- [ ] Add confidence calibration notes.
- [ ] Add forecast source attribution summary.
- [ ] Add forecast diff command between two runs.
- [ ] Add stale-source warnings.
- [ ] Add asset coverage warnings.
- [ ] Add sector-specific prioritization rules.
- [ ] Add negative tests for unsafe forecast fields.
- [ ] Add human review workflow before using forecasts outside fixture mode.
- [ ] Add "why this prediction appears" trace for each forecast item.

## P2: Integration Handoff

- [x] Splunk saved-search review template export exists.
- [x] Elastic detection-rule review template export exists.
- [x] Microsoft Sentinel analytic-rule review template export exists.
- [x] Jira remediation ticket export exists.
- [x] ServiceNow remediation task export exists.
- [x] Export manifest hashes every artifact.
- [x] Exports are validated for unsafe text and keys.
- [x] Console can generate integration handoff bundles.
- [ ] Add QRadar review template if customer demand exists.
- [ ] Add GitHub Issues review template if customer demand exists.
- [ ] Add Azure DevOps work item review template if customer demand exists.
- [ ] Add ServiceNow field mapping configuration.
- [ ] Add Jira project/issue-type mapping configuration.
- [x] Add integration export schema tests.
- [x] Add customer-filled placeholder validation.
- [x] Add export review checklist embedded in each handoff bundle.
- [x] Add SOC analyst sign-off fields.
- [x] Add one-click zip packaging for handoff artifacts.

## P2: Operator Identity And Audit

- [x] Operator label can be passed to control server requests.
- [x] Approval events are hash-chained.
- [x] Denial events are hash-chained.
- [x] Integration export events are hash-chained.
- [x] Sandbox artifact events are hash-chained.
- [x] Evidence includes approval record hash.
- [x] Denied approvals do not generate artifacts.
- [x] Add local audit export command.
- [x] Add audit log verification command.
- [x] Add audit retention cleanup.
- [x] Add audit redaction report.
- [x] Add operator identity format guidance.
- [x] Add signed operator approval design.
- [~] Add RBAC roles: viewer, analyst, approver, admin.
- [ ] Add SSO/SAML/OIDC design.
- [ ] Add approval quorum design for higher-risk modes.
- [ ] Add break-glass policy design for production incidents.

## P2: Security And CSO Backlog

- [~] Run a full secrets archaeology pass before any public release. Scanner now
  exists; latest full scan flags historical `LOG4SHELL_INSTRUCTIONS.md`
  password-like content that needs cleanup, rotation, or explicit exception;
  public release review stays blocked until the owner decision is recorded.
  See `docs/SECRET_HISTORY_REVIEW.md`.
- [ ] Add dependency pinning and update cadence.
- [ ] Add software supply-chain risk register.
- [ ] Add SBOM for Prophet itself.
- [ ] Add SLSA-style provenance target for release artifacts.
- [ ] Add static analysis for Python.
- [ ] Add static analysis for TypeScript.
- [ ] Add shellcheck for scripts.
- [x] Add threat model for pilot mode: `docs/SAFETY_ARCHITECTURE.md`.
- [x] Add threat model for production mode: `docs/THREAT_MODEL.md`.
- [ ] Add LLM/AI trust-boundary review if model-based components are added.
- [ ] Add secure coding checklist for future contributors.
- [ ] Add vulnerability disclosure process.
- [ ] Add dependency license review.
- [x] Add data classification labels for every artifact type.
- [ ] Add abuse-case review for every future live integration.

## P2: Developer Experience

- [x] Add root README quickstart.
- [x] Add `scripts/check-local-env.sh`.
- [x] Add clear Python version requirements.
- [x] Add clear Node version requirements.
- [x] Add virtualenv setup instructions.
- [x] Add npm install troubleshooting.
- [x] Add "first successful run" target under 3 minutes.
- [x] Add Makefile or Justfile.
- [x] Add architecture diagram.
- [x] Add module ownership map.
- [x] Add CLI reference for assets, OSINT, forecaster, sandbox, evidence,
  integrations, and policy.
- [x] Add `--help` examples to every CLI.
- [x] Add docs tests for documented commands.

## P3: Commercial Readiness

- [x] Buyer FAQ exists.
- [x] Pilot scope exists.
- [x] Commercial readiness doc exists.
- [x] Defense-tech readiness review exists.
- [x] Add pilot statement of work template.
- [x] Add CISO evaluator checklist.
- [x] Add data boundary appendix.
- [x] Add pricing and packaging memo.
- [x] Add customer success criteria template.
- [x] Add post-pilot conversion plan.
- [x] Add procurement/security questionnaire draft.
- [x] Add FedRAMP/CMMC/SOC 2 gap map.
- [x] Add export-control review placeholder.
- [x] Add data processing addendum notes.
- [x] Add support model for pilots.
- [x] Add incident communication template.
- [x] Add onboarding/offboarding checklist.
- [x] Add customer reference architecture.

## P3: Production Architecture

- [x] Decide first production model: single-tenant, customer-managed, or
  hosted multi-tenant.
- [x] Add production architecture doc.
- [ ] Add deployment architecture doc.
- [~] Add tenant isolation model.
- [ ] Add secrets handling design.
- [ ] Add customer data retention and deletion workflow.
- [ ] Add backup and restore plan.
- [ ] Add observability design.
- [ ] Add incident response playbook.
- [ ] Add formal disaster recovery target.
- [ ] Add environment promotion flow: dev, staging, pilot, production.
- [ ] Add release train policy.
- [ ] Add database choice and schema if server-side persistence is needed.
- [ ] Add artifact storage design.
- [ ] Add encryption-at-rest and encryption-in-transit requirements.
- [ ] Add customer key management design if required.
- [ ] Add on-prem/offline deployment option analysis.

## P3: Runtime And Operations

- [ ] Add production configuration system.
- [ ] Add structured logging.
- [ ] Add metrics.
- [ ] Add health checks.
- [ ] Add readiness checks.
- [ ] Add liveness checks if containerized.
- [ ] Add distributed trace plan if services split.
- [ ] Add error budgets for pilot services.
- [x] Add runbook for failed evidence generation.
- [x] Add runbook for failed sandbox validation.
- [x] Add runbook for policy-blocked evaluator actions.
- [x] Add runbook for dependency audit failures.
- [ ] Add deployment rollback procedure.
- [ ] Add production support dashboard.

## P3: Product Management

- [x] Define the primary buyer persona.
- [x] Define the primary evaluator persona.
- [x] Define the primary daily user persona.
- [x] Define the first paid wedge.
- [x] Decide whether Prophet is positioned as evidence automation, predictive
  defense planning, or a broader anticipatory defense platform.
- [x] Define what must be true for a paid pilot to convert.
- [x] Define the non-goals for the next 90 days.
- [x] Define the competitive set.
- [x] Add a roadmap with v0.1, v0.2, v0.3, v1.0 milestones.
- [x] Add pricing hypotheses.
- [x] Add pilot acceptance criteria.
- [x] Add success metrics: time to evidence, false-positive review burden,
  analyst time saved, policy-blocked unsafe action rate.
- [x] Add customer interview guide.
- [x] Add feedback collection form.
- [x] Add product validation plan.
- [x] Add customer discovery guide.
- [x] Add outreach playbook.
- [x] Add design partner pilot offer.
- [x] Add customer validation scorecard.

## P3: UX And Design

- [ ] Decide whether the console is a demo console or a daily analyst console.
- [ ] Add information architecture for daily analyst use.
- [ ] Add design system tokens.
- [ ] Add dark/light mode decision.
- [ ] Add empty, loading, error, and success states for every panel.
- [ ] Add export history view.
- [ ] Add audit history view.
- [ ] Add policy review view.
- [ ] Add asset import wizard.
- [ ] Add sandbox run view.
- [ ] Add evidence comparison view.
- [ ] Add pilot walkthrough mode.
- [ ] Add accessibility target and test plan.
- [ ] Add browser compatibility target.

## P4: Research And Advanced Modeling

- [ ] Decide whether Prophet needs ML/LLM prediction or can stay rules plus
  evidence assembly for v0.x.
- [ ] Add model card if a model-based component is introduced.
- [ ] Add eval set for forecast quality.
- [ ] Add hallucination and unsafe-output guardrails for generated text.
- [ ] Add deterministic mode for buyer evidence.
- [ ] Add reproducibility manifest for any model output.
- [ ] Add human review gate for generated recommendations.
- [ ] Add adversarial prompt injection review for OSINT inputs.
- [ ] Add model/data provenance to evidence.
- [ ] Add "no customer data in model training" policy unless explicitly
  approved by contract.

## P4: Governance And Compliance

- [ ] Add formal data classification policy.
- [ ] Add data retention automation.
- [ ] Add deletion workflow.
- [ ] Add audit review workflow.
- [ ] Add access review workflow.
- [ ] Add change management workflow.
- [ ] Add vendor risk register.
- [ ] Add customer environment boundary documentation.
- [x] Add compliance evidence map for SOC 2, ISO 27001, CMMC, FedRAMP, and
  internal security review.
- [ ] Add legal review checklist for live collection.
- [ ] Add legal review checklist for defense customer use cases.
- [ ] Add export-control review checklist.

## P4: Testing Matrix

- [x] Cyber unit tests.
- [x] World-side unit tests.
- [x] Asset unit tests.
- [x] Policy unit tests.
- [x] Sandbox unit tests.
- [x] Evidence unit tests.
- [x] Integration unit tests.
- [x] Console lint/build.
- [x] Console control evidence smoke.
- [x] Console browser smoke.
- [x] Fresh clone smoke on macOS.
- [x] Fresh clone smoke on Linux.
- [ ] Python version matrix.
- [ ] Node version matrix.
- [x] CI smoke hash verification.
- [x] Docs command verification.
- [x] Safety scan verification.
- [x] Schema validation verification.
- [x] Negative sandbox validation.
- [x] Policy-blocked live mode tests.

## P4: Documentation Map

- [x] Root README: quickstart and repo map.
- [x] `docs/PILOT_DEMO.md`: evaluator path.
- [x] `docs/PILOT_SCOPE.md`: included and excluded surfaces.
- [x] `docs/BUYER_FAQ.md`: buyer Q&A.
- [x] `docs/COMMERCIAL_READINESS.md`: production gap narrative.
- [x] `docs/DEFENSE_TECH_READINESS_REVIEW.md`: defense-tech review.
- [x] `docs/SAFETY_ARCHITECTURE.md`: safety boundary.
- [x] `docs/PILOT_POLICY_REVIEW.md`: policy review.
- [x] `docs/INTEGRATION_HANDOFF_GUIDE.md`: integration templates.
- [x] `docs/ASSET_IMPORT_GUIDE.md`: asset input path.
- [x] `docs/RELEASE_CHECKLIST.md`: release gate.
- [x] `docs/PROPHET_MASTER_TODO.md`: full backlog.
- [x] `docs/PRODUCTION_ARCHITECTURE.md`: future production design.
- [x] `docs/THREAT_MODEL.md`: future formal threat model.
- [x] `docs/PRODUCTION_EXECUTION_PLAN.md`: production execution roadmap.
- [x] `docs/COMPLIANCE_GAP_MAP.md`: production security review gap map.
- [x] `docs/production-readiness-backlog.json`: machine-readable production backlog.

## P5: Future Product Tracks

- [ ] Customer-managed pilot appliance.
- [ ] Hosted single-tenant pilot.
- [ ] Offline evidence package.
- [ ] Analyst console.
- [ ] CISO evidence dashboard.
- [ ] SIEM/ticket review workflow.
- [ ] SBOM ingestion.
- [ ] Official-source live collection with policy approval.
- [ ] Sandbox container execution.
- [ ] Sandbox VM execution.
- [ ] Production audit export.
- [ ] Production RBAC/SSO.
- [ ] Compliance evidence automation.

## 7-Day Execution Plan

- [x] Day 1: Convert this working tree into reviewable commits.
- [x] Day 1: Run full Python and console acceptance.
- [x] Day 1: Fix any smoke or lint regressions.
- [x] Day 2: Add root evaluator README and 3-minute path.
- [x] Day 2: Add policy status panel or console policy-blocked states.
- [x] Day 3: Add evidence JSON Schema and validation tests.
- [x] Day 3: Add sandbox artifact schema and validation tests.
- [x] Day 4: Add CI jobs for smoke hashes, policy lint, and unsafe text scan.
- [x] Day 5: Add audit export and audit verification command.
- [x] Day 5: Add audit retention cleanup.
- [x] Day 6: Add customer evaluator worksheet and CISO checklist.
- [~] Day 7: Run fresh clone smoke and package an internal pilot release.

## 30-Day Execution Plan

- [ ] Week 1: Stabilize the local buyer pilot package.
- [ ] Week 1: Finish release docs and smoke gates.
- [ ] Week 2: Add schemas for policy, evidence, sandbox, integrations, and
  asset imports.
- [ ] Week 2: Add deeper unsafe-content scanning and mutation tests.
- [ ] Week 3: Package sandbox runner in a reproducible container.
- [ ] Week 3: Add a second sandbox defensive profile.
- [ ] Week 4: Add production architecture, threat model, and customer data
  boundary docs.
- [ ] Week 4: Prepare a paid pilot SOW, success criteria, and security review
  packet.

## 90-Day Execution Plan

- [ ] Month 1: Ship buyer pilot package with deterministic evidence and
  integration handoffs.
- [ ] Month 2: Add policy-governed customer asset/SBOM ingestion and sandbox
  hardening.
- [ ] Month 2: Run first controlled evaluator trials with only fixture or
  customer-approved sanitized inputs.
- [ ] Month 3: Decide production architecture based on buyer demand.
- [ ] Month 3: Build RBAC/SSO, audit export, retention automation, and
  deployment runbooks if paid pilot demand justifies it.

## Strict Non-Goals Until Explicitly Approved

- [DO NOT BUILD] Offensive exploitation workflows.
- [DO NOT BUILD] Live target validation against third-party systems.
- [DO NOT BUILD] Credential collection.
- [DO NOT BUILD] Raw scraper text in evidence outputs.
- [DO NOT BUILD] Private customer hostnames in committed fixtures.
- [DO NOT BUILD] Real IP addresses in committed fixtures.
- [DO NOT BUILD] Automated deployment of detections into customer SIEMs.
- [DO NOT BUILD] Automated ticket creation in customer systems.

## Immediate Next Commands

Run these before calling the current pilot package stable:

```bash
git diff --check
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

## Final Reality Check

Prophet is pilot-ready only for the documented, fixture-backed defensive
workflow. It is not done as an entire defense-tech platform or production
ready. The next serious milestone is a clean, tagged, reproducible buyer pilot
release with policy, evidence, audit, safety, console, and integration handoff
all verified from a fresh clone.
