# Shared Output Contract

Each research track returns this schema:

## Schema

### `thesis`
One paragraph that states the track's main recommendation.

### `recommended_scope`
Concrete scope choices for V1. Must say what to include and exclude.

### `top_risks`
The most likely ways the current idea or demo path fails.

### `top_cuts`
Capabilities that sound good but should be removed from V1.

### `stage_safe_claims`
Claims that are safe to say on stage because they are either visible, sourced, or explicitly framed as prototype logic.

### `open_questions`
Only unresolved questions that materially affect build or pitch quality.

## Evidence Rules

Every recommendation in this pack should be traceable to one of four evidence classes:

- `real` — implemented behavior in the current repo
- `replayed` — precomputed scenario or cached evidence
- `heuristic` — deterministic logic or curated thresholds
- `mocked` — placeholder UI or staged artifact not backed by runtime logic

No pitch claim should cross those boundaries silently.

## Output Standard

Each memo should also call out:
- the single hero scenario it assumes
- the primary operator persona
- the core claim the user should remember
- the most important cuts required to keep the demo honest
