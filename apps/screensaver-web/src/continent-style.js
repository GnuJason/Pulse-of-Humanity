// Screensaver-only display metadata.
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
