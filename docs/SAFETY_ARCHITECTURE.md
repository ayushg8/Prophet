# Safety Architecture

Prophet's commercial credibility depends on a strong safety boundary. The
system should create defensive priority, patch guidance, detection content, and
evidence. It should not create operational attack capability.

## Core Boundary

```text
raw sources -> sanitizer -> safe facts -> forecaster -> exposure-class portfolio
                                                         |
                                                         v
                                               defense artifact validator
                                                         |
                                                         v
                                                operator console + audit
```

Raw collection and live validation are isolated from the main application. The
main app receives only sanitized facts and schema-validated artifacts.

## Raw-To-Sanitized Boundary

```text
Raw collection zone                         Sanitization gate                         Product zone
-------------------                         -----------------                         ------------
official/source APIs                         parse allowlisted fields                  sanitized JSONL snapshot
seed fixtures             ───────────────▶   drop raw bodies, posts, logs   ───────▶   source_ref metadata
isolated scraper host                         hash source/input basis                  forecast source_refs
customer-owned metadata                       reject target URLs/hosts                 evidence summaries
                                             write redaction report                    handoff review templates

            Raw source text, credentials, handles, live hosts, telemetry, and
            screenshots must stop at the sanitization gate.
```

Allowed across the boundary:

- Source ID, source label, source class, public citation URL, observation date,
  parser status, and hash/provenance metadata.
- Short, non-sensitive summaries that omit raw post bodies, scanner rows,
  telemetry, logs, usernames, handles, hostnames, IP addresses, and screenshots.
- Fixture or customer-approved asset/SBOM metadata that already passed the
  asset import safety checks.

Rejected at or before the boundary:

- Raw source body or scraper output fields such as `raw_text`, `raw_html`,
  `raw_body`, `message_text`, `source_text`, and `raw_scraper_text`.
- Live target URLs, private hostnames, live IPs, callback/webhook/request URLs,
  arbitrary target input, credentials, cookies, SSH keys, session files, and
  payload/procedure text.
- Raw customer scanner exports, raw telemetry, raw logs, screenshots of
  customer systems, or unredacted support bundles.

Current enforcement:

- `world-side/scraper/config/source_catalog.json` and
  `policy/source-catalog-allowlist.json` constrain approved source IDs.
- `world-side/forecaster/models.py` validates sanitized forecast inputs and
  source references.
- `evidence/bundle.py` rejects raw source/scraper field names and pasted
  raw-source markers before evidence export.
- `scripts/check-default-output-safety.py` scans policy-listed default outputs
  for live-target URL fields while allowing public source citations.
- `scripts/check-release-safety.py` blocks raw collection paths, runtime
  artifacts in commits, private hostnames, live IPs, credentials, unsafe command
  text, and missing policy hashes in release-bound artifacts.

Reviewer rule: if a source fact cannot be represented with the allowed fields
above, it is not ready for the buyer pilot. Keep it outside product paths until
the sanitizer, policy, tests, and buyer data boundary are updated.

## Layers

### 1. Collection Isolation

Collection belongs on an isolated scraper host or approved customer collection
plane. The main app should never ingest raw posts, raw scrape output, handles,
invite links, credentials, or session files.

Current implementation:

- Sanitized JSONL fixture path.
- Source catalog safety tests.
- Live collection workflow disabled by default.

### 2. Contract Validation

JSON contracts reject unsafe content before the console renders it.

Current implementation:

- `world-side/forecaster/models.py`
- `cyber-side/validator.py`
- unit tests for banned keys, live target fields, procedural language, and
  payload-like content.

### 3. Human Authorization

The console pauses before validation execution. In production this approval
should include operator identity, reason code, target scope, and artifact hash.

Current implementation:

- Human gate in the replay flow.
- Runbook framing for sandbox-only operation.

### 4. Sandbox Validation

Validation must run only against approved sandboxes, digital twins, or
vulnerable-by-design lab environments. Production should use ephemeral runners
with no route to arbitrary external targets.

Current implementation:

- Fixture-backed validation status.
- Localhost-only validation scope enforced in artifacts.

### 5. Evidence Export

