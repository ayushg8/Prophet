# Prophet Release Checklist

Use this checklist before every internal alpha or customer-pilot build.

For local commits, enable the repository hook once:

```bash
git config core.hooksPath .githooks
```

## Validation Gate

- [ ] Run `make validation-dashboard DATE=YYYY-MM-DD` against the current
  private validation workspace.
- [ ] If the dashboard verdict is `insufficient_data`, keep the production
  build gate closed and do not add production platform scope.
- [ ] If the dashboard verdict is `pilot_pull_detected`, convert the design
  partner path first; do not treat it as permission to build the next
  production slice.
- [ ] Only `build_next_slice` opens production platform work, and only from
  real anonymized buyer validation.
- [ ] Use `make goal-resume DATE=YYYY-MM-DD` after a restored `/goal` session
  before relying on an existing private draft or send-copy file.

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

- [ ] `make python-tests` passes for scripts, policy, assets, cyber-side,
  world-side, sandbox runner, evidence, and integrations.
- [ ] `cd prophet-console && npm run acceptance` passes.
- [ ] `cd prophet-console && npm audit --audit-level=moderate` passes or has a documented exception.
- [ ] `make console-demo` starts the localhost-only control API and evaluator
  UI in one terminal and stops both with `Ctrl-C` or process termination.
- [ ] With the local demo running, `make console-live-check` passes. This checks
  readiness plus the evidence and integration demo endpoints and validates the
  local runtime audit log.
- [ ] `git diff --check` passes.
- [ ] `make release-hygiene` passes for the current worktree.
- [ ] `make secrets-archaeology` has been run before public release, and any
  historical findings have an explicit cleanup, rotation, or false-positive
  decision. Use `docs/SECRET_HISTORY_REVIEW.md` for the current finding and
  safe review path.
- [ ] `python3 scripts/check-doc-links.py` passes, either directly or through
  `make release-hygiene`.
- [ ] `python3 scripts/check-release-safety.py --tracked --paths-only` passes, including policy-hash coverage checks for release-bound JSON artifacts.
- [ ] `python3 scripts/check-release-safety.py --staged` passes before commit.
- [ ] `python3 -m unittest discover -s scripts/tests -v` passes.
- [ ] Manual `GET /api/readiness` returns zero blocking failures.

  ```bash
  make console-demo
  make console-live-check
  ```

## Artifact Review

- [ ] Runtime outputs are under ignored `outputs/runtime` directories.
- [ ] No `outputs/runtime` artifact is tracked or staged.
- [ ] Evidence JSON and Markdown hashes are recorded in the release note.
- [ ] Integration manifest and handoff file hashes are recorded in the release note.
- [ ] No unsafe raw customer input is committed.
- [ ] Demo screenshots, if included, are redacted and contain no live target details.
- [ ] If responsive screenshots are needed, run
  `cd prophet-console && npm run capture:screenshots`, then
  `make console-screenshot-check`, and review
  `evidence/outputs/runtime/console-screenshots/manifest.json` before sharing.

## Release Note

- [ ] Summarize the scenario, policy ID/hash, evidence hash, integration manifest hash, and known open blockers.
- [ ] Name whether the build is internal alpha, friendly pilot, or paid pilot candidate.
- [ ] List manual steps needed to reproduce the demo from a clean checkout.

## Release Tag Gate

- [ ] Do not create or push a public pilot release tag while
  `make secrets-archaeology` has unresolved git-history findings.
- [ ] Resolve the historical `LOG4SHELL_INSTRUCTIONS.md` finding through
  `docs/SECRET_HISTORY_REVIEW.md` before tagging the public fixture/hash set.
- [ ] Record the owner/reviewer decision without pasting the matched line or
  value into GitHub, docs, release notes, or agent prompts.
- [ ] The decision must choose one release path: rotate/revoke plus history
  rewrite or clean-repo release; explicit false-positive exception with
  rationale; or block public release when ownership is unknown.
- [ ] Recheck PR status, release hygiene, validation dashboard, and the
  smoke-hash evidence immediately before creating a tag.
- [ ] The tag message must name the release notes path, policy hash, smoke hash
  manifest, validation verdict, build-gate state, and any remaining non-release
  product blockers.

## Local Demo Rollback

- [ ] If a local demo run corrupts or confuses runtime state, restore the known
  fixture-backed pilot outputs with:

  ```bash
  ./scripts/run-pilot-demo-smoke.sh --clean-runtime --yes
  shasum -a 256 -c scripts/pilot-demo-smoke.sha256 --quiet
  ```

- [ ] If the console readiness endpoint was running with ad hoc environment
  variables, stop the control server and restart it without those variables
  before evaluating the default pilot path.
- [ ] Do not use `git reset --hard` or delete tracked files to recover local
  demo state; runtime outputs are ignored and should be regenerated instead.
