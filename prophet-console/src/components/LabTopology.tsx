// 'use client' not needed — no Next.js here, Vite SPA
// LabTopology: fixed SVG node graph showing the actual lab topology.
// Nodes animate based on current phase prop.

import { useEffect, useRef } from 'react';

type Phase = 'INTEL' | 'PLAN' | 'EXECUTE' | 'DEFEND' | null;
type ExploitStatus = 'idle' | 'running' | 'vulnerable' | 'blocked';

interface LabTopologyProps {
  currentPhase: Phase;
  exploitStatus: ExploitStatus;
}

// Edge animation state per edge key
type EdgeState = 'idle' | 'active' | 'compromised' | 'patched';

function getEdgeStates(
  phase: Phase,
  exploitStatus: ExploitStatus
): Record<string, EdgeState> {
  if (!phase) return {};

  if (phase === 'INTEL') {
    return {
      'api-engine': 'active',
      'operator-api': 'active',
    };
  }
  if (phase === 'PLAN') {
    return {
      'operator-api': 'active',
      'api-engine': 'active',
      'engine-target': 'active',
    };
  }
  if (phase === 'EXECUTE') {
    if (exploitStatus === 'vulnerable') {
      return {
        'api-engine': 'active',
        'engine-target': 'compromised',
        'engine-sandbox': 'compromised',
      };
    }
    return {
      'api-engine': 'active',
      'engine-target': 'active',
      'engine-sandbox': 'active',
    };
  }
  if (phase === 'DEFEND') {
    if (exploitStatus === 'blocked') {
      return {
        'operator-api': 'patched',
        'api-engine': 'patched',
        'engine-target': 'patched',
        'engine-sandbox': 'patched',
      };
    }
    return {
      'api-engine': 'active',
      'engine-target': 'active',
    };
  }
  return {};
}

function edgeColor(state: EdgeState): string {
  switch (state) {
    case 'active':      return '#f59e0b';
    case 'compromised': return '#f85149';
    case 'patched':     return '#3fb950';
    case 'idle':
    default:            return '#21262d';
  }
}

function edgeOpacity(state: EdgeState): number {
  if (state === 'idle') return 0.35;
  return 0.9;
}

