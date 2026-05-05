import { useCallback, useRef, useState } from 'react';
import { Header } from './components/Header';
import { TriageQueue } from './components/TriageQueue';
import { PhaseProgress } from './components/PhaseProgress';
import { AgentStream } from './components/AgentStream';
import { ExploitPanel } from './components/ExploitPanel';
import { DefencePanel } from './components/DefencePanel';
import { ApprovalGate } from './components/ApprovalGate';
import { Landing } from './components/Landing';
import { PerlinHero } from './components/PerlinHero';
import { LabTopology } from './components/LabTopology';
import { PreflightChecklist } from './components/PreflightChecklist';
import { LiveFeedTicker } from './components/LiveFeedTicker';
import { RunbookDrawer } from './components/RunbookDrawer';
import { ForecastPanel } from './components/ForecastPanel';
import {
  EvidencePanel,
  type EvidenceArtifactSource,
  type EvidenceAssetContext,
  type EvidenceBundle,
  type EvidenceStatus,
} from './components/EvidencePanel';
import {
  IntegrationPanel,
  type IntegrationManifest,
  type IntegrationStatus,
} from './components/IntegrationPanel';
import { PolicyStatusPanel } from './components/PolicyStatusPanel';
import { ReadinessPanel } from './components/ReadinessPanel';
import { cves } from './data/cves';
import { mockEvents } from './data/mockEvents';
import type {
  AgentEvent,
  PatchDiffEvent,
  SigmaRuleEvent,
  ExploitStatusEvent,
  ForecastSummaryEvent,
} from './data/mockEvents';
import { getForecastForCandidate } from './data/worldSide';
import type { StrikeForecast } from './data/worldSide';
import { startReplay } from './data/replayController';
import type { ReplayHandle } from './data/replayController';
import { sanitize } from './lib/sanitize';
import './index.css';

const VM_SCRAPER_ENABLED = import.meta.env.VITE_PROPHET_ENABLE_VM_SCRAPER === '1';
const CONTROL_ORIGIN =
  import.meta.env.VITE_PROPHET_CONTROL_ORIGIN || 'http://127.0.0.1:8787';
const CONTROL_HEADERS = {
  'x-prophet-control': 'local-console',
  'x-prophet-operator': 'local-console',
};

type Phase = 'INTEL' | 'PLAN' | 'EXECUTE' | 'DEFEND';
type ExploitStatus = 'idle' | 'running' | 'vulnerable' | 'blocked';
type ScraperRunState = 'idle' | 'running' | 'ok' | 'error' | 'blocked';

interface ActionFailurePayload {
  status?: string;
  message?: string;
}

interface ScraperRunResponse {
  ok: boolean;
  status: string;
  message?: string;
  forecast?: StrikeForecast;
  stdoutTail?: string;
  stderrTail?: string;
}

interface CyberDemoArtifactResponse {
  ok: boolean;
  status: string;
  message?: string;
  artifact?: {
    predicted_exploit?: {
      exploit_class_label?: string;
      non_actionable_rationale?: string;
    };
    defense?: {
      patch?: {
        diff?: string;
      };
      sigma_rule?: {
        yaml?: string;
      };
    };
    validation?: {
      pre_patch_status?: string;
      post_patch_status?: string;
      post_patch_excerpt?: string;
    };
  };
}

interface CyberPredictionPortfolioResponse {
  ok: boolean;
  status: string;
  message?: string;
  portfolio?: {
    zero_day_predictions?: Array<{
      exploit_class_label?: string;
    }>;
    one_day_predictions?: Array<{
      exploit_class_label?: string;
      known_cve_ids?: string[];
    }>;
  };
}

interface EvidenceDemoBundleResponse {
  ok: boolean;
  status: string;
  message?: string;
  artifactSource?: string;
  artifactSourceLabel?: string;
  artifactMode?: string;
  bundle?: EvidenceBundle;
  markdown?: string;
  paths?: {
    defenseArtifact?: string;
  };
}

interface IntegrationDemoExportResponse {
  ok: boolean;
  status: string;
  message?: string;
  manifest?: IntegrationManifest;
  paths?: {
    manifest?: string;
    outDir?: string;
  };
}

function forecastForCveId(cveId: string): StrikeForecast | null {
  const cve = cves.find((item) => item.cveId === cveId);
  const candidateId = cve?.worldCandidateId ?? null;
  return candidateId ? getForecastForCandidate(candidateId) ?? null : null;
}

