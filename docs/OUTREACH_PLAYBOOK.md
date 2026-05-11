# Outreach Playbook

Date: 2026-05-05

The outreach goal is not a demo. The goal is to find people who have recently
felt the pain of evidence-backed vulnerability prioritization.

## Target Segments

### Segment A: DIB Product Or Platform Security

Best first target.

Pain hypothesis:

- They maintain edge systems, deployable kits, or mission-adjacent products.
- They need to prove what to harden first under customer/government pressure.
- They already have scanners but still need an evidence narrative.

Titles:

- Director of Product Security
- Head of Platform Security
- VP Security Engineering
- Vulnerability Management Lead
- Mission Assurance Lead

### Segment B: Federal Mission Owner Or FFRDC/Integrator Advisor

Good discovery target; may not be buyer.

Pain hypothesis:

- They need prioritization and briefing artifacts.
- They care about KEV/BOD pressure and mission impact.
- They may influence but not buy.

### Segment C: SOC/CTI Leader

Useful if they brief leadership.

Pain hypothesis:

- They stitch together threat intel, scanner data, tickets, and detections.
- They need defensible handoff artifacts.

### Avoid Initially

- Red teams.
- MSSPs.
- Generic startup advisors without buyer context.
- Buyers asking first for offensive or live validation.

## Warm Intro Ask

```text
I'm testing a narrow defense workflow: helping DIB/federal security teams turn
asset/SBOM context, KEV/threat context, and sandbox validation into an
audit-ready "what should we harden first and why" evidence packet.

I'm not looking for generic feedback. I'm trying to talk to people who have had
to justify vulnerability prioritization to leadership, mission owners, or
government customers.

Who is the most operationally honest person you know in product security,
platform security, vulnerability management, or CTI who has felt that pain?
```

## Cold Email

Subject options:

- Quick question on vulnerability prioritization evidence
- How do you prove what to harden first?
- DIB security prioritization workflow question

Body:

```text
Hi,

I'm building Prophet, a policy-bound evidence workflow for defensive
prioritization. It does not do live target testing or exploit generation.

The narrow problem I'm testing: when a high-profile CVE, KEV item, or external
pressure window hits, security teams often have scanner output but still need to
justify what to harden first, why now, and what SOC/platform handoff should
follow.

Is that a real pain in your world, or does your current stack already solve it?

If you've dealt with this recently, I'd value 20 minutes to understand your
workflow. I can show a fixture-backed evidence packet, but mostly I want to hear
how you handle this today.

No sales deck, no live data ask.
```

## LinkedIn DM

```text
I'm testing a narrow DIB/federal security workflow: evidence-backed
prioritization for "what should we harden first and why?" after high-pressure
CVE/KEV events.

Not live testing, not exploit tooling. More like an audit-ready packet that
connects asset/SBOM context, source basis, validation, and SOC handoff.

Have you had to build that kind of justification manually? If yes, could I ask
you 3-4 questions about the workflow?
```

## Follow-Up After Interest

```text
Thanks. The useful version of this call is not a pitch.

I'd like to understand:

1. The last time prioritization was painful.
2. What tools and artifacts were involved.
3. What leadership or the SOC needed that was hard to produce.
4. Whether a policy-bound evidence packet would have helped.

If that pain is real, I can show the current fixture-backed demo near the end.
```

## Post-Demo Follow-Up

```text
Thanks for reviewing Prophet.

My read of your workflow:

- Pain:
- Current tools:
- Missing evidence:
- Stakeholders:
- Possible pilot slice:

The narrow pilot I would propose is one approved asset/SBOM family, one exposure
class, and one evidence/handoff package. No live targets, no payloads, no raw
customer telemetry.

Does that match what would be useful, or did I misunderstand the pain?
```

For qualified buyers, send the structured follow-up in
`docs/BUYER_FOLLOW_UP_PACKAGE.md`. Do not send the package as a cold deck or to
buyers who asked for live/offensive capability.

To generate daily first-touch, follow-up, backfill, and referral drafts from
the private tracker, render the outreach block JSON first, then render the
operator-facing message pack:

```bash
python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format json \
  --out validation/private/today-outreach-block.json
python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format markdown \
  --out validation/private/today-outreach-block.md
python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --require-date YYYY-MM-DD \
  --format json \
  --out validation/private/today-message-pack.json
python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --require-date YYYY-MM-DD \
  --format markdown \
  --out validation/private/today-message-pack.md
```

