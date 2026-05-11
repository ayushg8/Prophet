# Prophet Full Finish Plan

Date: 2026-05-05

Historical context: this broader V1 plan was recovered during the `/goal`
salvage. Use `docs/CODEX_CEO_FINISH_BRIEF.md`,
`docs/PROPHET_COMPLETION_AUDIT.md`, `docs/PROPHET_TODO.md`, and the validation
dashboard as the current source of truth. Do not start production work from this
plan while customer validation remains `insufficient_data`.

Method: gstack-style CEO, customer, engineering, CSO, QA, and DX loop.

## Finish Definition

Prophet is finished for V1 when a customer can bring approved metadata, run a
policy-bounded defensive forecast, review a defense package, validate it only in
an approved sandbox, export evidence and handoff templates, and audit who
approved what without Prophet ever becoming a live-target exploit runner.

V1 is not "autonomous cyber offense." V1 is a defensive exposure
prioritization, sandbox validation, and evidence workflow.

## Current State

Completion estimates:

- Internal alpha: 65-72%.
- Friendly customer pilot: 45-55%.
- Paid pilot package: 38-48%.
- V1 controlled production: 20-30%.

The system already has deterministic forecast, fixture-backed seeded OSINT,
asset/SBOM seedsets, policy linting, safe exploit-class portfolio, localhost
sandbox artifact, evidence bundle, SIEM/ticketing handoff exporter, console
readiness, console evidence, console handoff export, CI, and acceptance checks.

The remaining work is mostly about customer input, policy/audit hardening,
production deployment, multi-scenario proof, and repeatable release discipline.

## Customer Promise

The strongest customer-facing sentence:

> Prophet tells a mission owner which exposure class to harden before a pressure
> window, produces a reviewable defense package, validates it in an approved
> sandbox, and exports an audit trail for the SOC and leadership.

Every feature should support one of these jobs:

- Explain why this exposure class matters now.
- Prove the input and source basis.
- Generate a safe review package.
- Validate a defensive block in a controlled environment.
- Export evidence and review templates.
- Preserve policy, approval, and audit context.

## Workstream 1: Customer Input

Goal: accept customer-owned metadata safely.

Tasks:

- Define CSV asset inventory schema. Done for simple CSV.
- Add CSV import CLI and fixture. Done.
- Add row-level validation and rejection report. Done.
- Reject hostnames, IPs, URLs, credentials, secrets, raw target names, and
  payload-like text.
- Add CycloneDX parser.
- Add SPDX parser.
- Hash original customer-owned input without committing unsafe raw files.
- Show accepted/rejected counts in console.
- Add second sector fixture to prove Prophet is not hardcoded to edge appliances.

Done when:

- A customer can import a small approved CSV/SBOM fixture.
- Unsafe rows are rejected with actionable cleanup reasons.
- The derived seedset feeds forecast/evidence without storing forbidden fields.

## Workstream 2: Policy And Audit

Goal: make every run policy-bound and reviewable.

Tasks:

- Extend policy examples with source allowlists, validation profiles, export
  restrictions, and retention hints. Done.
- Enforce allowed source IDs in seeded OSINT snapshot generation. Done.
- Enforce allowed sandbox profiles. Done.
- Enforce policy-bound integration export restrictions. Done for review
  templates.
- Add policy comparison output against the default pilot policy.
- Add operator identity field to control server requests. Done for local console labels.
- Add approval denial path. Done for evidence denial audit without bundle generation.
- Add hash-chained local audit log under ignored runtime output. Done for approval,
  denial, and integration export events.
- Include approval event hash in evidence and integration manifests. Done.
- Add audit export for customer security review.

Done when:

- A customer-specific policy can narrow sources, validation, exports, and
  retention.
- Every generated artifact links to a policy hash and approval hash.
- Denied approvals cannot generate evidence or handoff artifacts.

## Workstream 3: Console Workflow

Goal: make the console usable by a customer evaluator without reading code.

Tasks:

