# PROPHET — Policy, Dual-Use, and Disclosure Pressure Test

> Research output from agent run 2026-05-02. Question: What is safe to build and demo, and what gets us flagged or DQ'd?

**Recommendation:** Build it, with hard constraints. The concept is buildable and demo-able at a hackathon with defence-tech judges — but only if Phase II (exploit generation) operates exclusively against vulnerable-by-design targets, the demo never surfaces a runnable payload, and the team applies for Anthropic's Cyber Verification Program before the event. Without those three measures, a single screenshot from the demo could misrepresent what Claude is doing and create reputational and AUP-compliance problems for the team.

---

## (a) TL;DR — Verdict

**Build it with these constraints:**

1. Phase II (exploit generation) runs only against explicitly vulnerable-by-design targets (Metasploitable, DVWA, OWASP Juice Shop, retired HTB boxes, or a locally spun CVE-reproduction container). No live infrastructure, no unpatched production systems.
2. The demo stops at "exploit class identified + patch co-generated." It does not show a working payload executing. The output Claude surfaces is a patch diff and a threat-intelligence report, not shellcode.
3. Apply to Anthropic's Cyber Verification Program (CVP) today — approval is 2–5 business days, free, and gives the team documented authorization to use Claude for dual-use security work. Without it, you are in a legal grey zone under the live AUP.
4. "Mythos" in the sketch may refer to Anthropic's internal Claude Mythos Preview model — do not claim to use or integrate it; access is restricted to Project Glasswing partners.

---

## (b) Anthropic AUP-Relevant Excerpts with Direct Citations

### The Live AUP (effective September 15, 2025)

