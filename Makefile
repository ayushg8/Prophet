PYTHONPATH_SAFE ?= .:cyber-side:world-side
VALIDATION_DIR ?= validation/private
VALIDATION_TARGETS ?= $(VALIDATION_DIR)/validation-targets.json
VALIDATION_LOG ?= $(VALIDATION_DIR)/customer-validation-log.json
VALIDATION_BLOCK_JSON ?= $(VALIDATION_DIR)/today-outreach-block.json
VALIDATION_BLOCK_MD ?= $(VALIDATION_DIR)/today-outreach-block.md
VALIDATION_MESSAGE_PACK_JSON ?= $(VALIDATION_DIR)/today-message-pack.json
VALIDATION_MESSAGE_PACK_MD ?= $(VALIDATION_DIR)/today-message-pack.md
VALIDATION_NEXT_DRAFT_MD ?= $(VALIDATION_DIR)/today-next-draft.md
VALIDATION_SEND_COPY_TXT ?= $(VALIDATION_DIR)/today-send-copy.txt
VALIDATION_SEND_COPY_DIR ?= $(VALIDATION_DIR)/send-copy-$(VALIDATION_RUN_DATE)
VALIDATION_SEND_COPY_BATCH_MANIFEST_JSON ?= $(VALIDATION_SEND_COPY_DIR)/manifest.json
VALIDATION_STATUS_JSON ?= $(VALIDATION_DIR)/today-outreach-status.json
VALIDATION_STATUS_MD ?= $(VALIDATION_DIR)/today-outreach-status.md
VALIDATION_TEAM_UPDATE_MD ?= $(VALIDATION_DIR)/today-team-update.md
VALIDATION_WEEKLY_REVIEW_JSON ?= $(VALIDATION_DIR)/today-weekly-review.json
VALIDATION_WEEKLY_REVIEW_MD ?= $(VALIDATION_DIR)/today-weekly-review.md
VALIDATION_NEXT_ACTION_MD ?= $(VALIDATION_DIR)/NEXT_ACTION.md
VALIDATION_INTERVIEW_JSON ?= $(if $(INTERVIEW),$(INTERVIEW),$(VALIDATION_DIR)/customer-validation-interview-next.json)
VALIDATION_RUN_DATE ?= $(if $(DATE),$(DATE),$(shell date +%F))
DATE_ARG := $(if $(DATE),--date $(DATE),)
REQUIRE_DATE_ARG := --require-date $(VALIDATION_RUN_DATE)
CONFIRM_SENT_VALUE := $(strip $(CONFIRM_SENT))
CONFIRM_TARGET_VALUE := $(strip $(CONFIRM_TARGET))
CONFIRM_LOG_VALUE := $(strip $(CONFIRM_LOG))
CONFIRM_PRUNE_VALUE := $(strip $(CONFIRM_PRUNE))
REPLACE_EXAMPLE_SEED_VALUE := $(strip $(REPLACE_EXAMPLE_SEED))
REFRESH_README_VALUE := $(strip $(REFRESH_README))
CONFIRM_SENT_ARG = $(if $(CONFIRM_SENT_VALUE),$(if $(filter-out 1,$(CONFIRM_SENT_VALUE)),$(error CONFIRM_SENT must be 1 when set),--confirm-sent),)
CONFIRM_SENT_COPY_ARG = $(if $(CONFIRM_SENT_VALUE),--require-copy-artifact --send-copy $(VALIDATION_SEND_COPY_TXT) --send-copy-batch-manifest $(VALIDATION_SEND_COPY_BATCH_MANIFEST_JSON),)
CONFIRM_TARGET_ARG = $(if $(CONFIRM_TARGET_VALUE),$(if $(filter-out 1,$(CONFIRM_TARGET_VALUE)),$(error CONFIRM_TARGET must be 1 when set),--confirm-target),--dry-run)
CONFIRM_LOG_ARG = $(if $(CONFIRM_LOG_VALUE),$(if $(filter-out 1,$(CONFIRM_LOG_VALUE)),$(error CONFIRM_LOG must be 1 when set),--confirm-log),)
CONFIRM_PRUNE_ARG = $(if $(CONFIRM_PRUNE_VALUE),$(if $(filter-out 1,$(CONFIRM_PRUNE_VALUE)),$(error CONFIRM_PRUNE must be 1 when set),--confirm-prune),)
REPLACE_EXAMPLE_SEED_ARG = $(if $(REPLACE_EXAMPLE_SEED_VALUE),$(if $(filter-out 1,$(REPLACE_EXAMPLE_SEED_VALUE)),$(error REPLACE_EXAMPLE_SEED must be 1 when set),--replace-example-seed),)
REFRESH_README_ARG = $(if $(REFRESH_README_VALUE),$(if $(filter-out 1,$(REFRESH_README_VALUE)),$(error REFRESH_README must be 1 when set),--refresh-readme),)

