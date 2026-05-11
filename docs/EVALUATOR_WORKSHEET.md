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

Use `docs/EXPOSURE_CLASSIFICATION_GUIDE.md` if the evaluator needs help turning
a buyer workflow into a safe exposure-class label.

| Question | Notes |
|---|---|
| Which exposure class would the customer want modeled first? | |
| Which asset/SBOM export can the customer provide safely? | |
| Which public sources should be allowed in a customer policy? | |
| Which sandbox or digital-twin environment could validate defenses? | |
| Which SIEM and ticketing handoff formats matter for the pilot? | |
| What evidence retention period does the customer require? | |
| What would make the pilot a paid expansion? | |

## CISO / Executive Review

Use this section when the reviewer owns risk, budget, or security approval.
Do not advance to a paid or sponsored pilot unless the reviewer can answer the
decision questions with concrete evidence.

| Question | Pass/Fail | Notes |
|---|---|---|
| Does the packet answer "why this first?" better than the current workflow? | | |
| Can the reviewer identify the team that would use the evidence? | | |
| Is the approved customer data boundary clear enough for security review? | | |
| Are the safety boundaries clear: no live targets, no payloads, no raw telemetry, no production pushes? | | |
| Are policy hash, approval hash, evidence hash, and handoff manifest hash reviewable outside the UI? | | |
| Does the pilot have written success criteria and a named sponsor or budget path? | | |
| Does the buyer want another scoped evidence workflow, not broad platform work? | | |
| Does the validation dashboard still keep production build scope closed unless it reaches `build_next_slice`? | | |

Executive go/no-go:

| Outcome | Use When | Notes |
|---|---|---|
| Stop | The buyer cannot name a recent painful prioritization event or trusted reviewer. | |
| Repeat narrowly | The pain is real but the selected asset/SBOM slice was wrong. | |
| Convert design partner | The buyer wants another scoped workflow with written success criteria and a sponsor. | |
| Build next slice | The dashboard reaches `build_next_slice` and the next slice maps to the proven evidence or integration gap. | |

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
