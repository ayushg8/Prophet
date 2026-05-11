# Validation Daily Brief

Date: 2026-05-05

Use this brief before each validation work session.

If you need to rebuild the private workspace for a prior outreach day, run
`python3 scripts/init-validation-sprint.py --date YYYY-MM-DD`; otherwise the
initializer prints dry-run examples using the current local date. The Makefile
wrappers also accept `DATE=YYYY-MM-DD`.
If the ignored private README is stale after a recovery, refresh only that
operator guide without overwriting private tracker/log files:
`python3 scripts/init-validation-sprint.py --date YYYY-MM-DD --refresh-readme`
or `make validation-init DATE=YYYY-MM-DD REFRESH_README=1`.
After a terminal restore, machine sleep, or crash, run `date +%F`. If that date
is not the outreach day you are operating, pass `DATE=YYYY-MM-DD` explicitly to
`make validation-pack`, `make validation-next-draft`, `make
validation-apply-draft`, `make validation-log-interview`, and `make
validation-status`, and `make validation-dashboard`.
Use `make validation-resume DATE=YYYY-MM-DD`, or
`make goal-resume DATE=YYYY-MM-DD` after a lost `/goal` session, when an
outreach pack already exists and you want the dashboard plus the existing next
draft in one no-write command.

## Today's Objective

Book or run qualified discovery calls. Do not optimize the product before the
market speaks.

## Today's Minimum

- 5 targeted asks.
- 2 follow-ups.
- 1 referral ask.
- 1 update to the private validation log.
- 1 scorecard run.

Generate the day's safe target block, message pack, and status reports from the
private tracker:

```bash
make validation-pack DATE=YYYY-MM-DD
```

The Makefile wrapper writes JSON and Markdown outputs for the outreach block,
message pack, and outreach status. Manual equivalent for the first step:

```bash
python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format json \
  --out validation/private/today-outreach-block.json
python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format markdown \
  --out validation/private/today-outreach-block.md
```

If the block says no follow-ups are due, use the `Follow-Up Gap Backfill`
section as extra first-touch asks for that day. Do not invent fake follow-ups;
send the backfill asks, then set `outreach_sent` and a real `follow_up_due`
date after each ask.
On or after that due date, the outreach block treats `outreach_sent` targets
with `follow_up_due <= YYYY-MM-DD` as due follow-ups, so operators do not need a
manual pre-promotion step before generating the next follow-up draft.

Generate safe send-ready drafts from that block if you are not using the
Makefile wrapper:

```bash
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

Each draft includes a `validation-target-update.py --dry-run` command for audit
detail, plus safer Make commands for normal execution. Run
`make validation-apply-draft TARGET=... DATE=YYYY-MM-DD` first; it dry-runs the
generated update by default and rejects stale packs. Add `CONFIRM_SENT=1` only
after the message was actually sent and the anonymized target update is correct.
Confirmation wrappers require the exact value `1`; values such as
`CONFIRM_SENT=0`, `CONFIRM_TARGET=false`, or `CONFIRM_LOG=yes` fail closed.
The dry-run JSON echoes the exact dry-run, confirmed-send, status, and dashboard
commands for the selected target.
Generated tracker commands include `--require-current-status` guards so stale
commands fail instead of moving an already-advanced target backward.
The generated markdown starts with an execution checklist for the day's send,
dry-run, and tracker-update loop.
Drafts are source-aware: `warm_intro_needed` targets ask for an intro, while
`cold_outreach` targets use direct discovery copy.
To render only one draft while sending, add `--target-label`, for example:

```bash
python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --target-label target-dib-platform-004 \
  --require-date YYYY-MM-DD \
  --format markdown
```

If you only need pasteable outbound text for a specific anonymized target, use
the copy-only format:

```bash
python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --target-label target-dib-platform-004 \
  --require-date YYYY-MM-DD \
  --format send-text
