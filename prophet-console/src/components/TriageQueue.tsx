import type { CVERecord } from '../data/cves';

interface CVECardProps {
  cve: CVERecord;
  selected: boolean;
  onSelect: () => void;
}

function cvssColor(label: CVERecord['cvssLabel']): string {
  switch (label) {
    case 'CRITICAL': return 'var(--danger)';
    case 'HIGH': return '#e3b341';
    case 'MEDIUM': return 'var(--info)';
    case 'LOW': return 'var(--secondary)';
  }
}

function CVECard({ cve, selected, onSelect }: CVECardProps) {
  return (
    <button
      className={`cve-card${selected ? ' cve-card--selected' : ''}`}
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`Select ${cve.cveId}`}
    >
      <div className="cve-card-header">
        <span className="cve-rank">#{cve.rank}</span>
        <span className="cve-id">{cve.cveId}</span>
        <span
          className="cvss-chip"
          style={{ color: cvssColor(cve.cvssLabel), borderColor: cvssColor(cve.cvssLabel) }}
        >
          {cve.cvss.toFixed(1)}
        </span>
      </div>

      <div className="cve-vendor">
        {cve.vendor} · {cve.product}
      </div>

      <div className="cve-desc">{cve.description}</div>

      <div className="cve-epss-row">
        <span className="cve-epss-label">EPSS</span>
        <div
          className="cve-epss-track"
          role="progressbar"
          aria-valuenow={cve.epss * 100}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`EPSS score ${(cve.epss * 100).toFixed(0)}%`}
        >
          <div
            className="cve-epss-fill"
            style={{ width: `${cve.epss * 100}%` }}
          />
        </div>
        <span className="cve-epss-val">{(cve.epss * 100).toFixed(0)}%</span>
      </div>

      <div className="cve-signals">
        {cve.nuclei && <span className="signal-chip signal-active">NUCLEI ✓</span>}
        {cve.exploitDb && <span className="signal-chip signal-active">EXPLOIT-DB ✓</span>}
        <span className="signal-chip signal-active">ATT&CK {cve.attackTechnique}</span>
      </div>
    </button>
  );
}

interface TriageQueueProps {
  cves: CVERecord[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export function TriageQueue({ cves, selectedId, onSelect }: TriageQueueProps) {
  const activeCount = cves.length * 2 + 2;

  return (
    <aside className="triage-queue" aria-label="Triage Queue">
      <div className="panel-header">
        {/* Eyebrow-style header with ◢ / ◣ chevron pattern */}
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          TRIAGE QUEUE
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <span className="panel-header-badge">{activeCount} ACTIVE</span>
      </div>

      <div className="queue-list">
        {cves.map((cve) => (
          <CVECard
            key={cve.cveId}
            cve={cve}
            selected={cve.cveId === selectedId}
            onSelect={() => onSelect(cve.cveId)}
          />
        ))}
      </div>
    </aside>
  );
}
