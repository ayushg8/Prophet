# Prophet CLI Safety Matrix

Last updated: 2026-05-10

This matrix defines the no-live-target guardrail for local buyer-pilot CLIs.
It covers command surfaces that accept mutable operator, customer, policy,
source, forecast, sandbox, evidence, or export input.
For operator examples and command sequencing, use `docs/CLI_REFERENCE.md`.

Run the guard suite with:

```bash
PYTHONPATH=.:cyber-side:world-side:world-side/scraper python3 -m unittest scripts.tests.test_cli_no_live_targets -v
```

## Covered Buyer-Pilot CLIs

| CLI | Guard exercised |
|---|---|
| `python3 -m assets.import_csv` | Rejects hostname-like customer asset rows before sanitized inventory output. |
| `python3 -m assets.inventory` | Rejects live-IP-like text in inventory JSON before seedset generation. |
| `python3 -m forecaster.cli` | Rejects Direction A candidate files with live-target keys before forecast generation. |
| `python3 -m scraper_side.cli` | Rejects live collection for unapproved hosts before any network request. |
| `python3 -m scraper_side.snapshot` | Rejects `--live` when the pilot policy is supplied. |
| `python3 -m predictor` | Rejects portfolio validation input containing live-target keys. |
| `python3 -m sandbox_runner` | Rejects non-fixture sandbox mode unless explicitly gated, and still has no packaged public container mode. |
| `python3 -m evidence.audit` | Rejects unsafe operator labels and keeps approval event outputs under ignored `outputs/runtime` paths. |
| `python3 -m evidence.bundle` | Rejects evidence output paths outside `evidence/outputs/runtime/`. |
| `python3 -m integrations.export` | Rejects handoff exports that the supplied policy does not allow. |
| `python3 -m policy.lint` | Rejects policies with `live_targets_allowed` enabled. |
| `python3 -m policy.retention` | Rejects retention runs under policies with `live_targets_allowed` enabled. |

## Covered Validation Sprint CLIs

Validation sprint CLIs operate on public examples or ignored
`validation/private/` files. They must not introduce names, emails, phone
numbers, URLs, private hostnames, IPs, raw customer artifacts, or claims that
outreach happened when it did not.

