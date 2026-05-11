# Pilot Output Snippets

These snippets show the shape of the buyer-safe edge-appliance pilot outputs.
They are not the authoritative artifacts. The authoritative artifacts are
generated under ignored `*/outputs/runtime/` paths by:

```bash
./scripts/run-pilot-demo-smoke.sh
```

Verify current runtime files against the packaged manifest with:

```bash
shasum -a 256 -c scripts/pilot-demo-smoke.sha256 --quiet
```

Do not paste raw customer exports, raw source records, raw validation logs,
target names, credentials, live IPs, private hostnames, screenshots, or payload
material into this file.

## Asset Import Manifest

Path:
`assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.manifest.json`

Packaged SHA-256:
`503a9f34dc84fc8124e9d581ca9d69829d655a8055399c1efbdc56f7779caa04`

Redacted snippet:

```json
{
  "schema_version": "asset_csv_import_manifest.v0.1",
  "inventory_id": "demo-dib-edge-appliance-csv-import",
  "import_summary": {
    "accepted_row_count": 3,
    "rejected_row_count": 0,
    "total_row_count": 3
  },
  "source": {
    "raw_csv_embedded": false,
    "raw_row_values_embedded": false,
    "raw_csv_sha256": "4b7e789a3d4cbcf081b9e3a6258bbb97cc14db075f80532a8cca5d60b71b1635"
  },
  "safety_attestation": {
    "customer_owned_metadata_only": true,
    "manifest_contains_hashes_only_for_raw_input": true,
    "no_collection_performed": true
  }
}
```

What this proves: the pilot can accept customer-safe metadata while keeping raw
CSV values out of the review artifact.

## Forecast Output

Path:
`world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json`

Packaged SHA-256:
`6fb56fdc9ffd3ac7ca1d0a593bc444e0b46c72d134e6785dd7a2ce4b981ed151`

Redacted snippet:

```json
{
  "schema_version": "world_forecast.v0.1",
  "forecast_id": "ws-20260504-6b31ef03",
  "summary": {
    "one_line": "For edge-device auth bypass, rank edge-appliance initial access and pre-positioning highest and treat 2026-05-02 to 2026-05-16 as the lead strike-window forecast.",
    "stage3_priority": "Prioritize detection and blocking for perimeter-device access patterns, configuration drift, and suspicious administrative sessions."
  },
  "top_window": {
    "start_date": "2026-05-02",
    "end_date": "2026-05-16",
    "confidence": "high"
  },
  "top_vector": {
    "vector_class": "edge-appliance initial access and pre-positioning",
    "target_sector": "US federal and defense-industrial perimeter services",
    "likely_objective": "persistence"
  }
}
```

What this proves: the forecast artifact is sector and class level. It is not a
live target list or an attack procedure.

## Evidence Bundle

Path:
`evidence/outputs/runtime/latest-edge-appliance.json`

Packaged SHA-256:
`9570017c12c2132f7b60fc2d8458bcfd9eef88683dc0b58a5905ba4c6bbe6e3c`

Redacted snippet:

```json
{
  "schema_version": "prophet_evidence_bundle.v0.1",
  "bundle_id": "peb-9021f74651743b33",
  "policy": {
    "policy_id": "prophet-pilot-fixture-localhost-v0.1",
    "policy_sha256": "7d051922a110f024188b522b89d11782151cce2d58fa606f7c319c48f405075c",
    "enforced": true
  },
  "validation_summary": {
    "sandbox_scope": "localhost only; deterministic fixture simulation; no network egress",
    "pre_patch_status": "vulnerable",
    "post_patch_status": "blocked",
    "failure_evidence": {
      "result": "passed",
      "failure_detected": false,
      "failure_kind": "none"
    }
  },
  "sandbox_provenance": {
    "profile": "edge-appliance-fixture",
    "mode": "fixture",
    "raw_logs_retained": false,
    "no_network_egress": true
  },
  "forecast_summary": {
    "source_ref_ids": [
      "src_chatter_fixture_001",
      "src_context_chatter",
      "src_hist_10_corpus",
      "src_hist_8_corpus"
    ],
    "vector": {
      "why_this_vector": "Perimeter appliance cases in the corpus, especially Volt Typhoon and Ivanti, make this the strongest fit."
    }
  },
  "safety_attestation": {
    "no_live_targets": true,
    "no_live_target_data_included": true,
    "no_payloads": true,
    "no_credentials": true,
    "no_raw_scraper_text": true
  }
}
```

