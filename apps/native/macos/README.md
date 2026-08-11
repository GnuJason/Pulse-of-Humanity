# Pulse of Humanity macOS Screen Saver Bundle

This bundle wraps the offline `dist/screensaver-web` build in a native `ScreenSaverView` backed by `WKWebView`.

## Behavior

- Loads the bundled `index.html` from the bundle resources with no network access.
- Supports both preview mode and full-screen mode through the native Screen Saver host.
- Exits on mouse movement, mouse clicks, scroll-wheel input, and key presses in full-screen mode.
- Disables the web runtime's fullscreen and JS-level exit handling so the native wrapper owns host behavior.

## Build

Commands:

- `npm run sync:native-assets`
- `bash apps/native/macos/build.sh`

The build script emits `apps/native/macos/build/PulseOfHumanity.saver`.

## Install

- `bash apps/native/macos/install.sh`

The installer copies the bundle to `~/Library/Screen Savers`.