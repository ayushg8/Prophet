# Prophet

Prophet is a policy-bound evidence system for defensive exposure
prioritization. It helps security teams decide what exposure class to harden
first, explain why that decision is reasonable, validate only in safe fixture or
approved sandbox modes, and hand off review artifacts to SOC and platform
teams.

```text
prioritize exposure -> explain evidence -> validate safely -> hand off review artifacts
```

The product claim is deliberately narrow: Prophet does not discover zero-days,
does not generate offensive payloads, does not test live infrastructure, and
does not deploy controls autonomously. It produces an auditable "why this
first" package from approved asset/SBOM metadata, public vulnerability context,
policy checks, deterministic validation summaries, and safe handoff templates.

## Why This Exists

Federal and defense networks are structurally reactive. CISA KEV/BOD pressure,
EPSS probability signals, SBOM obligations, and leadership scrutiny all create
the same operational question: when the queue is too large, what should be
hardened first and what evidence proves that decision was reasonable?

For defense-tech buyers, the wedge is not another scanner or exposure graph.
The wedge is a repeatable defensive evidence loop:

- **Prioritize**: rank the exposure class that deserves attention first.
- **Explain**: show source basis, asset/SBOM basis, confidence, freshness, and
  assumptions.
- **Validate safely**: use deterministic fixtures, localhost, or an explicitly
  approved sandbox only.
- **Hand off**: export evidence, audit, SIEM, and ticketing review templates
  without production pushes.

## Current Working Surfaces

| Surface | Status | Notes |
|---|---|---|
| Forecaster | Working | Deterministic Python; no runtime LLM or external API dependency. |
| Asset import | Working | Imports customer-safe CSV metadata with row-level cleanup reports and optional seedsets. |
| Asset-seeded OSINT | Working | Generates safe metadata seedsets and policy-gated fixture-backed public-source snapshots. |
| Contract validators | Working | Reject payloads, credentials, live targets, procedural instructions, and schema drift. |
| Exposure-class portfolio | Working | Produces safe non-operational defensive class recommendations for demo and analyst review. |
| Sandbox runner | Working | Deterministic localhost fixture artifact for the edge-appliance profile. |
| Evidence export | Working | Generates policy-bound JSON + Markdown evidence bundles from validated fixtures. |
| Integration handoff | Working | Exports safe SIEM and ticketing review templates from validated evidence. |
| Policy linting | Working | Validates customer pilot policies, allowed modes, source IDs, sandbox profiles, blocked controls, and runtime output paths. |
| React operator console | Working | Fixture-backed end-to-end replay with human gate, defense artifact, and validation status. |
| Local control server | Working | Serves sanitized demo refresh and fixture artifacts on localhost. |
| Live collection workflow | Disabled by default | Requires `PROPHET_ENABLE_VM_SCRAPER=1` and an approved isolated collection plan. |
| Private research integration | Not packaged | Public repo includes safe interfaces and fixtures only; lab-only research remains outside product paths. |

## Architecture

```text
approved asset/SBOM metadata
       |                 sanitized public context
       v                          |
 assets/ import + seedset         v
       |               world-side/ forecaster
       |                          |
       +----------+---------------+
                  |
                  v
       cyber-side/ defensive portfolio
                  |
                  v
       sandbox_runner/ fixture validation
                  |
                  v
       evidence/ bundle + audit trail
                  |
       +----------+---------------+
       |                          |
       v                          v
integrations/ review templates    prophet-console/ evaluator UI
```

The contracts are the product boundary:

- `world-side/INTERFACE.md`: candidate and forecast schemas.
- `cyber-side/INTERFACE.md`: defense artifact schema.
- `cyber-side/validator.py`: payload and live-target rejection.
- `world-side/forecaster/models.py`: forecast safety and schema validation.

## Module Ownership

Ownership here means the canonical place to change behavior. Keep edits inside
the owning module unless a contract update requires coordinated changes.

