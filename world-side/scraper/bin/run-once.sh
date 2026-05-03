#!/usr/bin/env bash
# Run one scraper collection + sanitization pass on the isolated scraper host.
#
# This wrapper intentionally knows only paths and process order. The collector
# and sanitizer implementations can land later without changing this file.

set -euo pipefail

umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCRAPER_BASE_DIR="${SCRAPER_BASE_DIR:-/srv/scraper}"
SCRAPER_BASE_DIR="${SCRAPER_BASE_DIR%/}"
[ -n "$SCRAPER_BASE_DIR" ] || SCRAPER_BASE_DIR="/"
SCRAPER_APP_DIR="${SCRAPER_APP_DIR:-$SCRAPER_BASE_DIR/app}"
SCRAPER_VENV_DIR="${SCRAPER_VENV_DIR:-$SCRAPER_BASE_DIR/venv}"
SCRAPER_RAW_DIR="${SCRAPER_RAW_DIR:-$SCRAPER_BASE_DIR/raw}"
SCRAPER_OUTPUT_DIR="${SCRAPER_OUTPUT_DIR:-$SCRAPER_BASE_DIR/output}"
SCRAPER_LOG_DIR="${SCRAPER_LOG_DIR:-$SCRAPER_BASE_DIR/logs}"
SCRAPER_STATE_DIR="${SCRAPER_STATE_DIR:-$SCRAPER_BASE_DIR/state}"
SCRAPER_RUN_DIR="${SCRAPER_RUN_DIR:-$SCRAPER_BASE_DIR/run}"
SCRAPER_TMP_DIR="${SCRAPER_TMP_DIR:-$SCRAPER_BASE_DIR/tmp}"
SCRAPER_PYTHON="${SCRAPER_PYTHON:-$SCRAPER_VENV_DIR/bin/python}"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

