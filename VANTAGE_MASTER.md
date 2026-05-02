# VANTAGE — Master Document

> *Adversaries scatter their signals across domains. VANTAGE is the position above the noise — where the picture becomes one, and the next move becomes visible.*

**Project for:** 3rd Annual NatSec Hackathon · Shack15, San Francisco · May 2-3, 2026
**Problem statements addressed:** PS3 (Mission Command & Control) primary; PS1 (Sensor Analysis & Integration) and PS5 (General National Security) secondary.
**License:** MIT (open source per hackathon rules)

This is the canonical, all-in-one reference. If you're a new teammate joining at the kickoff happy hour, read **Part I** (the project) and **Part III** (the pitch). If you're already on board and building, **Part II** (the build) and **Part V** (TAK setup) are the working docs. **Part IV** (the military primer) is the homework that makes you sound credible to judges.

---

## Table of Contents

**Part I — The Project**
1. [TL;DR](#1-tldr)
2. [Why VANTAGE Exists — The Four Gaps](#2-why-vantage-exists--the-four-gaps)
3. [The Four Agents](#3-the-four-agents)
4. [Architecture](#4-architecture)
5. [Tech Stack](#5-tech-stack)
6. [Partner Tool Fit](#6-partner-tool-fit)

**Part II — Building It**
7. [The 60-Second Demo Arc](#7-the-60-second-demo-arc)
8. [Build Plan — 24 Hours, 4 People](#8-build-plan--24-hours-4-people)
9. [Stretch Goals — Good to Amazing](#9-stretch-goals--good-to-amazing)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Repos to Borrow From](#11-repos-to-borrow-from)
12. [TAK Integration — iTAK + FreeTAKServer + CoT](#12-tak-integration--itak--freetakserver--cot)

**Part III — Pitching It**
13. [Why VANTAGE Wins (Judging Criteria Map)](#13-why-vantage-wins-judging-criteria-map)
14. [vs Palantir — The S-2 Day-in-the-Life Comparison](#14-vs-palantir--the-s-2-day-in-the-life-comparison)
15. [Pitch Lines & Stage Talking Points](#15-pitch-lines--stage-talking-points)
16. [Future Direction — AI Battle Staff](#16-future-direction--ai-battle-staff)

**Part IV — Knowing Your Domain (Military Primer)**
17. [Structure — How the Military Is Organized](#17-structure)
18. [Doctrine — How They Plan and Fight](#18-doctrine)
19. [Intelligence — How They Know What They Know](#19-intelligence)
20. [Systems — The C2 Stack You're Competing With](#20-systems)
21. [Adversary Playbook](#21-adversary-playbook)
22. [Strategic Geography](#22-strategic-geography)
23. [The Red Lines — DoD 3000.09 and Human-in-the-Loop](#23-the-red-lines)
24. [Culture & Language](#24-culture--language)
25. [Acronym Glossary](#25-acronym-glossary)

**Part V — References & Logistics**
26. [Hackathon Logistics & Partner Resources](#26-hackathon-logistics--partner-resources)
27. [Submission Checklist](#27-submission-checklist)
28. [Sources & Sister Docs](#28-sources--sister-docs)

---

# Part I — The Project

## 1. TL;DR

VANTAGE is a multi-agent intelligence platform that turns the public-data firehose — AIS, ADS-B, news, sanctions lists, satellite imagery, cyber telemetry — into a real-time picture of what adversaries are *actually doing*. Where today's C2 systems show commanders **what is happening**, VANTAGE tells them **what is about to happen, what it means, what is being hidden, and how it all connects.**

A swarm of four specialized agents — a Forecaster, a Translator, an Unmasker, and a Synthesizer — runs continuously over live data, with the operator sitting in the human-in-the-loop seat that the AI can never bypass.

We can build a working version in 24 hours.

**The single sentence to lock in:**

> *"Today's C2 systems show commanders what's happening. VANTAGE tells them what's about to happen — and what it means."*

---

## 2. Why VANTAGE Exists — The Four Gaps

Today's C2 stack — Palantir Gotham, Maven Smart System, Anduril Lattice, ATAK — has solved sensing, fusion, and dashboarding. But operators still complain about four hard gaps:

1. **They are reactive, not predictive.** Modern systems alert *after* a vessel goes dark, *after* a flight drops off radar, *after* the convoy is hit. They don't tell you what's *about* to happen.
2. **They show data, not meaning.** Operators get raw tracks and tentative IDs. A non-expert (a commander, a cabinet secretary, a coalition partner) can't read what the data implies for *their* decision.
3. **They miss active deception.** Adversaries spoof AIS, change MMSI, switch flags, ghost their transponders, and run ship-to-ship transfers in the dark. Most "anomaly" detectors notice *absence* of signal — they don't notice *active lies*.
4. **They're siloed by domain.** Maritime tools don't talk to cyber tools don't talk to news/SIGINT. Adversaries operate across all of them at once. A coordinated probe at sea + a port-network intrusion + a state-media announcement is one operation; today's C2 sees three unrelated alerts.

VANTAGE is built around closing exactly these four gaps. Each agent maps to one gap.

---

## 3. The Four Agents

### 🔮 The FORECASTER — predicts what's about to happen
Maintains a library of "evasion patterns" mined from historical AIS/ADS-B gaps and their context. Continuously runs every tracked entity against the library using nearest-neighbor similarity on time-series features (heading volatility, owner-history, proximity to chokepoints, prior gap-frequency). When match-confidence crosses a threshold, raises a soft alert: *"Entity X likely to go dark within N minutes."*

**Demo moment:** a soft countdown timer next to a tanker — *"Predicted dark event in 00:23:14"* — and then it actually goes dark on stage. Once the judges see that happen live, you've won the round.

### 🗣️ The TRANSLATOR — explains what matters, to whom
Same evidence, different audiences. The same alert reads as:

| Audience | What they see |
|---|---|
| Tactical operator | "AIS gap, vessel 9342847, Hormuz at 27.4°N 56.8°E, ROE check requested" |
| Theater commander | "Iranian-linked tanker, sanctions hit on owner, fits ship-to-ship transfer pattern, 7th evasion this quarter" |
| Cabinet-level | "Iran is moving sanctioned crude through the Strait. ~$80M shipment. Likely buyer: China." |
| Public-facing | "An oil tanker is doing something unusual near the Strait of Hormuz." |

Built as one Codex agent with role personas. Cached completions. A single dropdown on each alert: **"Show me as ___."**

**Demo moment:** judge flips the dropdown live. Watches the same alert become actionable for four different people.

### 🎭 The UNMASKER — detects active deception
This is the one that turns judges' heads. Every other anomaly tool notices when a signal disappears. VANTAGE notices when a signal is *actively lying*.

Checks invariants the adversary cannot help breaking:
- **Kinematic plausibility** — could a ship physically have moved that far in that time?
- **Identity persistence** — has the MMSI / IMO / name been quietly changed?
- **Flag-of-convenience switches** — flag changes that precede sketchy runs by weeks
- **STS transfer signatures** — two vessels co-located, both AIS off, neither in port
- **Sensor-truth disagreement** — what AIS *claims* vs. what Danti's satellite imagery *shows*

When any invariant breaks, the Unmasker raises a flag with the specific contradiction.

**Demo moment:** side-by-side panel — *Claims* (left, white) vs. *Reality* (right, red). "Vessel claims to be 80km from here. Satellite says it's 400m off our pier."

### 🕸️ The SYNTHESIZER — connects across domains, surfaces intent
Runs a sliding temporal window across all feeds (maritime, aviation, news/GDELT, sanctions, optionally Shodan/Censys for cyber-side probes). Clusters events by time + geography + actor and asks the LLM: *"do these tell a coherent story?"* — with strong constraints to admit "no narrative" rather than confabulate.

When a story emerges, surfaces *one* unified alert that proposes the narrative and shows the receipts.

**Demo moment:** three boring individual alerts on the dashboard — a tanker incident, a port-system anomaly, a Xinhua statement. Then the Synthesizer pops up with one card: *"Possible coordinated probe — confidence 0.74"* with the four contributing events as expandable evidence. The judges understand they just saw *intent* synthesized from noise.

---

## 4. Architecture

```
                     ┌─────────────────────────────────┐
   Live data feeds → │   Ingest layer (Python async)   │
                     │   AIS · ADS-B · GDELT ·         │
                     │   OpenSanctions · Danti · news  │
                     └──────────────┬──────────────────┘
                                    │ event stream
                     ┌──────────────▼──────────────────┐
                     │      AGENT SWARM (Codex)         │
                     │                                  │
                     │   FORECASTER ─┐                  │
                     │   UNMASKER ───┼─→ alert queue   │
                     │   SYNTHESIZER ┘                  │
                     │                                  │
                     │   TRANSLATOR ← (per-audience)    │
                     └──────────────┬──────────────────┘
                                    │ structured alerts
                     ┌──────────────▼──────────────────┐
                     │     VANTAGE CONSOLE (React)      │
                     │  • Live world map (Deck.gl)      │
                     │  • Swarm activity panel          │
                     │  • Audience dropdown             │
                     │  • Evidence drill-down           │
                     │  • Human-in-the-loop gate        │
                     │  • CoT publisher → TAK Server    │
                     └─────────────────────────────────┘
```

Tools (Danti, OpenSanctions, AIS history, satellite imagery) wrapped as **MCP servers** so any agent can call any tool. Each agent has a structured-output schema (Pydantic) and a hard 8-second timeout with a fallback path. Memory is a small SQLite-backed event store that persists across investigations so the swarm can recognize repeat-offender patterns.

---

## 5. Tech Stack

**Core**
- Python 3.12 async backend (FastAPI + Server-Sent Events for live updates)
- React + TypeScript console (Vite, Tailwind, shadcn/ui)
- Deck.gl + Mapbox GL for the live world map
- SQLite (event store) + Qdrant (vector memory)
- OpenAI Agents SDK for the swarm orchestration
- MCP Python SDK for tool wrappers

**Data**
- AIS firehose: aishub.net + MarineCadastre historical
- ADS-B: OpenSky Network public API
- News: GDELT 15-min event feed + NewsAPI
- Entities: OpenSanctions + Wikidata grounding
- Geo intel & satellite: Danti
- Optional cyber: Shodan, Censys

**Models**
- OpenAI Codex / GPT-class for agents (per hackathon partner access)
- `sentence-transformers` (all-MiniLM-L6-v2) for cheap semantic clustering
- `scipy.spatial` for nearest-neighbor pattern matching

---

## 6. Partner Tool Fit

| Partner | Role in VANTAGE | Why it matters |
|---|---|---|
| **OpenAI Codex** | Powers the four agents; written in JSON-schema'd ReAct loops | Built for exactly this; partner access removes the cost question |
| **Danti** | Geospatial intel + satellite imagery for the Unmasker | Underused by other teams = differentiation; gives Unmasker its punch line |
| **Palantir AIP** | (Optional) ontology + dashboard if a teammate is fluent | Fastest path to enterprise polish; skip if Foundry's learning curve eats too much time |

**Honest call:** for a 24-hour build, prioritize Codex + Danti + open stack. Add Palantir AIP only if a team member already knows Foundry — otherwise Workshop's learning curve will burn 6-8 hours you can't afford.

**Sign up tonight (before doors):**
- Palantir free dev tier — `https://signup.palantirfoundry.com/signup?signupPermitCode=NAT_SEC_HACKATHON`
- Codex access form (linked in the hacker-resources packet) — required + has pre-work
- Danti access form (linked in the hacker-resources packet)

---

# Part II — Building It

## 7. The 60-Second Demo Arc

1. **Open with a live world map.** Thousands of vessels and aircraft moving in real time. Mention this is real data, right now.
2. **The Forecaster ticks.** A tanker in the Strait of Hormuz gets a soft countdown — *"predicted dark event in 23 min."*
3. **It happens.** Vessel goes dark on stage. Forecaster confidence ratchets up.
4. **The Unmasker overlays.** A separate panel: *Claims* vs. *Reality*. Owner-on-paper says one thing; OpenSanctions says another. Kinematics impossible.
5. **The Synthesizer connects.** A second alert from the cyber feed (a port-system probe at Fujairah) joins the maritime alert, plus a Xinhua release about "freedom of navigation." One card pops: *"Likely coordinated probe — 0.74."*
6. **The Translator switches voices.** Judge picks "show me as cabinet secretary." The same alert becomes one paragraph the SecDef would actually read.
7. **The human gate.** Operator must accept or reject the synthesized alert before it propagates. *"Nothing happens without human sign-off."*
8. **Close:** *"Built in 24 hours. Running on real data. Open source."*

Total: 60 seconds. Three "holy shit" moments (the predicted dark event, the deception unmask, the cross-domain narrative). Judges remember.

**If you've added the TAK integration (recommended):** between steps 7 and 8, hold up a phone running iTAK and show the same alert appearing as a Cursor-on-Target event on a real military-grade tactical client. *"And it shows up natively in the TAK ecosystem operators already use."* That is the credibility flex of the round.

---

## 8. Build Plan — 24 Hours, 4 People

### Hour 0-4 · Scaffolding (everyone)
- Repo stand-up, Codex access confirmed, Danti account live
- Data feeds connected and streaming to a local event log
- Bare React shell with map and an empty alert panel

### Hour 4-12 · Pillars in parallel
- **Person 1 — Forecaster.** Pattern-mining script over historical AIS gaps; nearest-neighbor matcher; Codex agent wrapper with confidence calibration.
- **Person 2 — Unmasker.** Kinematic + identity invariant checkers; Danti integration for sat-imagery cross-check; "Claims vs. Reality" panel.
- **Person 3 — Synthesizer + Translator.** Sliding-window event clustering; LLM narrative proposer with strict "no story" fallback; audience-persona translator.
- **Person 4 — Console + demo.** React map, swarm activity panel with live agent traces, audience dropdown, evidence drill-down. **Owns the demo script and rehearses it five times.**

### Hour 12-18 · Integration + agent debate panel
- All four agents publishing to one alert queue
- Visible agent reasoning trace on the right side of the console
- Pre-load three "hero scenarios" with cached real data so demo timing is deterministic
- Wrap external tools as MCP servers

### Hour 18-22 · Polish + scenario cache
- Smooth out the demo path — every click should feel intentional
- Pre-cache evidence packets for the three hero alerts
- Build a "live mode" / "demo mode" toggle so a quiet data window can't kill the pitch
- README, repo polish, license, GitHub public

### Hour 22-24 · Submission + dry runs
- Record the 1-minute demo video required for submission
- Push all dependencies, write quickstart, verify clean clone works
- Three full demo dry runs against a cold console

---

## 9. Stretch Goals — Good to Amazing

VANTAGE on its baseline is solid. Here are five upgrades, ranked by bang-per-hour, that push it from *good* to *amazing*. Each survives independently if the others fail.

### 9.1 The ADVERSARY — a fifth agent (1.5 hours)
A red-team agent that role-plays the opponent and proposes their likely next move. *"If I were Iran, having just gone dark in Hormuz, here's what I'd do in the next 24 hours and why."* When the Adversary and Forecaster agree on a prediction, confidence goes through the roof. Adversarial multi-agent reasoning is hot 2026 research; no one else at the hackathon will have it.

### 9.2 Time-Machine validation (2 hours)
Pre-load a real historical incident — Houthi attack on the *Galaxy Leader*, Iranian seizure of *MSC Aries*, an actual Chinese maritime militia standoff. Run VANTAGE against the data from *before* the event. Show VANTAGE correctly predicting it hours before it happened. Closest thing to undeniable proof. Judges go from "interesting" to "holy shit" in three seconds.

### 9.3 CoT → ATAK / iTAK on a real phone (1 hour)
Every VANTAGE alert publishes as a Cursor-on-Target event into a TAK Server. Bring an iPhone running iTAK to the demo. Watch alerts pop up on the phone next to the laptop, in proper military symbology. **Single biggest credibility flex with military judges in the room.** Setup details in [Section 12](#12-tak-integration--itak--freetakserver--cot).

### 9.4 Multilingual OSINT ingestion (3 hours)
Add Russian Telegram, Chinese Weibo, Farsi news to your sources. Auto-translate via Whisper/Codex. VANTAGE becomes a *global* awareness system instead of an English-bubble OSINT tool. This is Vannevar's moat in miniature.

### 9.5 Counter-AI mode (1 hour, even if just a slide)
Adversaries will start using GANs to fabricate fake AIS tracks, fake satellite imagery, fake news content. Have the Unmasker include a "synthetic signal" check — frequency-domain artifacts in spoofed AIS, statistical fingerprints of fabricated news. Even one slide about this in the pitch makes you look 18 months ahead of competitors.

### 9.6 Bonus theatrics (sub-hour each)
- **3D globe instead of flat map** — `react-globe.gl`. Same data, dramatically better visual.
- **Sound design** — soft tone for Forecaster ticks, sharper one for Unmasker catches, chord for Synthesizer connections. Sensory layering aids memory.
- **Voice-driven Q&A** — judge asks VANTAGE a question with their voice, VANTAGE responds. Whisper + TTS.
- **Auto-generated OPORD-format brief** — at end of demo, VANTAGE outputs a one-page operations order in proper five-paragraph format. Officers in the room will recognize the format instantly.

### 9.7 What to AVOID adding
- **Custom finetuned model** — Vannevar's full-time job; you won't do it well in 24 hours.
- **Hardware demo on a Raspberry Pi** — cinematic but networking demos break.
- **A second hero region** — Hormuz is enough. Mention extensibility, don't build it.
- **Anything that requires another partner integration tonight** — Codex + Danti + maybe AIP is plenty.

### 9.8 If I had 6 extra hours
1. The Adversary agent (1.5h) — biggest depth upgrade per line of code
2. Time-Machine validation on a real Houthi event (2h) — undeniable proof
3. CoT → ATAK on a phone (1h) — biggest flex with military judges
4. 3D globe instead of flat map (1h) — pure visual upgrade
5. Sound design + one voice-Q&A query (0.5h) — sensory layer

When you walk out of judging and another team asks *"what made yours different?"* — they should be able to point at a specific thing they remember. **The Adversary agent. The Houthi prediction. The phone running iTAK. The globe.** Each one is a memory hook.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Live data is too quiet during demo | "Live mode" / "demo mode" toggle with three pre-cached hero scenarios |
| LLM hallucinates a narrative | Synthesizer prompt forces "no narrative" output when evidence is thin; show source receipts on every claim |
| Agent latency stalls demo | 8-second hard timeout per agent; fallback to last-known-good; pre-warm model contexts |
| Unmasker triggers false positive on stage | Use historically-validated dark-vessel cases for the demo; show the kinematic math, not just the verdict |
| Looks like "ChatGPT for generals" | The four-agent swarm trace panel makes the work visible. Show debate, show tool calls, show evidence trails. |
| Scope creep into Battle Staff territory | Stay disciplined: this hackathon = the four pillars only. Battle Staff is the "what we'd build next" slide. |
| TAK integration breaks because phone & laptop aren't on the same Wi-Fi | Use phone hotspot. Test the day before. |
| Judge asks "how is this not Palantir?" | Use the day-in-the-life script in [Section 14](#14-vs-palantir--the-s-2-day-in-the-life-comparison). |

---

## 11. Repos to Borrow From

### Top 8 to clone first
1. **[OpenAI Agents SDK](https://github.com/openai/openai-agents-python)** — production multi-agent framework. The cleanest fit for the four-agent swarm.
2. **[pyais](https://github.com/M0r13n/pyais)** — pure-Python AIS message parser. Ten lines and you have a live tanker feed.
3. **[Microsoft GraphRAG](https://github.com/microsoft/GraphRAG)** — LLM-powered entity-graph extraction. Backbone for the Synthesizer.
4. **[dump1090](https://github.com/antirez/dump1090)** — ADS-B Mode S decoder.
5. **[Kepler.gl](https://github.com/keplergl/kepler.gl)** / **[Deck.gl](https://github.com/visgl/deck.gl)** — geospatial visualization.
6. **[OpenSanctions](https://github.com/opensanctions/opensanctions)** — entity grounding for vessel owners and operators.
7. **[milsymbol](https://github.com/spatialillusions/milsymbol)** — MIL-STD-2525 / NATO APP-6 military symbology, drop into any map.
8. **[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)** — wrap each data source as a tool any agent can call.

### TAK / CoT ecosystem
- **[FreeTAKServer](https://github.com/FreeTAKTeam/FreeTakServer)** — the OSS TAK Server. Pip-installable.
- **[goATAK](https://github.com/kdudkov/goatak)** — lightweight Go-based ATAK server alternative.
- **[node-cot](https://github.com/dfpc-coe/node-cot)** — Cursor-on-Target encoder/decoder.

### Multi-agent frameworks (pick one)
- **[OpenAI Agents SDK](https://github.com/openai/openai-agents-python)** *(recommended for VANTAGE — pairs with Codex)*
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — graph-based multi-agent
- **[Microsoft AutoGen](https://github.com/microsoft/autogen)** — debate patterns
- **[CrewAI](https://github.com/crewAIInc/crewAI)** — role-based personas
- **[smolagents](https://github.com/huggingface/smolagents)** — minimal code-writing agents
- **[Pydantic AI](https://github.com/pydantic/pydantic-ai)** — structured outputs

### Knowledge graph & viz
- **[Neo4j Community](https://github.com/neo4j/neo4j)** / **[Memgraph](https://github.com/memgraph/memgraph)** — graph databases
- **[react-force-graph](https://github.com/vasturiano/react-force-graph)** / **[Sigma.js](https://github.com/jacomyal/sigma.js)** — graph visualization
- **[react-globe.gl](https://github.com/vasturiano/react-globe.gl)** — 3D globe (stretch goal)

### Sensor fusion (defense pedigree)
- **[stone-soup (UK DSTL)](https://github.com/dstl/Stone-Soup)** — multi-target tracking + sensor fusion. Cite this in your README and judges raise an eyebrow.
- **[FilterPy](https://github.com/rlabbe/filterpy)** — Kalman / particle filters.

### Cyber & RF anomaly (PS4 adjacent)
- **[Falco](https://github.com/falcosecurity/falco)**, **[Suricata](https://github.com/OISF/suricata)**, **[Zeek](https://github.com/zeek/zeek)** — network anomaly / IDS.

A fuller list with categories and caveats lives in `repo_explore.md`.

---

## 12. TAK Integration — iTAK + FreeTAKServer + CoT

### What TAK is, in 60 seconds
**Tactical Assault Kit** is the lingua franca of military situational awareness. ATAK on Android, iTAK on iPhone, WinTAK on Windows. Used by Special Forces, conventional infantry, fire/rescue, SWAT, FEMA. Think of it as the iMessage of military operations — every operator on the network sees the same shared map of friendlies, enemies, objectives.

The protocol is **Cursor on Target (CoT)**, an XML schema invented by MITRE in 2002. Every event is *what / when / where* — simple enough for low-bandwidth radio links, expressive enough for any tactical entity.

### Why VANTAGE emits CoT
- TAK is what operators actually use.
- If VANTAGE alerts emit as CoT, they appear natively on every TAK device on the network — soldier's phone, command-post laptop, drone operator's tablet.
- For the demo, holding up a phone running iTAK with VANTAGE alerts popping up live is the strongest possible "we get the deployed ecosystem" signal.

### Setup tonight (about an hour total)

**Step 1 — iTAK on iPhone (10 min)**
- Install iTAK from App Store (TAK Product Center, free).
- First launch: pick a callsign (`VANTAGE-01`), team color (cyan), role (HQ).
- Skip the server config — use solo mode to explore the UI.
- Long-press the map to drop a marker; pinch to zoom; open chat panel; place a contact icon.

**Step 2 — Spin up FreeTAKServer (15 min)**
```bash
pip install FreeTAKServer --break-system-packages
# follow the README quickstart at https://github.com/FreeTAKTeam/FreeTakServer
```
Default ports: 8087 (SSL), 8089 (TCP), 8088 (web UI/dashboard). Open the dashboard in a browser to confirm it's alive.

**Step 3 — Connect iTAK to your laptop (5 min)**
- Same Wi-Fi network for phone and laptop.
- iTAK → Settings → Network → Add Server.
- Use your laptop's local IP, port `8089`, protocol `TCP`. (SSL needs cert provisioning; skip for hackathon.)

**Step 4 — Send a test CoT (10 min)**
A 20-line Python script that opens a TCP socket to FreeTAKServer and shoots one CoT XML message. If it works, a custom map icon appears on the iPhone within seconds. Pseudo-code:
```python
import socket, datetime
cot_xml = f"""<?xml version='1.0' standalone='yes'?>
<event version='2.0' uid='vantage-test-001' type='a-h-S' how='m-g'
       time='{datetime.datetime.utcnow().isoformat()}Z'
       start='{datetime.datetime.utcnow().isoformat()}Z'
       stale='{(datetime.datetime.utcnow()+datetime.timedelta(minutes=10)).isoformat()}Z'>
  <point lat='26.5' lon='56.3' hae='0' ce='10' le='10'/>
  <detail><contact callsign='SOTHYS-DARK'/></detail>
</event>"""
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.42', 8089))   # your laptop's IP
sock.send(cot_xml.encode())
```
Type `a-h-S` is "atom, hostile, sea-surface" — a red diamond on the map. Use `a-f-S` for friendly (cyan), `a-u-S` for unknown (yellow).

**Step 5 — Wire VANTAGE alerts (during build)**
Every alert from the swarm queue gets one line: publish a CoT event to the TAK Server. Use red for high-confidence Unmasker hits, yellow for low-confidence Synthesizer narratives. Now alerts appear in iTAK live.

### Gotchas
- iTAK won't see FreeTAKServer if your phone and laptop aren't on the same network. Hotel/coffee-shop "guest" Wi-Fi often blocks peer discovery — use your phone's hotspot.
- Port 8089 is plain-text TCP. Fine for demo. Don't run this in production.
- Default callsign/team colors render cyan friendly. Your VANTAGE alerts should emit red hostile or yellow unknown depending on confidence — clear visual differentiator.

---

# Part III — Pitching It

## 13. Why VANTAGE Wins (Judging Criteria Map)

| Criterion | Weight | VANTAGE's answer |
|---|---|---|
| **Technical Demo** | 35% | Working system on real live data. Three "holy shit" demo moments in under 60 seconds. Visible multi-agent trace. With TAK stretch goal: a real military client showing alerts in real time. |
| **Military Impact** | 30% | Closes the four hardest gaps in current C2 (predictive · contextualization · deception · cross-domain). Every gap is a documented operator pain point. Hits PS3 directly, with reach into PS1 and PS5. |
| **Creativity** | 25% | Four-agent swarm with visible debate, audience-aware translation, and active-deception detection are all under-explored. The "Claims vs. Reality" Unmasker pattern is fresh. |
| **Presentation** | 10% | "Today's C2 systems show commanders what's happening. VANTAGE tells them what's about to happen — and what it means." One sentence, locked in. |

---

## 14. vs Palantir — The S-2 Day-in-the-Life Comparison

This is the killer pitch material. When a judge asks *"how is this different from Palantir?"*, the day-in-the-life comparison wins the room.

### Setting
A battalion S-2 (intelligence officer, captain or major) in CENTCOM. AOR includes the Strait of Hormuz. Job: produce the morning intelligence brief for the commander, then push real-time updates as things change.

### A morning with Palantir Gotham + AIP

**0500** — arrives at the battalion TOC. Logs into Gotham on the SIPR terminal. Desktop client takes ~30 seconds to load.
**0510** — opens the overnight intel reports queue: 47 unread documents. Skims headlines, flags six for deep read.
**0530** — needs Iranian shadow-fleet activity overnight. Constructs Gotham query: vessel entities tagged `shadow_fleet`, last activity in past 24h, AOR overlapping Hormuz. Fourteen vessels return; three look notable.
**0600** — for each notable vessel: clicks into the entity, walks the ownership graph, opens the imagery layer, scrolls through linked reports, copies key data points into a notes file. Five to ten clicks per vessel. Twenty minutes for three ships.
**0630** — opens AIP, asks: *"Summarize maritime activity in Hormuz past 24 hours, focus on sanctioned entities."* Gets a paragraph. Reads carefully — missed one vessel he found by hand, hallucinated a connection. Has to verify everything.
**0700** — pulls everything into PowerPoint. Four slides. Last-minute formatting fixes.
**0730** — battalion morning brief. *"Sir, here's the maritime picture for the last 24 hours. Three vessels of interest, two likely conducting sanctions evasion."* Brief is already three hours stale by the time it lands.
**1000** — imagery comes in: a vessel has just gone dark. Back into Gotham. New query. New cross-reference. Manual update, pinged report.

This pattern repeats all day. **Every event = manual investigation + manual brief update.** The S-2 spends most of their time wrangling data, not exercising judgment.

### The same morning with VANTAGE

**0500** — arrives at the TOC. Opens laptop. VANTAGE has been running overnight, agents continuously processing AIS, ADS-B, news, and sanctions feeds.
**0501** — VANTAGE dashboard greets the S-2 with three priority alerts ranked by composite confidence × impact:

> **🔴 ALERT 1 · Confidence 0.84** — Iranian-linked tanker (M/V Sothys) went dark in Strait of Hormuz at 0234L. **Forecaster** predicted the dark event 47 minutes prior. **Adversary** suggests STS transfer at 26.5°N 56.3°E within 18 hours. **Translator** has draft narratives in tactical, theater, cabinet, and public registers.

> **🟡 ALERT 2 · Confidence 0.61** — Iranian government Falcon 50 (EP-IGB) ADS-B pattern: Tehran → Damascus → Sana'a in past 36 hours. **Synthesizer** correlated with three Houthi spokesman statements timed within ±2 hours of each leg.

> **🔴 ALERT 3 · Confidence 0.91** — Vessel claiming to be Cook-Islands-flagged "Berkeley" emerged near Fujairah at 0410L. **Unmasker** flags identity flip: kinematic profile, AIS history, and SAR imagery match yesterday's "Sothys" — same hull, different paperwork. Deception confirmed.

**0520** — S-2 expands each alert, reviews the agent reasoning trace, accepts Alert 1 and Alert 3, kicks Alert 2 to a watchlist.
**0540** — clicks **Generate Morning Brief**. VANTAGE emits a one-page OPORD-format document. S-2 reviews, edits, tags two items for commander attention.
**0700** — battalion morning brief. No PowerPoint. One page in hand.

> *"Sir, three things. One — Iranian shadow-fleet vessel went dark in Hormuz overnight, high confidence sanctions evasion, 18-hour STS window opens at 1000Z. Two — low-confidence pattern of Iranian official aviation timing with Houthi messaging, flagged for follow-up. Three — we caught a vessel running an identity flip, kinematic evidence is irrefutable."*
>
> Commander: *"What do you recommend?"*
>
> *"Sir, recommend tipping NAVCENT on Alert 1, kicking Alert 2 to theater J-2, and forwarding Alert 3 to the legal team for sanctions enforcement referral."*

**0730** — brief is done. Commander has actionable picture in 30 minutes instead of three hours. S-2 spent that time on **judgment**, not query construction.

### Side-by-side, by task

| What the S-2 needs to do | With Gotham + AIP | With VANTAGE |
|---|---|---|
| Get situational awareness at start of shift | Build queries, read 47 reports, manually cross-reference, ~90 min | Read three pre-ranked alerts, ~10 min |
| Investigate a specific anomaly | Open entity, walk graph, open imagery, 5-10 clicks | Click alert; the four-agent investigation already ran |
| Cross-domain correlation | Manually open four tools, often missed | Synthesizer surfaces unified narratives automatically |
| Detect adversary deception | Implicitly — only if S-2 happens to look | Explicitly — Unmasker runs invariant checks continuously |
| Predict next adversary move | S-2 intuition | Forecaster + Adversary agent propose explicitly |
| Brief the commander | Build PowerPoint, ~45 min, stale by delivery | Auto-generated OPORD-format one-pager, real-time |
| Translate for non-experts | Manually re-write for the secretary/coalition partner | Translator emits four audience versions automatically |
| Time from event to operator awareness | Hours | Seconds to minutes |

### The honest version (don't hide this from judges)
VANTAGE is not a Palantir replacement.
1. Gotham's ontology is the product of 20 years of work integrating heterogeneous classified data sources. VANTAGE operates on the OSINT subset. For deep classified all-source work, the S-2 still needs Gotham.
2. VANTAGE is decision support, not authoritative record. The documentary trail still lives in Gotham.
3. **The best deployment is hybrid.** VANTAGE consumes Foundry as one of its data sources via MCP. Palantir holds the data; VANTAGE does the autonomous analysis. *Together, they outperform either alone.*

This honesty is a strategic asset. Judges respect builders who scope their claims accurately. *"We don't replace Palantir, we orchestrate it"* is much stronger than *"we beat Palantir."*

---

## 15. Pitch Lines & Stage Talking Points

### The single locked-in sentence
> *"Today's C2 systems show commanders what's happening. VANTAGE tells them what's about to happen — and what it means."*

### Variants for different judge questions

**"What sets you apart from Palantir?"**
> *"Palantir is a tool an analyst uses. VANTAGE is a co-worker that uses tools. Different category, different user. We don't replace Palantir — we sit between Palantir and the commander."*

**"With Palantir, the S-2 spends 90 minutes building the picture. With VANTAGE, the S-2 reads three alerts and spends that 90 minutes thinking."**

**"What about Anduril Lattice?"**
> *"Lattice fuses what's visible. Maven targets what it sees. VANTAGE finds what's actively being hidden, predicts what's coming, and connects the dots across domains."*

**"Is this 3000.09-compliant?"**
> *"Yes. VANTAGE is a human-in-the-loop decision-support system. We do not engage targets. Every alert ships with an evidence trail and a human authorization gate."*

**"How do you handle hallucination?"**
> *"Two layers. Every alert ships with source receipts — clickable evidence. And the Synthesizer is prompted with a strict 'no narrative' fallback when evidence is thin. We'd rather miss a story than confabulate one."*

**"What's the moat against Palantir adding this?"**
> *"AIP is moving in this direction, true. The differences that persist: we're agent-native from the ground up, not a chat layer on an enterprise platform. We're open-source and laptop-deployable in minutes, not classified-network-only with six-month onboarding. And we're built for non-analysts — commanders, staffers, secretaries — by default."*

**The talk-like-a-pro lines (drop one in every answer)**
- *"VANTAGE is OSINT-leaning all-source fusion that delivers indications and warnings without waiting for classified collection."*
- *"We're not replacing the kill chain — we're compressing the early steps so the commander's decision happens inside the adversary's loop."*
- *"VANTAGE is built for the S-2 to give the commander a synthesized intelligence picture before the morning brief — not for the operator to stare at a screen."*
- *"The fight isn't kinetic — it's gray zone. VANTAGE is built to see five disconnected events as one operation."*
- *"Our hero demo runs over the Strait of Hormuz because that's where the gray-zone playbook is most active right now."*

---

## 16. Future Direction — AI Battle Staff

VANTAGE is the **awareness** layer. The natural extension is the **planning** layer.

The U.S. Army uses a formal planning ritual called **MDMP** (Military Decision Making Process) — seven steps from receipt of mission to orders production, run by a battle staff organized into specialized sections (S-1 personnel, S-2 intelligence, S-3 operations, S-4 logistics, S-5 plans, S-6 communications/cyber). Real staffs spend 8-72 hours running this.

The v2 of VANTAGE builds an AI agent for each staff section. They consume VANTAGE's intelligence layer (the four pillars) and produce three ranked courses of action with risk profiles, sustainment requirements, and intelligence gaps. The commander gets not just *what's happening and why*, but *here are three ways to respond, ranked.*

**For the hackathon: this is the "what we'd build next" slide.** Don't try to build it. Mention it. Tease it. Show the slide and move on.

**The clean user story to tell from stage:**

> *"S-2 uses VANTAGE to compress hours of intelligence prep into seconds — predictive, deception-aware, narrative-grade. S-3 walks into the planning meeting with that picture already in hand and spends their time on what only they can do: deciding how to respond."*

---

# Part IV — Knowing Your Domain (Military Primer)

This part is the homework that makes you sound credible to judges. Eight modular sections + a glossary. Each section has its own TL;DR, key concepts, "why this matters for VANTAGE" callout, and a "talk like a pro" line you can drop into your pitch.

---

## 17. Structure
*How the U.S. military is organized*

### TL;DR
The military is structured along three axes at once: **service** (Army, Navy, Air Force, Marines, Space Force, Coast Guard), **geography** (combatant commands like CENTCOM and INDOPACOM), and **echelon** (units that nest from squad up through corps). Most of your conversations about VANTAGE will involve a battalion-or-above commander supported by a staff of 4-12 officers, each of whom owns one slice of the picture.

### The branches
- **Army** — ground force, biggest by headcount.
- **Navy** — ships, carriers, submarines, naval aviation.
- **Air Force** — aircraft, missiles, bulk of intelligence platforms.
- **Marines** — light, fast, expeditionary; under Department of the Navy.
- **Space Force** — newest branch, owns satellites and orbital domain.
- **Coast Guard** — under DHS in peacetime, Navy in wartime; matters a lot for the maritime gray zone.

### Combatant commands (geographic ones)
- **CENTCOM** — Middle East and Central Asia. *The Hormuz scenario in your demo is CENTCOM's lane.*
- **INDOPACOM** — Indo-Pacific. The biggest, the most strategically loaded.
- **EUCOM** — Europe (Russia, Ukraine, NATO).
- **AFRICOM**, **NORTHCOM**, **SOUTHCOM** — Africa, North America, Latin America.
- Functional: **SOCOM** (special ops), **STRATCOM** (nuclear), **CYBERCOM** (cyber), **TRANSCOM** (logistics), **SPACECOM** (space).

### Unit hierarchy (Army terms)
A **squad** (~10) → **platoon** (~30) → **company** (~100) → **battalion** (~600) → **brigade** (~3-5k) → **division** (~15k) → **corps** (~50k+).
The level you'll most often address with VANTAGE is **battalion** or **brigade** — that's where commanders need synthesized decision support.

### Ranks (simplified)
- **NCOs** (sergeants, E-5 to E-9) — experienced backbone.
- **Junior officers** (lieutenants, captains, O-1 to O-3) — first leadership roles.
- **Field grades** (major, lieutenant colonel, colonel, O-4 to O-6) — battalion and brigade commanders. *Primary "user" archetype.*
- **Flag officers** (general, admiral, O-7 to O-10) — theater commanders, joint chiefs. *"Pitch to the secretary" archetype.*

### The staff sections — *very important for VANTAGE*

| Section | Owns |
|---|---|
| **S-1** | Personnel, admin |
| **S-2** | **Intelligence** — enemy, terrain, weather. *This is where VANTAGE lives.* |
| **S-3** | **Operations** — current fight, COA development |
| **S-4** | Logistics, sustainment |
| **S-5** | Plans (longer horizon) |
| **S-6** | Communications, signals, cyber |

S- at battalion/brigade. G- at higher Army echelons. N- in Navy. A- in Air Force. J- for joint.

### Why this matters for VANTAGE
You're building a tool that a battalion S-2 uses to prepare a briefing that informs a battalion commander's decision. Every demo should make clear *which person you're helping* and *what decision they're making*.

### Talk like a pro
> *"VANTAGE is built for the S-2 to give the commander a synthesized intelligence picture before the morning brief — not for the operator to stare at a screen."*

---

## 18. Doctrine
*How they plan and fight*

### TL;DR
Three concepts cover 80% of what you'll hear: the **OODA loop** (basic decision cycle), the **kill chain** (canonical sequence from "we see something" to "we hit it and assess"), and **MDMP** (formal staff planning process). Modern doctrine obsesses over **tempo** — being faster than the adversary's loop. VANTAGE's pitch is *we compress the loop.*

### The OODA loop (Boyd, 1970s)
**O**bserve → **O**rient → **D**ecide → **A**ct. Repeat. The side that completes the loop faster — and *gets inside* the adversary's loop — wins. Modern doctrine talks about **tempo** (rate and rhythm relative to the enemy), not just raw speed.

### The kill chain (F2T2EA)
**F**ind → **F**ix → **T**rack → **T**arget → **E**ngage → **A**ssess.
- Find — detect that something is there
- Fix — pin down where it is
- Track — keep custody as it moves
- Target — decide it's worth hitting and prepare
- Engage — actually use force
- Assess — battle damage assessment

SOF variant: **F3EAD** (find, fix, finish, exploit, analyze, disseminate).
Modern story: "kill chain compression" — shrinking time from Find to Engage from hours to minutes. *Maven Smart System exists to do this.*

### MDMP — Military Decision Making Process
Seven steps: receipt of mission → mission analysis → COA development → COA wargaming → COA comparison → COA approval → orders production. Real staffs run this in 8-72 hours. The "AI Battle Staff" extension of VANTAGE automates this. **"COA"** = Course of Action.

### Rules of Engagement (ROE)
Legal/policy guardrails on when force can be used, against whom, how much. **Standing ROE** = peacetime baseline. **Supplemental ROE** = mission-specific. Every engagement has to be ROE-compliant.

### CONOPS / OPORD
- **CONOPS** — the high-level concept of operations.
- **OPORD** — formal five-paragraph order: Situation, Mission, Execution, Service Support, Command & Signal.

### Why this matters for VANTAGE
VANTAGE compresses the OODA loop *for the commander's staff.* The Forecaster and Synthesizer collapse "Observe" and "Orient" from hours to seconds. The Translator collapses "brief the commander" from minutes to one paragraph. The Unmasker resists adversary attempts to corrupt the "Observe" step. You hand off "Decide" to the human; "Act" is downstream.

### Talk like a pro
> *"We're not replacing the kill chain. We're compressing the early steps — find, fix, track — so the commander's decision happens inside the adversary's loop."*

---

## 19. Intelligence
*How they know what they know*

### TL;DR
Intelligence is divided by collection method (the "INTs"), processed through a five-step **intelligence cycle**, and the holy grail is **all-source** fusion. The most important conceptual distinction for VANTAGE is **track vs. identity**: a sensor blip says *"something is here,"* but knowing *what* it is requires correlation. Most C2 systems are great at tracks and weak at identity.

### The INTs

| Acronym | What it is | Example |
|---|---|---|
| **HUMINT** | Human intelligence | Source in foreign port reports a sanctioned shipment |
| **SIGINT** | Signals & comms | Intercepted radio between adversary ships |
| **IMINT** | Imagery (sat, aerial, drone) | Satellite photo of a tank column |
| **GEOINT** | Geospatial — maps, terrain | Heatmap of incidents along a route |
| **OSINT** | Open source — news, social, public DBs | Bellingcat-style investigation |
| **MASINT** | Measurement & signature | Submarine acoustic fingerprint |
| **FININT** | Financial — banking, sanctions | OpenSanctions hit on vessel owner |
| **CYBINT** | Cyber telemetry, malware | Detection of port-system intrusion |

### The intelligence cycle
Tasking → Collection → Processing → Analysis → Dissemination → Feedback. VANTAGE accelerates the **processing → analysis → dissemination** legs.

### "All-source"
Aspirational state where you fuse every INT into one coherent picture. Palantir Gotham and Maven exist to chase this. **VANTAGE is an all-source synthesizer that emphasizes OSINT-leaning sources.**

### Track vs. identity (the critical distinction)
- A **track** is a sensor blip — *something is at these coordinates*.
- An **identity** is the answer to *what is it?* — a specific vessel, a known unit, a particular person.
- The hardest problem in modern C2 is identity assignment: an operator drowning in tracks but unable to confidently identify which ones matter.
- VANTAGE's Unmasker doesn't just confirm tracks — it *disputes* them.

### Indications and Warnings (I&W)
The intelligence discipline of detecting precursors of adversary action. Inherently predictive. **Your Forecaster pillar is essentially an automated I&W system.**

### Why this matters for VANTAGE
You are an OSINT-heavy all-source synthesizer that produces I&W-grade outputs. Each data source maps to an INT — AIS/ADS-B (OSINT/MASINT-flavored), news/GDELT (OSINT), Danti satellite imagery (IMINT/GEOINT), OpenSanctions (FININT). This vocabulary places you on the existing intelligence map immediately.

### Talk like a pro
> *"VANTAGE is OSINT-leaning all-source fusion that delivers indications and warnings without waiting for classified collection."*

---

## 20. Systems
*The C2 stack you're competing with*

### TL;DR
Five names cover 90%: **Palantir** (Gotham/Foundry/AIP/Maven), **Anduril** (Lattice), **ATAK/TAK**, **Vannevar** (intel analysis), **Shield AI** (autonomy). Each owns part of the picture. **VANTAGE lives in the gaps between them.**

### Palantir
- **Gotham** — original intelligence platform. Ontology-driven. Used by IC since post-9/11. Strong at link analysis, weak at NL query.
- **Foundry** — broader data platform.
- **AIP** — LLM layer (2023). Got DIA / classified-network accreditation for GPT-class models in late 2024 (genuinely new).
- **Maven Smart System (MSS)** — Palantir-built AI targeting/fusion engine. Now CJADC2 cornerstone, transitioning to formal program of record.

### Anduril Lattice
Mesh-networked, AI-first C2. Recently won a multi-billion-dollar Army enterprise contract. Designed for "mosaic warfare." Big assumption: persistent connectivity (breaks under jamming).

### ATAK / WinTAK / CivTAK + TAK Server
- **ATAK** — Android Tactical Assault Kit. Phone-based COP for ground units.
- **WinTAK** — Windows desktop equivalent.
- **CivTAK** — civilian-released version.
- **TAK Server** — federated comms/data backend.
- **CoT** (Cursor on Target) — open XML schema. Lightweight enough for crappy radio. *If VANTAGE emits CoT, our alerts appear natively in any TAK device on the network.*

### Vannevar Labs — Decrypt
Gen-AI for foreign-language intelligence. Deployed across many DoD sites. 10x analyst throughput. **Lesson: domain-finetuned models beat generic LLMs on military analysis.**

### Shield AI / Hivemind
Autonomy SDK for unmanned platforms. Lives at platform-control layer, *downstream* of C2.

### CJADC2
**Combined Joint All-Domain Command and Control** — the DoD's modernization umbrella. CENTCOM has deployed minimum viable capability since spring 2024. Most modern AI defense programs justify themselves under CJADC2.

### Where VANTAGE fits
- **Lattice** fuses what's visible. **VANTAGE** finds what's hidden.
- **Maven** detects targets. **VANTAGE** predicts adversary moves and surfaces intent.
- **Vannevar** analyzes intel after the fact. **VANTAGE** synthesizes intent in real time.
- **ATAK** is the operator's window. **VANTAGE** can emit alerts as CoT into that window.
- **CJADC2** is the umbrella. VANTAGE is the awareness layer that feeds it.

### Why this matters for VANTAGE
You will be asked, on stage, *"how is this different from Lattice?"* and *"why doesn't Palantir do this?"* Be able to name Lattice, Maven, and Gotham without hesitation, place VANTAGE in the gap, and demonstrate you've thought about why no incumbent has built it yet.

### Talk like a pro
> *"Lattice fuses what's visible and Maven targets what it sees. VANTAGE finds what's actively being hidden, predicts what's coming, and connects the dots across domains."*

---

## 21. Adversary Playbook

### TL;DR
Modern adversaries operate in the **"gray zone"** — actions short of war, designed to achieve strategic effects without triggering a kinetic response. The toolkit: **AIS spoofing, GPS jamming, flag-of-convenience switches, shell-company ownership, shadow fleets, influence operations, cyber probes, proxy violence.** VANTAGE is purpose-built to detect these.

### Gray zone
Aggressive activities that stay below the threshold of armed conflict. Examples: Russian "little green men" in Crimea, Chinese maritime militia in South China Sea, Iranian proxy militias, state-attributed ransomware. Strategic logic: chip away without giving the adversary a clean *casus belli*.

### Hybrid warfare
Coordinated mix of military, cyber, information, economic, proxy. Russia-Ukraine is the textbook case. **The Synthesizer pillar exists because hybrid warfare is multi-domain by design.**

### Maritime gray zone — the VANTAGE sweet spot
- **Sanctions evasion** — moving cargo past Western sanctions.
- **The "shadow fleet"** — opaque-ownership tankers used by Iran, Russia, North Korea, Venezuela. Hundreds of vessels, possibly more than a thousand since 2022.
- **AIS spoofing** — broadcasting a false position.
- **AIS dark periods** — turning off the transponder. Common before STS transfers.
- **STS (ship-to-ship) transfers** — meeting at sea to transfer cargo, often with both AIS off.
- **Flag-of-convenience switches** — re-flagging in lax-jurisdiction registries.
- **MMSI / IMO / name changes** — quietly altering identifiers between voyages.

### Aviation gray zone
- ADS-B spoofing (rarer but documented)
- Dropping off radar near sensitive airspace
- Civil aircraft used for surveillance
- Dual-use commercial drone proliferation

### Information operations
- State-affiliated media coordinated with operational tempo
- Social-media astroturfing
- Disinformation injected into adversary OSINT feeds (real concern for systems like VANTAGE)

### Cyber probes
- DDoS timed with operations
- Probes against port and logistics IT
- Pre-positioning malware in critical infrastructure

### Concrete recent examples (use in your demo)
- **Houthi attacks in the Red Sea / Bab-el-Mandeb** (2023-ongoing) — civilian shipping under missile/drone attack.
- **Russian Black Sea fleet** — Ukrainian USVs attacking Russian warships.
- **Iranian shadow fleet** — sanctions-evading oil exports, IRGC Navy seizures.
- **Chinese maritime militia in South China Sea** — fishing fleets as paramilitary, Second Thomas Shoal standoffs.
- **Severed undersea cables in the Baltic** (2023-ongoing) — attributed to Russian/Chinese vessels.

### Why this matters for VANTAGE
**Every demo example you give should pull from this world.** Maritime gray zone is the sweet spot — public data, named adversaries, fresh news cycle. Use real ship names, real chokepoints, real sanctioning regimes. **Specificity is credibility.**

### Talk like a pro
> *"The fight isn't kinetic — it's gray zone. Adversaries spoof, lie, switch flags, and time their cyber and info ops to maritime moves. VANTAGE is built to see all of that as one operation, not five disconnected events."*

---

## 22. Strategic Geography

### TL;DR
The world has a small number of strategically loaded places. Know the **theaters**, the **chokepoints**, and the **adversary forward areas**. For VANTAGE's hero demo, pick **one** region (probably Hormuz) and stay there.

### Theaters and what's contested
- **Indo-Pacific (INDOPACOM)** — China rising, Taiwan flashpoint, North Korea unstable, South China Sea contested island-building. *Biggest US strategic concern of the next decade.*
- **Middle East (CENTCOM)** — Iran nuclear and conventional pressure, Iranian proxies, Israel ongoing conflicts, Syria/Iraq fragmented.
- **Europe (EUCOM)** — Russia-Ukraine war, NATO eastern flank, Baltic and Black Sea incidents, Arctic militarization.
- **Africa (AFRICOM)** — multiple coups (Sahel), Russian/Wagner footprint, terrorism in Horn of Africa.
- **Latin America (SOUTHCOM)** — narcotics flows, Venezuelan instability.
- **Arctic** — accelerating Russian and Chinese activity, ice-route opening.

### Maritime chokepoints — memorize

| Chokepoint | Why it matters | Adversary angle |
|---|---|---|
| **Strait of Hormuz** | ~20-30% of global oil trade | Iran can mine / harass. *Primary VANTAGE demo zone.* |
| **Bab-el-Mandeb** | Suez approaches | Houthi attacks, Iranian-backed |
| **Suez Canal** | Europe-Asia shortcut | Egyptian sovereignty; *Ever Given* 2021 |
| **Strait of Malacca** | China's main oil route; ~25% of global trade | Chinese chokepoint anxiety drives Belt & Road |
| **Taiwan Strait** | TSMC, China-Taiwan | Most strategically loaded body of water on earth |
| **South China Sea** | Disputed islands, $3T+ annual trade | Chinese island-building, Philippine standoffs |
| **Bosphorus / Dardanelles** | Russian Black Sea access | Turkish control, Montreux Convention |
| **English Channel** | NATO/UK lifeline | Russian shadow shipping, undersea cable risk |
| **Bering Strait** | Arctic gateway | Russia/China Arctic posture |

### Key US bases (just enough)
**Diego Garcia** (Indian Ocean), **Guam** (Pacific), **Bahrain** (5th Fleet HQ), **Ramstein** (Germany), **Yokosuka/Sasebo** (Japan), **Camp Humphreys** (Korea, biggest overseas base).

### Why this matters for VANTAGE
Pick **one** region for your hero demo. **Strongly recommend Hormuz / Bab-el-Mandeb.** Public data, recent incidents, named adversaries. Mention extensibility to South China Sea, Black Sea, Baltic. Avoid invented countries or hypothetical scenarios. **Real ship + real chokepoint + real ownership trail = irrefutable credibility.**

### Talk like a pro
> *"Our hero demo runs over the Strait of Hormuz because that's where the gray-zone playbook is most active right now. The architecture extends to the Taiwan Strait and the Black Sea without code changes."*

---

## 23. The Red Lines
*DoD Directive 3000.09 and human-in-the-loop*

### TL;DR
The most important policy document for any AI defense product is **DoD Directive 3000.09 (Autonomy in Weapon Systems)**, originally 2012, updated January 2023. Three regimes: **in-the-loop**, **on-the-loop**, **out-of-the-loop**. **The line between getting deployed and getting killed by reviewers is whether you respect this doctrine.**

### The three regimes

| Regime | What it means | Where it's allowed |
|---|---|---|
| **Human-in-the-loop** | AI recommends; human authorizes each action | Default for lethal force |
| **Human-on-the-loop** | AI selects and engages; human can override | Time-critical defense (counter-UAS, point defense) |
| **Human-out-of-the-loop** | AI acts alone | Heavily restricted; not authorized for strategic targets |

### Why "human-in-the-loop" is a religion
1. **Ethics** — broad consensus that machines must not autonomously decide to kill.
2. **Legality** — every engagement has to be ROE/LOAC-compliant. AI cannot be held legally accountable; commanders can.
3. **Practicality** — AI is wrong sometimes. Cost of a wrong target is asymmetric.

### What the 2023 update changed
Streamlined senior-leader review. Explicitly allowed human-on-the-loop for defensive systems where "system speed exceeds human cognitive speed." Did not relax constraints on offensive lethal autonomy.

### The JAG bottleneck
A **Judge Advocate General officer** reviews targeting packages for ROE/LOAC compliance. Often the real bottleneck in modern kill chains — not technical processing, but waiting for legal review.

### Why this matters for VANTAGE
- **Never claim autonomy.** Always show the human gate.
- Frame the AI as **augmentation**, not replacement.
- Build in **explainable rationale** for every recommendation.
- Show the **audit trail** — every alert has receipts.
- If anyone asks "is this 3000.09-compliant?" the answer is *"yes, we're a human-in-the-loop decision-support system; we do not engage targets."*

### Talk like a pro
> *"VANTAGE is fully aligned with DoD 3000.09 — the system is decision support, not weapons employment. Every recommendation has an evidence trail and a human authorization gate."*

---

## 24. Culture & Language
*How to sound like you belong*

### TL;DR
Military culture rewards **brevity, directness, and respect for hierarchy.** Acronym density is high but you only need ~30. Time and date formats are different. Biggest cultural sin: overclaiming experience. Biggest cultural win: acknowledging what you don't know while showing you've done the homework.

### How they talk
- **Laconic.** Short sentences, no fluff.
- **Direct.** "Here's the situation, here's what I need." No buried qualifiers.
- **Hierarchical.** Sir/ma'am is universal in formal contexts.
- **Comm-check phrases.** "How copy?" "Over." "Out." (Don't say both — *over* means continue, *out* means done.)

### Time and date formats
- **Time:** 24-hour clock, no colon. *1430* not *14:30*. Time zone often a single letter — *Z* for Zulu/UTC, *L* for local.
- **Date:** Day-Month(abbrev)-Year. *02MAY26* not *5/2/2026*.

### Cardinal sins
- **Calling a Marine a "soldier."** Soldiers are Army. Marines are Marines.
- **"The Pentagon decided X."** The Pentagon is a building. The decision was made by SecDef, OSD, the Joint Chiefs, or a specific service.
- **Calling AI "autonomous"** without qualification. Triggers 3000.09 alarm bells.
- **Overclaiming military experience.** If you haven't, don't pretend.
- **Using "killchain" casually.** It's a serious term tied to lethal force.

### Fast credibility wins
- **Name a real adversary system.** *"We're not trying to clone Lattice."*
- **Use a chokepoint correctly.** *"Hormuz"* not *"the Iran area."*
- **Distinguish strategic / operational / tactical.** Strategic = national, years. Operational = theater, months. Tactical = unit, hours-days.
- **Reference DoD 3000.09 by number.**
- **Acknowledge what you don't know.** *"I'm not a military operator, so I'd want to validate this assumption with someone who is."*

### What to do if you don't know something on stage
*"That's a great question. I don't know the precise answer, but here's how I'd think about it — and I'd want to validate with the operator community before deploying."* This response wins. Bullshitting loses.

### Why this matters for VANTAGE
You will be in a room with people who genuinely speak this language. Goal: *respect* them, communicate clearly, make obvious you've done the homework. **Officers love builders who try to learn. They despise builders who pretend.**

### Talk like a pro
> *"I'm a builder, not an operator — I built VANTAGE by talking to people who do this for a living and reading enough doctrine to know what I don't know. Here's what we built and why."*

---

## 25. Acronym Glossary

| Acronym | Meaning |
|---|---|
| AIS | Automatic Identification System (maritime transponder) |
| ADS-B | Automatic Dependent Surveillance-Broadcast (aviation transponder) |
| AOR | Area of Responsibility |
| ATAK | Android Tactical Assault Kit |
| BDA | Battle Damage Assessment |
| C2 | Command and Control |
| CJADC2 | Combined Joint All-Domain Command and Control |
| COA | Course of Action |
| COP | Common Operational Picture |
| CoT | Cursor on Target (data schema) |
| CONOPS | Concept of Operations |
| ELINT | Electronic Intelligence |
| F2T2EA | Find, Fix, Track, Target, Engage, Assess |
| GEOINT | Geospatial Intelligence |
| HUMINT | Human Intelligence |
| IMINT | Imagery Intelligence |
| ISR | Intelligence, Surveillance, Reconnaissance |
| I&W | Indications and Warnings |
| JAG | Judge Advocate General (legal officer) |
| LOAC | Law of Armed Conflict |
| MASINT | Measurement and Signature Intelligence |
| MDMP | Military Decision Making Process |
| MSS | Maven Smart System |
| OODA | Observe, Orient, Decide, Act |
| OPORD | Operations Order |
| OSD | Office of the Secretary of Defense |
| OSINT | Open-Source Intelligence |
| RF | Radio Frequency |
| ROE | Rules of Engagement |
| SIGINT | Signals Intelligence |
| SOCOM | Special Operations Command |
| SOF | Special Operations Forces |
| STS | Ship-to-Ship (transfer) |
| TAK | Tactical Assault Kit (the broader ecosystem) |
| TOC | Tactical Operations Center |
| UAS / UAV | Unmanned Aerial System / Vehicle |

---

# Part V — References & Logistics

## 26. Hackathon Logistics & Partner Resources

### Event basics
- **Where:** Shack15, 2nd floor of the Ferry Building, San Francisco. Overnight access.
- **Wi-Fi:** SHACK15_Members / M3mb3r$4L!f3
- **Kickoff happy hour:** May 1 (tonight), 5pm PT, Stanford. Register via Luma link in resources packet.
- **Day 1 (May 2):** 0900 doors → 1145 hacking starts → 1300 lunch → 1900 dinner → 2200 doors close (no reentry).
- **Day 2 (May 3):** 0900 doors → 1200 submissions due → 1215 first round → 1410 finalists demo on stage → 1515 winners → 1600 doors close.
- **Submission form:** https://cerebralvalley.ai/e/3rd-annual-natsec-hackathon/submit

### Rules to remember
- Public GitHub repo at submission.
- All work started from scratch during the hackathon.
- Teams up to 4.
- Project must fit one of the five problem statements.
- Submit a 1-minute demo video (YouTube/Loom).

### Prizes
1st $20K · 2nd $12K · 3rd $8K · 4th $6K · 5th $4K (provided by U.S. Army).

### Partner resources to set up TONIGHT
- **Palantir AIP free dev tier** — `https://signup.palantirfoundry.com/signup?signupPermitCode=NAT_SEC_HACKATHON`
- **Palantir hardware (CASK)** — for PS1/PS2; not needed for VANTAGE
- **OpenAI Codex access form** — required for our agent swarm; has pre-work (linked in resources packet)
- **Danti access form** — geospatial intel; sign up tonight

### OSINT firehose
- DEFCON inspiration scrape: https://defcon-inspiration.cerebralvalley.ai/
- Network/Internet monitoring: https://shodan.io
- AI OSINT search: https://exa.ai
- AIS shipping data: https://www.aishub.net
- Historical AIS API: https://developer.barentswatch.no/docs/AIS/historic-ais-api/
- Vessel traffic dump: https://hub.marinecadastre.gov/pages/vesseltraffic
- Flight tracking: https://www.flightradar24.com
- Viz tools: https://kepler.gl, https://deck.gl
- Simulated hardware: https://wokwi.com

### Judging
- **Technical Demo 35%** · **Military Impact 30%** · **Solution Creativity 25%** · **Presentation & Pitch 10%**
- Round 1: ~3 min pitch + 1-2 min Q/A in groups
- Final round: top 6 teams demo on stage to a panel, ~3 min + 2-3 min Q/A
- **Show what you built. Do not show a presentation.** (They literally said this in writing.)

### Contacts
- Questions: ray@cerebralvalley.ai or Discord
- Codex/Danti questions: joshb@cerebralvalley.ai
- Discord: https://discord.com/invite/xgEaYSfZ2x

---

## 27. Submission Checklist

- [ ] GitHub repo public (MIT license file in root)
- [ ] README with quickstart (`make demo` or equivalent runs the pre-cached hero scenarios)
- [ ] 1-minute demo video uploaded to YouTube/Loom
- [ ] All teammates listed in submission form
- [ ] Problem statement: PS3 (Mission Command & Control)
- [ ] Submission form filled out: https://cerebralvalley.ai/e/3rd-annual-natsec-hackathon/submit
- [ ] If using TAK stretch goal: phone charged and tested with FreeTAKServer the night before final demo
- [ ] Three full demo dry runs against a cold console
- [ ] Pitch lines from [Section 15](#15-pitch-lines--stage-talking-points) memorized

---

## 28. Sources & Sister Docs

### Primary doctrine and policy
- [DoD Directive 3000.09 (autonomy in weapons)](https://www.dau.edu/blogs/new-dod-directive-300009-autonomy-weapon-systems)
- [F2T2EA Kill Chain — Wikipedia](https://en.wikipedia.org/wiki/Kill_chain_(military))
- [F3EAD SOF Targeting](https://sofsupport.org/f3ead-sof-specific-targeting-in-the-intelligence-cycle/)
- [Mosaic Warfare — DARPA](https://www.darpa.mil/news/features/mosaic-warfare)

### Programs and systems we mention
- [CJADC2 progress 2025 — GovConWire](https://www.govconwire.com/articles/cjadc2-progress-areas-beginning-2025-dod)
- [CENTCOM JADC2 deployment — DefenseScoop](https://defensescoop.com/2024/04/03/centcom-jadc2-deploy-minimum-viable-capability/)
- [Maven Smart System — DefenseScoop](https://defensescoop.com/2025/05/23/dod-palantir-maven-smart-system-contract-increase/)
- [Anduril $20B Army contract — Army Recognition](https://www.armyrecognition.com/news/army-news/2026/u-s-army-awards-20b-anduril-to-deploy-lattice-ai-open-architecture-for-battlefield-integration/)
- [Anduril Lattice C&C](https://www.anduril.com/lattice/command-and-control)
- [Palantir Foundry / Gotham / AIP](https://www.palantir.com/platforms/foundry/)
- [Vannevar at Talisman Sabre 2025](https://www.vannevarlabs.com/blog/2025/09/09/deploying-agentic-ai-at-talisman-sabre-25/)
- [MIT Tech Review — Anduril AI demo](https://www.technologyreview.com/2024/12/10/1108354/we-saw-a-demo-of-the-new-ai-system-powering-andurils-vision-for-war/)

### TAK / CoT
- [Cursor on Target — FreeTAK docs](https://freetakteam.github.io/FreeTAKServer-User-Docs/About/architecture/mil_std_2525/)
- [FreeTAKServer GitHub](https://github.com/FreeTAKTeam/FreeTakServer)
- [CivTAK](https://www.civtak.org/)

### Open data (the firehose VANTAGE drinks from)
- [aishub.net AIS feed](https://www.aishub.net/)
- [MarineCadastre vessel traffic](https://hub.marinecadastre.gov/pages/vesseltraffic)
- [OpenSky Network ADS-B](https://opensky-network.org/)
- [GDELT global event database](https://www.gdeltproject.org/)
- [OpenSanctions](https://www.opensanctions.org/)
- [ACLED](https://acleddata.com/)

### Open-source tools we depend on
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [pyais](https://github.com/M0r13n/pyais)
- [dump1090](https://github.com/antirez/dump1090)
- [Microsoft GraphRAG](https://github.com/microsoft/GraphRAG)
- [Kepler.gl](https://github.com/keplergl/kepler.gl) / [Deck.gl](https://github.com/visgl/deck.gl)
- [milsymbol](https://github.com/spatialillusions/milsymbol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [stone-soup (UK DSTL)](https://github.com/dstl/Stone-Soup)

### Sister docs in this folder
- `README.md` — the project README (VANTAGE spec, lighter version of this master doc)
- `LOOM_operators_manual.md` — military primer (an earlier draft, content folded into Part IV here)
- `S2_workflow_comparison.md` — the day-in-the-life Palantir vs. VANTAGE doc (folded into Section 14)
- `repo_explore.md` — full curated repo list (longer than Section 11)
- `PS3_brainstorm_brief.md` — original PS3 research that led to VANTAGE

This master doc supersedes the others where they overlap. Use the sisters as deep-dives when you need them.

---

## Final note

VANTAGE wins the hackathon if three things are true on Sunday at 1410:

1. **The demo runs.** Three "holy shit" moments in 60 seconds. A predicted dark event, an unmasked deception, a synthesized cross-domain narrative.
2. **The pitch lands.** *"Today's C2 systems show commanders what's happening. VANTAGE tells them what's about to happen — and what it means."*
3. **The team is credible.** Talk-like-a-pro lines drop naturally. The DoD 3000.09 question gets a clean answer. No one calls a Marine a soldier.

Everything in this document serves those three outcomes. Build for them.

Now go win.
