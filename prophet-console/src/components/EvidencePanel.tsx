import { useState } from 'react';

export type EvidenceStatus = 'idle' | 'generating' | 'ok' | 'error' | 'blocked';

export type EvidenceArtifactSourceKey = 'sandbox_runtime' | 'checked_in_fixture' | string;

export interface EvidenceArtifactSource {
  key?: EvidenceArtifactSourceKey;
  label?: string;
  mode?: string;
  path?: string;
}

export interface EvidenceAssetContext {
  inventory_id?: string;
  matched_exposure_class?: string;
  affected_asset_count?: number;
  criticality_summary?: Record<string, number>;
  recommended_owner_queue?: string[];
}

export interface EvidenceOpenSourceSummary {
  integrated?: boolean;
  record_count?: number;
  freshness?: {
    status?: string;
    newest_record_observed_at?: string;
    newest_record_age_days?: number | null;
    freshness_window_days?: number;
  };
  source_health?: {
    status?: string;
    successful_source_count?: number;
    failed_source_count?: number;
  };
  source_failures?: Array<{
    source_id?: string;
    status?: string;
    error?: string;
  }>;
  successful_sources?: string[];
  failed_sources?: string[];
}

export interface EvidenceBundle {
  bundle_id?: string;
  bundle_sha256?: string;
  input_refs?: {
    forecast_id?: string;
    artifact_id?: string;
  };
  operator_approval?: {
    decision?: string;
  };
  validation_summary?: {
    post_patch_status?: string;
  };
  open_source_summary?: EvidenceOpenSourceSummary;
  asset_context?: EvidenceAssetContext;
}

interface EvidencePanelProps {
  bundle: EvidenceBundle | null;
  markdown: string;
  status: EvidenceStatus;
  error?: string;
  artifactSource?: EvidenceArtifactSource | null;
  onGenerate: () => void;
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button className="copy-btn" type="button" onClick={handleCopy} aria-label={label}>
      [ {copied ? 'COPIED' : 'COPY'} ]
    </button>
  );
}

function shortHash(value?: string): string {
  if (!value) return 'pending';
  return value.length > 18 ? `${value.slice(0, 18)}...` : value;
}

function formatAgeDays(value?: number | null): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'unknown';
  }
  return `${Number.isInteger(value) ? value : value.toFixed(2)}d`;
}

function sourceHealthTone(summary?: EvidenceOpenSourceSummary): 'ok' | 'warn' | 'unknown' {
  if (!summary?.integrated) {
    return 'unknown';
  }

  const failedCount =
    summary.source_health?.failed_source_count ??
    summary.source_failures?.length ??
    summary.failed_sources?.length ??
    0;
  const healthStatus = summary.source_health?.status?.toLowerCase();
  const freshnessStatus = summary.freshness?.status?.toLowerCase();

  if (failedCount > 0 || healthStatus === 'degraded' || freshnessStatus === 'stale') {
    return 'warn';
  }

  return 'ok';
}

function artifactSourceCopy(source?: EvidenceArtifactSource | null): {
  label: string;
  detail: string;
  tone: 'runtime' | 'fixture' | 'unknown';
} {
  if (!source?.key) {
    return {
      label: 'Source pending',
      detail: 'Generate evidence to select a defense artifact.',
      tone: 'unknown',
    };
  }

  if (source.key === 'sandbox_runtime') {
    return {
      label: source.label || 'Sandbox runtime artifact',
      detail: source.path || 'Validated localhost sandbox output.',
      tone: 'runtime',
    };
  }

  if (source.key === 'checked_in_fixture') {
    return {
      label: source.label || 'Checked-in defense fixture',
      detail: source.path || 'Fixture-backed defensive artifact.',
      tone: 'fixture',
    };
  }

  return {
    label: source.label || source.key,
    detail: source.path || source.mode || 'Evidence artifact source recorded.',
    tone: 'unknown',
  };
}

