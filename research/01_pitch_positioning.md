# Pitch / Positioning Memo

## thesis
VANTAGE should pitch as one operator console for catching a single maritime deception event before it becomes a larger incident. The winning claim is not "we built a general intelligence platform"; it is "we show commanders what is about to happen, why it matters, and where human approval enters." Narrowing to one replayed Hormuz-style vessel case gives the team one clean story that judges can understand in under a minute.

## recommended_scope
- Single hero scenario: a sanctions-linked tanker approaching the Strait of Hormuz is flagged before a dark event, then contradicted by ownership and movement evidence.
- Primary operator persona: battalion or regional watch intelligence officer responsible for triaging and escalating the alert.
- Core claim: VANTAGE surfaces one early warning, fuses the evidence, and routes it through a human decision gate faster than a reactive dashboard.
- Top 3 demo hooks:
  - A visible countdown or warning window before the vessel "goes dark"
  - A "claims vs reality" contradiction panel that makes deception concrete
  - An audience switcher that turns the same facts into commander-ready language
- Safe differentiators:
  - human approval gate as part of the product, not as an afterthought
  - deception framing around broken invariants, not generic anomaly buzzwords
  - one fused story instead of multiple unrelated alerts

## top_risks
- The project reads like "Palantir but smaller" if the pitch stays too broad.
- The Forecaster promise sounds like unverifiable AI prediction if the logic is not framed as prototype replay or heuristic detection.
- Cross-domain narrative synthesis can sound like hallucinated storytelling unless every supporting event is visible and bounded.

## top_cuts
- Broad "all domains, all adversaries" language
- Live ADS-B or live satellite dependency in the main demo path
- Claims that the system autonomously understands intent across arbitrary feeds
- Any second hero region or parallel scenario

## stage_safe_claims
- "This prototype is built around a replay-first maritime deception scenario."
- "The console shows four reasoning stages: forecast, unmask, synthesize, translate."
- "The operator must approve escalation before the system changes mission state."
- "The same evidence can be rendered differently for different audiences."
- "We designed the demo so it still works if external feeds fail during judging."

## open_questions
- Which exact historical or synthetic vessel incident will become the canonical replay?
- Will the audience switcher stop at Watch Officer, Commander, and Cabinet Secretary, or should it be reduced to two personas for speed?
- Does the team want to claim "predictive" on stage, or use "early warning" as the safer term?

## judge_objections
- "How is this not just Palantir or Maven with an LLM layer?"
- "What is actually real here versus replayed or narrated?"
- "Why should I trust the system not to hallucinate a story?"
