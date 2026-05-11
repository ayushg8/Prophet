# Prophet Finish Change Inventory

Date: 2026-05-11

This inventory groups the current CEO/product finish-pass commits so they can
be reviewed or pushed to the existing PR without relying on terminal history.
It does not tag, deploy, or mark the product complete.

## Current Gate

- Customer validation verdict: `insufficient_data`.
- Production build gate: closed.
- Production readiness: `26.7%`.
- Critical open readiness items: `29`.
- Outreach status: 8 pending send/update items, 0 attention errors.
- GitHub PR `#5` exists for branch `prophet-pilot-consolidation-2026-05-05`
  and the finish-pass commits have been pushed. PR `#5` is ready for internal
  buyer-pilot review, checks are green on the pushed head, and merge/release
  decisions still require a fresh check.

Do not create production platform commits from this inventory until real
validation reaches `build_next_slice`.

## Suggested Review/Commit Groups

### 1. CEO/Product Positioning And Commercial Readiness

Purpose: reposition Prophet as a policy-bound defensive exposure evidence
workflow and keep the commercial wedge narrow.

Files:

- `AGENTS.md`
- `README.md`
- `docs/COMMERCIAL_READINESS.md`
- `docs/BUYER_FAQ.md`
- `docs/DESIGN_PARTNER_PILOT_OFFER.md`
- `docs/PILOT_SCOPE.md`
- `docs/PRODUCT_VALIDATION_PLAN.md`
- `docs/CUSTOMER_DISCOVERY_GUIDE.md`
- `docs/OUTREACH_PLAYBOOK.md`
- `docs/VALIDATION_DAILY_BRIEF.md`
- `docs/VALIDATION_SPRINT_CHECKLIST.md`
- `docs/EXPOSURE_CLASSIFICATION_GUIDE.md`
- `scripts/tests/test_product_validation_plan_docs.py`
- `scripts/tests/test_exposure_classification_guide_docs.py`

Review focus:

- Copy should not claim zero-day certainty, exploit capability, live target
  validation, autonomous remediation, or production readiness.
- Buyer promise should stay on "why this first, why now, what evidence can be
  handed to SOC/audit/leadership?"
- Root agent instructions should route future agents to
  `docs/CODEX_CEO_FINISH_BRIEF.md`, `docs/PROPHET_COMPLETION_AUDIT.md`, the
  closed build gate, and validation sprint commands. After a crash or restored
  terminal, `AGENTS.md` should send agents through the dashboard-first
  `next_draft_exists` and `next_draft_matches_next_pending` checks before
  rerendering drafts or touching tracker state; those checks now require the
  draft target, outreach date, and verified status to match.

### 2. Validation Sprint Tooling

Purpose: make the buyer validation sprint executable with private, sanitized
metadata.

Files:

- `scripts/customer-validation-scorecard.py`
- `scripts/customer-validation-log-add.py`
- `scripts/validation-sprint-dashboard.py`
- `scripts/validation-targets-scorecard.py`
- `scripts/validation-outreach-block.py`
- `scripts/validation-message-pack.py`
- `scripts/validation-next-action.py`
- `scripts/validation-next-draft.py`
- `scripts/validation-send-copy-batch.py`
- `scripts/validation-apply-draft-update.py`
- `scripts/validation-outreach-status.py`
- `scripts/validation-reply-triage.py`
- `scripts/validation-weekly-review.py`
- `scripts/validation-prune-private.py`
- `scripts/validation-target-update.py`
- `scripts/validation-prepare-interview.py`
- `scripts/init-validation-sprint.py`
- `docs/customer-validation-log.example.json`
- `docs/customer-validation-interview.template.json`
- `docs/validation-targets.example.json`
- `scripts/tests/test_customer_validation_scorecard.py`
- `scripts/tests/test_customer_validation_log_add.py`
- `scripts/tests/test_init_validation_sprint.py`
- `scripts/tests/test_validation_prepare_interview.py`
- `scripts/tests/test_validation_sprint_dashboard.py`
- `scripts/tests/test_validation_next_action.py`
- `scripts/tests/test_validation_targets_scorecard.py`
- `scripts/tests/test_make_validation_targets.py`
- `scripts/tests/test_validation_outreach_block.py`
- `scripts/tests/test_validation_message_pack.py`
- `scripts/tests/test_validation_next_draft.py`
- `scripts/tests/test_validation_send_copy_batch.py`
- `scripts/tests/test_validation_apply_draft_update.py`
- `scripts/tests/test_validation_outreach_status.py`
- `scripts/tests/test_validation_reply_triage.py`
- `scripts/tests/test_validation_weekly_review.py`
- `scripts/tests/test_validation_target_update.py`
- `scripts/tests/test_cli_reference_docs.py`
- `scripts/tests/test_cli_safety_matrix_docs.py`
- `scripts/tests/test_agent_operating_manual.py`
- `scripts/tests/test_goal_recovery_docs.py`

Review focus:

- `workflow_pain_theme` is required so the build gate depends on repeated pain,
  not scattered enthusiasm.
- `pilot_pull_detected` must not open production build scope; only
  `build_next_slice` should.
- `build_next_slice` must be target-backed before production scope opens:
  counted interviews need matching anonymized targets in `call_booked` or
  `completed` with matching segment/persona metadata, so explicit
  untracked-interview bypass records cannot unlock the build gate by
  themselves.
- Message packs must remain private operator aids and must not include names,
  emails, phone numbers, URLs, hostnames, IPs, or raw customer artifacts.
