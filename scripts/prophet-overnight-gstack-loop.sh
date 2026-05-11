#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOURS="8"
SLEEP_SECONDS="60"
MAX_CYCLES="99"
CODEX_BIN="${CODEX_BIN:-codex}"
GSTACK_BIN="${GSTACK_BIN:-/Users/dullet/.gstack/repos/gstack/bin}"
RUN_DIR="${RUN_DIR:-evidence/outputs/runtime/gstack-overnight-loop}"
PID_FILE="$RUN_DIR/supervisor.pid"
STOP_FILE="$RUN_DIR/STOP"
SUPERVISOR_LOG="$RUN_DIR/supervisor.log"

usage() {
  cat <<'USAGE'
Usage: scripts/prophet-overnight-gstack-loop.sh [--hours N] [--sleep-seconds N] [--max-cycles N]

Runs an autonomous Prophet hardening loop. Each cycle invokes `codex exec` with
a bounded prompt: plan one safe slice, implement it, update docs/TODOs, run
focused verification, log to GStack, and return.

Runtime files:
  evidence/outputs/runtime/gstack-overnight-loop/supervisor.pid
  evidence/outputs/runtime/gstack-overnight-loop/supervisor.log
  evidence/outputs/runtime/gstack-overnight-loop/STOP

Stop:
  touch evidence/outputs/runtime/gstack-overnight-loop/STOP
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hours)
      HOURS="${2:?missing --hours value}"
      shift 2
      ;;
    --sleep-seconds)
      SLEEP_SECONDS="${2:?missing --sleep-seconds value}"
      shift 2
      ;;
    --max-cycles)
      MAX_CYCLES="${2:?missing --max-cycles value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$RUN_DIR"

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "Prophet overnight loop already running with PID $existing_pid" >&2
    exit 1
  fi
fi

rm -f "$STOP_FILE"
echo "$$" > "$PID_FILE"

cleanup() {
  rm -f "$PID_FILE"
}
trap cleanup EXIT

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$SUPERVISOR_LOG"
}

number_re='^[0-9]+([.][0-9]+)?$'
if ! [[ "$HOURS" =~ $number_re ]]; then
  echo "--hours must be numeric" >&2
  exit 2
