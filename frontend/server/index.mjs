import { createReadStream, existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  publicEnv,
  replacePublicEnvPlaceholders,
  resolvePublicEnv,
} from './publicEnv.js';

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

const BFF_ROUTES = {
  contact: '/app/contact',
  travelBySlug: '/app/travel/',
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
    return {
      bodyAttributes: '',
      headMarkup: '',
      htmlAttributes: '',
    };
  }

  return {
    bodyAttributes: helmet.bodyAttributes?.toString?.() || '',
    headMarkup: [
      helmet.title?.toString?.() || '',
      helmet.priority?.toString?.() || '',
      helmet.meta?.toString?.() || '',
      helmet.link?.toString?.() || '',
      helmet.script?.toString?.() || '',
      helmet.style?.toString?.() || '',
      helmet.base?.toString?.() || '',
      helmet.noscript?.toString?.() || '',
    ].join(''),
    htmlAttributes: helmet.htmlAttributes?.toString?.() || '',
  };
}

function injectTagAttributes(template, tagName, attributes) {
  if (!attributes) {
    return template;
  }

  const pattern = new RegExp(`<${tagName}([^>]*)>`, 'i');
  return template.replace(pattern, (_, existing = '') => {
    const normalizedExisting = String(existing).trim();
    return `<${tagName}${normalizedExisting ? ` ${normalizedExisting}` : ''} ${attributes}>`;
  });
}

function getForwardedValue(value) {
  if (Array.isArray(value)) {
    return value[0] || '';
  }

  if (typeof value === 'string') {
    return value.split(',')[0]?.trim() || '';
  }

  return '';
}

function getRequestOrigin(req) {
  const forwardedProto = getForwardedValue(req.headers['x-forwarded-proto']);
  const forwardedHost = getForwardedValue(req.headers['x-forwarded-host']);
  const host =
    forwardedHost || getForwardedValue(req.headers.host) || 'localhost';
  const proto = forwardedProto || 'http';

  return `${proto}://${host}`;
}

function serializeStateForHtml(state) {
  return JSON.stringify(state)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function serializePublicEnvForHtml(config) {
  return serializeStateForHtml({
    API_URL: config.API_URL,
    GA_TRACKING_ID: config.GA_TRACKING_ID,
    PROJECT_OWNER: config.PROJECT_OWNER,
    SITE_DOMAIN: config.SITE_DOMAIN,
  });
}

function getRequestPublicEnv(req) {
  const requestOrigin = getRequestOrigin(req);
  const requestUrl = new URL(requestOrigin);
  return resolvePublicEnv({
    ...publicEnv,
    SITE_DOMAIN: requestUrl.host,
  });
}

function getBackendBaseUrl(requestPublicEnv) {
  return process.env.SSR_API_URL || requestPublicEnv.API_URL;
}

function getBackendForwardHeaders(requestPublicEnv, acceptLanguage) {
  const headers = {
    Accept: 'application/json',
  };

  if (typeof acceptLanguage === 'string' && acceptLanguage.trim()) {
    headers['Accept-Language'] = acceptLanguage;
  }

  try {
    const publicApiUrl = new URL(requestPublicEnv.API_URL);
    headers.Host = publicApiUrl.host;
    headers['X-Forwarded-Host'] = publicApiUrl.host;
    headers['X-Forwarded-Proto'] = publicApiUrl.protocol.replace(':', '');
  } catch {
    // Ignore malformed public API URLs and fall back to transport defaults.
  }

  return headers;
}

async function fetchBackendJson(req, backendPath, requestUrl) {
  const requestPublicEnv = getRequestPublicEnv(req);
  const upstreamBaseUrl = getBackendBaseUrl(requestPublicEnv);
  const upstreamUrl = new URL(backendPath, upstreamBaseUrl);

  if (requestUrl?.search) {
    upstreamUrl.search = requestUrl.search;
  }

  const startedAt = Date.now();
  const response = await fetch(upstreamUrl, {
    headers: getBackendForwardHeaders(
      requestPublicEnv,
      req.headers['accept-language']
    ),
  });
  const durationMs = Date.now() - startedAt;
  const text = await response.text();

  let payload;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  return {
    durationMs,
    payload,
    requestPublicEnv,
    response,
    upstreamBaseUrl,
    upstreamUrl,
  };
}

async function readJsonBody(req) {
  const chunks = [];

  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }

  if (chunks.length === 0) {
    return null;
  }

  const rawBody = Buffer.concat(chunks).toString('utf8');
  return rawBody ? JSON.parse(rawBody) : null;
}

