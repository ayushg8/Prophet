# Pilot Troubleshooting

Use this guide when the local buyer pilot fails before or during the smoke,
console, or acceptance path. Keep the evaluation fixture-backed,
policy-bound, and localhost-only while debugging.

Do not add target hosts, credentials, private hostnames, customer secrets, raw
scraper text, live collection, or non-fixture sandbox modes to work around a
local setup problem.

## Fast Environment Check

Run these from the repo root:

```bash
python3 --version
bash --version
git --version
```

For console or acceptance review:

```bash
cd prophet-console
node --version
npm --version
npx playwright --version
```

Expected versions:

| Tool | Required for | Expected |
|---|---|---|
| Python | Smoke path, policy, evidence, sandbox, integrations | 3.11 or newer |
| Bash | Smoke scripts | Any modern Bash-compatible shell |
| Node | Console and acceptance path | 24.x |
| npm | Console dependency install and scripts | Bundled with Node 24 |
| Playwright | Browser smoke inside `npm run acceptance` | Installed from `prophet-console/package-lock.json` |

## Python Problems

### `python3: command not found`

Install Python 3.11 or newer, then rerun:

```bash
python3 --version
./scripts/run-pilot-demo-smoke.sh
```

Do not switch to a system Python below 3.11. The pilot scripts and tests assume
3.11-era standard library behavior.

### `ModuleNotFoundError` in policy, evidence, or world-side commands

Run commands from the repo root and keep the documented `PYTHONPATH` prefix.
For example:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
```

If the smoke script fails with an import error, record the exact command and
first traceback line in `docs/EVALUATOR_WORKSHEET.md`. Do not patch around it
by copying modules or changing generated artifact paths.

### Smoke script says a runtime path is outside `outputs/runtime`

Stop the pilot review. Runtime outputs must stay under ignored
`*/outputs/runtime/` directories. Re-run the dry run to inspect the planned
outputs without writing them:

```bash
./scripts/run-pilot-demo-smoke.sh --dry-run
```

## Shell Problems

### `Permission denied` running the smoke script

Run the script through Bash:

```bash
bash scripts/run-pilot-demo-smoke.sh
```

If that passes, note the local executable-bit issue in the worksheet. Do not
move the script, duplicate it, or write outputs outside the runtime directories.

### `env: bash: No such file or directory`

Use a machine with a Bash-compatible shell available, or run from a terminal
where `bash --version` succeeds. The buyer pilot scripts are not validated for
PowerShell-only execution.

## Node And npm Problems

### `node: command not found` or `npm: command not found`

Install Node 24 with npm, then verify from the console package:

```bash
cd prophet-console
node --version
npm --version
```

Only the console and browser acceptance path require Node. The three-minute
smoke path should still run with Python and Bash alone.

### `npm ci` fails because the Node version is too old

Switch to Node 24 and rerun:

```bash
cd prophet-console
npm ci
```

Do not edit `package-lock.json` to satisfy a local version mismatch. The lockfile
is part of the reviewed console contract.

### `npm run dev:control` says the port is already in use

Stop the previous local console/control-server process if you started one
earlier, then rerun:

```bash
cd prophet-console
npm run dev:control
```

The control server must remain bound to localhost for pilot review. Do not
change it to a public interface for convenience.

## Playwright Problems

### `Executable doesn't exist` or browser install errors

Install the checked-in Playwright browser dependency from the console package:

```bash
cd prophet-console
npx playwright install chromium
```

Then rerun the browser smoke:

```bash
npm run test:smoke
```

If browser installation is blocked by the evaluator environment, still run the
three-minute smoke path and record the Playwright blocker separately. Do not
mark console acceptance complete until the browser smoke passes.

### `npm run acceptance` fails after the Python smoke succeeds

Run the console checks one at a time to isolate the failing layer:

```bash
cd prophet-console
npm run lint
npm run build
npm run test:control:evidence
npm run test:smoke
```

If `test:control:evidence` fails, inspect only sanitized runtime outputs under
`evidence/outputs/runtime/` and `integrations/outputs/runtime/`. If
`test:smoke` fails, keep Playwright traces local and do not paste customer data
or raw scraper text into issue notes.

## Hash Or Policy Drift Problems

### Smoke hash mismatch

Explain the mismatch with hashes only:

```bash
python3 scripts/diff-pilot-demo-fixtures.py \
  --baseline scripts/pilot-demo-smoke.sha256 \
  --fail-on-diff
```

Do not update `scripts/pilot-demo-smoke.sha256` unless the artifact contract
change has been reviewed.

### Policy hash drift

Run the policy runtime verification from
`docs/TECHNICAL_VALIDATION_WALKTHROUGH.md`. A missing or changed policy hash is
release-blocking until the artifact and policy change are reviewed together.

## When To Stop

Stop the buyer-ready claim for the current run if:

- Python smoke fails.
- A hash mismatch is unexplained.
- Runtime policy drift appears.
- Any output path leaves ignored `outputs/runtime` directories.
- Console acceptance is claimed without a passing Playwright smoke.
- A workaround would require live collection, live targets, credentials,
  private hostnames, raw scraper text, or offensive workflow.