fi
if ! [[ "$SLEEP_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "--sleep-seconds must be an integer" >&2
  exit 2
fi
if ! [[ "$MAX_CYCLES" =~ ^[0-9]+$ ]]; then
  echo "--max-cycles must be an integer" >&2
  exit 2
fi

END_EPOCH="$(python3 - "$HOURS" <<'PY'
import sys, time
hours = float(sys.argv[1])
print(int(time.time() + hours * 3600))
PY
)"

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
  echo "codex CLI not found: $CODEX_BIN" >&2
  exit 1
fi

if [[ ! -x "$GSTACK_BIN/gstack-timeline-log" ]]; then
  echo "gstack timeline logger not found under $GSTACK_BIN" >&2
  exit 1
fi

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
log "starting Prophet overnight GStack loop on branch=$branch hours=$HOURS max_cycles=$MAX_CYCLES"
"$GSTACK_BIN/gstack-timeline-log" \
  '{"skill":"prophet-overnight-loop","event":"started","branch":"'"$branch"'","outcome":"running"}' \
  2>/dev/null || true

cycle=0
while [[ "$(date +%s)" -lt "$END_EPOCH" && "$cycle" -lt "$MAX_CYCLES" ]]; do
  if [[ -f "$STOP_FILE" ]]; then
    log "stop file detected; exiting loop"
    break
  fi

  cycle=$((cycle + 1))
  cycle_id="$(printf '%03d' "$cycle")"
  cycle_dir="$RUN_DIR/cycle-$cycle_id"
  mkdir -p "$cycle_dir"
  prompt_file="$cycle_dir/prompt.md"
  jsonl_log="$cycle_dir/codex-events.jsonl"
  last_message="$cycle_dir/last-message.md"
  status_file="$cycle_dir/status.txt"

  log "cycle $cycle_id started"
  git status --short --untracked-files=all > "$cycle_dir/git-status-before.txt" || true
  "$GSTACK_BIN/gstack-timeline-log" \
    '{"skill":"prophet-overnight-loop","event":"cycle_started","branch":"'"$branch"'","cycle":"'"$cycle_id"'"}' \
    2>/dev/null || true

  cat > "$prompt_file" <<'PROMPT'
You are Codex running inside the Prophet overnight GStack loop.

Mission: improve Prophet as a buyer-ready, defensive cyber/evidence pilot while the production build gate remains closed. Plan, execute, verify, checkpoint, and return. Do one coherent slice per cycle. Do not stall on questions.

Hard safety boundary:
- Prophet only. Do not add unrelated product tracks.
- No live targets, no payload generation, no credentials, no private hostnames, no raw scraper text, no offensive workflow.
- Keep default mode fixture-backed, seeded-OSINT-backed, policy-bound, and localhost-only.
- Do not add production platform scope while customer validation is `insufficient_data`.
- Only `build_next_slice` opens production platform work. `pilot_pull_detected` means convert design partners first.
- Do not mark messages sent, calls booked, interviews completed, pilot signals, or paid paths unless the real external action happened and the sanitized private record was reviewed.
- Never run destructive git commands. Do not reset, checkout, clean, force-push, or delete user work.
- Do not commit or push unless the user explicitly asked in the current prompt. This loop did not ask you to commit.
- Runtime outputs must stay under ignored outputs/runtime directories.
- Do not commit anything under `validation/private/`.

Use GStack:
- Read recent GStack timeline/checkpoint context with `/Users/dullet/.gstack/repos/gstack/bin/gstack-timeline-read`.
- Log start/completion with `/Users/dullet/.gstack/repos/gstack/bin/gstack-timeline-log`.
- Use the GStack style of plan -> execute -> verify -> checkpoint summary.
- If context is unclear, consult the repo docs/TODOs and make the safest reasonable assumption.

Cycle workflow:
1. Read `docs/CODEX_CEO_FINISH_BRIEF.md`, `docs/PROPHET_COMPLETION_AUDIT.md`, `docs/PROPHET_TODO.md`, and recent GStack timeline.
2. Run `make validation-dashboard DATE=YYYY-MM-DD` for the active outreach date, or `make goal-resume DATE=YYYY-MM-DD` after a restored `/goal` session.
3. If the dashboard is `insufficient_data`, pick the highest-leverage unblocked validation-sprint or safe-pilot-packaging item that can be completed in one cycle.
4. Do not pick production platform work unless the dashboard reaches `build_next_slice`.
5. State the micro-plan in your own working output.
6. Implement it with minimal, localized edits.
7. Update the relevant TODO/docs.
8. Run focused tests. If the slice touches the buyer smoke path, run `./scripts/run-pilot-demo-smoke.sh`.
9. Always run `git diff --check` and the relevant release-safety scan.
10. Log the completed cycle to GStack timeline.
11. Final response must include: files changed, tests run, pass/fail, current validation verdict/build gate, remaining risk, and next recommended slice.

Good next areas while validation remains `insufficient_data`:
- Buyer validation sprint tooling, recovery docs, and stale-state guards.
- Copy-only outreach/send-boundary safety.
- Aggregate-only validation handoffs that avoid private target details.
- Buyer-facing evidence packaging that improves qualified review quality.
- Release hygiene that preserves the closed production build gate.

Be strict: do not mark TODO items complete unless code/docs/tests actually support it.
PROMPT

  set +e
  "$CODEX_BIN" exec \
    -C "$ROOT_DIR" \
    -s danger-full-access \
    --json \
    --output-last-message "$last_message" \
    - < "$prompt_file" > "$jsonl_log" 2>&1
  codex_status=$?
  set -e
  echo "$codex_status" > "$status_file"

  git status --short --untracked-files=all > "$cycle_dir/git-status-after.txt" || true
  if [[ "$codex_status" -eq 0 ]]; then
    log "cycle $cycle_id completed"
    "$GSTACK_BIN/gstack-timeline-log" \
      '{"skill":"prophet-overnight-loop","event":"cycle_completed","branch":"'"$branch"'","cycle":"'"$cycle_id"'","outcome":"success"}' \
      2>/dev/null || true
  else
    log "cycle $cycle_id failed with status=$codex_status; continuing after cooldown"
    "$GSTACK_BIN/gstack-timeline-log" \
      '{"skill":"prophet-overnight-loop","event":"cycle_completed","branch":"'"$branch"'","cycle":"'"$cycle_id"'","outcome":"error","status":"'"$codex_status"'"}' \
      2>/dev/null || true
  fi

  if [[ -f "$STOP_FILE" ]]; then
    log "stop file detected after cycle $cycle_id"
    break
  fi
  sleep "$SLEEP_SECONDS"
done

log "Prophet overnight GStack loop finished after $cycle cycle(s)"
"$GSTACK_BIN/gstack-timeline-log" \
  '{"skill":"prophet-overnight-loop","event":"completed","branch":"'"$branch"'","outcome":"finished","cycles":"'"$cycle"'"}' \
  2>/dev/null || true
