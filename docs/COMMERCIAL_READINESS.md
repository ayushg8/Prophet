# Commercial Readiness Plan

This document separates the credible product from the hackathon scaffolding.
The goal is to make Prophet defensible to investors, defense-tech buyers, and
security teams without overstating what currently works.

## Product Thesis

Prophet should be positioned as a policy-bound evidence workflow for
organizations that already have scanners, SIEMs, SBOM tools, exposure
management, threat intel, and ticketing systems. It does not replace those
systems. It helps operators turn those inputs into a defensible "why this
first" prioritization record and safe SOC/platform handoff.

The first sellable product is:

> A defensive exposure prioritization evidence copilot for mission-critical
> systems.

## May 2026 Market Reality

Current research supports a narrow evidence wedge, not a broad platform build:

- CISA BOD 22-01 requires federal civilian agencies to remediate KEV entries on
  CISA-set deadlines, and CISA says KEV should be an input to vulnerability
  prioritization rather than the only triage criterion. The current CISA KEV
  JSON feed reports catalog version `2026.05.08` with 1,590 vulnerabilities.
  Sources: [CISA BOD 22-01](https://www.cisa.gov/news-events/directives/bod-22-01-reducing-significant-risk-known-exploited-vulnerabilities),
  [CISA KEV JSON](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json).
- EPSS is already the standard language for "probability of exploitation in the
  next 30 days"; FIRST is explicit that EPSS is probabilistic and should not be
  sold as certainty. Prophet should consume EPSS-like pressure as evidence, not
  claim perfect prediction. Source: [FIRST EPSS model](https://www.first.org/epss/model).
- CMMC pressure is now contractual, not speculative. The 32 CFR CMMC program
  rule became effective on 2024-12-16, and the 48 CFR DFARS rule tying CMMC to
  contracts became effective on 2025-11-10. That makes DIB buyers more likely
  to care about defensible evidence, assessment posture, and audit trails.
  Sources: [32 CFR CMMC Program rule](https://www.federalregister.gov/documents/2024/10/15/2024-22905/cybersecurity-maturity-model-certification-cmmc-program),
  [48 CFR DFARS CMMC rule](https://www.federalregister.gov/documents/2025/09/10/2025-17359/defense-federal-acquisition-regulation-supplement-assessing-contractor-implementation-of).
- Incumbents already sell broad exposure management, prioritization, business
  context, attack-path analysis, and SIEM/ticket workflows. Tenable positions
  exposure management around unified data, business context, prioritization, and
  executive risk communication; Wiz emphasizes exploitability validation,
  ownership, and remediation workflows; Microsoft Sentinel analytics rules
  already generate alerts and incidents. Sources: [Tenable exposure management](https://www.tenable.com/exposure-management),
  [Wiz exposure management](https://www.wiz.io/solutions/exposure-management),
  [Microsoft Sentinel threat detection](https://learn.microsoft.com/en-us/azure/sentinel/threat-detection).

CEO implication: Prophet should not compete as "another scanner" or "better
exploit validation." The commercial test is whether DIB/federal-adjacent buyers
lack an audit-ready evidence packet that bridges existing tools into a
leadership/SOC decision.

## Buyer

Best-fit early buyers:

- Defense primes and DIB suppliers with exposed edge infrastructure.
- Federal-adjacent mission owners or integrators responsible for BOD/KEV,
  CMMC/NIST, and mission-assurance evidence.
- SOC and CTI teams that need to brief non-cyber leadership.
- Platform security teams maintaining deployable edge kits or disconnected
  environments.

Poor-fit early buyers:

- Teams looking for autonomous exploitation.
- MSSPs that need broad commodity scanning coverage.
- Buyers who require production live-target validation on day one.
- Buyers whose existing exposure platform already produces trusted,
  audit-ready prioritization and handoff evidence.

## Product Management Decisions

Primary buyer persona:

- DIB or federal-adjacent product security, platform security, vulnerability
  management, or mission-assurance leader.
- Owns the decision, budget path, or executive explanation for what exposure
  class should move first.

Primary evaluator persona:

- CISO, deputy CISO, mission owner, product-security leader, SOC/CTI leader, or
  security reviewer who can judge whether the evidence packet is trustworthy.

Primary daily user persona:

- Security operator, vulnerability management lead, product security program
  manager, or SOC/platform reviewer who assembles, reviews, or hands off the
  prioritization packet.

First paid wedge:

- One approved asset/SBOM family.
- One exposure-class prioritization decision.
- One evidence bundle with policy hash, source basis, asset basis, audit/hash
  manifest, and SIEM/ticket review templates.

Positioning decision:

- Prophet is evidence automation for defensive prioritization.
- Prophet is not a zero-day prediction product, exploit platform, autonomous
  defense system, scanner replacement, or broad anticipatory defense platform.

Paid-pilot conversion requires:

- A recent painful prioritization event.
- A repeated `workflow_pain_theme`.
- A named operating reviewer and sponsor or budget path.
- Approved customer-safe metadata boundary.
- Written pilot success criteria.
- Explicit rejection of live target testing, payloads, raw telemetry, and
  production control pushes.

Next-90-day non-goals:

- No live/offensive validation.
- No raw scanner or telemetry ingestion.
- No production SIEM/ticket pushes.
- No autonomous remediation.
- No hosted multi-tenant production build unless validation reaches
  `build_next_slice`.
- No custom integrations without a paid or sponsored pilot path.

Competitive set:

- Scanners and exposure-management platforms.
- SIEM and ticketing systems.
- SBOM and asset-inventory systems.
- CTI and KEV/EPSS-style prioritization workflows.
- Manual executive/audit evidence packets built in docs, tickets, and slides.

Prophet should complement those systems by producing the trusted "why this
first?" packet, not compete as another source of findings.

Success metrics:

- Time to create a leadership/SOC-ready evidence packet.
- Manual evidence assembly steps removed.
- Stakeholder trust in the "why this first?" rationale.
- Reviewer burden from irrelevant or false-positive findings.
- Number of unsafe requests blocked by policy.
- Number of buyers willing to repeat the workflow on another exposure class.

Feedback collection form:

```text
Account label:
Persona:
Workflow pain theme:
Recent painful event:
Current tools:
Manual evidence work:
Stakeholders who trust or reject the packet:
What Prophet made clearer:
What Prophet failed to answer:
Would they run it on another exposure class?
Sponsor, budget, or procurement path:
Next step:
```

## MVP Scope

The first sellable MVP should include:

- Deterministic forecaster with reproducible input bundles.
- Customer-owned asset/SBOM import, starting with a safe CSV importer that
  rejects unsafe rows and emits a cleanup report.
- Safe asset/SBOM seedset generation and seeded OSINT metadata enrichment.
- Safe exposure-class portfolio generation.
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
- Claims of zero-day prediction or exploit validation against real customer
  infrastructure.

## Required Hardening Before Paid Pilots

| Area | Required Work |
|---|---|
| Identity | Local operator labels, hash-chained approval records, RBAC decision primitive, and signed operator approval design exist; implement SSO/RBAC-backed signed approvals only after buyer/security-review pull. |
| Data | Separate raw collection, sanitized facts, and customer-owned context. |
| Validation | Package sandbox runners as reproducible containers or ephemeral VMs. |
| Integrations | Export to SIEM, Jira/ServiceNow, SBOM/asset systems, and evidence stores. |
| Governance | Source/profile/export allowlists and retention hints exist; add policy comparison, retention cleanup, and customer approval workflows. |
| Quality | CI, golden smoke hashes, browser smoke, dependency audit, and release checklists exist; add schema compatibility and mutation tests. |
| Security | Keep historical exploit lab material quarantined from default product distributions. |

## Demand Validation Gate

Do not build the full controlled-production roadmap until buyer pull is visible.
Use `docs/PRODUCT_VALIDATION_PLAN.md` and score anonymized discovery logs with
`scripts/customer-validation-scorecard.py`.

The minimum signal to keep building is:

- 15 qualified discovery conversations.
- 8 high-pain accounts.
- 3 design-partner pilot discussions.
- 1 paid, sponsored, or procurement-sponsored pilot path.

If the repeated pain is not evidence-backed prioritization and SOC/leadership
handoff, narrow or pivot before adding more platform infrastructure.

Current validation verdict from the example dashboard is `insufficient_data`.
Until private validation logs show `build_next_slice`, commercial work should
improve outreach, demo packaging, evidence clarity, and pilot conversion
materials rather than production platform scope. If the scorecard reaches
`pilot_pull_detected`, convert the design partner before adding platform scope.

## Evidence Bundle

Every production run should emit an evidence bundle with:

- Forecast ID and input hashes.
- Source references and confidence scores.
- Asset seed summary and seeded OSINT basis when supplied.
- Exposure-class portfolio with non-actionable defensive rationale.
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
- Live collection workflow disabled by default.
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
console. It still does not package production collection, production defense
generation, RBAC, signed approvals, automated retention cleanup, or deployment
hardening. That is acceptable for a paid pilot only when the fixture and
localhost boundaries are stated clearly.
