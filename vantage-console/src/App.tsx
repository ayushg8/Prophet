import './App.css'

type AgentStatus = 'tracking' | 'warning' | 'ready'
type AlertStatus = 'active' | 'review' | 'actioned'

type Agent = {
  name: string
  status: AgentStatus
  summary: string
  confidence: string
}

type Alert = {
  id: string
  title: string
  severity: 'critical' | 'elevated' | 'watch'
  status: AlertStatus
  location: string
  timestamp: string
  summary: string
}

const agents: Agent[] = [
  {
    name: 'Forecaster',
    status: 'warning',
    summary: 'Predicted dark event window opens in 23 minutes for tanker 9342847.',
    confidence: '0.82',
  },
  {
    name: 'Unmasker',
    status: 'ready',
    summary: 'AIS claim conflicts with sanctions-linked ownership and pier-side imagery.',
    confidence: '0.91',
  },
  {
    name: 'Synthesizer',
    status: 'ready',
    summary: 'Maritime anomaly, port probe, and state-media traffic cluster into one narrative.',
    confidence: '0.74',
  },
  {
    name: 'Translator',
    status: 'tracking',
    summary: 'Audience-specific brief prepared for watch floor, commander, and cabinet level.',
    confidence: '0.88',
  },
]

const alerts: Alert[] = [
  {
    id: 'A-17',
    title: 'Coordinated movement pattern detected near restricted maritime corridor',
    severity: 'critical',
    status: 'review',
    location: 'Strait of Hormuz',
    timestamp: '12:34 ZULU',
    summary: 'Three independent signals converged in the last 27 minutes.',
  },
  {
    id: 'B-04',
    title: 'Port network anomaly aligned with vessel loitering pattern',
    severity: 'elevated',
    status: 'active',
    location: 'Fujairah',
    timestamp: '12:19 ZULU',
    summary: 'Collection recommended before asset dispersal.',
  },
  {
    id: 'C-09',
    title: 'State-media language shift references freedom of navigation corridor',
    severity: 'watch',
    status: 'active',
    location: 'Tehran media desk',
    timestamp: '12:07 ZULU',
    summary: 'Narrative change amplifies maritime pressure indicators.',
  },
]

const timeline = [
  '11:52 ZULU  Tanker 9342847 reduces broadcast cadence while approaching chokepoint.',
  '12:08 ZULU  OpenSanctions match adds owner-risk context and prior flag-switch history.',
  '12:19 ZULU  Port telemetry shows credential-stuffing against logistics gateway.',
  '12:34 ZULU  Synthesizer pushes unified alert above watch threshold.',
]

const evidence = [
  {
    label: 'Signals',
    value: 'AIS gap probability up 37 percent against baseline route behavior.',
  },
  {
    label: 'Movement',
    value: 'Projected loiter point is 400m off declared track and outside normal traffic lane.',
  },
  {
    label: 'Assessment',
    value: 'Matches prior gray-zone staging behavior with 87 percent confidence.',
  },
]

const severityTone: Record<Alert['severity'], string> = {
  critical: 'tone-critical',
  elevated: 'tone-elevated',
  watch: 'tone-watch',
}

const statusTone: Record<AgentStatus, string> = {
  tracking: 'tone-tracking',
  warning: 'tone-warning',
  ready: 'tone-ready',
}

function App() {
  return (
    <main className="console-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">VANTAGE / Mission Command Console</p>
          <h1>Detect, explain, and approve the next move before the signal goes dark.</h1>
        </div>
        <div className="hero-metrics">
          <div>
            <span>Scenario</span>
            <strong>Operational Replay / Strait Watch</strong>
          </div>
          <div>
            <span>Audience</span>
            <strong>Cabinet Secretary</strong>
          </div>
          <div>
            <span>Review State</span>
            <strong>Human Approval Required</strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <aside className="panel queue-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Alert Queue</p>
              <h2>One focal story, three supporting signals</h2>
            </div>
            <span className="live-pill">Live Replay</span>
          </div>

          <div className="alert-list">
            {alerts.map((alert) => (
              <article key={alert.id} className={`alert-card ${severityTone[alert.severity]}`}>
                <div className="alert-meta">
                  <span>{alert.id}</span>
                  <span>{alert.timestamp}</span>
                </div>
                <h3>{alert.title}</h3>
                <p>{alert.summary}</p>
                <div className="alert-footer">
                  <span>{alert.location}</span>
                  <span className="status-chip">{alert.status}</span>
                </div>
              </article>
            ))}
          </div>
        </aside>

        <section className="panel map-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Operational Canvas</p>
              <h2>Map-centered, but demo-driven</h2>
            </div>
            <span className="map-status">Region Focus / Hormuz</span>
          </div>

          <div className="map-frame">
            <div className="grid-overlay" />
            <div className="route route-one" />
            <div className="route route-two" />
            <div className="marker marker-critical">
              <span />
              <p>Tanker 9342847</p>
            </div>
            <div className="marker marker-support">
              <span />
              <p>Port Probe</p>
            </div>
            <div className="map-caption">
              <strong>Why this surfaced</strong>
              <p>Three independent signals converged in the last 27 minutes.</p>
            </div>
          </div>

          <div className="timeline">
            {timeline.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        </section>
      </section>

      <section className="insight-grid">
        <section className="panel agent-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Agent Stack</p>
              <h2>Four agents, one assessment path</h2>
            </div>
          </div>

          <div className="agent-list">
            {agents.map((agent) => (
              <article key={agent.name} className="agent-card">
                <div className="agent-title">
                  <h3>{agent.name}</h3>
                  <span className={`status-dot ${statusTone[agent.status]}`}>{agent.status}</span>
                </div>
                <p>{agent.summary}</p>
                <strong>Confidence {agent.confidence}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="panel evidence-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Evidence Drill-Down</p>
              <h2>Show the receipts, then ask for the decision</h2>
            </div>
          </div>

          <div className="evidence-list">
            {evidence.map((item) => (
              <article key={item.label} className="evidence-card">
                <span>{item.label}</span>
                <p>{item.value}</p>
              </article>
            ))}
          </div>

          <div className="decision-card">
            <div>
              <p className="panel-kicker">Recommended Action</p>
              <h3>Escalate to regional watch and task additional collection.</h3>
              <p>This is the earliest decision point before asset dispersal.</p>
            </div>
            <div className="decision-actions">
              <button type="button" className="primary-action">
                Approve tasking
              </button>
              <button type="button" className="secondary-action">
                Hold for review
              </button>
            </div>
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
