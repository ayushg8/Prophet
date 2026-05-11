#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

START_EPOCH="$(date +%s)"

export PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/cyber-side:${ROOT_DIR}/world-side:${ROOT_DIR}/world-side/scraper${PYTHONPATH:+:${PYTHONPATH}}"

GENERATED_AT="2026-05-04T20:30:00Z"
POLICY="policy/prophet-pilot-policy.json"
SECTOR="edge-appliance"
TOTAL_STEPS=13

HASH_MANIFEST=""
ASSET_CSV=""
ASSET_INVENTORY=""
CSV_INVENTORY=""
CSV_IMPORT_REPORT=""
CSV_IMPORT_MANIFEST=""
CSV_SEEDSET=""
ASSET_SEEDSET=""
SEEDED_OSINT_JSONL=""
SEEDED_OSINT_MANIFEST=""
FORECAST_OUT=""
PORTFOLIO_OUT=""
SANDBOX_ARTIFACT=""
SANDBOX_RUN_MANIFEST=""
EVIDENCE_JSON=""
EVIDENCE_MD=""
INTEGRATION_OUT_DIR=""
INTEGRATION_ZIP=""
AUDIT_LOG=""
APPROVAL_RECORD=""
AUDIT_EXPORT=""
AUDIT_RETENTION_REPORT=""
CANDIDATE=""
SANDBOX_PROFILE=""
CSV_IMPORT_ID=""
CSV_SCOPE=""
CSV_SEEDSET_RUN_ID=""
ASSET_SEEDSET_RUN_ID=""
SANDBOX_RUN_ID=""
EVIDENCE_RUN_ID=""
INTEGRATION_EXPORT_ID=""
SECTOR_SUMMARY=""

RUNTIME_DIRS=(
  "assets/outputs/runtime"
  "world-side/outputs/runtime"
  "cyber-side/outputs/runtime"
  "evidence/outputs/runtime"
  "integrations/outputs/runtime"
)

GENERATED_FILES=()
RUNTIME_POLICY_ARTIFACTS=()

DRY_RUN=0
CLEAN_RUNTIME=0
CLEAN_RUNTIME_CONFIRMED=0

