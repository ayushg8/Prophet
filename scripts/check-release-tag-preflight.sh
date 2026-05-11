#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH_SAFE="${PYTHONPATH_SAFE:-.:cyber-side:world-side}"
VALIDATION_LOG="${VALIDATION_LOG:-validation/private/customer-validation-log.json}"
VALIDATION_TARGETS="${VALIDATION_TARGETS:-validation/private/validation-targets.json}"
VALIDATION_RUN_DATE="${DATE:-$(date +%F)}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-release-tag-preflight.sh [DATE=YYYY-MM-DD]

Run the read-only public pilot release-tag preflight.

This fails closed unless:

- the git worktree has no tracked or untracked non-ignored changes
- release hygiene passes
- full secrets archaeology, including git history, passes
- the validation dashboard allows build_next_slice from real buyer evidence
- staged-path release safety passes

After the clean-worktree and release-hygiene prerequisites pass, this reports
both the full secrets archaeology result and the real-validation build gate
result before exiting, so release owners can see every current blocker.

This script does not stage, commit, push, tag, rewrite history, delete files,
copy ignored private validation artifacts, or mark outreach as sent.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ $# -gt 0 ]]; then
  echo "error: unknown argument: $1" >&2
  usage >&2
  exit 2
fi

printf '[1/6] Checking clean tracked worktree\n'
git diff --quiet

printf '[2/6] Checking clean staged state\n'
git diff --cached --quiet

printf '[3/6] Checking no untracked non-ignored files\n'
untracked_count="$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')"
if [[ "$untracked_count" != "0" ]]; then
  echo "release tag preflight failed: $untracked_count untracked non-ignored file(s) exist" >&2
  exit 1
fi

printf '[4/6] Running release hygiene\n'
./scripts/check-release-hygiene.sh

preflight_failed=0

printf '[5/6] Running full secrets archaeology\n'
if ! ./scripts/check-secrets-archaeology.sh; then
  printf 'release tag preflight blocker: full secrets archaeology failed; review docs/SECRET_HISTORY_REVIEW.md.\n' >&2
  preflight_failed=1
fi

printf '[6/6] Checking real-validation build gate\n'
if ! dashboard_json="$(
  PYTHONPATH="$PYTHONPATH_SAFE" python3 scripts/validation-sprint-dashboard.py \
    --log "$VALIDATION_LOG" \
    --targets "$VALIDATION_TARGETS" \
    --require-date "$VALIDATION_RUN_DATE"
)"; then
  printf 'release tag preflight blocker: validation dashboard failed.\n' >&2
  preflight_failed=1
elif ! printf '%s\n' "$dashboard_json" | python3 -c '
import json
import sys

data = json.load(sys.stdin)
build_gate = data.get("build_gate") or {}
allowed = bool(build_gate.get("allowed_to_build_next_slice"))
reason = build_gate.get("reason") or "no reason reported"
verdict = ((data.get("customer_validation") or {}).get("verdict"))
target_verdict = ((data.get("target_backed_validation") or {}).get("verdict"))
if not allowed:
    print(
        "release tag preflight failed: build gate is closed "
        f"(customer_validation={verdict}, target_backed_validation={target_verdict}): {reason}",
        file=sys.stderr,
    )
    sys.exit(1)
print("Real-validation build gate is open.")
'; then
  preflight_failed=1
fi

if [[ "$preflight_failed" != "0" ]]; then
  printf 'Prophet release tag preflight failed.\n' >&2
  exit 1
fi

printf 'Prophet release tag preflight passed.\n'