- Weekly review reports must stay read-only: they can flag stale private
  artifacts and pruning candidates, but must not delete files or mutate
  trackers/logs. The JSON report should expose a stable `review_date` field so
  machine-readable handoffs do not have to infer the date from Markdown.
- The private prune helper should default to a dry-run plan, protect
  validation trackers/logs/templates/README files, verify `validation/private/`
  is gitignored before deletion, and require `--confirm-prune` /
  `CONFIRM_PRUNE=1` before removing generated ignored private artifacts.
- `--target-label` should render one source-aware draft without mutating private
  trackers.
- `--target-label ... --format send-text` and `make validation-draft-copy`
  should render only one copy-only subject/body without target labels, tracker
  commands, or private metadata.
- `make validation-send-copy-batch DATE=YYYY-MM-DD` should write one private
  neutral-named copy-only `.txt` file per verified pending draft, plus a
  private manifest with copy-file SHA-256 values and outbound-boundary fields,
  checklist, and README, only after generated dry-run commands still verify.
  Operators should copy file
  contents into outreach channels rather than attaching the files.
- The outreach status checker should verify pending generated dry-run commands
  without mutating private trackers, reject date-mismatched packs, and flag
  stale commands as `needs_attention`.
- The reply triage helper should accept only sanitized classifications, never
  reply text, and should emit no-write guidance plus `CONFIRM_TARGET=1`
  commands only for reviewed `book_call` and `disqualify` actions.
- The validation dashboard should surface outreach execution counts when a
  private message pack exists, without exposing message bodies or private
  recipient details. `DATE=YYYY-MM-DD` should reject message packs generated
  for another outreach day.
- `make validation-team-update DATE=YYYY-MM-DD` should print only aggregate
  validation counts and shareable next actions, with no target labels, commands,
  message bodies, or private validation paths.
- Operator-facing private validation docs should use
  `make validation-dashboard DATE=YYYY-MM-DD` or the raw
  `--require-date YYYY-MM-DD --message-pack validation/private/today-message-pack.json`
  equivalent in recovered-session workflows, so restored terminals do not
  accidentally inspect a stale message pack.
- `scripts/init-validation-sprint.py --date YYYY-MM-DD` should print recovered-
  day commands with matching `--date` / `--require-date` guards, include the
  safe `make validation-next-draft` / `make validation-apply-draft` dry-run
  outreach loop, and the private README template should mirror those guards.
- `make validation-pack` should refresh the outreach block, message pack, and
  paired outreach status JSON/Markdown together so status files cannot lag
  behind a regenerated pack.
- `make validation-status DATE=YYYY-MM-DD` should verify private outreach
  status, reject packs not generated for the requested outreach day, and expose
  the next pending target plus dry-run/confirmed-send commands at the top level
  of `today-outreach-status.json`.
- `make validation-resume DATE=YYYY-MM-DD` should run the dashboard and print
  the existing next-draft file only when it still matches the current next
  pending target, without mutating private tracker state.
- `make goal-resume DATE=YYYY-MM-DD` should remain a no-write alias for the
  same restored `/goal` recovery path.
- `make validation-next-draft` should render and write only the first pending
  draft whose generated dry-run tracker command still verifies against the
  private target tracker, and it should reject packs not dated today unless
  `DATE=YYYY-MM-DD` is supplied.
- `make validation-apply-draft TARGET=... DATE=YYYY-MM-DD` should dry-run the
  exact generated tracker update before sending or writing, reject stale packs,
  echo the dry-run, confirmed-send, status, and dashboard commands, and write
  only when `CONFIRM_SENT=1` is supplied after a real send and a matching
  copy-only send artifact is verified.
- Raw `scripts/validation-target-update.py --confirm-target` should block
  send-derived `intro_requested` / `outreach_sent` writes so post-send tracker
  changes cannot bypass
  `scripts/validation-apply-draft-update.py` and copy-only artifact
  verification.
- `make validation-reply-triage TARGET=... REPLY=... DATE=YYYY-MM-DD` should
  wrap the no-write reply helper, accept only sanitized classifications, and
  leave the private target tracker unchanged.
- Make confirmation wrappers should fail closed unless confirmation is exactly
  `1` for `CONFIRM_SENT`, `CONFIRM_TARGET`, or `CONFIRM_LOG`.
- Generated tracker commands should include `--require-current-status` guards so
  stale commands cannot move advanced targets backward.
- Reply handling should keep private details out of the target tracker; booked
  calls and disqualifications should clear follow-up dates with
  `--clear-follow-up-due`.
- Target tracking should reject malformed top-level/target dates, due follow-up
  statuses without due dates, and advanced statuses with stale follow-up dates.
- Targets should move to `completed` only after the sanitized interview log is
  updated, and completed-target commands should require the current status to be
  `call_booked`.

### 3. Buyer Pilot Packaging And Evidence Review

Purpose: make the safe local buyer pilot easier to evaluate.

Files:

