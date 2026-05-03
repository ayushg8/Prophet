# Cyber-Side Integration Asks — Idan's lane

Idan is integrating Palantir / Danti / private context separately. This file
captures exactly what the Exploit Engine needs from those integrations to land
on the Direction C contract without surprises during demo.

The cyber side's job is to consume **already-sanitized** structured data and
emit a Direction C artifact. The cyber side does not call those external
systems directly during the demo — Idan brings the data forward.

## What Idan must provide

### 1. Palantir-derived context (consumed by the engine, not by the Console)

The engine treats Palantir output as a private enrichment layer. From it we need:

| Field | Type | Purpose | Where it lands in Direction C |
|---|---|---|---|
| Adversary class label | string | Cross-check against `forecast.strategic_frame.adversary_class` | Embedded in `predicted_exploit.non_actionable_rationale` |
| Sector pressure score | number 0.0–1.0 | Boosts/dampens `predicted_exploit.confidence_score` | `confidence_score` |
| Sector-level target class | string (no live targets) | Validates that the sandbox replay matches a sector the forecast already names | `non_actionable_rationale` |
| Citation handle | opaque string | Provenance for the run, not a URL | `audit.run_id` suffix only |

**Hard rule:** nothing returned by Palantir gets copied into the artifact
verbatim. Only the four fields above survive the boundary, and only in
sanitized form. No Palantir object IDs, no upstream document text, no
operator-identifying metadata.

### 2. Danti-derived corroboration (optional, used as a tie-breaker)

If Danti provides a structured signal (e.g. corroborating reporting on the
predicted exploit class), Idan should expose it as:

```jsonc
{
  "danti_corroboration": {
    "supports_class": "boolean",         // does Danti agree this exploit class is plausible
    "supports_window": "boolean",        // does Danti agree the strike window is consistent
    "narrative":      "string",          // 1–2 sentences, sanitized
    "as_of":          "ISO 8601 string"
  }
}
```

The engine then folds the narrative into
`predicted_exploit.non_actionable_rationale` after a sanitization pass. The
booleans only nudge confidence — they never override the forecast.

### 3. Private context (anything else Idan brings forward)

Anything that does not fit cleanly into the two slots above is treated as
**not loadable** by the engine. If Idan needs a new field on Direction C,
update `cyber-side/INTERFACE.md` first, then the validator, then the fixture.
Adding ad-hoc keys to the artifact will fail validation.

## What the cyber side will not do

- Make outbound calls to Palantir or Danti from the demo machine. The engine
  reads pre-sanitized JSON Idan stages locally.
- Persist Palantir or Danti data inside the public repo. Anything pulled from
  those systems lives in `.gitignore`d directories on the Dell.
- Surface raw upstream text in the Console. The Console only renders the
  Direction C artifact, which is already sanitized by the validator.

## Handoff format

Idan stages the inputs as three files on the Dell:

```text
/opt/prophet/inputs/
├── candidate-<id>.json          ← Direction A candidate (from Forecaster set)
├── forecast-<id>.json           ← Direction B forecast   (from Forecaster set)
└── private-context-<id>.json    ← Palantir + optional Danti, sanitized to the
                                    fields listed above; gitignored
```

The engine reads all three, runs the sandbox validation, and writes a single
Direction C artifact to `/opt/prophet/cyber-side/outputs/`. That artifact is
the only thing that crosses back to the Console.

## Verification before demo

Before the engine writes a final artifact for the stage, Idan runs:

```bash
PYTHONPATH=cyber-side python3 -c \
  'import json,sys; from validator import validate_exploit_engine_artifact;
   validate_exploit_engine_artifact(json.loads(open(sys.argv[1]).read()));
   print("OK")' \
  /opt/prophet/cyber-side/outputs/<artifact>.json
```

If the validator rejects the artifact, the Console gets the fallback fixture
in `cyber-side/fixtures/exploit-engine-output-edge-appliance.json` instead.

## Open questions (track with Idan)

- Confirm the Palantir handle format Idan settles on, so the validator can be
  tightened from "string" to a specific shape.
- Confirm whether Danti corroboration will be available on demo day or only
  for the post-event writeup.
- Confirm that the Dell's network policy permits the Direction C artifact to
  be served to the Console host (read-only, single JSON file).
