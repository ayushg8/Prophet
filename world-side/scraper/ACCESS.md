# Scraper Machine — Access Guide

> **Teammates onboarding:** see [`TEAMMATE_SETUP.md`](./TEAMMATE_SETUP.md) for the 5-minute SSH setup walkthrough. This file is the architectural background and OPSEC reference.

> The scraper runs on an **isolated physical box treated as a sacrificial VM.** It pulls Tor / Telegram / deep-web chatter on behalf of World Side. We never run scraping on the main dev laptop or on the demo machine.

## Why isolate

Three risks we contain by isolation:

1. **Network exposure.** Tor misconfiguration can leak the real client IP. A dedicated machine means a leak cannot deanonymize the team's primary laptop or the demo box.
2. **Content liability.** Some sources host content that is illegal to fetch — never mind store. Raw artifacts stay on the isolated box. Only sanitized, source-attributed records cross to the main dev box.
3. **AUP exposure.** Raw scraped text can trip Anthropic's policy if it ends up in a Claude prompt verbatim. We sanitize *before* anything reaches the agent loop.

## What lives where

| Scraper machine (isolated)                  | Main dev box (running World Side)        |
|---------------------------------------------|------------------------------------------|
| Tor daemon (`tor` package, SOCKS5 :9050)    | Strike-window forecaster + analogy engine |
| Scraping scripts (`httpx` over Tor, Telethon) | Historical campaign corpus               |
| Raw scraped artifacts (encrypted at rest)   | Sanitized chatter records (`chatter.jsonl`) |
| Telegram session files, account credentials | Public source URLs only                  |

The main box never sees raw scrape output. **Sanitization is the boundary.**

## Scraper-side pipeline

The current tracked scraper-side package is `world-side/scraper/scraper_side/`. It is stdlib-only and emits the exact sanitized JSONL shape that `forecaster --chatter` consumes.

Local dry run from repo root:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli \
  --collector cisa-kev \
  --input kve.json \
  --limit 25 \
  --out /tmp/prophet-cisa.jsonl
```

Then feed it into Stage 2:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --chatter /tmp/prophet-cisa.jsonl \
  --out world-side/outputs/world-forecast.json
```

Optional live collection is off by default and limited to allowlisted official HTTPS hosts:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli \
  --collector cisa-kev \
  --live \
  --limit 25 \
  --out /srv/scraper/output/cisa-kev.jsonl
