#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB_ONLY=0
BUILD_MACOS=0

for arg in "$@"; do
  case "$arg" in
    --web-only)
      WEB_ONLY=1
      BUILD_MACOS=0
      ;;
    --include-macos)
      BUILD_MACOS=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ "$(uname -s)" == "Darwin" && $WEB_ONLY -eq 0 && $BUILD_MACOS -eq 0 ]]; then
  BUILD_MACOS=1
fi

export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1767225600}"

cd "$REPO_ROOT"
npm run build:screensaver

if [[ $BUILD_MACOS -eq 1 ]]; then
  npm run build:native:assets
  bash native/macos-saver/build.sh
fi

node scripts/package-release-artifacts.mjs