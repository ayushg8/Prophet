# Prophet — Presentation Script

> Judge-facing talk track for the 3rd Annual National Security Hackathon (PS4 — Digital Defense and Cybersecurity).
> Two versions: a 60-second submission cut and a 3–4 minute live pitch.
> Stay non-actionable. No exploit steps, no raw scrape content, no live-target naming.

---

## Mission statement (use verbatim if asked)

**Prophet predicts cyber attacks before they happen and ships the defense in the same loop.** It fuses geopolitical signals with an exploit-class predictor to answer three questions at once — *when* the strike window opens, *how* the adversary will strike, and *what exploit class* they will use — then generates the patch and the Sigma detection rule before the campaign runs.

---

## 60-second version (submission video)

> Target: 150–160 spoken words. One breath per paragraph.

**[0:00–0:08] Hook.**
Twenty-nine percent of the vulnerabilities in CISA's Known Exploited list were weaponized on or before disclosure day. Federal mandates require patching them. Defenders are reactive by structure.

**[0:08–0:22] What Prophet does.**
Prophet inverts that. Geopolitical signals tell us *when* a strike window opens and *how* an adversary will strike. An exploit-class predictor tells us *which* class they will reach for. One agent loop generates the patch and a Sigma detection rule before the adversary's day zero.

**[0:22–0:48] Demo glance.**
On the Console you see a strike window dated against a real diplomatic event, a strike vector class, and a ranked CVE candidate. We approve. The agent reasons in the open, validates against an isolated sandbox, and emits a patch plus a Sigma rule. Re-run shows blocked.

**[0:48–1:00] Why it matters.**
This is "left of boom" for cyber — predict, validate, defend in one loop, runnable on a forward-deployed edge kit. National defense moves from rear-view to forward-looking.

---

## 3–4 minute live version

> Target: ~520–600 spoken words. Pause beats marked with `…`. Slide/Console cues in **[brackets]**.

### 1. Open — the timing problem (0:00–0:30)

**[Slide: KEV stat overlaid on a campaign timeline]**

Defenders today live on the right side of "boom." A vulnerability is weaponized, observed in the wild, listed in CISA's KEV catalog, and only then patched. Twenty-nine percent of KEV entries were exploited *on or before* the day they were disclosed. EPSS — the industry's forecasting score — missed more than eighty percent of those entries above its own confidence threshold before they were listed.

Federal mandate BOD 22-01 requires every Federal Civilian Executive Branch agency to remediate KEV entries on a clock. DoD weapons platforms, defense-industrial-base contractor networks, and critical-infrastructure operators run the same software. The clock starts after the adversary already moved.

Reactive defense isn't a discipline problem. It's a structural one.

### 2. The Prophet inversion (0:30–1:10)

**[Slide: three-component diagram — Forecaster → Exploit Engine → Console]**

Prophet flips the timing. Three components, one loop.

The **Forecaster** ingests geopolitical signals — diplomatic calendars, conflict indicators, sanctions activity, official advisories — and fuses them with a historical campaign corpus of how state-class adversaries have behaved in similar windows. It outputs two things: a **strike window** with a date range and a confidence score, and a **strike vector class** describing the adversary's most likely tradecraft for that window. Sector-level only. Never named live targets.

Every forecast has to answer three linked questions, not one: **why this exploit, why now, why this adversary.** A state actor only burns a high-value exploit when the geopolitical payoff justifies the burn. Prophet triangulates all three.

The **Exploit Engine** takes a CVE candidate and the forecast, predicts the **exploit class** the adversary would reach for, and produces a deterministic localhost sandbox artifact under policy. Same agent run, it generates a **zero-day defense**: a patch primitive and a Sigma detection rule. The public demo never writes or runs a novel exploit; it shows validated fixture evidence, not live target activity.

The defense lands in two places. The system gets the patch and the rule. The defender team gets an early alert — "this is the vector to watch in this window." Even when the patch can't be applied immediately for operational reasons, the SOC posture has already shifted.

The **Console** is where the loop becomes legible. Strike window on a timeline, strike vector ranked alongside historical analogies, the agent's reasoning streamed live, and the defense artifacts at the end.

### 3. The scraper — how we collect without burning ourselves (1:10–1:40)

**[Slide: scraper isolation boundary diagram]**

Collection is the most dangerous part of any system that touches geopolitical chatter. We isolate it three ways.

First, the scraper runs on a **dedicated, sacrificial machine** — never the dev box, never the demo machine. Tor misconfigurations cannot deanonymize the team's primary laptop.

Second, **only sanitized records cross the boundary** back to the Forecaster. The validator is an allowlist: it strips raw text, handles, invite links, onion addresses, credentials, and any field not on the schema. The main box never sees a raw artifact.

Third, **we lead with open, official feeds** — CISA KEV, NVD, FIRST EPSS, vendor PSIRTs, federal advisories, public threat-research RSS. Higher-risk lanes — onion landing-page metadata, public Telegram channel metadata — are catalogued but disabled by default and gated on explicit human review and VM-only execution. Nothing in the catalog references real channel names, onion addresses, or victim lists.

