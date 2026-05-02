# Prophet — Hackathon Context

> Compiled 2026-05-02. Reconciles `PROPHET_TECHNICAL_WRITEUP.md` and `research/PROPHET_feasibility.md` against the constraints of the **3rd Annual National Security Hackathon (by Army xTech)**.

## Event

- **Name:** 3rd Annual National Security Hackathon (by Army xTech, hosted by Cerebral Valley)
- **Dates:** Saturday 2026-05-02 → Sunday 2026-05-03
- **Venue:** Shack15, 1 Ferry Building Suite 201, San Francisco, CA 94111 (2nd floor)
- **Discord:** https://discord.com/invite/xgEaYSfZ2x
- **Wifi:** `SHACK15_Members` / `M3mb3r$4L!f3`
- **Prizes:** 1st $20K · 2nd $12K · 3rd $8K · 4th $6K · 5th $4K (sponsored by U.S. Army)
- **Team size:** up to 4

## Schedule (working clock)

| Day | Time (PT) | Event |
|---|---|---|
| Sat May 2 | 0900 | Doors open; team formation |
| Sat May 2 | 1100 | Welcome + presentations |
| Sat May 2 | **1145** | **Hacking starts** |
| Sat May 2 | 1300 | Lunch |
| Sat May 2 | 1900 | Dinner |
| Sat May 2 | 2200 | Doors close — overnight stay OK, no reentry |
| Sun May 3 | 0900 | Doors reopen |
| Sun May 3 | **1200** | **Hacking stops · submissions due** |
| Sun May 3 | 1215–1400 | Round 1 judging (3-min pitch + 1–2 min Q&A) |
| Sun May 3 | 1410 | Top 6 finalists demo on stage (3 min + 2–3 min Q&A) |
| Sun May 3 | 1515 | Winners announced |

**Effective hack window:** ~24 hours if we stay overnight, ~13 hours if we don't. Assume overnight; the feasibility plan's hour-by-hour assumes 24h.

## Team and components

Three-person team. Two named components, one fused loop.

- **Cyber Side** — Alexander + Idan. Identifies the next likely zero-day or CVE class. Runs the validation loop: exploit fired against a vulnerable container, patch and Sigma rule generated, block confirmed. Answers *what* will be exploited.
- **World Side** — Ayush. Threat-timing forecaster. Reads chatter (Telegram, dark-web sources) and geopolitical context, fuses with a historical campaign corpus, produces strike-window forecasts grounded in cited evidence. Answers *when* and *why*.

Cyber Side hands its exploit candidate to World Side. World Side hands a strike-window forecast back. The two outputs merge into the final alert: *"deploy this patch and this Sigma rule during this window because of these reasons."*

World Side details: see `world-side/ROLE.md`.

## Problem statement fit

**Primary: Problem Statement 4 — Digital Defense and Cybersecurity.** The PS4 example "deployable security scanning toolkit that validates containerized AI model deployments against known-good baselines, detecting anomalous files, tampered libraries, or embedded threats before models influence operational decisions" is a direct subset of Prophet's loop. Prophet generalises: predict-then-validate against any containerised target, and emit the patch + detection rule in the same agent run.

**Secondary: Problem Statement 3 — Mission C2.** Prophet's predict → exploit → defend → validate loop is the **defender's kill chain**: F2T2EA (Find / Fix / Track / Target / Engage / Assess) reframed for vulnerability operations. The PS3 example "automates key steps in the kill chain... while maintaining human-in-the-loop oversight and explainable rationale" maps cleanly — the Phase 2/3 approval gate is exactly that human-in-the-loop step.

We pitch PS4 as the primary. The PS3 framing is a backup if a judge pushes on military impact.

## Why this matters for NATSEC (the 30%-weighted impact pitch)

