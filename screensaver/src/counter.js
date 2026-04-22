// counter.js — top-floating global counter with eased global total + ticked b/d.

import { worldNow, dailyCounts } from "./simulation.js";
import { fmtInt, fmtSigned, palette, icons } from "./formatters.js";
import { motion, damp } from "./motion.js";

export function createCounter(host) {
  const root = document.createElement("div");
  root.className = "ss-counter";
  root.setAttribute("role", "status");
  root.setAttribute("aria-live", "polite");
  root.innerHTML = `
    <div class="ss-counter__label">World population, now</div>
    <div class="ss-counter__total"><span class="num">0</span></div>
    <div class="ss-counter__metrics">
      <div class="ss-counter__metric" data-k="b">
        <span class="ss-counter__icon">${icons.birth}</span>
        <span class="ss-counter__num">0</span>
        <span class="ss-counter__sub">births today</span>
      </div>
      <div class="ss-counter__sep">&middot;</div>
      <div class="ss-counter__metric" data-k="d">
        <span class="ss-counter__icon">${icons.death}</span>
        <span class="ss-counter__num">0</span>
        <span class="ss-counter__sub">deaths today</span>
      </div>
      <div class="ss-counter__sep">&middot;</div>
      <div class="ss-counter__metric" data-k="n">
        <span class="ss-counter__icon">${icons.net}</span>
        <span class="ss-counter__num">0</span>
        <span class="ss-counter__sub">net change</span>
      </div>
    </div>
  `;
  host.appendChild(root);

  const totalEl = root.querySelector(".ss-counter__total .num");
  const bEl = root.querySelector('[data-k="b"] .ss-counter__num');
  const dEl = root.querySelector('[data-k="d"] .ss-counter__num');
  const nEl = root.querySelector('[data-k="n"] .ss-counter__num');
  const bIcon = root.querySelector('[data-k="b"] .ss-counter__icon');
  const dIcon = root.querySelector('[data-k="d"] .ss-counter__icon');
  const nIcon = root.querySelector('[data-k="n"] .ss-counter__icon');
  bIcon.style.color = palette.birth;
  dIcon.style.color = palette.death;
  nIcon.style.color = palette.net;
  bEl.style.color = palette.birth;
  dEl.style.color = palette.death;
  nEl.style.color = palette.net;

  // Continuous (lerped) display value for the world total.
  let displayedTotal = worldNow(Date.now());
  // Last integer values for births/deaths/net (used to detect tick-up).
  let lastB = 0, lastD = 0, lastN = 0;
  let pulseCounter = 0;

  function pop(el) {
    if (!motion.enabled) return;
    el.classList.remove("ss-pop");
    // Force reflow so the animation restarts.
    void el.offsetWidth;
    el.classList.add("ss-pop");
  }

  function tick(tMs, dtSec) {
    const target = worldNow(tMs);
    if (motion.enabled) {
      displayedTotal = damp(displayedTotal, target, motion.counterLerpPerSec, dtSec);
    } else {
      displayedTotal = target;
    }
    totalEl.textContent = fmtInt(displayedTotal);

    const d = dailyCounts(tMs);
    const bi = Math.floor(d.birthsToday);
    const di = Math.floor(d.deathsToday);
    const ni = Math.floor(d.netToday);

    if (bi !== lastB) { bEl.textContent = fmtInt(bi); pop(bEl); lastB = bi; }
    if (di !== lastD) { dEl.textContent = fmtInt(di); pop(dEl); lastD = di; }
    if (ni !== lastN) { nEl.textContent = fmtSigned(ni); lastN = ni; }

    // Optional very subtle breath on the total, gated by motion.
    if (motion.enabled) {
      pulseCounter += dtSec;
      const breath = 1 + 0.004 * Math.sin(pulseCounter * 0.6);
      totalEl.style.transform = `scale(${breath.toFixed(4)})`;
    }
  }

  return { tick, root };
}