| CLI | Guard exercised |
|---|---|
| `python3 scripts/init-validation-sprint.py` | Initializes ignored private templates, uses sanitized dry-run examples, and supports `--refresh-readme` / `make validation-init REFRESH_README=1` to refresh only the ignored private README without overwriting private tracker/log templates. |
| `python3 scripts/validation-outreach-block.py` | Validates anonymized targets and rejects sensitive target text before generating a daily block. |
| `python3 scripts/validation-message-pack.py` | Builds source-aware safe drafts from a validated block, supports `--require-date` for date-mismatched packs, emits dry-run tracker commands only, and supports `--target-label ... --format send-text` for one copy-only outbound draft without target labels or tracker metadata. |
| `python3 scripts/validation-next-draft.py` | Renders one pending draft only after dry-run tracker verification; `--require-date` rejects date-mismatched packs; Markdown output warns that the tracker/audit draft must not be pasted to buyers; `--format send-text` emits one subject line plus the message body without target labels, tracker commands, alternate subject options, or status metadata; `--out` can write the current draft under ignored `validation/private/`. |
| `python3 scripts/validation-send-copy-batch.py` | Writes one neutral-named copy-only `.txt` file per verified pending draft after dry-run tracker verification; `--require-date` rejects date-mismatched packs; operators copy the file contents into outreach channels rather than attaching files; writes a neutral `COPY_ONLY_INDEX.md` that omits target labels and tracker commands plus a private `SUBJECT_ORDER.md` helper; the private manifest records copy-file SHA-256 values and machine-readable outbound-boundary fields showing only the numbered copy files are buyer-sendable while manifest/checklist/README/index/subject-order files are not. |
| `python3 scripts/validation-apply-draft-update.py` | Dry-runs the exact generated tracker update by default, supports `--require-date` for stale-pack rejection, requires a matching copy-only send artifact before confirmed writes, echoes dry-run/`CONFIRM_SENT=1`/status/dashboard commands, and writes only with `--confirm-sent`. |
| `python3 scripts/validation-outreach-status.py` | Compares a message pack with the private tracker, supports `--require-date` for date-mismatched pack rejection, exposes `next_pending_target_label` plus dry-run/`CONFIRM_SENT=1` commands, and flags stale generated commands as `needs_attention`. |
| `python3 scripts/validation-reply-triage.py` | No-write reply helper that accepts only a sanitized classification, never reply text; validates the target tracker, checks current target status, emits dry-run commands, and emits `CONFIRM_TARGET=1` commands only for `book_call` and `disqualify`. |
| `python3 scripts/validation-target-update.py` | Updates one anonymized target only after schema, date, sensitive-text, and `--require-current-status` checks pass; confirmed completed writes require a matching sanitized validation-log interview; dry-run send-derived `intro_requested` / `outreach_sent` updates are allowed for generated-command verification, but confirmed send-derived writes are blocked so post-send writes must use `scripts/validation-apply-draft-update.py` with matching copy-only artifact verification; raw CLI writes only with `--confirm-target` for non-send target transitions, and Make wrappers for booked, disqualified, and completed targets write only with `CONFIRM_TARGET=1`. |
| `python3 scripts/validation-prepare-interview.py` | Writes an intentionally incomplete private interview starter only from a booked anonymized target; the starter should fail validation until real sanitized call outcomes are filled. |
| `python3 scripts/customer-validation-log-add.py` | Validates sanitized interview notes without writing by default; normal confirmed writes require the interview `account_label`, segment, and persona to match a booked anonymized target unless `--allow-untracked-interview` is explicit; writes only with `--confirm-log`; can replace the initialized example seed only with explicit `--replace-example-seed`, `--require-target-status call_booked`, matching target metadata, and no `--allow-untracked-interview`; reports `gaps_to_verdicts`; and rejects sensitive contact or private infrastructure text. |
| `python3 scripts/customer-validation-scorecard.py` | Keeps the production build gate closed unless repeated workflow pain and pilot evidence thresholds are met, and reports `gaps_to_verdicts` for validation planning. |
| `python3 scripts/validation-targets-scorecard.py` | Validates anonymized outreach targets, duplicate labels, top-level and target date fields, due follow-ups with due dates, cleared follow-up dates for advanced statuses, and sensitive text. |
| `python3 scripts/validation-sprint-dashboard.py` | Combines validation scorecards, keeps `pilot_pull_detected` separate from `build_next_slice`, requires `target_backed_validation` to reach `build_next_slice` before opening production scope, counts only interviews tied to anonymized targets in `call_booked` or `completed` with matching segment/persona metadata for that gate, supports `--require-date` for date-mismatched private message packs, reports `next_draft_state`, `send_copy_state`, `send_copy_batch_state`, `send_copy_batch_readme_exists`, `send_copy_batch_checklist_exists`, `send_copy_batch_copy_index_exists`, and `send_copy_batch_subject_order_exists`, verifies the existing next draft's target/date/status/body through `next_draft_matches_next_pending`, verifies the copy-only send text through `send_copy_matches_next_pending`, verifies whole-block copy files, manifest fields, manifest operator notes, manifest outbound-boundary fields, copy-file SHA-256 values, batch README body, batch checklist body, neutral copy-index body, and subject-order body through `send_copy_batch_matches_current_pack` before treating the batch path as usable, points operators to the one-draft outreach path plus exact Make dry-run/`CONFIRM_SENT=1` commands when a private message pack exists, and supports `--format team` for sanitized aggregate-only shared updates that omit target labels, commands, message bodies, and private validation paths while showing gate-counted buyer evidence before any raw example-seed counts. |
| `python3 scripts/validation-next-action.py` | Renders a private ignored `NEXT_ACTION.md` handoff from the current dashboard; `--date` rejects stale packs, `--out` writes the ignored handoff, and the helper does not send outreach, prune artifacts, confirm writes, or mutate trackers/logs. |
| `python3 scripts/validation-weekly-review.py` | Builds a read-only private weekly review, validates the private tracker/log, reports message-pack age, date-guarded outreach execution readiness, send-copy batch README/checklist/copy-index state, ignored private artifact counts, stale private artifacts, and pruning candidates, and does not delete files or mutate trackers/logs. |
| `python3 scripts/validation-prune-private.py` | Builds a dry-run pruning plan from the weekly review for generated ignored private validation artifacts only, protects validation trackers/logs/templates/README files, requires matching `--review-date`, and removes eligible artifacts only with `--confirm-prune`; the Make wrapper writes only with `CONFIRM_PRUNE=1`. |

