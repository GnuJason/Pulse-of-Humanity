#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$PROJECT_DIR/../../.." && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
BUNDLE_DIR="$BUILD_DIR/PulseOfHumanity.saver"
RESOURCES_DIR="$BUNDLE_DIR/Contents/Resources"
EXECUTABLE_DIR="$BUNDLE_DIR/Contents/MacOS"
VERSION="$(tr -d '\r\n' < "$REPO_ROOT/VERSION")"
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1767225600}"
SOURCE_DATE_ISO="$(date -u -r "$SOURCE_DATE_EPOCH" +%Y-%m-%dT%H:%M:%SZ)"

if [[ ! -d "$PROJECT_DIR/generated-assets" ]]; then
  echo "Bundled screensaver assets were not found. Run npm run sync:native-assets first." >&2
  exit 1
fi

rm -rf "$BUNDLE_DIR"
mkdir -p "$RESOURCES_DIR" "$EXECUTABLE_DIR"

cp "$PROJECT_DIR/Info.plist" "$BUNDLE_DIR/Contents/Info.plist"
cp -R "$PROJECT_DIR/generated-assets" "$RESOURCES_DIR/screensaver"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$BUNDLE_DIR/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$BUNDLE_DIR/Contents/Info.plist"

xcrun clang \
  -fobjc-arc \
  -framework Cocoa \
  -framework ScreenSaver \
  -framework WebKit \
  -bundle \
  -o "$EXECUTABLE_DIR/PulseOfHumanity" \
  "$PROJECT_DIR/src/PulseOfHumanityView.m"

cat > "$BUILD_DIR/release-metadata.json" <<EOF
{
  "name": "Pulse of Humanity",
  "version": "$VERSION",
  "platform": "macos",
  "package": ".saver",
  "sourceDateEpoch": $SOURCE_DATE_EPOCH,
  "sourceDateIso": "$SOURCE_DATE_ISO"
}
EOF

echo "Built $BUNDLE_DIR"