async function forwardBackendWrite(req, backendPath) {
  const requestPublicEnv = getRequestPublicEnv(req);
  const upstreamBaseUrl = getBackendBaseUrl(requestPublicEnv);
  const upstreamUrl = new URL(backendPath, upstreamBaseUrl);
  const body = await readJsonBody(req);

  const startedAt = Date.now();
  const response = await fetch(upstreamUrl, {
    method: req.method,
    headers: {
      ...getBackendForwardHeaders(
        requestPublicEnv,
        req.headers['accept-language']
      ),
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : null,
  });
  const durationMs = Date.now() - startedAt;
  const text = await response.text();

  let payload;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  return {
    durationMs,
    payload,
    response,
    upstreamBaseUrl,
    upstreamUrl,
  };
}

function isTravelBffRoute(pathname) {
  return /^\/app\/travel\/[^/]+\/[^/]+\/[^/]+\/?$/.test(pathname);
}

function getTravelBackendPath(pathname) {
  const match = pathname.match(/^\/app\/travel\/([^/]+)\/([^/]+)\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, countrySlug, placeSlug, dateSlug] = match;
  return `/v1/travel/${countrySlug}/${placeSlug}/${dateSlug}/`;
}

async function handleBffRequest(req, res, requestUrl, start) {
  const pathname = requestUrl.pathname;
  let backendPath = null;

  switch (pathname) {
    case BFF_ROUTES.contact:
      if (req.method !== 'POST') {
        res.writeHead(405, {
          'Content-Type': 'application/json; charset=utf-8',
          Allow: 'POST',
        });
        res.end(JSON.stringify({ message: 'Method not allowed.' }));
        return true;
      }
      backendPath = '/v1/contact/';
      break;
    default:
      if (isTravelBffRoute(pathname)) {
        backendPath = getTravelBackendPath(pathname);
      }
      break;
  }

  if (!backendPath) {
    return false;
  }

  const backendFetch =
    req.method === 'POST'
      ? await forwardBackendWrite(req, backendPath)
      : await fetchBackendJson(req, backendPath, requestUrl);
  const { durationMs, payload, response, upstreamBaseUrl, upstreamUrl } =
    backendFetch;

  res.writeHead(response.status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(JSON.stringify(payload));

  logRequest({
    kind: 'bff',
    method: req.method,
    path: requestUrl.pathname,
    query: requestUrl.search || '',
    status: response.status,
    duration_ms: Date.now() - start,
    upstream_duration_ms: durationMs,
    upstream_path: `${upstreamUrl.pathname}${upstreamUrl.search}`,
    upstream_base_url: upstreamBaseUrl,
  });

  return true;
}

function logRequest(info) {
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      service: 'frontend-ssr',
      ...info,
    })
  );
}

