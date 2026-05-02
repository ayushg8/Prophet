# VANTAGE UI Launch Plan

## Goal

Ship one credible operator console that supports the full VANTAGE story in under 60 seconds:

1. Detect an anomaly.
2. Explain why it matters.
3. Route it through human approval.
4. Show an actioned outcome.

This is a launch plan for a hackathon build, not a full product roadmap.

## Product Shape

Build one primary dashboard, not a multi-page application.

- Left rail: ranked alert queue with one clearly dominant critical alert.
- Center: operational canvas with map or map-like theater view.
- Right or lower section: evidence drill-down, recommendation, and approval controls.
- Top band: mission status, selected audience, scenario label, and review state.

The core experience should feel like one mission console with layered drill-down rather than a set of separate tools.

## Launch-Critical Panels

### 1. Main Operations Console

The opening screen for the demo and the default user workspace.

- Preloaded mission theater
- Live-looking activity
- One high-priority alert above the fold
- Human review state visible without clicking

### 2. Alert Detail And Evidence View

This is where trust is earned.

- Why the alert surfaced
- Timeline of source events
- Cross-domain evidence
- Confidence and provenance

### 3. Agent Insight Stack

Four agents should appear as one assessment pipeline, not four disconnected AI widgets.

- Forecaster: what happens next
- Unmasker: what is deceptive or inconsistent
- Synthesizer: what the combined story means
- Translator: how to reframe it for each audience

### 4. Decision Gate

The approval moment is mandatory because it reinforces human-in-the-loop credibility.

- Approve
- Hold
- Escalate

### 5. Audience Brief Layer

The same alert should re-render for a different audience without changing the underlying facts.

Recommended launch audiences:

- Watch Officer
- Commander
- Cabinet Secretary

## Demo Arc

### 0 to 10 seconds

Open directly on the active console. No login, no blank state, no setup flow.

### 10 to 25 seconds

Open the critical alert and show:

- What happened
- Why the system cares
- Confidence

### 25 to 40 seconds

Reveal evidence fusion:

- Movement anomaly
- Ownership or sanctions contradiction
- Supporting cyber or media signal

### 40 to 52 seconds

Surface the recommendation:

- Escalate to regional watch
- Task additional collection
- Explain why this is the earliest decision point

### 52 to 60 seconds

Approve the recommendation and show the outcome:

- Tasking created
- Decision logged
- Mission state updated

## Build Priorities

### Must Be Real

- UI layout and transitions
- Alert selection flow
- Detail drawer or evidence panel
- Approval state change
- Reliable, clickable demo path

### Can Be Simulated

- Live data feeds
- LLM depth behind summaries
- Streaming volume
- Satellite or external source provenance

Rule: anything a judge can click twice should behave like a real product.

## Technical Recommendation

Start with:

- React
- TypeScript
- Vite
- Local CSS for speed

Add next if time allows:

- `zod` for event validation
- `zustand` for UI state
- `@tanstack/react-query` for live and replay adapters
- `maplibre-gl` or `deck.gl` for the operational canvas

Keep a strict `mock | live` adapter boundary so demo stability is never tied to backend readiness.

## First 6 Hours

### Hour 0 to 1

- Scaffold app
- Replace starter UI
- Lock visual direction

### Hour 1 to 2

- Define mock alerts and event shapes
- Build queue and selected alert state

### Hour 2 to 3

- Build map or theater panel
- Add timeline and evidence sections

### Hour 3 to 4

- Add agent stack
- Add recommendation card

### Hour 4 to 5

- Add approval gate
- Add audience switching labels

### Hour 5 to 6

- Polish the golden demo path
- Pre-seed the scenario replay state
- Rehearse the 60-second flow

## Design Rules

- Serious, restrained, and dense beats flashy.
- Motion should clarify state changes, not decorate them.
- Confidence and provenance should stay near every important claim.
- One focal story is stronger than ten simultaneous alerts.
- If the map becomes a time sink, demote it and protect the queue-to-decision loop.

## Failure Strategy

If live data fails, switch to `Operational Replay`.

Suggested line:

> We designed VANTAGE for degraded environments, so I’m switching to the last verified operational replay. Same workflow, same analyst experience.

That fallback should use the same UI, the same click path, and precomputed assessments where needed.
