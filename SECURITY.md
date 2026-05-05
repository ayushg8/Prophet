# Security Policy

Prophet is a defensive forecasting and validation system. Treat the public repo
as a safe demo and contract reference, not as permission to run offensive
activity.

## Supported Use

Allowed by default:

- Run deterministic forecaster tests and fixture generation locally.
- Load sanitized fixture data into the console.
- Validate JSON artifacts with the included validators.
- Generate defensive patch, detection, and audit artifacts from approved inputs.
- Test patches in isolated, vulnerable-by-design sandboxes owned by the
  operator.

Not allowed by default:

- Running validation against live third-party systems.
- Running the scraper VM workflow without an approved isolated collection plan.
- Storing raw scraper output in this repo.
- Adding payload bytes, credentials, hostnames, IPs, session files, or private
  keys to artifacts.
- Turning the console into a live exploit runner.

## Allowed Research Boundary

Prophet research in this public repo must stay at the defensive planning,
contract validation, and evidence-review layer. Acceptable research outputs are
safe schemas, synthetic or sanitized fixtures, defensive detection logic,
patch-review summaries, localhost sandbox validation summaries, and audit
evidence that a buyer can inspect.

Do not add live target collection, target-control instructions, exploit
transport steps, payload material, raw source captures, credentials, private
infrastructure names, or customer-identifying host data. If a future pilot needs
broader validation, document the customer authorization, approved sandbox scope,
operator identity, retention requirement, and rollback plan before any artifact
is imported into Prophet.

## Safe Fixture Creation Checklist

Before adding or updating a fixture, confirm:

- The fixture is fictional, synthetic, public metadata, or explicitly
  customer-approved for this repo.
- The fixture describes product families, sectors, exposure classes, or package
  families instead of named live systems.
- The fixture contains no credentials, keys, session material, raw scraper
  bodies, payload bytes, operational steps, private hostnames, live IPs, or
  named customer infrastructure.
- The fixture passes the relevant validator or linter before it is used by the
  console, evidence exporter, sandbox runner, or integration handoff.
- Any generated output path stays under an ignored `*/outputs/runtime/`
  directory.
- The source, policy ID, policy hash, and generation time are captured when the
  artifact is part of the buyer evidence path.

## Customer Data Handling Checklist

Before importing any customer-owned artifact:

- Confirm the artifact is in scope for the pilot policy and written approval.
- Prefer product-family, package-family, owner-group, exposure-class, and
  business-criticality metadata over system-specific identifiers.
- Run the customer import through the safe importer or schema validator first;
  do not hand-edit unsafe rows into accepted artifacts.
- Reject or redact hostnames, URLs, live IPs, account names, credentials,
  secrets, raw logs, raw tickets, raw scanner output, and incident narratives
  that identify a live environment.
- Store derived runtime outputs only under ignored `*/outputs/runtime/`
  directories and include hashes rather than raw unsafe source values.
- Record retention expectations, operator label, approval decision, policy ID,
  and policy hash in the evidence or audit trail.

## Runtime Gates

The local control server disables live VM scraping unless explicitly opted in:

```bash
PROPHET_ENABLE_VM_SCRAPER=1 npm run dev:control
```

Only use this flag after confirming the scraper host, source catalog, legal
authority, retention policy, and sanitization workflow. The default product path
should use `DEMO REFRESH` and validated fixture artifacts.

## Artifact Rules

Accepted artifacts must be:

- Schema-valid.
- Sector-level, not named-target-level.
- Free of credentials, raw collection, payloads, and target-control steps.
- Bound to localhost or an approved sandbox validation scope.
- Reviewable by a human operator before export.

Validators enforce part of this boundary, but operator review remains required
before using any generated defense artifact in a real environment.

Lab-only exploit validation scaffolding must stay outside the public repo in a
private research repo or local archive. See `docs/RESEARCH_LAB_POLICY.md`.

## Reporting Issues

Open a private issue or contact the project owner if you find:

- A committed secret or credential.
- Raw scrape data.
- Payload material in a supposedly safe fixture.
- A way for the console to contact non-localhost infrastructure by default.
- A validator bypass.

Do not post sensitive details publicly until the project owner has had a chance
to remove or rotate affected material.
