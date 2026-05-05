# Evaluator Worksheet

Use this worksheet during a buyer, security, or mission-owner review. The
answers should reference generated runtime artifacts and hashes, not screenshots
or informal claims.

## Run Summary

| Field | Notes |
|---|---|
| Evaluator | |
| Date | |
| Scenario reviewed | Edge-appliance defensive pilot |
| Smoke command passed? | |
| Evidence bundle path | `evidence/outputs/runtime/latest-edge-appliance.json` |
| Evidence bundle SHA-256 | |
| Policy ID | |
| Policy SHA-256 | |
| Approval record SHA-256 | |
| Integration manifest SHA-256 | |

## Evidence Review

| Question | Pass/Fail | Notes |
|---|---|---|
| Does the forecast name a strike window and strike vector? | | |
| Does the evidence explain the asset/SBOM basis without live targets? | | |
| Does the evidence include seeded OSINT source IDs and hashes? | | |
| Does the defense artifact stay non-operational and defensive? | | |
| Does the sandbox validation result stay localhost/fixture-scoped? | | |
| Does the bundle include policy ID/hash and approval record hash? | | |
| Do generated handoff files read as review templates, not auto-deploy actions? | | |
| Are all generated outputs under ignored `outputs/runtime` directories? | | |

## Buyer Fit

| Question | Notes |
|---|---|
| Which exposure class would the customer want modeled first? | |
| Which asset/SBOM export can the customer provide safely? | |
| Which public sources should be allowed in a customer policy? | |
| Which sandbox or digital-twin environment could validate defenses? | |
| Which SIEM and ticketing handoff formats matter for the pilot? | |
| What evidence retention period does the customer require? | |
| What would make the pilot a paid expansion? | |

## Safety Boundary

Confirm before any customer-owned artifact is imported:

- No credentials, session files, private keys, live IPs, private hostnames, or
  raw scraper text are included.
- The selected policy passes `python3 -m policy.lint --policy <path>`.
- Allowed source IDs, sandbox profiles, and integration export kinds are
  explicitly listed in the policy.
- Runtime outputs remain under ignored `*/outputs/runtime/` paths.
- Any non-fixture validation plan has separate written approval.

## Decision

| Outcome | Notes |
|---|---|
| Ready for internal alpha? | |
| Ready for customer pilot discussion? | |
| Blockers before paid pilot | |
| Next agreed slice | |
