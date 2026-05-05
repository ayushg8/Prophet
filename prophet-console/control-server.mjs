import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const port = Number(process.env.PROPHET_CONTROL_PORT || 8787);
const vmScraperEnabled = process.env.PROPHET_ENABLE_VM_SCRAPER === '1';
const workflowScript = path.join(repoRoot, 'world-side/scripts/run-scraper-vm-workflow.sh');
const worldSideDir = path.join(repoRoot, 'world-side');
const scraperSideDir = path.join(repoRoot, 'world-side/scraper');
const cyberSideDir = path.join(repoRoot, 'cyber-side');
const sourceCatalogFile = path.join(repoRoot, 'world-side/scraper/config/source_catalog.json');
const candidateFile = path.join(
  repoRoot,
  'world-side/fixtures/exploit-candidate-edge-appliance.json',
);
const goldenForecastFile = path.join(
  repoRoot,
  'world-side/outputs/golden-forecast-edge-appliance.json',
);
const demoChatterFile = path.join(
  repoRoot,
  'world-side/fixtures/sanitized-chatter-sample.jsonl',
);
const demoOsintSnapshotFile = path.join(
  repoRoot,
  'world-side/fixtures/osint-snapshot-sample.jsonl',
);
const demoOsintManifestFile = path.join(
  repoRoot,
  'world-side/fixtures/osint-snapshot-sample.manifest.json',
);
const demoSeededOsintSnapshotFile = path.join(
  repoRoot,
  'world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.jsonl',
);
const demoSeededOsintManifestFile = path.join(
  repoRoot,
  'world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.manifest.json',
);
const seededOsintFixtureDir = path.join(repoRoot, 'world-side/fixtures/seeded-osint');
const cyberArtifactFile = path.join(
  repoRoot,
  'cyber-side/fixtures/exploit-engine-output-edge-appliance.json',
);
const cyberPortfolioFile = path.join(
  repoRoot,
  'cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json',
);
const assetInventoryFile = path.join(
  repoRoot,
  'assets/fixtures/dib-edge-appliance-inventory.json',
);
const assetSeedsetFile = path.join(
  repoRoot,
  'assets/fixtures/dib-edge-appliance-seedset.json',
);
const policyFile = path.join(repoRoot, 'policy/prophet-pilot-policy.json');
const evidenceRuntimeJson = path.join(
  repoRoot,
  'evidence/outputs/runtime/latest-edge-appliance.json',
);
const evidenceRuntimeMarkdown = path.join(
  repoRoot,
  'evidence/outputs/runtime/latest-edge-appliance.md',
);
const sandboxRuntimeArtifact = path.join(
  repoRoot,
  'cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json',
);
const integrationRuntimeManifest = path.join(
  repoRoot,
  'integrations/outputs/runtime/latest-edge-appliance/manifest.json',
);
const integrationRuntimeDir = path.join(
  repoRoot,
  'integrations/outputs/runtime/latest-edge-appliance',
);
const operatorAuditLog = process.env.PROPHET_OPERATOR_AUDIT_LOG
  ? path.resolve(repoRoot, process.env.PROPHET_OPERATOR_AUDIT_LOG)
  : path.join(repoRoot, 'evidence/outputs/runtime/operator-audit-log.jsonl');
const approvalRecordRuntimeJson = process.env.PROPHET_APPROVAL_RECORD_JSON
  ? path.resolve(repoRoot, process.env.PROPHET_APPROVAL_RECORD_JSON)
  : path.join(repoRoot, 'evidence/outputs/runtime/latest-approval-record.json');
const readinessEvidenceRuntimeJson =
  process.env.PROPHET_READINESS_EVIDENCE_RUNTIME_JSON || evidenceRuntimeJson;
const readinessEvidenceRuntimeMarkdown =
  process.env.PROPHET_READINESS_EVIDENCE_RUNTIME_MARKDOWN || evidenceRuntimeMarkdown;
const readinessIntegrationRuntimeManifest =
  process.env.PROPHET_READINESS_INTEGRATION_MANIFEST || integrationRuntimeManifest;
const readinessOperatorAuditLog =
  process.env.PROPHET_READINESS_OPERATOR_AUDIT_LOG || operatorAuditLog;
const forecastOut = path.join(
  repoRoot,
  'world-side/outputs/runtime/live-scraper-forecast-edge-appliance.json',
);
const demoForecastOut = path.join(
  repoRoot,
  'world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json',
);
const incomingDir = path.join(repoRoot, 'world-side/data/chatter/incoming/console');
const policyAllowedModes = {
  asset_context: ['fixture', 'customer_owned_metadata'],
  osint_collection: ['fixture', 'seeded_osint'],
  forecast_generation: ['fixture', 'seeded_osint'],
  validation: ['fixture', 'localhost_sandbox'],
  evidence_generation: ['fixture', 'localhost_sandbox'],
};
const policyBlockedControls = [
  'live_targets_allowed',
  'live_vm_scraper_allowed',
  'arbitrary_target_input_allowed',
  'payload_generation_allowed',
  'raw_scraper_text_allowed',
  'private_hostnames_allowed',
  'credentials_allowed',
];
const policyRequiredAttestations = [
  'no_live_targets',
  'no_payloads',
  'no_credentials',
  'no_raw_scraper_text',
  'no_private_hostnames',
];
const policyRetentionLimits = {
  runtime_outputs_max_days: 90,
  audit_log_max_days: 365,
  customer_metadata_max_days: 90,
};

let activeRun = null;
let lastResult = null;