log() {
    printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

require_absolute_path() {
    local name="$1"
    local path="$2"

    case "$path" in
        /*) ;;
        *) fail "$name must be an absolute path; got: $path" ;;
    esac
}

guard_scoped_path() {
    local name="$1"
    local path="$2"

    require_absolute_path "$name" "$path"

    case "$path" in
        /|/srv|/srv/)
            fail "$name is too broad for a scraper runtime path: $path"
            ;;
    esac
}

guard_child_path() {
    local name="$1"
    local path="$2"

    require_absolute_path "$name" "$path"

    case "$path" in
        "$SCRAPER_BASE_DIR"/*) ;;
        *) fail "$name must live under SCRAPER_BASE_DIR ($SCRAPER_BASE_DIR); got: $path" ;;
    esac
}

find_first_existing() {
    local candidate

    for candidate in "$@"; do
        if [ -f "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

resolve_optional_step() {
    local env_name="$1"
    local override="$2"
    shift 2

    if [ -n "$override" ]; then
        require_absolute_path "$env_name" "$override"
        [ -f "$override" ] || fail "$env_name points to a missing file: $override"
        printf '%s\n' "$override"
        return 0
    fi

    find_first_existing "$@" || true
}

run_step() {
    local label="$1"
    local step_path="$2"

    log "Starting $label: $step_path"

    case "$step_path" in
        *.py)
            "$SCRAPER_PYTHON" "$step_path"
            ;;
        *.sh)
            bash "$step_path"
            ;;
        *)
            if [ -x "$step_path" ]; then
                "$step_path"
            else
                "$SCRAPER_PYTHON" "$step_path"
            fi
            ;;
    esac

    log "Finished $label"
}

guard_scoped_path "SCRAPER_BASE_DIR" "$SCRAPER_BASE_DIR"
guard_child_path "SCRAPER_APP_DIR" "$SCRAPER_APP_DIR"
guard_child_path "SCRAPER_VENV_DIR" "$SCRAPER_VENV_DIR"
guard_child_path "SCRAPER_RAW_DIR" "$SCRAPER_RAW_DIR"
guard_child_path "SCRAPER_OUTPUT_DIR" "$SCRAPER_OUTPUT_DIR"
guard_child_path "SCRAPER_LOG_DIR" "$SCRAPER_LOG_DIR"
guard_child_path "SCRAPER_STATE_DIR" "$SCRAPER_STATE_DIR"
guard_child_path "SCRAPER_RUN_DIR" "$SCRAPER_RUN_DIR"
guard_child_path "SCRAPER_TMP_DIR" "$SCRAPER_TMP_DIR"
require_absolute_path "SCRAPER_PYTHON" "$SCRAPER_PYTHON"

[ -x "$SCRAPER_PYTHON" ] || fail "scraper virtualenv not found at $SCRAPER_PYTHON; run bootstrap-scraper-machine.sh first"
"$SCRAPER_PYTHON" - <<'PY'
import sys

if sys.prefix == sys.base_prefix:
    raise SystemExit("ERROR: SCRAPER_PYTHON is not inside a virtualenv")
PY

mkdir -p "$SCRAPER_RAW_DIR" "$SCRAPER_OUTPUT_DIR" "$SCRAPER_LOG_DIR" "$SCRAPER_STATE_DIR" "$SCRAPER_RUN_DIR" "$SCRAPER_TMP_DIR"

RUN_ID="${SCRAPER_RUN_ID:-$(date -u '+%Y%m%dT%H%M%SZ')}"
LOG_FILE="$SCRAPER_LOG_DIR/run-once-$RUN_ID.log"
LOCK_FILE="$SCRAPER_RUN_DIR/run-once.lock"

export SCRAPER_BASE_DIR
export SCRAPER_APP_DIR
export SCRAPER_RAW_DIR
export SCRAPER_OUTPUT_DIR
export SCRAPER_LOG_DIR
export SCRAPER_STATE_DIR
export SCRAPER_RUN_DIR
export TMPDIR="$SCRAPER_TMP_DIR"

SANITIZER_PATH="$(
    resolve_optional_step "SCRAPER_SANITIZER" "${SCRAPER_SANITIZER:-}" \
        "$SCRIPT_DIR/sanitize-once" \
        "$SCRIPT_DIR/sanitize-once.sh" \
        "$SCRIPT_DIR/sanitize-once.py" \
        "$SCRIPT_DIR/sanitizer" \
        "$SCRIPT_DIR/sanitizer.sh" \
        "$SCRIPT_DIR/sanitizer.py" \
        "$SCRAPER_APP_DIR/sanitize-once" \
        "$SCRAPER_APP_DIR/sanitize-once.py" \
        "$SCRAPER_APP_DIR/sanitizer" \
        "$SCRAPER_APP_DIR/sanitizer.py" \
        "$SCRAPER_APP_DIR/world-side/scraper/sanitize-once.py" \
        "$SCRAPER_APP_DIR/world-side/scraper/sanitizer.py" \
)"

COLLECTOR_PATH="$(
    resolve_optional_step "SCRAPER_COLLECTOR" "${SCRAPER_COLLECTOR:-}" \
        "$SCRIPT_DIR/collect-once" \
        "$SCRIPT_DIR/collect-once.sh" \
        "$SCRIPT_DIR/collect-once.py" \
        "$SCRIPT_DIR/collector" \
        "$SCRIPT_DIR/collector.sh" \
        "$SCRIPT_DIR/collector.py" \
        "$SCRAPER_APP_DIR/collect-once" \
        "$SCRAPER_APP_DIR/collect-once.py" \
        "$SCRAPER_APP_DIR/collector" \
        "$SCRAPER_APP_DIR/collector.py" \
        "$SCRAPER_APP_DIR/world-side/scraper/collect-once.py" \
        "$SCRAPER_APP_DIR/world-side/scraper/collector.py" \
)"

if [ -z "$SANITIZER_PATH" ]; then
    fail "no sanitizer found; refusing to run collectors until sanitization exists"
fi

if command -v flock >/dev/null 2>&1; then
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        fail "another scraper run is already active: $LOCK_FILE"
    fi
else
    log "WARN: flock is unavailable; continuing without a concurrency lock"
fi

{
    log "Run id: $RUN_ID"
    log "Raw dir: $SCRAPER_RAW_DIR"
    log "Output dir: $SCRAPER_OUTPUT_DIR"

    if [ -n "$COLLECTOR_PATH" ]; then
        run_step "collector" "$COLLECTOR_PATH"
    else
        log "No collector found; running sanitizer only."
    fi

    run_step "sanitizer" "$SANITIZER_PATH"
    log "Run complete."
} >> "$LOG_FILE" 2>&1

log "Scraper run finished. Log: $LOG_FILE"
