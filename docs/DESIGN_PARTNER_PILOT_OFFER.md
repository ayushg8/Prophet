# Design Partner Pilot Offer

Date: 2026-05-05

This is the narrow offer to make after discovery shows real pain. Do not offer
a broad production platform. Offer one evidence workflow.

## Pilot Promise

Prophet will produce a policy-bound evidence package that helps your team decide
and justify what exposure class to harden first for one approved asset or SBOM
family.

The pilot is not a request to replace your scanner, SIEM, SBOM system,
ticketing system, or exposure-management platform. It is a test of whether your
team lacks a trusted evidence bridge between those tools when leadership,
customer, KEV/BOD, CMMC, or mission pressure asks, "why this first?"

## Pilot Scope

Included:

- One approved product family, asset family, or SBOM slice.
- Customer-safe metadata only.
- Fixture-backed or customer-approved public-source context.
- Policy-bound forecast and evidence generation.
- Reviewable patch/detection/SOC handoff templates.
- Local or customer-approved sandbox validation summary.
- Audit trail with policy hash and artifact hashes.

Excluded:

- Live target validation.
- Exploit payload generation.
- Autonomous patch deployment.
- Raw telemetry ingestion.
- Raw scanner export storage.
- Production SIEM/ticket push without separate approval.
- CUI handling unless separately scoped and reviewed.

## Ideal Pilot Buyer

- Owns vulnerability prioritization, product security, platform security, CTI,
  or mission assurance.
- Has felt pressure to justify "why this first?"
- Can provide sanitized asset/SBOM metadata.
- Can review evidence with SOC/platform stakeholders.
- Can sponsor a paid pilot or introduce the budget owner.

## Pilot Inputs

Customer provides:

- Sanitized asset/SBOM metadata at product-family or package-family level.
- Exposure classes or business criticality categories.
- Current prioritization workflow description.
- Target SIEM/ticketing format preference.
- Retention requirements.
- Written approval for any non-fixture source or sandbox mode.

Prophet provides:

- Safe importer and rejection report.
- Policy file.
- Evidence bundle.
- Audit export.
- SIEM/ticketing review templates.
- Final findings memo.

## Success Criteria

The pilot succeeds if the customer says at least three are true:

- Prophet reduced time to create a leadership/SOC-ready prioritization packet.
- Prophet connected asset context, public-source context, and evidence better
  than the current workflow.
- Prophet produced a defensible "why this first?" artifact.
- Prophet's policy/audit/hash posture made the output easier to trust.
- The team would run this workflow again for another exposure class.
- The team wants integration into an existing scanner, SIEM, ticketing, or SBOM
  workflow.

The pilot fails or should not proceed if the customer cannot name a recent
prioritization event, cannot identify a stakeholder who needed the evidence, or
already has a trusted incumbent workflow that produces the same evidence packet.

## Suggested Paid Pilot Shape

Duration:

- 4-6 weeks.

Work:

- Week 1: Scope and safe metadata import.
- Week 2: Generate first evidence package.
- Week 3: Review with SOC/platform/security leadership.
- Week 4: Revise evidence and handoff format.
- Week 5-6: Optional second exposure class or integration dry-run design.

Commercial:

- Paid design partner, not free consulting.
- Price should be high enough to prove pain but low enough for pilot approval.
- If procurement is slow, require a named executive sponsor and written pilot
  success criteria before custom work.

## Pricing And Packaging Memo

Do not publish broad platform pricing before demand is proven. Use pricing as a
validation tool: a buyer who will not sponsor even a narrow pilot may not have
urgent pain.

Package ladder:

| Package | Use When | Includes | Excludes |
|---|---|---|---|
| Discovery review | Buyer has not described a recent painful event. | Workflow questions, fixture-backed evidence walkthrough, qualification. | Custom work, customer metadata import, integration design. |
| Paid design-partner pilot | Buyer has repeated pain, safe metadata, reviewer access, and a sponsor. | One approved asset/SBOM slice, one evidence packet, review templates, final findings memo. | Production deployment, live validation, raw telemetry, broad platform access. |
| Sponsored procurement path | Procurement is slow but an executive sponsor can fund or route the pilot. | Same as design-partner pilot, with written success criteria and procurement sponsor. | Free custom work while waiting for procurement. |
| Build-next-slice scope | Private validation reaches `build_next_slice`. | Only the proven evidence or integration gap from the pilot. | Unvalidated platform roadmap, multi-tenant production scope, unrelated features. |

Pricing principles:

- Charge for custom pilot work once a buyer asks Prophet to use customer-owned
  metadata or adapt the evidence packet.
- Keep the first paid pilot narrow enough for a single sponsor to approve.
- Do not discount by adding scope; reduce scope if approval is hard.
- Do not accept unpaid pilots that require customer-specific work, special
  integrations, or security review.
- If the buyer cannot name budget, sponsor, procurement path, or operating
  reviewer, keep the conversation in discovery.

## Pilot Support Model

Use this support model only for a scoped design-partner pilot. It is not a
production SLA.

Roles:

