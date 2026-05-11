/**
 * Forecast data layer — types and typed constants derived from safe fixtures
 * forecaster fixtures and golden outputs.
 *
 * JSON data is inlined here rather than imported as JSON modules because the
 * project tsconfig uses moduleResolution: "bundler" without resolveJsonModule,
 * and Vite handles JSON natively at bundle time. Inlining keeps tsc happy with
 * zero new config changes.
 */

// ── Direction-A types (defense candidate input) ─────────────────────────────

export type CandidateType =
  | 'known_cve'
  | 'representative_cve'
  | 'hypothesized_zero_day'
  | 'exploit_class';

export type IntendedEffect =
  | 'control'
  | 'shutdown'
  | 'disruption'
  | 'data_theft'
  | 'persistence'
  | 'unknown';

export type Destructiveness =
  | 'non_destructive'
  | 'disruptive'
  | 'destructive'
  | 'unknown';

export type PublicStatus =
  | 'not_found'
  | 'public_poc_found'
  | 'observed_in_wild'
  | 'known_cve_overlap'
  | 'unknown';

export type ConfidenceLabel = 'high' | 'medium' | 'low';

export interface CandidateIdentity {
  candidate_type: CandidateType;
  candidate_label: string;
  cve_id: string | null;
  cve_class_label: string;
  target_product: string;
  target_component?: string;
  cwe_ids: string[];
}

export interface AttackHypothesis {
  attack_vector: string;
  intended_effect: IntendedEffect;
  destructiveness: Destructiveness;
  narrative: string;
}

export interface CandidateRationale {
  narrative: string;
  confidence: ConfidenceLabel;
  stage1_priority_score: number | null;
  priority_score_notes: string;
}

export interface Weaponization {
  public_check_performed: boolean;
  public_status: PublicStatus;
  public_poc_available: boolean;
  public_poc_url: string | null;
  nuclei_template_available: boolean;
  in_the_wild_observed: boolean;
  kev_listed: boolean;
  epss_score: number | null;
}

export interface CandidateSourceRef {
  label: string;
  url: string;
  supports: string;
}

export interface ExploitCandidate {
  candidate_id: string;
  generated_at: string;
  identity: CandidateIdentity;
  attack_hypothesis: AttackHypothesis;
  rationale: CandidateRationale;
  weaponization: Weaponization;
  source_refs: CandidateSourceRef[];
}

// ── Direction-B types (forecaster output) ───────────────────────────────────

export type LikelyObjective =
  | 'control'
  | 'shutdown'
  | 'disruption'
  | 'data_theft'
  | 'persistence'
  | 'unknown';

export interface HistoricalAnalogy {
  case_id: string;
  case_name: string;
  pattern_matched: string;
  time_to_burn: string;
  source_ref_ids: string[];
}

export interface StrikeWindow {
  window_id: string;
  rank: number;
  start_date: string;
  end_date: string;
  confidence: ConfidenceLabel;
  confidence_score: number;
  why_this_window: string;
  trigger_signals: string[];
  historical_analogies: HistoricalAnalogy[];
  source_ref_ids: string[];
}

export interface StrikeVector {
  vector_id: string;
  rank: number;
  vector_class: string;
  target_sector: string;
  likely_objective: LikelyObjective;
  non_actionable_mechanism: string;
  candidate_fit: string;
  confidence: ConfidenceLabel;
  confidence_score: number;
  why_this_vector: string;
  defensive_implication: string;
  source_ref_ids: string[];
}

export interface StrategicFrame {
  adversary_class: string;
  target_scope: string;
  geographic_scope: string;
  forecast_assumptions: string[];
  excluded_uses: string[];
}

export interface ForecastSummary {
  one_line: string;
  recommended_demo_path: string;
  stage3_priority: string;
  analyst_notes: string[];
}

export interface SourceRef {
  id: string;
  label: string;
  url: string;
  date: string;
  supports: string;
}

export interface AssetSeedContext {
  integrated?: boolean;
  asset_count?: number;
  exposure_classes?: string[];
  owner_queues?: string[];
  cve_seed_count?: number;
  package_seed_count?: number;
}

export interface StrikeForecast {
  forecast_id: string;
  generated_at: string;
  input_candidate_id: string;
  schema_version: string;
  strategic_frame: StrategicFrame;
  strike_windows: StrikeWindow[];
  strike_vectors: StrikeVector[];
  summary: ForecastSummary;
  asset_seed_context?: AssetSeedContext;
  source_refs: SourceRef[];
}

// ── Inlined fixture data ────────────────────────────────────────────────────

