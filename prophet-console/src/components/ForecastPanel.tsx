// ForecastPanel: analyst-readable forecast brief for the mission context strip.

import type { SourceRefProps } from './SourceCitation';
import type { EvidenceAssetContext } from './EvidencePanel';
import './forecast.css';

// ── Types ─────────────────────────────────────────────────────────────────

export interface StrategicFrameProps {
  adversary_class: string;
  target_scope: string;
  geographic_scope: string;
  forecast_assumptions?: string[];
  excluded_uses?: string[];
}

export interface StrikeVectorProps {
  vector_id: string;
  rank: number;
  vector_class: string;
  target_sector: string;
  likely_objective: string;
  non_actionable_mechanism?: string;
  candidate_fit?: string;
  confidence: 'high' | 'medium' | 'low';
  confidence_score: number;
  why_this_vector?: string;
  defensive_implication?: string;
  source_ref_ids?: string[];
}

export interface StrikeWindowProps {
  window_id: string;
  rank: number;
  start_date: string;
  end_date: string;
  confidence: 'high' | 'medium' | 'low';
  confidence_score: number;
  why_this_window?: string;
  trigger_signals?: string[];
  source_ref_ids?: string[];
}

export interface ForecastSummaryProps {
  one_line: string;
  recommended_demo_path: string;
  stage3_priority?: string;
  analyst_notes?: string[];
}

export interface ForecastAssetSeedContext {
  integrated?: boolean;
  asset_count?: number;
  exposure_classes?: string[];
  owner_queues?: string[];
  cve_seed_count?: number;
  package_seed_count?: number;
}

export interface ForecastPanelData {
  forecast_id: string;
  generated_at: string;
  input_candidate_id?: string;
  strategic_frame: StrategicFrameProps;
  strike_windows?: StrikeWindowProps[];
  strike_vectors: StrikeVectorProps[];
  summary: ForecastSummaryProps;
  asset_seed_context?: ForecastAssetSeedContext;
  source_refs?: SourceRefProps[];
}

interface CandidateRailProps {
  cveId: string;
  vendor: string;
  product: string;
  cvss: number;
  cvssLabel: string;
  epss: number;
  attackTechnique: string;
  vulnClass: string;
  kevDateAdded: string;
}

interface ForecastPanelProps {
  forecast?: ForecastPanelData | null;
  candidate?: CandidateRailProps;
  assetContext?: EvidenceAssetContext | null;
  onScraperRun?: () => void;
  onDemoRefresh?: () => void;
  sourceRefreshGateStatus?: 'unknown' | 'allowed' | 'blocked';
  scraperRunState?: 'idle' | 'running' | 'ok' | 'error' | 'blocked';
  scraperStatusMessage?: string;
}

interface SourceRail {
  label: string;
  refs: SourceRefProps[];
}

// ── Default fallback data (edge-appliance golden fixture) ─────────────────