- `docs/BUYER_FOLLOW_UP_PACKAGE.md`
- `docs/PILOT_RELEASE_NOTES.md`
- `docs/CONSOLE_EXPECTED_SCREENSHOTS.md`
- `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`
- `docs/OPERATOR_IDENTITY_GUIDE.md`
- `docs/SIGNED_EVIDENCE_MANIFEST_DESIGN.md`
- `docs/SIGNED_OPERATOR_APPROVAL_DESIGN.md`
- `docs/SIGNED_POLICY_DESIGN.md`
- `docs/PROPHET_COMPLETION_AUDIT.md`
- `docs/EVALUATOR_WORKSHEET.md`
- `docs/EVALUATOR_START_HERE.md`
- `docs/ASSET_IMPORT_GUIDE.md`
- `docs/PILOT_DEMO.md`
- `docs/PILOT_OUTPUT_SNIPPETS.md`
- `docs/PILOT_TROUBLESHOOTING.md`
- `docs/PILOT_POLICY_REVIEW.md`
- `docs/ANALYST_WALKTHROUGH.md`
- `docs/TECHNICAL_VALIDATION_WALKTHROUGH.md`
- `docs/DEMO_OPERATOR_CHECKLIST.md`
- `docs/GLOSSARY.md`
- `docs/INTEGRATION_HANDOFF_GUIDE.md`
- `docs/INTEGRATION_HANDOFF_REVIEW.md`
- `docs/DEFENSE_TECH_READINESS_REVIEW.md`
- `docs/PROPHET_GSTACK_ALPHA_REVIEW.md`
- `docs/SAFETY_ARCHITECTURE.md`
- `docs/THREAT_MODEL.md`
- `sandbox_runner/runner.py`
- `sandbox_runner/tests/test_runner.py`
- `scripts/tests/test_asset_import_guide_docs.py`
- `scripts/tests/test_pilot_policy_review_docs.py`
- `scripts/tests/test_signed_policy_design_docs.py`
- `scripts/tests/test_safety_architecture_docs.py`
- `scripts/tests/test_cli_no_live_targets.py`
- `evidence/bundle.py`
- `evidence/fixtures/prophet-evidence-edge-appliance.json`
- `evidence/prophet-evidence-bundle.schema.json`
- `evidence/tests/test_evidence_bundle.py`
- `integrations/export.py`
- `integrations/tests/test_export.py`

Review focus:

- Evidence claims should match the fixture-backed smoke path.
- Evidence validation should reject raw scraper/source field names and pasted
  raw-source markers.
- Safety architecture should show the raw collection zone, sanitization gate,
  allowed metadata, rejected raw/source fields, and enforcement scripts.
- Safety architecture should also include the pilot-mode threat model for
  private validation artifacts, copy-only outreach, localhost control actions,
  runtime evidence sharing, example-seed validation counts, and weekly-review
  handoffs.
- Signed policy design should stay design-only and gated on buyer/security
  review or `build_next_slice`, without keys or signing code.
- Asset import guidance should describe how to create fictional customer-safe
  fixtures without names, hosts, URLs, exact deployment details, scanner rows,
  telemetry, logs, screenshots, credentials, or payload material.
- Pilot policy review should document source terms review, customer-approved
  source allowlist notes, and future source-catalog change review without
  implying live collection approval.
- Release notes should say release-candidate notes, not a git tag.
- Signed evidence manifests remain design-only; detached signatures are still
  gated on buyer/security-review pull.
- Signed operator approvals remain design-only; signing, keys, SSO/RBAC-backed
  approval, quorum, and production push modes remain gated.
- Non-fixture sandbox modes should require a sanitized customer approval record
  before the disabled mode is considered; the public repo should still have no
  packaged container execution profile.

### 4. Console Evaluator Mode And Safe Demo Copy

Purpose: make buyer demos clearer and safer by defaulting the console toward
evaluator/demo-only language.

Files:

- `prophet-console/package.json`
- `prophet-console/playwright.screenshots.config.ts`
- `prophet-console/README.md`
- `prophet-console/control-server.mjs`
- `prophet-console/src/App.tsx`
- `prophet-console/src/components/AgentStream.tsx`
- `prophet-console/src/components/ApprovalGate.tsx`
- `prophet-console/src/components/DefencePanel.tsx`
- `prophet-console/src/components/EvidencePanel.tsx`
- `prophet-console/src/components/ExploitPanel.tsx`
- `prophet-console/src/components/ForecastPanel.tsx`
- `prophet-console/src/components/Header.tsx`
- `prophet-console/src/components/IntegrationPanel.tsx`
- `prophet-console/src/components/LabTopology.tsx`
- `prophet-console/src/components/Landing.tsx`
- `prophet-console/src/components/LiveFeedTicker.tsx`
- `prophet-console/src/components/PolicyStatusPanel.tsx`
- `prophet-console/src/components/PreflightChecklist.tsx`
- `prophet-console/src/components/RunbookDrawer.tsx`
- `prophet-console/src/components/TriageQueue.tsx`
- `prophet-console/src/data/cves.ts`
- `prophet-console/src/data/forecastIndex.ts`
- `prophet-console/src/data/mockEvents.ts`
- `prophet-console/src/data/worldSide.ts`
- `prophet-console/src/index.css`
- `prophet-console/src/lib/sanitize.ts`
- `prophet-console/tests/console.smoke.ts`
- `prophet-console/tests/console.screenshots.ts`
- `prophet-console/tests/control-evidence-smoke.mjs`
- `scripts/tests/test_console_policy_button_enablement.py`

Review focus:

- Evaluator mode should hide or soften non-demo/live-sounding controls.
- Console copy should say cached, fixture, local-control, or demo-only where
  appropriate.
- Control endpoints should remain policy-gated.
- Responsive screenshot capture should stay fixture-backed and write only to
  ignored runtime output under `evidence/outputs/runtime/console-screenshots/`.

### 5. Production Readiness And Release Hygiene

Purpose: keep the production path honest without opening production build scope.

Files:

