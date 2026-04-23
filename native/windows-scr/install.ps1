param(
  [string]$InstallRoot = "$env:LOCALAPPDATA\PulseOfHumanityScreensaver"
)

$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $projectDir "build"
$screensaverBinary = Join-Path $buildDir "PulseOfHumanity.scr"

if (-not (Test-Path $screensaverBinary)) {
  throw "Build output not found at $screensaverBinary. Run native/windows-scr/build.ps1 first."
}

New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
Copy-Item $screensaverBinary (Join-Path $InstallRoot "PulseOfHumanity.scr") -Force

$assetSource = Join-Path $buildDir "assets"
$assetTarget = Join-Path $InstallRoot "assets"
Remove-Item $assetTarget -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item $assetSource $assetTarget -Recurse -Force

$desktopKey = "HKCU:\Control Panel\Desktop"
Set-ItemProperty -Path $desktopKey -Name SCRNSAVE.EXE -Value (Join-Path $InstallRoot "PulseOfHumanity.scr")
Set-ItemProperty -Path $desktopKey -Name ScreenSaveActive -Value "1"

Write-Host "Installed Pulse of Humanity screensaver to $InstallRoot"