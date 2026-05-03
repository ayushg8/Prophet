/**
 * forecastIndex.ts — lightweight lookup helpers for the World-Side data layer.
 *
 * Downstream components import from here when they need a quick Record<id, …>
 * lookup rather than iterating over the full arrays in worldSide.ts.
 */

import {
  type ExploitCandidate,
  type StrikeForecast,
  candidates,
  forecasts,
} from './worldSide';

/** The candidate the demo starts on (edge-appliance path). */
export const defaultCandidateId = 'cs-fixture-edge-appliance-001';

/** All candidates indexed by candidate_id. */
export const candidatesById: Record<string, ExploitCandidate> =
  Object.fromEntries(candidates.map((c) => [c.candidate_id, c]));

/** All forecasts indexed by the input_candidate_id they correspond to. */
export const forecastsByCandidateId: Record<string, StrikeForecast> =
  Object.fromEntries(forecasts.map((f) => [f.input_candidate_id, f]));
