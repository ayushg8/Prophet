// SourceCitation: inline pill chip for a single source reference.
// No new dependencies. 'use client' not needed — no Next.js; Vite SPA.

import { useState } from 'react';
import './forecast.css';

export interface SourceRefProps {
  id: string;
  label: string;
  url: string;
  date?: string;
  supports?: string;
}

interface SourceCitationProps {
  source: SourceRefProps;
}

export function SourceCitation({ source }: SourceCitationProps) {
  const [hovered, setHovered] = useState(false);

  const handleClick = () => {
    window.open(source.url, '_blank', 'noopener');
  };

  return (
    <button
      type="button"
      className="src-pill"
      onClick={handleClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={`Source: ${source.label} — ${source.url}`}
    >
      [{source.id}]
      {hovered && (
        <span className="src-tooltip" role="tooltip">
          <span className="src-tooltip-label">{source.label}</span>
          <span className="src-tooltip-url">{source.url}</span>
        </span>
      )}
    </button>
  );
}