- `docs/PRODUCTION_ARCHITECTURE.md`
- `docs/PRODUCTION_EXECUTION_PLAN.md`
- `docs/PROPHET_COMPLETION_PLAN.md`
- `docs/PROPHET_FULL_FINISH_PLAN.md`
- `docs/PROPHET_GSTACK_WORKLOG.md`
- `docs/CLI_SAFETY_MATRIX.md`
- `docs/COMPLIANCE_GAP_MAP.md`
- `docs/production-readiness-backlog.json`
- `docs/PROPHET_TODO.md`
- `docs/PROPHET_MASTER_TODO.md`
- `docs/PROPHET_FINISH_CHANGE_INVENTORY.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/SECRET_HISTORY_REVIEW.md`
- `.github/pull_request_template.md`
- `docs/OVERNIGHT_CHANGE_REPORT.md`
- `docs/OVERNIGHT_CONSOLIDATION_TODO.md`
- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `Makefile`
- `scripts/check-default-output-safety.py`
- `scripts/check-doc-links.py`
- `scripts/check-release-hygiene.sh`
- `scripts/check-secrets-archaeology.sh`
- `scripts/check-local-env.sh`
- `scripts/check-console-live-demo.sh`
- `scripts/check-console-screenshots.py`
- `scripts/prophet-overnight-gstack-loop.sh`
- `scripts/run-console-demo.sh`
- `scripts/run-worktree-smoke.sh`
- `scripts/run-pilot-demo-smoke.sh`
- `scripts/run-policy-blocked-demo.sh`
- `scripts/tests/test_check_default_output_safety.py`
- `scripts/tests/test_check_console_screenshots.py`
- `scripts/tests/test_finish_inventory_docs.py`
- `scripts/tests/test_overnight_loop_prompt.py`
- `scripts/tests/test_pilot_release_notes_docs.py`
- `scripts/tests/test_production_readiness_scorecard.py`
- `scripts/tests/test_pull_request_template_docs.py`
- `scripts/tests/test_release_checklist_docs.py`
- `scripts/tests/test_secret_history_review_docs.py`

Review focus:

- Production implementation remains gated on `build_next_slice`.
- Readiness status should reflect evidence-backed completed items only.
- Public release review should stay blocked on the historical secret-history
  owner decision until `docs/SECRET_HISTORY_REVIEW.md` has an approved path.
- The release checklist should force the validation dashboard/build-gate
  decision before any internal alpha or customer-pilot build.
- The PR template should force the same validation/build-gate decision, keep
  `pilot_pull_detected` out of production build authorization, and block
  staging private validation or runtime artifacts.
- The overnight GStack loop prompt should start from the recovered goal,
  require the dated validation dashboard or `make goal-resume`, and avoid
  production platform work while validation is `insufficient_data`.
- Historical overnight consolidation docs should point back to the current
  CEO finish brief, completion audit, TODO, and validation dashboard rather
  than acting as current production authorization.
- `make help` should keep the restored-session path explicit: run the dated
  validation dashboard first, then send the existing copy-only file only when
  `next_draft_exists=true` and it matches the current next pending
  target/date/status/body.
- The pilot smoke should scan policy-listed default outputs for live-target URL
  fields while allowing public source citations, and should verify
  policy-listed OSINT snapshot provenance manifests.
- Pilot release tag remains blocked until the historical secret-history finding
  has an owner decision. A true GitHub fresh clone of the PR branch at
  `6fe55f3` passed on macOS with 26 verified pilot hashes. The GitHub Actions
  `python` job runs on `ubuntu-latest` and now names the Linux fresh-clone pilot
  smoke steps. Rerun true macOS fresh-clone smoke after any further commit
  before merge or release decisions. PR checks are green on the pushed head, but
  must be rechecked before merge or release decisions.
- `make worktree-smoke` should remain a local pre-commit release-hygiene check:
  it may clone HEAD to `/tmp`, overlay non-ignored dirty files, and run the safe
  root smoke, but must not copy `validation/private/`, stage, commit, push, tag,
  or run production platform work.
- `make release-hygiene` should remain read-only: it may run whitespace checks,
  release-safety scans, current-worktree secret scanning, policy lint,
  default-output URL/provenance safety, and local Markdown link checking, but
  must not stage, commit, push, tag, delete files, or copy ignored private
  validation artifacts.
- `make secrets-archaeology` runs the full current-worktree plus git-history secret
  scan and currently flags historical `LOG4SHELL_INSTRUCTIONS.md`
  password-like content that needs cleanup, rotation, or an explicit exception
  before public release.
- `make console-screenshot-check` should remain a local screenshot-sharing
  verifier: it may check ignored screenshot paths, PNG hashes, PNG dimensions,
  and fixture-backed sharing boundaries, but must not stage or copy generated
  screenshots.

## Ignored Private Validation Outputs

These files are generated for local operation and are intentionally ignored by
`.gitignore`:

- `validation/private/README.md`
- `validation/private/NEXT_ACTION.md`
- `validation/private/customer-validation-log.json`
- `validation/private/customer-validation-interview.template.json`
- `validation/private/customer-validation-interview-next.json`
- `validation/private/validation-targets.json`
- `validation/private/today-outreach-block.json`
- `validation/private/today-outreach-block.md`
- `validation/private/today-message-pack.json`
- `validation/private/today-message-pack.md`
- `validation/private/today-next-draft.md`
- `validation/private/today-send-copy.txt`
- `validation/private/today-outreach-status.json`
- `validation/private/today-outreach-status.md`
- `validation/private/today-team-update.md`
- `validation/private/today-weekly-review.json`
- `validation/private/today-weekly-review.md`
- `validation/private/send-copy-2026-05-10/`
- `validation/private/send-copy-2026-05-10/README.md`
- `validation/private/send-copy-2026-05-10/CHECKLIST.md`
- `validation/private/send-copy-2026-05-11/`
- `validation/private/send-copy-2026-05-11/README.md`
- `validation/private/send-copy-2026-05-11/CHECKLIST.md`
- `validation/private/send-copy-2026-05-11/COPY_ONLY_INDEX.md`
- `validation/private/send-copy-2026-05-11/SUBJECT_ORDER.md`