| Module | Owns | Primary docs/tests |
|---|---|---|
| `assets/` | Customer-safe asset/SBOM metadata import and seedsets. | `docs/ASSET_IMPORT_GUIDE.md`, `assets/tests/` |
| `world-side/` | Sanitized source ingestion and forecast generation. | `world-side/INTERFACE.md`, `world-side/tests/` |
| `cyber-side/` | Defensive portfolio fixtures and artifact validation. | `cyber-side/INTERFACE.md`, `cyber-side/tests/` |
| `sandbox_runner/` | Deterministic fixture validation profiles. | `sandbox_runner/tests/` |
| `evidence/` | Evidence bundle, audit log, redaction, and retention outputs. | `evidence/tests/` |
| `integrations/` | SIEM/ticket review-template exports. | `docs/INTEGRATION_HANDOFF_GUIDE.md`, `integrations/tests/` |
| `policy/` | Pilot policy schema, linting, source allowlists, and retention gates. | `docs/PILOT_POLICY_REVIEW.md`, `policy/tests/` |
| `prophet-console/` | Evaluator UI and localhost control server. | `prophet-console/README.md`, `prophet-console/tests/` |
| `scripts/` | Smoke, validation sprint, release-safety, and operator helpers. | `docs/CLI_REFERENCE.md`, `scripts/tests/` |
| `validation/private/` | Ignored private buyer validation workspace. | `docs/VALIDATION_DAILY_BRIEF.md` |

## Quickstart

### Three-Minute Evaluator Path

Use this when an evaluator wants to prove the defensive pilot loop from a fresh
clone without reading code or enabling live collection.

Prerequisites:

- Python 3.9 or newer.
- Bash-compatible shell.
- Optional for console review: Node 24 or newer and npm.

From the repo root:

```bash
./scripts/check-local-env.sh
./scripts/run-pilot-demo-smoke.sh
```

Expected result:

- The pilot policy lints successfully.
- Safe asset import, seeded OSINT, forecast refresh, sandbox validation,
  evidence export, audit export, retention reporting, and SIEM/ticketing
  handoff export all complete.
- The final hash check matches `scripts/pilot-demo-smoke.sha256`.
- Runtime policy-hash drift checks pass for the generated evidence, OSINT,
  sandbox, audit, and integration artifacts.
- Outputs stay under ignored `*/outputs/runtime/` directories.

The smoke path is fixture-backed, policy-bound, and localhost-only. It does not
contact live targets, generate payloads, read credentials, or require private
hostnames.

For a customer-facing evaluation path, start with
`docs/EVALUATOR_START_HERE.md` and record findings in
`docs/EVALUATOR_WORKSHEET.md`. Operators should use
`docs/DEMO_OPERATOR_CHECKLIST.md` before a live buyer review, and non-cyber
reviewers can use `docs/GLOSSARY.md` for terminology. For a deeper analyst
review, use `docs/ANALYST_WALKTHROUGH.md`. For local setup failures, use
`docs/PILOT_TROUBLESHOOTING.md`.

After the smoke run, inspect:

- `evidence/outputs/runtime/latest-edge-appliance.md`
- `evidence/outputs/runtime/latest-edge-appliance.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-retention.json`
- `integrations/outputs/runtime/latest-edge-appliance/manifest.json`

### Internal Acceptance

Run the full internal-alpha acceptance path from the console package:

```bash
cd prophet-console
npm run acceptance
```

The acceptance command runs the root pilot smoke, console lint/build,
control-server evidence/readiness smoke, and Playwright browser smoke.

Common operator wrappers are available from the repo root:

