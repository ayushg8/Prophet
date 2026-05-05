# Pilot Scope

## Goal

Validate Prophet as a defensive exposure prioritization and evidence workflow
for a defense-tech customer.

## In Scope

- Forecasting pressure windows and likely exposure classes.
- Customer-safe CSV asset inventory import with row-level cleanup report.
- Asset/SBOM inventory conversion into safe OSINT seedsets.
- Fixture-backed seeded OSINT metadata enrichment.
- Safe exploit-class portfolio generation.
- Reviewable patch and detection artifact summaries.
- Deterministic localhost sandbox artifact generation through
  `sandbox_runner`.
- Evidence bundle export in JSON and Markdown.
- Safe SIEM and ticketing handoff templates from validated evidence.
- Local operator labels, approval/denial audit events, and hash-chained runtime
  audit logs.
- Optional fictional or customer-owned asset/SBOM context at metadata level.
- Pilot policy enforcement for fixture, seeded OSINT, localhost sandbox, allowed
  source IDs, allowed sandbox profiles, and allowed integration export kinds.
- Policy linting for customer-specific allowed modes, blocked controls,
  attestations, retention hints, and runtime output paths.

## Out Of Scope

- Live target testing.
- Arbitrary target URL input.
- Exploit payload generation or delivery.
- Credential handling.
- Raw scraper output in the product repo.
- Production patch deployment.
- Cryptographic signing beyond SHA-256 hashing.
- Live OSINT collection unless a future policy explicitly enables it.

## Required Customer Inputs

- Pilot success criteria.
- Approved data boundary.
- Asset/SBOM fixture or customer-owned inventory export.
- Exposure classes or mission systems to model at sector/product-family level.
- Approval workflow for validation.
- Pilot policy review for allowed sources, sandbox profile, integration export
  kinds, validation mode, and evidence retention.
- Evidence retention and access-control requirements.

## Acceptance Criteria

- Customer can run `./scripts/run-pilot-demo-smoke.sh` from a fresh clone.
- The selected pilot policy passes `python3 -m policy.lint --policy <path>`.
- Any seeded OSINT snapshot and sandbox artifact are generated under that
  policy's allowed source IDs and sandbox profiles.
- Any SIEM, ticketing, or audit handoff export is generated under that policy's
  allowed integration export list.
- Console generates a fixture-backed evidence bundle.
- Evidence contains forecast, seeded OSINT basis, asset seed summary, portfolio,
  defense, validation, approval record hash, safety, policy ID/hash, source
  references, and SHA-256 hashes.
- The top-level smoke command verifies deterministic runtime artifact hashes
  against the packaged smoke hash manifest.
- Integration handoff outputs contain review templates and hashes, not automatic
  production deployment actions.
- No evidence field contains credentials, raw payload strings, live IPs,
  private hostnames, or target-control steps.
- Pilot stakeholders can distinguish fixture-backed behavior from future
  customer sandbox validation.
- Runtime outputs stay under ignored `*/outputs/runtime/` directories.
