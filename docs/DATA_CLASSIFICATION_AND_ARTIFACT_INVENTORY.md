# Data Classification And Artifact Inventory

Date: 2026-05-10

This inventory defines what Prophet may store or export in the buyer pilot and
what must stay out of product paths. It is a planning and review artifact, not a
claim that production data controls are complete.

## Classification Levels

| Level | Meaning | Default Handling |
|---|---|---|
| Public repo safe | Safe to commit when generated from fixtures, examples, or public documentation. | May live in tracked docs, fixtures, schemas, tests, and hash manifests. |
| Runtime local | Safe only as generated local output. | Must stay under ignored `*/outputs/runtime/` paths and must not be committed. |
| Private validation | Sanitized but customer-discovery related. | Must stay under ignored `validation/private/` paths. Export only anonymized summaries. |
| Customer-controlled metadata | Approved customer-owned asset, SBOM, workflow, or policy metadata. | Production storage requires tenant scope, retention, deletion, and approval controls. The public pilot uses fictional fixtures only. |
| Prohibited | Unsafe for Prophet product paths. | Reject, redact, or keep outside the repo. Never include in evidence or prompts. |

Global prohibited content:

- Credentials, secrets, tokens, SSH keys, session files, cookies, or API keys.
- Live IPs, private hostnames, customer hostnames, target URLs, or arbitrary
  target input.
- Payloads, target-control instructions, exploit procedures, or offensive
  automation.
- Raw scraper/source text, raw customer telemetry, raw logs, screenshots of
  customer systems, or unredacted support bundles.
- Real names, emails, phone numbers, handles, or private organization details in
  validation logs, outreach targets, or buyer notes.

Public documentation URLs for official/vendor/source references are allowed when
they are evidence citations, not targets.

## Artifact Inventory

