# Integration Handoff Review

Prophet integration exports are review templates. They are not production
deployments and they do not call SIEM, ticketing, or customer APIs.

## Generated Files

The console and smoke script write ignored runtime files under:

```text
integrations/outputs/runtime/latest-edge-appliance/
```

Expected files:

- `manifest.json`
- `siem/splunk_saved_search.json`
- `siem/elastic_detection_rule.ndjson`
- `siem/sentinel_analytic_rule.json`
- `tickets/jira_remediation_ticket.json`
- `tickets/servicenow_remediation_task.json`
- `audit/operator_approval_event.json`
- `review_checklist.md`

## SOC Review Checklist

- Confirm `manifest.mode` is `review_template_only`.
- Confirm `safety_attestation.no_external_api_calls` is `true`.
- Confirm the evidence bundle hash in `manifest.evidence_refs.bundle_sha256`
  matches the reviewed evidence bundle.
- Confirm policy ID and policy SHA-256 match the pilot policy approved for the
  evaluation.
- Confirm `manifest.policy_restrictions.allowed_integration_exports` matches
  the approved SIEM, ticketing, and audit export list.
- Confirm `manifest.customer_placeholder_validation.status` is
  `customer_mapping_required`.
- Confirm every generated `<...>` placeholder is listed in
  `manifest.customer_placeholder_validation.items` before customer mapping.
- Replace customer placeholders only inside the customer environment.
- Tune query fields and thresholds against customer-owned telemetry.
- Attach the Prophet evidence hash and policy hash to the change ticket.
- Have a human SOC owner approve the final production detection before deploy.
- Complete `review_checklist.md` and keep it with the customer change record.
- Confirm `review_checklist.md` includes sign-off fields for reviewer role,
  evidence hash, policy hash, placeholder mapping, telemetry mapping, customer
  owner approval, and deployment decision.

## What Not To Do

- Do not deploy generated SIEM templates without customer review.
- Do not add live target names, private hostnames, IPs, credentials, raw logs, or
  payload strings to the exported files.
- Do not convert the handoff templates into API calls from the public demo repo.
- Do not treat ticket exports as approved remediation orders; they are draft
  review records.

## Console Path

1. Start the local control server with `npm run dev:control`.
2. Start the console with `npm run dev:evaluator`.
3. Load the defense fixture or generate a sandbox artifact.
4. Generate the evidence bundle.
5. Click **Export Handoff**.
6. Review the manifest hash and output path in the Handoff panel.

## Acceptance Signal

The handoff is ready for customer review when:

- Evidence generation completed without validation errors.
- The Handoff panel shows an export ID, `review_template_only` mode, file count,
  export hash, evidence bundle ID, and policy ID.
- The manifest includes `customer_placeholder_validation` and lists the
  customer-owned telemetry, owner, queue, or project placeholders that must be
  mapped before use.
- `npm run test:control:evidence` passes.
- `./scripts/run-pilot-demo-smoke.sh` passes.
