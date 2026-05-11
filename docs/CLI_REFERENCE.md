# Prophet CLI Reference

Last updated: 2026-05-11

Use this reference for the safe local pilot and validation sprint command
surface. It complements `docs/CLI_SAFETY_MATRIX.md`, which explains the
guardrails each CLI enforces.

## Safety Boundary

- Default to fixtures, localhost, and ignored runtime outputs.
- Write generated artifacts under `*/outputs/runtime/` or `validation/private/`.
- Do not pass raw scraper output, credentials, secrets, payloads, private
  hostnames, live IPs, target URLs, or raw customer notes to any command.
- Treat `--live` scraper options as outside the default buyer pilot. They
  require explicit source selection, approved public HTTPS collection boundary,
  and the isolated scraper environment.
- Handoff exports are review templates only. They do not push to SIEM,
  ticketing, remediation, or production systems.

## Environment

Most Python commands are stdlib-only but need repo modules on `PYTHONPATH`.
Use the narrowest path that matches the command:

```bash
PYTHONPATH=. python3 -m assets.inventory --help
PYTHONPATH=world-side:world-side/scraper:. python3 -m forecaster.cli --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.bundle --help
```

The root `Makefile` wraps the most common safe operator checks:

```bash
make help
make check-local-env
make pilot-ready-check DATE=2026-05-11
make pilot-ready-check-full DATE=2026-05-11
make python-tests
make worktree-smoke
make pilot-smoke
make console-demo
make validation-init DATE=2026-05-11 REFRESH_README=1
make validation-pack DATE=2026-05-11
make validation-next-draft DATE=2026-05-11
make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11
make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call DATE=2026-05-11
make validation-status DATE=2026-05-11
make validation-dashboard DATE=2026-05-11
make validation-resume DATE=2026-05-11
make release-hygiene
make secrets-archaeology
make release-safety
```

`make worktree-smoke` clones HEAD to a temporary directory, overlays current
non-ignored dirty files, excludes ignored private validation files, and runs
the safe root pilot smoke without staging, committing, pushing, or tagging.

`make python-tests` runs the scripts, cyber-side, world-side, assets, sandbox
runner, policy, evidence, and integration Python unit suites. Use it before a
pilot commit or PR review when you need the full Python verification set.

`make release-hygiene` is the read-only pre-commit hygiene wrapper. It runs
tracked and untracked whitespace checks, release-safety scans for tracked diffs
and untracked files, tracked path policy-hash coverage, staged-path safety,
current-worktree secret scanning, pilot policy lint, default-output
URL/provenance safety, and local Markdown link checking.

`make secrets-archaeology` runs the full current-worktree plus git-history secret scan.
It reports only paths and commit IDs, not matched values. Treat any
finding as a public-release blocker until the underlying secret or false
positive is reviewed.

`make console-demo` starts the localhost-only control API and evaluator UI in
one terminal. On a fresh checkout, run `cd prophet-console && npm ci` first. If
default ports are already occupied, use alternate localhost ports:

```bash
PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 make console-demo
```

With the local demo already running, `make console-live-check` verifies the UI,
readiness API, evidence demo-bundle endpoint, integration demo-export endpoint,
and runtime audit log. It writes only ignored runtime outputs.

If a qualified reviewer asks for redacted visual handoff material, capture
ignored desktop/mobile console screenshots after the fixture smoke:

```bash
cd prophet-console
npm run capture:screenshots
```

Review `evidence/outputs/runtime/console-screenshots/manifest.json` before
sharing. `make console-screenshot-check` verifies the manifest hashes, PNG
dimensions, ignored runtime paths, and sharing boundary. Do not commit
generated PNGs.

`make validation-dashboard` reports both the customer scorecard and
`target_backed_validation`. Production build scope opens only when both reach
`build_next_slice`; interviews logged through the explicit
`--allow-untracked-interview` bypass remain useful learning but do not satisfy
the target-backed gate. Target-backed interviews must also match the target
tracker's segment/persona metadata.

## Pilot Smoke

Check local prerequisites:

```bash
./scripts/check-local-env.sh
./scripts/check-local-env.sh --strict-console
```

Run the default evaluator path:

```bash
./scripts/run-pilot-demo-smoke.sh
```

Useful options:

```bash
./scripts/run-pilot-demo-smoke.sh --dry-run
./scripts/run-pilot-demo-smoke.sh --sector financial-workflow
./scripts/run-pilot-demo-smoke.sh --clean-runtime --yes
```

