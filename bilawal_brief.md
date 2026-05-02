# Bilawal Sidhu — Synthesis Brief for VANTAGE

> Source: 16 transcripts pulled from @bilawalsidhu (May 2026) + spatialintelligence.ai. Substack body is paywalled; About page and YouTube transcripts carried the load. **He is, almost literally, the public-facing demo reel for the product we are building.** Read accordingly.

---

## Who he is

Ex-Google PM (AR/VR & 3D Maps; shipped Google Earth photogrammetry, Google's 3D Tiles, and 6 years of VPS work). Now a 1.6M-follower creator + TED Tech Curator & Host + a16z Scout. Email: `bilawal@metaversity.us` (he explicitly invites *"creative tech / defense tech founders"*). His current obsession — almost all 2025–2026 videos — is **4D god's-eye-view reconstructions of geopolitical events using only OSINT**, the exact territory VANTAGE plays in. He recently landed press by "vibe-coding Palantir in a weekend" — Palantir's co-founder publicly responded.

---

## His tech stack (what he names by name)

**Reality capture / splats**
- **Reality Capture** (Epic) — photogrammetry pose / 3D registration; he uses it as the "front end" for splat training.
- **Postshot** — desktop splat trainer on NVIDIA GPUs; his preferred trainer.
- **Brush** — splat trainer for Apple Silicon (M-series Macs).
- **Polycam, Varjo Teleport, Scaniverse (Niantic), Luma** — capture apps.
- **XGrids Lixel K1 (~$5K) and Portal Cam (~$15K)** — LiDAR + 360 RGB capture rigs with RTK GPS and on-device LiDAR-SLAM. *Lichtfeld Studio is mentioned in the user prompt but does not appear in any transcript I pulled — he may use it; can't confirm from this corpus.*
- **SPZ format** (Niantic, now in glTF) for splat compression. **MEGA, HAC++** research formats for further compression.
- **Octane Render 2026** (Otoy) — first commercial path tracer that natively renders + relights Gaussian splats.
- **Infinite Realities "DEIS" stage** — 192-camera 4D capture rig (used in *Superman* 2025).
- **Arcturus** — 4D splats for live sports.

**WorldView / God's Eye View (his app)**
- Browser-based 3D globe (he says **"Google's 3D tiles up in this joint"**) — implies CesiumJS / Google Photorealistic 3D Tiles.
- Live data layers: **OpenSky Network** (commercial flights), **ADS-B Exchange** (military flights, GPS-jamming tiles), **NORAD TLEs** (live satellite tracking), live AIS, **Austin TX public CCTV** projected onto 3D geometry (1 frame/min), **OpenStreetMap** for landmark POIs and road-network particle systems, USGS earthquake feed.
- Visual treatment: shaders for **CRT, NVG night-vision, FLIR/thermal**, bloom, sharpening, configurable post-FX in browser.
- Built using **multiple parallel CLI agents** in tmux-style panels: he names **Claude (4.6), Codex (5.2/5.3), Gemini (3.1)** as the coding LLMs.
- LLM stack he discusses for fusion/orient layer: **Claude 3.5 Sonnet** (reportedly the model running inside Maven), **Anthropic** as the contractor.

**OSINT data sources he references**
- Sentinel-1 (free SAR, 12-day revisit), Capella, ICEYE, Umbra, Synspective, Spire (RF + AIS), Hawkeye 360 (RF geoloc), Maxar/Vantor, Planet, Cosmo-SkyMed, NISAR, Pleiades Neo, WorldView Legion, Persona-3 (RU), Gaofen-11/12 (CN), USA-234 Topaz.
- Adtech-derived geolocation (Candy Crush ad-network as ship-tracking proxy for shadow fleets).
- Vantor "Raptor" terrain-matched VPS for GPS-denied drones.
- Anduril **Pulsar** (passive RF EW), **Lattice** (sensor fusion).

---

## Projects most relevant to VANTAGE

| # | Project | Summary | Technique | Link |
|---|---|---|---|---|
| 1 | **Operation Epic Fury 4D replay** (1.8M views) | Full 4D replay of Iran strike on a 3D globe: sat overhead, civ+mil flights rerouting, GPS-jamming tiles, AIS, kinetic events. Solo, one weekend. | Browser 3D globe + agent swarm capturing OSINT "before the cache clears." | https://youtu.be/0p8o7AeHDzg |
| 2 | **Strait of Hormuz 4D timeline** | Quantifies 92.2% transit drop, correlates with Brent/WTI, identifies Iran's new "toll-booth" route past Larak Island. | Time-scrubbed playback (6 hr/sec); AIS-gap detection; pipeline overlay. | https://youtu.be/ccZzOGnT4Cg |
| 3 | **US–Iran Ceasefire monitor** | Uses transit-event count as ground truth contradicting the official "Strait is open" narrative. | Synced timeline: transits ↔ oil futures. | https://youtu.be/7HEUCLc7aL8 |
| 4 | **Palantir Maven breakdown** (latest) | Explains Maven's OODA loop and says explicitly: *"the only piece that doesn't exist commercially is the fusion layer... that's what I'm building."* | Announces a B2C twin called **Argus**. | https://youtu.be/CHLFl26p7Po |
| 5 | **"Vibe-coded Palantir"** | Build log: realtime sats, OpenSky, ADSBExchange military, projected CCTV, particle-traffic — all browser, all OSINT, parallel-agent CLI workflow. | OSM as geocoder for camera framing. | https://youtu.be/rXvU7bPJ8n4 |
| 6 | **4D Splats Explained** | State of 4D splats in production (Superman, ASAP Rocky, Jurassic World scout). Compression race: SPZ → glTF, MEGA, HAC++. | Vocab primer for our splat-library pitch. | https://youtu.be/3BsKFoU3ucg |
| 7 | **SAR explainer** | InSAR sub-mm deformation, TomoSAR mapped pyramid interiors, Sentinel-1 free, GMTI sats coming 2028. | Science layer behind the Unmasker. | https://youtu.be/UKLuei1CnZY |
| 8 | **WiFi/RF Sensing** | XR + Hawkeye 360 dark-vessel RF geoloc — *"you can go dark on AIS, but you can't go dark on physics."* | Ammunition for Unmasker pitch. | https://youtu.be/0OdR8rRMz3I |
| 9 | **Skyfall GS** | Diffusion-augmented splats from satellite imagery → flyable 3D cities of aerial-denied regions. | Stretch path for splat library beyond drone footage. | https://youtu.be/VWdmXlRpL84 |
| 10 | **Capture-to-splat workflow** | Phone → DSLR → LiDAR rig — Reality Capture → Postshot pipeline. | Production recipe for our pre-baked splats. | https://youtu.be/ctraRclNiZA |

---

## What we should integrate or learn (SCOPE.md deltas)

1. **Steal his visual treatment.** CRT / NVG / FLIR shader presets, sparse-vs-full detection toggle, NORAD-ID-on-hover. ~2 hrs of GLSL, exponential demo polish. Add to §11 as "Spy-aesthetic shader pack."
2. **Satellite-overpass correlation.** His most powerful narrative trick: correlate each ground event with which (and whose) satellite was overhead. NORAD TLEs via Celestrak/N2YO. Trivial cost; *"China's Gaofen-12 was overhead 4 min before this event"* sells the pitch. Add to Synthesizer.
3. **Capture-before-cache-clears.** He sets agent swarms loose at the moment of an event to scrape signals before takedowns. Build a standing OSINT-capture agent that snapshots AIS gaps, ADS-B drops, Telegram, Sentinel tasking when Forecaster confidence crosses threshold. §15 stretch.
4. **Match his free data stack for the demo.** OpenSky (civ flights), ADSBExchange (mil), MarineTraffic/Spire (AIS), Sentinel-1 (free SAR), Hawkeye 360 (RF), USGS (quakes). Keep Danti; add these as fallbacks so we are never demo-blocked.
5. **Splat pipeline = Reality Capture → Postshot** (NVIDIA) or **Brush** (Mac). Update §10 with named tools.
6. **OODA framing for the pitch.** Observe→Forecaster intake; Orient→Synthesizer; Decide→Forecaster+Translator; Act→our human-gated escalation. Lift into README opener.
7. **Killer Q&A line:** *"the only piece that doesn't exist commercially is the fusion layer."* Our exact wedge against Palantir/Lattice — use it.

---

## What we should NOT replicate

1. **Not a vibe-coded one-person demo.** His edge is solo + YouTube. Ours is product-grade chain-of-custody, signed actions, DoD 3000.09, four-persona translator. He doesn't have or want any of that.
2. **Not "spy movie" — decision support.** His framing: *"this looks like a freaking spy movie!"* Ours: *"this is what an S-2 briefs at 0600."* Same pixels, different tagline.
3. **Don't compete on splat quantity.** He has ASAP Rocky rigs; we have ~5 hero-scene splats — used as **evidence** (Unmasker reality reference), not eye candy.
4. **Skip his "Argus" personal-twin angle.** B2C; we are B2G. Stay in lane.
5. **Don't regress to client-only.** He's all-browser because he's solo. We have a real backend (event store, KG, MCP servers). Don't let visual envy collapse the architecture.

---

## Top 5 videos for the team to actually watch

1. **"Palantir's AI Targeting System Running the Iran War"** (`CHLFl26p7Po`, 16 min, 2 days old) — *The* OODA framing + his explicit "fusion layer is what's missing" thesis, which is our wedge. **Mandatory.**
2. **"Ex-Google PM Builds God's Eye to Monitor Iran in 4D"** (`0p8o7AeHDzg`, 11 min, 1.8M views) — The flagship demo. Watch for the satellite-overpass correlation trick, GPS-jamming tile rendering, and how he narrates the cascading no-fly zones. This is the demo *we* are giving in 24 hours.
3. **"Ex-Google Maps PM Vibe Coded Palantir In a Weekend"** (`rXvU7bPJ8n4`, 10 min) — His engineering build log. Note the agent-per-data-source decomposition and the OpenStreetMap-for-camera-framing trick.
4. **"This Satellite Revealed Things We Were Never Meant to See"** (`UKLuei1CnZY`, 14 min) — Best primer on SAR, InSAR, GMTI, and ICEYE/Capella for selling the Unmasker's deception-detection thesis to a non-expert judge.
5. **"Holographic Video is Finally Here. 4D Gaussian Splats Explained!"** (`3BsKFoU3ucg`, 10 min) — Vocabulary check for talking 3D/4D splats credibly + the Hollywood-shipped social proof.

(Honourable mention: `0OdR8rRMz3I` "Your WiFi Can See You" — best one-liner for our pitch: *"You can go dark on AIS, but you can't go dark on physics."*)

---

## Outreach angle

**Yes — but only after we have a 60-sec demo video.** Two asks, in order:

1. **Endorsement / signal-boost.** One retweet to 1.6M in our exact niche > any judge prize. Pitch to `bilawal@metaversity.us`: *"You said the fusion layer is what's missing. We built it as a real product — agent swarm, deception detection, PDF-to-SCIF pipeline — what you can't ship from a weekend vibe-code. 60-sec video below."*
2. **Content collab — the contrast piece.** *"Bilawal vibe-coded the front end. Here's what the back end looks like when a defense-product team builds the same on the same timeline."* He gets a 4-min video; we get 1.6M qualified eyeballs.

**Avoid:** asking for his code/splats/WorldView access (he's monetizing it). Don't ask him to judge or advise. Don't mention the hackathon prize — frame it as a product launch he caught early.

---

*Compiled from yt-dlp auto-subs of 16 videos pulled 2026-05-02. No transcripts were missing. Full transcripts in `/tmp/bilawal_subs/` (will be cleaned up).*