```bash
make help
make check-local-env
make pilot-ready-check DATE=YYYY-MM-DD
make pilot-ready-check-full DATE=YYYY-MM-DD
make pilot-smoke
make supply-chain-sbom DATE=YYYY-MM-DD
make supply-chain-sbom-check DATE=YYYY-MM-DD
make validation-pack DATE=YYYY-MM-DD
make validation-init DATE=YYYY-MM-DD REFRESH_README=1
make validation-next-draft DATE=YYYY-MM-DD
make validation-send-copy DATE=YYYY-MM-DD
make validation-apply-draft TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-pre-send-check TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-pre-send-check-all DATE=YYYY-MM-DD
make validation-log-interview DATE=YYYY-MM-DD
make validation-draft TARGET=target-dib-platform-004 DATE=YYYY-MM-DD
make validation-draft-copy TARGET=target-dib-platform-004 DATE=YYYY-MM-DD
make validation-send-copy-batch DATE=YYYY-MM-DD
make validation-contact-form-copy DATE=YYYY-MM-DD
make validation-contact-form-copy-check DATE=YYYY-MM-DD
make validation-send-batch-ready-save DATE=YYYY-MM-DD
make validation-status DATE=YYYY-MM-DD
make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call DATE=YYYY-MM-DD
make validation-dashboard DATE=YYYY-MM-DD
make validation-team-update DATE=YYYY-MM-DD
make validation-team-update-save DATE=YYYY-MM-DD
make validation-next-action-save DATE=YYYY-MM-DD
make validation-working-product-handoff-save DATE=YYYY-MM-DD
make validation-weekly-review DATE=YYYY-MM-DD
make validation-prune-private DATE=YYYY-MM-DD
make validation-resume DATE=YYYY-MM-DD
make goal-resume DATE=YYYY-MM-DD
make python-tests
make worktree-smoke
make release-hygiene
make release-safety
```

`make supply-chain-sbom-check` validates the ignored generated supply-chain
review artifact. It is the correct check for that runtime review file;
release-safety intentionally rejects generated runtime outputs as commit
content.

