#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUNTIME_DIR="evidence/outputs/runtime/policy-blocked-live-demo"
REPORT_JSON="$RUNTIME_DIR/report.json"
CONTROL_LOG="$RUNTIME_DIR/control-server.log"
PORT="${PROPHET_POLICY_BLOCKED_DEMO_PORT:-8792}"

die() {
  echo "error: $*" >&2
  exit 2
}

ensure_ignored_runtime_path() {
  local path="$1"
  if [[ "$path" != evidence/outputs/runtime && "$path" != evidence/outputs/runtime/* ]]; then
    die "refusing to write outside evidence/outputs/runtime: $path"
  fi
  if git check-ignore -q -- "$path" || git check-ignore -q -- "${path%/}/"; then
    return 0
  fi
  die "refusing to write path that is not ignored by git: $path"
}

ensure_ignored_runtime_path "$RUNTIME_DIR"
ensure_ignored_runtime_path "$REPORT_JSON"
ensure_ignored_runtime_path "$CONTROL_LOG"
mkdir -p "$RUNTIME_DIR"

export PROPHET_POLICY_BLOCKED_DEMO_PORT="$PORT"
export PROPHET_POLICY_BLOCKED_DEMO_RUNTIME_DIR="$RUNTIME_DIR"
export PROPHET_POLICY_BLOCKED_DEMO_REPORT="$REPORT_JSON"
export PROPHET_POLICY_BLOCKED_DEMO_LOG="$CONTROL_LOG"

node --input-type=module <<'NODE'
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const repoRoot = process.cwd();
const consoleRoot = path.join(repoRoot, 'prophet-console');
const runtimeDir = path.join(repoRoot, process.env.PROPHET_POLICY_BLOCKED_DEMO_RUNTIME_DIR);
const reportPath = path.join(repoRoot, process.env.PROPHET_POLICY_BLOCKED_DEMO_REPORT);
const controlLogPath = path.join(repoRoot, process.env.PROPHET_POLICY_BLOCKED_DEMO_LOG);
const port = Number(process.env.PROPHET_POLICY_BLOCKED_DEMO_PORT || 8792);
const baseUrl = `http://127.0.0.1:${port}`;

let stdout = '';
let stderr = '';

await mkdir(runtimeDir, { recursive: true });

const child = spawn(process.execPath, ['./control-server.mjs'], {
  cwd: consoleRoot,
  env: {
    ...process.env,
    PROPHET_CONTROL_PORT: String(port),
    PROPHET_ENABLE_VM_SCRAPER: '0',
    SCRAPER_SSH_TARGET: 'localhost-policy-blocked-fixture',
    PROPHET_OPERATOR_AUDIT_LOG: path.join(
      process.env.PROPHET_POLICY_BLOCKED_DEMO_RUNTIME_DIR,
      'operator-audit-log.jsonl',
    ),
    PROPHET_APPROVAL_RECORD_JSON: path.join(
      process.env.PROPHET_POLICY_BLOCKED_DEMO_RUNTIME_DIR,
      'approval-record.json',
    ),
  },
  stdio: ['ignore', 'pipe', 'pipe'],
});

child.stdout.on('data', (chunk) => {
  stdout += chunk.toString();
});
child.stderr.on('data', (chunk) => {
  stderr += chunk.toString();
});

try {
  const healthBefore = await waitForHealth();
  const policyStatusResponse = await fetch(`${baseUrl}/api/policy/status`);
  const policyStatus = await policyStatusResponse.json();
  assert(policyStatusResponse.status === 200, `expected policy status HTTP 200, got ${policyStatusResponse.status}`);
  assert(policyStatus.ok === true, 'policy status payload.ok must be true');

  const liveVmGate = policyStatus.actionGates?.find((gate) => gate.id === 'live_vm_scraper');
  assert(liveVmGate?.status === 'blocked', 'live collection gate must be blocked by policy');
  assert(
    policyStatus.blockedControls?.includes('live_vm_scraper_allowed'),
    'blocked controls must include live_vm_scraper_allowed',
  );
  assert(
    policyStatus.policy?.controls?.live_vm_scraper_allowed === false,
    'pilot policy must keep live_vm_scraper_allowed false',
  );

  const deniedResponse = await fetch(`${baseUrl}/api/scraper/run`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'policy-blocked-demo',
    },
  });
  const deniedPayload = await deniedResponse.json();
  assert(deniedResponse.status === 403, `expected policy-blocked HTTP 403, got ${deniedResponse.status}`);
  assert(deniedPayload.ok === false, 'denial payload.ok must be false');
  assert(deniedPayload.status === 'policy_blocked', `unexpected denial status: ${deniedPayload.status}`);
  assert(
    /policy blocks live collection/i.test(deniedPayload.message ?? ''),
    'denial message must explain that policy blocks live collection',
  );
  assert(
    deniedPayload.policy?.policySha256 === policyStatus.policy?.policySha256,
    'denial policy hash must match policy status hash',
  );

  const healthAfter = await (await fetch(`${baseUrl}/health`)).json();
  assert(
    JSON.stringify(healthAfter.lastResult ?? null) === JSON.stringify(healthBefore.lastResult ?? null),
    'policy-blocked request must not start or mutate a control workflow result',
  );

  const report = {
    schema_version: 'prophet_policy_blocked_live_demo.v0.1',
    generated_at: process.env.PROPHET_GENERATED_AT || '2026-05-05T08:45:00Z',
    control_server: {
      base_url: baseUrl,
      localhost_only: true,
      vm_scraper_enabled: Boolean(policyStatus.summary?.vmScraperEnabled),
    },
    attempted_action: {
      method: 'POST',
      endpoint: '/api/scraper/run',
      description: 'live collection workflow request',
      expected_policy_control: 'live_vm_scraper_allowed',
    },
    policy: {
      policy_id: policyStatus.policy?.policyId,
      policy_sha256: policyStatus.policy?.policySha256,
      gate_status: liveVmGate.status,
      blocked_controls: policyStatus.blockedControls,
    },
    denial: {
      http_status: deniedResponse.status,
      status: deniedPayload.status,
      message: deniedPayload.message,
      policy_sha256: deniedPayload.policy?.policySha256,
    },
    safety_attestation: {
      localhost_only_request: true,
      no_live_targets_contacted: true,
      no_payload_generation: true,
      no_credentials: true,
      no_raw_scraper_text: true,
      no_workflow_started_after_denial: true,
      runtime_output_ignored: true,
    },
  };
  const reportBody = `${JSON.stringify(report, null, 2)}\n`;
  await writeFile(reportPath, reportBody, 'utf8');
  const reportSha256 = createHash('sha256').update(reportBody).digest('hex');

  console.log('Policy-blocked live behavior demo');
  console.log(`- Result: PASS`);
  console.log(`- Attempted action: POST /api/scraper/run on ${baseUrl}`);
  console.log(`- Expected denial: HTTP ${deniedResponse.status} ${deniedPayload.status}`);
  console.log(`- Policy: ${report.policy.policy_id} ${report.policy.policy_sha256}`);
  console.log(`- Report: ${path.relative(repoRoot, reportPath)}`);
  console.log(`- Report SHA-256: ${reportSha256}`);
  console.log('- Safety: localhost-only request, no live targets, no raw scraper text, no credentials, no payload generation.');
} finally {
  child.kill('SIGTERM');
  await waitForExit(child);
  await writeFile(
    controlLogPath,
    `STDOUT\n${stdout}\n\nSTDERR\n${stderr}\n`,
    'utf8',
  );
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`${message}\n\ncontrol server stderr:\n${stderr}`);
  }
}

async function waitForHealth() {
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) return response.json();
    } catch {
      // Server is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`control server did not start\n${stderr}`);
}

async function waitForExit(process) {
  if (process.exitCode !== null || process.signalCode !== null) return;
  await Promise.race([
    new Promise((resolve) => process.once('exit', resolve)),
    new Promise((resolve) => setTimeout(resolve, 2_000)),
  ]);
}
NODE
