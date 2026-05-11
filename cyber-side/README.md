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
| Palantir / Danti / private context | Idan's environment | Idan integrating separately. |
| Forecaster (Direction B) | `world-side/` | Yes. Goldens in `world-side/outputs/`. |
| Console | `prophet-console/` | Yes. Reads goldens by default. |
| Exploit Engine artifact | `cyber-side/fixtures/` | **Yes — fixture path works without Dell.** |
| Exploit prediction portfolio | `cyber-side/predictor.py` | **Yes — deterministic, no API keys.** |

The public demo path is fixture-backed and local-only. Any lab-only validation
scaffolding lives in a private research repo or local archive outside this
public tree.

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

## Operating modes

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

### Mode B — private research validation

Private research validation may emit fresh Direction C artifacts, but the
public repo does not include lab setup scripts, exploit services, or
operator steps for exploitation. The contract in `cyber-side/INTERFACE.md` is
the only shape the Console accepts; anything copied back from a private lab must
pass `cyber-side/validator.py` before use.

Validate any private-lab artifact before showing it in the Console:

```bash
PYTHONPATH=cyber-side python3 -c \
  'import json,sys; from validator import validate_exploit_engine_artifact;
   validate_exploit_engine_artifact(json.loads(open(sys.argv[1]).read()));
   print("OK")' \
  cyber-side/outputs/run-YYYYMMDD-HHMM-edge-appliance.json
```

## What goes into a live run, and what does not

**Goes in:**

- A Direction B forecast from `world-side/outputs/`.
- A Direction A candidate from `world-side/fixtures/`.
- A private, approved vulnerable-by-design sandbox identifier.
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
- Lab-only exploit validation scaffolding must stay in a private research repo
  or local archive outside this public tree.
- The lab is sandbox-only. Do not point the engine at anything else.