const server = createServer(async (req, res) => {
  const allowedOrigin = setCors(req, res);

  if (req.method === 'OPTIONS') {
    res.writeHead(allowedOrigin ? 204 : 403);
    res.end();
    return;
  }

  if (req.method === 'GET' && req.url === '/health') {
    const policy = await loadPilotPolicyStatus();
    writeJson(res, 200, {
      ok: true,
      running: Boolean(activeRun),
      lastResult,
      target: process.env.SCRAPER_SSH_TARGET || 'prophet-scraper',
      vmScraperEnabled,
      policy,
    });
    return;
  }

  if (req.method === 'GET' && req.url === '/api/readiness') {
    const report = await buildReadinessReport();
    writeJson(res, 200, report);
    return;
  }

  if (req.method === 'GET' && req.url === '/api/policy/status') {
    const report = await buildPolicyStatusReport();
    writeJson(res, 200, report);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/scraper/run') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }

    if (policyContext.policy.controls.live_vm_scraper_allowed !== true) {
      writeJson(res, 403, {
        ok: false,
        status: 'policy_blocked',
        policy: policyPayload(policyContext),
        message:
          'Pilot policy blocks live VM scraper workflows; use the fixture-backed demo refresh instead.',
      });
      return;
    }

    if (!vmScraperEnabled) {
      writeJson(res, 403, {
        ok: false,
        status: 'vm_scraper_disabled',
        message:
          'Live scraper VM workflow is disabled. Set PROPHET_ENABLE_VM_SCRAPER=1 only after an approved isolated collection plan is ready.',
      });
      return;
    }

    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A scraper VM workflow is already running.',
      });
      return;
    }

    activeRun = runWorkflow();
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    writeJson(res, result.ok ? 200 : 500, result);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/scraper/demo-refresh') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }
    const policyError = policyModeError(policyContext.policy, [
      ['osint_collection', 'seeded_osint'],
      ['forecast_generation', 'seeded_osint'],
    ]);
    if (policyError) {
      writeJson(res, 403, {
        ok: false,
        status: 'policy_blocked',
        policy: policyPayload(policyContext),
        message: policyError,
      });
      return;
    }

    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A Prophet control workflow is already running.',
      });
      return;
    }

    activeRun = runDemoRefresh();
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    writeJson(res, result.ok ? 200 : 500, result);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/cyber/demo-artifact') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }
    const policyError = policyModeError(policyContext.policy, [['validation', 'fixture']]);
    if (policyError) {
      writeJson(res, 403, {
        ok: false,
        status: 'policy_blocked',
        policy: policyPayload(policyContext),
        message: policyError,
      });
      return;
    }

    try {
      const artifact = JSON.parse(await readFile(cyberArtifactFile, 'utf8'));
      writeJson(res, 200, {
        ok: true,
        status: 'cyber_artifact_loaded',
        message: 'Cyber fixture loaded from cyber-side/fixtures.',
        artifact,
      });
    } catch (error) {
      writeJson(res, 500, {
        ok: false,
        status: 'cyber_artifact_unreadable',
        message: `Cyber fixture could not be read: ${error.message}`,
      });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/cyber/prediction-portfolio') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    try {
      const portfolio = JSON.parse(await readFile(cyberPortfolioFile, 'utf8'));
      writeJson(res, 200, {
        ok: true,
        status: 'prediction_portfolio_loaded',
        message: 'Exploit prediction portfolio loaded from cyber-side/fixtures.',
        portfolio,
      });
    } catch (error) {
      writeJson(res, 500, {
        ok: false,
        status: 'prediction_portfolio_unreadable',
        message: `Prediction portfolio could not be read: ${error.message}`,
      });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/evidence/demo-bundle') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }
    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A Prophet control workflow is already running.',
      });
      return;
    }

    activeRun = runEvidenceDemoBundle(operatorLabelFromRequest(req));
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    const statusCode = result.ok
      ? 200
      : result.status === 'policy_blocked'
        ? 403
      : result.status === 'evidence_validation_failed'
        ? 422
        : 500;
    writeJson(res, statusCode, result);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/evidence/deny') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }
    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A Prophet control workflow is already running.',
      });
      return;
    }

    activeRun = recordEvidenceDenial(policyContext, operatorLabelFromRequest(req));
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    writeJson(res, result.ok ? 200 : 500, result);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/cyber/sandbox-artifact') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }
    const policyError = policyModeError(policyContext.policy, [
      ['validation', 'localhost_sandbox'],
    ]);
    if (policyError) {
      writeJson(res, 403, {
        ok: false,
        status: 'policy_blocked',
        policy: policyPayload(policyContext),
        message: policyError,
      });
      return;
    }

    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A Prophet control workflow is already running.',
      });
      return;
    }

    activeRun = runSandboxArtifact();
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    writeJson(res, result.ok ? 200 : 422, result);
    return;
  }

  if (req.method === 'POST' && req.url === '/api/integrations/demo-export') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
      return;
    }

    const policyContext = await loadPilotPolicyOrRespond(res);
    if (!policyContext) {
      return;
    }

    if (activeRun) {
      writeJson(res, 409, {
        ok: false,
        status: 'busy',
        message: 'A Prophet control workflow is already running.',
      });
      return;
    }

    activeRun = runIntegrationDemoExport(policyContext, operatorLabelFromRequest(req));
    const result = await activeRun;
    activeRun = null;
    lastResult = {
      ok: result.ok,
      status: result.status,
      finishedAt: result.finishedAt,
      message: result.message,
    };
    const statusCode = result.ok
      ? 200
      : result.status === 'policy_blocked'
        ? 403
      : result.status === 'evidence_missing'
        ? 409
      : result.status === 'integration_export_validation_failed'
        ? 422
        : 500;
    writeJson(res, statusCode, result);
    return;
  }

  writeJson(res, 404, {
    ok: false,
    status: 'not_found',
    message: 'Unknown Prophet control endpoint.',
  });
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Prophet control server listening on http://127.0.0.1:${port}`);
  console.log(`Scraper target: ${process.env.SCRAPER_SSH_TARGET || 'prophet-scraper'}`);
  console.log(`Live scraper VM workflow: ${vmScraperEnabled ? 'enabled' : 'disabled'}`);
});