Do not commit private validation files. Export only aggregate counts or
sanitized examples.

## Verification Snapshot

Latest verification run for this inventory:

- `python3 -m unittest discover -s scripts/tests -v`: 365 tests passed after
  the send-boundary dashboard, copy-only resume boundary, CLI-reference,
  validation-resume, goal-resume, validation-team-update, validation-weekly-review,
  validation-next-action handoff generation, weekly-review `review_date`,
  weekly-review target-backed build-gate coverage, outreach execution,
  and date-mismatch coverage,
  raw apply-draft confirmed-write copy-artifact guard coverage,
  raw target-update direct `intro_requested` / `outreach_sent` confirmed-write rejection,
  raw target-update completed-call validation-log guard coverage,
  target-backed build-gate and segment/persona metadata-match coverage,
  guarded log append segment/persona metadata-match and CLI help coverage,
  CLI-safety-matrix coverage for that guard,
  policy-signing design guardrail,
  reply-triage helper and Make wrapper guardrails,
  release-checklist validation-gate and pre-commit hook guard,
  overnight-loop validation-gate guard, overnight historical-doc guard,
  default-output URL safety, raw-to-sanitized boundary
  docs, customer-safe fixture-generation docs, exposure-classification guide
  docs, source-governance policy review, and OSINT provenance manifest check
  updates, including goal-recovery docs,
  policy-bound console button enablement coverage,
  coverage, current-resume-source coverage, validation operator recovery docs
  coverage, weekly-review guardrail/report coverage, operational TODO
  private-artifact pruning coverage, finish-inventory commit-splitting coverage,
  release-hygiene evidence coverage, dirty-worktree inventory coverage,
  aggregate-only team update coverage, PR template gate/private-artifact
  coverage, changelog gate/review-guardrail coverage, copy-only send-text CLI
  leakage coverage,
  base send-text outbound-copy leak rejection,
  single-send outbound-copy leak rejection, copy-only send-batch coverage,
  send-copy batch checklist coverage,
  send-copy batch outbound-copy leak rejection,
  send-copy metadata staleness rejection,
  send-copy batch dashboard ready/stale/hash/boundary coverage,
  confirmed-send copy-artifact guard coverage,
  no-write reply triage command coverage,
  target-specific copy-only draft coverage,
  atomic saved-update failure coverage, private README inventory coverage,
  booked-target log-append guard coverage,
  example-seed replacement coverage,
  replace-seed target-status guard coverage,
  matching validation-log completion guard coverage, raw confirmed-log target
  guard coverage, explicit untracked-interview bypass coverage, untracked-count
  docs coverage, ignored private validation output scan coverage, one-terminal
  console-demo help/dependency/runtime port-conflict/non-localhost-host docs
  coverage,
  release-checklist console-demo and python-tests wrapper coverage, pilot-release-note runnable-product
  coverage, worktree-smoke wrapper coverage, all-Python Make wrapper coverage,
  same-target wrong-date next-draft rejection, example-seed build-gate
  coverage, running-console live-check coverage, and console screenshot
  manifest verification coverage.
- `make python-tests`: passed on 2026-05-11 as the release-hygiene wrapper for
  scripts, cyber-side, world-side, assets, sandbox runner, policy, evidence,
  and integration Python suites.
- `make goal-resume DATE=YYYY-MM-DD` now aliases the same no-write recovered
  `/goal` path as `make validation-resume DATE=YYYY-MM-DD`.
- `make validation-resume DATE=YYYY-MM-DD` and `make goal-resume
  DATE=YYYY-MM-DD` wrap pasteable outbound copy in `BEGIN COPY-ONLY SEND TEXT`
  / `END COPY-ONLY SEND TEXT`, then print `DO NOT SEND BELOW THIS LINE` before
  tracker/audit metadata.
- `scripts/init-validation-sprint.py --date YYYY-MM-DD --refresh-readme` now
  refreshes the ignored private operator README with the same copy-only resume
  boundary guidance without overwriting private tracker/log files.
- `make validation-team-update DATE=YYYY-MM-DD` and
  `make validation-team-update-save DATE=YYYY-MM-DD` now include aggregate
  send-copy readiness and match state, without target labels, commands, paths,
  or message bodies.
- `make validation-send-copy DATE=2026-05-11` passed and wrote
  `validation/private/today-send-copy.txt` for the verified next draft as one
  subject line plus the message body, without target labels, tracker commands,
  alternate subject options, or status metadata.
- `make validation-send-copy-batch DATE=2026-05-11` is covered by focused
  tests and writes one private neutral-named copy-only `.txt` file per verified
  pending draft under `validation/private/send-copy-2026-05-11/`, plus a
  private manifest with copy-file SHA-256 values and outbound-boundary fields,
  checklist, README, neutral `COPY_ONLY_INDEX.md` that omits target labels
  and tracker commands, and private `SUBJECT_ORDER.md`.
- `make validation-dashboard DATE=2026-05-11` verifies the generated batch
  directory through `send_copy_batch_state: ready`,
  `send_copy_batch_matches_current_pack: true`,
  `send_copy_batch_readme_exists: true`,
  `send_copy_batch_checklist_exists: true`,
  `send_copy_batch_copy_index_exists: true`,
  `send_copy_batch_subject_order_exists: true`, and 8 copy files.
  The dashboard now checks copy-file SHA-256 values, manifest outbound-boundary
  fields, batch README body, batch checklist body, neutral copy-index body,
  subject-order body, and
  manifest operator notes, not only file existence.
