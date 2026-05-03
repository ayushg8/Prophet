# Interface Contract — Cyber Side ↔ World Side

> **Status: DRAFT — Alex feedback incorporated, needs final lock.**
> Owner: Ayush (World Side). Reviewer: Alexander (Cyber Side).
> This file defines the JSON shapes the two halves of Prophet exchange. Locking this lets both halves develop in parallel against mocks.

## What this contract covers

Two directions of handoff:

- **A. Cyber Side → World Side** — the exploit candidate (this draft)
- **B. World Side → Cyber Side / merge layer** — the strike-window + strike-vector forecast (this draft)

Direction A tells World Side what class of exploit Cyber Side is considering. Direction B tells Cyber Side and the merge layer when an adversary would be most likely to spend that capability, which high-level vector class best fits the timing, and why.

---

## Direction A: Cyber Side → World Side (exploit candidate)

Cyber Side emits this when their loop identifies a likely next exploit candidate. World Side consumes it as the trigger to run a strike-window forecast.

For hackathon compliance, `hypothesized_zero_day` means a forecasted vulnerability class or candidate label, not a real undisclosed exploit payload. Demo exploitation remains governed by repo-level scope in `HACKATHON.md`.

### Conceptual buckets

1. **Identity** — what the exploit is
2. **Attack hypothesis** — how the adversary would use it at a high level
3. **Rationale** — why Cyber Side flagged it
4. **Weaponization / public exposure status** — whether the idea overlaps public or observed exploitation
5. **Evidence** — sources supporting claims in the candidate
6. **Metadata** — id and timestamp

### Schema

```jsonc
{
  // metadata
  "candidate_id":   "string",         // unique per emission, e.g. "cs-20260502-a1b2"
  "generated_at":   "string",         // ISO 8601 UTC

  // identity
  "identity": {
    "candidate_type":  "known_cve | representative_cve | hypothesized_zero_day | exploit_class",
                                      // REQUIRED
    "candidate_label": "string",      // REQUIRED — e.g. "exploit_1" or "CVE-2024-3400"
    "cve_id":          "string | null",
                                      // optional; null if no public CVE exists yet
    "cve_class_label": "string",      // REQUIRED for hypothesized/class candidates
                                      // e.g. "edge-device auth bypass"
    "target_product":  "string",      // REQUIRED — product or product family
    "target_component":"string",      // optional — e.g. "admin gateway"
    "cwe_ids":         ["string"]     // optional — e.g. ["CWE-287"]
  },

  // high-level attack hypothesis, not payload instructions
  "attack_hypothesis": {
    "attack_vector":   "string",      // REQUIRED — e.g. "unauthenticated edge access"
    "intended_effect": "control | shutdown | disruption | data_theft | persistence | unknown",
                                      // REQUIRED
    "destructiveness": "non_destructive | disruptive | destructive | unknown",
                                      // REQUIRED
    "narrative":       "string"       // REQUIRED — 1–3 sentences, no exploit steps
  },

  // rationale
  "rationale": {
    "narrative":              "string",
                                      // REQUIRED — 1–3 sentences explaining the pick
    "confidence":             "high | medium | low",
                                      // REQUIRED
    "stage1_priority_score":  "number | null",
                                      // optional; 0.0–1.0 technical/Cyber-side score
    "priority_score_notes":   "string"
                                      // optional; Stage 2 computes geo/timing confidence separately
  },

  // public exposure / weaponization status (optional but preferred)
  "weaponization": {
    "public_check_performed":   "boolean",
    "public_status":            "not_found | public_poc_found | observed_in_wild | known_cve_overlap | unknown",
    "public_poc_available":     "boolean",
    "public_poc_url":           "string | null",
    "nuclei_template_available":"boolean",
    "in_the_wild_observed":     "boolean",
    "kev_listed":               "boolean",
    "epss_score":               "number | null" // 0.0–1.0, null if no CVE exists
  },

  // every non-obvious claim above should point to at least one source
  "source_refs": [
    {
      "label":    "string",
      "url":      "string",
      "supports": "string"            // short phrase naming the claim it supports
    }
  ]
}
```

### Worked example

