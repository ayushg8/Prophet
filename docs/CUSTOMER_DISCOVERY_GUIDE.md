# Customer Discovery Guide

Date: 2026-05-05

Use this guide to test whether Prophet is a real product. The goal is to learn
what buyers already do under pressure, not to get compliments on the demo.

## Call Structure

### First 5 Minutes: Context

- "What is your role in vulnerability prioritization or mission-system security?"
- "What kinds of systems are hardest to prioritize?"
- "When a high-profile CVE, KEV item, or geopolitical pressure window appears,
  what happens internally?"

### Next 15 Minutes: Current Workflow

Ask for specifics:

- "Tell me about the last time this was painful."
- "What triggered the scramble?"
- "Who asked for the answer?"
- "What tools did you check?"
- "What artifact did you produce?"
- "How long did it take?"
- "What was missing from the artifact?"
- "Who disagreed with the prioritization?"
- "What happened after the meeting?"

Push if answers are vague:

- "Can you name the exact team that owned the decision?"
- "Was this hours, days, or weeks of work?"
- "What did leadership need that the scanner did not provide?"
- "Did anyone ask, 'why this first?'"

### Next 10 Minutes: Status Quo

- "What tools are already in the loop?"
- "Which one is the source of truth?"
- "Where does scanner output stop being enough?"
- "Do you already use EPSS, KEV, threat intel, or exposure-management scoring?"
- "When CISA KEV, BOD, CMMC, or a government customer creates urgency, what
  evidence must be attached to the decision?"
- "Which part is still manual: asset/SBOM context, source justification,
  leadership briefing, SOC handoff, ticket writing, or audit trail?"
- "What do you trust?"
- "What do you ignore?"
- "What gets copied into tickets or leadership briefings manually?"

### Next 10 Minutes: Prophet Demo

Only demo after they describe a real workflow.

Show:

- Evidence Markdown.
- Policy ID/hash.
- Asset/SBOM basis.
- Source freshness and hashes.
- Sandbox validation summary.
- SIEM/ticketing review templates.
- Audit trail.

Say:

> This is not a scanner and not live validation. The question is whether an
> evidence packet like this would reduce the burden of deciding and proving what
> to harden first.

### Final 10 Minutes: Buying Signal

- "If this worked on one approved asset family, who would care?"
- "What would have to be true to run a pilot?"
- "What data could you safely provide?"
- "What would you refuse to provide?"
- "What system would this need to hand off to?"
- "Who owns budget for this pain?"
- "Can we schedule a design-partner pilot review with that person?"

## Strong Positive Signals

- They describe a recent event without prompting.
- They mention leadership, auditors, government customer pressure, or mission
  owner pressure.
- They say the hard part is explaining and proving priority, not finding CVEs.
- They already stitch together scanner, KEV, threat intel, SBOM, and tickets.
- They ask if Prophet can work with sanitized asset/SBOM data.
- They request the evidence sample.
- They introduce a second stakeholder.
- They ask about pilot scope, timeline, security review, or cost.

## Weak Or Negative Signals

- "Interesting" with no specific workflow.
- "Our scanner already does this."
- "We just patch everything critical."
- "Come back when you integrate with our full stack."
- "Can it exploit or validate against live targets?"
- "No budget owner, but I like it."
- "Send me a deck" with no next meeting.

## Do Not Say

- "We predict zero-days."
- "Autonomous cyber defense."
- "It replaces your scanner."
- "It can validate against your live environment."
- "Production ready."
- "CMMC/FedRAMP ready."

## Better Language

- "Evidence-backed prioritization."
- "A defensible packet for what to harden first."
- "Policy-bound, fixture-backed pilot."
- "Review templates, not production pushes."
- "Customer-owned metadata only."
- "No live targets, no payloads, no raw scraper text."

## Scoring Rubric

Score 1-5:

- Pain: how painful and repeated is the workflow?
- Urgency: does this matter now or someday?
- Status quo weakness: are current tools insufficient?
- Buyer access: can this person reach the budget owner?
- Data feasibility: can they provide safe metadata?
- Pilot pull: do they ask for or accept a concrete next step?

Interpretation:

- 24-30: strong design-partner candidate.
- 18-23: keep discovering; may become real.
- 12-17: weak signal.
- 6-11: not an ICP or not urgent.

## Required Notes

Capture:

- Anonymized account label.
- Segment.
- Persona.
- Qualified/not-qualified call flag.
- Current workflow.
- Recent painful event.
- Existing tools.
- Status quo gap.
- Desired output.
- Controlled `workflow_pain_theme`.
- Six score fields: `pain_score`, `urgency_score`,
  `status_quo_weakness_score`, `buyer_access_score`,
  `data_feasibility_score`, and `pilot_pull_score`.
- Budget signal.
- Pilot signal.
- Objections.
- Next step.

Do not capture:

- Names.
- Emails.
- Phone numbers.
- Private hostnames.
- IPs.
- Raw screenshots.
- Raw tickets.
- Raw scanner exports.
- Customer secrets.
