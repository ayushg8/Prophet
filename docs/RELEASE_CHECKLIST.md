# Prophet Release Checklist

Use this checklist before every internal alpha or customer-pilot build.

For local commits, enable the repository hook once:

```bash
git config core.hooksPath .githooks
```

## Safety Boundary

- [ ] Live targets remain blocked by policy.
- [ ] Payload generation remains blocked by policy.
- [ ] Raw scraper text, credentials, private hostnames, and arbitrary target input remain blocked.
- [ ] Unauthorized control interfaces and command-upload paths are not enabled.
- [ ] All generated customer-facing artifacts are review templates or evidence outputs, not production pushes.

## Policy And Audit

- [ ] `python3 -m policy.lint --policy policy/prophet-pilot-policy.json` passes.
- [ ] Source IDs used by seeded OSINT are listed in `allowed_source_ids`.
- [ ] Enabled source catalog entries match `policy/source-catalog-allowlist.json`; this is release-review coverage and does not enable live collection.
- [ ] Console actions that can invoke live collection are routed through an explicit control-server policy gate.
- [ ] Sandbox profiles used by validation are listed in `allowed_sandbox_profiles`.
- [ ] Integration export kinds are listed in `allowed_integration_exports`.
- [ ] Evidence includes `policy_sha256` and, for console runs, `approval_record_sha256`.
- [ ] Evidence JSON, OSINT manifests, sandbox artifacts, and integration manifests include `policy_sha256`.
- [ ] `python3 -m evidence.audit validate --log <runtime-audit-log>` passes for any exported runtime audit log.
- [ ] `python3 -m evidence.audit export --log <runtime-audit-log> --out-json <runtime-audit-export>` passes when a security reviewer needs the local approval trail.

## Verification

- [ ] Python unit suites pass for policy, assets, cyber-side, world-side, sandbox runner, evidence, and integrations.
- [ ] `cd prophet-console && npm run acceptance` passes.
- [ ] `cd prophet-console && npm audit --audit-level=moderate` passes or has a documented exception.
- [ ] `git diff --check` passes.
- [ ] `python3 scripts/check-release-safety.py --tracked --paths-only` passes, including policy-hash coverage checks for release-bound JSON artifacts.
- [ ] `python3 scripts/check-release-safety.py --staged` passes before commit.
- [ ] `python3 -m unittest discover -s scripts/tests -v` passes.
- [ ] Manual `GET /api/readiness` returns zero blocking failures.

## Artifact Review

- [ ] Runtime outputs are under ignored `outputs/runtime` directories.
- [ ] No `outputs/runtime` artifact is tracked or staged.
- [ ] Evidence JSON and Markdown hashes are recorded in the release note.
- [ ] Integration manifest and handoff file hashes are recorded in the release note.
- [ ] No unsafe raw customer input is committed.
- [ ] Demo screenshots, if included, are redacted and contain no live target details.

## Release Note

- [ ] Summarize the scenario, policy ID/hash, evidence hash, integration manifest hash, and known open blockers.
- [ ] Name whether the build is internal alpha, friendly pilot, or paid pilot candidate.
- [ ] List manual steps needed to reproduce the demo from a clean checkout.
