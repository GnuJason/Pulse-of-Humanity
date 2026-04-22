// hover-engine.js — pointer routing, continent highlight, glass micro-panel.

import { CONTINENT_LABELS } from "./anchor.js";
import { continentNow } from "./simulation.js";
import { fmtCompact, fmtSigned, palette, icons } from "./formatters.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export function createHoverEngine({ svg, hoverLayer, continentGroups, panelHost }) {
  // --- Glass panel ----------------------------------------------------------
  const panel = document.createElement("div");
  panel.className = "ss-panel";
  panel.setAttribute("role", "tooltip");
  panel.setAttribute("aria-live", "polite");
  panel.style.opacity = "0";
  panel.style.pointerEvents = "none";
  panel.innerHTML = `
    <div class="ss-panel__title"></div>
    <div class="ss-panel__pop"><span class="num"></span></div>
    <div class="ss-panel__rows">
      <div class="ss-panel__row" data-k="b">
        <span class="ss-panel__icon">${icons.birth}</span>
        <span class="ss-panel__label">Births today</span>
        <span class="ss-panel__val"></span>
      </div>
      <div class="ss-panel__row" data-k="d">
        <span class="ss-panel__icon">${icons.death}</span>
        <span class="ss-panel__label">Deaths today</span>
        <span class="ss-panel__val"></span>
      </div>
      <div class="ss-panel__row" data-k="n">
        <span class="ss-panel__icon">${icons.net}</span>
        <span class="ss-panel__label">Net change</span>
        <span class="ss-panel__val"></span>
      </div>
    </div>
  `;
  panelHost.appendChild(panel);

  const titleEl = panel.querySelector(".ss-panel__title");
  const popEl   = panel.querySelector(".ss-panel__pop .num");
  const bVal    = panel.querySelector('[data-k="b"] .ss-panel__val');
  const dVal    = panel.querySelector('[data-k="d"] .ss-panel__val');
  const nVal    = panel.querySelector('[data-k="n"] .ss-panel__val');
  const bIcon   = panel.querySelector('[data-k="b"] .ss-panel__icon');
  const dIcon   = panel.querySelector('[data-k="d"] .ss-panel__icon');
  const nIcon   = panel.querySelector('[data-k="n"] .ss-panel__icon');
  bIcon.style.color = palette.birth;
  dIcon.style.color = palette.death;
  nIcon.style.color = palette.net;
  bVal.style.color = palette.birth;
  dVal.style.color = palette.death;
  nVal.style.color = palette.net;

  // --- State ----------------------------------------------------------------
  let activeKey = null;
  let lastPointer = { x: 0, y: 0 };

  function setActive(continentKey) {
    if (continentKey === activeKey) return;
    activeKey = continentKey;

    // Clear hover layer.
    while (hoverLayer.firstChild) hoverLayer.removeChild(hoverLayer.firstChild);

    if (!continentKey) {
      panel.style.opacity = "0";
      return;
    }

    const group = continentGroups[continentKey];
    if (!group) return;

    // Clone every country path of this continent into hoverLayer w/ glow fill.
    // Fix Option 2: hover clones carry NO stroke. This eliminates the faint
    // stray line that could appear over North America when hovering Europe,
    // caused by stroked geometry on overlapping cloned paths.
    for (const p of group.paths) {
      const clone = p.cloneNode(false);
      clone.setAttribute("fill", group.tint.glow);
      clone.setAttribute("stroke", "none");
      clone.setAttribute("stroke-width", "0");
      clone.setAttribute("vector-effect", "non-scaling-stroke");
      clone.setAttribute("filter", "url(#ss-innerglow)");
      clone.setAttribute("class", "ss-country ss-country--active");
      hoverLayer.appendChild(clone);
    }

    titleEl.textContent = CONTINENT_LABELS[continentKey];
    panel.style.opacity = "1";
  }

  function updatePanelNumbers(tMs) {
    if (!activeKey) return;
    const c = continentNow(activeKey, tMs);
    if (!c) return;
    popEl.textContent = fmtCompact(c.population);
    bVal.textContent = fmtSigned(c.birthsToday);
    dVal.textContent = fmtSigned(-c.deathsToday);
    nVal.textContent = fmtSigned(c.netToday);
  }

  function positionPanel(clientX, clientY) {
    if (!activeKey) return;
    const pad = 14;
    const rect = panelHost.getBoundingClientRect();
    const w = panel.offsetWidth || 220;
    const h = panel.offsetHeight || 120;
    let x = clientX - rect.left + pad;
    let y = clientY - rect.top  + pad;
    if (x + w + pad > rect.width)  x = clientX - rect.left - w - pad;
    if (y + h + pad > rect.height) y = clientY - rect.top  - h - pad;
    if (x < pad) x = pad;
    if (y < pad) y = pad;
    panel.style.transform = `translate(${x}px, ${y}px)`;
  }

  // --- Listeners ------------------------------------------------------------
  function onPointerMove(e) {
    lastPointer.x = e.clientX;
    lastPointer.y = e.clientY;
    const target = e.target;
    if (target && target.nodeType === 1 && target.classList?.contains("ss-country")) {
      const k = target.getAttribute("data-continent");
      setActive(k);
      positionPanel(e.clientX, e.clientY);
    } else {
      setActive(null);
    }
  }
  function onPointerLeave() { setActive(null); }

  svg.addEventListener("pointermove", onPointerMove, { passive: true });
  svg.addEventListener("pointerleave", onPointerLeave, { passive: true });

  // Programmatic API for the test harness.
  function activateByKey(key) {
    setActive(key);
    if (key) positionPanel(window.innerWidth / 2, window.innerHeight / 2);
  }

  return {
    update: updatePanelNumbers, // call each RAF tick
    activateByKey,
    get active() { return activeKey; },
  };
}
