# Pilot Demo

This demo is designed for a paid pilot conversation with a CISO, mission owner,
investor, or contracting officer. It shows the product boundary, not an
offensive capability.

For the shortest evaluator path, use `docs/EVALUATOR_START_HERE.md`. For local
setup failures, use `docs/PILOT_TROUBLESHOOTING.md`. For buyer notes and
pass/fail review, use `docs/EVALUATOR_WORKSHEET.md`. For the operator running
the review, use `docs/DEMO_OPERATOR_CHECKLIST.md`; for shared terminology, use
`docs/GLOSSARY.md`. For redacted example output snippets with packaged hashes,
use `docs/PILOT_OUTPUT_SNIPPETS.md`.

## What Is Real Today

- Deterministic forecaster output for the edge-appliance and financial-workflow
  scenarios.
- Customer-safe CSV asset import with accepted/rejected row report.
- Asset import manifest with raw CSV hash, sanitized output hashes, and proof
  that raw row values were not embedded.
- Asset inventory to safe asset/SBOM OSINT seedset generation.
- Fixture-backed seeded OSINT snapshot generation from tracked public-source
  fixtures.
- Safe non-operational exposure-class defense portfolio generation.
- Deterministic `sandbox_runner` output for the edge-appliance and
  financial-workflow fixture profiles.
- Sandbox run manifest with artifact hash, sanitized log hash, policy hash, and
  explicit proof that no raw logs were retained.
- A fail-closed customer approval gate before any non-fixture sandbox mode is
  considered. The public repo still has no packaged container execution profile.
- Validated Direction C defense artifact with patch summary, Sigma summary,
  localhost-only validation status, and cyber-side validator coverage.
- JSON and Markdown evidence bundle export with SHA-256 hashes, an explicit
  no-live-target-data assertion, sandbox profile/run-manifest provenance,
  sandbox pass/failure/timeout evidence, and a CISO review summary table. The
  Markdown forecast section includes the selected window rationale, vector
  rationale, and cited forecast source IDs.
- Hash-chained operator audit log validation and safe audit summary export with
  a machine-checkable redaction report.
- Safe SIEM and ticketing handoff export from validated evidence. These are
  review templates, not auto-deploying production integrations, and they carry
  the same no-live-target-data assertion.
- Pilot policy enforcement through `policy/prophet-pilot-policy.json`.
- Policy linting for default and customer-specific policies, including
  allowed-mode, source allowlist, sandbox-profile allowlist, blocked-control,
  attestation, runtime-output checks, and semantic comparison against the
  default pilot policy.
- Localhost control server endpoints for demo refresh, fixture loading, and
  evidence generation. Evidence generation prefers the latest valid sandbox
  runtime artifact when present and permitted by policy; otherwise it falls back
  to the checked-in defense fixture.
- React console workflow for fixture-backed replay and evidence export.

## What Is Fixture-Backed

- The defense artifact is a tracked fixture.
- The validation result is a sandbox fixture or deterministic simulation.
- The asset inventory is fictional and product-family level only.
- The evidence bundle can include the fictional asset/SBOM context to show the
  pilot integration shape.
- The asset/SBOM seedset is derived from that fixture and contains only CVE,
  package, product-family, exposure-class, owner queue, source ID, and hash
  metadata.
- The seeded OSINT snapshot reads tracked fixture responses unless `--live` is
  explicitly supplied to the snapshot CLI. The packaged demo does not use live
  collection.

## Disabled By Default

- Live collection workflows.
- Live exploit validation.
- Arbitrary target input.
- Private research lab scaffolding.
- Production deployment or patch application.

## Three-Minute Walkthrough

From a fresh clone:

```bash
cd Prophet
./scripts/run-pilot-demo-smoke.sh
```

To run the second packaged sector fixture:

```bash
./scripts/run-pilot-demo-smoke.sh --sector financial-workflow
```

To preview the runtime outputs before generating them:

```bash
./scripts/run-pilot-demo-smoke.sh --dry-run
```

To start from a clean runtime workspace, use the guarded cleanup option. It
removes only contents of the known ignored `outputs/runtime` directories after
confirmation:

```bash
PROPHET_CONFIRM_CLEAN_RUNTIME=clean-runtime ./scripts/run-pilot-demo-smoke.sh --clean-runtime
```