`--clean-runtime` only touches known ignored `outputs/runtime` directories after
checking the paths are ignored by git.

## Asset And SBOM Metadata

Import an approved CSV into an asset inventory and optional seedset:

```bash
PYTHONPATH=. python3 -m assets.import_csv \
  --csv assets/fixtures/dib-edge-appliance-inventory.csv \
  --inventory-id customer-safe-import \
  --scope "Customer-owned product-family metadata; no live targets named." \
  --generated-at 2026-05-05T08:00:00Z \
  --fixture \
  --out assets/outputs/runtime/customer-safe-inventory.json \
  --report-out assets/outputs/runtime/customer-safe-import-report.json \
  --seedset-out assets/outputs/runtime/customer-safe-seedset.json \
  --seedset-run-id customer-safe-seedset
```

Validate an inventory and emit a safe OSINT seedset:

```bash
PYTHONPATH=. python3 -m assets.inventory \
  --inventory assets/fixtures/dib-edge-appliance-inventory.json \
  --generated-at 2026-05-05T08:00:00Z \
  --run-id pilot-demo-asset-seedset \
  --out assets/outputs/runtime/asset-osint-seeds-edge-appliance.json
```

## Sanitized OSINT

List or collect from approved source catalog entries:

```bash
PYTHONPATH=world-side/scraper:. python3 -m scraper_side.cli \
  --catalog world-side/scraper/config/source_catalog.json \
  --list-sources
```

Build an offline seeded snapshot from checked-in fixtures:

```bash
PYTHONPATH=world-side/scraper:. python3 -m scraper_side.snapshot \
  --catalog world-side/scraper/config/source_catalog.json \
  --source cisa_vulnrichment_cve_record_seed \
  --source osv_query_api_seed \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --seed-fixture-dir world-side/fixtures/seeded-osint \
  --limit-per-source 1 \
  --generated-at 2026-05-05T08:00:00Z \
  --policy policy/prophet-pilot-policy.json \
  --out-jsonl world-side/outputs/runtime/seeded-osint-edge-appliance.jsonl \
  --out-manifest world-side/outputs/runtime/seeded-osint-edge-appliance.manifest.json
```

## Forecaster

Generate a forecast from a safe candidate, optional sanitized OSINT snapshot,
and optional asset seedset:

```bash
PYTHONPATH=world-side:world-side/scraper:. python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --osint-snapshot world-side/fixtures/osint-snapshot-sample.jsonl \
  --osint-manifest world-side/fixtures/osint-snapshot-sample.manifest.json \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --generated-at 2026-05-05T08:00:00Z \
  --out world-side/outputs/runtime/forecast-with-asset-seeds.json
```

## Exposure Portfolio

Generate a safe defensive class portfolio from a forecast:

```bash
PYTHONPATH=cyber-side python3 -m predictor \
  --forecast world-side/outputs/golden-forecast-edge-appliance.json \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --generated-at 2026-05-05T08:00:00Z \
  --out cyber-side/outputs/runtime/latest-prediction-portfolio-edge-appliance.json
```

Validate an existing portfolio fixture:

```bash
PYTHONPATH=cyber-side python3 -m predictor \
  --validate-only \
  --forecast cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json
```

## Sandbox Fixtures

Run a predefined fixture sandbox profile:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m sandbox_runner run \
  --profile edge-appliance-fixture \
  --mode fixture \
  --generated-at 2026-05-05T08:00:00Z \
  --run-id pilot-demo-sandbox \
  --policy policy/prophet-pilot-policy.json \
  --out cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json \
  --manifest-out cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json
```

Container mode is not part of the default buyer pilot. Any non-fixture sandbox
mode now fails closed unless the operator supplies a sanitized
`prophet_sandbox_customer_approval.v0.1` record with matching `profile`,
`mode`, `decision: approved`, `approved_for: ["non_fixture_sandbox_mode"]`,
and true safety attestations for no live targets, no payloads, no credentials,
customer boundary review, and policy review. Supplying that record does not
enable container execution in this public repo; it only proves the customer
approval gate was satisfied before the still-disabled mode is considered.

## Evidence And Audit

Append and validate a local operator audit event:

Operator labels are sanitized local pilot labels, not production identity. Use
`docs/OPERATOR_IDENTITY_GUIDE.md` before changing `--operator-label`.

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit append \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --policy policy/prophet-pilot-policy.json \
  --event-type operator_approval \
  --operator-label fixture \
  --decision bypassed_for_fixture \
  --generated-at 2026-05-05T08:00:00Z \
  --out-event evidence/outputs/runtime/pilot-demo-approval-record.json

PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit validate \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl
```