`make validation-status` prints the Markdown status report for humans and
refreshes `validation/private/today-outreach-status.json` for machine-readable
checks, including `next_pending_target_label` and the exact next dry-run /
`CONFIRM_SENT=1` commands. `make validation-dashboard` reports
`outreach_execution.next_draft_state` plus both
`outreach_execution.next_draft_exists` and
`outreach_execution.next_draft_matches_next_pending`, plus
`outreach_execution.send_copy_state` and
`outreach_execution.send_copy_matches_next_pending`, plus
`outreach_execution.contact_form_copy_state`,
`outreach_execution.contact_form_copy_matches_current_pack`, and
`outreach_execution.next_pending_pre_send_check_command`; treat the already-rendered
`validation/private/today-next-draft.md` as tracker context, then send from
`validation/private/today-send-copy.txt` only when both the draft and copy-only
text match the current next pending target/date/status/body.
`make validation-send-copy` writes `validation/private/today-send-copy.txt`
for the same verified next draft without target labels, tracker commands, or
status metadata, so operators can copy only the outbound text.
The repo intentionally does not store recipient names, emails, LinkedIn URLs,
or outbound channel details. The external outreach channel and real contact
must come from outside the repo before sending any copy-only draft.
`make validation-send-copy-batch` writes one neutral-named copy-only `.txt`
file per verified pending draft under
`validation/private/send-copy-YYYY-MM-DD/`. The dashboard
reports `outreach_execution.send_copy_batch_state` and
`outreach_execution.send_copy_batch_matches_current_pack`, plus
`outreach_execution.send_copy_batch_readme_exists` and
`outreach_execution.send_copy_batch_checklist_exists`, and
`outreach_execution.send_copy_batch_copy_index_exists`, and
`outreach_execution.send_copy_batch_subject_order_exists`, and
`outreach_execution.send_copy_batch_do_not_send_exists`; open the `.txt` files
and copy only their contents when those fields are ready/true. Do not attach
the files. The match check covers the numbered copy files, manifest fields,
manifest operator notes, manifest outbound-boundary fields, copy-file SHA-256
values, batch README body, batch checklist body with per-draft pre-send commands, neutral copy-index body,
subject-order body, and DO_NOT_SEND guard; do not send the private manifest,
checklist, copy index, subject-order helper, DO_NOT_SEND guard, or batch README.
`make validation-contact-form-copy DATE=YYYY-MM-DD` writes shorter neutral
`.txt` files under `validation/private/contact-form-copy-YYYY-MM-DD/` for
public contact forms that need compact copy. Run
`make validation-contact-form-copy-check DATE=YYYY-MM-DD` before relying on an
existing contact-form copy directory; the dashboard also reports
`outreach_execution.contact_form_copy_state` and
`outreach_execution.contact_form_copy_matches_current_pack`. Only the numbered
file contents are outbound copy; the manifest, checklist, index, README, and
DO_NOT_SEND guard stay private.
`make validation-pre-send-check TARGET=... DATE=YYYY-MM-DD` is the dry-run
pre-send wrapper: it runs the dashboard, existing send-copy batch check, fresh
contact-form copy check when that directory exists, weekly review, prune
dry-run, and tracker-update dry run, and it refuses all `CONFIRM_*` write
guards.
`make validation-pre-send-check-all DATE=YYYY-MM-DD` verifies the existing
send-copy batch, the contact-form copy batch when present, and every pending
generated tracker update in one dry-run report. It is useful before sending a
full outreach block; it still does not send messages or write tracker state.
`make validation-send-batch-ready-save DATE=YYYY-MM-DD` writes that full
pre-send report to ignored `validation/private/SEND_BATCH_READY.md` for local
handoff after a restore or before a full send block. It is private operator
metadata, refuses `CONFIRM_*` guards, sends nothing, and writes no tracker
state.
`make validation-draft-copy TARGET=... DATE=YYYY-MM-DD` prints the same
copy-only shape for one selected target without writing `today-send-copy.txt`.
`make validation-resume` runs the dashboard, prints copy-only send text only
when `send_copy_state` is `ready` and
`send_copy_matches_next_pending` is true, wraps the send text in begin/end
markers, and prints the existing next draft below a do-not-send divider only
when it still matches the current next pending target/date/status/body.
`make goal-resume` is the same no-write wrapper for a restored `/goal` session.
`make python-tests` runs the full Python unit-suite set for scripts,
cyber-side, world-side, assets, sandbox runner, policy, evidence, and
integrations before a pilot commit or PR review.
`make validation-team-update` prints a sanitized aggregate-only status update
for shared team notes; it omits target labels, commands, message bodies, and
private validation paths. It includes aggregate send-copy readiness and match
state without revealing the target or text. `make validation-team-update-save`
writes the same aggregate-only update to
`validation/private/today-team-update.md` for local handoff. The raw dashboard
also supports `--format text` for a concise
send-boundary summary and `--format team` for the aggregate update.
`make validation-next-action-save` wraps
`scripts/validation-next-action.py` and writes a regenerated private
`validation/private/NEXT_ACTION.md` handoff from the current dashboard so a
restored session does not depend on stale PR/head, worktree, CI, or
send-boundary notes. The handoff includes send-copy and contact-form copy
readiness checks before any restored session sends outreach.
`make validation-working-product-handoff-save` writes the ignored private
`validation/private/WORKING_PRODUCT_HANDOFF.md` from the current git state,
build gate, validation sprint state, and configured local console ports. If the
demo is running on alternate ports, pass them through the Make environment, for
example `PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 make
validation-working-product-handoff-save DATE=YYYY-MM-DD`.
`make validation-weekly-review` writes a read-only private weekly review under
`validation/private/`; it reports the validation gate, message-pack age, stale
private artifacts, and pruning candidates, but does not delete files, send
messages, or mutate trackers/logs. `make validation-prune-private` dry-runs a
confirmation-gated plan for generated ignored private artifacts only; add
`CONFIRM_PRUNE=1` only after reviewing the plan.
Validation Make confirmation variables are exact write guards: only
`CONFIRM_SENT=1`, `CONFIRM_TARGET=1`, `CONFIRM_LOG=1`, and
`CONFIRM_PRUNE=1` can write. Values such as `0`, `false`, `yes`, or `1 0`
fail closed.
For replies, run `make validation-reply-triage TARGET=... REPLY=... DATE=...`
with only the sanitized classification (`book_call`, `disqualify`, `keep_pending`, or
`manual_review`). It wraps `scripts/validation-reply-triage.py`, does not accept
reply text, does not write files, and emits `CONFIRM_TARGET=1` commands only
for reviewed booked-call or disqualification updates.