configure_sector() {
  case "$SECTOR" in
    edge-appliance)
      HASH_MANIFEST="scripts/pilot-demo-smoke.sha256"
      ASSET_CSV="assets/fixtures/dib-edge-appliance-inventory.csv"
      ASSET_INVENTORY="assets/fixtures/dib-edge-appliance-inventory.json"
      CSV_INVENTORY="assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.json"
      CSV_IMPORT_REPORT="assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.report.json"
      CSV_IMPORT_MANIFEST="assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.manifest.json"
      CSV_SEEDSET="assets/outputs/runtime/demo-dib-edge-appliance-seedset-from-csv.json"
      ASSET_SEEDSET="assets/outputs/runtime/demo-dib-edge-appliance-seedset.json"
      SEEDED_OSINT_JSONL="world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.jsonl"
      SEEDED_OSINT_MANIFEST="world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.manifest.json"
      FORECAST_OUT="world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json"
      PORTFOLIO_OUT="cyber-side/outputs/runtime/latest-prediction-portfolio-edge-appliance.json"
      SANDBOX_ARTIFACT="cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json"
      SANDBOX_RUN_MANIFEST="cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json"
      EVIDENCE_JSON="evidence/outputs/runtime/latest-edge-appliance.json"
      EVIDENCE_MD="evidence/outputs/runtime/latest-edge-appliance.md"
      INTEGRATION_OUT_DIR="integrations/outputs/runtime/latest-edge-appliance"
      INTEGRATION_ZIP="integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip"
      AUDIT_LOG="evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl"
      APPROVAL_RECORD="evidence/outputs/runtime/pilot-demo-approval-record.json"
      AUDIT_EXPORT="evidence/outputs/runtime/pilot-demo-operator-audit-export.json"
      AUDIT_RETENTION_REPORT="evidence/outputs/runtime/pilot-demo-operator-audit-retention.json"
      CANDIDATE="world-side/fixtures/exploit-candidate-edge-appliance.json"
      SANDBOX_PROFILE="edge-appliance-fixture"
      CSV_IMPORT_ID="demo-dib-edge-appliance-csv-import"
      CSV_SCOPE="Fictional defense-industrial CSV inventory; product-family metadata only."
      CSV_SEEDSET_RUN_ID="pilot-demo-csv-seedset"
      ASSET_SEEDSET_RUN_ID="pilot-demo-asset-seedset"
      SANDBOX_RUN_ID="pilot-demo-sandbox"
      EVIDENCE_RUN_ID="pilot-demo-evidence"
      INTEGRATION_EXPORT_ID="pilot-demo-integration-export"
      SECTOR_SUMMARY="edge-appliance defense-industrial fixture"
      ;;
    financial-workflow)
      HASH_MANIFEST="scripts/pilot-demo-smoke-financial-workflow.sha256"
      ASSET_CSV="assets/fixtures/financial-workflow-inventory.csv"
      ASSET_INVENTORY="assets/fixtures/financial-workflow-inventory.json"
      CSV_INVENTORY="assets/outputs/runtime/demo-financial-workflow-inventory-from-csv.json"
      CSV_IMPORT_REPORT="assets/outputs/runtime/demo-financial-workflow-inventory-from-csv.report.json"
      CSV_IMPORT_MANIFEST="assets/outputs/runtime/demo-financial-workflow-inventory-from-csv.manifest.json"
      CSV_SEEDSET="assets/outputs/runtime/demo-financial-workflow-seedset-from-csv.json"
      ASSET_SEEDSET="assets/outputs/runtime/demo-financial-workflow-seedset.json"
      SEEDED_OSINT_JSONL="world-side/outputs/runtime/demo-seeded-osint-snapshot-financial-workflow.jsonl"
      SEEDED_OSINT_MANIFEST="world-side/outputs/runtime/demo-seeded-osint-snapshot-financial-workflow.manifest.json"
      FORECAST_OUT="world-side/outputs/runtime/demo-scraper-forecast-financial-workflow.json"
      PORTFOLIO_OUT="cyber-side/outputs/runtime/latest-prediction-portfolio-financial-workflow.json"
      SANDBOX_ARTIFACT="cyber-side/outputs/runtime/latest-sandbox-artifact-financial-workflow.json"
      SANDBOX_RUN_MANIFEST="cyber-side/outputs/runtime/latest-sandbox-run-manifest-financial-workflow.json"
      EVIDENCE_JSON="evidence/outputs/runtime/latest-financial-workflow.json"
      EVIDENCE_MD="evidence/outputs/runtime/latest-financial-workflow.md"
      INTEGRATION_OUT_DIR="integrations/outputs/runtime/latest-financial-workflow"
      INTEGRATION_ZIP="integrations/outputs/runtime/latest-financial-workflow-review-bundle.zip"
      AUDIT_LOG="evidence/outputs/runtime/pilot-demo-financial-workflow-operator-audit-log.jsonl"
      APPROVAL_RECORD="evidence/outputs/runtime/pilot-demo-financial-workflow-approval-record.json"
      AUDIT_EXPORT="evidence/outputs/runtime/pilot-demo-financial-workflow-operator-audit-export.json"
      AUDIT_RETENTION_REPORT="evidence/outputs/runtime/pilot-demo-financial-workflow-operator-audit-retention.json"
      CANDIDATE="world-side/fixtures/exploit-candidate-financial-theft.json"
      SANDBOX_PROFILE="financial-workflow-fixture"
      CSV_IMPORT_ID="demo-financial-workflow-csv-import"
      CSV_SCOPE="Fictional financial workflow CSV inventory; product-family and workflow-class metadata only."
      CSV_SEEDSET_RUN_ID="pilot-demo-financial-workflow-csv-seedset"
      ASSET_SEEDSET_RUN_ID="pilot-demo-financial-workflow-asset-seedset"
      SANDBOX_RUN_ID="pilot-demo-financial-workflow-sandbox"
      EVIDENCE_RUN_ID="pilot-demo-financial-workflow-evidence"
      INTEGRATION_EXPORT_ID="pilot-demo-financial-workflow-integration-export"
      SECTOR_SUMMARY="financial workflow fixture"
      ;;
    *)
      die "unknown sector: $SECTOR"
      ;;
  esac

  GENERATED_FILES=(
    "$CSV_INVENTORY"
    "$CSV_IMPORT_REPORT"
    "$CSV_IMPORT_MANIFEST"
    "$CSV_SEEDSET"
    "$ASSET_SEEDSET"
    "$SEEDED_OSINT_JSONL"
    "$SEEDED_OSINT_MANIFEST"
    "$FORECAST_OUT"
    "$PORTFOLIO_OUT"
    "$SANDBOX_ARTIFACT"
    "$SANDBOX_RUN_MANIFEST"
    "$EVIDENCE_JSON"
    "$EVIDENCE_MD"
    "$AUDIT_LOG"
    "$APPROVAL_RECORD"
    "$AUDIT_EXPORT"
    "$AUDIT_RETENTION_REPORT"
    "$INTEGRATION_OUT_DIR/manifest.json"
    "$INTEGRATION_OUT_DIR/siem/splunk_saved_search.json"
    "$INTEGRATION_OUT_DIR/siem/elastic_detection_rule.ndjson"
    "$INTEGRATION_OUT_DIR/siem/sentinel_analytic_rule.json"
    "$INTEGRATION_OUT_DIR/tickets/jira_remediation_ticket.json"
    "$INTEGRATION_OUT_DIR/tickets/servicenow_remediation_task.json"
    "$INTEGRATION_OUT_DIR/audit/operator_approval_event.json"
    "$INTEGRATION_OUT_DIR/review_checklist.md"
    "$INTEGRATION_ZIP"
  )

  RUNTIME_POLICY_ARTIFACTS=(
    "$SEEDED_OSINT_MANIFEST"
    "$SANDBOX_ARTIFACT"
    "$SANDBOX_RUN_MANIFEST"
    "$APPROVAL_RECORD"
    "$AUDIT_EXPORT"
    "$AUDIT_RETENTION_REPORT"
    "$EVIDENCE_JSON"
    "$INTEGRATION_OUT_DIR/manifest.json"
    "$INTEGRATION_OUT_DIR/audit/operator_approval_event.json"
  )
}