- Customer sponsor: owns budget, success criteria, and go/no-go decisions.
- Customer operator: provides approved metadata and reviews evidence output.
- Prophet operator: runs the approved workflow, shares evidence, and records
  pilot issues.
- Security reviewer: confirms the data boundary and safety exclusions.

Cadence:

- Kickoff: confirm scope, success criteria, data boundary, retention, and
  handoff format.
- Weekly review: inspect the evidence packet, issue log, and next slice.
- Ad hoc support: handle blocked pilot runs, unclear evidence, or policy
  questions during agreed working hours.
- Closeout: decide stop, repeat narrowly, convert design partner, or build next
  slice.

Supported during the pilot:

- Fixture-backed or approved metadata import questions.
- Policy lint and policy comparison questions.
- Evidence bundle and hash review questions.
- SIEM/ticket review-template interpretation.
- Sanitized workflow and success-criteria updates.

Not supported without a separate scope:

- Live target testing.
- Payload generation.
- Raw telemetry troubleshooting.
- Production SIEM/ticket deployment.
- Customer incident response.
- CUI handling or regulated-data processing.

## Pilot Onboarding / Offboarding Checklist

Use this checklist before the first customer-owned metadata review and at
pilot closeout.

Onboarding:

- Name the customer sponsor, customer operator, security reviewer, and Prophet
  operator.
- Confirm the recent prioritization event, workflow pain, and written success
  criteria.
- Confirm the approved data boundary from `docs/PILOT_SCOPE.md`.
- Confirm the retention expectation and where generated pilot artifacts may
  live.
- Confirm the allowed policy modes, public sources, sandbox profile, and
  handoff export kinds.
- Run the fixture-backed smoke before accepting any customer metadata.
- Record the first approved asset/SBOM slice at product-family or
  package-family level only.

Offboarding:

- Deliver the final evidence packet, audit/hash manifest, and findings memo.
- Record the go/no-go outcome: stop, repeat narrowly, convert design partner,
  or build next slice.
- Delete or rotate ignored local runtime outputs according to the agreed
  retention expectation.
- Delete or rotate private validation notes that are no longer needed.
- Confirm no credentials, live IPs, private hostnames, raw telemetry,
  screenshots, payload material, or CUI entered product paths.
- Keep only customer-approved summaries and hashes for future reference.

## Pilot Issue Communication Template

Use this for pilot issues only. Do not include private data.

```text
Subject: Prophet pilot issue: <blocked run | evidence question | policy question>

Summary:
- Pilot slice:
- Issue type:
- Impact on pilot success criteria:
- Artifact path or hash, if safe:

Safety check:
- No credentials, private hostnames, live IPs, raw telemetry, screenshots, or
  payload material included.
- No production system was changed.

Requested next step:
- Rerun fixture-backed workflow.
- Review policy or data boundary.
- Clarify evidence packet.
- Pause the pilot.
```

## SOW-Lite Template

```text
Objective:
Produce an audit-ready defensive prioritization evidence package for one
approved asset/SBOM family.

Customer inputs:
- Sanitized asset/SBOM metadata.
- Approved source/policy constraints.
- Target review stakeholders.
- Preferred handoff formats.

Prophet deliverables:
- Policy-bound evidence bundle.
- Source and asset basis summary.
- Defensive artifact summary.
- Sandbox validation summary where approved.
- SIEM/ticketing review templates.
- Audit and hash manifest.
- Final pilot findings memo.

Out of scope:
- Live target testing.
- Payload generation.
- Raw telemetry storage.
- Production control deployment.
- CUI handling unless separately approved.
- Claims that Prophet predicts zero-days or validates real exploitability.

Success criteria:
- Customer can decide whether Prophet should advance to a production-shaped
  integration pilot.
```

## Conversion Ask

At the end of a strong demo:

```text
It sounds like the pain is not finding more vulnerabilities. The pain is
building a defensible packet for why one exposure class should move first.

The narrow pilot I would propose is one approved asset/SBOM family and one
evidence package, with no live targets or raw telemetry. If this saves your team
time and creates a better leadership/SOC handoff, we can discuss integration.

Who would need to approve that pilot, and is this worth putting a paid design
partner scope around?
```

## Post-Pilot Conversion Plan

Do not treat a good demo as permission to build production scope. Convert only
from a completed paid or sponsored pilot review.

At the end of the pilot, choose one outcome:

- Stop: Prophet did not reduce evidence work or the incumbent workflow already
  solves the problem.
- Repeat narrowly: the pain is real, but the first asset/SBOM slice was the
  wrong slice.
- Convert design partner: the buyer wants another scoped evidence workflow with
  written success criteria and a named sponsor.
- Build next slice: the validation dashboard reaches `build_next_slice`, the
  buyer names a budget or procurement path, and the next slice is limited to the
  integration or evidence gap proven in the pilot.

Before any build-next-slice work, require:

- Written pilot readout against the success criteria above.
- Named buyer sponsor and operating stakeholder.
- Approved data boundary and retention expectation.
- Security review of the proposed customer-safe metadata flow.
- Explicit exclusion of live target testing, payload generation, raw telemetry
  storage, autonomous remediation, and production control pushes.

If those conditions are not met, keep working the validation sprint instead of
building platform scope.
