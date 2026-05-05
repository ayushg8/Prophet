# Validation Daily Brief

Date: 2026-05-05

Use this brief before each validation work session.

## Today's Objective

Book or run qualified discovery calls. Do not optimize the product before the
market speaks.

## Today's Minimum

- 5 targeted asks.
- 2 follow-ups.
- 1 referral ask.
- 1 update to the private validation log.
- 1 scorecard run.

## Script

Primary ask:

```text
I'm testing whether evidence-backed vulnerability prioritization is a real pain
for DIB/federal-adjacent security teams.

Not exploit tooling, not live validation. The question is: when pressure hits,
how do you prove what to harden first and what handoff should follow?

Have you had to build that justification manually?
```

If yes:

```text
Could I ask 20 minutes of workflow questions? I mostly want to understand the
last time this was painful. I can show a fixture-backed evidence packet at the
end if useful.
```

If no:

```text
That is useful. What tool or workflow already solves it well enough?
```

## Do Not Do

- Do not say "zero-day prediction."
- Do not lead with AI.
- Do not ask for raw customer data.
- Do not demo before understanding the current workflow.
- Do not build a requested integration unless they commit to a pilot path.

## Scorecard Command

```bash
python3 scripts/customer-validation-scorecard.py \
  --log validation/private/customer-validation-log.json
```

## Decision Rule

- `insufficient_data`: keep booking calls.
- `do_not_build_yet`: revise ICP/positioning.
- `keep_discovering`: keep calls and ask for pilot pull.
- `pilot_pull_detected`: convert to design partner.
- `build_next_slice`: build only what the committed pilot needs.