const DEFAULT_FORECAST: ForecastPanelData = {
  forecast_id: 'ws-golden-edge-appliance-001',
  generated_at: '2026-05-03T00:05:00Z',
  strategic_frame: {
    adversary_class: 'PRC-prepositioning-class',
    target_scope: 'US federal, defense-industrial, and critical-infrastructure perimeter services',
    geographic_scope: 'US federal and allied Indo-Pacific defense ecosystem',
    forecast_assumptions: [
      'The forecast candidate is an edge-appliance access class rather than a named CVE.',
      'Forecasting is sector-level only and does not identify live targets.',
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
        'The May 14-15 Trump-Xi summit creates a high-value collection and positioning window around US-PRC negotiations.',
      trigger_signals: [
        'Trump-Xi bilateral summit',
        'US-PRC diplomatic collection window',
        'edge-appliance pre-positioning pattern',
      ],
      source_ref_ids: ['src_calendar_trump_xi', 'src_hist_8', 'src_hist_10'],
    },
  ],
  strike_vectors: [
    {
      vector_id: 'vec_1',
      rank: 1,
      vector_class: 'edge-appliance initial access and persistence',
      target_sector: 'federal civilian agencies, defense contractors, and critical-infrastructure perimeter services',
      likely_objective: 'persistence',
      confidence: 'medium',
      confidence_score: 0.72,
      why_this_vector:
        'Volt Typhoon and Ivanti anchors both show edge or perimeter appliance access as a recurring state-linked pattern against US and allied infrastructure.',
      defensive_implication:
        'Prioritize detection, inventory, configuration review, and safe localhost validation around the selected perimeter-service class.',
      source_ref_ids: ['src_hist_8', 'src_hist_10', 'src_cisa_aa24_038a'],
    },
  ],
  summary: {
    one_line:
      'For an edge-appliance candidate, the strongest forecast is PRC-style pre-positioning around May 2026 diplomatic and Indo-Pacific defense windows.',
    recommended_demo_path:
      'Use a safe edge-service fixture and show how timing context prioritizes perimeter detection over unsafe output generation.',
    stage3_priority:
      'Validate a defensive block and alert around perimeter-service access indicators in a local demo environment.',
  },
};

const RAIL_ORDER = [
  'Official signals',
  'Geopolitical calendar',
  'Historical analogies',
  'Public chatter',
  'Vendor intelligence',
  'OSINT context',
];

// ── Helpers ───────────────────────────────────────────────────────────────

function confidenceLabel(score: number): string {
  if (score >= 0.7) return 'High';
  if (score >= 0.45) return 'Medium';
  return 'Low';
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function parseDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day, 12));
}

function formatDate(value: string): string {
  const date = parseDate(value);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}

function formatWindow(window: StrikeWindowProps | null): string {
  if (!window) return 'No window available';
  const start = formatDate(window.start_date);
  const end = formatDate(window.end_date);
  const year = parseDate(window.end_date).getUTCFullYear();
  return `${start} - ${end}, ${year}`;
}

function daysInWindow(window: StrikeWindowProps | null): string {
  if (!window) return 'Waiting for forecast output';
  const start = parseDate(window.start_date);
  const end = parseDate(window.end_date);
  const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1);
  return `${days} day window, rank ${window.rank}, ${confidenceLabel(window.confidence_score)} confidence`;
}

