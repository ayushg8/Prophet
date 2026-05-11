# Prophet Pilot Release Notes

Date: 2026-05-11
Status: internal buyer-pilot baseline merged to `main`, not a git tag
Branch: `main`
Baseline product/runtime commit checked: `1929dc0`

These notes identify the safe fixture/hash set for the current buyer pilot.
This release candidate does not authorize live target validation.
They do not authorize live target validation, live collection workflows, payload
generation, production SIEM/ticket pushes, or autonomous remediation.

## Product Claim

Prophet is a policy-bound evidence workflow for defensive exposure
prioritization. The pilot helps an evaluator inspect:

- What exposure class Prophet recommends hardening first.
- Why the recommendation is reasonable now.
- Which fixture, source, policy, approval, sandbox, and handoff artifacts support
  that answer.
- Which SOC/ticketing review templates are generated for human review.

## Runnable Local Product

From a prepared checkout with console dependencies installed:

```bash
make console-demo
```

This starts the localhost-only control API and evaluator UI in one terminal.
Use `Ctrl-C` to stop both processes. The default local endpoints are:

- Evaluator UI: `http://127.0.0.1:5173/`
- Readiness API: `http://127.0.0.1:8787/api/readiness`

If the default ports are already in use:

```bash
PROPHET_CONTROL_PORT=8877 PROPHET_CONSOLE_PORT=5273 make console-demo
```

The launcher rejects non-localhost UI hosts and fails before spawning child
processes if dependencies are missing or ports are occupied.

For the full local product gate:

```bash
make pilot-ready-check-full DATE=2026-05-11
```

That command runs the environment check, default buyer pilot smoke, dated
validation dashboard, production-readiness summary, release-safety scan,
console lint/build, control evidence smoke, Playwright console smoke tests, and
console dependency audit.

With a local demo already running, the focused live check is:

```bash
make console-live-check
```

That command checks the localhost UI, readiness API, evidence endpoint,
integration export endpoint, and runtime audit log.

## Smoke Manifests

Default edge-appliance smoke:

- Command: `./scripts/run-pilot-demo-smoke.sh`
- Hash manifest: `scripts/pilot-demo-smoke.sha256`
- Expected runtime artifact hashes: 26
- Reviewed policy ID: `prophet-pilot-fixture-localhost-v0.1`
- Reviewed policy SHA-256:
  `7d051922a110f024188b522b89d11782151cce2d58fa606f7c319c48f405075c`

Financial-workflow smoke:

- Command: `./scripts/run-pilot-demo-smoke.sh --sector financial-workflow`
- Hash manifest: `scripts/pilot-demo-smoke-financial-workflow.sha256`
- Expected runtime artifact hashes: 26
- Reviewed policy ID: `prophet-pilot-fixture-localhost-v0.1`
- Reviewed policy SHA-256:
  `7d051922a110f024188b522b89d11782151cce2d58fa606f7c319c48f405075c`

## Default Generated Artifact Anchors

After the default smoke passes, the main reviewer artifacts are:

- Evidence JSON: `evidence/outputs/runtime/latest-edge-appliance.json`
- Evidence JSON SHA-256:
  `9570017c12c2132f7b60fc2d8458bcfd9eef88683dc0b58a5905ba4c6bbe6e3c`
- Evidence Markdown: `evidence/outputs/runtime/latest-edge-appliance.md`
- Evidence Markdown SHA-256:
  `e537d54dc6a365e8dfb682efe86da2eb5e23fc2270a2b550c869d3d8e63fa7b1`
- Integration manifest:
  `integrations/outputs/runtime/latest-edge-appliance/manifest.json`
- Integration manifest SHA-256:
  `dfe1d31264779b5168b6f8bd3cb07eca641c901d795897dae882acf4a4da1d7f`
- Handoff review checklist:
  `integrations/outputs/runtime/latest-edge-appliance/review_checklist.md`
