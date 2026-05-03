# Interface Contract — Exploit Engine ↔ Forecaster

This file defines the JSON shapes Prophet's components exchange. Both sides implement against these schemas.

**Direction A:** Exploit Engine → Forecaster (exploit candidate)
**Direction B:** Forecaster → Exploit Engine / Console (strike forecast)
**Direction C:** Exploit Engine → Console (predicted exploit + defense + validation). Defined in `cyber-side/INTERFACE.md`.

---

## Direction A: Exploit Engine → Forecaster

The Exploit Engine emits an exploit candidate when it identifies a likely next zero-day or CVE class. The Forecaster consumes it to generate a strike forecast.

`hypothesized_zero_day` means a forecasted vulnerability class or label, not a real undisclosed exploit payload.

### Schema

```jsonc
{
  "candidate_id":   "string",       // unique per emission, e.g. "cs-20260502-a1b2"
  "generated_at":   "string",       // ISO 8601 UTC

  "identity": {
    "candidate_type":  "known_cve | representative_cve | hypothesized_zero_day | exploit_class",
    "candidate_label": "string",    // e.g. "exploit_1" or "CVE-2024-3400"
    "cve_id":          "string | null",
    "cve_class_label": "string",    // e.g. "edge-device auth bypass"
    "target_product":  "string",
    "target_component":"string",    // optional
    "cwe_ids":         ["string"]   // optional, e.g. ["CWE-287"]
  },

  "attack_hypothesis": {
    "attack_vector":   "string",    // e.g. "unauthenticated edge access"
    "intended_effect": "control | shutdown | disruption | data_theft | persistence | unknown",
    "destructiveness": "non_destructive | disruptive | destructive | unknown",
    "narrative":       "string"     // 1–3 sentences, no exploit steps
  },

  "rationale": {
    "narrative":             "string",  // 1–3 sentences explaining the pick
    "confidence":            "high | medium | low",
    "stage1_priority_score": "number | null",  // 0.0–1.0 technical score
    "priority_score_notes":  "string"
  },

  "weaponization": {
    "public_check_performed":    "boolean",
    "public_status":             "not_found | public_poc_found | observed_in_wild | known_cve_overlap | unknown",
    "public_poc_available":      "boolean",
    "public_poc_url":            "string | null",
    "nuclei_template_available": "boolean",
    "in_the_wild_observed":      "boolean",
    "kev_listed":                "boolean",
    "epss_score":                "number | null"
  },

  "source_refs": [
    {
      "label":    "string",
      "url":      "string",
      "supports": "string"
    }
  ]
}
```

### Example

See `world-side/fixtures/exploit-candidate-edge-appliance.json` for a complete worked example.

---

## Direction B: Forecaster → Exploit Engine / Console

The Forecaster emits a strike forecast after receiving an exploit candidate. The Exploit Engine uses it for defensive scenario selection; the Console displays it alongside the exploit generation stream.

`strike_vectors` are high-level adversary tradecraft descriptions — no exploit payloads, no target-control steps, no named live targets.

### Schema

```jsonc
{
  "forecast_id":        "string",   // e.g. "ws-20260502-0001"
  "generated_at":       "string",   // ISO 8601 UTC
  "input_candidate_id": "string",   // links back to Direction A candidate_id
  "schema_version":     "string",   // e.g. "world_forecast.v0.1"

  "strategic_frame": {
    "adversary_class":      "string",
    "target_scope":         "string",   // sector-level only, no named live targets
    "geographic_scope":     "string",
    "forecast_assumptions": ["string"],
    "excluded_uses": [
      "No exploit payloads",
      "No target-control instructions",
      "No named live targets"
    ]
  },

  "strike_windows": [
    {
      "window_id":       "string",  // e.g. "win_1"
      "rank":            "number",
      "start_date":      "string",  // YYYY-MM-DD
      "end_date":        "string",  // YYYY-MM-DD
      "confidence":      "high | medium | low",
      "confidence_score":"number",  // 0.0–1.0
      "why_this_window": "string",  // 2–4 sentence cited rationale
      "trigger_signals": ["string"],
      "historical_analogies": [
        {
          "case_id":        "string",
          "case_name":      "string",
          "pattern_matched":"string",
          "time_to_burn":   "string",
          "source_ref_ids": ["string"]
        }
      ],
      "source_ref_ids": ["string"]
    }
  ],

  "strike_vectors": [
    {
      "vector_id":               "string",  // e.g. "vec_1"
      "rank":                    "number",
      "vector_class":            "string",  // e.g. "edge-appliance initial access"
      "target_sector":           "string",
      "likely_objective":        "control | shutdown | disruption | data_theft | persistence | unknown",
      "non_actionable_mechanism":"string",  // high-level only, no exploit procedure
      "candidate_fit":           "string",
      "confidence":              "high | medium | low",
      "confidence_score":        "number",  // 0.0–1.0
      "why_this_vector":         "string",
      "defensive_implication":   "string",
      "source_ref_ids":          ["string"]
    }
  ],

  "summary": {
    "one_line":             "string",
    "recommended_demo_path":"string",
    "stage3_priority":      "string",
    "analyst_notes":        ["string"]
  },

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

### Example

See `world-side/outputs/golden-forecast-edge-appliance.json` for a complete worked example with real geopolitical citations.

---

## What stays out of this contract

- Patch / Sigma rule — separate Exploit Engine output, merged at the Console layer.
  See **Direction C** in `cyber-side/INTERFACE.md`.
- Sandbox validation result — separate Exploit Engine output, also Direction C.
- Actual exploit payloads, exploit-generation logic, or target-control instructions
- Internal reasoning chains or tool call logs — only conclusions cross the wire