.PHONY: help
help:
	@printf '%s\n' \
		'Prophet operator targets:' \
		'  make check-local-env         Check local pilot prerequisites.' \
		'  make pilot-ready-check       Run env, smoke, validation dashboard, readiness, and release-safety.' \
		'  make pilot-ready-check-full  Run pilot-ready-check plus console acceptance and audit.' \
		'  make worktree-smoke          Temp-clone HEAD, overlay dirty non-ignored files, and run safe smoke.' \
		'  make pilot-smoke              Run the default buyer pilot smoke.' \
		'  make pilot-smoke-clean        Regenerate ignored runtime smoke outputs.' \
		'  make console-acceptance       Run console acceptance from prophet-console/.' \
		'  make console-audit            Run npm audit for the console.' \
		'  make console-demo             Start control server and evaluator UI in one local terminal; Ctrl-C to stop.' \
		'  make console-live-check       Check running local console readiness, evidence, integration, and audit endpoints.' \
		'  make console-screenshot-check Verify generated console screenshot manifest hashes, dimensions, and ignored paths.' \
		'  make console-control          Run the local console control server; Ctrl-C to stop.' \
		'  make console-ui               Run the evaluator console UI; start console-control first.' \
		'  make scripts-test             Run scripts unit tests.' \
		'  make python-tests             Run all Python unit suites for pilot/release verification.' \
		'  make validation-init          Initialize ignored private validation files; optional DATE=YYYY-MM-DD, REFRESH_README=1.' \
		'  make validation-pack          Generate outreach block, message pack, and status; optional DATE=YYYY-MM-DD.' \
		'  make validation-next-draft    Render/write next verified draft; rejects packs not dated today unless DATE=YYYY-MM-DD.' \
		'  make validation-send-copy     Render/write copy-only next draft text without tracker metadata; optional DATE=YYYY-MM-DD.' \
		'  make validation-send-copy-batch Write copy-only text files for all verified pending drafts; optional DATE=YYYY-MM-DD.' \
		'  make validation-send-copy-check Verify existing batch copy files are outbound-only; optional DATE=YYYY-MM-DD.' \
		'  make validation-draft         Render one draft; requires TARGET=target-label, rejects packs not dated today unless DATE=YYYY-MM-DD.' \
		'  make validation-draft-copy    Print copy-only text for one target; requires TARGET=target-label, optional DATE=YYYY-MM-DD.' \
		'  make validation-apply-draft   Dry-run/apply tracker update; requires TARGET=target-label, optional DATE=YYYY-MM-DD, CONFIRM_SENT=1 after actual send.' \
		'  make validation-reply-triage  No-write reply triage; requires TARGET=target-label, REPLY=book_call|disqualify|keep_pending|manual_review, optional DATE=YYYY-MM-DD.' \
		'  make validation-book-call     Dry-run/mark a replied target call_booked; requires TARGET=target-label, optional DATE=YYYY-MM-DD, CONFIRM_TARGET=1.' \
		'  make validation-disqualify-target Dry-run/disqualify a target; requires TARGET=target-label, optional DATE=YYYY-MM-DD, CONFIRM_TARGET=1.' \
		'  make validation-prepare-interview Write incomplete private interview starter for a booked target; requires TARGET=target-label, optional DATE=YYYY-MM-DD.' \
		'  make validation-complete-call Dry-run/mark completed after matching sanitized interview log; requires TARGET=target-label, optional DATE=YYYY-MM-DD, CONFIRM_TARGET=1.' \
		'  make validation-log-interview Validate/log sanitized interview for booked target; optional INTERVIEW=path, DATE=YYYY-MM-DD, REPLACE_EXAMPLE_SEED=1 for first real interview, CONFIRM_LOG=1.' \
		'  make validation-status        Print Markdown status and write next-target JSON; rejects packs not dated today unless DATE=YYYY-MM-DD.' \
		'  make validation-dashboard     Run dashboard; rejects packs not dated today unless DATE=YYYY-MM-DD.' \
		'  make validation-team-update  Print sanitized aggregate-only validation update; optional DATE=YYYY-MM-DD.' \
		'  make validation-team-update-save Write sanitized aggregate-only update under validation/private/; optional DATE=YYYY-MM-DD.' \
		'  make validation-next-action-save Write regenerated private NEXT_ACTION.md handoff; optional DATE=YYYY-MM-DD.' \
		'  make validation-weekly-review Write read-only private weekly review report; optional DATE=YYYY-MM-DD.' \
		'  make validation-prune-private Dry-run pruning of generated ignored private artifacts; optional DATE=YYYY-MM-DD, CONFIRM_PRUNE=1 after review.' \
		'  make validation-resume        Run dashboard and print existing next draft when present; optional DATE=YYYY-MM-DD.' \
		'  make goal-resume              Alias for validation-resume after a lost /goal session; optional DATE=YYYY-MM-DD.' \
		'  Restore path: run make validation-dashboard DATE=YYYY-MM-DD first; use today-send-copy.txt for outbound text only after today-next-draft.md matches the next pending target/date/status/body.' \
		'  After a restored/crashed session, pass DATE=YYYY-MM-DD explicitly if the shell date is not the outreach date.' \
		'  make release-hygiene          Run read-only whitespace, safety, current-secret, policy, and default-output checks.' \
		'  make secrets-archaeology      Run full read-only current + git-history secret scan.' \
		'  make release-safety           Run release safety over the current diff.' \
		'  make release-safety-staged    Run release safety over staged paths.'

