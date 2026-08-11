// motion.js — central animation tokens + reduced-motion gate.
// Pure module. No side effects on import beyond reading matchMedia.

const reducedMotionMQ =
  typeof window !== "undefined" && typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : { matches: false, addEventListener: () => {} };

export const motion = {
  // True unless the user (or the harness) has forced reduced motion.
  enabled: !reducedMotionMQ.matches,
  // Durations are in ms and are halved (or zeroed) when reduced.
  fast: 180,
  med: 320,
  slow: 800,
  // Lerp constant for the global counter (per-second damping).
  counterLerpPerSec: 6,
};

// Allow the harness to force a value; production never calls this.
export function setReducedMotion(reduced) {
  motion.enabled = !reduced;
}

reducedMotionMQ.addEventListener?.("change", (e) => {
  motion.enabled = !e.matches;
});

// Critically-damped lerp toward target.
// dt in seconds. k in 1/sec. Frame-rate independent.
export function damp(current, target, k, dt) {
  const lambda = 1 - Math.exp(-k * dt);
  return current + (target - current) * lambda;
}

export function clamp(v, lo, hi) {
  return v < lo ? lo : v > hi ? hi : v;
}
