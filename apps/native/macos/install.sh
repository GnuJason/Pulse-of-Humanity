#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$PROJECT_DIR/build/PulseOfHumanity.saver"
INSTALL_DIR="$HOME/Library/Screen Savers"

if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "Build output not found at $BUNDLE_DIR. Run apps/native/macos/build.sh first." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/PulseOfHumanity.saver"
cp -R "$BUNDLE_DIR" "$INSTALL_DIR/PulseOfHumanity.saver"

echo "Installed PulseOfHumanity.saver to $INSTALL_DIR"