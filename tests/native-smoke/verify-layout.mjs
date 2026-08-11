import assert from "node:assert/strict";
import fs from "node:fs";

const windowsSource = fs.readFileSync("apps/native/windows/src/PulseOfHumanityScr.cpp", "utf8");
const macosSource = fs.readFileSync("apps/native/macos/src/PulseOfHumanityView.m", "utf8");
const linuxStub = fs.readFileSync("apps/native/linux/pulse-of-humanity.xml", "utf8");

assert.match(windowsSource, /AppMode::Preview/);
assert.match(windowsSource, /screensaver\.local/);
assert.match(macosSource, /ScreenSaverView/);
assert.match(macosSource, /loadFileURL/);
assert.match(linuxStub, /<screensaver/);