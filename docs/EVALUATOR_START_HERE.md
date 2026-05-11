# Evaluator Start Here

Use this path when you want to decide whether Prophet is credible as a
defensive cyber/evidence pilot from a fresh clone. It is intentionally
fixture-backed, policy-bound, and localhost-only.

## Three-Minute Buyer Path

Prerequisites:

- Python 3.9 or newer.
- Bash-compatible shell.
- Optional for console review: Node 24 or newer and npm.

If a prerequisite is missing or the local environment blocks the smoke,
console, or Playwright path, use `docs/PILOT_TROUBLESHOOTING.md`.
For the person running a buyer review, use
`docs/DEMO_OPERATOR_CHECKLIST.md`. For non-cyber terminology, use
`docs/GLOSSARY.md`. If a buyer asks for visual handoff materials, use
`docs/CONSOLE_EXPECTED_SCREENSHOTS.md` before capturing any redacted console
images.

From the repo root:

```bash
./scripts/check-local-env.sh
./scripts/run-pilot-demo-smoke.sh
```

Optional helper commands:

```bash
./scripts/run-pilot-demo-smoke.sh --dry-run
./scripts/check-local-env.sh --strict-console
PROPHET_CONFIRM_CLEAN_RUNTIME=clean-runtime ./scripts/run-pilot-demo-smoke.sh --clean-runtime
./scripts/run-policy-blocked-demo.sh
```

`--dry-run` lists the ignored runtime files the smoke path will generate.
`check-local-env.sh --strict-console` requires Node 24 or newer and npm when
the console path will be shown.
`--clean-runtime` removes only contents of the known ignored `outputs/runtime`
directories after explicit confirmation. `run-policy-blocked-demo.sh` is the
safe failure-mode check: it starts the localhost control server, attempts the
disabled live collection action, and requires the policy-bound
`policy_blocked` denial before writing a report under ignored runtime outputs.

Expected result:

- The pilot policy lints successfully.
- Customer-safe asset CSV import, asset seedset generation, seeded OSINT,
  forecast refresh, sandbox artifact generation, evidence export, evidence
  redaction reporting, audit export, audit redaction reporting,
  audit-retention reporting, and SIEM/ticketing handoff export all complete.
- The final step prints SHA-256 hashes and confirms they match
  `scripts/pilot-demo-smoke.sha256`.
- Generated runtime artifacts are checked against the reviewed pilot policy
  hash, so drift between policy and evidence is release-blocking.
- Outputs are written only under ignored `*/outputs/runtime/` directories.
- The optional policy-blocked demo returns `HTTP 403` for the live collection
  endpoint and records that no workflow was started.

Inspect these generated files:

| Question | File |
|---|---|
| What exposure did Prophet prioritize? | `world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json` |
| What defense evidence was produced? | `evidence/outputs/runtime/latest-edge-appliance.md` |
| What policy governed the run? | `evidence/outputs/runtime/latest-edge-appliance.json` |
| Was there an operator approval trail? | `evidence/outputs/runtime/pilot-demo-operator-audit-export.json` |
| What review templates can a SOC inspect? | `integrations/outputs/runtime/latest-edge-appliance/manifest.json`, `integrations/outputs/runtime/latest-edge-appliance/review_checklist.md`, and `integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip` |

For redacted examples of those outputs with packaged SHA-256 values, use
`docs/PILOT_OUTPUT_SNIPPETS.md`.

Stop the evaluation if the smoke command fails, a hash mismatch appears, or any
runtime artifact reports a policy-hash drift. Also stop if any artifact path is
outside an ignored `outputs/runtime` directory.

## Twelve-Minute Console Path

For the detailed analyst script, artifact checkpoints, and pass/fail criteria,
use `docs/ANALYST_WALKTHROUGH.md`.

After the smoke command passes:

```bash
(cd prophet-console && npm ci)
make console-demo
```

This starts the localhost-only control API and evaluator UI in one terminal.
Press `Ctrl-C` to stop both processes when the review is done.

If you prefer separate terminals:

```bash
make console-control
```

In a second terminal:

```bash
make console-ui
```

Open `http://127.0.0.1:5173`, enter the console, and confirm the header says
`EVALUATOR · DEMO ONLY`. This is the standard buyer-review mode. It hides
non-demo live collection controls and leaves only fixture/demo actions visible.
Then review:

1. Forecast panel: strike window, strike vector, confidence, and source rail.
2. Human gate: approval/denial behavior for fixture-scoped validation.
3. Defense output: patch summary, Sigma summary, and validation status.
4. Evidence panel: bundle hash, policy hash, source hashes, and export path.
5. Integration panel: generated SIEM/ticketing handoff manifest.
6. Alpha readiness: fixture, policy, evidence, export, and safety-boundary
   checks.

The console path should remain local-only. Do not switch to operator mode,
enable live collection workflows, add live target input, or paste customer
secrets or raw scraper text.

## Thirty-Minute Technical Path

For a deeper evaluator review of policy JSON Schema validation, runtime policy
hash drift checks, focused unit suites, release safety scanning, and evidence
integrity, use `docs/TECHNICAL_VALIDATION_WALKTHROUGH.md`.

## What This Pilot Proves

- Prophet can turn safe asset context and seeded public-source context into a
  defensible exposure-prioritization record.
- The default demo is reproducible and hash-verified.
- Evidence includes policy ID/hash, approval record hash, source hashes,
  forecast context, defense artifact context, validation status, and handoff
  export hashes.
- Audit export includes a redaction report proving the raw event log was not
  embedded in the customer-review artifact.
- Integration outputs are review templates, not production pushes.

## What This Pilot Does Not Prove

- Production SaaS readiness.
- Live attack prediction, live target validation, or live collection.
- Exploit generation, payload delivery, or target-control capability.
- Autonomous patch deployment.
- Production SIEM/ticketing pushes.
- RBAC, SSO, tenant isolation, production secrets handling, signed evidence
  manifests, or signed operator approvals.

If a review requires live targets, offensive validation, raw scraper output, or
production control changes, stop the standard pilot review. That is outside this
buyer-safe package and must not be worked around during evaluation.

Use `docs/EVALUATOR_WORKSHEET.md` to record findings during a customer review.
Use `docs/CONSOLE_EXPECTED_SCREENSHOTS.md` only for secondary visual handoff
materials; hashes and generated artifacts remain the primary evidence. If a
reviewer asks for responsive screenshots, run
`cd prophet-console && npm run capture:screenshots`, then
`make console-screenshot-check`, and review the ignored redacted runtime output
before sharing.
