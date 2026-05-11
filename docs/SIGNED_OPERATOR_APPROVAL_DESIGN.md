# Signed Operator Approval Design

Date: 2026-05-10

This design describes a future production approval record for Prophet. It does
not implement signing, create keys, add RBAC, add SSO, or change the current
buyer pilot. The current pilot still uses sanitized local operator labels and a
hash-chained local audit log.

## Goal

Signed operator approvals should answer these review questions for a production
or customer-managed pilot:

1. Which authenticated principal approved or denied the action?
2. Which tenant, policy, run, evidence bundle, and handoff export were in scope?
3. What exact action was approved?
4. Was the approval recorded before the evidence or handoff artifact was
   shared?
5. Did the approval payload change after it was signed?
6. Did the signer have the required role and approval authority at signing time?

This strengthens the **validate safely** and **hand off** jobs. It does not add
live collection, target-control workflows, exploit tooling, production pushes,
or autonomous remediation.

## Current Pilot Boundary

Current pilot approvals are intentionally narrower:

- `evidence.audit` writes hash-chained local audit events.
- Operator identity is a sanitized local label such as `fixture` or
  `local-console`.
- Evidence bundles carry the approval record hash.
- Integration handoff manifests carry the approval hash forward.
- Audit exports summarize safe fields and omit raw event bodies.

This is sufficient for the local fixture-backed buyer pilot. It is not
production identity, non-repudiation, SSO, RBAC, customer authorization, or
quorum approval.

## Preconditions Before Implementation

Do not implement signed operator approvals until these exist:

- Authenticated production principal from an approved identity provider.
- Tenant-scoped RBAC decision for the requested action.
- Durable artifact records for policy, run, evidence, approval, and export.
- Immutable approved evidence state.
- Customer-specific retention policy.
- Key management decision: customer-managed key, KMS/HSM, or other approved
  signing backend.
- Buyer or security-review requirement that unsigned local approvals are a
  blocker.
- Validation dashboard reaches `build_next_slice`, unless a qualified buyer
  requires this only for a scoped paid pilot.

## Proposed Schema

Initial schema name:

```text
prophet_signed_operator_approval.v0.1
```

Proposed JSON shape:

```json
{
  "schema_version": "prophet_signed_operator_approval.v0.1",
  "approval_id": "psoa-<sha256-prefix>",
  "generated_at": "2026-05-10T00:00:00Z",
  "tenant": {
    "tenant_id": "<tenant-id>",
    "environment": "pilot"
  },
  "principal": {
    "subject_id": "<idp-subject-id>",
    "identity_provider": "oidc",
    "role": "approver"
  },
  "authorization": {
    "decision": "allowed",
    "role_checked": true,
    "required_role": "approver",
    "policy_id": "prophet-pilot-fixture-localhost-v0.1",
    "policy_sha256": "<sha256>"
  },
  "approval": {
    "action": "share_evidence_bundle",
    "decision": "approved",
    "reason_code": "customer_review",
    "scope": "one approved asset/SBOM family and one evidence bundle",
    "expires_at": "2026-05-17T00:00:00Z"
  },
  "refs": {
    "run_id": "<run-id>",
    "evidence_bundle_id": "peb-...",
    "evidence_bundle_sha256": "<sha256>",
    "handoff_export_id": "<export-id>",
    "handoff_manifest_sha256": "<sha256>"
  },
  "safety_attestation": {
    "no_live_targets": true,
    "no_live_target_data_included": true,
    "no_payloads": true,
    "no_credentials": true,
    "review_templates_only": true
  },
  "signature": {
    "status": "unsigned_design_only",
    "algorithm": null,
    "key_id": null,
    "signed_payload_sha256": null,
    "signature_path": null
  }
}
```

## Canonical Payload

The signed payload should be canonical JSON:

- UTF-8.
- Sorted object keys.
- No insignificant whitespace.
- Stable timestamp format.
- Relative artifact references only.
- No symlinks, path traversal, absolute paths, or runtime temp paths outside
  approved artifact storage.
- No generated signature fields included in the signed payload.

`signed_payload_sha256` is the SHA-256 of this canonical unsigned payload. The
signature signs that digest or canonical body according to the selected signing
backend.

## Prohibited Fields

Signed approval records must not include:

- Credentials, secrets, tokens, or key material.
- Raw customer telemetry, raw source text, raw logs, or raw collection output.
- Live IPs, private hostnames, target URLs, or arbitrary target input.
- Payloads, procedures, commands, or exploit steps.
- Personal names, emails, phone numbers, or private organization details.
- Browser session data, cookies, or identity provider tokens.

Use opaque principal IDs and tenant IDs only after the customer identity design
has been approved.

## Verification Flow

A verifier should:

1. Validate the signed approval schema.
2. Confirm the approval references an immutable evidence bundle or export.
3. Recompute referenced artifact hashes.
4. Confirm the policy hash matches the policy in effect at approval time.
5. Confirm the authorization block records an allowed approver decision.
6. Confirm the approval has not expired.
7. Confirm safety attestations are true and compatible with the active policy.
8. Verify the signature when `signature.status` is not
   `unsigned_design_only`.
9. Confirm the approval event appears in the durable audit chain.

Any failure blocks sharing evidence, exporting handoffs, or advancing a
customer-approved dry-run.

## Quorum And Break-Glass

Higher-risk modes need more than one approval:

- Customer-approved dry-run: one customer approver and one Prophet operator.
- Production push: configured quorum, rollback metadata, and customer owner
  approval.
- Break-glass action: incident reason, expiry, after-action review, and special
  audit event.

These modes remain out of scope for the current local pilot.

## Migration From Local Labels

Local labels should remain available for fixture and evaluator workflows. In
production mode:

- Local identity providers are rejected.
- Browser-provided role or tenant claims are ignored.
- Tenant membership is resolved server-side.
- Approval authority is checked immediately before the approval is recorded.
- The local operator label can appear only as a migration note, never as the
  signing identity.

## Implementation Gate

Do not implement signing or key handling until one of these is true:

- A qualified buyer requires signed operator approvals for a paid pilot.
- A security reviewer identifies unsigned approvals as a blocker.
- The validation dashboard reaches `build_next_slice`.

Until then, the current hash-chained audit log, approval record hash, evidence
hashes, and deterministic handoff review ZIP are enough for the local buyer
pilot.

## Acceptance Criteria For Future Implementation

- Unit tests reject unsigned, expired, role-mismatched, tenant-mismatched, and
  tampered approval records.
- Unit tests prove canonical payload hashing is stable.
- Signature verification fails closed when key ID, signature, algorithm, or
  payload hash does not match.
- Production mode rejects local identity providers.
- Evidence and handoff export refuse to proceed when required signed approval
  verification fails.
- Safety scans reject prohibited fields inside signed approval records.
- Private keys are never committed, printed, stored in runtime outputs, or sent
  to agent prompts.
