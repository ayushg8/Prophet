# Validation Sprint Checklist

Date: 2026-05-05

This is the daily operating checklist for proving or disproving Prophet demand.
Do not add production platform scope while this checklist is red.

## Setup

- [ ] Initialize the private local workspace:

  ```bash
	  python3 scripts/init-validation-sprint.py
	  ```

  Add `--date YYYY-MM-DD`, or use `make validation-init DATE=YYYY-MM-DD`, only
  when recovering or replaying a prior outreach day.
  Add `--refresh-readme` only when you need to update the ignored private
  README without overwriting private tracker/log files. The Make equivalent is
  `make validation-init DATE=YYYY-MM-DD REFRESH_README=1`.
  After a terminal restore, machine sleep, or crash, check `date +%F` and pass
  `DATE=YYYY-MM-DD` explicitly if the shell date is not the outreach date.
  Use `make goal-resume DATE=YYYY-MM-DD` after a lost `/goal` session as a
  no-write way to print the dashboard and current valid next draft without
  writing tracker state.

- [ ] Do not commit anything under `validation/private/`.
- [ ] Prepare the 10-minute demo around generated evidence, not platform
  architecture.
- [ ] Keep `docs/OUTREACH_PLAYBOOK.md` and `docs/CUSTOMER_DISCOVERY_GUIDE.md`
  open during outreach and calls.
- [ ] Generate today's outreach block, message pack, and status reports from
  the private tracker:

  ```bash
  make validation-pack DATE=YYYY-MM-DD
  ```

  Manual equivalent for the first step:

  ```bash
  python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format json \
    --out validation/private/today-outreach-block.json
  python3 scripts/validation-outreach-block.py --date YYYY-MM-DD --format markdown \
    --out validation/private/today-outreach-block.md
  ```
- [ ] If no follow-ups are due, use the outreach block's
  `Follow-Up Gap Backfill` section as extra first-touch asks. Do not invent
  fake follow-ups.
- [ ] Generate safe message drafts from today's outreach block if you are not
  using the Makefile wrapper:

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

- [ ] Before sending each message, run the draft's safe Make dry-run command.
  Write only after the dry-run is correct and the send is confirmed.
- [ ] Prefer the guarded wrapper for sent drafts:
  `make validation-apply-draft TARGET=target-dib-platform-001 DATE=YYYY-MM-DD`;
  add `CONFIRM_SENT=1` only after the message was actually sent.
- [ ] Treat confirmation variables as exact guards: only
  `CONFIRM_SENT=1`, `CONFIRM_TARGET=1`, or `CONFIRM_LOG=1` can write; `0`,
  `false`, or any other value must fail closed.
- [ ] Confirm generated tracker commands include `--require-current-status`
  guards before applying any write.
- [ ] Use the generated source-aware copy as intended:
  `warm_intro_needed` targets ask for an intro; `cold_outreach` targets use
  direct discovery copy.
- [ ] Render the next verified pending draft with
  `make validation-next-draft DATE=YYYY-MM-DD` before picking target labels
  manually; it also writes
  `validation/private/today-next-draft.md`.
- [ ] Render copy-only send text with
  `make validation-send-copy DATE=YYYY-MM-DD` when sending from a clean artifact;
  it writes `validation/private/today-send-copy.txt` with one subject line and
  the message body, without target labels, tracker commands, alternate subject
  options, or status metadata.
- [ ] If sending the whole block in one sitting, render one copy-only file per
  verified pending draft with
  `make validation-send-copy-batch DATE=YYYY-MM-DD`. It writes under
  `validation/private/send-copy-YYYY-MM-DD/`; open the numbered `.txt` files
  and copy only their contents into the outreach channel. Do not attach the
  `.txt` files, and do not send the private manifest, checklist, copy index,
  subject-order helper, or batch README. Use the
  batch only after the dashboard reports `send_copy_batch_state: ready` and
  `send_copy_batch_matches_current_pack: true` with
  `send_copy_batch_readme_exists: true` and
  `send_copy_batch_checklist_exists: true` and
  `send_copy_batch_copy_index_exists: true` and
  `send_copy_batch_subject_order_exists: true`. The match check also verifies the
  manifest operator notes, manifest outbound-boundary fields, copy-file
  SHA-256 values, batch README body, batch checklist body, and neutral
  copy-index body and subject-order body.
- [ ] Before using an existing send-copy batch, run
  `make validation-send-copy-check DATE=YYYY-MM-DD`. It verifies neutral
  numbered filenames, one `Subject:` line per file, copy-file SHA-256 matches,
  and no target labels or tracker metadata in the outbound `.txt` files.
