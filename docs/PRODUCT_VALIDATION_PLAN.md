# Prophet Product Validation Plan

Date: 2026-05-05

This plan pauses broad production-platform work until buyer demand is proven.
The goal is not to convince ourselves Prophet is clever. The goal is to find
whether real defense/security buyers pull Prophet toward a paid pilot.

## Brutal Thesis

Do not sell Prophet as "AI predicts zero-days." That pitch is too hard to
prove, sounds unsafe, and runs straight into threat-intel and exposure-management
incumbents.

The testable wedge is:

> Prophet creates audit-ready evidence for high-pressure vulnerability
> prioritization: what to harden first, why now, what sources support it, and
> what reviewable SOC/platform handoff comes next.

## Market-Informed Hypothesis

The market already has strong systems for vulnerability discovery, exposure
management, exploitability scoring, SIEM analytics, and ticket routing. The
buyer pain to validate is narrower:

> "Our tools tell us many things are risky. Under KEV/BOD/CMMC/customer
> pressure, we still need to produce a trusted evidence packet explaining why
> one exposure class moves first and what SOC/platform teams should review."

This hypothesis is only worth building around if buyers say the evidence
workflow is painful despite their current scanner, exposure-management, SIEM,
SBOM, and ticketing stack. If an incumbent product already gives them a
trusted, audit-ready "why this first" package, Prophet should narrow or pivot.

## Validation Goal

Within 30-45 days, prove or disprove that DIB/federal-adjacent security teams
have a painful, budgeted, repeated workflow around evidence-backed defensive
prioritization.

Do not count compliments. Count behavior:

- They give time after seeing the demo.
- They describe a recent painful prioritization event.
- They show or describe their current workflow.
- Their `workflow_pain_theme` clusters around the same narrow pain, not scattered
  curiosity.
- They offer sample asset/SBOM or process artifacts.
- They introduce another stakeholder.
- They agree to a paid or sponsored pilot.

## Hard Go/No-Go

### Continue Building If

- 15 qualified discovery conversations are completed.
- At least 8 score `high_pain`.
- At least 5 describe the same narrow workflow pain.
- The scorecard's `repeated_workflow_pain_count` is at least 5 for one
  controlled `workflow_pain_theme`.
- At least 3 agree to a design-partner pilot discussion.
- At least 1 agrees to pay, sponsor, or procurement-sponsor a pilot.
- The repeated pain is about evidence, prioritization, or leadership/SOC handoff,
  not generic "AI cyber would be cool."

### Pause Or Pivot If

- Buyers say their scanner/exposure-management platform already solves it.
- Buyers can show an existing report that leadership, auditors, SOC, and
  platform owners already trust for the same decision.
- They like the demo but cannot name a recent painful incident.
- They want live exploitation or autonomous remediation as the core value.
- They refuse to provide even sanitized workflow artifacts.
- No one will introduce a budget owner.
- The only interest is from people without budget, operational pain, or urgency.

## Primary ICP

Start narrow:

- Defense prime or DIB supplier security/platform leader.
- Owns exposed edge infrastructure, deployable environments, SBOM, or mission
  system security.
- Has to brief leadership or government customers after KEV/BOD/critical CVE
  pressure.
- Already has scanners and ticketing; the pain is prioritization and evidence,
  not raw vulnerability discovery.

Likely titles:

- VP Security
- Director of Product Security
- Director of Platform Security
- Head of Vulnerability Management
- CISO or deputy CISO at a DIB supplier
- CTI/SOC lead who briefs non-cyber leadership
- Mission assurance or cyber resilience lead

Avoid initially:

- MSSPs needing commodity scale.
- Red teams wanting offensive tooling.
- Buyers demanding production integrations before validating the workflow.
- Anyone whose first ask is live third-party validation.

## 45-Day Sprint

### Week 1: Package The Ask

- Freeze production-platform feature work.
- Merge or stabilize the current pilot branch.
- Prepare a 10-minute demo around the evidence bundle, not the UI.
- Send 30 targeted warm/cold outreach messages.
- Book 5 conversations.
- Record every conversation in an anonymized validation log.

Exit gate:

- At least 5 qualified conversations scheduled.
- At least 2 people agree to review generated evidence artifacts.

### Week 2: Discovery Before Demo

- Run 5-8 calls.
- Ask about recent prioritization pain before showing Prophet.
- Do not pitch until the buyer explains current workflow.
- Score each call with `scripts/customer-validation-scorecard.py`.
- Assign one controlled `workflow_pain_theme` per qualified call so repeated
  pain can be measured.
- Revise pitch based on buyer language.

Exit gate:

- At least 3 high-pain calls.
- At least 2 repeated workflow pains.
- At least 1 buyer offers a sanitized sample artifact or second stakeholder.

