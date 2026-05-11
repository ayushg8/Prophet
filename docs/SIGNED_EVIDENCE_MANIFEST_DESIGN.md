# Signed Evidence Manifest Design

Date: 2026-05-10

This design explains how Prophet should turn the current hash-based evidence
bundle into a signed review artifact for a future paid or sponsored pilot. It
does not implement signing, create keys, or change the current buyer demo. The
current pilot remains fixture-backed, localhost-only, and review-template-only.

## Goal

Give a buyer or security reviewer a single manifest they can verify without
trusting the console UI:

1. Which files were produced?
2. Which policy governed the run?
3. Which operator approval was recorded?
4. Which forecast, sandbox artifact, evidence bundle, and handoff templates were
   included?
5. Did any file change after approval?
6. Which signing identity, if enabled later, attested to the bundle?

The design strengthens the **hand off** job. It does not add live validation,
production push, exploit tooling, or autonomous remediation.

## Current Inputs

The signed manifest should wrap artifacts Prophet already emits:

- Evidence bundle JSON and Markdown.
- Pilot policy JSON and policy SHA-256.
- Operator approval record and approval record SHA-256.
- Operator audit export and audit chain hash.
- Optional future signed operator approval record, when required by
  `docs/SIGNED_OPERATOR_APPROVAL_DESIGN.md`.
- Forecast output hash.
- Exposure-class portfolio hash.
- Sandbox artifact and sandbox run manifest hashes.
- Integration handoff manifest plus SIEM/ticket review template hashes.
- Data classification inventory version.
- Release smoke hash manifest when available.

## Manifest Scope

The manifest signs metadata and hashes, not raw customer data.

Allowed in the manifest:

- Relative repo/runtime paths.
- SHA-256 hashes.
- Schema versions.
- Policy ID and policy hash.
- Bundle ID and evidence bundle hash.
- Approval event ID and approval hash.
- Export ID and integration manifest hash.
- Safety attestations.
- Data classification labels.
- Optional public verification key ID or certificate reference.

Prohibited in the manifest:

- Credentials, secrets, tokens, or key material.
- Live IPs, hostnames, URLs used as targets, or arbitrary target input.
- Raw source text, raw customer telemetry, or raw logs.
- Payloads, procedures, commands, or exploit steps.
- Real buyer/contact names, emails, phone numbers, or private organization
  details.

## Proposed Schema

Initial schema name:

```text
prophet_signed_evidence_manifest.v0.1
```

Proposed JSON shape:

```json
{
  "schema_version": "prophet_signed_evidence_manifest.v0.1",
  "manifest_id": "psem-<sha256-prefix>",
  "generated_at": "2026-05-10T00:00:00Z",
  "bundle_id": "peb-...",
  "policy": {
    "policy_id": "prophet-pilot-fixture-localhost-v0.1",
    "policy_sha256": "<sha256>"
  },
  "data_classification": {
    "inventory": "docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md",
    "default_level": "runtime local",
    "prohibited_content_attestation": true
  },
  "artifacts": [
    {
      "kind": "evidence_json",
      "path": "evidence/outputs/runtime/latest-edge-appliance.json",
      "sha256": "<sha256>",
      "classification": "runtime local",
      "exportable": true
    }
  ],
  "audit": {
    "approval_record_sha256": "<sha256>",
    "operator_audit_export_sha256": "<sha256>",
    "previous_event_hash": "<sha256-or-null>"
  },
  "safety_attestation": {
    "no_live_targets": true,
    "no_live_target_data_included": true,
    "no_payloads": true,
    "no_credentials": true,
    "no_private_hostnames": true,
    "review_templates_only": true
  },
  "signature": {
    "status": "unsigned_design_only",
    "algorithm": null,
    "key_id": null,
    "signature_path": null,
    "signed_payload_sha256": null
  }
}
```

## Canonicalization

Before signing, Prophet should produce a canonical manifest body:

- UTF-8 JSON.
- Sorted object keys.
- No insignificant whitespace.
- Stable timestamp format.
- Relative paths only.
- No symlinks or path traversal.
- No generated signature fields included in the signed payload.

The `signed_payload_sha256` is the SHA-256 of this canonical unsigned manifest
body. The detached signature, when implemented, signs that digest or canonical
body according to the selected signing backend.

## Detached Signature Plan

Detached signature support should be optional and disabled in the public pilot
until a buyer or security reviewer asks for it.

Future supported modes:

| Mode | Use | Requirement |
|---|---|---|
| `unsigned_design_only` | Current repo design and fixture pilot. | No key material. |
| `local_dev_key` | Developer-only non-production verification. | Key generated outside repo; public key path only. |
| `customer_managed_key` | Customer-managed pilot appliance. | Customer owns signing key and rotation. |
| `kms_or_hsm` | Controlled production. | KMS/HSM policy, identity, audit, and rotation. |

Private keys must never be committed, printed, stored in runtime outputs, or
sent to agent prompts.

## Verification Flow

A verifier should:

1. Load the signed evidence manifest.
2. Validate the manifest schema.
3. Reject absolute paths, path traversal, symlinks, and missing files.
4. Recompute every artifact SHA-256.
5. Confirm evidence bundle `bundle_sha256` matches the evidence JSON body.
6. Confirm policy hash matches the referenced policy file.
7. Confirm approval hash and audit export hash match their files.
8. Confirm integration handoff manifest hashes every emitted template.
9. Confirm safety attestations are true and compatible with the active policy.
10. If signature status is not `unsigned_design_only`, verify the detached
    signature with the configured public key or key service.

Verification failure must block sharing the review bundle.

## Review Bundle Layout

Future signed review bundles should be directories under ignored runtime output
paths, for example:

```text
integrations/outputs/runtime/latest-edge-appliance-review-bundle/
├── manifest.json
├── manifest.json.sig          # optional future detached signature
├── evidence/
│   ├── latest-edge-appliance.json
│   └── latest-edge-appliance.md
├── audit/
│   ├── approval-record.json
│   └── operator-audit-export.json
├── handoff/
│   └── latest-edge-appliance/
│       └── manifest.json
└── review-checklist.md
```

The bundle may include copies of review artifacts or references to them, but
the manifest must make the choice explicit with `bundle_layout: copied` or
`bundle_layout: referenced`.

## Implementation Gate

Do not implement detached signatures or signed review bundle packaging until
one of these happens:

- A qualified buyer asks for signed evidence as a pilot requirement.
- A security reviewer identifies unsigned evidence as a blocker.
- The validation dashboard reaches `build_next_slice`.

Until then, the current hash manifest, policy hash checks, audit chain, and
release smoke hashes are enough for the local buyer pilot.

## Acceptance Criteria For Future Implementation

- Unit tests reject tampered artifacts, missing files, path traversal, absolute
  paths, and unsafe classifications.
- Unit tests prove `signed_payload_sha256` is stable across repeated runs with
  identical inputs.
- Signature verification fails closed when the signature, key ID, or signed
  payload hash does not match.
- Review bundles contain no prohibited fields from
  `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`.
- The pilot smoke still runs without signature support.
- Public docs say signed manifests are optional future hardening unless a buyer
  explicitly requires them.
