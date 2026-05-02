# Project Prophet — High-Level Technical Writeup

> Compiled 2026-05-02 from the partner's whiteboard sketch (`research/PROJECT_PROPHET_SKETCH.md`) and two parallel research passes (`research/PROPHET_competitive_landscape.md`, `research/PROPHET_policy_risk.md`). Feasibility report still inbound.

## Did I understand the sketch? Yes.

Quick replay of what I read off the whiteboard, panel by panel, so you can correct me before we build on it:

- **Panel 1 — "Zero day exploits."** Three software inputs (A, B, C) flowing into a "System" that gets X'd by zero-day defects. Annotation **"predict defects"** is the thesis. Named bits: **Mythos**, **Anthropic**, **Claude plugin layer**, **Maven** (likely Palantir Maven, given the OODA-loop framing).
- **Panel 2 — "CISA."** Two grounding datasets: **CVE** (historical corpus) and **KEV** (Known Exploited Vulnerabilities — written "KVE" in the sketch but unambiguous from context).
- **Panel 3 — "Build."** A 4-stage pipeline (I→II→III→IV) glued to two work-tracks: prompt scaffolding + presentation. Flow: hypothesis/reduction → simulation → defence simulation → block → scale.
- **Panel 4 — "Technical / Greek plan."** Same four phases, restated more concretely: **(I)** gather strategic intel; **(II)** generate new zero-day exploit; **(III)** simulate exploit + lock down virtual system; **(IV)** detect, block, enable, scale. KEV features feed in at the front.

One thing the policy/risk research surfaced that's worth flagging: **"Mythos" is almost certainly Anthropic's *Claude Mythos Preview* model**, which sits behind Project Glasswing — a restricted frontier model for autonomous zero-day discovery (announced April 2026, ~11 named partners, $100M credit pool). Access is gated and not available via standard API. We should **not** claim to use it. We use the public Claude API under the Cyber Verification Program. If the partner intended Glasswing access, that's a months-long partnership process and a separate conversation.

## What it is, in one paragraph

Project Prophet is a Claude-orchestrated agent loop that uses CISA's CVE corpus and KEV catalog as a forward-looking signal — not the rear-view mirror everyone else uses them as — to **predict the next class of vulnerability that will be weaponized**, **generate a candidate exploit against a sandboxed vulnerable-by-design target**, and **co-generate the corresponding patch/detection rule in the same agent run**. The novelty is the closed loop: predict → exploit → defend → validate, with KEV grounding the prediction and Claude orchestrating the four phases. The output we surface is the prediction score, the exploit class label, the patch diff, and the sandbox validation result — never raw exploit code.

## Architecture (logical)

```
                 ┌────────────────────────────────────────────┐
                 │ INTEL LAYER                                │
                 │  CISA KEV  ·  NVD CVE 2.0  ·  EPSS v4      │
                 │  MITRE ATT&CK · GitHub GHSA · ProjectDisc. │
                 └──────────────────────┬─────────────────────┘
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
              ┌───────────────────────┐   ┌───────────────────────┐
              │ I. PREDICTOR          │   │ Sandbox Substrate     │
              │ Claude reasons over   │   │ vulhub / Metasploit3 /│
              │ KEV history features  │   │ DVWA / Juice Shop in  │
              │ (CWE, CPE, time-to-   │   │ network-isolated docker│
              │ KEV, EPSS) → ranks    │   │ compose; ephemeral    │
              │ likely-next classes   │   │ per run, no egress    │
              └───────────┬───────────┘   └───────────┬───────────┘
                          │                           │
                          └────────────┬──────────────┘
                                       ▼
                       ┌──────────────────────────────┐
                       │ II. EXPLOIT-GEN (sandbox)    │
                       │ Claude (CVP-authorized) +    │
                       │ MCP tools, scoped to a single│
                       │ named vuln-by-design target  │
                       │ — output never persisted raw │
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │ III. DEFENCE CO-GEN          │
                       │ patch diff + Sigma rule +    │
                       │ Snort/Suricata sig + WAF rule│
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │ IV. VALIDATE & SCALE         │
                       │ re-run exploit vs patched    │
                       │ target → expect block;       │
                       │ emit signed report + audit   │
                       │ log; fan out across classes  │
                       └──────────────────────────────┘
```

## Component breakdown

| Layer | Component | Tech | Notes |
|---|---|---|---|
| Intel | KEV ingest | CISA `known_exploited_vulnerabilities.json` | daily refresh; ~3,600 entries |
| Intel | CVE ingest | NVD CVE API 2.0 | rate-limited; cache locally |
| Intel | Exploit-likelihood scoring | EPSS v4 (FIRST.org) | baseline to beat |
| Intel | Threat-actor mapping | MITRE ATT&CK STIX | optional Phase IV enrichment |
| Predictor | Reasoning model | Claude Opus 4.7 (or Sonnet 4.6) via Anthropic API | requires CVP authorization |
| Predictor | Feature pipeline | Python | CWE, CPE, vendor, time-to-KEV deltas as inputs |
| Sandbox | Vulnerable target | vulhub, Metasploitable3, DVWA, Juice Shop, retired HTB | Docker compose, ephemeral |
| Sandbox | Network isolation | docker network + host iptables egress block | demo-able to judges |
| Exploit-gen | Tool use | Claude + MCP servers | scoped tools only |
| Defence-gen | Patch surface | unified diff + Sigma + Snort + WAF rule | machine-emit, human-readable |
| Validation | Re-attack runner | sandboxed pytest harness | pass = patch blocks exploit class |
| Orchestration | Agent loop | parallel CLI workers (tmux pattern) | borrow Bilawal's pattern |
| UI | Dashboard | React/TS — reuse `vantage-console/` if integrating | predict→defend timeline view |