- Direct outbound copy checks found no target labels, validation commands,
  tracker commands, manifest/checklist references, or confirmation commands in
  the 8 numbered `.txt` files or `validation/private/today-send-copy.txt`; each
  outbound `.txt` file contains exactly one `Subject:` line.
- `make validation-send-copy-check DATE=2026-05-11` verifies the existing
  send-copy batch without rewriting it, including neutral filenames, one
  `Subject:` line per file, copy-file SHA-256 matches, no target labels or
  tracker metadata in numbered `.txt` files, and exact README/checklist/copy
  index match against the current manifest-derived send order.
- `docs/PROPHET_COMPLETION_AUDIT.md` now lists the batch directory as a current
  copy-only send option and keeps the batch manifest with copy-file SHA-256
  values and outbound-boundary fields below the outbound boundary as private
  tracker/audit metadata alongside the batch checklist and batch README.
- Ignored private validation outputs passed release-safety scanning over 40
  paths and no-index whitespace checks, including the current next draft,
  copy-only send text, message pack, outreach status, aggregate-only team
  update, and weekly review report.
- `make validation-weekly-review DATE=2026-05-11` passed after the weekly
  review JSON handoff fix; its private artifact count now ignores atomic
  `.tmp.` handoff files and `validation/private/today-weekly-review.json`
  reports `review_date: 2026-05-11`, `generated_for: 2026-05-11`,
  `outreach_execution.state: ready`, `private_artifacts.file_count: 40`, and
  `private_artifacts.stale_file_count: 0`.
- `make validation-prune-private DATE=2026-05-11` passed as a dry run and
  reported one eligible generated ignored private artifact candidate,
  `validation/private/send-copy-2026-05-10/`, without deleting anything.
  Confirmed pruning remains gated on `CONFIRM_PRUNE=1` after operator review.
- Product validation plan docs coverage verifies that `pilot_pull_detected` is
  a design-partner conversion signal and only `build_next_slice` opens the
  production build gate.
- `PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v`:
  62 tests passed after adding raw scraper/source field and marker rejection to
  the evidence bundle validator, making the Markdown Forecast section surface
  selected window rationale, vector rationale, and cited forecast source IDs,
  requiring `forecast_summary.vector.why_this_vector` in the published
  evidence schema, and carrying sandbox run-manifest provenance into the
  evidence bundle with mismatch rejection.
- `./scripts/check-local-env.sh`: passed on local Python 3.9.6, Node v25.5.0,
  bash, git, shasum, and npm.
- `./scripts/run-pilot-demo-smoke.sh`: passed in 1s on 2026-05-10 after the
  handoff checklist, customer-placeholder validation, review-ZIP packaging, and
  default-output URL safety updates; rerun after the evidence forecast-rationale
  Markdown and sandbox-provenance update and verified 26 pilot demo hashes against
  `scripts/pilot-demo-smoke.sha256`, checked default-output URLs, and checked
  1 OSINT provenance manifest.
- `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`: passed in 2s
  on 2026-05-10 after the review-ZIP packaging and sandbox-provenance update;
  verified 26 pilot demo hashes against
  `scripts/pilot-demo-smoke-financial-workflow.sha256`.
- `make worktree-smoke`: passed on 2026-05-11 after overlaying 0
  non-ignored dirty files into a temporary clone from the local commit set,
  running
  `./scripts/check-local-env.sh`, and passing the default smoke with 26
  verified hashes.
- `make console-demo`: running in a detached local `screen` session on
  `http://127.0.0.1:5291/` with control readiness at
  `http://127.0.0.1:8891/api/readiness`; readiness returned `ok: true` and
  `blockingFailures: 0`.
- `cd prophet-console && npm run acceptance`: passed, including root pilot
  smoke, console lint/build, control evidence smoke, and 5 Playwright tests.
- `cd prophet-console && npm audit --audit-level=moderate`: passed with 0
  vulnerabilities.
- `cd prophet-console && npm run capture:screenshots`: passed and generated 6
  fixture-backed desktop/mobile evaluator screenshots plus
  `evidence/outputs/runtime/console-screenshots/manifest.json` under ignored
  runtime output. The manifest records the fixture-backed/no-customer-system
  boundary, and the screenshot test rejects live-target text, credentials,
  payload markers, and auto-deploy wording in rendered UI text.
- `make console-screenshot-check`: passed against the generated screenshot
  manifest, verifying ignored runtime paths, PNG hashes, PNG dimensions, and
  fixture-backed sharing boundary before any screenshot sharing.
- Manual `GET /api/readiness`: passed with `ok: true` and 0 blocking failures
  against the current pilot runtime outputs.
- `docs/PILOT_SCOPE.md`: buyer review criteria now state the pass/fail
  standard for validating the pilot without opening production scope.
- `docs/RELEASE_CHECKLIST.md`: local demo rollback now regenerates ignored
  runtime outputs instead of using destructive git commands, and the release
  checklist now forces the private validation dashboard/build-gate decision
  before internal alpha or customer-pilot builds.
- `CHANGELOG.md`: unreleased buyer pilot package entry records the closed build
  gate, validation sprint status, safety boundary, known blockers, and
  verification references.
- `README.md`: repository map now covers the top-level pilot, validation,
  policy, console, evidence, integration, and ignored private-validation
  surfaces.
