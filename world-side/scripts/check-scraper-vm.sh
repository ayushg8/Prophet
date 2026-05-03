#!/usr/bin/env bash
# Read-only readiness check for the isolated scraper host. Uses SSH key auth
# only and never prompts for, stores, or transmits a password.

set -u

SCRAPER_SSH_TARGET="${SCRAPER_SSH_TARGET:-prophet-scraper}"
SCRAPER_REMOTE_APP="${SCRAPER_REMOTE_APP:-/srv/scraper/app}"
SCRAPER_REMOTE_OUTPUT="${SCRAPER_REMOTE_OUTPUT:-/srv/scraper/output}"
SCRAPER_REMOTE_PYTHON="${SCRAPER_REMOTE_PYTHON:-/srv/scraper/venv/bin/python}"

SSH_OPTS=(
    -o BatchMode=yes
    -o NumberOfPasswordPrompts=0
    -o ConnectTimeout=8
)

failures=0

log() {
    printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

ok() {
    printf 'OK: %s\n' "$*"
}

warn() {
    printf 'WARN: %s\n' "$*" >&2
}

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    failures=$((failures + 1))
}

remote() {
    ssh "${SSH_OPTS[@]}" "$SCRAPER_SSH_TARGET" "$@"
}

log "Checking scraper VM target: $SCRAPER_SSH_TARGET"

if ! remote "printf 'ready\n'" >/dev/null 2>/tmp/prophet-scraper-check.err; then
    fail "SSH key auth or network reachability is not ready for $SCRAPER_SSH_TARGET"
    sed 's/^/  /' /tmp/prophet-scraper-check.err >&2
    warn "Fix ~/.ssh/config, network/VPN, and authorized_keys before using RUN SCRAPER VM."
    exit 1
fi
ok "SSH key auth works"

if remote "test -d '$SCRAPER_REMOTE_APP'"; then
    ok "remote app directory exists: $SCRAPER_REMOTE_APP"
else
    fail "remote app directory missing: $SCRAPER_REMOTE_APP"
fi

if remote "test -x '$SCRAPER_REMOTE_APP/bin/run-once.sh'"; then
    ok "remote Linux run wrapper exists"
else
    fail "remote run wrapper missing or not executable: $SCRAPER_REMOTE_APP/bin/run-once.sh"
fi

if remote "test -x '$SCRAPER_REMOTE_PYTHON'"; then
    ok "remote scraper virtualenv exists: $SCRAPER_REMOTE_PYTHON"
else
    fail "remote scraper virtualenv missing: $SCRAPER_REMOTE_PYTHON"
fi

if remote "test -d '$SCRAPER_REMOTE_OUTPUT'"; then
    ok "remote output directory exists: $SCRAPER_REMOTE_OUTPUT"
else
    fail "remote output directory missing: $SCRAPER_REMOTE_OUTPUT"
fi

if [ "${PROPHET_CHECK_RUN_SMOKE:-0}" = "1" ]; then
    log "Running optional safe CISA KEV smoke test on scraper VM"
    if remote "PYTHONPATH='$SCRAPER_REMOTE_APP' '$SCRAPER_REMOTE_PYTHON' -m scraper_side.cli --collector cisa-kev --live --limit 2 --out '$SCRAPER_REMOTE_OUTPUT/cisa-kev-readiness-smoke.jsonl'"; then
        ok "safe live collector smoke test wrote sanitized JSONL"
    else
        fail "safe live collector smoke test failed"
    fi
else
    warn "Skipping live source smoke test. Set PROPHET_CHECK_RUN_SMOKE=1 to run CISA KEV metadata collection."
fi

if [ "$failures" -gt 0 ]; then
    fail "$failures readiness check(s) failed"
    exit 1
fi

ok "scraper VM is ready for the console RUN SCRAPER VM button"