const candidateEdgeAppliance: ExploitCandidate = {
  candidate_id: 'cs-fixture-edge-appliance-001',
  generated_at: '2026-05-02T23:55:00Z',
  identity: {
    candidate_type: 'exploit_class',
    candidate_label: 'fixture_edge_appliance_access',
    cve_id: null,
    cve_class_label: 'edge-device auth bypass',
    target_product: 'enterprise VPN and secure edge appliance family',
    target_component: 'administrative access plane',
    cwe_ids: ['CWE-287', 'CWE-306'],
  },
  attack_hypothesis: {
    attack_vector:
      'Perimeter-appliance access that could support initial access or persistence at a sector level.',
    intended_effect: 'persistence',
    destructiveness: 'non_destructive',
    narrative:
      'This fixture models a hypothesized edge-appliance access class for defensive forecasting. It intentionally describes only the target class and expected operational effect, with no exploit procedure or live target.',
  },
  rationale: {
    narrative:
      'The defense evidence layer flags this class because recent public reporting and the Prophet corpus both show state-linked actors using VPN, router, and other edge appliances as durable access points. The forecaster uses it to test PRC-style pre-positioning and diplomatic-event timing logic.',
    confidence: 'medium',
    stage1_priority_score: 0.74,
    priority_score_notes:
      'Fixture score for pipeline testing only; forecaster computes geopolitical timing separately.',
  },
  weaponization: {
    public_check_performed: true,
    public_status: 'unknown',
    public_poc_available: false,
    public_poc_url: null,
    nuclei_template_available: false,
    in_the_wild_observed: false,
    kev_listed: false,
    epss_score: null,
  },
  source_refs: [
    {
      label: 'Historical corpus: Volt Typhoon pre-positioning',
      url: 'world-side/data/historical_pairings.md#8-volt-typhoon--taiwan-strait-pre-positioning-campaign',
      supports:
        'edge and SOHO infrastructure can be used for long-dwell pre-positioning against US critical infrastructure',
    },
    {
      label: 'Historical corpus: Ivanti Connect Secure PRC-nexus operations',
      url: 'world-side/data/historical_pairings.md#10-ivanti-connect-secure-unc5221--prc-ops-dec-2023jan-2024',
      supports:
        'enterprise VPN and security appliances are recurring state-linked initial-access targets',
    },
    {
      label: 'CISA AA24-038A',
      url: 'https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a',
      supports:
        'PRC state-sponsored actors maintained access to US critical infrastructure for possible future disruption',
    },
  ],
};

const candidateFinancialTheft: ExploitCandidate = {
  candidate_id: 'cs-fixture-financial-theft-001',
  generated_at: '2026-05-02T23:55:00Z',
  identity: {
    candidate_type: 'exploit_class',
    candidate_label: 'fixture_financial_workflow_theft',
    cve_id: null,
    cve_class_label:
      'financial messaging or digital-asset custody workflow compromise',
    target_product:
      'financial messaging, payment operations, and digital-asset custody workflows',
    target_component: 'transaction approval and settlement workflow',
    cwe_ids: ['CWE-287', 'CWE-522'],
  },
  attack_hypothesis: {
    attack_vector:
      'High-level compromise of financial workflow access used for theft or fraudulent transfer attempts.',
    intended_effect: 'data_theft',
    destructiveness: 'non_destructive',
    narrative:
      'This fixture models a revenue-driven theft scenario for defensive forecasting. It avoids transaction mechanics, exploit steps, and institution-specific targeting.',
  },
  rationale: {
    narrative:
      'The defense evidence layer flags this class when sanctions pressure or cryptocurrency-theft reporting suggests a revenue-motivated actor could spend access against financial workflows. The forecaster uses it to test DPRK/Lazarus-style sanctions and market-window timing logic.',
    confidence: 'medium',
    stage1_priority_score: 0.69,
    priority_score_notes:
      'Fixture score for pipeline testing only; forecaster computes geopolitical timing separately.',
  },
  weaponization: {
    public_check_performed: true,
    public_status: 'unknown',
    public_poc_available: false,
    public_poc_url: null,
    nuclei_template_available: false,
    in_the_wild_observed: false,
    kev_listed: false,
    epss_score: null,
  },
  source_refs: [
    {
      label: 'Historical corpus: Lazarus / Bangladesh Bank SWIFT heist',
      url: 'world-side/data/historical_pairings.md#3-lazarus--bangladesh-bank-swift-heist--sanctions-retaliation-pattern-feb-2016',
      supports:
        'DPRK-linked operations have used financial infrastructure theft as a revenue response to sanctions pressure',
    },
    {
      label: 'Sanctions state: DPRK cyber-fraud and IT-worker sanctions',
      url: 'world-side/data/sanctions_state.md#43-dprk-north-korea',
      supports:
        'DPRK cyber operations are revenue-driven and accelerate when sanctions tighten revenue channels',
    },
    {
      label: 'MITRE ATT&CK Lazarus Group',
      url: 'https://attack.mitre.org/groups/G0032/',
      supports:
        'Lazarus is a documented DPRK-linked threat group associated with financial theft campaigns',
    },
  ],
};

