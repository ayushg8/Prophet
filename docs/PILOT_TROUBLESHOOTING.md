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
| Python | Smoke path, policy, evidence, sandbox, integrations | 3.9 or newer |
| Bash | Smoke scripts | Any modern Bash-compatible shell |
| Node | Console and acceptance path | 24 or newer |
| npm | Console dependency install and scripts | Bundled with Node 24+ |
| Playwright | Browser smoke inside `npm run acceptance` | Installed from `prophet-console/package-lock.json` |

## Python Problems

### `python3: command not found`

Install Python 3.9 or newer, then rerun:

```bash
python3 --version
./scripts/run-pilot-demo-smoke.sh
```

Do not switch to a system Python below 3.9. The current pilot scripts and tests
are verified on the local Python 3.9 path.

### Optional virtualenv setup

The Python pilot path uses the standard library and repo-local modules, so a
virtualenv is optional. Use one only to isolate local tooling:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 --version
./scripts/check-local-env.sh
./scripts/run-pilot-demo-smoke.sh
```

No `pip install` step is required for the root smoke path. Keep generated
virtualenv files out of commits.

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

Install Node 24 or newer with npm, then verify from the console package:

```bash
cd prophet-console
node --version
npm --version
```

Only the console and browser acceptance path require Node. The three-minute
smoke path should still run with Python and Bash alone.

### `npm ci` fails because the Node version is too old

Switch to Node 24 or newer and rerun:

```bash
cd prophet-console
npm ci
```

Do not edit `package-lock.json` to satisfy a local version mismatch. The lockfile
is part of the reviewed console contract.

### `make console-demo` says a port is already in use

`make console-demo` checks the control API and evaluator UI ports before it
starts child processes. If the default ports are already occupied, either stop
the previous local console/control-server process or run the demo on alternate
localhost ports:

```bash
PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 make console-demo
```

The control server and UI must remain bound to localhost for pilot review. Do
not change them to a public interface for convenience.

### `make console-live-check` fails

Keep the console running and confirm the ports match the demo process:

```bash
PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 make console-live-check
```

Use the same port overrides that were used for `make console-demo`. This check
calls only localhost readiness, evidence demo-bundle, and integration
demo-export endpoints, then validates the ignored runtime audit log. If it
fails, inspect only sanitized runtime outputs under `evidence/outputs/runtime/`
and `integrations/outputs/runtime/`; do not enable live collection or weaken
the audit safety attestation to make it pass.

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

### Dependency audit fails

Run the audit from the console package so npm reads the reviewed lockfile:

```bash
cd prophet-console
npm audit --audit-level=moderate
```

If it reports a moderate or higher issue, stop the buyer-ready claim for the
console path until the dependency change is reviewed. Do not bypass the audit
with `--force`, regenerate `package-lock.json` opportunistically, or add a new
package during a buyer review. The root Python smoke may still be shown only if
the review does not claim browser-console acceptance.

Record the package name, severity, and advisory URL in the worksheet. Do not
paste token values, environment variables, local paths outside the repo, or
customer data into the note.

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

## Policy-Blocked Evaluator Action Runbook

Use this when the console, control API, or smoke path returns `policy_blocked`
or `HTTP 403` during a buyer/evaluator review. In the standard pilot, this is
usually a correct safety result, not a failure.

### Expected policy-blocked actions

These actions should stay blocked in the public buyer pilot:

- Live collection workflow.
- Live target input.
- Arbitrary target input.
- Payload generation.
- Raw scraper text.
- Private hostnames.
- Credentials.

Do not bypass the policy, change environment flags, edit the policy file, or
switch to operator mode during a buyer review to make one of these actions run.

### Operator response

1. State that the requested action is outside the standard fixture-backed pilot.
2. Use the sanitized demo path instead: click `Refresh demo` in the console or
   rerun `./scripts/run-pilot-demo-smoke.sh`.
3. If the buyer wants proof of the guardrail, run:

   ```bash
   ./scripts/run-policy-blocked-demo.sh
   ```

4. Share only the result shape and hash/report path:
   `evidence/outputs/runtime/policy-blocked-live-demo/report.json`.
5. Record the request as a buyer validation signal if it affects pilot scope,
   but do not mark validation progress, calls booked, or messages sent unless
   the corresponding real buyer event happened.

### If the block looks unexpected

Run these checks without changing policy state:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
cd prophet-console
npm run test:control:evidence
```

If the policy linter or control evidence smoke fails, stop the review and keep
runtime outputs local. If they pass, treat the blocked action as expected and
continue with the fixture-backed demo.

### Escalation boundary

Only a separate scoped customer policy, legal/source-terms review, sanitized
customer approval record, and `build_next_slice` validation state can justify
future work on broader policy-enabled modes. Until then, policy-blocked
evaluator actions are evidence that the pilot boundary is working.

## Evidence Generation Failure Runbook

Use this when `evidence.bundle`, `npm run test:control:evidence`, or the
console evidence button fails.

1. Stop sharing the current evidence output.
2. Confirm the latest defense artifact is a fixture or approved localhost
   sandbox artifact under an ignored runtime output path.
3. Rerun the evidence unit suite:

   ```bash
   PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
   ```

4. Rerun the default smoke:

   ```bash
   ./scripts/run-pilot-demo-smoke.sh
   ```

5. If the failure persists, keep the bundle local and record only the failing
   command, exit status, artifact path, and hash state in the worksheet.

Do not fix evidence generation by copying raw scraper text, disabling
redaction, weakening `no_live_target_data`, editing policy hashes, or moving
outputs outside ignored `outputs/runtime` directories.

## Sandbox Validation Failure Runbook

Use this when `sandbox_runner`, the smoke path, or the console validation
status does not reach the expected fixture-backed `blocked` result.

1. Treat the run as not buyer-ready.
2. Verify the run stayed in fixture or localhost-sandbox mode:

   ```bash
   PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
   ```

3. Inspect only sanitized runtime artifacts and manifests:
   `cyber-side/outputs/runtime/*sandbox*` and
   `cyber-side/outputs/runtime/*manifest*`.
4. If the result is a known failure/timeout fixture, use the evidence failure
   evidence path and explain that the defense did not pass.
5. If the mode is non-fixture, stop unless a sanitized customer approval record
   and reviewed policy explicitly allow it.

Do not introduce live targets, raw logs, network egress, container execution,
credentials, or private hostnames to make validation pass.

## When To Stop

Stop the buyer-ready claim for the current run if:

- Python smoke fails.
- A hash mismatch is unexplained.
- Runtime policy drift appears.
- Evidence generation fails or cannot validate the bundle.
- Sandbox validation fails outside an expected failure/timeout evidence path.
- The console dependency audit reports a moderate or higher issue.
- Any output path leaves ignored `outputs/runtime` directories.
- Console acceptance is claimed without a passing Playwright smoke.
- A workaround would require live collection, live targets, credentials,
  private hostnames, raw scraper text, or offensive workflow.
