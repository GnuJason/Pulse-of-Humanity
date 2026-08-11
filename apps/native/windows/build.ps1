param(
  [string]$Arch = "x64",
  [string]$WebView2Sdk = $env:WEBVIEW2_SDK_DIR
)

$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path (Split-Path (Split-Path $projectDir -Parent) -Parent) -Parent
$buildDir = Join-Path $projectDir "build"
$assetSource = Join-Path $projectDir "generated-assets"
$assetTarget = Join-Path $buildDir "assets\screensaver"
$sourceFile = Join-Path $projectDir "src\PulseOfHumanityScr.cpp"
$version = (Get-Content (Join-Path $repoRoot "VERSION") -Raw).Trim()
$sourceDateEpoch = if ($env:SOURCE_DATE_EPOCH) { [long]$env:SOURCE_DATE_EPOCH } else { 1767225600 }

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
  throw "cl.exe was not found. Run this script from a Visual Studio Developer PowerShell session."
}

if (-not $WebView2Sdk) {
  throw "Set WEBVIEW2_SDK_DIR to the installed WebView2 SDK root before building."
}

$includeDir = Join-Path $WebView2Sdk "include"
$libDir = Join-Path $WebView2Sdk "lib\$Arch"
$loaderLib = Join-Path $libDir "WebView2LoaderStatic.lib"
if (-not (Test-Path $loaderLib)) {
  $loaderLib = Join-Path $libDir "WebView2Loader.lib"
}

if (-not (Test-Path $assetSource)) {
  throw "Bundled screensaver assets were not found at $assetSource. Run npm run sync:native-assets first."
}

Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $assetTarget -Force | Out-Null
Copy-Item (Join-Path $assetSource "*") $assetTarget -Recurse -Force

Push-Location $buildDir
try {
  & cl.exe `
    /nologo `
    /std:c++20 `
    /utf-8 `
    /EHsc `
    /DUNICODE `
    /D_UNICODE `
    /DWIN32_LEAN_AND_MEAN `
    /I $includeDir `
    $sourceFile `
    /Fe:PulseOfHumanity.scr `
    /link `
    /SUBSYSTEM:WINDOWS `
    user32.lib `
    gdi32.lib `
    ole32.lib `
    shell32.lib `
    $loaderLib
}
finally {
  Pop-Location
}

$metadata = [ordered]@{
  name = "Pulse of Humanity"
  version = $version
  platform = "windows"
  package = ".scr"
  sourceDateEpoch = $sourceDateEpoch
  sourceDateIso = [DateTimeOffset]::FromUnixTimeSeconds($sourceDateEpoch).UtcDateTime.ToString("o")
}
$metadata | ConvertTo-Json | Set-Content (Join-Path $buildDir "release-metadata.json") -Encoding utf8