.PHONY: check-local-env
check-local-env:
	@./scripts/check-local-env.sh

.PHONY: pilot-smoke
pilot-smoke:
	@./scripts/run-pilot-demo-smoke.sh

.PHONY: pilot-smoke-clean
pilot-smoke-clean:
	@./scripts/run-pilot-demo-smoke.sh --clean-runtime --yes
	@shasum -a 256 -c scripts/pilot-demo-smoke.sha256 --quiet

.PHONY: pilot-ready-check
pilot-ready-check:
	@printf '%s\n' '[1/5] Checking local environment'
	@./scripts/check-local-env.sh
	@printf '%s\n' '[2/5] Running default buyer pilot smoke'
	@./scripts/run-pilot-demo-smoke.sh
	@printf '%s\n' '[3/5] Checking validation dashboard and build gate'
	@python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--format text
	@printf '%s\n' '[4/5] Checking production readiness summary'
	@python3 scripts/production-readiness-scorecard.py | python3 -c 'import json, sys; data = json.load(sys.stdin); print("Production readiness: {}% ({} critical open item(s))".format(data["readiness_percent"], data["critical_open_count"]))'
	@printf '%s\n' '[5/5] Running release safety over current diff'
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 scripts/check-release-safety.py --diff

.PHONY: pilot-ready-check-full
pilot-ready-check-full:
	@$(MAKE) --no-print-directory pilot-ready-check DATE=$(VALIDATION_RUN_DATE)
	@printf '%s\n' '[6/7] Running console acceptance'
	@$(MAKE) --no-print-directory console-acceptance
	@printf '%s\n' '[7/7] Running console dependency audit'
	@$(MAKE) --no-print-directory console-audit