const candidateWiperShutdown: ExploitCandidate = {
  candidate_id: 'cs-fixture-wiper-shutdown-001',
  generated_at: '2026-05-02T23:55:00Z',
  identity: {
    candidate_type: 'exploit_class',
    candidate_label: 'fixture_disruptive_shutdown_access',
    cve_id: null,
    cve_class_label: 'disruptive shutdown or wiper-capable access path',
    target_product:
      'enterprise endpoint, identity, and service-management environments',
    target_component: 'service availability and endpoint management plane',
    cwe_ids: [],
  },
  attack_hypothesis: {
    attack_vector:
      'Pre-positioned access used for disruptive service shutdown or wiper-like effects at a fleet level.',
    intended_effect: 'shutdown',
    destructiveness: 'disruptive',
    narrative:
      'This fixture models a disruptive scenario for timing forecasts without describing how to gain access, move laterally, or deploy payloads. It is intended for safe validation of strike-window and defensive-priority logic.',
  },
  rationale: {
    narrative:
      'The defense evidence layer flags this class when geopolitical triggers suggest an actor may prefer availability disruption over stealthy collection. The forecaster uses it to test Russia/GRU-style sanctions, anniversary, and kinetic-alignment timing logic.',
    confidence: 'medium',
    stage1_priority_score: 0.71,
    priority_score_notes:
      'Fixture score for pipeline testing only; forecaster computes geopolitical timing separately.',
  },
  weaponization: {
    public_check_performed: true,
    public_status: 'unknown',
    public_poc_available: false,
    public_poc_url: null,
    nuclei_template_available: false,
    in_the_wild_observed: false,
    kev_listed: false,
    epss_score: null,
  },
  source_refs: [
    {
      label: 'Historical corpus: WhisperGate and HermeticWiper',
      url: 'world-side/data/historical_pairings.md#5-whispergate--hermeticwiper--russian-invasion-of-ukraine-janfeb-2022',
      supports:
        'Russian GRU-linked wiper activity has been timed to imminent military and diplomatic crisis windows',
    },
    {
      label: 'Historical corpus: NotPetya',
      url: 'world-side/data/historical_pairings.md#1-sandworm--notpetya--ukraine-pre-anniversary-june-2017',
      supports:
        'destructive malware has historically clustered around sanctions and symbolic dates',
    },
    {
      label: 'CISA AA22-057A',
      url: 'https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-057a',
      supports:
        'CISA documented destructive malware targeting Ukrainian organizations around the 2022 invasion',
    },
  ],
};

