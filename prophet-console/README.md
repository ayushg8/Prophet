# Prophet Console

The Prophet Console is the real-time web UI for Prophet's prediction pipeline. It displays:

- **Strike windows** — when the target is most vulnerable, from the Forecaster
- **Strike vectors** — how adversaries will likely strike, from the Forecaster
- **Exploit generation stream** — live agent reasoning as the Exploit Engine runs
- **Zero-day defense** — generated patch + Sigma rule, once the exploit loop completes

## Stack

React + TypeScript + Vite. The demo works without a backend by loading static forecaster fixtures and replaying recorded agent events. An optional local-only control server can trigger the isolated scraper VM and refresh the forecast while running on localhost.

## Run

```bash
cd prophet-console
npm install
npm run dev
# opens at http://localhost:5173
```

Optional scraper VM control button:

```bash
cd prophet-console
npm run dev:control
# listens on http://127.0.0.1:8787
```

With both commands running, `DEMO REFRESH` uses the tracked sanitized chatter fixture and refreshes the forecast locally. `LOAD FIXTURE` in the Defence panel loads the cyber-side Direction C fixture from `cyber-side/fixtures/exploit-engine-output-edge-appliance.json` into the Exploit and Defence panels. `RUN SCRAPER VM` calls the local control server, which uses SSH key auth to run `world-side/scripts/run-scraper-vm-workflow.sh`. That script pulls back sanitized JSONL only, validates it through the Forecaster, and returns a refreshed forecast to the Console. If key auth is not ready, the button fails closed and does not prompt for a password.

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