Generate the buyer-review evidence bundle:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.bundle \
  --forecast world-side/outputs/golden-forecast-edge-appliance.json \
  --portfolio cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json \
  --artifact cyber-side/fixtures/exploit-engine-output-edge-appliance.json \
  --asset-inventory assets/fixtures/dib-edge-appliance-inventory.json \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --policy policy/prophet-pilot-policy.json \
  --approval-record evidence/outputs/runtime/pilot-demo-approval-record.json \
  --sandbox-run-manifest cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json \
  --operator-label fixture \
  --approval-decision bypassed_for_fixture \
  --generated-at 2026-05-05T08:00:00Z \
  --run-id pilot-demo-evidence \
  --out-json evidence/outputs/runtime/latest-edge-appliance.json \
  --out-md evidence/outputs/runtime/latest-edge-appliance.md
```

Export a safe audit summary or retention report when a reviewer asks:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit export \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --out-json evidence/outputs/runtime/pilot-demo-operator-audit-export.json

PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit retention \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --policy policy/prophet-pilot-policy.json \
  --out-json evidence/outputs/runtime/pilot-demo-operator-audit-retention.json
```

## Integration Handoffs

Export safe SIEM and ticket review templates from an evidence bundle:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m integrations.export \
  --bundle evidence/outputs/runtime/latest-edge-appliance.json \
  --out-dir integrations/outputs/runtime/latest-edge-appliance \
  --zip-out integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip \
  --generated-at 2026-05-05T08:00:00Z \
  --export-id pilot-demo-integration-export \
  --policy policy/prophet-pilot-policy.json
```

Review templates are customer-facing artifacts for inspection. They are not
connector pushes. The optional ZIP is a deterministic review bundle containing
the same validated files.

## Policy

Lint the packaged pilot policy:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json \
  --schema policy/prophet-pilot-policy.schema.json
```

Compare a customer-specific policy to the pilot baseline:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/examples/fixture-only-policy.json \
  --compare-to policy/prophet-pilot-policy.json
```

Check policy-bound runtime retention:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.retention \
  --policy policy/prophet-pilot-policy.json \
  --out-json evidence/outputs/runtime/pilot-demo-runtime-retention.json
```

Do not use retention delete flags during evaluator reviews.

## Validation Sprint

Initialize ignored private validation files:

```bash
python3 scripts/init-validation-sprint.py --date 2026-05-11
python3 scripts/init-validation-sprint.py --date 2026-05-11 --refresh-readme
```

Use `--refresh-readme` after a recovered session when
`validation/private/README.md` needs current operator guidance but private
tracker/log files must not be overwritten.
The Make equivalent is
`make validation-init DATE=2026-05-11 REFRESH_README=1`.

Generate the daily block, message pack, and status reports:

```bash
make validation-pack DATE=2026-05-11
make validation-status DATE=2026-05-11
```

`make validation-status` prints the Markdown status report for humans. For
machine-readable checks, read `validation/private/today-outreach-status.json`;
it includes `next_pending_target_label`, the next safe dry-run apply command,
and the matching `CONFIRM_SENT=1` command.

After a terminal restore, machine sleep, or crash, run `date +%F`. If the shell
date is not the outreach day you are operating, pass `DATE=YYYY-MM-DD`
explicitly to the validation Make targets.

Manual equivalent:

```bash
python3 scripts/validation-outreach-block.py \
  --date 2026-05-11 \
  --format json \
  --out validation/private/today-outreach-block.json
python3 scripts/validation-outreach-block.py \
  --date 2026-05-11 \
  --format markdown \
  --out validation/private/today-outreach-block.md

python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --require-date 2026-05-11 \
  --format json \
  --out validation/private/today-message-pack.json
python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --require-date 2026-05-11 \
  --format markdown \
  --out validation/private/today-message-pack.md

python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date 2026-05-11 \
  --format json \
  --out validation/private/today-outreach-status.json
python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date 2026-05-11 \
  --format markdown \
  --out validation/private/today-outreach-status.md
```

Render the next verified pending draft for send-by-send execution:

