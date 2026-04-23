import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  DEFAULT_SOURCE_DATE_EPOCH,
  getSourceDate,
  getSourceDateEpoch,
  readVersion,
  writeJson,
} from "./release-lib.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const version = await readVersion(repoRoot);
const sourceDateEpoch = getSourceDateEpoch();
const metadata = {
  name: "Pulse of Humanity Screensaver",
  version,
  sourceDateEpoch,
  sourceDateIso: getSourceDate().toISOString(),
  reproducibleSinceEpoch: DEFAULT_SOURCE_DATE_EPOCH,
};

await writeJson(path.join(repoRoot, "screensaver", "dist", "release-metadata.json"), metadata);
await writeJson(path.join(repoRoot, "dist", "releases", "release-metadata.json"), metadata);