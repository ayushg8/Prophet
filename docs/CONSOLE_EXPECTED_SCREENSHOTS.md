# Console Expected Screenshot Artifacts

Date: 2026-05-10
Status: expected artifact guide plus ignored runtime capture path

Use this guide when preparing a redacted console handoff for a qualified buyer
review. The default package should rely on hashes and generated artifacts first;
screenshots are secondary visual evidence for orientation.

Do not capture customer systems, customer names, private hostnames, live IPs,
raw scraper text, payload material, credentials, browser bookmarks, terminal
tabs, or unreviewed runtime output. Use only the fixture-backed local console at
`http://127.0.0.1:5173` after `./scripts/run-pilot-demo-smoke.sh` passes.

## Capture Rules

- Capture from a clean local run after the smoke hash check passes.
- Use fixture-backed seeded source data only.
- Keep the browser viewport at desktop width unless a buyer specifically asks
  for responsive review.
- Redact the operating system chrome if it shows names, paths outside this repo,
  messaging apps, emails, or other workspace context.
- Store any captured images outside git unless the user explicitly asks to add
  redacted artifacts.
- Treat a screenshot as failed if it shows live target fields, VM collection,
  payload strings, raw requests, private hostnames, live IPs, or auto-deploy
  integration language.

## Responsive Runtime Capture

After the pilot smoke passes, generate local desktop and mobile screenshots:

```bash
cd prophet-console
npm run capture:screenshots
```

The command reruns the fixture-backed pilot smoke, starts the localhost-only
control API and evaluator UI, captures desktop and mobile screenshots, and
writes them under:

```text
evidence/outputs/runtime/console-screenshots/
```

That directory is ignored runtime output. Do not commit or attach the generated
PNG files unless a reviewer explicitly asks for redacted visual artifacts and
the files pass the capture rules above. Use
`evidence/outputs/runtime/console-screenshots/manifest.json` to review the
generated file list, viewport sizes, hashes, and sharing boundary.

Before sharing any generated screenshots, verify the manifest:

```bash
make console-screenshot-check
```

The verifier checks that generated screenshot paths stay under ignored runtime
output, PNG hashes and dimensions match the manifest, and the manifest keeps
the fixture-backed/no-customer-system sharing boundary.

## Expected Artifacts

| ID | Console state | Required visible signals | Forbidden signals |
|---|---|---|---|
| `console-01-entry` | First console view after entering from the landing page. | Alpha readiness panel, policy status panel, fixture mode, safety boundary, live collection workflow policy-blocked. | Live target input, VM run controls, payload generation, production push language. |
| `console-02-forecast` | After `Refresh demo` completes. | Forecast brief, strike window, strike vector, source rail, `Demo forecast refreshed`, sector-level language. | Raw OSINT text, target hostnames, live scraper success claims. |
| `console-03-approval-gate` | Human gate during the replay loop. | Human-in-the-loop gate, localhost fixture scope, no live infrastructure warning, fixture validation plan. | Nuclei execution framing, lab host addresses, arbitrary target fields. |
| `console-04-defense-validation` | After loading the defense fixture or completing the replay. | Defense validation status, `BLOCKED`, localhost sandbox fixture, patch and Sigma review tabs. | Exploit status header, exploit payload output, real service identifiers. |
| `console-05-evidence` | After generating the evidence bundle. | Bundle ID, bundle SHA-256, policy hash, approval hash, sandbox artifact source, source freshness, redaction report. | Raw scraper text, raw validation logs, customer screenshots. |
| `console-06-handoff` | After exporting integration handoff templates. | Integration manifest, `review_template_only`, SIEM/ticketing files, evidence refs, approval refs. | Auto-deploy, production push, credentials, customer endpoint URLs. |
| `console-07-policy-blocked` | Optional failure-mode demo from `./scripts/run-policy-blocked-demo.sh`. | `policy_blocked`, `HTTP 403`, no workflow started, report path under ignored runtime outputs. | Live target access, live collection success, generated payloads. |

## Reviewer Notes

- The evidence bundle and integration manifest remain the source of truth.
- Screenshots are useful only if they make the four jobs obvious:
  prioritize, explain, validate safely, and hand off.
- If the console differs from this guide, decide whether the screenshot guide is
  stale or the console has drifted away from the buyer-safe product narrative.
