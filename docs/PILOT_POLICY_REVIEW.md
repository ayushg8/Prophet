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

Future signed policy review is documented in `docs/SIGNED_POLICY_DESIGN.md`.
That design does not implement key handling or signature verification; it
defines how a future buyer/security review could make policy files
tamper-evident after a paid-pilot or `build_next_slice` gate.

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

## Source Terms And License Review

Prophet's default buyer pilot uses fixture-backed seeded OSINT and public source
citations. The existence of a catalog entry or citation URL is not permission to
collect, store, redistribute, or automate against that source in a customer
pilot.

Before enabling a new source or using a customer-requested source in a pilot,
record a short review note that answers:

- Source ID and catalog path.
- Source owner or publisher.
- Public documentation or terms URL reviewed.
- Whether API keys, accounts, paid access, robots.txt, rate limits, or usage
  restrictions apply.
- Whether the source permits the intended collection mode, retention period,
  and customer sharing path.
- Whether raw bodies, diffs, comments, examples, screenshots, or full records
  must be discarded after parsing.
- Whether the sanitizer emits only approved fields, public citations, hashes,
  and short analyst-safe summaries.
- Whether the source can be represented with `retention.raw_collection_retained`
  set to `false`.

Do not treat this checklist as legal approval. If the terms are unclear,
commercial, account-gated, personal-data-bearing, movement-tracking, or likely
to expose target/victim details, leave the source disabled until legal/customer
approval and sanitizer tests exist.

## Customer-Approved Source Allowlist

For a design-partner pilot, source approval should be explicit and narrow. A
customer-approved source allowlist should contain only sanitized source IDs and
review metadata, not credentials, raw exports, target lists, private URLs, or
collector secrets.

Minimum fields for a customer source allowlist note:

```text
source_id:
source_class:
customer_approval_owner:
approval_date:
approved_collection_mode:
approved_retention_days:
raw_collection_retained: false
allowed_output_fields:
prohibited_fields:
sanitizer_or_parser:
policy_id:
policy_sha256:
reviewer:
```

Rules:

- Add the source ID to the pilot policy only after the customer approval note
  exists and the sanitizer/parser has tests.
- Keep credentials, API keys, account names, private URLs, and raw customer
  exports out of the allowlist note.
- Prefer fixture, seeded, or customer-provided metadata over live collection.
- Keep live collection disabled unless a separate customer policy explicitly
  authorizes the exact source, host, cadence, retention, and sanitized fields.
- Re-run `policy.lint`, source-catalog allowlist checks, release-safety checks,
  and the relevant sanitizer tests after every allowlist change.

## Future Source Catalog Changes

Every future enabled source catalog entry needs both policy and release-review
coverage:

1. Add or update the catalog entry in
   `world-side/scraper/config/source_catalog.json`.
2. Keep `enabled: false` until the terms, customer approval, and sanitizer
   tests are complete.
3. If the source becomes enabled, add its ID to
   `policy/source-catalog-allowlist.json` with release-review intent only.
4. Add the source ID to `allowed_source_ids` in the pilot or customer policy
   only when the policy is meant to allow that source for that pilot.
5. Run:

   ```bash
   PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
     --policy policy/prophet-pilot-policy.json

   PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py \
     --tracked --paths-only
   ```

6. Confirm runtime outputs still contain source citations and summaries only,
   not raw records, private hostnames, live target URLs, credentials, or
   payload/procedure material.

The release allowlist is a safety review artifact. It does not grant live
collection, bypass source terms, or authorize customer data handling.

## Future Required-Source Failure Budgets

The current buyer pilot summarizes source freshness and sanitized source
failures in evidence, but it does not implement required-source failure budgets.
Before any customer-specific policy depends on live or customer-approved source
collection, define a fail-closed source budget in policy and tests.

Minimum future policy fields:

```text
required_source_ids:
required_source_classes:
freshness_window_days:
minimum_successful_required_sources:
maximum_failed_required_sources:
failure_action: block_forecast_and_evidence
degraded_action: evidence_warning_only
```

Rules for future implementation:

- If a required source is unavailable, stale beyond the approved freshness
  window, missing from the sanitized manifest, or missing policy coverage,
  forecast and evidence generation must fail closed before buyer sharing.
- If optional sources fail, evidence may continue only when the policy allows a
  degraded result and the evidence lists sanitized failure summaries.
- Required-source failures must never echo raw source bodies, private URLs,
  credentials, hostnames, IPs, or raw customer telemetry.
- Failure budgets must be evaluated against sanitized manifests and source IDs,
  not free-text scrape output.
- Runtime artifacts must record the policy hash and the source-budget decision
  so `policy.lint --verify-runtime-artifacts` or a future verifier can detect
  drift.

Implementation remains gated on buyer/security-review demand or
`build_next_slice`; do not add live collection or customer source processing
only to satisfy this design.

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
