# Prophet Demo Operator Checklist

This checklist is for the current buyer-pilot package. It uses the checked-in
fixture path only: sanitized forecast inputs, deterministic sandbox artifact,
policy-bound evidence, and review-template exports. Do not run live validation,
live scraper collection, or vulnerable third-party lab images for this demo.

## T-30 Minutes

- [ ] Demo laptop on power, notifications off.
- [ ] Console tab ready at `http://127.0.0.1:5173`.
- [ ] Control server terminal ready in `prophet-console`.
- [ ] Confirm the live VM scraper is disabled unless a separate approved
  collection plan exists: `PROPHET_ENABLE_VM_SCRAPER` is unset or not `1`.
- [ ] Confirm no `.env.local`, SSH keys, session files, or runtime outputs are
  open in the editor.

## T-20 Minutes

- [ ] Run the deterministic smoke command:

  ```bash
  ./scripts/run-pilot-demo-smoke.sh
  ```

- [ ] Confirm it verifies all hashes against
  `scripts/pilot-demo-smoke.sha256`.
- [ ] Start the local control server:

  ```bash
  cd prophet-console
  npm run dev:control
  ```

- [ ] Start the console in a second terminal:

  ```bash
  cd prophet-console
  npm run dev
  ```

## T-10 Minutes

- [ ] `PreflightChecklist` is green.
- [ ] `ForecastPanel` shows the edge-appliance strike window and vector.
- [ ] `ReadinessPanel` shows zero blocking failures.
- [ ] Evidence and handoff panels are idle and ready to generate runtime
  artifacts.

## Demo Run Order

1. Click `DEMO REFRESH` to show seeded, fixture-backed OSINT and forecast
   refresh.
2. Click `LOAD FIXTURE` or generate the deterministic sandbox artifact from
   the control flow.
3. Generate the evidence bundle.
4. Export the SIEM/ticketing handoff templates.
5. Show the evidence bundle hash, policy hash, approval record hash, and
   integration manifest hash.
6. Open `docs/PILOT_DEMO.md` for the expected output table if a reviewer asks
   how to reproduce the run.

## Recovery

| Failure | Recovery |
|---|---|
| Console will not load | Run `cd prophet-console && npm run build`, then inspect build errors. |
| Control server offline | Restart `npm run dev:control` and re-run `/health`. |
| Evidence generation fails | Run `./scripts/run-pilot-demo-smoke.sh` and inspect the first failing validator. |
| Hash gate fails | Treat as a release-blocking artifact drift until the contract change is reviewed. |
| Browser smoke fails | Use Playwright artifacts from CI or rerun `npm run test:smoke`. |

## Non-Negotiables

- No live targets.
- No payloads.
- No credentials.
- No private hostnames or IPs.
- No raw scraper text.
- No automatic SIEM, ticketing, or patch deployment.
- No vulnerable third-party lab images in the buyer demo.

## Post-Demo

- [ ] Keep generated runtime artifacts under ignored `outputs/runtime`
  directories.
- [ ] Record only the policy hash, evidence hash, integration manifest hash,
  and known blockers in the release note.
- [ ] Do not publish screenshots containing customer data or raw terminal
  output.