- Handoff review checklist SHA-256:
  `0e7429be2462071053988df1ec4ee42a8ac23e2104cdcde15814c45ccbd9a910`
- Handoff review ZIP:
  `integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip`
- Handoff review ZIP SHA-256:
  `e676da036f9f5e4d8c2bbbe6306486654a6463dcba37f5985e9a8b1392e29280`
- Audit export:
  `evidence/outputs/runtime/pilot-demo-operator-audit-export.json`
- Audit export SHA-256:
  `aed651d9fd244e6d55a9db7078079984e8d023ba8b699df22f784205e80caca7`

## Verification Performed

- Local worktree smoke passed on 2026-05-10 after adding the handoff review
  checklist artifact, manifest customer-placeholder validation, and Forecast
  section rationale/source-ID rendering in the evidence Markdown.
- PR `#5` merged to `main` on 2026-05-11 at
  `04fb56b4c4c5d3e48a1de0f286f3f12c43ad9dd4`; the GitHub `main` CI run for
  that merge commit completed successfully.
- The latest checked product/runtime head is
  `1929dc0211f9d4567774df8b22a674afd01df48b`
  (`1929dc0 Opt CI actions into Node 24 runtime`). The GitHub `main` CI run
  for that head completed successfully:
  <https://github.com/Ayush1298567/Prophet/actions/runs/25663480672>.
- `cd prophet-console && npm run acceptance` passed locally at `1929dc0`,
  including the root pilot smoke, console lint, TypeScript/Vite build, control
  evidence smoke, and 5 Playwright console tests.
- `make pilot-ready-check-full DATE=2026-05-11` passed on 2026-05-11 at
  PR head `0026d85` before merge, including console lint/build, control
  evidence smoke, 5 Playwright console tests, and
  `npm audit --audit-level=moderate` with 0 vulnerabilities. The merge commit
  `04fb56b` has no tree diff from that verified PR head.
- `cd prophet-console && npm run capture:screenshots` passed and generated 6
  redacted desktop/mobile evaluator screenshots under ignored
  `evidence/outputs/runtime/console-screenshots/`.
- `make console-screenshot-check` passed against the generated screenshot
  manifest, verifying ignored runtime paths, PNG hashes, PNG dimensions, and
  the fixture-backed sharing boundary.
- `python3 -m unittest discover -s scripts/tests -v` passed with 367 tests,
  including validation-gate, send-boundary, console-demo, documented
  exposure classification guide, pre-commit hook, and release-note guardrail
  coverage.
- `make python-tests` passed on 2026-05-11 across the scripts, cyber-side,
  world-side, assets, sandbox runner, policy, evidence, and integration Python
  suites.
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --diff`
  passed over 0 paths in the clean committed worktree.
- There are 0 untracked non-ignored files after the local commit split; the
  release-hygiene wrapper handles that clean state without skipping the other
  gates.
- `make release-hygiene` passed on 2026-05-11, including tracked/untracked
  whitespace, release-safety scans, staged-path safety, current-worktree secret
  scanning, policy lint, and default-output URL/provenance safety over 7
  outputs and 1 OSINT provenance manifest.
- Full `make secrets-archaeology` is available for public-release review and
  currently flags historical `LOG4SHELL_INSTRUCTIONS.md` password-like content
  that needs cleanup, rotation, or an explicit exception before public release.
  Use `docs/SECRET_HISTORY_REVIEW.md` for the safe review path.
- Manual local checks returned `http://127.0.0.1:5173/` HTTP 200 and
  `http://127.0.0.1:8787/api/readiness` with `ok: true` and no blocking
  failures.
- Manual live console checks also passed on alternate ports `5291` / `8891`:
  readiness returned `ok: true` with no blocking failures, evidence generation
  returned `evidence_bundle_generated`, integration export returned
  `integration_handoff_exported`, and both audit events attested
  `no_live_target_data_included`.
