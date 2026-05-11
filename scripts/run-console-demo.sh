#!/usr/bin/env bash
set -euo pipefail

CONTROL_PORT="${PROPHET_CONTROL_PORT:-8787}"
UI_HOST="${PROPHET_CONSOLE_HOST:-127.0.0.1}"
UI_PORT="${PROPHET_CONSOLE_PORT:-5173}"
CONTROL_PID=""
UI_PID=""

usage() {
  cat <<'USAGE'
Usage: ./scripts/run-console-demo.sh

Start the safe local Prophet evaluator console in one terminal.

Environment:
  PROPHET_CONTROL_PORT  Control API port, default 8787.
  PROPHET_CONSOLE_HOST  UI host, default 127.0.0.1; must be 127.0.0.1 or localhost.
  PROPHET_CONSOLE_PORT  UI port, default 5173.

The launcher starts:
  - localhost-only control API at http://127.0.0.1:8787
  - evaluator UI at http://127.0.0.1:5173

Run `cd prophet-console && npm ci` before this launcher on a fresh checkout.

Press Ctrl-C to stop both processes. This does not enable live collection,
production pushes, live target validation, or offensive workflows.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

cleanup() {
  local exit_code=$?
  if [[ -n "$UI_PID" ]] && kill -0 "$UI_PID" >/dev/null 2>&1; then
    kill "$UI_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$CONTROL_PID" ]] && kill -0 "$CONTROL_PID" >/dev/null 2>&1; then
    kill "$CONTROL_PID" >/dev/null 2>&1 || true
  fi
  wait "$UI_PID" >/dev/null 2>&1 || true
  wait "$CONTROL_PID" >/dev/null 2>&1 || true
  exit "$exit_code"
}

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "error: missing required command '$name'" >&2
    exit 1
  fi
}

require_localhost_host() {
  local host="$1"
  case "$host" in
    127.0.0.1|localhost)
      ;;
    *)
      echo "error: console host must be localhost-only; set PROPHET_CONSOLE_HOST to 127.0.0.1 or localhost" >&2
      exit 1
      ;;
  esac
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local deadline=$((SECONDS + 30))
  while ! curl -fsS "$url" >/dev/null 2>&1; do
    if [[ -n "$CONTROL_PID" ]] && ! kill -0 "$CONTROL_PID" >/dev/null 2>&1; then
      echo "error: control server exited before $label was ready" >&2
      return 1
    fi
    if [[ -n "$UI_PID" ]] && ! kill -0 "$UI_PID" >/dev/null 2>&1; then
      echo "error: console UI exited before $label was ready" >&2
      return 1
    fi
    if [[ "$SECONDS" -ge "$deadline" ]]; then
      echo "error: timed out waiting for $label at $url" >&2
      return 1
    fi
    sleep 1
  done
}

require_port_available() {
  local host="$1"
  local port="$2"
  local label="$3"
  if ! python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
except OSError:
    raise SystemExit(1)
PY
  then
    echo "error: $label port $port is already in use on $host" >&2
    echo "If this is an existing Prophet demo, verify it with make console-live-check before starting another one." >&2
    echo "Otherwise stop the existing process or set PROPHET_${label}_PORT to another port before running make console-demo." >&2
    exit 1
  fi
}

require_localhost_host "$UI_HOST"
require_command curl
require_command npm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

"$REPO_ROOT/scripts/check-local-env.sh" --strict-console

if [[ ! -x "$REPO_ROOT/prophet-console/node_modules/.bin/vite" ]]; then
  echo "error: console dependencies are not installed; run 'cd prophet-console && npm ci' before make console-demo" >&2
  exit 1
fi

require_port_available "127.0.0.1" "$CONTROL_PORT" "CONTROL"
require_port_available "$UI_HOST" "$UI_PORT" "CONSOLE"

trap cleanup INT TERM EXIT

cd "$REPO_ROOT/prophet-console"

echo "Starting Prophet local evaluator console..."
PROPHET_CONTROL_PORT="$CONTROL_PORT" npm run dev:control &
CONTROL_PID=$!

npm run dev:evaluator -- --host "$UI_HOST" --port "$UI_PORT" --strictPort &
UI_PID=$!

wait_for_url "http://127.0.0.1:${CONTROL_PORT}/api/readiness" "control readiness"
wait_for_url "http://${UI_HOST}:${UI_PORT}/" "evaluator UI"

echo
echo "Prophet console is running:"
echo "  Evaluator UI: http://${UI_HOST}:${UI_PORT}/"
echo "  Readiness:    http://127.0.0.1:${CONTROL_PORT}/api/readiness"
echo
echo "Press Ctrl-C to stop both local processes."

while :; do
  if ! kill -0 "$CONTROL_PID" >/dev/null 2>&1; then
    echo "control server exited" >&2
    wait "$CONTROL_PID"
    exit $?
  fi
  if ! kill -0 "$UI_PID" >/dev/null 2>&1; then
    echo "console UI exited" >&2
    wait "$UI_PID"
    exit $?
  fi
  sleep 1
done
