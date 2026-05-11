# Incident Response Playbook

Date: 2026-05-11

This playbook covers Prophet's current buyer-pilot operating mode: local,
fixture-backed, policy-bound, and customer-safe evidence generation. It is not a
claim that Prophet is production SaaS ready. It defines how to handle incidents
without widening scope, hiding evidence, or leaking sensitive details.

## Scope

Covered incident classes:

- Data spill or unsafe customer artifact in the repo, runtime output, private
  validation workspace, message pack, evidence bundle, screenshot, or handoff.
- Credential, token, key, session file, or secret-like value exposure.
- Policy bypass, including live target validation, payload generation, raw
  scraper text import, or non-localhost control action.
- Integration misfire, including an attempted production push or incorrect
  customer handoff artifact.
- Sandbox escape or unapproved network, filesystem, process, CPU, memory, disk,
  or timeout behavior.
- Customer notification for a confirmed or credible pilot-impacting incident.

Out of scope for this public repo:

- Live incident handling for a customer production environment.
- Offensive validation, live exploitation, or payload execution.
- Public disclosure of secret values, raw customer data, hostnames, IPs,
  credentials, or incident narratives that identify a customer.

## Roles

| Role | Responsibility |
|---|---|
| Incident lead | Owns severity, timeline, containment, and closeout. |
| Security reviewer | Reviews evidence, unsafe data exposure, policy bypasses, and notification language. |
| Operator | Stops unsafe local runs, preserves safe metadata, and runs read-only checks. |
| Repo owner | Approves cleanup, history rewrite, release block, or public communication. |
| Customer sponsor | Receives pilot-impacting notifications and approves customer-side next steps. |

One person may hold multiple roles during a local pilot, but the closeout record
must name who made the decision.

## Severity

| Severity | Examples | Default action |
|---|---|---|
| SEV-1 | Real credential exposure, customer data spill, live target action, production integration change, sandbox escape with external effect. | Stop work, contain immediately, notify owner, prepare customer notification if customer data or systems may be affected. |
| SEV-2 | Policy bypass attempt blocked after partial artifact creation, unsafe private validation note, wrong handoff generated but not sent. | Stop the workflow, quarantine artifacts, run safety checks, document closeout. |
| SEV-3 | Documentation/process gap, stale private message pack, local runtime artifact confusion, no unsafe data or external effect. | Correct process, rerun checks, record no customer impact. |

If severity is unclear, treat it as SEV-2 until reviewed.

## First 15 Minutes

1. Stop the unsafe workflow. For local demo processes, use normal process
   termination such as `Ctrl-C`; do not run destructive git cleanup.
2. Preserve safe metadata: command name, timestamp, commit SHA, policy ID,
   artifact path, and hashes. Do not paste raw values into chat, issues, docs,
   or PR comments.
3. Identify whether customer data, credentials, live target data, or production
   systems could be involved.
4. Run the narrowest relevant read-only check:

   ```bash
   git status --short --branch --untracked-files=all
   make release-hygiene
   make validation-dashboard DATE=YYYY-MM-DD
   ```

5. If the incident concerns historical secrets, use
   `docs/SECRET_HISTORY_REVIEW.md` and do not print matched values.

## Scenario Playbooks

### Data Spill

Trigger examples:

- Raw customer notes, screenshots, logs, hostnames, IPs, URLs, account names,
  credentials, or incident narrative appear in a committed file, runtime output,
  private validation artifact, message pack, or evidence bundle.

Containment:

- Stop sharing the artifact.
- Move review to local/private channels.
- Record only safe metadata: path, hash, commit, timestamp, and reviewer.
- Run release safety against the path if it is still present locally:

  ```bash
  PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py <path>
  ```

Decision:

- If customer data was committed or sent externally, repo owner and customer
  sponsor decide notification and cleanup.
- If only ignored local private data was involved, delete or rotate the local
  artifact after recording safe hashes and outcome.
- Do not rewrite history, force-push, or delete branches without explicit repo
  owner approval.

### Credential Exposure

Trigger examples:

- `.env.local`, private key, token, session file, password-like value, API key,
  SSH key, certificate, or integration credential appears in repo history,
  current files, runtime outputs, or CI logs.