function SourceFreshnessCard({ summary }: { summary?: EvidenceOpenSourceSummary }) {
  const freshness = summary?.freshness;
  const health = summary?.source_health;
  const failures = summary?.source_failures ?? [];
  const successfulCount =
    health?.successful_source_count ?? summary?.successful_sources?.length ?? 0;
  const failedCount =
    health?.failed_source_count ?? failures.length ?? summary?.failed_sources?.length ?? 0;
  const freshnessStatus = freshness?.status ?? (summary?.integrated ? 'reported' : 'pending');
  const healthStatus = health?.status ?? (summary?.integrated ? 'reported' : 'pending');
  const tone = sourceHealthTone(summary);

  return (
    <div
      className={`evidence-source-health evidence-source-health--${tone}`}
      aria-label="Source freshness and failures"
    >
      <div className="evidence-source-health-header">
        <span>OSINT basis</span>
        <strong>{`${freshnessStatus} / ${healthStatus}`}</strong>
      </div>

      <div className="evidence-source-health-grid">
        <div>
          <span>Newest record</span>
          <strong>{freshness?.newest_record_observed_at ?? 'unknown'}</strong>
        </div>
        <div>
          <span>Newest age</span>
          <strong>{formatAgeDays(freshness?.newest_record_age_days)}</strong>
        </div>
        <div>
          <span>Sources ok</span>
          <strong>{successfulCount}</strong>
        </div>
        <div>
          <span>Failures</span>
          <strong>{failedCount}</strong>
        </div>
      </div>

      {failures.length > 0 ? (
        <ul className="evidence-source-failure-list">
          {failures.slice(0, 3).map((failure, index) => (
            <li key={`${failure.source_id ?? 'source'}-${index}`}>
              <strong>{failure.source_id ?? 'unknown source'}</strong>
              <span>{failure.error ?? failure.status ?? 'failure recorded'}</span>
            </li>
          ))}
        </ul>
      ) : (
        <small>No sanitized source failures recorded.</small>
      )}
    </div>
  );
}

export function EvidencePanel({
  bundle,
  markdown,
  status,
  error,
  artifactSource,
  onGenerate,
}: EvidencePanelProps) {
  const jsonText = bundle ? JSON.stringify(bundle, null, 2) : '';
  const isGenerating = status === 'generating';
  const sourceCopy = artifactSourceCopy(artifactSource);

  return (
    <div className="evidence-panel panel" aria-label="Evidence bundle panel">
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          EVIDENCE
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <button
          className="evidence-generate-btn"
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          aria-label="Generate evidence bundle"
        >
          [ {isGenerating ? 'GENERATING' : 'GENERATE EVIDENCE'} ]
        </button>
      </div>

      {status === 'idle' && (
        <div className="evidence-placeholder">
          <span className="evidence-placeholder-icon" aria-hidden>◨</span>
          <span>AWAITING EVIDENCE EXPORT</span>
          <span className="evidence-placeholder-sub">
            Load fixture or complete Prophet loop first
          </span>
        </div>
      )}

      {status === 'generating' && (
        <div className="evidence-status evidence-status--generating" aria-live="polite">
          Generating validated JSON and Markdown bundle...
        </div>
      )}

      {(status === 'error' || status === 'blocked') && (
        <div
          className={`evidence-status evidence-status--${status}`}
          aria-live="polite"
        >
          {error || 'Evidence generation failed.'}
        </div>
      )}

      {status === 'ok' && bundle && (
        <div className="evidence-content">
          <div
            className={`evidence-artifact-source evidence-artifact-source--${sourceCopy.tone}`}
            aria-label="Sandbox artifact source"
          >
            <span>Artifact source</span>
            <strong>{sourceCopy.label}</strong>
            <small title={sourceCopy.detail}>{sourceCopy.detail}</small>
          </div>

          <SourceFreshnessCard summary={bundle.open_source_summary} />

          <div className="evidence-metrics">
            <div>
              <span>Bundle ID</span>
              <strong>{bundle.bundle_id ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Bundle SHA-256</span>
              <strong title={bundle.bundle_sha256}>{shortHash(bundle.bundle_sha256)}</strong>
            </div>
            <div>
              <span>Forecast ID</span>
              <strong>{bundle.input_refs?.forecast_id ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Artifact ID</span>
              <strong>{bundle.input_refs?.artifact_id ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Approval</span>
              <strong>{bundle.operator_approval?.decision ?? 'unknown'}</strong>
            </div>
            <div>
              <span>Validation</span>
              <strong>{bundle.validation_summary?.post_patch_status ?? 'unknown'}</strong>
            </div>
          </div>

          <div className="evidence-copy-row">
            <CopyButton text={jsonText} label="Copy evidence JSON" />
            <CopyButton text={markdown} label="Copy evidence Markdown" />
          </div>
        </div>
      )}
    </div>
  );
}
