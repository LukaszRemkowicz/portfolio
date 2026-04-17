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

import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { detectLanguage } from './detectLanguage.js';
import { pipeDocument } from './documentRender.js';
import { handleBffRequest } from './backendProxy.js';
import { handleInternalRequest } from './internalCacheRoute.js';
import { logError, logRequest, toErrorPayload } from './logging.js';
import { getRequestId } from './requestMeta.js';
import { serveStatic } from './staticAssets.js';

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

    if (await serveStatic(req, res, clientDistDir)) {
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
      requestId,
      {
        indexHtmlPath,
        serverEntryPath,
        useClientRenderOnly,
      }
    );
  } catch (error) {
    logError(
      {
        event: 'request_failed',
        path: req.url || '/',
        method: req.method,
        ...toErrorPayload(error),
      },
      requestId
    );
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
  logRequest({
    event: 'server_started',
    host: '0.0.0.0',
    port,
  });
});