function isPolicyBlocked(payload: ActionFailurePayload): boolean {
  return payload.status === 'policy_blocked';
}

function actionFailureMessage(payload: ActionFailurePayload, fallback: string): string {
  const message = sanitize(payload.message || fallback);
  return isPolicyBlocked(payload) ? `Policy blocked: ${message}` : message;
}

export default function App() {
  const [view, setView] = useState<'landing' | 'console'>('landing');
  const [isRunning, setIsRunning] = useState(false);
  const [selectedCveId, setSelectedCveId] = useState('CVE-2021-44228');
  const [currentPhase, setCurrentPhase] = useState<Phase | null>(null);
  const [completedPhases, setCompletedPhases] = useState<Phase[]>([]);
  const [streamEvents, setStreamEvents] = useState<AgentEvent[]>([]);
  const [gateOpen, setGateOpen] = useState(false);
  const [exploitStatus, setExploitStatus] = useState<ExploitStatus>('idle');
  const [exploitExcerpt, setExploitExcerpt] = useState<string | undefined>(undefined);
  const [patchDiff, setPatchDiff] = useState<string | null>(null);
  const [sigmaRule, setSigmaRule] = useState<string | null>(null);
  const [runReady, setRunReady] = useState(false);
  const [runbookOpen, setRunbookOpen] = useState(false);
  const [scraperRunState, setScraperRunState] = useState<ScraperRunState>('idle');
  const [scraperStatusMessage, setScraperStatusMessage] = useState<string | undefined>(
    VM_SCRAPER_ENABLED
      ? 'Start npm run dev:control to enable approved VM runs'
      : 'Live VM scraper disabled; use sanitized demo refresh',
  );
  const [isLoadingCyberFixture, setIsLoadingCyberFixture] = useState(false);
  const [evidenceBundle, setEvidenceBundle] = useState<EvidenceBundle | null>(null);
  const [evidenceMarkdown, setEvidenceMarkdown] = useState('');
  const [evidenceStatus, setEvidenceStatus] = useState<EvidenceStatus>('idle');
  const [evidenceError, setEvidenceError] = useState<string | undefined>(undefined);
  const [evidenceArtifactSource, setEvidenceArtifactSource] =
    useState<EvidenceArtifactSource | null>(null);
  const [integrationManifest, setIntegrationManifest] = useState<IntegrationManifest | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus>('idle');
  const [integrationError, setIntegrationError] = useState<string | undefined>(undefined);
  const [integrationOutputPath, setIntegrationOutputPath] = useState<string | undefined>(undefined);
  const [assetContext, setAssetContext] = useState<EvidenceAssetContext | null>(null);
  // runCycle increments each time the user resets, so PreflightChecklist re-runs
  const [runCycle, setRunCycle] = useState(0);
  const [activeForecast, setActiveForecast] = useState<StrikeForecast | null>(() =>
    forecastForCveId('CVE-2021-44228'),
  );

  const replayRef = useRef<ReplayHandle | null>(null);
  const selectedCve = cves.find((item) => item.cveId === selectedCveId) ?? cves[0];

  const handleEvent = useCallback((event: AgentEvent) => {
    if (event.kind === 'phase') {
      setCurrentPhase(event.phase);
      setStreamEvents((prev) => [...prev, event]);
    } else if (event.kind === 'phase_complete') {
      setCompletedPhases((prev) =>
        prev.includes(event.phase) ? prev : [...prev, event.phase]
      );
      setCurrentPhase(null);
      setStreamEvents((prev) => [...prev, event]);
    } else if (event.kind === 'human_gate') {
      setGateOpen(true);
      setStreamEvents((prev) => [...prev, event]);
    } else if (event.kind === 'exploit_status') {
      const e = event as ExploitStatusEvent;
      setExploitStatus(e.status);
      if (e.responseExcerpt) setExploitExcerpt(e.responseExcerpt);
      setStreamEvents((prev) => [...prev, event]);
    } else if (event.kind === 'patch_diff') {
      setPatchDiff((event as PatchDiffEvent).content);
    } else if (event.kind === 'sigma_rule') {
      setSigmaRule((event as SigmaRuleEvent).content);
    } else if (event.kind === 'forecast_summary') {
      setActiveForecast((event as ForecastSummaryEvent).forecast);
      setStreamEvents((prev) => [...prev, event]);
    } else {
      // historical_analogy, source_ref, etc. — render inline in the stream
      setStreamEvents((prev) => [...prev, event]);
    }
  }, []);

  const handleRun = () => {
    setIsRunning(true);
    setStreamEvents([]);
    setCurrentPhase(null);
    setCompletedPhases([]);
    setGateOpen(false);
    setExploitStatus('idle');
    setExploitExcerpt(undefined);
    setPatchDiff(null);
    setSigmaRule(null);
    setEvidenceBundle(null);
    setEvidenceMarkdown('');
    setEvidenceStatus('idle');
    setEvidenceError(undefined);
    setEvidenceArtifactSource(null);
    setIntegrationManifest(null);
    setIntegrationStatus('idle');
    setIntegrationError(undefined);
    setIntegrationOutputPath(undefined);

    const handle = startReplay(
      mockEvents,
      handleEvent,
      () => {
        // Gate opened via handleEvent processing the human_gate event
      },
      () => {
        setIsRunning(false);
        replayRef.current = null;
      },
    );
    replayRef.current = handle;
  };

  const handleScraperRun = useCallback(async () => {
    setScraperRunState('running');
    setScraperStatusMessage('Contacting local control server and scraper VM...');

    try {
      const response = await fetch(`${CONTROL_ORIGIN}/api/scraper/run`, {
        method: 'POST',
        headers: CONTROL_HEADERS,
      });
      const payload = (await response.json()) as ScraperRunResponse;

      if (!response.ok || !payload.ok) {
        setScraperRunState(isPolicyBlocked(payload) ? 'blocked' : 'error');
        setScraperStatusMessage(
          actionFailureMessage(
            payload,
            'Scraper VM workflow failed. Check the control server terminal.',
          ),
        );
        return;
      }

      if (payload.forecast) {
        setActiveForecast(payload.forecast);
      }

      setScraperRunState('ok');
      setScraperStatusMessage(payload.message || 'Scraper VM forecast refreshed.');
    } catch {
      setScraperRunState('error');
      setScraperStatusMessage(
        'Local control server offline. Run npm run dev:control in prophet-console.',
      );
    }
  }, []);

  const handleDemoRefresh = useCallback(async () => {
    setScraperRunState('running');
    setScraperStatusMessage('Refreshing forecast from sanitized demo chatter...');

    try {
      const response = await fetch(`${CONTROL_ORIGIN}/api/scraper/demo-refresh`, {
        method: 'POST',
        headers: CONTROL_HEADERS,
      });
      const payload = (await response.json()) as ScraperRunResponse;

      if (!response.ok || !payload.ok) {
        setScraperRunState(isPolicyBlocked(payload) ? 'blocked' : 'error');
        setScraperStatusMessage(
          actionFailureMessage(
            payload,
            'Demo refresh failed. Check the control server terminal.',
          ),
        );
        return;
      }

      if (payload.forecast) {
        setActiveForecast(payload.forecast);
      }

      setScraperRunState('ok');
      setScraperStatusMessage(payload.message || 'Demo forecast refreshed.');
    } catch {
      setScraperRunState('error');
      setScraperStatusMessage(
        'Local control server offline. Run npm run dev:control in prophet-console.',
      );
    }
  }, []);

  const handleLoadCyberFixture = useCallback(async () => {
    setIsLoadingCyberFixture(true);

    try {
      const response = await fetch(`${CONTROL_ORIGIN}/api/cyber/demo-artifact`, {
        method: 'POST',
        headers: CONTROL_HEADERS,
      });
      const payload = (await response.json()) as CyberDemoArtifactResponse;

      if (!response.ok || !payload.ok || !payload.artifact) {
        setExploitStatus('idle');
        setExploitExcerpt(
          actionFailureMessage(
            payload,
            'Cyber fixture unavailable. Start npm run dev:control.',
          ),
        );
        return;
      }

      const artifact = payload.artifact;
      const patch = artifact.defense?.patch?.diff ?? null;
      const sigma = artifact.defense?.sigma_rule?.yaml ?? null;
      const postStatus = artifact.validation?.post_patch_status;
      const excerpt = artifact.validation?.post_patch_excerpt;
      const rationale = artifact.predicted_exploit?.non_actionable_rationale;

      setPatchDiff(patch);
      setSigmaRule(sigma);
      setEvidenceBundle(null);
      setEvidenceMarkdown('');
      setEvidenceStatus('idle');
      setEvidenceError(undefined);
      setEvidenceArtifactSource(null);
      setIntegrationManifest(null);
      setIntegrationStatus('idle');
      setIntegrationError(undefined);
      setIntegrationOutputPath(undefined);
      setExploitStatus(postStatus === 'blocked' || postStatus === 'not_vulnerable'
        ? 'blocked'
        : postStatus === 'vulnerable'
          ? 'vulnerable'
          : 'idle');
      setExploitExcerpt(sanitize(excerpt || payload.message || 'Cyber fixture loaded.'));
      if (rationale) {
        setStreamEvents((prev) => [
          ...prev,
          {
            kind: 'text',
            content: sanitize(`Cyber fixture loaded: ${rationale}`),
          },
        ]);
      }

      try {
        const portfolioResponse = await fetch(`${CONTROL_ORIGIN}/api/cyber/prediction-portfolio`, {
          method: 'POST',
          headers: CONTROL_HEADERS,
        });
        const portfolioPayload = (await portfolioResponse.json()) as CyberPredictionPortfolioResponse;
        const portfolio = portfolioPayload.portfolio;
        const zeroDays = portfolio?.zero_day_predictions ?? [];
        const oneDays = portfolio?.one_day_predictions ?? [];
        const topZeroDay = zeroDays[0]?.exploit_class_label;
        const topOneDay = oneDays[0]?.exploit_class_label;

        if (portfolioResponse.ok && portfolioPayload.ok && topZeroDay && topOneDay) {
          setStreamEvents((prev) => [
            ...prev,
            {
              kind: 'text',
              content: sanitize(
                `Prediction portfolio loaded: ${zeroDays.length} hypothesized zero-day classes and ${oneDays.length} one-day replay classes. Top zero-day class: ${topZeroDay}. Top one-day class: ${topOneDay}.`,
              ),
            },
          ]);
        }
      } catch {
        // Portfolio visibility is a demo enhancement; the Direction C artifact still drives defence rendering.
      }
    } catch {
      setExploitStatus('idle');
      setExploitExcerpt(
        sanitize('Local control server offline. Run npm run dev:control in prophet-console.'),
      );
    } finally {
      setIsLoadingCyberFixture(false);
    }
  }, []);

  const handleGenerateEvidence = useCallback(async () => {
    const artifactReady = Boolean(patchDiff && sigmaRule) || exploitStatus === 'blocked';
    if (!artifactReady) {
      setEvidenceStatus('error');
      setEvidenceError('Load defense fixture or complete Prophet loop first.');
      setEvidenceArtifactSource(null);
      return;
    }

    setEvidenceStatus('generating');
    setEvidenceError(undefined);
    setEvidenceArtifactSource(null);

    try {
      const response = await fetch(`${CONTROL_ORIGIN}/api/evidence/demo-bundle`, {
        method: 'POST',
        headers: CONTROL_HEADERS,
      });
      const payload = (await response.json()) as EvidenceDemoBundleResponse;

      if (!response.ok || !payload.ok || !payload.bundle) {
        setEvidenceStatus(isPolicyBlocked(payload) ? 'blocked' : 'error');
        setEvidenceError(
          actionFailureMessage(payload, 'Evidence bundle generation failed.'),
        );
        return;
      }

      setEvidenceBundle(payload.bundle);
      setEvidenceMarkdown(payload.markdown || '');
      setEvidenceArtifactSource({
        key: payload.artifactSource,
        label: payload.artifactSourceLabel,
        mode: payload.artifactMode,
        path: payload.paths?.defenseArtifact,
      });
      setAssetContext(payload.bundle.asset_context ?? null);
      setEvidenceStatus('ok');
      setIntegrationManifest(null);
      setIntegrationStatus('idle');
      setIntegrationError(undefined);
      setIntegrationOutputPath(undefined);
    } catch {
      setEvidenceStatus('error');
      setEvidenceError(
        'Local control server offline. Run npm run dev:control in prophet-console.',
      );
    }
  }, [exploitStatus, patchDiff, sigmaRule]);

  const handleExportIntegrations = useCallback(async () => {
    if (evidenceStatus !== 'ok' || !evidenceBundle) {
      setIntegrationStatus('error');
      setIntegrationError('Generate a validated evidence bundle before exporting handoff files.');
      return;
    }

    setIntegrationStatus('generating');
    setIntegrationError(undefined);

    try {
      const response = await fetch(`${CONTROL_ORIGIN}/api/integrations/demo-export`, {
        method: 'POST',
        headers: CONTROL_HEADERS,
      });
      const payload = (await response.json()) as IntegrationDemoExportResponse;

      if (!response.ok || !payload.ok || !payload.manifest) {
        setIntegrationStatus(isPolicyBlocked(payload) ? 'blocked' : 'error');
        setIntegrationError(
          actionFailureMessage(payload, 'Integration handoff export failed.'),
        );
        return;
      }

      setIntegrationManifest(payload.manifest);
      setIntegrationOutputPath(payload.paths?.manifest);
      setIntegrationStatus('ok');
    } catch {
      setIntegrationStatus('error');
      setIntegrationError(
        'Local control server offline. Run npm run dev:control in prophet-console.',
      );
    }
  }, [evidenceBundle, evidenceStatus]);

  const handleAuthorize = () => {
    setGateOpen(false);
    replayRef.current?.authorize();
  };

  const handleHold = () => {
    setGateOpen(false);
    replayRef.current?.reset();
    setIsRunning(false);
    setRunCycle((c) => c + 1);
    void fetch(`${CONTROL_ORIGIN}/api/evidence/deny`, {
      method: 'POST',
      headers: CONTROL_HEADERS,
    }).catch(() => {
      // The local audit server may be offline during static UI review.
    });
  };

  const handleSelectCve = (cveId: string) => {
    setSelectedCveId(cveId);
    setActiveForecast(forecastForCveId(cveId));
  };

  if (view === 'landing') {
    return <Landing onEnter={() => setView('console')} />;
  }

  return (
    <>
      {/*
        Global atmospheric layers — z-index 0–3.
        pointer-events: none on all, so console interactions pass through.
        Mesh at opacity 0.12, segments 64 for console performance.
      */}
      <PerlinHero className="console-mesh" segments={64} />
      <div className="console-dither" aria-hidden />
      <div className="console-vignette" aria-hidden />
      <div className="console-scanlines" aria-hidden />

      {/* Console shell — z-index 5 */}
      <div className="app">
        <Header
          isRunning={isRunning}
          onRunClick={handleRun}
          onRunbookClick={() => setRunbookOpen(true)}
          runReady={runReady}
        />

        {/* Mission Context brief — forecast, timing, candidate, and source rails */}
        <div className="mission-context" aria-label="World Side forecast and strike windows">
          <ForecastPanel
            forecast={activeForecast}
            candidate={selectedCve}
            assetContext={assetContext}
            onScraperRun={VM_SCRAPER_ENABLED ? handleScraperRun : undefined}
            onDemoRefresh={handleDemoRefresh}
            scraperRunState={scraperRunState}
            scraperStatusMessage={scraperStatusMessage}
          />
        </div>

        <div className="main-layout">
          {/* Left column: Preflight + Triage */}
          <div className="left-column">
            <PreflightChecklist
              isRunning={runCycle}
              onReady={setRunReady}
            />
            <TriageQueue
              cves={cves}
              selectedId={selectedCveId}
              onSelect={handleSelectCve}
            />
          </div>

          <main className="center-column">
            <PhaseProgress
              currentPhase={currentPhase}
              completedPhases={completedPhases}
            />
            <AgentStream events={streamEvents} gateOpen={gateOpen} />
          </main>

          <aside className="right-column">
            <LabTopology
              currentPhase={currentPhase}
              exploitStatus={exploitStatus}
            />
            <ExploitPanel status={exploitStatus} responseExcerpt={exploitExcerpt} />
            <DefencePanel
              patchDiff={patchDiff}
              sigmaRule={sigmaRule}
              onLoadFixture={handleLoadCyberFixture}
              isLoadingFixture={isLoadingCyberFixture}
            />
            <EvidencePanel
              bundle={evidenceBundle}
              markdown={evidenceMarkdown}
              status={evidenceStatus}
              error={evidenceError}
              artifactSource={evidenceArtifactSource}
              onGenerate={handleGenerateEvidence}
            />
            <IntegrationPanel
              manifest={integrationManifest}
              status={integrationStatus}
              error={integrationError}
              outputPath={integrationOutputPath}
              onExport={handleExportIntegrations}
            />
            <PolicyStatusPanel />
            <ReadinessPanel />
          </aside>
        </div>

        {/* Live feed ticker — bottom bar */}
        <LiveFeedTicker />

        {gateOpen && (
          <ApprovalGate onAuthorize={handleAuthorize} onHold={handleHold} />
        )}
      </div>

      {/* Runbook drawer — outside .app so it overlays everything */}
      <RunbookDrawer open={runbookOpen} onClose={() => setRunbookOpen(false)} />
    </>
  );
}
