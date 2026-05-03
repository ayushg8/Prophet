// StrikeWindowTimeline: horizontal timeline of ranked strike windows.
// Clicking a bar expands an inline detail panel with analogy cards + source chips.
// 'use client' pattern: needs useState for selected window — this is a Vite SPA, no Next.js.

import { useState } from 'react';
import { HistoricalAnalogyCard } from './HistoricalAnalogyCard';
import type { HistoricalAnalogyProps } from './HistoricalAnalogyCard';
import { SourceCitation } from './SourceCitation';
import type { SourceRefProps } from './SourceCitation';
import './forecast.css';

// ── Types ─────────────────────────────────────────────────────────────────

export interface StrikeWindowProps {
  window_id: string;
  rank: number;
  start_date: string;
  end_date: string;
  confidence: 'high' | 'medium' | 'low';
  confidence_score: number;
  why_this_window: string;
  trigger_signals: string[];
  historical_analogies: HistoricalAnalogyProps[];
  source_ref_ids: string[];
}

export interface StrikeForecastProps {
  forecast_id: string;
  generated_at: string;
  strike_windows: StrikeWindowProps[];
  source_refs: SourceRefProps[];
}

interface StrikeWindowTimelineProps {
  forecast?: StrikeForecastProps | null;
}

// ── Default fallback data (edge-appliance golden fixture) ─────────────────

const DEFAULT_FORECAST: StrikeForecastProps = {
  forecast_id: 'ws-golden-edge-appliance-001',
  generated_at: '2026-05-03T00:05:00Z',
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
          time_to_burn: 'weeks of stealth exploitation around public disclosure',
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
        'The Shangri-La Dialogue and Tiananmen anniversary form an Indo-Pacific defense and political-symbolism cluster.',
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
      source_ref_ids: ['src_calendar_shangri_la', 'src_calendar_tiananmen', 'src_hist_8'],
    },
  ],
  source_refs: [
    {
      id: 'src_calendar_trump_xi',
      label: 'Calendar events: Trump-Xi bilateral summit',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'May 14-15, 2026 US-PRC diplomatic summit is a high-value collection window',
    },
    {
      id: 'src_calendar_shangri_la',
      label: 'Calendar events: Shangri-La Dialogue',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'May 29-31, 2026 Indo-Pacific defense forum is a defense-ministry collection window',
    },
    {
      id: 'src_calendar_tiananmen',
      label: 'Calendar events: Tiananmen anniversary',
      url: 'world-side/data/calendar_events.md#master-chronological-table',
      date: '2026-05-02',
      supports: 'June 4 anniversary creates PRC dissident and political-symbolism pressure',
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
      supports: 'PRC-nexus actors have targeted enterprise VPN and edge appliances',
    },
  ],
};

// ── Helpers ───────────────────────────────────────────────────────────────

/** Parse a YYYY-MM-DD string into a Date at noon UTC (avoids DST issues). */
function parseDate(s: string): Date {
  const [y, m, d] = s.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d, 12));
}

/** Format a Date as "DD MMM" in compact mono-caps style. */
function fmtDateShort(d: Date): string {
  const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  return `${String(d.getUTCDate()).padStart(2, '0')} ${months[d.getUTCMonth()]}`;
}

/** Map confidence score (0–1) to bar height between 8px and 32px. */
function scoreToHeight(score: number): number {
  return Math.round(8 + (score * (32 - 8)));
}

// ── Component ─────────────────────────────────────────────────────────────

