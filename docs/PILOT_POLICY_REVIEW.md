# Pilot Policy Review

Prophet pilot policies are small JSON files that define which safe modes,
source IDs, sandbox profiles, and runtime output locations are allowed for an
evaluation. It also controls which SIEM, ticketing, and audit handoff templates
can be exported. The packaged default is `policy/prophet-pilot-policy.json`.

## Review Command

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
```

The linter validates the policy against
`policy/prophet-pilot-policy.schema.json` by default, then runs the semantic
safety checks used by the pilot. It prints the policy ID, canonical SHA-256,
allowed modes, allowed source IDs, allowed sandbox profiles, allowed integration
exports, blocked controls, attestations, retention hints, and runtime output
paths.

To validate against an explicit schema path:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json \
  --schema policy/prophet-pilot-policy.schema.json
```

To compare a customer or narrower example policy against the default pilot
policy:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/examples/fixture-only-policy.json \
  --compare-to policy/prophet-pilot-policy.json
```

The `comparison` block reports semantic differences from the baseline:
changed policy ID, added/removed allowed modes, source IDs, sandbox profiles,
integration exports, attestation changes, retention changes, and runtime output
path changes. A comparison is still fail-closed: both policies must pass the
linter before any differences are printed.

The pilot smoke script runs the runtime drift check automatically after golden
hash verification. To prove generated runtime artifacts still match the
reviewed policy file outside the smoke path, run:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json \
  --verify-runtime-artifacts \
    world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.manifest.json \
    cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json \
    cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json \
    evidence/outputs/runtime/latest-edge-appliance.json \
    evidence/outputs/runtime/pilot-demo-operator-audit-export.json \
    evidence/outputs/runtime/pilot-demo-operator-audit-retention.json \
    integrations/outputs/runtime/latest-edge-appliance/manifest.json
```

The `runtime_policy_verification` block reports each known artifact schema and
fails if any evidence, OSINT, sandbox, audit, or integration artifact carries a
missing or different policy SHA-256.

To review runtime-output and customer-metadata retention without exposing raw
artifact bodies:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.retention \
  --policy policy/prophet-pilot-policy.json \
  --generated-at 2026-05-05T00:00:00Z \
  --out-json evidence/outputs/runtime/pilot-demo-runtime-retention.json
```

The report hashes each file, uses `retention.runtime_outputs_max_days` for
runtime artifacts, uses `retention.customer_metadata_max_days` for asset import
metadata under `assets/outputs/runtime/`, and delegates hash-chained audit-log
cleanup to `evidence.audit retention`. To remove expired managed runtime files,
add both `--delete-expired` and `--confirm-retention-delete`.

## Buyer Review Checklist

- `controls.live_targets_allowed` is `false`.
- `controls.live_vm_scraper_allowed` is `false`.
- `controls.arbitrary_target_input_allowed` is `false`.
- `controls.payload_generation_allowed` is `false`.
- `controls.raw_scraper_text_allowed` is `false`.
- `controls.private_hostnames_allowed` is `false`.
- `controls.credentials_allowed` is `false`.
- `allowed_source_ids` contains only approved catalog source IDs.
- `policy/source-catalog-allowlist.json` covers every currently enabled source
  catalog entry for release review; it does not enable live collection.
- `allowed_sandbox_profiles` contains only approved deterministic or customer
  sandbox profile IDs.
- `allowed_integration_exports` contains only approved review-template export
  IDs.
- `default_outputs` remain under ignored `*/outputs/runtime/` directories.
- Evidence and integration manifests show the same policy ID and policy hash.
- Runtime policy verification passes for the generated evidence, OSINT,
  sandbox, audit, and integration artifacts.
- `schema_path` in the linter output points at the reviewed policy schema.
- `retention.raw_collection_retained` is `false`.
- `retention.deletion_review_required` is `true`.
- Runtime, audit, and customer metadata retention days fit the approved pilot
  boundary.
- Any customer-specific policy comparison has no unexpected expanded modes,
  sources, sandbox profiles, export kinds, or retention windows.

## Enforcement Points

- `scraper_side.snapshot --policy <path>` rejects `--live` collection and any
  source ID not listed in `allowed_source_ids`.
- `scripts/check-release-safety.py --tracked --paths-only` rejects enabled
  source catalog entries missing from `policy/source-catalog-allowlist.json`.
- `sandbox_runner run --policy <path>` rejects policies that do not allow
  `localhost_sandbox` validation and rejects sandbox profiles not listed in
  `allowed_sandbox_profiles`.
- `evidence.bundle --policy <path>` validates allowed modes and includes the
  policy ID/hash in the evidence bundle.
- `evidence.audit append --policy <path>` records the policy ID/hash in each
  local approval, denial, or export audit event.
- `evidence.audit retention --policy <path>` reports audit-log retention status
  from `retention.audit_log_max_days` and only deletes a fully expired runtime
  audit log when `--delete-expired-log --confirm-retention-delete` are both
  supplied.
- `policy.retention --policy <path>` reports runtime-output and customer
  metadata retention status from the reviewed policy and only deletes expired
  managed runtime files when `--delete-expired --confirm-retention-delete` are
  both supplied.
- `integrations.export --policy <path>` rejects SIEM, ticketing, or audit
  handoff export kinds not listed in `allowed_integration_exports`.
- `policy.lint --verify-runtime-artifacts <paths...>` rejects runtime artifact
  sets whose embedded policy hashes drift from the reviewed policy file.

Policies are not a substitute for RBAC, production-grade retention automation,
or production authorization. They are the paid-pilot fail-closed boundary.