The smoke command imports a safe CSV asset fixture, runs asset seedset
generation, fixture-backed seeded OSINT, forecast refresh, safe defense portfolio
generation, deterministic sandbox artifact generation, evidence bundle
generation, audit export, artifact/log manifest generation, audit-retention
reporting, SIEM/ticketing handoff export, local operator approval audit
logging, policy linting, validation, golden hash verification, and runtime
policy-hash drift verification. It does not contact live targets or require
private context.

To explain whether a local demo run changed from the packaged fixture contract,
use the hash-only diff command:

```bash
python3 scripts/diff-pilot-demo-fixtures.py
```

The output lists only repo-relative artifact paths and SHA-256 hashes. It does
not print evidence, OSINT, sandbox, audit, or integration artifact contents.

To show the approved failure mode, run the policy-blocked live behavior demo:

```bash
./scripts/run-policy-blocked-demo.sh
```

This starts the localhost control server on an alternate port, calls the live VM
scraper endpoint with the required local-console header, and verifies the
expected `HTTP 403` / `policy_blocked` denial. The script writes a small
machine-readable report to
`evidence/outputs/runtime/policy-blocked-live-demo/report.json` and does not
contact live targets, generate payloads, read credentials, or print raw scraper
text.

Then inspect:

- `evidence/outputs/runtime/latest-edge-appliance.json`
- `evidence/outputs/runtime/latest-edge-appliance.md`
- `assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.manifest.json`
- `cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- `evidence/outputs/runtime/pilot-demo-operator-audit-retention.json`
- `integrations/outputs/runtime/latest-edge-appliance/manifest.json`

For the financial workflow sector, inspect the matching
`latest-financial-workflow.*` and `demo-financial-workflow-*` runtime paths.

Show bundle ID, bundle SHA-256, forecast ID, sandbox artifact ID, policy ID,
policy SHA-256, approval record hash, validation result, source hashes, and
the CISO review summary table at the top of the Markdown report.
For security review, the smoke script exports the local operator audit summary,
its redaction report, and the retention report. To regenerate those files
directly:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit export \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --out-json evidence/outputs/runtime/pilot-demo-operator-audit-export.json
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit retention \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --policy policy/prophet-pilot-policy.json \
  --out-json evidence/outputs/runtime/pilot-demo-operator-audit-retention.json
```

## Twelve-Minute Walkthrough

For a minute-by-minute analyst review that covers the console, evidence bundle,
operator audit, and SIEM/ticket handoff exports, use
`docs/ANALYST_WALKTHROUGH.md`.

1. Explain the forecast: strike window, vector, source rail, and defensive
   implication.
2. Show the exposure-class portfolio: prioritized defensive classes and
   known-pressure replay classes, with no payloads or live target steps.
3. Run the full Prophet replay and pause at the human gate.
4. Authorize the fixture-scoped validation.
5. Show vulnerable-to-blocked transition, patch summary, and Sigma summary.
6. Generate the evidence bundle.
7. Open the Markdown report and walk through source refs, safety attestation,
   and hashes.
8. Explain how customer asset inventory or SBOM context becomes safe OSINT
   seedsets for a paid pilot.

## Thirty-Minute Technical Walkthrough

For a technical buyer review of policy schema validation, runtime policy-hash
drift checks, focused unit suites, release safety scanning, policy-blocked live
behavior, and evidence integrity, use
`docs/TECHNICAL_VALIDATION_WALKTHROUGH.md`.

## Demo Commands

```bash
./scripts/run-pilot-demo-smoke.sh
```

```bash
PYTHONPATH=. python3 -m unittest discover -s assets/tests -v
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests -v
PYTHONPATH=world-side:world-side/scraper:. python3 -m unittest discover -s world-side/tests -v
PYTHONPATH=.:cyber-side python3 -m unittest discover -s sandbox_runner/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s policy/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s evidence/tests -v
PYTHONPATH=.:cyber-side:world-side python3 -m unittest discover -s integrations/tests -v
```

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/prophet-pilot-policy.json
```

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m policy.lint \
  --policy policy/examples/fixture-only-policy.json \
  --compare-to policy/prophet-pilot-policy.json
```

```bash
(cd prophet-console && npm ci)
make console-demo
```

This starts the localhost-only control API and evaluator UI in one terminal.
Press `Ctrl-C` to stop both when the review is done.