usage() {
  cat <<USAGE
Usage: ./scripts/run-pilot-demo-smoke.sh [--sector edge-appliance|financial-workflow] [--dry-run] [--clean-runtime] [--yes]

Options:
  --sector NAME    Smoke sector to run. Defaults to edge-appliance.
  --dry-run         Print the runtime outputs this smoke run would generate.
  --clean-runtime   Remove existing ignored runtime outputs before running.
  --yes             Confirm --clean-runtime in non-interactive automation.
  -h, --help        Show this help text.

Safety:
  --clean-runtime only touches the known outputs/runtime directories and first
  verifies each target is ignored by git. Without --yes, type "clean runtime"
  at the prompt to confirm.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 2
}

is_under_runtime_dir() {
  local path="$1"
  local runtime_dir
  for runtime_dir in "${RUNTIME_DIRS[@]}"; do
    if [[ "$path" == "$runtime_dir" || "$path" == "$runtime_dir/"* ]]; then
      return 0
    fi
  done
  return 1
}

ensure_ignored_runtime_path() {
  local path="$1"
  is_under_runtime_dir "$path" || die "refusing to clean non-runtime path: $path"
  if git check-ignore -q -- "$path" || git check-ignore -q -- "${path%/}/"; then
    return 0
  fi
  die "refusing to clean path that is not ignored by git: $path"
}

