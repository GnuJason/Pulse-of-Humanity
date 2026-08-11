param(
  [switch]$SkipWindowsNative
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path (Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent) -Parent

if (-not $env:SOURCE_DATE_EPOCH) {
  $env:SOURCE_DATE_EPOCH = "1767225600"
}

Push-Location $repoRoot
try {
  npm run build:screensaver
  node tools/release/stamp-release.mjs
  node tools/release/screensaver-scripts/build-zip.mjs

  if (-not $SkipWindowsNative) {
    npm run sync:native-assets
    powershell -ExecutionPolicy Bypass -File apps/native/windows/build.ps1
  }

  node tools/release/package-release-artifacts.mjs
}
finally {
  Pop-Location
}