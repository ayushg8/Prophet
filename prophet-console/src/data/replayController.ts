import type { AgentEvent, TextEvent } from './mockEvents';

export type ReplayCallback = (event: AgentEvent) => void;
export type GateResolver = () => void;

export interface ReplayHandle {
  authorize: () => void;
  reset: () => void;
}

const MS_PER_CHAR = 22; // typewriter speed: ~22ms per char (matches TypewriterText interval)

function textDurationMs(content: string): number {
  // Wait for about 40% of the typewriter duration — enough for the text to
  // feel live before the next event appears, without stalling the whole demo.
  return Math.ceil(content.length * MS_PER_CHAR * 0.4);
}

export function startReplay(
  events: AgentEvent[],
  onEvent: ReplayCallback,
  onGate: (resolve: GateResolver) => void,
): ReplayHandle {
  let cancelled = false;
  let gateResolve: (() => void) | null = null;

  const authorize = () => {
    if (gateResolve) {
      const r = gateResolve;
      gateResolve = null;
      r();
    }
  };

  const reset = () => {
    cancelled = true;
    gateResolve = null;
  };

  const delay = (ms: number) =>
    new Promise<void>((resolve) => {
      const t = setTimeout(resolve, ms);
      // Allow cancellation
      const check = setInterval(() => {
        if (cancelled) {
          clearTimeout(t);
          clearInterval(check);
          resolve();
        }
      }, 50);
      setTimeout(() => clearInterval(check), ms + 100);
    });

  async function run() {
    for (let i = 0; i < events.length; i++) {
      if (cancelled) break;
      const event = events[i];

      if (event.kind === 'phase') {
        await delay(400);
        onEvent(event);
        await delay(300);
      } else if (event.kind === 'phase_complete') {
        await delay(300);
        onEvent(event);
        await delay(500);
      } else if (event.kind === 'tool_call') {
        onEvent(event);
        // Wait for the tool "execution" duration + buffer
        await delay(event.durationMs + 200);
      } else if (event.kind === 'text') {
        // Emit the event — typewriter effect is handled by the component
        onEvent(event);
        // Wait for the approximate typewriter duration before next event
        await delay(textDurationMs((event as TextEvent).content) + 300);
      } else if (event.kind === 'human_gate') {
        onEvent(event);
        // Pause until authorize() is called
        await new Promise<void>((resolve) => {
          gateResolve = resolve;
          onGate(resolve);
        });
        if (cancelled) break;
        await delay(300);
      } else if (event.kind === 'exploit_status') {
        onEvent(event);
        await delay(500);
      } else if (event.kind === 'patch_diff') {
        onEvent(event);
        await delay(600);
      } else if (event.kind === 'sigma_rule') {
        onEvent(event);
        await delay(600);
      } else {
        onEvent(event);
        await delay(250);
      }
    }
  }

  run();

  return { authorize, reset };
}
