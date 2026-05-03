# Sanctions State — Cyber-Threat Motivation Snapshot

**Project:** Prophet (threat-timing forecaster)
**Snapshot date:** 2026-05-02
**Purpose:** Sanctions are a leading indicator of state-aligned cyber retaliation. This file inventories what is currently in force, what was added recently, and what is signaled but not yet imposed — to feed the world-layer motive model.
**Knowledge cutoff caveat:** Author's training cutoff is January 2026. Entries dated after that point are sourced from web search at compile time. Where 2026 actions could not be confirmed against primary government sources (some Council/Treasury pages return 403/timeout to automated fetch), the entry is sourced from law-firm or major-press secondary reporting and flagged.

---

## 1. Recent US OFAC actions, Feb–May 2026

OFAC posts under the cyber-related (CYBER2), DPRK, IRGC, and Russia (RUSSIA-EO14024 / EO13848) authorities. The following are the cyber-relevant or cyber-adjacent designations in the snapshot window. For the live feed see [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions).

| Date | Authority | Target | Why it matters | Source |
|---|---|---|---|---|
| 2026-02-12 | Counter-narcotics | IMG Academy LLC settlement ($1.72M) | Not cyber, but signals OFAC's renewed enforcement appetite — sets the climate. | [Steptoe Sanctions Update Feb 2 2026](https://www.steptoe.com/en/news-publications/international-compliance-blog/weekly-sanctions-update-february-2-2026.html) |
| 2026-02-24 | CYBER2 | 3 Russian individuals (Oleg Kucherov, Marina Vasanovich, Sergey Zelenyuk), 1 Tajik national (Azizjon Mamashoyev), Russian co. **Matrix**, UAE cos. **Advance Security Solutions** and **Special Technology Services** | Targets a zero-day broker network accused of buying exploits stolen from a US defense contractor. Direct hit on the offensive-cyber supply chain — historically these designations correlate with retaliatory ops from the broker's customers. | [TechCrunch](https://techcrunch.com/2026/02/24/treasury-sanctions-russian-zero-day-broker-accused-of-buying-exploits-stolen-from-u-s-defense-contractor/) · [HSToday](https://www.hstoday.us/subject-matter-areas/cybersecurity/treasury-imposes-cyber-related-sanctions-on-russian-and-uae-individuals-entities/) · [Al-Monitor](https://www.al-monitor.com/originals/2026/02/us-imposes-cyber-related-sanctions-russian-uae-individuals-and-entities) |
| 2026-03-12 | DPRK / cyber-fraud | 6 individuals (Nguyen Quang Viet, Do Phi Khanh, Hoang Van Nguyen, Yun Song Guk, Hoang Minh Quang, York Louis Celestino Herrera) + 2 entities (**Amnokgang Technology Development Co.**, **Quangvietdnbg International Services Co.**) + 21 crypto addresses | DPRK IT-worker network operating from N. Korea, Vietnam, Laos, Spain. Treasury attributes ~$800M in 2024 revenue funneled to WMD programs. Coral Sleet / Jasper Sleet / PurpleDelta / Wagemole cluster. | [Treasury press release sb0230](https://home.treasury.gov/news/press-releases/sb0230) · [Hacker News writeup](https://thehackernews.com/2026/03/ofac-sanctions-dprk-it-worker-network.html) · [Chainalysis](https://www.chainalysis.com/blog/ofac-targets-north-korean-it-workers-crypto-march-2026/) |
| 2026-03-18 | EO14024 delistings | Removed Russian/Turkish/Emirati persons including Evgeniya Tyurikova | Counter-flow: shows Treasury is willing to delist where cooperation is forthcoming. Not motive-relevant for retaliation but useful baseline for the model. | [Mayer Brown Russia Update March 2026](https://www.mayerbrown.com/en/insights/publications/2026/03/russia-ukraine-sanctions-update---month-of-march-2026) |
| 2026-04-23 | Cyber-related Designations + GL | Counter Terrorism, Counter Narcotics & Cyber-related package; new cyber General License issued same day | OFAC's regular omnibus update including CYBER2 entries. Specific names rolled into combined notice — see SDN diff. | [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions) |
| 2026-04-23 | EO13224 / Iran-financing | ~40 shipping firms + Chinese "teapot" refinery **Hengli Petrochemical** | Targets Iranian oil revenue stream that funds IRGC cyber/proxy ops. Indirect cyber motive: tightens IRGC budget pressure. | [Steptoe Sanctions Update Apr 13 2026](https://www.steptoe.com/en/news-publications/stepwise-risk-outlook/sanctions-update-april-13-2026.html) |
| 2026-04-24 | Iran / IRGC | Updated Central Bank of Iran SDN entry: 2 new crypto addresses added (frozen 2026-04-23) | Hits IRGC-affiliate laundering routes. CBI–IRGC ties make this a near-direct motive trigger for IRGC cyber operators (Emennet Pasargad cluster, CyberAv3ngers). | [Chainalysis CBI April 2026](https://www.chainalysis.com/blog/central-bank-of-iran-designation-ofac-update-april-2026/) |
| 2026-04 (per E.O. 13848) | Election interference | IRGC subordinate org + Moscow-based GRU affiliate org and its director | Public attribution of 2024 election interference to GRU/IRGC affiliates. Naming these orgs surfaces operators who may now feel "burned" — historically associated with infrastructure shifts and follow-on ops. | [Treasury jy2766](https://home.treasury.gov/news/press-releases/jy2766) |
| 2026-04-28 | Iran-related | Iran Designations + new Iran-related GL | Routine Iran-program update; specifics roll into SDN diff. | [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions) |
| 2026-04-29 | RUSSIA-EO14024 | Amended Russia-related GL + amended FAQs | Mostly oil/maritime adjustments, not new cyber designations, but signals continuing pressure on the financial perimeter. | [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions) |

**Section 1 entry count: 10**

---

## 2. Recent EU consolidated additions, 2026

EU cyber-sanctions framework (Council Decision (CFSP) 2019/797 + Regulation 2019/796) was extended in May 2025 through 18 May 2028 ([Consilium press, May 2025](https://www.consilium.europa.eu/en/press/press-releases/2025/05/12/cyber-attacks-council-extends-sanctions-and-legal-framework/)). With the March 2026 listings, the horizontal cyber-sanctions regime now covers **19 individuals and 7 entities**.

| Date | Listing regime | Target | Cyber relevance | Source |
|---|---|---|---|---|
| 2026-01-29 | Iran human-rights / military support to Russia (Decision (CFSP) 2026/265) | 15 persons + 6 entities | Not cyber per se, but covers Iranian officials including SCC (Supreme Council of Cyberspace) figures previously listed; tightens IRGC adjacent personnel net. | [Consilium 2026-01-29](https://www.consilium.europa.eu/en/press/press-releases/2026/01/29/iran-council-adopts-new-sanctions-over-serious-human-rights-violations-and-iran-s-continued-support-to-russia-s-war-of-aggression-against-ukraine/) |
| 2026-03-16 | Cyber framework (CFSP 2019/797) | **Integrity Technology Group** (CN) — front for Flax Typhoon, ~65,000 devices compromised across 6 EU states 2022–2023 | First EU listing of a Chinese cyber front-company under the cyber regime. Unprecedented escalation against PRC contractors. | [Consilium 2026-03-16](https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/cyber-attacks-against-the-eu-and-its-member-states-council-sanctions-three-entities-and-two-individuals/) · [The Register](https://www.theregister.com/2026/03/17/eu_iran_cyber_sanctions/) |
| 2026-03-16 | Cyber framework | **Anxun Information Technology** (CN, "i-SOON") + 2 co-founders (individuals) | Hacking-for-hire vendor used against EU and third-country critical infrastructure. Listing the founders personally is a doctrinal shift. | [Consilium 2026-03-16](https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/cyber-attacks-against-the-eu-and-its-member-states-council-sanctions-three-entities-and-two-individuals/) · [France MEAE 2026-03-17](https://www.diplomatie.gouv.fr/en/french-foreign-policy/france-and-europe/events-and-news-relating-to-france-s-european-policy/news/article/cybersecurity-the-eu-sanctions-several-private-cyber-offensive-ecosystem-actors) |
| 2026-03-16 | Cyber framework | **Emennet Pasargad** (IR) | French subscriber DB breach + sale; 2024 Paris Olympics billboard compromise; Swedish SMS-service compromise. EU's most direct call-out of an IRGC-linked operator. | [Consilium 2026-03-16](https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/cyber-attacks-against-the-eu-and-its-member-states-council-sanctions-three-entities-and-two-individuals/) |
| 2026-03-16 | Russia hybrid-threats framework | 4 individuals added for FIMI (foreign information manipulation and interference) | Not pure cyber, but the same operator pool runs both — hybrid listings frequently precede ops-tempo shifts. | [Consilium 2026-03-16 hybrid threats](https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/russian-hybrid-threats-four-individuals-added-to-eu-sanctions-list-for-information-manipulation-activities/) |
| 2026-03-16 | Iran human-rights | Additional 16 persons + 3 entities | Tightens Iran personnel net; bleeds over to cyber via IRGC coverage. | [Consilium 2026-03-16 Iran HR](https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/iran-council-sanctions-an-additional-16-persons-and-three-entities-over-serious-human-rights-violations/) |
| 2026-03-30 | Iran human-rights | Regime extended to April 2027 | Continuation, no new names. | [Consilium 2026-03-30](https://www.consilium.europa.eu/en/press/press-releases/2026/03/30/human-rights-in-iran-council-extends-sanctions-regime-until-april-2027/) |
| 2026-04-23 | Russia (20th package) | 120 additional individual listings + sectoral measures incl. **ban on provision of cybersecurity services to Russia** + Euromore + Pravfond foundation | First time cybersecurity services are themselves a controlled trade. Direct supply-chain disruption of any defensive ops Russia could buy from EU vendors. | [EU Finance Commission](https://finance.ec.europa.eu/news/eu-adopts-20th-package-sanctions-against-russia-2026-04-23_en) · [Crowell & Moring brief](https://www.crowell.com/en/insights/client-alerts/deadlock-broken-eu-adopts-20th-russia-sanctions-package) · [Trade Compliance Hub](https://www.tradecomplianceresourcehub.com/2026/04/24/eus-20th-sanctions-package-on-russia/) |

**Section 2 entry count: 8**

---

## 3. Recent UK OFSI designations, 2026

The UK OFSI Consolidated List was retired on **2026-01-28**; the **UK Sanctions List (UKSL)** maintained by FCDO is now the single authoritative source ([gov.uk single-list guidance](https://www.gov.uk/guidance/moving-to-a-single-list-for-uk-sanctions-designations-28-january-2026)).

Cyber regime as of late Apr 2026 contains **95 designations (82 individuals, 13 organisations)** per OFSI annual review summary ([OFSI Strategy 2026-29 blog](https://ofsi.blog.gov.uk/2026/04/15/ofsi-strategy-2026-29/)).

| Date | Regime | Target / Action | Cyber relevance | Source |
|---|---|---|---|---|
| 2025-12-04 | Cyber + Russia | UK + Poland joint action: GRU + 11 GRU officers designated for hybrid warfare and cyber operations across Europe; Poland indicts FSB-linked Russian | Sets the cyber threat picture going into 2026 — operators named here are already mid-campaign per Polish wiper detections (Dec 29 2025 wind/solar SCADA wipers). | [The Record](https://therecord.media/uk-sanctions-gru-personnel-accused-murder-civilians-ukraine) · [gov.uk GRU profile](https://www.gov.uk/government/publications/profile-gru-cyber-and-hybrid-threat-operations/profile-gru-cyber-and-hybrid-threat-operations) |
| 2025-12-09 | Cyber | 2 new designations | Routine. | [BCL Sanctions Round-Up](https://www.bcl.com/news/sanctions-round-up-ofac-designations-ofsi-s-new-strategy-and-a-rare-uk-prosecution) |
| 2026-Q1 (cumulative) | Cyber | **8 new designations** added during Q1 2026 to the cyber regime | Includes state-backed operatives, ransomware actors, and "ecosystem enablers." Specific names roll into UKSL diff. | [BCL Sanctions Round-Up Mar 2026](https://www.bcl.com/news/sanctions-round-up-key-uk-legal-developments-and-enforcement-trends-march-2026) · [Cyber list](https://www.gov.uk/guidance/cyber-list-of-designations-and-sanctions-notices) |
| 2026-02-06 | Russia | 1 variation, 1 revocation | Adjustments to existing entries. | [Commons Library Briefing CBP-10342](https://researchbriefings.files.parliament.uk/documents/CBP-10342/CBP-10342.pdf) |
| 2026-02-10 | Russia | 1 specification corrected | Administrative. | [Commons Library Briefing CBP-10342](https://researchbriefings.files.parliament.uk/documents/CBP-10342/CBP-10342.pdf) |
| 2026-02-24 | Russia (FCDO Sanctions Notice No. 12 of 2026) | Russia regime maintenance update | Cumulative Russia-regime headline: **3,280 individuals/entities/ships** (3,045 since 2022-02-24). | [BVI FSC FCDO Notice 24-Feb-2026 (PDF)](https://www.bvifsc.vg/sites/default/files/24_february_2026_-fcdo_uk_sanctions_notice-_russia_sanctions_regime_no._12.pdf) · [Commons Library CBP-10342](https://researchbriefings.files.parliament.uk/documents/CBP-10342/CBP-10342.pdf) |
| 2026-02-03 (reported) | Cyber — enforcement | OFSI opens **first-ever investigations** into UK cyber-sanctions breaches (5 financial-services firms) | First enforcement action under the regime since 2020. Signals OFSI's willingness to prosecute ransomware payments to designated actors. | [The Record](https://therecord.media/uk-investing-first-suspected-breach-cyber-sanctions) · [Mishcon de Reya](https://www.mishcon.com/news/ofsi-investigates-first-cyber-sanctions-breaches-after-five-years-of-dormancy) |
| 2026-04-15 | Strategy / structural | OFSI 2026–2029 Strategy published — emphasises AI tooling, crypto investigation, cyber priority | Forward indicator: OFSI is staffing up for cyber. Expect more designations in H2 2026. | [OFSI Strategy 2026-29](https://ofsi.blog.gov.uk/2026/04/15/ofsi-strategy-2026-29/) |

**Section 3 entry count: 8**

---

## 4. Currently sanctioned regimes — cyber retaliation profile

### 4.1 Russia
**Sanctions weight (May 2026):** Heaviest in modern history. EU has now adopted **20 packages** since Feb 2022; the 20th (2026-04-23) added a ban on providing cybersecurity services to Russia. UK has 3,280+ Russia-regime designations. US continues EO 14024 + EO 13694 dual-track.
**Retaliation pattern:** Sandworm/APT44 (GRU Unit 74455) has consistently increased operational tempo in lockstep with sanctions waves — wipers SwiftSlicer (2023), ZEROLOT against Ukrainian energy (Oct 2024–Mar 2025), Polish wind/solar SCADA wipers (2025-12-29). APT28 (Unit 26165) maintains parallel espionage tempo. Pattern: destructive ops cluster within 4–8 weeks after major sanctions packages.
**2024–2026 evidence:** Polish wiper incidents Dec 2025; ongoing Ukrainian-grid attacks; targeting of NATO logistics nodes. UK's Dec 2025 designation of 11 GRU officers is being framed as preceding a Sandworm op-tempo bump.
**Sources:** [Sandworm/APT44 profile (Brandefense)](https://brandefense.io/blog/sandworm-apt-2025/) · [Kyiv Independent on Russia cyber export](https://kyivindependent.com/russia-forged-new-cyber-weapons-to-attack-ukraine-now-theyre-going-international/) · [gov.uk GRU profile](https://www.gov.uk/government/publications/profile-gru-cyber-and-hybrid-threat-operations/profile-gru-cyber-and-hybrid-threat-operations)

### 4.2 Iran
**Sanctions weight (May 2026):** Comprehensive US embargo restored under "Maximum Pressure 2.0"; Iran-related GL refresh on 2026-04-28; CBI re-designation expanded with crypto addresses 2026-04-24. EU has Iran HR regime extended to April 2027 + cyber listings (Emennet Pasargad).
**Retaliation pattern:** Tit-for-tat against perceived aggression. Historical anchors: Op Ababil (DDoS on US banks, 2012), Shamoon (Saudi Aramco, 2012), Sands Casino (2014), election interference 2020/2024. IRGC tasks Emennet Pasargad-like front companies for high-profile influence ops.
**2024–2026 evidence:** APT35 sustained campaigns late-2024 through end-2025 (BellaCPP, PowerLess); CyberAv3ngers (IRGC-linked) targeting US/Israeli OT/water-utility PLCs; **March 2026 attack on US medical-tech firm claimed in retaliation for US strikes** (200K systems wiped, 50TB exfil claimed). Pay2Key.I2P emerged as state-aligned RaaS by 2025. Iran retaliation specifically scales after sanctions tightenings or kinetic events.
**Sources:** [Trellix Iranian Cyber Capability 2026](https://www.trellix.com/blogs/research/the-iranian-cyber-capability-2026/) · [SecAlliance Israel-Iran cyber strategy](https://www.secalliance.com/blog/irans-cyber-strategy-and-the-israel-iran-conflict) · [Industrial Cyber on KELA Iran proxies](https://industrialcyber.co/ransomware/iranian-hackers-target-us-critical-infrastructure-through-ransomware-proxies-kela-warns/) · [CSIS Iran sustained campaign](https://industrialcyber.co/industrial-cyber-attacks/csis-flags-irans-shift-from-episodic-cyberattacks-to-sustained-campaign-against-critical-infrastructure/)

### 4.3 DPRK (North Korea)
**Sanctions weight (May 2026):** Comprehensive US embargo; UN sanctions panel still operational. Mar 2026 OFAC IT-worker designations (Sect. 1) hit revenue side directly.
**Retaliation pattern:** Less "retaliatory" and more **revenue-driven** — DPRK uses cyber for theft to fund WMD programs. Sanctions tightening *accelerates* operational tempo because revenue gap widens. Lazarus, Bluenoroff, Andariel are confirmed RGB-controlled per OFAC.
**2024–2026 evidence:** Bybit heist Feb 2025 ($1.5B — largest single crypto heist on record, FBI confirmed DPRK); KelpDAO Apr 2026 ($290M); $575M+ confirmed stolen in April 2026 alone; Chainalysis attributes $3.4B theft to DPRK in 2025. IT-worker scheme generated ~$800M in 2024 alone.
**Sources:** [FBI IC3 PSA on Bybit](https://www.ic3.gov/psa/2025/psa250226) · [Chainalysis DPRK March 2026](https://www.chainalysis.com/blog/ofac-targets-north-korean-it-workers-crypto-march-2026/) · [38 North digital kleptocracy](https://www.38north.org/2026/01/from-digital-kleptocracy-to-rogue-crypto-superpower/) · [UPI on KelpDAO](https://www.upi.com/Top_News/World-News/2026/04/22/KelpDAO-LayerZero-North-Korea-crypto-hack-theft-Lazarus-Group/6151776848419/)

### 4.4 Belarus
**Sanctions weight (May 2026):** Targeted (not comprehensive). Lukashenko regime, state enterprises, individuals tied to HR abuses + facilitation of Russia's war in Ukraine. EU/UK/US.
**Retaliation pattern:** Limited independent cyber capability. Belarus Cyber Partisans (anti-regime) are noisier than Lukashenko's offensive units. Most "Belarusian" attribution traces back to Russian co-located ops.
**2024–2026 evidence:** Belarusian entity added to EU 17th package (May 2025) for supplying drone components — non-cyber. Limited direct cyber retaliation evidence.
**Sources:** [Sanctions Lawyers OFAC list 2026](https://sanctionslawyers.net/blog-en/ofac-sanctioned-countries-list-2026/) · [Consilium 17th package](https://www.consilium.europa.eu/en/press/press-releases/2025/05/20/russia-s-war-of-aggression-against-ukraine-eu-agrees-17th-package-of-sanctions/)

### 4.5 China — key sanctioned entities
**Sanctions weight (May 2026):** No comprehensive embargo, but escalating entity-level designations. Key cyber-front designations:
- **Integrity Technology Group** (Flax Typhoon) — sanctioned by US (Jan 2025) and EU (Mar 2026).
- **Sichuan Juxinhe Network Technology** (Salt Typhoon) — US Jan 2025 + technology company support designation Jan 2025.
- **Anxun Information Technology / i-SOON** — EU Mar 2026.
- Individuals: **Yin Kecheng**, **Zhou Shuai** (with **Shanghai Heiying Information Technology**) — US Jan/Mar 2025.

**Retaliation pattern:** Less overtly retaliatory; Chinese cyber actors operate on long horizons (Volt Typhoon = pre-positioning for disruption, Salt Typhoon = signals/telecom espionage). Sanctions designations have not measurably altered tempo, but have increased operator OPSEC and front-company churn.
**2024–2026 evidence:** Salt Typhoon US-telecom compromises confirmed Oct 2024+; Volt Typhoon pre-positioning in US critical-infrastructure environments (CRS/CISA reporting); EU's first PRC cyber listings (Mar 2026) suggests next-wave disclosures incoming.
**Sources:** [Treasury jy2792 Salt Typhoon](https://home.treasury.gov/news/press-releases/jy2792) · [Treasury sb0042 Yin Kecheng](https://home.treasury.gov/news/press-releases/sb0042) · [CRS Volt Typhoon brief](https://www.congress.gov/crs_external_products/IF/HTML/IF12798.web.html) · [The Hacker News Jan 2025](https://thehackernews.com/2025/01/us-sanctions-chinese-cybersecurity-firm.html)

### 4.6 Cuba
**Sanctions weight (May 2026):** Comprehensive US embargo restored; SST (State Sponsor of Terrorism) re-designation reinstated by Trump administration; targeted measures on military/intelligence-linked entities.
**Retaliation pattern:** Negligible offensive-cyber capability of its own. Cuba is more often a **host** for Russian/Chinese SIGINT (Lourdes facility legacy) than an actor. Low priority for Prophet's motive model.
**Sources:** [Sanctions Lawyers OFAC 2026 guide](https://sanctionslawyers.net/blog-en/ofac-sanctioned-countries-list-2026/)

### 4.7 Venezuela
**Sanctions weight (May 2026):** Targeted. Significant 2026 thaw: GL 52 issued **2026-03-18** authorising certain PDVSA-related transactions following the ousting of Maduro; broader licensing relaxations underway.
**Retaliation pattern:** No meaningful offensive-cyber program; primarily uses Russian/Cuban technical support. The current direction is *de-escalation*, not new motive.
**Sources:** [OFAC Recent Actions](https://ofac.treasury.gov/recent-actions) · [Sanctions Lawyers 2026](https://sanctionslawyers.net/blog-en/ofac-sanctioned-countries-list-2026/)

### 4.8 Syria
**Sanctions weight (May 2026):** Comprehensive sanctions remain in place but undergoing review post-Assad transition (post-Dec 2024 regime change context). Significant licensing carve-outs being expanded.
**Retaliation pattern:** Syrian Electronic Army (SEA) active 2011–2014 then dormant. No current state-aligned offensive cyber unit of note. Iran-aligned militias operating from Syrian territory carry the cyber load via IRGC channels — covered under §4.2.
**Sources:** [Sanctions Lawyers 2026](https://sanctionslawyers.net/blog-en/ofac-sanctioned-countries-list-2026/)

---

## 5. Pending or threatened sanctions packages

These create *anticipatory* motive — adversaries may pre-position before the package lands. Watch the model's lead-time signal here.

| Signal | Status (as of 2026-05-02) | Anticipatory cyber risk | Source |
|---|---|---|---|
| **Sanctioning Russia Act of 2025** (Graham/Blumenthal, 80+ Senate cosponsors) | Active in Senate. Would impose secondary tariffs/sanctions on countries funding Russia's war. | High. If passed, would massively widen the SDN net to third-country oil buyers (India, China, Turkey-linked). Expect Sandworm-tempo bump. | [Sen. Moran floor speech, Mar 2026](https://www.moran.senate.gov/public/index.cfm/2026/3/video-sen-moran-speaks-on-the-senate-floor-urging-reinstating-sanctions-on-russia-iran) |
| **Trump 50% secondary-tariff threat** on any country supplying weapons to Iran | Announced; not yet operationalised via EO. | Medium-high. Operationalisation would directly squeeze IRGC supply chain → expect Emennet Pasargad-cluster ops escalation. | [Atlantic Council dispatch](https://www.atlanticcouncil.org/dispatches/sanctions-waivers-on-russian-and-iranian-oil-are-set-to-expire/) |
| **Russia oil-tanker GL expiration** (the Mar-12-loaded GL expired 2026-04-11; Iran-equivalent expired 2026-04-19) | Already lapsed; new GLs may or may not follow. | High in the 2–6 week window post-expiration as actors digest the new constraint. | [Atlantic Council](https://www.atlanticcouncil.org/dispatches/sanctions-waivers-on-russian-and-iranian-oil-are-set-to-expire/) · [Mayer Brown March update](https://www.mayerbrown.com/en/insights/publications/2026/03/russia-ukraine-sanctions-update---month-of-march-2026) |
| **Bills prohibiting future OFAC oil GLs for Russia** + 30-day mandate to designate Russian oil/gas/maritime persons | Introduced; unclear voting timeline. | Medium. If enacted, removes Treasury flexibility — adversaries lose negotiating channel, motive for retaliation rises. | [Steptoe Apr 13 2026](https://www.steptoe.com/en/news-publications/stepwise-risk-outlook/sanctions-update-april-13-2026.html) |
| **EU 21st Russia package** (signaled, not yet drafted publicly) | Speculative as of May 2 2026. EU sources suggest energy + financial-services tightening; no cyber-specific previews public. | Medium. The 20th package's cybersecurity-services ban sets precedent; a 21st could extend to managed-detection/SOC services. | [EU Sanctions Helpdesk on 20th](https://eu-sanctions-compliance-helpdesk.europa.eu/20th-package-sanctions-against-russia_en) |
| **OFSI cyber-regime expansion (Q3 2026 signal)** | OFSI 2026-29 Strategy commits to AI tooling + crypto investigators. No specific names announced. | Medium. Capability build-up implies more designations within 6 months. | [OFSI Strategy 2026-29](https://ofsi.blog.gov.uk/2026/04/15/ofsi-strategy-2026-29/) |
| **DPRK additional crypto-mixer / OTC-broker designations** | Strongly signaled by Treasury after Bybit (2025) and KelpDAO (Apr 2026). Specific targets not public. | High. Each round of DPRK financial-route designations historically precedes operational pivot to new mixers within 2–4 weeks. | [Chainalysis 2026 crypto crime report](https://www.chainalysis.com/blog/crypto-sanctions-2026/) · [TRM Labs](https://www.trmlabs.com/resources/blog/beyond-it-worker-fraud-ofacs-latest-dprk-designations-show-broader-sanctions-and-national-security-risk) |

**Section 5 entry count: 7**

---

## Sources I wanted but couldn't access

- **`https://www.consilium.europa.eu/en/press/press-releases/2026/03/16/...` (cyber listings)** — direct WebFetch returned HTTP 403 (likely WAF blocking automated UA). Content reconstructed from secondary law-firm and press coverage (Consilium URL still cited as primary; verify by browser before going to production).
- **`https://ofac.treasury.gov/recent-actions`** — direct WebFetch timed out (60s). Specific SDN-diff names for the 2026-04-23 omnibus and 2026-04-28 Iran-related action could not be enumerated; the per-date OFAC page should be pulled into the data pipeline directly via the SDN delta XML feed rather than HTML scraping.
- **UK Sanctions List (UKSL) machine-readable diff per 2026-Q1** — referenced via [gov.uk page](https://www.gov.uk/government/publications/the-uk-sanctions-list) but per-designation diffs require parsing the ODS/CSV; the **8 new cyber designations Q1 2026** count is from BCL Solicitors' summary, not raw FCDO source. Recommend pulling the UKSL ODS into Prophet's ETL.
- **Iran 2026-04-28 designation specifics** — listed on OFAC Recent Actions index but full press release not reachable via WebFetch.
- **EU 19th package detail** — 2025 Q4, briefly cited; no 2026 cyber-specific carve-outs found in search snippets.

---

## Entry counts

| Section | Entries |
|---|---|
| 1. US OFAC Feb–May 2026 | 10 |
| 2. EU 2026 additions | 8 |
| 3. UK OFSI 2026 | 8 |
| 4. Regime cyber profiles | 8 (Russia, Iran, DPRK, Belarus, China, Cuba, Venezuela, Syria) |
| 5. Pending / threatened | 7 |
| **Total** | **41** |
