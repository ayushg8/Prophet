# PROPHET — Hackathon Feasibility & 24-Hour Build Plan

> Research output from agent run 2026-05-02. Question: What's the minimum credible demo we can build in 24 hours, and what infrastructure/data is actually needed?

## TL;DR — Go / No-Go + Sharpest Demo Frame

**GO — with a strictly scoped MVP.**

A 24-hour team can credibly demo the full loop end-to-end *if* "prediction" is reframed as triage enrichment (not novel zero-day forecasting), the exploit step runs a pre-existing Nuclei template against a one-command Vulhub container, and the "patch" step is a Claude-generated WAF rule or config diff. The loop is real. The novelty is the orchestration and the co-generation of defence alongside offence in a single agent run.

**Sharpest demo framing (one sentence for judges):**

> "Prophet ingests today's NVD drops, scores them against KEV history and EPSS, picks the one most likely to be weaponized in the next 30 days, fires a Nuclei template against an isolated vulnerable container, and returns a patch diff and Sigma detection rule — all inside a single Claude agent loop with a human-in-the-loop approval gate."

That is a complete, demonstrable, policy-safe story. It does not require novel exploit generation, model fine-tuning, or live-infra access.

---

## Chosen Architecture — Named Components

```
┌─────────────────────────────────────────────────────┐
│                  Prophet Agent Loop                 │
│              (Claude claude-sonnet-4-6, tool use)   │
│                                                     │
│  Tool: fetch_kev()          → CISA KEV JSON feed    │
│  Tool: fetch_nvd_recent()   → NVD CVE API v2        │
│  Tool: score_epss()         → FIRST.org EPSS API    │
│  Tool: search_exploitdb()   → searchsploit CLI      │
│  Tool: check_nuclei_tmpl()  → local template repo   │
│  Tool: run_nuclei()         → Nuclei binary         │
│  Tool: apply_patch()        → docker exec env var   │
│  Tool: generate_sigma()     → Claude write YAML     │
│  Tool: verify_blocked()     → re-run Nuclei         │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / docker exec (localhost only)
          ┌──────────▼──────────┐
          │  Vulhub Container   │
          │  (target CVE)       │
          └─────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  FastAPI backend    │  ← SSE stream to UI
          │  + React/TS/Vite UI │
          └─────────────────────┘
```

**Orchestration layer:** Python calling the Anthropic Messages API with tool use. No LangChain, no CrewAI — those frameworks add debugging surface in a 24-hour window. Claude handles the plan-execute-evaluate loop natively through tool dispatch.

**UI layer:** React + TypeScript + Vite. Four panels: CVE triage queue, live agent reasoning stream, exploit result badge, patch diff + Sigma rule viewer. FastAPI backend streams events via SSE. Each finished run also emits a Maven-shaped JSON fusion object so the same data can be consumed by a Palantir Maven surface (real or mocked) for the sponsor demo.

**Data layer:** All feeds are public JSON/REST, no auth except NVD (free API key, activates via email in minutes). Snapshot all feeds to local JSON at build start to insulate the demo from rate limits and outages.

---

## Data & Sandbox Reference Table

| Source | URL | Auth | Rate Limit | Notes |
|---|---|---|---|---|
| CISA KEV JSON | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | None | None (static file) | 1,200+ entries; one GET; updated daily |
| NVD CVE API v2 | `https://services.nvd.nist.gov/rest/json/cves/2.0` | Free API key (`nvd.nist.gov/developers/request-an-api-key`) | 5 req/30 s (no key), 50 req/30 s (key) | Filter `pubStartDate`; paginate with `resultsPerPage` |
| EPSS API | `https://api.first.org/data/v1/epss` | None | Not published; no key in practice | Batch: `?cve=CVE-A,CVE-B`; `&date=` for history back to 2021; v4 model as of March 2025 |
| MITRE ATT&CK STIX | `https://github.com/mitre-attack/attack-stix-data` | None | N/A (static clone) | v19.0 released April 2026; query with `mitreattack-python` |
| Exploit-DB / searchsploit | `https://gitlab.com/exploit-database/exploitdb` | None | N/A (local) | `searchsploit -j <CVE>` returns JSON; daily git updates; offline-capable |
| Nuclei Templates | `https://github.com/projectdiscovery/nuclei-templates` | None | N/A (local) | 1,496 KEV-aligned templates confirmed as of 2025; `nuclei -t http/cves/ -u <target>` |
| GitHub Advisory DB | `https://api.github.com/graphql` | Free PAT, no scopes | 5,000 pts/hr | GraphQL `securityAdvisories` query by CVE ID |
| Vulhub targets | `https://github.com/vulhub/vulhub` | None | N/A (local Docker) | `git clone && cd <CVE-dir> && docker compose up -d` |