| Artifact Type | Examples | Classification | Allowed Fields | Storage Rule | Retention Rule | Export Rule |
|---|---|---|---|---|---|---|
| Product and pilot docs | `README.md`, `docs/PILOT_DEMO.md`, `docs/BUYER_FAQ.md` | Public repo safe | Product claims, safe commands, public links, safety boundaries, fixture paths. | Tracked docs. | Keep with release history. | May share publicly after safety review. |
| Pilot policy and schema | `policy/prophet-pilot-policy.json`, `policy/*.schema.json` | Public repo safe | Allowed modes, blocked controls, source/profile/export allowlists, retention hints, policy hash. | Tracked policy files. | Keep with release history. | May share with evaluators. |
| Example fixtures | `world-side/fixtures/`, `cyber-side/fixtures/`, `assets/fixtures/` | Public repo safe | Fictional sector, class-level exposure, CVE IDs, public source refs, non-actionable rationale. | Tracked fixtures after validator and release-safety checks. | Keep with release history. | May share with evaluators. |
| Customer-safe asset import source | `assets/fixtures/demo-dib-edge-appliance-inventory.csv` | Public repo safe for fictional fixtures; customer-controlled metadata in real pilots | Product family, owner queue, exposure class, synthetic or approved asset labels. | Fictional fixtures may be tracked. Real customer files must not enter public repo. | Pilot customer files follow customer policy and deletion agreement. | Export only sanitized import reports and seed summaries. |
| Asset import reports | `assets/outputs/runtime/*report.json`, `*manifest.json` | Runtime local | Accepted/rejected counts, hash-only source manifest, redacted rejection reason, safety attestation. | Ignored runtime path. | Default 30 days for runtime outputs unless policy says shorter. | May share hash-only report if no unsafe row values are present. |
| Asset/SBOM seedsets | `assets/outputs/runtime/*seedset*.json` | Runtime local; customer-controlled metadata in real pilots | Exposure class, product family, fictional or approved owner queue, counts, source hash refs. | Ignored runtime path. Production requires tenant-scoped artifact store. | Default 30 days for runtime pilot outputs; production per tenant policy. | May be embedded in evidence as summary only. |
| Source catalog | `world-side/scraper/source_catalog.json` | Public repo safe | Source IDs, official API/documentation URLs, allowed status, parser metadata. | Tracked after allowlist coverage checks. | Keep with release history. | May share with evaluators. |
| Seeded public-source snapshot | `world-side/outputs/runtime/*snapshot*.jsonl` | Runtime local | Sanitized source facts, source IDs, timestamps, public CVE/source refs, parser status. | Ignored runtime path. | Default 30 days; raw collection is not retained. | Export only summarized source basis and hashes in evidence. |
| Forecast output | `world-side/outputs/runtime/*forecast*.json` | Runtime local; public repo safe for golden fixtures | Strike window, strike vector, confidence, assumptions, source refs, asset seed summary. | Runtime outputs ignored; selected golden fixtures may be tracked after review. | Runtime default 30 days; golden fixtures kept with release history. | May share if no live targets or private customer data are present. |
| Exposure-class portfolio | `cyber-side/outputs/runtime/*portfolio*.json`, checked-in safe portfolio fixtures | Runtime local or public repo safe fixture | Defensive hypothesis class, known-pressure replay class, non-actionable rationale, CVE refs. | Runtime outputs ignored; safe fixtures tracked after validator checks. | Runtime default 30 days; fixtures kept with release history. | May share class-level summary; never export procedures or payloads. |
| Localhost sandbox artifact | `cyber-side/outputs/runtime/*sandbox-artifact*.json` | Runtime local | Fixture profile ID, pre/post status, patch summary, Sigma summary, validator result, policy hash. | Ignored runtime path. Production requires sandbox provenance and tenant scope. | Runtime default 30 days. | May feed evidence bundle; do not export as proof of live exploitability. |
| Sandbox run manifest | `cyber-side/outputs/runtime/*run-manifest*.json` | Runtime local | Profile ID, artifact hash, validator result, local mode, policy hash, timing metadata. | Ignored runtime path. | Runtime default 30 days. | May share hash/provenance summary with evidence. |
| Evidence bundle JSON/Markdown | `evidence/outputs/runtime/latest-*.json`, `*.md` | Runtime local | Forecast ID, artifact hashes, policy hash, approval hash, source freshness, validation summary, safety attestation, redaction report. | Ignored runtime path. Production requires immutable tenant-scoped storage. | Runtime default 30 days; production per tenant retention. | Primary buyer/audit export when safety checks pass. |
| Approval record | `evidence/outputs/runtime/*approval-record.json` | Runtime local | Sanitized local operator label, decision, scope, policy hash, approval record hash, timestamp. | Ignored runtime path. Production requires authenticated identity and durable audit store. See `docs/OPERATOR_IDENTITY_GUIDE.md`. | Runtime default 90 days for audit outputs unless policy says shorter. | May export as part of audit packet. |
| Audit log and audit export | `evidence/outputs/runtime/*audit*.json*` | Runtime local | Hash-chained events, sanitized local operator label, decision, action, artifact refs, previous event hash, policy hash. | Ignored runtime path. Production requires immutable audit store and authenticated identity. See `docs/OPERATOR_IDENTITY_GUIDE.md`. | Runtime default 90 days; production per audit retention policy. | May export sanitized audit summaries and hash chains. |
| Retention report | `evidence/outputs/runtime/*retention.json` | Runtime local | Artifact refs, age, policy max days, deletion eligibility, safety attestation. | Ignored runtime path. | Keep until runtime cleanup or policy deletion. | May share with security reviewers. |
| SIEM/ticket handoff templates | `integrations/outputs/runtime/latest-*/` and `integrations/outputs/runtime/*-review-bundle.zip` | Runtime local | Review-template-only Splunk, Elastic, Sentinel, Jira, ServiceNow, manifest, hashes, customer-placeholder validation, handoff review checklist, and deterministic review ZIP. | Ignored runtime path. Production requires tenant scope and integration policy. | Runtime default 30 days; production per tenant/export policy. | May share as draft review templates; not approved production pushes. |
| Validation targets | `docs/validation-targets.example.json`, `validation/private/validation-targets.json` | Example is public repo safe; private tracker is private validation | Anonymous segment, persona, priority, status, next action, dates. | Example tracked; private tracker ignored. | Private validation data reviewed weekly and deleted when no longer needed. | Export aggregate counts only. |
| Customer validation interview log | `docs/customer-validation-log.example.json`, `validation/private/customer-validation-log.json` | Example is public repo safe; private log is private validation | Anonymous account label, segment, persona, scores, objections, next step. | Example tracked; private log ignored. | Private validation data reviewed weekly and deleted when no longer needed. | Export anonymized scorecard summaries only. |
| Outreach/message packs and status | `validation/private/today-outreach-block.*`, `today-message-pack.*`, `today-next-draft.md`, `today-send-copy.txt`, `today-outreach-status.*` | Private validation | Target labels, segment, persona, safe draft text, tracker commands, send/update state, mismatch fields. `today-send-copy.txt` intentionally emits one subject line plus the message body and omits target labels, tracker commands, alternate subject options, and status metadata. | Ignored `validation/private/`. | Delete or rotate after the daily outreach block is complete. | Do not export except aggregate activity counts; use `today-send-copy.txt` only as outbound copy text after the verified dry-run passes and the dashboard reports matching ready states for the next draft and send-copy file. |
| Aggregate validation team update | `validation/private/today-team-update.md` | Private validation, aggregate-only | Validation verdict, build gate state, aggregate call/outreach counts, send-copy readiness, and shareable next actions without target labels, commands, message bodies, contact details, URLs, hostnames, IPs, or private buyer notes. | Ignored `validation/private/`. | Delete or rotate after the daily or weekly team update is complete. | May share if generated by the aggregate-only renderer and safety-reviewed. |
| Console screenshots | `docs/CONSOLE_EXPECTED_SCREENSHOTS.md`, `evidence/outputs/runtime/console-screenshots/` | Runtime local; public repo safe only after redaction review | Fixture mode, hashes, policy status, evidence summaries, no private desktop/browser data. | Expected screenshot checklist may be tracked; generated PNGs stay ignored unless explicitly approved. | Runtime default 30 days; keep only approved/redacted screenshots. | May share only after redaction checklist passes. |
| Release hash manifests | `scripts/pilot-demo-smoke*.sha256`, `docs/PILOT_RELEASE_NOTES.md` | Public repo safe | File paths, SHA-256 hashes, policy hash, smoke result metadata. | Tracked release evidence. | Keep with release history. | May share with evaluators. |
| Production backlog and security planning docs | `docs/production-readiness-backlog.json`, architecture, threat model, compliance docs | Public repo safe | Roadmap, gaps, non-goals, acceptance gates, evidence paths. | Tracked docs. | Keep with release history. | May share as honest readiness evidence. |
| Private lab/archive material | Private research repo, local archives | Prohibited in product paths | None in public product paths. | Keep outside public repo and outside buyer demo paths. | Govern separately under private lab policy. | Do not export through Prophet pilot package. |

