# Console Accessibility And Browser Target

Date: 2026-05-11

This target applies to the local evaluator console used in the buyer pilot. It
does not claim production WCAG certification, screen-reader certification,
cross-browser enterprise support, mobile app support, or hosted SaaS readiness.

## Accessibility Target

For the current buyer pilot, the console should support:

- Keyboard entry into the operator console.
- Keyboard opening and closing of the evaluator runbook drawer.
- Named buttons and form-like controls.
- Hidden drawers and hidden regions removed from the tab order.
- Stable accessible labels for the main buyer-review panels:
  triage queue, forecast brief, defence panel, evidence bundle panel,
  integration handoff panel, policy status panel, and alpha readiness panel.

The target is intentionally narrow because the console is still a local
fixture-backed evaluator surface. Before any production or broader buyer-facing
release, add a full accessibility review that covers contrast, focus order,
screen-reader announcements, reduced-motion behavior, responsive layouts, and
manual assistive-technology testing.

## Current Automated Coverage

`prophet-console/tests/console.smoke.ts` covers the current target:

- `console supports keyboard navigation for the evaluator runbook path`
- `console accessibility smoke keeps controls named and hidden drawers out of tab order`

Run it through the existing acceptance wrapper:

```bash
cd prophet-console
npm run test:smoke
```

or as part of:

```bash
cd prophet-console
npm run acceptance
```

The root pilot readiness wrapper also runs console acceptance:

```bash
make pilot-ready-check-full DATE=YYYY-MM-DD
```

## Browser Target

Current supported browser target for the buyer pilot is Chromium through
Playwright, running against the local Vite console and localhost-only control
API.

Current non-claims:

- No Safari support claim.
- No Firefox support claim.
- No mobile browser support claim.
- No hosted or customer-network browser support claim.
- No production SSO, tenant, or RBAC browser-flow support claim.

Before a buyer-facing release that depends on more than Chromium, add a browser
matrix covering Chromium, Firefox, and WebKit/Safari-equivalent behavior, then
record known differences in this file and in the release checklist.

## Release Rule

Do not describe the console as broadly accessible or cross-browser supported
unless the matching manual review and browser matrix have been run for the exact
release commit.
