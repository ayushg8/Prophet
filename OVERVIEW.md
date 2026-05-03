# Prophet — Project Overview

> A plain-language walkthrough of the project from highest level down to file-level
> detail. For a quick orientation if you are new to the repo, or for a refresher
> before demo day. For agent onboarding rules see `AGENTS.md`. For event
> constraints and pitch arc see `HACKATHON.md`.

## 1. One sentence

**Prophet predicts, in advance, what kind of cyber attack is most likely to
happen next, then automatically writes the patch and detection rule that would
block it — and proves the patch works in a sandboxed copy of the vulnerable
software.**

It is a 24-hour hackathon project for the 3rd Annual National Security
Hackathon (Army xTech), problem statement **PS4 — Digital Defense and
Cybersecurity**.

## 2. The core idea (the "wedge")

Most cybersecurity tools look backward: a CVE gets disclosed → patches get
written → defenders catch up. By the time the CISA Known Exploited
Vulnerabilities (KEV) list adds a CVE, **29% of those CVEs were already
exploited on or before disclosure day**. Defenders are structurally late.

Prophet flips this. It uses two streams of information:

- **Geopolitical signals** — what is going on in the world right now (summits,
  anniversaries, sanctions, escalations) — to predict *when* an attack window
  opens.
- **Historical exploit corpus + KEV** — to predict *what kind* of attack is
  most likely in that window.

It then generates a defense (patch + Sigma detection rule) and validates that
defense in a sandboxed copy of vulnerable software. All in one agent loop.
**Predict → exploit class → defend → validate**, before the campaign runs.

The wedge is the three-leg combo: predict + exploit + defend in one loop.
Existing tools do parts of it but none ship the full loop today.

## 3. What we are not claiming

This is the difference between a believable demo and one that gets challenged
off stage:

- We are **not finding new zero-days.** We replay historical, fully-disclosed
  CVEs and show that Prophet would have flagged the *class* before disclosure.
- We **never show exploit code on screen.** What the judge sees: prediction
  score, exploit class label, patch diff, sandbox validation result. Payload
  bytes never cross the UI.
- Targets are **vulnerable-by-design** sandbox containers (Vulhub, DVWA, Juice
  Shop). Never live infrastructure.

When we say "predicts a zero-day" we mean *predicts the next likely
vulnerability class* — not "discovers a brand-new bug nobody knew about."

## 4. The three components, one pipeline

```
┌───────────────┐   strike forecast    ┌─────────────────┐   defense artifact   ┌────────────┐
│  FORECASTER   │ ───────────────────► │  EXPLOIT ENGINE │ ───────────────────► │  CONSOLE   │
│  (world-side) │                      │   (cyber-side)  │                      │ (React UI) │
└───────────────┘ ◄─────────────────── └─────────────────┘                      └────────────┘
                   exploit candidate
```

| Component | Lives in | Owner | Job |
|---|---|---|---|
| **Forecaster** | `world-side/` | Ayush | Reads geopolitical signals + historical campaigns. Outputs *when* and *how* an attack is likely. |
| **Exploit Engine** | `cyber-side/` (contract) + Idan's Dell box (live engine) | Idan + Alexander | Takes the forecast, picks an exploit class, validates it in a sandbox, generates patch + Sigma rule. |
| **Console** | `prophet-console/` | Shared | React UI that streams agent reasoning and displays the strike window, exploit status, defense, and validation. |

Three JSON contracts hold the components together:

- **Direction A** — Exploit Engine → Forecaster: "here is a candidate exploit class to forecast against."
- **Direction B** — Forecaster → Exploit Engine + Console: "here is the strike window and strike vector."
- **Direction C** — Exploit Engine → Console: "here is the predicted exploit class, the patch, the Sigma rule, and the sandbox validation result."

A and B are documented in `world-side/INTERFACE.md`. C is in
`cyber-side/INTERFACE.md`. Each contract has a stdlib-only Python validator
that rejects payloads, credentials, live targets, or procedural language.

