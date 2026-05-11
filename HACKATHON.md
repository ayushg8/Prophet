# Prophet — Hackathon Context

> Historical context: this hackathon-era document is retained for provenance.
> It is not the current product direction. For current work, use `AGENTS.md`,
> `docs/CODEX_CEO_FINISH_BRIEF.md`, and `docs/PROPHET_COMPLETION_AUDIT.md`.
> Prophet is now scoped as a policy-bound defensive exposure evidence workflow,
> not zero-day prediction, exploit tooling, live target validation, or
> autonomous remediation.

**Event:** 3rd Annual National Security Hackathon (Army xTech, hosted by Cerebral Valley)
**Dates:** Sat 2026-05-02 11:45 PT → Sun 2026-05-03 12:00 PT
**Venue:** Shack15, 1 Ferry Building Suite 201, San Francisco, CA 94111
**Submission:** Public repo URL + 1-min demo video + PS4 + team roster

## Team

| Person | Component | Status |
|---|---|---|
| Ayush | Forecaster (world-side) | **Done** |
| Idan | Exploit Engine (cyber-side, SSH machine) | In progress overnight |
| Alexander | Exploit Engine + Console integration | Ongoing |

## Current status (2026-05-02 evening)

| Component | What's done | What's next |
|---|---|---|
| **Forecaster** | Full pipeline done. Outputs `strike_windows` + `strike_vectors` JSON. Golden fixtures checked in. | Feed live scraper data when available |
| **Console** | Core layout, Perlin hero, component shells built | Wire forecaster JSON into `StrikeWindowTimeline` + `ForecastPanel`. Plan exploit-stream display |
| **Exploit Engine** | Log4Shell lab environment set up (Java PoC, LDAP server, scripts) | Idan working overnight; returns AM with zero-day exploit + defense artifacts |
| **Integration** | `worldSide.ts` loader exists; golden fixtures loading | Connect live output; wire exploit engine stream to Console |

## Immediate priorities

1. **Show forecaster output on the Console** — `StrikeWindowTimeline` and `ForecastPanel` should display real strike windows + strike vectors from `world-side/outputs/golden-*.json`
2. **Plan the exploit generation display** — how does the Console show the zero-day exploit being generated in real time? (streaming agent events → `AgentStream`, result → `ExploitPanel`)
3. **Plan the defense display** — `DefencePanel` shows the generated patch + Sigma rule
4. **Wire it all together** — when Idan's exploit engine returns, the full loop: forecaster JSON → exploit engine → patch + Sigma → Console shows everything

## Problem statement fit

**Primary: PS4 — Digital Defense and Cybersecurity.** Prophet generalizes the PS4 model: predict → validate against a containerized target → emit patch + detection rule in one agent run.

**Secondary: PS3 — Mission C2.** The predict → exploit → defend → validate loop maps to the defender's kill chain (F2T2EA). The human review gate between exploit and defend is exactly the human-in-the-loop step PS3 requires.

## Why this matters (the 30%-weighted impact pitch)

- **CISA BOD 22-01** makes KEV remediation mandatory for all Federal Civilian Executive Branch agencies. DoD weapons platforms and contractor networks share the same KEV-listed CVEs.
- **29% of KEV entries** were exploited on or before disclosure day (VulnCheck). EPSS missed >80% of KEV entries above its 0.5 threshold before listing. Defenders are reactive by structure.
- Prophet flips KEV from rear-view to forward-looking: predict the next class, validate in sandbox, ship patch + Sigma before the adversary's Day 0. "Left of boom" for cyber.
- Same loop runs disconnected on a Palantir CASK-class edge kit — predict, validate, patch a forward-deployed system without phoning home.

## Hackathon compliance