**Get the NVD API key now** — apply at `nvd.nist.gov/developers/request-an-api-key` using the team email. It activates within minutes and 10x the request rate.

---

## The Prediction Claim — Chosen Option and Why

**Chosen: Option (c) — Triage prediction (which of today's NVD drops will hit KEV within 30 days).**

Option (a) — fine-tune on pre-2024 KEV — is eliminated. A training run consumes 6–8 hours of a 24-hour window and requires GPU access not assumed in scope.

Option (b) — EPSS as baseline, Prophet adds context — is partially correct but "we beat EPSS" is a claim that needs held-out evaluation data to be credible. Research (arxiv 2411.02618) shows EPSS v3 correctly flagged less than 20% of KEV entries above 0.5 probability *before* they were listed, and only 8.3% above 0.9 — so the baseline is genuinely weak. However, demonstrating a statistical delta in a live demo without a pre-built evaluation harness is risky.

Option (c) is the most demo-able: it runs live on real data, produces a ranked shortlist with visible reasoning, and any judge can read the rationale. Prophet's triage signals on top of EPSS are: (1) Nuclei template exists (strongest weaponization signal — means a public exploit scanner template already exists), (2) Exploit-DB entry present, (3) ATT&CK technique mapped (context EPSS doesn't use), (4) composite CVSS/EPSS rank. A CVE in today's NVD feed that has an EPSS above 0.6, a Nuclei template, and an ATT&CK mapping is demonstrably higher-priority than one with just a CVSS 9.8 and no exploit tooling. This is defensible methodology.

**The "prediction" framing to judges:** "EPSS alone has historically missed over 80% of KEV entries before they were listed. Prophet adds weaponization-readiness signals — specifically, the existence of a working scanner template — that EPSS's threat intelligence feed doesn't use. We're not claiming a trained model; we're claiming a better-structured triage reasoning chain."

---

## Agent Orchestration Pattern

Modelled on HackingBuddyGPT's round-based capability architecture (capability-based tool dispatch, sliding history, hard round limit) but structured into four explicit phases:

**Phase 1 — Intel.** Tools: `fetch_kev`, `fetch_nvd_recent`, `score_epss`, `search_exploitdb`, `check_nuclei_tmpl`. Claude reads all feeds and produces a ranked candidate list with per-CVE rationale. Output: the top CVE ID and a structured evidence dict.

**Phase 2 — Exploit Planning.** Tools: `check_nuclei_tmpl`, `read_template`. Claude selects the highest-confidence Nuclei template for the top candidate and describes what it does. If no template exists, Claude generates a minimal HTTP probe description (not a weaponized payload). Human review gate fires here — one Approve button before execution.

**Phase 3 — Execution.** Tools: `run_nuclei`, `read_container_logs`. Nuclei fires against the Vulhub container on localhost. Claude reads stdout and confirms exploit outcome (e.g., "RCE confirmed via JNDI callback").

**Phase 4 — Defence Co-generation.** Tools: `generate_sigma`, `apply_patch`, `verify_blocked`. Claude writes a Sigma detection rule for the exploitation pattern and a minimal patch (config diff or version pin). Patch is applied via `docker exec`. Nuclei re-runs. Claude confirms the block.

**Key design rules:**
- Each phase gets its own Messages API call with a summarized prior-phase context — this keeps individual calls well under the context window and makes phase boundaries recoverable.
- Max 8 rounds per phase. Hard limit; no exceptions during demo.
- `stream=True` on every call. The UI renders tool-call events and text deltas in real time. This is the most visually compelling part of the demo.
- `MOCK=true` env var swaps all tool functions to pre-canned returns. The mock adapter is built and tested in hours 3–5 and is the demo fallback throughout.

---

## Sandbox / Vulnerable-Target Decision

**Winner: Vulhub Docker Compose — Log4Shell (CVE-2021-44228) as primary demo target.**

