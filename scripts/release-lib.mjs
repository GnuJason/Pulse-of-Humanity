import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

import JSZip from "jszip";

export const DEFAULT_SOURCE_DATE_EPOCH = 1767225600;

export async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
}

export async function readVersion(repoRoot) {
  const raw = await fs.readFile(path.join(repoRoot, "VERSION"), "utf8");
  return raw.trim();
}

export function getSourceDateEpoch() {
  const raw = process.env.SOURCE_DATE_EPOCH;
  if (!raw) {
    return DEFAULT_SOURCE_DATE_EPOCH;
  }

  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`Invalid SOURCE_DATE_EPOCH: ${raw}`);
  }
  return value;
}

export function getSourceDate() {
  return new Date(getSourceDateEpoch() * 1000);
}

export function toPosixPath(filePath) {
  return filePath.split(path.sep).join("/");
}

export async function collectFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await collectFiles(fullPath));
      continue;
    }
    files.push(fullPath);
  }
  return files;
}

export async function zipDirectory({ sourceDir, outputPath, prefix = "" }) {
  const files = await collectFiles(sourceDir);
  const zip = new JSZip();
  const fixedDate = getSourceDate();

  for (const filePath of files) {
    const relPath = toPosixPath(path.relative(sourceDir, filePath));
    const archivePath = prefix ? `${prefix}/${relPath}` : relPath;
    const data = await fs.readFile(filePath);
    zip.file(archivePath, data, {
      compression: "DEFLATE",
      compressionOptions: { level: 9 },
      date: fixedDate,
    });
  }

  const zipBuffer = await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 9 },
    platform: "UNIX",
  });

  await ensureDir(path.dirname(outputPath));
  await fs.writeFile(outputPath, zipBuffer);
}

export async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(data).digest("hex");
}

export async function describeArtifact(filePath, { relativeTo } = {}) {
  const stats = await fs.stat(filePath);
  return {
    path: toPosixPath(relativeTo ? path.relative(relativeTo, filePath) : filePath),
    size: stats.size,
    sha256: await sha256File(filePath),
  };
}

export async function writeJson(filePath, payload) {
  await ensureDir(path.dirname(filePath));
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}