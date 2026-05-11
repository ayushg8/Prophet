# Thirty-Minute Technical Validation Walkthrough

Use this path when a technical evaluator wants to verify Prophet's policy,
test, and evidence controls without enabling live collection. The path stays
fixture-backed, seeded-OSINT-backed, policy-bound, and localhost-only.

## Preconditions

Start from the repo root on a clean-enough checkout. The working tree can have
local edits, but generated runtime files must remain under ignored
`*/outputs/runtime/` directories.

Required tools:

- Python 3.9 or newer.
- Bash-compatible shell.
- Node 24 or newer and npm if the evaluator runs console acceptance.

If a required tool is missing, use `docs/PILOT_TROUBLESHOOTING.md` before
changing commands or paths.

Do not add target hosts, credentials, private hostnames, raw scraper text, or
customer secrets. Do not enable live collection workflows or any non-fixture
sandbox mode.

## Timeboxed Review

| Time | Action | Command or artifact |
|---|---|---|
| 0:00-3:00 | Generate the local pilot artifacts and prove the packaged hash contract. | `./scripts/run-pilot-demo-smoke.sh` |
| 3:00-6:00 | Validate the reviewed pilot policy against the JSON Schema and semantic safety checks. | `PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint --policy policy/prophet-pilot-policy.json --schema policy/prophet-pilot-policy.schema.json` |
| 6:00-9:00 | Compare the narrow fixture-only policy against the default pilot policy. Expanded modes, sources, sandbox profiles, exports, or retention windows should be intentional. | `PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint --policy policy/examples/fixture-only-policy.json --compare-to policy/prophet-pilot-policy.json` |
| 9:00-12:00 | Verify generated runtime artifacts still carry the reviewed policy hash. | See the runtime policy verification command below. |
| 12:00-16:00 | Run the validator-heavy Python suites that cover policy, evidence, sandbox, and integration handoffs. | See the focused unit commands below. |
| 16:00-20:00 | Run release safety scanning for tracked files. This catches unsafe terms, runtime artifact staging, missing policy hashes, and console live-action gates. | `python3 scripts/check-release-safety.py --tracked --paths-only` |
| 20:00-23:00 | Explain any local artifact drift using hashes only. | `python3 scripts/diff-pilot-demo-fixtures.py --baseline scripts/pilot-demo-smoke.sha256 --fail-on-diff` |
| 23:00-26:00 | Prove the approved live-action failure mode remains blocked by policy. | `./scripts/run-policy-blocked-demo.sh` |
| 26:00-30:00 | Inspect the buyer evidence and record pass/fail notes. | `evidence/outputs/runtime/latest-edge-appliance.md`; `docs/EVALUATOR_WORKSHEET.md` |

## Runtime Policy Verification

Run this after the smoke command succeeds:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json \
  --verify-runtime-artifacts \
    world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.manifest.json \
    cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json \
    cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json \
    evidence/outputs/runtime/latest-edge-appliance.json \
    evidence/outputs/runtime/pilot-demo-operator-audit-export.json \
    evidence/outputs/runtime/pilot-demo-operator-audit-retention.json \
    integrations/outputs/runtime/latest-edge-appliance/manifest.json
```

Expected result:

- Every listed artifact is recognized by schema.
- Every policy hash matches `policy/prophet-pilot-policy.json`.
- No artifact with missing policy hash is accepted.

## Focused Unit Commands

These are the fastest technical checks for the defensive pilot contract:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v
python3 -m unittest discover -s scripts/tests -v
```

If time permits, add the broader contract suites:

```bash
PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
```

For the React console acceptance path:

```bash
cd prophet-console
npm run acceptance
```

`npm run acceptance` includes the root smoke command, console lint/build,
control-server evidence/readiness smoke, and Playwright smoke.

## Evidence Review

Open `evidence/outputs/runtime/latest-edge-appliance.md` and confirm:

- The CISO summary table is present.
- `policy_id`, `policy_sha256`, bundle hash, forecast hash, defense artifact
  hash, approval record hash, and source hashes are present.
- The seeded OSINT basis names source IDs and freshness/failure status without
  raw scraper text.
- Sandbox validation status is fixture-backed and localhost-only.
- The evidence includes the no-live-target-data assertion.
- Integration outputs are marked as review templates, not production pushes.

Then inspect:

- `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-retention.json`
- `integrations/outputs/runtime/latest-edge-appliance/manifest.json`

The audit export should be hash-chained and redacted. The integration manifest
should include file hashes and the same policy hash as the evidence bundle.

## Pass Criteria

- Smoke hashes match `scripts/pilot-demo-smoke.sha256`.
- Policy lint, schema validation, comparison, and runtime policy verification
  all pass.
- Focused unit suites pass.
- Release safety scan passes.
- The policy-blocked demo returns `HTTP 403` and records `policy_blocked`.
- Every generated output reviewed is under an ignored `outputs/runtime`
  directory.

## Stop Criteria

Stop the evaluation and do not call the pilot buyer-ready if any of these
occur:

- A smoke hash mismatch appears without an approved fixture manifest update.
- Runtime policy verification reports a missing or changed policy hash.
- Release safety scanning finds a credential, private hostname, live IP,
  unsafe command, runtime artifact, or unapproved source catalog entry.
- Console or control-server behavior starts a live workflow instead of a
  policy-blocked denial.
- Any evidence or handoff artifact claims live-target validation.

## Notes For Evaluators

This walkthrough proves the public pilot boundary and artifact integrity. It
does not prove production SaaS controls such as RBAC, SSO, tenant isolation,
production secrets handling, or signed evidence manifests.
