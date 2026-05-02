# Data / Demo Operations Memo

## thesis
The safest demo model is hybrid: one deterministic replayed maritime incident drives the story, while live context exists only as ambient atmosphere. The hero path should not depend on public APIs behaving at show time.

## recommended_scope
- Recommended source mix:
  - historical AIS or AIS-like vessel track for the hero timeline
  - cached sanctions or ownership enrichment
  - one supporting news or cyber signal
  - optional pre-captured imagery if access is already confirmed
- Replay plan:
  - precompute the alert queue, timeline, evidence panel, and recommendation state
  - treat agent outputs as locked artifacts for the hero scenario
  - use the same UI for replay and any ambient live context
- Live vs replay boundary:
  - `replay`: hero alert, evidence trail, recommendation, approval path
  - `live`: background traffic, passive headlines, ambient map motion

## top_risks
- Public API throttling or outage during the demo
- Judges mistaking replay for fake data if the distinction is not framed cleanly
- Overpromising cross-domain fusion with thin or low-confidence supporting evidence

## top_cuts
- live OpenSky or other rate-limited aviation dependencies in the core path
- live satellite lookup on stage
- real-time sanctions joins during the demo
- cyber telemetry unless the team already controls a stable source

## stage_safe_claims
- "The hero flow uses a verified operational replay."
- "The same console can switch between replay and live ambient context."
- "External data is prefetched or cached so the analyst workflow remains stable in degraded conditions."
- "Supporting evidence is intentionally bounded to a small number of receipts."

## open_questions
- Which source will provide the cleanest replayable vessel timeline?
- Will the supporting signal be news, cyber, or both?
- Does the team have confirmed access to any imagery provider worth showing?

## failure_modes
- Quiet or noisy live data ruins the stage timing.
- Source latency creates dead air between clicks.
- A weak evidence item makes the Synthesizer feel like narrative theater.

## operator_checklist
- preload all hero scenario assets locally
- verify the app works offline or with network disruption
- rehearse both `Live Context` and `Operational Replay` paths
- prepare one sentence that explains the replay boundary without sounding defensive

## source_notes
- OpenSky's public FAQ explicitly states the REST API is provided "as is" and that rate limits currently apply to key endpoints, which is why aviation data should stay off the critical demo path.
- OpenSanctions publishes component-level API and data-pipeline status, which makes it better suited to prefetched enrichment than on-stage live matching.
- FreeTAKServer is real and viable for a stretch demo, but it should only be attempted after the main console is deterministic.