```

On the isolated host, the full run wrapper now uses the checked-in
`bin/collect-once.py` and `bin/sanitize-once.py` boundary scripts. It writes a
collection manifest, a sanitization manifest, and sanitized JSONL only:

```bash
SCRAPER_LIVE=1 SCRAPER_LIMIT=50 /srv/scraper/app/bin/run-once.sh
```

The source inventory lives in `world-side/scraper/config/source_catalog.json`. Only implemented official collectors run by default; high-risk, auth-gated, commercial, movement-tracking, and target-enumeration lanes are disabled until a human explicitly approves the collection plan.

Current collector-ready low-risk feeds:

- CISA KEV JSON
- NVD CVE JSON
- FIRST EPSS API metadata
- State Department travel-advisory RSS
- DOJ cyber-filtered press-release metadata
- Federal Register sanctions/export-control metadata
- OFAC SDN aggregate program/type metadata
- NOAA/NHC Atlantic and Eastern Pacific RSS
- CISA cybersecurity and ICS advisory index metadata
- GitHub Advisory Database metadata
- ProjectDiscovery Nuclei Templates commit metadata, without file bodies or diffs
- Openwall oss-security index metadata
- Fortinet PSIRT RSS headline metadata
- Ivanti security-advisory RSS headline metadata
- Reddit public security-community listing metadata, without authors, comments, or bodies
- ReliefWeb disaster metadata for infrastructure-stress context
- GDELT public article-list metadata for geopolitical/news-cycle context, without article bodies
- GDACS public disaster-alert RSS metadata
- USGS significant-earthquake GeoJSON metadata, without surfacing raw geometry

Cataloged but disabled by default:

- World Monitor Bootstrap API until a key is obtained out-of-band and a sanitizer review is complete
- Shodan and Exa until API-key handling and aggregate-only query review exist
- Telegram public-channel metadata until VM-only collection is approved
- Onion landing/leak/forum/paste metadata until VM-only collection is approved
- AIS/shipping and flight sources until terms, auth, and aggregate-only privacy rules are reviewed
- Mastodon hashtag RSS until a concrete instance/tag expansion plan is reviewed
- Kepler.gl, deck.gl, Wokwi, OSINT Framework, and DEFCON inspiration references as tools/references, not scrape targets

World Monitor can become an optional context enhancer after a `WORLDMONITOR_API_KEY`
is placed in gitignored `.env.local`. Prophet must continue to run without it:
golden forecasts and public/open feeds are the demo path, while Idan-owned
private integrations stay disabled until authorization, terms, and sanitizer
review are complete. World Monitor's public docs describe API-key use with the
`X-WorldMonitor-Key` header and a `/api/bootstrap` endpoint; keep that key
outside git and outside prompts. References: [World Monitor quickstart](https://www.worldmonitor.app/docs/usage-quickstart), [World Monitor platform API](https://www.worldmonitor.app/docs/api-platform).

For Linux scheduling, copy `bin/prophet-scraper.service` and
`bin/prophet-scraper.timer` into `/etc/systemd/system/` on the isolated host,
review the environment values, then enable the timer:

```bash
sudo cp /srv/scraper/app/bin/prophet-scraper.service /etc/systemd/system/
sudo cp /srv/scraper/app/bin/prophet-scraper.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now prophet-scraper.timer
```

For Windows, use `run-once-windows.ps1 -AllEnabled -Live` from Task Scheduler.
The one-source form remains better for smoke tests.

## Collection lanes

The scraper machine can collect from six lanes. Each lane must output the same sanitized JSONL record shape before anything returns to the main box.

| Lane | Examples | Allowed output | Never collect |
|------|----------|----------------|---------------|
| Official government signals | CISA KEV/advisories, NVD, FIRST EPSS, OFAC sanctions, State travel advisories, DOJ releases | URLs, dates, actor/sector tags, analyst-safe summary | None, these are public sources |
| Public technical chatter | GitHub advisory/CVE mentions, public Nuclei template metadata, vendor advisories, public threat-intel feeds | Public URL, product/vector class, safe summary | Proof-of-concept payloads, exploit steps, credentials |
| Public social chatter | Public Telegram channels, public forums, public social posts where access is lawful and non-interactive | Aggregated theme, source type, confidence, source hash/URL if safe | Handles, private links, invite links, personal data, raw post text |
| High-risk metadata only | Public onion landing pages, ransomware leak-site headlines/categories | Metadata-only theme and timestamp, no raw page content | Onion addresses in repo, stolen files, victim dumps, credentials, malware samples, private/paid forums |
| OSINT context feeds | Shodan aggregate counts, Exa public-search summaries, AIS/flight aggregate context | Aggregate context, coarse region/sector labels, analyst-safe summary | Host/IP lists, vessel/flight identifiers, precise movement trails, raw query exports |
| Analysis tooling references | Kepler.gl, deck.gl, Wokwi, OSINT Framework | Tool name, public URL, intended use case | Private exports, secrets, target lists, exploit material |

For demo reliability, prefer official/public feeds first and use high-risk metadata only as a supporting signal. Tor/onion collection is optional and must stay metadata-only.

Telegram/onion/high-risk sources are represented as **manual sanitized JSONL import
lanes**, not as auto-enabled scrapers. The VM-side operator may generate a
local `*.sanitized.jsonl` file with the record shape below and point a temporary
catalog entry at that file. The checked-in catalog keeps these entries disabled
and contains no channel names, invite links, onion addresses, forum endpoints,
or target/victim lists.

## Sanitized record contract

World Side now has a main-box validator for sanitized records in `world-side/forecaster/chatter.py`. Runtime records should be newline-delimited JSON objects shaped like this:

```json
{
  "record_id": "chat_20260502_001",
  "observed_at": "2026-05-02T22:20:00Z",
  "source_type": "telegram_public_channel",
  "collection_tier": "public_chatter",
  "actor_hint": "PRC-nexus",
  "region_hint": "US / Indo-Pacific",
  "target_sector": "US federal and defense edge infrastructure",
  "vector_class": "edge-appliance access and pre-positioning",
  "motive_hint": "summit-timed collection interest",
  "confidence": "medium",
  "summary": "Sanitized analyst-safe summary only.",
  "source_ref": {
    "id": "src_chatter_20260502_001",
    "label": "Sanitized chatter record",
    "url": "sanitized://scraper-record/chat_20260502_001",
    "date": "2026-05-02",
    "supports": "current chatter signal for timing forecast"
  }
}
```

The validator is an allowlist: unsupported keys are rejected. It also rejects raw fields like `raw_text`, `message_text`, `html`, `credentials`, `session`, `password`, and values containing onion addresses, private keys, password material, raw IP addresses, email addresses, invite links, or social handles. Keep real runtime files in gitignored `incoming/` until they are reviewed; use the tracked fixture in `world-side/fixtures/sanitized-chatter-sample.jsonl` for local tests.

## SSH access pattern

Every value in this section is a placeholder. Real values live OUTSIDE the repo:

- Your `~/.ssh/config` on the main box
- A gitignored `world-side/scraper/.env.local`

### One-time: generate a key dedicated to the scraper

```bash
ssh-keygen -t ed25519 -f ~/.ssh/prophet_scraper_ed25519 -C "prophet-scraper"
ssh-copy-id -i ~/.ssh/prophet_scraper_ed25519.pub <SCRAPER_USER>@<SCRAPER_HOST>
```

Keep this key dedicated. Do not reuse a personal SSH key.

### `~/.ssh/config` entry (NOT in this repo)

```
Host prophet-scraper
  HostName       <REAL_IP_OR_LAN_HOSTNAME>
  User           <SCRAPER_USERNAME>
  Port           <SSH_PORT>
  IdentityFile   ~/.ssh/prophet_scraper_ed25519
  IdentitiesOnly yes
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

