# Prophet — Demo Operator Checklist

> One operator drives the Console. One operator is on standby with the recovery laptop and the second terminal. Run this list verbatim. Times below are wall-clock from "judges seated."

---

## T-30 minutes — environment

- [ ] Demo laptop on venue power, not battery. Brightness max. Notifications off (Do Not Disturb).
- [ ] Browser closed except one window: `http://localhost:5173` (Console) and one terminal tab.
- [ ] Wifi joined and confirmed: `curl -s https://www.cisa.gov/ -o /dev/null -w "%{http_code}\n"` returns `200`.
- [ ] Phone hotspot tethered as backup network, **not** active.
- [ ] Scraper machine **off** or on its own network. It does not run during the demo.
- [ ] Demo machine clock matches venue clock (forecasts reference dates).

## T-20 minutes — services up

- [ ] Console dev server running:
  ```
  cd prophet-console && npm run dev
  ```
  Verify: title bar reads "Prophet Console", Perlin hero animates.
- [ ] Control server up if using `DEMO REFRESH`, `LOAD FIXTURE`, or `RUN SCRAPER VM`:
  ```
  cd prophet-console && npm run dev:control
  ```
- [ ] Default stage path: `DEMO REFRESH` + `LOAD FIXTURE`. Use `RUN SCRAPER VM` only if `world-side/scripts/check-scraper-vm.sh` passes.
- [ ] Vulhub sandbox image pre-warmed for the primary CVE:
  ```
  docker compose -f vulhub/log4j/CVE-2021-44228/docker-compose.yml up -d
  ```
  Wait until container reports healthy. Confirm Solr UI loads on `localhost:8983`.
- [ ] Backup CVE pre-warmed in parallel (CVE-2021-41773, fully air-gapped). Even if we don't switch, having it warm saves 30 seconds on recovery.

## T-10 minutes — Console state

- [ ] `PreflightChecklist` panel: all green.
- [ ] `TriageQueue`: top candidate is the demo CVE, ranked.
- [ ] `StrikeWindowTimeline`: golden forecast loaded (`golden-forecast-edge-appliance.json`). At least one window visible with confidence and dates.
- [ ] `ForecastPanel`: `ATTACK METHOD / STRIKE VECTOR` and `TIMEFRAME / STRIKE WINDOW` visible.
- [ ] `AgentStream`: cleared / collapsed, ready to fill.
- [ ] `DefencePanel`: empty or fixture-loaded, depending on the chosen demo path.

## T-2 minutes — operator handoff

- [ ] Speaker has the script open on a phone (not the demo machine).
- [ ] Backup operator has second terminal ready with:
  - `docker logs <container> --tail 20` for "patch applied" proof
  - `nuclei -t <template-path> -u http://localhost:<port>` for re-run proof
- [ ] Network sanity re-check: `curl -s https://oast.pro -o /dev/null -w "%{http_code}\n"` if running interactsh-dependent CVE. If it fails, **switch to backup CVE before going live.**

---

## On stage — demo run order

> Speaker leads, operator clicks. Each step has a fallback noted.

1. **Open with the strike window.** Click `win_1` on `StrikeWindowTimeline`. Highlight the date band, the confidence score, and one historical analogy by name. *Fallback: if click misregisters, scroll to it and use the keyboard.*
2. **Refresh safely.** Click `DEMO REFRESH` to show the forecaster consuming sanitized chatter. *Fallback: if the control server is down, narrate the already-loaded golden fixture.*
3. **Pick the strike vector.** Read the `ATTACK METHOD / STRIKE VECTOR` and `TIMEFRAME / STRIKE WINDOW` deliverables aloud. *Fallback: read the `vector_class` and `target_sector` if the status line is noisy.*
4. **Load cyber defense fixture.** Click `LOAD FIXTURE` in `DefencePanel`. The right rail should show `BLOCKED`, patch diff, and Sigma rule. *Fallback: use the normal replay with `INITIATE PROPHET LOOP`.*
5. **Run the full loop if time allows.** Click `INITIATE PROPHET LOOP`, approve the human gate, and let `AgentStream` fill with reasoning + citations. *Fallback: if stream is slow, use the time to talk about the loop architecture.*
6. **Patch + Sigma render.** `DefencePanel` shows the patch primitive and the Sigma rule. Read the defense summary aloud. *Fallback: if the rule doesn't render, show the cyber-side fixture JSON in the second terminal.*
7. **Blocked result.** The badge flips to BLOCKED from the cyber fixture or replay. Pause on it for two seconds. *Fallback: read the sanitized validation excerpt from the `ExploitPanel`.*

Total target time on stage: **90 seconds for the loop**, plus speaker context.

---

## Recovery scenarios

| Failure | Switch to | Time cost |
|---|---|---|
| Console won't load | Backup laptop with `npm run preview` of the built bundle | ~30 sec |
| Interactsh callback fails (network) | Switch primary CVE to CVE-2021-41773 (air-gapped) | Pre-warmed; ~10 sec |
| Vulhub container won't start | Use the second pre-warmed CVE | ~5 sec |
| Agent stream stalls | Narrate the loop, then show the recorded run from `mockEvents.ts` via `replayController` | ~15 sec |
| Patch render breaks | Switch to the second terminal, show `docker logs` env-var diff | ~10 sec |
| Wifi drops entirely | Hotspot on, refresh; if interactsh-dependent CVE, switch to air-gapped backup | ~30 sec |

If two failures hit in a row, **stop demoing, finish the pitch on the slides, and offer to re-run the loop in person at the booth.** Don't fight the machine on stage.

---

## OPSEC — non-negotiable on demo day

- [ ] **No scraper traffic from the demo machine.** Scraper VM is off or on its own network.
- [ ] **No real victim names, channel names, onion addresses, or operator handles** anywhere on screen — Console, terminal, slides, browser tabs.
- [ ] **No exploit payloads visible** in the Console. The agent log shows reasoning and tool calls, not raw exploit syntax. If a tool-call card shows a payload, collapse it before going on stage.
- [ ] **No `.env.local`, no SSH keys, no session files** open in the editor or terminal history. Clear scrollback before going live.
- [ ] **Forecaster output is the golden fixture.** No live scrape data on stage; that lane is for the post-demo conversation only.

---

## Post-demo — judges at the booth

- [ ] Have the JSON contract (`world-side/INTERFACE.md`) ready to show.
- [ ] Have one alternate CVE loop ready to run on request (CVE-2021-41773 if primary was Log4Shell, vice versa).
- [ ] Have the source-catalog page from `world-side/scraper/ACCESS.md` open to answer scraper questions.
- [ ] Speaker carries one printed copy of `prophet_script.md` for citation lookups during Q&A.

---

## Post-event — within 24 hours

- [ ] Stop and remove all Vulhub containers: `docker compose down` in each warmed directory.
- [ ] Verify no `.env.local`, no SSH keys, no raw scrape artifacts in `git status --ignored` before any subsequent push.
- [ ] Archive the demo recording to a private location; do not upload anywhere that indexes raw agent logs.
