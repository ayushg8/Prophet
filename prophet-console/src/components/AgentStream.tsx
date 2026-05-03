import { useEffect, useRef, useState } from 'react';
import type {
  AgentEvent,
  ToolCallEvent,
  TextEvent,
  PhaseEvent,
  PhaseCompleteEvent,
  ExploitStatusEvent,
  HistoricalAnalogyEvent,
  SourceRefEvent,
} from '../data/mockEvents';
import { HistoricalAnalogyCard } from './HistoricalAnalogyCard';
import { SourceCitation } from './SourceCitation';

// Typewriter component for text events
function TypewriterText({ content }: { content: string }) {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = 0;
    let interval: number | undefined;
    const resetFrame = window.requestAnimationFrame(() => {
      setDisplayed('');
      interval = window.setInterval(() => {
        if (indexRef.current < content.length) {
          indexRef.current += 1;
          setDisplayed(content.slice(0, indexRef.current));
        } else if (interval !== undefined) {
          window.clearInterval(interval);
        }
      }, 22);
    });
    return () => {
      window.cancelAnimationFrame(resetFrame);
      if (interval !== undefined) window.clearInterval(interval);
    };
  }, [content]);

  return (
    <p className="stream-text">
      {displayed}
      {displayed.length < content.length && <span className="cursor-blink">▎</span>}
    </p>
  );
}

// Tool call card: elevated surface + backdrop blur
function ToolCallCard({ event }: { event: ToolCallEvent }) {
  const [elapsed, setElapsed] = useState<number | null>(null);

  useEffect(() => {
    const start = Date.now();
    const t = setTimeout(() => {
      setElapsed((Date.now() - start) / 1000);
    }, event.durationMs);
    return () => clearTimeout(t);
  }, [event.durationMs]);

  return (
    <div className="tool-call-card stream-item">
      <div className="tool-call-header">
        <span className="tool-call-icon" aria-hidden>⟩</span>
        <span className="tool-call-name">{event.tool}()</span>
        <div className="tool-call-status">
          {elapsed === null ? (
            <span className="tool-running">running…</span>
          ) : (
            <span className="tool-done">✓ {elapsed.toFixed(2)}s</span>
          )}
        </div>
      </div>
      {Object.keys(event.args).length > 0 && (
        <div className="tool-call-args">
          {Object.entries(event.args).map(([k, v]) => (
            <span key={k} className="tool-arg">
              <span className="tool-arg-key">{k}</span>
              <span className="tool-arg-eq">=</span>
              <span className="tool-arg-val">{JSON.stringify(v)}</span>
            </span>
          ))}
        </div>
      )}
      {event.result && elapsed !== null && (
        <div className="tool-call-result">
          <span className="tool-result-prefix">→ </span>
          {event.result}
        </div>
      )}
    </div>
  );
}

// Phase-start divider: amber hairline with mono label
function PhaseBadge({ event }: { event: PhaseEvent }) {
  // Format: ── PHASE I · INTEL ──
  const label = `── ${event.label.toUpperCase()} ──`;
  return (
    <div className="phase-badge stream-item" role="separator" aria-label={event.label}>
      <div className="phase-badge-line" aria-hidden />
      <span className="phase-badge-label">{label}</span>
      <div className="phase-badge-line" aria-hidden />
    </div>
  );
}

// Phase-complete divider: green hairline with mono label
function PhaseCompleteBadge({ event }: { event: PhaseCompleteEvent }) {
  const label = `── ${event.phase} COMPLETE ──`;
  return (
    <div className="phase-complete-badge stream-item" role="separator" aria-label={`${event.phase} complete`}>
      <div className="phase-complete-line" aria-hidden />
      <span className="phase-complete-label">{label}</span>
      <div className="phase-complete-line" aria-hidden />
    </div>
  );
}

function ExploitStatusBadge({ event }: { event: ExploitStatusEvent }) {
  if (event.status === 'running') {
    return (
      <div className="exploit-status-badge exploit-status-badge--running stream-item">
        <span className="exploit-status-dot exploit-status-dot--running" aria-hidden />
        <span>EXECUTING NUCLEI TEMPLATE…</span>
      </div>
    );
  }
  return null;
}

function HumanGatePlaceholder() {
  return (
    <div className="gate-placeholder stream-item">
      <span className="gate-lock" aria-hidden>⊗</span>
      <span className="gate-text">Human authorization gate — awaiting operator decision</span>
    </div>
  );
}

interface AgentStreamProps {
  events: AgentEvent[];
  gateOpen: boolean;
}

export function AgentStream({ events, gateOpen }: AgentStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <>
      {/* Eyebrow-style header: mono caps, letter-spacing 0.42em, amber */}
      <div className="agent-stream-header" aria-hidden>
        AGENT REASONING STREAM
      </div>
      <div className="agent-stream" aria-label="Agent reasoning stream" aria-live="polite">
        {events.length === 0 && (
          <div className="stream-empty">
            <span className="stream-empty-icon" aria-hidden>◈</span>
            <span>Awaiting initialization — press INITIATE PROPHET LOOP to begin</span>
          </div>
        )}

        {events.map((event, idx) => {
          const key = `${event.kind}-${idx}`;

          if (event.kind === 'phase') {
            return <PhaseBadge key={key} event={event as PhaseEvent} />;
          }
          if (event.kind === 'phase_complete') {
            return <PhaseCompleteBadge key={key} event={event as PhaseCompleteEvent} />;
          }
          if (event.kind === 'tool_call') {
            return <ToolCallCard key={key} event={event as ToolCallEvent} />;
          }
          if (event.kind === 'text') {
            return (
              <div key={key} className="stream-item stream-text-wrapper">
                <TypewriterText content={(event as TextEvent).content} />
              </div>
            );
          }
          if (event.kind === 'human_gate') {
            if (gateOpen) {
              return null; // modal is shown separately
            }
            return <HumanGatePlaceholder key={key} />;
          }
          if (event.kind === 'exploit_status') {
            return <ExploitStatusBadge key={key} event={event as ExploitStatusEvent} />;
          }
          if (event.kind === 'historical_analogy') {
            const e = event as HistoricalAnalogyEvent;
            return (
              <div key={key} className="stream-item stream-analogy-wrapper">
                <div className="stream-analogy-eyebrow">
                  ◢ HISTORICAL ANALOGY · {e.windowId.toUpperCase()} ◣
                </div>
                <HistoricalAnalogyCard analogy={e.analogy} />
              </div>
            );
          }
          if (event.kind === 'source_ref') {
            const e = event as SourceRefEvent;
            return (
              <div key={key} className="stream-item stream-source-wrapper">
                <span className="stream-source-prefix">◢ SOURCE</span>
                <SourceCitation source={e.ref} />
              </div>
            );
          }
          // patch_diff, sigma_rule, forecast_summary handled in panels, not stream
          return null;
        })}

        <div ref={bottomRef} />
      </div>
    </>
  );
}