```bash
make validation-next-draft DATE=2026-05-11
make validation-send-copy DATE=2026-05-11

python3 scripts/validation-next-draft.py \
  --message-pack validation/private/today-message-pack.json \
  --targets validation/private/validation-targets.json \
  --require-date 2026-05-11 \
  --format markdown \
  --out validation/private/today-next-draft.md

python3 scripts/validation-next-draft.py \
  --message-pack validation/private/today-message-pack.json \
  --targets validation/private/validation-targets.json \
  --require-date 2026-05-11 \
  --format send-text \
  --out validation/private/today-send-copy.txt
```

When sending from the rendered draft, copy the generated subject/body as-is, or
personalize only in the outreach channel after pasting. Use
`today-send-copy.txt` when you want an outbound copy artifact with one subject
line and the message body, without target labels, tracker commands, alternate
subject options, or status metadata. Do not store recipient names, private
contact details, or new claims in repo files.

Render one copy-only file per verified pending draft when sending a whole
outreach block:

```bash
make validation-send-copy-batch DATE=2026-05-11
make validation-send-copy-check DATE=2026-05-11

python3 scripts/validation-send-copy-batch.py \
  --message-pack validation/private/today-message-pack.json \
  --targets validation/private/validation-targets.json \
  --require-date 2026-05-11 \
  --out-dir validation/private/send-copy-2026-05-11

python3 scripts/validation-send-copy-batch.py \
  --check-dir validation/private/send-copy-2026-05-11 \
  --require-date 2026-05-11
```

Open the generated numbered `.txt` files and copy only their subject/body
contents into the outreach channel. Do not attach the `.txt` files; filenames,
`manifest.json`, `CHECKLIST.md`, `COPY_ONLY_INDEX.md`, `SUBJECT_ORDER.md`, and
batch `README.md` are private tracker/operator metadata and should not be
pasted or sent to a buyer; do not send the private manifest, checklist, copy index,
subject-order helper, or batch README. The dashboard verifies the directory through
`send_copy_batch_state`, `send_copy_batch_matches_current_pack`,
`send_copy_batch_readme_exists`, `send_copy_batch_checklist_exists`, and
`outreach_execution.send_copy_batch_copy_index_exists`, and
`outreach_execution.send_copy_batch_subject_order_exists`; the
match check covers numbered copy files, manifest fields, manifest operator
notes, manifest outbound-boundary fields, copy-file SHA-256 values, the batch
README body, the batch checklist body, neutral copy-index body, and
subject-order body. Rerun
the batch command before using the directory if the state is not ready or any
ready/check boolean is not true. The dated directory convention is
`validation/private/send-copy-YYYY-MM-DD/`.
`make validation-send-copy-check` directly verifies the existing numbered
`.txt` files against the private manifest: neutral filenames, one `Subject:`
line each, SHA-256 matches, no target labels, no tracker commands, and no
private metadata.

Render a specific target draft when needed:

```bash
make validation-draft TARGET=target-dib-platform-004 DATE=2026-05-11
make validation-draft-copy TARGET=target-dib-platform-004 DATE=2026-05-11

python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --target-label target-dib-platform-004 \
  --require-date 2026-05-11 \
  --format markdown

python3 scripts/validation-message-pack.py \
  --block validation/private/today-outreach-block.json \
  --target-label target-dib-platform-004 \
  --require-date 2026-05-11 \
  --format send-text
```

Use `validation-draft-copy` or `--format send-text` only for copy-only outbound
text for a selected anonymized target. It does not write
`validation/private/today-send-copy.txt`, so it does not change the dashboard's
next-pending send-copy match state.

Dry-run the generated tracker update before sending, then apply it only after a
confirmed send:

```bash
make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11
make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11 CONFIRM_SENT=1
make validation-log-interview DATE=2026-05-11
make validation-log-interview DATE=2026-05-11 CONFIRM_LOG=1

python3 scripts/validation-apply-draft-update.py \
  --message-pack validation/private/today-message-pack.json \
  --targets validation/private/validation-targets.json \
  --target-label target-dib-platform-001 \
  --require-date 2026-05-11
```

The dry-run JSON echoes `dry_run_apply_command`, `confirmed_apply_command`,
`status_command`, and `dashboard_command` so a restored terminal can continue
without reconstructing the next command by hand.
`make validation-log-interview` requires the interview `account_label`, segment,
and persona to match an anonymized target currently in `call_booked`.
When `CONFIRM_SENT=1` is used through Make, or `--confirm-sent` is used
directly, the apply helper also verifies a matching copy-only send artifact
from `today-send-copy.txt` or the current send-copy batch manifest before
writing the private tracker.

