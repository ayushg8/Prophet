# Exploit Engine — Cyber Side

The Exploit Engine consumes a Forecaster strike forecast (Direction B) plus an
exploit candidate (Direction A) and emits a Direction C artifact: a predicted
exploit class, a non-actionable rationale, a defense (patch + Sigma rule), and
a sandbox validation result. The Console renders that artifact in `ExploitPanel`,
`DefencePanel`, and `AgentStream`.

**Owners:** Idan + Alexander.
**This file owner:** Ayush — defines the contract and the fallback fixture path.

## Demo reality (2026-05-02 → 2026-05-03)

| Asset | Where it lives | Reachable now? |
|---|---|---|
| Dell lab box (Log4Shell sandbox) | Idan's local network | **No.** Network unreachable from dev box. |
| Palantir / Danti / private context | Idan's environment | Idan integrating separately. |
| Forecaster (Direction B) | `world-side/` | Yes. Goldens in `world-side/outputs/`. |
| Console | `prophet-console/` | Yes. Reads goldens by default. |
| Exploit Engine artifact | `cyber-side/fixtures/` | **Yes — fixture path works without Dell.** |
| Exploit prediction portfolio | `cyber-side/predictor.py` | **Yes — deterministic, no API keys.** |

The demo therefore has two operating modes. The fixture mode is the one the
Console reads today; the live mode is what runs once Dell access is restored.

## Alex action item — exploit prediction portfolio

Alex asked for a Python path that consumes geopolitical context and produces:

- 5 hypothesized zero-day exploit classes.
- 5 known one-day / KEV replay classes.
- 2-3 supporting sources per prediction.
- A one-sentence defensive rationale and defense primitive per prediction.

That path is now:

```bash
PYTHONPATH=cyber-side python3 -m predictor \
  --forecast world-side/outputs/generated-forecast-edge-appliance-with-chatter.json \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --out cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json
```

The predictor is deterministic and fixture-safe. It does **not** call OpenAI,
does **not** generate exploit payloads, and does **not** target live systems.
It maps the Forecaster's strike vector/window into class-level exploit
predictions plus defensive patch/detection focus so the demo can show
"why this exploit, why now, why this adversary" without needing API keys.
The local Console control server exposes it at
`POST /api/cyber/prediction-portfolio`, and the Console summarizes the loaded
5+5 portfolio in the AgentStream after the defense fixture is loaded.

## Two operating modes

### Mode A — fixture mode (works right now, no Dell required)

The Console can render the full pipeline using only:

- `world-side/outputs/golden-forecast-edge-appliance.json` (Direction B)
- `cyber-side/fixtures/exploit-engine-output-edge-appliance.json` (Direction C)
- `cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json`
  (safe prediction portfolio for Alex's 5+5 request)

This is the path used for stage rehearsals, screen-recording the demo, and any
contingency where the Dell is unavailable at submission time.

How to verify:

```bash
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests
PYTHONPATH=world-side:world-side/scraper python3 -m unittest discover -s world-side/tests
PYTHONPATH=cyber-side python3 -m predictor \
  --validate-only \
  --forecast cyber-side/fixtures/predicted-exploit-portfolio-edge-appliance.json
```

How to view in the Console (separate workstream — reads Direction C as JSON):

```bash
cd prophet-console
npm install
npm run dev
# open the demo route; ExploitPanel + DefencePanel render the fixture
```

### Mode B — live mode (Dell back online, run by Idan)

When the Dell is reachable, the Exploit Engine runs end-to-end on Idan's
machine and emits a fresh Direction C artifact that the Console picks up
instead of the fixture. The contract in `cyber-side/INTERFACE.md` is the only
shape the Console accepts; anything that validates against
`cyber-side/validator.py` is wire-compatible.

The live mode runs against a **vulnerable-by-design sandbox container** on the
Dell — never against operational infrastructure. The lab files at the repo
root (`log4shell_setup.py`, `VulnerableApp.java`, `Exploit.java`,
`LOG4SHELL_INSTRUCTIONS.md`, `setup_lab.ps1`, etc.) describe the historical
Log4Shell stand-up that Idan provisioned for the rehearsal.

## Operator runbook (Mode B — once Dell access exists)

These commands are the only ones the operator should need on demo day. They
assume Idan has restored SSH to the Dell and that the Log4Shell sandbox
container is running on `[LAB-HOST]:8080`.

> Replace `[LAB-HOST]` with the operator-supplied sandbox hostname. Do not put
> the actual hostname in this file or in any committed artifact.

### 1. Sanity-check the sandbox is up

Run from the Dell, not the dev box:

```bash
# verify the sandbox responds
curl -sS -o /dev/null -w "%{http_code}\n" "http://[LAB-HOST]:8080/"
# expected: 200
```

### 2. Confirm the validation tool is present

```bash
nuclei -version
# expected: nuclei v3.x or later
```

### 3. Run the engine against the forecast

This is the one command that drives the full Mode B loop. The engine reads
both Direction A and Direction B inputs and writes a Direction C artifact:

```bash
# from the Dell, with the engine repo checked out
exploit-engine run \
  --candidate /opt/prophet/world-side/fixtures/exploit-candidate-edge-appliance.json \
  --forecast  /opt/prophet/world-side/outputs/golden-forecast-edge-appliance.json \
  --sandbox   "[LAB-HOST]:8080" \
  --out       /opt/prophet/cyber-side/outputs/run-$(date +%Y%m%d-%H%M)-edge-appliance.json
```

The engine binary is Idan's deliverable; the contract it must satisfy is
`cyber-side/INTERFACE.md`.

### 4. Validate the artifact before showing it on stage

This step is the one the operator must not skip. It catches contract drift,
banned keys, and accidental payload material before anything reaches the
Console:

```bash
PYTHONPATH=cyber-side python3 -c \
  'import json,sys; from validator import validate_exploit_engine_artifact;
   validate_exploit_engine_artifact(json.loads(open(sys.argv[1]).read()));
   print("OK")' \
  cyber-side/outputs/run-YYYYMMDD-HHMM-edge-appliance.json
```

### 5. Hand the artifact to the Console

Copy the validated artifact into the Console's data directory or expose it
behind the existing loader (see `prophet-console/src/data/`). The Console
reads Direction C as static JSON.

### 6. If the live run fails on stage

Drop straight back to Mode A by switching the loader to the fixture in
`cyber-side/fixtures/exploit-engine-output-edge-appliance.json`. The judge sees
the same panels render with the same content; only the audit `emitted_by`
field changes.

## What goes into a live run, and what does not

**Goes in:**

- A Direction B forecast from `world-side/outputs/`.
- A Direction A candidate from `world-side/fixtures/`.
- The vulnerable-by-design sandbox identifier on the Dell.
- A localhost-only validation scope.

**Stays out — non-negotiable:**

- Any non-sandbox target.
- Any real exploit payload bytes in the artifact (the Sigma rule references
  detection patterns; that is detection metadata, not a payload).
- Any operational hostname, IP, credential, or session key.
- Raw LLM reasoning chains or scraper output.

The validator in `cyber-side/validator.py` enforces these as contract rules,
not as suggestions.

## Files

```text
cyber-side/
├── README.md                         ← this file
├── INTERFACE.md                      ← Direction C contract
├── INTEGRATIONS.md                   ← what Idan must provide from Palantir/Danti
├── predictor.py                      ← safe 5 zero-day + 5 one-day portfolio generator
├── validator.py                      ← stdlib-only contract checker
├── fixtures/
│   ├── exploit-engine-output-edge-appliance.json  ← Mode A artifact
│   └── predicted-exploit-portfolio-edge-appliance.json
└── tests/
    ├── test_exploit_engine_artifact.py            ← Direction C fixture tests
    └── test_predictor_portfolio.py                ← prediction portfolio tests
```

## Test commands

```bash
# cyber-side contract + fixture
PYTHONPATH=cyber-side python3 -m unittest discover -s cyber-side/tests

# world-side regression
PYTHONPATH=world-side:world-side/scraper python3 -m unittest discover -s world-side/tests
```

## OPSEC reminders inherited from `AGENTS.md`

- Never commit `.env.local`, SSH keys, session files, or raw scrape output.
- The Dell SSH passwords referenced in `LOG4SHELL_INSTRUCTIONS.md` and
  `qwen_agent.py` must come from out-of-band channels and never from a
  committed file.
- The lab is sandbox-only. Do not point the engine at anything else.
