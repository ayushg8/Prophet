import { spawn } from 'node:child_process';
import { mkdir, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const port = 8791;
const baseUrl = `http://127.0.0.1:${port}`;
const consoleRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = path.resolve(consoleRoot, '..');
const readinessTemp = await mkdtemp(path.join(tmpdir(), 'prophet-readiness-'));
const runtimeRoot = path.join(repoRoot, 'evidence/outputs/runtime');
await mkdir(runtimeRoot, { recursive: true });
const controlRuntimeTemp = await mkdtemp(path.join(runtimeRoot, 'control-evidence-smoke-'));
const operatorAuditLog = path.join(controlRuntimeTemp, 'operator-audit-log.jsonl');
const approvalRecordJson = path.join(controlRuntimeTemp, 'latest-approval-record.json');
const expectedAuditLogPath = path.relative(repoRoot, operatorAuditLog);
const expectedApprovalRecordPath = path.relative(repoRoot, approvalRecordJson);
const child = spawn('node', ['./control-server.mjs'], {
  cwd: consoleRoot,
  env: {
    ...process.env,
    PROPHET_CONTROL_PORT: String(port),
    PROPHET_OPERATOR_AUDIT_LOG: operatorAuditLog,
    PROPHET_APPROVAL_RECORD_JSON: approvalRecordJson,
    PROPHET_READINESS_EVIDENCE_RUNTIME_JSON: path.join(readinessTemp, 'missing-evidence.json'),
    PROPHET_READINESS_EVIDENCE_RUNTIME_MARKDOWN: path.join(readinessTemp, 'missing-evidence.md'),
    PROPHET_READINESS_INTEGRATION_MANIFEST: path.join(readinessTemp, 'missing-integration-manifest.json'),
    PROPHET_READINESS_OPERATOR_AUDIT_LOG: path.join(readinessTemp, 'missing-operator-audit-log.jsonl'),
  },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let stderr = '';
child.stderr.on('data', (chunk) => {
  stderr += chunk.toString();
});

try {
  const health = await waitForHealth();
  assert(
    health.policy?.policyId === 'prophet-pilot-fixture-localhost-v0.1',
    'health policy id missing',
  );
  assert(
    health.policy?.retention?.runtime_outputs_max_days === 30,
    'health policy retention hints missing',
  );
  const lastResultBeforeReadiness = JSON.stringify(health.lastResult ?? null);

  const policyStatusResponse = await fetch(`${baseUrl}/api/policy/status`);
  const policyStatus = await policyStatusResponse.json();
  assert(
    policyStatusResponse.status === 200,
    `expected policy status HTTP 200, got ${policyStatusResponse.status}`,
  );
  assert(policyStatus.ok === true, 'policy status payload.ok must be true');
  assert(
    policyStatus.policy?.policyId === 'prophet-pilot-fixture-localhost-v0.1',
    'policy status policy id missing',
  );
  assert(
    policyStatus.blockedControls?.includes('live_targets_allowed'),
    'policy status must expose blocked live target control',
  );
  const liveVmGate = policyStatus.actionGates?.find((gate) => gate.id === 'live_vm_scraper');
  assert(liveVmGate?.status === 'blocked', 'live VM scraper gate must be policy-blocked');
  const demoRefreshGate = policyStatus.actionGates?.find(
    (gate) => gate.id === 'fixture_demo_refresh',
  );
  assert(demoRefreshGate?.status === 'allowed', 'fixture demo refresh gate must be allowed');

  const liveRunResponse = await fetch(`${baseUrl}/api/scraper/run`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'control-smoke',
    },
  });
  const liveRunPayload = await liveRunResponse.json();
  assert(
    liveRunResponse.status === 403,
    `expected policy-blocked scraper HTTP 403, got ${liveRunResponse.status}`,
  );
  assert(
    liveRunPayload.status === 'policy_blocked',
    `unexpected live scraper block status: ${liveRunPayload.status}`,
  );
  assert(
    /policy blocks live vm scraper/i.test(liveRunPayload.message ?? ''),
    'live scraper block message must explain the policy denial',
  );

  const readinessResponse = await fetch(`${baseUrl}/api/readiness`);
  const readiness = await readinessResponse.json();
  assert(readinessResponse.status === 200, `expected readiness HTTP 200, got ${readinessResponse.status}`);
  assert(readiness.ok === true, 'readiness should not be blocked by missing runtime exports');
  assert(readiness.summary?.blockingFailures === 0, 'readiness should have no blocking failures');
  assert(Array.isArray(readiness.checks), 'readiness checks missing');
  const checkIds = readiness.checks.map((check) => check.id);
  for (const expectedId of [
    'pilot_policy',
    'safety_boundary',
    'forecast_fixture',
    'asset_seedset',
    'seeded_osint',
    'prediction_portfolio',
    'defense_artifact',
    'sandbox_runtime',
    'evidence_bundle',
    'integration_handoff',
    'operator_audit',
    'open_blockers',
  ]) {
    assert(checkIds.includes(expectedId), `readiness missing stable check id ${expectedId}`);
  }
  const evidenceCheck = readiness.checks.find((check) => check.id === 'evidence_bundle');
  assert(evidenceCheck?.status === 'warn', 'missing runtime evidence should warn');
  assert(evidenceCheck?.blocking === false, 'missing runtime evidence should not block');

  const healthAfterReadiness = await (await fetch(`${baseUrl}/health`)).json();
  assert(
    JSON.stringify(healthAfterReadiness.lastResult ?? null) === lastResultBeforeReadiness,
    'readiness endpoint must not mutate control server lastResult',
  );

  const denialResponse = await fetch(`${baseUrl}/api/evidence/deny`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'control-smoke',
    },
  });
  const denialPayload = await denialResponse.json();
  assert(denialResponse.status === 200, `expected denial HTTP 200, got ${denialResponse.status}`);
  assert(denialPayload.ok === true, 'denial payload.ok must be true');
  assert(
    denialPayload.status === 'operator_denial_recorded',
    `unexpected denial status: ${denialPayload.status}`,
  );
  assert(
    denialPayload.auditEvent?.event_type === 'operator_denial',
    'denial must write an operator_denial audit event',
  );
  assert(!denialPayload.bundle, 'denial path must not generate an evidence bundle');

  const sandboxResponse = await fetch(`${baseUrl}/api/cyber/sandbox-artifact`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'control-smoke',
    },
  });
  const sandboxPayload = await sandboxResponse.json();
  assert(sandboxResponse.status === 200, `expected sandbox HTTP 200, got ${sandboxResponse.status}`);
  assert(sandboxPayload.ok === true, 'sandbox payload.ok must be true');
  assert(
    sandboxPayload.path === 'cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json',
    'sandbox runtime path missing',
  );

  const response = await fetch(`${baseUrl}/api/evidence/demo-bundle`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'control-smoke',
    },
  });
  const payload = await response.json();
  assert(response.status === 200, `expected HTTP 200, got ${response.status}`);
  assert(payload.ok === true, 'payload.ok must be true');
  assert(payload.status === 'evidence_bundle_generated', `unexpected status: ${payload.status}`);
  assert(payload.bundle?.bundle_id, 'bundle_id missing');
  assert(payload.bundle?.bundle_sha256, 'bundle_sha256 missing');
  assert(payload.bundle?.policy?.policy_id === 'prophet-pilot-fixture-localhost-v0.1', 'policy missing');
  assert(payload.bundle?.hashes?.policy_sha256, 'policy hash missing');
  assert(payload.bundle?.operator_approval?.operator_label === 'control-smoke', 'operator label missing');
  assert(payload.bundle?.operator_approval?.approval_record_hash, 'approval record hash missing');
  assert(payload.bundle?.hashes?.approval_record_sha256, 'approval record hash not included in bundle hashes');
  assert(payload.auditEvent?.event_hash === payload.bundle?.operator_approval?.approval_record_hash, 'audit event hash should match evidence approval record');
  assert(payload.bundle?.open_source_summary?.freshness?.status === 'current', 'source freshness status missing');
  assert(
    payload.bundle?.open_source_summary?.source_health?.failed_source_count === 0,
    'source failure count missing',
  );
  assert(payload.paths?.approvalRecord === expectedApprovalRecordPath, 'approval record path missing');
  assert(payload.paths?.auditLog === expectedAuditLogPath, 'audit log path missing');
  assert(payload.artifactSource === 'sandbox_runtime', 'evidence should prefer sandbox runtime artifact');
  assert(
    payload.artifactSourceLabel === 'sandbox runtime artifact',
    'evidence artifact source label missing',
  );
  assert(payload.artifactMode === 'localhost_sandbox', 'evidence artifact mode missing');
  assert(
    payload.paths?.defenseArtifact ===
      'cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json',
    'evidence defense artifact source path missing',
  );
  assert(payload.bundle?.asset_seed_summary?.cve_seed_count === 4, 'asset seed summary missing');
  assert(payload.markdown?.includes('## Safety Attestation'), 'markdown missing safety section');
  assert(payload.markdown?.includes('## Policy Controls'), 'markdown missing policy section');
  assert(payload.markdown?.includes('## Asset/SBOM Seeds'), 'markdown missing asset seed section');
  assert(
    payload.markdown?.includes('## Source Freshness And Failures'),
    'markdown missing source freshness section',
  );

  const integrationResponse = await fetch(`${baseUrl}/api/integrations/demo-export`, {
    method: 'POST',
    headers: {
      'x-prophet-control': 'local-console',
      'x-prophet-operator': 'control-smoke',
    },
  });
  const integrationPayload = await integrationResponse.json();
  assert(
    integrationResponse.status === 200,
    `expected integration HTTP 200, got ${integrationResponse.status}`,
  );
  assert(integrationPayload.ok === true, 'integration payload.ok must be true');
  assert(
    integrationPayload.status === 'integration_handoff_exported',
    `unexpected integration status: ${integrationPayload.status}`,
  );
  assert(
    integrationPayload.manifest?.mode === 'review_template_only',
    'integration export must be review_template_only',
  );
  assert(
    integrationPayload.manifest?.safety_attestation?.no_external_api_calls === true,
    'integration export must attest no external API calls',
  );
  assert(
    integrationPayload.manifest?.evidence_refs?.policy_id === 'prophet-pilot-fixture-localhost-v0.1',
    'integration export policy ref missing',
  );
  assert(
    integrationPayload.manifest?.evidence_refs?.approval_record_hash ===
      payload.bundle?.operator_approval?.approval_record_hash,
    'integration export approval hash ref missing',
  );
  assert(
    payload.auditEvent?.chain?.previous_event_hash === denialPayload.auditEvent?.event_hash,
    'approval audit event should chain to the prior denial event',
  );
  assert(
    integrationPayload.auditEvent?.chain?.previous_event_hash === payload.auditEvent?.event_hash,
    'integration audit event should chain to the approval event',
  );
  assert(
    Object.keys(integrationPayload.manifest?.files ?? {}).length === 7,
    'integration manifest must list all handoff files',
  );
  assert(
    integrationPayload.paths?.manifest ===
      'integrations/outputs/runtime/latest-edge-appliance/manifest.json',
    'integration manifest path missing',
  );
  assert(
    integrationPayload.paths?.auditLog === expectedAuditLogPath,
    'integration audit log path missing',
  );
} finally {
  child.kill('SIGTERM');
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`${message}\n${stderr}`);
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
