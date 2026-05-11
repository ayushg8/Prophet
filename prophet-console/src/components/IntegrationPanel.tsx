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
  downloadError?: string;
  downloadingArtifact?: string | null;
  outputPath?: string;
  onExport: () => void;
  onDownloadArtifact?: (artifactId: string) => void;
}

function shortHash(value?: string): string {
  if (!value) return 'pending';
  return value.length > 18 ? `${value.slice(0, 18)}...` : value;
}

const ARTIFACT_LABELS: Record<string, string> = {
  manifest: 'Manifest',
  splunk_saved_search: 'Splunk',
  elastic_detection_rule: 'Elastic',
  sentinel_analytic_rule: 'Sentinel',
  jira_ticket: 'Jira',
  servicenow_task: 'ServiceNow',
  operator_audit_event: 'Audit event',
  review_checklist: 'Checklist',
  review_zip: 'Review ZIP',
};

const ARTIFACT_ORDER = [
  'manifest',
  'splunk_saved_search',
  'elastic_detection_rule',
  'sentinel_analytic_rule',
  'jira_ticket',
  'servicenow_task',
  'operator_audit_event',
  'review_checklist',
];

function artifactEntries(files?: Record<string, string>): Array<[string, string]> {
  const entries = Object.entries(files ?? {});
  return entries.sort(([left], [right]) => {
    const leftIndex = ARTIFACT_ORDER.indexOf(left);
    const rightIndex = ARTIFACT_ORDER.indexOf(right);
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
  });
}

export function IntegrationPanel({
  manifest,
  status,
  error,
  downloadError,
  downloadingArtifact,
  outputPath,
  onExport,
  onDownloadArtifact,
}: IntegrationPanelProps) {
  const isGenerating = status === 'generating';
  const fileCount = Object.keys(manifest?.files ?? {}).length;
  const downloads = artifactEntries(manifest?.files);

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

          {onDownloadArtifact && downloads.length > 0 && (
            <div className="integration-downloads" aria-label="Handoff artifact downloads">
              <div className="integration-downloads-header">
                <span>Review Downloads</span>
                <strong>local only</strong>
              </div>
              <div className="integration-download-grid">
                {downloads.map(([artifactId, relativePath]) => {
                  const label = ARTIFACT_LABELS[artifactId] ?? artifactId;
                  const isDownloading = downloadingArtifact === artifactId;
                  return (
                    <button
                      key={artifactId}
                      className="integration-download-btn"
                      type="button"
                      onClick={() => onDownloadArtifact(artifactId)}
                      disabled={Boolean(downloadingArtifact)}
                      aria-label={`Download ${label} handoff artifact`}
                      title={relativePath}
                    >
                      <span>{label}</span>
                      <small>{isDownloading ? 'downloading' : relativePath}</small>
                    </button>
                  );
                })}
                <button
                  className="integration-download-btn integration-download-btn--zip"
                  type="button"
                  onClick={() => onDownloadArtifact('review_zip')}
                  disabled={Boolean(downloadingArtifact)}
                  aria-label="Download review ZIP handoff artifact"
                >
                  <span>{ARTIFACT_LABELS.review_zip}</span>
                  <small>{downloadingArtifact === 'review_zip' ? 'downloading' : 'validated bundle'}</small>
                </button>
              </div>
              {downloadError && (
                <div className="integration-download-error" aria-live="polite">
                  {downloadError}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