The `make validation-resume DATE=YYYY-MM-DD` wrapper is a no-write recovery aid:
it runs the dashboard with the date guard, prints the copy-only send text only
when `send_copy_state` is `ready` and `send_copy_matches_next_pending` is true,
and prints the already-rendered
`validation/private/today-next-draft.md` only when it still matches the current
next pending target/date/status/body. `make goal-resume DATE=YYYY-MM-DD` is the same no-write
path with a name that matches a restored `/goal` session.
`make validation-reply-triage TARGET=... REPLY=book_call DATE=YYYY-MM-DD` is a
no-write wrapper over `scripts/validation-reply-triage.py`; it accepts only the
sanitized reply classification and emits the safe dry-run / reviewed
`CONFIRM_TARGET=1` commands.
`make validation-send-copy DATE=YYYY-MM-DD` writes
`validation/private/today-send-copy.txt` for the same verified next draft,
as one subject line plus the message body, without target labels, tracker
commands, alternate subject options, or status metadata.
`make validation-send-copy-batch DATE=YYYY-MM-DD` writes one neutral-named
copy-only `.txt` file per verified pending draft under
`validation/private/send-copy-YYYY-MM-DD/`;
open those `.txt` files and copy only their contents when the dashboard reports
`send_copy_batch_state` is ready and
`send_copy_batch_matches_current_pack`, `send_copy_batch_readme_exists`, and
`send_copy_batch_checklist_exists`, plus `send_copy_batch_copy_index_exists`
and `send_copy_batch_subject_order_exists`, are true. Do not attach the files; the match
check also covers copy-file SHA-256 values, manifest operator notes, manifest
outbound-boundary fields, the batch README body, the batch checklist body, and
the neutral copy-index body and subject-order body.
`make validation-team-update DATE=YYYY-MM-DD` is the shared-status wrapper for
the dashboard's aggregate-only team renderer, including aggregate send-copy readiness
and match state without target labels, commands, paths, or message bodies.
`make validation-team-update-save DATE=YYYY-MM-DD` writes the same
aggregate-only update to the ignored private validation workspace through a
temporary file and preserves the previous saved update if rendering fails.
`make validation-next-action-save DATE=YYYY-MM-DD` regenerates the ignored
private `NEXT_ACTION.md` handoff from the current dashboard and writes only
that handoff; it does not send, delete, or mutate trackers/logs.
`make validation-weekly-review DATE=YYYY-MM-DD` writes read-only private weekly
review JSON/Markdown under `validation/private/` for pruning review; it does
not send, delete, or confirm-update anything.
`make validation-prune-private DATE=YYYY-MM-DD` dry-runs the generated-artifact
prune plan and writes only with `CONFIRM_PRUNE=1` after review.
Make confirmation wrappers fail closed unless the value is exactly `1`:
`CONFIRM_SENT=1`, `CONFIRM_TARGET=1`, `CONFIRM_LOG=1`, `CONFIRM_PRUNE=1`, and
`REFRESH_README=1`.

## Related Release Utilities

`scripts/check-release-safety.py` is covered by
`scripts/tests/test_check_release_safety.py`, including unsafe IP, secret,
runtime artifact, source-catalog allowlist, and console live-action policy-gate
checks.

`scripts/diff-pilot-demo-fixtures.py` and
`scripts/verify-pilot-demo-hashes.py` read deterministic fixture/hash inputs and
do not accept target-control, live host, credential, or network collection
parameters.

Validation sprint safety docs are checked by
`scripts/tests/test_cli_safety_matrix_docs.py`. Behavior is covered by the
`scripts/tests/test_validation_*.py`, `test_customer_validation_*.py`, and
`test_make_validation_targets.py` suites.
