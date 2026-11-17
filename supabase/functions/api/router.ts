import * as astro from "./astrophotography.ts";
import { loadConfig, missingEnv } from "./config.ts";
import * as contact from "./contact.ts";
import * as core from "./core.ts";
import { type Ctx, detail, htmlError, json, makeCtx } from "./http.ts";
import * as shop from "./shop.ts";
import { safeEqual } from "./signing.ts";
import * as users from "./users.ts";

type Handler = (ctx: Ctx, ...args: string[]) => Response | Promise<Response>;

/** Header the FE Worker adds to every call; value is API_ORIGIN_SECRET. */
export const ORIGIN_SECRET_HEADER = "x-origin-secret";

const SLUG = "([-a-zA-Z0-9_]+)"; // Django <slug:...>
const LOOKUP = "([^/.]+)"; // DRF default lookup_value_regex

// Paths are the same as DRF serves them (FE paths: /v1/..., /image-urls/..., /image-files/...).
const ROUTES: [RegExp, Handler][] = [
  [/^\/health$/, core.health],
  [/^\/v1\/health$/, core.health],
  [/^\/v1\/settings\/$/, () => core.settings()],
  [/^\/v1\/profile\/$/, users.profile],
  [/^\/v1\/background\/$/, astro.background],
  [/^\/v1\/astroimages\/$/, astro.listImages],
  [/^\/v1\/astroimages\/latest\/$/, astro.latestImages],
  [new RegExp(`^/v1/astroimages/${LOOKUP}/$`), astro.imageDetail],
  [/^\/v1\/travel-highlights\/$/, astro.travelHighlights],
  [new RegExp(`^/v1/travel/${SLUG}/${SLUG}/${SLUG}/$`), astro.travelBySlugs],
  [/^\/v1\/tags\/$/, astro.tags],
  [/^\/v1\/categories\/$/, () => astro.categories()],
  [/^\/v1\/shop\/products\/$/, shop.products],
  [/^\/(?:image-urls|v1\/images)\/$/, astro.imageUrls],
  [new RegExp(`^/(?:image-urls|v1/images)/${SLUG}/$`), astro.imageUrl],
  [new RegExp(`^/(?:image-files|v1/images)/${SLUG}/serve/$`), astro.serveImage],
];

// Bad percent-encoding stays literal, so it is just an unknown slug (404) as in Django.
function safeDecode(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

export async function handler(req: Request): Promise<Response> {
  // shortcut: no rate limiting; add at Cloudflare or here before launch
  try {
    // Hidden API: only the FE Worker knows the secret (sent server-side, never by browsers).
    // Checked first, so callers without it learn nothing about the configuration.
    const expected = Deno.env.get("API_ORIGIN_SECRET");
    if (!expected) return detail("Service misconfigured.", 503);
    const secret = req.headers.get(ORIGIN_SECRET_HEADER) ?? "";
    if (!safeEqual(secret, expected)) return detail("Forbidden.", 403);
    const missing = missingEnv();
    if (missing.length) return json({ detail: "Service misconfigured.", missing }, 503);
    const ctx = makeCtx(req, loadConfig());
    const isContact = ctx.path === "/v1/contact/";
    if (isContact && req.method === "POST") return await contact.submit(req);
    if (isContact || (req.method !== "GET" && req.method !== "HEAD")) {
      return detail(`Method "${req.method}" not allowed.`, 405);
    }
    for (const [re, run] of ROUTES) {
      const m = re.exec(ctx.path);
      if (m) return await run(ctx, ...m.slice(1).map(safeDecode));
    }
    return ctx.path.startsWith("/v1/")
      ? detail(`Endpoint '${ctx.path}' not found.`, 404)
      : htmlError(404, "Not Found", "The requested resource was not found on this server.");
  } catch (err) {
    console.error(err);
    return json({ detail: "Server error." }, 500);
  }
}
