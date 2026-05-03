# Prophet Research Talking Points

These notes summarize the two papers Alex flagged and translate them into
stage-safe talking points for Prophet. Keep the claims modest: use these as
method inspiration, not as proof that Prophet has solved zero-day prediction.

## Paper 1 — XAI + interoperable zero-day detection

Source: [Interoperability and Explicable AI-based Zero-Day Attacks Detection Process in Smart Community](https://arxiv.org/html/2408.02921v2)

Useful method ideas:

- **Interoperability as detection leverage.** The paper argues that zero-day
  detection improves when security systems share data across layers. Prophet's
  equivalent is the source rail: CISA/KEV, geopolitical calendars, sanctions,
  vendor reports, sanitized chatter, and historical campaign analogies all
  become one forecast object instead of separate dashboards.
- **Intermediate layer before IDPS.** The paper places an ML/XAI layer between
  raw interoperable telemetry and the final intrusion detection/prevention
  layer. Prophet has the same shape: Forecaster and Exploit Predictor sit
  between collection and the Console's defense output.
- **Explainability matters.** The paper uses SHAP-style feature attribution to
  explain which features contributed to attack-pattern and anomaly detection.
  Prophet's current explainability is source-ref based; a future version can
  expose explicit feature weights for the Cyber Pressure Index.
- **Measure detection and operational value.** The paper discusses accuracy,
  false positives, incident response time, attack-surface reduction, and
  efficiency. Those become good evaluation criteria for Prophet beyond "does
  the demo render."

Stage line:

> "We are not just alerting on CVEs. We are building an explainable middle
> layer that fuses interoperable signals into a forecast, then hands defenders
> a ranked window, vector, and defense primitive."

Limits to acknowledge:

- The paper is broad and smart-city/IoE oriented, so we should not imply it
  directly validates Prophet's geopolitical forecasting. It mainly supports
  the architecture pattern: interoperable signals, explainable intermediate
  model, and defensive handoff.

## Paper 2 — Measuring AI agents on multi-step cyber ranges

Source: [Measuring AI Agents' Progress on Multi-Step Cyber Attack Scenarios](https://arxiv.org/html/2603.11214v1)

Useful method ideas:

- **Evaluate chains, not isolated tricks.** The paper measures model progress
  across a 32-step corporate range and a 7-step ICS range. Prophet should frame
  the demo as a chain too: scrape/sanitize -> forecast -> predict class ->
  generate defense -> validate in fixture/sandbox.
- **Milestone scoring.** The paper groups long cyber tasks into milestones and
  measures steps completed. Prophet can score demo readiness similarly:
  Forecaster valid, prediction portfolio valid, Direction C valid, Console
  render valid, defense fixture loaded.
- **Inference-time compute and context compaction matter.** The paper shows
  that longer agent runs with compaction improve progress. This supports our
  choice to use Codex terminal / agent-in-the-loop for Stage 3 rather than a
  brittle API-only app loop.
- **Human-in-the-loop is the realistic threat and defense model.** The paper
  says modest human intervention can help with agent failure modes. Prophet
  embraces that: the operator approves the loop, sees source refs, and keeps
  raw scraper content outside the main box.
- **Active defense should be part of future scoring.** The paper notes that
  their ranges record alerts but do not let defenders block or slow the agent.
  Prophet's differentiator is that the loop ends with patch and Sigma outputs,
  not just attack progress.

Stage line:

> "Modern AI cyber capability is best measured as chained progress through a
> realistic range. Prophet uses that same idea defensively: we chain forecast,
> exploit-class prediction, and zero-day defense generation into one operator
> workflow."

Limits to acknowledge:

- The paper evaluates offensive agent capability in simulated ranges. We should
  cite it to justify sandboxed, milestone-based evaluation, not to claim we
  can autonomously conduct real operations.

## How this maps to today's repo

- `world-side/` implements the interoperable signal layer and strike forecast.
- `cyber-side/predictor.py` implements Alex's 5 zero-day + 5 one-day safe
  prediction portfolio from the Forecaster output.
- `cyber-side/fixtures/exploit-engine-output-edge-appliance.json` is the
  Direction C defense artifact for the console.
- `prophet-console/` makes the chain legible to judges without exposing raw
  scraper data or exploit detail.