What this proves: the evidence bundle ties policy, validation, and safety
attestations together in one reviewable artifact.

## Evidence Markdown

Path:
`evidence/outputs/runtime/latest-edge-appliance.md`

Packaged SHA-256:
`e537d54dc6a365e8dfb682efe86da2eb5e23fc2270a2b550c869d3d8e63fa7b1`

Redacted snippet:

```text
Bundle peb-9021f74651743b33 records a validated Prophet fixture run.
The prioritized vector is edge-appliance initial access and pre-positioning.
Validation finished with blocked.

Forecast:
- Why this window: sanitized public chatter overlaps the candidate profile.
- Why this vector: perimeter appliance cases make this the strongest fit.
- Cited forecast source IDs: src_chatter_fixture_001, src_context_chatter, src_hist_10_corpus, src_hist_8_corpus

Safety boundary:
- No live targets: true
- No live target data included: true
- Fixture backed: true
- Validation scope: localhost only; deterministic fixture simulation

Sandbox provenance:
- Profile: edge-appliance-fixture
- Raw logs retained: false
- No network egress: true
```

What this proves: a non-technical reviewer can inspect the same evidence without
opening the JSON bundle.

## Audit Export

Path:
`evidence/outputs/runtime/pilot-demo-operator-audit-export.json`

Packaged SHA-256:
`aed651d9fd244e6d55a9db7078079984e8d023ba8b699df22f784205e80caca7`

Redacted snippet:

```json
{
  "schema_version": "prophet_operator_audit_export.v0.1",
  "event_count": 1,
  "event_type_counts": {
    "operator_approval": 1
  },
  "decision_counts": {
    "bypassed_for_fixture": 1
  },
  "latest_event_hash": "5df35f7f7b8a4f963791f8fc5fa616ebed9601a3965a53753b52271dcb968866",
  "redaction_report": {
    "summary_fields_only": true,
    "source_log_embedded": false,
    "raw_event_bodies_embedded": false
  }
}
```

What this proves: the review artifact summarizes the approval chain without
embedding raw runtime event bodies.

## Integration Handoff Manifest

Path:
`integrations/outputs/runtime/latest-edge-appliance/manifest.json`

Packaged SHA-256:
`dfe1d31264779b5168b6f8bd3cb07eca641c901d795897dae882acf4a4da1d7f`

Review ZIP:
`integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip`

Review ZIP SHA-256:
`e676da036f9f5e4d8c2bbbe6306486654a6463dcba37f5985e9a8b1392e29280`

Redacted snippet:

```json
{
  "schema_version": "prophet_integration_export.v0.1",
  "mode": "review_template_only",
  "summary": {
    "title": "Prophet defense handoff for edge-appliance initial access and pre-positioning",
    "validation_status": "blocked",
    "vector_class": "edge-appliance initial access and pre-positioning"
  },
  "safety_attestation": {
    "review_templates_only": true,
    "no_external_api_calls": true,
    "no_live_targets": true,
    "no_live_target_data_included": true,
    "customer_placeholders_required": true
  },
  "customer_placeholder_validation": {
    "schema_version": "prophet.customer_placeholder_validation.v0.1",
    "status": "customer_mapping_required",
    "review_signoff_field": "placeholders_mapped"
  }
}
```

What this proves: integration output is a SOC/ticketing review package, not a
production push.

## Stop Conditions

Stop review and regenerate artifacts if:

- Any packaged SHA-256 does not match `scripts/pilot-demo-smoke.sha256`.
- Any artifact reports policy-hash drift.
- Any runtime artifact includes live targets, credentials, private hostnames,
  live IPs, raw source text, raw customer rows, payload material, or target
  control steps.
- A requested pilot depends on live/offensive validation or autonomous
  remediation.
