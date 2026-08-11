// formatters.js — number formatting, semantic palette, inline icon SVGs.

const intGrouped = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const intGroupedFixed1 = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function fmtInt(n) {
  return intGrouped.format(Math.round(n));
}

// Compact form for the panel: 1,234,567 -> "1.23M"
export function fmtCompact(n) {
  const abs = Math.abs(n);
  if (abs >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (abs >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (abs >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return intGroupedFixed1.format(Math.round(n));
}

export function fmtSigned(n) {
  const r = Math.round(n);
  return (r >= 0 ? "+" : "") + intGrouped.format(r);
}

// Semantic palette — desaturated, earthy, never fluorescent.
export const palette = {
  birth: "#a8d4a3",   // warm jade
  death: "#e0b680",   // muted amber
  net:   "#9ec6c7",   // soft teal / cool slate
  textPrimary: "rgba(240, 238, 232, 0.92)",
  textMuted:   "rgba(240, 238, 232, 0.55)",
};

// Tiny inline SVG icons (16x16 viewBox). currentColor so CSS controls hue.
export const icons = {
  birth: `<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
    <path d="M8 2.5c1.6 1.4 2.6 2.9 2.6 4.4a2.6 2.6 0 1 1-5.2 0c0-1.5 1-3 2.6-4.4z"
      fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
  </svg>`,
  death: `<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
    <circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.2"/>
    <path d="M5.2 6.5c.4-.6 1-1 1.7-1M9.1 5.5c.7 0 1.3.4 1.7 1" stroke="currentColor"
      stroke-width="1.2" stroke-linecap="round" fill="none"/>
  </svg>`,
  net: `<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
    <path d="M3 8h10M9 4l4 4-4 4" fill="none" stroke="currentColor"
      stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`,
};