Verify outreach execution and update one anonymized target:

```bash
make validation-status DATE=2026-05-11

python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date 2026-05-11 \
  --format json \
  --out validation/private/today-outreach-status.json
python3 scripts/validation-outreach-status.py \
  --verify-dry-run-commands \
  --require-date 2026-05-11 \
  --format markdown \
  --out validation/private/today-outreach-status.md

python3 scripts/validation-reply-triage.py \
  --target-label target-dib-platform-004 \
  --classification book_call \
  --date 2026-05-11 \
  --format markdown

make validation-reply-triage TARGET=target-dib-platform-004 REPLY=book_call DATE=2026-05-11

python3 scripts/validation-reply-triage.py \
  --target-label target-dib-platform-004 \
  --classification disqualify \
  --date 2026-05-11 \
  --format json

python3 scripts/validation-target-update.py \
  --target-label target-dib-platform-004 \
  --status intro_requested \
  --last-touch 2026-05-11 \
  --follow-up-due 2026-05-13 \
  --require-current-status identified \
  --dry-run

make validation-book-call TARGET=target-dib-platform-004 DATE=2026-05-11
make validation-book-call TARGET=target-dib-platform-004 DATE=2026-05-11 CONFIRM_TARGET=1
make validation-disqualify-target TARGET=target-dib-platform-004 DATE=2026-05-11
make validation-prepare-interview TARGET=target-dib-platform-004 DATE=2026-05-11
make validation-complete-call TARGET=target-dib-platform-004 DATE=2026-05-11
```

The raw target update CLI validates without writing by default. Confirmed
send-derived `intro_requested` / `outreach_sent` writes are blocked there; use
`make validation-apply-draft TARGET=... DATE=YYYY-MM-DD CONFIRM_SENT=1` after
the real send and matching copy-only artifact verification. Use
`--confirm-target` only after reviewing non-send target transitions, and prefer
the Make wrappers above during outreach. `make validation-complete-call` requires the validation
log to contain a sanitized interview whose `account_label` matches the
anonymized target label before the target can be marked completed.
`scripts/validation-reply-triage.py` is a no-write reply helper: pass only the
sanitized classification (`book_call`, `disqualify`, `keep_pending`, or
`manual_review`), never reply text. It emits the safe dry-run command and, only
for booked/disqualified replies, the matching `CONFIRM_TARGET=1` command to run
after review. Prefer the `make validation-reply-triage TARGET=... REPLY=...`
wrapper during normal outreach.

Append a sanitized interview and rerun the dashboard:

```bash
python3 scripts/validation-prepare-interview.py \
  --target-label target-dib-platform-004 \
  --date 2026-05-11 \
  --out validation/private/customer-validation-interview-next.json

python3 scripts/customer-validation-log-add.py \
  --interview-json validation/private/customer-validation-interview-next.json \
  --updated-at 2026-05-11 \
  --require-target-status call_booked

# The guarded append requires the interview account_label, segment, and persona
# to match the booked anonymized target.

python3 scripts/customer-validation-log-add.py \
  --interview-json validation/private/customer-validation-interview-next.json \
  --updated-at 2026-05-11 \
  --require-target-status call_booked \
  --confirm-log

# First real interview only: remove the initialized example seed.
python3 scripts/customer-validation-log-add.py \
  --interview-json validation/private/customer-validation-interview-next.json \
  --updated-at 2026-05-11 \
  --require-target-status call_booked \
  --replace-example-seed

# Seed replacement must stay tied to a booked anonymized target.
# Do not combine --replace-example-seed with --allow-untracked-interview.

python3 scripts/validation-sprint-dashboard.py \
  --require-date 2026-05-11 \
  --message-pack validation/private/today-message-pack.json
python3 scripts/validation-sprint-dashboard.py \
  --require-date 2026-05-11 \
  --message-pack validation/private/today-message-pack.json \
  --format text
python3 scripts/validation-sprint-dashboard.py \
  --require-date 2026-05-11 \
  --message-pack validation/private/today-message-pack.json \
  --format team
make validation-dashboard DATE=2026-05-11
make validation-team-update DATE=2026-05-11
make validation-team-update-save DATE=2026-05-11
make validation-next-action-save DATE=2026-05-11
make validation-weekly-review DATE=2026-05-11
make validation-resume DATE=2026-05-11
make goal-resume DATE=2026-05-11
```

