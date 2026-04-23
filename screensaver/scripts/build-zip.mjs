import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs/promises";

import {
  ensureDir,
  readVersion,
  zipDirectory,
} from "../../scripts/release-lib.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const distDir = path.join(repoRoot, "screensaver", "dist");
const releasesDir = path.join(repoRoot, "dist", "releases");
const zipPath = path.join(repoRoot, "static", "screensaver.zip");

const version = await readVersion(repoRoot);
const versionedZipPath = path.join(releasesDir, `pulse-of-humanity-screensaver-v${version}.zip`);

await ensureDir(releasesDir);
await zipDirectory({
  sourceDir: distDir,
  outputPath: versionedZipPath,
  prefix: "screensaver",
});
await fs.copyFile(versionedZipPath, zipPath);