.PHONY: worktree-smoke
worktree-smoke:
	@./scripts/run-worktree-smoke.sh

.PHONY: console-acceptance
console-acceptance:
	@cd prophet-console && npm run acceptance

.PHONY: console-audit
console-audit:
	@cd prophet-console && npm audit --audit-level=moderate

.PHONY: console-demo
console-demo:
	@./scripts/run-console-demo.sh

.PHONY: console-live-check
console-live-check:
	@./scripts/check-console-live-demo.sh

.PHONY: console-screenshot-check
console-screenshot-check:
	@python3 scripts/check-console-screenshots.py --format text

.PHONY: console-control
console-control:
	@cd prophet-console && npm run dev:control

.PHONY: console-ui
console-ui:
	@cd prophet-console && npm run dev:evaluator

.PHONY: scripts-test
scripts-test:
	@python3 -m unittest discover -s scripts/tests -v

.PHONY: python-tests
python-tests:
	@printf '%s\n' '[1/8] Running scripts tests'
	@python3 -m unittest discover -s scripts/tests -v
	@printf '%s\n' '[2/8] Running cyber-side tests'
	@PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
	@printf '%s\n' '[3/8] Running world-side tests'
	@PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
	@printf '%s\n' '[4/8] Running asset tests'
	@PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
	@printf '%s\n' '[5/8] Running sandbox runner tests'
	@PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
	@printf '%s\n' '[6/8] Running policy tests'
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 -m unittest discover -s policy/tests -v
	@printf '%s\n' '[7/8] Running evidence tests'
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 -m unittest discover -s evidence/tests -v
	@printf '%s\n' '[8/8] Running integration tests'
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 -m unittest discover -s integrations/tests -v

.PHONY: validation-init
validation-init:
	@python3 scripts/init-validation-sprint.py \
		--private-dir $(VALIDATION_DIR) \
		$(DATE_ARG) \
		$(REFRESH_README_ARG)

.PHONY: validation-pack
validation-pack:
	@python3 scripts/validation-outreach-block.py $(DATE_ARG) \
		--targets $(VALIDATION_TARGETS) \
		--format json \
		--out $(VALIDATION_BLOCK_JSON) \
		> /dev/null
	@python3 scripts/validation-outreach-block.py $(DATE_ARG) \
		--targets $(VALIDATION_TARGETS) \
		--format markdown \
		--out $(VALIDATION_BLOCK_MD) \
		> /dev/null
	@python3 scripts/validation-message-pack.py \
		--block $(VALIDATION_BLOCK_JSON) \
		--format json \
		--out $(VALIDATION_MESSAGE_PACK_JSON) \
		> /dev/null
	@python3 scripts/validation-message-pack.py \
		--block $(VALIDATION_BLOCK_JSON) \
		--format markdown \
		--out $(VALIDATION_MESSAGE_PACK_MD) \
		> /dev/null
	@$(MAKE) --no-print-directory validation-status > /dev/null
	@printf 'Wrote validation pack and status files under %s\n' '$(VALIDATION_DIR)'

.PHONY: validation-draft
validation-draft:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-draft TARGET=target-dib-platform-004 [DATE=YYYY-MM-DD]'; exit 2; }
	@python3 scripts/validation-message-pack.py \
		--block $(VALIDATION_BLOCK_JSON) \
		--target-label $(TARGET) \
		$(REQUIRE_DATE_ARG) \
		--format markdown

.PHONY: validation-draft-copy
validation-draft-copy:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-draft-copy TARGET=target-dib-platform-004 [DATE=YYYY-MM-DD]'; exit 2; }
	@python3 scripts/validation-message-pack.py \
		--block $(VALIDATION_BLOCK_JSON) \
		--target-label $(TARGET) \
		$(REQUIRE_DATE_ARG) \
		--format send-text

