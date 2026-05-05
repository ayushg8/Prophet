export type IntegrationStatus = 'idle' | 'generating' | 'ok' | 'error' | 'blocked';

export interface IntegrationManifest {
  export_id?: string;
  mode?: string;
  evidence_refs?: {
    bundle_id?: string;
    policy_id?: string;
    policy_sha256?: string;
  };
  files?: Record<string, string>;
  hashes?: {
    export_body_sha256?: string;
  };
}

interface IntegrationPanelProps {
  manifest: IntegrationManifest | null;
  status: IntegrationStatus;
  error?: string;
  outputPath?: string;
  onExport: () => void;
}

function shortHash(value?: string): string {
  if (!value) return 'pending';
  return value.length > 18 ? `${value.slice(0, 18)}...` : value;
}

export function IntegrationPanel({
  manifest,
  status,
  error,
  outputPath,
  onExport,
}: IntegrationPanelProps) {
  const isGenerating = status === 'generating';
  const fileCount = Object.keys(manifest?.files ?? {}).length;

  return (
    <div className="integration-panel panel" aria-label="Integration handoff panel">
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          HANDOFF
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <button
          className="integration-export-btn"
          type="button"
          onClick={onExport}
          disabled={isGenerating}
          aria-label="Export integration handoff templates"
        >
          [ {isGenerating ? 'EXPORTING' : 'EXPORT HANDOFF'} ]
        </button>
      </div>

      {status === 'idle' && (
        <div className="integration-placeholder">
          <span className="integration-placeholder-icon" aria-hidden>▧</span>
          <span>AWAITING HANDOFF EXPORT</span>
          <span className="integration-placeholder-sub">
            Generate evidence before SOC review templates
          </span>
        </div>
      )}

      {status === 'generating' && (
        <div className="integration-status integration-status--generating" aria-live="polite">
          Exporting SIEM, ticketing, and audit review templates...
        </div>
      )}

      {(status === 'error' || status === 'blocked') && (
        <div
          className={`integration-status integration-status--${status}`}
          aria-live="polite"
        >
          {error || 'Integration handoff export failed.'}
        </div>
      )}

      {status === 'ok' && manifest && (
        <div className="integration-content">
          <div className="integration-metrics">
            <div>
              <span>Export ID</span>
              <strong>{manifest.export_id ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>{manifest.mode ?? 'review_template_only'}</strong>
            </div>
            <div>
              <span>Files</span>
              <strong>{fileCount}</strong>
            </div>
            <div>
              <span>Export hash</span>
              <strong title={manifest.hashes?.export_body_sha256}>
                {shortHash(manifest.hashes?.export_body_sha256)}
              </strong>
            </div>
            <div>
              <span>Evidence</span>
              <strong>{manifest.evidence_refs?.bundle_id ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Policy</span>
              <strong title={manifest.evidence_refs?.policy_sha256}>
                {manifest.evidence_refs?.policy_id ?? 'unknown'}
              </strong>
            </div>
          </div>

          {outputPath && (
            <div className="integration-path">
              <span>Output</span>
              <strong>{outputPath}</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