```

The Makefile wrapper is shorter for the same operation:

```bash
make validation-next-draft DATE=YYYY-MM-DD
make validation-send-copy DATE=YYYY-MM-DD
make validation-send-copy-batch DATE=YYYY-MM-DD
make validation-send-copy-check DATE=YYYY-MM-DD
make validation-draft TARGET=target-dib-platform-004 DATE=YYYY-MM-DD
make validation-draft-copy TARGET=target-dib-platform-004 DATE=YYYY-MM-DD
```

Use `make validation-next-draft DATE=YYYY-MM-DD` first during normal
send-by-send execution. It selects the first pending draft whose dry-run tracker
command still verifies against the private target tracker and refuses a pack
generated for a different date. It also writes
`validation/private/today-next-draft.md` so the current
draft survives terminal interruptions. Use `make validation-draft TARGET=...`
only when you intentionally want a specific target label; it also rejects stale
packs unless `DATE=YYYY-MM-DD` matches the outreach pack date.
Use `make validation-send-copy DATE=YYYY-MM-DD` when you want a copy-only text
file for the verified next draft; it writes
`validation/private/today-send-copy.txt` with one subject line and the message
body, without target labels, tracker commands, alternate subject options, or
status metadata. Send from that file only after the dashboard
reports `send_copy_state: ready` and
`send_copy_matches_next_pending: true`.
Use `make validation-send-copy-batch DATE=YYYY-MM-DD` when you want one
copy-only `.txt` file per verified pending draft under
`validation/private/send-copy-YYYY-MM-DD/`. The generated manifest, checklist,
batch README, and neutral `COPY_ONLY_INDEX.md` are private tracker/operator
metadata; `SUBJECT_ORDER.md` is also private tracker/operator metadata for
file/subject order. Open the numbered `.txt` files and copy only their
subject/body contents into the outreach channel after running the matching
dry-run command for each target. Do not attach the `.txt` files, because
filenames and the directory are private operator workflow. Use them only when
the dashboard reports `send_copy_batch_state: ready` and
`send_copy_batch_matches_current_pack: true`, with
`send_copy_batch_readme_exists: true` and
`send_copy_batch_checklist_exists: true`, and
`send_copy_batch_copy_index_exists: true`, and
`send_copy_batch_subject_order_exists: true`. The batch match check also verifies
manifest operator notes, manifest outbound-boundary fields, copy-file SHA-256
values, the batch README body, the batch checklist body, and the neutral
copy-index body and subject-order body.
Use `make validation-send-copy-check DATE=YYYY-MM-DD` before using an existing
batch directory; it verifies neutral numbered filenames, one `Subject:` line
per file, copy-file SHA-256 matches, and no target labels or tracker metadata
in the outbound `.txt` files.
Use `make validation-draft-copy TARGET=... DATE=YYYY-MM-DD` only when you want
copy-only text for a selected target without writing
`validation/private/today-send-copy.txt`; it does not change the dashboard's
next-pending send-copy match.
When sending from the rendered draft, copy the generated subject/body as-is, or
personalize only in the outreach channel after pasting. Do not store recipient
names, private contact details, or new claims in repo files.

Before sending, dry-run the generated tracker update with:

```bash
make validation-apply-draft TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
```

Send the draft only after that dry-run is clean. Write the private tracker only
after the message was actually sent and the matching copy-only send artifact
exists:

```bash
make validation-apply-draft TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_SENT=1
```

Check send/update progress against the private target tracker:

```bash
make validation-status DATE=YYYY-MM-DD
```

The wrapper refreshes both `today-outreach-status.json` and
`today-outreach-status.md` and rejects packs that do not match the requested
outreach date. The JSON includes `next_pending_target_label`,
`next_pending_dry_run_apply_command`, and
`next_pending_confirmed_apply_command` so a restored terminal can recover the
next send/update boundary without parsing every draft. Manual equivalent:

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

Use `--verify-dry-run-commands` before sending to prove the generated tracker
commands still apply to the current private tracker. If it reports
`needs_attention`, regenerate the message pack or inspect the target status
before sending.

After sending an ask, update only the anonymized target tracker:

```bash
python3 scripts/validation-target-update.py \
  --target-label target-dib-platform-001 \
  --status outreach_sent \
  --require-current-status identified \
  --require-current-status intro_requested \
  --last-touch YYYY-MM-DD \
  --follow-up-due YYYY-MM-DD \
  --next-action "Send follow-up if no reply." \
  --dry-run
```

Prefer the exact dated tracker command in
`validation/private/today-message-pack.md`; the command above shows the field
shape only. The raw target-update CLI validates without writing by default and
blocks confirmed send-derived `intro_requested` / `outreach_sent` writes. Use
`make validation-apply-draft TARGET=... DATE=YYYY-MM-DD CONFIRM_SENT=1` only
after the real send and matching copy-only artifact verification; reserve
`--confirm-target` for non-send transitions such as booked calls,
disqualification, and completion.

When a buyer replies, classify the reply before touching the tracker:

- `book_call`: relevant workflow pain, call request, or routing to the workflow
  owner.
- `disqualify`: live testing, offensive validation, exploit capability, raw
  target review, production pushes, or clearly outside the ICP.
- `keep_pending`: noncommittal answer, deck request without workflow, or a
  later-follow-up ask.
- `manual_review`: private customer details, unclear scope, procurement/legal
  conditions, or security-review asks.

Never paste reply text, names, emails, phone numbers, URLs, hostnames, IPs,
screenshots, raw tickets, scanner rows, or customer artifacts into the tracker.

Use the no-write reply triage helper first, with only the sanitized classification:

```bash
make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call DATE=YYYY-MM-DD

