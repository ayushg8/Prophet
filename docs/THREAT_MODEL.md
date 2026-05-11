# Prophet Threat Model

Date: 2026-05-05

This is the first production threat model. It covers the controlled production
target, not only the current fixture-backed pilot.

## Assets

- Customer asset/SBOM metadata.
- Sanitized OSINT snapshots.
- Forecasts and prediction portfolios.
- Sandbox artifacts and run manifests.
- Evidence bundles.
- Integration handoff artifacts.
- Approval records.
- Audit logs.
- Policies and policy versions.
- Integration credentials and secret references.
- Tenant, user, role, and identity metadata.

## Actors

- Customer viewer.
- Customer analyst.
- Customer approver.
- Customer admin.
- Prophet operator.
- Integration service account.
- External attacker.
- Malicious or careless insider.
- Compromised browser session.
- Compromised integration endpoint.

## Trust Boundaries

- Browser to API.
- API to worker.
- Worker to artifact store.
- API to database.
- API to identity provider.
- API to integration endpoint.
- Sandbox runtime to host environment.
- Customer metadata to sanitized derived artifacts.

## STRIDE Analysis

### Spoofing

Risks:

- A local operator label is treated as production identity.
- A forged identity claim creates an admin or approver session.
- A service account is reused across tenants.

Required controls:

- OIDC validation with issuer, audience, signature, expiry, and nonce checks.
- Server-side tenant membership lookup.
- Service-account scoping by tenant and integration.
- Local labels remain demo-only and are disallowed in production mode.
- Audit event records authenticated subject and role.

Acceptance tests:

- Missing or unsigned identity claims are rejected.
- User without tenant membership cannot access tenant data.
- Service account from tenant A cannot export tenant B artifacts.

### Tampering

Risks:

- Evidence JSON is edited after approval.
- Policy hash is replaced in runtime artifacts.
- Sandbox artifact is swapped after validation.
- Integration payload is changed after approval.

Required controls:

- Content-addressed artifacts.
- Immutable approved evidence state.
- Policy hash verification before export.
- Approval event hash chain.
- Integration manifest hashes every emitted file.
- Signed policy design, with implementation gated on buyer/security-review need
  or `build_next_slice`.
- Signed evidence manifest design, with optional detached signature support only
  after a buyer/security-review gate.
- Signed operator approval design, with implementation gated on authenticated
  identity, RBAC, and buyer/security-review need.

Acceptance tests:

- Modified evidence fails hash verification.
- Drifted policy hash blocks export.
- Swapped sandbox artifact fails evidence validation.

### Repudiation

Risks:

- Operator denies approving an evidence export.
- Customer cannot reconstruct who changed policy.
- Incident response lacks enough audit context.

Required controls:

- Durable audit events for every approval, denial, export, policy change, and
  retention action.
- Audit chain verification.
- Actor ID, role, tenant ID, run ID, policy hash, artifact hashes, and decision
  recorded in each event.
- Retention rules preserve audit logs longer than runtime artifacts.

Acceptance tests:

- Audit chain breaks are detected.
- Denied approval cannot generate evidence or handoff artifacts.
- Policy change produces a distinct audit event.

### Information Disclosure

Risks:

- Evidence includes raw customer hostnames, credentials, or raw source text.
- Tenant A reads tenant B data.
- Logs include sensitive customer values.
- Integration credentials leak into evidence.

Required controls:

- Tenant isolation in every query and artifact lookup.
- Safe import validators reject unsafe identifiers.
- Redaction reports accompany generated evidence.
- Logs use IDs, hashes, and categories instead of raw customer values.
- Secrets manager handles credentials by reference only.
- Release safety scan rejects generated runtime artifacts and unsafe text.

Acceptance tests:

- Tenant isolation negative tests.
- Unsafe import rows do not appear in accepted output or rejection report.
- Evidence generation rejects raw text, credentials, private hostnames, and live
  target values.
- Logs and audit exports do not contain secret values.

### Denial Of Service

Risks:

- Large imports exhaust parser resources.
- Sandbox run consumes host resources.
- Repeated evidence jobs fill artifact storage.
- Integration retries overload customer systems.

Required controls:

- Upload size and row-count limits.
- Worker timeouts.
- Sandbox CPU, memory, disk, and timeout limits.
- Per-tenant rate limits.
- Retention cleanup and artifact quotas.
- Integration retry budgets.

Acceptance tests:

- Oversized imports are rejected with safe errors.
- Sandbox timeout emits failure evidence without raw logs.
- Job queue enforces retry and cancellation policy.

### Elevation Of Privilege

Risks:

- Viewer triggers evidence export.
- Analyst pushes integration payloads without approval.
- Policy edit enables live collection or non-fixture sandbox mode.
- Compromised worker writes artifacts for another tenant.

Required controls:

- Server-side RBAC for every mutating endpoint.
- Policy schema rejects unsafe controls by default.
- Approval quorum for higher-risk modes.
- Workers receive scoped run context and cannot choose tenant IDs.
- Break-glass actions require special audit and post-incident review.

Acceptance tests:

- Viewer, analyst, approver, admin, and auditor permissions are tested.
- Policy-blocked actions fail closed.
- Worker cannot create artifact outside assigned tenant/run.

## Abuse Cases

- Buyer asks Prophet to validate against a real third-party target.
  Response: block by policy; create denial audit event; direct buyer to approved
  sandbox process.

- Analyst uploads raw scanner export with hostnames and IPs.
  Response: reject unsafe rows; emit cleanup report without echoing raw values.

- SOC wants one-click production detection deployment.
  Response: use review templates or dry-run until approval-required push mode,
  rollback, and customer integration controls exist.

- Source collector is redirected to an unapproved host.
  Response: reject redirect and final URL outside allowlist.

- Integration credential appears in a config file.
  Response: release safety and secret scanning must fail; rotate credential;
  record incident if exposed.

## Production Security Requirements

- Identity provider integration before production operators exist.
- Tenant isolation tests before customer data enters durable storage.
- Secrets manager before real integrations exist.
- Artifact immutability before signed approvals are trusted.
- No-egress sandbox before non-fixture validation is considered.
- Security review before multi-tenant hosted deployment.

## Residual Risks

- Forecast quality still needs evaluation against real customer review outcomes.
- Compliance readiness depends on deployment environment and customer data
  classification.
- Live official-source collection requires legal/source-terms review.
- Push integrations create operational risk even when technically safe.

## Review Cadence

Update this threat model when:

- A new data source is added.
- A new integration mode is added.
- A sandbox mode changes.
- Identity or tenant model changes.
- Production deployment target changes.
- A security review or incident finds a new class of risk.