With the console running, verify the live local endpoints before the buyer
joins:

```bash
make console-live-check
```

This calls only the localhost readiness, evidence demo-bundle, and integration
demo-export endpoints. It writes ignored runtime evidence/handoff/audit outputs
and confirms the audit events include the required no-live-target-data
attestation.

If a qualified reviewer asks for responsive visual handoff artifacts, run:

```bash
cd prophet-console
npm run capture:screenshots
cd ..
make console-screenshot-check
```

Share screenshots only after the verifier passes and the reviewer explicitly
asks for redacted visual material.

If you prefer separate terminals:

```bash
make console-control
```

In a second terminal:

```bash
make console-ui
```

Open `http://127.0.0.1:5173`.

## Runtime Outputs

The smoke script writes only ignored runtime artifacts. The final validation
steps verify the generated artifact hashes against
`scripts/pilot-demo-smoke.sha256` for the default edge-appliance sector, or
`scripts/pilot-demo-smoke-financial-workflow.sha256` for
`--sector financial-workflow`, and check that the generated evidence, OSINT,
sandbox, audit, and integration runtime artifacts still carry the reviewed
pilot policy hash. A hash mismatch or policy-hash drift is release-blocking
until the artifact contract change is reviewed and this document is updated.
If a reviewer needs the reason for a mismatch, run
`python3 scripts/diff-pilot-demo-fixtures.py --baseline scripts/pilot-demo-smoke.sha256`.
For two saved hash manifests, use `--candidate-manifest`; for a copied runtime
workspace, use `--candidate-root`. The command reports unchanged, changed,
missing, and added hash entries without exposing raw artifact text.
The evidence Markdown now includes a dedicated source freshness and failure
section so reviewers can see the seeded OSINT snapshot age, source health, and
any sanitized source failures without exposing raw scraper text.
The Forecast section also surfaces the selected window rationale, vector
rationale, and cited forecast source IDs so reviewers can trace "why this
first, why now" without opening the raw forecast JSON.
It also includes a validation failure-evidence subsection that distinguishes
passed, failed, and timeout outcomes using sanitized status fields only; no raw
validation logs or target data are embedded.
The Console evidence panel mirrors the same source freshness and failure
signals after evidence generation, so reviewers do not need to open the JSON
first.