### Week 3: Demo And Narrow Pilot Offer

- Run demo only for qualified buyers.
- Show the 3-minute smoke and evidence bundle.
- Ask what would need to be true for a paid pilot.
- Send `docs/BUYER_FOLLOW_UP_PACKAGE.md` only after the buyer confirms a real
  workflow and stakeholder.
- Offer a narrow design partner pilot.
- Capture objections.

Exit gate:

- At least 3 pilot discussions.
- At least 1 buyer names budget, procurement path, or internal sponsor.

### Week 4: Design Partner Conversion

- Send the SOW-lite pilot offer.
- Ask for a paid pilot, not "feedback."
- Define pilot success around one workflow: evidence-backed prioritization for
  one exposure class or asset family.
- Do not build custom integrations unless a buyer commits.

Exit gate:

- 1 paid/sponsored pilot or 3 strong design partners with real artifacts.

### Days 31-45: Decide

Continue only if demand is real. If not, pivot the positioning or stop.

Decision options:

- **Go:** Build production v0.5 platform foundation.
- **Narrow:** Build a lighter evidence automation tool for vulnerability
  leadership workflows.
- **Pivot:** Reposition around compliance/evidence packets, not prediction.
- **Stop:** Do not build further without buyer pull.

## Demo Narrative

Use this order:

1. "Show me how you decide what gets fixed first when a high-profile CVE or KEV
   pressure hits."
2. "Where does evidence live today?"
3. "Who do you need to convince?"
4. "What would make that faster or more defensible?"
5. Then show Prophet evidence output.

Do not lead with:

- AI.
- Zero-day prediction.
- Autonomous defense.
- Live validation.
- Full platform roadmap.

## What To Measure

Required fields are enforced by `scripts/customer-validation-scorecard.py`.

- Segment.
- Persona.
- Current workflow.
- Recent painful event.
- Pain score.
- Urgency score.
- Existing tools.
- Why existing tools are insufficient.
- Desired output.
- Budget signal.
- Pilot signal.
- Objections.
- Next step.

## Source Of Truth

Use a private anonymized log based on
`docs/customer-validation-log.example.json`.
Use a private anonymized target tracker based on
`docs/validation-targets.example.json`.

Initialize both under ignored local storage with:

```bash
python3 scripts/init-validation-sprint.py
```

Do not commit real names, emails, phone numbers, company-private details, raw
customer hostnames, IPs, screenshots, transcripts, or proprietary artifacts.

Run:

```bash
python3 scripts/customer-validation-scorecard.py --log path/to/private-validation-log.json
```

Track outreach targets with:

```bash
python3 scripts/validation-targets-scorecard.py --targets path/to/private-targets.json
```

Use the combined daily dashboard with:

```bash
make validation-dashboard DATE=YYYY-MM-DD
```

When a private message pack exists, the dashboard includes
`outreach_execution` so the daily view shows pending send/update count,
dry-run verified/failed/skipped counts, and stale-command attention items.
The customer scorecard also includes `gaps_to_verdicts`, which makes the
remaining counts to `pilot_pull_detected` and `build_next_slice` explicit.
When `example_seed_log` is true, seed/example counts are not treated as
effective validation evidence and do not reduce those gaps.
The dashboard also reports `target_backed_validation`; production build scope
stays closed unless the interviews counted toward `build_next_slice` match
anonymized target labels whose tracker status is `call_booked` or `completed`
and whose segment/persona metadata matches the tracker.
The explicit `--allow-untracked-interview` bypass can preserve out-of-band
learning, but it cannot open the production build gate by itself.
Use `REPLACE_EXAMPLE_SEED=1` with the first real sanitized private interview to
remove the initialized example seed instead of manually editing the log. That
replacement must use a booked anonymized target through the Make wrapper or
`--require-target-status call_booked`; do not use the raw
`--allow-untracked-interview` bypass for seed replacement.

The scorecard returns a verdict:

- `insufficient_data`
- `do_not_build_yet`
- `keep_discovering`
- `pilot_pull_detected`
- `build_next_slice`

Only `build_next_slice` opens the production build gate.
`pilot_pull_detected` is a design-partner conversion signal, not permission to
add production platform scope.
The dashboard requires both the customer scorecard and `target_backed_validation`
to reach `build_next_slice` before `allowed_to_build_next_slice` becomes true.

## Next Build Only After Pull

If the private validation dashboard reaches `build_next_slice`, build the
smallest production slice required by the committed design partner:

1. Durable evidence store.
2. Tenant/RBAC API around evidence and policy.
3. Customer-safe SBOM/asset ingestion.
4. One integration dry-run path.
5. Sandbox container provenance.

Everything else waits.