For recovered outreach days, pass a date through the validation wrappers:
`make validation-init DATE=YYYY-MM-DD`,
`make validation-pack DATE=YYYY-MM-DD`,
`make validation-next-draft DATE=YYYY-MM-DD`,
`make validation-apply-draft TARGET=target-label DATE=YYYY-MM-DD`, or
`make validation-status DATE=YYYY-MM-DD`, or
`make validation-dashboard DATE=YYYY-MM-DD`, or
`make validation-resume DATE=YYYY-MM-DD`.
After a terminal restore or machine sleep/crash, run `date +%F` and pass
`DATE=YYYY-MM-DD` explicitly if the shell date is not the outreach date you are
operating.
For the full safe local command surface, use `docs/CLI_REFERENCE.md`; for
guardrail coverage, use `docs/CLI_SAFETY_MATRIX.md`.

### Focused Contract Checks

Run the contract slices directly:

```bash
make python-tests
```

Or run individual suites directly:

```bash
PYTHONPATH=. python3 -m unittest discover -s policy/tests -v
PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v
PYTHONPATH=cyber-side python3 -m predictor --validate-only \
  --forecast cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json
```

Import a safe customer-owned asset CSV fixture:

```bash
PYTHONPATH=. python3 -m assets.import_csv \
  --csv assets/fixtures/dib-edge-appliance-inventory.csv \
  --inventory-id customer-safe-import \
  --scope "Customer-owned product-family metadata; no live targets named." \
  --generated-at 2026-05-05T08:00:00Z \
  --fixture \
  --out assets/outputs/runtime/customer-safe-inventory.json \
  --report-out assets/outputs/runtime/customer-safe-import-report.json \
  --seedset-out assets/outputs/runtime/customer-safe-seedset.json
```

Lint the packaged pilot policy or a customer-specific policy before a demo:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
```

See `docs/ASSET_IMPORT_GUIDE.md` and `docs/PILOT_POLICY_REVIEW.md` for the
customer CSV and policy review contracts.

Generate the pilot evidence bundle:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.bundle \
  --forecast world-side/outputs/golden-forecast-edge-appliance.json \
  --portfolio cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json \
  --artifact cyber-side/fixtures/exploit-engine-output-edge-appliance.json \
  --asset-inventory assets/fixtures/dib-edge-appliance-inventory.json \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --policy policy/prophet-pilot-policy.json \
  --operator-label fixture \
  --approval-decision bypassed_for_fixture \
  --out-json evidence/outputs/runtime/latest-edge-appliance.json \
  --out-md evidence/outputs/runtime/latest-edge-appliance.md
```

Run the evaluator console:

```bash
(cd prophet-console && npm ci)
make console-demo
```

This starts both the localhost-only control API and the evaluator UI in one
terminal. Press `Ctrl-C` to stop both processes.

If the default ports are already in use, keep the services on localhost and use
alternate ports:

```bash
PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 make console-demo
```

If you prefer separate terminals:

```bash
make console-control
```

In a second terminal:

```bash
make console-ui
```

Open `http://127.0.0.1:5173`. The control server listens on
`http://127.0.0.1:8787` and stays local-only.