print_dry_run() {
  echo "Pilot demo smoke dry run"
  echo
  echo "Runtime directories:"
  local runtime_dir
  for runtime_dir in "${RUNTIME_DIRS[@]}"; do
    echo "- $runtime_dir"
  done
  echo
  echo "Generated files:"
  local generated_file
  for generated_file in "${GENERATED_FILES[@]}"; do
    echo "- $generated_file"
  done
  if (( CLEAN_RUNTIME )); then
    echo
    echo "Cleanup preview:"
    for runtime_dir in "${RUNTIME_DIRS[@]}"; do
      ensure_ignored_runtime_path "$runtime_dir"
      if [[ -d "$runtime_dir" ]]; then
        echo "- would remove current contents of $runtime_dir"
      else
        echo "- $runtime_dir does not exist yet"
      fi
    done
  fi
}

confirm_clean_runtime() {
  if (( CLEAN_RUNTIME_CONFIRMED )); then
    return 0
  fi
  if [[ "${PROPHET_CONFIRM_CLEAN_RUNTIME:-}" == "clean-runtime" ]]; then
    return 0
  fi
  if [[ -t 0 ]]; then
    local answer
    read -r -p 'Type "clean runtime" to remove ignored runtime outputs before the smoke run: ' answer
    [[ "$answer" == "clean runtime" ]] && return 0
  fi
  die "--clean-runtime requires confirmation with --yes, PROPHET_CONFIRM_CLEAN_RUNTIME=clean-runtime, or the interactive prompt"
}

clean_runtime_outputs() {
  confirm_clean_runtime
  echo "Cleaning ignored runtime outputs"
  local runtime_dir entry
  for runtime_dir in "${RUNTIME_DIRS[@]}"; do
    ensure_ignored_runtime_path "$runtime_dir"
    mkdir -p "$runtime_dir"
    while IFS= read -r -d '' entry; do
      ensure_ignored_runtime_path "$entry"
      rm -rf -- "$entry"
    done < <(find "$runtime_dir" -mindepth 1 -maxdepth 1 -print0)
  done
}

while (($#)); do
  case "$1" in
    --sector)
      [[ $# -ge 2 ]] || die "--sector requires a value"
      SECTOR="$2"
      shift
      ;;
    --sector=*)
      SECTOR="${1#--sector=}"
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    --clean-runtime)
      CLEAN_RUNTIME=1
      ;;
    --yes)
      CLEAN_RUNTIME_CONFIRMED=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "unknown argument: $1"
      ;;
  esac
  shift
done

configure_sector

if (( DRY_RUN )); then
  print_dry_run
  exit 0
fi

if (( CLEAN_RUNTIME )); then
  clean_runtime_outputs
fi

mkdir -p \
  assets/outputs/runtime \
  world-side/outputs/runtime \
  cyber-side/outputs/runtime \
  evidence/outputs/runtime \
  integrations/outputs/runtime

echo "[1/${TOTAL_STEPS}] Linting pilot policy"
python3 -m policy.lint --policy "$POLICY"

echo "[2/${TOTAL_STEPS}] Importing customer-safe CSV asset inventory"
python3 -m assets.import_csv \
  --csv "$ASSET_CSV" \
  --inventory-id "$CSV_IMPORT_ID" \
  --scope "$CSV_SCOPE" \
  --generated-at "$GENERATED_AT" \
  --fixture \
  --out "$CSV_INVENTORY" \
  --report-out "$CSV_IMPORT_REPORT" \
  --seedset-out "$CSV_SEEDSET" \
  --seedset-run-id "$CSV_SEEDSET_RUN_ID" \
  --manifest-out "$CSV_IMPORT_MANIFEST"

echo "[3/${TOTAL_STEPS}] Generating asset/SBOM seedset"
python3 -m assets.inventory \
  --inventory "$ASSET_INVENTORY" \
  --generated-at "$GENERATED_AT" \
  --run-id "$ASSET_SEEDSET_RUN_ID" \
  --out "$ASSET_SEEDSET"

