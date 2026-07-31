import { logWarning } from './logging.js';

export const MAX_JSON_BODY_BYTES = 64 * 1024;

export class RequestValidationError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.name = 'RequestValidationError';
    this.statusCode = statusCode;
  }
}

export class MalformedRequestTargetError extends RequestValidationError {
  constructor() {
    super(400, 'Malformed request target.');
    this.name = 'MalformedRequestTargetError';
  }
}

/**
 * Reject invalid percent encoding before the request reaches URL parsing or
 * static-path decoding.
 */
export function assertValidRequestTarget(requestTarget) {
  try {
    decodeURI(requestTarget || '/');
  } catch {
    throw new MalformedRequestTargetError();
  }
}

/**
 * Return a compact client error for malformed request targets and record the
 * rejection without routing probe noise through the generic SSR error path.
 */
export function rejectMalformedRequestTarget(
  req,
  res,
  start,
  requestId,
  now = Date.now()
) {
  const requestTarget = req.url || '/';

  try {
    assertValidRequestTarget(requestTarget);
    return false;
  } catch (error) {
    if (!(error instanceof MalformedRequestTargetError)) {
      throw error;
    }
  }

  if (!res.headersSent) {
    res.writeHead(400, {
      'Content-Type': 'text/plain; charset=utf-8',
    });
    res.end('Bad Request');
  } else {
    res.destroy();
  }

  logWarning(
    {
      event: 'request_rejected',
      kind: 'security_probe',
      method: req.method,
      path: requestTarget.slice(0, 2048),
      reason: 'malformed_request_target',
      status: 400,
      duration_ms: now - start,
    },
    requestId
  );
  return true;
}

/**
 * Read and parse a JSON request body.
 */
export async function readJsonBody(req) {
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

export function assertJsonContentType(req) {
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
