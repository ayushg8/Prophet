# Defense-Tech Readiness Review

Date: 2026-05-05

Review method: GStack-style loop across CEO/founder, engineering, CSO, and QA
lenses. This is a product-readiness assessment, not a claim that Prophet is
production-ready.

## Executive Verdict

Prophet is now credible as a repeatable paid-pilot package for defensive
exposure prioritization. The product should be sold as a decision-support and
evidence workflow for DIB, federal, and mission-owner teams that already have
scanners, SIEM, ticketing, SBOM, and vulnerability-management tools.

It should not yet be sold as an autonomous exploitation, live validation, or
production deployment system. The strong posture is the narrow one: fixture and
localhost-sandbox evaluation, customer-owned metadata only, policy-bound
evidence, and safe handoff templates for SOC review.

## What Is Real

- Deterministic forecaster with reproducible fixture and seeded-OSINT inputs.
- Fictional asset/SBOM inventory, safe CSV import, and safe seedset generation.
- Fixture-backed public-source OSINT snapshot generation.
- Safe exposure-class defense portfolio with non-actionable rationale.
- Deterministic sandbox runner artifact for the edge-appliance profile.
- Direction C artifact validator that rejects payloads, target-control fields,
  credentials, live targets, and unsafe text.
- Policy-bound evidence bundle with forecast, OSINT basis, asset seed summary,
  defense artifact, validation summary, safety attestation, policy hash, and
  SHA-256 hashes.
- Policy-gated source allowlists for seeded OSINT and sandbox-profile allowlists
  for deterministic validation artifacts.
- Policy-gated SIEM, ticketing, and audit handoff export allowlists.
- SIEM and ticketing handoff templates generated from validated evidence.
- Local operator labels, denial recording, and hash-chained audit events for
  approval and handoff export.
- Policy retention hints for runtime outputs, local audit logs, customer
  metadata, raw collection retention, and deletion review.
- React console and localhost control server for fixture-backed demo refresh,
  sandbox artifact generation, and evidence export.
- CI coverage for Python contracts, console lint/build, control evidence smoke,
  dependency audit, golden smoke hashes, and optional browser smoke.

## Defense Buyer Fit

The best first buyer is a team with exposed edge infrastructure and leadership
pressure to act before KEV or scanner findings become urgent. The wedge is not
finding every CVE. The wedge is helping a mission owner answer: which exposure
class should we harden first, why now, what evidence supports the decision, and
what reviewable defense package can the SOC and platform team take next?

Best-fit evaluators:

- Defense prime or DIB supplier platform-security teams.
- Federal mission owners responsible for BOD/KEV response.
- SOC and CTI teams that brief non-cyber leadership.
- Teams maintaining deployable edge kits, disconnected environments, or digital
  twins.

Poor-fit evaluators:

- Buyers demanding autonomous exploitation or live target testing.
- MSSPs needing broad commodity scanner coverage on day one.
- Teams requiring production patch deployment before trust, RBAC, signing, and
  retention are implemented.

## CSO Findings

Strong controls:

- Lab exploit material is not part of the default product flow.
- Runtime outputs are ignored and generated under `*/outputs/runtime/`.
- Live collection workflows are blocked by policy and an environment gate.
- Evidence and integration exporters validate hashes and reject unsafe keys or
  text.
- The new policy linter rejects unknown modes, enabled live controls, missing
  attestations, unsafe source/profile allowlist entries, and default outputs
  outside ignored runtime directories.

Remaining security gaps:

- No RBAC or SSO identity model.
- No cryptographic signing for approval records.
- No automated retention/deletion workflow for customer data.
- No formal STRIDE threat model for the production architecture.
- No containerized sandbox profile with image hashes, egress limits, and
  reproducible build record.

## Engineering Findings

The repo now has the right contracts: world forecast, exposure-class portfolio,
Direction C artifact, evidence bundle, integration manifest, policy file, and
validators. That is the right defense-tech shape because every interface can be
shown to a buyer and every artifact can be hashed.

The main architecture risk is that policy is still split across Python,
Node/control-server checks, and future integration restrictions. The new linter
reduces this risk for demos, but the next engineering step should centralize
policy semantics enough that source allowlists, sandbox profiles, exports,
retention, and operator approvals all use one policy interpretation.

## QA Findings

The pilot path is repeatable from one command:

```bash
./scripts/run-pilot-demo-smoke.sh
```

The smoke path is non-live and now includes policy linting before generating
runtime artifacts. Python unit tests cover contracts, sandbox runner, evidence,
integration export, assets, and policy linting. Console tests cover lint/build,
control evidence smoke, and browser smoke.

QA gaps:

- No mutation suite for unsafe evidence/export text.
- No fixture freshness check.
- No schema compatibility test for each public CLI.

## Paid-Pilot Blockers

Before a serious paid pilot, complete:

1. CISO evaluator checklist and data-boundary appendix.
2. Audit retention cleanup workflow and customer-facing audit export review.
3. Expected redacted artifact screenshots for sales handoff.
4. Production gap register with owner and target version.

Before production, complete:

1. RBAC/SSO and tenant isolation.
2. Signed evidence and approval records.
3. Approved sandbox orchestration with no-egress controls.
4. Formal threat model and incident response playbook.
5. Retention/deletion workflows and deployment hardening.

## Next Sprint

The next best work is audit retention cleanup/export, policy hash coverage
across every runtime manifest, then the sandbox container design. That sequence
strengthens buyer evaluation without widening the live-target surface.
