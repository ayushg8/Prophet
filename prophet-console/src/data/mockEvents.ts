import { sanitize } from '../lib/sanitize';
import { forecastsByCandidateId } from './forecastIndex';
import type { StrikeForecast, HistoricalAnalogy, SourceRef as WorldSourceRef } from './worldSide';

// ── Existing event-kind union (unchanged names) ─────────────────────────────

export type EventKind =
  | 'phase'
  | 'tool_call'
  | 'text'
  | 'phase_complete'
  | 'human_gate'
  | 'exploit_status'
  | 'patch_diff'
  | 'sigma_rule'
  // New World-Side event variants
  | 'forecast_summary'
  | 'historical_analogy'
  | 'source_ref';

export interface PhaseEvent {
  kind: 'phase';
  phase: 'INTEL' | 'PLAN' | 'EXECUTE' | 'DEFEND';
  label: string;
}

export interface ToolCallEvent {
  kind: 'tool_call';
  id: string;
  tool: string;
  args: Record<string, unknown>;
  durationMs: number;
  result?: string;
}

export interface TextEvent {
  kind: 'text';
  content: string;
}

export interface PhaseCompleteEvent {
  kind: 'phase_complete';
  phase: 'INTEL' | 'PLAN' | 'EXECUTE' | 'DEFEND';
}

export interface HumanGateEvent {
  kind: 'human_gate';
}

export interface ExploitStatusEvent {
  kind: 'exploit_status';
  status: 'running' | 'vulnerable' | 'blocked';
  responseExcerpt?: string;
}

export interface PatchDiffEvent {
  kind: 'patch_diff';
  content: string;
}

export interface SigmaRuleEvent {
  kind: 'sigma_rule';
  content: string;
}

// ── New World-Side event variants ───────────────────────────────────────────

/** Carries the full StrikeForecast object for the active candidate. */
export interface ForecastSummaryEvent {
  kind: 'forecast_summary';
  forecast: StrikeForecast;
}

/** Agent cites a historical analogy from the World-Side corpus. */
export interface HistoricalAnalogyEvent {
  kind: 'historical_analogy';
  analogy: HistoricalAnalogy;
  windowId: string;
}

/** Inline citation chip referencing a World-Side source. */
export interface SourceRefEvent {
  kind: 'source_ref';
  ref: WorldSourceRef;
}

export type AgentEvent =
  | PhaseEvent
  | ToolCallEvent
  | TextEvent
  | PhaseCompleteEvent
  | HumanGateEvent
  | ExploitStatusEvent
  | PatchDiffEvent
  | SigmaRuleEvent
  | ForecastSummaryEvent
  | HistoricalAnalogyEvent
  | SourceRefEvent;

// ── Real Log4j patch diff ────────────────────────────────────────────────────
const PATCH_DIFF = `--- a/VulnerableApp/run.bat
+++ b/VulnerableApp/run.bat
@@ -1,6 +1,10 @@
 @echo off
-java -cp "VulnerableApp.jar;log4j-api-2.14.0.jar;log4j-core-2.14.0.jar" VulnerableApp
+rem PRIMARY MITIGATION: disable JNDI message lookups globally
+java ^
+  -Dlog4j2.formatMsgNoLookups=true ^
+  -Dlog4j2.disableJndi=true ^
+  -cp "VulnerableApp.jar;log4j-api-2.14.0.jar;log4j-core-2.14.0.jar" ^
+  VulnerableApp

--- a/VulnerableApp/log4j2.xml
+++ b/VulnerableApp/log4j2.xml
@@ -3,7 +3,7 @@
   <Appenders>
     <Console name="Console" target="SYSTEM_OUT">
-      <PatternLayout pattern="%d{HH:mm:ss} [%t] %-5level %logger - %msg%n"/>
+      <PatternLayout pattern="%d{HH:mm:ss} [%t] %-5level %logger - %msg{nolookups}%n"/>
     </Console>
   </Appenders>

--- a/VulnerableApp/build-classpath.sh
+++ b/VulnerableApp/build-classpath.sh
@@ -8,3 +8,8 @@
 javac -cp "log4j-api-2.14.0.jar:log4j-core-2.14.0.jar" VulnerableApp.java
+
+rem FALLBACK: remove JndiLookup.class from log4j-core JAR (Log4j <= 2.15)
+rem This eliminates the lookup class entirely from the classpath.
+zip -q -d log4j-core-2.14.0.jar \\
+  org/apache/logging/log4j/core/lookup/JndiLookup.class`;

