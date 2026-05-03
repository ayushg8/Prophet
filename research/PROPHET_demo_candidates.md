# PROPHET — Demo Candidate Shortlist

> Compiled 2026-05-02 from a two-agent investigation: investigator A mined CISA's KEV catalog for recognition + narrative; investigator B independently cross-referenced Vulhub Docker reproductions against ProjectDiscovery Nuclei templates for tractability. This file is the synthesis: 5 historical KEV CVEs we can replay end-to-end through the Prophet loop in 24 hours.

> **Scope reminder:** Prophet replays *historical, fully-disclosed* KEV entries against vulnerable-by-design sandboxes. Per `PROPHET_policy_risk.md`, we do not generate novel exploits and we never surface raw exploit code in the demo UI. The output to judges is: prediction score, exploit class label, patch diff, sandbox validation result.

## Selection method

Each candidate had to clear two independent filters:

1. **Recognition + narrative (investigator A):** does a judge nod when they hear the name? Is the exploit primitive visually clear? Is the patch primitive a one-liner (env var, version pin, config flag)?
2. **Tractability (investigator B):** does a Vulhub Docker-compose reproduction exist *and* does a ProjectDiscovery Nuclei template exist? Can we run `docker compose up -d` on demo hardware in under 5 minutes?

The intersection of A's top-15 and B's confirmed-both-sides-13 produced 7 viable candidates. Final 5 picked for: vuln-class diversity (no two from the same CWE family in the front three), demo-day risk balance (3 of 5 fully air-gapped), and at least 2 with judge-instant-recognition names.

---

## The 5 hypothesis cards

### 1. CVE-2021-44228 / Log4Shell — The anchor

| Field | Value |
|---|---|
| Class | JNDI lookup → library RCE (CWE-917) |
| Vulhub | `log4j/CVE-2021-44228/` (Solr 8.11.0 image) |
| Nuclei | `http/cves/2021/CVE-2021-44228.yaml` |
| Exploit primitive | HTTP header containing `${jndi:ldap://...}` triggers a JNDI callback |
| Patch primitive | `LOG4J_FORMAT_MSG_NO_LOOKUPS=true` env var, restart container |
| Spin-up | `docker compose up -d`, ~10 sec |
| Air-gapped? | **No** — Nuclei template requires interactsh callback |
| KEV listing | 2021-12-10 |

**Hypothesis Prophet validates:** Given pre-disclosure context (CWE-917 + Apache library breadth + an emerging Nuclei template), Prophet's triage signals would have ranked this above EPSS's 30-day window — and the one-env-var patch is a textbook case of defence co-generation in under 60 seconds.

**Risk:** Needs interactsh (oast.pro hosted server is fine, but a network blip kills the demo). Keep as primary *if* network is reliable on demo day, else demote to backup.

---

### 2. CVE-2021-41773 / Apache 2.4.49 Path Traversal — The tractability anchor

| Field | Value |
|---|---|
| Class | Path traversal → arbitrary file read → RCE via mod_cgi (CWE-22) |
| Vulhub | `httpd/CVE-2021-41773/` |
| Nuclei | `http/cves/2021/CVE-2021-41773.yaml` |
| Exploit primitive | GET request with encoded `../` traversal |
| Patch primitive | Dockerfile base image bump to Apache 2.4.50 |
| Spin-up | `docker compose build && up -d`, ~30 sec |
| Air-gapped? | **Yes** — Nuclei matches `/etc/passwd` content in HTTP body, no callback |
| KEV listing | 2021-11-03 |

**Hypothesis Prophet validates:** Even with no internet egress, Prophet's loop completes end-to-end — exploit confirmed by file content in HTTP body, patch confirmed by a 404 on the same request after image rebuild.

**Risk:** Lowest of the five. This is the demo-day insurance policy.

---

### 3. CVE-2022-22965 / Spring4Shell — The recognition multiplier

| Field | Value |
|---|---|
| Class | ClassLoader manipulation → JSP webshell write (CWE-94) |
| Vulhub | `spring/CVE-2022-22965/` (WebMVC 5.3.17) |
| Nuclei | `http/cves/2022/CVE-2022-22965.yaml` |
| Exploit primitive | crafted POST setting `class.module.classLoader.resources.context.parent.pipeline.first.pattern` |
| Patch primitive | image bump to Spring 5.3.18+ |
| Spin-up | `docker compose up -d`, ~15 sec |
| Air-gapped? | **No** — interactsh callback |
| KEV listing | 2022-04-04 |

**Hypothesis Prophet validates:** A vuln class adjacent to but distinct from Log4Shell (web framework deserialization vs library JNDI) — Prophet generalizes the loop without rewriting tooling.

**Risk:** Interactsh-dependent. If network fails, demote to backup.

---

### 4. CVE-2023-22527 / Confluence SSTI — The currency case

| Field | Value |
|---|---|
| Class | Server-side template injection → OGNL RCE (CWE-74) |
| Vulhub | `confluence/CVE-2023-22527/` (Confluence 8.5.3, no license wizard required per docs) |
| Nuclei | `http/cves/2023/CVE-2023-22527.yaml` |
| Exploit primitive | crafted POST to `/template/aui/text-inline.vm` |
| Patch primitive | image version pin |
| Spin-up | `docker compose up -d`, ~2 min (Confluence start-up is heavier) |
| Air-gapped? | **Yes** — response-header match, no callback |
| KEV listing | 2024-01-24 |

