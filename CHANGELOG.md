# Changelog

## Unreleased - Buyer Pilot Package

Status: validation sprint active; production build gate closed.

This package reframes Prophet as a policy-bound defensive exposure evidence
workflow for buyer validation. It supports a local, fixture-backed pilot that
helps reviewers inspect:

- Which exposure class should be reviewed first.
- Why that recommendation is supported by approved fixture, source, asset/SBOM,
  policy, sandbox, audit, and handoff evidence.
- Which SOC and ticketing review templates a human operator can inspect.
- Which safety controls keep live targets, payloads, raw customer telemetry,
  credentials, and production pushes out of the pilot path.

Added or updated:

- Buyer validation sprint docs, private-safe outreach tooling, target tracker,
  message pack generator, status checker, one-draft rendering, dashboard
  stale-date guard, and guarded tracker updater.
- Customer validation scorecards that keep `pilot_pull_detected` separate from
  the production `build_next_slice` gate.
- Buyer follow-up package, pilot acceptance criteria, and completion audit.
- Pilot release notes with current smoke manifests, policy hash, evidence
  hashes, handoff manifest hashes, runnable `make console-demo` local product
  path, and full `make pilot-ready-check-full DATE=2026-05-11` verification
  gate.
- PR template guardrails that require the validation dashboard verdict,
  closed/open build-gate result, private-artifact boundary, and current local
  verification wrappers before review.
- Console acceptance path, readiness checks, policy-blocked control states, and
  a manual readiness verification command.
- Data classification inventory and signed evidence manifest design for future
  buyer/security review.

Known blockers:

- Real buyer demand remains unproven: current validation verdict is
  `insufficient_data`.
- Production platform work remains closed until real private validation reaches
  `build_next_slice`.
- Release tag, historical secret-history decision, and real buyer validation
  remain open. Linux fresh-clone smoke is covered by the Ubuntu CI pilot smoke.

Verification references:

- `docs/PILOT_RELEASE_NOTES.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/PROPHET_COMPLETION_AUDIT.md`
- `docs/PROPHET_FINISH_CHANGE_INVENTORY.md`