The dashboard JSON includes `outreach_execution.next_draft_state`,
`outreach_execution.next_draft_exists`, and
`outreach_execution.next_draft_matches_next_pending`, plus
`outreach_execution.send_copy_state` and
`outreach_execution.send_copy_matches_next_pending`, and for whole-block sends,
`outreach_execution.send_copy_batch_state` plus
`outreach_execution.send_copy_batch_matches_current_pack` and
`outreach_execution.send_copy_batch_readme_exists` plus
`outreach_execution.send_copy_batch_checklist_exists` plus
`outreach_execution.send_copy_batch_copy_index_exists` plus
`outreach_execution.send_copy_batch_subject_order_exists`. Treat the already-rendered
`validation/private/today-next-draft.md` as tracker/audit metadata only when the
state is `ready`; that means the draft target, outreach date, and verified
status match the current next pending target. Run
`make validation-send-copy DATE=YYYY-MM-DD` and send from
`validation/private/today-send-copy.txt` only when `send_copy_state` is `ready`,
then use the dashboard's dated dry-run / `CONFIRM_SENT=1` commands for that
target after the actual send. The
`make validation-send-copy-batch DATE=YYYY-MM-DD` path is usable only when
`send_copy_batch_state` is `ready` and
`send_copy_batch_matches_current_pack`, `send_copy_batch_readme_exists`, and
`send_copy_batch_checklist_exists`, `send_copy_batch_copy_index_exists`, and
`send_copy_batch_subject_order_exists` are true; the match check also verifies
manifest operator notes, manifest outbound-boundary fields, copy-file SHA-256
values, the batch README body, the batch checklist body, and the neutral
copy-index body and subject-order body.
`validation-resume` wrapper runs the same dashboard check, prints the
copy-only send text only when it matches, wraps it in begin/end markers, and
prints the already-rendered next draft below a do-not-send divider only when it
still matches the current next pending target/date/status/body.
`make goal-resume` is an alias for the same no-write recovery path after a lost
`/goal` session. Use `--format text` when you want the dashboard's send-boundary summary
without the full JSON payload. Use `--format team` or
`make validation-team-update DATE=YYYY-MM-DD` for a sanitized aggregate-only
status update that omits target labels, commands, message bodies, and private
validation paths. It includes aggregate send-copy readiness fields so shared
status can show whether the outbound copy is ready without revealing the target
or text. It reports gate-counted buyer evidence first; if the log is still the
example seed, raw seed counts are labeled as ignored placeholders. Use
`make validation-team-update-save DATE=YYYY-MM-DD` to write that aggregate-only
update to `validation/private/today-team-update.md`.
Use `make validation-next-action-save DATE=YYYY-MM-DD` to regenerate the
ignored private `validation/private/NEXT_ACTION.md` operator handoff from the
current dashboard, including the send boundary, current next target, and local
git head, without touching tracker/log state.
Make confirmation variables are exact write guards: only `CONFIRM_SENT=1`,
`CONFIRM_TARGET=1`, and `CONFIRM_LOG=1` can write. Values such as `0`, `false`,
`yes`, or `1 0` fail closed.

Build a read-only private weekly review before pruning or rotating validation
artifacts:

```bash
make validation-weekly-review DATE=2026-05-11

python3 scripts/validation-weekly-review.py \
  --private-dir validation/private \
  --targets validation/private/validation-targets.json \
  --log validation/private/customer-validation-log.json \
  --message-pack validation/private/today-message-pack.json \
  --review-date 2026-05-11 \
  --format json \
  --out validation/private/today-weekly-review.json
python3 scripts/validation-weekly-review.py \
  --private-dir validation/private \
  --targets validation/private/validation-targets.json \
  --log validation/private/customer-validation-log.json \
  --message-pack validation/private/today-message-pack.json \
  --review-date 2026-05-11 \
  --format markdown \
  --out validation/private/today-weekly-review.md
```

The weekly review is read-only. It validates the private tracker and log,
reports the current validation gate using the same target-backed build-gate rule
as the dashboard, message-pack age, date-guarded outreach execution readiness,
ignored private file count, stale private artifacts, and pruning candidates. It
does not delete files, send messages, or mutate trackers/logs.