const forecastEdgeAppliance: StrikeForecast = {
  forecast_id: 'ws-golden-edge-appliance-001',
  generated_at: '2026-05-03T00:05:00Z',
  input_candidate_id: 'cs-fixture-edge-appliance-001',
  schema_version: 'world_forecast.v0.1',
  strategic_frame: {
    adversary_class: 'PRC-prepositioning-class',
    target_scope:
      'US federal, defense-industrial, and critical-infrastructure perimeter services',
    geographic_scope: 'US federal and allied Indo-Pacific defense ecosystem',
    forecast_assumptions: [
      'The forecast candidate is an edge-appliance access class rather than a named CVE.',
      'Forecasting is sector-level only and does not identify live targets.',
      'Current context includes May 2026 US-PRC and Indo-Pacific diplomatic events.',
    ],
    excluded_uses: [
      'No exploit payloads',
      'No target-control instructions',
      'No named live targets',
    ],
  },
  strike_windows: [
    {
      window_id: 'win_1',
      rank: 1,
      start_date: '2026-05-08',
      end_date: '2026-05-18',
      confidence: 'medium',
      confidence_score: 0.67,
      why_this_window:
        'The May 14-15 Trump-Xi summit creates a high-value collection and positioning window around US-PRC negotiations. The historical Volt Typhoon and Ivanti anchors support edge and perimeter infrastructure as a durable PRC-nexus access pattern rather than a one-day burn event.',
      trigger_signals: [
        'Trump-Xi bilateral summit',
        'US-PRC diplomatic collection window',
        'edge-appliance pre-positioning pattern',
      ],
      historical_analogies: [
        {
          case_id: 'hist_8',
          case_name: 'Volt Typhoon / Taiwan Strait pre-positioning',
          pattern_matched:
            'Long-dwell access against US critical infrastructure can be held for a later crisis trigger.',
          time_to_burn: 'multi-year dwell; activation tied to future crisis',
          source_ref_ids: ['src_hist_8'],
        },
        {
          case_id: 'hist_10',
          case_name: 'Ivanti Connect Secure / UNC5221',
          pattern_matched:
            'PRC-nexus actors have repeatedly targeted enterprise edge and VPN appliances across diplomatic and Taiwan-related windows.',
          time_to_burn:
            'weeks of stealth exploitation around public disclosure and Taiwan election timing',
          source_ref_ids: ['src_hist_10'],
        },
      ],
      source_ref_ids: ['src_calendar_trump_xi', 'src_hist_8', 'src_hist_10'],
    },
    {
      window_id: 'win_2',
      rank: 2,
      start_date: '2026-05-26',
      end_date: '2026-06-04',
      confidence: 'medium',
      confidence_score: 0.6,
      why_this_window:
        'The Shangri-La Dialogue and Tiananmen anniversary form an Indo-Pacific defense and political-symbolism cluster. The corpus supports PRC-nexus pre-positioning through edge infrastructure when Taiwan, dissident, or defense-ministry collection incentives rise.',
      trigger_signals: [
        'Shangri-La Dialogue',
        'Tiananmen anniversary',
        'Indo-Pacific defense-ministry collection',
      ],
      historical_analogies: [
        {
          case_id: 'hist_8',
          case_name: 'Volt Typhoon / Taiwan Strait pre-positioning',
          pattern_matched:
            'Pre-positioning against US and allied critical infrastructure is linked to Taiwan-crisis contingency planning.',
          time_to_burn: 'no destructive burn observed; access can remain dormant',
          source_ref_ids: ['src_hist_8'],
        },
      ],
      source_ref_ids: [
        'src_calendar_shangri_la',
        'src_calendar_tiananmen',
        'src_hist_8',
      ],
    },
  ],
  strike_vectors: [
    {
      vector_id: 'vec_1',
      rank: 1,
      vector_class: 'edge-appliance initial access and persistence',
      target_sector:
        'federal civilian agencies, defense contractors, and critical-infrastructure perimeter services',
      likely_objective: 'persistence',
      non_actionable_mechanism:
        'Adversary interest centers on exposed perimeter services as access and observation points; this forecast does not include exploitation details or target-control steps.',
      candidate_fit:
        "Directly matches the fixture candidate's edge-device auth-bypass class and non-destructive persistence effect.",
      confidence: 'medium',
      confidence_score: 0.72,
      why_this_vector:
        'Volt Typhoon and Ivanti anchors both show edge or perimeter appliance access as a recurring state-linked pattern against US and allied infrastructure.',
      defensive_implication:
        'Prioritize detection, inventory, configuration review, and safe localhost validation around the selected perimeter-service class.',
      source_ref_ids: ['src_hist_8', 'src_hist_10', 'src_cisa_aa24_038a'],
    },
    {
      vector_id: 'vec_2',
      rank: 2,
      vector_class: 'living-off-the-land persistence after perimeter access',
      target_sector:
        'critical-infrastructure operators and government-adjacent managed networks',
      likely_objective: 'persistence',
      non_actionable_mechanism:
        'Post-access behavior is treated as high-level administrative-tool abuse and persistence risk, not as a procedural guide.',
      candidate_fit:
        'Fits an edge candidate when the forecast emphasizes pre-positioning rather than immediate disruption.',
      confidence: 'medium',
      confidence_score: 0.61,
      why_this_vector:
        "CISA's Volt Typhoon reporting describes long-term access and living-off-the-land behavior in critical-infrastructure environments.",
      defensive_implication:
        'The localhost replay can validate detections for anomalous administrative activity in a safe toy environment.',
      source_ref_ids: ['src_cisa_aa24_038a', 'src_hist_8'],
    },
  ],
  summary: {
    one_line:
      'For an edge-appliance candidate, the strongest forecast is PRC-style pre-positioning around May 2026 diplomatic and Indo-Pacific defense windows.',
    recommended_demo_path:
      'Use a safe edge-service fixture and show how timing context prioritizes perimeter detection over unsafe output generation.',
    stage3_priority:
      'Validate a defensive block and alert around perimeter-service access indicators in a local demo environment.',
    analyst_notes: [
      'Confidence is medium because the window is diplomatically motivated, while the Volt Typhoon anchor shows access can remain dormant until a future crisis.',
      'All vector descriptions are intentionally non-actionable and sector-level.',
    ],
  },
  source_refs: [
    {
      id: 'src_calendar_trump_xi',
      label: 'Calendar events: Trump-Xi bilateral summit',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports:
        'May 14-15, 2026 US-PRC diplomatic summit is a high-value collection window',
    },
    {
      id: 'src_calendar_shangri_la',
      label: 'Calendar events: Shangri-La Dialogue',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports:
        'May 29-31, 2026 Indo-Pacific defense forum is a defense-ministry collection window',
    },
    {
      id: 'src_calendar_tiananmen',
      label: 'Calendar events: Tiananmen anniversary',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports:
        'June 4 anniversary creates PRC dissident and political-symbolism pressure',
    },
    {
      id: 'src_hist_8',
      label: 'Historical corpus: Volt Typhoon',
      url: 'world-side/data/historical_pairings.md#8-volt-typhoon--taiwan-strait-pre-positioning-campaign',
      date: '2026-05-02',
      supports:
        'PRC-linked pre-positioning against US critical infrastructure can persist for years pending a crisis trigger',
    },
    {
      id: 'src_hist_10',
      label: 'Historical corpus: Ivanti Connect Secure',
      url: 'world-side/data/historical_pairings.md#10-ivanti-connect-secure-unc5221--prc-ops-dec-2023jan-2024',
      date: '2026-05-02',
      supports:
        'PRC-nexus actors have targeted enterprise VPN and edge appliances',
    },
    {
      id: 'src_cisa_aa24_038a',
      label: 'CISA AA24-038A',
      url: 'https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a',
      date: '2024-02-07',
      supports:
        'PRC state-sponsored actors maintained persistent access to US critical infrastructure for possible future disruption',
    },
  ],
};

