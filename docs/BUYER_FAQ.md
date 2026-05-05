# Buyer FAQ

## Does Prophet find zero-days?

No. Prophet predicts exposure classes that deserve defensive priority. The
public repo does not discover new bugs or provide exploit delivery.

## Does the console attack live targets?

No. The default console calls localhost control endpoints and fixture-backed
workflows. Live VM scraping is disabled unless explicitly gated, and arbitrary
target input is not packaged.

## What does a pilot validate?

A pilot validates whether Prophet can prioritize the right exposure class,
explain the timing, generate reviewable defensive artifacts, and export an
evidence bundle leadership can audit.

## What can an evaluator run immediately?

From a fresh clone, run:

```bash
./scripts/run-pilot-demo-smoke.sh
```

It imports a safe fictional CSV asset inventory, generates a safe asset
seedset, fixture-backed seeded OSINT snapshot, forecast, deterministic
localhost sandbox artifact, and JSON/Markdown evidence bundle. It also exports
safe SIEM and ticketing review templates. The evidence and handoff manifests
include policy ID/hash and SHA-256 hashes for the input and output artifacts.
The smoke path lints the pilot policy before generating runtime outputs,
records a fixture-scoped operator approval event, and verifies deterministic
artifact hashes against `scripts/pilot-demo-smoke.sha256`.

## What inputs does a customer provide?

- Approved asset or SBOM inventory at product-family level.
- Exposure classes or defensive priorities.
- Approved source feeds or sanitized context.
- A customer-approved sandbox or digital twin if validation moves beyond
  deterministic fixtures.
- Operator approval policy, allowed-mode policy, and evidence-retention
  requirements.

The packaged CSV importer accepts product-family metadata only and rejects
hostnames, IPs, URLs, credentials, unsupported columns, and raw target names.

## What leaves the customer environment?

For a normal pilot, no raw customer telemetry, credentials, private hostnames,
or live IPs should leave the customer environment. Evidence exports should stay
inside the agreed pilot data boundary.

## Is the evidence bundle signed?

The current bundle includes SHA-256 hashes over normalized inputs, the pilot
policy, the canonical bundle body, and the local approval record. Console runs
write hash-chained local audit events for approval, denial, and handoff export.
Key management and cryptographic signing are intentionally deferred.

## Can this integrate with SIEM, SBOM, or ticketing systems?

Yes. The first integration targets should be defensive systems: asset inventory,
SBOM, vulnerability management, SIEM, and ticketing. Offensive integrations are
out of scope for the default product.

Today, Prophet can write SIEM and ticketing review templates from a validated
evidence bundle. Those files are handoff artifacts for customer review, not
automatic production deployments.

## Where is lab exploit material?

Not in the public product tree. Lab-only exploit validation scaffolding belongs
in a private research repo or local archive under access control.

## Can the demo use live targets?

No. The packaged pilot policy allows fixture, seeded OSINT, and localhost
sandbox modes only. Live VM scraping, live targets, arbitrary target input,
payload generation, private hostnames, and credentials are blocked by default.

## Can a customer use a narrower pilot policy?

Yes. The repo includes policy examples for fixture-only, seeded-OSINT-only, and
localhost-sandbox evaluation. Run `python3 -m policy.lint --policy <path>` before
using a customer policy. The OSINT snapshot CLI, `sandbox_runner`, and
integration exporter now enforce source allowlists, sandbox-profile allowlists,
handoff-export allowlists, and retention hints when `--policy` is supplied.
Use `python3 -m policy.lint --policy <customer-policy> --compare-to
policy/prophet-pilot-policy.json` to show exactly what changed from the default
pilot policy before an evaluator approves it.
