// simulation.js — pure functions for the deterministic population simulation.
// Inputs: anchor (from anchor.js), authoritative epoch ms.
// Outputs: numbers. No DOM, no globals, no random.

import { STATIC_ANCHOR, BASE_CONTINENTS } from "./anchor.js";

const MS_PER_SECOND = 1000;

// Compute UTC midnight (epoch ms) for the day containing tMs.
function getUtcDayStartMs(tMs) {
  const d = new Date(tMs);
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 0, 0, 0, 0);
}

export function elapsedSeconds(tMs, anchor = STATIC_ANCHOR) {
  return Math.max(0, (tMs - anchor.baselineTimestampMs) / MS_PER_SECOND);
}

export function secondsSinceUtcMidnight(tMs) {
  return Math.max(0, (tMs - getUtcDayStartMs(tMs)) / MS_PER_SECOND);
}

// Global authoritative population at tMs.
export function worldNow(tMs, anchor = STATIC_ANCHOR) {
  const elapsed = elapsedSeconds(tMs, anchor);
  const net = anchor.birthsPerSecond - anchor.deathsPerSecond;
  return anchor.baselinePopulation + elapsed * net;
}

// Births / deaths since UTC midnight, globally.
export function dailyCounts(tMs, anchor = STATIC_ANCHOR) {
  const s = secondsSinceUtcMidnight(tMs);
  return {
    birthsToday: s * anchor.birthsPerSecond,
    deathsToday: s * anchor.deathsPerSecond,
    netToday:    s * (anchor.birthsPerSecond - anchor.deathsPerSecond),
  };
}

// Per-continent state at tMs.
export function continentNow(continentKey, tMs, anchor = STATIC_ANCHOR) {
  const c = BASE_CONTINENTS[continentKey];
  if (!c) return null;
  const elapsed = elapsedSeconds(tMs, anchor);
  const secondsToday = secondsSinceUtcMidnight(tMs);
  const net = c.birthsPerSecond - c.deathsPerSecond;
  return {
    population:      c.population + elapsed * net,
    birthsToday:     secondsToday * c.birthsPerSecond,
    deathsToday:     secondsToday * c.deathsPerSecond,
    netToday:        secondsToday * net,
    birthsPerSecond: c.birthsPerSecond,
    deathsPerSecond: c.deathsPerSecond,
  };
}

// Convenience: snapshot every continent at once.
export function allContinentsNow(tMs, anchor = STATIC_ANCHOR) {
  const out = {};
  for (const k of Object.keys(BASE_CONTINENTS)) {
    out[k] = continentNow(k, tMs, anchor);
  }
  return out;
}