// ── Detection-only Sigma rule rendered as a defensive artifact ───────────────
const SIGMA_RULE = `title: Log4Shell JNDI Lookup Detection
id: b7e4f2a1-9c83-4d56-a0e7-12f3456789ab
status: stable
description: >
  Detects suspicious JNDI lookup markers in web and application logs for
  CVE-2021-44228. Detection-only; no response action or exploit procedure is
  encoded in this rule.
references:
  - https://www.cisa.gov/known-exploited-vulnerabilities-catalog
  - https://nvd.nist.gov/vuln/detail/CVE-2021-44228
author: Prophet Agent Loop — Defence fixture
date: 2026/05/02
modified: 2026/05/02
tags:
  - attack.initial_access
  - attack.execution
  - attack.t1190
  - cve.2021.44228
  - cisa.kev
logsource:
  category: webserver
detection:
  lookup_markers:
    cs-user-agent|contains:
      - 'jndi:'
      - 'jndi%3A'
    cs-referer|contains:
      - 'jndi:'
      - 'jndi%3A'
    cs-x-forwarded-for|contains:
      - 'jndi:'
  app_log_jndi:
    EventID: 4688
    CommandLine|contains:
      - 'jndi:ldap'
      - 'jndi:rmi'
      - 'jndi:dns'
      - 'jndi:iiop'
  condition: lookup_markers or app_log_jndi
fields:
  - cs-user-agent
  - cs-referer
  - cs-x-forwarded-for
  - CommandLine
falsepositives:
  - Authorized blue-team validation traffic
level: critical
`;

// ── World-Side context for the edge-appliance demo path ─────────────────────
const edgeForecast = forecastsByCandidateId['cs-fixture-edge-appliance-001'];
const topWindow = edgeForecast?.strike_windows[0];
const topVector = edgeForecast?.strike_vectors[0];
const voltAnchor = topWindow?.historical_analogies[0];
const trumpXiRef = edgeForecast?.source_refs.find(
  (r) => r.id === 'src_calendar_trump_xi'
);
const hist8Ref = edgeForecast?.source_refs.find((r) => r.id === 'src_hist_8');
const cisaRef = edgeForecast?.source_refs.find(
  (r) => r.id === 'src_cisa_aa24_038a'
);