- Keep Alpha Readiness visible and read-only.
- Keep Integration Handoff export in the operator flow.
- Add policy status detail in readiness or a compact policy panel.
- Add asset import/upload review screen.
- Add source freshness and failure indicators.
- Add sandbox artifact source badge: checked-in fixture vs runtime artifact.
- Add policy-blocked error states for every controlled action.
- Add export path and hash display for evidence and handoff files.
- Add evaluator mode that hides non-demo controls.
- Remove or soften lab-only wording in customer-facing views.
- Add accessibility pass for buttons, status regions, and scrollable panels.

Done when:

- A non-engineer evaluator can run refresh, defense fixture, evidence, handoff,
  readiness, and review without terminal help except starting local servers.

## Workstream 4: Sandbox And Validation

Goal: make validation reproducible and acceptable to security reviewers.

Tasks:

- Package sandbox runner as a reproducible container.
- Add container image hash to sandbox artifacts.
- Document no-egress and resource limits.
- Add second sandbox profile.
- Add negative validation fixture where defense does not block.
- Add timeout and failure evidence path. Done for the fixture-backed evidence
  bundle; container runtime timeout controls remain a separate sandbox task.
- Keep the sandbox run manifest with log hashes and no raw logs in the smoke
  path.
- Add customer approval gate before any non-fixture sandbox mode.

Done when:

- A reviewer can reproduce the sandbox artifact and prove no external target was
  touched.

## Workstream 5: OSINT And Source Governance

Goal: make source basis trustworthy without raw collection leakage.

Tasks:

- Add official-source live collection policy gates.
- Add source freshness metadata to forecast and evidence.
- Add required-source failure budgets.
- Fail closed when required sources are unavailable.
- Document source license/terms review notes.
- Collapse duplicate source refs in evidence summaries.
- Document customer-approved source allowlist process.
- Document raw-to-sanitized boundary diagram.
- Verify provenance manifests for policy-listed default runtime snapshots.

Done when:

- Evidence explains which source classes were used, how fresh they are, and why
  raw text never crossed the boundary.

## Workstream 6: Production Architecture

Goal: make V1 deployable in a controlled customer environment.

Tasks:

- Decide single-tenant vs multi-tenant first architecture.
- Add deployment architecture doc.
- Add secrets handling design.
- Add RBAC and SSO/SAML/OIDC plan.
- Add tenant isolation model.
- Add retention/deletion workflow.
- Add logging and observability model.
- Add backup and restore plan.
- Add formal STRIDE threat model.
- Add incident response playbook.
- Add compliance evidence map.

Done when:

- A customer security team can review deployment, data flow, identity, logging,
  retention, and incident response before a pilot.

## Workstream 7: Quality And Release

Goal: every pilot build is reproducible.

Tasks:

- Keep `npm run acceptance` green.
- Add golden artifact hash tests.
- Add mutation tests for unsafe evidence/export text.
- Add fixture freshness checks.
- Add API contract tests for every control endpoint.
- Add Playwright screenshot artifacts on failure.
- Add dependency audit workflow.
- Add release checklist.
- Add PR template with safety checklist.
- Add changelog and build note discipline.

Done when:

- A release can be recreated from source and every customer-facing artifact has
  stable hashes or an intentional change note.

## Recommended Build Order

1. Policy-bound source and sandbox allowlists.
2. Operator identity, denial path, and audit hash chain.
3. Console policy/status and asset import views.
4. Golden artifact hash tests and release checklist.
5. Second sector fixture and sandbox profile.
6. Production architecture, threat model, and deployment docs.
7. RBAC/SSO, retention, observability, backup, and incident response.

## Strict Self-Check Loop

For each future gstack loop:

1. Read `docs/PROPHET_TODO.md` and this plan.
2. Pick the highest customer-visible item that does not widen unsafe scope.
3. Implement the smallest complete slice.
4. Add unit/API/browser coverage proportional to risk.
5. Run `cd prophet-console && npm run acceptance`.
6. Run `git diff --check`.
7. Update TODO and this plan if scope or status changes.
8. Leave no unexplained running process.