### Connect

```bash
ssh prophet-scraper
```

### Deploy scraper package after key auth works

Do this only after the dedicated public key has been added to the scraper host and `ssh prophet-scraper` succeeds without a password.

Linux scraper host:

```bash
rsync -avz \
  ./world-side/scraper/ \
  prophet-scraper:/srv/scraper/app/

ssh prophet-scraper 'bash /srv/scraper/app/bin/bootstrap-scraper-machine.sh'
```

Then run a safe official-feed smoke test on the scraper host:

```bash
ssh prophet-scraper \
  'PYTHONPATH=/srv/scraper/app python3 -m scraper_side.cli --collector cisa-kev --live --limit 5 --out /srv/scraper/output/cisa-kev-smoke.jsonl'
```

Windows OpenSSH scraper host:

```bash
tar -czf /tmp/prophet-scraper-deploy.tgz \
  --exclude='__pycache__' \
  --exclude='.env.local' \
  --exclude='*.pyc' \
  -C world-side/scraper .

ssh prophet-scraper "powershell -NoProfile -ExecutionPolicy Bypass -Command \"New-Item -ItemType Directory -Force C:\srv\scraper\app,C:\srv\scraper\output,C:\srv\scraper\logs | Out-Null\""

scp /tmp/prophet-scraper-deploy.tgz prophet-scraper:C:/srv/scraper/prophet-scraper-deploy.tgz

ssh prophet-scraper "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Remove-Item -Recurse -Force C:\srv\scraper\app\* -ErrorAction SilentlyContinue; tar -xzf C:\srv\scraper\prophet-scraper-deploy.tgz -C C:\srv\scraper\app; C:\srv\scraper\app\bin\bootstrap-scraper-windows.ps1\""

ssh prophet-scraper "powershell -NoProfile -ExecutionPolicy Bypass -File C:\srv\scraper\app\bin\run-once-windows.ps1 -Live -Collector cisa-kev -Limit 5 -Out C:\srv\scraper\output\cisa-kev-smoke.jsonl"
```

Run all enabled safe sources with manifests:

```bash
ssh prophet-scraper "powershell -NoProfile -ExecutionPolicy Bypass -File C:\srv\scraper\app\bin\run-once-windows.ps1 -AllEnabled -Live -Limit 50"
```

Pull only sanitized output back:

```bash
rsync -avz \
  prophet-scraper:/srv/scraper/output/cisa-kev-smoke.jsonl \
  ./world-side/data/chatter/incoming/
```

For Windows OpenSSH:

```bash
scp prophet-scraper:C:/srv/scraper/output/cisa-kev-smoke.jsonl \
  ./world-side/data/chatter/incoming/
```

### Pull sanitized output back to the main box

```bash
rsync -avz \
  prophet-scraper:/srv/scraper/output/ \
  ./world-side/data/chatter/incoming/
```

Validate the pulled batch locally before any cleanup:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --chatter ./world-side/data/chatter/incoming/<batch>.jsonl \
  --out /tmp/prophet-validated-forecast.json
```

Only after validation succeeds should the scraper-side file be archived or deleted.

## Password rotation

If any scraper-machine password was pasted into chat, treat it as burned. Rotate it outside this repo using the venue/admin channel or an interactive SSH session with a teammate present. After rotation:

1. Confirm key-based SSH still works for `prophet-scraper`.
2. Remove password auth if the team agrees and the host has a recovery path.
3. Do not write the new password in `.env.local`, docs, commits, screenshots, or prompts.
4. Re-run `git status --ignored` before publishing to make sure no secret-bearing file is visible.

## OPSEC rules — never commit

- Real IP / hostname / port of the scraper machine
- SSH private keys (`*_ed25519`, `*_rsa`, `*.pem`)
- Telegram session files (`*.session`)
- Onion addresses being scraped
- Account credentials, API tokens, bearer tokens
- Raw scrape artifacts (anything in `world-side/data/chatter/raw/` or `incoming/`)

The repo `.gitignore` enforces this. Verify before any push:

```bash
git check-ignore -v world-side/scraper/.env.local
git status --ignored | grep -E "scraper|chatter"
```

Expected: `.env.local` is ignored; `secrets/` and any raw artifact directory are ignored.

## What goes in the repo

- This file (template only — no real values)
- `.env.example` — variable names with no values
- `SETUP.md` — the scraper machine setup checklist (next step, not yet written)
- The sanitized chatter validator and forecaster adapter in `world-side/forecaster/chatter.py`
- Safe fixtures under `world-side/fixtures/` for demo and tests