const forecastFinancialTheft: StrikeForecast = {
  forecast_id: 'ws-golden-financial-theft-001',
  generated_at: '2026-05-03T00:05:00Z',
  input_candidate_id: 'cs-fixture-financial-theft-001',
  schema_version: 'world_forecast.v0.1',
  strategic_frame: {
    adversary_class: 'DPRK-revenue-generation-class',
    target_scope:
      'financial institutions, payment operations, and digital-asset custody workflows',
    geographic_scope: 'US and allied financial ecosystem',
    forecast_assumptions: [
      'The forecast candidate is a workflow-compromise class rather than a named CVE.',
      'The forecast models theft risk at the sector level and does not include transaction instructions.',
      'Current context includes 2026 DPRK sanctions pressure and scheduled financial market events.',
    ],
    excluded_uses: [
      'No exploit payloads',
      'No target-control instructions',
      'No named live targets',
    ],
  },
  strike_windows: [
    {
      window_id: 'win_1',
      rank: 1,
      start_date: '2026-05-12',
      end_date: '2026-06-17',
      confidence: 'medium',
      confidence_score: 0.7,
      why_this_window:
        'The March 2026 DPRK IT-worker sanctions directly targeted revenue channels, and the corpus gives a 30-90 day burn range for DPRK financial theft after revenue-pressure triggers. The June 16-17 FOMC meeting adds a market-stress date inside that sanctions-response band.',
      trigger_signals: [
        'DPRK revenue-channel sanctions',
        'FOMC market event',
        'financial-theft historical pattern',
      ],
      historical_analogies: [
        {
          case_id: 'hist_3',
          case_name: 'Lazarus / Bangladesh Bank SWIFT heist',
          pattern_matched:
            'DPRK-linked theft operations align with sanctions tightening and foreign-currency pressure.',
          time_to_burn: '~30 days from nuclear-test sanctions trigger to SWIFT theft',
          source_ref_ids: ['src_hist_3'],
        },
      ],
      source_ref_ids: [
        'src_sanctions_dprk',
        'src_calendar_fomc_june',
        'src_hist_3',
      ],
    },
    {
      window_id: 'win_2',
      rank: 2,
      start_date: '2026-09-09',
      end_date: '2026-09-18',
      confidence: 'medium',
      confidence_score: 0.62,
      why_this_window:
        'The DPRK Founding Day anniversary and the September FOMC meeting create a second symbolic and market-timing cluster. The calendar file explicitly tags DPRK national-day windows and FOMC meetings as financial-risk signals for Lazarus/APT38-style activity.',
      trigger_signals: [
        'DPRK Founding Day',
        'September FOMC meeting',
        'sanctions-funded revenue pressure',
      ],
      historical_analogies: [
        {
          case_id: 'hist_3',
          case_name: 'Lazarus / Bangladesh Bank SWIFT heist',
          pattern_matched:
            'Revenue-driven DPRK operations prefer financial infrastructure and custody workflows.',
          time_to_burn:
            '30-90 days after revenue-pressure trigger in corpus summary',
          source_ref_ids: ['src_hist_3'],
        },
      ],
      source_ref_ids: [
        'src_calendar_dprk_day',
        'src_calendar_fomc_sept',
        'src_hist_3',
      ],
    },
  ],
  strike_vectors: [
    {
      vector_id: 'vec_1',
      rank: 1,
      vector_class: 'financial-messaging or custody workflow compromise',
      target_sector:
        'banks, payment processors, and digital-asset custody providers',
      likely_objective: 'data_theft',
      non_actionable_mechanism:
        'Adversary interest centers on abusing access to financial workflows for theft; no transaction mechanics, tooling details, or target names are included.',
      candidate_fit:
        "Directly matches the fixture candidate's financial workflow compromise class and revenue objective.",
      confidence: 'medium',
      confidence_score: 0.73,
      why_this_vector:
        'The Bangladesh Bank anchor and DPRK sanctions profile both identify financial theft as the characteristic DPRK cyber response to revenue pressure.',
      defensive_implication:
        'Prioritize monitoring, approval controls, and alerting around abnormal financial workflow behavior in safe simulated data.',
      source_ref_ids: ['src_hist_3', 'src_sanctions_dprk', 'src_mitre_lazarus'],
    },
    {
      vector_id: 'vec_2',
      rank: 2,
      vector_class: 'IT-worker or contractor-access abuse',
      target_sector:
        'financial technology, digital-asset, and payment operations vendors',
      likely_objective: 'persistence',
      non_actionable_mechanism:
        'The vector remains at workforce-access and vendor-risk level without describing impersonation, onboarding, or access procedures.',
      candidate_fit:
        'Fits the candidate when the workflow calls for a non-CVE revenue-access scenario tied to sanctions pressure.',
      confidence: 'medium',
      confidence_score: 0.58,
      why_this_vector:
        'The sanctions and indictment snapshots both identify DPRK IT-worker revenue schemes as active pressure points in 2025-2026.',
      defensive_implication:
        'The localhost replay can demonstrate checks against synthetic contractor-access anomalies rather than unsafe output material.',
      source_ref_ids: ['src_sanctions_dprk', 'src_indictments_dprk_it'],
    },
  ],
  summary: {
    one_line:
      'For a financial-theft candidate, the strongest forecast is DPRK revenue pressure peaking in the May-June 2026 sanctions-response and FOMC window.',
    recommended_demo_path:
      'Use a synthetic financial-workflow fixture and show how sanctions and market dates raise timing confidence.',
    stage3_priority:
      'Validate controls and alerts for abnormal workflow use in a toy financial dataset.',
    analyst_notes: [
      'The enum currently uses data_theft for theft-class operations; downstream code may later add a dedicated financial_theft objective.',
      'All financial vectors are intentionally non-procedural.',
    ],
  },
  source_refs: [
    {
      id: 'src_hist_3',
      label: 'Historical corpus: Lazarus / Bangladesh Bank SWIFT heist',
      url: 'world-side/data/historical_pairings.md#3-lazarus--bangladesh-bank-swift-heist--sanctions-retaliation-pattern-feb-2016',
      date: '2026-05-02',
      supports: 'DPRK-linked financial theft followed sanctions and revenue pressure',
    },
    {
      id: 'src_sanctions_dprk',
      label: 'Sanctions state: DPRK profile and March 2026 IT-worker sanctions',
      url: 'world-side/data/sanctions_state.md#43-dprk-north-korea',
      date: '2026-05-02',
      supports:
        'DPRK cyber operations are revenue-driven and sanctions tightening accelerates tempo',
    },
    {
      id: 'src_calendar_fomc_june',
      label: 'Calendar events: June FOMC meeting',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'June 16-17, 2026 FOMC meeting is a financial market event',
    },
    {
      id: 'src_calendar_dprk_day',
      label: 'Calendar events: DPRK Founding Day',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports:
        'September 9, 2026 DPRK Founding Day is tagged as an anniversary window for DPRK activity',
    },
    {
      id: 'src_calendar_fomc_sept',
      label: 'Calendar events: September FOMC meeting',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'September 15-16, 2026 FOMC meeting is a financial market event',
    },
    {
      id: 'src_indictments_dprk_it',
      label: 'Indictments state: DPRK IT-worker scheme defendants',
      url: 'world-side/data/indictments_state.md#18-four-north-korean-it-worker-scheme-defendants-charged--june-2025',
      date: '2026-05-02',
      supports: 'DPRK IT-worker schemes are a documented revenue-generation pathway',
    },
    {
      id: 'src_mitre_lazarus',
      label: 'MITRE ATT&CK Lazarus Group',
      url: 'https://attack.mitre.org/groups/G0032/',
      date: '2026-05-02',
      supports: 'Lazarus is a documented DPRK-linked threat group',
    },
  ],
};

