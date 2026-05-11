# Prophet Completion Plan

Date: 2026-05-05

Historical context: this is an older completion-plan artifact recovered during
the `/goal` salvage. Use `docs/CODEX_CEO_FINISH_BRIEF.md`,
`docs/PROPHET_COMPLETION_AUDIT.md`, `docs/PROPHET_TODO.md`, and the validation
dashboard as the current source of truth. Do not treat unchecked items here as
permission to build production scope while customer validation remains
`insufficient_data`.

Method: GStack autoplan-style review across CEO/founder, engineering, CSO, QA,
and DX lenses. Intermediate decisions are auto-decided using completeness,
explicitness, reuse, and defensive safety as the tie-breakers.

## Product North Star

Prophet becomes a controlled defensive exposure prioritization product:

1. Ingest approved public context plus customer-owned asset/SBOM metadata.
2. Forecast pressure windows and likely exposure classes.
3. Generate reviewable defense artifacts and SOC handoff templates.
4. Validate only in approved fixture, localhost, or customer sandbox profiles.
5. Emit signed, policy-bound evidence for operators, CISOs, and mission owners.

Prophet does not become a live-target exploit runner, autonomous patch deployer,
or raw intelligence warehouse.

## Completion Definition

### Paid Pilot Complete

- One-command evaluator path works from fresh clone.
- Console can refresh demo forecast, generate sandbox artifact, generate
  evidence, and export SIEM/ticketing handoff files.
- Customer-safe CSV asset inventory import exists with row-level rejection.
- Policy linter enforces allowed modes, source IDs, sandbox profiles, output
  paths, and safety controls.
- Local audit log captures operator approvals and export events with hashes.
- Buyer docs include SOW, data boundary appendix, CISO checklist, SOC export
  checklist, and success criteria.
- Full local acceptance suite passes.

### Production Design Complete

- Single-tenant vs multi-tenant architecture is decided and documented.
- RBAC/SSO, tenant isolation, retention/deletion, backup/restore, and incident
  response are specified.
- Sandbox runner has a reproducible container profile with image hash,
  resource limits, and no-egress controls.
- Evidence and approval records are signed or hash-chained.
- Formal threat model and compliance evidence map exist.

### Controlled Production Complete

- Customer data boundary is enforced in code.
- Deployment target has secrets handling, observability, backups, retention,
  SSO, RBAC, and audit export.
- Production sandbox orchestration is approved, no-egress, and scoped by policy.
- Release process includes dependency audit, golden artifact hashes, Playwright
  artifacts, schema compatibility tests, and signoff checklist.

## Critical Path

1. Console integration export workflow.
2. Customer CSV asset import.
3. Policy-bound source and sandbox profile enforcement.
4. Operator identity and audit hash chain.
5. Golden artifact hash tests and release checklist.
6. Buyer docs package.
7. Sandbox container profile design.
8. Second sector fixture.
9. Production architecture and security design.

## P0: Finish Buyer Pilot Surface

- [x] Add console integration export button/panel.
- [x] Add `/api/integrations/demo-export` control endpoint.
- [x] Show manifest hash, export file count, and output paths in the console.
- [x] Add control smoke assertions for integration export.
- [x] Add browser smoke coverage for the export panel.
- [x] Add SOC review checklist for generated SIEM/ticket handoff templates.
- [x] Add integration one-pager explaining review-template-only semantics.

## P1: Customer Asset Import

- [x] Define CSV columns and required fields.
- [x] Implement `assets.import_csv` parser.
- [x] Reject live IPs, hostnames, URLs, credentials, raw target names, and
  unsupported columns.
- [x] Emit accepted/rejected row counts and row-level cleanup errors.
- [x] Convert accepted rows into `asset_inventory.v0.1`.
- [x] Add a safe fictional CSV fixture.
- [x] Add tests for accepted import, unsafe rejection, and deterministic hashes.
- [x] Wire import into docs and the root smoke path.

## P2: Policy Enforcement

- [x] Schema-versioned policy file.
- [x] Policy examples and linter.
- [x] Add `allowed_source_ids` and enforce them in seeded OSINT snapshot
  generation.
- [x] Add `allowed_sandbox_profiles` and enforce them in `sandbox_runner`.
- [x] Add retention hints and lint them.
- [ ] Add policy comparison against the packaged default.
- [x] Add policy-bound restrictions for integration exports.
- [x] Include policy hash in every runtime manifest.

## P3: Operator Identity And Audit

- [x] Add local operator identity to control requests.
- [x] Add denial path for approval gate.
- [x] Write immutable local audit events under ignored runtime outputs.
- [x] Hash-chain audit events.
- [x] Include approval event hash in evidence bundles.
- [ ] Export audit manifest for customer security review.
- [ ] Document future SSO/RBAC roles: viewer, analyst, approver, admin.

## P4: Sandbox And Validation

- [ ] Add container profile design doc.
- [ ] Add Dockerfile or OCI build notes for deterministic local validation.
- [ ] Include image digest, profile ID, no-egress statement, and resource limits
  in sandbox artifacts.
- [ ] Add negative validation fixture where defense does not block.
- [x] Add timeout/failure evidence path.
- [ ] Require policy approval before any non-fixture mode.

## P5: Buyer Documentation

- [ ] Pilot statement of work template.
- [ ] Data boundary appendix.
- [ ] CISO evaluator checklist.
- [ ] SOC export review checklist.
- [ ] Customer success criteria template.
- [ ] Pricing and packaging memo.
- [ ] Production gap register with owner and target version.
- [ ] Demo scripts for 3-, 12-, and 30-minute walkthroughs.

## P6: Quality Gates

- [x] Golden hash tests for smoke output.
- [ ] Unsafe-text mutation tests for evidence and integration exports.
- [ ] CLI schema compatibility tests.
- [x] Dependency audit workflow.
- [x] Playwright screenshot/trace artifacts on failure.
- [x] Release checklist and PR safety template.
- [ ] Coverage report for validator-heavy modules.

## P7: Production Track

- [ ] Single-tenant vs multi-tenant decision.
- [ ] Deployment architecture.
- [ ] Secrets handling design.
- [ ] Customer data retention/deletion workflow.
- [ ] SSO/SAML/OIDC plan.
- [ ] Tenant isolation model.
- [ ] Logging and observability model.
- [ ] Backup and restore plan.
- [ ] Formal STRIDE threat model.
- [ ] Incident response playbook.
- [ ] Compliance evidence map.

## Auto-Decisions

| Decision | Classification | Choice | Rationale |
|---|---|---|---|
| Next implementation slice | Mechanical | Console integration export | Backend exporter already exists; the buyer-visible gap is triggering and inspecting it from the console. |
| Scope posture | Mechanical | Paid pilot before production | Current system is credible for fixture/localhost evaluation, not production. |
| Safety posture | Mechanical | Keep live targets blocked | Defense-tech trust depends on default non-live behavior. |
| Policy direction | Mechanical | Extend current linter | Reuse existing schema and tests before adding broader authorization complexity. |
| QA bar | Mechanical | Full acceptance suite | Buyer path spans Python, control server, and browser. |

## Context-Rot Guardrail

At each long-running checkpoint:

1. Re-read `docs/PROPHET_TODO.md`, this plan, and `git status --short`.
2. Log the current GStack timeline event.
3. Run focused tests for touched modules before widening to acceptance.
4. Update TODO status only after tests pass.
5. Do not revert dirty files unless the user explicitly asks.
