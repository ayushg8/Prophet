# Project Prophet — Whiteboard Transcription

> Source: hand-drawn sketch by partner, shared 2026-05-02. Original image: `~/Downloads/Project Prophet.png`. This file is my best-effort interpretation of the handwriting; treat low-confidence items as such.

## Panel 1 — "Zero day exploits" (top)

- Three software inputs labelled **A, B, C** all flow into a single **System** marked with X's (suggests vulnerabilities being injected/found).
- Annotation: **"predict defects"** (the ambition: anticipate vulns rather than react).
- Named tooling on the page:
  - **Anthropic** (model/platform).
  - **Claude plugin layer** — the orchestration surface.
  - **Maven** — **Palantir Maven Smart System**, the OODA-loop fusion product. Locked in as Prophet's integration target (Palantir is an official hackathon sponsor; positioning to their stack is the wedge into the gov/defence-tech buyer).
  - **Mythos** — read as a ceiling reference to Anthropic's Project Glasswing / Claude Mythos Preview. We do **not** claim to use it; access is gated. Prophet runs on the public Claude API under the CVP. See `PROPHET_policy_risk.md`.
- Project measures listed: **predict, deter, simulate**.

## Panel 2 — "CISA"

- Expansion: **Central Information Security Agency** (the actual name is *Cybersecurity and Infrastructure Security Agency*; partner used a close variant).
- Two data sources circled:
  - **I — CVE** (labelled *Historical*) — the full CVE corpus.
  - **II — KEV** (labelled *Known Vul Exploit*; written as "KVE" but clearly the **Known Exploited Vulnerabilities** catalog).
- Implication: ground the system in CISA's authoritative datasets — CVE for breadth, KEV for "what's actually being exploited in the wild."

## Panel 3 — "Build"

- **Prompt scaffolding**, **Presentation** — top-level work tracks.
- A 4-stage pipeline boxed as **I | II | III | IV**.
- Flow:
  - **Hypothesis / Reduction** → **I. Simulation**
  - **Better context** → **Generation** → branches:
    - **Threat / Exploit** path
    - **II. Defence simulation** → **Block** → **Scale**

## Panel 4 — "Technical / Greek plan"

- Left column: **Prompt foundation** + a "Technical" stack (rows suggest layered components).
- Arrow to **Greek plan / Debug**.
- Center: **Claude plugin** as the execution surface, fed by **Human system / Threat vectors**.
- The four numbered phases (re-stated, more concrete this time):
  - **I.** Gathers **strategic intel** → detect (KEV features feed in here).
  - **II.** Generates **new zero-day exploit** (this is the bold/contentious step).
  - **III.** Simulates exploit, **locks down system (virtual)** — i.e., runs it in a sandbox.
  - **IV.** Detects / blocks / enables / **show** → **Scale**.

## Pulled-together thesis (my reading, not the partner's words)

Project Prophet = an **AI agent loop that uses CISA CVE+KEV data to predict where the next zero-day will land, generates a candidate exploit in a sandbox, then auto-generates and validates the corresponding defence**. The Claude plugin layer is the orchestration surface. Positioning is a **Palantir Maven-integrated defence-tech fusion play** — predictive vuln OODA loop, not a pure pentest tool. Outputs (prediction, exploit class, patch, validation result) are shaped to land on Maven as fusion objects.

The novel claim is **prediction + defence co-generation**, not just AI-assisted pentesting. Closest commercial analogues: XBOW (autonomous pentesting), Horizon3.ai (NodeZero), Pentera, ProjectDiscovery's Nuclei + AI work, and academic LLM-exploit-generation papers.

## Open questions for the partner

1. What's the demo target — predict a real KEV ahead of disclosure, or replay a historical KEV to show the loop end-to-end?
2. Are we sandboxing real exploit code (needs an isolated VM/container infra) or staying entirely at the *description/IOCs* layer?
3. What does "Greek plan" mean in panel 4? (Possibly a project codename, possibly "attack plan.")
4. Maven integration depth for the demo — real Palantir Maven sponsor slot, or a Maven-shaped mock surface that consumes the same JSON fusion objects?

## Risk flags (we should think about these before agents run)

- **AUP / dual-use.** Anthropic's usage policy permits authorized security research and defensive work; it does not permit producing weaponizable exploits against real third-party systems. Phase II must stay inside an isolated sandbox against synthetic targets, or against vulnerable-by-design VMs (Metasploitable, HTB retired boxes, OWASP Juice Shop, DVWA) — never live infra without explicit authorization.
- **Novelty bar is high.** "AI agent that pentests" is a crowded space in 2025–2026. The wedge has to be sharper than "we have Claude in a loop."
- **Hackathon scope.** A 24-hour build cannot deliver real zero-day prediction. The MVP is almost certainly a *replay*: pick 3–5 historical KEV entries, show that the Prophet loop, given only pre-disclosure context, would have produced the exploit class + the patch class.