Every production run should leave an audit trail that lets a reviewer answer:

- What inputs were used?
- Which sources supported the forecast?
- Which exposure class was prioritized?
- Which defense was generated?
- Who approved validation?
- Where did validation run?
- What changed after the defense was applied?

## Default Deny Controls

The product should default-deny:

- Non-localhost validation.
- Raw source ingestion.
- Payload-like strings in artifacts.
- Credentials and host identifiers.
- Live collection workflow activation.
- Automatic deployment to production.

## Pilot Mode Threat Model

This pilot-mode threat model covers the current fixture-backed, localhost-only
buyer pilot. The broader controlled-production STRIDE model is in
`docs/THREAT_MODEL.md`.

Pilot assets:

- Fixture asset/SBOM inputs and generated seedsets.
- Sanitized seeded OSINT snapshots and provenance manifests.
- Forecast, sandbox, evidence, approval, audit, and integration handoff runtime
  artifacts under ignored `*/outputs/runtime/` paths.
- Private validation trackers, message packs, copy-only send files, weekly
  reviews, and interview templates under ignored `validation/private/`.
- Local pilot policy and source allowlist files.

Pilot actors:

- Local operator running the demo and validation sprint.
- Buyer/evaluator reviewing sanitized evidence and handoff templates.
- Future agent or restored terminal session resuming work from repo docs.
- Accidental committer, over-helpful automation, or local browser user.

Pilot trust boundaries:

- Public repo to ignored runtime outputs.
- Ignored `validation/private/` workspace to shareable aggregate updates.
- Copy-only outreach text to private tracker/audit metadata.
- Localhost console/control API to generated runtime artifacts.
- Fixture or customer-owned metadata to sanitized evidence and review
  templates.

Pilot abuse cases and controls:

| Abuse case | Control | Verification |
|---|---|---|
| Private target labels, tracker commands, or contact details leak into outbound outreach. | Use copy-only send files and neutral numbered batch files; keep manifests, checklists, copy indexes, subject-order helpers, and tracker commands private. | `validation-send-copy-batch` checks, dashboard ready/match checks, and release-safety scans. |
| A restored session sends stale outreach or writes stale tracker state. | Require `DATE=YYYY-MM-DD`, dashboard-first recovery, dry-run tracker commands, and exact `CONFIRM_SENT=1` after a real send. | `make goal-resume`, `make validation-status`, `make validation-dashboard`, and validation sprint tests. |
| Runtime evidence or screenshots contain live target data, raw source text, credentials, private hostnames, or live IPs. | Default outputs are policy-listed, sanitized, ignored runtime artifacts; release checks reject unsafe fields and staged runtime paths. | `check-default-output-safety.py`, `check-release-safety.py`, screenshot manifest checks, and pilot smoke hash verification. |
| Localhost console actions become live collection or production pushes. | Control server actions are policy-gated, fixture-backed, localhost-only, and integration outputs are review templates. | `make console-live-check`, console acceptance tests, policy lint, and release checklist gates. |
| A local operator mistakes example validation seed data for buyer pull. | Scorecard marks example logs, dashboard reports effective counts, and production build gate requires target-backed real interviews. | `validation-sprint-dashboard.py`, `customer-validation-scorecard.py`, and target-backed gate tests. |
| Private weekly-review handoffs overcount transient temp files or stale artifacts. | Weekly review is read-only, ignores atomic `.tmp.` files, reports stale ignored artifacts, and never deletes or mutates trackers. | `validation-weekly-review.py` tests and private artifact safety scans. |

Pilot acceptance rule: if a risk requires durable identity, tenant isolation,
secrets, production pushes, live collection, or customer data retention
automation to control it, do not solve it inside the current pilot. Keep the
production build gate closed until real validation reaches `build_next_slice`.

## Productization Recommendation

Lab-only exploit validation scaffolding belongs in a private research repo or
local archive outside this public tree. The commercial distribution should
contain contracts, safe fixtures, tests, evidence export, and deterministic
sandbox orchestration wrappers, not exploit lab scripts. See
`docs/RESEARCH_LAB_POLICY.md`.
