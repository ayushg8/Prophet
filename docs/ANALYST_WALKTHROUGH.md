# Twelve-Minute Analyst Walkthrough

Use this path when an analyst or security leader wants to inspect Prophet
beyond the three-minute smoke command, but still inside the safe pilot
boundary. The path is fixture-backed, seeded-OSINT-backed, policy-bound, and
localhost-only.

## Preconditions

Run the smoke path first from the repo root:

```bash
./scripts/run-pilot-demo-smoke.sh
```

Continue only if the command passes, the final hash check matches
`scripts/pilot-demo-smoke.sha256`, and no policy-hash drift is reported.

Expected generated files:

- `world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json`
- `evidence/outputs/runtime/latest-edge-appliance.md`
- `evidence/outputs/runtime/latest-edge-appliance.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- `integrations/outputs/runtime/latest-edge-appliance/manifest.json`

## Console Setup

Terminal 1:

```bash
cd prophet-console
npm ci
npm run dev:control
```

Terminal 2:

```bash
cd prophet-console
npm run dev
```

Open `http://127.0.0.1:5173`. Keep the console local. Do not enable VM
scraping, enter customer secrets, add target hosts, or paste raw scraper text.

## Timeboxed Review

| Time | Action | Evidence to point at |
|---|---|---|
| 0:00-1:00 | Confirm the safety boundary. The pilot is a defensive evidence workflow, not a live-target workflow. | `policy/prophet-pilot-policy.json`; console Policy Status panel. |
| 1:00-2:30 | Review the forecast. Name the strike window, strike vector, confidence, and source rail. | Console Forecast panel; `world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json`. |
| 2:30-4:00 | Review asset and seeded OSINT basis. Confirm sources are fixture-backed and customer-safe. | Evidence Markdown Open Source Basis and Asset/SBOM Seeds sections. |
| 4:00-5:30 | Review the human gate. Approvals and denials must create local audit evidence before validation or handoff. | Console gate state; `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`. |
| 5:30-7:00 | Review the defense artifact. Focus on patch summary, Sigma summary, and validation status. | Console Defense output; Evidence Defensive Output and Validation Evidence sections. |
| 7:00-8:30 | Review bundle integrity. Read bundle ID, bundle SHA-256, policy ID/hash, approval record hash, and artifact hashes. | Top of `evidence/outputs/runtime/latest-edge-appliance.md`; JSON `hashes` section. |
| 8:30-10:00 | Review source freshness, source failures, and redaction report. Confirm raw collection text is excluded. | Evidence Source Freshness And Failures and Redaction Report sections. |
| 10:00-11:00 | Review handoff exports. Confirm SIEM and ticket files are review templates, not production pushes. | Console Integration panel; `integrations/outputs/runtime/latest-edge-appliance/manifest.json`. |
| 11:00-12:00 | Record buyer fit and blockers. Decide whether the next pilot slice is policy, asset import, sandbox profile, or integration review. | `docs/EVALUATOR_WORKSHEET.md`. |

## Pass Criteria

- The console shows fixture, policy, evidence, export, and safety-boundary
  checks as ready.
- Evidence includes policy ID/hash, approval record hash, forecast hash,
  defense artifact hash, sandbox validation status, source hashes, and the
  no-live-target-data assertion.
- Integration exports are marked `review_template_only` and include hashes in
  the manifest.
- The audit export is hash-chained and has a redaction report.
- Every generated output reviewed is under an ignored `outputs/runtime`
  directory.

## Stop Criteria

Stop the review and do not present the run as buyer-ready if any of these
occur:

- Smoke hashes do not match the packaged manifest.
- Runtime artifacts report policy-hash drift.
- Console policy status cannot load.
- Any output path is outside an ignored `outputs/runtime` directory.
- Any artifact includes credentials, private hostnames, live IPs, raw scraper
  text, payload bytes, or live-target validation claims.
- Handoff files look like production API calls instead of review templates.

## Analyst Notes

Use `docs/EVALUATOR_WORKSHEET.md` while walking through the console. Capture
hashes and file paths, not screenshots as the primary evidence. The strongest
buyer conversation is usually the gap analysis: which customer-owned asset or
SBOM export can be imported safely, which source IDs should be allowlisted,
which sandbox profile would be approved, and which SIEM/ticketing handoff
format should be reviewed first.
