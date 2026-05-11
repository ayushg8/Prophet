import { useCallback, useEffect, useMemo, useState } from 'react';

const CONTROL_ORIGIN =
  import.meta.env.VITE_PROPHET_CONTROL_ORIGIN || 'http://127.0.0.1:8787';

type ReadinessCheckStatus = 'pass' | 'warn' | 'fail';
type LoadState = 'loading' | 'ok' | 'error';

interface ReadinessCheck {
  id: string;
  label: string;
  status: ReadinessCheckStatus;
  details: string;
  blocking: boolean;
}

interface ReadinessReport {
  ok: boolean;
  generatedAt: string;
  missionId: string;
  checks: ReadinessCheck[];
  summary: {
    total: number;
    pass: number;
    warn: number;
    fail: number;
    blockingFailures: number;
    policyId?: string | null;
    policySha256?: string | null;
    vmScraperEnabled: boolean;
    controlServer: string;
    aiMode: string;
    safetyBoundary: string;
  };
}

function shortHash(value?: string | null): string {
  if (!value) return 'pending';
  return value.length > 14 ? value.slice(0, 14) : value;
}

function statusText(status: ReadinessCheckStatus): string {
  if (status === 'pass') return 'PASS';
  if (status === 'warn') return 'WARN';
  return 'FAIL';
}

function formatGeneratedAt(value?: string): string {
  if (!value) return 'not loaded';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().slice(11, 19).concat('Z');
}

export function ReadinessPanel() {
  const [report, setReport] = useState<ReadinessReport | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);

  const fetchReadiness = useCallback(async () => {
    const response = await fetch(`${CONTROL_ORIGIN}/api/readiness`);
    const payload = (await response.json()) as ReadinessReport;
    if (!response.ok) {
      throw new Error('Readiness endpoint returned an error.');
    }
    return payload;
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialReadiness() {
      try {
        const payload = await fetchReadiness();
        if (cancelled) return;
        setReport(payload);
        setLoadState('ok');
      } catch {
        if (cancelled) return;
        setReport(null);
        setError('Control server offline. Run npm run dev:control.');
        setLoadState('error');
      }
    }

    void loadInitialReadiness();
    return () => {
      cancelled = true;
    };
  }, [fetchReadiness]);

  const loadReadiness = useCallback(async () => {
    setLoadState('loading');
    setError(null);

    try {
      const payload = await fetchReadiness();
      setReport(payload);
      setLoadState('ok');
    } catch {
      setReport(null);
      setError('Control server offline. Run npm run dev:control.');
      setLoadState('error');
    }
  }, [fetchReadiness]);

  const topChecks = useMemo(() => report?.checks ?? [], [report]);
  const summary = report?.summary;

  return (
    <div className="readiness-panel panel" aria-label="Alpha readiness panel">
      <div className="panel-header">
        <span className="panel-header-title">ALPHA READINESS</span>
        <button
          className="readiness-refresh-btn"
          type="button"
          onClick={() => void loadReadiness()}
          disabled={loadState === 'loading'}
          aria-label="Refresh alpha readiness"
        >
          [ {loadState === 'loading' ? 'CHECKING' : 'REFRESH'} ]
        </button>
      </div>

      {loadState === 'error' && (
        <div className="readiness-status readiness-status--error" role="status">
          {error}
        </div>
      )}

      {summary && (
        <div className="readiness-content">
          <div className="readiness-summary" aria-label="Readiness summary">
            <div className={report.ok ? 'readiness-score readiness-score--ok' : 'readiness-score readiness-score--fail'}>
              <span>{report.ok ? 'READY' : 'BLOCKED'}</span>
              <strong>{summary.pass}/{summary.total}</strong>
            </div>
            <div>
              <span>Warn</span>
              <strong>{summary.warn}</strong>
            </div>
            <div>
              <span>Fail</span>
              <strong>{summary.fail}</strong>
            </div>
            <div>
              <span>Policy</span>
              <strong title={summary.policyId ?? undefined}>{shortHash(summary.policySha256)}</strong>
            </div>
            <div>
              <span>AI mode</span>
              <strong>{summary.aiMode}</strong>
            </div>
            <div>
              <span>Generated</span>
              <strong>{formatGeneratedAt(report.generatedAt)}</strong>
            </div>
          </div>

          <ul className="readiness-check-list" aria-label="Readiness checks">
            {topChecks.map((check) => (
              <li
                key={check.id}
                className={`readiness-check readiness-check--${check.status}`}
              >
                <span className="readiness-check-status">
                  {statusText(check.status)}
                </span>
                <span className="readiness-check-main">
                  <strong>{check.label}</strong>
                  <span>{check.details}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
