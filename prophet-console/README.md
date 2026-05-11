# Prophet Console

The Prophet Console is the local evaluator UI for the safe buyer-pilot path. It
shows the fixture-backed forecast, defensive exposure-class portfolio, evidence
bundle, policy status, audit trail, and review-only SIEM/ticket handoff
templates.

## Stack

React + TypeScript + Vite. The evaluator demo loads static fixtures and uses an
optional localhost-only control server to refresh sanitized fixture outputs,
generate evidence, and export review templates. The public pilot path does not
perform live collection, payload generation, production pushes, or autonomous
remediation.

## Run

```bash
(cd prophet-console && npm install)
make console-control
```

In a second terminal:

```bash
make console-ui
```

The UI opens at `http://127.0.0.1:5173`; the control server listens on
`http://127.0.0.1:8787`.

With both commands running, fixture refresh uses tracked sanitized fixtures and
seeded OSINT, evidence generation writes ignored runtime artifacts, and handoff
export writes review templates under `integrations/outputs/runtime/`.

Readiness check:

```bash
curl http://127.0.0.1:8787/api/readiness
```

The Alpha Readiness panel uses this read-only endpoint. Missing runtime evidence
or integration exports are warnings until an operator generates them; policy or
core fixture failures are blocking.

Integration handoff export:

```bash
curl -X POST -H 'x-prophet-control: local-console' \
  http://127.0.0.1:8787/api/integrations/demo-export
```

The Handoff panel uses this localhost-only endpoint after evidence generation.
It writes review templates under `integrations/outputs/runtime/`; it does not
call customer SIEM or ticketing APIs.

Full internal-alpha acceptance:

```bash
npm run acceptance
```

Responsive screenshot capture for a qualified reviewer:

```bash
npm run capture:screenshots
```

This writes desktop/mobile screenshots and a manifest under
`../evidence/outputs/runtime/console-screenshots/`. Those files are ignored
runtime output and require redaction review before sharing.

Before relying on the live VM button:

```bash
cd ..
world-side/scripts/check-scraper-vm.sh
```

## How it connects to Prophet

### Forecaster data

Forecaster output lives in `world-side/outputs/*.json`. The Console loads it via `src/data/worldSide.ts`.

```ts
// src/data/worldSide.ts
import { getForecastForCandidate } from './worldSide';
const forecast = getForecastForCandidate('cs-fixture-edge-appliance-001');
// → { strike_windows: [...], strike_vectors: [...], strategic_frame: {...}, summary: {...} }
```

To use a freshly generated forecast: run the Forecaster, copy output to `world-side/outputs/`, update the candidate mapping in `worldSide.ts`.

### Exploit Engine stream

In the demo, the exploit agent stream is replayed from `src/data/mockEvents.ts` via `src/data/replayController.ts`. When Idan's live exploit engine is ready, wire its SSE stream to the same event types.

## Key components

| Component | What it shows |
|---|---|
| `StrikeWindowTimeline` | Strike windows from the Forecaster (ranked, dated, with confidence) |
| `ForecastPanel` | Strike vectors + strategic frame |
| `AgentStream` | Live reasoning stream from the Exploit Engine |
| `ExploitPanel` | Zero-day exploit prediction result |
| `DefencePanel` | Generated patch + Sigma rule |
| `IntegrationPanel` | SIEM, ticketing, and audit handoff export |
| `ApprovalGate` | Human review gate between exploit and defense phases |
| `PhaseProgress` | Four-phase progress bar (INTEL → PLAN → EXECUTE → DEFEND) |
| `TriageQueue` | CVE triage queue (ranked candidates) |
| `PerlinHero` | Animated landing page background (Perlin noise, visual only) |
| `PreflightChecklist` | Pre-run environment checks |
| `LiveFeedTicker` | Scrolling geopolitical signal feed |
| `HistoricalAnalogyCard` | Historical campaign analogy cards |
| `LabTopology` | Lab environment topology diagram |
| `RunbookDrawer` | Collapsible runbook panel |
| `SourceCitation` | Source citation badges |
| `ReadinessPanel` | Read-only policy, fixture, evidence, export, and safety readiness |
