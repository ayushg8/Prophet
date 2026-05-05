import { useCallback, useEffect, useMemo, useState } from 'react';

const CONTROL_ORIGIN =
  import.meta.env.VITE_PROPHET_CONTROL_ORIGIN || 'http://127.0.0.1:8787';

type LoadState = 'loading' | 'ok' | 'error';
type PolicyGateStatus = 'allowed' | 'blocked';

interface PolicyActionGate {
  id: string;
  label: string;
  status: PolicyGateStatus;
  details: string;
}

interface PolicyStatusReport {
  ok: boolean;
  status: string;
  generatedAt: string;
  message?: string;
  policy?: {
    policyId?: string;
    policySha256?: string;
    path?: string;
    allowedModes?: Record<string, string[]>;
    allowedSourceIds?: string[];
    allowedSandboxProfiles?: string[];
    allowedIntegrationExports?: string[];
    retention?: {
      runtime_outputs_max_days?: number;
      audit_log_max_days?: number;
      customer_metadata_max_days?: number;
    };
  };
  blockedControls: string[];
  actionGates: PolicyActionGate[];
  summary: {
    blockedControlCount: number;
    allowedGateCount: number;
    blockedGateCount: number;
    vmScraperEnabled: boolean;
    controlServer: string;
  };
}

const CONTROL_LABELS: Record<string, string> = {
  live_targets_allowed: 'Live targets',
  live_vm_scraper_allowed: 'Live VM scraper',
  arbitrary_target_input_allowed: 'Arbitrary target input',
  payload_generation_allowed: 'Payload generation',
  raw_scraper_text_allowed: 'Raw scraper text',
  private_hostnames_allowed: 'Private hostnames',
  credentials_allowed: 'Credentials',
};

function shortHash(value?: string): string {
  if (!value) return 'pending';
  return value.length > 18 ? `${value.slice(0, 18)}...` : value;
}

function gateStatusText(status: PolicyGateStatus): string {
  return status === 'allowed' ? 'ALLOWED' : 'POLICY BLOCKED';
}

function controlLabel(value: string): string {
  return CONTROL_LABELS[value] ?? value.replaceAll('_', ' ');
}

function formatGeneratedAt(value?: string): string {
  if (!value) return 'not loaded';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().slice(11, 19).concat('Z');
}

export function PolicyStatusPanel() {
  const [report, setReport] = useState<PolicyStatusReport | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);

  const fetchPolicyStatus = useCallback(async () => {
    const response = await fetch(`${CONTROL_ORIGIN}/api/policy/status`);
    const payload = (await response.json()) as PolicyStatusReport;
    if (!response.ok) {
      throw new Error(payload.message || 'Policy status endpoint returned an error.');
    }
    return payload;
  }, []);

  const loadPolicyStatus = useCallback(async () => {
    setLoadState('loading');
    setError(null);

    try {
      const payload = await fetchPolicyStatus();
      setReport(payload);
      setLoadState('ok');
    } catch {
      setReport(null);
      setError('Control server offline. Run npm run dev:control.');
      setLoadState('error');
    }
  }, [fetchPolicyStatus]);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialPolicyStatus() {
      try {
        const payload = await fetchPolicyStatus();
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

    void loadInitialPolicyStatus();
    return () => {
      cancelled = true;
    };
  }, [fetchPolicyStatus]);

  const blockedControls = useMemo(
    () => report?.blockedControls.map(controlLabel) ?? [],
    [report],
  );

  const retentionLabel = report?.policy?.retention
    ? `${report.policy.retention.runtime_outputs_max_days ?? 'n/a'}d runtime / ${
        report.policy.retention.audit_log_max_days ?? 'n/a'
      }d audit`
    : 'pending';

  return (
    <div className="policy-status-panel panel" aria-label="Policy status panel">
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          POLICY STATUS
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <button
          className="policy-status-refresh-btn"
          type="button"
          onClick={() => void loadPolicyStatus()}
          disabled={loadState === 'loading'}
          aria-label="Refresh policy status"
        >
          [ {loadState === 'loading' ? 'CHECKING' : 'REFRESH'} ]
        </button>
      </div>

      {loadState === 'error' && (
        <div className="policy-status-alert policy-status-alert--error" role="status">
          {error}
        </div>
      )}

      {report && loadState !== 'loading' && (
        <div className="policy-status-content">
          {!report.ok && (
            <div className="policy-status-alert policy-status-alert--error" role="status">
              {report.message || 'Pilot policy is unreadable.'}
            </div>
          )}

          {report.policy && (
            <>
              <div className="policy-status-summary" aria-label="Policy summary">
                <div>
                  <span>Policy</span>
                  <strong title={report.policy.policyId}>{report.policy.policyId ?? 'unknown'}</strong>
                </div>
                <div>
                  <span>SHA-256</span>
                  <strong title={report.policy.policySha256}>
                    {shortHash(report.policy.policySha256)}
                  </strong>
                </div>
                <div>
                  <span>Runtime</span>
                  <strong>{report.summary.vmScraperEnabled ? 'VM flag on' : 'Fixture mode'}</strong>
                </div>
                <div>
                  <span>Retention</span>
                  <strong title={retentionLabel}>{retentionLabel}</strong>
                </div>
                <div>
                  <span>Sources</span>
                  <strong>{report.policy.allowedSourceIds?.length ?? 0} allowed</strong>
                </div>
                <div>
                  <span>Generated</span>
                  <strong>{formatGeneratedAt(report.generatedAt)}</strong>
                </div>
              </div>

              <ul className="policy-gate-list" aria-label="Policy action gates">
                {report.actionGates.map((gate) => (
                  <li
                    key={gate.id}
                    className={`policy-gate policy-gate--${gate.status}`}
                  >
                    <span className="policy-gate-status">{gateStatusText(gate.status)}</span>
                    <span className="policy-gate-main">
                      <strong>{gate.label}</strong>
                      <span>{gate.details}</span>
                    </span>
                  </li>
                ))}
              </ul>

              <div className="policy-blocked-controls" aria-label="Policy blocked controls">
                <span>Blocked controls</span>
                <div>
                  {blockedControls.map((control) => (
                    <strong key={control}>{control}</strong>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
