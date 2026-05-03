# Forecaster — World Side

The Forecaster is Prophet's geopolitical intelligence engine. It ingests sanitized chatter and world-event signals, fuses them with a historical campaign corpus, and outputs a **strike window** (when) and **strike vector** (how) for a given exploit candidate.

**Owner:** Ayush

## What It Outputs

Given an exploit candidate JSON from the Exploit Engine, the Forecaster produces a `world_forecast.v0.1` object with:

- `strike_windows` — ranked time windows with confidence, trigger signals, and historical analogies
- `strike_vectors` — ranked attack methods consistent with the geopolitical context
- `strategic_frame` — adversary class, target scope, and forecast assumptions
- `summary` — one-line forecast and recommended demo path

Full schema lives in `INTERFACE.md`.

## Boundaries

- Does not predict specific CVEs or generate exploit code — that is the Exploit Engine's job.
- Does not identify live targets — sector-level only.
- Does not run scraping on the main dev box — collection belongs on the isolated scraper machine.
- Only sanitized JSONL crosses from scraper-side into the forecaster or app.

## Directory Layout

```text
world-side/
├── README.md              ← this file
├── INTERFACE.md           ← JSON contract with Exploit Engine
├── app/                   ← static World Console demo
├── forecaster/            ← Python forecasting engine
├── scraper/               ← isolated scraper package, catalog, and run scripts
├── data/                  ← geopolitical corpus and timing context
├── fixtures/              ← exploit candidate mocks and sanitized chatter sample
└── outputs/               ← golden and generated forecasts
```

## Run The Forecaster

From repo root:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --out world-side/outputs/generated-forecast-edge-appliance.json
```

With sanitized chatter:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --chatter world-side/fixtures/sanitized-chatter-sample.jsonl \
  --out world-side/outputs/generated-forecast-edge-appliance.json
```

Run tests:

```bash
PYTHONPATH=world-side:world-side/scraper python3 -m unittest discover -s world-side/tests
```

## World Console

`world-side/app/` is a static Prophet World Console inspired by World Monitor. It renders:

- Live Source Feed
- Geopolitical Pressure Map
- Cyber Pressure Index
- Forecast Detail Page
- fixture-backed Demo Mode

Run it locally:

```bash
cd world-side
python3 -m http.server 8765
```

Then open `http://localhost:8765/app/`. It uses golden forecasts and sanitized fixtures by default, so it works without live internet or API keys.

The main Vite console in `prophet-console/` also reads World Side forecast data for the broader Prophet demo.

## Scraper

Dry-run a safe local collector:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli \
  --collector cisa-kev \
  --input kve.json \
  --limit 25 \
  --out /tmp/prophet-cisa.jsonl
```

List the loaded source catalog:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.cli --list-sources
```

Current enabled low-risk lanes include official government feeds, vendor advisories, GitHub advisory metadata, Reddit public listing metadata, GDACS, and USGS GeoJSON metadata. World Monitor, Shodan, Exa, Telegram, onion, AIS/flight, ReliefWeb, GDELT, and other private/risky or rate-limited lanes remain disabled unless a human explicitly approves the integration plan.

On isolated hosts:

- Linux: run `scraper/bin/bootstrap-scraper-machine.sh`, then `/srv/scraper/app/bin/run-once.sh`.
- Windows OpenSSH: deploy to `C:\srv\scraper\app`, run `bootstrap-scraper-windows.ps1`, then `run-once-windows.ps1`.

The main React console can trigger a Linux scraper host through
`scripts/run-scraper-vm-workflow.sh` when `prophet-console/control-server.mjs`
is running locally. The workflow uses SSH key auth only, pulls back sanitized
JSONL and the sanitization manifest, then writes a runtime forecast under
`world-side/outputs/runtime/` for the browser session.

Check live VM readiness before the demo:

```bash
world-side/scripts/check-scraper-vm.sh
```

Set `PROPHET_CHECK_RUN_SMOKE=1` to add a safe CISA KEV metadata smoke test.

See `scraper/ACCESS.md` and `scraper/TEAMMATE_SETUP.md` for OPSEC, SSH, and deployment details.