**Hypothesis Prophet validates:** SSTI / template-engine bugs are the recurring weaponized class of 2023–2024; Prophet's signal stack flags this category specifically because Nuclei templates lag KEV by days, not weeks, for SSTI patterns.

**Risk:** Confluence start-up is the slowest in the set. Pre-warm before demo.

---

### 5. CVE-2017-5638 / Apache Struts2 S2-045 — The Equifax legend

| Field | Value |
|---|---|
| Class | OGNL injection via `Content-Type` header (CWE-20) |
| Vulhub | `struts2/s2-045/` |
| Nuclei | `http/cves/2017/CVE-2017-5638.yaml` |
| Exploit primitive | malformed multipart `Content-Type` triggers OGNL evaluation in Struts file-upload error path |
| Patch primitive | image bump to Struts 2.3.32 |
| Spin-up | `docker compose up -d`, ~20 sec |
| Air-gapped? | **Yes** — matches command output (`root` / `uid=`) in response |
| KEV listing | 2021-11-03 (added retroactively by CISA) |

**Hypothesis Prophet validates:** The CVE that took down Equifax. Prophet's signals pre-existed the breach by months — the historical replay shows that a KEV-grounded triage loop in 2017 would have ranked this within the top tier, and the patch generation produces the same one-line fix Apache shipped.

**Risk:** x86 image, may run slowly under Rosetta on Apple Silicon. Test on demo hardware in hour 0.

---

## Demo orchestration

| Slot | CVE | Why this slot |
|---|---|---|
| **Primary on stage** | CVE-2021-44228 (Log4Shell) | Maximum recognition; the canonical AI-security-demo CVE |
| **Live backup** (pre-loaded in queue) | CVE-2021-41773 (Apache traversal) | Cleanest end-to-end loop; no internet dependency; "always works" |
| **Q&A ammo** ("show me another one") | CVE-2017-5638 (Struts2 / Equifax) | Strong historical narrative; no interactsh; different exploit family |
| **Currency ammo** ("is this only old stuff?") | CVE-2023-22527 (Confluence) | Most recent in pool; demonstrates the loop generalizes to 2023 SSTI |
| **Class-diversity ammo** | CVE-2022-22965 (Spring4Shell) | Different framework, different patch primitive |

Risk balance: 3 of 5 work fully air-gapped; 2 of 5 carry the strongest names but need internet. If demo network is the bigger worry, swap Spring4Shell out and promote Struts2 into the main 3.

---

## Hour 0–1 gate (per `PROPHET_feasibility.md`)

Pick **one** CVE and verify the substrate works end-to-end before any agent-loop code gets written. Recommended order:

1. **CVE-2021-41773** first (no interactsh, ~30 sec spin-up). If `docker compose up -d` + `nuclei -t http/cves/2021/CVE-2021-41773.yaml -u http://localhost` returns "Vulnerable," substrate is proven.
2. Then **CVE-2021-44228** (canonical demo). If interactsh works on demo network, this becomes the on-stage CVE.
3. Then **CVE-2017-5638** as the third confirmed loop (gives us 3 air-gapped paths if network is unreliable).

Do not move to hour 1–3 (tool layer) until at least one CVE clears the hour 0–1 gate.

---

## Single-coverage CVEs (parked, not promoted)

For reference, these have either Vulhub *or* Nuclei but not both confirmed:

- **CVE-2016-4437 (Apache Shiro)** — both exist but Java gadget-chain payloads are fragile; descope.
- **CVE-2021-40438 (Apache mod_proxy SSRF)** — both exist but SSRF-via-Sigma is hard to visualize in 90 sec.
- **CVE-2024-23897 (Jenkins file read)** — Vulhub only, no Nuclei template found.
- **CVE-2022-42889 (Text4Shell)** — neither side confirmed at expected paths.

---

## CVEs eliminated despite high recognition

These came up in investigator A's top-15 but lacked confirmed Vulhub + Nuclei coverage in 24h-build terms:

- **CVE-2023-34362 / MOVEit** — no canonical Vulhub reproduction; SQLi→token chain is too multi-stage for 90 sec.
- **CVE-2021-34473 / ProxyShell** — Exchange Server reproduction infeasible in Vulhub; chain of 3 CVEs.
- **CVE-2023-4966 / Citrix Bleed** — NetScaler image not freely distributable.
- **CVE-2023-46604 / ActiveMQ** — Vulhub coverage exists but interactsh-dependent and shell-spawn visualization adds setup burden.

These belong in the post-hackathon roadmap if Prophet ships beyond the demo.

---

## Sources

This file synthesizes two parallel research agents (2026-05-02). Primary sources cited inline in their reports; key references:

- [CISA KEV JSON feed](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)
- [vulhub/vulhub](https://github.com/vulhub/vulhub) — directory listings confirmed for all 5 picks
- [projectdiscovery/nuclei-templates](https://github.com/projectdiscovery/nuclei-templates) — template paths confirmed for all 5 picks
- Per-CVE Vulhub + Nuclei paths verified against the GitHub raw-file API on 2026-05-02
