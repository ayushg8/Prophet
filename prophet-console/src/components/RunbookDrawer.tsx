// RunbookDrawer: right-hand drawer with the judge-safe demo operator flow.
// It intentionally avoids exploit steps and raw payload material.

import { sanitize } from '../lib/sanitize';

interface RunbookDrawerProps {
  open: boolean;
  onClose: () => void;
}

interface RunbookSection {
  id: string;
  heading: string;
  steps: string[];
}

// Derived from presentation/demo_checklist.md. Keep this operator-facing and
// non-actionable: no payloads, no live targets, no raw scrape content.
const SECTIONS: RunbookSection[] = [
  {
    id: 'mission',
    heading: 'MISSION',
    steps: [
      'Prophet predicts the strike window, strike vector, and exploit class, then renders the defense artifact.',
      'Keep the demo sector-level and localhost-only. Do not name live targets or raw sources.',
      'Use DEMO REFRESH and LOAD FIXTURE as the reliable path; use RUN SCRAPER VM only after readiness checks pass.',
    ],
  },
  {
    id: 'services',
    heading: 'SERVICES',
    steps: [
      'Run the console: cd prophet-console && npm run dev.',
      'Run the local control server: cd prophet-console && npm run dev:control.',
      'Open http://127.0.0.1:5173 and enter the operator console.',
      'Optional VM check: world-side/scripts/check-scraper-vm.sh.',
    ],
  },
  {
    id: 'world',
    heading: 'FORECAST FLOW',
    steps: [
      'Click DEMO REFRESH to rebuild the forecast from sanitized fixture chatter.',
      'Read the two deliverables aloud: Attack Method / Strike Vector and Timeframe / Strike Window.',
      'Click the top strike-window bar to show trigger signals and historical analogies.',
      'If RUN SCRAPER VM is used, confirm the status line says the VM run completed before narrating it as live.',
    ],
  },
  {
    id: 'cyber',
    heading: 'CYBER FIXTURE FLOW',
    steps: [
      'Click LOAD FIXTURE in Defence Artifacts to load the cyber-side Direction C artifact.',
      'Confirm Exploit Status flips to BLOCKED and the post-patch validation excerpt appears.',
      'Show PATCH and SIGMA tabs as the generated zero-day defense output.',
      'Use INITIATE PROPHET LOOP for the full replay stream if time allows.',
    ],
  },
  {
    id: 'talktrack',
    heading: 'TALK TRACK',
    steps: [
      'Problem: reactive patching starts after weaponization and disclosure.',
      'Method: Forecaster predicts when and how; Exploit Engine predicts what; Console renders the defense.',
      'Safety: scraper VM collects, sanitizer validates, main box only sees sanitized JSONL.',
      'Close: predict the strike, generate the defense, ship before the campaign runs.',
    ],
  },
  {
    id: 'recovery',
    heading: 'RECOVERY',
    steps: [
      'If the VM is unreachable, use DEMO REFRESH and say live collection is disabled for stage safety.',
      'If the control server is offline, start npm run dev:control and retry the fixture buttons.',
      'If the replay stalls, load the cyber fixture and continue from the defense panels.',
      'If two failures happen, finish the pitch using the script and offer a booth rerun.',
    ],
  },
  {
    id: 'opsec',
    heading: 'OPSEC',
    steps: [
      'No raw scraper output on screen.',
      'No secrets, SSH keys, .env.local files, session files, or passwords on screen.',
      'No exploit payload syntax or live target indicators in the narration.',
      'Keep all cyber output framed as localhost sandbox validation and defense generation.',
    ],
  },
];

export function RunbookDrawer({ open, onClose }: RunbookDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="runbook-backdrop"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={`runbook-drawer${open ? ' runbook-drawer--open' : ''}`}
        aria-label="Lab runbook"
        aria-hidden={!open}
      >
        <div className="runbook-header">
          <div className="runbook-eyebrow">PROPHET DEMO RUNBOOK</div>
          <button
            className="runbook-close"
            onClick={onClose}
            aria-label="Close runbook"
          >
            [ CLOSE ]
          </button>
        </div>

        <div className="runbook-subheader">
          <span className="runbook-cve">PS4 DIGITAL DEFENSE</span>
          <span className="runbook-sep">·</span>
          <span>Forecaster + Exploit Engine + Console</span>
          <span className="runbook-sep">·</span>
          <span>fixture-safe mode</span>
        </div>

        <div className="runbook-body">
          {SECTIONS.map((section, sIdx) => (
            <div key={section.id} className="runbook-section">
              <div className="runbook-section-heading">
                <span className="runbook-section-num">{String(sIdx + 1).padStart(2, '0')}</span>
                <span>{section.heading}</span>
              </div>
              <ol className="runbook-steps">
                {section.steps.map((step, i) => (
                  <li key={i} className="runbook-step">
                    <span className="runbook-step-num">{i + 1}.</span>
                    <span className="runbook-step-text">
                      {sanitize(step)}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>

        <div className="runbook-footer">
          <span>LAB-001</span>
          <span className="runbook-footer-sep">·</span>
          <span>PROPHET</span>
          <span className="runbook-footer-sep">·</span>
          <span>DEMO SAFE</span>
          <span className="runbook-footer-sep">·</span>
          <span>CLASSIFICATION FOUO</span>
        </div>
      </aside>
    </>
  );
}