```json
{
  "candidate_id": "cs-20260502-a1b2",
  "generated_at": "2026-05-02T18:30:00Z",
  "identity": {
    "candidate_type": "hypothesized_zero_day",
    "candidate_label": "exploit_1",
    "cve_id": null,
    "cve_class_label": "edge-device auth bypass",
    "target_product": "ExampleCorp Secure Gateway",
    "target_component": "admin session gateway",
    "cwe_ids": ["CWE-287"]
  },
  "attack_hypothesis": {
    "attack_vector": "Unauthenticated edge-device access leading to remote administrative control.",
    "intended_effect": "shutdown",
    "destructiveness": "disruptive",
    "narrative": "The candidate assumes an adversary can gain control of an exposed gateway and disable service availability without destroying the host."
  },
  "rationale": {
    "narrative": "Cyber Side flagged this because recent public advisories show repeated exploitation of edge and VPN appliances for initial access. The candidate is high value because control of the gateway affects downstream access and availability.",
    "confidence": "medium",
    "stage1_priority_score": 0.72,
    "priority_score_notes": "Technical priority only; World Side computes geopolitical timing separately."
  },
  "weaponization": {
    "public_check_performed": true,
    "public_status": "not_found",
    "public_poc_available": false,
    "public_poc_url": null,
    "nuclei_template_available": false,
    "in_the_wild_observed": false,
    "kev_listed": false,
    "epss_score": null
  },
  "source_refs": [
    {
      "label": "CISA edge-device advisory",
      "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
      "supports": "edge and VPN appliances are repeatedly exploited for initial access"
    }
  ]
}
```

---

## Alex feedback incorporated

From 2026-05-02 discussion:

1. Cyber Side may hypothesize a new candidate from known exploited-vulnerability patterns, then check whether that idea is already public or observed.
2. Cyber Side may emit a local label such as `exploit_1` rather than a CVE. Therefore `cve_id` is optional and `candidate_label` is required.
3. Any Cyber Side score is treated as a technical priority score. World Side owns geopolitical/timing confidence.
4. Cyber Side can provide the expected attack vector and intended effect. For current demo framing, expected effect may be control or shutdown rather than destruction.

## Remaining questions for final lock

Please confirm or modify each:

1. **Are the `candidate_type` enum values right?**
   Proposed: `known_cve`, `representative_cve`, `hypothesized_zero_day`, `exploit_class`.

2. **Can Cyber Side always provide `attack_vector` and `intended_effect`?**
   World Side can run without them, but they materially improve analogy matching.

3. **Will Cyber Side provide `source_refs` for its technical claims?**
   If not, World Side must treat unsupported Stage 1 claims as assumptions and look up sources before surfacing them.

4. **Should `stage1_priority_score` exist now or stay null until later?**
   If no metric is ready, leave it null and put the explanation in `priority_score_notes`.

---

## What stays out of this contract

- Cyber Side's patch / Sigma rule — that's a *separate* output that merges with my forecast at the alert layer, not part of the exploit-candidate handoff
- Cyber Side's sandbox validation result — same, separate output
- Actual exploit payloads, exploit-generation logic, target-control steps, shell commands, or instructions — this contract carries the conclusion, not the procedure
- Internal reasoning chains, tool call logs, etc. — only the conclusions cross the wire

---

## Direction B: World Side → Cyber Side / merge layer (strike forecast)

World Side emits this after receiving an exploit candidate. Cyber Side can use it as **agent context** for defensive scenario selection, demo narrative, and validation prioritization. The merge layer can display it beside the patch / Sigma output.

This is a defensive forecast, not targeting guidance. `strike_vectors` describe adversary tradecraft at a sourced, high-level class level: actor class, target sector, vector class, likely objective, and defensive implication. They must not include exploit payloads, target-control steps, shell commands, named live targets, credential paths, or instructions for gaining access.

### Conceptual buckets

1. **Forecast identity** — id, timestamp, and candidate linkage
2. **Strategic frame** — adversary class, target sector, and scenario assumptions
3. **Strike windows** — ranked date ranges with confidence and cited reasons
4. **Strike vectors** — ranked high-level vector classes with confidence and cited reasons
5. **Evidence** — historical analogies, current context, and source refs
6. **Defensive implications** — what to prioritize in Stage 3 / final alert

