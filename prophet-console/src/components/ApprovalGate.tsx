interface ApprovalGateProps {
  onAuthorize: () => void;
  onHold: () => void;
}

export function ApprovalGate({ onAuthorize, onHold }: ApprovalGateProps) {
  return (
    <div className="gate-overlay" role="dialog" aria-modal="true" aria-labelledby="gate-title">
      <div className="gate-card">
        <div className="gate-card-header">
          {/* Eyebrow: AUTHORIZATION REQUIRED — amber, 0.42em */}
          <div className="gate-eyebrow">AUTHORIZATION REQUIRED</div>

          {/* Title: thin display caps, font-weight 200, matching landing__title scaled down */}
          <h2 id="gate-title" className="gate-title">HUMAN-IN-THE-LOOP GATE</h2>

          {/* Amber gradient divider */}
          <div className="gate-divider" aria-hidden />

          <p className="gate-subtitle">
            Phase III — Nuclei template execution pending operator approval
          </p>
        </div>

        <div className="gate-body">
          <div className="gate-detail-grid">
            <div className="gate-detail-row">
              <span className="gate-detail-key">TARGET</span>
              <span className="gate-detail-val mono">[LAB-HOST]:8080 · VulnerableApp · sandboxed</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">CVE</span>
              <span className="gate-detail-val mono">CVE-2021-44228 — Log4Shell · CVSS 10.0</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">CLASS</span>
              <span className="gate-detail-val">JNDI lookup exploit class</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">TEMPLATE</span>
              <span className="gate-detail-val mono">http/cves/2021/CVE-2021-44228.yaml</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">EXECUTOR</span>
              <span className="gate-detail-val mono">Codex terminal · operator approved</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">PLAN</span>
              <span className="gate-detail-val">Run fixture-scoped validation against the localhost sandbox · render defense artifact · keep rollback sandbox-only</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">ACTION</span>
              <span className="gate-detail-val">Public validation template · detection and patch validation only</span>
            </div>
            <div className="gate-detail-row">
              <span className="gate-detail-key">SCOPE</span>
              <span className="gate-detail-val">Sandbox-isolated lab target · fixture fallback available · no live infrastructure</span>
            </div>
          </div>

          <div className="gate-warning" role="alert">
            <span className="gate-warning-icon" aria-hidden>△</span>
            <span>
              Execution is scoped to a network-isolated, vulnerable-by-design container.
              No live infrastructure will be contacted. Operator assumes responsibility
              for confirming sandbox containment before proceeding.
            </span>
          </div>
        </div>

        {/* Bracketed buttons side by side */}
        <div className="gate-actions">
          <button
            className="gate-btn gate-btn--hold"
            onClick={onHold}
            aria-label="Hold — pause execution and reset"
          >
            <span className="gate-btn-bracket">[</span>
            HOLD AND RESET
            <span className="gate-btn-bracket">]</span>
          </button>
          <button
            className="gate-btn gate-btn--authorize"
            onClick={onAuthorize}
            aria-label="Authorize execution"
          >
            <span className="gate-btn-bracket">[</span>
            AUTHORIZE EXECUTION
            <span className="gate-btn-bracket">]</span>
          </button>
        </div>

        {/* Operator session footer */}
        <div className="gate-footer">
          <span>OPERATOR</span>
          <span className="gate-footer-sep">·</span>
          <span>idan@prophet.local</span>
          <span className="gate-footer-sep">·</span>
          <span>SESSION 3F2A91</span>
        </div>
      </div>
    </div>
  );
}
