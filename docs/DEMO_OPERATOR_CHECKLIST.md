# Demo Operator Checklist

Use this checklist before and during a buyer pilot review. It keeps the demo
inside the approved Prophet boundary: fixture-backed, seeded-OSINT-backed,
policy-bound, and localhost-only.

## Before The Review

- Confirm the repo is the intended Prophet workspace.
- Confirm no customer secrets, raw scraper text, live IPs, private hostnames, or
  credential files were added to the working tree.
- Confirm Python 3.9 or newer is available.
- If the console will be shown, confirm Node 24 or newer and npm are available.
- Read `docs/EVALUATOR_START_HERE.md` and keep
  `docs/EVALUATOR_WORKSHEET.md` open for pass/fail notes.
- Review the active pilot policy: `policy/prophet-pilot-policy.json`.
- Use only safe local operator labels such as `fixture` or `local-console`;
  see `docs/OPERATOR_IDENTITY_GUIDE.md`.
- Do not enable live collection workflows or any non-fixture validation mode
  for a standard buyer review. The sandbox runner requires a sanitized
  customer approval record before any non-fixture mode is even considered, and
  the public repo still ships no container execution profile.

## Preflight Commands

Run these from the repo root:

```bash
./scripts/run-pilot-demo-smoke.sh --dry-run
./scripts/run-pilot-demo-smoke.sh
python3 scripts/diff-pilot-demo-fixtures.py
./scripts/run-policy-blocked-demo.sh
git diff --check
```

Pass conditions:

- The smoke script completes and its hash check matches
  `scripts/pilot-demo-smoke.sha256`.
- The runtime policy-hash drift check passes.
- The fixture diff command reports no unexpected hash drift unless the demo
  contract was intentionally updated and reviewed.
- The policy-blocked demo returns the expected denied live-action result.
- `git diff --check` reports no whitespace errors.

Stop the review if any preflight command fails.

## Optional Console Setup

Use two terminals:

```bash
cd prophet-console
npm ci
npm run dev:control
```

```bash
cd prophet-console
npm run dev:evaluator
```

Open `http://127.0.0.1:5173`. Evaluator mode is the standard buyer-review
mode; it shows fixture/demo controls and hides non-demo live collection
controls even if an operator has a local collection environment configured.
Keep the console local-only. Do not paste customer secrets, raw scraper text,
hostnames, IP addresses, URLs, or unreviewed customer data into the UI.

Before the buyer joins, run `make console-live-check` from the repo root while
the console is still running. It verifies readiness plus the local evidence and
integration endpoints, validates the runtime audit log, and writes only ignored
runtime outputs.

If the buyer asks for responsive visual follow-up, run
`cd prophet-console && npm run capture:screenshots`, then
`make console-screenshot-check`. Share screenshots only after the verifier
passes and the buyer explicitly asked for redacted visual material.

Use `npm run dev:operator` only for an internal, approved operator review. It
does not enable live collection by itself; live collection still requires the
separate `VITE_PROPHET_ENABLE_VM_SCRAPER=1` flag, control-server policy gates,
and a written isolated collection plan.

## Three-Minute Talk Track

- Start with the product boundary: Prophet prioritizes defensive exposure
  classes and exports evidence; it does not run live target workflows.
- Show the smoke command result and deterministic hash check.
- Open `evidence/outputs/runtime/latest-edge-appliance.md`.
- Point to the strike window, strike vector, asset seed summary, seeded OSINT
  source refs, policy ID/hash, approval record hash, and validation status.
- Open `integrations/outputs/runtime/latest-edge-appliance/manifest.json`.
- Explain that SIEM and ticketing outputs are review templates, not automatic
  production changes.
- Show the policy-blocked report if the buyer asks how unsafe actions fail.
- Use the policy-blocked evaluator action runbook in
  `docs/PILOT_TROUBLESHOOTING.md` if the console or control API returns
  `policy_blocked` / `HTTP 403` during review.

## Artifact Checkpoints

| Question | Runtime artifact |
|---|---|
| What did the forecast say? | `world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json` |
| What evidence can leadership review? | `evidence/outputs/runtime/latest-edge-appliance.md` |
| What policy governed the run? | `evidence/outputs/runtime/latest-edge-appliance.json` |
| What approval trail exists? | `evidence/outputs/runtime/pilot-demo-operator-audit-export.json` |
| What handoff templates were generated? | `integrations/outputs/runtime/latest-edge-appliance/manifest.json` |
| Did unsafe live behavior stay blocked? | `evidence/outputs/runtime/policy-blocked-live-demo/report.json` |

## Stop Gates

Stop and mark the worksheet as blocked if:

- Any command reports a hash mismatch, policy-hash drift, or validation failure
  outside the expected policy-blocked demo.
- Any generated artifact appears outside an ignored `outputs/runtime`
  directory.
- Any artifact contains credentials, private hostnames, live IPs, raw scraper
  text, or target-control instructions.
- A buyer asks to test a live target during the standard public pilot review.
- A non-fixture validation plan lacks the sanitized sandbox customer approval
  record, written customer approval, and a reviewed policy.

## After The Review

- Record decisions and blockers in `docs/EVALUATOR_WORKSHEET.md`.
- Share artifact paths and SHA-256 values, not raw customer-sensitive content.
- Use `docs/CONSOLE_EXPECTED_SCREENSHOTS.md` before preparing any redacted
  console visuals for follow-up.
- Keep runtime outputs local unless the customer data-boundary agreement allows
  sharing.
- Do not commit generated runtime outputs.
- Capture the next pilot slice: source allowlist, asset/SBOM input, sandbox
  profile, SIEM/ticketing format, retention period, or evidence requirement.
