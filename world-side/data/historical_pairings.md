# Historical Geopolitics ↔ Cyber Campaign Pairings

> **Purpose.** Bedrock corpus for Prophet's threat-timing forecaster. Each entry is an analogy anchor of the form: "When *X* geopolitical situation occurred, actor *Y* deployed a *Z*-class exploit within *N* days." The forecaster matches today's situation against these signatures to estimate when an adversary will burn an exploit.
>
> **Compiled.** 2026-05-02. Cases below describe events that have already occurred; this is a reference document, not a how-to.
>
> **Conventions.**
> - "Time-to-burn" = elapsed time between the cited *geopolitical trigger* and the *first observed deployment* of the exploit/wiper/intrusion. Intelligence-collection access often pre-dates the trigger by months; the burn is when the actor *spent* it.
> - Confidence labels apply to public attribution at time of writing.
> - Where dates are reported only at week granularity in primary sources, time-to-burn is given as a range.

---

## 1. Sandworm / NotPetya / Ukraine pre-anniversary, June 2017

**Geopolitical context window.** May–late June 2017. Sustained Russia–Ukraine conflict in Donbas; the EU on 19 June 2017 extended its economic sanctions on Russia by six months over Ukraine. Ukraine had been pursuing the EU Association Agreement (signed in 2014; full entry into force on 1 September 2017) and was preparing for Constitution Day on 28 June. Russia–West relations were also souring around expulsions and counter-sanctions.

**Cyber event.** **27 June 2017** — NotPetya wiper masquerading as ransomware released via a hijacked update to M.E.Doc, a Ukrainian tax-accounting application used by ~80% of Ukrainian businesses. Propagated via **EternalBlue (MS17-010 / CVE-2017-0144)** and **EternalRomance (CVE-2017-0145)** SMB exploits plus credential theft (Mimikatz-style) and PsExec/WMI lateral movement. Victims: Ukrainian government, banks, Kyiv Boryspil airport, Chernobyl monitoring; spilled to Maersk, Merck, FedEx/TNT, Mondelez, Reckitt Benckiser. ~$10B global damage. **Attribution: Russian GRU Unit 74455 ("Sandworm") — high confidence**: joint UK NCSC + US CIA + Five Eyes attribution Feb 2018; US DoJ indictment of six GRU officers Oct 2020 names NotPetya.

**Time-to-burn.** ~4–6 weeks from sanctions extension (19 Jun) and Constitution-Day-eve symbolism (28 Jun) to release on 27 Jun. The supply-chain access (M.E.Doc backdoored update server) had been established months earlier — burn window measures the gap from trigger to *deployment*, not access.

**Pattern signature.** Russia (GRU) → Ukraine; supply-chain compromise of locally ubiquitous software → wiper disguised as ransomware → spillover via worm-class SMB exploit. Trigger features: anniversary/holiday symbolism, sanctions extension, sustained low-grade conflict.

**Why it's a useful anchor.** Today's situation invokes this if: (a) Russia faces fresh sanctions or sees a Western policy line crossed, (b) there is a date with symbolic resonance (national day, anniversary of an invasion), and (c) prior reporting indicates supply-chain access already established in target geography. Tightening sanctions + anniversary date = elevated odds of a destructive-malware burn within ~30 days.

