// core/sitemaps.py + Django's sitemap template: GET /sitemap.xml (sections in urls.py order).
import { FALLBACK_URL_SLUG } from "./astrophotography.ts";
import { db } from "./db.ts";
import { dateSlug, drfDateTime } from "./format.ts";
import type { Ctx } from "./http.ts";
import { PAGE_SIZE } from "./pagination.ts";

type Entry = { path: string; lastmod: string | null; freq: string; priority: string };

/** Django autoescape. */
const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");

/** Epoch seconds -> `date:"Y-m-d"` in Europe/Warsaw; null stays null (element omitted). */
const day = (epoch: string | null) => epoch === null ? null : drfDateTime(epoch).slice(0, 10);

/** GET /sitemap.xml */
export async function sitemap(ctx: Ctx): Promise<Response> {
  const sql = db();
  const [flags, images, locs] = await Promise.all([
    sql<{ programming_enabled: boolean; shop_enabled: boolean }[]>`
      select programming_enabled, shop_enabled from core_landingpagesettings
      order by id desc limit 1`,
    sql<{ slug: string; updated: string }[]>`
      select slug, extract(epoch from updated_at)::text as updated
      from astrophotography_astroimage order by created_at desc`,
    sql<
      { country_slug: string; place_slug: string | null; lower: string | null; updated: string }[]
    >`select country_slug, place_slug, lower(adventure_date)::text as lower,
        extract(epoch from updated_at)::text as updated
      from astrophotography_mainpagelocation where is_active order by adventure_date desc`,
  ]);
  const f = flags[0];
  const latest = images.reduce<string | null>(
    (m, i) => m === null || Number(i.updated) > Number(m) ? i.updated : m,
    null,
  );
  const pages = Math.ceil(images.length / PAGE_SIZE);
  const entries: Entry[] = [
    ...["/", "/astrophotography", "/privacy", ...(f?.programming_enabled ? ["/programming"] : [])]
      .map((path) => ({ path, lastmod: null, freq: "daily", priority: "1.0" })),
    ...Array.from({ length: pages > 1 ? pages - 1 : 0 }, (_, i) => ({
      path: `/astrophotography?page=${i + 2}`,
      lastmod: day(latest),
      freq: "weekly",
      priority: "0.6",
    })),
    ...images.map((i) => ({
      path: `/astrophotography/${i.slug}`,
      lastmod: day(i.updated),
      freq: "weekly",
      priority: "0.8",
    })),
    ...(f?.shop_enabled ? [{ path: "/shop", lastmod: null, freq: "daily", priority: "0.8" }] : []),
    // shortcut: Django 500s on an active location without adventure_date; skip it here.
    ...locs.filter((l) => l.lower).map((l) => ({
      path: `/travel/${l.country_slug || FALLBACK_URL_SLUG}/${l.place_slug || FALLBACK_URL_SLUG}/${
        dateSlug(l.lower!)
      }`,
      lastmod: day(l.updated),
      freq: "monthly",
      priority: "0.7",
    })),
  ];
  const host = new URL(ctx.cfg.publicBaseUrl).host;
  const urls = entries.map((e) =>
    `<url><loc>${esc(`https://${host}${e.path}`)}</loc>${
      e.lastmod ? `<lastmod>${e.lastmod}</lastmod>` : ""
    }<changefreq>${e.freq}</changefreq><priority>${e.priority}</priority></url>`
  ).join("");
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
    `${urls}\n</urlset>\n`;
  return new Response(body, {
    headers: { "content-type": "application/xml", "cache-control": "max-age=43200" },
  });
}