### Schema

```jsonc
{
  // metadata
  "forecast_id":        "string",     // unique per forecast, e.g. "ws-20260502-0001"
  "generated_at":       "string",     // ISO 8601 UTC
  "input_candidate_id": "string",     // Cyber Side candidate_id
  "schema_version":     "string",     // e.g. "world_forecast.v0.1"

  // strategic frame
  "strategic_frame": {
    "adversary_class":      "string", // e.g. "PRC-prepositioning-class"
    "target_scope":         "string", // sector/category only, not named live targets
    "geographic_scope":     "string", // e.g. "US federal / DIB infrastructure"
    "forecast_assumptions": ["string"],
    "excluded_uses": [
      "No exploit payloads",
      "No target-control instructions",
      "No named live targets"
    ]
  },

  // ranked strike windows
  "strike_windows": [
    {
      "window_id":       "string",    // e.g. "win_1"
      "rank":            "number",
      "start_date":      "string",    // YYYY-MM-DD
      "end_date":        "string",    // YYYY-MM-DD
      "confidence":      "high | medium | low",
      "confidence_score":"number",    // 0.0–1.0
      "why_this_window": "string",    // 2–4 sentence cited rationale
      "trigger_signals": ["string"],  // sanctions, indictment, election, kinetic move, holiday, etc.
      "historical_analogies": [
        {
          "case_id":          "string",
          "case_name":        "string",
          "pattern_matched":  "string",
          "time_to_burn":     "string",
          "source_ref_ids":   ["string"]
        }
      ],
      "source_ref_ids": ["string"]
    }
  ],

  // ranked strike vectors; high-level only
  "strike_vectors": [
    {
      "vector_id":             "string", // e.g. "vec_1"
      "rank":                  "number",
      "vector_class":          "string", // e.g. "edge-appliance initial access"
      "target_sector":         "string", // e.g. "federal civilian agencies / DIB edge services"
      "likely_objective":      "control | shutdown | disruption | data_theft | persistence | unknown",
      "non_actionable_mechanism":"string",
                                    // high-level description; no exploit procedure
      "candidate_fit":         "string", // how it maps to the Stage 1 candidate
      "confidence":            "high | medium | low",
      "confidence_score":      "number", // 0.0–1.0
      "why_this_vector":       "string",
      "defensive_implication": "string",
      "source_ref_ids":        ["string"]
    }
  ],

  // final synthesis for UI / merge layer
  "summary": {
    "one_line":             "string",
    "recommended_demo_path":"string",
    "stage3_priority":      "string",
    "analyst_notes":        ["string"]
  },

  // every claim above should point here
  "source_refs": [
    {
      "id":       "string",
      "label":    "string",
      "url":      "string",
      "date":     "string",
      "supports": "string"
    }
  ]
}
```

### Worked example

This is a shape example only. Dates and scores below are placeholders until the live current-context files are read and cited.

