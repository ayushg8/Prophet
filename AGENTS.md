# Agent Operating Manual — Prophet

> If you are an AI agent joining this repo, read this file first. It is your complete orientation.

## What Prophet is

Prophet predicts cyber attacks before they happen by fusing geopolitical intelligence with exploit analysis. It answers three questions in one loop: *when* is the attack window, *how* will they strike, and *what* is the exploit class — then generates a defense before the campaign runs.

Built for the **3rd Annual National Security Hackathon (Army xTech)** at Shack15, San Francisco. Hacking window: Sat 2026-05-02 11:45 PT → Sun 2026-05-03 12:00 PT. Repo is public on submission.

**Primary problem statement: PS4 — Digital Defense and Cybersecurity.**

## Three components, one pipeline

```
┌──────────────────────────────────────────┐
│  FORECASTER                              │
│  Scrapes geopolitical signals, fuses     │
│  with historical campaign corpus         │
│  → strike_window + strike_vector JSON    │
│  Owner: Ayush                            │
└────────────────────┬─────────────────────┘
                     │  world_forecast JSON
                     ▼
┌──────────────────────────────────────────┐
│  EXPLOIT ENGINE                          │
│  Takes the forecast + CVE candidate,     │
│  generates zero-day exploit prediction   │
│  + zero-day defense (patch + Sigma rule) │
│  Owner: Idan + Alexander                 │
└────────────────────┬─────────────────────┘
                     │  exploit + defense artifacts
                     ▼
┌──────────────────────────────────────────┐
│  CONSOLE                                 │
│  React UI — shows the full pipeline:     │
│  strike window, strike vector, exploit   │
│  generation stream, defense output       │
│  Owner: shared                           │
└──────────────────────────────────────────┘
```

The JSON contract between Forecaster and Exploit Engine is in `world-side/INTERFACE.md`.

## Terminology — use this everywhere

| Term | Meaning |
|---|---|
| **strike window** | Time frame when a target is most vulnerable, based on geopolitical pressure |
| **strike vector** | Attack method most likely in that window (e.g. edge-appliance initial access) |
| **zero-day exploit** | Predicted exploit class the adversary would use |
| **zero-day defense** | Patch + Sigma detection rule generated to counter it |
| **the console** | The React web UI at `prophet-console/` |
| **the forecaster** | World-side scraper + forecasting engine at `world-side/` |
| **the exploit engine** | Cyber-side agent running on Idan's SSH machine |

Do not use "Stage 1/2/3/4" or "Cyber Side/World Side" as primary framing — those were coordination labels during planning. Use the component names above.

## Repo map

```
Prophet/
├── AGENTS.md                        ← you are here
├── HACKATHON.md                     ← event constraints, judging, pitch arc
├── PROPHET_TECHNICAL_WRITEUP.md     ← background design (pre-event, read-only context)
├── research/
│   └── PROPHET_demo_candidates.md   ← CVE selection for demo
├── intel/
│   ├── README.md                    ← dataset docs
│   └── cisa_kev_2026-05-01.json     ← CISA KEV seed
├── world-side/                      ← Forecaster
│   ├── README.md                    ← forecaster orientation + how to run
│   ├── INTERFACE.md                 ← Direction A + B JSON contract; pointer to Direction C
│   ├── forecaster/                  ← forecasting engine (Python)
│   ├── scraper/                     ← isolated scraper machine
│   ├── data/                        ← geopolitical corpus (research artifacts)
│   ├── fixtures/                    ← exploit candidate mocks for dev/test
│   └── outputs/                     ← generated forecasts (golden + live)
├── cyber-side/                      ← Exploit Engine contract + fixture path
│   ├── README.md                    ← Mode A (fixture) + Mode B (Dell live) runbook
│   ├── INTERFACE.md                 ← Direction C contract (engine → Console)
│   ├── INTEGRATIONS.md              ← Idan's Palantir/Danti handoff
│   ├── validator.py                 ← stdlib-only artifact validator
│   ├── fixtures/                    ← Direction C goldens for fixture mode
│   └── tests/                       ← unittest coverage for the validator
├── prophet-console/                 ← Console (React + Vite + TS)
│   └── src/
│       ├── components/              ← UI components
│       └── data/                    ← worldSide.ts, mockEvents, cves, replayController
└── [demo lab files]                 ← Log4Shell setup, Java PoC, scripts (root-level)
```

## Current status (2026-05-02, active hackathon)

| Component | Status |
|---|---|
| Forecaster | **Done.** Outputs `strike_windows` + `strike_vectors` JSON. Golden fixtures in `world-side/outputs/`. |
| Console | **In progress.** Core layout and components built. Integration with forecaster JSON underway. |
| Exploit Engine | **In progress.** Idan working on Dell locally; Dell currently unreachable from dev box. Contract: Direction A + B in `world-side/INTERFACE.md`, Direction C in `cyber-side/INTERFACE.md`. Fixture-mode demo path works without Dell. |
| Demo (Log4Shell) | **Setup done.** Java PoC and lab scripts at repo root. See `LOG4SHELL_INSTRUCTIONS.md`. |

## OPSEC — non-negotiable

- **Never commit** `.env.local`, SSH keys (`*_ed25519`, `*.pem`, `*.key`), session files (`*.session`), or raw scrape output.
- **Scraping runs only on the isolated scraper machine** — never on dev boxes or the demo machine.
- **Sanitize before any Claude prompt** — never paste raw scrape output.
- Verify with `git check-ignore -v <file>` before pushing anything from the lab environment.

## Code discipline

- **Don't add features beyond what the task requires.** 24h clock punishes over-engineering.
- **Don't rewrite from scratch unilaterally.** Ask Ayush before any major structural change.
- **No `node_modules/`, build outputs, or generated files in commits.**
- **No destructive git ops** (`reset --hard`, `push --force`, `branch -D`) without explicit instruction.
- **Application code is live.** Forecaster is done; Console and Exploit Engine are actively being built.

## Working with Ayush

- Small steps, confirm, proceed — don't dump giant artifacts.
- Ask before architectural decisions.
- Update existing files in place rather than creating parallel ones.
- Multi-agent: write only to your component's canonical path. Surface conflicts before merging.
