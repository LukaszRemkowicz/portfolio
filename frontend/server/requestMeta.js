import { randomUUID } from 'node:crypto';

/**
 * Normalize forwarded header values into a single string.
 */
export function getForwardedValue(value) {
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
export function getRequestOrigin(req) {
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
export function getRequestId(req) {
  return getForwardedValue(req.headers['x-request-id']) || randomUUID();
}
