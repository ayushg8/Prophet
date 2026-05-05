# Validation Sprint Checklist

Date: 2026-05-05

This is the daily operating checklist for proving or disproving Prophet demand.
Do not add production platform scope while this checklist is red.

## Setup

- [ ] Create a private local folder: `validation/private/`.
- [ ] Copy `docs/customer-validation-log.example.json` to
  `validation/private/customer-validation-log.json`.
- [ ] Do not commit anything under `validation/private/`.
- [ ] Prepare the 10-minute demo around generated evidence, not platform
  architecture.
- [ ] Keep `docs/OUTREACH_PLAYBOOK.md` and `docs/CUSTOMER_DISCOVERY_GUIDE.md`
  open during outreach and calls.

## Daily Loop

Every weekday:

- [ ] Send 5 targeted warm/cold asks.
- [ ] Send 2 follow-ups.
- [ ] Ask every warm contact for one more specific intro.
- [ ] Book or run at least one qualified conversation when possible.
- [ ] Log each conversation in the private validation log.
- [ ] Run the scorecard.

```bash
python3 scripts/customer-validation-scorecard.py \
  --log validation/private/customer-validation-log.json
```

## Call Rules

- [ ] Start with the buyer's current workflow.
- [ ] Ask for the last painful prioritization event.
- [ ] Ask what artifact they had to produce.
- [ ] Ask who needed convincing.
- [ ] Ask what their existing tools did not provide.
- [ ] Show Prophet only after the pain is specific.
- [ ] Ask for a concrete next step.

## Weekly Review

Every Friday:

- [ ] Count qualified calls.
- [ ] Count high-pain calls.
- [ ] Count repeated workflow pains.
- [ ] Count stakeholder introductions.
- [ ] Count safe artifact offers.
- [ ] Count design-partner pilot discussions.
- [ ] Count paid/sponsored pilot signals.
- [ ] Decide: continue, narrow, pivot, or stop.

## No-Build Gate

Do not build more production infrastructure unless the scorecard returns one of:

- `pilot_pull_detected`
- `build_next_slice`

Exceptions:

- Fix broken tests.
- Fix safety issues.
- Improve validation artifacts that directly increase call quality.
- Package the existing pilot for a scheduled buyer review.

## Passing Signal

The validation sprint is passing when:

- 15 qualified calls are logged.
- 8 are high pain.
- 5 describe the same narrow workflow pain.
- 3 discuss a scoped design-partner pilot.
- 1 shows paid, sponsored, or procurement-sponsored pilot pull.

## Stop Signal

Stop or pivot if:

- Buyers cannot name a recent painful event.
- Buyers believe existing scanner/exposure-management tooling already solves
  the workflow.
- Buyers only want offensive/live validation.
- No one will introduce the budget owner.
- No one will provide even sanitized workflow artifacts.
