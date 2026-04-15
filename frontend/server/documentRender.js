import { readFile } from 'node:fs/promises';
import { PassThrough } from 'node:stream';
import { pathToFileURL } from 'node:url';
import {
  publicEnv,
  replacePublicEnvPlaceholders,
  resolvePublicEnv,
} from './publicEnv.js';
import { getRequestOrigin } from './requestMeta.js';
import { logRequest } from './logging.js';

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

async function renderDocument(
  url,
  acceptLanguage,
  requestOrigin,
  requestId,
  { indexHtmlPath, serverEntryPath, useClientRenderOnly }
) {
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
      statusCode: 200,
      stream,
      suffix: parts[1],
      prefix: `${parts[0]}<div id="root">`,
    };
  }

  const { renderStream } = await import(pathToFileURL(serverEntryPath).href);

  const {
    stream,
    helmetContext,
    dehydratedState,
    language,
    abort,
    statusCode,
  } = await renderStream(url, acceptLanguage, requestOrigin, requestId);
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
    statusCode,
    stream,
    suffix: parts[1].replace('</body>', `${dehydratedStateScript}</body>`),
    prefix: `${parts[0]}<div id="root">`,
  };
}

export async function pipeDocument(
  req,
  res,
  requestUrl,
  start,
  url,
  acceptLanguage,
  requestId,
  options
) {
  const requestOrigin = getRequestOrigin(req);
  const { abort, language, statusCode, stream, prefix, suffix } =
    await renderDocument(
      url,
      acceptLanguage,
      requestOrigin,
      requestId,
      options
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
          status: statusCode,
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

    res.writeHead(statusCode, {
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
