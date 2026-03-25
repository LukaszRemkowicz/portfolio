/**
 * Frontend SSR runtime server.
 *
 * This server is responsible for:
 *
 * - serving built frontend assets
 * - rendering SSR HTML documents
 * - exposing FE-owned transport endpoints for browser JSON flows
 * - forwarding internal requests to the backend
 * - injecting public environment values into the HTML shell
 * - handling internal SSR cache invalidation webhooks
 * - emitting structured request logs
 */

import { createReadStream, existsSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { PassThrough } from 'node:stream';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  publicEnv,
  replacePublicEnvPlaceholders,
  resolvePublicEnv,
} from './publicEnv.js';
import { invalidateCacheTags } from './ssrCache.js';
import {
  normalizeBffPayload,
  normalizePublicMediaUrl,
} from './mediaNormalization.js';
import { getFrontendTransportRoute } from './views/bff.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, '..');
const clientDistDir = path.join(appRoot, 'dist');
const serverEntryPath = path.join(appRoot, 'dist', 'server', 'entry-server.js');
const indexHtmlPath = path.join(clientDistDir, 'index.html');
const port = Number(process.env.PORT || process.env.FRONTEND_PORT || 8080);
const environment = (
  process.env.ENVIRONMENT ||
  process.env.VITE_ENVIRONMENT ||
  process.env.NODE_ENV ||
  'development'
).toLowerCase();
const useClientRenderOnly = ['development', 'dev', 'local'].includes(
  environment
);

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
 * Detect a supported language tag from an Accept-Language header or cookie.
 */
function detectLanguage(acceptLanguage) {
  if (!acceptLanguage) return 'en';

  const languages = acceptLanguage
    .split(',')
    .map(lang => lang.split(';')[0].trim().toLowerCase());

  for (const lang of languages) {
    if (lang.startsWith('pl')) return 'pl';
    if (lang.startsWith('en')) return 'en';
  }

  return 'en';
}

const INTERNAL_CACHE_INVALIDATION_ROUTE = '/internal/cache/invalidate';
const MAX_JSON_BODY_BYTES = 64 * 1024;

class RequestValidationError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.name = 'RequestValidationError';
    this.statusCode = statusCode;
  }
}

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
function isSafeStaticPath(pathname) {
  const decoded = decodeURIComponent(pathname);
  const resolved = path.resolve(clientDistDir, `.${decoded}`);
  return resolved.startsWith(clientDistDir) ? resolved : null;
}

/**
 * Serve a built static asset from the client dist directory.
 */
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

/**
 * Extract HTML head and attribute markup from the Helmet SSR context.
 */
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

/**
 * Inject SSR-produced attributes into the opening HTML or BODY tag.
 */
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

/**
 * Normalize forwarded header values into a single string.
 */
function getForwardedValue(value) {
  if (Array.isArray(value)) {
    return value[0] || '';
  }

  if (typeof value === 'string') {
    return value.split(',')[0]?.trim() || '';
  }

  return '';
}

/**
 * Reconstruct the public request origin from forwarded/request headers.
 */
function getRequestOrigin(req) {
  const forwardedProto = getForwardedValue(req.headers['x-forwarded-proto']);
  const forwardedHost = getForwardedValue(req.headers['x-forwarded-host']);
  const host =
    forwardedHost || getForwardedValue(req.headers.host) || 'localhost';
  const proto = forwardedProto || 'http';

  return `${proto}://${host}`;
}

/**
 * Reuse an incoming request ID or create a new one for this request.
 */
function getRequestId(req) {
  return getForwardedValue(req.headers['x-request-id']) || randomUUID();
}

/**
 * Escape serialized state for safe inline HTML embedding.
 */