The live Acceptable Use Policy at [https://www.anthropic.com/legal/aup](https://www.anthropic.com/legal/aup) prohibits:

> "Discover or exploit vulnerabilities in systems, networks, or applications without authorization of the system owner."
> "Create or distribute malware, ransomware, or other types of malicious code."
> "Gain unauthorized access to systems, networks, applications, or devices."

There is no blanket research exemption written into the AUP text itself. Authorization by the system owner is the dividing line in the policy. Source: [Anthropic AUP](https://www.anthropic.com/legal/aup); [Usage Policy Update (Sept 2025)](https://www.anthropic.com/news/usage-policy-update).

### Real-Time Cyber Safeguards (live, 2026)

Anthropic has deployed real-time safeguards on its most capable models that create two explicit tiers:

**Tier 1 — Prohibited, non-adjustable:** "Cybersecurity activities that are almost always used maliciously and have little to no legitimate defensive application such as mass data exfiltration or ransomware code development."

**Tier 2 — Blocked by default, unlockable via CVP:** "Cybersecurity activities that have legitimate defensive applications, such as vulnerability exploitation or offensive security tooling development."

Source: [Real-time cyber safeguards on Claude — Help Center](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude)

Project Prophet's Phase II (generating candidate exploits) almost certainly falls in Tier 2. Without CVP approval, your API calls will be blocked or degraded mid-demo.

### The Cyber Verification Program (CVP)

The CVP is Anthropic's formal mechanism for security professionals to unlock Tier 2 capability. It is:
- Free
- Application-based (2–5 business day approval)
- Scoped to: "authorized pentesting, red teaming, threat intelligence, and CTF environments"
- Requires: work email (non-personal domain preferred), organizational affiliation, description of blocked use cases, and evidence of legitimacy (OSCP/GPEN/CISSP cert, published CVEs, or signed company letter)
- Not available on Bedrock or Vertex at time of writing; available on the direct Anthropic API and Microsoft Foundry

Source: [Anthropic Cyber Verification Program — Undercode Testing](https://undercodetesting.com/anthropics-cyber-verification-program-unlocking-for-offensive-security-heres-how-to-apply-and-use-it-video/)

CVP approval does not remove Tier 1 blocks. Ransomware generation, mass exfiltration tools, and weaponized payloads against real systems remain off-limits for everyone, always.

### API vs. claude.ai Consumer Distinction

The CVP applies to the Anthropic API. The claude.ai consumer interface has a different and more conservative permission envelope. All hackathon tooling should go through the API directly. Do not build the demo against a claude.ai browser session — you will hit more refusals and have no path to CVP unlocking. Source: [Claude Code Security](https://www.anthropic.com/news/claude-code-security); [Real-time cyber safeguards Help Center](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude).

### Project Glasswing and "Mythos"

The sketch references "Mythos." Anthropic launched Project Glasswing in April 2026 around a model called Claude Mythos Preview — a frontier-class model capable of autonomously discovering and chaining zero-day vulnerabilities. Access is restricted: it is not publicly available and is only accessible to Project Glasswing's 11 named partners and ~40 approved critical-infrastructure organizations, with up to $100M in usage credits committed. Do not claim to use Mythos Preview. If you want to reference it, say "Anthropic's Project Glasswing demonstrates the ceiling of what this class of model can do; Prophet uses the publicly available Claude API with CVP authorization."

Source: [Project Glasswing](https://www.anthropic.com/glasswing); [CyberScoop coverage](https://cyberscoop.com/project-glasswing-anthropic-ai-open-source-software-vulnerabilities/)

---

## (c) 5 Hardest Judge Questions + Answers

**Q1: "What stops someone from extracting the exploit code Claude generated and using it against a real target?"**

Answer: Three layers. First, the exploit generation prompt is scoped to a named synthetic target (e.g., Metasploitable3 with CVE-XXXX-YYYY patched in at build time) — the output is structurally tied to that environment, not a general-purpose payload. Second, no exploit output is persisted to disk or logged in plain text; the agent loop consumes it internally and surfaces only the patch diff and the threat-class label. Third, the demo itself never shows exploit code in the UI — judges see the prediction score, the exploit class (e.g., "heap overflow in libjpeg via malformed EXIF header"), and the generated patch, not the exploit bytes. XBOW uses an identical framing: "exploit validation uses controlled challenges that confirm exploitability without modifying data or disrupting systems."

**Q2: "Is this actually generating novel zero-days, or are you replaying known CVEs?"**

Honest answer (and the right one): "For a hackathon build, Prophet replays historical KEV entries using pre-disclosure context to show the prediction and co-generation loop end-to-end. Genuine zero-day discovery against production software would require weeks of fuzzing infrastructure and legal authorization from the software vendor — that is out of scope here. The novel claim is the OODA-loop architecture: predict the vulnerability class, co-generate the defence, validate both in sandbox. We are demonstrating that the pipeline works; we are not claiming to have discovered a new CVE today."

This answer protects you from over-claiming and satisfies defence-tech judges who know the difference.

**Q3: "What's your containment story — if the sandbox breaks, what happens?"**

Answer: "The sandbox runs in a fully isolated Docker network with no internet egress and no host filesystem mounts. The vulnerable target VM is ephemeral — spun up per run, destroyed after. We do not run this on shared cloud infrastructure. For the demo, we're running on a local machine with the network interface for the sandbox container blocked at the host firewall level. We can show the docker-compose config and iptables rules on request." If you do not have this built before the hackathon, build it — this answer has to be true.

**Q4: "Anthropic's AUP prohibits exploit generation — how are you compliant?"**

Answer: "We applied to and received approval from Anthropic's Cyber Verification Program, which is the formal mechanism for security research teams using the API for authorized penetration testing and red-team work. Our use case — vulnerability class prediction and patch co-generation against sandboxed vulnerable-by-design targets — maps directly to the CVP's authorized-pentesting category. We operate entirely within the owner-authorized exception in the AUP: we own or control every target system Prophet touches." Have the CVP approval email in your back pocket.

**Q5: "Could you adapt Prophet to scan live production systems without authorization?"**

Answer: "Technically the pipeline could be repointed at any target — so could Nmap, Burp Suite, or Metasploit. What prevents misuse is the same combination that prevents Metasploit misuse: legal authorization requirements, ethical use constraints, and in our case, the CVP scope restriction. We have not built auto-discovery of internet-facing targets. The target specification is a manual, explicit input. Pointing it at a system without authorization would be a CFAA violation by the operator, not a product flaw — the same position XBOW, NodeZero, and Pentera all take." This is accurate and matches industry-standard framing.

---

## (d) Concrete Guardrails Checklist for the Team

### Targets — Safe
- Metasploitable 2 / 3 (intentionally vulnerable Linux VMs)
- DVWA (Damn Vulnerable Web Application)
- OWASP Juice Shop
- Vulhub Docker-compose CVE reproductions (use only CVEs that are fully patched and publicly disclosed — KEV entries older than 12 months are safe)
- Retired HackTheBox machines (official HTB retired-machine policy explicitly permits this)
- Custom CVE-reproduction containers you build yourself for specific historical CVEs

### Targets — Never
- Any live internet-facing system you do not own
- Cloud provider infrastructure (even your own, unless isolated from production)
- Any system running unpatched software that Prophet's output could actually compromise
- Systems belonging to third parties without a signed authorization letter

### What to Log
- Timestamp, target name, CVE reference, predicted exploit class, generated patch diff, sandbox execution result (pass/fail), Claude token usage
- Do NOT log: raw exploit code, shellcode, payload bytes, any output that could function as a standalone PoC
- Use structured logs (JSON) so you can show judges a clean audit trail

### What NOT to Publish in a Public Repository
- Any generated exploit code, even pseudocode that is structurally a PoC
- The exact prompt chain that instructs Claude to produce exploit output — this is dual-use
- API keys, CVP approval credentials
- Any output from Phase II (the exploit generation phase) in raw form
- Recordings or screenshots of the exploit generation step

Publish freely: the patch generation prompts, the KEV/CVE ingestion pipeline, the defence-validation logic, the OODA-loop architecture diagram, the sandbox Dockerfile.

### What the Demo Should and Should Not Show

Show: the prediction score for a historical KEV, the exploit class label, the generated patch diff, the sandbox test result confirming the patch blocks the exploit class, the threat intelligence report.

Do not show: exploit code executing in the sandbox, a shell being spawned, privilege escalation output, any output that reads as "Claude wrote an attack."

The demo stopping point is: "Prophet predicted this class of vulnerability, co-generated this patch, and our sandbox confirmed the patch blocks it. Here is the before/after diff." Full stop.

---

## (e) Suggested Public-Facing Language

### What to Say

"Project Prophet is a defensive AI agent that uses CISA's CVE and KEV datasets to predict where vulnerability classes will emerge next, co-generates candidate patches, and validates them in an isolated sandbox. The loop is: predict, defend, validate — not attack."

"We built a prediction and patch co-generation pipeline. The system identifies exploit classes in historical KEV data and auto-generates the corresponding defensive fix."

"Prophet operates against vulnerable-by-design sandbox targets only. Every system it touches is one we own and control for the purpose of validating whether the generated defence works."

"We use the Anthropic API under the Cyber Verification Program, which is Anthropic's authorization pathway for legitimate security research and red-team tooling."

### What NOT to Say

Do not say: "Claude generates zero-day exploits." Say: "Claude predicts exploit classes and generates patches."

Do not say: "We tested this against real CVEs." Say: "We validated our pipeline against historical KEV entries reproduced in our isolated sandbox."

Do not say: "The AI found a new vulnerability." Say: "The prediction loop flagged a vulnerability class consistent with historical KEV patterns."

Do not say: "Here is the exploit code Claude wrote." Do not show exploit code in the demo at all.

### The One-Line Pitch

"We built an AI OODA loop that predicts where the next class of exploitable vulnerability will land and co-generates the patch before attackers get there — not a pentest tool, a prediction and defence engine."

---

## Options Considered (for the exploit-generation phase specifically)

### Option A — Full exploit generation, show payload in demo
- Pros: visually dramatic, proves the loop works end-to-end
- Cons: AUP violation risk without CVP; one screenshot reads as "Anthropic ships malware factory"; DQ risk at any hackathon with responsible-AI judges; creates a public record you cannot take back
- Verdict: Do not do this

### Option B — Exploit class identification only, no code generation
- Pros: fully safe, unambiguously within AUP, easy to explain
- Cons: the "Prophet" name and "zero-day" framing lose punch; less differentiated from existing vuln-scanner tooling
- Verdict: Safe fallback if CVP approval doesn't come through in time

### Option C — Generate exploit internally, surface only patch and class label (recommended)
- Pros: loop is technically complete (proves the prediction feeds actual exploit logic); demo shows the defensively meaningful output; AUP-compliant with CVP; matches XBOW/DARPA framing; judges can ask "did it actually work?" and the answer is "yes, validated in sandbox"
- Cons: requires CVP approval, requires airtight sandbox, requires discipline not to screenshot the intermediate step
- Source: [XBOW platform framing](https://xbow.com/platform); [AIxCC responsible disclosure](https://www.darpa.mil/news/2025/aixcc-results)
- Verdict: This is the recommended path

### Option D — Operate entirely at description/IOC layer, no code execution
- Pros: completely safe, no infrastructure required, fastest to build in 24 hours
- Cons: not differentiated, not credible to defence-tech judges who will ask "did you actually run it?"
- Verdict: Use as the fallback if the sandbox isn't ready

## What Changes the Answer

- If the team does not get CVP approval before the hackathon, drop to Option B or D — without CVP, Phase II is technically non-compliant with the live AUP even in sandbox context.
- If the hackathon is hosted on shared cloud infrastructure (AWS/GCP multi-tenant), the containment story breaks. This needs to run on local hardware with network isolation you control.
- If a judge asks to see the exploit output and you show it, you have created a public record of Claude generating attack code. Decide your "no" answer before the demo starts and brief every team member.
- "Mythos" in the sketch is read as a ceiling reference to Claude Mythos Preview / Project Glasswing, not an integration target. Decision (2026-05-02): Prophet does **not** position relative to Glasswing and does **not** claim Mythos access. The integration target is **Palantir Maven** (Palantir is an official hackathon sponsor). Plan on the standard Claude API under CVP authorization (Sonnet 4.6 or Opus 4.7, whichever your CVP covers).

---

## Sources

- [Anthropic Acceptable Use Policy (live)](https://www.anthropic.com/legal/aup) — Prohibits exploit generation without owner authorization; no blanket research exemption in policy text
- [Anthropic Usage Policy Update, Sept 2025](https://www.anthropic.com/news/usage-policy-update) — Details the Sept 15 changes; adds "malicious computer/network" section; confirms owner authorization as the line
- [Real-time cyber safeguards on Claude — Help Center](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude) — Defines two tiers: prohibited (non-adjustable) and high-risk dual-use (adjustable via CVP)
- [Anthropic Cyber Verification Program — Undercode Testing](https://undercodetesting.com/anthropics-cyber-verification-program-unlocking-for-offensive-security-heres-how-to-apply-and-use-it-video/) — CVP application requirements, what it unlocks, what stays prohibited
- [Anthropic Claude Code Security](https://www.anthropic.com/news/claude-code-security) — Anthropic's own framing of defender-first positioning; quotes the dual-use paradox explicitly
- [Project Glasswing](https://www.anthropic.com/glasswing) — Restricted-access Mythos Preview initiative; $100M in credits; acknowledges AI can find and chain zero-days but restricts access to vetted defenders
- [DARPA AIxCC Results](https://www.darpa.mil/news/2025/aixcc-results) — "Cyber reasoning systems" language; 18 real vulnerabilities responsibly disclosed; open-source release of CRS tools
- [AIxCC SoK paper (arXiv)](https://arxiv.org/abs/2602.07666) — Competition design and lessons learned; responsible disclosure via Kudu Dynamics + OSTIF
- [XBOW Platform](https://xbow.com/platform) — "Creative AI discovers; deterministic logic decides what's real"; non-destructive validation language; constrained and observable framing
- [Horizon3.ai NodeZero](https://horizon3.ai/nodezero/) — "Autonomously find, fix, and validate real risks"; "proven attack paths" framing; avoids "exploit generation" language
- [CISA Coordinated Vulnerability Disclosure Program](https://www.cisa.gov/resources-tools/programs/coordinated-vulnerability-disclosure-program) — 45-day vendor timeline before CISA may disclose; CVE assignment as CNA of last resort; multi-step analysis and coordination process
- [Anthropic Mythos / eSecurity Planet](https://www.esecurityplanet.com/threats/anthropic-probes-alleged-unauthorized-access-to-ai-security-tool-mythos/) — Background on Mythos as Anthropic's internal security tool name
- [Undercode Testing — AIxCC framing](https://undercodetesting.com/the-0-billion-future-of-offensive-security-why-agentic-ai-is-making-traditional-pentesting-obsolete-video/) — Industry framing of agentic offensive security tools in 2025-2026
- [Picuss Security — Glasswing Paradox](https://www.picussecurity.com/resource/blog/anthropics-project-glasswing-paradox) — Third-party analysis of the dual-use tension in Glasswing
