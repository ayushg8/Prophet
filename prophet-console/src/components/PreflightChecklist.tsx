// PreflightChecklist: mirrors the real setup_status.py checks.
// Each item ticks ✓ in sequence over 1.2s on mount.
// All checks must be ✓ before the run button enables.
// Re-runs on reset (isRunning: false → true transition).

import { useEffect, useState } from 'react';

interface CheckItem {
  id: string;
  label: string;
  detail: string;
}

const CHECKS: CheckItem[] = [
  { id: 'kev',       label: 'KEV CATALOG',       detail: 'refreshed 14:32Z' },
  { id: 'nvd',       label: 'NVD CVE 2.0',        detail: 'streaming' },
  { id: 'epss',      label: 'EPSS v4 BASELINE',   detail: 'loaded' },
  { id: 'target',    label: 'LAB TARGET',          detail: '[LAB-HOST]:8080 · reachable' },
  { id: 'vulnapp',   label: 'VULNERABLEAPP',       detail: 'Log4j 2.14.0 · running' },
  { id: 'sandbox',   label: 'SANDBOX ISOLATION',   detail: 'enforced' },
  { id: 'cvp',       label: 'ANTHROPIC CVP',       detail: 'authorized' },
  { id: 'qwen',      label: 'QWEN EXECUTOR',       detail: 'online · [LLM-HOST]:1234' },
];

// Total animation budget: 1.2s across all items
const TICK_INTERVAL_MS = 1200 / CHECKS.length;

interface PreflightChecklistProps {
  /** Increments on each run/reset cycle — used to re-trigger animation */
  isRunning: number;
  onReady: (ready: boolean) => void;
}

export function PreflightChecklist({ isRunning, onReady }: PreflightChecklistProps) {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [animating, setAnimating] = useState(true);

  // Re-run checklist animation on each run cycle
  useEffect(() => {
    setChecked(new Set());
    setAnimating(true);
    onReady(false);

    let idx = 0;
    const tick = () => {
      if (idx >= CHECKS.length) {
        setAnimating(false);
        onReady(true);
        return;
      }
      const id = CHECKS[idx].id;
      setChecked((prev) => new Set([...prev, id]));
      idx += 1;
      timer = window.setTimeout(tick, TICK_INTERVAL_MS);
    };

    let timer = window.setTimeout(tick, 200);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning]);

  const allDone = checked.size === CHECKS.length;

  return (
    <div className="preflight" aria-label="Pre-flight checks">
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          PRE-FLIGHT
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <span
          className={`panel-header-badge preflight-badge${allDone ? ' preflight-badge--ready' : ''}`}
          aria-live="polite"
        >
          {allDone ? 'READY' : `${checked.size}/${CHECKS.length}`}
        </span>
      </div>

      <ul className="preflight-list" role="list" aria-label="Pre-flight check items">
        {CHECKS.map((item) => {
          const done = checked.has(item.id);
          const isNext = !done && checked.size === CHECKS.findIndex((c) => c.id === item.id) && animating;
          return (
            <li
              key={item.id}
              className={`preflight-item${done ? ' preflight-item--done' : isNext ? ' preflight-item--checking' : ''}`}
              aria-label={`${item.label}: ${done ? 'passed' : 'pending'}`}
            >
              <span className="preflight-tick" aria-hidden>
                {done ? '✓' : isNext ? '…' : '·'}
              </span>
              <span className="preflight-label">{item.label}</span>
              <span className="preflight-detail">{item.detail}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
