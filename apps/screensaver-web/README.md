# Pulse of Humanity — Screensaver

Offline Vite runtime for the Pulse of Humanity screensaver.

## Run it

The screensaver is pure static frontend (HTML + ES modules + one tiny vendor JS).

### Recommended: any static server

```bash
# from the repo root
python3 -m http.server --directory dist/screensaver-web 8080
# then open http://localhost:8080/index.html
# or the test harness:  http://localhost:8080/test-harness.html
```

### `file://` (zero-server)

You can also open `dist/screensaver-web/index.html` directly. Most browsers will block the
`fetch()` of `assets/world-110m.json` over `file://`. The page handles that
automatically: a `<script src="assets/world-110m.js">` tag pre-loads the same
data onto `window.__WORLD_TOPO__`, and `src/main.js` falls back to it when
`fetch()` fails. No user action required.

## What it does

- Renders a cinematic Equal-Earth world map (TopoJSON → SVG).
- Soft continent tints, faint graticule, atmospheric ocean gradient + vignette.
- Hover any country: that **continent** lights up with an inner glow, and a
  glass micro-panel shows live births / deaths / net change today.
- Top-centered floating counter: world population (eased), and today's
  births / deaths / net (ticked, with semantic accent colors).
- Respects `prefers-reduced-motion`.
- One RAF loop. Pure-function simulation. No backend.

## File map

```
apps/screensaver-web/
  index.html               # Production entry point
  test-harness.html        # FPS meter, time-warp, programmatic hover
  README.md                # This file
  src/
    main.js                # Boot + RAF loop
    population.js          # generated deterministic population consumer
    continent-style.js     # screensaver-only display metadata
    simulation.js          # Pure functions: worldNow / continentNow / dailyCounts
    map-renderer.js        # Equal Earth projection + SVG builder
    hover-engine.js        # Pointer routing + glow + glass panel
    counter.js             # Floating global counter
    formatters.js          # Intl + palette + inline icons
    motion.js              # Reduced-motion gate + lerp utilities
    country-continent.js   # ISO numeric -> continent map (see Notes)
  styles/
    screensaver.css        # All visuals
  assets/
    world-110m.json        # Natural Earth 110m via world-atlas (TopoJSON)
    world-110m.js          # Same content, exposed as window.__WORLD_TOPO__
    LICENSE-naturalearth.txt
  vendor/
    topojson-client.min.js # ~7KB, ISC; converts TopoJSON -> GeoJSON
    LICENSE-topojson-client.txt
```

## Notes

- **Why a country→continent map exists:** the original architecture proposal
  assumed Natural Earth's `CONTINENT` property would be present at runtime.
  The world-atlas v2 distillation strips properties to `{ name }` only, so we
  map by ISO 3166-1 numeric `id` (with three name-based fallbacks for
  N. Cyprus, Somaliland, Kosovo). See `src/country-continent.js`.

- **Population contract:** `src/population.js` is generated from
  `shared/population-anchor.json`. Run `npm run generate:population-contract`
  after changing the contract.

## Vendor / asset provenance

| File | Source | License | SHA-256 |
|---|---|---|---|
| `assets/world-110m.json` | `world-atlas@2` (`countries-110m.json`) via jsdelivr | Public Domain (Natural Earth) | `2516c915867c7baf18ddec727aec46c315541a07cfb3d79a6559b05d5e94eee8` |
| `assets/world-110m.js` | Generated locally by wrapping the JSON above as `window.__WORLD_TOPO__ = ...;` | Public Domain (Natural Earth) | `d23d69ac0f723bb3e5f4cd383f8bd69938c5bb307abb12193d6625d1da93cbe7` |
| `vendor/topojson-client.min.js` | `topojson-client@3` (UMD min build) via jsdelivr | ISC | `25cd02ae486cc5063e0215a4e4cfb15de83700c87ac48bac4d57dc6aaf3ebb89` |

Verify any time:

```bash
sha256sum apps/screensaver-web/assets/world-110m.json \
          apps/screensaver-web/assets/world-110m.js \
          apps/screensaver-web/vendor/topojson-client.min.js
```

## Rollback

The runtime is isolated from the deprecated download site. Its shared dependency
is the generated population contract; native wrappers consume only build output.

```bash
# Atomic rollback
rm -rf apps/screensaver-web/

# Verify nothing else references it
npm run build:screensaver
npm run test:monorepo
```

If committed as a single feature commit:

```bash
git revert <commit-sha>
```

Before committing:

```bash
git clean -fd dist/screensaver-web/
```
