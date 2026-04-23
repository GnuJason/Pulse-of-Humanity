import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const screensaverDir = path.resolve(__dirname, "..");
const distDir = path.join(screensaverDir, "dist");
const sourceIndexPath = path.join(screensaverDir, "index.html");
const distIndexPath = path.join(distDir, "index.html");
const naturalEarthLicenseSrc = path.join(screensaverDir, "assets", "LICENSE-naturalearth.txt");
const naturalEarthLicenseDest = path.join(distDir, "assets", "LICENSE-naturalearth.txt");

const sourceIndex = await fs.readFile(sourceIndexPath, "utf8");
const distIndex = sourceIndex.replaceAll("./dist/assets/", "./assets/");

await fs.mkdir(path.join(distDir, "assets"), { recursive: true });
await fs.writeFile(distIndexPath, distIndex);
await fs.copyFile(naturalEarthLicenseSrc, naturalEarthLicenseDest);