python3 scripts/validation-reply-triage.py \
  --target-label target-dib-platform-001 \
  --classification book_call \
  --date YYYY-MM-DD \
  --format markdown
```

If the reply is `book_call`, clear the follow-up date and move the target
forward:

```bash
make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
```

Run the first command as a dry-run. Add `CONFIRM_TARGET=1` only after the
summary is correct.

If the reply is `disqualify`, disqualify the target without adding private
details:

```bash
make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
```

Run the first command as a dry-run. Add `CONFIRM_TARGET=1` only after confirming
the disqualification is correct and sanitized.

After a qualified call, prepare an intentionally incomplete private interview
starter from the booked anonymized target, then append only sanitized interview
notes:

```bash
make validation-prepare-interview TARGET=target-dib-platform-001 DATE=YYYY-MM-DD

python3 scripts/customer-validation-log-add.py \
  --interview-json validation/private/customer-validation-interview-next.json \
  --updated-at YYYY-MM-DD
```

Preferred wrapper:

```bash
make validation-log-interview DATE=YYYY-MM-DD
```

Add `CONFIRM_LOG=1` only after the sanitized interview record is reviewed.
The wrapper fails unless the interview `account_label`, segment, and persona
match an anonymized target currently in `call_booked`.
The direct `customer-validation-log-add.py` CLI also validates without writing
by default. Normal confirmed raw writes require `--require-target-status call_booked`
with matching account label, segment, and persona metadata, or the explicit
`--allow-untracked-interview` bypass.
The untracked bypass can capture out-of-band learning, but those interviews are
not enough to open the production build gate. The dashboard's
`target_backed_validation` gate counts only interviews whose `account_label`
matches an anonymized target in `call_booked` or `completed` with matching
segment/persona metadata.
The generated interview starter should fail validation until real sanitized
call outcomes are filled.

If the dashboard reports `example_seed_log: true` or the team update says
`Validation data mode: example seed`, treat all call and signal counts as
template data. Replace the initialized seed with real anonymized buyer
interviews before using any qualified-call, pilot-pull, or paid/sponsored count
as validation evidence. In that state, `gaps_to_verdicts` is calculated from
zero effective buyer evidence even if the seed contains example counts.
The shared team update prints gate-counted calls and signals first; raw example
seed counts are labeled as ignored placeholders.
For the first real private interview, dry-run:

```bash
make validation-log-interview DATE=YYYY-MM-DD REPLACE_EXAMPLE_SEED=1
```

After the sanitized record is reviewed, write with:

```bash
make validation-log-interview DATE=YYYY-MM-DD REPLACE_EXAMPLE_SEED=1 CONFIRM_LOG=1
```

The direct CLI form is also available:

```bash
python3 scripts/customer-validation-log-add.py \
  --account-label target-dib-platform-001 \
  --segment dib_platform_security \
  --persona director_product_security \
  --qualified true \
  --current-workflow "Scanner, SBOM review, ticket queue, manual briefing." \
  --recent-painful-event "Had to justify edge appliance remediation order." \
  --existing-tool scanner \
  --existing-tool ticketing \
  --status-quo-gap "No audit-ready packet for why this first." \
  --desired-output "Evidence packet with source basis and SOC review handoff." \
  --workflow-pain-theme evidence_packet_gap \
  --pain-score 5 \
  --urgency-score 4 \
  --status-quo-weakness-score 4 \
  --buyer-access-score 3 \
  --data-feasibility-score 4 \
  --pilot-pull-score 3 \
  --budget-signal could_sponsor_design_partner \
  --pilot-signal asked_for_scoped_pilot \
  --objection "Needs security review." \
  --next-step "Send pilot scope." \
  --updated-at YYYY-MM-DD \
  --require-target-status call_booked \
  --replace-example-seed
```

Review the summary first. Write only after confirming the record contains no
names, emails, phone numbers, URLs, private hostnames, IPs, raw customer
artifacts, or secrets.
Do not combine first-interview seed replacement with
`--allow-untracked-interview`; the replacement must be tied to a booked
anonymized target and the CLI rejects that bypass.

After the interview log is updated, mark the anonymized target complete:

```bash
make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
```

Run the first command as a dry-run. It fails unless the validation log contains
a sanitized interview whose `account_label` matches the anonymized target label.
Add `CONFIRM_TARGET=1` only after the sanitized interview log has been written
and the dry-run summary is correct.

Use one controlled `workflow_pain_theme` per qualified call so the dashboard can
prove whether pain is repeated rather than scattered:

- `evidence_packet_gap`
- `leadership_briefing_gap`
- `soc_ticket_handoff_gap`
- `asset_sbom_context_gap`
- `prioritization_conflict`
- `compliance_audit_pressure`
- `existing_tools_sufficient`
- `offensive_live_validation_request`
- `other`

## Script

Primary ask:

```text
I'm testing whether evidence-backed vulnerability prioritization is a real pain
for DIB/federal-adjacent security teams.

