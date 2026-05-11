# Production Architecture

Date: 2026-05-05

## Architecture Decision

Use a customer-managed or hosted single-tenant deployment as the first
production architecture. Do not start with multi-tenant SaaS.

Rationale:

- Defense buyers often need clear environment boundaries for early pilots.
- The current product already has a strong local policy/evidence boundary.
- Single-tenant deployment reduces cross-customer blast radius while RBAC,
  audit, retention, and operations mature.
- Multi-tenant SaaS can still be a later architecture once tenant isolation has
  negative tests and security review evidence.

## Production Principles

- Policy enforcement is server-side and mandatory.
- Every customer artifact has tenant scope.
- Runtime-generated artifacts are immutable after approval.
- Evidence is content-addressed and hash-verifiable.
- Integrations default to review-template or dry-run mode.
- Push actions require approval, role permission, policy allowlist, and audit.
- The sandbox has no default egress and never targets external infrastructure.
- Secrets are referenced by handle, never embedded in evidence.
- Every operator action leaves a durable audit event.

## Logical Components

```text
browser console
    |
    v
production API
    |-- auth and RBAC
    |-- policy engine
    |-- run orchestration
    |-- evidence API
    |-- integration API
    |
    +--> Postgres
    |
    +--> artifact store
    |
    +--> job queue / workers
              |-- asset and SBOM import worker
              |-- seeded OSINT worker
              |-- forecast worker
              |-- sandbox worker
              |-- evidence worker
              |-- integration worker
```

## Service Boundaries

### Console

The console is a client. It may show policy state, readiness, evidence,
handoff exports, and approval prompts, but it must not be the authority for
authorization. Server responses remain the source of truth.

### API Service

The API owns:

- Authentication context.
- Tenant context.
- RBAC decisions.
- Policy evaluation.
- Run lifecycle.
- Evidence lifecycle.
- Integration export lifecycle.
- Readiness and health summaries.

### Workers

Workers execute deterministic workflows:

- Asset/SBOM import.
- Seedset generation.
- Seeded OSINT snapshot generation.
- Forecast generation.
- Sandbox validation.
- Evidence generation.
- Integration handoff export.

Workers must receive tenant ID, policy hash, run ID, and approval context from
the API. They should not invent those values.

### Database

Use Postgres for production metadata:

- tenants
- users
- roles
- memberships
- service accounts
- policies
- policy versions
- runs
- run steps
- artifact records
- evidence bundles
- approval records
- audit events
- integration configurations
- retention tasks

Every customer-scoped table needs tenant ID or a justified global exemption.

### Artifact Store

Store evidence, manifests, source snapshots, sandbox run manifests, and handoff
bundles in an object store abstraction. The first local implementation can use
filesystem storage under ignored runtime paths, but the interface should support
S3-compatible storage later.

Each artifact record should include:

- tenant ID
- artifact type
- schema version
- policy ID
- policy hash
- content hash
- storage URI
- created by
- created at
- retention class
- redaction status

### Secrets

Production integrations must use a secrets manager abstraction. Evidence and
logs may include a secret reference ID, never a secret value. Local development
can use placeholder handles.

## Data Flow

### Customer Input

1. Operator uploads approved asset or SBOM metadata.
2. API validates tenant, role, policy, and file type.
3. Import worker parses and rejects unsafe fields.
4. Accepted sanitized output is stored as an artifact.
5. Rejection report stores row numbers and cleanup categories without unsafe raw
   values.

### Forecast And Evidence

1. Operator starts a run.
2. API binds run to tenant and policy version.
3. Workers generate seedset, OSINT snapshot, forecast, sandbox artifact, and
   evidence.
4. Evidence bundle records all input and output hashes.
5. Approval event marks bundle reviewed, approved, denied, exported, or revoked.

### Integration

1. Operator requests handoff export.
2. API checks role, policy export allowlist, and evidence approval state.
3. Integration worker emits review templates or dry-run payloads.
4. Push mode remains blocked until explicit production controls exist.
5. Audit event records export or denied export.

## Trust Boundaries

| Boundary | Rule |
|---|---|
| Browser to API | Browser input is untrusted; API revalidates policy, tenant, and role. |
| API to worker | Worker receives signed or server-generated run context. |
| Worker to artifact store | Worker writes content-addressed artifacts and returns hashes. |
| Artifact store to evidence | Evidence only references validated artifacts with matching hashes. |
| API to integration | Integration actions require policy allowlist and approval state. |
| Sandbox runtime | Sandbox has no default network egress and cannot accept live targets by default. |
| Customer data | Customer metadata is tenant-scoped and subject to retention/deletion controls. |

## Environment Profiles

| Environment | Purpose | Data |
|---|---|---|
| local | Developer and evaluator workflow | Fixtures and ignored runtime outputs |
| staging | Production-shaped test deployment | Synthetic or approved test data |
| pilot | Single customer pilot | Customer-approved metadata only |
| production | Controlled paid deployment | Contract-approved data only |

## Migration Path From Current Repo

1. Keep the existing local pilot scripts as fixture-mode acceptance tests.
2. Add a production API beside the current control server instead of mutating the
   demo server into production.
3. Move policy, evidence, audit, sandbox, and integration modules behind service
   interfaces.
4. Add Postgres metadata and artifact storage records.
5. Add tenant/RBAC checks before enabling customer data or real integrations.
6. Keep console fixture mode available for demos, but route production mode
   through authenticated API calls.

## Open Architecture Decisions

- Exact API framework.
- Database migration tool.
- Object storage provider for customer-managed deployments.
- Job queue technology.
- OIDC provider assumptions.
- Whether hosted single-tenant is required before customer-managed appliance.
- Whether signed policy implementation is required before customer-approved
  dry-run; the design is documented separately.
- Whether detached signature implementation is required in v1.0 or v1.1; the
  signed evidence manifest design is documented separately.
- Whether signed operator approvals are required before customer-approved
  dry-run or push modes; the design is documented separately.

## Acceptance Gates

- Tenant-scoped API tests.
- Policy enforcement tests for every mutating endpoint.
- Artifact immutability tests.
- Evidence reproducibility tests.
- Integration dry-run tests.
- Sandbox no-egress/resource-limit tests.
- Backup/restore drill.
- Incident response drill.