| Option | Spin-up time | Exploit-to-block loop | Eliminated? |
|---|---|---|---|
| Vulhub (Log4Shell) | `git clone + docker compose up -d`, under 5 min | Excellent — restart container resets state cleanly | No — primary |
| Vulhub (Struts S2-061) | Same | Excellent — same pattern | No — backup |
| DVWA | `docker run`, under 2 min | Partial — web app vulns only, limited CVE specificity | Use only if both Vulhub targets fail |
| OWASP Juice Shop | `docker run`, under 2 min | Partial — OWASP-10 style; no CVE-specific loop | Useful as UI backdrop; not for exploit loop |
| Metasploitable3 | Vagrant + VirtualBox, 30–60 min | Poor | Eliminated |
| HackTheBox retired | VPN + subscription | Requires external network; policy risk | Eliminated |

Log4Shell wins because: the Vulhub environment is stable and well-documented; the Nuclei KEV template exists and is confirmed working; the exploit (JNDI injection via `${jndi:ldap://...}`) is visually clear in logs; and the patch (set `LOG4J_FORMAT_MSG_NO_LOOKUPS=true` via `docker exec` env var, then restart) is instant and verifiable by re-running Nuclei and seeing "Not Vulnerable."

---

## Hour-by-Hour Build Plan (24 Hours)

### Hours 0–1: Environment Lock

- Clone Vulhub; run `docker compose up -d` in `vulhub/log4j/CVE-2021-44228`. Confirm the container is reachable.
- Request NVD API key at `nvd.nist.gov/developers/request-an-api-key` with team email.
- Snapshot all feeds to local JSON: CISA KEV (one GET), NVD last 7 days, EPSS scores for the top 100 NVD CVEs. Save to `data/` directory. This is your demo data cache.
- Install dependencies: `anthropic`, `httpx`, `python-dotenv`, `nuclei` binary, `searchsploit`.
- **Decision gate:** Fire the Nuclei Log4Shell template manually against the container. It must succeed. If not, switch to Struts S2-061 immediately. Do not leave this for hour 18.

### Hours 1–3: Tool Layer

- Implement all 9 tool functions as plain Python functions returning typed dicts. Each function is independently testable.
- `fetch_kev()`: GET + parse; return list of `{cveID, dateAdded, shortDescription}`.
- `fetch_nvd_recent(days=7)`: NVD API v2; filter by `pubStartDate`; paginate.
- `score_epss(cve_ids: list)`: batch EPSS call; return `{cve: {score, percentile}}`.
- `search_exploitdb(cve_id)`: `subprocess` to `searchsploit -j`; parse JSON output.
- `check_nuclei_template(cve_id)`: `find ./nuclei-templates/http/cves -name f"*{cve_id}*"`; returns bool + path.
- `run_nuclei(template_path, target_url)`: subprocess; parse stdout for vulnerable/not-vulnerable.
- `apply_patch(container_name, env_var, value)`: `docker exec` to set env var and restart service.
- `generate_sigma(cve_id, exploit_details)`: Claude sub-call (or part of main loop); return YAML string.
- `verify_blocked(template_path, target_url)`: same as `run_nuclei`; expect "Not Vulnerable" result.
- Write `mock_adapter.py` with hardcoded returns for every tool. Wire `MOCK=true` env var in tool dispatch.

### Hours 3–5: Agent Loop Core

- Define Anthropic tool schemas (JSON) for all 9 tools.
- Write `ProphetAgent` class: system prompt, tool dispatch method, phase transition logic, round counter.
- System prompt constraint (critical for AUP compliance): "You are a defensive security research assistant. You have explicit authorization to test only `localhost` containers managed by the Prophet sandbox. You may not attempt connections to any host outside `127.0.0.1` or `localhost`."
- Wire phases 1–4. Test with `MOCK=true`. Confirm all four phases complete and produce structured output.
- Add `stream=True`; write an event emitter that pushes phase events, tool calls, and text deltas to a Python queue. UI will consume this queue.

### Hours 5–7: Live Loop Testing

- Run the full agent loop against the real Vulhub Log4Shell container with real data feeds.
- Debug: token limits, tool schema mismatches, Nuclei output parsing edge cases, Docker networking on the local machine.
- Target: full loop (all 4 phases) completes in under 3 minutes. Time it three times.
- Record one complete successful run as a JSON event log. This is the replay artifact.

### Hours 7–10: UI Shell