- [ ] Send from `validation/private/today-send-copy.txt` only when the dashboard
  reports `next_draft_state: ready`, `next_draft_matches_next_pending: true`,
  `send_copy_state: ready`, and `send_copy_matches_next_pending: true`.
- [ ] Copy the generated subject/body as-is, or personalize only in the
  outreach channel after pasting. Do not store recipient names, private contact
  details, or new claims in repo files.
- [ ] Render individual drafts with `--target-label` and `--require-date` when
  sending one ask at a time, or use
  `make validation-draft TARGET=target-dib-platform-004 DATE=YYYY-MM-DD`.
- [ ] Render selected-target copy-only subject/body text with
  `make validation-draft-copy TARGET=target-dib-platform-004 DATE=YYYY-MM-DD`
  only when you do not want to write
  `validation/private/today-send-copy.txt`.
- [ ] Check progress against the target tracker:

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
- [ ] Stop and inspect the tracker if the status report shows
  `needs_attention`; that means at least one generated update command is stale
  or no longer applies.
- [ ] After each ask, update the anonymized target status and follow-up date:

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
  Use `make validation-pack DATE=YYYY-MM-DD` when regenerating a prior
  outreach day.
  Use the exact dated tracker command generated in
  `validation/private/today-message-pack.md` when available.
  The raw target-update CLI validates without writing by default and blocks
  confirmed send-derived `intro_requested` / `outreach_sent` writes. Use
  `make validation-apply-draft TARGET=... DATE=YYYY-MM-DD CONFIRM_SENT=1`
  only after the real send and matching copy-only artifact verification.
  Reserve `--confirm-target` for non-send transitions such as booked calls,
  disqualification, and completion.
- [ ] If a buyer books a call, move the target to `call_booked` and clear the
	  follow-up date:

  ```bash
  make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
  make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
  ```
  Run the first command as a dry-run. Add `CONFIRM_TARGET=1` only after the
  summary is correct.
- [ ] If a buyer asks for live/offensive capability or is outside the ICP, move
  the target to `disqualified` and keep private details out of the tracker.

  ```bash
  make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
  make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
  ```
  Run the first command as a dry-run. Add `CONFIRM_TARGET=1` only after the
  disqualification is confirmed and sanitized.
- [ ] After each call, prepare an intentionally incomplete private interview
  starter from the booked anonymized target, then append sanitized notes to the
  private validation log:

  ```bash
  make validation-prepare-interview TARGET=target-dib-platform-001 DATE=YYYY-MM-DD

	  python3 scripts/customer-validation-log-add.py \
	    --interview-json validation/private/customer-validation-interview-next.json \
	    --updated-at YYYY-MM-DD
	  ```
  Prefer the wrapper:

  ```bash
  make validation-log-interview DATE=YYYY-MM-DD
  ```

  Add `CONFIRM_LOG=1` only after the sanitized record is reviewed.
  The wrapper fails unless the interview `account_label`, segment, and persona
  match an anonymized target currently in `call_booked`.
  The direct CLI validates without writing by default. Confirmed raw writes
  require `--require-target-status call_booked` with matching account label,
  segment, and persona metadata, or the explicit `--allow-untracked-interview`
  bypass.
  The untracked bypass can preserve out-of-band learning, but the dashboard's
  `target_backed_validation` gate counts only interviews whose `account_label`
  matches an anonymized target in `call_booked` or `completed` with matching
  segment/persona metadata.
  The generated starter should fail validation until real sanitized call
  outcomes are filled.
- [ ] If the dashboard reports `example_seed_log: true` or the team update says
  `Validation data mode: example seed`, treat all call and signal counts as
  template data. Replace the initialized seed with real anonymized buyer
  interviews before using any qualified-call, pilot-pull, or paid/sponsored
  count as validation evidence. Example seed logs do not reduce
  `gaps_to_verdicts`.
- [ ] On the first real private interview, dry-run
  `make validation-log-interview DATE=YYYY-MM-DD REPLACE_EXAMPLE_SEED=1`, then
  write with `CONFIRM_LOG=1` only after the sanitized record is reviewed. This
  removes the public example interview and clears `example_seed_log`.
  Do not use `--allow-untracked-interview` for seed replacement; the first real
  interview must match a booked anonymized target.
