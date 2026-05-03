import { useEffect, useRef, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-diff';
import 'prismjs/components/prism-yaml';

type DefenceTab = 'patch' | 'sigma';

interface DefencePanelProps {
  patchDiff: string | null;
  sigmaRule: string | null;
}

// Bracketed [ COPY ] / [ COPIED ] button
function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button className="copy-btn" onClick={handleCopy} aria-label={label}>
      [ {copied ? 'COPIED' : 'COPY'} ]
    </button>
  );
}

interface CodeBlockProps {
  code: string;
  language: string;
}

// Elevated surface + backdrop-blur code block
function CodeBlock({ code, language }: CodeBlockProps) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (ref.current) {
      Prism.highlightElement(ref.current);
    }
  }, [code, language]);

  return (
    <pre className="defence-code-pre">
      <code ref={ref} className={`language-${language}`}>
        {code}
      </code>
    </pre>
  );
}

export function DefencePanel({ patchDiff, sigmaRule }: DefencePanelProps) {
  const [activeTab, setActiveTab] = useState<DefenceTab>('patch');

  const hasContent = patchDiff !== null || sigmaRule !== null;

  return (
    <div className="defence-panel panel" aria-label="Defence panel">
      {/* Eyebrow-style header */}
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          DEFENCE ARTIFACTS
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        {hasContent && (
          <div className="defence-tabs" role="tablist" aria-label="Defence artifact tabs">
            <button
              role="tab"
              aria-selected={activeTab === 'patch'}
              className={`defence-tab${activeTab === 'patch' ? ' defence-tab--active' : ''}`}
              onClick={() => setActiveTab('patch')}
            >
              PATCH
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'sigma'}
              className={`defence-tab${activeTab === 'sigma' ? ' defence-tab--active' : ''}`}
              onClick={() => setActiveTab('sigma')}
            >
              SIGMA
            </button>
          </div>
        )}
      </div>

      {!hasContent && (
        <div className="defence-placeholder">
          <span className="defence-placeholder-icon" aria-hidden>◧</span>
          <span>AWAITING DEFENCE GENERATION</span>
          <span className="defence-placeholder-sub">
            Patch diff and Sigma rule will appear after Phase IV
          </span>
        </div>
      )}

      {hasContent && (
        <div className="defence-content">
          {activeTab === 'patch' && (
            <div className="defence-tab-content" role="tabpanel" aria-label="Patch diff">
              {patchDiff ? (
                <>
                  <div className="defence-tab-toolbar">
                    <span className="defence-file-label">log4j2.xml · docker-compose.yml</span>
                    <CopyButton text={patchDiff} label="Copy patch diff" />
                  </div>
                  <CodeBlock code={patchDiff} language="diff" />
                </>
              ) : (
                <div className="defence-tab-pending">Generating patch…</div>
              )}
            </div>
          )}

          {activeTab === 'sigma' && (
            <div className="defence-tab-content" role="tabpanel" aria-label="Sigma rule">
              {sigmaRule ? (
                <>
                  <div className="defence-tab-toolbar">
                    <span className="defence-file-label">log4shell-detection.yml</span>
                    <CopyButton text={sigmaRule} label="Copy Sigma rule" />
                  </div>
                  <CodeBlock code={sigmaRule} language="yaml" />
                </>
              ) : (
                <div className="defence-tab-pending">Generating rule…</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