| Artifact | Path | SHA-256 from packaged smoke |
|---|---|---|
| CSV-imported inventory | `assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.json` | `db3e5a41ffb6e34d0ff9566b04d71191dc71d10a44fdf44a0d63794dca615e06` |
| CSV import report | `assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.report.json` | `b14e2bb024422da2556082fe2e0218c7524753e458fa73ee49e78f1a828b97e7` |
| CSV import manifest | `assets/outputs/runtime/demo-dib-edge-appliance-inventory-from-csv.manifest.json` | `503a9f34dc84fc8124e9d581ca9d69829d655a8055399c1efbdc56f7779caa04` |
| CSV-derived seedset | `assets/outputs/runtime/demo-dib-edge-appliance-seedset-from-csv.json` | `123f9fc76beb82ac46fd51b29f33973592cee767053e2cd81678d05d0dfe0779` |
| Asset seedset | `assets/outputs/runtime/demo-dib-edge-appliance-seedset.json` | `6663d5e478552f85ff818934087be4c04421a8fc71aae5086f854ef7d05d3e9e` |
| Seeded OSINT snapshot | `world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.jsonl` | `fc63bb35f1fe50e8b227667141d0402e5f5f219661c350383f5a7b53caa19aff` |
| Seeded OSINT manifest | `world-side/outputs/runtime/demo-seeded-osint-snapshot-edge-appliance.manifest.json` | `e762cea08ad5d86d1de0cf10101d82e20b5ef907d29d3d2e9a7a095adda62486` |
| Forecast | `world-side/outputs/runtime/demo-scraper-forecast-edge-appliance.json` | `6fb56fdc9ffd3ac7ca1d0a593bc444e0b46c72d134e6785dd7a2ce4b981ed151` |
| Exposure-class portfolio | `cyber-side/outputs/runtime/latest-prediction-portfolio-edge-appliance.json` | `17ccfce769448b2a0d6fa52ecd0072bfccdac18c54cfbc252078b7fdd4a15298` |
| Sandbox artifact | `cyber-side/outputs/runtime/latest-sandbox-artifact-edge-appliance.json` | `11bbd7e9ce10cae33596cb8f482af2fa82866f6734e8130d29d08dc14d0666d9` |
| Sandbox run manifest | `cyber-side/outputs/runtime/latest-sandbox-run-manifest-edge-appliance.json` | `bc85d0e9eb2d4caf9bf85a550b396b765ec522b26af6e2e78ea144ad852522f8` |
| Operator audit log | `evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl` | `347fb8c83140feffed763691589f6a6eb2a04586e9041fb0912a0bbe0056a76a` |
| Operator approval record | `evidence/outputs/runtime/pilot-demo-approval-record.json` | `08f0018221b89de2be8b503ae4b7c7d2e06e1d055243eb987a4b6a35cb25fe3c` |
| Operator audit export | `evidence/outputs/runtime/pilot-demo-operator-audit-export.json` | `aed651d9fd244e6d55a9db7078079984e8d023ba8b699df22f784205e80caca7` |
| Operator audit retention report | `evidence/outputs/runtime/pilot-demo-operator-audit-retention.json` | `e26c02e1543c809f9dfb3c3ac40f36c817092a40af0b4d0538fedafe043e249f` |
| Evidence JSON | `evidence/outputs/runtime/latest-edge-appliance.json` | `9570017c12c2132f7b60fc2d8458bcfd9eef88683dc0b58a5905ba4c6bbe6e3c` |
| Evidence Markdown | `evidence/outputs/runtime/latest-edge-appliance.md` | `e537d54dc6a365e8dfb682efe86da2eb5e23fc2270a2b550c869d3d8e63fa7b1` |
| Integration manifest | `integrations/outputs/runtime/latest-edge-appliance/manifest.json` | `dfe1d31264779b5168b6f8bd3cb07eca641c901d795897dae882acf4a4da1d7f` |
| Splunk handoff | `integrations/outputs/runtime/latest-edge-appliance/siem/splunk_saved_search.json` | `b589650ea4204854045aa5b74ca41d409e8c9da3354e6540b1391fdab6986080` |
| Elastic handoff | `integrations/outputs/runtime/latest-edge-appliance/siem/elastic_detection_rule.ndjson` | `fa82bc122cf426b9126ccfd77efbd148b5736cc4626df33ddf0c8a46645ba362` |
| Sentinel handoff | `integrations/outputs/runtime/latest-edge-appliance/siem/sentinel_analytic_rule.json` | `227982baeb8a8f70dd15d25f04f4ae7b2fdd6135c1fb9bc53b19191a299a1c54` |
| Jira ticket handoff | `integrations/outputs/runtime/latest-edge-appliance/tickets/jira_remediation_ticket.json` | `e115e5d0127126de4f2951faa0e251de81d5c5247bdb2e9026be072848de7d0a` |
| ServiceNow task handoff | `integrations/outputs/runtime/latest-edge-appliance/tickets/servicenow_remediation_task.json` | `65293c8c79f18b6e087735f5cf2321852c858b564131af00f6b73e80678cce93` |
| Operator audit event | `integrations/outputs/runtime/latest-edge-appliance/audit/operator_approval_event.json` | `d2dcde2f37e5aa0572afc04588587600ddabfdfadef064c6bdf1ad15f06bf1d4` |
| Handoff review checklist | `integrations/outputs/runtime/latest-edge-appliance/review_checklist.md` | `0e7429be2462071053988df1ec4ee42a8ac23e2104cdcde15814c45ccbd9a910` |
| Handoff review ZIP | `integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip` | `e676da036f9f5e4d8c2bbbe6306486654a6463dcba37f5985e9a8b1392e29280` |

The evidence bundle includes the enforced pilot policy:

- Policy ID: `prophet-pilot-fixture-localhost-v0.1`
- Policy SHA-256: `7d051922a110f024188b522b89d11782151cce2d58fa606f7c319c48f405075c`
- Allowed source IDs: `cisa_vulnrichment_cve_record_seed`,
  `osv_query_api_seed`, `redhat_security_data_cve_api`
- Allowed sandbox profiles: `edge-appliance-fixture`,
  `financial-workflow-fixture`
- Allowed integration exports: Splunk, Elastic, Sentinel, Jira, ServiceNow, and
  operator audit review templates
