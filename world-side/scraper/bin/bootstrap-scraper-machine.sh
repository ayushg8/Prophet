#!/usr/bin/env bash
# Bootstrap the isolated Prophet scraper machine.
#
# Idempotent and public-safe:
# - creates only the scraper service tree under SCRAPER_BASE_DIR
# - installs Python packages only into the scraper virtualenv
# - reads no secrets and contains no host/user/password/IP values

set -euo pipefail

umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SCRAPER_BASE_DIR="${SCRAPER_BASE_DIR:-/srv/scraper}"
SCRAPER_BASE_DIR="${SCRAPER_BASE_DIR%/}"
[ -n "$SCRAPER_BASE_DIR" ] || SCRAPER_BASE_DIR="/"
SCRAPER_APP_DIR="${SCRAPER_APP_DIR:-$SCRAPER_BASE_DIR/app}"
SCRAPER_VENV_DIR="${SCRAPER_VENV_DIR:-$SCRAPER_BASE_DIR/venv}"
SCRAPER_REQUIREMENTS="${SCRAPER_REQUIREMENTS:-$SCRAPER_DIR/requirements.txt}"
SCRAPER_RUN_USER="${SCRAPER_RUN_USER:-${SUDO_USER:-$(id -un)}}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

info() {
    printf '%s\n' "$*"
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
            fail "$name is too broad for a scraper bootstrap path: $path"
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

run_as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        fail "creating $SCRAPER_BASE_DIR requires root privileges; rerun with sudo or choose a writable SCRAPER_BASE_DIR"
    fi
}

install_dir() {
    local mode="$1"
    local path="$2"

    if [ "$(id -u)" -eq 0 ]; then
        run_as_root install -d -m "$mode" -o "$SCRAPER_RUN_USER" -g "$SCRAPER_RUN_GROUP" "$path"
    elif [ "$(id -un)" = "$SCRAPER_RUN_USER" ] && install -d -m "$mode" "$path" 2>/dev/null; then
        chmod "$mode" "$path"
    elif command -v sudo >/dev/null 2>&1; then
        run_as_root install -d -m "$mode" -o "$SCRAPER_RUN_USER" -g "$SCRAPER_RUN_GROUP" "$path"
    else
        fail "cannot create $path; rerun with sudo or choose a writable SCRAPER_BASE_DIR"
    fi
}

chown_venv_if_needed() {
    if [ "$(id -u)" -eq 0 ] || [ "$(id -un)" != "$SCRAPER_RUN_USER" ]; then
        run_as_root chown -R "$SCRAPER_RUN_USER:$SCRAPER_RUN_GROUP" "$SCRAPER_VENV_DIR"
    fi
}

guard_scoped_path "SCRAPER_BASE_DIR" "$SCRAPER_BASE_DIR"
guard_child_path "SCRAPER_APP_DIR" "$SCRAPER_APP_DIR"
guard_child_path "SCRAPER_VENV_DIR" "$SCRAPER_VENV_DIR"

[ -n "$PYTHON_BIN" ] || fail "python3 was not found on PATH"
id "$SCRAPER_RUN_USER" >/dev/null 2>&1 || fail "SCRAPER_RUN_USER does not exist on this host: $SCRAPER_RUN_USER"
SCRAPER_RUN_GROUP="${SCRAPER_RUN_GROUP:-$(id -gn "$SCRAPER_RUN_USER")}"

if [ -e "$SCRAPER_VENV_DIR" ] && [ ! -f "$SCRAPER_VENV_DIR/pyvenv.cfg" ]; then
    fail "SCRAPER_VENV_DIR exists but is not a Python virtualenv: $SCRAPER_VENV_DIR"
fi

info "Preparing scraper directories under $SCRAPER_BASE_DIR ..."
install_dir 0750 "$SCRAPER_BASE_DIR"
install_dir 0750 "$SCRAPER_APP_DIR"
install_dir 0750 "$SCRAPER_BASE_DIR/logs"
install_dir 0750 "$SCRAPER_BASE_DIR/output"
install_dir 0700 "$SCRAPER_BASE_DIR/raw"
install_dir 0750 "$SCRAPER_BASE_DIR/run"
install_dir 0700 "$SCRAPER_BASE_DIR/state"
install_dir 0700 "$SCRAPER_BASE_DIR/tmp"

info "Creating or refreshing virtualenv at $SCRAPER_VENV_DIR ..."
"$PYTHON_BIN" -m venv "$SCRAPER_VENV_DIR"
chown_venv_if_needed

VENV_PYTHON="$SCRAPER_VENV_DIR/bin/python"
[ -x "$VENV_PYTHON" ] || fail "virtualenv python was not created at $VENV_PYTHON"

"$VENV_PYTHON" - <<'PY'
import sys

if sys.prefix == sys.base_prefix:
    raise SystemExit("virtualenv safety check failed: pip target is not isolated")
PY

if [ "${SCRAPER_SKIP_PIP_INSTALL:-0}" = "1" ]; then
    info "Skipping pip install because SCRAPER_SKIP_PIP_INSTALL=1."
elif [ -f "$SCRAPER_REQUIREMENTS" ]; then
    info "Installing Python requirements from $SCRAPER_REQUIREMENTS ..."
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_REQUIRE_VIRTUALENV=true \
        "$VENV_PYTHON" -m pip install --requirement "$SCRAPER_REQUIREMENTS" --upgrade-strategy only-if-needed
else
    info "No requirements file found at $SCRAPER_REQUIREMENTS; skipping pip install."
fi
chown_venv_if_needed

BOOTSTRAP_MARKER="$SCRAPER_BASE_DIR/state/bootstrap.ok"
{
    printf 'bootstrapped_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'base_dir=%s\n' "$SCRAPER_BASE_DIR"
    printf 'venv_dir=%s\n' "$SCRAPER_VENV_DIR"
} > "$BOOTSTRAP_MARKER"
if [ "$(id -u)" -eq 0 ] || [ "$(id -un)" != "$SCRAPER_RUN_USER" ]; then
    run_as_root chown "$SCRAPER_RUN_USER:$SCRAPER_RUN_GROUP" "$BOOTSTRAP_MARKER"
fi

info ""
info "Bootstrap complete."
info "Base:   $SCRAPER_BASE_DIR"
info "Venv:   $SCRAPER_VENV_DIR"
info "Output: $SCRAPER_BASE_DIR/output"
info ""
info "Run one collection/sanitization pass later with:"
info "  $SCRIPT_DIR/run-once.sh"