// Dashed-marching animation offset ref per edge
function useMarchingDash(active: boolean, canvasRef: React.RefObject<SVGPathElement | null>) {
  const rafRef = useRef<number>(0);
  const offsetRef = useRef(0);

  useEffect(() => {
    if (!active) {
      if (canvasRef.current) {
        canvasRef.current.style.strokeDashoffset = '0';
      }
      cancelAnimationFrame(rafRef.current);
      return;
    }

    const animate = () => {
      offsetRef.current -= 1.2;
      if (canvasRef.current) {
        canvasRef.current.style.strokeDashoffset = String(offsetRef.current);
      }
      rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [active, canvasRef]);
}

interface EdgeProps {
  id: string;
  d: string;
  state: EdgeState;
  label?: string;
  labelX?: number;
  labelY?: number;
}

function Edge({ id, d, state, label, labelX, labelY }: EdgeProps) {
  const pathRef = useRef<SVGPathElement>(null);
  useMarchingDash(state === 'active', pathRef);

  const color = edgeColor(state);
  const opacity = edgeOpacity(state);
  const isDashed = state !== 'idle';

  return (
    <g opacity={opacity}>
      <path
        id={id}
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={isDashed ? 1.5 : 1}
        strokeDasharray={isDashed ? '6 4' : 'none'}
        ref={pathRef}
        style={{ transition: 'stroke 400ms ease-out, opacity 400ms ease-out' }}
      />
      {label && labelX !== undefined && labelY !== undefined && (
        <text
          x={labelX}
          y={labelY}
          fill={color}
          fontSize="7"
          fontFamily="'JetBrains Mono', monospace"
          letterSpacing="0.12em"
          textAnchor="middle"
          style={{ opacity: state !== 'idle' ? 0.9 : 0.35 }}
        >
          {label}
        </text>
      )}
    </g>
  );
}

interface NodeProps {
  x: number;
  y: number;
  label: string;
  sublabel?: string;
  color: string;
  active: boolean;
  dim?: boolean;
  size?: number;
}

function Node({ x, y, label, sublabel, color, active, dim, size = 28 }: NodeProps) {
  const r = size / 2;
  const opacity = dim ? 0.45 : 1;

  return (
    <g opacity={opacity}>
      {/* Outer glow ring when active */}
      {active && (
        <circle
          cx={x}
          cy={y}
          r={r + 5}
          fill="none"
          stroke={color}
          strokeWidth={1}
          opacity={0.3}
          style={{ animation: 'topology-pulse 1.4s ease-in-out infinite' }}
        />
      )}
      {/* Node body */}
      <rect
        x={x - r}
        y={y - r}
        width={size}
        height={size}
        rx={3}
        fill="rgba(15, 20, 25, 0.92)"
        stroke={color}
        strokeWidth={active ? 1.5 : 1}
        style={{ transition: 'stroke 400ms ease-out' }}
      />
      {/* Label above */}
      <text
        x={x}
        y={y - r - 5}
        fill={color}
        fontSize="7.5"
        fontFamily="'JetBrains Mono', monospace"
        letterSpacing="0.08em"
        textAnchor="middle"
        fontWeight="500"
        style={{ transition: 'fill 400ms ease-out' }}
      >
        {label}
      </text>
      {/* Sub-label below */}
      {sublabel && (
        <text
          x={x}
          y={y + r + 10}
          fill="rgba(125, 133, 144, 0.8)"
          fontSize="6.5"
          fontFamily="'JetBrains Mono', monospace"
          letterSpacing="0.06em"
          textAnchor="middle"
        >
          {sublabel}
        </text>
      )}
    </g>
  );
}

// Sub-node: smaller square node
interface SubNodeProps {
  x: number;
  y: number;
  label: string;
  color: string;
  active: boolean;
}

function SubNode({ x, y, label, color, active }: SubNodeProps) {
  return (
    <g>
      <rect
        x={x - 9}
        y={y - 6}
        width={18}
        height={12}
        rx={2}
        fill="rgba(10, 13, 18, 0.9)"
        stroke={active ? color : '#21262d'}
        strokeWidth={active ? 1 : 0.75}
        style={{ transition: 'stroke 400ms ease-out' }}
      />
      <text
        x={x}
        y={y + 3.5}
        fill={active ? color : '#484f58'}
        fontSize="5.5"
        fontFamily="'JetBrains Mono', monospace"
        letterSpacing="0.08em"
        textAnchor="middle"
        style={{ transition: 'fill 400ms ease-out' }}
      >
        {label}
      </text>
    </g>
  );
}

export function LabTopology({ currentPhase, exploitStatus }: LabTopologyProps) {
  const edgeStates = getEdgeStates(currentPhase, exploitStatus);

  const getEdge = (id: string): EdgeState => edgeStates[id] ?? 'idle';

  // Node positions — 280x260 SVG canvas
  const OPERATOR  = { x: 44,  y: 38  };
  const API       = { x: 140, y: 38  };
  const ENGINE    = { x: 140, y: 130 };
  const TARGET    = { x: 236, y: 200 };
  // Sub-nodes under TARGET
  const VULN_APP  = { x: 196, y: 238 };
  const PRIV_LOW  = { x: 240, y: 238 };

  const isPhaseActive = (p: string) => currentPhase === p;

  return (
    <div className="lab-topology" aria-label="Lab topology">
      <div className="panel-header">
        <span className="panel-header-title">
          <span className="panel-header-chevron" aria-hidden>◢</span>
          LAB TOPOLOGY
          <span className="panel-header-chevron--right" aria-hidden>◣</span>
        </span>
        <span className="panel-header-badge">CVE-2021-44228</span>
      </div>

      <div className="topology-svg-wrapper">
        <svg
          viewBox="0 0 280 260"
          width="280"
          height="260"
          aria-hidden="true"
          style={{ overflow: 'visible' }}
        >
          <defs>
            <style>{`
              @keyframes topology-pulse {
                0%, 100% { opacity: 0.35; transform-origin: center; transform: scale(1); }
                50% { opacity: 0.7; transform-origin: center; transform: scale(1.08); }
              }
            `}</style>
          </defs>

          {/* ── Edges ────────────────────────────────────────────────── */}

          {/* Operator → Codex loop */}
          <Edge
            id="operator-api"
            d={`M ${OPERATOR.x + 14} ${OPERATOR.y} L ${API.x - 14} ${API.y}`}
            state={getEdge('operator-api')}
            label="ORCHESTRATE"
            labelX={(OPERATOR.x + API.x) / 2}
            labelY={OPERATOR.y - 8}
          />

          {/* Codex loop → fixture runner */}
          <Edge
            id="api-engine"
            d={`M ${API.x} ${API.y + 14} L ${ENGINE.x} ${ENGINE.y - 14}`}
            state={getEdge('api-engine')}
            label="TASK"
            labelX={API.x + 18}
            labelY={(API.y + ENGINE.y) / 2}
          />

          {/* Fixture runner → Target (curved) */}
          <Edge
            id="engine-target"
            d={`M ${ENGINE.x + 14} ${ENGINE.y + 8} C ${ENGINE.x + 60} ${ENGINE.y + 40} ${TARGET.x - 30} ${TARGET.y - 40} ${TARGET.x - 14} ${TARGET.y}`}
            state={getEdge('engine-target')}
            label="VALIDATE"
            labelX={ENGINE.x + 62}
            labelY={ENGINE.y + 50}
          />

          {/* Fixture runner → Target via sandbox control path */}
          <Edge
            id="engine-sandbox"
            d={`M ${ENGINE.x + 10} ${ENGINE.y + 12} C ${ENGINE.x + 80} ${ENGINE.y + 70} ${TARGET.x - 20} ${TARGET.y - 20} ${TARGET.x} ${TARGET.y + 14}`}
            state={getEdge('engine-sandbox')}
            label="SANDBOX"
            labelX={ENGINE.x + 88}
            labelY={ENGINE.y + 85}
          />

          {/* Target → sub-nodes */}
          <line
            x1={TARGET.x - 8}
            y1={TARGET.y + 14}
            x2={VULN_APP.x}
            y2={VULN_APP.y - 6}
            stroke="#21262d"
            strokeWidth={0.75}
            opacity={0.5}
          />
          <line
            x1={TARGET.x + 4}
            y1={TARGET.y + 14}
            x2={PRIV_LOW.x}
            y2={PRIV_LOW.y - 6}
            stroke="#21262d"
            strokeWidth={0.75}
            opacity={0.5}
          />

          {/* ── Nodes ────────────────────────────────────────────────── */}

          {/* Operator */}
          <Node
            x={OPERATOR.x}
            y={OPERATOR.y}
            label="OPERATOR"
            sublabel="you"
            color="#7d8590"
            active={false}
            dim={true}
            size={26}
          />

          {/* Codex loop */}
          <Node
            x={API.x}
            y={API.y}
            label="CODEX LOOP"
            sublabel="operator-in-loop"
            color={isPhaseActive('INTEL') || isPhaseActive('PLAN') || isPhaseActive('EXECUTE') || isPhaseActive('DEFEND')
              ? '#f59e0b' : '#484f58'}
            active={currentPhase !== null}
            size={28}
          />

          {/* Fixture executor */}
          <Node
            x={ENGINE.x}
            y={ENGINE.y}
            label="FIXTURE RUNNER"
            sublabel="cyber artifact loader"
            color={isPhaseActive('EXECUTE') || isPhaseActive('PLAN') || isPhaseActive('DEFEND')
              ? '#58a6ff' : '#484f58'}
            active={
              currentPhase === 'PLAN' ||
              currentPhase === 'EXECUTE' ||
              currentPhase === 'DEFEND'
            }
            size={28}
          />

          {/* Windows target */}
          <Node
            x={TARGET.x}
            y={TARGET.y}
            label="WIN [LAB-HOST]"
            sublabel="Windows 11 · target"
            color={
              exploitStatus === 'vulnerable' ? '#f85149' :
              exploitStatus === 'blocked'    ? '#3fb950' :
              currentPhase === 'EXECUTE'     ? '#f85149' :
              '#484f58'
            }
            active={currentPhase === 'EXECUTE' || currentPhase === 'DEFEND'}
            size={28}
          />

          {/* VulnerableApp sub-node */}
          <SubNode
            x={VULN_APP.x}
            y={VULN_APP.y}
            label=":8080"
            color={exploitStatus === 'blocked' ? '#3fb950' : exploitStatus === 'vulnerable' ? '#f85149' : '#484f58'}
            active={currentPhase === 'EXECUTE' || currentPhase === 'DEFEND'}
          />

          {/* Privilege sub-node — shows priv differential */}
          <SubNode
            x={PRIV_LOW.x}
            y={PRIV_LOW.y}
            label="SYSTEM"
            color={exploitStatus === 'vulnerable' ? '#f85149' : exploitStatus === 'blocked' ? '#3fb950' : '#484f58'}
            active={exploitStatus === 'vulnerable' || exploitStatus === 'blocked'}
          />

          {/* ── Legend ───────────────────────────────────────────────── */}
          <g transform="translate(8, 212)">
            {[
              { color: '#21262d', label: 'IDLE' },
              { color: '#f59e0b', label: 'ACTIVE' },
              { color: '#f85149', label: 'COMPROMISED' },
              { color: '#3fb950', label: 'PATCHED' },
            ].map(({ color, label }, i) => (
              <g key={label} transform={`translate(0, ${i * 11})`}>
                <rect x={0} y={-4} width={14} height={2} fill={color} rx={1} />
                <text
                  x={18}
                  y={0}
                  fill="#484f58"
                  fontSize="6"
                  fontFamily="'JetBrains Mono', monospace"
                  letterSpacing="0.1em"
                >
                  {label}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