- `Makefile`: safe root wrappers now cover pilot readiness preflight, full
  pilot readiness with console acceptance/audit, pilot smoke, worktree-overlay
  smoke, release hygiene, console acceptance and audit, one-terminal console
  demo launch, running-console live checks, console control server, console evaluator UI, validation
  pack/status/dashboard/resume, next-draft and target-specific draft rendering,
  script tests, and release-safety scans
  without adding deploy, tag, stage, or production targets. `make help` now
  points restored operators to the dashboard-first send boundary before
  touching tracker state.
- `git diff --check`: passed.
- `git diff --name-status`: no deleted tracked files.
- `git ls-files --deleted`: no deleted tracked files.
- `make pilot-ready-check DATE=2026-05-11`: passed, including local environment
  check, default buyer pilot smoke, dated validation dashboard, production
  readiness summary, and release-safety diff scan.
- `make pilot-ready-check-full DATE=2026-05-11`: passed at PR head `6fe55f3`
  at verification time, including the same readiness preflight, console
  lint/build, control evidence smoke, 5 Playwright tests, and console
  dependency audit.
- `make worktree-smoke`: local wrapper added for repeatable dirty-worktree
  overlay smoke. It clones HEAD to `/tmp`, overlays current non-ignored dirty
  files, excludes ignored private validation files, then runs
  `./scripts/check-local-env.sh` and `./scripts/run-pilot-demo-smoke.sh`.
- `./scripts/run-worktree-smoke.sh`: passed on 2026-05-11. It overlayed 0
  non-ignored dirty files, copied no ignored `validation/private/` artifacts,
  applied 0 tracked deletions, and the temp-clone smoke passed with 26 verified
  hashes.
- `make release-hygiene`: read-only wrapper added for tracked/untracked
  whitespace checks, release-safety scans, tracked path policy-hash coverage,
  staged safety, current-worktree secret scanning, policy lint, default-output
  URL/provenance safety, and local Markdown link checking.
- `PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 timeout 25 ./scripts/run-console-demo.sh`:
  started the localhost-only control API and evaluator UI on alternate ports,
  printed both local URLs, and stopped both processes when the timed run ended.
- Live console endpoints on `5291` / `8891` were rechecked after patching the
  audit append path. `POST /api/evidence/demo-bundle` returned
  `evidence_bundle_generated`; `POST /api/integrations/demo-export` returned
  `integration_handoff_exported`; both audit events included
  `safety_attestation.no_live_target_data_included: true`. The local
  `evidence/outputs/runtime/operator-audit-log.jsonl` then validated with two
  hash-chained events.
- `PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 make console-live-check`:
  passed against the running local demo, including UI reachability, readiness,
  evidence generation, integration export, safety attestation checks, and
  audit-log validation.
- `./scripts/run-console-demo.sh` against already-running default ports now
  fails before spawning children with a clean `CONTROL port 8787 is already in
  use` message and an alternate-port hint.
- `PROPHET_CONSOLE_HOST=0.0.0.0 ./scripts/run-console-demo.sh` now fails
  before dependency checks or child spawning with a localhost-only host error.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff`:
  passed over 0 paths in the clean committed worktree.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --tracked --paths-only`:
  passed over 347 tracked paths, including release-bound policy-hash coverage
  checks.
- `python3 -m policy.lint --policy policy/prophet-pilot-policy.json`:
  passed and reported policy ID `prophet-pilot-fixture-localhost-v0.1` with
  `live_targets_allowed`, `payload_generation_allowed`,
  `credentials_allowed`, `private_hostnames_allowed`, and
  `raw_scraper_text_allowed` all false.
- `python3 scripts/check-default-output-safety.py --policy policy/prophet-pilot-policy.json --format text`:
  passed over 7 policy-listed default outputs and 1 OSINT provenance manifest.
- `python3 scripts/check-doc-links.py`: passed over 86 Markdown source files
  with external URLs and ignored private/runtime output skipped.
