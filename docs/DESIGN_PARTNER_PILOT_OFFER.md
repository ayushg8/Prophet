# Design Partner Pilot Offer

Date: 2026-05-05

This is the narrow offer to make after discovery shows real pain. Do not offer
a broad production platform. Offer one evidence workflow.

## Pilot Promise

Prophet will produce a policy-bound evidence package that helps your team decide
and justify what exposure class to harden first for one approved asset or SBOM
family.

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
