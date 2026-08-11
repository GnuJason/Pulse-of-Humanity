# Pulse of Humanity Windows Screensaver Wrapper

This wrapper builds a native `.scr` host around the offline `dist/screensaver-web` build.

## Behavior

- `/s` or no argument launches full-screen mode.
- `/p <HWND>` launches preview mode inside the provided parent window.
- `/c` opens a configuration stub dialog.
- Full-screen mode exits on mouse movement, mouse buttons, wheel input, touch, and key presses.
- Assets are synced into ignored `generated-assets` before a native build.

## Build

Requirements:

- Visual Studio Developer PowerShell with `cl.exe` on `PATH`
- WebView2 SDK installed and `WEBVIEW2_SDK_DIR` pointing at its root

Commands:

- `npm run sync:native-assets`
- `powershell -ExecutionPolicy Bypass -File apps/native/windows/build.ps1`

The build script emits `apps/native/windows/build/PulseOfHumanity.scr` and copies synced assets next to it.

## Install

- `powershell -ExecutionPolicy Bypass -File apps/native/windows/install.ps1`

The installer performs a per-user install under `%LOCALAPPDATA%\PulseOfHumanityScreensaver` and registers the `.scr` path in `HKCU\Control Panel\Desktop`.