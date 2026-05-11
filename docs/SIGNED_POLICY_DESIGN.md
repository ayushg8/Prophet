# Signed Policy Design

Date: 2026-05-10

This design describes how Prophet should make policy files tamper-evident for a
future paid or sponsored pilot. It does not implement signing, create keys,
change policy enforcement, or change the current buyer demo. The current pilot
continues to rely on schema validation, semantic policy linting, policy hashes,
runtime artifact policy-hash checks, and release-safety scans.

## Goal

Signed policies should answer these review questions:

1. Which exact policy governed a run, approval, evidence bundle, and handoff?
2. Was the policy reviewed before use?
3. Did the policy change after review?
4. Which authority approved the policy version?
5. Did generated artifacts carry the same policy hash?
6. If signatures are enabled later, did the signature verify against an
   approved public key or customer-managed key service?

This strengthens the **validate safely** and **hand off** jobs. It does not add
live collection, target-control workflows, exploit tooling, production pushes,
or autonomous remediation.

## Current Pilot Boundary

The current local pilot already has policy integrity checks:

- `policy.lint` validates the policy JSON Schema and semantic safety rules.
- `policy.lint --verify-runtime-artifacts` confirms runtime artifacts carry the
  reviewed policy hash.
- Evidence, audit, sandbox, OSINT, and integration artifacts include policy ID
  and policy SHA-256.
- The release safety checker rejects missing policy-hash coverage for release
  artifact paths.
- Default policy controls keep live targets, payload generation, credentials,
  private hostnames, raw scraper text, and arbitrary target input disabled.

Those checks are sufficient for the fixture-backed local buyer pilot.

## Scope

Signed policy support should wrap policy metadata and hashes, not customer data.

Allowed in a signed policy record:

- Policy ID and policy SHA-256.
- Policy schema version.
- Relative policy path.
- Review status and review timestamp.
- Reviewer role or opaque reviewer ID.
- Allowed modes, source IDs, sandbox profiles, and export kinds as hashes or
  exact policy fields.
- Signature metadata when enabled later.

Prohibited in a signed policy record:

- Credentials, secrets, tokens, private keys, or signing material.
- Customer names, emails, phone numbers, hostnames, IPs, or target URLs.
- Raw source text, raw customer telemetry, raw logs, or screenshots.
- Payloads, exploit steps, procedures, or target-control instructions.
- Identity provider tokens, browser session data, cookies, or API keys.

## Proposed Schema

Initial schema name:

```text
prophet_signed_policy.v0.1
```

Proposed JSON shape:

```json
{
  "schema_version": "prophet_signed_policy.v0.1",
  "signed_policy_id": "psp-<sha256-prefix>",
  "generated_at": "2026-05-10T00:00:00Z",
  "policy": {
    "policy_id": "prophet-pilot-fixture-localhost-v0.1",
    "policy_path": "policy/prophet-pilot-policy.json",
    "policy_schema": "policy/prophet-pilot-policy.schema.json",
    "policy_sha256": "<sha256>"
  },
  "review": {
    "status": "reviewed",
    "reviewer_role": "security_reviewer",
    "reviewed_at": "2026-05-10T00:00:00Z",
    "review_scope": "fixture-backed local buyer pilot"
  },
  "safety_attestation": {
    "live_targets_allowed": false,
    "payload_generation_allowed": false,
    "credentials_allowed": false,
    "private_hostnames_allowed": false,
    "raw_scraper_text_allowed": false,
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

## Canonicalization

Before signing, Prophet should produce a canonical unsigned policy record:

- UTF-8 JSON.
- Sorted object keys.
- No insignificant whitespace.
- Stable timestamp format.
- Relative paths only.
- No symlinks, path traversal, or absolute paths.
- No generated signature fields included in the signed payload.
- `policy_sha256` computed from the exact reviewed policy file.

`signed_payload_sha256` is the SHA-256 of the canonical unsigned policy record.
The detached signature, when implemented, signs that digest or canonical body
according to the selected signing backend.

## Signature Modes

Signature support should remain disabled until a buyer or security reviewer
requires it.

| Mode | Use | Requirement |
|---|---|---|
| `unsigned_design_only` | Current design and fixture pilot. | No key material. |
| `local_dev_key` | Developer-only non-production verification. | Key generated outside repo; public key path only. |
| `customer_managed_key` | Customer-managed pilot appliance. | Customer owns signing key and rotation. |
| `kms_or_hsm` | Controlled production. | KMS/HSM policy, identity, audit, and rotation. |

Private keys must never be committed, printed, stored in runtime outputs, or
sent to agent prompts.

## Verification Flow

A verifier should:

1. Load the signed policy record.
2. Validate the signed policy schema.
3. Reject absolute paths, path traversal, symlinks, and missing files.
4. Run `policy.lint` against the referenced policy and schema.
5. Recompute `policy_sha256`.
6. Confirm the policy safety attestations match the policy controls.
7. Confirm all runtime artifacts in the review bundle carry the same policy
   hash.
8. Confirm the policy hash matches any evidence manifest, signed evidence
   manifest, operator approval record, audit export, sandbox manifest, OSINT
   provenance manifest, and integration handoff manifest.
9. If signature status is not `unsigned_design_only`, verify the detached
   signature with the configured public key or key service.

Verification failure must block sharing the review bundle or exporting handoff
templates.

## Versioning And Rotation

Future signed policy records should support:

- `policy_version`.
- `supersedes_signed_policy_id`.
- `effective_at`.
- `expires_at`.
- `revoked_at`.
- `revocation_reason`.

Policy rotation must not mutate prior evidence. Older evidence bundles should
continue to reference the policy hash that governed their original run.

## Implementation Gate

Do not implement policy signing, key handling, signature verification, policy
rotation, or policy migration machinery until one of these happens:

- A qualified buyer requires signed policies for a paid pilot.
- A security reviewer identifies unsigned policies as a blocker.
- The validation dashboard reaches `build_next_slice`.

Until then, the current schema validation, semantic linting, policy hash
propagation, runtime drift checks, and release-safety scans are enough for the
local buyer pilot.

## Acceptance Criteria For Future Implementation

- Unit tests reject tampered policies, missing files, path traversal, absolute
  paths, unsafe controls, and policy hash drift.
- Unit tests prove `signed_payload_sha256` is stable across repeated runs with
  identical inputs.
- Signature verification fails closed when key ID, algorithm, signature, or
  payload hash does not match.
- Runtime artifact verification fails if any evidence, audit, sandbox, OSINT,
  or integration artifact carries a different policy hash.
- Safety scans reject prohibited fields inside signed policy records.
- Public docs say signed policies are optional future hardening unless a buyer
  explicitly requires them.