.PHONY: validation-next-draft
validation-next-draft:
	@python3 scripts/validation-next-draft.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--format markdown \
		--out $(VALIDATION_NEXT_DRAFT_MD)

.PHONY: validation-send-copy
validation-send-copy:
	@python3 scripts/validation-next-draft.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--format send-text \
		--out $(VALIDATION_SEND_COPY_TXT)

.PHONY: validation-send-copy-batch
validation-send-copy-batch:
	@python3 scripts/validation-send-copy-batch.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--out-dir $(VALIDATION_SEND_COPY_DIR) \
		--manifest-out $(VALIDATION_SEND_COPY_BATCH_MANIFEST_JSON)

.PHONY: validation-send-copy-check
validation-send-copy-check:
	@python3 scripts/validation-send-copy-batch.py \
		--check-dir $(VALIDATION_SEND_COPY_DIR) \
		$(REQUIRE_DATE_ARG)

.PHONY: validation-apply-draft
validation-apply-draft:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-apply-draft TARGET=target-dib-platform-001 [DATE=YYYY-MM-DD] [CONFIRM_SENT=1]'; exit 2; }
	@python3 scripts/validation-apply-draft-update.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		--target-label $(TARGET) \
		$(REQUIRE_DATE_ARG) \
		$(CONFIRM_SENT_COPY_ARG) \
		$(CONFIRM_SENT_ARG)

.PHONY: validation-reply-triage
validation-reply-triage:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call [DATE=YYYY-MM-DD]'; exit 2; }
	@test -n "$(REPLY)" || { echo 'Usage: make validation-reply-triage TARGET=target-dib-platform-001 REPLY=book_call [DATE=YYYY-MM-DD]'; exit 2; }
	@python3 scripts/validation-reply-triage.py \
		--targets $(VALIDATION_TARGETS) \
		--target-label $(TARGET) \
		--classification $(REPLY) \
		--date $(VALIDATION_RUN_DATE) \
		--format markdown

.PHONY: validation-log-interview
validation-log-interview:
	@test -f "$(VALIDATION_INTERVIEW_JSON)" || { echo 'Usage: make validation-log-interview [INTERVIEW=validation/private/customer-validation-interview-next.json] [DATE=YYYY-MM-DD] [REPLACE_EXAMPLE_SEED=1] [CONFIRM_LOG=1]'; exit 2; }
	@python3 scripts/customer-validation-log-add.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		--interview-json $(VALIDATION_INTERVIEW_JSON) \
		--require-target-status call_booked \
		--updated-at $(VALIDATION_RUN_DATE) \
		$(REPLACE_EXAMPLE_SEED_ARG) \
		$(CONFIRM_LOG_ARG)

.PHONY: validation-prepare-interview
validation-prepare-interview:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-prepare-interview TARGET=target-dib-platform-001 [DATE=YYYY-MM-DD]'; exit 2; }
	@python3 scripts/validation-prepare-interview.py \
		--targets $(VALIDATION_TARGETS) \
		--target-label $(TARGET) \
		--date $(VALIDATION_RUN_DATE) \
		--out $(VALIDATION_INTERVIEW_JSON)

.PHONY: validation-book-call
validation-book-call:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-book-call TARGET=target-dib-platform-001 [DATE=YYYY-MM-DD] [CONFIRM_TARGET=1]'; exit 2; }
	@python3 scripts/validation-target-update.py \
		--targets $(VALIDATION_TARGETS) \
		--target-label $(TARGET) \
		--status call_booked \
		--require-current-status intro_requested \
		--require-current-status outreach_sent \
		--require-current-status follow_up_due \
		--last-touch $(VALIDATION_RUN_DATE) \
		--updated-at $(VALIDATION_RUN_DATE) \
		--clear-follow-up-due \
		--next-action "Prepare discovery call." \
		$(CONFIRM_TARGET_ARG)

