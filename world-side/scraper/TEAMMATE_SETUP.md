# Teammate Setup — Scraper Access

> For Alexander, Idan, or anyone else who needs SSH access to the Prophet scraper machine. Follow these once. Total time under 5 minutes.

## What you need from Ayush (out-of-band, e.g. Discord DM)

A file named `.env.local` containing the real host / user / port for the scraper. **Do not paste these values in the public repo or in any channel where they might be logged.**

## Steps

### 1. Drop the env file in place

```bash
cp ~/Downloads/.env.local world-side/scraper/.env.local
```

`.env.local` is gitignored. Confirm with:

```bash
git status
```

It should not appear as a tracked or untracked file. If it does, stop and check `.gitignore`.

### 2. Run the setup script

```bash
bash world-side/scraper/setup-access.sh
```

The script:
- Generates a per-user SSH key at `~/.ssh/prophet_scraper_ed25519` (only if you don't already have one — it never overwrites).
- Adds a `Host prophet-scraper` block to your `~/.ssh/config` (only if not already present).
- Prints your **public** key at the end.

It is idempotent — safe to run twice.

### 3. Send your public key to Ayush

The last block of the script's output is your public key. Copy that whole line and DM it to Ayush. He appends it to the scraper's `~/.ssh/authorized_keys`.

**Send the public key only.** The matching private key file (`~/.ssh/prophet_scraper_ed25519` — no `.pub` extension) never leaves your machine.

### 4. Test the connection

```bash
ssh prophet-scraper
```

You should land in a shell on the scraper box. Type `exit` to disconnect.

## Pulling sanitized chatter back to your box

Once your access is live:

```bash
rsync -avz --remove-source-files \
  prophet-scraper:/srv/scraper/output/ \
  ./world-side/data/chatter/incoming/
```

`world-side/data/chatter/incoming/` is gitignored. Sanitized records get processed locally before they reach the analogy engine — never paste raw scrape output into a Claude prompt.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Permission denied (publickey)` | Ayush hasn't added your public key to `authorized_keys` yet, or you accidentally sent the private key instead of the `.pub` file. |
| `Connection refused` | Scraper machine is off, or you're not on the correct network / VPN. |
| `ssh: Could not resolve hostname` | Bad value in `.env.local`, or DNS / LAN issue. |
| `ERROR: .env.local not found` | You haven't placed the env file at `world-side/scraper/.env.local`. |
| `Host prophet-scraper already in ~/.ssh/config — not modifying.` | Normal on a re-run. If host/user/port changed, edit that block by hand. |

## OPSEC reminders

- **Never commit `.env.local`.** It is gitignored, but always check `git status` before pushing.
- **Never share your private key.** Send only the `.pub` file.
- **Don't run scrapers on your laptop.** Only on the scraper machine itself.
- **Don't paste raw scrape output into Claude.** Sanitize first via the on-host pipeline.

## What lives where (recap)

| Where | What |
|---|---|
| `world-side/scraper/.env.local` | Host/user/port (gitignored, sent by Ayush) |
| `~/.ssh/prophet_scraper_ed25519` | Your private key — never leaves your box |
| `~/.ssh/prophet_scraper_ed25519.pub` | Your public key — you DM this to Ayush |
| `~/.ssh/config` | The `Host prophet-scraper` block |

Full architecture and the why-isolate explanation: see `ACCESS.md`.
