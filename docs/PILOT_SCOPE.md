# Pilot Scope

## Goal

Validate Prophet as a defensive exposure prioritization and evidence workflow
for a defense-tech customer.

## In Scope

- Forecasting pressure windows and likely exposure classes.
- Customer-safe CSV asset inventory import with row-level cleanup report.
- Asset/SBOM inventory conversion into safe OSINT seedsets.
- Fixture-backed seeded OSINT metadata enrichment.
- Safe exposure-class defense portfolio generation.
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

Use `docs/EXPOSURE_CLASSIFICATION_GUIDE.md` to choose exposure-class labels
that are useful for prioritization without naming live systems.

For the customer-safe post-demo package and success criteria template, use
`docs/BUYER_FOLLOW_UP_PACKAGE.md`.

## Customer Pilot Reference Architecture

This is the reference architecture for a scoped design-partner pilot. It is not
a hosted production architecture.

```text
Customer environment
  approved asset/SBOM metadata only
  current prioritization workflow description
  preferred SIEM/ticket review format
          |
          | sanitized metadata and written policy choices
          v
Prophet local pilot workstation
  policy lint and comparison
  safe asset/SBOM import
  fixture-backed or approved public-source context
  localhost sandbox summary
  evidence bundle, audit/hash manifest, review templates
          |
          | customer-approved summaries, hashes, and review templates
          v
Customer review
  security/product/SOC reviewer
  leadership or mission owner
  pilot sponsor
```

Boundary rules:

- No customer credentials, private hostnames, live IPs, target URLs, raw
  telemetry, raw scanner exports, or screenshots enter the pilot workstation.
- No production SIEM, ticketing, patching, or control system is changed by the
  pilot.
- Runtime outputs remain local and ignored unless the customer approves sharing
  a sanitized evidence packet.
- Future production architecture requires a separate decision on identity,
  tenant isolation, durable storage, secrets, audit retention, and deployment.
- Current pilot-mode threat boundaries are documented in
  `docs/SAFETY_ARCHITECTURE.md`; controlled-production threats are documented
  separately in `docs/THREAT_MODEL.md`.

## Pilot Data Boundary Appendix

Use this boundary before accepting any customer-owned pilot artifact. If the
buyer cannot agree to it, keep the pilot fixture-only.

Allowed customer-provided inputs:

- Product-family, package-family, or asset-family labels.
- Sanitized asset/SBOM metadata with no hostnames, IPs, credentials, or user
  records.
- Exposure classes, business criticality categories, and owner queue labels.
- Current workflow descriptions and preferred handoff formats.
- Written policy choices for allowed public sources, sandbox profile, export
  kinds, validation mode, retention, and review stakeholders.

Prohibited inputs:

- Credentials, secrets, session files, private keys, cookies, or API tokens.
- Live IPs, private hostnames, customer hostnames, target URLs, or arbitrary
  target input.
- Raw scanner exports, raw telemetry, raw logs, raw scraper text, screenshots
  of customer systems, or unredacted support bundles.
- Payloads, exploit procedures, target-control steps, or offensive automation.
- CUI or regulated data unless a separate written scope, storage boundary, and
  security review are completed first.

Storage and retention:

- The public pilot uses fictional fixtures only.
- Real customer metadata must not enter the public repo.
- Local pilot runtime outputs must stay under ignored `*/outputs/runtime/`
  paths.
- Private validation notes must stay under ignored `validation/private/`.
- Customer-controlled metadata requires a written retention and deletion
  expectation before use.

Export rules:

- Prefer hash-only manifests, sanitized summaries, and evidence Markdown before
  sharing full JSON.
- Share SIEM/ticket outputs only as review templates, not production-ready
  pushes.
- Do not share screenshots unless they pass
  `docs/CONSOLE_EXPECTED_SCREENSHOTS.md`.
- Use `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md` as the controlling
  review reference when in doubt.

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

## Buyer Review Criteria

Treat the pilot as useful only if the evaluator can say all of these are true:

- The evidence packet explains why one exposure class should be reviewed first.
- The evidence basis is reviewable without trusting the console UI alone.
- Safety boundaries are clear: no live targets, no payloads, no raw customer
  telemetry, and no production pushes.
- The SOC/ticket handoff templates are understandable as review templates.
- The buyer can name the stakeholder who would use or reject the packet.
- The buyer can name what would need to change before a paid or sponsored pilot.

Treat the pilot as not validated if the buyer only likes the demo, cannot name a
recent painful prioritization workflow, or wants live/offensive validation.
`pilot_pull_detected` means convert design partners first; only
`build_next_slice` opens production implementation scope.