Containment:

- Treat as real until the owner proves otherwise.
- Revoke or rotate the credential before cleanup if it could be real or reused.
- For historical findings, follow `docs/SECRET_HISTORY_REVIEW.md`; do not paste
  matched values.
- Run:

  ```bash
  ./scripts/check-secrets-archaeology.sh --current-only
  make secrets-archaeology
  ```

Decision:

- Real or possibly reused: rotate/revoke, then approve clean-repo release or
  history cleanup separately.
- Demo/test false positive: record reviewer, date, and rationale without the
  matched value.
- Unknown ownership: block public release.

### Policy Bypass

Trigger examples:

- Live target validation, payload generation, raw scraper import,
  non-localhost control action, or production push becomes reachable by default.

Containment:

- Stop the run and keep the production build gate closed.
- Capture command, environment variables, policy ID/hash, endpoint path, and
  generated artifact paths without customer data.
- Run:

  ```bash
  make release-hygiene
  make console-live-check
  ```

Decision:

- If default fixture/localhost safety was bypassed, block release until a test
  proves the path fails closed.
- If a buyer asked for unsafe capability, disqualify or re-scope the pilot
  rather than promising the feature.

### Integration Misfire

Trigger examples:

- A handoff artifact is sent to the wrong reviewer.
- A connector attempts to push instead of producing a review template.
- Placeholder telemetry or owner fields are incorrect in an exported manifest.

Containment:

- Stop export and mark the artifact as not approved.
- Confirm no production system changed.
- Regenerate review-only handoffs from fixture or approved metadata.
- Validate the manifest and release safety checks before resharing.

Decision:

- If no production change occurred, record SEV-2 or SEV-3 closeout depending on
  customer exposure.
- If a production system changed, treat as SEV-1 and notify the customer sponsor
  with the known action, time, artifact, and rollback status.

### Sandbox Escape

Trigger examples:

- Sandbox profile contacts external network unexpectedly.
- Resource limits fail.
- A non-fixture sandbox mode runs without approval.
- Runtime writes outside approved ignored output directories.

Containment:

- Stop the sandbox process.
- Preserve safe metadata: profile ID, run ID, policy hash, manifest hash,
  command, and allowed sandbox profile.
- Do not rerun the profile until the escape cause is understood.

Decision:

- Non-fixture or externally effective behavior is SEV-1.
- Fixture-only local limit failure is SEV-2 until tests prove containment.
- Release stays blocked until no-egress/resource-limit checks or documented
  runtime controls cover the failure mode.

## Customer Notification

Notify a customer sponsor when any of these are true:

- Customer data may have been exposed outside the approved retention boundary.
- A credential or customer-owned secret may have been exposed.
- A production customer system may have been contacted or changed.
- A customer-visible artifact was sent with unsafe data or materially wrong
  evidence.

Use this structure and keep it value-free:

```text
Subject: Prophet pilot incident notice

We identified a Prophet pilot issue on <date/time>.

What happened:
- <safe summary without secrets, hostnames, IPs, raw notes, or payload details>

What may be affected:
- <artifact class, workflow, or approved metadata category>

What we have done:
- <containment action>
- <validation check>
- <current status>

What we need from you:
- <approval, review, or confirmation request>

We will provide a closeout summary after review.
```

Do not include raw customer data, secret values, private infrastructure names,
live IPs, exploit material, or unreviewed speculation.

## Closeout Record

Every SEV-1 or SEV-2 needs a private closeout record with:

- Date and time range.
- Severity and incident class.
- Incident lead and security reviewer.
- Safe artifact paths and hashes.
- Commit SHA and policy hash if applicable.
- Customer impact decision.
- Notification decision and date.
- Root cause.
- Corrective action.
- Tests or checks rerun.
- Remaining POA&M item, if any.

Public docs may record only aggregate process changes and sanitized references.

## Verification Commands

Run the relevant subset before closeout:

```bash
git diff --check
make release-hygiene
make validation-dashboard DATE=YYYY-MM-DD
python3 -m unittest discover -s scripts/tests -v
PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff
```

For a customer-facing pilot artifact, also rerun the pilot smoke or console
acceptance path that generated the artifact.
