// HistoricalAnalogyCard: compact card for one historical analogy entry.
// Used inside StrikeWindowTimeline's expanded detail view.

import './forecast.css';

export interface HistoricalAnalogyProps {
  case_id: string;
  case_name: string;
  pattern_matched: string;
  time_to_burn: string;
  source_ref_ids?: string[];
}

interface HistoricalAnalogyCardProps {
  analogy: HistoricalAnalogyProps;
}

export function HistoricalAnalogyCard({ analogy }: HistoricalAnalogyCardProps) {
  return (
    <div className="hac-card" aria-label={`Historical analogy: ${analogy.case_name}`}>
      <div className="hac-header">
        <span className="hac-case-id">{analogy.case_id}</span>
        <span className="hac-case-name">{analogy.case_name}</span>
      </div>
      <div className="hac-body">{analogy.pattern_matched}</div>
      <div className="hac-footer">
        <span className="hac-burn-chip" aria-label={`Time to burn: ${analogy.time_to_burn}`}>
          ◢ {analogy.time_to_burn}
        </span>
      </div>
    </div>
  );
}
