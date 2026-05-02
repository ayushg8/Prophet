# VANTAGE Synthesis Brief

## Bottom Line
Build VANTAGE V1 as a replay-first maritime deception console for a single Hormuz-style incident. The demo should show one operator catching an early warning, inspecting evidence, switching audience language, and approving escalation. Everything else is secondary.

## Starting Point
- Current implementation baseline: frontend-only console shell in [/Users/macintosh/Documents/hackathon_0526/vantage-console](/Users/macintosh/Documents/hackathon_0526/vantage-console)
- Canonical concept source: [/Users/macintosh/Documents/hackathon_0526/VANTAGE_MASTER.md](/Users/macintosh/Documents/hackathon_0526/VANTAGE_MASTER.md)
- Existing UI launch framing: [/Users/macintosh/Documents/hackathon_0526/UI_LAUNCH_PLAN.md](/Users/macintosh/Documents/hackathon_0526/UI_LAUNCH_PLAN.md)

## Recommended Demo Flow
1. Open on the existing mission console with one dominant critical alert.
2. Show the early-warning state on a sanctions-linked tanker nearing a chokepoint.
3. Open the evidence view and reveal the contradiction:
   - movement anomaly
   - ownership or sanctions mismatch
   - one supporting news or cyber signal
4. Switch the same alert from operator language to commander or cabinet language.
5. End at the human approval gate and commit the recommended action.

## Locked Build Scope

### Real
- polished frontend interaction path in the current React app
- selection, evidence reveal, audience switching, approval state change
- one structured scenario contract shared across UI panels

### Replayed
- hero incident timeline
- agent outputs for the chosen scenario
- sanctions and ownership evidence
- supporting signal and any imagery evidence

### Heuristic
- forecast confidence wording
- contradiction logic such as impossible movement or identity inconsistency
- synthesis recommendation derived from a bounded set of events

### Mocked
- broad live multi-domain ingestion
- autonomous multi-agent runtime if not actually implemented
- any stretch integration not visible in the demo

## Demo Story To Tell
- Primary operator persona: regional watch intelligence officer
- Single hero scenario: sanctions-linked tanker near Hormuz enters an early-warning window, then accumulates contradiction evidence before escalation
- Core audience takeaway: VANTAGE does not try to replace command judgment; it compresses the path from weak signal to human-reviewed action

## Approved Claim Set
- "This prototype demonstrates a replay-first analyst workflow for maritime deception detection."
- "VANTAGE combines early warning, evidence fusion, audience-specific translation, and human approval in one console."
- "The demo is intentionally scoped to one operational pattern so every key step is inspectable."
- "The architecture leaves room for future live adapters without making them dependencies for the demo."

## Claims To Soften Or Drop
- Soften:
  - `prediction` to `early warning` unless the visible logic is strong
  - `agent swarm` to `four reasoning stages` unless runtime traces are real
- Drop:
  - live broad-spectrum multi-domain fusion as a V1 promise
  - parity framing with Palantir, Maven, or Lattice
  - real-time adversary intent inference as a stage claim

## Stretch Goals To Defer
- TAK or iTAK publishing
- Palantir AIP integration
- live ADS-B or satellite queries
- graph memory, vector search, or general ingestion framework
- second hero scenario or second region

## 24-Hour Team Shape
- Person 1: finalize scenario JSON, evidence text, and claim boundaries
- Person 2: harden the main console and detail flow
- Person 3: add persona switching, approval state, and final recommendation behavior
- Person 4: own demo script, fallback path, and rehearsal discipline

## Acceptance Criteria
- The full story runs cleanly in under 60 seconds.
- The UI survives without external network access.
- A skeptical judge can tell which parts are real, replayed, heuristic, or mocked.
- Every important claim is either visible on screen or clearly framed as prototype logic.
- The scope remains one polished flow rather than multiple half-built integrations.

## Verification Against Plan
- `24-hour fit`: yes, if the team stays inside the current frontend and scenario-fixture model
- `offline-safe demo`: yes, if hero assets and evidence are local
- `claim boundaries`: yes, if the team uses the approved claim set and softens prediction language
- `evidence labeling`: yes, if rehearsal script and UI distinguish real, replayed, heuristic, and mocked behaviors
