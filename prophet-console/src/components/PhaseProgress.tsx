type Phase = 'INTEL' | 'PLAN' | 'EXECUTE' | 'DEFEND';

const PHASES: { id: Phase; label: string; short: string; roman: string }[] = [
  { id: 'INTEL',   label: 'I — INTEL',     short: 'INTEL',   roman: 'I'   },
  { id: 'PLAN',    label: 'II — PLAN',     short: 'PLAN',    roman: 'II'  },
  { id: 'EXECUTE', label: 'III — EXECUTE', short: 'EXECUTE', roman: 'III' },
  { id: 'DEFEND',  label: 'IV — DEFEND',  short: 'DEFEND',  roman: 'IV'  },
];

interface PhaseProgressProps {
  currentPhase: Phase | null;
  completedPhases: Phase[];
}

export function PhaseProgress({ currentPhase, completedPhases }: PhaseProgressProps) {
  function getPhaseState(phase: Phase): 'completed' | 'active' | 'pending' {
    if (completedPhases.includes(phase)) return 'completed';
    if (currentPhase === phase) return 'active';
    return 'pending';
  }

  return (
    <div className="phase-progress" role="navigation" aria-label="Phase progress">
      {PHASES.map((phase, idx) => {
        const state = getPhaseState(phase.id);
        const isLast = idx === PHASES.length - 1;

        return (
          <div key={phase.id} className="phase-item">
            <div
              className={`phase-node phase-node--${state}`}
              aria-label={`${phase.label}: ${state}`}
            >
              {state === 'completed' && <span className="phase-check">✓</span>}
              {state === 'active'    && <span className="phase-pulse" />}
              {state === 'pending'   && <span className="phase-num">{phase.roman}</span>}
            </div>
            {/* Phase label in mono caps, letter-spacing 0.32em via CSS */}
            <div className={`phase-label phase-label--${state}`}>{phase.short}</div>
            {!isLast && (
              <div
                className={`phase-connector phase-connector--${state === 'completed' ? 'completed' : 'pending'}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
