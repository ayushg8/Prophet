# RBAC And Tenant Isolation Model

Date: 2026-05-05

This is the first production authorization model. It does not turn the local
pilot console into a production service by itself. It defines the reusable
server-side decision point that the production API must call before any
customer-scoped action.

Implementation:

- `prophet_platform/authorization.py`
- `prophet_platform/tests/test_authorization.py`

## Core Rule

Every production action must answer three questions server-side:

1. Who is the authenticated principal?
2. Which tenant owns the resource?
3. Does at least one tenant-scoped role allow this action?

If any answer is missing, Prophet denies the action.

## Roles

| Role | Intended Permissions |
|---|---|
| `viewer` | Read readiness, policy, and run state. |
| `analyst` | Viewer permissions plus create runs, forecast, fixture sandbox, and evidence generation. |
| `approver` | Analyst permissions plus approve/deny evidence and export handoff bundles. |
| `auditor` | Read readiness, policy, run state, and audit records. |
| `admin` | Tenant admin for all production actions inside the tenant. |

Admins are still tenant-scoped. Admin role does not allow cross-tenant access.

## Tenant Resource

The first primitive is:

```text
tenant_id
resource_type
resource_id
```

The production API should wrap every policy, run, evidence bundle, approval
record, audit event, integration config, and artifact record in this model.

## Production Identity

Local operator labels are acceptable for the local buyer pilot. They are not
accepted in production mode. Production identity must come from an approved
identity provider such as OIDC, with SAML planned for customers that require it.

The authorization core rejects local identity providers when
`production_mode=True`.

## Deny-By-Default Behavior

The authorization core denies:

- Unknown actions.
- Unknown roles.
- Empty role sets.
- Unsafe identifiers.
- Cross-tenant access.
- Local identity providers in production mode.
- Actions not allowed by the principal's role.

## API Integration Requirements

When the production API is added:

- Do not trust tenant ID from browser state.
- Resolve tenant membership from authenticated identity.
- Load the resource's tenant ID from durable storage.
- Call `authorize(...)` before mutating policy, runs, evidence, sandbox,
  integrations, users, or audit state.
- Record the authorization decision in the audit event for sensitive actions.
- Keep local demo labels isolated from production identity.

## Tests Already Present

The current test harness proves:

- Approvers can approve same-tenant evidence.
- Viewers cannot export handoff bundles.
- Tenant mismatch is denied even for admins.
- Local identity providers are rejected in production mode.
- Local identity providers can still be used in development mode.
- Unknown roles are denied.
- Unsafe identifiers are rejected.

## Remaining Work

- Persist tenants, users, roles, memberships, and service accounts.
- Add OIDC claim validation.
- Add SAML design for customers that require it.
- Add API middleware that resolves principal and tenant context.
- Add database-backed tenant isolation tests.
- Add approval quorum and break-glass controls for higher-risk modes.
