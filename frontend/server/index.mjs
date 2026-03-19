import { createReadStream, existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, '..');
const clientDistDir = path.join(appRoot, 'dist');
const serverEntryPath = path.join(appRoot, 'dist', 'server', 'entry-server.js');
const indexHtmlPath = path.join(clientDistDir, 'index.html');
const port = Number(process.env.PORT || process.env.FRONTEND_PORT || 8080);

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
    headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
  } else {
    headers['Cache-Control'] = 'public, max-age=3600';
  }

  return headers;
}

function isSafeStaticPath(pathname) {
  const decoded = decodeURIComponent(pathname);
  const resolved = path.resolve(clientDistDir, `.${decoded}`);
  return resolved.startsWith(clientDistDir) ? resolved : null;
}

async function serveStatic(req, res) {
  const targetPath = isSafeStaticPath(req.url || '/');
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

function renderHelmet(helmetContext) {
  const helmet = helmetContext?.helmet;
  if (!helmet) {
    return '';
  }

  return [
    helmet.title?.toString?.() || '',
    helmet.priority?.toString?.() || '',
    helmet.meta?.toString?.() || '',
    helmet.link?.toString?.() || '',
    helmet.script?.toString?.() || '',
    helmet.style?.toString?.() || '',
    helmet.base?.toString?.() || '',
    helmet.noscript?.toString?.() || '',
  ].join('');
}

async function renderDocument(url) {
  const [{ render }, template] = await Promise.all([
    import(pathToFileURL(serverEntryPath).href),
    readFile(indexHtmlPath, 'utf8'),
  ]);

  const { html, helmetContext } = await render(url);
  const headMarkup = renderHelmet(helmetContext);

  return template
    .replace('</head>', `${headMarkup}</head>`)
    .replace('<div id="root"></div>', `<div id="root">${html}</div>`);
}

const server = http.createServer(async (req, res) => {
  try {
    const host = req.headers.host || 'localhost';
    const requestUrl = new URL(req.url || '/', `http://${host}`);

    if (requestUrl.pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ status: 'ok' }));
      return;
    }

    if (await serveStatic(req, res)) {
      return;
    }

    const html = await renderDocument(requestUrl.pathname + requestUrl.search);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
    });
    res.end(html);
  } catch (error) {
    console.error('[frontend-ssr] request failed', error);
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Internal Server Error');
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log(`[frontend-ssr] listening on 0.0.0.0:${port}`);
});
