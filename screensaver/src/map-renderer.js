// map-renderer.js — Equal Earth projection + GeoJSON -> SVG path builder.
// Pure rendering. No interactivity (see hover-engine.js).
//
// Equal Earth projection:
//   B. Šavrič, T. Patterson, B. Jenny (2018). "The Equal Earth map projection."
//   Closed-form, equal-area, visually pleasing. ~30 LOC.

import { CONTINENT_TINTS, CONTINENT_LABELS } from "./anchor.js";
import { continentForFeature } from "./country-continent.js";

const SVG_NS = "http://www.w3.org/2000/svg";

// --- Equal Earth projection -------------------------------------------------
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796;
const M = Math.sqrt(3) / 2;

function equalEarth(lonDeg, latDeg) {
  const lon = (lonDeg * Math.PI) / 180;
  const lat = (latDeg * Math.PI) / 180;
  const t = Math.asin(M * Math.sin(lat));
  const t2 = t * t;
  const t6 = t2 * t2 * t2;
  const x = (lon * Math.cos(t)) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)));
  const y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [x, y];
}

// Pre-computed projection extent: project corners to find bounds.
// Equal Earth max-x is at (180, 0); max-y at (0, 90).
const EE_MAX_X = equalEarth(180, 0)[0];
const EE_MAX_Y = equalEarth(0, 90)[1];

// Build a fitted projector: fits projection bounds into [0,width]x[0,height]
// with `padding` inside, preserving aspect ratio.
function makeFitted(width, height, padding = 8) {
  const innerW = width - 2 * padding;
  const innerH = height - 2 * padding;
  const projW = 2 * EE_MAX_X;
  const projH = 2 * EE_MAX_Y;
  const scale = Math.min(innerW / projW, innerH / projH);
  const cx = width / 2;
  const cy = height / 2;
  return function project(lon, lat) {
    const [x, y] = equalEarth(lon, lat);
    return [cx + x * scale, cy - y * scale];
  };
}

// --- GeoJSON path builder ---------------------------------------------------
// Split rings at antimeridian crossings (|Δlon| > 180°) so polygons like Fiji
// and Russia don't stretch a thin strip across the entire map.
function ringToPath(ring, project) {
  if (ring.length === 0) return "";
  let d = "";
  let penDown = false;
  let prevLon = null;
  for (let i = 0; i < ring.length; i++) {
    const [lon, lat] = ring[i];
    const [x, y] = project(lon, lat);
    const xs = x.toFixed(2);
    const ys = y.toFixed(2);
    if (!penDown || (prevLon !== null && Math.abs(lon - prevLon) > 180)) {
      d += "M" + xs + " " + ys;
      penDown = true;
    } else {
      d += "L" + xs + " " + ys;
    }
    prevLon = lon;
  }
  return d + "Z";
}

function geometryToPath(geom, project) {
  if (!geom) return "";
  if (geom.type === "Polygon") {
    return geom.coordinates.map((ring) => ringToPath(ring, project)).join("");
  }
  if (geom.type === "MultiPolygon") {
    return geom.coordinates
      .map((poly) => poly.map((ring) => ringToPath(ring, project)).join(""))
      .join("");
  }
  return "";
}