## Default Retention Rules

- Runtime local outputs: 30 days unless the active pilot policy is stricter.
- Runtime audit outputs: 90 days unless the active pilot policy is stricter.
- Private validation outreach and interview records: review weekly and delete
  when no longer needed for demand validation.
- Public repo safe fixtures/docs: retained with release history.
- Customer-controlled metadata in a real pilot: requires a written
  customer-specific retention and deletion agreement before use.

## Export Review Rules

Before sharing any artifact outside the local evaluator machine:

1. Confirm it is not classified as prohibited.
2. Confirm it is not private validation data unless only aggregate/anonymized
   summaries are being shared.
3. Run the relevant validator or release-safety scan.
4. Confirm runtime artifacts are generated under ignored `*/outputs/runtime/`
   paths.
5. Share hashes, manifests, and evidence summaries before sharing full JSON.
6. Do not share screenshots unless they pass
   `docs/CONSOLE_EXPECTED_SCREENSHOTS.md`.

## Remaining Production Work

This inventory closes the design-level classification gap for the buyer pilot
and production planning. It does not replace:

- Tenant-scoped durable storage.
- Authenticated production identity.
- Customer-specific retention/deletion workflows.
- Secrets management.
- Signed policy implementation.
- Signed evidence manifest implementation.
- Signed operator approval implementation.
- External security review.