## The wedge (why this is real)

Three legs that no shipping product currently combines:

1. **Predict** — KEV-grounded forecasting of which vulnerability *class* surfaces next. Today's market: VulnCheck is faster than CISA at confirming KEV membership, EPSS scores 30-day exploitation probability — both still backward-looking. No one uses KEV as a *training signal* to predict the next class.
2. **Exploit-gen** — sandboxed zero-day generation. XBOW, NodeZero, Pentera, Hadrian all do this for *finding*, not for *predicted classes*; NodeZero explicitly bans GenAI from exploit execution.
3. **Defend-co-gen** — patch + detection rule produced in the same loop. Qualys Agent Val (Mar 2026) chains exploit-validation to remediation but doesn't *generate* either. APPATCH and SAN2PATCH (USENIX 2025) generate patches but stand alone from exploit-gen.

The window before incumbents close it: **12–18 months**, plausibly less. Qualys Agent Val and TrendAI+Anthropic AESIR (Apr 2026, on Claude Opus 4.7) are converging on the same loop from opposite directions.

## What we cannot do, and what to do instead

**Cannot:** generate genuine novel zero-days against production software in 24 hours; that's a months-long fuzzing-infra problem.

**Do instead:** **Replay 3–5 historical KEV entries**. Withhold post-disclosure context, run Prophet against the pre-disclosure information, show the predictor would have flagged the class days/weeks before KEV publication, generate the exploit class + patch, validate in sandbox. This is falsifiable, demo-able in 60 seconds, and structurally identical to the production loop — just with known answers as ground truth.

## Hackathon-shaped MVP (24h target)

Mirroring the format of `UI_LAUNCH_PLAN.md` so it's easy to slot alongside VANTAGE:

| Hour | Build |
|---|---|
| 0–1 | Scaffold repo (or branch off VANTAGE); apply for Anthropic CVP; spin Docker sandbox skeleton |
| 1–3 | Ingest KEV JSON, NVD CVE 2.0; pick 3 historical KEV entries as the demo set |
| 3–5 | Predictor agent: feature pipeline + Claude prompt; verify it would have ranked the demo classes high pre-disclosure |
| 5–8 | Exploit-gen (sandbox-only) for one demo class, against a vulhub container; logs scrubbed |
| 8–10 | Defence-gen: patch diff + Sigma rule + Suricata sig |
| 10–12 | Validator: re-run exploit against patched container, expect block; signed audit log |
| 12–16 | UI dashboard — predict→defend timeline + per-step evidence drawer |
| 16–20 | Add 2 more demo classes; rehearse 60-second demo arc |
| 20–24 | Polish, fallback (replay-only) demo path if sandbox flakes |

## Critical guardrails (non-negotiable)

1. **Apply to Anthropic Cyber Verification Program now.** 2–5 day approval. Without it, Tier-2 cyber capability is blocked at the API mid-demo. This is the single highest-leverage action; do it before anything else.
2. **Vulnerable-by-design targets only.** Metasploitable3 / DVWA / Juice Shop / vulhub / retired HTB. Never live infra, never multi-tenant cloud, never anything we don't own.
3. **Demo never shows exploit code.** Surface: prediction score, exploit class label, patch diff, validation pass/fail. Stop there. Treat raw exploit output as we would treat a credential — it does not leave the agent loop.
4. **Public repo discipline.** Publish: ingest pipeline, defence-gen prompts, sandbox Dockerfile, OODA architecture. Do not publish: exploit-gen prompts, raw exploit output, screenshots of Phase II.
5. **Don't over-claim.** Replay framing is the truth. "Prophet predicted the class pre-disclosure and co-generated the patch" is defensible. "Prophet found a zero-day" is not — and is also bad for getting Anthropic on side.

## Open questions for the partner

1. **Adjacent to VANTAGE, replacing it, or a feature inside it?** Strong candidate: Prophet becomes VANTAGE's **Unmasker mode** — same UI shell, same human-in-the-loop approval gate, different agent stack and data domain (vulnerability intel instead of geopolitical OSINT).
2. **What does "Greek plan" mean in panel 4?** Project codename, attack-plan reference, or something else?
3. **"Mythos" — confirm intent.** Public Claude API + CVP, or were they targeting Project Glasswing access?
4. **Demo target for the partner-judging round.** Which 3 KEV entries should we replay? I'd suggest a mix: one web-app (e.g., ShareFile zero-day), one network protocol (e.g., Citrix Bleed), one library (e.g., libwebp / log4j) — to show the loop generalizes.

## Top-level recommendation

**Go.** The wedge is real, the build is feasible in 24h as a replay demo, and the policy path is clear if we move on CVP today. The biggest risk is over-claiming in the pitch — the technical concept is strong enough that we don't need to.
