import { invalidateCacheTags } from './ssrCache.js';
import { logError, logRequest } from './logging.js';
import {
  assertJsonContentType,
  readJsonBody,
  RequestValidationError,
} from './requestValidation.js';

export const INTERNAL_CACHE_INVALIDATION_ROUTE = '/internal/cache/invalidate';

function isAuthorizedInternalCacheRequest(req) {
  const expectedToken = process.env.SSR_CACHE_INVALIDATION_TOKEN || '';
  if (!expectedToken) {
    logError({
      event: 'cache_invalidation_token_missing',
      path: INTERNAL_CACHE_INVALIDATION_ROUTE,
      method: req.method,
      message:
        'SSR_CACHE_INVALIDATION_TOKEN is not set — rejecting cache invalidation request',
    });
    return false;
  }

  const authHeader = req.headers.authorization || '';
  return authHeader === `Bearer ${expectedToken}`;
}

export async function handleInternalRequest(
  req,
  res,
  requestUrl,
  start,
  requestId
) {
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