The generated drafts are private operator aids. They contain target labels and
message bodies only, not real names, emails, URLs, hostnames, IPs, screenshots,
or customer artifacts. Each draft includes a dry-run tracker update command for
audit detail and safer Make commands for normal execution.
Generated tracker commands include `--require-current-status` guards so stale
commands fail instead of moving an already-advanced target backward.
Run `make validation-apply-draft TARGET=... DATE=YYYY-MM-DD` before sending or
writing; it dry-runs the exact generated update and rejects stale packs. Add
`CONFIRM_SENT=1` only after a confirmed send. The Make wrapper also requires a
matching copy-only send artifact from `make validation-send-copy` or
`make validation-send-copy-batch` before it writes the tracker.
The Make wrapper requires exactly `CONFIRM_SENT=1`; any other non-empty
confirmation value fails closed.
Drafts are source-aware: `warm_intro_needed` targets ask for an intro, while
`cold_outreach` targets use direct discovery copy.
For normal send-by-send execution, run
`make validation-next-draft DATE=YYYY-MM-DD`; it renders the first pending draft
whose generated dry-run tracker command still verifies, rejects date-mismatched
packs, and writes `validation/private/today-next-draft.md`.
When you want a copy-only artifact for the sending channel, run
`make validation-send-copy DATE=YYYY-MM-DD`; it writes
`validation/private/today-send-copy.txt` without target labels, tracker
commands, or status metadata.
When sending from the rendered draft, copy the generated subject/body as-is, or
personalize only in the outreach channel after pasting. Do not store recipient
names, private contact details, or new claims in repo files.
The repo intentionally does not store recipient names, emails, LinkedIn URLs,
or outbound channel details. The external outreach channel and real contact
must come from outside the repo before sending any copy-only draft.
To render a specific draft, use
`make validation-draft TARGET=target-dib-platform-004 DATE=YYYY-MM-DD`; it
rejects packs that do not match the requested outreach date.

To check which drafted asks are still pending after outreach, run:

```bash
make validation-status DATE=YYYY-MM-DD
```

Manual equivalent:

```bash
python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date YYYY-MM-DD \
  --format json \
  --out validation/private/today-outreach-status.json
python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date YYYY-MM-DD \
  --format markdown \
  --out validation/private/today-outreach-status.md
```

The verifier checks pending generated tracker commands against the current
private tracker without writing and rejects date-mismatched packs when
`--require-date` is supplied. Treat `needs_attention` as a stale-command
warning and regenerate the pack or inspect the target before sending. In the
dashboard, also treat nonzero `dry_run_failed_count` as a stop signal before
sending more drafts from that pack.

When someone replies, triage the reply before touching the tracker:

- `book_call`: They describe relevant workflow pain, ask for a discovery call,
  or offer to route you to the workflow owner. Use `call_booked`.
- `disqualify`: They ask for live testing, offensive validation, exploit
  capability, raw target review, production pushes, or they are clearly outside
  the ICP. Use `disqualified`.
- `keep_pending`: They give a noncommittal answer, ask for a deck without a
  workflow, or say to follow up later. Keep the target in its current sent or
  follow-up status and update only the follow-up plan when a real date exists.
- `manual_review`: The reply contains private customer details, unclear scope,
  procurement/legal conditions, or a security-review ask. Do not paste the
  reply into the tracker; summarize only the safe action after review.

Use the no-write helper to turn the sanitized classification into the next safe
command:

```bash
make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call DATE=YYYY-MM-DD

python3 scripts/validation-reply-triage.py \
  --target-label target-dib-platform-001 \
  --classification book_call \
  --date YYYY-MM-DD \
  --format markdown
```

Update only the anonymized target tracker:

- `call_booked`: run
  `make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD`.
  Add `CONFIRM_TARGET=1` only after the dry-run summary is correct.
- `disqualified`: run
  `make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD`.
  Add `CONFIRM_TARGET=1` only after confirming the disqualification is safe and
  sanitized.
- `completed`: after the sanitized interview log is updated, run
  `make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD`.
  Add `CONFIRM_TARGET=1` only after the dry-run summary is correct.
- Never paste reply text, names, emails, phone numbers, URLs, hostnames, IPs,
  screenshots, or customer artifacts into the tracker.

## Referral Ask

```text
Who else has had to answer "why are we fixing this first?" under pressure from
leadership, a customer, or a government requirement?

An ideal intro is someone who owns vulnerability prioritization, product
security, platform security, CTI, or mission assurance and has felt the evidence
burden personally.
```

## Daily Target

For 30 days:

- 5 targeted asks per day.
- 2 follow-ups per day.
- If fewer than 2 follow-ups are due, use the outreach block's
  `Follow-Up Gap Backfill` section as extra first-touch asks and set real
  follow-up dates after sending.
- 3 discovery calls per week minimum.
- 1 design partner ask per qualified high-pain call.

Stop optimizing docs if calls are not happening.
