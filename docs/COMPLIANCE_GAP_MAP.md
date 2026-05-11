# Compliance And Security Review Gap Map

Date: 2026-05-05

This map is a planning artifact, not a certification claim. It is meant to help
Prophet prepare for defense-tech buyer security review, CMMC/NIST-style review,
FedRAMP-style SaaS review if hosted for federal agencies, and SOC 2 style
commercial security review.

## Current Position

The repo is strong for a controlled local buyer pilot:

- Deterministic fixture-backed smoke path.
- Policy-bound evidence bundle.
- Runtime artifact hashes.
- Release safety scans.
- Local audit chain.
- Review-template integration exports.
- Console smoke coverage.
- CI for Python, console, dependency audit, and release safety.

The repo is not yet production-compliance-ready because it lacks:

- Production identity provider integration.
- RBAC.
- Tenant isolation.
- Durable database and artifact store.
- Production secrets handling.
- Backup and restore.
- Incident response playbook.
- Security control matrix.
- Production-enforced data classification controls.
- External security review.

## Evidence Already Present

| Area | Existing Evidence |
|---|---|
| Secure default mode | `SECURITY.md`, `docs/SAFETY_ARCHITECTURE.md`, release safety tests |
| Policy gate | `policy/prophet-pilot-policy.json`, `policy/lint.py`, policy tests |
| Evidence integrity | Evidence bundle hashes, approval hash, audit log tests |
| Runtime output boundary | `.gitignore`, release safety scan, smoke hashes |
| Integration safety | Review-template exporter and tests |
| Sandbox safety | Fixture-mode `sandbox_runner`, validator tests |
| Data classification | `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md` |
| CI discipline | `.github/workflows/ci.yml`, dependency audit workflow |
| Buyer documentation | Evaluator, pilot, FAQ, walkthrough, and troubleshooting docs |

## Major Gaps By Security Domain

| Domain | Current State | Production Gap | Target Evidence |
|---|---|---|---|
| Access control | Local labels and control server only | OIDC/SAML, RBAC, service accounts, tenant membership | Auth design, role matrix, negative tests |
| Tenant isolation | Not production-mode yet | Tenant IDs in every persisted object and query | Data model, API tests, isolation test harness |
| Audit and accountability | Local hash chain exists | Durable production audit store and policy change audit | Audit schema, export, retention, chain verification |
| Configuration management | Scripts and CI exist | Environment promotion, config validation, release train | Deployment runbooks, config schema, changelog |
| Identification and authentication | Demo operator labels | IdP-backed user identity and service identity | OIDC/SAML docs and tests |
| Incident response | Security policy exists | Formal IR playbook and notification templates | IR plan, tabletop notes, contact matrix |
| Risk assessment | Defense readiness docs exist | Formal risk register and recurring review | Risk register, POA&M, review cadence |
| System and communications protection | Localhost/default fixture safety | TLS, secure headers, encrypted storage, network policy | Deployment architecture and security tests |
| System and information integrity | Validators and CI exist | Vulnerability management and patch cadence | Dependency review, SAST, container scan, remediation SLA |
| Data retention | Runtime retention exists and data classification inventory is documented | Customer data retention/deletion workflow | Data inventory, retention jobs, deletion audit |
| Backup and recovery | Not implemented | Backup, restore, and DR targets | Backup policy, restore drill evidence |
| Supply chain | npm audit and dependency boundary | SBOM for Prophet, provenance, license review | SBOM, provenance notes, dependency risk register |

## CMMC/NIST 800-171 Oriented Work

Do before claiming readiness for environments that may handle CUI:

- Define whether Prophet will process, store, or transmit CUI.
- Draft a System Security Plan.
- Map system components, data flows, and boundaries.
- Add access control family evidence: users, roles, least privilege, session
  handling, service accounts.
- Add audit and accountability evidence: audit event schema, retention, review.
- Add configuration management evidence: release train, change approvals,
  deployment baselines.
- Add incident response plan and tabletop exercise.
- Add risk assessment and POA&M process.
- Add media/storage handling rules for evidence artifacts.
- Add system integrity process: scanning, dependency review, patch cadence.

Do not represent the current local pilot as CMMC-ready. It is a controlled demo
with useful evidence patterns.

## FedRAMP-Style SaaS Work

Only relevant if Prophet becomes a hosted federal cloud service. Before that:

- Decide hosted single-tenant versus multi-tenant.
- Select a compliant hosting environment and services.
- Define system boundary and inherited controls.
- Implement continuous monitoring, vulnerability scanning, logging, and
  incident response.
- Complete SSP, control implementation statements, and POA&M.
- Add secure deployment, backup, restore, and disaster recovery evidence.

The current repo is not a FedRAMP package.

## SOC 2 Style Work

Useful for commercial buyers even without federal requirements:

- Security policy.
- Access reviews.
- Change management.
- Vendor/dependency risk process.
- Vulnerability management.
- Incident response.
- Backup and recovery.
- Logging and monitoring.
- Customer data deletion.
- Evidence of control operation over time.

## Security Packet Contents

The v1.0 customer packet should include:

- Product overview and non-goals.
- Architecture diagram.
- Data flow diagram.
- Data classification inventory.
- Access control and RBAC matrix.
- Identity provider integration notes.
- Tenant isolation model.
- Policy engine description.
- Evidence integrity model.
- Audit log model.
- Retention/deletion procedure.
- Secrets handling design.
- Sandbox isolation design.
- Integration safety model.
- Deployment model.
- Backup/restore plan.
- Incident response playbook.
- Vulnerability disclosure process.
- Dependency and supply-chain review.
- POA&M with owners and dates.

## Immediate Compliance Actions

1. Keep the production readiness scorecard in CI.
2. Turn the data classification inventory into enforceable production controls.
3. Add RBAC/tenant model design before production code.
4. Add durable audit and evidence storage design.
5. Add incident response playbook.
6. Add secrets manager design.
7. Add backup/restore design.
8. Add control matrix once the production architecture is implemented enough to
   be meaningful.

## Buyer-Facing Language

Accurate:

- "Prophet has a repeatable, policy-bound local pilot with deterministic
  evidence and safety gates."
- "Production controls are planned and tracked; identity, tenancy, durable
  storage, operations, and compliance are not complete yet."

Do not say:

- "CMMC ready."
- "FedRAMP ready."
- "Production SaaS ready."
- "Autonomous cyber defense."
- "Validated against live targets."
