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

### Pull sanitized output back to the main box

```bash
rsync -avz --remove-source-files \
  prophet-scraper:/srv/scraper/output/ \
  ./world-side/data/chatter/incoming/
```

`--remove-source-files` keeps the scraper's disk clean and ensures records are processed exactly once.

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
- A sanitizer script (later) that runs on the main box, turning `incoming/` files into source-attributed `chatter.jsonl` records suitable for the analogy engine
