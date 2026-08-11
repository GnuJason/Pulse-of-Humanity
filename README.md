# Pulse of Humanity

Pulse of Humanity is a screensaver-first monorepo for an offline, deterministic population visualization.

## Layout

- `apps/screensaver-web`: Vite source for the offline browser runtime.
- `apps/native/windows`, `apps/native/macos`, and `apps/native/linux`: platform wrapper targets.
- `apps/download-site`: deprecated Flask/Render download site, retained only as an archive.
- `shared/population-anchor.json`: canonical demographic contract.
- `tools/generate-population-contract`: emits Python and JavaScript consumers from the contract.
- `tools/release`: release build and native asset-sync tooling.
- `tests`: population contract, screensaver runtime, and native layout checks.

## Development

```bash
npm ci
npm run build:screensaver
npm run test:monorepo
```

The web build writes to ignored `dist/screensaver-web`. It does not create a ZIP, installer, signed artifact, or notarized bundle.

## Population Contract

Edit `shared/population-anchor.json`, then run:

```bash
npm run generate:population-contract
```

This updates `shared/population.py` and `apps/screensaver-web/src/population.js`. Do not edit generated consumers directly.

## Status

Windows and macOS wrappers are source-isolated and consume assets copied from the web build. Linux currently contains an explicit XScreenSaver/browser-host placeholder. Packaging, installers, signing, and notarization are deferred to the next phase.
