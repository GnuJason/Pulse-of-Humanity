// main.js — bootstraps the screensaver.
// 1. Loads world TopoJSON (fetch -> file:// fallback)
// 2. Converts to GeoJSON FeatureCollection via topojson-client
// 3. Builds map + counter + hover engine
// 4. Drives a single RAF loop

import { renderMap } from "./map-renderer.js";
import { createHoverEngine } from "./hover-engine.js";
import { createCounter } from "./counter.js";

const TOPO_URL = new URL("../assets/world-110m.json", import.meta.url).href;
const TOPO_FALLBACK_URL = new URL("../assets/world-110m.js", import.meta.url).href;

let topoFallbackPromise = null;

function loadTopoFallback() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Fallback topology is only available in a browser environment."));
  }
  if (window.__WORLD_TOPO__) {
    return Promise.resolve(window.__WORLD_TOPO__);
  }
  if (!topoFallbackPromise) {
    topoFallbackPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = TOPO_FALLBACK_URL;
      script.async = true;
      script.onload = () => {
        if (window.__WORLD_TOPO__) {
          resolve(window.__WORLD_TOPO__);
          return;
        }
        reject(new Error("Fallback topology script loaded without defining __WORLD_TOPO__."));
      };
      script.onerror = () => reject(new Error("Failed to load fallback topology script."));
      document.head.appendChild(script);
    });
  }
  return topoFallbackPromise;
}

async function loadTopo() {
  // Preferred: fetch JSON (works on http(s):// and most browsers' file:// when allowed).
  try {
    const r = await fetch(TOPO_URL);
    if (r.ok) return await r.json();
    throw new Error(`HTTP ${r.status}`);
  } catch (e) {
    // Fallback for file:// where fetch() is blocked: load the JS-wrapped copy
    // only when the primary JSON fetch fails.
    try {
      return await loadTopoFallback();
    } catch (fallbackError) {
      throw new Error(
        "Failed to load world-110m.json and fallback topology script. " +
        "Original error: " + e.message + ". " +
        "Fallback error: " + fallbackError.message
      );
    }
  }
}

function getTopojson() {
  // topojson-client is a UMD bundle; it exposes `topojson` on window.
  if (typeof window !== "undefined" && window.topojson) return window.topojson;
  throw new Error("topojson-client not loaded. Include vendor/topojson-client.min.js before main.js.");
}

let activeRuntime = null;
let startToken = 0;

export const DEFAULT_SCREENAVER_CONFIG = Object.freeze({
  startOnLoad: true,
  idleTimeoutMs: 0,
  cursorHideDelayMs: 2000,
  fullscreen: false,
  exitOnInput: {
    enabled: false,
    mousemove: true,
    keydown: true,
    click: true,
    wheel: true,
    touchstart: true,
  },
});

function mergeConfig(config = {}) {
  return {
    ...DEFAULT_SCREENAVER_CONFIG,
    ...config,
    exitOnInput: {
      ...DEFAULT_SCREENAVER_CONFIG.exitOnInput,
      ...(config.exitOnInput || {}),
    },
  };
}

export async function start({
  mapHost,
  counterHost,
  panelHost,
  width,
  height,
  timeProvider,             // optional () => epochMs, for time-warp in harness
} = {}) {
  startToken += 1;
  const token = startToken;

  if (activeRuntime) {
    activeRuntime.teardown();
  }

  mapHost     = mapHost     || document.getElementById("ss-map");
  counterHost = counterHost || document.getElementById("ss-counter-host");
  panelHost   = panelHost   || document.getElementById("ss-panel-host");

  const topo = await loadTopo();
  if (token !== startToken) {
    return {
      paused: true,
      teardown() {},
      pause() {},
      resume() {},
    };
  }

  const topojson = getTopojson();
  const fc = topojson.feature(topo, topo.objects.countries);

  let destroyed = false;
  let paused = false;
  let frameId = 0;
  let lastTs = performance.now();
  let mapInfo = renderMap(mapHost, fc, { width, height });
  let counter = createCounter(counterHost);
  let hover = createHoverEngine({
    svg: mapInfo.svg,
    hoverLayer: mapInfo.hoverLayer,
    continentGroups: mapInfo.continentGroups,
    panelHost,
  });

  function createHover(mapState, activeKey = null) {
    const nextHover = createHoverEngine({
      svg: mapState.svg,
      hoverLayer: mapState.hoverLayer,
      continentGroups: mapState.continentGroups,
      panelHost,
    });
    if (activeKey) nextHover.activateByKey(activeKey);
    return nextHover;
  }

  function stopFrame() {
    if (frameId) {
      cancelAnimationFrame(frameId);
      frameId = 0;
    }
  }

  function frame(now) {
    if (destroyed || paused) return;
    const dt = Math.min(0.1, (now - lastTs) / 1000); // clamp big jumps
    lastTs = now;
    const tMs = timeProvider ? timeProvider() : Date.now();
    counter.tick(tMs, dt);
    hover.update(tMs);
    frameId = requestAnimationFrame(frame);
  }

  function onResize() {
    if (destroyed) return;
    const activeKey = hover.active;
    hover.destroy();
    mapInfo.resize({ width, height });
    hover = createHover(mapInfo, activeKey);
  }

  function pause() {
    if (destroyed || paused) return;
    paused = true;
    stopFrame();
  }

  function resume() {
    if (destroyed || !paused) return;
    paused = false;
    lastTs = performance.now();
    frameId = requestAnimationFrame(frame);
  }

  function onVisibilityChange() {
    if (document.hidden) {
      pause();
      return;
    }
    resume();
  }

  function teardown() {
    if (destroyed) return;
    destroyed = true;
    paused = true;
    stopFrame();
    window.removeEventListener("resize", onResize);
    document.removeEventListener("visibilitychange", onVisibilityChange);
    hover.destroy();
    counter.destroy();
    mapInfo.destroy();
    if (activeRuntime?.token === token) {
      activeRuntime = null;
    }
  }

  window.addEventListener("resize", onResize, { passive: true });
  document.addEventListener("visibilitychange", onVisibilityChange);

  if (!document.hidden) {
    frameId = requestAnimationFrame(frame);
  } else {
    paused = true;
  }

  activeRuntime = {
    token,
    teardown,
    pause,
    resume,
  };

  // Expose for harness; production will simply ignore.
  return {
    get mapInfo() { return mapInfo; },
    get counter() { return counter; },
    get hover() { return hover; },
    get paused() { return paused; },
    teardown,
    pause,
    resume,
  };
}