echo "[4/${TOTAL_STEPS}] Building fixture-backed seeded OSINT snapshot"
python3 -m scraper_side.snapshot \
  --catalog world-side/scraper/config/source_catalog.json \
  --source cisa_vulnrichment_cve_record_seed \
  --source osv_query_api_seed \
  --source redhat_security_data_cve_api \
  --asset-seedset "$ASSET_SEEDSET" \
  --seed-fixture-dir world-side/fixtures/seeded-osint \
  --policy "$POLICY" \
  --generated-at "$GENERATED_AT" \
  --limit-per-source 1 \
  --max-seeds-per-source 4 \
  --max-records 50 \
  --require-records \
  --out-jsonl "$SEEDED_OSINT_JSONL" \
  --out-manifest "$SEEDED_OSINT_MANIFEST"

echo "[5/${TOTAL_STEPS}] Refreshing forecast from sanitized fixtures and seeded OSINT"
python3 -m forecaster.cli \
  --candidate "$CANDIDATE" \
  --chatter world-side/fixtures/sanitized-chatter-sample.jsonl \
  --osint-snapshot world-side/fixtures/osint-snapshot-sample.jsonl \
  --osint-manifest world-side/fixtures/osint-snapshot-sample.manifest.json \
  --osint-snapshot "$SEEDED_OSINT_JSONL" \
  --osint-manifest "$SEEDED_OSINT_MANIFEST" \
  --asset-seedset "$ASSET_SEEDSET" \
  --generated-at "$GENERATED_AT" \
  --out "$FORECAST_OUT"

echo "[6/${TOTAL_STEPS}] Generating safe exposure-class defense portfolio"
python3 -m predictor \
  --forecast "$FORECAST_OUT" \
  --candidate "$CANDIDATE" \
  --generated-at "$GENERATED_AT" \
  --out "$PORTFOLIO_OUT"

echo "[7/${TOTAL_STEPS}] Emitting deterministic localhost sandbox artifact and run manifest"
python3 -m sandbox_runner run \
  --profile "$SANDBOX_PROFILE" \
  --policy "$POLICY" \
  --generated-at "$GENERATED_AT" \
  --run-id "$SANDBOX_RUN_ID" \
  --out "$SANDBOX_ARTIFACT" \
  --manifest-out "$SANDBOX_RUN_MANIFEST"

echo "[8/${TOTAL_STEPS}] Generating policy-bound evidence bundle"
python3 -m evidence.audit append \
  --log "$AUDIT_LOG" \
  --reset-log \
  --policy "$POLICY" \
  --event-type operator_approval \
  --operator-label fixture \
  --decision bypassed_for_fixture \
  --generated-at "$GENERATED_AT" \
  --run-id "$EVIDENCE_RUN_ID" \
  --artifact-id "$SANDBOX_RUN_ID" \
  --reason "fixture-approved pilot evidence generation" \
  --out-event "$APPROVAL_RECORD" >/dev/null
python3 -m evidence.bundle \
  --forecast "$FORECAST_OUT" \
  --portfolio "$PORTFOLIO_OUT" \
  --artifact "$SANDBOX_ARTIFACT" \
  --asset-inventory "$ASSET_INVENTORY" \
  --asset-seedset "$ASSET_SEEDSET" \
  --policy "$POLICY" \
  --approval-record "$APPROVAL_RECORD" \
  --sandbox-run-manifest "$SANDBOX_RUN_MANIFEST" \
  --operator-label fixture \
  --approval-decision bypassed_for_fixture \
  --generated-at "$GENERATED_AT" \
  --run-id "$EVIDENCE_RUN_ID" \
  --out-json "$EVIDENCE_JSON" \
  --out-md "$EVIDENCE_MD"

echo "[9/${TOTAL_STEPS}] Exporting safe audit summary and retention report"
python3 -m evidence.audit export \
  --log "$AUDIT_LOG" \
  --generated-at "$GENERATED_AT" \
  --out-json "$AUDIT_EXPORT" >/dev/null
