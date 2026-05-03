import { useEffect, useState } from 'react';

interface StatusPillProps {
  label: string;
  dotColor: string;
}

// Status pill with ◢ prefix and ◣ suffix chevrons — matches landing sidebar
function StatusPill({ label, dotColor }: StatusPillProps) {
  return (
    <div className="status-pill">
      <span className="status-chevron" aria-hidden>◢</span>
      <span className="status-dot" style={{ background: dotColor }} aria-hidden />
      <span className="status-label">{label}</span>
      <span className="status-chevron--right" aria-hidden>◣</span>
    </div>
  );
}

interface HeaderProps {
  isRunning: boolean;
  onRunClick: () => void;
  onRunbookClick: () => void;
  runReady: boolean;
}

export function Header({ isRunning, onRunClick, onRunbookClick, runReady }: HeaderProps) {
  const [clock, setClock] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const zulu = clock.toISOString().slice(11, 19).concat('Z');

  return (
    <div className="header-wrapper">
      {/* Classification banner */}
      <div className="classification-banner" role="banner">
        <span className="classification-label">UNCLASSIFIED // FOUO</span>
        <span className="classification-right">{zulu}</span>
      </div>

      {/* Main header */}
      <header className="header">
        <div className="header-left">
          <span className="header-title">PROPHET // OPERATOR CONSOLE</span>
        </div>

        {/* Centered console label */}
        <div className="header-center" aria-hidden>
          <span className="header-console-label">PROPHET</span>
        </div>

        <div className="header-right">
          <StatusPill dotColor="var(--success)" label="KEV FEED · LIVE" />
          <StatusPill dotColor="var(--success)" label="NVD STREAMING" />
          <StatusPill dotColor="var(--success)" label="CODEX TERMINAL · READY" />
          <StatusPill dotColor="var(--info)" label="FIXTURE MODE · ARMED" />
          <StatusPill dotColor="var(--success)" label="SANDBOX · ISOLATED" />

          <button
            className="runbook-btn"
            onClick={onRunbookClick}
            aria-label="Open Lab Runbook"
          >
            <span className="run-btn-bracket">[</span>
            RUNBOOK
            <span className="run-btn-bracket">]</span>
          </button>

          {!isRunning && (
            <button
              className="run-btn"
              onClick={onRunClick}
              disabled={!runReady}
              aria-label="Initiate Prophet Loop"
              title={runReady ? undefined : 'Waiting for pre-flight checks…'}
            >
              <span className="run-btn-bracket">[</span>
              INITIATE PROPHET LOOP
              <span className="run-btn-bracket">]</span>
            </button>
          )}
          {isRunning && (
            <div className="running-indicator" aria-live="polite" aria-label="Prophet loop running">
              <span className="running-dot" aria-hidden />
              <span>[ RUNNING... ]</span>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}