const forecastWiperShutdown: StrikeForecast = {
  forecast_id: 'ws-golden-wiper-shutdown-001',
  generated_at: '2026-05-03T00:05:00Z',
  input_candidate_id: 'cs-fixture-wiper-shutdown-001',
  schema_version: 'world_forecast.v0.1',
  strategic_frame: {
    adversary_class: 'Russia-GRU-disruption-class',
    target_scope:
      'government, defense-industrial, and critical-infrastructure availability surfaces',
    geographic_scope: 'US, NATO, and Ukraine-aligned infrastructure',
    forecast_assumptions: [
      'The forecast candidate is a disruptive shutdown class rather than an implementation description.',
      'Forecasting remains sector-level and defensive.',
      'Current context includes recent Russia sanctions pressure and upcoming NATO and symbolic-date windows.',
    ],
    excluded_uses: [
      'No exploit payloads',
      'No target-control instructions',
      'No named live targets',
    ],
  },
  strike_windows: [
    {
      window_id: 'win_1',
      rank: 1,
      start_date: '2026-05-21',
      end_date: '2026-06-18',
      confidence: 'medium',
      confidence_score: 0.68,
      why_this_window:
        'The sanctions snapshot says Russia destructive operations cluster 4-8 weeks after major sanctions packages, and the EU 20th Russia package landed on April 23, 2026. This window also includes Russia Day on June 12, which the calendar treats as a symbolic cyber-activation date.',
      trigger_signals: [
        'EU 20th Russia sanctions package',
        '4-8 week sanctions-response band',
        'Russia Day symbolic window',
      ],
      historical_analogies: [
        {
          case_id: 'hist_1',
          case_name: 'Sandworm / NotPetya',
          pattern_matched:
            'Sanctions and symbolic dates preceded destructive malware deployment in the Ukraine context.',
          time_to_burn:
            '4-6 weeks from sanctions extension and calendar symbolism to release',
          source_ref_ids: ['src_hist_1'],
        },
        {
          case_id: 'hist_5',
          case_name: 'WhisperGate / HermeticWiper',
          pattern_matched:
            'Wiper-class deployment aligned to crisis and military-timing windows.',
          time_to_burn: 'hours to days around final crisis trigger',
          source_ref_ids: ['src_hist_5'],
        },
      ],
      source_ref_ids: [
        'src_sanctions_russia',
        'src_calendar_russia_day',
        'src_hist_1',
        'src_hist_5',
      ],
    },
    {
      window_id: 'win_2',
      rank: 2,
      start_date: '2026-07-05',
      end_date: '2026-07-10',
      confidence: 'medium',
      confidence_score: 0.61,
      why_this_window:
        'The July 7-8 NATO Summit is a defense-policy event likely to draw Russian collection, signaling, and hacktivist-adjacent pressure. The historical wiper anchors support disruption as a plausible class only when paired with a separate sanctions, military, or symbolic trigger.',
      trigger_signals: [
        'NATO Summit',
        'defense-ministry attention window',
        'Russia sanctions background pressure',
      ],
      historical_analogies: [
        {
          case_id: 'hist_5',
          case_name: 'WhisperGate / HermeticWiper',
          pattern_matched:
            'Disruptive cyber effects can align with broader military and diplomatic pressure.',
          time_to_burn: 'hours to days around final trigger',
          source_ref_ids: ['src_hist_5'],
        },
      ],
      source_ref_ids: [
        'src_calendar_nato',
        'src_sanctions_russia',
        'src_hist_5',
      ],
    },
  ],
  strike_vectors: [
    {
      vector_id: 'vec_1',
      rank: 1,
      vector_class: 'disruptive endpoint or service-availability shutdown',
      target_sector:
        'government services, defense-industrial support networks, and critical-infrastructure operators',
      likely_objective: 'shutdown',
      non_actionable_mechanism:
        'The vector describes only the strategic effect: disruption of service availability after prior access. It omits access paths, lateral movement, payload details, and target names.',
      candidate_fit:
        "Directly matches the fixture candidate's shutdown effect and disruptive destructiveness label.",
      confidence: 'medium',
      confidence_score: 0.7,
      why_this_vector:
        'NotPetya, WhisperGate, and HermeticWiper provide corpus anchors for Russian-linked destructive or disruptive operations around sanctions, symbolism, and crisis timing.',
      defensive_implication:
        'Prioritize recovery readiness, destructive-action detection, and safe simulation of availability-loss alerts.',
      source_ref_ids: ['src_hist_1', 'src_hist_5', 'src_cisa_aa22_057a'],
    },
    {
      vector_id: 'vec_2',
      rank: 2,
      vector_class: 'hacktivist-front disruption and deniable signaling',
      target_sector:
        'NATO-aligned public services and government-facing web infrastructure',
      likely_objective: 'disruption',
      non_actionable_mechanism:
        'The vector remains at public-service disruption and information-signaling level without identifying systems or methods.',
      candidate_fit:
        'Fits a shutdown candidate when political signaling matters more than durable espionage.',
      confidence: 'low',
      confidence_score: 0.49,
      why_this_vector:
        'The indictment and sanctions snapshots describe Russia-aligned criminal and hacktivist ecosystems, but this fixture does not include live chatter, so confidence stays low.',
      defensive_implication:
        'Use only as a secondary scenario for UI narrative unless current sanitized chatter raises confidence.',
      source_ref_ids: ['src_indictments_carr', 'src_sanctions_russia'],
    },
  ],
  summary: {
    one_line:
      'For a wiper/shutdown candidate, the strongest forecast is a Russia-linked disruption window from late May to mid-June 2026, driven by recent sanctions and symbolic timing.',
    recommended_demo_path:
      'Use a local synthetic service and demonstrate detection, blocking, and recovery messaging for disruption without payload details.',
    stage3_priority:
      'Validate alerts and rollback controls for service-availability loss in a safe demo environment.',
    analyst_notes: [
      'Confidence is medium because sanctions and calendar triggers align, but no sanitized chatter fixture is present.',
      'The forecast is defensive and intentionally excludes any deployment mechanics.',
    ],
  },
  source_refs: [
    {
      id: 'src_hist_1',
      label: 'Historical corpus: NotPetya',
      url: 'world-side/data/historical_pairings.md#1-sandworm--notpetya--ukraine-pre-anniversary-june-2017',
      date: '2026-05-02',
      supports: 'destructive malware historically aligned with sanctions and symbolic dates',
    },
    {
      id: 'src_hist_5',
      label: 'Historical corpus: WhisperGate / HermeticWiper',
      url: 'world-side/data/historical_pairings.md#5-whispergate--hermeticwiper--russian-invasion-of-ukraine-janfeb-2022',
      date: '2026-05-02',
      supports: 'Russian-linked wiper deployment aligned with military crisis timing',
    },
    {
      id: 'src_sanctions_russia',
      label: 'Sanctions state: Russia cyber retaliation profile',
      url: 'world-side/data/sanctions_state.md#41-russia',
      date: '2026-05-02',
      supports:
        'Russia destructive operations cluster within 4-8 weeks after major sanctions packages',
    },
    {
      id: 'src_calendar_russia_day',
      label: 'Calendar events: Russia Day',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'June 12, 2026 Russia Day is a symbolic cyber-activity window',
    },
    {
      id: 'src_calendar_nato',
      label: 'Calendar events: NATO Summit Ankara',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'July 7-8, 2026 NATO Summit is a high-value defense-policy event',
    },
    {
      id: 'src_cisa_aa22_057a',
      label: 'CISA AA22-057A',
      url: 'https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-057a',
      date: '2022-02-26',
      supports:
        'CISA documented destructive malware targeting Ukrainian organizations around the 2022 invasion',
    },
    {
      id: 'src_indictments_carr',
      label: 'Indictments state: CARR and NoName057(16)',
      url: 'world-side/data/indictments_state.md#112-ukrainian-national-charged-for-carr-gru-directed-and-noname05716--9-dec-2025',
      date: '2026-05-02',
      supports:
        'Russia-linked hacktivist and CARR activity is tracked in recent prosecution context',
    },
  ],
};

// ── Public exports ──────────────────────────────────────────────────────────

export const candidates: ExploitCandidate[] = [
  candidateEdgeAppliance,
  candidateFinancialTheft,
  candidateWiperShutdown,
];

export const forecasts: StrikeForecast[] = [
  forecastEdgeAppliance,
  forecastFinancialTheft,
  forecastWiperShutdown,
];

export function getForecastForCandidate(
  candidateId: string
): StrikeForecast | undefined {
  return forecasts.find((f) => f.input_candidate_id === candidateId);
}