Live local endpoint check:

```bash
make console-live-check
```

This verifies the UI, readiness API, evidence demo-bundle endpoint, integration
demo-export endpoint, and runtime audit log. It writes only ignored runtime
outputs.

If a qualified reviewer asks for responsive visual artifacts, run
`cd prophet-console && npm run capture:screenshots`, then
`make console-screenshot-check` before sharing the ignored redacted runtime
screenshots.

Open `http://127.0.0.1:5173`, enter the console, use **Refresh demo**, load the
defense fixture, generate the evidence bundle, export the handoff templates, and
check **Alpha Readiness**.

## Safety Model

Prophet should be sold and evaluated as a defensive decision and validation
system, not an exploit-delivery system.

- No live infrastructure testing from the public console.
- No raw scraper output crosses into the main app.
- No credentials, IPs, or operational hostnames in committed artifacts.
- No payload bytes in accepted JSON contracts.
- Policy-gated OSINT snapshots can use only approved source IDs, and
  `sandbox_runner` can use only approved profiles.
- Live collection workflows are disabled unless explicitly enabled with
  `PROPHET_ENABLE_VM_SCRAPER=1`.
- Production validation must run only in approved, isolated, vulnerable-by-design
  sandboxes.

See `SECURITY.md` for operating rules.

## Commercial Path

The credible first product is a **Defensive Exposure Prioritization Copilot**:

1. Ingest approved public and customer-owned context.
2. Forecast pressure windows and likely exposure classes.
3. Generate a reviewable defense package: patch guidance, Sigma/YARA/SIEM logic,
   test plan, and audit record.
4. Validate only in a customer-approved sandbox or digital twin.
5. Export an evidence bundle for security leadership, mission owners, and
   compliance teams.

Near-term integrations should focus on defensive systems: SBOM/asset inventory,
SIEM, ticketing, vulnerability management, and sandbox orchestration. Offensive
or live-target integrations should stay out of the default product.

Production-readiness planning is tracked in:

- `docs/PRODUCTION_EXECUTION_PLAN.md`
- `docs/PRODUCTION_ARCHITECTURE.md`
- `docs/THREAT_MODEL.md`
- `docs/COMPLIANCE_GAP_MAP.md`
- `docs/production-readiness-backlog.json`

Generate the current production readiness scorecard with:

```bash
python3 scripts/production-readiness-scorecard.py
```

Before adding more production-platform scope, run the product validation track:

- `docs/PRODUCT_VALIDATION_PLAN.md`
- `docs/CUSTOMER_DISCOVERY_GUIDE.md`
- `docs/OUTREACH_PLAYBOOK.md`
- `docs/DESIGN_PARTNER_PILOT_OFFER.md`

Score anonymized discovery evidence with:

```bash
python3 scripts/customer-validation-scorecard.py --log docs/customer-validation-log.example.json
```

Plan outreach from an anonymized target tracker with:

```bash
python3 scripts/validation-targets-scorecard.py --targets docs/validation-targets.example.json
```

Initialize the gitignored private validation workspace and print the daily
dashboard with:

```bash
python3 scripts/init-validation-sprint.py
python3 scripts/validation-sprint-dashboard.py \
  --require-date YYYY-MM-DD \
  --message-pack validation/private/today-message-pack.json
```

Use `python3 scripts/init-validation-sprint.py --date YYYY-MM-DD` when
recovering a prior outreach day; otherwise the generated dry-run examples use
the current local date. The Makefile wrappers also accept
`DATE=YYYY-MM-DD`.
Use `python3 scripts/init-validation-sprint.py --date YYYY-MM-DD --refresh-readme`
to update only the ignored private README after a recovered session without
overwriting private tracker or log files. The Make equivalent is
`make validation-init DATE=YYYY-MM-DD REFRESH_README=1`.

Run the daily private validation loop from the ignored workspace:

```bash
make validation-pack DATE=YYYY-MM-DD
make validation-status DATE=YYYY-MM-DD
```

`make validation-pack` writes the outreach block, message pack, and outreach
status files in both JSON and Markdown. Manual equivalents:
`make validation-status` prints the Markdown status report for humans; read
`validation/private/today-outreach-status.json` for machine-readable checks,
including the next pending target and the exact safe apply commands.

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

python3 scripts/validation-target-update.py \
  --target-label target-dib-platform-001 \
  --status outreach_sent \
  --require-current-status identified \
  --require-current-status intro_requested \
  --last-touch YYYY-MM-DD \
  --follow-up-due YYYY-MM-DD \
  --next-action "Send follow-up if no reply." \
  --dry-run

make validation-book-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-disqualify-target TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call DATE=YYYY-MM-DD
make validation-prepare-interview TARGET=target-dib-platform-001 DATE=YYYY-MM-DD
make validation-complete-call TARGET=target-dib-platform-001 DATE=YYYY-MM-DD

python3 scripts/customer-validation-log-add.py \
  --interview-json validation/private/customer-validation-interview-next.json \
  --updated-at YYYY-MM-DD

make validation-dashboard DATE=YYYY-MM-DD
```

Send drafts from `validation/private/today-message-pack.md`. Use the generated
Make commands for tracker updates. For booked calls, run
`make validation-prepare-interview TARGET=target-label DATE=YYYY-MM-DD` to
write an intentionally incomplete private interview starter, fill only
sanitized fields, run `make validation-log-interview DATE=YYYY-MM-DD`, then add
`CONFIRM_LOG=1` only after the record contains no names, emails, phone numbers,
URLs, private hostnames, IPs, raw customer artifacts, or secrets.
`make validation-log-interview` requires the interview `account_label`,
segment, and persona to match an anonymized target currently in `call_booked`,
so logged interviews stay tied to booked validation work.
On the first real private interview after initialization, add
`REPLACE_EXAMPLE_SEED=1` to remove the public example seed and clear
`example_seed_log`; dry-run it first, then combine it with `CONFIRM_LOG=1` only
after the sanitized record is reviewed.
Seed replacement must stay tied to a booked anonymized target: use the Make
wrapper or the raw CLI with `--require-target-status call_booked`. Do not use
the raw `--allow-untracked-interview` bypass with `REPLACE_EXAMPLE_SEED=1`; the
CLI rejects that combination.
`make validation-complete-call` also requires the validation log to contain a
sanitized interview whose `account_label` matches the anonymized target label.
The raw `customer-validation-log-add.py` script is also no-write by default and
writes only with `--confirm-log`; normal confirmed raw writes require
`--require-target-status call_booked`, with matching account label, segment,
and persona metadata, or the explicit `--allow-untracked-interview` bypass.
The bypass can record out-of-band learning, but it does not open the production
build gate. The dashboard requires `target_backed_validation` to reach
`build_next_slice`, which means counted interviews must match anonymized targets
currently in `call_booked` or `completed` with the same segment/persona
metadata.
The raw `validation-target-update.py` script is no-write by default. Confirmed
send-derived `intro_requested` / `outreach_sent` writes are blocked there; use `make validation-apply-draft
TARGET=... DATE=YYYY-MM-DD CONFIRM_SENT=1` after the real send and matching
copy-only artifact verification. Non-send target transitions write only with
`--confirm-target`.
Prefer the dated tracker commands generated in the private message pack over
the manual examples above.
When sending one ask at a time, use
`make validation-next-draft DATE=YYYY-MM-DD` to render the next verified
pending tracker/audit draft and write `validation/private/today-next-draft.md`.
Then run `make validation-send-copy DATE=YYYY-MM-DD` and send from
`validation/private/today-send-copy.txt`. Use `make validation-draft
TARGET=target-dib-platform-004 DATE=YYYY-MM-DD` when you need a specific target
label, or `make validation-draft-copy TARGET=target-dib-platform-004
DATE=YYYY-MM-DD` when you need only the pasteable subject/body for that target.
If sending the whole block, run `make validation-send-copy-batch
DATE=YYYY-MM-DD` and copy only the generated `.txt` file contents after the
dashboard reports `outreach_execution.send_copy_batch_state: ready` and
`outreach_execution.send_copy_batch_matches_current_pack: true` with
`outreach_execution.send_copy_batch_readme_exists: true` and
`outreach_execution.send_copy_batch_checklist_exists: true`,
`outreach_execution.send_copy_batch_copy_index_exists: true`, and
`outreach_execution.send_copy_batch_subject_order_exists: true`, and
`outreach_execution.send_copy_batch_do_not_send_exists: true`; the match check
also verifies the manifest operator notes, manifest outbound-boundary fields,
copy-file SHA-256 values, batch README body, batch checklist body with per-draft pre-send commands, neutral
copy-index body, subject-order body, and DO_NOT_SEND guard. Do not attach the
files. Use the private batch checklist to run each target's pre-send check
immediately before that numbered copy file is sent.
For public contact forms with tighter limits, run
`make validation-contact-form-copy DATE=YYYY-MM-DD`, verify the directory with
`make validation-contact-form-copy-check DATE=YYYY-MM-DD`, and copy only the
numbered `.txt` file contents from
`validation/private/contact-form-copy-YYYY-MM-DD/`.
Before sending, use
`make validation-apply-draft TARGET=target-dib-platform-001 DATE=YYYY-MM-DD`
to dry-run the generated tracker update; then, after a confirmed send, rerun it
with `CONFIRM_SENT=1` only after the message was actually sent and the
anonymized update is correct.
The confirmation value must be exactly `1`; `CONFIRM_SENT=0`,
`CONFIRM_TARGET=false`, `CONFIRM_LOG=yes`, and `CONFIRM_SENT='1 0'` do not
write.
The Make wrappers reject private packs that do not match today's date unless you
explicitly pass `DATE=YYYY-MM-DD`.
If the dashboard reports `outreach_execution.next_draft_state: ready`,
`outreach_execution.next_draft_matches_next_pending: true`,
`outreach_execution.send_copy_state: ready`, and
`outreach_execution.send_copy_matches_next_pending: true`, send from
`validation/private/today-send-copy.txt` and use the dashboard's dated dry-run
/ `CONFIRM_SENT=1` commands for the listed target. That match includes the
draft target, outreach date, verified status, tracker/audit draft body, and
copy-only text body.
Use `make validation-resume DATE=YYYY-MM-DD` after a restored terminal when you
want the dashboard and matching already-rendered draft printed together.

## Repository Map

```text
assets/             Customer-safe asset/SBOM fixtures, import CLI, and tests.
cyber-side/         Defensive portfolio fixtures, artifact contract, and validator.
docs/               Buyer pilot, validation, safety, release, and readiness docs.
evidence/           Policy-bound JSON/Markdown evidence bundles and audit helpers.
integrations/       SIEM, ticketing, and audit handoff review-template exporters.
intel/              Public seed data used by fixtures.
policy/             Pilot policy schema, examples, linting, and policy tests.
prophet-console/    React operator console, localhost control server, browser tests.
research/           Demo candidate notes; no live/offensive runtime path.
sandbox_runner/     Deterministic localhost sandbox simulation profiles.
scripts/            Smoke, validation, release-safety, and operator helper scripts.
validation/private/ Ignored private validation workspace for sanitized buyer notes.
world-side/         Forecaster, source sanitization, fixtures, and runtime outputs.
```

Lab-only exploit validation scaffolding is not part of the public product tree.
It belongs in a private research repo or local archive outside this repository;
see `docs/RESEARCH_LAB_POLICY.md`.