.PHONY: validation-disqualify-target
validation-disqualify-target:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-disqualify-target TARGET=target-dib-platform-001 [DATE=YYYY-MM-DD] [CONFIRM_TARGET=1]'; exit 2; }
	@python3 scripts/validation-target-update.py \
		--targets $(VALIDATION_TARGETS) \
		--target-label $(TARGET) \
		--status disqualified \
		--require-current-status identified \
		--require-current-status intro_requested \
		--require-current-status outreach_sent \
		--require-current-status follow_up_due \
		--require-current-status call_booked \
		--last-touch $(VALIDATION_RUN_DATE) \
		--updated-at $(VALIDATION_RUN_DATE) \
		--clear-follow-up-due \
		--next-action "Disqualified from current validation sprint." \
		$(CONFIRM_TARGET_ARG)

.PHONY: validation-complete-call
validation-complete-call:
	@test -n "$(TARGET)" || { echo 'Usage: make validation-complete-call TARGET=target-dib-platform-001 [DATE=YYYY-MM-DD] [CONFIRM_TARGET=1]'; exit 2; }
	@python3 scripts/validation-target-update.py \
		--targets $(VALIDATION_TARGETS) \
		--validation-log $(VALIDATION_LOG) \
		--target-label $(TARGET) \
		--status completed \
		--require-current-status call_booked \
		--require-validation-log-account \
		--last-touch $(VALIDATION_RUN_DATE) \
		--updated-at $(VALIDATION_RUN_DATE) \
		--clear-follow-up-due \
		--next-action "Logged sanitized discovery outcome." \
		$(CONFIRM_TARGET_ARG)

.PHONY: validation-status
validation-status:
	@python3 scripts/validation-outreach-status.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		--verify-dry-run-commands \
		$(REQUIRE_DATE_ARG) \
		--format json \
		--out $(VALIDATION_STATUS_JSON) \
		> /dev/null
	@python3 scripts/validation-outreach-status.py \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--targets $(VALIDATION_TARGETS) \
		--verify-dry-run-commands \
		$(REQUIRE_DATE_ARG) \
		--format markdown \
		--out $(VALIDATION_STATUS_MD)

.PHONY: validation-dashboard
validation-dashboard:
	@python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON)

.PHONY: validation-team-update
validation-team-update:
	@python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--format team

.PHONY: validation-team-update-save
validation-team-update-save:
	@mkdir -p "$(dir $(VALIDATION_TEAM_UPDATE_MD))"
	@set -e; \
	tmp=$$(mktemp "$(VALIDATION_TEAM_UPDATE_MD).tmp.XXXXXX"); \
	trap 'rm -f "$$tmp"' EXIT; \
	python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--format team \
		> "$$tmp"; \
	mv "$$tmp" "$(VALIDATION_TEAM_UPDATE_MD)"; \
	trap - EXIT; \
	printf 'Wrote sanitized aggregate-only team update to %s\n' '$(VALIDATION_TEAM_UPDATE_MD)'

.PHONY: validation-next-action-save
validation-next-action-save:
	@python3 scripts/validation-next-action.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--date $(VALIDATION_RUN_DATE) \
		--out $(VALIDATION_NEXT_ACTION_MD) \
		> /dev/null
	@printf 'Wrote regenerated private next-action handoff to %s\n' '$(VALIDATION_NEXT_ACTION_MD)'