- [ ] After the interview log is updated, mark the anonymized target
  `completed` with `--clear-follow-up-due` and no private details:

  ```bash
  make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
  make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD CONFIRM_TARGET=1
  ```
  Run the first command as a dry-run. It fails unless the validation log
  contains a sanitized interview whose `account_label` matches the anonymized
  target label. Add `CONFIRM_TARGET=1` only after the sanitized interview log
  has been written and the dry-run summary is correct.
- [ ] Use the direct CLI form only when faster than editing the JSON template:

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
	    --next-step "Send pilot scope." \
	    --updated-at YYYY-MM-DD \
	    --require-target-status call_booked
	  ```
- [ ] Write the interview log only after confirming the record contains no
  names, emails, phone numbers, URLs, private hostnames, IPs, raw customer
  artifacts, or secrets.

## Daily Loop

Every weekday:

- [ ] Send 5 targeted warm/cold asks.
- [ ] Send 2 follow-ups.
- [ ] If fewer than 2 follow-ups are due, send the listed follow-up backfill
  asks and create real follow-up dates.
- [ ] Ask every warm contact for one more specific intro.
- [ ] Book or run at least one qualified conversation when possible.
- [ ] Log each conversation in the private validation log.
- [ ] Run the dashboard and check `outreach_execution` for pending verified
  sends, stale commands, `next_draft_state`, `send_copy_state`, and nonzero
  `dry_run_failed_count`.

```bash
make validation-dashboard DATE=YYYY-MM-DD
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

- [ ] Run `make validation-dashboard DATE=YYYY-MM-DD` and copy only the
  aggregate verdict, counts, and next action into the team update.
- [ ] Prefer the aggregate-only team update renderer for shared status:
  `make validation-team-update DATE=YYYY-MM-DD`. It omits target labels,
  commands, message bodies, and private validation paths, while including
  aggregate send-copy readiness and match state.
- [ ] Use `make validation-team-update-save DATE=YYYY-MM-DD` when you need the
  same aggregate update saved locally at `validation/private/today-team-update.md`.
  It writes through a temporary file and preserves the previous saved update if
  rendering fails.
- [ ] Run `make validation-weekly-review DATE=YYYY-MM-DD` to write a read-only
  private review before pruning. It reports the validation gate, message-pack
  age, date-guarded outreach execution readiness, send-copy batch
  README/checklist/copy-index state, stale private artifacts, unsafe or
  outdated private send-copy warnings, and pruning candidates without deleting
  files or mutating trackers/logs.
- [ ] Use the matching outreach date so stale private packs fail closed.
- [ ] Run `make validation-status DATE=YYYY-MM-DD` if a private message pack
  exists, and use only aggregate status counts in shared updates.
- [ ] Do not mark messages sent, calls booked, interviews completed, pilot
  signals, or paid/sponsored paths unless the real external action happened and
  the sanitized private state is known.
- [ ] Dry-run every pruning or status-update command first. Add
  `CONFIRM_SENT=1`, `CONFIRM_TARGET=1`, or `CONFIRM_LOG=1` only for a real
  send, reply, call, or reviewed sanitized log entry.
- [ ] Confirm `validation/private/` remains ignored before deleting, rotating,
  or regenerating private generated packs.
- [ ] Count qualified calls.
- [ ] Count high-pain calls.
- [ ] Count repeated workflow pains.
- [ ] Count stakeholder introductions.
- [ ] Count safe artifact offers.
- [ ] Count design-partner pilot discussions.
- [ ] Count paid/sponsored pilot signals.
- [ ] Prune stale private targets: disqualify targets that asked for
  live/offensive capability, advance sent targets that have real replies, and
  leave no target in a status that no longer matches the last outreach event.
- [ ] Delete or rotate stale ignored private message packs after the week is
  logged; regenerate a fresh pack before the next outreach block.
- [ ] Review `validation/private/customer-validation-interview-next.json` if it
  exists. Log it only after a real call and sanitized review; delete or rotate
  it only when it is known stale.
- [ ] Review `docs/PROPHET_TODO.md` and `docs/PROPHET_MASTER_TODO.md`; mark an
  item complete only when the referenced code, docs, tests, and checks exist.
- [ ] Leave the production build gate closed unless the private dashboard
  returns `build_next_slice`.
- [ ] Decide: continue, narrow, pivot, or stop.

## No-Build Gate

Do not build more production infrastructure unless the scorecard returns:

- `build_next_slice`

If the scorecard returns `pilot_pull_detected`, convert interested accounts into
a design-partner pilot before building the next production slice.
Even when the scorecard returns `build_next_slice`, the dashboard opens
`allowed_to_build_next_slice` only if `target_backed_validation` also reaches
`build_next_slice`.

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
