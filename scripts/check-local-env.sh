#!/usr/bin/env bash
set -euo pipefail

STRICT_CONSOLE=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-local-env.sh [--strict-console]

Check local prerequisites for the safe Prophet buyer pilot.

Options:
  --strict-console   Require Node 24 or newer and npm for console acceptance.
  -h, --help         Show this help text.

The root pilot smoke requires Python 3.9+, bash, git, and shasum.
The console path additionally requires Node 24+ and npm.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict-console)
      STRICT_CONSOLE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

FAILURES=0
WARNINGS=0

ok() {
  printf '[ok] %s\n' "$*"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf '[warn] %s\n' "$*"
}

fail() {
  FAILURES=$((FAILURES + 1))
  printf '[fail] %s\n' "$*"
}

require_command() {
  local name="$1"
  local description="$2"
  if command -v "$name" >/dev/null 2>&1; then
    ok "$description: $(command -v "$name")"
  else
    fail "$description: missing command '$name'"
  fi
}

optional_command() {
  local name="$1"
  local description="$2"
  if command -v "$name" >/dev/null 2>&1; then
    ok "$description: $(command -v "$name")"
  elif [[ "$STRICT_CONSOLE" -eq 1 ]]; then
    fail "$description: missing command '$name'"
  else
    warn "$description: missing command '$name' (required only for console path)"
  fi
}

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3: missing; install Python 3.9 or newer"
    return
  fi

  local version
  version="$(python3 --version 2>&1)"
  if python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
  then
    ok "python3: $version"
  else
    fail "python3: $version; require Python 3.9 or newer"
  fi
}

check_node() {
  if ! command -v node >/dev/null 2>&1; then
    if [[ "$STRICT_CONSOLE" -eq 1 ]]; then
      fail "node: missing; install Node 24 or newer for console acceptance"
    else
      warn "node: missing (required only for console path)"
    fi
    return
  fi

  local version major
  version="$(node --version 2>&1)"
  major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || printf '0')"
  if [[ "$major" -ge 24 ]]; then
    ok "node: $version"
  elif [[ "$STRICT_CONSOLE" -eq 1 ]]; then
    fail "node: $version; require Node 24 or newer for console acceptance"
  else
    warn "node: $version; Node 24 or newer is required only for console acceptance"
  fi
}

printf 'Prophet local environment check\n'
check_python
require_command bash "bash"
require_command git "git"
require_command shasum "shasum"
check_node
optional_command npm "npm"

if [[ "$FAILURES" -gt 0 ]]; then
  printf 'Result: blocked for root pilot smoke (%s failure(s), %s warning(s)).\n' "$FAILURES" "$WARNINGS"
  exit 1
fi

if [[ "$WARNINGS" -gt 0 ]]; then
  printf 'Result: ready for root pilot smoke; console path has %s warning(s).\n' "$WARNINGS"
else
  printf 'Result: ready for root pilot smoke and console path.\n'
fi