async function renderDocument(url, acceptLanguage, requestOrigin) {
  const [{ renderStream }, template] = await Promise.all([
    import(pathToFileURL(serverEntryPath).href),
    readFile(indexHtmlPath, 'utf8'),
  ]);
  const requestPublicEnv = resolvePublicEnv({
    ...publicEnv,
    SITE_DOMAIN: new URL(requestOrigin).host,
  });

  const { stream, helmetContext, dehydratedState, language, abort } =
    await renderStream(url, acceptLanguage, requestOrigin);
  const { bodyAttributes, headMarkup, htmlAttributes } =
    renderHelmet(helmetContext);
  const publicEnvScript = `<script>window.__PUBLIC_ENV__ = ${serializePublicEnvForHtml(
    requestPublicEnv
  )};</script>`;
  const initialLanguageScript = `<script>window.__INITIAL_LANGUAGE__ = ${JSON.stringify(language)};</script>`;
  const dehydratedStateScript = `<script>window.__REACT_QUERY_STATE__ = ${serializeStateForHtml(
    dehydratedState
  )};</script>`;

  const rootMarker = '<div id="root"></div>';
  const processedTemplate = injectTagAttributes(
    injectTagAttributes(
      replacePublicEnvPlaceholders(template, requestPublicEnv).replace(
        '</head>',
        `${headMarkup}${publicEnvScript}${initialLanguageScript}</head>`
      ),
      'html',
      htmlAttributes
    ),
    'body',
    bodyAttributes
  );

  const parts = processedTemplate.split(rootMarker);
  if (parts.length !== 2) {
    abort();
    throw new Error('SSR template root marker not found exactly once.');
  }

  return {
    abort,
    language,
    stream,
    suffix: parts[1].replace('</body>', `${dehydratedStateScript}</body>`),
    prefix: `${parts[0]}<div id="root">`,
  };
}

async function pipeDocument(req, res, requestUrl, start, url, acceptLanguage) {
  const requestOrigin = getRequestOrigin(req);
  const { abort, language, stream, prefix, suffix } = await renderDocument(
    url,
    acceptLanguage,
    requestOrigin
  );

  return new Promise((resolve, reject) => {
    let finished = false;
    const onClientClose = () => {
      if (!finished) {
        abort();
      }
    };

    const complete = () => {
      if (finished) {
        return;
      }

      finished = true;
      logRequest({
        kind: 'document',
        method: req.method,
        path: requestUrl.pathname,
        query: requestUrl.search || '',
        host: req.headers.host || 'localhost',
        language: String(req.headers['accept-language'] || language),
        status: 200,
        duration_ms: Date.now() - start,
        streaming: true,
      });
      resolve();
    };

    const fail = error => {
      if (finished) {
        return;
      }

      finished = true;
      req.off('close', onClientClose);
      abort();
      reject(error);
    };

    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'X-Accel-Buffering': 'no',
    });
    req.on('close', onClientClose);
    res.write(prefix);
    res.flushHeaders?.();

    stream.on('error', fail);
    stream.on('end', () => {
      req.off('close', onClientClose);
      res.end(suffix);
      complete();
    });
    stream.pipe(res, { end: false });
  });
}

const server = http.createServer(async (req, res) => {
  const start = Date.now();
  try {
    const host = req.headers.host || 'localhost';
    const requestUrl = new URL(req.url || '/', `http://${host}`);

    if (requestUrl.pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ status: 'ok' }));
      logRequest({
        kind: 'health',
        method: req.method,
        path: requestUrl.pathname,
        status: 200,
        duration_ms: Date.now() - start,
      });
      return;
    }

    if (await handleBffRequest(req, res, requestUrl, start)) {
      return;
    }

    if (await serveStatic(req, res)) {
      logRequest({
        kind: 'static',
        method: req.method,
        path: requestUrl.pathname,
        status: 200,
        duration_ms: Date.now() - start,
      });
      return;
    }

    await pipeDocument(
      req,
      res,
      requestUrl,
      start,
      requestUrl.pathname + requestUrl.search,
      req.headers['accept-language'] || 'en'
    );
  } catch (error) {
    console.error('[frontend-ssr] request failed', error);
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Internal Server Error');
    } else {
      res.destroy(error instanceof Error ? error : undefined);
    }
    logRequest({
      kind: 'document',
      method: req.method,
      path: req.url || '/',
      status: 500,
      duration_ms: Date.now() - start,
      error: error instanceof Error ? error.message : String(error),
    });
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log(`[frontend-ssr] listening on 0.0.0.0:${port}`);
});