async function runWorkflow() {
  const startedAt = new Date().toISOString();
  const env = {
    ...process.env,
    LOCAL_FORECAST_OUT: forecastOut,
    LOCAL_INCOMING_DIR: incomingDir,
    SCRAPER_SSH_TARGET: process.env.SCRAPER_SSH_TARGET || 'prophet-scraper',
  };

  const child = spawn('bash', [workflowScript], {
    cwd: repoRoot,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let stdout = '';
  let stderr = '';

  child.stdout.on('data', (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
  });

  const exitCode = await new Promise((resolve) => {
    child.on('close', resolve);
    child.on('error', () => resolve(1));
  });

  const finishedAt = new Date().toISOString();

  if (exitCode !== 0) {
    return {
      ok: false,
      status: 'failed',
      startedAt,
      finishedAt,
      exitCode,
      message: summarizeFailure(stderr, stdout),
      stdoutTail: tail(stdout),
      stderrTail: tail(stderr),
    };
  }

  try {
    const forecast = JSON.parse(await readFile(forecastOut, 'utf8'));
    return {
      ok: true,
      status: 'completed',
      startedAt,
      finishedAt,
      exitCode,
      message: 'Scraper VM run completed and forecast was refreshed.',
      forecast,
      stdoutTail: tail(stdout),
      stderrTail: tail(stderr),
    };
  } catch (error) {
    return {
      ok: false,
      status: 'forecast_unreadable',
      startedAt,
      finishedAt,
      exitCode,
      message: `Workflow finished, but the forecast file could not be read: ${error.message}`,
      stdoutTail: tail(stdout),
      stderrTail: tail(stderr),
    };
  }
}

async function runDemoRefresh() {
  const startedAt = new Date().toISOString();
  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, worldSideDir, scraperSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };

  const snapshotChild = spawn(
    'python3',
    [
      '-m',
      'scraper_side.snapshot',
      '--catalog',
      sourceCatalogFile,
      '--source',
      'cisa_vulnrichment_cve_record_seed',
      '--source',
      'osv_query_api_seed',
      '--source',
      'redhat_security_data_cve_api',
      '--asset-seedset',
      assetSeedsetFile,
      '--seed-fixture-dir',
      seededOsintFixtureDir,
      '--policy',
      policyFile,
      '--generated-at',
      '2026-05-04T20:30:00Z',
      '--limit-per-source',
      '1',
      '--max-seeds-per-source',
      '4',
      '--max-records',
      '50',
      '--require-records',
      '--out-jsonl',
      demoSeededOsintSnapshotFile,
      '--out-manifest',
      demoSeededOsintManifestFile,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  const snapshotResult = await collectChild(snapshotChild);
  const snapshotFinishedAt = new Date().toISOString();
  if (snapshotResult.exitCode !== 0) {
    return {
      ok: false,
      status: 'demo_seeded_osint_failed',
      startedAt,
      finishedAt: snapshotFinishedAt,
      exitCode: snapshotResult.exitCode,
      message: 'Asset-seeded OSINT snapshot generation failed.',
      stdoutTail: tail(snapshotResult.stdout),
      stderrTail: tail(snapshotResult.stderr),
    };
  }

  const child = spawn(
    'python3',
    [
      '-m',
      'forecaster.cli',
      '--candidate',
      candidateFile,
      '--chatter',
      demoChatterFile,
      '--osint-snapshot',
      demoOsintSnapshotFile,
      '--osint-manifest',
      demoOsintManifestFile,
      '--osint-snapshot',
      demoSeededOsintSnapshotFile,
      '--osint-manifest',
      demoSeededOsintManifestFile,
      '--asset-seedset',
      assetSeedsetFile,
      '--out',
      demoForecastOut,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  const result = await collectChild(child);
  const finishedAt = new Date().toISOString();

  if (result.exitCode !== 0) {
    return {
      ok: false,
      status: 'demo_refresh_failed',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Demo forecast refresh failed. Check the control server terminal.',
      stdoutTail: tail(`${snapshotResult.stdout}\n${result.stdout}`),
      stderrTail: tail(`${snapshotResult.stderr}\n${result.stderr}`),
    };
  }

  try {
    const forecast = JSON.parse(await readFile(demoForecastOut, 'utf8'));
    return {
      ok: true,
      status: 'demo_refreshed',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message:
        'Demo forecast refreshed from sanitized fixture chatter, OSINT snapshot, and asset-seeded OSINT metadata.',
      forecast,
      stdoutTail: tail(`${snapshotResult.stdout}\n${result.stdout}`),
      stderrTail: tail(`${snapshotResult.stderr}\n${result.stderr}`),
    };
  } catch (error) {
    return {
      ok: false,
      status: 'demo_forecast_unreadable',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: `Demo refresh finished, but the forecast file could not be read: ${error.message}`,
      stdoutTail: tail(`${snapshotResult.stdout}\n${result.stdout}`),
      stderrTail: tail(`${snapshotResult.stderr}\n${result.stderr}`),
    };
  }
}

async function runEvidenceDemoBundle(operatorLabel = 'local-console') {
  const startedAt = new Date().toISOString();
  const forecastFile = await chooseEvidenceForecastFile();
  let policyContext;
  try {
    policyContext = await loadPilotPolicy();
  } catch (error) {
    return {
      ok: false,
      status: 'policy_unreadable',
      startedAt,
      finishedAt: new Date().toISOString(),
      message: `Pilot policy could not be read: ${sanitizeMessage(error.message)}`,
    };
  }
  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, cyberSideDir, worldSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };
  const artifactChoice = await chooseEvidenceArtifactFile(env, policyContext.policy);
  const policyError = policyModeError(policyContext.policy, [
    ['evidence_generation', artifactChoice.mode],
    ['validation', artifactChoice.mode],
  ]);
  if (policyError) {
    return {
      ok: false,
      status: 'policy_blocked',
      startedAt,
      finishedAt: new Date().toISOString(),
      policy: policyPayload(policyContext),
      message: policyError,
    };
  }

  const fixtures = [
    ['forecast', forecastFile],
    ['prediction portfolio', cyberPortfolioFile],
    ['defense artifact', artifactChoice.file],
    ['asset inventory', assetInventoryFile],
    ['asset seedset', assetSeedsetFile],
    ['pilot policy', policyFile],
  ];
  for (const [label, file] of fixtures) {
    try {
      JSON.parse(await readFile(file, 'utf8'));
    } catch (error) {
      return {
        ok: false,
        status: 'evidence_fixture_unreadable',
        startedAt,
        finishedAt: new Date().toISOString(),
        fixture: label,
        message: `Evidence fixture could not be read: ${label}.`,
        detail: sanitizeMessage(error.message),
      };
    }
  }

  const approvalAudit = await appendAuditEvent(env, {
    eventType: 'operator_approval',
    operatorLabel,
    decision: 'bypassed_for_fixture',
    generatedAt: startedAt,
    runId: 'console-demo-edge-appliance',
    artifactId: artifactChoice.source,
    reason: 'fixture-approved console evidence generation',
    outEvent: approvalRecordRuntimeJson,
  });
  if (!approvalAudit.ok) {
    return {
      ok: false,
      status: 'audit_append_failed',
      startedAt,
      finishedAt: new Date().toISOString(),
      policy: policyPayload(policyContext),
      message: approvalAudit.message,
      stdoutTail: tail(approvalAudit.stdout ?? ''),
      stderrTail: tail(approvalAudit.stderr ?? ''),
    };
  }

  const child = spawn(
    'python3',
    [
      '-m',
      'evidence.bundle',
      '--forecast',
      forecastFile,
      '--portfolio',
      cyberPortfolioFile,
      '--artifact',
      artifactChoice.file,
      '--asset-inventory',
      assetInventoryFile,
      '--asset-seedset',
      assetSeedsetFile,
      '--policy',
      policyFile,
      '--approval-record',
      approvalRecordRuntimeJson,
      '--operator-label',
      operatorLabel,
      '--approval-decision',
      'bypassed_for_fixture',
      '--run-id',
      'console-demo-edge-appliance',
      '--out-json',
      evidenceRuntimeJson,
      '--out-md',
      evidenceRuntimeMarkdown,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  const result = await collectChild(child);
  const finishedAt = new Date().toISOString();
  if (result.exitCode !== 0) {
    return {
      ok: false,
      status: 'evidence_validation_failed',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: summarizeEvidenceFailure(result.stderr, result.stdout),
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
    };
  }

  try {
    const bundle = JSON.parse(await readFile(evidenceRuntimeJson, 'utf8'));
    const markdown = await readFile(evidenceRuntimeMarkdown, 'utf8');
    return {
      ok: true,
      status: 'evidence_bundle_generated',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: `Evidence bundle generated from validated ${artifactChoice.sourceLabel}.`,
      policy: policyPayload(policyContext),
      artifactSource: artifactChoice.source,
      artifactSourceLabel: artifactChoice.sourceLabel,
      artifactMode: artifactChoice.mode,
      auditEvent: approvalAudit.event,
      bundle,
      markdown,
      paths: {
        json: 'evidence/outputs/runtime/latest-edge-appliance.json',
        markdown: 'evidence/outputs/runtime/latest-edge-appliance.md',
        defenseArtifact: artifactChoice.relativePath,
        approvalRecord: displayPath(approvalRecordRuntimeJson),
        auditLog: displayPath(operatorAuditLog),
      },
    };
  } catch (error) {
    return {
      ok: false,
      status: 'evidence_output_unreadable',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Evidence generator completed, but runtime output could not be read.',
      detail: sanitizeMessage(error.message),
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
    };
  }
}

async function chooseEvidenceForecastFile() {
  try {
    const forecast = JSON.parse(await readFile(demoForecastOut, 'utf8'));
    if (
      forecast?.schema_version === 'world_forecast.v0.1' &&
      forecast?.open_source_signals?.integrated === true &&
      forecast?.asset_seed_context?.integrated === true
    ) {
      return demoForecastOut;
    }
  } catch {
    // Fall back to the checked-in golden fixture.
  }
  return goldenForecastFile;
}

async function chooseEvidenceArtifactFile(env, policy) {
  if (
    policyAllows(policy, 'validation', 'localhost_sandbox') &&
    policyAllows(policy, 'evidence_generation', 'localhost_sandbox') &&
    await validatesDirectionCArtifact(sandboxRuntimeArtifact, env)
  ) {
    return {
      file: sandboxRuntimeArtifact,
      relativePath: 'cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json',
      source: 'sandbox_runtime',
      sourceLabel: 'sandbox runtime artifact',
      mode: 'localhost_sandbox',
    };
  }
  return {
    file: cyberArtifactFile,
    relativePath: 'cyber-side/fixtures/exploit-engine-output-edge-appliance.json',
    source: 'checked_in_fixture',
    sourceLabel: 'checked-in defense fixture',
    mode: 'fixture',
  };
}

async function validatesDirectionCArtifact(file, env) {
  try {
    JSON.parse(await readFile(file, 'utf8'));
  } catch {
    return false;
  }
  const child = spawn(
    'python3',
    [
      '-c',
      'import json,sys; from validator import validate_exploit_engine_artifact; validate_exploit_engine_artifact(json.load(open(sys.argv[1], encoding="utf-8")))',
      file,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  const result = await collectChild(child);
  return result.exitCode === 0;
}

async function runSandboxArtifact() {
  const startedAt = new Date().toISOString();
  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, cyberSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };
  const child = spawn(
    'python3',
    [
      '-m',
      'sandbox_runner',
      'run',
      '--profile',
      'edge-appliance-fixture',
      '--policy',
      policyFile,
      '--run-id',
      'console-sandbox-edge-appliance',
      '--out',
      sandboxRuntimeArtifact,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  const result = await collectChild(child);
  const finishedAt = new Date().toISOString();
  if (result.exitCode !== 0) {
    return {
      ok: false,
      status: 'sandbox_artifact_failed',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: sanitizeMessage(result.stderr || result.stdout || 'Sandbox runner failed.'),
    };
  }

  try {
    const artifact = JSON.parse(await readFile(sandboxRuntimeArtifact, 'utf8'));
    return {
      ok: true,
      status: 'sandbox_artifact_generated',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Deterministic sandbox fixture artifact generated.',
      artifact,
      path: 'cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json',
    };
  } catch (error) {
    return {
      ok: false,
      status: 'sandbox_artifact_unreadable',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Sandbox artifact was generated but could not be read.',
      detail: sanitizeMessage(error.message),
    };
  }
}

async function recordEvidenceDenial(policyContext, operatorLabel = 'local-console') {
  const startedAt = new Date().toISOString();
  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, cyberSideDir, worldSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };
  const denialAudit = await appendAuditEvent(env, {
    eventType: 'operator_denial',
    operatorLabel,
    decision: 'denied',
    generatedAt: startedAt,
    runId: 'console-demo-edge-appliance',
    reason: 'operator denied console evidence generation',
  });
  const finishedAt = new Date().toISOString();
  if (!denialAudit.ok) {
    return {
      ok: false,
      status: 'audit_append_failed',
      startedAt,
      finishedAt,
      policy: policyPayload(policyContext),
      message: denialAudit.message,
      stdoutTail: tail(denialAudit.stdout ?? ''),
      stderrTail: tail(denialAudit.stderr ?? ''),
    };
  }
  return {
    ok: true,
    status: 'operator_denial_recorded',
    startedAt,
    finishedAt,
    message: 'Operator denial recorded in the local hash-chained audit log. No evidence bundle was generated.',
    policy: policyPayload(policyContext),
    auditEvent: denialAudit.event,
    paths: {
      auditLog: displayPath(operatorAuditLog),
    },
  };
}

async function runIntegrationDemoExport(policyContext, operatorLabel = 'local-console') {
  const startedAt = new Date().toISOString();
  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, cyberSideDir, worldSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };

  const evidence = await readJsonMaybe(evidenceRuntimeJson);
  if (!evidence.ok) {
    return {
      ok: false,
      status: 'evidence_missing',
      startedAt,
      finishedAt: new Date().toISOString(),
      policy: policyPayload(policyContext),
      message:
        'Generate the evidence bundle before exporting SIEM and ticketing handoff templates.',
      detail: evidence.error,
    };
  }

  const evidencePolicyId = evidence.value?.policy?.policy_id;
  if (evidencePolicyId && evidencePolicyId !== policyContext.policyId) {
    return {
      ok: false,
      status: 'policy_blocked',
      startedAt,
      finishedAt: new Date().toISOString(),
      policy: policyPayload(policyContext),
      message:
        'Evidence bundle policy does not match the active pilot policy; regenerate evidence before exporting handoff templates.',
    };
  }

  const child = spawn(
    'python3',
    [
      '-m',
      'integrations.export',
      '--bundle',
      evidenceRuntimeJson,
      '--policy',
      policyContext.path,
      '--export-id',
      'console-demo-integration-export',
      '--out-dir',
      integrationRuntimeDir,
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  const result = await collectChild(child);
  const finishedAt = new Date().toISOString();
  if (result.exitCode !== 0) {
    return {
      ok: false,
      status: 'integration_export_validation_failed',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: summarizeIntegrationFailure(result.stderr, result.stdout),
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
      policy: policyPayload(policyContext),
    };
  }

  try {
    const manifest = JSON.parse(await readFile(integrationRuntimeManifest, 'utf8'));
    const exportAudit = await appendAuditEvent(env, {
      eventType: 'integration_handoff_exported',
      operatorLabel,
      decision: 'integration_handoff_exported',
      generatedAt: finishedAt,
      runId: 'console-demo-integration-export',
      bundleId: manifest.evidence_refs?.bundle_id,
      bundleSha256: manifest.evidence_refs?.bundle_sha256,
      exportId: manifest.export_id,
      reason: 'policy-approved console integration handoff export',
    });
    if (!exportAudit.ok) {
      return {
        ok: false,
        status: 'audit_append_failed',
        startedAt,
        finishedAt: new Date().toISOString(),
        exitCode: exportAudit.exitCode,
        message: exportAudit.message,
        stdoutTail: tail(exportAudit.stdout ?? ''),
        stderrTail: tail(exportAudit.stderr ?? ''),
        policy: policyPayload(policyContext),
      };
    }
    return {
      ok: true,
      status: 'integration_handoff_exported',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Safe SIEM, ticketing, and audit handoff templates exported for operator review.',
      policy: policyPayload(policyContext),
      auditEvent: exportAudit.event,
      manifest,
      paths: {
        manifest: 'integrations/outputs/runtime/latest-edge-appliance/manifest.json',
        splunk: 'integrations/outputs/runtime/latest-edge-appliance/siem/splunk_saved_search.json',
        elastic: 'integrations/outputs/runtime/latest-edge-appliance/siem/elastic_detection_rule.ndjson',
        sentinel: 'integrations/outputs/runtime/latest-edge-appliance/siem/sentinel_analytic_rule.json',
        jira: 'integrations/outputs/runtime/latest-edge-appliance/tickets/jira_remediation_ticket.json',
        servicenow: 'integrations/outputs/runtime/latest-edge-appliance/tickets/servicenow_remediation_task.json',
        audit: 'integrations/outputs/runtime/latest-edge-appliance/audit/operator_approval_event.json',
        auditLog: displayPath(operatorAuditLog),
      },
    };
  } catch (error) {
    return {
      ok: false,
      status: 'integration_export_unreadable',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: 'Integration exporter completed, but the runtime manifest could not be read.',
      detail: sanitizeMessage(error.message),
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
      policy: policyPayload(policyContext),
    };
  }
}

async function appendAuditEvent(env, options) {
  const args = [
    '-m',
    'evidence.audit',
    'append',
    '--log',
    operatorAuditLog,
    '--policy',
    policyFile,
    '--event-type',
    options.eventType,
    '--operator-label',
    sanitizeOperatorLabel(options.operatorLabel),
    '--decision',
    options.decision,
    '--reason',
    options.reason,
  ];
  if (options.generatedAt) {
    args.push('--generated-at', options.generatedAt);
  }
  if (options.runId) {
    args.push('--run-id', options.runId);
  }
  if (options.artifactId) {
    args.push('--artifact-id', options.artifactId);
  }
  if (options.bundleId) {
    args.push('--bundle-id', options.bundleId);
  }
  if (options.bundleSha256) {
    args.push('--bundle-sha256', options.bundleSha256);
  }
  if (options.exportId) {
    args.push('--export-id', options.exportId);
  }
  if (options.outEvent) {
    args.push('--out-event', options.outEvent);
  }

  const child = spawn('python3', args, {
    cwd: repoRoot,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const result = await collectChild(child);
  if (result.exitCode !== 0) {
    return {
      ok: false,
      exitCode: result.exitCode,
      stdout: result.stdout,
      stderr: result.stderr,
      message: summarizeAuditFailure(result.stderr, result.stdout),
    };
  }
  try {
    return {
      ok: true,
      exitCode: result.exitCode,
      event: JSON.parse(result.stdout),
      stdout: result.stdout,
      stderr: result.stderr,
    };
  } catch (error) {
    return {
      ok: false,
      exitCode: result.exitCode,
      stdout: result.stdout,
      stderr: result.stderr,
      message: `Audit event was appended but could not be parsed: ${sanitizeMessage(error.message)}`,
    };
  }
}

async function loadPilotPolicyOrRespond(res) {
  try {
    return await loadPilotPolicy();
  } catch (error) {
    writeJson(res, 500, {
      ok: false,
      status: 'policy_unreadable',
      message: `Pilot policy could not be read: ${sanitizeMessage(error.message)}`,
      policyPath: 'policy/prophet-pilot-policy.json',
    });
    return null;
  }
}

async function buildPolicyStatusReport() {
  const generatedAt = new Date().toISOString();

  try {
    const policyContext = await loadPilotPolicy();
    const actionGates = buildPolicyActionGates(policyContext.policy);
    const blockedControls = policyBlockedControls.filter(
      (control) => policyContext.policy.controls?.[control] === false,
    );

    return {
      ok: true,
      status: 'policy_loaded',
      generatedAt,
      policy: policyPayload(policyContext),
      blockedControls,
      actionGates,
      summary: {
        blockedControlCount: blockedControls.length,
        allowedGateCount: actionGates.filter((gate) => gate.status === 'allowed').length,
        blockedGateCount: actionGates.filter((gate) => gate.status === 'blocked').length,
        vmScraperEnabled,
        controlServer: 'localhost-only',
      },
    };
  } catch (error) {
    return {
      ok: false,
      status: 'policy_unreadable',
      generatedAt,
      message: `Pilot policy could not be read: ${sanitizeMessage(error.message)}`,
      policyPath: 'policy/prophet-pilot-policy.json',
      blockedControls: [],
      actionGates: [],
      summary: {
        blockedControlCount: 0,
        allowedGateCount: 0,
        blockedGateCount: 0,
        vmScraperEnabled,
        controlServer: 'localhost-only',
      },
    };
  }
}

function buildPolicyActionGates(policy) {
  return [
    modeGate(
      policy,
      'fixture_demo_refresh',
      'Fixture demo refresh',
      [
        ['osint_collection', 'seeded_osint'],
        ['forecast_generation', 'seeded_osint'],
      ],
      'Seeded OSINT and fixture forecast refresh are policy-approved.',
    ),
    modeGate(
      policy,
      'cyber_defense_fixture',
      'Cyber defense fixture',
      [['validation', 'fixture']],
      'Checked-in defensive fixture artifacts are policy-approved.',
    ),
    modeGate(
      policy,
      'localhost_sandbox',
      'Localhost sandbox',
      [['validation', 'localhost_sandbox']],
      'Deterministic localhost sandbox validation is policy-approved.',
    ),
    evidenceGate(policy),
    integrationGate(policy),
    controlGate(
      policy,
      'live_vm_scraper',
      'Live VM scraper',
      'live_vm_scraper_allowed',
      'Policy blocks live VM scraper workflow; only sanitized fixture refresh is available.',
      'Policy and environment allow an isolated scraper VM workflow.',
      vmScraperEnabled,
    ),
    controlGate(
      policy,
      'live_target_input',
      'Live target input',
      'live_targets_allowed',
      'Policy blocks live target input for this pilot.',
      'Policy allows live target input.',
    ),
  ];
}

function modeGate(policy, id, label, checks, allowedDetails) {
  const policyError = policyModeError(policy, checks);
  return {
    id,
    label,
    status: policyError ? 'blocked' : 'allowed',
    details: policyError || allowedDetails,
    checks: checks.map(([category, mode]) => ({ category, mode })),
  };
}

function evidenceGate(policy) {
  const modes = ['localhost_sandbox', 'fixture'].filter(
    (mode) =>
      policyAllows(policy, 'evidence_generation', mode) &&
      policyAllows(policy, 'validation', mode),
  );
  return {
    id: 'evidence_bundle',
    label: 'Evidence bundle',
    status: modes.length > 0 ? 'allowed' : 'blocked',
    details:
      modes.length > 0
        ? `Evidence generation may use ${modes.join(' or ')} defensive artifacts.`
        : 'Pilot policy does not allow an evidence generation mode.',
    checks: modes.map((mode) => ({ category: 'evidence_generation', mode })),
  };
}

function integrationGate(policy) {
  const exports = Array.isArray(policy.allowed_integration_exports)
    ? policy.allowed_integration_exports
    : [];
  return {
    id: 'integration_handoff',
    label: 'Integration handoff',
    status: exports.length > 0 ? 'allowed' : 'blocked',
    details:
      exports.length > 0
        ? `${exports.length} SIEM, ticketing, and audit handoff template type(s) are policy-approved.`
        : 'Pilot policy does not allow integration handoff exports.',
    checks: exports.map((mode) => ({ category: 'integration_export', mode })),
  };
}

function controlGate(
  policy,
  id,
  label,
  control,
  blockedDetails,
  allowedDetails,
  requiredRuntimeFlag = true,
) {
  const controlAllowed = policy.controls?.[control] === true;
  const allowed = controlAllowed && requiredRuntimeFlag;
  return {
    id,
    label,
    status: allowed ? 'allowed' : 'blocked',
    details: allowed ? allowedDetails : blockedDetails,
    checks: [{ category: 'control', mode: control }],
  };
}

async function buildReadinessReport() {
  const generatedAt = new Date().toISOString();
  const checks = [];
  let policyContext = null;

  try {
    policyContext = await loadPilotPolicy();
    checks.push(
      readinessCheck(
        'pilot_policy',
        'Pilot policy',
        'pass',
        `${policyContext.policyId}; sha256 ${shortHash(policyContext.policySha256)}`,
        true,
      ),
    );
  } catch (error) {
    checks.push(
      readinessCheck(
        'pilot_policy',
        'Pilot policy',
        'fail',
        `Policy is unreadable or invalid: ${sanitizeMessage(error.message)}`,
        true,
      ),
    );
  }

  checks.push(await safetyBoundaryCheck(policyContext));
  checks.push(await forecastFixtureCheck());
  checks.push(await assetSeedsetCheck());
  checks.push(await seededOsintCheck());
  checks.push(await predictionPortfolioCheck());
  checks.push(await defenseArtifactCheck());
  checks.push(await sandboxRuntimeCheck());
  checks.push(await evidenceBundleCheck());
  checks.push(await integrationHandoffCheck());
  checks.push(await operatorAuditCheck());
  checks.push(await openBlockersCheck());

  const summary = summarizeReadiness(checks, policyContext);
  return {
    ok: summary.blockingFailures === 0,
    generatedAt,
    missionId: 'prophet-edge-appliance-internal-alpha',
    checks,
    summary,
  };
}

async function safetyBoundaryCheck(policyContext) {
  if (!policyContext) {
    return readinessCheck(
      'safety_boundary',
      'Safety boundary',
      'fail',
      'Cannot prove safety boundary without a valid pilot policy.',
      true,
    );
  }

  const blockedControls = [
    'live_targets_allowed',
    'live_vm_scraper_allowed',
    'arbitrary_target_input_allowed',
    'payload_generation_allowed',
    'raw_scraper_text_allowed',
    'private_hostnames_allowed',
    'credentials_allowed',
  ];
  const unsafeControl = blockedControls.find(
    (control) => policyContext.policy.controls?.[control] !== false,
  );
  if (unsafeControl) {
    return readinessCheck(
      'safety_boundary',
      'Safety boundary',
      'fail',
      `Policy control ${unsafeControl} is not false.`,
      true,
    );
  }

  if (vmScraperEnabled) {
    return readinessCheck(
      'safety_boundary',
      'Safety boundary',
      'warn',
      'Live scraper VM flag is enabled; policy still blocks live VM workflows by default.',
      false,
    );
  }

  return readinessCheck(
    'safety_boundary',
    'Safety boundary',
    'pass',
    'Live targets, payload generation, raw scraper text, credentials, and VM scraping are blocked by default.',
    true,
  );
}

async function forecastFixtureCheck() {
  const forecast = await readJsonMaybe(goldenForecastFile);
  if (!forecast.ok) {
    return readinessCheck(
      'forecast_fixture',
      'Forecast fixture',
      'fail',
      `Golden forecast is unreadable: ${forecast.error}`,
      true,
    );
  }
  if (forecast.value?.schema_version !== 'world_forecast.v0.1') {
    return readinessCheck(
      'forecast_fixture',
      'Forecast fixture',
      'fail',
      'Golden forecast does not use world_forecast.v0.1.',
      true,
    );
  }
  const windows = forecast.value.strike_windows?.length ?? 0;
  const vectors = forecast.value.strike_vectors?.length ?? 0;
  return readinessCheck(
    'forecast_fixture',
    'Forecast fixture',
    'pass',
    `${forecast.value.forecast_id || 'forecast'} has ${windows} strike window(s) and ${vectors} strike vector(s).`,
    true,
  );
}

async function assetSeedsetCheck() {
  const seedset = await readJsonMaybe(assetSeedsetFile);
  if (!seedset.ok) {
    return readinessCheck(
      'asset_seedset',
      'Asset seedset',
      'fail',
      `Asset seedset fixture is unreadable: ${seedset.error}`,
      true,
    );
  }
  if (seedset.value?.schema_version !== 'asset_osint_seedset.v0.1') {
    return readinessCheck(
      'asset_seedset',
      'Asset seedset',
      'fail',
      'Asset seedset does not use asset_osint_seedset.v0.1.',
      true,
    );
  }
  const cves = seedset.value.cve_seeds?.length ?? 0;
  const packages = seedset.value.package_seeds?.length ?? 0;
  return readinessCheck(
    'asset_seedset',
    'Asset seedset',
    'pass',
    `${seedset.value.seedset_id || 'seedset'} includes ${cves} CVE seed(s) and ${packages} package seed(s).`,
    true,
  );
}

async function seededOsintCheck() {
  const catalog = await readJsonMaybe(sourceCatalogFile);
  if (!catalog.ok) {
    return readinessCheck(
      'seeded_osint',
      'Seeded OSINT',
      'fail',
      `Source catalog is unreadable: ${catalog.error}`,
      true,
    );
  }

  let sourceDirs = [];
  try {
    sourceDirs = await readdir(seededOsintFixtureDir);
  } catch (error) {
    return readinessCheck(
      'seeded_osint',
      'Seeded OSINT',
      'fail',
      `Seeded OSINT fixture directory is unreadable: ${sanitizeMessage(error.message)}`,
      true,
    );
  }

  const sourceCount = Array.isArray(catalog.value?.sources)
    ? catalog.value.sources.length
    : Object.keys(catalog.value?.sources ?? {}).length;
  return readinessCheck(
    'seeded_osint',
    'Seeded OSINT',
    'pass',
    `${sourceCount} catalog source(s); ${sourceDirs.length} seeded fixture source group(s) available.`,
    true,
  );
}

async function predictionPortfolioCheck() {
  const portfolio = await readJsonMaybe(cyberPortfolioFile);
  if (!portfolio.ok) {
    return readinessCheck(
      'prediction_portfolio',
      'Prediction portfolio',
      'fail',
      `Prediction portfolio fixture is unreadable: ${portfolio.error}`,
      true,
    );
  }
  if (portfolio.value?.schema_version !== 'exploit_prediction_portfolio.v0.1') {
    return readinessCheck(
      'prediction_portfolio',
      'Prediction portfolio',
      'fail',
      'Prediction portfolio does not use exploit_prediction_portfolio.v0.1.',
      true,
    );
  }
  const zeroDayCount = portfolio.value.zero_day_predictions?.length ?? 0;
  const oneDayCount = portfolio.value.one_day_predictions?.length ?? 0;
  return readinessCheck(
    'prediction_portfolio',
    'Prediction portfolio',
    'pass',
    `${zeroDayCount} hypothesized zero-day class(es) and ${oneDayCount} one-day replay class(es).`,
    true,
  );
}

async function defenseArtifactCheck() {
  const artifact = await readJsonMaybe(cyberArtifactFile);
  if (!artifact.ok) {
    return readinessCheck(
      'defense_artifact',
      'Defense artifact',
      'fail',
      `Defense artifact fixture is unreadable: ${artifact.error}`,
      true,
    );
  }
  if (artifact.value?.schema_version !== 'exploit_engine_artifact.v0.1') {
    return readinessCheck(
      'defense_artifact',
      'Defense artifact',
      'fail',
      'Defense artifact does not use exploit_engine_artifact.v0.1.',
      true,
    );
  }
  const postPatchStatus = artifact.value.validation?.post_patch_status || 'unknown';
  return readinessCheck(
    'defense_artifact',
    'Defense artifact',
    'pass',
    `${artifact.value.artifact_id || 'artifact'} validates as ${postPatchStatus}.`,
    true,
  );
}

async function sandboxRuntimeCheck() {
  const sandbox = await readJsonMaybe(sandboxRuntimeArtifact);
  if (!sandbox.ok) {
    return readinessCheck(
      'sandbox_runtime',
      'Sandbox runtime artifact',
      'warn',
      'No runtime sandbox artifact found yet; console can generate one from the deterministic localhost fixture.',
      false,
    );
  }
  const postPatchStatus = sandbox.value.validation?.post_patch_status || 'unknown';
  const artifactId = sandbox.value.artifact_id || 'sandbox artifact';
  return readinessCheck(
    'sandbox_runtime',
    'Sandbox runtime artifact',
    postPatchStatus === 'blocked' || postPatchStatus === 'not_vulnerable' ? 'pass' : 'warn',
    `${artifactId} runtime validation status is ${postPatchStatus}.`,
    false,
  );
}

async function evidenceBundleCheck() {
  const bundle = await readJsonMaybe(readinessEvidenceRuntimeJson);
  if (!bundle.ok) {
    return readinessCheck(
      'evidence_bundle',
      'Evidence bundle',
      'warn',
      'No runtime evidence bundle found yet; generate evidence after loading the defense fixture or sandbox artifact.',
      false,
    );
  }
  const markdown = await readTextMaybe(readinessEvidenceRuntimeMarkdown);
  if (!markdown.ok) {
    return readinessCheck(
      'evidence_bundle',
      'Evidence bundle',
      'warn',
      `Evidence JSON exists, but Markdown export is missing: ${markdown.error}`,
      false,
    );
  }
  return readinessCheck(
    'evidence_bundle',
    'Evidence bundle',
    'pass',
    `${bundle.value.bundle_id || 'bundle'} sha256 ${shortHash(bundle.value.bundle_sha256)}; Markdown export available.`,
    false,
  );
}

async function integrationHandoffCheck() {
  const manifest = await readJsonMaybe(readinessIntegrationRuntimeManifest);
  if (!manifest.ok) {
    return readinessCheck(
      'integration_handoff',
      'Integration handoff',
      'warn',
      'No runtime integration handoff manifest found yet; run the pilot smoke or integration export before customer handoff.',
      false,
    );
  }
  const fileCount = Object.keys(manifest.value.files ?? {}).length;
  return readinessCheck(
    'integration_handoff',
    'Integration handoff',
    'pass',
    `${manifest.value.export_id || 'export'} includes ${fileCount} hashed SIEM, ticketing, and audit file(s).`,
    false,
  );
}

async function operatorAuditCheck() {
  const existing = await readTextMaybe(readinessOperatorAuditLog);
  if (!existing.ok) {
    return readinessCheck(
      'operator_audit',
      'Operator audit log',
      'warn',
      'No local operator audit log found yet; generating evidence creates a hash-chained approval record.',
      false,
    );
  }

  const env = {
    ...process.env,
    PYTHONPATH: [repoRoot, cyberSideDir, worldSideDir, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(path.delimiter),
  };
  const child = spawn(
    'python3',
    ['-m', 'evidence.audit', 'validate', '--log', readinessOperatorAuditLog],
    {
      cwd: repoRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  const result = await collectChild(child);
  if (result.exitCode !== 0) {
    return readinessCheck(
      'operator_audit',
      'Operator audit log',
      'fail',
      summarizeAuditFailure(result.stderr, result.stdout),
      true,
    );
  }
  try {
    const summary = JSON.parse(result.stdout);
    return readinessCheck(
      'operator_audit',
      'Operator audit log',
      'pass',
      `${summary.event_count || 0} hash-chained audit event(s); latest hash ${shortHash(summary.latest_event_hash)}.`,
      false,
    );
  } catch (error) {
    return readinessCheck(
      'operator_audit',
      'Operator audit log',
      'fail',
      `Audit log validated but summary could not be parsed: ${sanitizeMessage(error.message)}`,
      true,
    );
  }
}

async function openBlockersCheck() {
  const todo = await readTextMaybe(path.join(repoRoot, 'docs/PROPHET_TODO.md'));
  if (!todo.ok) {
    return readinessCheck(
      'open_blockers',
      'Open blockers',
      'warn',
      `Could not read docs/PROPHET_TODO.md: ${todo.error}`,
      false,
    );
  }

  const currentNextSteps = todo.text
    .split('\n')
    .filter((line) => /^\d+\.\s/.test(line.trim())).length;
  const openP0Items = countOpenItems(todo.text, '## P0:', '## P1:');
  const openP1Items = countOpenItems(todo.text, '## P1:', '## P2:');
  const status = openP0Items > 0 ? 'warn' : 'pass';
  return readinessCheck(
    'open_blockers',
    'Open blockers',
    status,
    `${openP0Items} P0 item(s), ${openP1Items} P1 item(s), and ${currentNextSteps} ordered next step(s) remain in docs/PROPHET_TODO.md.`,
    false,
  );
}

function summarizeReadiness(checks, policyContext) {
  const pass = checks.filter((check) => check.status === 'pass').length;
  const warn = checks.filter((check) => check.status === 'warn').length;
  const fail = checks.filter((check) => check.status === 'fail').length;
  const blockingFailures = checks.filter(
    (check) => check.status === 'fail' && check.blocking,
  ).length;
  const warningIds = checks
    .filter((check) => check.status === 'warn')
    .map((check) => check.id);
  const failureIds = checks
    .filter((check) => check.status === 'fail')
    .map((check) => check.id);

  return {
    total: checks.length,
    pass,
    warn,
    fail,
    blockingFailures,
    warningIds,
    failureIds,
    policyId: policyContext?.policyId ?? null,
    policySha256: policyContext?.policySha256 ?? null,
    vmScraperEnabled,
    controlServer: 'localhost-only',
    aiMode: 'deterministic-fixture-replay',
    safetyBoundary: 'live targets, payload generation, raw scraper text, credentials, and VM scraping blocked by default',
  };
}

function readinessCheck(id, label, status, details, blocking) {
  return {
    id,
    label,
    status,
    details,
    blocking,
  };
}

async function readJsonMaybe(file) {
  try {
    return { ok: true, value: JSON.parse(await readFile(file, 'utf8')) };
  } catch (error) {
    return { ok: false, error: sanitizeMessage(error.message) };
  }
}

async function readTextMaybe(file) {
  try {
    return { ok: true, text: await readFile(file, 'utf8') };
  } catch (error) {
    return { ok: false, error: sanitizeMessage(error.message) };
  }
}

function countOpenItems(text, startMarker, endMarker) {
  const start = text.indexOf(startMarker);
  if (start === -1) return 0;
  const end = text.indexOf(endMarker, start + startMarker.length);
  const section = end === -1 ? text.slice(start) : text.slice(start, end);
  return section.split('\n').filter((line) => line.trim().startsWith('- [ ]')).length;
}

function shortHash(value) {
  if (!value || typeof value !== 'string') return 'pending';
  return value.length > 16 ? value.slice(0, 16) : value;
}

async function loadPilotPolicyStatus() {
  try {
    return policyPayload(await loadPilotPolicy());
  } catch (error) {
    return {
      ok: false,
      status: 'policy_unreadable',
      message: sanitizeMessage(error.message),
      path: 'policy/prophet-pilot-policy.json',
    };
  }
}

async function loadPilotPolicy() {
  const policy = JSON.parse(await readFile(policyFile, 'utf8'));
  validatePilotPolicy(policy);
  return {
    policy,
    policyId: policy.policy_id,
    policySha256: createHash('sha256').update(canonicalJson(policy)).digest('hex'),
    path: 'policy/prophet-pilot-policy.json',
  };
}

function validatePilotPolicy(policy) {
  if (!policy || typeof policy !== 'object' || Array.isArray(policy)) {
    throw new Error('pilot policy must be a JSON object');
  }
  if (policy.schema_version !== 'prophet_pilot_policy.v0.1') {
    throw new Error('pilot policy schema_version must be prophet_pilot_policy.v0.1');
  }
  if (!policy.policy_id || typeof policy.policy_id !== 'string') {
    throw new Error('pilot policy requires policy_id');
  }
  if (!policy.allowed_modes || typeof policy.allowed_modes !== 'object') {
    throw new Error('pilot policy requires allowed_modes');
  }
  if (!policy.controls || typeof policy.controls !== 'object') {
    throw new Error('pilot policy requires controls');
  }
  const categories = Object.keys(policyAllowedModes);
  for (const category of Object.keys(policy.allowed_modes)) {
    if (!policyAllowedModes[category]) {
      throw new Error(`pilot policy has unknown allowed_modes category ${category}`);
    }
  }
  for (const category of categories) {
    const modes = policy.allowed_modes[category];
    if (!Array.isArray(modes) || modes.length === 0 || modes.some((mode) => typeof mode !== 'string')) {
      throw new Error(`pilot policy allowed_modes.${category} must be a non-empty string array`);
    }
    const duplicates = modes.filter((mode, index) => modes.indexOf(mode) !== index);
    if (duplicates.length > 0) {
      throw new Error(`pilot policy allowed_modes.${category} contains duplicate modes`);
    }
    const allowed = policyAllowedModes[category];
    const unknown = modes.filter((mode) => !allowed.includes(mode));
    if (unknown.length > 0) {
      throw new Error(`pilot policy allowed_modes.${category} has unknown modes: ${unknown.join(', ')}`);
    }
  }
  for (const control of Object.keys(policy.controls)) {
    if (!policyBlockedControls.includes(control)) {
      throw new Error(`pilot policy has unknown control ${control}`);
    }
  }
  for (const control of policyBlockedControls) {
    if (policy.controls[control] !== false) {
      throw new Error(`pilot policy controls.${control} must be false`);
    }
  }
  if (!Array.isArray(policy.required_attestations) || policy.required_attestations.length === 0) {
    throw new Error('pilot policy required_attestations must be a non-empty string array');
  }
  for (const attestation of policyRequiredAttestations) {
    if (!policy.required_attestations.includes(attestation)) {
      throw new Error(`pilot policy required_attestations missing ${attestation}`);
    }
  }
  validatePolicyRetention(policy.retention);
}

function validatePolicyRetention(retention) {
  if (!retention || typeof retention !== 'object' || Array.isArray(retention)) {
    throw new Error('pilot policy requires retention object');
  }
  const allowedFields = [
    ...Object.keys(policyRetentionLimits),
    'raw_collection_retained',
    'deletion_review_required',
  ];
  for (const field of Object.keys(retention)) {
    if (!allowedFields.includes(field)) {
      throw new Error(`pilot policy retention has unknown field ${field}`);
    }
  }
  for (const [field, maxDays] of Object.entries(policyRetentionLimits)) {
    const value = retention[field];
    if (!Number.isInteger(value) || value < 1 || value > maxDays) {
      throw new Error(`pilot policy retention.${field} must be 1-${maxDays} days`);
    }
  }
  if (retention.raw_collection_retained !== false) {
    throw new Error('pilot policy retention.raw_collection_retained must be false');
  }
  if (retention.deletion_review_required !== true) {
    throw new Error('pilot policy retention.deletion_review_required must be true');
  }
}

function policyModeError(policy, checks) {
  for (const [category, mode] of checks) {
    if (!policyAllows(policy, category, mode)) {
      return `Pilot policy ${policy.policy_id} does not allow ${category} mode ${mode}.`;
    }
  }
  return '';
}

function policyAllows(policy, category, mode) {
  const modes = policy.allowed_modes?.[category];
  return Array.isArray(modes) && modes.includes(mode);
}

function policyPayload(policyContext) {
  return {
    ok: true,
    policyId: policyContext.policyId,
    policySha256: policyContext.policySha256,
    path: policyContext.path,
    allowedModes: policyContext.policy.allowed_modes,
    allowedSourceIds: policyContext.policy.allowed_source_ids ?? [],
    allowedSandboxProfiles: policyContext.policy.allowed_sandbox_profiles ?? [],
    allowedIntegrationExports: policyContext.policy.allowed_integration_exports ?? [],
    retention: policyContext.policy.retention,
    controls: policyContext.policy.controls,
  };
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJson(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

function collectChild(child) {
  let stdout = '';
  let stderr = '';

  child.stdout.on('data', (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
  });

  return new Promise((resolve) => {
    child.on('close', (exitCode) => {
      resolve({ exitCode, stdout, stderr });
    });
    child.on('error', (error) => {
      resolve({ exitCode: 1, stdout, stderr: `${stderr}\n${error.message}` });
    });
  });
}

function setCors(req, res) {
  const origin = req.headers.origin;
  const allowedOrigin =
    !origin ||
    /^http:\/\/127\.0\.0\.1:\d+$/.test(origin) ||
    /^http:\/\/localhost:\d+$/.test(origin);

  if (origin && allowedOrigin) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'content-type,x-prophet-control,x-prophet-operator');
  return allowedOrigin;
}

function writeJson(res, status, payload) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(payload, null, 2));
}

function isConsoleRequest(req, allowedOrigin) {
  return allowedOrigin && req.headers['x-prophet-control'] === 'local-console';
}

function operatorLabelFromRequest(req) {
  return sanitizeOperatorLabel(req.headers['x-prophet-operator'] || 'local-console');
}

function displayPath(file) {
  const relative = path.relative(repoRoot, file);
  return relative && !relative.startsWith('..') && !path.isAbsolute(relative) ? relative : file;
}

function sanitizeOperatorLabel(value) {
  const raw = Array.isArray(value) ? value[0] : value;
  const cleaned = String(raw || 'local-console')
    .trim()
    .replace(/@/g, '-')
    .replace(/[^A-Za-z0-9 _./+-]/g, '-')
    .slice(0, 120);
  return cleaned || 'local-console';
}

function writeForbidden(res) {
  writeJson(res, 403, {
    ok: false,
    status: 'forbidden',
    message: 'Prophet control endpoint only accepts explicit localhost console requests.',
  });
}

function tail(text, max = 4000) {
  if (!text) return '';
  return text.length <= max ? text : text.slice(text.length - max);
}

function summarizeFailure(stderr, stdout) {
  const combined = `${stderr}\n${stdout}`;
  if (/Permission denied|publickey|BatchMode|NumberOfPasswordPrompts/i.test(combined)) {
    return 'Scraper VM SSH key auth is not ready. Add the public key to authorized_keys and retry.';
  }
  if (/Connection timed out|Operation timed out|No route to host|Could not resolve|Connection refused/i.test(combined)) {
    return 'Scraper VM is not reachable from this network.';
  }
  if (/virtualenv not found|bootstrap/i.test(combined)) {
    return 'Scraper VM is reachable, but the scraper package needs deployment/bootstrap.';
  }
  return 'Scraper VM workflow failed. Check stdout/stderr tails for details.';
}

function summarizeEvidenceFailure(stderr, stdout) {
  const combined = sanitizeMessage(`${stderr}\n${stdout}`);
  if (/validation|schema|banned|payload|localhost|scope|fixture/i.test(combined)) {
    return combined || 'Evidence validation failed.';
  }
  return 'Evidence bundle generation failed. Check the control server terminal.';
}

function summarizeIntegrationFailure(stderr, stdout) {
  const combined = sanitizeMessage(`${stderr}\n${stdout}`);
  if (/validation|schema|banned|payload|credential|hostname|policy|evidence/i.test(combined)) {
    return combined || 'Integration handoff export validation failed.';
  }
  return 'Integration handoff export failed. Check the control server terminal.';
}

function summarizeAuditFailure(stderr, stdout) {
  const combined = sanitizeMessage(`${stderr}\n${stdout}`);
  if (/audit|policy|operator|hash|runtime|schema|decision/i.test(combined)) {
    return combined || 'Operator audit append failed.';
  }
  return 'Operator audit append failed. Check the control server terminal.';
}

function sanitizeMessage(message) {
  return String(message || '')
    .replace(/\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b/g, '[INTERNAL-IP]')
    .replace(/\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b/g, '[IP-REDACTED]')
    .replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, '[EMAIL-REDACTED]')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 800);
}
