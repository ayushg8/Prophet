# Safety Architecture

Prophet's commercial credibility depends on a strong safety boundary. The
system should create defensive priority, patch guidance, detection content, and
evidence. It should not create operational attack capability.

## Core Boundary

```text
raw sources -> sanitizer -> safe facts -> forecaster -> exploit-class portfolio
                                                         |
                                                         v
                                               defense artifact validator
                                                         |
                                                         v
                                                operator console + audit
```

Raw collection and live validation are isolated from the main application. The
main app receives only sanitized facts and schema-validated artifacts.

## Layers

### 1. Collection Isolation

Collection belongs on an isolated scraper host or approved customer collection
plane. The main app should never ingest raw posts, raw scrape output, handles,
invite links, credentials, or session files.

Current implementation:

- Sanitized JSONL fixture path.
- Source catalog safety tests.
- VM scraper workflow disabled by default.

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
- VM scraper activation.
- Automatic deployment to production.

## Productization Recommendation

Lab-only exploit validation scaffolding belongs in a private research repo or
local archive outside this public tree. The commercial distribution should
contain contracts, safe fixtures, tests, evidence export, and deterministic
sandbox orchestration wrappers, not exploit lab scripts. See
`docs/RESEARCH_LAB_POLICY.md`.