```json
{
  "forecast_id": "ws-20260502-0001",
  "generated_at": "2026-05-02T23:45:00Z",
  "input_candidate_id": "cs-20260502-a1b2",
  "schema_version": "world_forecast.v0.1",
  "strategic_frame": {
    "adversary_class": "PRC-prepositioning-class",
    "target_scope": "US federal and defense-industrial edge infrastructure",
    "geographic_scope": "US federal / DIB infrastructure",
    "forecast_assumptions": [
      "Stage 1 candidate is an edge-device access class.",
      "Forecast uses sector-level targets only; no named live targets."
    ],
    "excluded_uses": [
      "No exploit payloads",
      "No target-control instructions",
      "No named live targets"
    ]
  },
  "strike_windows": [
    {
      "window_id": "win_1",
      "rank": 1,
      "start_date": "2026-05-15",
      "end_date": "2026-05-31",
      "confidence": "medium",
      "confidence_score": 0.64,
      "why_this_window": "Placeholder: this window would be justified only if current geopolitical context shows a Taiwan, sanctions, indictment, or military-posture trigger. Historical anchors suggest pre-positioned access may sit dormant until a separate trigger arrives.",
      "trigger_signals": ["Taiwan-related escalation", "sanctions or indictment pressure"],
      "historical_analogies": [
        {
          "case_id": "hist_8",
          "case_name": "Volt Typhoon / Taiwan Strait pre-positioning",
          "pattern_matched": "PRC-linked pre-positioning against US critical infrastructure can persist for years and activate around a crisis trigger.",
          "time_to_burn": "multi-year dwell; burn tied to future crisis trigger",
          "source_ref_ids": ["src_hist_8_corpus"]
        }
      ],
      "source_ref_ids": ["src_hist_8_corpus"]
    }
  ],
  "strike_vectors": [
    {
      "vector_id": "vec_1",
      "rank": 1,
      "vector_class": "edge-appliance initial access",
      "target_sector": "federal civilian agencies and defense-industrial perimeter services",
      "likely_objective": "persistence",
      "non_actionable_mechanism": "Adversary uses exposed perimeter infrastructure as an initial-access and persistence point; details remain at the ATT&CK / sector level.",
      "candidate_fit": "Matches a Stage 1 candidate framed as edge-device auth bypass or perimeter control.",
      "confidence": "medium",
      "confidence_score": 0.68,
      "why_this_vector": "Historical corpus anchors include repeated exploitation or pre-positioning through edge and perimeter appliances in PRC-nexus and Russia-linked cases.",
      "defensive_implication": "Prioritize validation around perimeter-device detection, configuration hardening, and Sigma/Nuclei coverage for the selected demo class.",
      "source_ref_ids": ["src_hist_8_corpus", "src_hist_10_corpus"]
    }
  ],
  "summary": {
    "one_line": "If the candidate is an edge-device access class, World Side should rank perimeter-service compromise highest and time it around sourced geopolitical triggers rather than technical readiness alone.",
    "recommended_demo_path": "Use the top strike window and vector as context for selecting a safe localhost validation scenario.",
    "stage3_priority": "Validate detection and blocking for the vector class Cyber Side can safely demonstrate.",
    "analyst_notes": [
      "Confidence must be recomputed after reading current context files.",
      "Vector descriptions are intentionally non-actionable."
    ]
  },
  "source_refs": [
    {
      "id": "src_hist_8_corpus",
      "label": "Historical corpus: Volt Typhoon / Taiwan Strait pre-positioning",
      "url": "world-side/data/historical_pairings.md#8-volt-typhoon--taiwan-strait-pre-positioning-campaign",
      "date": "2026-05-02",
      "supports": "pre-positioned access can sit dormant until a crisis trigger"
    },
    {
      "id": "src_hist_10_corpus",
      "label": "Historical corpus: Ivanti Connect Secure / PRC ops",
      "url": "world-side/data/historical_pairings.md#10-ivanti-connect-secure-unc5221--prc-ops-dec-2023jan-2024",
      "date": "2026-05-02",
      "supports": "edge and VPN appliance exploitation is a recurring access pattern"
    }
  ]
}
```

### Direction B lock questions

Please confirm or modify:

1. **Does Cyber Side need one combined JSON object, or separate `strike_windows.json` and `strike_vectors.json` files?**
   I recommend one object so source refs and confidence scoring stay consistent.

2. **Should `target_scope` stay sector-level only?**
   I recommend yes. Named live targets are not needed for the demo and create unnecessary safety and OPSEC risk.

3. **Should `strike_vectors` be allowed to include ATT&CK technique IDs?**
   I recommend yes if they stay at technique level, not procedure level.

4. **What confidence scale should the UI display?**
   This draft gives both label and `0.0–1.0` score, so the UI can show whichever is faster.

---

## After this is locked

Once Alex signs off, I will:

1. Write `world-side/fixtures/exploit-candidate-*.json` — three mock candidates Cyber Side can develop against and World Side can use to test the analogy engine.
2. Write `world-side/fixtures/world-forecast-*.json` — one or two Direction B outputs the UI and merge layer can consume.
3. Add a Python pydantic model or JSON Schema so both sides validate at runtime, not silently drift.
