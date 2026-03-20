import { createReadStream, existsSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  publicEnv,
  replacePublicEnvPlaceholders,
  resolvePublicEnv,
} from './publicEnv.js';
import { invalidateCacheTags } from './ssrCache.js';
import { resolveBffBackendPath } from './views/bff.js';

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

const INTERNAL_CACHE_INVALIDATION_ROUTE = '/internal/cache/invalidate';

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

function getRequestId(req) {
  return getForwardedValue(req.headers['x-request-id']) || randomUUID();
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

function getBackendForwardHeaders(
  requestPublicEnv,
  acceptLanguage,
  requestOrigin,
  requestId
) {
  const headers = {
    Accept: 'application/json',
  };

  if (typeof acceptLanguage === 'string' && acceptLanguage.trim()) {
    headers['Accept-Language'] = acceptLanguage;
  }

  try {
    const publicSiteUrl = requestOrigin
      ? new URL(requestOrigin)
      : new URL(`https://${requestPublicEnv.SITE_DOMAIN}`);
    headers.Host = publicSiteUrl.host;
    headers['X-Forwarded-Host'] = publicSiteUrl.host;
    headers['X-Forwarded-Proto'] = publicSiteUrl.protocol.replace(':', '');
  } catch {
    // Ignore malformed public API URLs and fall back to transport defaults.
  }

  if (requestId) {
    headers['X-Request-ID'] = requestId;
  }

  return headers;
}

async function fetchBackendJson(req, backendPath, requestUrl, requestId) {
  const requestPublicEnv = getRequestPublicEnv(req);
  const requestOrigin = getRequestOrigin(req);
  const upstreamBaseUrl = getBackendBaseUrl(requestPublicEnv);
  const upstreamUrl = new URL(backendPath, upstreamBaseUrl);

  if (requestUrl?.search) {
    upstreamUrl.search = requestUrl.search;
  }

  const startedAt = Date.now();
  const response = await fetch(upstreamUrl, {
    headers: getBackendForwardHeaders(
      requestPublicEnv,
      req.headers['accept-language'],
      requestOrigin,
      requestId
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

function isAuthorizedInternalCacheRequest(req) {
  const expectedToken = process.env.SSR_CACHE_INVALIDATION_TOKEN || '';
  if (!expectedToken) {
    return true;
  }

  const authHeader = req.headers.authorization || '';
  return authHeader === `Bearer ${expectedToken}`;
}

async function handleInternalRequest(req, res, requestUrl, start, requestId) {
  if (requestUrl.pathname !== INTERNAL_CACHE_INVALIDATION_ROUTE) {
    return false;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, {
      'Content-Type': 'application/json; charset=utf-8',
      Allow: 'POST',
    });
    res.end(JSON.stringify({ message: 'Method not allowed.' }));
    logRequest(
      {
        kind: 'cache-invalidate',
        method: req.method,
        path: requestUrl.pathname,
        status: 405,
        duration_ms: Date.now() - start,
      },
      requestId
    );
    return true;
  }

  if (!isAuthorizedInternalCacheRequest(req)) {
    res.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ message: 'Unauthorized.' }));
    logRequest(
      {
        kind: 'cache-invalidate',
        method: req.method,
        path: requestUrl.pathname,
        status: 401,
        duration_ms: Date.now() - start,
      },
      requestId
    );
    return true;
  }

  const body = (await readJsonBody(req)) || {};
  const result = invalidateCacheTags(Array.isArray(body.tags) ? body.tags : []);

  res.writeHead(200, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(JSON.stringify(result));

  logRequest(
    {
      kind: 'cache-invalidate',
      method: req.method,
      path: requestUrl.pathname,
      status: 200,
      duration_ms: Date.now() - start,
      tags: result.tags,
      invalidated_keys: result.invalidatedKeys,
    },
    requestId
  );

  return true;
}

async function forwardBackendWrite(req, backendPath, requestId) {
  const requestPublicEnv = getRequestPublicEnv(req);
  const requestOrigin = getRequestOrigin(req);
  const upstreamBaseUrl = getBackendBaseUrl(requestPublicEnv);
  const upstreamUrl = new URL(backendPath, upstreamBaseUrl);
  const body = await readJsonBody(req);

  const startedAt = Date.now();
  const response = await fetch(upstreamUrl, {
    method: req.method,
    headers: {
      ...getBackendForwardHeaders(
        requestPublicEnv,
        req.headers['accept-language'],
        requestOrigin,
        requestId
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

async function handleBffRequest(req, res, requestUrl, start, requestId) {
  const resolvedView = resolveBffBackendPath(requestUrl.pathname, req.method);

  if (!resolvedView) {
    return false;
  }

  if (resolvedView.methodNotAllowed) {
    res.writeHead(405, {
      'Content-Type': 'application/json; charset=utf-8',
      Allow: resolvedView.allow,
    });
    res.end(JSON.stringify({ message: 'Method not allowed.' }));
    return true;
  }

  const backendFetch =
    req.method === 'POST'
      ? await forwardBackendWrite(req, resolvedView.backendPath, requestId)
      : await fetchBackendJson(
          req,
          resolvedView.backendPath,
          requestUrl,
          requestId
        );
  const { durationMs, payload, response, upstreamBaseUrl, upstreamUrl } =
    backendFetch;

  res.writeHead(response.status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(JSON.stringify(payload));

  logRequest(
    {
      kind: 'bff',
      method: req.method,
      path: requestUrl.pathname,
      query: requestUrl.search || '',
      status: response.status,
      duration_ms: Date.now() - start,
      upstream_duration_ms: durationMs,
      upstream_path: `${upstreamUrl.pathname}${upstreamUrl.search}`,
      upstream_base_url: upstreamBaseUrl,
    },
    requestId
  );

  return true;
}

function logRequest(info, requestId) {
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      service: 'frontend-ssr',
      request_id: requestId,
      ...info,
    })
  );
}

async function renderDocument(url, acceptLanguage, requestOrigin, requestId) {
  const [{ renderStream }, template] = await Promise.all([
    import(pathToFileURL(serverEntryPath).href),
    readFile(indexHtmlPath, 'utf8'),
  ]);
  const requestPublicEnv = resolvePublicEnv({
    ...publicEnv,
    SITE_DOMAIN: new URL(requestOrigin).host,
  });

  const { stream, helmetContext, dehydratedState, language, abort } =
    await renderStream(url, acceptLanguage, requestOrigin, requestId);
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

async function pipeDocument(
  req,
  res,
  requestUrl,
  start,
  url,
  acceptLanguage,
  requestId
) {
  const requestOrigin = getRequestOrigin(req);
  const { abort, language, stream, prefix, suffix } = await renderDocument(
    url,
    acceptLanguage,
    requestOrigin,
    requestId
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
      logRequest(
        {
          kind: 'document',
          method: req.method,
          path: requestUrl.pathname,
          query: requestUrl.search || '',
          host: req.headers.host || 'localhost',
          language: String(req.headers['accept-language'] || language),
          status: 200,
          duration_ms: Date.now() - start,
          streaming: true,
        },
        requestId
      );
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
  const requestId = getRequestId(req);
  res.setHeader('X-Request-ID', requestId);
  try {
    const host = req.headers.host || 'localhost';
    const requestUrl = new URL(req.url || '/', `http://${host}`);

    if (requestUrl.pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ status: 'ok' }));
      logRequest(
        {
          kind: 'health',
          method: req.method,
          path: requestUrl.pathname,
          status: 200,
          duration_ms: Date.now() - start,
        },
        requestId
      );
      return;
    }

    if (await handleInternalRequest(req, res, requestUrl, start, requestId)) {
      return;
    }

    if (await handleBffRequest(req, res, requestUrl, start, requestId)) {
      return;
    }

    if (await serveStatic(req, res)) {
      logRequest(
        {
          kind: 'static',
          method: req.method,
          path: requestUrl.pathname,
          status: 200,
          duration_ms: Date.now() - start,
        },
        requestId
      );
      return;
    }

    await pipeDocument(
      req,
      res,
      requestUrl,
      start,
      requestUrl.pathname + requestUrl.search,
      req.headers['accept-language'] || 'en',
      requestId
    );
  } catch (error) {
    console.error('[frontend-ssr] request failed', error);
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Internal Server Error');
    } else {
      res.destroy(error instanceof Error ? error : undefined);
    }
    logRequest(
      {
        kind: 'document',
        method: req.method,
        path: req.url || '/',
        status: 500,
        duration_ms: Date.now() - start,
        error: error instanceof Error ? error.message : String(error),
      },
      requestId
    );
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log(`[frontend-ssr] listening on 0.0.0.0:${port}`);
});