// --- Graticule (lon/lat grid) ----------------------------------------------
function buildGraticule(project, stepDeg = 30) {
  const lines = [];
  // Meridians
  for (let lon = -180; lon <= 180; lon += stepDeg) {
    let d = "";
    for (let lat = -89; lat <= 89; lat += 2) {
      const [x, y] = project(lon, lat);
      d += (lat === -89 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
    }
    lines.push(d);
  }
  // Parallels
  for (let lat = -60; lat <= 60; lat += stepDeg) {
    let d = "";
    for (let lon = -180; lon <= 180; lon += 2) {
      const [x, y] = project(lon, lat);
      d += (lon === -180 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
    }
    lines.push(d);
  }
  return lines;
}

// --- Public API -------------------------------------------------------------
function buildMap(host, featureCollection, options = {}) {
  const width  = options.width  || host.clientWidth  || 1600;
  const height = options.height || host.clientHeight || 900;
  const project = makeFitted(width, height, options.padding ?? 8);

  // Clear host.
  while (host.firstChild) host.removeChild(host.firstChild);

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.setAttribute("class", "ss-map");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "World map of population dynamics by continent");

  // <defs>: ocean radial gradient + inner-glow filter + subtle elevation noise.
  const defs = document.createElementNS(SVG_NS, "defs");
  defs.innerHTML = `
    <radialGradient id="ss-ocean" cx="50%" cy="50%" r="78%">
      <stop offset="0%"   stop-color="#11223d"/>
      <stop offset="40%"  stop-color="#0a1524"/>
      <stop offset="75%"  stop-color="#050a13"/>
      <stop offset="100%" stop-color="#02040a"/>
    </radialGradient>
    <filter id="ss-elevation" x="0%" y="0%" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="1.2" numOctaves="1" seed="7" stitchTiles="stitch" result="t"/>
      <feColorMatrix in="t" type="matrix"
        values="0 0 0 0 0
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 0.06 0"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
    <filter id="ss-innerglow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2.2" result="b"/>
      <feOffset in="b" dx="0" dy="0" result="ob"/>
      <feFlood flood-color="#fff7e0" flood-opacity="0.38"/>
      <feComposite in2="ob" operator="in" result="glow"/>
      <feComposite in="glow" in2="SourceGraphic" operator="over"/>
    </filter>
  `;
  svg.appendChild(defs);

  // Ocean
  const ocean = document.createElementNS(SVG_NS, "rect");
  ocean.setAttribute("x", "0"); ocean.setAttribute("y", "0");
  ocean.setAttribute("width", String(width));
  ocean.setAttribute("height", String(height));
  ocean.setAttribute("fill", "url(#ss-ocean)");
  svg.appendChild(ocean);

  // Graticule
  const grat = document.createElementNS(SVG_NS, "g");
  grat.setAttribute("class", "ss-graticule");
  for (const d of buildGraticule(project)) {
    const p = document.createElementNS(SVG_NS, "path");
    p.setAttribute("d", d);
    grat.appendChild(p);
  }
  svg.appendChild(grat);

  // Land layer
  const land = document.createElementNS(SVG_NS, "g");
  land.setAttribute("class", "ss-land");

  // Group by continent so the hover engine can highlight the whole region cheaply.
  const continentGroups = {};
  const allPaths = [];

  for (const feature of featureCollection.features) {
    const continent = continentForFeature(feature);
    if (!continent) continue; // unknown territory: skip (rare)
    const tint = CONTINENT_TINTS[continent];
    if (!tint) continue;

    const path = document.createElementNS(SVG_NS, "path");
    const d = geometryToPath(feature.geometry, project);
    if (!d) continue;
    path.setAttribute("d", d);
    path.setAttribute("fill", tint.base);
    path.setAttribute("stroke", "rgba(0,0,0,0.55)");
    path.setAttribute("stroke-width", "0.4");
    path.setAttribute("vector-effect", "non-scaling-stroke");
    path.setAttribute("class", "ss-country");
    path.setAttribute("data-continent", continent);
    path.setAttribute("data-name", feature?.properties?.name || "");
    path.setAttribute("data-id", feature.id ?? "");

    if (!continentGroups[continent]) {
      continentGroups[continent] = {
        key: continent,
        label: CONTINENT_LABELS[continent],
        tint,
        paths: [],
      };
    }
    continentGroups[continent].paths.push(path);
    allPaths.push(path);
    land.appendChild(path);
  }

  svg.appendChild(land);

  // Elevation overlay: clone the land geometry once into a second group and
  // apply the turbulence-driven shading filter. Blend on top at low opacity so
  // the effect is *felt* (landform texture) rather than *seen* (visible noise).
  const elev = land.cloneNode(true);
  elev.setAttribute("class", "ss-land ss-land--elevation");
  elev.setAttribute("filter", "url(#ss-elevation)");
  elev.setAttribute("style", "mix-blend-mode: overlay; opacity: 0.28; pointer-events: none;");
  // Strip the pointer-events from clones too (defense in depth).
  for (const p of elev.querySelectorAll("path")) {
    p.setAttribute("pointer-events", "none");
  }
  svg.appendChild(elev);

  // Hover layer (empty until a continent is active). Sits above land,
  // below counter (which is HTML, not SVG).
  const hoverLayer = document.createElementNS(SVG_NS, "g");
  hoverLayer.setAttribute("class", "ss-hover-layer");
  hoverLayer.setAttribute("aria-hidden", "true");
  svg.appendChild(hoverLayer);

  host.appendChild(svg);

  return { svg, hoverLayer, continentGroups, allPaths, width, height };
}

/**
 * Renders the map into `host` (an HTMLElement). Returns metadata used by the
 * hover engine: { svg, continentGroups, allPaths }.
 */
export function renderMap(host, featureCollection, options = {}) {
  let currentOptions = { ...options };
  const mapInfo = buildMap(host, featureCollection, currentOptions);

  function resize(nextOptions = {}) {
    currentOptions = { ...currentOptions, ...nextOptions };
    const nextMap = buildMap(host, featureCollection, currentOptions);
    Object.assign(mapInfo, nextMap);
    return mapInfo;
  }

  function destroy() {
    while (host.firstChild) host.removeChild(host.firstChild);
  }

  mapInfo.resize = resize;
  mapInfo.destroy = destroy;

  return mapInfo;
}
