import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const port = Number(process.env.PROPHET_CONTROL_PORT || 8787);
const workflowScript = path.join(repoRoot, 'world-side/scripts/run-scraper-vm-workflow.sh');
const worldSideDir = path.join(repoRoot, 'world-side');
const candidateFile = path.join(
  repoRoot,
  'world-side/fixtures/exploit-candidate-edge-appliance.json',
);
const demoChatterFile = path.join(
  repoRoot,
  'world-side/fixtures/sanitized-chatter-sample.jsonl',
);
const cyberArtifactFile = path.join(
  repoRoot,
  'cyber-side/fixtures/exploit-engine-output-edge-appliance.json',
);
const cyberPortfolioFile = path.join(
  repoRoot,
  'cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json',
);
const forecastOut = path.join(
  repoRoot,
  'world-side/outputs/runtime/live-scraper-forecast-edge-appliance.json',
);
const demoForecastOut = path.join(
  repoRoot,
  'world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json',
);
const incomingDir = path.join(repoRoot, 'world-side/data/chatter/incoming/console');

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
    writeJson(res, 200, {
      ok: true,
      running: Boolean(activeRun),
      lastResult,
      target: process.env.SCRAPER_SSH_TARGET || 'prophet-scraper',
    });
    return;
  }

  if (req.method === 'POST' && req.url === '/api/scraper/run') {
    if (!isConsoleRequest(req, allowedOrigin)) {
      writeForbidden(res);
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

  writeJson(res, 404, {
    ok: false,
    status: 'not_found',
    message: 'Unknown Prophet control endpoint.',
  });
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Prophet control server listening on http://127.0.0.1:${port}`);
  console.log(`Scraper target: ${process.env.SCRAPER_SSH_TARGET || 'prophet-scraper'}`);
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
    PYTHONPATH: [worldSideDir, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
  };

  const child = spawn(
    'python3',
    [
      '-m',
      'forecaster.cli',
      '--candidate',
      candidateFile,
      '--chatter',
      demoChatterFile,
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
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
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
      message: 'Demo forecast refreshed from sanitized fixture chatter.',
      forecast,
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
    };
  } catch (error) {
    return {
      ok: false,
      status: 'demo_forecast_unreadable',
      startedAt,
      finishedAt,
      exitCode: result.exitCode,
      message: `Demo refresh finished, but the forecast file could not be read: ${error.message}`,
      stdoutTail: tail(result.stdout),
      stderrTail: tail(result.stderr),
    };
  }
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
  res.setHeader('Access-Control-Allow-Headers', 'content-type,x-prophet-control');
  return allowedOrigin;
}

function writeJson(res, status, payload) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(payload, null, 2));
}

function isConsoleRequest(req, allowedOrigin) {
  return allowedOrigin && req.headers['x-prophet-control'] === 'local-console';
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