- `PROPHET_CONTROL_PORT=8891 PROPHET_CONSOLE_PORT=5291 make console-live-check`
  passed against the running local demo, including audit-log validation.
- Default and financial-workflow smoke manifests now verify 26 artifact hashes.
- `make worktree-smoke` passed on 2026-05-11 after overlaying the current
  0 non-ignored dirty files into a temporary clone from the local commit set,
  running
  `./scripts/check-local-env.sh`, and passing the default smoke with 26
  verified hashes.
- A true GitHub fresh clone of branch
  `prophet-pilot-consolidation-2026-05-05` at PR head `6fe55f3` at
  verification time passed on macOS on 2026-05-11 with
  `./scripts/check-local-env.sh` and `./scripts/run-pilot-demo-smoke.sh`,
  verifying 26 pilot hashes.
- A true GitHub fresh clone of GitHub `main` at verification time,
  `91b91e630a418b83cb9c00ff959e47be5897ac6a` passed on macOS on
  2026-05-11 with `./scripts/check-local-env.sh` and
  `./scripts/run-pilot-demo-smoke.sh`, verifying 26 pilot hashes and reporting
  no policy drift. This is a checked-baseline true fresh-clone proof, not a
  moving claim about later documentation-only commits. Rerun this check before
  release tagging if a later release tag moves beyond this commit.
- Documentation-only commit `ad5eb5c` passed GitHub `main` CI on 2026-05-11,
  including the Linux fresh-clone pilot smoke. It does not replace the macOS
  true-clone baseline above.
- Later documentation-only commits should not be appended here one-by-one.
  Verify the current pushed head with GitHub `main` CI and local handoff gates
  such as `make release-hygiene`,
  `make pilot-ready-check-full DATE=2026-05-11`, `make console-live-check`, and
  `make validation-send-copy-check DATE=2026-05-11`. Those checks verify the
  handoff state without changing the product/runtime baseline.
- The GitHub Actions `python` job runs on `ubuntu-latest` and now names the
  `Linux fresh-clone pilot smoke preflight` plus
  `Linux fresh-clone pilot smoke` steps, covering the Linux fresh-clone smoke
  gate for pushed heads.
- GitHub workflows opt JavaScript actions into Node 24 with
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`, so the CI path is already testing
  the upcoming hosted-runner action runtime. GitHub still emits a deprecation
  annotation for Node 20-targeted actions, but the latest CI annotation confirms
  those actions are being forced to run on Node 24. Documentation-only commits
  after this point must rerun their doc/test/safety gates, but they do not
  change the checked runtime baseline unless product code or workflows change.
- `make worktree-smoke` is now the repeatable local wrapper for that pre-commit
  worktree-overlay check. It clones HEAD to `/tmp`, overlays non-ignored dirty
  files, excludes ignored private validation files, and runs the safe root
  pilot smoke without staging, committing, pushing, or tagging.
- `./scripts/run-worktree-smoke.sh` is the script behind `make worktree-smoke`;
  the latest wrapper run verified the clean local commit set with 0 overlay
  files and 26 smoke hashes.
- Smoke verification checked runtime artifact policy hashes against
  `policy/prophet-pilot-policy.json`.

## Release Blockers

- No git release tag has been created for this fixture/hash set; public tagging
  is blocked until the historical secret-history finding has an owner decision.
- PR `#5` is merged to `main` for the internal buyer-pilot baseline.
- Customer validation remains `insufficient_data`; production platform build
  remains gated.
- Production readiness remains below controlled-production requirements.

## Evaluator Stop Conditions

Stop the pilot review if:

- Smoke hashes do not match the packaged manifest.
- Runtime policy-hash drift is reported.
- Any artifact includes live targets, credentials, private hostnames, live IPs,
  raw scraper text, payload instructions, or customer screenshots.
- The requested pilot depends on live/offensive validation or autonomous
  remediation.
