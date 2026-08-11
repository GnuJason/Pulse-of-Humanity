import "../styles/screensaver.css";
import * as topojson from "topojson-client";
import { createScreensaverController } from "./main.js";

if (typeof window !== "undefined" && !window.topojson) {
  window.topojson = topojson;
}

const config = {
  startOnLoad: true,
  idleTimeoutMs: 0,
  cursorHideDelayMs: 2000,
  fullscreen: true,
  exitOnInput: {
    enabled: true,
    mousemove: true,
    keydown: true,
    click: true,
    wheel: true,
    touchstart: true,
  },
  ...(typeof window !== "undefined" ? window.__PULSE_OF_HUMANITY_SCREENSAVER_CONFIG__ : {}),
};

const controller = createScreensaverController({ config });

if (typeof window !== "undefined") {
  window.__PULSE_OF_HUMANITY_SCREENSAVER__ = controller;
}

controller.initialize();