export function createScreensaverController({ config, ...startOptions } = {}) {
  const runtimeConfig = mergeConfig(config);
  const activityEvents = ["mousemove", "keydown", "click", "wheel", "touchstart"];
  let runtime = null;
  let idleTimerId = 0;
  let cursorTimerId = 0;
  let destroyed = false;
  let cursorHidden = false;

  function clearIdleTimer() {
    if (idleTimerId) {
      clearTimeout(idleTimerId);
      idleTimerId = 0;
    }
  }

  function clearCursorTimer() {
    if (cursorTimerId) {
      clearTimeout(cursorTimerId);
      cursorTimerId = 0;
    }
  }

  function showCursor() {
    if (!cursorHidden) return;
    document.documentElement.style.cursor = "";
    cursorHidden = false;
  }

  function hideCursor() {
    if (!runtime) return;
    document.documentElement.style.cursor = "none";
    cursorHidden = true;
  }

  function scheduleCursorHide() {
    clearCursorTimer();
    showCursor();
    if (!runtime || runtimeConfig.cursorHideDelayMs < 0) return;
    cursorTimerId = window.setTimeout(hideCursor, runtimeConfig.cursorHideDelayMs);
  }

  async function requestFullscreen() {
    if (!runtimeConfig.fullscreen || typeof document === "undefined") return false;
    if (document.fullscreenElement || !document.documentElement.requestFullscreen) return false;
    try {
      await document.documentElement.requestFullscreen({ navigationUI: "hide" });
      return true;
    } catch {
      return false;
    }
  }

  async function activate() {
    if (destroyed) return null;
    clearIdleTimer();
    if (!runtime) {
      runtime = await start(startOptions);
    }
    scheduleCursorHide();
    await requestFullscreen();
    return runtime;
  }

  function armIdleTimer() {
    if (destroyed || runtime) return;
    clearIdleTimer();
    if (runtimeConfig.idleTimeoutMs <= 0) {
      return;
    }
    idleTimerId = window.setTimeout(() => {
      idleTimerId = 0;
      void activate();
    }, runtimeConfig.idleTimeoutMs);
  }

  function shouldExitOnInput(eventType) {
    return runtimeConfig.exitOnInput.enabled && runtimeConfig.exitOnInput[eventType] === true;
  }

  function restoreAfterExit() {
    clearCursorTimer();
    showCursor();
  }

  async function exit() {
    clearIdleTimer();
    if (!runtime) {
      restoreAfterExit();
      return;
    }
    const currentRuntime = runtime;
    runtime = null;
    currentRuntime.teardown();
    restoreAfterExit();
    if (document.fullscreenElement && document.exitFullscreen) {
      try {
        await document.exitFullscreen();
      } catch {
        // Ignore browser/webview fullscreen exit failures.
      }
    }
  }

  function onActivity(event) {
    if (destroyed) return;
    if (runtime) {
      if (shouldExitOnInput(event.type)) {
        void exit();
        return;
      }
      scheduleCursorHide();
      return;
    }
    armIdleTimer();
  }

  function attachListeners() {
    for (const eventName of activityEvents) {
      window.addEventListener(eventName, onActivity, { passive: eventName !== "keydown" });
    }
  }

  function detachListeners() {
    for (const eventName of activityEvents) {
      window.removeEventListener(eventName, onActivity);
    }
  }

  function initialize() {
    if (destroyed) return;
    attachListeners();
    if (runtimeConfig.startOnLoad) {
      void activate();
      return;
    }
    armIdleTimer();
  }

  function teardown() {
    if (destroyed) return;
    destroyed = true;
    detachListeners();
    clearIdleTimer();
    clearCursorTimer();
    if (runtime) {
      runtime.teardown();
      runtime = null;
    }
    showCursor();
  }

  return {
    config: runtimeConfig,
    initialize,
    activate,
    armIdleTimer,
    exit,
    teardown,
    get active() { return runtime !== null; },
    get runtime() { return runtime; },
  };
}
