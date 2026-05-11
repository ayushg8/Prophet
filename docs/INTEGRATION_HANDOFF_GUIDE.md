# Integration Handoff Guide

Prophet integration exports are review templates. They are not production
deployments and they do not call customer SIEM, ticketing, or API endpoints.

## What Gets Exported

The handoff bundle writes:

- Splunk saved-search review template.
- Elastic detection-rule review template.
- Microsoft Sentinel analytic-rule review template.
- Jira remediation ticket review template.
- ServiceNow remediation task review template.
- Operator audit event.
- Handoff review checklist.
- Manifest with hashes for every file.
- Optional deterministic review ZIP containing the same validated files.

Runtime path:

```text
integrations/outputs/runtime/latest-edge-appliance/
```

## Operator Flow

1. Run the safe demo refresh if needed.
2. Load the defense fixture or complete the Prophet loop.
3. Generate the evidence bundle.
4. Export handoff templates from the console Handoff panel or the pilot smoke
   script.
5. Review the manifest hash and evidence bundle hash before sending files to a
   customer environment.
6. Review `manifest.customer_placeholder_validation.items` and map every listed
   placeholder only inside the customer environment.
7. Complete `review_checklist.md` before adapting templates in customer-owned
   SIEM or ticketing systems.
8. Use the review ZIP only as a convenience package; the manifest and checklist
   inside it still control review.

## Safety Boundary

The exporter enforces:

- `mode: review_template_only`.
- No external API calls.
- Customer placeholder validation in the manifest.
- No live target details.
- No payload text.
- No credentials.
- No private hostnames.
- Customer placeholders required before deployment.

Customer operators must map placeholders, field names, owners, indexes, data
views, workspaces, projects, and assignment groups inside their own systems.

## Acceptance Command

```bash
cd prophet-console
npm run acceptance
```

The acceptance path generates evidence and handoff artifacts, validates them,
checks the console, and browser-smokes the operator flow.
