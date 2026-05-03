// ForecastPanel: compact summary card surfacing strategic_frame, top strike_vector,
// and summary fields from a World Side forecast.
// Uses useState for confidence bar animation mount trigger — 'use client' pattern.

import { useEffect, useRef, useState } from 'react';
import type { SourceRefProps } from './SourceCitation';
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

export interface ForecastPanelData {
  forecast_id: string;
  generated_at: string;
  strategic_frame: StrategicFrameProps;
  strike_windows?: StrikeWindowProps[];
  strike_vectors: StrikeVectorProps[];
  summary: ForecastSummaryProps;
  source_refs?: SourceRefProps[];
}

interface ForecastPanelProps {
  forecast?: ForecastPanelData | null;
  onScraperRun?: () => void;
  onDemoRefresh?: () => void;
  scraperRunState?: 'idle' | 'running' | 'ok' | 'error';
  scraperStatusMessage?: string;
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
      'The Stage 1 candidate is an edge-appliance access class rather than a named CVE.',
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
      'Use a safe edge-service fixture and show how timing context prioritizes perimeter detection over payload generation.',
    stage3_priority:
      'Validate a defensive block and alert around perimeter-service access indicators in a local demo environment.',
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────

function confidenceLabel(score: number): string {
  if (score >= 0.7) return 'HIGH';
  if (score >= 0.45) return 'MEDIUM';
  return 'LOW';
}

function formatWindow(window: StrikeWindowProps | null): string {
  if (!window) return 'NO WINDOW AVAILABLE';
  return `${window.start_date} -> ${window.end_date}`;
}

// ── Component ─────────────────────────────────────────────────────────────

export function ForecastPanel({
  forecast,
  onScraperRun,
  onDemoRefresh,
  scraperRunState = 'idle',
  scraperStatusMessage,
}: ForecastPanelProps) {
  // Controls animated fill of the confidence bar on mount
  const [fillWidth, setFillWidth] = useState(0);
  const mountedRef = useRef(false);

  const data = forecast ?? DEFAULT_FORECAST;
  const topVector = data.strike_vectors?.[0] ?? null;
  const topWindow = data.strike_windows?.[0] ?? null;
  const frame = data.strategic_frame;
  const summary = data.summary;

  // Animate the confidence bar to its target value after mount
  useEffect(() => {
    if (mountedRef.current) return;
    mountedRef.current = true;
    // Defer one frame so CSS transition fires
    const id = window.requestAnimationFrame(() => {
      setFillWidth(topVector ? topVector.confidence_score * 100 : 0);
    });
    return () => window.cancelAnimationFrame(id);
  }, [topVector]);

  // Also reset animation when forecast changes
  useEffect(() => {
    setFillWidth(0);
    const id = window.requestAnimationFrame(() => {
      setFillWidth(topVector ? topVector.confidence_score * 100 : 0);
    });
    return () => window.cancelAnimationFrame(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.forecast_id]);

  if (!data || !frame) {
    return (
      <div className="fp-card" aria-label="Forecast panel">
        <div className="fp-header">
          <span className="fp-eyebrow">
            <span className="fp-eyebrow-chevron" aria-hidden>◢</span>
            WORLD SIDE FORECAST
            <span className="fp-eyebrow-chevron" aria-hidden>◣</span>
          </span>
        </div>
        <div className="fp-null-state">NO FORECAST AVAILABLE</div>
      </div>
    );
  }

  return (
    <div className="fp-card" aria-label="World Side forecast panel">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="fp-header">
        <span className="fp-eyebrow">
          <span className="fp-eyebrow-chevron" aria-hidden>◢</span>
          WORLD SIDE FORECAST
          <span className="fp-eyebrow-chevron" aria-hidden>◣</span>
        </span>
        {(onScraperRun || onDemoRefresh) && (
          <div className="fp-action-group">
            {onDemoRefresh && (
              <button
                className="fp-action-btn fp-action-btn--secondary"
                type="button"
                onClick={onDemoRefresh}
                disabled={scraperRunState === 'running'}
                aria-label="Refresh forecast from sanitized demo fixture"
                title="Uses the tracked sanitized chatter fixture and forecaster locally"
              >
                <span className="fp-action-bracket">[</span>
                DEMO REFRESH
                <span className="fp-action-bracket">]</span>
              </button>
            )}
            {onScraperRun && (
              <button
                className="fp-action-btn"
                type="button"
                onClick={onScraperRun}
                disabled={scraperRunState === 'running'}
                aria-label="Run isolated scraper VM workflow"
                title="Runs local control server -> SSH scraper VM -> sanitized JSONL -> forecast"
              >
                <span className="fp-action-bracket">[</span>
                {scraperRunState === 'running' ? 'RUNNING' : 'RUN SCRAPER VM'}
                <span className="fp-action-bracket">]</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Two-column body ─────────────────────────────────────────── */}
      <div className="fp-body">
        {scraperStatusMessage && (
          <div className={`fp-control-status fp-control-status--${scraperRunState}`}>
            {scraperStatusMessage}
          </div>
        )}

        <div className="fp-deliverables" aria-label="Forecast deliverables">
          <div className="fp-deliverable">
            <span className="fp-deliverable-label">ATTACK METHOD / STRIKE VECTOR</span>
            <span className="fp-deliverable-value">
              {topVector?.vector_class ?? 'NO VECTOR AVAILABLE'}
            </span>
            <span className="fp-deliverable-note">
              {topVector?.target_sector ?? 'Waiting for forecast output'}
            </span>
          </div>

          <div className="fp-deliverable">
            <span className="fp-deliverable-label">TIMEFRAME / STRIKE WINDOW</span>
            <span className="fp-deliverable-value">{formatWindow(topWindow)}</span>
            <span className="fp-deliverable-note">
              {topWindow
                ? `Rank ${topWindow.rank} · ${topWindow.confidence.toUpperCase()} confidence`
                : 'Waiting for forecast output'}
            </span>
          </div>
        </div>

        {/* Left column */}
        <div className="fp-col">
          <div className="fp-field">
            <span className="fp-field-label">ADVERSARY CLASS</span>
            <span className="fp-field-value">{frame.adversary_class}</span>
          </div>
          <div className="fp-field">
            <span className="fp-field-label">TARGET SCOPE</span>
            <span className="fp-field-value--small">{frame.target_scope}</span>
          </div>
          <div className="fp-field">
            <span className="fp-field-label">GEOGRAPHIC SCOPE</span>
            <span className="fp-field-value--small">{frame.geographic_scope}</span>
          </div>
        </div>

        {/* Right column */}
        <div className="fp-col">
          {topVector ? (
            <>
              <div className="fp-field">
                <span className="fp-field-label">TOP STRIKE VECTOR</span>
                <span className="fp-field-value">{topVector.vector_class}</span>
              </div>
              <div className="fp-field">
                <span className="fp-field-label">LIKELY OBJECTIVE</span>
                <span className="fp-field-value">{topVector.likely_objective.toUpperCase()}</span>
              </div>
              <div className="fp-field">
                <span className="fp-field-label">CONFIDENCE</span>
                <div className="fp-confidence-row" aria-label={`Confidence: ${confidenceLabel(topVector.confidence_score)}`}>
                  <div className="fp-confidence-track" aria-hidden>
                    <div
                      className="fp-confidence-fill"
                      style={{ width: `${fillWidth}%` }}
                    />
                  </div>
                  <span className="fp-confidence-label">
                    {confidenceLabel(topVector.confidence_score)}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="fp-field">
              <span className="fp-field-label">TOP STRIKE VECTOR</span>
              <span className="fp-field-value--small">—</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <div className="fp-footer">
        <div className="fp-footer-row">
          <span className="fp-footer-key">ONE LINE</span>
          <span className="fp-footer-val">{summary.one_line}</span>
        </div>
        <div className="fp-footer-row">
          <span className="fp-footer-key">DEMO PATH</span>
          <span className="fp-footer-val fp-footer-val--mono">
            {summary.recommended_demo_path}
          </span>
        </div>
        <div className="fp-disclaimer" aria-label="Disclaimer">
          DEFENSIVE FORECAST — NON-ACTIONABLE
        </div>
      </div>
    </div>
  );
}
