import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const sourceDir = path.join(repoRoot, "screensaver", "dist");

const targets = [
  path.join(repoRoot, "native", "windows-scr", "assets", "screensaver"),
  path.join(repoRoot, "native", "macos-saver", "resources", "screensaver"),
];

async function syncTarget(targetDir) {
  await rm(targetDir, { recursive: true, force: true });
  await mkdir(path.dirname(targetDir), { recursive: true });
  await cp(sourceDir, targetDir, { recursive: true });
}

async function main() {
  await Promise.all(targets.map(syncTarget));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});