export const mockEvents: AgentEvent[] = [
  // ── Phase I: Intel ─────────────────────────────────────────────────────────
  { kind: 'phase', phase: 'INTEL', label: 'Phase I — Intel' },

  {
    kind: 'tool_call',
    id: 'tc-001',
    tool: 'fetch_kev',
    args: {},
    durationMs: 340,
    result:
      '3,612 entries loaded · last updated 2026-05-02T00:00:00Z · CVE-2021-44228 rank #4',
  },

  {
    kind: 'tool_call',
    id: 'tc-002',
    tool: 'fetch_nvd_recent',
    args: { days: 7, resultsPerPage: 2000 },
    durationMs: 520,
    result:
      '1,247 CVEs retrieved · pubStartDate: 2026-04-25 · CVE-2021-44228 confirmed critical',
  },

  {
    kind: 'text',
    content: sanitize(
      'CISA KEV catalog loaded: 3,612 entries. CVE-2021-44228 (Log4Shell) appears at rank #4 on the Known Exploited Vulnerabilities list — classified as emergency-level by CISA in December 2021. NVD confirms CVSS 10.0 / CRITICAL with vector AV:N/AC:L/PR:N/UI:N. Beginning EPSS batch scoring across the recent 7-day cohort.'
    ),
  },

  {
    kind: 'tool_call',
    id: 'tc-003',
    tool: 'score_epss',
    args: { cve: 'CVE-2021-44228', model_version: 'v4' },
    durationMs: 310,
    result: 'score: 0.97454 · percentile: 0.999 · 30-day trend: stable high',
  },

  {
    kind: 'text',
    content: sanitize(
      'EPSS v4 score for CVE-2021-44228: 0.97 — 99.9th percentile of exploitation probability. This is among the highest EPSS scores in the CVE corpus. Widespread deployment, weak input-handling patterns in logging paths, and confirmed in-the-wild exploitation drive this score.'
    ),
  },

  {
    kind: 'tool_call',
    id: 'tc-004',
    tool: 'probe_target_lab',
    args: { host: '[LAB-HOST]', port: 8080 },
    durationMs: 890,
    result:
      'localhost fixture reachable · Java sandbox profile · vulnerable dependency detected',
  },

  {
    kind: 'text',
    content: sanitize(
      'Lab fixture confirmed: Java 8 runtime with Log4j 2.14.0 inside a vulnerable-by-design localhost sandbox. The fixture models a logging-path exposure for defensive validation only; no live infrastructure or raw exploit material is loaded.\n\nForecaster candidate classification: enterprise VPN and secure edge appliance family · cve_class_label: edge-device auth bypass · CWE-287 / CWE-306.'
    ),
  },

  {
    kind: 'tool_call',
    id: 'tc-005',
    tool: 'check_nuclei_template',
    args: { cve: 'CVE-2021-44228' },
    durationMs: 45,
    result:
      'public validation template metadata available · fixture-safe path selected',
  },

  {
    kind: 'tool_call',
    id: 'tc-006',
    tool: 'search_exploitdb',
    args: { cve: 'CVE-2021-44228' },
    durationMs: 88,
    result:
      'public exploit-index metadata present · raw entries not loaded',
  },

  {
    kind: 'tool_call',
    id: 'tc-007',
    tool: 'map_attack_technique',
    args: { cve: 'CVE-2021-44228' },
    durationMs: 62,
    result:
      'T1190 — Exploit Public-Facing Application · technique family mapped · no procedure loaded',
  },

  // World-Side: query_world_side returns the strike-window forecast
  {
    kind: 'tool_call',
    id: 'tc-007b',
    tool: 'query_world_side',
    args: {
      candidate: {
        candidate_id: 'cs-fixture-edge-appliance-001',
        cve_class_label: 'edge-device auth bypass',
        target_product: 'enterprise VPN and secure edge appliance family',
        cwe_ids: ['CWE-287', 'CWE-306'],
      },
    },
    durationMs: 420,
    result: sanitize(
      `forecast_id: ws-golden-edge-appliance-001 · adversary_class: PRC-prepositioning-class · top_window: 2026-05-08 to 2026-05-18 (confidence: 0.67 medium) · trigger: Trump-Xi bilateral summit · top_vector: edge-appliance initial access and persistence · defensive_implication: Prioritize detection, inventory, configuration review, and safe localhost validation`
    ),
  },

  // Emit the full forecast object for the UI merge layer
  ...(edgeForecast ? [{ kind: 'forecast_summary' as const, forecast: edgeForecast }] : []),

  {
    kind: 'text',
    content: sanitize(
      'Signal summary for CVE-2021-44228: KEV rank #4, EPSS 0.97 (99.9th percentile), public validation metadata available, exploit-index metadata counted without loading raw entries, and ATT&CK T1190 mapped. The localhost fixture uses an affected Log4j profile. Designating CVE-2021-44228 as the representative exploit class for the demo. Proceeding to Phase II planning.'
    ),
  },

  // Inline source-ref chip for the CISA advisory that anchors the Intel phase
  ...(cisaRef
    ? [{ kind: 'source_ref' as const, ref: cisaRef }]
    : []),

  { kind: 'phase_complete', phase: 'INTEL' },

  // ── Phase II: Plan ─────────────────────────────────────────────────────────
  { kind: 'phase', phase: 'PLAN', label: 'Phase II — Defense Plan' },

  {
    kind: 'tool_call',
    id: 'tc-008',
    tool: 'read_nuclei_template',
    args: { path: 'http/cves/2021/CVE-2021-44228.yaml' },
    durationMs: 38,
    result:
      'Template metadata loaded · public validation profile · no raw request material displayed',
  },

  {
    kind: 'tool_call',
    id: 'tc-009',
    tool: 'inspect_target',
    args: {
      target: '[LAB-HOST]:8080',
      service: 'VulnerableApp · Java 8 + Log4j 2.14.0',
    },
    durationMs: 210,
    result:
      'fixture response observed · vulnerable logging-path profile · localhost only',
  },

  {
    kind: 'text',
    content: sanitize(
      'Validation plan for CVE-2021-44228 on the localhost fixture:\n\nUse the public validation template as a bounded, operator-approved check against a vulnerable-by-design sandbox. The console records only class-level pre/post-patch status, defense output, and citations. It does not display payload syntax, request material, target-control steps, or live indicators.'
    ),
  },

  {
    kind: 'text',
    content: sanitize(
      'World-Side context — Adversary class: PRC-prepositioning. Top strike window: 2026-05-08 to 2026-05-18, confidence 0.67 (medium). Primary trigger: Trump-Xi bilateral summit (May 14-15, 2026). Historical anchor: Volt Typhoon / Taiwan Strait pre-positioning — long-dwell access against US critical infrastructure held pending a future crisis trigger. Vector class: edge-appliance initial access and persistence targeting federal civilian agencies, defense contractors, and critical-infrastructure perimeter services.'
    ),
  },

  // Historical analogy citation — Volt Typhoon
  ...(voltAnchor && topWindow
    ? [
        {
          kind: 'historical_analogy' as const,
          analogy: voltAnchor,
          windowId: topWindow.window_id,
        },
      ]
    : []),

  // Inline citation chip for the Trump-Xi calendar trigger
  ...(trumpXiRef ? [{ kind: 'source_ref' as const, ref: trumpXiRef }] : []),

  {
    kind: 'text',
    content: sanitize(
      `Plan summary for operator authorization: run fixture-scoped validation against the localhost sandbox · render the Log4j defense artifact · keep rollback sandbox-only. Forecaster strike vector: ${topVector?.vector_class ?? 'edge-appliance initial access'}. Forwarding validation plan for human authorization gate.`
    ),
  },

  { kind: 'human_gate' },

  // ── Phase III: Execute ─────────────────────────────────────────────────────
  { kind: 'phase', phase: 'EXECUTE', label: 'Phase III — Validate' },

  { kind: 'exploit_status', status: 'running' },

  {
    kind: 'tool_call',
    id: 'tc-010',
    tool: 'run_nuclei',
    args: {
      template: 'http/cves/2021/CVE-2021-44228.yaml',
      target: '[LAB-HOST]:8080',
      scope: 'localhost fixture',
    },
    durationMs: 2840,
    result:
      '[CVE-2021-44228] [fixture] pre-patch validation · VULNERABLE',
  },

  {
    kind: 'tool_call',
    id: 'tc-011',
    tool: 'inspect_response',
    args: { target: '[LAB-HOST]:8080', method: 'GET' },
    durationMs: 420,
    result:
      'fixture response observed · validation evidence recorded · no request material displayed',
  },

  {
    kind: 'text',
    content: sanitize(
      `Validation template complete. The vulnerable-by-design sandbox returns the expected pre-patch class-level status without displaying request material or target-control steps.\n\nStatus: representative exploit class confirmed in localhost fixture · sandbox containment OK.\n\nForecaster vector match: ${topVector?.vector_class ?? 'edge-appliance initial access'} — perimeter-appliance access class validated in an isolated environment. Proceeding to Phase IV — Defence Co-generation.`
    ),
  },

  {
    kind: 'exploit_status',
    status: 'vulnerable',
    responseExcerpt: sanitize(
      'pre_patch_status: vulnerable\nscope: localhost fixture\nno payloads or live indicators displayed\nsandbox containment OK'
    ),
  },

  { kind: 'phase_complete', phase: 'EXECUTE' },

  // ── Phase IV: Defend ───────────────────────────────────────────────────────
  { kind: 'phase', phase: 'DEFEND', label: 'Phase IV — Defence Co-gen' },

  {
    kind: 'tool_call',
    id: 'tc-012',
    tool: 'apply_patch',
    args: {
      target: '[LAB-HOST]:8080',
      jvm_flag: '-Dlog4j2.formatMsgNoLookups=true',
      layout: '%msg{nolookups}',
    },
    durationMs: 680,
    result: 'JVM flag applied · log4j2.xml updated · service restart scheduled',
  },

  {
    kind: 'text',
    content: sanitize(
      `Generating two-layer defence for CVE-2021-44228 on the lab target:\n\nPrimary mitigation: set JVM system property -Dlog4j2.formatMsgNoLookups=true. This disables JNDI message lookups globally in Log4j without requiring a library version upgrade. Takes effect on service restart.\n\nSecondary / defence-in-depth: update log4j2.xml PatternLayout to use %msg{nolookups}. This ensures the logging appender never evaluates lookup expressions even if the JVM flag is removed.\n\nFallback: remove org/apache/logging/log4j/core/lookup/JndiLookup.class from the log4j-core JAR. This eliminates the lookup mechanism entirely at the classpath level — the recommended approach for Log4j versions 2.10 through 2.14.x where upgrading is not immediately feasible.\n\nWorld-Side defensive implication: ${topVector?.defensive_implication ?? 'Prioritize detection, inventory, configuration review, and safe localhost validation around the selected perimeter-service class.'}`
    ),
  },

  {
    kind: 'tool_call',
    id: 'tc-013',
    tool: 'restart_service',
    args: { service: 'VulnerableApp', host: '[LAB-HOST]' },
    durationMs: 1340,
    result:
      'Service restarted · VulnerableApp running · Log4j 2.14.0 with formatMsgNoLookups=true',
  },

  {
    kind: 'tool_call',
    id: 'tc-014',
    tool: 'generate_sigma',
    args: {
      cve: 'CVE-2021-44228',
      log_fields: ['web headers', 'application logs'],
    },
    durationMs: 920,
    result:
      'Sigma rule generated · status: stable · level: critical · detection-only fields',
  },

  {
    kind: 'patch_diff',
    content: PATCH_DIFF,
  },

  {
    kind: 'sigma_rule',
    content: SIGMA_RULE,
  },

  {
    kind: 'tool_call',
    id: 'tc-015',
    tool: 'verify_blocked',
    args: {
      template: 'http/cves/2021/CVE-2021-44228.yaml',
      target: '[LAB-HOST]:8080',
    },
    durationMs: 2610,
    result:
      '[CVE-2021-44228] [fixture] post-patch validation · NOT VULNERABLE',
  },

  {
    kind: 'exploit_status',
    status: 'blocked',
    responseExcerpt: sanitize(
      'post_patch_status: blocked\nfixture validation: NOT VULNERABLE\npatch validated · block confirmed'
    ),
  },

  {
    kind: 'text',
    content: sanitize(
      'Validation complete. The patched fixture returns NOT VULNERABLE, the Log4j mitigation primitive is represented in the defense artifact, and the Sigma rule is syntactically valid for SIEM deployment. Emitting signed audit record.'
    ),
  },

  // Historical analogy citation from Volt Typhoon for the Defend phase summary
  ...(hist8Ref ? [{ kind: 'source_ref' as const, ref: hist8Ref }] : []),

  {
    kind: 'tool_call',
    id: 'tc-016',
    tool: 'emit_maven_fusion_object',
    args: {
      cve: 'CVE-2021-44228',
      exploit_class: 'JNDI lookup exploit class',
      sandbox_result: 'BLOCKED',
      patch_applied: true,
      kev_rank: 4,
      epss: 0.97,
      world_side_forecast_id: 'ws-golden-edge-appliance-001',
      adversary_class: 'PRC-prepositioning-class',
      top_strike_window: '2026-05-08 / 2026-05-18',
    },
    durationMs: 180,
    result:
      'Fusion object emitted · run_id: PRO-20260502-001 · signed SHA256: a3f9…c142',
  },

  { kind: 'phase_complete', phase: 'DEFEND' },
];
