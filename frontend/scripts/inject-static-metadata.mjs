import {
  copyFile,
  mkdir,
  readFile,
  readdir,
  stat,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  publicEnv,
  replacePublicEnvPlaceholders,
} from '../server/publicEnv.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const distDir = path.join(rootDir, 'dist');
const publicDir = path.join(rootDir, 'public');

const STATIC_METADATA_FILES = [
  'sitemap.xml',
  'robots.txt',
  'manifest.json',
  path.join('locales', 'en', 'translation.json'),
  path.join('locales', 'pl', 'translation.json'),
];

async function copyDirectory(sourceDir, targetDir) {
  await mkdir(targetDir, { recursive: true });
  const entries = await readdir(sourceDir, { withFileTypes: true });

  for (const entry of entries) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);

    if (entry.isDirectory()) {
      await copyDirectory(sourcePath, targetPath);
      continue;
    }

    await mkdir(path.dirname(targetPath), { recursive: true });
    await copyFile(sourcePath, targetPath);
  }
}

async function replaceMetadataFile(relativePath) {
  const targetPath = path.join(distDir, relativePath);

  try {
    const targetStat = await stat(targetPath);
    if (!targetStat.isFile()) {
      return;
    }
  } catch {
    return;
  }

  const current = await readFile(targetPath, 'utf8');
  const next = replacePublicEnvPlaceholders(current, publicEnv);

  if (next !== current) {
    await writeFile(targetPath, next);
  }
}

async function main() {
  const preservedIndexHtml = await readFile(path.join(distDir, 'index.html'));

  await copyDirectory(publicDir, distDir);
  await writeFile(path.join(distDir, 'index.html'), preservedIndexHtml);

  for (const relativePath of STATIC_METADATA_FILES) {
    await replaceMetadataFile(relativePath);
  }
}

await main();
