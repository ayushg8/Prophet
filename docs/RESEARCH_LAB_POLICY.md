# Research Lab Policy

Prophet's public repository is the product, contract, fixture, and audit surface.
Exploit-validation lab scaffolding belongs in a private, access-controlled
research environment.

## Public Repo Boundary

The public repo may contain:

- Safe JSON contracts and validators.
- Non-actionable fixtures.
- Console workflows that call only localhost control endpoints.
- Evidence bundles that summarize validation without raw payload strings,
  credentials, private hostnames, live IPs, or target-control steps.
- Documentation for safety boundaries and pilot scope.

The public repo must not contain:

- Lab exploit source or compiled artifacts.
- Payload-serving scripts or operator runbooks for exploitation.
- Real hostnames, IPs, credentials, keys, session files, or raw scrape output.
- Instructions that turn a fixture into a live target-control workflow.

## Private Research Boundary

Lab-only validation work must live in a separate private research repo or a
local archive outside this public tree. Access should be limited to approved
operators, and any lab output copied back into Prophet must pass the Direction C
validator and the evidence bundle validator before it is shown in the console or
shared with a pilot customer.

## Pilot Rule

Paid pilots use approved customer-owned context, safe fixtures, or isolated
customer-approved sandboxes. Live infrastructure testing is out of scope unless
there is a separate written authorization, an isolated runner, and a reviewed
validation plan.