Not exploit tooling, not live validation, and not another scanner. The question
is: when KEV/BOD/CMMC/customer pressure hits, how do you prove what to harden
first and what SOC/platform handoff should follow?

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

Incumbent check:

```text
When your scanner, exposure-management platform, SIEM, SBOM, and ticketing tools
disagree or produce too much output, which artifact does leadership actually
trust for the final prioritization decision?
```

## Do Not Do

- Do not say "zero-day prediction."
- Do not lead with AI.
- Do not ask for raw customer data.
- Do not demo before understanding the current workflow.
- Do not build a requested integration unless they commit to a pilot path.

## Scorecard Command

```bash
make validation-dashboard DATE=YYYY-MM-DD
```

Use an explicit `DATE=YYYY-MM-DD` when recovering a specific outreach day; it
fails if the private message pack was generated for a different date.

When today's private message pack exists, the dashboard also reports
`outreach_execution`: pending send/update count, dry-run verified/failed/skipped
counts, and any `needs_attention` targets. It also names the next anonymized
target and the exact Make dry-run / `CONFIRM_SENT=1` commands for that draft.
If `validation/private/today-next-draft.md` already exists, the dashboard
reports `next_draft_state`, `next_draft_exists`, and whether
`next_draft_matches_next_pending` is true. Send from
`validation/private/today-send-copy.txt` only when `next_draft_state` is
`ready`, `next_draft_matches_next_pending` is true, `send_copy_state` is
`ready`, and `send_copy_matches_next_pending` is true. Ready means the draft
target, outreach date, verified status, tracker/audit draft body, and
copy-only text body match the current next pending target. Otherwise rerender
or refresh the stale artifact, or continue logging if the state is
`not_needed`.
Do not send a stale pack if `needs_attention` or `dry_run_failed_count` is
nonzero.

The `customer_validation.gaps_to_verdicts` section shows the exact remaining
qualified-call, high-pain, repeated-pain, pilot-pull, and paid/sponsored counts
before `pilot_pull_detected` or `build_next_slice` can be reached. Example
seed logs do not reduce those gaps.

For a shared team update, use the aggregate-only renderer:

```bash
make validation-team-update DATE=YYYY-MM-DD
make validation-team-update-save DATE=YYYY-MM-DD
make validation-weekly-review DATE=YYYY-MM-DD
```

Both omit target labels, commands, message bodies, and private validation paths.
The team update includes aggregate send-copy readiness and match state so the
team can see whether the outbound copy is ready without seeing the target or
text. When the validation log is still the example seed, the team update shows
zero gate-counted buyer evidence and labels raw seed counts as ignored.
The save target writes the aggregate handoff to
`validation/private/today-team-update.md` through a temporary file, preserving
the previous saved update if rendering fails.

Use `make validation-weekly-review DATE=YYYY-MM-DD` for the private Friday
review before pruning or rotating ignored artifacts. It writes
`validation/private/today-weekly-review.json` and
`validation/private/today-weekly-review.md`, reports outreach execution
readiness with the matching review date, target-backed build-gate status,
send-copy batch README/checklist/copy-index state, stale private artifacts, and
unsafe or outdated private send-copy warnings, and pruning candidates, and does
not delete files or mutate trackers/logs.

After reviewing that report, use `make validation-prune-private
DATE=YYYY-MM-DD` to dry-run pruning for generated ignored private artifacts
only. Add `CONFIRM_PRUNE=1` only after you have reviewed the plan and confirmed
the current dated send-copy batch is ready. The pruning helper protects private
trackers, logs, templates, and README files.

## Decision Rule

- `insufficient_data`: keep booking calls.
- `do_not_build_yet`: revise ICP/positioning.
- `keep_discovering`: keep calls and ask for pilot pull.
- `pilot_pull_detected`: convert to design partner.
- `build_next_slice`: build only what the committed pilot needs.

`build_next_slice` opens production scope only when the customer scorecard and
`target_backed_validation` both reach that verdict. `pilot_pull_detected` and
untracked interviews are conversion/learning signals, not production-build
permission.
