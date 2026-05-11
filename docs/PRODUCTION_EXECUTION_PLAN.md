# Prophet Production Execution Plan

Date: 2026-05-05

This plan turns Prophet from a repeatable local buyer pilot into a controlled
production defense-tech product. The current pilot is valuable because it is
safe, deterministic, policy-bound, and testable. Production work should preserve
that posture while adding identity, tenancy, durable storage, approved customer
data, real operations, and security-review evidence.

Do not treat this as permission to build the whole platform before buyer pull.
The demand-validation source of truth is `docs/PRODUCT_VALIDATION_PLAN.md`.
Production implementation should proceed only after the validation scorecard
shows `build_next_slice` from real anonymized customer interviews.
`pilot_pull_detected` means convert the design partner first; it is not yet a
production build gate.

## Production Definition

Prophet is production-ready when a customer can:

1. Authenticate with an approved identity provider.
2. Work inside an isolated tenant or customer-managed deployment.
3. Import approved customer-owned asset, SBOM, and security metadata.
4. Generate policy-bound forecasts, sandbox validation summaries, evidence, and
   integration handoffs.
5. Review and approve every higher-risk action with durable audit trails.
6. Export to real SOC and ticketing systems in dry-run or approved push mode.
7. Verify evidence, approvals, policies, and generated artifacts by hash.
8. Operate the system with logs, metrics, backups, incident response, and
   rollback procedures.
9. Pass a customer security review without relying on private explanations from
   the builders.

Prophet is not production-ready if it is only a local demo, if tenant isolation
is convention-only, if approvals are local labels only, if generated artifacts
are not durable, if source/data retention is not enforceable, or if deployment
depends on manual repo knowledge.

## Hard Non-Goals

- No live target validation against third-party systems.
- No exploit payload generation.
- No autonomous patch deployment.
- No raw source capture warehouse.
- No production push to SIEM, EDR, ticketing, or cloud systems without customer
  approval, RBAC, policy allowlist, audit event, and rollback metadata.
- No multi-tenant hosted production launch before tenant isolation tests and
  security review are complete.

## First Product Shape

The first production shape should be a customer-managed or single-tenant pilot
appliance, not a broad hosted multi-tenant SaaS. That choice reduces blast
radius, simplifies security review, and matches defense buyers who often prefer
controlled environments for early pilots.

Recommended sequence:

1. Local pilot release.
2. Customer-managed single-tenant staging stack.
3. Hosted single-tenant pilot, if a customer wants hosted operations.
4. Multi-tenant SaaS only after tenant isolation, operations, and compliance
   controls are proven.

## Milestone Plan

The machine-readable source of truth is
`docs/production-readiness-backlog.json`. The human summary is below.

| Milestone | Target | Outcome |
|---|---:|---|
| M0 Pilot Release Baseline | v0.3 | Merge, tag, and independently verify the current buyer pilot. |
| M1 Production Architecture And Security Design | v0.4 | Architecture, threat model, compliance gap map, and measurable backlog. |
| M2 Durable Platform Foundation | v0.5 | API, durable database, artifact store, jobs, and config. |
| M3 Identity, RBAC, And Tenant Isolation | v0.6 | OIDC/RBAC/tenant boundaries with negative tests. |
| M4 Customer Data And Source Operations | v0.7 | SBOM/customer metadata ingestion, source freshness, retention/deletion. |
| M5 Sandbox And Validation Hardening | v0.7 | Containerized no-egress sandbox with provenance and resource limits. |
| M6 Real Integration Workflows | v0.8 | Customer-approved dry-run and push paths for SOC/ticketing systems. |
| M7 Observability, Deployment, And Operations | v0.9 | Logs, metrics, health checks, backup/restore, deployment runbooks. |
| M8 Security Review And Compliance Packet | v1.0 | Customer security packet, supply-chain packet, external review readiness. |

## Critical Path

1. Close the pilot release baseline.
2. Build the production-shaped API and persistence layer.
3. Add tenant-scoped data model before adding more live/customer data.
4. Add RBAC and OIDC before adding production approvals.
5. Move evidence, policies, approvals, and exports into durable immutable
   storage.
6. Add customer-owned SBOM and asset ingestion with retention controls.
7. Containerize the sandbox runner with no-egress/resource controls.
8. Add dry-run integrations, then approval-required push integrations.
9. Add observability, backups, deployment runbooks, and incident response.
10. Package compliance/security evidence.

## 30-Day Execution Plan

### Week 1: Release And Architecture Lock

- Run the product validation sprint in `docs/PRODUCT_VALIDATION_PLAN.md`.
- Keep PR #5 ready for internal buyer-pilot review.
- Merge the pilot package and tag the fixture/hash set only after the
  historical secret-history owner decision and final release checks are clear.
- Run fresh-clone smoke on macOS and Linux.
- Publish release notes with generated artifact hashes.
- Keep `scripts/production-readiness-scorecard.py` green in CI.
- Review `docs/PRODUCTION_ARCHITECTURE.md`, `docs/THREAT_MODEL.md`, and
  `docs/COMPLIANCE_GAP_MAP.md` as the production baseline.

