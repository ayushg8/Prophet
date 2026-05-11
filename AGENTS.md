# Agent Operating Manual - Prophet

> If you are an AI agent joining this repo, read this file first. It is the
> current orientation for the Prophet buyer-pilot and validation work.

## Current Product Direction

Prophet is a policy-bound evidence workflow for defensive exposure
prioritization. It helps a security team answer:

1. What exposure class should we review or harden first?
2. Why now?
3. What approved asset/SBOM and public vulnerability context supports that
   decision?
4. What evidence, audit trail, and SOC/ticket review artifact can we hand to
   stakeholders?

Prophet is not an exploit platform, live attack prediction product, live target
validation tool, autonomous remediation system, or raw OSINT warehouse.

The current CEO/product finish goal is tracked in:

- `docs/CODEX_CEO_FINISH_BRIEF.md`
- `docs/PROPHET_COMPLETION_AUDIT.md`
- `docs/PROPHET_TODO.md`
- `docs/PROPHET_FINISH_CHANGE_INVENTORY.md`

If a `/goal` session is lost, restart from the "Recovered Goal Source / Goal
Setter" section in `docs/PROPHET_COMPLETION_AUDIT.md`, then run
`make goal-resume DATE=YYYY-MM-DD`.

## Build Gate

The production build gate is closed until real buyer validation reaches
`build_next_slice`.

Do not add production platform scope while customer validation is
`insufficient_data`. In that state, the correct work is:

- Operate the buyer validation sprint.
- Improve safe pilot packaging only when it supports validation.
- Keep evidence, handoff, audit, and outreach tooling policy-bound.
- Make the next customer conversation easier to run and log safely.

`pilot_pull_detected` means convert design partners first. It is not permission
to build the next production slice.

## First Commands

From the repo root:

```bash
git status --short --branch --untracked-files=all
make validation-dashboard
make validation-team-update
make validation-team-update-save
make validation-next-action-save
make validation-weekly-review
make validation-prune-private
make validation-status
make validation-resume
make goal-resume
make validation-next-draft
make validation-send-copy
make validation-send-copy-batch
make validation-draft-copy TARGET=target-dib-platform-004
```

`make validation-status` prints the Markdown report for humans and refreshes
`validation/private/today-outreach-status.json` for machine-readable checks.
`make validation-team-update-save DATE=YYYY-MM-DD` writes the aggregate-only
local team handoff to `validation/private/today-team-update.md` without target
labels, commands, message bodies, or private validation paths.
`make validation-next-action-save DATE=YYYY-MM-DD` regenerates the ignored
private `validation/private/NEXT_ACTION.md` handoff from the current dashboard
so restored sessions do not carry stale PR/head or send-boundary state.
`make validation-weekly-review DATE=YYYY-MM-DD` writes a read-only private
weekly report for stale artifact/pruning review without deleting files or
mutating trackers/logs. `make validation-prune-private DATE=YYYY-MM-DD` reads
that weekly report and prints a dry-run cleanup plan for generated ignored private artifacts.
It protects trackers/logs/templates/README files and removes files only when
`CONFIRM_PRUNE=1` is supplied after operator review.

For a recovered outreach day, include the date:

```bash
make validation-pack DATE=YYYY-MM-DD
make validation-dashboard DATE=YYYY-MM-DD
make validation-team-update DATE=YYYY-MM-DD
make validation-team-update-save DATE=YYYY-MM-DD
make validation-next-action-save DATE=YYYY-MM-DD
make validation-weekly-review DATE=YYYY-MM-DD
make validation-prune-private DATE=YYYY-MM-DD
make validation-status DATE=YYYY-MM-DD
make validation-resume DATE=YYYY-MM-DD
make goal-resume DATE=YYYY-MM-DD
make validation-next-draft DATE=YYYY-MM-DD
make validation-send-copy DATE=YYYY-MM-DD
make validation-send-copy-batch DATE=YYYY-MM-DD
make validation-draft-copy TARGET=target-dib-platform-004 DATE=YYYY-MM-DD
```

Run the dashboard first after a crash or restored terminal. Treat
`validation/private/today-next-draft.md` as the tracker/audit artifact, then
send from `validation/private/today-send-copy.txt` only when the dashboard
reports `outreach_execution.next_draft_state: ready`, with both
`outreach_execution.next_draft_exists: true` and
`outreach_execution.next_draft_matches_next_pending: true`, and also reports
`outreach_execution.send_copy_state: ready` and
`outreach_execution.send_copy_matches_next_pending: true`. A ready draft and
send-copy file must match the current next pending target, outreach date,
verified draft status, and copy-only text body.
`make validation-resume DATE=YYYY-MM-DD` performs that dashboard check and
prints the copy-only send text inside begin/end markers, then prints the
existing tracker/audit draft below a do-not-send divider only when it still
matches the current next pending target/date/status/body.
`make goal-resume DATE=YYYY-MM-DD` is the same no-write recovery path with a
name that matches lost `/goal` sessions.
When sending a whole outreach block, use `make validation-send-copy-batch
DATE=YYYY-MM-DD` only after the dashboard reports
`outreach_execution.send_copy_batch_state: ready` and
`outreach_execution.send_copy_batch_matches_current_pack: true`, with
`outreach_execution.send_copy_batch_readme_exists: true` and
`outreach_execution.send_copy_batch_checklist_exists: true` and
`outreach_execution.send_copy_batch_copy_index_exists: true` and
`outreach_execution.send_copy_batch_subject_order_exists: true`; the match check
covers the numbered copy files, manifest fields, manifest operator notes,
manifest outbound-boundary fields, copy-file SHA-256 values, batch README body,
batch checklist body, neutral copy-index body, and subject-order body. Open the
generated `.txt` files and copy only their contents into the outreach channel.
Do not attach the files, and do not send the private manifest, checklist, copy index,
subject-order helper, or batch README.

