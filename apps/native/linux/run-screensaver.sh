#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ENTRYPOINT="$REPO_ROOT/dist/screensaver-web/index.html"

if [[ ! -f "$ENTRYPOINT" ]]; then
  echo "Build the web runtime first: npm run build:screensaver" >&2
  exit 1
fi

exec "${BROWSER:-xdg-open}" "$ENTRYPOINT"