After reading the weekly review, build a confirmation-gated prune plan for
generated ignored private artifacts:

```bash
make validation-prune-private DATE=2026-05-11

python3 scripts/validation-prune-private.py \
  --weekly-review validation/private/today-weekly-review.json \
  --private-dir validation/private \
  --review-date 2026-05-11 \
  --format markdown
```

The prune helper is dry-run by default. It only considers generated private
validation artifacts such as outdated `send-copy-YYYY-MM-DD` batches or unsafe
copy-only send text flagged by the weekly review. It protects validation
trackers, logs, templates, and README files. Use `CONFIRM_PRUNE=1` or
`--confirm-prune` only after reviewing the plan.

The interview log appender validates and prints the projected scorecard summary
without writing by default. Use `--confirm-log` only after the sanitized record
is reviewed. Normal confirmed raw writes require
`--require-target-status call_booked` with matching account label, segment, and
persona metadata, or the explicit `--allow-untracked-interview` bypass.
First-interview seed replacement is stricter: `--replace-example-seed` requires
`--require-target-status call_booked`, matching target metadata, and rejects `--allow-untracked-interview`.
The interview preparation helper writes an intentionally incomplete private
starter from a booked anonymized target; it should fail validation until real
sanitized call outcomes are filled.

## Release And Readiness Checks

Run focused scorecards:

```bash
python3 scripts/customer-validation-scorecard.py \
  --log docs/customer-validation-log.example.json

python3 scripts/validation-targets-scorecard.py \
  --targets docs/validation-targets.example.json

python3 scripts/production-readiness-scorecard.py
```

The customer validation scorecard includes `gaps_to_verdicts` so operators can
see remaining counts before `pilot_pull_detected` or `build_next_slice`.

Run safety scans:

```bash
PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff
PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --staged
```

Run CLI guard coverage:

```bash
PYTHONPATH=.:cyber-side:world-side:world-side/scraper \
  python3 -m unittest scripts.tests.test_cli_no_live_targets -v
```

## Getting Help

Every Python module above supports `--help`. Subcommand CLIs also support help
at the subcommand level.

The docs test suite executes these help commands directly:

```text
make help
./scripts/check-local-env.sh --help
./scripts/run-console-demo.sh --help
./scripts/check-console-live-demo.sh --help
python3 scripts/check-console-screenshots.py --help
./scripts/check-release-hygiene.sh --help
python3 scripts/check-doc-links.py --help
./scripts/run-pilot-demo-smoke.sh --help
PYTHONPATH=. python3 -m assets.import_csv --help
PYTHONPATH=. python3 -m assets.inventory --help
PYTHONPATH=world-side/scraper:. python3 -m scraper_side.cli --help
PYTHONPATH=world-side/scraper:. python3 -m scraper_side.snapshot --help
PYTHONPATH=world-side:world-side/scraper:. python3 -m forecaster.cli --help
PYTHONPATH=cyber-side python3 -m predictor --help
PYTHONPATH=.:cyber-side:world-side python3 -m sandbox_runner --help
PYTHONPATH=.:cyber-side:world-side python3 -m sandbox_runner run --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.bundle --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit append --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit validate --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit export --help
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit retention --help
PYTHONPATH=.:cyber-side:world-side python3 -m integrations.export --help
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint --help
PYTHONPATH=.:cyber-side:world-side python3 -m policy.retention --help
python3 scripts/init-validation-sprint.py --help
python3 scripts/validation-outreach-block.py --help
python3 scripts/validation-message-pack.py --help
python3 scripts/validation-next-draft.py --help
python3 scripts/validation-send-copy-batch.py --help
python3 scripts/validation-apply-draft-update.py --help
python3 scripts/validation-outreach-status.py --help
python3 scripts/validation-reply-triage.py --help
python3 scripts/validation-target-update.py --help
python3 scripts/validation-prepare-interview.py --help
python3 scripts/customer-validation-log-add.py --help
python3 scripts/customer-validation-scorecard.py --help
python3 scripts/validation-targets-scorecard.py --help
python3 scripts/validation-sprint-dashboard.py --help
python3 scripts/validation-next-action.py --help
python3 scripts/validation-weekly-review.py --help
python3 scripts/validation-prune-private.py --help
python3 scripts/check-release-safety.py --help
python3 scripts/production-readiness-scorecard.py --help
```