- Scaffold React + Vite + TypeScript.
- Four-panel layout (dense, restrained, no decorative animations — defence-tech console, not a marketing site):
  - Left: CVE triage queue, ranked, with EPSS score and triage signals per row. Clicking a row selects it.
  - Center: Agent reasoning stream. Tool call events appear as typed cards; text deltas stream in as prose. Phase badges (Intel / Plan / Execute / Defend) show current state.
  - Bottom-left: Exploit result panel. Shows Nuclei output, a "VULNERABLE" or "BLOCKED" badge, and a before/after status.
  - Bottom-right: Patch diff viewer (syntax-highlighted code block) + Sigma rule YAML (syntax-highlighted). A "Copy" button on each.
- FastAPI backend with `/run` POST endpoint (starts agent) and `/stream` SSE endpoint (emits events from the queue).
- Implement `REPLAY` mode: load the pre-recorded JSON event log; stream it with 150 ms delays between events.

### Hours 10–13: Demo Path Polish

- Pre-seed the golden CVE (Log4Shell) as rank 1 in the queue so it is visible immediately on open.
- Add the Human Review Gate between Phase 2 and Phase 3: a modal with "Exploit Plan" summary and a single "Approve Execution" button. The agent loop pauses on a `threading.Event` until the button is clicked. This is the most important UX moment — it demonstrates human-in-the-loop and gives the presenter a beat.
- Add phase progress bar (4 steps, each lights up on completion).
- Test the full 90-second demo arc: open console → see queue → approve exploit → watch stream → see BLOCKED badge → show Sigma rule.
- Design rules: serious and dense beats flashy; motion clarifies state changes only; every important claim shows its provenance.

### Hours 13–16: Hardening and Fallback

- Build complete REPLAY mode; confirm it is visually indistinguishable from the live run.
- Rehearse fallback line: "The sandbox is running in isolation mode — I'm switching to the last verified operational replay. Same workflow, same analyst experience."
- `docker save` all required images to local tar files. Test cold-start from tar: `docker load < log4shell.tar && docker compose up -d`. This must work with zero internet.
- Add error boundaries to every UI panel. Panels degrade to last known state, not blank crash screens.
- Write a pre-demo checklist (6 items max) for the presenter to run 5 minutes before the judge walkthrough.

### Hours 16–19: Second CVE (Stretch Goal)

- If ahead of schedule: wire Struts S2-061 (CVE-2020-17530) as a second selectable target in the queue.
- This demonstrates Prophet generalizes: different CVE, different technology, different patch approach (version upgrade vs. env var).
- If behind schedule: skip entirely. Invest the hours in UI polish and rehearsal instead.

### Hours 19–21: Rehearsal

- Three full demo rehearsals with the presenter on the actual demo hardware.
- Time each run. Target: under 90 seconds for the core loop, under 3 minutes with Q&A simulation.
- Drill the three most likely judge challenges (see failure modes section below).
- Confirm the REPLAY fallback arc is practiced and flows identically to the live arc.

### Hours 21–23: Freeze and Pre-load

- Code freeze. No new features, no refactors.
- Start the Vulhub container. Confirm it is running and reachable. Leave it running.
- Open the UI. Confirm the queue shows Log4Shell at rank 1. Screenshot this state.
- NVD API key confirmed in `.env`. MOCK mode confirmed as fallback if API is down.

### Hour 23–24: Buffer

- Sleep, or fix the single most critical issue found in the hour 21 check.
- Do not add features.

---

## Demo Failure Modes and Mitigations

