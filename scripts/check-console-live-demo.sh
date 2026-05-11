#!/usr/bin/env bash
set -euo pipefail

CONTROL_PORT="${PROPHET_CONTROL_PORT:-8787}"
UI_HOST="${PROPHET_CONSOLE_HOST:-127.0.0.1}"
UI_PORT="${PROPHET_CONSOLE_PORT:-5173}"
PYTHONPATH_SAFE="${PYTHONPATH_SAFE:-.:cyber-side:world-side}"
OPERATOR_LABEL="${PROPHET_LIVE_CHECK_OPERATOR:-live-check}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-console-live-demo.sh

Check an already-running local Prophet evaluator console.

Environment:
  PROPHET_CONTROL_PORT        Control API port, default 8787.
  PROPHET_CONSOLE_HOST        UI host, default 127.0.0.1; must be 127.0.0.1 or localhost.
  PROPHET_CONSOLE_PORT        UI port, default 5173.
  PROPHET_LIVE_CHECK_OPERATOR Safe local audit operator label, default live-check.

This check calls the localhost-only readiness, evidence demo-bundle, and
integration demo-export endpoints. It writes only ignored runtime outputs and
local audit events. It does not enable live collection, live target validation,
production pushes, or offensive workflows.

Start the demo first with:

  make console-demo
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTROL_ORIGIN="http://127.0.0.1:${CONTROL_PORT}"
UI_ORIGIN="http://${UI_HOST}:${UI_PORT}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/prophet-console-live-check.XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

require_localhost_host "$UI_HOST"
require_command curl
require_command python3

cd "$REPO_ROOT"

readiness_json="$TMP_DIR/readiness.json"
evidence_json="$TMP_DIR/evidence.json"
integration_json="$TMP_DIR/integration.json"

curl -fsS "$CONTROL_ORIGIN/api/readiness" -o "$readiness_json"
curl -fsS "$UI_ORIGIN/" >/dev/null

python3 - "$readiness_json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

if payload.get("ok") is not True:
    raise SystemExit("readiness ok must be true")
if payload.get("summary", {}).get("blockingFailures") != 0:
    raise SystemExit("readiness blockingFailures must be 0")
PY

curl -fsS \
  -X POST \
  -H 'x-prophet-control: local-console' \
  -H "x-prophet-operator: ${OPERATOR_LABEL}" \
  "$CONTROL_ORIGIN/api/evidence/demo-bundle" \
  -o "$evidence_json"

audit_log="$(
  python3 - "$evidence_json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

if payload.get("ok") is not True:
    raise SystemExit(f"evidence endpoint failed: {payload.get('status')}")
if payload.get("status") != "evidence_bundle_generated":
    raise SystemExit(f"unexpected evidence status: {payload.get('status')}")
audit_event = payload.get("auditEvent") or {}
safety = audit_event.get("safety_attestation") or {}
if safety.get("no_live_target_data_included") is not True:
    raise SystemExit("evidence audit event missing no_live_target_data_included")
if not payload.get("bundle", {}).get("bundle_id"):
    raise SystemExit("evidence bundle_id missing")
print(payload.get("paths", {}).get("auditLog", ""))
PY
)"

curl -fsS \
  -X POST \
  -H 'x-prophet-control: local-console' \
  -H "x-prophet-operator: ${OPERATOR_LABEL}" \
  "$CONTROL_ORIGIN/api/integrations/demo-export" \
  -o "$integration_json"

python3 - "$integration_json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

if payload.get("ok") is not True:
    raise SystemExit(f"integration endpoint failed: {payload.get('status')}")
if payload.get("status") != "integration_handoff_exported":
    raise SystemExit(f"unexpected integration status: {payload.get('status')}")
audit_event = payload.get("auditEvent") or {}
safety = audit_event.get("safety_attestation") or {}
if safety.get("no_live_target_data_included") is not True:
    raise SystemExit("integration audit event missing no_live_target_data_included")
if payload.get("manifest", {}).get("mode") != "review_template_only":
    raise SystemExit("integration manifest must be review_template_only")
PY

if [[ -n "$audit_log" ]]; then
  PYTHONPATH="$PYTHONPATH_SAFE" python3 -m evidence.audit validate \
    --log "$audit_log" >/dev/null
fi

python3 - "$readiness_json" "$evidence_json" "$integration_json" "$UI_ORIGIN" "$CONTROL_ORIGIN" "$audit_log" <<'PY'
import json
import sys

readiness_path, evidence_path, integration_path, ui_origin, control_origin, audit_log = sys.argv[1:]
with open(readiness_path, encoding="utf-8") as handle:
    readiness = json.load(handle)
with open(evidence_path, encoding="utf-8") as handle:
    evidence = json.load(handle)
with open(integration_path, encoding="utf-8") as handle:
    integration = json.load(handle)

print("Prophet live console check passed.")
print(f"- UI: {ui_origin}")
print(f"- Readiness: {control_origin}/api/readiness")
print(f"- Blocking failures: {readiness.get('summary', {}).get('blockingFailures')}")
print(f"- Evidence endpoint: {evidence.get('status')} ({evidence.get('bundle', {}).get('bundle_id')})")
print(f"- Integration endpoint: {integration.get('status')} ({integration.get('manifest', {}).get('export_id')})")
if audit_log:
    print(f"- Audit log validated: {audit_log}")
PY
