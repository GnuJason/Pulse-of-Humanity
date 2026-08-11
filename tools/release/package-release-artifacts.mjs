import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  describeArtifact,
  ensureDir,
  getSourceDate,
  getSourceDateEpoch,
  readVersion,
  writeJson,
  zipDirectory,
} from "./release-lib.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const releaseDir = path.join(repoRoot, "dist", "releases");

const version = await readVersion(repoRoot);
const sourceDate = getSourceDate();
const sourceDateEpoch = getSourceDateEpoch();

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function packageWindows() {
  const buildDir = path.join(repoRoot, "apps", "native", "windows", "build");
  const scrPath = path.join(buildDir, "PulseOfHumanity.scr");
  if (!(await exists(scrPath))) {
    return [];
  }

  const versionedScrName = `pulse-of-humanity-windows-scr-v${version}.scr`;
  const versionedScrPath = path.join(releaseDir, versionedScrName);
  const zipName = `pulse-of-humanity-windows-scr-v${version}.zip`;
  const zipPath = path.join(releaseDir, zipName);
  await fs.copyFile(scrPath, versionedScrPath);
  await zipDirectory({
    sourceDir: buildDir,
    outputPath: zipPath,
    prefix: "PulseOfHumanity-windows-scr",
  });

  const buildMetadataPath = path.join(buildDir, "release-metadata.json");

  return [
    {
      key: "windowsScr",
      label: "Windows .scr wrapper",
      target: "windows",
      ...(await describeArtifact(versionedScrPath, { relativeTo: repoRoot })),
    },
    {
      key: "windowsScrArchive",
      label: "Windows .scr package archive",
      target: "windows",
      ...(await describeArtifact(zipPath, { relativeTo: repoRoot })),
    },
  ];
}

async function packageMacos() {
  const bundleDir = path.join(repoRoot, "apps", "native", "macos", "build", "PulseOfHumanity.saver");
  if (!(await exists(bundleDir))) {
    return [];
  }

  const zipName = `pulse-of-humanity-macos-saver-v${version}.zip`;
  const zipPath = path.join(releaseDir, zipName);
  await zipDirectory({
    sourceDir: bundleDir,
    outputPath: zipPath,
    prefix: "PulseOfHumanity.saver",
  });

  return [
    {
      key: "macosSaverArchive",
      label: "macOS .saver package archive",
      target: "macos",
      ...(await describeArtifact(zipPath, { relativeTo: repoRoot })),
    },
  ];
}

const screensaverZipPath = path.join(releaseDir, `pulse-of-humanity-screensaver-v${version}.zip`);
if (!(await exists(screensaverZipPath))) {
  throw new Error(`Expected screensaver artifact was not found at ${screensaverZipPath}`);
}

const manifest = {
  name: "Pulse of Humanity Screensaver",
  version,
  sourceDateEpoch,
  sourceDateIso: sourceDate.toISOString(),
  generatedArtifacts: [
    {
      key: "screensaverZip",
      label: "Screensaver offline ZIP",
      target: "universal",
      ...(await describeArtifact(screensaverZipPath, { relativeTo: repoRoot })),
    },
    ...(await packageWindows()),
    ...(await packageMacos()),
  ],
};

await writeJson(path.join(releaseDir, "artifact-manifest.json"), manifest);