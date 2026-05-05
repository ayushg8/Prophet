# Commercial Readiness Plan

This document separates the credible product from the hackathon scaffolding.
The goal is to make Prophet defensible to investors, defense-tech buyers, and
security teams without overstating what currently works.

## Product Thesis

Prophet should be positioned as an anticipatory defense layer for organizations
that already have scanners, SIEMs, SBOM tools, and ticketing systems. It does
not replace those systems. It tells operators which exposure class deserves
attention before a geopolitical pressure window turns into a cyber campaign.

The first sellable product is:

> A defensive exposure prioritization and validation copilot for mission-critical
> systems.

## Buyer

Best-fit early buyers:

- Defense primes and DIB suppliers with exposed edge infrastructure.
- Federal mission owners responsible for BOD/KEV response.
- SOC and CTI teams that need to brief non-cyber leadership.
- Platform security teams maintaining deployable edge kits or disconnected
  environments.

Poor-fit early buyers:

- Teams looking for autonomous exploitation.
- MSSPs that need broad commodity scanning coverage.
- Buyers who require production live-target validation on day one.

## MVP Scope

The first sellable MVP should include:

- Deterministic forecaster with reproducible input bundles.
- Customer-owned asset/SBOM import, starting with a safe CSV importer that
  rejects unsafe rows and emits a cleanup report.
- Safe asset/SBOM seedset generation and seeded OSINT metadata enrichment.
- Safe exploit-class portfolio generation.
- Patch and detection artifact generation.
- Deterministic localhost sandbox artifact generation, later upgraded to
  customer-approved sandbox or digital-twin validation.
- Human authorization gate.
- Per-customer pilot policy linting and enforcement for allowed modes, source
  IDs, sandbox profiles, integration export kinds, blocked controls,
  attestations, and runtime output boundaries.
- Evidence export: forecast, rationale, sources, defense artifact, validation
  result, pilot policy ID/hash, and audit metadata.
- Safe SIEM and ticketing handoff templates generated from validated evidence.

It should exclude:

- Live third-party target testing.
- Raw social or dark-web content in the main app.
- Payload generation.
- Fully autonomous patch deployment.

## Required Hardening Before Paid Pilots

| Area | Required Work |
|---|---|
| Identity | Local operator labels and hash-chained approval records exist; add RBAC, SSO, and signed approval records. |
| Data | Separate raw collection, sanitized facts, and customer-owned context. |
| Validation | Package sandbox runners as reproducible containers or ephemeral VMs. |
| Integrations | Export to SIEM, Jira/ServiceNow, SBOM/asset systems, and evidence stores. |
| Governance | Source/profile/export allowlists and retention hints exist; add policy comparison, retention cleanup, and customer approval workflows. |
| Quality | CI, golden smoke hashes, browser smoke, dependency audit, and release checklists exist; add schema compatibility and mutation tests. |
| Security | Keep historical exploit lab material quarantined from default product distributions. |

## Evidence Bundle

Every production run should emit an evidence bundle with:

- Forecast ID and input hashes.
- Source references and confidence scores.
- Asset seed summary and seeded OSINT basis when supplied.
- Exploit-class portfolio with non-actionable rationale.
- Defense artifact diff or configuration guidance.
- Detection content and supported log sources.
- Sandbox validation pre/post status.
- Human approval record.
- Policy ID/hash and allowed-mode summary.
- Export hash and timestamp.
- Integration handoff manifest for SIEM/ticketing review templates when
  generated.

This is the artifact a CISO, mission owner, or contracting officer can review.

## Roadmap

### 0.2: Credible Demo

- Root README, security policy, and CI.
- Safe demo refresh and fixture artifact loading.
- VM scraper disabled by default.
- Browser-tested console replay.

### 0.3: Repeatable Pilot Package

- Top-level `./scripts/run-pilot-demo-smoke.sh` evaluator path.
- Fixture-backed asset-seeded OSINT snapshot generation.
- Deterministic sandbox runner artifact for the edge-appliance profile.
- Policy-bound evidence bundle export with SHA-256 hash coverage.
- Console evidence export that prefers a valid sandbox runtime artifact when
  present and permitted by policy, otherwise falls back to the checked-in
  fixture.
- Browser smoke workflow available as an optional CI workflow.

### 0.4: Defense Pilot

- SIEM export review templates.
- Ticketing export review templates.
- SBOM/asset enrichment.
- Per-customer policy examples, source/profile/export allowlists, and linter.
- Local operator audit logs with hash-chained approval, denial, and handoff
  export events.

### 1.0: Controlled Production

- Multi-tenant or single-tenant deployment mode.
- Approved sandbox orchestration.
- Compliance-ready retention and deletion controls.
- Formal model, source, and artifact evaluation harness.

## Honest Current State

The current repo is now a repeatable buyer pilot package: deterministic
forecasting, safe CSV asset import, safe asset seedset generation,
fixture-backed seeded OSINT, deterministic sandbox artifact generation,
policy-bound source/profile/export enforcement, policy-bound evidence export,
policy linting, contract tests, CI coverage, golden smoke hash verification,
local hash-chained operator audit, integration handoff templates, and a working
console. It still does not package a live exploit engine, production collection
plane, RBAC, signed approvals, automated retention cleanup, or deployment
hardening. That is acceptable for a paid pilot only when the fixture and
localhost boundaries are stated clearly.
