# Prophet Demo Candidate Archive

This archive no longer lists live exploit reproduction candidates. Prophet's
current public demo is the fixture-backed, policy-bound buyer pilot documented
in `docs/PILOT_DEMO.md`.

## Current Demo Contract

- Use sanitized forecast fixtures and seeded OSINT fixtures.
- Use fictional customer-owned asset/SBOM metadata.
- Use deterministic `sandbox_runner` output for approved localhost fixture
  profiles.
- Emit evidence, audit, and SIEM/ticketing review templates.
- Do not run live targets, vulnerable third-party lab images, exploit payloads,
  callback infrastructure, or target-control validation steps.

## Scenario Families

Safe fixture families that remain useful for product evaluation:

- Edge-appliance access and persistence.
- Financial workflow theft risk.
- Disruptive service shutdown risk.

These scenarios should be represented as non-actionable candidate metadata,
asset seedsets, forecasts, evidence bundles, and policy-controlled validation
artifacts. Any future live or containerized validation plan belongs in a
customer-approved sandbox design and must go through policy, CSO, and release
review before it is added to the default product flow.