The output is one shape: sanitized JSONL with sector-level tags and analyst-safe summaries. That's all the Forecaster ever sees.

### 4. Demo — the loop on screen (1:40–3:00)

**[Console: PreflightChecklist green, TriageQueue populated]**

Pre-flight is green. Forecaster fixtures are loaded, the sandbox image is up, and the agent has its scope locked to localhost.

**[Click a strike window on `StrikeWindowTimeline`]**

Window one: a ten-day band tied to a real diplomatic event in May 2026. Confidence medium, sixty-seven. Two historical analogies — long-dwell pre-positioning against US perimeter infrastructure, and a real edge-appliance campaign against VPN gateways. Trigger signals: a bilateral summit and an edge-appliance pre-positioning pattern.

**[Click strike vector `vec_1` on `ForecastPanel`]**

Vector one: edge-appliance initial access and persistence. Sector scope: federal civilian, defense contractors, and critical-infrastructure perimeter services. The defensive implication is what matters here — *which* control fails first under this class of access.

**[Click the top CVE in the triage queue, hit Approve on `ApprovalGate`]**

The Exploit Engine runs. Reasoning streams into `AgentStream` — you can see every tool call, every check, every citation. The sandbox returns "vulnerable." The agent generates the **patch primitive** — a single environment variable in this case — and a valid Sigma rule that detects the precursor to this class of access.

**[Re-run shows BLOCKED, DefencePanel renders patch + Sigma]**

Same request after patch is applied: blocked. Sigma rule rendered as YAML. Total wall-clock: under two minutes from forecast to defense. Nothing fabricated. Every state change is traceable in the agent log.

### 5. Why this matters (3:00–3:30)

**[Slide: BOD 22-01 → DoD/DIB → CASK edge kit]**

Three reasons this matters for national defense.

One, the **mandate is real**. BOD 22-01 makes KEV remediation a compliance obligation across the federal civilian branch, and DoD platforms inherit the same software stack. Prophet pushes the patch left of the listing.

Two, **the demo has a resilient fixture path**. The forecast, validation artifact, defense panels, evidence bundle, and integration handoff files run from golden JSON and deterministic localhost sandbox output. Approved private integrations can enrich the same contract later without changing the default product surface.

Three, **same structure scales**. Today the demo replays historical KEV entries. The same loop ingests new exploit candidates as soon as the Exploit Engine emits them. We don't ship a one-CVE trick; we ship the loop.

### 6. Close (3:30–3:50)

Prophet runs today as an operator-in-the-loop Codex terminal workflow with deterministic fixtures for the stage demo. Production scope can swap in approved private integrations and stronger agent runners without changing the contract. The ask is simple: a forward-looking defense posture for the systems federal mandate already covers, with the patch and the detection rule co-generated in the same loop.

Predict the strike. Generate the defense. Ship before the campaign runs.

That's Prophet.

---

## Things to never say on stage

- "Zero-day discovery" / "we find new vulnerabilities." We replay disclosed KEV entries against vulnerable-by-design sandboxes. The novelty is the loop, not the exploit.
- Specific named live targets, real victim names, channel names, onion addresses, or operator handles.
- Exploit steps, payload syntax, or anything resembling a how-to.
- "100% accurate" or any unbounded confidence claim. The Forecaster emits ranked confidence; respect it.

## Phrases to keep crisp

- "Strike window" — *when*. Ranked, dated, with confidence.
- "Strike vector" — *how*. Class-level adversary tradecraft.
- "Exploit class" — *what*. The CVE family the Exploit Engine predicts.
- "Zero-day defense" — patch primitive + Sigma rule generated in the same loop.
- "Left of boom" — the framing. Forward-looking, not rear-view.

## Judge-challenge ammo (one-liners)

- *"Is the patch real or are you faking the badge?"* — "Open the evidence bundle, sandbox artifact, validation summary, and SHA-256 hashes. The state transition is recorded in the artifact contract, not just the UI."
- *"How is this different from XBOW or NodeZero?"* — "They find and validate. They don't predict ahead of KEV listing, and they don't co-generate the patch in the same loop. Prophet does both."
- *"What about a CVE not in your demo?"* — "The public pilot path is fixture-backed. New customer scenarios become approved metadata, policy, and sandbox-profile work before they enter the demo."
- *"How do you not leak when scraping?"* — "Isolated machine, sanitization at the boundary, allowlist validator. Open feeds first, high-risk lanes off by default and gated on human review."
- *"Give me a non-cyber example of why timing matters."* — "Strait of Hormuz. An adversary disables naval communications infrastructure right before targeting an isolated ship — comms down, no help inbound, dead in the water. The exploit is only worth burning when the geopolitical window makes the target reachable and isolated. That's the same logic Prophet applies to perimeter infrastructure during diplomatic windows."