python3 -m evidence.audit retention \
  --log "$AUDIT_LOG" \
  --policy "$POLICY" \
  --generated-at "$GENERATED_AT" \
  --out-json "$AUDIT_RETENTION_REPORT" >/dev/null

echo "[10/${TOTAL_STEPS}] Exporting safe SIEM and ticketing handoff templates"
python3 -m integrations.export \
  --bundle "$EVIDENCE_JSON" \
  --policy "$POLICY" \
  --generated-at "$GENERATED_AT" \
  --export-id "$INTEGRATION_EXPORT_ID" \
  --out-dir "$INTEGRATION_OUT_DIR" \
  --zip-out "$INTEGRATION_ZIP"

echo "[11/${TOTAL_STEPS}] Validating outputs and printing hashes"
python3 -c 'import json,sys; from validator import validate_exploit_engine_artifact; validate_exploit_engine_artifact(json.load(open(sys.argv[1], encoding="utf-8")))' "$SANDBOX_ARTIFACT"
python3 -c 'import json,sys; from sandbox_runner.schema import validate_sandbox_run_manifest_schema; validate_sandbox_run_manifest_schema(json.load(open(sys.argv[1], encoding="utf-8")))' "$SANDBOX_RUN_MANIFEST"
python3 -m evidence.audit validate --log "$AUDIT_LOG" >/dev/null
python3 -c 'from evidence.audit import validate_audit_export, validate_audit_retention_report; import json,sys; validate_audit_export(json.load(open(sys.argv[1], encoding="utf-8"))); validate_audit_retention_report(json.load(open(sys.argv[2], encoding="utf-8")))' "$AUDIT_EXPORT" "$AUDIT_RETENTION_REPORT"
python3 -c 'from evidence.bundle import load_json, validate_evidence_bundle; import sys; validate_evidence_bundle(load_json(sys.argv[1]))' "$EVIDENCE_JSON"
python3 -c 'from integrations.export import load_json, validate_integration_export; import sys; validate_integration_export(load_json(sys.argv[1]))' "$INTEGRATION_OUT_DIR/manifest.json"
python3 scripts/verify-pilot-demo-hashes.py --manifest "$HASH_MANIFEST"

echo "[12/${TOTAL_STEPS}] Checking default output URL safety"
python3 scripts/check-default-output-safety.py --policy "$POLICY" --format text

echo "[13/${TOTAL_STEPS}] Verifying runtime artifact policy hashes"
python3 -m policy.lint \
  --policy "$POLICY" \
  --verify-runtime-artifacts "${RUNTIME_POLICY_ARTIFACTS[@]}" >/dev/null

END_EPOCH="$(date +%s)"
ELAPSED_SECONDS="$((END_EPOCH - START_EPOCH))"
ELAPSED_MINUTES="$((ELAPSED_SECONDS / 60))"
ELAPSED_REMAINDER="$((ELAPSED_SECONDS % 60))"
if (( ELAPSED_MINUTES > 0 )); then
  ELAPSED_TEXT="${ELAPSED_MINUTES}m ${ELAPSED_REMAINDER}s"
else
  ELAPSED_TEXT="${ELAPSED_SECONDS}s"
fi

cat <<SUMMARY

Pilot demo smoke summary
- Result: PASS in ${ELAPSED_TEXT}.
- Sector: ${SECTOR_SUMMARY}.
- Mode: fixture-backed seeded OSINT, deterministic localhost sandbox, policy-bound exports.
- Safety: no live targets, no live target URLs, no raw scraper text, no credentials, no payload generation.
- Policy drift: generated runtime artifacts match ${POLICY}.
- Evidence bundle: ${EVIDENCE_MD}
- Audit review: ${AUDIT_EXPORT}
- Integration handoff templates: ${INTEGRATION_OUT_DIR}/manifest.json
- Integration review ZIP: ${INTEGRATION_ZIP}

SUMMARY