- Explicit untracked file checks: no-index whitespace checks passed over 0
  untracked non-ignored files, and release hygiene reported no untracked
  non-ignored files to scan.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --staged`: passed with 0 staged paths.
- `python3 scripts/validation-sprint-dashboard.py`: `insufficient_data`,
  `allowed_to_build_next_slice: false`, 8 verified outreach drafts pending,
  0 outreach items needing attention.
- `make validation-pack DATE=2026-05-11`: passed and refreshed paired private
  outreach block, message pack, and outreach status JSON/Markdown files.
- `make validation-next-draft DATE=2026-05-11`: passed and wrote
  `validation/private/today-next-draft.md` for `target-dib-platform-001`.
- `make validation-apply-draft TARGET=target-dib-platform-001 DATE=2026-05-11`:
  passed as a dry run without writing. The generated update would move
  `target-dib-platform-001` from `identified` to `outreach_sent`, set
  `last_touch` to `2026-05-11`, set `follow_up_due` to `2026-05-14`, and set
  `next_action` to `Send follow-up if no reply.`.
- `make validation-status DATE=2026-05-11`: passed with 8 pending send/update
  items, 8 dry-run verified tracker updates, and 0 attention errors.
- `make validation-dashboard DATE=2026-05-11`: passed with
  `insufficient_data`, `allowed_to_build_next_slice: false`, and the next
  pending target `target-dib-platform-001`; dashboard JSON now includes
  `send_copy_path`, `send_copy_command`, `send_copy_state`, and
  `send_copy_matches_next_pending`, plus `send_copy_batch_dir`,
  `send_copy_batch_state`, `send_copy_batch_readme_exists`,
  `send_copy_batch_checklist_exists`, `send_copy_batch_copy_index_exists`, and
  `send_copy_batch_subject_order_exists`, and
  `send_copy_batch_matches_current_pack`.
- Generated message pack, next-draft, send-copy, outreach-status, and dashboard
  next-action text now instruct operators to run the dry-run tracker update
  before sending or writing, send copy-only text outside the repo only after
  that dry-run passes, then use `CONFIRM_SENT=1` only after the actual send is
  confirmed. When `validation/private/today-next-draft.md` already exists, the
  dashboard reports `next_draft_exists: true` plus
  `next_draft_matches_next_pending`; it tells the operator to use
  `validation/private/today-send-copy.txt` only when both the tracker/audit
  draft and copy-only send body still match the current next pending
  target/date/status/body, otherwise it tells the operator to refresh the stale
  artifact.
- Private validation recovery docs now use date-guarded dashboard commands in
  operator workflows: `AGENTS.md`, `README.md`,
  `docs/VALIDATION_DAILY_BRIEF.md`, `docs/VALIDATION_SPRINT_CHECKLIST.md`,
  `docs/CLI_REFERENCE.md`, and `docs/PRODUCT_VALIDATION_PLAN.md`.
- `scripts/init-validation-sprint.py --date YYYY-MM-DD` now prints the
  same-date `make validation-dashboard DATE=YYYY-MM-DD` command before the
  same-date `make validation-next-draft DATE=YYYY-MM-DD` command, and the
  ignored private README
  mirrors that dashboard-first restored-session flow. `--refresh-readme`
  rewrites only that ignored private README without overwriting private
  tracker/log files; `make validation-init DATE=YYYY-MM-DD REFRESH_README=1`
  wraps the same safe refresh path.
- `docs/PROPHET_MASTER_TODO.md`: Day 1 through Day 6 of the 7-day execution
  plan are reconciled against actual evidence and marked complete. Day 7
  remains partial because fresh-clone smoke is covered, but release packaging
  and tagging remain blocked by the historical secret-history owner decision
  and unproven buyer demand.
- `python3 scripts/production-readiness-scorecard.py`: readiness `26.7%`,
  29 critical open items.

## PR Handoff Draft

Use this as a starting point if the user asks to open a PR. Do not paste
private validation files, message bodies, target names, contact details, or
runtime output contents into the PR.

```markdown
## Summary

- Reframes Prophet as a policy-bound defensive exposure evidence workflow for
  buyer validation.
- Adds guarded validation-sprint tooling for private outreach, source-aware
  message packs, copy-only send artifacts, reply triage, target updates,
  interview logging, weekly review, and dashboard-first recovery after a lost
  `/goal` session.
- Hardens the local buyer pilot with policy/hash checks, evidence rationale,
  sandbox provenance, review-only SIEM/ticket handoffs, deterministic review
  ZIPs, console readiness/download paths, and release-hygiene wrappers.

## Validation Gate

- Customer validation verdict: `insufficient_data`.
- Target-backed validation verdict: `insufficient_data`.
- `allowed_to_build_next_slice`: `false`.
- Current outreach pack: 8 pending send/update items, 0 needing attention,
  8 dry-run verified.
- Next operator action: send copy-only private outreach for
  `target-dib-platform-001`, then run the generated dry-run tracker update
  before any confirmed private tracker write.
- This PR does not add production platform scope. `pilot_pull_detected` remains
  a design-partner conversion signal; only `build_next_slice` opens production
  platform work.

## Safety Boundary

- No live targets, payload generation, credentials, raw scraper text, private
  hostnames, production pushes, or autonomous remediation.
- Integration outputs remain review templates.
- Do not stage `validation/private/`, runtime outputs, private buyer notes,
  send-copy files, or raw outreach artifacts.

## Verification

- `make pilot-ready-check-full DATE=2026-05-11` passed at PR head `6fe55f3`
  at verification time.
- `make python-tests` passed.
- `make release-hygiene` passed.
- `make console-live-check` passed against the running local demo.
- `make console-screenshot-check` passed against the generated screenshot
  manifest.
- Manual local checks returned `http://127.0.0.1:5173/` HTTP 200 and
  `http://127.0.0.1:8787/api/readiness` with `ok: true` and no blocking
  failures.
- Manual live console evidence and integration endpoint checks also passed
  on the alternate local control endpoint `http://127.0.0.1:8891`.
- `make worktree-smoke` passed after overlaying 0 non-ignored dirty files from
  the clean local commit set and copying no ignored private validation artifacts.
- `git diff --check` passed.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff`
  passed over 0 paths in the clean committed worktree.
- `make secrets-archaeology` is the remaining public-release security review
  blocker: current-worktree scanning passes, but full git-history scanning
  flags historical `LOG4SHELL_INSTRUCTIONS.md` password-like content in 3
  commits. Use `docs/SECRET_HISTORY_REVIEW.md` and do not paste the matched
  values into GitHub.

## Known Blockers

- Real buyer demand remains unproven.
- Production readiness remains 26.7% with 29 critical open items.
- Full git-history secret archaeology remains unresolved; rotate/clean/except
  the historical `LOG4SHELL_INSTRUCTIONS.md` finding before public release.
- Release tag remains blocked until the historical secret-history finding has
  an owner decision. True GitHub fresh-clone smoke passed on macOS; exact-head
  evidence belongs in the PR verification notes because documentation commits
  can move the branch head, and the check should be rerun after any further
  commit before merge or release decisions.
  Linux fresh-clone smoke is covered by the Ubuntu CI pilot smoke steps.
- PR `#5` has the finish-pass commits pushed and checks are green on the
  current pushed head, and is ready for internal buyer-pilot review; verify
  `gh pr checks 5` again before merge or release decisions.
```

Before any commit or PR, rerun the relevant console acceptance, pilot smoke,
release-safety, and validation dashboard checks for the exact staged diff.
