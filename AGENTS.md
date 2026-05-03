# Agent Operating Manual — Prophet

> **Read this file first.** If you are an AI agent (Claude Code, Codex, Cursor, or any other) joining this work, this is your orientation. The detailed specs live in adjacent files; this doc tells you what to read, how to behave, and what not to do.

## What Prophet is

**One** cyber-threat-prediction system being built for the **3rd Annual National Security Hackathon (Army xTech)** at Shack15, San Francisco. Hacking window: **Saturday 2026-05-02 11:45 PT → Sunday 2026-05-03 12:00 PT**. The repo will be public on submission.

Prophet's premise: cyber attacks aren't random — they follow geopolitical pressure and rhyme with history. Prophet fuses exploit prediction, timing forecasting, and defense validation into one loop, and surfaces the result before the campaign runs.

Primary problem statement: **PS4 — Digital Defense and Cybersecurity**. Secondary: PS3 Mission C2.

## One system, four stages

Prophet is **one system with four stages**. Do not treat it as two separate systems with an API between them. It is a single pipeline with multiple human owners covering different stages.

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 1 — EXPLOIT PREDICTION                            │
│ Identify the next likely zero-day or CVE class          │
│ Owners: Alexander, Idan ("Cyber Side")                  │
└──────────────────────┬──────────────────────────────────┘
                       │  exploit candidate (JSON, contract in INTERFACE.md)
                       ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 2 — TIMING FORECAST                               │
│ Strike-window forecast grounded in geopolitics + history│
│ Owner: Ayush ("World Side")                             │
└──────────────────────┬──────────────────────────────────┘
                       │
   (in parallel with Stage 2:)
┌─────────────────────────────────────────────────────────┐
│ STAGE 3 — DEFENSE VALIDATION                            │
│ Sandbox the exploit, generate patch + Sigma rule, block │
│ Owners: Alexander, Idan                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 4 — MERGED ALERT                                  │
│ Final SOC-consumable artifact: patch + window + reasons │
└─────────────────────────────────────────────────────────┘
```

The handoffs between stages are **internal contracts**, not system-to-system APIs. They exist so different humans can develop in parallel without blocking each other.

## Team labels (for coordination only)

When docs say "Cyber Side" or "World Side," those are **team labels**, not separate systems:

- **Cyber Side** — Alexander + Idan. Own stages 1 and 3.
- **World Side** — Ayush. Owns stage 2.
- Stage 4 (merge) is shared.

Use these labels when assigning work or talking about ownership. Do not use them as if Prophet were two products.

## Hackathon rules — non-negotiable

- **Public repo on submission.** Anything in this repo becomes public. Never commit secrets.
- **New work only.** All *application code* must be written from scratch between Sat 11:45 PT and Sun 12:00 PT. Pre-event research, planning docs, and the curated data corpus are explicit exceptions and live in clearly-marked artifact folders.
- **Tooling must be openly accessible.** Standard Anthropic API, public Vulhub images, public Nuclei templates, public CISA/NVD/EPSS feeds, public threat-intel reports. No private datasets, no proprietary models.

## Repo map

```
Prophet/
├── AGENTS.md                       ← you are here
├── HACKATHON.md                    ← hackathon constraints, judging plan, hour-by-hour
├── PROPHET_TECHNICAL_WRITEUP.md    ← pre-event design writeup (PLANNING ARTIFACT)
├── research/                       ← pre-event research (PLANNING ARTIFACTS)
├── world-side/                     ← Stage 2 (timing forecaster) — Ayush
│   ├── README.md                   ← world-side agent orientation
│   ├── ROLE.md                     ← Stage 2 role definition
│   ├── INTERFACE.md                ← Stage 1 → Stage 2 contract (DRAFT)
│   ├── data/                       ← analogy corpus + geopolitical context (RESEARCH ARTIFACTS)
│   │   ├── historical_pairings.md
│   │   ├── calendar_events.md
│   │   ├── indictments_state.md
│   │   └── sanctions_state.md
│   └── scraper/                    ← isolated scraper machine docs + SSH
└── cyber-side/                     ← Stages 1 + 3 — TBD when Alexander/Idan need a folder
```

If you are working on Stage 1 or Stage 3 and `cyber-side/` doesn't exist yet, ask Ayush before creating it.

## Working conventions — binding for all agents

### OPSEC

- **Never commit** `.env.local`, SSH keys (`*_ed25519`, `*.pem`, `*.key`), session files (`*.session`), or raw scrape artifacts. All are gitignored — verify with `git check-ignore -v <file>` before any push.
- **Scraping happens only on the isolated scraper machine.** Never on Ayush's main dev box. Never on the demo machine.
- **Never paste raw scrape output into a Claude prompt.** Sanitize first.

### Code discipline

- **No application code yet.** All current files are planning docs, research artifacts, or scaffolding. Code starts Sat 11:45 PT.
- **Don't add features beyond what the task requires.** The 24h clock punishes over-engineering.
- **Don't rewrite from scratch unilaterally.** If you think a major rewrite is needed, ask Ayush.
- **No commits of `node_modules/`, build outputs, or generated files.** Already gitignored.

### Working with the human

- **Step-by-step delivery.** Don't dump giant artifacts on Ayush. Small steps, confirm, proceed.
- **Ask before architectural decisions.** Ayush is the human in the loop.
- **Cross-stage contracts** (e.g. `world-side/INTERFACE.md`) need both stages' confirmation before either side implements.
- **Never use destructive git ops** (`reset --hard`, `push --force`, `branch -D`, `clean -f`) without explicit instruction.

### Documentation

- **Every claim cites a source.** This is the rule for the data corpus, every prediction, every forecast surfaced in the demo.
- **Use the unified-system framing.** "Stage 1 produces an exploit candidate consumed by Stage 2." Not "the cyber team's system talks to my system."
- **Don't write CLAUDE.md, README.md, or summary docs unsolicited.** Update existing docs in place.

## Reading order for new agents

1. **This file (`AGENTS.md`)** — orientation
2. **`HACKATHON.md`** — full hackathon constraints, judging plan, demo arc
3. **`world-side/README.md`** — if working on Stage 2
4. **`world-side/INTERFACE.md`** — if touching the Stage 1 → Stage 2 contract
5. **`world-side/data/historical_pairings.md`** — if building the analogy engine
6. **`PROPHET_TECHNICAL_WRITEUP.md`** + **`research/`** — pre-event design context, planning artifacts only — do not treat as binding architecture

## Multi-agent etiquette

Ayush runs multiple agents in parallel and uses the main Claude Code session as the coordinator. To avoid stepping on each other:

- **Write to the canonical paths only.** Stage 2 work goes in `world-side/`. Stage 1/3 work goes in `cyber-side/` (when it exists). Don't create parallel folders like `world-layer/` or `cyber/`.
- **If you find a parallel folder that shouldn't exist, surface it to Ayush before merging.** Another agent may be mid-write.
- **Update existing files in place** rather than creating new ones with overlapping scope.
- **If unsure where something belongs, ask Ayush.** A 10-second clarification beats a 30-minute reconciliation.

## Status as of last edit (2026-05-02)

- Planning docs, data corpus, and access scaffolding in place.
- `world-side/INTERFACE.md` drafted, awaiting Alexander's sign-off on Stage 1 output shape.
- Scraper machine network reachability being resolved by Idan (venue wifi appears to block peer-to-peer; Tailscale is the likely fix).
- **No application code written yet.** Code starts Sat 11:45 PT.
