// Same algorithm as backend/common/utils/signing.py (HMAC-SHA256 hex of "{id}:{expiry}"),
// keyed by MEDIA_SIGNING_KEY instead of Django's SECRET_KEY.
const enc = new TextEncoder();

const hex = (buf: ArrayBuffer) =>
  [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

export async function sign(key: string, resourceId: string, timestamp: number): Promise<string> {
  const k = await crypto.subtle.importKey(
    "raw",
    enc.encode(key),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return hex(await crypto.subtle.sign("HMAC", k, enc.encode(`${resourceId}:${timestamp}`)));
}

export async function signedParams(
  key: string,
  resourceId: string,
  expirationSeconds: number,
  now = Math.floor(Date.now() / 1000),
): Promise<{ s: string; e: number }> {
  const e = now + expirationSeconds;
  return { s: await sign(key, resourceId, e), e };
}

/** Constant-time string compare (lengths are public). */
export function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function validateSigned(
  key: string,
  resourceId: string,
  signature: string,
  expiry: string,
  now = Math.floor(Date.now() / 1000),
): Promise<boolean> {
  if (!key || !/^\s*[+-]?\d+\s*$/.test(expiry)) return false;
  const timestamp = Number.parseInt(expiry, 10);
  if (timestamp < now) return false;
  return safeEqual(signature, await sign(key, resourceId, timestamp));
}