export function StrikeWindowTimeline({ forecast }: StrikeWindowTimelineProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const data = forecast ?? DEFAULT_FORECAST;

  if (!data.strike_windows || data.strike_windows.length === 0) {
    return (
      <div className="swt-card" aria-label="Strike window timeline">
        <div className="swt-header">
          <span className="swt-eyebrow">
            <span className="swt-eyebrow-chevron" aria-hidden>◢</span>
            STRIKE WINDOWS · RANKED
            <span className="swt-eyebrow-chevron" aria-hidden>◣</span>
          </span>
        </div>
        <div className="swt-null-state">NO WINDOWS AVAILABLE</div>
      </div>
    );
  }

  // Build timeline range: generated_at → +60 days
  const origin = parseDate(data.generated_at.slice(0, 10));
  const rangeMs = 60 * 24 * 60 * 60 * 1000;
  const endTime = new Date(origin.getTime() + rangeMs);

  /** Map a Date to a fraction [0, 1] along the timeline. */
  const toFrac = (d: Date): number =>
    Math.min(1, Math.max(0, (d.getTime() - origin.getTime()) / rangeMs));

  // Date ticks every 7 days
  const ticks: Date[] = [];
  for (let i = 0; i <= 60; i += 7) {
    ticks.push(new Date(origin.getTime() + i * 24 * 60 * 60 * 1000));
  }
  // Always include the final date
  if (ticks[ticks.length - 1].getTime() !== endTime.getTime()) {
    ticks.push(endTime);
  }

  // Build a lookup for source refs by id
  const refMap = new Map<string, SourceRefProps>(
    (data.source_refs ?? []).map((r) => [r.id, r])
  );

  const selectedWindow = data.strike_windows.find((w) => w.window_id === selectedId) ?? null;

  const handleBarClick = (windowId: string) => {
    setSelectedId((prev) => (prev === windowId ? null : windowId));
  };

  return (
    <div className="swt-card" aria-label="Strike window timeline">
      <div className="swt-header">
        <span className="swt-eyebrow">
          <span className="swt-eyebrow-chevron" aria-hidden>◢</span>
          STRIKE WINDOWS · RANKED
          <span className="swt-eyebrow-chevron" aria-hidden>◣</span>
        </span>
      </div>

      <div className="swt-body">
        {/* ── Axis + bars ────────────────────────────────────────────── */}
        <div className="swt-axis-wrap" role="img" aria-label="Strike window timeline axis">
          {/* Horizontal axis line */}
          <div className="swt-axis-line" aria-hidden />

          {/* Date ticks and labels */}
          {ticks.map((t, i) => {
            const pct = toFrac(t) * 100;
            return (
              <div key={i} style={{ position: 'absolute', left: `${pct}%`, bottom: 0 }}>
                <div className="swt-tick" aria-hidden />
                <div className="swt-date-label">{fmtDateShort(t)}</div>
              </div>
            );
          })}

          {/* Strike window bars */}
          {data.strike_windows.map((win) => {
            const startFrac = toFrac(parseDate(win.start_date));
            const endFrac   = toFrac(parseDate(win.end_date));
            const widthPct  = Math.max(1, (endFrac - startFrac) * 100);
            const leftPct   = startFrac * 100;
            const barHeight = scoreToHeight(win.confidence_score);
            const isActive  = selectedId === win.window_id;

            return (
              <div
                key={win.window_id}
                className={`swt-window-group${isActive ? ' swt-window-group--active' : ''}`}
                style={{
                  left: `${leftPct}%`,
                  width: `${widthPct}%`,
                  bottom: '24px',
                }}
                role="button"
                tabIndex={0}
                aria-pressed={isActive}
                aria-label={`Strike window ${win.window_id}, ${win.confidence} confidence (${win.confidence_score.toFixed(2)}), ${win.start_date} to ${win.end_date}`}
                onClick={() => handleBarClick(win.window_id)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleBarClick(win.window_id); }}
              >
                {/* Label above bar */}
                <div className="swt-bar-label">
                  {win.window_id.toUpperCase()} · {win.confidence_score.toFixed(2)}
                </div>

                {/* The colored bar itself */}
                <div
                  className={`swt-window-bar swt-window-bar--${win.confidence}`}
                  style={{ height: `${barHeight}px` }}
                  aria-hidden
                />

                {/* Trigger signal chips */}
                {win.trigger_signals.length > 0 && (
                  <div className="swt-signals" aria-label="Trigger signals">
                    {win.trigger_signals.map((sig) => (
                      <span key={sig} className="swt-signal-chip">
                        <span className="swt-signal-chip-chevron" aria-hidden>◢</span>
                        {sig.toUpperCase()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Expanded detail panel ──────────────────────────────────── */}
        {selectedWindow && (
          <div className="swt-detail" role="region" aria-label={`Detail for ${selectedWindow.window_id}`}>
            <div className="swt-detail-heading">
              ◢ {selectedWindow.window_id.toUpperCase()} · WHY THIS WINDOW
            </div>
            <p className="swt-detail-why">{selectedWindow.why_this_window}</p>

            {selectedWindow.historical_analogies.length > 0 && (
              <div className="swt-detail-analogies" aria-label="Historical analogies">
                {selectedWindow.historical_analogies.map((a) => (
                  <HistoricalAnalogyCard key={a.case_id} analogy={a} />
                ))}
              </div>
            )}

            {selectedWindow.source_ref_ids.length > 0 && (
              <div className="swt-detail-sources" aria-label="Source citations">
                {selectedWindow.source_ref_ids.map((rid) => {
                  const ref = refMap.get(rid);
                  if (!ref) return null;
                  return <SourceCitation key={rid} source={ref} />;
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
