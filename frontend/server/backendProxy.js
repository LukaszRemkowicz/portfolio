import { publicEnv, resolvePublicEnv } from './publicEnv.js';
import { normalizeBffPayload } from './mediaNormalization.js';
import { getRequestOrigin } from './requestMeta.js';
import {
  assertJsonContentType,
  readJsonBody,
  RequestValidationError,
} from './requestValidation.js';
import { logRequest } from './logging.js';
import { getFrontendTransportRoute } from './views/bff.js';

/**
 * Resolve the request-scoped public env used by SSR and backend forwarding.
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
    response,
    upstreamBaseUrl,
    upstreamUrl,
  };
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
    response,
    upstreamBaseUrl,
    upstreamUrl,
  };
}

export async function handleBffRequest(req, res, requestUrl, start, requestId) {
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
