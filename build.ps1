param(
  [switch]$SkipWindowsNative
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $env:SOURCE_DATE_EPOCH) {
  $env:SOURCE_DATE_EPOCH = "1767225600"
}

Push-Location $repoRoot
try {
  npm run build:screensaver

  if (-not $SkipWindowsNative) {
    npm run build:native:assets
    powershell -ExecutionPolicy Bypass -File native/windows-scr/build.ps1
  }

  node scripts/package-release-artifacts.mjs
}
finally {
  Pop-Location
}