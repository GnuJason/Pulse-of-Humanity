// main.js — bootstraps the screensaver.
// 1. Loads world TopoJSON (fetch -> file:// fallback)
// 2. Converts to GeoJSON FeatureCollection via topojson-client
// 3. Builds map + counter + hover engine
// 4. Drives a single RAF loop

import { renderMap } from "./map-renderer.js";
import { createHoverEngine } from "./hover-engine.js";
import { createCounter } from "./counter.js";

const TOPO_URL = new URL("../assets/world-110m.json", import.meta.url).href;

async function loadTopo() {
  // Preferred: fetch JSON (works on http(s):// and most browsers' file:// when allowed).
  try {
    const r = await fetch(TOPO_URL);
    if (r.ok) return await r.json();
    throw new Error(`HTTP ${r.status}`);
  } catch (e) {
    // Fallback for file:// where fetch() is blocked: use the JS-wrapped copy
    // injected by index.html via <script src="assets/world-110m.js">.
    if (typeof window !== "undefined" && window.__WORLD_TOPO__) {
      return window.__WORLD_TOPO__;
    }
    throw new Error(
      "Failed to load world-110m.json (fetch failed and __WORLD_TOPO__ fallback missing). " +
      "Original error: " + e.message
    );
  }
}

function getTopojson() {
  // topojson-client is a UMD bundle; it exposes `topojson` on window.
  if (typeof window !== "undefined" && window.topojson) return window.topojson;
  throw new Error("topojson-client not loaded. Include vendor/topojson-client.min.js before main.js.");
}

export async function start({
  mapHost,
  counterHost,
  panelHost,
  width,
  height,
  timeProvider,             // optional () => epochMs, for time-warp in harness
} = {}) {
  mapHost     = mapHost     || document.getElementById("ss-map");
  counterHost = counterHost || document.getElementById("ss-counter-host");
  panelHost   = panelHost   || document.getElementById("ss-panel-host");

  const topo = await loadTopo();
  const topojson = getTopojson();
  const fc = topojson.feature(topo, topo.objects.countries);

  const mapInfo = renderMap(mapHost, fc, { width, height });
  const counter = createCounter(counterHost);
  const hover   = createHoverEngine({
    svg: mapInfo.svg,
    hoverLayer: mapInfo.hoverLayer,
    continentGroups: mapInfo.continentGroups,
    panelHost,
  });

  let lastTs = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - lastTs) / 1000); // clamp big jumps
    lastTs = now;
    const tMs = timeProvider ? timeProvider() : Date.now();
    counter.tick(tMs, dt);
    hover.update(tMs);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // Expose for harness; production will simply ignore.
  return { mapInfo, counter, hover };
}
