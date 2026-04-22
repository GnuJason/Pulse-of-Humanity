// anchor.js — frozen constants copied from population.py (STATIC_ANCHOR + BASE_CONTINENTS).
// Source of truth for the parent app: /population.py
// This module is intentionally a stand-alone copy so the screensaver runs
// without any backend dependency. If parent constants change, update here.

export const STATIC_ANCHOR = Object.freeze({
  baselinePopulation: 8130371000,
  baselineTimestamp: "2026-01-01T00:00:00Z",
  baselineTimestampMs: Date.UTC(2026, 0, 1, 0, 0, 0, 0),
  birthsPerSecond: 4.28,
  deathsPerSecond: 2.06,
  source: "UN WPP 2024 Medium Variant (static)",
});

// Continent baseline populations + per-second rates.
// Keys MUST match the continent codes assigned in country-continent.js.
export const BASE_CONTINENTS = Object.freeze({
  Africa:        { population: 1420000000, birthsPerSecond: 2.7,  deathsPerSecond: 0.9  },
  Asia:          { population: 4700000000, birthsPerSecond: 4.5,  deathsPerSecond: 2.1  },
  Europe:        { population:  750000000, birthsPerSecond: 0.9,  deathsPerSecond: 1.1  },
  North_America: { population:  600000000, birthsPerSecond: 0.7,  deathsPerSecond: 0.6  },
  South_America: { population:  430000000, birthsPerSecond: 0.6,  deathsPerSecond: 0.4  },
  Oceania:       { population:   44000000, birthsPerSecond: 0.05, deathsPerSecond: 0.03 },
  Antarctica:    { population:       1100, birthsPerSecond: 0.0,  deathsPerSecond: 0.0  },
});

// Display labels (with spaces).
export const CONTINENT_LABELS = Object.freeze({
  Africa: "Africa",
  Asia: "Asia",
  Europe: "Europe",
  North_America: "North America",
  South_America: "South America",
  Oceania: "Oceania",
  Antarctica: "Antarctica",
});

// Tints for the cinematic map. Desaturated, earthy, harmonious.
// Each tint includes a base land color + a deeper accent for hover glow.
export const CONTINENT_TINTS = Object.freeze({
  Africa:        { base: "#b89a73", glow: "#e4c999" }, // warm sand
  Asia:          { base: "#a0846e", glow: "#cdb093" }, // muted clay
  Europe:        { base: "#8fa089", glow: "#c2d0ba" }, // pale moss
  North_America: { base: "#8593a0", glow: "#b7c4cf" }, // cool slate
  South_America: { base: "#b08c6a", glow: "#d9b48a" }, // soft terracotta
  Oceania:       { base: "#b8a36b", glow: "#e4cc8f" }, // dusty gold (Australia)
  Antarctica:    { base: "#a8b2b8", glow: "#d7dee2" }, // soft ice
});