## 5. Component 1 — The Forecaster (`world-side/`)

### What it does, in plain words

You give it a candidate exploit class (e.g. "edge-appliance auth bypass"). It
looks at three things:

1. **A calendar of upcoming geopolitical events** (Trump-Xi summit,
   Shangri-La Dialogue, Tiananmen anniversary, etc.) — to find time windows
   where adversary pressure is high.
2. **A historical corpus of past campaigns** (Volt Typhoon, Ivanti Connect
   Secure, NotPetya, etc.) — to find patterns where this kind of vulnerability
   was used in similar political contexts.
3. **CISA KEV + EPSS scores** — to ground everything in real exploit data.

It outputs a `world_forecast.v0.1` JSON with:

- **`strike_windows`** — ranked time periods (e.g. "May 8–18, 2026,
  confidence 0.67, triggered by Trump-Xi summit, analogous to Volt Typhoon").
- **`strike_vectors`** — ranked attack methods (e.g. "edge-appliance initial
  access and persistence, targeting federal civilian agencies").
- **`strategic_frame`** — adversary class, target sector, geographic scope,
  and a hard-coded `excluded_uses` block ("No exploit payloads, No
  target-control instructions, No named live targets").
- **`summary`** — one-line forecast for the Console.

### How it is actually built

Pure Python. **No LLM at runtime, no external API calls.** The forecaster is
deterministic: same inputs → same outputs. By design — it has to work offline
on demo day.

Files inside `world-side/forecaster/` (~3,500 lines of Python):

| File | What it does |
|---|---|
| `loaders.py` | Reads CISA KEV JSON, calendar events from markdown, historical corpus. |
| `corpus.py` | Loads the campaign + threat-actor + escalation context bundle. |
| `chatter.py` | Loads sanitized scraper output (when available). |
| `features.py` | Computes features for matching (CWE, geographic scope, time deltas). |
| `matcher.py` | Matches a candidate exploit class against historical analogies. |
| `scoring.py` | Computes confidence scores for windows and vectors. |
| `generator.py` | Stitches it all together into the final forecast JSON. |
| `models.py` | Contract validator. Enforces the "no payloads / no live targets / no procedural language" rules. |
| `cli.py` | Command-line entry point: `python -m forecaster.cli --candidate ... --out ...` |

### The data layer (`world-side/data/`)

Hand-curated markdown files the forecaster reads:

- `calendar_events.md` — geopolitical event calendar.
- `historical_pairings.md` — 12 historical campaigns paired with their
  triggering geopolitical context.
- `threat_actors.md` — adversary class profiles.
- `escalation_state.md`, `indictments_state.md`, `sanctions_state.md` —
  current-state snapshots.

### The scraper (`world-side/scraper/`)

Separate, isolated subsystem. Pulls "chatter" from public sources (CISA,
GDACS, USGS, vendor advisories, GitHub advisory metadata) and produces
**sanitized JSONL** the forecaster can consume. Runs only on an isolated
machine — never on the dev box. Only sanitized output crosses into the
forecaster.

### Outputs (`world-side/outputs/`)

- `golden-forecast-edge-appliance.json` — canonical demo forecast (PRC
  pre-positioning around the Trump-Xi summit).
- `golden-forecast-financial-theft.json` — DPRK financial-theft scenario.
- `golden-forecast-wiper-shutdown.json` — destructive-wiper scenario.
- Plus regenerated copies the forecaster produces deterministically.

These are fixtures so the demo works without internet or live scraping.

## 6. Component 2 — The Exploit Engine (`cyber-side/` + Dell live box)

### What it does, in plain words

It reads the Forecaster's output, picks an exploit *class* that fits the
strike vector, runs **detection-only** validation against a vulnerable-by-design
sandbox, generates a patch + Sigma detection rule, applies the patch, re-runs
validation to confirm the patch blocks the attack, and emits a single JSON
artifact summarizing all of that.

For the demo the canonical example is **Log4Shell (CVE-2021-44228)**:

1. Forecaster says "edge-appliance access, PRC pre-positioning, May 2026."
2. Engine picks JNDI-lookup RCE as the representative class.
3. Engine spins up a vulnerable Log4j 2.14.0 container (Vulhub).
4. Engine runs a Nuclei template; the template confirms the lookup fires via
   an out-of-band DNS callback. No shell is spawned.
5. Engine writes the defense: `formatMsgNoLookups=true` JVM flag, hardened
   `log4j2.xml`, plus a fallback JAR-strip of `JndiLookup.class`. Sigma rule
   detects JNDI strings in HTTP headers.
6. Engine restarts the service with the patch applied, re-runs the same
   Nuclei template — gets "NOT VULNERABLE."
7. Engine emits the **Direction C artifact**: predicted exploit class,
   non-actionable rationale, patch diff, Sigma rule, pre/post validation
   status, audit fields.

### Two operating modes

**Mode A — fixture mode (works right now, no Dell):**

- Console loads `cyber-side/fixtures/exploit-engine-output-edge-appliance.json`.
- That fixture contains a fully validated Direction C artifact.
- Demo renders end-to-end without any live engine.
- Safety net for stage day.

**Mode B — live mode (Dell back online, run by Idan):**

- Idan runs the actual engine on the Dell.
- It produces a fresh Direction C artifact.
- Console loads that instead of the fixture.
- If anything goes wrong on stage, fall back to Mode A by switching the loader.

The Dell is currently unreachable, so Mode A is the only confirmed-working
path today.

### The validator

`cyber-side/validator.py` is a stdlib-only Python module that enforces the
Direction C contract. It rejects:

- Banned keys (`payload`, `credentials`, `target_host`, `ip`, `commands`, …).
- Procedural language in narrative fields (`"curl ..."`, `"run the following..."`).
- Diffs that *add* lines containing exploit-payload tokens (`${jndi:`, etc.).
- Sigma rules where the YAML `id` does not match `rule_id`.
- Validation scopes that are not localhost-only.
- Confidence scores outside 0.0–1.0.
- Wrong schema version, missing fields, duplicate source IDs.

`cyber-side/tests/test_exploit_engine_artifact.py` exercises the golden
fixture passing and 9 ways drift would be caught. All 10 tests pass.

### The lab files at the repo root

Operational scaffolding that runs on the Dell when it is reachable. Not part
of the public demo:

- `LOG4SHELL_INSTRUCTIONS.md` — step-by-step setup runbook.
- `log4shell_setup.py` — automates installing Java 8 + Log4j 2.14.0 + an HTTP
  service + an LDAP server on a Windows host.
- `VulnerableApp.java`, `Exploit.java`, `Exploit.class` — the Java target and
  the proof-of-exploit class that runs in the sandbox.
- `setup_lab.ps1`, `fix_service.ps1` — PowerShell helpers.
- `demo_script.py` — runs the historical Log4Shell demo end-to-end.
- `setup_status.py` — sanity-check script.
- `qwen_agent.py` — auto-setup agent that drove the Windows machine via a
  local Qwen model.
- `ldap_server.py`, `log4j2.xml`, `TestJNDI.java` — supporting bits.

These exist because the engine needs a real sandbox to validate against. They
reference the Dell but no credentials are committed — passwords are
out-of-band per OPSEC.

## 7. Component 3 — The Console (`prophet-console/`)

### What it does

A React + Vite + TypeScript single-page app that visualizes the entire
pipeline. The judge sees this on stage. It has an "INITIATE PROPHET LOOP"
button that walks through four phases.

### The four phases (rendered as `AgentStream`)

1. **Phase I — Intel.** Tool calls fire (`fetch_kev`, `score_epss`,
   `probe_target_lab`, `query_world_side`). Forecaster output flows in.
   Citations and historical analogies render as cards.
2. **Phase II — Plan.** Engine narrates which exploit class it is picking and
   why, with a sanitized payload structure (placeholders, not real bytes).
   A `human_gate` event pauses for operator authorization.
3. **Phase III — Execute.** Nuclei runs against the sandbox. `ExploitPanel`
   flips to "VULNERABLE" when the JNDI callback is received.
4. **Phase IV — Defend.** Patch and Sigma rule generate. `DefencePanel`
   renders both with a copy button. Engine re-runs validation; `ExploitPanel`
   flips to "BLOCKED."

### The components

| Component | Job |
|---|---|
| `Header.tsx`, `PerlinHero.tsx`, `Landing.tsx` | Visual shell. |
| `PhaseProgress.tsx` | Top progress bar showing the active phase. |
| `LiveFeedTicker.tsx` | Marquee of recent forecaster source items. |
| `StrikeWindowTimeline.tsx` | Renders strike windows on a timeline with confidence. |
| `ForecastPanel.tsx` | Full Direction B forecast detail panel. |
| `HistoricalAnalogyCard.tsx` | One historical campaign analogy card. |
| `SourceCitation.tsx` | Inline citation chip with date and supports text. |
| `TriageQueue.tsx`, `PreflightChecklist.tsx` | Pre-launch context. |
| `ApprovalGate.tsx` | Human-authorization modal between Phase II and III. |
| `AgentStream.tsx` | Streaming agent reasoning column — typewriter text, tool-call cards, phase dividers, exploit-status badges. |
| `ExploitPanel.tsx` | Right-column panel: target, CVE, vector, status badge, Nuclei output. |
| `DefencePanel.tsx` | Tabs for Patch (diff syntax) and Sigma (YAML). Reads from the Direction C artifact. |
| `LabTopology.tsx` | Diagram of the sandbox topology. |
| `RunbookDrawer.tsx` | Slide-out runbook for the operator. |

### The data layer (`prophet-console/src/data/`)

| File | Purpose |
|---|---|
| `worldSide.ts` | TypeScript types + loader for the Direction B forecast. |
| `forecastIndex.ts` | Maps `candidate_id` → loaded `StrikeForecast` object. |
| `cves.ts` | CVE metadata for the demo set. |
| `mockEvents.ts` | Hand-built event stream that drives the demo. Hardcodes the Log4Shell scenario today and merges in the world-side forecast. |
| `replayController.ts` | Drives the demo: emits events with timing, handles the human gate. |

The Console runs entirely on static JSON from `world-side/outputs/` and
`cyber-side/fixtures/`. No backend required.

## 8. The data contracts in detail

### Direction A — Exploit candidate

Cyber side says: "Forecaster, please tell me about *this* class of vulnerability."

```
candidate_id, generated_at,
identity { candidate_type, cve_class_label, target_product, cwe_ids },
attack_hypothesis { attack_vector, intended_effect, destructiveness, narrative },
rationale { narrative, confidence, score },
weaponization { kev_listed, epss_score, public_poc_available, ... },
source_refs [ ... ]
```

Validated by `world-side/forecaster/models.py::ExploitCandidate`.

### Direction B — Strike forecast

Forecaster's main output.

```
forecast_id, schema_version: "world_forecast.v0.1",
strategic_frame { adversary_class, target_scope, excluded_uses [ ... ] },
strike_windows [ { start_date, end_date, confidence, why_this_window, historical_analogies, ... } ],
strike_vectors [ { vector_class, target_sector, non_actionable_mechanism, defensive_implication, ... } ],
summary, source_refs
```

Validated by `world-side/forecaster/models.py::WorldForecast`.

### Direction C — Exploit Engine artifact

Engine output. New as of 2026-05-02.

```
artifact_id, schema_version: "exploit_engine_artifact.v0.1",
input_refs { candidate_id, forecast_id, vector_id },
predicted_exploit { exploit_class_label, cwe_ids, cve_id, kev_listed, epss_score,
                    non_actionable_rationale, confidence, confidence_score },
defense {
  patch { summary, patch_format, diff, applies_to, rollback_note },
  sigma_rule { rule_id, title, yaml, level, logsources }
},
validation { sandbox_id, scope (must say "localhost only"),
             pre_patch_status, pre_patch_excerpt, post_patch_status, post_patch_excerpt,
             validation_tool, validation_template, wall_time_seconds },
operator_notes { human_gate_decision, operator_label, post_run_caveats },
audit { run_id, signed_sha256, emitted_by },
source_refs [ ... ]
```

Validated by `cyber-side/validator.py::validate_exploit_engine_artifact`.

## 9. The intel grounding (`intel/`)

`intel/cisa_kev_2026-05-01.json` is a sample of the CISA Known Exploited
Vulnerabilities catalog. Full catalog is `kve.json` at the repo root (1.3 MB).

KEV is the spine. CISA BOD 22-01 makes KEV remediation mandatory for federal
agencies. Prophet uses it as a forward-looking signal instead of a rear-view
checklist.

## 10. Research artifacts (`research/`)

`research/PROPHET_demo_candidates.md` is pre-event research that picked five
historical KEV CVEs for the demo: Log4Shell, Apache 2.4.49 path traversal,
Spring4Shell, Confluence SSTI, Struts2 OGNL. Each filtered for: (a) judge
recognition value, (b) Vulhub Docker reproduction available, (c) Nuclei
template available. Log4Shell is the on-stage anchor; the others are backups.

## 11. Where the project actually stands right now

| Component | Status | What works |
|---|---|---|
| Forecaster | **Done** | Pipeline runs, golden fixtures emit, 19 tests pass. |
| Exploit Engine contract + fixture | **Done** | Direction C contract written, golden fixture validates, 10 tests pass. |
| Exploit Engine live | **Blocked on Dell** | Idan has the Dell locally, integrating Palantir/Danti, currently unreachable. |
| Console | **In progress** | Components built, mockEvents stream wired, forecaster JSON wired, panels render. Codex pushed cyber-side fixture loading. |
| Demo lab files | **Done** | Log4Shell sandbox setup runs on the Dell. |

The fixture mode is the safety net. If the Dell never comes back, the demo
still runs.

## 12. The OPSEC rules (why so many guards)

- Repo is **public** on submission.
- No exploit payloads, credentials, hostnames, IPs, raw scrape output, or
  session files in commits.
- Scraping runs only on the isolated scraper machine.
- Sandbox-only validation; never live infrastructure.
- Validators enforce these as contract rules, not suggestions.

## 13. The pitch in 90 seconds

> "29% of CISA's KEV entries are weaponized on or before disclosure day.
> Defenders are reactive by structure. Prophet inverts that. Geopolitical
> signals tell us *when* and *how*. One agent loop predicts the exploit class,
> validates it in a sandbox, and ships the patch + Sigma rule before the
> campaign runs.
>
> [Click] Strike window — May 8 to 18, anchored by the Trump-Xi summit and
> Volt Typhoon analogy.
>
> [Click] Edge-appliance vector — Log4Shell as the representative class.
>
> [Approve] Watch the agent: Nuclei fires, callback received, **VULNERABLE**.
> Patch generates: `formatMsgNoLookups=true`. Patch applies. Re-run:
> **BLOCKED**. Sigma rule shown.
>
> Same loop runs disconnected on a Palantir CASK-class edge kit. Left of boom
> for cyber."

## 14. Where to look next

- New to the repo? Read `AGENTS.md` for ground rules, then come back here.
- Working on the Forecaster? `world-side/README.md` and
  `world-side/INTERFACE.md`.
- Working on the Exploit Engine or Direction C? `cyber-side/README.md` and
  `cyber-side/INTERFACE.md`.
- Working on the Console? `prophet-console/src/data/mockEvents.ts` is the
  starting point for the demo flow.
- Pitching or rehearsing? `HACKATHON.md` for the judging rubric and pitch arc.