| Failure Mode | Likelihood | Mitigation |
|---|---|---|
| CISA KEV or NVD API unreachable | Medium | Pre-cached JSON snapshots in `data/`. Agent reads from cache. UI shows "Data as of [timestamp]". |
| Docker image pull times out | Medium | Images pre-pulled and saved to `.tar`. `docker load` before demo. Cold-start tested in hours 13–16. |
| Nuclei template fires false negative | Low-Medium | Confirmed working in hour 0. Backup Struts target confirmed in hour 0. Both paths tested. |
| Claude tool call schema mismatch | Low | All schemas validated end-to-end with mock adapter in hours 3–5 before any live call. |
| Context window overflow mid-loop | Low-Medium | Phase boundaries reset context with summarized prior-phase output. Each Messages call is independently bounded. |
| UI SSE stream drops | Low-Medium | UI reconnects automatically; last-known state preserved. REPLAY mode as hard fallback. |
| "Show me a CVE not in the demo" challenge | Certain | `check_nuclei_template(CVE-XXXX)` can run live in the UI in under 5 seconds. Show it. Be honest about Vulhub environment requirement for the full loop. |
| "Is the patch actually applied?" challenge | Certain | Show `docker logs` before and after in a second terminal. The "BLOCKED" badge must be backed by real Nuclei output, not a fake state change. |
| Anthropic AUP blocks a tool call | Low (with proper system prompt) | System prompt explicitly scopes to localhost sandbox. The CVP application is filed in advance. Exploitation of a localhost container against a known-vulnerable-by-design image is within the permitted dual-use category. |
| "This is just a script with Claude labels on it" | Certain | The streaming reasoning output, the human approval gate, and the live Nuclei execution + verified block are the evidence. Have Docker logs open in a second window. Show the raw agent reasoning text, not just the result cards. |

---

## What We Are NOT Building

- A novel exploit generator. Prophet selects and executes existing Nuclei templates. No new shellcode, no new CVE exploitation chains synthesized by Claude.
- A trained ML prediction model. Triage scoring is structured prompt reasoning over public signals. Not a fine-tuned classifier, not a regression model.
- A production SIEM integration. The Sigma rule is generated and syntactically valid YAML but is not loaded into a running Elastic/Splunk/Wazuh instance.
- A multi-target scanner. One CVE, one container, one loop per demo run. Parallelism is explicitly out of scope.
- Live-infra testing against any host outside localhost. The sandbox boundary is absolute.
- Custom model weights or fine-tuning. Current Stage 2 runs as deterministic Python and the hackathon demo can be operated through Codex terminal / agent-in-the-loop without a runtime AI API key.
- An ATT&CK navigator visualization. ATT&CK technique references appear as text annotations in the triage output; no interactive graph.
- Statistical validation of the prediction claim. No backtested precision/recall table is produced in 24 hours. The claim is methodological, not empirical.
- Real zero-day discovery. The sketch's "generate new zero-day" (Panel 4, Phase II) is the one item that is explicitly descoped. Legally and technically, this is the right call for a hackathon demo targeting judges, not a red team engagement.

---

## Sources

- [CISA KEV Catalog](https://www.cisa.gov/resources-tools/resources/kev-catalog) — official landing page; JSON feed URL confirmed
- [NVD API Key Announcement](https://nvd.nist.gov/general/news/API-Key-Announcement) — rate limits: 5 req/30 s without key, 50 req/30 s with key
- [NVD API Key Request](https://nvd.nist.gov/developers/request-an-api-key) — free, instant activation via email
- [FIRST.org EPSS API](https://www.first.org/epss/api) — base URL `https://api.first.org/data/v1/epss`; no auth required; batch query supported; history to 2021
- [MITRE ATT&CK STIX Data](https://github.com/mitre-attack/attack-stix-data) — v19.0 April 2026; free download; no auth
- [Exploit-DB / searchsploit](https://gitlab.com/exploit-database/exploitdb) — `searchsploit -j` for JSON output; offline-capable; daily updates
- [Nuclei Templates](https://github.com/projectdiscovery/nuclei-templates) — 1,496 KEV templates confirmed 2025; community-maintained; free
- [Vulhub](https://github.com/vulhub/vulhub) — `docker compose up -d` per CVE directory; Log4Shell and Struts confirmed
- [HackingBuddyGPT](https://github.com/ipa-lab/hackingBuddyGPT) — round-based capability architecture; capability dispatch pattern; sliding history for token management
- [Anthropic Cyber Safeguards](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude) — CVP program; dual-use security work conditionally permitted with org verification
- [EPSS Efficacy Paper (arXiv 2411.02618)](https://arxiv.org/abs/2411.02618) — less than 20% of KEV CVEs flagged above 0.5 EPSS before listing; baseline weakness that justifies Prophet's enrichment argument
- [GitHub Advisory Database](https://github.com/advisories) — GraphQL at `https://api.github.com/graphql`; free PAT, no scopes required
- [EPSS Data Stats / Model](https://www.first.org/epss/data_stats) — EPSS v4 released March 2025; daily score updates
- [Nuclei Templates Monthly May 2025](https://projectdiscovery.io/blog/nuclei-templates-monthly-may-2025) — confirmed KEV template count and cadence