.PHONY: validation-weekly-review
validation-weekly-review:
	@python3 scripts/validation-weekly-review.py \
		--private-dir $(VALIDATION_DIR) \
		--targets $(VALIDATION_TARGETS) \
		--log $(VALIDATION_LOG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--review-date $(VALIDATION_RUN_DATE) \
		--format json \
		--out $(VALIDATION_WEEKLY_REVIEW_JSON) \
		> /dev/null
	@python3 scripts/validation-weekly-review.py \
		--private-dir $(VALIDATION_DIR) \
		--targets $(VALIDATION_TARGETS) \
		--log $(VALIDATION_LOG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--review-date $(VALIDATION_RUN_DATE) \
		--format markdown \
		--out $(VALIDATION_WEEKLY_REVIEW_MD)

.PHONY: validation-prune-private
validation-prune-private:
	@python3 scripts/validation-prune-private.py \
		--weekly-review $(VALIDATION_WEEKLY_REVIEW_JSON) \
		--private-dir $(VALIDATION_DIR) \
		--review-date $(VALIDATION_RUN_DATE) \
		$(CONFIRM_PRUNE_ARG) \
		--format markdown

.PHONY: validation-resume
validation-resume:
	@python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--format text
	@dashboard_states=$$(python3 scripts/validation-sprint-dashboard.py \
		--log $(VALIDATION_LOG) \
		--targets $(VALIDATION_TARGETS) \
		$(REQUIRE_DATE_ARG) \
		--message-pack $(VALIDATION_MESSAGE_PACK_JSON) \
		--format json | python3 -c 'import json, sys; data = json.load(sys.stdin); outreach = data.get("outreach_execution", {}); print(outreach.get("next_draft_state", "unknown")); print(outreach.get("send_copy_state", "unknown"))'); \
	next_draft_state=$$(printf '%s\n' "$$dashboard_states" | sed -n '1p'); \
	send_copy_state=$$(printf '%s\n' "$$dashboard_states" | sed -n '2p'); \
	if [ -f "$(VALIDATION_NEXT_DRAFT_MD)" ] && [ "$$next_draft_state" = "ready" ]; then \
		if [ -f "$(VALIDATION_SEND_COPY_TXT)" ] && [ "$$send_copy_state" = "ready" ]; then \
			printf '\nBEGIN COPY-ONLY SEND TEXT: %s\n\n' "$(VALIDATION_SEND_COPY_TXT)"; \
			sed -n '1,120p' "$(VALIDATION_SEND_COPY_TXT)"; \
			printf '\nEND COPY-ONLY SEND TEXT\n'; \
		else \
			printf '\nCopy-only send text is missing or stale. Run: make validation-send-copy DATE=%s\n' "$(VALIDATION_RUN_DATE)"; \
		fi; \
		printf '\nDO NOT SEND BELOW THIS LINE. Tracker/audit metadata follows.\n'; \
		printf '\nAlready-rendered next draft with tracker metadata: %s\n\n' "$(VALIDATION_NEXT_DRAFT_MD)"; \
		sed -n '1,220p' "$(VALIDATION_NEXT_DRAFT_MD)"; \
	elif [ "$$next_draft_state" = "not_needed" ]; then \
		printf '\nNo next draft is needed for the current outreach pack.\n'; \
	elif [ -f "$(VALIDATION_NEXT_DRAFT_MD)" ]; then \
		printf '\nExisting next draft is stale or unreadable for the current next target: %s\n' "$(VALIDATION_NEXT_DRAFT_MD)"; \
		printf 'Run: make validation-next-draft DATE=%s\n' "$(VALIDATION_RUN_DATE)"; \
	else \
		printf '\nNo next draft file found. Run: make validation-next-draft DATE=%s\n' "$(VALIDATION_RUN_DATE)"; \
	fi

.PHONY: goal-resume
goal-resume: validation-resume

.PHONY: release-safety
release-safety:
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 scripts/check-release-safety.py --diff

.PHONY: release-hygiene
release-hygiene:
	@PYTHONPATH_SAFE=$(PYTHONPATH_SAFE) ./scripts/check-release-hygiene.sh

.PHONY: secrets-archaeology
secrets-archaeology:
	@./scripts/check-secrets-archaeology.sh

.PHONY: release-safety-staged
release-safety-staged:
	@PYTHONPATH=$(PYTHONPATH_SAFE) python3 scripts/check-release-safety.py --staged
