# Operator Identity Guide

Use this guide for the local buyer pilot only. Prophet's current operator
identity is a sanitized local label used to bind approval, denial, sandbox, and
handoff events into a hash-chained audit trail.

This is not production identity, SSO, RBAC, customer authentication,
non-repudiation, or legal approval authority.

## Allowed Local Labels

Use role or workstation labels that are meaningful during a demo but do not
identify a person or environment.

Good examples:

- `fixture`
- `local-console`
- `pilot-reviewer-01`
- `product-security-reviewer`
- `soc-reviewer-local`

Allowed characters are letters, numbers, spaces, `_`, `.`, `/`, `+`, and `-`.
Keep labels under 121 characters.

Prefer role labels over people labels. If two reviewers use the same machine,
use generic labels such as `pilot-reviewer-01` and keep the reviewer mapping
outside Prophet unless the customer has approved a production identity design.

## Disallowed Labels

Do not use:

- Personal names.
- Emails.
- Phone numbers.
- Account IDs.
- Hostnames.
- IP addresses.
- Private organization names.
- Customer system names.
- Credentials, tokens, ticket URLs, or chat handles.

Bad examples should be described by category, not written into repo docs. Do
not include email-shaped labels, hostname-shaped labels, private-address
labels, personal-name labels, customer-name labels, or credential-like labels.

## How To Use

For smoke runs, keep the default fixture label. For manual pilot commands, pass
a safe local label:

```bash
PYTHONPATH=.:cyber-side:world-side python3 -m evidence.audit append \
  --log evidence/outputs/runtime/pilot-demo-operator-audit-log.jsonl \
  --policy policy/prophet-pilot-policy.json \
  --event-type operator_approval \
  --operator-label local-console \
  --decision bypassed_for_fixture \
  --generated-at 2026-05-05T08:00:00Z \
  --run-id pilot-demo-evidence
```

Console and smoke flows may also write local audit outputs through:

- `PROPHET_OPERATOR_AUDIT_LOG`
- `PROPHET_APPROVAL_RECORD_JSON`

Those variables are runtime output paths, not identity providers. The operator
label still needs to be a sanitized local label.

## How It Is Enforced

`evidence.audit` validates operator labels before writing an event. It rejects:

- Empty labels.
- Labels longer than 121 characters.
- Labels that start with unsupported punctuation.
- Email-like text.
- Hostname-like text.
- IP-like text.
- Secret-like text.

Audit exports summarize the local label and hash chain. They do not embed raw
event bodies, raw collection text, customer notes, credentials, private
hostnames, live IPs, or target-control instructions.

## What This Proves

The local label proves that Prophet can create a reviewable approval trail for
the fixture pilot. It does not prove production user identity. Production use
still needs authenticated identity, role checks, tenant scope, durable audit
storage, and customer-approved signing or identity provider integration.
See `docs/SIGNED_OPERATOR_APPROVAL_DESIGN.md` for the future signed approval
design.

Do not treat a local label as enough for production approvals, production
connector pushes, customer data access, or non-fixture validation modes.

## Review Rule

If an operator label would reveal a person, private system, customer, or
environment, replace it with a generic role label before generating evidence.

Stop the pilot review if the buyer requires real user identity, SSO, RBAC,
quorum approval, or signed operator approvals before they will trust the
evidence. Those are valid production requirements, but they are outside the
current local buyer-pilot scope until validation reaches `build_next_slice`.
