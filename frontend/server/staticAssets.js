import { createReadStream, existsSync } from 'node:fs';
import path from 'node:path';

const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

/**
 * Build cache and content-type headers for a static asset response.
 */
function getStaticHeaders(filePath) {
  const ext = path.extname(filePath);
  const type = MIME_TYPES[ext] || 'application/octet-stream';
  const headers = { 'Content-Type': type };

  if (
    filePath.includes(`${path.sep}assets${path.sep}`) ||
    ext === '.css' ||
    ext === '.js' ||
    ext === '.woff' ||
    ext === '.woff2'
  ) {
    headers['Cache-Control'] = 'public, max-age=31536000, immutable';
  } else if (ext === '.html') {
    headers['Cache-Control'] = 'private, no-cache, must-revalidate';
  } else {
    headers['Cache-Control'] = 'public, max-age=3600';
  }

  return headers;
}

/**
 * Resolve a requested static path only when it stays inside the built client directory.
 */
function isSafeStaticPath(pathname, clientDistDir) {
  const decoded = decodeURIComponent(pathname);
  const resolved = path.resolve(clientDistDir, `.${decoded}`);
  return resolved.startsWith(clientDistDir) ? resolved : null;
}

/**
 * Serve a built static asset from the client dist directory.
 */
export async function serveStatic(req, res, clientDistDir) {
  const targetPath = isSafeStaticPath(req.url || '/', clientDistDir);
  if (!targetPath || !existsSync(targetPath)) {
    return false;
  }

  const stats = await import('node:fs/promises').then(fs =>
    fs.stat(targetPath)
  );
  if (!stats.isFile()) {
    return false;
  }

  res.writeHead(200, getStaticHeaders(targetPath));
  createReadStream(targetPath).pipe(res);
  return true;
}