Exit criteria:

- Pilot release is reproducible.
- Production readiness scorecard validates.
- No production work is started without a target milestone and acceptance gate.

### Week 2: Platform Skeleton

- Add an API service boundary for runs, policies, evidence, integrations, and
  readiness.
- Add a local development database profile.
- Add migration files for tenant, policy, run, artifact, approval, and audit
  tables.
- Add content-addressed artifact storage abstraction.
- Add job status abstraction for forecast, sandbox, evidence, and export work.

Exit criteria:

- Local tests create tenant-scoped runs and artifacts.
- Pilot smoke can still run without production services.
- New production services fail closed without policy and tenant context.

### Week 3: Identity And Tenant Enforcement

- Define organization, tenant, workspace, user, role, service-account, and
  policy-binding models.
- Add RBAC permissions for viewer, analyst, approver, admin, and auditor.
- Add OIDC design and local development identity adapter.
- Add negative tests proving tenant A cannot read tenant B data.
- Add server-side checks for every evidence/export action.

Exit criteria:

- Every persisted customer object has tenant scope.
- Authorization is tested at the service layer, not only in the console.
- Local operator labels remain demo-only and cannot masquerade as production
  identity.

### Week 4: Data And Evidence Durability

- Add SBOM ingestion for CycloneDX first, then SPDX.
- Add source failure budgets and fail-closed behavior for required sources.
- Add immutable evidence bundle storage with bundle lifecycle states.
- Add signed evidence manifest design and optional detached signature path.
- Add retention and deletion workflow design, then first local implementation.

Exit criteria:

- Approved customer metadata can enter without unsafe identifiers.
- Evidence is reproducible from stored inputs, policy hash, and artifact hashes.
- Expired runtime/customer metadata can be reported and deleted under policy.

## 60-Day Execution Plan

- Containerize sandbox runner.
- Add no-egress and resource-limit checks.
- Add image digest and run manifest provenance to evidence.
- Add dry-run connectors for SIEM and ticketing.
- Add secrets manager abstraction.
- Add structured logs, health checks, metrics, and runbooks.
- Draft customer security review packet.

Exit criteria:

- A single-tenant customer-managed pilot stack can be deployed and operated.
- Dry-run integrations validate shape without changing production systems.
- Operators can diagnose failed runs without reading source code.

## 90-Day Execution Plan

- Add approval-required integration push mode only for approved customer
  sandbox tenants.
- Complete backup/restore drills.
- Complete incident response playbook.
- Complete NIST/CMMC-oriented security packet and POA&M.
- Run secrets archaeology and public release review.
- Schedule external security review.

Exit criteria:

- Prophet is credible for paid controlled production pilots.
- Critical and high security gaps are closed or tracked with accepted owner and
  date.
- Customer security review can proceed from docs and artifacts.

## Workstream Backlog

### Platform

- API service.
- Database schema.
- Migrations.
- Artifact store.
- Job queue.
- Config validation.
- Local stack.
- Deployment profiles.

### Identity And Authorization

- Tenant model.
- User model.
- RBAC.
- OIDC.
- SAML plan.
- Service accounts.
- Approval quorum.
- Break-glass.

### Customer Data

- CSV import hardening.
- CycloneDX parser.
- SPDX parser.
- PURL normalization.
- CPE normalization.
- Source provenance.
- Data classification.
- Retention/deletion.

### Evidence And Audit

- Immutable evidence lifecycle.
- Signed manifests.
- Approval record signatures.
- Audit export.
- Audit retention.
- Chain verification.
- Evidence diffing.
- Revocation metadata.

### Sandbox

- Reproducible container.
- No-egress.
- Resource limits.
- Image digest.
- Run manifest.
- Negative validation.
- Timeout handling.
- Non-fixture approval gate.

### Integrations

- Splunk.
- Elastic.
- Sentinel.
- Jira.
- ServiceNow.
- Secrets manager.
- Dry-run mode.
- Approval-required push mode.
- Rollback/revoke metadata.

### Operations

- Logs.
- Metrics.
- Traces.
- Health checks.
- Readiness checks.
- Backup/restore.
- Deployment runbooks.
- Incident response.
- Support dashboard.

### Security And Compliance

- Threat model.
- Control matrix.
- SSP draft.
- POA&M.
- Vulnerability disclosure.
- Dependency review.
- Release provenance.
- SBOM for Prophet.
- External security review.

## Measurement

Run:

```bash
python3 scripts/production-readiness-scorecard.py
```

The scorecard is intentionally not a marketing percentage. It is a delivery
control: every `done` item must have repo evidence, every `blocked` item must
name its blocker, and every critical open item remains visible.

## Current Verdict

Prophet is close to done for a local buyer pilot. It is not close to done as a
production defense-tech platform until M2 through M8 are built and verified.
The right next move is not to add more predictions; it is to make identity,
tenancy, persistence, policy, evidence, and operations production-shaped.