**Sources.**
- [CISA Petya Ransomware Alert TA17-181A](https://www.cisa.gov/news-events/alerts/2017/07/01/petya-ransomware)
- [Wired — "The Untold Story of NotPetya, the Most Devastating Cyberattack in History" (Andy Greenberg, 22 Aug 2018)](https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/)
- [US DoJ Indictment, Six Russian GRU Officers (Oct 2020)](https://www.justice.gov/opa/pr/six-russian-gru-officers-charged-connection-worldwide-deployment-destructive-malware-and)
- [MITRE ATT&CK G0034 Sandworm Team](https://attack.mitre.org/groups/G0034/)
- [Wikipedia — 2017 Ukraine ransomware attacks](https://en.wikipedia.org/wiki/2017_Ukraine_ransomware_attacks)

---

## 2. APT28 / DNC hack / 2016 US election cycle

**Geopolitical context window.** March–June 2016. US Presidential primary in full swing; the Obama administration was extending sanctions on Russia over Crimea (Executive Order 13685 framework in effect), and Russia was responding to NATO posture in eastern Europe. The DNC was a politically high-value target with thin defensive posture relative to its profile.

**Cyber event.** **March 2016** — spearphishing of John Podesta (Clinton campaign chair) via Bitly-shortened spoofed Google login link; credentials harvested ~19 March 2016. **April 2016** — APT28 (Fancy Bear / GRU 26165) gained DNC network access; APT29 (Cozy Bear / SVR) had already been resident since ~2015. **6 April 2016** — DCCC employee spearphished. CrowdStrike engaged 30 April; investigation begins 1 May. **14 June 2016** — Washington Post + CrowdStrike public disclosure. **15 June 2016** — Guccifer 2.0 persona launched as deflection. Tools: X-Agent backdoor, X-Tunnel, custom credential harvesters; spearphishing rather than novel CVE was the primary vector. **Attribution: GRU Unit 26165 + Unit 74455 — very high confidence**: 13 July 2018 DoJ indictment (Mueller) of 12 GRU officers; ODNI Jan 2017 ICA.

**Time-to-burn.** Election-cycle "trigger" is broad (primaries running Feb–Jun 2016). From Podesta phish (~mid-March) to first dump via DCLeaks (mid-June 2016): **~13 weeks**. From operational access to weaponization-via-leak ~8–10 weeks.

**Pattern signature.** Russia (GRU) → US political party / campaign infrastructure during election cycle; vector = credential phishing, not zero-day; payoff = curated leaks via cut-out persona/site (DCLeaks, Guccifer 2.0, WikiLeaks). Target sector = political/civil-society, not enterprise.

**Why it's a useful anchor.** Invoke when: (a) a major Western election is within 6–12 months, (b) an adversary has a clear preferred outcome, (c) pre-positioning indicators on campaign or party infrastructure exist. Pattern predicts *information operation*, not destructive cyber; time-to-burn is dictated by news-cycle leverage, not technical readiness.

**Sources.**
- [US DoJ Indictment of 12 GRU Officers (Mueller, 13 Jul 2018)](https://www.justice.gov/file/1080281/download)
- [ODNI ICA — "Assessing Russian Activities and Intentions in Recent US Elections" (Jan 2017)](https://www.dni.gov/files/documents/ICA_2017_01.pdf)
- [CrowdStrike — "Bears in the Midst: Intrusion into the DNC" (Dmitri Alperovitch, 15 Jun 2016)](https://www.crowdstrike.com/blog/bears-midst-intrusion-democratic-national-committee/)
- [MITRE ATT&CK G0007 APT28](https://attack.mitre.org/groups/G0007/)
- [Alliance for Securing Democracy — incident page](https://securingdemocracy.gmfus.org/incident/russian-government-backed-hackers-target-american-political-parties-organizations-and-campaigns-in-the-2016-presidential-election/)

---

## 3. Lazarus / Bangladesh Bank SWIFT heist / sanctions-retaliation pattern, Feb 2016

**Geopolitical context window.** Late 2015–Feb 2016. North Korea under sustained, tightening UN and US Treasury sanctions; DPRK conducted its **fourth nuclear test on 6 January 2016** and a satellite launch on 7 February 2016; the US/UN began drafting new sanctions (UNSC Res. 2270 was adopted 2 March 2016). The Kim regime was actively seeking foreign-currency revenue replacements as licit channels closed.

**Cyber event.** **4–5 February 2016** — Lazarus operators issued **35 fraudulent SWIFT MT103 messages** from Bangladesh Bank's account at the Federal Reserve Bank of New York, attempting ~$951M in transfers. Tools: custom malware against the SWIFT Alliance Access workstation (modified `liboradb.dll`), printer-driver tampering to suppress confirmation prints, knowledge of bank-end internal procedures. Five transactions cleared totaling ~$101M; ~$81M reached RCBC accounts in Manila (laundered through Philippine casinos), $20M was recalled from Sri Lanka. **Attribution: DPRK Reconnaissance General Bureau ("Lazarus" / "APT38" / "BeagleBoyz") — very high confidence**: Sep 2018 DoJ complaint against Park Jin Hyok; Aug 2020 CISA AA20-239A "BeagleBoyz" advisory; UN Panel of Experts reports.

**Time-to-burn.** From the 6 Jan 2016 nuclear test (sanctions-tightening trigger) to the SWIFT heist 4–5 Feb 2016: **~30 days**. Initial network access predated this by ~12+ months; the burn window measures *spend*, not establish.

**Pattern signature.** DPRK → financial infrastructure (banks, crypto exchanges, DeFi bridges) when sanctions tighten or revenue gaps widen. Vector = bespoke tooling against high-value financial messaging/custody systems; preference for lateral targets in jurisdictions with weak AML rather than the primary US/EU banks. Target sector = financial / crypto.

**Why it's a useful anchor.** Invoke when: DPRK faces a fresh sanctions package, missile/nuclear test backlash, or a sudden FX shortfall, AND there is reporting of pre-positioning at a financial-messaging/custody target. Predicts theft-class operation (not espionage, not destructive); burn typically within 30–90 days of the revenue-pressure trigger. The 2022 Ronin/Axie hit ($625M) follows the same shape.

**Sources.**
- [CISA AA20-239A — "Guidance on the North Korean Cyber Threat" / BeagleBoyz](https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-106a)
- [US DoJ Complaint — US v. Park Jin Hyok (8 Jun 2018, unsealed 6 Sep 2018)](https://www.justice.gov/opa/press-release/file/1092091/download)
- [Reuters — "How the New York Fed fumbled over the Bangladesh Bank cyber-heist"](https://www.reuters.com/investigates/special-report/cyber-heist-federal/)
- [BAE Systems Threat Research blog — "Two Bytes to $951m"](https://baesystemsai.blogspot.com/2016/04/two-bytes-to-951m.html)
- [MITRE ATT&CK G0032 Lazarus Group](https://attack.mitre.org/groups/G0032/)

---

## 4. SolarWinds (SUNBURST) / APT29 / Trump–Biden transition

**Geopolitical context window.** Sep 2019 (initial access) → Dec 2020 (discovery). Operationally relevant *trigger* window: late 2020 US presidential transition; the SVR's standing collection mission against US federal civilian agencies was in a high-priority phase as the new administration's foreign-policy posture took shape. The compromise was discovered against the backdrop of Treasury/Commerce intrusions and FireEye's own breach disclosure.

**Cyber event.** **Sep 2019** — initial access to SolarWinds build environment. **Oct 2019** — innocuous test code injected. **Feb 2020** — SUNBURST backdoor inserted into Orion build pipeline (versions 2019.4 HF5 through 2020.2.1). **Mar–Jun 2020** — trojanized updates pushed to ~18,000 customers; ~100 organizations and 9 US federal agencies (Treasury, Commerce, State, DHS, DOE, NTIA, NIH, NIST, US Courts) actively breached. **8 Dec 2020** — FireEye discloses theft of red-team tools. **13 Dec 2020** — FireEye + SolarWinds + Microsoft go public on SUNBURST. CVEs subsequently associated with the campaign include **CVE-2020-10148** (SolarWinds Orion authentication bypass), **CVE-2021-26855 / 26857 / 26858 / 27065** (ProxyLogon — separate but contemporaneous APT29-adjacent activity is contested). Tools: SUNBURST, TEARDROP, RAINDROP, GoldMax, Sibot, GoldFinder. **Attribution: Russian SVR / APT29 / "Cozy Bear" / Mandiant UNC2452 — very high confidence**: joint US (CISA, FBI, NSA, ODNI) statement 5 Jan 2021; formal sanctions and attribution to SVR on 15 Apr 2021 (E.O. 14024).

**Time-to-burn.** Long-fuse espionage, not a triggered burn. From build-system access (Sep 2019) to first weaponized update push (Mar 2020): **~6 months** of patient operational development. From weaponization to discovery: **~9 months**. Anchor for this case is *dwell + restraint*, not speed.

**Pattern signature.** Russia (SVR) → US/allied government and tech-supply-chain; vector = software supply-chain compromise of widely deployed enterprise software (Orion, then later Mimecast, JetBrains TeamCity-adjacent reporting); operational tempo = espionage with extreme operational security, no destructive payload, selective second-stage deployment to ~0.5% of access surface.

**Why it's a useful anchor.** Invoke when: indicators of supply-chain compromise of widely-distributed enterprise tooling appear, AND target geography is US/allied federal civilian or large-tech vendors, AND no destructive intent is observed. Predicts a long collection-oriented campaign with selective second-stage deployment; time-to-burn from access → weaponization is *months*, not days. Useful counter-example to the "Russia always destructive" frame — SVR ≠ GRU.

**Sources.**
- [CISA Alert AA20-352A — "Advanced Persistent Threat Compromise of Government Agencies, Critical Infrastructure, and Private Sector Organizations"](https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a)
- [Mandiant / FireEye — "Highly Evasive Attacker Leverages SolarWinds Supply Chain to Compromise Multiple Global Victims With SUNBURST Backdoor" (13 Dec 2020)](https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor/)
- [White House Statement / Treasury E.O. 14024 (15 Apr 2021)](https://home.treasury.gov/news/press-releases/jy0127)
- [MITRE ATT&CK Campaign C0024 SolarWinds Compromise](https://attack.mitre.org/campaigns/C0024/)
- [Mandiant — "UNC2452 Merged into APT29"](https://cloud.google.com/blog/topics/threat-intelligence/unc2452-merged-into-apt29)

---

## 5. WhisperGate + HermeticWiper / Russian invasion of Ukraine, Jan–Feb 2022

**Geopolitical context window.** Nov 2021–Feb 2022. Russian force buildup on Ukraine's borders observed from Nov 2021; Geneva, NATO–Russia Council, OSCE diplomatic talks collapsed mid-Jan 2022; US/UK begin warning publicly of imminent invasion late Jan; **24 Feb 2022** — Russia launches full-scale invasion. Cyber operations functioned as the opening salvo and as parallel disruption alongside kinetic action.

**Cyber event.**
- **13 Jan 2022** — **WhisperGate** MBR-corrupting wiper deployed against Ukrainian government, non-profit, and IT orgs. Microsoft MSTIC tracks as DEV-0586 (later **Cadet Blizzard** / GRU Unit 29155); public disclosure 15 Jan 2022.
- **23 Feb 2022 (~16:00 UTC)** — **HermeticWiper** (Trojan.Killdisk / DriveSlayer) deployed against Ukrainian government, financial, and telecoms organizations, hours before the kinetic invasion. Signed with a stolen Hermetica Digital Ltd. certificate. Accompanied by **HermeticWizard** (worm/spreader) and **HermeticRansom** (decoy). Attributed to **Sandworm** (GRU 74455).
- **24 Feb 2022** — **IsaacWiper** at Ukrainian government targets; same day, Viasat KA-SAT modem network disrupted (**AcidRain** wiper) — attributed by EU + US + UK to Russia in May 2022.
- **Mar–Apr 2022** — **CaddyWiper**, **DoubleZero**; Apr 2022 attempted **Industroyer2** strike on a Ukrainian electricity provider (foiled, per ESET + CERT-UA).

CVEs: WhisperGate and HermeticWiper did not pivot on novel CVEs; they relied on access-via-credentials/insider-deployment plus signed-driver abuse (EaseUS Partition Master driver). **Attribution: GRU (Sandworm + Cadet Blizzard) — very high confidence**: CISA AA22-057A and updates; multiple Five-Eyes joint statements May 2022; UK NCSC + EU statements on Viasat May 2022.

**Time-to-burn.** From beginning of overt diplomatic-collapse signaling (early Jan 2022) to first wiper (WhisperGate 13 Jan): **~2 weeks**. From final pre-invasion diplomacy collapse (~21–22 Feb) to HermeticWiper deployment (23 Feb): **~24–48 hours**. Coordinated H-hour-aligned cyber.

**Pattern signature.** Russia (GRU) → Ukraine + spillover to allied infrastructure (Viasat → European wind farms); vector = wipers timed to military operations; payload = destructive, not extortive; exploit-of-novel-CVE not the limiting factor — *access pre-positioning* is.

**Why it's a useful anchor.** Invoke when: a state actor is mobilizing kinetic forces and Western intelligence is publicly warning of imminent action AND prior reporting indicates pre-positioned access in target geography. Predicts wiper-class deployment within hours-to-days of H-hour, with at least one disruptive cyber preceding kinetic by hours. Strongest known modern example of cyber-kinetic timing coupling.

**Sources.**
- [CISA AA22-057A — "Destructive Malware Targeting Organizations in Ukraine"](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-057a)
- [Microsoft MSTIC — "Destructive malware targeting Ukrainian organizations" (15 Jan 2022)](https://www.microsoft.com/en-us/security/blog/2022/01/15/destructive-malware-targeting-ukrainian-organizations/)
- [SentinelLabs — "HermeticWiper — New Destructive Malware Used In Cyber Attacks on Ukraine" (23 Feb 2022)](https://www.sentinelone.com/labs/hermetic-wiper-ukraine-under-attack/)
- [ESET Research — IsaacWiper / HermeticWizard / CaddyWiper threads](https://www.welivesecurity.com/2022/03/01/isaacwiper-hermeticwizard-wiper-worm-targeting-ukraine/)
- [EU Council — "Russian cyberattack on KA-SAT" attribution (10 May 2022)](https://www.consilium.europa.eu/en/press/press-releases/2022/05/10/russian-cyber-operations-against-ukraine-declaration-by-the-high-representative-on-behalf-of-the-european-union/)

---

## 6. Stuxnet / Iran nuclear program / Bushehr–Natanz escalation, 2009–2010

**Geopolitical context window.** 2007–2010. Iranian uranium-enrichment program at Natanz expanding (~8,700 IR-1 centrifuges by 2009 per IAEA). UNSC Res. 1737 (2006) / 1747 (2007) / 1803 (2008) / **1929 (9 Jun 2010)** — successively tighter sanctions. Israeli political signaling about kinetic strike options peaks 2008–2009; the cyber operation is widely understood as the lower-cost alternative.

**Cyber event.** **Stuxnet v0.5** active by 2007 (Symantec analysis, 2013). **Stuxnet v1.001** deployed June 2009 (timestamp in code). **Stuxnet v1.100 / v1.101** deployed Mar 2010 with USB LNK exploit for faster spread. Discovered publicly **17 June 2010** by VirusBlokAda (Belarus). Four Windows zero-days: **CVE-2010-2568** (LNK shortcut), **CVE-2010-2729** (Print Spooler), **CVE-2010-2743** (kbdclass keyboard layout privilege escalation), **CVE-2010-3338** (Task Scheduler privilege escalation); plus **CVE-2008-4250** (already-patched MS08-067 server service); plus a hardcoded Siemens SIMATIC WinCC database password. Payload: targeted Siemens S7-315 / S7-417 PLCs running specific Profibus configurations matching Natanz IR-1 cascade topology; manipulated centrifuge frequencies (1064 Hz → 2 Hz → 1410 Hz cycles) while spoofing nominal readings. **Attribution: joint US (NSA/CIA) + Israel (Unit 8200), program codename "Olympic Games" — high confidence based on extensive open-source reporting (David Sanger / NYT 2012, Ralph Langner technical analysis, Kim Zetter "Countdown to Zero Day"); never officially confirmed by either government**.

**Time-to-burn.** Programmatic, not triggered. Development under Bush admin (~2006–2008), accelerated under Obama (~2009–2010). v0.5 → v1.001 cycle ~2 years; v1.001 → v1.101 cycle ~9 months. From decision-window for kinetic alternatives (2008–2009) to first centrifuge damage (Nov 2009 – Jan 2010 per ISIS): **~12–18 months** of patient development. Indicates the *opposite* shape from a triggered burn: when state actors are building a precision physical-effects weapon, time-to-burn is governed by *targeting confidence* (cascade topology, PLC ladder logic), not by political trigger.

**Pattern signature.** US/Israel → Iran nuclear infrastructure; vector = ICS-aware worm with multiple Windows 0-days for propagation + bespoke PLC payload; payoff = sub-kinetic physical effects (destroyed ~1,000 IR-1 centrifuges per ISIS estimate). Target sector = state nuclear / critical industrial.

**Why it's a useful anchor.** Invoke when: there is sustained state-on-state pressure against a hardened physical target (nuclear, missile, military-industrial), kinetic options are politically expensive, AND there is access to specialized industrial-control programming knowledge. Predicts long development cycle (12–24 months), then narrow precision burn at a single window. Counter-anchor to election-cycle and invasion-aligned cases — *Stuxnet's burn was set by metallurgy, not politics*.

**Sources.**
- [Symantec — "W32.Stuxnet Dossier" v1.4 (Feb 2011, Falliere/Murchu/Chien)](https://docs.broadcom.com/doc/security-response-w32-stuxnet-dossier-11-en)
- [IEEE Spectrum — Ralph Langner "The Real Story of Stuxnet" (Mar 2013)](https://spectrum.ieee.org/the-real-story-of-stuxnet)
- [Institute for Science and International Security — "Did Stuxnet Take Out 1,000 Centrifuges at the Natanz Enrichment Plant?" (Albright/Brannan/Walrond, 22 Dec 2010)](https://isis-online.org/uploads/isis-reports/documents/stuxnet_FEP_22Dec2010.pdf)
- [NYT — David Sanger, "Obama Order Sped Up Wave of Cyberattacks Against Iran" (1 Jun 2012)](https://www.nytimes.com/2012/06/01/world/middleeast/obama-ordered-wave-of-cyberattacks-against-iran.html)
- [Wikipedia — Stuxnet](https://en.wikipedia.org/wiki/Stuxnet)

---

## 7. Industroyer / Ukraine Kyiv grid attack, Dec 2016

**Geopolitical context window.** Dec 2016. One year after the **23 Dec 2015** BlackEnergy3-enabled attack on Prykarpattyaoblenergo / Kyivoblenergo / Chernivtsioblenergo (~225K customers off, 1–6 hr). Russia–Ukraine conflict in Donbas ongoing; Minsk II implementation stalled; Crimea sanctions still in force. The 2016 attack was conducted on the *one-year anniversary* of the 2015 attack.

**Cyber event.** **17 Dec 2016 (~23:53 local)** — Ukrenergo Pivnichna 330 kV transmission substation north of Kyiv knocked offline for ~1 hr, dropping ~200 MW of capacity. Tool: **Industroyer** (a.k.a. **CRASHOVERRIDE**, ESET/Dragos), the first known malware designed *specifically* for electric-grid operations — modular framework with native protocol implementations for **IEC 60870-5-101**, **IEC 60870-5-104**, **IEC 61850**, and **OPC DA**, plus a Siemens SIPROTEC denial-of-service component (**CVE-2015-5374**) intended to brick relays after the trip. Initial access predates by ~6 months. **Attribution: Sandworm (GRU 74455) — high confidence**: ESET + Dragos technical attribution Jun 2017; explicit US DoJ Oct 2020 indictment names this attack.

**Time-to-burn.** Anniversary-locked. Initial access (per Dragos) Mar–Jun 2016 → deployment 17 Dec 2016: **~6–9 months access dwell**, then deployed on the symbolic anniversary date. Trigger-to-burn here is best modeled as "calendar-locked" rather than reactive.

**Pattern signature.** Russia (GRU) → Ukrainian electric infrastructure; vector = ICS-protocol-native malware framework, not a Windows CVE chain; payoff = brief but symbolic outage on holiday week. Target sector = transmission-grid SCADA. Anniversary symbolism is a strong tell.

**Why it's a useful anchor.** Invoke when: Russia has a prior cyber-physical operation against a target sector AND a calendar anniversary is approaching AND ICS-grade pre-positioning has been observed. Predicts a *demonstrative* (not maximum-damage) attack timed to the anniversary date itself, ±48 hours. The 2022 attempted Industroyer2 strike on a Ukrainian electricity provider (foiled 8 Apr 2022) is the same pattern, retried at H-hour scale.

**Sources.**
- [Dragos — "CRASHOVERRIDE: Analysis of the Threat to Electric Grid Operations" (Jun 2017)](https://www.dragos.com/wp-content/uploads/CrashOverride-01.pdf)
- [ESET — "WIN32/INDUSTROYER: A new threat for industrial control systems" (Cherepanov, 12 Jun 2017)](https://www.welivesecurity.com/wp-content/uploads/2017/06/Win32_Industroyer.pdf)
- [Wired — Andy Greenberg, "Crash Override: The Malware That Took Down a Power Grid" (12 Jun 2017)](https://www.wired.com/story/crash-override-malware/)
- [MITRE ATT&CK Campaign C0025 — 2016 Ukraine Electric Power Attack](https://attack.mitre.org/campaigns/C0025/)
- [Claroty Team82 — "Industroyer2 Variant Surfaces in Foiled Attack Against Ukraine Electricity Provider"](https://claroty.com/team82/blog/industroyer2-variant-surfaces-in-foiled-attack-against-ukraine-electricity-provider)

---

## 8. Volt Typhoon / Taiwan Strait pre-positioning campaign

**Geopolitical context window.** 2021–present. Taiwan Strait tensions sustained at elevated baseline (PLA exercises around Taiwan ROC ADIZ, US arms-sales packages, Aug 2022 Speaker Pelosi visit, Apr 2023 President Tsai US transit). PRC posture under Xi Jinping has explicitly framed Taiwan reunification as a non-negotiable objective; US assessment (per CIA Director Burns, Feb 2023) is that Xi has instructed PLA to be ready to invade by 2027.

**Cyber event.** **Mid-2021 onward** — Volt Typhoon (Microsoft naming; also Bronze Silhouette, Vanguard Panda, Insidious Taurus) compromises across US critical infrastructure: communications, energy, water/wastewater, transportation. Vectors include exploitation of **Fortinet FortiGuard** appliances and **end-of-life SOHO routers** (Cisco, Netgear, ASUS) for SOHO-router botnet (KV-Botnet) used to obscure traffic. Living-off-the-land (LotL) post-exploitation: **wmic, ntdsutil, netsh, PowerShell, certutil**. Persistence observed in some victim environments for **5+ years**. **24 May 2023** — first joint CSA (CISA + NSA + FBI + Five Eyes); **7 Feb 2024** — second joint CSA explicitly framing Volt Typhoon as **pre-positioning for disruption during a future crisis or conflict**, not espionage. **31 Jan 2024** — DOJ + FBI court-authorized takedown of KV-Botnet. **Attribution: PRC state-sponsored — high confidence**: explicit, named in joint US/UK/AU/CA/NZ statements; FBI Director Wray Congressional testimony 31 Jan 2024.

**Time-to-burn.** No burn yet. Anchor's value is the *gap*: access established 2021+, no destructive deployment as of May 2026 (compilation date). Indicates patient pre-positioning for a future trigger (Taiwan kinetic action, blockade, or major US response). For forecaster, this case calibrates the *upper bound* on dwell — multi-year access can sit unused if the strategic trigger has not arrived.

**Pattern signature.** PRC → US/allied critical infrastructure (water, power, comms, transport) in geographies *adjacent to a likely Taiwan-conflict supply line* (Guam, Hawaii observed); vector = LotL + edge-device CVEs, deliberately low custom-malware footprint; objective = pre-positioning for disruption, not collection.

**Why it's a useful anchor.** Invoke when: PRC pre-positioning indicators on US/allied critical infrastructure are being reported AND a Taiwan or South China Sea trigger event is in motion (PLA mobilization, formal blockade declaration, US carrier-group repositioning to WESTPAC). Predicts that destructive activation would track the *kinetic* trigger window (hours-to-days), like HermeticWiper did in Ukraine — but the access can sit dormant for years awaiting it.

**Sources.**
- [CISA AA24-038A — "PRC State-Sponsored Actors Compromise and Maintain Persistent Access to U.S. Critical Infrastructure" (7 Feb 2024)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a)
- [CISA AA23-144A — "PRC State-Sponsored Cyber Actor Living off the Land to Evade Detection" (24 May 2023)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-144a)
- [Microsoft Threat Intelligence — "Volt Typhoon targets US critical infrastructure with living-off-the-land techniques" (24 May 2023)](https://www.microsoft.com/en-us/security/blog/2023/05/24/volt-typhoon-targets-us-critical-infrastructure-with-living-off-the-land-techniques/)
- [DOJ — "U.S. Government Disrupts Botnet People's Republic of China Used to Conceal Hacking of Critical Infrastructure" (31 Jan 2024)](https://www.justice.gov/opa/pr/us-government-disrupts-botnet-peoples-republic-china-used-conceal-hacking-critical)
- [Unit 42 — "Threat Brief: Attacks on Critical Infrastructure Attributed to Insidious Taurus (Volt Typhoon)"](https://unit42.paloaltonetworks.com/volt-typhoon-threat-brief/)

---

## 9. MOVEit / Cl0p / Russia-aligned summer 2023

**Geopolitical context window.** Mid-2023. **23–24 Jun 2023 Wagner Group mutiny** in Russia destabilizing internal Russian security politics; Western sanctions on Russia approaching their 18-month mark; ongoing Ukrainian counter-offensive. Cl0p (a.k.a. **TA505 / FIN11 / Lace Tempest**) is a financially motivated criminal group widely assessed as Russia-based and operating with implicit state tolerance.

**Cyber event.** **CVE-2023-34362** — SQL injection zero-day in Progress MOVEit Transfer (a managed file-transfer appliance used widely for sensitive B2B file exchange). Earliest exploitation observed by Mandiant **27 May 2023** (some indicators back to **9 May 2023** per Fastly); mass exploitation over US Memorial Day weekend (27–29 May 2023). Progress disclosed **31 May 2023**; CVE assigned **2 Jun 2023**; Microsoft attributed **2 Jun 2023**; Cl0p public claim **5 Jun 2023**; CISA #StopRansomware advisory **7 Jun 2023**. Subsequent CVEs: **CVE-2023-35036** (9 Jun), **CVE-2023-35708** (15 Jun). >2,700 organizations and >95M individuals impacted (US DoE, BBC, British Airways, Aer Lingus, Shell, NY Department of Education, US OPM contractors, etc.) — primarily extortion-via-data-leak, not file encryption. **Attribution: Cl0p / TA505 — very high confidence (criminal); Russia-tolerated — medium confidence**: CISA AA23-158A, Mandiant, Microsoft.

**Time-to-burn.** Cl0p had been *holding* MOVEit zero-days since **mid-2021 per Kroll forensics** (test-pattern POCs in logs going back ~2 years). Burn was timed to the long US holiday weekend (Memorial Day, 29 May 2023) for response-window arbitrage. From acquisition of working exploit (estimate: late 2022/early 2023) to mass burn: many months of patience. From holiday window (29 May) to peak exploitation: 0 days.

**Pattern signature.** Russia-tolerated criminal → Western enterprise SaaS / managed file-transfer appliances; vector = pre-stockpiled n-day or 0-day in widely-deployed B2B appliances; timing = aligned to holiday/long-weekend response gaps; payoff = mass extortion, not destruction. Mirrors prior Cl0p campaigns: **GoAnywhere MFT (CVE-2023-0669, Feb 2023)**, **Accellion FTA (CVE-2021-27101 etc., Dec 2020–Jan 2021)**.

**Why it's a useful anchor.** Invoke when: a major Western holiday/long-weekend is approaching, a managed file-transfer or secure-comms appliance with thin attack surface is widely deployed, and Russia-tolerated criminal actors have demonstrated prior exploitation of comparable products. Predicts mass-exploitation burn at the start of the response gap. Cl0p's Accellion → GoAnywhere → MOVEit cadence (~12–18 months between major MFT burns) is a calibration baseline for the engine.

**Sources.**
- [CISA AA23-158A — "#StopRansomware: CL0P Ransomware Gang Exploits CVE-2023-34362 MOVEit Vulnerability"](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-158a)
- [Mandiant — "Zero-Day Vulnerability in MOVEit Transfer Exploited for Data Theft" (1 Jun 2023)](https://cloud.google.com/blog/topics/threat-intelligence/zero-day-moveit-data-theft/)
- [Rapid7 — "CVE-2023-34362: MOVEit Vulnerability Timeline of Events"](https://www.rapid7.com/blog/post/2023/06/14/etr-cve-2023-34362-moveit-vulnerability-timeline-of-events/)
- [Kroll — "Clop Ransomware MOVEit Transfer Vulnerability CVE-2023-34362"](https://www.kroll.com/en/publications/cyber/clop-ransomware-moveit-transfer-vulnerability-cve-2023-34362)
- [MITRE ATT&CK G0092 TA505](https://attack.mitre.org/groups/G0092/)

---

## 10. Ivanti Connect Secure (UNC5221) / PRC ops, Dec 2023–Jan 2024

**Geopolitical context window.** Late 2023. **15 Nov 2023 Biden–Xi Woodside summit** (APEC, San Francisco); attempted thaw following Aug 2022 Pelosi-visit fallout. Taiwan **13 Jan 2024 presidential election** — DPP candidate Lai Ching-te (PRC-disfavored) won. PRC strategic posture: continue pre-positioning while keeping diplomatic channel open.

**Cyber event.** **CVE-2023-46805** (auth bypass, 8.2) + **CVE-2024-21887** (command injection, 9.1) chained for unauthenticated RCE on Ivanti Connect Secure / Policy Secure VPN gateways. Earliest in-the-wild exploitation per Volexity + Mandiant: **3 Dec 2023**. Ivanti + Mandiant public disclosure: **10 Jan 2024**. Mandiant public attribution to **UNC5221** (suspected PRC-nexus): **12 Jan 2024**. CISA Emergency Directive 24-01: **19 Jan 2024**. Subsequent CVEs in same family: **CVE-2024-21888** (privilege escalation), **CVE-2024-21893** (SSRF, exploited as 0-day starting ~31 Jan 2024). Tools: GLASSTOKEN webshell, ZIPLINE passive backdoor, THINSPOOL dropper, LIGHTWIRE, WARPWIRE credential harvester. **Attribution: UNC5221 (suspected PRC-nexus) — Mandiant high confidence; broader PRC-state attribution remains "suspected"** as of public reporting. Same actor previously linked to **CVE-2023-4966 ("CitrixBleed")** zero-day exploitation since late Aug 2023 — the same playbook applied across enterprise VPN/edge appliances.

**Time-to-burn.** From access (3 Dec 2023) to public disclosure (10 Jan 2024): ~38 days of stealth exploitation. From Taiwan election (13 Jan 2024) to expanded burn (CVE-2024-21893 in-the-wild ~31 Jan): ~18 days. The interesting feature is that PRC-nexus exploitation continued *through* the Biden–Xi diplomatic thaw — suggesting cyber pre-positioning is not gated by ongoing diplomatic engagement.

**Pattern signature.** PRC-nexus → enterprise edge/perimeter appliances (VPN, NetScaler, Fortigate, SonicWall, Citrix) at scale; vector = chained 0-days in security appliances themselves (the ironic targets); objective = broad initial access for downstream selection. This decouples cyber-tempo from diplomatic-tempo — important calibration.

**Why it's a useful anchor.** Invoke when: enterprise edge/security-appliance 0-days are being burned at scale AND PRC-nexus indicators are reported AND a Taiwan-related election or diplomatic event is in the same quarter. Predicts that exploitation will *continue* across diplomatic thaws — useful counter-anchor to "tensions up → burn up" naive coupling.

**Sources.**
- [Mandiant — "Cutting Edge: Suspected APT Targets Ivanti Connect Secure VPN in New Zero-Day Exploitation" (12 Jan 2024)](https://cloud.google.com/blog/topics/threat-intelligence/ivanti-connect-secure-vpn-zero-day)
- [Volexity — "Active Exploitation of Two Zero-Day Vulnerabilities in Ivanti Connect Secure VPN" (10 Jan 2024)](https://www.volexity.com/blog/2024/01/10/active-exploitation-of-two-zero-day-vulnerabilities-in-ivanti-connect-secure-vpn/)
- [CISA Emergency Directive 24-01 (19 Jan 2024)](https://www.cisa.gov/news-events/directives/ed-24-01-mitigate-ivanti-connect-secure-and-ivanti-policy-secure-vulnerabilities)
- [Mandiant — "Suspected APT Targets Ivanti Pulse Connect Secure VPN — CVE-2023-4966 (CitrixBleed) Antecedent" (Oct 2023)](https://cloud.google.com/blog/topics/threat-intelligence/session-hijacking-citrix-cve-2023-4966)
- [Unit 42 — "Threat Brief: Multiple Ivanti Vulnerabilities"](https://unit42.paloaltonetworks.com/threat-brief-ivanti-cve-2023-46805-cve-2024-21887/)

---

## 11. Triton / TRISIS / Saudi petrochemical / Iran-region tensions, 2017

**Geopolitical context window.** 2017. **5 Jun 2017** Qatar diplomatic crisis (Saudi-led blockade); **Mar–May 2017** US Tomahawk strike on Syria; sustained Saudi–Iran proxy conflict in Yemen (Houthi ballistic missile launches at Saudi territory begin escalating mid-2017). Saudi petrochemical sector framed as a sovereignty asset; Iran's earlier 2012 Shamoon strike on Saudi Aramco was the precedent.

**Cyber event.** **June 2017** — first incident: an emergency plant-process shutdown system at a Saudi petrochemical facility (later identified by reporting as Tasnee or Petro Rabigh) was knocked offline, likely a tooling-deployment misfire. **Aug 2017** — **TRITON / TRISIS / HatMan** malware deployed against **Schneider Electric Triconex Tricon Safety Instrumented System (SIS)** controllers — the first known malware purpose-built to manipulate plant *safety* systems (i.e., the layer that prevents catastrophic physical outcomes). The deployment caused an *unintended* SIS-triggered safe shutdown when payload caused controller fault. No public CVE; payload abused engineering protocol on TriStation port 1502 + a custom RAT (`trilog.exe`) writing PPC payloads to controller memory. **Attribution: Russian TsNIIKhM (Central Scientific Research Institute of Chemistry and Mechanics, Moscow) — high confidence**: Mandiant/FireEye 23 Oct 2018; **23 Oct 2020 US Treasury OFAC sanctions** designate TsNIIKhM. The *initially* favored hypothesis was Iran (given the target geography); the attribution shift to Russia is itself an interesting signal — attribution can rotate as evidence matures.

**Time-to-burn.** From Qatar crisis / regional inflection (Jun 2017) to first observed deployment (Jun 2017): coincident, but causal link is weak — TsNIIKhM development cycle was likely independent of acute Saudi geopolitics. Better framing: this was a *capability demonstration* by Russia in a strategically valuable location, not a triggered burn. From access (estimated 2014–2016 per Mandiant) to first known deployment (Jun 2017): **~12–36 months** dwell.

**Pattern signature.** State actor (Russia in this case, but the *target sector* is the signal) → Safety Instrumented Systems at critical petrochemical/refining/nuclear facilities; vector = bespoke ICS-aware malware against named SIS product family (Triconex, ABB, Honeywell); payoff = ability to disable safety-shutoff during a future kinetic or cyber attack — i.e., *enabling capability*, not standalone effect.

**Why it's a useful anchor.** Invoke when: ICS-grade access is reported at a chemical/refining/nuclear/power site AND the actor's broader strategic posture suggests interest in *enabling* future physical effects (vs. immediate disruption). Predicts long dwell, low operational tempo, no destructive trigger absent a separate strategic decision. Also useful as the **attribution-rotation** anchor — initial regional-rivalry framing was wrong.

**Sources.**
- [US Treasury OFAC — "Treasury Sanctions Russian Government Research Institution Connected to the Triton Malware" (23 Oct 2020)](https://home.treasury.gov/news/press-releases/sm1162)
- [Mandiant / FireEye — "TRITON Attribution: Russian Government-Owned Lab Most Likely Built Custom Intrusion Tools for TRITON Attackers" (23 Oct 2018)](https://cloud.google.com/blog/topics/threat-intelligence/triton-attribution-russian-government-owned-lab-most-likely-built-tools/)
- [FBI/CISA Joint CSA on TRITON (25 Mar 2022)](https://www.ic3.gov/CSA/2022/220325.pdf)
- [MIT Technology Review — "Triton is the world's most murderous malware, and it's spreading" (Patrick Howell O'Neill, 5 Mar 2019)](https://www.technologyreview.com/2019/03/05/103328/cybersecurity-critical-infrastructure-triton-malware/)
- [MITRE ATT&CK — Software S0609 Triton Safety Instrumented System Attack Framework](https://attack.mitre.org/software/S0609/)

---

## 12. Shamoon / Saudi Aramco / Iran response to oil embargo, August 2012

**Geopolitical context window.** First half 2012. **1 Jul 2012** — full EU oil embargo on Iran took effect; US sanctions (NDAA 2012, signed Dec 2011) targeting CBI began phasing in; Iranian rial in collapse. Iran threatened to close the Strait of Hormuz. Saudi Aramco's increased production was directly substituting for sanctioned Iranian crude on the world market — making Aramco a politically symbolic target.

**Cyber event.** **15 Aug 2012 (~11:08 local)** — Shamoon (W32.DistTrack) wiper detonates simultaneously across ~30,000–35,000 Saudi Aramco workstations during the Islamic holiday of Lailat al Qadr (most staff away). Components: dropper, wiper using **EldoS RawDisk** kernel driver for direct disk access, reporter module exfiltrating filenames. Replaced files with a burning-US-flag image; rendered systems unbootable. Attack-path was insider-assisted credential theft, not a novel CVE. Aramco brought ~1,000 internal websites and email offline for ~2 weeks; cleanup took months. Hacktivist front "Cutting Sword of Justice" claimed responsibility. Days later (**Aug 2012**), **RasGas** (Qatar LNG) hit by similar/related wiper. **Attribution: Iran — high confidence**: Director-level US (then-Defense Sec Panetta speech 11 Oct 2012, NSA documents leaked later); various IC reports name IRGC-affiliated developers. Family lineage: Shamoon → **Shamoon 2** (Nov 2016, Saudi Ministry of Labor), → **Shamoon 3** (Dec 2018, SAIPEM), → **ZeroCleare/Dustman** (Dec 2019, Bahrain/Kuwait/Saudi).

**Time-to-burn.** From oil-embargo effective date (1 Jul 2012) to Shamoon burn (15 Aug 2012): **~45 days**. Initial network access predates by weeks-to-months. Holiday-window timing (Lailat al Qadr falling on a Friday weekend) is deliberate — same response-gap arbitrage seen in Cl0p / NotPetya / HermeticWiper.

**Pattern signature.** Iran → Gulf state hydrocarbons and downstream (Aramco, RasGas, Sadara, SAIPEM); vector = wiper deployed via insider-assisted credential abuse; payoff = mass workstation destruction with hacktivist deniability layer; timing = aligned to Islamic holiday window. Iran's preferred target sector is unambiguously *oil & gas + government adjacent to it*.

**Why it's a useful anchor.** Invoke when: a Gulf hydrocarbons producer is functioning as substitute supply for sanctioned Iranian volumes AND Iran is in acute economic pressure AND a religious/holiday window is approaching. Predicts wiper-class burn timed to that holiday window, with hacktivist front. The Shamoon → Shamoon 2 (4-year gap, also ~Saudi–Iran inflection) → Shamoon 3 cadence is a calibration baseline.

**Sources.**
- [CISA — Joint Security Awareness Report (JSAR-12-241-01B) "Shamoon/DistTrack Malware"](https://www.cisa.gov/news-events/ics-alerts/ics-alert-12-240-01b)
- [Symantec — "The Shamoon Attacks" (16 Aug 2012)](https://www.broadcom.com/support/security-center/protection-bulletin/the-shamoon-attacks)
- [SecDef Leon Panetta speech to Business Executives for National Security (11 Oct 2012)](https://www.defense.gov/News/Speeches/Speech/Article/606952/)
- [The Intercept — NSA document on Iran's Shamoon attack (10 Feb 2015)](https://theintercept.com/2015/02/10/nsa-iran-developing-sophisticated-cyber-attacks-learning-attacks/)
- [MITRE ATT&CK — Software S0140 Shamoon](https://attack.mitre.org/software/S0140/)

---

## Engine-facing summary table

| # | Case | Actor | Trigger class | Time-to-burn | Burn class |
|---|------|-------|---------------|--------------|------------|
| 1 | NotPetya 2017 | RU GRU 74455 | Sanctions extension + anniversary | 4–6 wks | Worm-wiper |
| 2 | DNC 2016 | RU GRU 26165 | Election cycle | ~13 wks (access→leak) | Info-op leak |
| 3 | Bangladesh Bank 2016 | DPRK RGB | Sanctions tightening / nuclear test | ~30 days | Financial theft |
| 4 | SolarWinds 2020 | RU SVR | Standing collection | 6 months access→weaponize, 9 months dwell | Espionage SC |
| 5 | WhisperGate/HermeticWiper 2022 | RU GRU | Imminent kinetic invasion | hours–days | Wiper at H-hour |
| 6 | Stuxnet 2009–10 | US/IL | Programmatic, alt to kinetic | 12–24 months dev | Physical sabotage |
| 7 | Industroyer 2016 | RU GRU 74455 | Anniversary of prior op | 6–9 mo dwell, calendar-locked | ICS demo |
| 8 | Volt Typhoon 2021– | PRC | Pre-positioning for Taiwan | 5+ yr dwell, no burn yet | Disruption-prep |
| 9 | MOVEit 2023 | RU-tolerated Cl0p | Holiday response gap | 0 days from holiday | Mass extortion |
| 10 | Ivanti UNC5221 2024 | PRC-nexus | Continuous; Taiwan election | weeks of stealth | Edge-appliance access |
| 11 | TRITON 2017 | RU TsNIIKhM | Capability demo | 12–36 mo dwell | SIS / safety attack |
| 12 | Shamoon 2012 | Iran | Sanctions / oil-embargo / holiday | ~45 days | Wiper w/ hacktivist front |

**Key signatures the engine should learn from these 12.**
1. **Trigger → burn windows cluster bimodally**: hours-to-days (when a kinetic or holiday window forces timing) vs. months-to-years (when development or pre-positioning dominates).
2. **Anniversary and holiday timing** is a strong tell across Russia, DPRK, Iran, and criminal proxies — discount any prediction that ignores calendar features.
3. **Attribution can rotate** (TRITON: Iran → Russia). Engine should weight contested attributions lower.
4. **Access ≠ burn.** Several cases (Volt Typhoon, SolarWinds, TRITON) have multi-year access without destructive deployment. Pre-positioning indicators alone do not predict imminent burn — they predict *capacity* to burn when a separate trigger arrives.
5. **Pair-state preferences**: Russia → Ukraine + spillover Europe; DPRK → financial; PRC → Taiwan-supply-line critical infra; Iran → Gulf hydrocarbons; criminal Russia-tolerated → Western enterprise SaaS.