function serializeStateForHtml(state) {
  return JSON.stringify(state)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

/**
 * Serialize the public env payload injected into the browser HTML shell.
 */
function serializePublicEnvForHtml(config) {
  return serializeStateForHtml({
    API_URL: config.API_URL,
    GA_TRACKING_ID: config.GA_TRACKING_ID,
    PROJECT_OWNER: config.PROJECT_OWNER,
    SITE_DOMAIN: config.SITE_DOMAIN,
  });
}

/**
 * Resolve the request-scoped public env used by SSR and HTML placeholder replacement.
 */
function getRequestPublicEnv(req) {
  const requestOrigin = getRequestOrigin(req);
  const requestUrl = new URL(requestOrigin);
  return resolvePublicEnv({
    ...publicEnv,
    SITE_DOMAIN: requestUrl.host,
  });
}

/**
 * Return the backend base URL used for internal server-side requests.
 */
function getBackendBaseUrl(requestPublicEnv) {
  return process.env.SSR_API_URL || requestPublicEnv.API_URL;
}

/**
 * Build backend request headers that preserve public host, language, and request correlation.
 *
 * @param {string|null} clientForwardedFor — The X-Forwarded-For value from the incoming
 *   nginx request. Forwarded to Django so DRF throttling operates on the real client IP
 *   rather than the frontend container's internal Docker IP.
 */
function getBackendForwardHeaders(
  requestPublicEnv,
  acceptLanguage,
  requestOrigin,
  requestId,
  cookieHeader = null,
  clientForwardedFor = null
) {
  const headers = {
    Accept: 'application/json',
  };

  const getCookie = (header, name) => {
    if (!header) return null;
    const cookies = header.split(';').map(c => c.trim());
    for (const cookie of cookies) {
      if (cookie.startsWith(`${name}=`)) {
        return cookie.substring(name.length + 1);
      }
    }
    return null;
  };

  const cookieLang = getCookie(cookieHeader, 'i18next');
  const forwardedLang = cookieLang || acceptLanguage;

  if (typeof forwardedLang === 'string' && forwardedLang.trim()) {
    headers['Accept-Language'] = forwardedLang;
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

  // Forward the real client IP so Django DRF throttling can rate-limit by the
  // original caller's address, not the frontend container's internal Docker IP.
  if (clientForwardedFor) {
    headers['X-Forwarded-For'] = clientForwardedFor;
  }

  return headers;
}

/**
 * Fetch and decode JSON payloads from the backend for FE-owned transport routes.
 */
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
      requestId,
      req.headers.cookie,
      req.headers['x-forwarded-for']
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

/**
 * Read and parse a JSON request body.
 */
async function readJsonBody(req) {
  const chunks = [];
  let totalBytes = 0;

  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    totalBytes += buffer.length;

    if (totalBytes > MAX_JSON_BODY_BYTES) {
      throw new RequestValidationError(
        413,
        `Request body exceeds ${MAX_JSON_BODY_BYTES} bytes.`
      );
    }

    chunks.push(buffer);
  }

  if (chunks.length === 0) {
    return null;
  }

  const rawBody = Buffer.concat(chunks).toString('utf8');

  try {
    return rawBody ? JSON.parse(rawBody) : null;
  } catch {
    throw new RequestValidationError(400, 'Malformed JSON request body.');
  }
}

function getHeaderValue(value) {
  if (Array.isArray(value)) {
    return value[0] || '';
  }

  return typeof value === 'string' ? value : '';
}

function assertJsonContentType(req) {
  const contentType = getHeaderValue(req.headers['content-type'])
    .split(';')[0]
    .trim()
    .toLowerCase();

  if (contentType !== 'application/json') {
    throw new RequestValidationError(
      415,
      'Unsupported Media Type. Expected application/json.'
    );
  }
}

function isAuthorizedInternalCacheRequest(req) {
  const expectedToken = process.env.SSR_CACHE_INVALIDATION_TOKEN || '';
  if (!expectedToken) {
    // Fail closed: if no token is configured this endpoint must be denied.
    // A missing token is a misconfiguration — log loudly so it is visible.
    console.error(
      '[frontend-ssr] SSR_CACHE_INVALIDATION_TOKEN is not set — rejecting cache invalidation request'
    );
    return false;
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

  let body;
  try {
    assertJsonContentType(req);
    body = (await readJsonBody(req)) || {};
  } catch (error) {
    if (error instanceof RequestValidationError) {
      res.writeHead(error.statusCode, {
        'Content-Type': 'application/json; charset=utf-8',
      });
      res.end(JSON.stringify({ message: error.message }));
      logRequest(
        {
          kind: 'cache-invalidate',
          method: req.method,
          path: requestUrl.pathname,
          status: error.statusCode,
          duration_ms: Date.now() - start,
          error: error.message,
        },
        requestId
      );
      return true;
    }
    throw error;
  }

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
  assertJsonContentType(req);

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
        requestId,
        req.headers.cookie,
        req.headers['x-forwarded-for']
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
    requestPublicEnv,
    response,
    upstreamBaseUrl,
    upstreamUrl,
  };
}

async function handleBffRequest(req, res, requestUrl, start, requestId) {
  const resolvedView = getFrontendTransportRoute(
    requestUrl.pathname,
    req.method
  );

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

  if (resolvedView.kind === 'image-file') {
    const requestPublicEnv = getRequestPublicEnv(req);
    const requestOrigin = getRequestOrigin(req);
    const upstreamBaseUrl = getBackendBaseUrl(requestPublicEnv);
    const upstreamUrl = new URL(resolvedView.backendPath, upstreamBaseUrl);
    const allowedParams = new URLSearchParams();
    for (const key of ['s', 'e']) {
      const value = requestUrl.searchParams.get(key);
      if (value) {
        allowedParams.set(key, value);
      }
    }
    upstreamUrl.search = allowedParams.toString();

    const startedAt = Date.now();
    const response = await fetch(upstreamUrl, {
      headers: getBackendForwardHeaders(
        requestPublicEnv,
        req.headers['accept-language'],
        requestOrigin,
        requestId,
        req.headers.cookie,
        req.headers['x-forwarded-for']
      ),
      redirect: 'manual',
    });
    const durationMs = Date.now() - startedAt;
    const body = Buffer.from(await response.arrayBuffer());
    const headers = {
      'Cache-Control':
        response.headers.get('cache-control') ||
        'private, no-cache, no-store, must-revalidate',
      'Content-Length': String(body.length),
      'Content-Type':
        response.headers.get('content-type') || 'application/octet-stream',
    };
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      headers['Content-Disposition'] = contentDisposition;
    }
    res.writeHead(response.status, headers);
    res.end(body);

    logRequest(
      {
        kind: 'bff-image',
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

  let backendFetch;
  try {
    backendFetch =
      req.method === 'POST'
        ? await forwardBackendWrite(req, resolvedView.backendPath, requestId)
        : await fetchBackendJson(
            req,
            resolvedView.backendPath,
            requestUrl,
            requestId
          );
  } catch (error) {
    if (error instanceof RequestValidationError) {
      res.writeHead(error.statusCode, {
        'Content-Type': 'application/json; charset=utf-8',
      });
      res.end(JSON.stringify({ message: error.message }));
      logRequest(
        {
          kind: 'bff',
          method: req.method,
          path: requestUrl.pathname,
          query: requestUrl.search || '',
          status: error.statusCode,
          duration_ms: Date.now() - start,
          error: error.message,
        },
        requestId
      );
      return true;
    }
    throw error;
  }

  const { durationMs, payload, response, upstreamBaseUrl, upstreamUrl } =
    backendFetch;
  const normalizedPayload = normalizeBffPayload(
    payload,
    resolvedView.kind,
    getRequestOrigin(req)
  );

  res.writeHead(response.status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(JSON.stringify(normalizedPayload));

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

function getTimestamp() {
  // Use en-CA as it provides YYYY-MM-DD which is a good base for ISO
  return new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    fractionalSecondDigits: 3,
  })
    .format(new Date())
    .replace(', ', 'T');
}

function logRequest(info, requestId) {
  console.log(
    JSON.stringify({
      ts: getTimestamp(),
      service: 'frontend-ssr',
      request_id: requestId,
      ...info,
    })
  );
}

async function renderDocument(url, acceptLanguage, requestOrigin, requestId) {
  const template = await readFile(indexHtmlPath, 'utf8');
  const requestPublicEnv = resolvePublicEnv({
    ...publicEnv,
    SITE_DOMAIN: new URL(requestOrigin).host,
  });

  if (useClientRenderOnly) {
    const publicEnvScript = `<script>window.__PUBLIC_ENV__ = ${serializePublicEnvForHtml(
      requestPublicEnv
    )};</script>`;
    const initialLanguageScript = `<script>window.__INITIAL_LANGUAGE__ = ${JSON.stringify(acceptLanguage)};</script>`;
    const rootMarker = '<div id="root"></div>';
    const processedTemplate = replacePublicEnvPlaceholders(
      template,
      requestPublicEnv
    ).replace('</head>', `${publicEnvScript}${initialLanguageScript}</head>`);
    const parts = processedTemplate.split(rootMarker);

    if (parts.length !== 2) {
      throw new Error('SSR template root marker not found exactly once.');
    }

    const stream = new PassThrough();
    stream.end('');

    return {
      abort: () => {},
      language: 'en',
      stream,
      suffix: parts[1],
      prefix: `${parts[0]}<div id="root">`,
    };
  }

  const { renderStream } = await import(pathToFileURL(serverEntryPath).href);

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
      'Cache-Control': 'private, no-cache, must-revalidate',
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

    function getCookie(cookieHeader, name) {
      if (!cookieHeader) return null;
      const cookies = cookieHeader.split(';').map(c => c.trim());
      for (const cookie of cookies) {
        if (cookie.startsWith(`${name}=`)) {
          return cookie.substring(name.length + 1);
        }
      }
      return null;
    }

    const cookieLang = getCookie(req.headers.cookie, 'i18next');
    const acceptLang = req.headers['accept-language'] || 'en';
    const finalLang = detectLanguage(cookieLang || acceptLang);

    await pipeDocument(
      req,
      res,
      requestUrl,
      start,
      requestUrl.pathname + requestUrl.search,
      finalLang,
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
