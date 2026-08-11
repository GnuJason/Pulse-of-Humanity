# Screensaver-First Monorepo

`apps/screensaver-web` owns the offline Vite runtime. `apps/native` owns platform wrappers. `shared/population-anchor.json` is the canonical demographic contract, and `tools/generate-population-contract/generate.mjs` emits its Python and JavaScript consumers.

`apps/download-site` is the archived Flask/Render application. It is deprecated and excluded from release builds. It remains only for a future decision about maintaining a public download portal.

Build outputs belong under root `dist/` and are not version controlled. Native generated assets are copied from `dist/screensaver-web` into ignored per-target `generated-assets` directories by `tools/release/sync-native-assets.mjs`.