| Rule | Status |
|---|---|
| Public repo on submission | `github.com/Ayush1298567/Prophet` is public |
| New work only | All code written Sat 11:45 PT → Sun 12:00 PT. `research/` and `world-side/data/` are pre-event artifacts, marked clearly |
| Tooling open and accessible | Operator-in-the-loop Codex terminal workflow, deterministic fixtures, public Vulhub images, public Nuclei template metadata, public CISA/NVD/EPSS feeds |
| Fits PS4 primary | Confirmed |

**No novel exploit generation.** The exploit engine orchestrates existing Nuclei templates against Vulhub containers. Agent scope is locked to `localhost / 127.0.0.1`. Targets are vulnerable-by-design images only.

## Judging criteria

| Weight | Criterion | Win plan |
|---|---|---|
| 35% | **Technical Demo** | Streaming agent reasoning + tool-call cards as visual centerpiece. Live path: geopolitical forecast → exploit candidate → "VULNERABLE" → patch generated → applied → re-run → "BLOCKED" + Sigma rule. Nothing fake; every state change traceable. |
| 30% | **Military Impact** | KEV mandate (BOD 22-01) → DoD/DIB exposure → 29% pre-disclosure exploitation → Prophet's "left of boom" inversion. Log4Shell hit DoD networks; ESF-22 was the federal response. CASK edge-kit fit for tactical-disconnected ops. |
| 25% | **Solution Creativity** | Forecast + exploit + defend in one loop, KEV as a forward signal. No competitor (XBOW, NodeZero, Pentera, Hadrian, Qualys, TrendAI AESIR) closes all three legs. |
| 10% | **Presentation** | Clean UI, no decorative motion beyond Perlin hero. Provenance on every claim. 90-second arc rehearsed 3× on hardware before submission. |

## 3-minute pitch arc

1. **0:00–0:20 — Hook.** "29% of CISA's Known Exploited Vulnerabilities are weaponised on or before disclosure day. Federal mandates require patching them. Defenders are reactive by structure."
2. **0:20–0:50 — Wedge.** "Prophet inverts KEV from rear-view to forward-looking. Geopolitical signals tell us *when* and *how*. One agent loop predicts the exploit class, validates it in a sandbox, and ships the patch + Sigma rule — before the campaign runs."
3. **0:50–2:20 — Demo.** Open Console → strike window + strike vector from forecaster → click CVE → approve → watch reasoning stream → "VULNERABLE" → patch generated → applied → re-run → "BLOCKED" → Sigma rule shown.
4. **2:20–2:45 — Impact.** BOD 22-01 mandate, DoD/DIB exposure, CASK edge-kit fit.
5. **2:45–3:00 — Ask.** "Prophet runs today as an operator-in-the-loop Codex terminal workflow with deterministic fixtures. Production can swap in approved private integrations without changing the contract."

## Three judge challenges to drill

1. *"Is the patch actually applied or are you faking the badge?"* — Pull up second terminal, show `docker logs` env-var diff, point at Nuclei "Not Vulnerable" output.
2. *"How is this different from XBOW / NodeZero?"* — "They find and validate. They don't predict ahead of KEV listing, and they don't co-generate the patch in the same loop. Prophet does both."
3. *"Show me a CVE not in your demo."* — Run `check_nuclei_template(CVE-XXXX)` live. Be honest about Vulhub coverage.

## Submission checklist (Sunday 1200)

- [ ] Public repo URL: `github.com/Ayush1298567/Prophet`
- [ ] 1-minute demo video URL (YouTube or Loom)
- [ ] Problem statement: **PS4 — Digital Defense and Cybersecurity**
- [ ] Team roster + emails
- [ ] One-paragraph project description in README

## Scope limits — do not let creep eat the demo

- No novel exploit generation (Nuclei template orchestration only)
- No trained ML model (structured prompt reasoning over public signals)
- No production SIEM integration (Sigma rule is valid YAML, not loaded into Elastic/Splunk)
- No multi-target parallelism
- No live-infra testing — localhost sandbox is absolute
- No real zero-day discovery
