# Technical Feasibility Memo

## thesis
The current repo is a React/Vite console shell, not a full platform. The realistic 24-hour build is a deterministic demo stack: a polished console, precomputed scenario JSON, simple stage transitions, and optional lightweight replay streaming. Anything more ambitious risks spending the hackathon on plumbing instead of the one-minute demo path.

## recommended_scope
- Must build:
  - a single polished console flow in the existing frontend
  - a structured scenario model for alerts, timeline events, evidence, personas, and approval state
  - visible four-agent stages in the UI
  - deterministic transitions between queue, detail, recommendation, and approval
- Stub or cache:
  - agent outputs as structured JSON
  - sanctions and ownership evidence
  - supporting media or cyber event
  - any imagery panel
- Do not build:
  - autonomous multi-agent orchestration runtime
  - live integrations as the critical path
  - generalized ingestion layer for multiple feeds
  - vector memory, graph search, or complex backends
- Recommended architecture:
  - `React console`
  - `scenario JSON fixtures`
  - optional `mock | replay` adapter boundary
  - pure client-side state unless a tiny replay service is needed for event timing

## top_risks
- Time loss on backend setup that does not materially improve the demo.
- UI polish stalls because the team tries to wire real feeds too early.
- The app exposes too many fake surfaces that judges can click into and break.

## top_cuts
- Qdrant, SQLite event memory, and MCP wrappers in V1
- live map libraries if the static theater panel already tells the story
- TAK, Palantir, and Danti as dependencies instead of stretch integrations
- a second page, admin panel, or settings flow

## stage_safe_claims
- "This prototype runs a replayed scenario through a real UI decision workflow."
- "The four agents are represented as explicit reasoning stages in the console."
- "The system is designed with a clean boundary between replayed inputs and future live adapters."
- "The approval state and recommended action are product behaviors, not slides."

## open_questions
- Does the team want the event flow fully client-side, or is a tiny SSE replay layer worth the extra complexity?
- Is the current map-like operational canvas enough, or should the demo spend time on a real map integration?
- Should the Translator be static copy by persona or an optional LLM-backed enhancement?

## 24_hour_execution_risks
- If the team starts on integrations before locking the JSON contract, the UI will churn.
- If the map becomes the centerpiece, it can consume the entire polish budget.
- If the stage path includes nondeterministic latency, rehearsal quality will collapse.