The next operational loop is:

1. Run `make validation-dashboard DATE=YYYY-MM-DD`.
2. If `next_draft_state` is not `ready` or
   `next_draft_matches_next_pending` is false, run `make
   validation-next-draft DATE=YYYY-MM-DD`; otherwise keep
   `validation/private/today-next-draft.md`.
3. Run `make validation-apply-draft TARGET=<target-label> DATE=YYYY-MM-DD` to
   dry-run the generated tracker update.
4. Run `make validation-send-copy DATE=YYYY-MM-DD` to write a
   copy-only send artifact without target labels or tracker commands.
5. Use `make validation-draft-copy TARGET=<target-label> DATE=YYYY-MM-DD` only
   when you need copy-only subject/body text for a selected target without
   writing `validation/private/today-send-copy.txt`.
6. If sending the whole block, run `make validation-send-copy-batch
   DATE=YYYY-MM-DD` and copy only the generated `.txt` file contents after the
   dashboard reports the batch state is ready and matches the current pack. Do
   not attach the files.
7. Send from `validation/private/today-send-copy.txt` only after that dry-run
   is clean and the dashboard reports `send_copy_state: ready` plus
   `send_copy_matches_next_pending: true`.
8. Add `CONFIRM_SENT=1` only after the sent message and anonymized update are
   correct.
9. Rerun `make validation-status DATE=YYYY-MM-DD` and
   `make validation-dashboard DATE=YYYY-MM-DD`.

Do not invent sent messages, buyer replies, calls, or pilot signals.

## Repo Map

```text
Prophet/
├── AGENTS.md                         current agent orientation
├── README.md                         buyer-pilot overview and commands
├── Makefile                          safe local operator wrappers
├── CHANGELOG.md                      unreleased buyer-pilot package notes
├── assets/                           customer-safe asset/SBOM fixtures
├── cyber-side/                       defensive portfolio and fixture contracts
├── docs/                             pilot, validation, safety, and product docs
├── evidence/                         evidence bundle and audit CLIs
├── integrations/                     review-template handoff exports
├── intel/                            checked-in public seed data
├── policy/                           local pilot policies and validators
├── prophet-console/                  React console and localhost control server
├── research/                         historical research artifacts
├── sandbox_runner/                   deterministic local sandbox simulation
├── scripts/                          smoke, validation, and release checks
├── validation/private/               ignored private validation workspace
└── world-side/                       forecaster and sanitized OSINT pipeline
```

Historical hackathon docs such as `HACKATHON.md` and
`PROPHET_TECHNICAL_WRITEUP.md` are useful background, not the current product
positioning source of truth.

## Safety Boundary

Default behavior must stay:

- Fixture-backed.
- Localhost or approved sandbox only.
- Policy-bound.
- Review-template-only for integrations.
- Customer-owned metadata only.
- Safe for buyer evaluation.

Never add or route product flows through:

- Live target validation.
- Payload generation.
- Arbitrary target input.
- Raw scraper text in evidence.
- Credentials, secrets, private hostnames, or live IPs.
- Autonomous production push actions.
- Archived lab exploit material.

Scraping and live collection remain outside the default buyer pilot. Follow the
policy and source-catalog checks before touching any collection workflow.

## Validation Sprint

The private validation workspace is under `validation/private/` and is ignored
by git. It may contain anonymized private target trackers, message packs,
status reports, and interview templates.

Use:

```bash
make validation-pack
make validation-next-draft
make validation-status
make validation-dashboard
make validation-team-update-save
make validation-weekly-review
make validation-prune-private
```

Only export aggregate counts or sanitized examples from private validation.
Never commit real buyer names, emails, phone numbers, URLs, private hostnames,
IPs, raw notes, screenshots, or customer artifacts.

## Checks Before Handoff

Run the narrow checks for your change:

```bash
git diff --check
python3 -m unittest discover -s scripts/tests -v
PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff
make release-safety-staged
```

If you add untracked files, explicitly scan them too:

```bash
git ls-files --others --exclude-standard -z |
  xargs -0 env PYTHONPATH=.:cyber-side:world-side \
  python3 scripts/check-release-safety.py
```

For pilot or console changes, also run the relevant smoke or acceptance command:

```bash
./scripts/run-pilot-demo-smoke.sh
cd prophet-console && npm run acceptance
```

## Code Discipline

- Prefer existing local patterns over new abstractions.
- Keep edits scoped to the current validation or safe pilot goal.
- Do not rewrite large subsystems without explicit approval.
- Do not add deploy, tag, push, or staging automation unless the user asks.
- Do not commit `node_modules/`, build outputs, runtime outputs, private
  validation files, secrets, or generated private artifacts.
- Do not use destructive git operations such as `git reset --hard`, force push,
  or branch deletion without explicit instruction.

## Working With Ayush

- Small steps, verify, then proceed.
- Ask before architectural decisions.
- Update canonical files in place instead of creating parallel docs.
- In multi-agent work, stay inside the files you own and surface conflicts
  before merging.
- If the goal feels "done," audit actual buyer validation first. If the
  dashboard still says `insufficient_data`, the product is not done.
