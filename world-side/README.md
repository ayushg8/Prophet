# World Side — Agent Context

> If you are an AI agent (Claude Code, Codex, etc.) joining this work, read this first. 60-second orientation. Detailed specs live in adjacent files.

## Project: Prophet

A cyber-threat-prediction system being built for the **3rd Annual National Security Hackathon (Army xTech)** at Shack15, San Francisco. Hacking window: Saturday 2026-05-02 11:45 PT → Sunday 2026-05-03 12:00 PT. **Public repo on submission.** Primary problem statement: **PS4 — Digital Defense and Cybersecurity**. Secondary: PS3 Mission C2.

Core idea: cyber attacks aren't random — they follow geopolitical pressure and rhyme with history. Prophet reads the world, predicts the cyber move, validates the defense in a sandbox, before the campaign runs.

## Team — three people, two components

- **Cyber Side** — Alexander + Idan. Identifies the next likely zero-day or CVE class. Runs a sandbox-and-patch loop: fire the exploit against a vulnerable container, generate the patch + Sigma rule, confirm the block. Answers *what* will be exploited.
- **World Side** — Ayush (your user). Threat-timing forecaster. Produces strike-window forecasts grounded in cited evidence. Answers *when* and *why*.

Cyber Side hands an exploit candidate to World Side. World Side hands a strike-window forecast back. Outputs merge into a single alert: *"deploy this patch and this Sigma rule during this window because of these reasons."*

## Ayush's role — World Side

**One line:** Cyber Side predicts *what* will be exploited. Ayush predicts *when* and *why*.

For each exploit candidate Cyber Side hands over, Ayush produces one forecast that answers three questions, with a cited source for every claim:

1. **Why this exploit?** — what makes it valuable to the adversary right now
2. **Why now?** — the time-sensitive geopolitical pressure that puts the value at peak in this window
3. **What's the window?** — a concrete date range with a confidence level

Engine inputs:

- **Historical campaign corpus** — past geopolitical trends paired with past zero-day usage. The analogy anchor.
- **Current geopolitical context** — sanctions, military escalations, indictments, election cycles. Open-source signal.
- **Current chatter** — Telegram channels, dark-web forums. Scraped on an **isolated machine**, sanitized before any record reaches a Claude prompt.

Ayush does **NOT** predict the exploit itself, run the exploit, or generate the patch — those are Cyber Side.

## Current project state

Planning docs, data corpus, scaffolding, and the first World Side forecaster implementation are now present. The data corpus remains a pre-event research artifact; the forecaster code was added during the hackathon window.

In flight:

- `INTERFACE.md` — JSON contract between Cyber Side and World Side. Drafted, awaiting Alexander's sign-off.
- `forecaster/` — stdlib-only Python package that turns a Cyber Side candidate JSON into a sourced `world_forecast.v0.1` JSON.
- `fixtures/` — safe Direction A candidate examples for edge-appliance, disruptive-shutdown, and financial-theft scenarios.
- `outputs/` — generated and golden Direction B forecast examples for UI / Cyber Side handoff.
- `tests/` — stdlib `unittest` smoke tests for loaders, schemas, CLI, source coverage, and non-actionable vector constraints.
- `scraper/` — isolated scraper machine access docs + setup script. Network reachability is being resolved by Idan (venue wifi appears to block peer-to-peer; Tailscale or similar is the likely fix).
- `scraper/config/source_catalog.json` — source matrix for official feeds, public chatter, high-risk metadata, OSINT context, and analysis-tool references. Safe official/RSS/API collectors are enabled; auth-gated, onion, Telegram, AIS/flight, and target-enumeration lanes are disabled by default.
- `data/` — historical pairings corpus, calendar of timing windows, indictment + sanctions snapshots. Substantial pre-event research artifacts; will feed the analogy engine and the current-context engine when those are built.

## Run the forecaster

From repo root:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --out world-side/outputs/generated-forecast-edge-appliance.json
```

Run tests:

```bash
PYTHONPATH=world-side python3 -m unittest discover -s world-side/tests
```

Optional sanitized chatter input:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --chatter world-side/fixtures/sanitized-chatter-sample.jsonl \
  --out world-side/outputs/generated-forecast-edge-appliance.json
```

Only pass sanitized JSONL here. Raw scraper output stays on the isolated scraper machine.

Dry-run the scraper-side sanitizer/official collector locally:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli \
  --collector cisa-kev \
  --input kve.json \
  --limit 25 \
  --out /tmp/prophet-cisa.jsonl
```

List the loaded source catalog:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli --list-sources
```

On a Linux isolated scraper host, use `scraper/bin/bootstrap-scraper-machine.sh` once, then emit sanitized JSONL into `/srv/scraper/output/`.

On a Windows OpenSSH scraper host, deploy `world-side/scraper/` to `C:\srv\scraper\app`, run `scraper/bin/bootstrap-scraper-windows.ps1`, then run `scraper/bin/run-once-windows.ps1` to emit sanitized JSONL into `C:\srv\scraper\output`.

## Files in this folder

- `ROLE.md` — full role definition for World Side
- `INTERFACE.md` — JSON contract with Cyber Side (DRAFT, pending sign-off)
- `forecaster/cli.py` — CLI entrypoint for producing forecast JSON
- `forecaster/chatter.py` — validates sanitized chatter JSONL and converts it into forecast context signals
- `forecaster/models.py` — Direction A / Direction B validation
- `forecaster/generator.py` — assembles `world_forecast.v0.1`
- `forecaster/loaders.py`, `corpus.py`, `features.py`, `matcher.py`, `scoring.py` — local data loading, feature extraction, matching, and scoring helpers
- `fixtures/` and `outputs/` — candidate and forecast examples
- `fixtures/sanitized-chatter-sample.jsonl` — safe chatter fixture; no raw posts, onion addresses, credentials, or targets
- `tests/` — smoke tests
- `data/historical_pairings.md` — analogy corpus (geopolitical event ↔ cyber-campaign pairings, fully sourced)
- `data/calendar_events.md` — forward calendar of high-value timing windows (May–Nov 2026)
- `data/indictments_state.md` — state-affiliated cyber indictments snapshot
- `data/sanctions_state.md` — current US/EU sanctions snapshot with cyber-motive analysis
- `scraper/ACCESS.md` — architecture + OPSEC for the isolated scraper machine
- `scraper/TEAMMATE_SETUP.md` — 5-minute SSH setup for teammates
- `scraper/setup-access.sh` — idempotent SSH access script
- `scraper/.env.example` — env template (real `.env.local` is gitignored)
- `scraper/scraper_side/` — stdlib scraper-side sanitization and official-feed collector package
- `scraper/config/source_catalog.json` — safe source inventory and lane rules

Repo-level:

- `../HACKATHON.md` — full hackathon constraints, judging plan, hour-by-hour
- `../PROPHET_TECHNICAL_WRITEUP.md` — pre-event design writeup (planning artifact)
- `../research/` — pre-event research (planning artifacts only, no code)

## Working norms for any agent picking up work

- **Don't run scrapers on Ayush's main dev box.** Scraping happens only on the isolated scraper machine.
- **Don't commit secrets.** `.env.local`, SSH keys (`*_ed25519`, `*.pem`), session files, raw scrape artifacts are all gitignored. Verify with `git check-ignore -v <file>` before any push.
- **Don't paste raw scrape output into Claude.** Sanitize first.
- **Ask before architectural decisions.** Ayush is the human in the loop. The contract with Cyber Side is collaborative — bend to whichever side is harder to change.
- **Step-by-step delivery.** Don't dump giant artifacts on Ayush. Small steps, confirm, then proceed.