- **CISA BOD 22-01** makes KEV remediation mandatory for all Federal Civilian Executive Branch agencies. DoD weapons platforms, base networks, and contractor environments inherit the same KEV-listed CVEs (Log4Shell, CitrixBleed, MOVEit, Ivanti Connect Secure, PAN-OS GlobalProtect — all hit DoD or DIB targets).
- The window between CVE publication and active exploitation collapsed in 2025: VulnCheck shows **29% of KEV entries were exploited on or before disclosure day**. EPSS, the current ML baseline, missed >80% of KEV entries above its 0.5 probability threshold before listing (arXiv 2411.02618). Defenders are reactive by structure.
- Prophet flips KEV from rear-view to forward-looking: predict the next class, validate the exploit chain in a sandbox, and ship the patch + Sigma rule before the adversary's Day 0. This is "left of boom" for cyber the same way sensor fusion is "left of boom" for kinetic ops.
- Tactical-edge framing: the same loop runs disconnected on a CASK-class edge kit (Palantir's offered hardware) — predict, validate, patch a forward-deployed system without phoning home.

## Hackathon rules — compliance plan

| Rule | Status / Plan |
|---|---|
| **Public GitHub repo on submission** | Repo `github.com/Ayush1298567/Prophet` is public. Keep it public. |
| **New work only — from scratch during the event** | The `research/` folder and `PROPHET_TECHNICAL_WRITEUP.md` are **planning documents** authored 2026-05-02 before the start. All code (`src/`, `ui/`, agent loop, sandbox config, UI) is written 1145 Sat → 1200 Sun. We will note this explicitly in `README.md`. |
| **Tooling open and reasonably available** | Anthropic Claude API, public Vulhub images, public Nuclei templates, public CISA/NVD/EPSS feeds — all freely accessible. No private datasets, no proprietary models. |
| **Fits one of five problem statements** | PS4 primary, PS3 secondary. Stated at submission. |
| **Team ≤ 4** | TBD — confirm at team formation 0900–1100 Sat. |

## Partner resources we plan to use (or considered)

| Partner | Resource | Decision |
|---|---|---|
| **Anthropic** (implicit via Claude API) | Standard Claude API + tool use | **Yes — core.** `claude-sonnet-4-6` for the agent loop. `claude-opus-4-7` for tougher reasoning if budget allows. |
| **Anthropic CVP** | Cyber Verification Program (gates Tier-2 cyber capability) | **Apply now, do not block on it.** Approval is 2–5 days, longer than the hackathon. Demo runs entirely within standard AUP — see "Reconciliation" below. |
| **Palantir AIP** | On-site account provisioning | **Stretch goal only.** If ahead at hour 16+, write Prophet's predicted-vulnerability output as an AIP Ontology object for partner-judge resonance. Otherwise drop. |
| **Palantir CASK** | Edge hardware kit (Problem Statements 1 & 2) | **Skip for build, mention in pitch.** "Prophet's loop is small enough to run disconnected on a CASK-class edge kit." Don't try to deploy on hardware in 24h. |
| **OpenAI Codex** | Workspace access | **Optional — IDE assist only.** Don't put a second model in the agent loop; complexity for no demo gain. |
| **Danti** | Geospatial intelligence | Not relevant to Prophet. Skip. |

## Reconciling the writeup with the hackathon

Two things in `PROPHET_TECHNICAL_WRITEUP.md` need tightening for the hackathon clock:

### 1. The CVP guardrail is impossible to satisfy in time

The writeup calls the Anthropic Cyber Verification Program application "non-negotiable" and "highest-leverage." CVP approval is 2–5 days; submission is in ~24 hours. We will not have CVP by demo time.

**Mitigation (already in `PROPHET_feasibility.md`):**

- Use only **existing Nuclei templates** for exploitation. We orchestrate, we do not synthesise novel exploits. This stays in the standard-AUP dual-use research lane.
- System prompt explicitly scopes the agent to `localhost` / `127.0.0.1` only. No outbound reachability from agent tools.
- Targets are **vulnerable-by-design** images only (Vulhub Log4Shell primary, Struts S2-061 backup).
- Pitch language: *"Prophet runs the orchestration loop on standard Claude API; the production version extends to variant analysis under Anthropic's Cyber Verification Program, which we've applied for."* We file the CVP application during the hackathon as an artifact of seriousness, but the demo does not depend on it.

### 2. The 24h plan needs the demo-video deliverable

Submission requires a **1-minute demo video** uploaded to YouTube/Loom. The feasibility doc's hour-by-hour ends at "buffer" — we slot the video as the explicit hour 21–22 task.

## Tightened hour-by-hour (anchored to the actual clock)

Saturday 1145 = Hour 0. Sunday 1200 = Hour 24:15.

| Hours | Wall clock (PT) | Build |
|---|---|---|
| 0–1 | Sat 1145–1245 | Env lock: clone Vulhub, `docker compose up -d` Log4Shell, fire Nuclei manually (must succeed), request NVD API key, snapshot all feeds to `data/`. **File Anthropic CVP application.** Decision gate: if Log4Shell flakes, switch to Struts S2-061 *now*, not at hour 18. |
| 1–3 | Sat 1245–1445 | Tool layer: 9 Python tool functions returning typed dicts; `mock_adapter.py` with hardcoded returns; `MOCK=true` env var wired through dispatch. |
| 3–5 | Sat 1445–1645 | Agent loop core: `ProphetAgent` class, system prompt with localhost scope, 4 phase definitions, tool schemas, streaming. Test with `MOCK=true`. |
| 5–7 | Sat 1645–1845 | Live loop: full 4-phase run against real Vulhub + real feeds. Time it 3×. Target <3 min. Record one successful run as JSON event log → REPLAY artifact. |
| 7–10 | Sat 1845–2145 | UI shell: React+Vite+TS, four-panel layout (queue · agent stream · exploit result · patch+sigma), FastAPI `/run` + SSE `/stream`. |
| 10–13 | Sat 2145 – Sun 0045 | Demo-path polish: pre-seed Log4Shell at rank 1, Human Review Gate modal between Phase 2 → 3, phase progress bar, full 90s arc rehearsal. |
| 13–16 | Sun 0045–0345 | Hardening + REPLAY mode equivalence; `docker save` images for offline cold-start; UI error boundaries; pre-demo checklist (≤6 items). |
| 16–19 | Sun 0345–0645 | **Stretch:** second CVE (Struts) OR AIP Ontology write OR ATT&CK technique annotations. Pick one or none — do not blow the critical path. |
| 19–21 | Sun 0645–0845 | 3 full rehearsals on demo hardware; drill the three most likely judge challenges; confirm REPLAY fallback indistinguishable from live. |
| 21–22 | Sun 0845–0945 | **Record 1-minute demo video** (YouTube/Loom). Pre-demo checklist → start Vulhub → record screen capture of the full arc → upload → put URL in submission form. |
| 22–23 | Sun 0945–1045 | Code freeze. Final preflight: container running, queue shows Log4Shell rank 1, NVD key live, MOCK fallback confirmed. |
| 23–24 | Sun 1045–1145 | Buffer. No new features. Sleep or fix the single most critical issue from preflight. |
| 24:15 | Sun 1200 | **Submit.** Public repo URL + 1-min video URL + problem statement (PS4) + team. |

## Judging criteria — how Prophet wins each

| Weight | Criterion | Win plan |
|---|---|---|
| 35% | **Technical Demo** | The streaming Claude reasoning + tool-call cards is the visual centerpiece. Live Nuclei output → "VULNERABLE" → patch via `docker exec` → re-run → "BLOCKED" badge, with `docker logs` visible in a second terminal as receipt. Nothing fake; every state change traceable. |
| 30% | **Military Impact** | KEV mandate (BOD 22-01) → DoD/DIB exposure → 29% pre-disclosure exploitation → Prophet's "left of boom" inversion. Concrete: Log4Shell hit DoD networks; ESF-22 was the federal response. Mention CASK-class edge fit for tactical-disconnected deployment. |
| 25% | **Solution Creativity** | Triple loop **predict → exploit → defend** in one Claude run, KEV as forward-looking signal — verifiably absent from XBOW, NodeZero, Pentera, Hadrian, Qualys Agent Val, TrendAI AESIR per `research/PROPHET_competitive_landscape.md`. Defender's kill chain framing reframes a familiar pattern. |
| 10% | **Presentation** | Dense, restrained UI (no decorative motion). Provenance shown for every claim. 90-second arc rehearsed 3× on hardware. |

### 3-minute pitch arc

1. **0:00–0:20 — Hook.** "29% of CISA's Known Exploited Vulnerabilities are weaponised on or before disclosure day. Federal mandates require patching them. Defenders are reactive by structure."
2. **0:20–0:50 — Wedge.** "Prophet inverts KEV from rear-view to forward-looking. One Claude agent, four phases: predict → exploit → defend → validate. No shipping product closes all three legs."
3. **0:50–2:20 — Demo.** Open dashboard → ranked queue → click Log4Shell → approve exploit → watch reasoning stream → "VULNERABLE" → patch generated → applied → re-run → "BLOCKED" → show Sigma rule.
4. **2:20–2:45 — Impact.** BOD 22-01 mandate, DoD/DIB exposure, edge-deployable on CASK-class kits.
5. **2:45–3:00 — Ask.** "Prophet runs on standard Claude API today. Production extends under Anthropic's Cyber Verification Program."

### Three judge challenges to drill

1. *"Is the patch actually applied or are you faking the badge?"* → Pull up second terminal, show `docker logs` env-var diff, point at real Nuclei "Not Vulnerable" output.
2. *"How is this different from XBOW / NodeZero?"* → Two sentences: "They find and validate. They don't predict ahead of KEV listing, and they don't co-generate the patch in the same loop. Prophet does both." Reference `research/PROPHET_competitive_landscape.md` if pressed.
3. *"Show me a CVE not in your demo."* → Run `check_nuclei_template(CVE-XXXX)` live in the UI. Be honest about Vulhub coverage for the full loop.

## Submission package (Sunday 1200)

- [ ] Public repo URL: `github.com/Ayush1298567/Prophet`
- [ ] 1-minute demo video URL (YouTube or Loom)
- [ ] Problem statement: **PS4 — Digital Defense and Cybersecurity**
- [ ] Team roster + emails (≤4 members)
- [ ] One-paragraph project description (lift from `PROPHET_TECHNICAL_WRITEUP.md` "What it is, in one paragraph", trimmed)
- [ ] README on the repo with: problem statement, what we built, how to run, demo video, attribution to research/ as pre-event planning only

## Open items before 1145 Sat

1. **Team formation** — solo or 2–4 people? Need to know before tool-layer split.
2. **Hardware** — one demo machine, ideally with battery + tethered hotspot fallback.
3. **CVP application filed?** — do this in hour 0 even though it won't return in time; the artifact matters for the pitch.
4. **NVD API key requested?** — same; do at hour 0.
5. **Anthropic API key + budget** — confirm key and a hard spend cap (the agent loop with streaming + 4 phases × ~8 tool rounds × 24h × rehearsals can run up costs).
6. **Palantir AIP credentials** — pick up at the venue if we want the stretch-goal integration.

## What stays out of scope (do not let scope creep eat the demo)

From `research/PROPHET_feasibility.md`'s "What we are NOT building" — re-affirmed under hackathon clock:

- No novel exploit generation (orchestration of existing Nuclei templates only).
- No trained ML prediction model (structured prompt reasoning over public signals).
- No production SIEM integration (Sigma rule is valid YAML, not loaded into Elastic/Splunk).
- No multi-target parallelism.
- No live-infra testing — localhost sandbox is absolute.
- No statistical backtested precision/recall table for the prediction claim.
- No real zero-day discovery. The sketch's Phase II "generate new zero-day" is descoped — explicitly, in writing, in the pitch.