function readable(value: string | undefined): string {
  if (!value) return 'Not available';
  return value
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function classifySource(ref: SourceRefProps): string {
  const text = `${ref.id} ${ref.label} ${ref.url} ${ref.supports}`.toLowerCase();
  if (/(cisa|kev|nvd|epss|ofac|state|travel|federal register|doj|noaa|mitre|attack)/.test(text)) {
    return 'Official signals';
  }
  if (/(calendar|summit|dialogue|anniversary|sanctions|fomc|nato|shangri|tiananmen|travel)/.test(text)) {
    return 'Geopolitical calendar';
  }
  if (/(historical|hist_|volt|ivanti|sandworm|lazarus|typhoon|moveit|viasat)/.test(text)) {
    return 'Historical analogies';
  }
  if (/(chatter|telegram|reddit|onion|darkweb|public channel|social)/.test(text)) {
    return 'Public chatter';
  }
  if (/(vendor|mandiant|volexity|crowdstrike|unit 42|talos|palo alto|eset|fortinet|microsoft|google)/.test(text)) {
    return 'Vendor intelligence';
  }
  return 'OSINT context';
}

function buildSourceRails(refs: SourceRefProps[] | undefined): SourceRail[] {
  if (!refs?.length) return [];
  const buckets = new Map<string, SourceRefProps[]>();
  for (const ref of refs) {
    const label = classifySource(ref);
    buckets.set(label, [...(buckets.get(label) ?? []), ref]);
  }
  return RAIL_ORDER
    .map((label) => ({ label, refs: buckets.get(label) ?? [] }))
    .filter((rail) => rail.refs.length > 0);
}

function sourcePreview(refs: SourceRefProps[]): string {
  return refs[0]?.supports || refs[0]?.label || 'Source context available';
}

// ── Component ─────────────────────────────────────────────────────────────

export function ForecastPanel({
  forecast,
  candidate,
  assetContext,
  onScraperRun,
  onDemoRefresh,
  sourceRefreshGateStatus = 'unknown',
  scraperRunState = 'idle',
  scraperStatusMessage,
}: ForecastPanelProps) {
  const data = forecast ?? DEFAULT_FORECAST;
  const topVector = data.strike_vectors?.[0] ?? null;
  const topWindow = data.strike_windows?.[0] ?? null;
  const frame = data.strategic_frame;
  const summary = data.summary;
  const sourceRails = buildSourceRails(data.source_refs);
  const triggerSignals = topWindow?.trigger_signals?.slice(0, 4) ?? [];
  const confidenceScore = topVector?.confidence_score ?? topWindow?.confidence_score ?? 0;
  const forecastAssetContext = data.asset_seed_context?.integrated
    ? data.asset_seed_context
    : null;
  const sourceRefreshAllowed = sourceRefreshGateStatus === 'allowed';
  const sourceRefreshPolicyMessage =
    sourceRefreshGateStatus === 'blocked'
      ? 'Policy blocks live source refresh; use the sanitized demo refresh.'
      : sourceRefreshGateStatus === 'unknown'
        ? 'Checking policy before enabling source refresh.'
        : null;
  const sourceRefreshButtonText =
    scraperRunState === 'running'
      ? 'Checking policy'
      : sourceRefreshGateStatus === 'blocked'
        ? 'Source refresh blocked'
        : sourceRefreshGateStatus === 'unknown'
          ? 'Checking policy'
          : 'Request source refresh';
  const exposureMatch = assetContext
    ? {
        count: assetContext.affected_asset_count ?? 0,
        label: assetContext.matched_exposure_class,
        owners: assetContext.recommended_owner_queue ?? [],
      }
    : forecastAssetContext
      ? {
          count: forecastAssetContext.asset_count ?? 0,
          label: forecastAssetContext.exposure_classes?.[0],
          owners: forecastAssetContext.owner_queues ?? [],
        }
      : null;

  if (!data || !frame) {
    return (
      <div className="fp-card fp-brief-card" aria-label="Forecast panel">
        <div className="fp-null-state">No forecast available</div>
      </div>
    );
  }

  return (
    <section className="fp-card fp-brief-card" aria-label="Forecast brief">
      <div className="fp-brief-header">
        <div className="fp-title-block">
          <span className="fp-kicker">Prophet brief</span>
          <h2>{readable(topVector?.vector_class)}</h2>
          <p>{summary.one_line}</p>
        </div>

        {(onScraperRun || onDemoRefresh) && (
          <div className="fp-action-group fp-action-group--brief">
            {onDemoRefresh && (
              <button
                className="fp-action-button fp-action-button--quiet"
                type="button"
                onClick={onDemoRefresh}
                disabled={scraperRunState === 'running'}
                aria-label="Refresh forecast from sanitized demo fixture"
                title="Uses the tracked sanitized chatter fixture and forecaster locally"
              >
                Refresh demo
              </button>
            )}
            {onScraperRun && (
              <button
                className="fp-action-button"
                type="button"
                onClick={onScraperRun}
                disabled={scraperRunState === 'running' || !sourceRefreshAllowed}
                aria-label="Request policy-gated source refresh"
                title={
                  sourceRefreshAllowed
                    ? 'Requests the local control server to run an approved source refresh and return sanitized forecast data'
                    : 'Policy has not allowed live source refresh; use the sanitized demo refresh'
                }
              >
                {sourceRefreshButtonText}
              </button>
            )}
            {sourceRefreshPolicyMessage && scraperRunState === 'idle' && (
              <span className="fp-control-status fp-control-status--blocked">
                {sourceRefreshPolicyMessage}
              </span>
            )}
            {scraperStatusMessage && scraperRunState !== 'idle' && (
              <span className={`fp-control-status fp-control-status--${scraperRunState}`}>
                {scraperStatusMessage}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="fp-brief-grid">
        <article className="fp-primary-card">
          <span className="fp-card-label">Most likely method</span>
          <strong>{readable(topVector?.vector_class)}</strong>
          <p>{topVector?.target_sector ?? 'Waiting for forecast output'}</p>
        </article>

        <article className="fp-primary-card">
          <span className="fp-card-label">Expected window</span>
          <strong>{formatWindow(topWindow)}</strong>
          <p>{daysInWindow(topWindow)}</p>
        </article>

        <article className="fp-primary-card fp-primary-card--candidate">
          <span className="fp-card-label">Candidate rail</span>
          <strong>{candidate?.cveId ?? data.input_candidate_id ?? 'Representative class'}</strong>
          <div className="fp-mini-metrics" aria-label="Candidate metrics">
            <span>{candidate ? `${candidate.vendor} ${candidate.product}` : readable(frame.target_scope)}</span>
            {candidate && <span>{candidate.cvssLabel} CVSS {candidate.cvss.toFixed(1)}</span>}
            {candidate && <span>EPSS {formatPercent(candidate.epss)}</span>}
            {candidate && <span>{candidate.vulnClass}</span>}
            {candidate && <span>{candidate.attackTechnique}</span>}
            {candidate && <span>KEV {formatDate(candidate.kevDateAdded)}</span>}
          </div>
        </article>

        {exposureMatch && (
          <article className="fp-primary-card fp-primary-card--asset">
            <span className="fp-card-label">Customer exposure match</span>
            <strong>{exposureMatch.count} fictional assets</strong>
            <p>{readable(exposureMatch.label)}</p>
            <div className="fp-mini-metrics" aria-label="Asset context metrics">
              {exposureMatch.owners.slice(0, 3).map((owner) => (
                <span key={owner}>{owner}</span>
              ))}
            </div>
          </article>
        )}
      </div>

      <div className="fp-support-grid">
        <section className="fp-brief-panel fp-brief-panel--wide">
          <div className="fp-panel-heading">
            <h3>Why now</h3>
            <span>{confidenceLabel(confidenceScore)} confidence</span>
          </div>
          <p>{topWindow?.why_this_window ?? topVector?.why_this_vector ?? summary.recommended_demo_path}</p>
          {triggerSignals.length > 0 && (
            <div className="fp-trigger-row" aria-label="Trigger signals">
              {triggerSignals.map((signal) => (
                <span key={signal}>{signal}</span>
              ))}
            </div>
          )}
        </section>

        <section className="fp-brief-panel">
          <div className="fp-panel-heading">
            <h3>Defense focus</h3>
            <span>{readable(topVector?.likely_objective)}</span>
          </div>
          <p>{topVector?.defensive_implication ?? summary.stage3_priority ?? summary.recommended_demo_path}</p>
          <div className="fp-confidence-row" aria-label={`Forecast confidence: ${confidenceLabel(confidenceScore)}`}>
            <div className="fp-confidence-track" aria-hidden>
              <div className="fp-confidence-fill" style={{ width: `${Math.round(confidenceScore * 100)}%` }} />
            </div>
            <span className="fp-confidence-label">{formatPercent(confidenceScore)}</span>
          </div>
        </section>

        <section className="fp-brief-panel fp-source-rail">
          <div className="fp-panel-heading">
            <h3>Source rail</h3>
            <span>{data.source_refs?.length ?? 0} refs</span>
          </div>
          <div className="fp-rail-list" aria-label="Grouped source rails">
            {sourceRails.length > 0 ? (
              sourceRails.map((rail) => (
                <div
                  key={rail.label}
                  className="fp-rail-item"
                  title={sourcePreview(rail.refs)}
                >
                  <strong>{rail.refs.length}</strong>
                  <span>{rail.label}</span>
                </div>
              ))
            ) : (
              <div className="fp-rail-empty">No source rail attached</div>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
