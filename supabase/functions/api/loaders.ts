// Shared read-only loaders for parler translation tables and places.
import { db, type Frag } from "./db.ts";
import type { Ctx } from "./http.ts";
import { countryName, getTranslation, translateField, type TrRow } from "./i18n.ts";

/**
 * Translation rows per master id (ordered by id, like parler's get_available_languages).
 * `ids` may be a subquery returning master ids, so the load needs no earlier round trip.
 */
export async function loadTranslations(
  table: string,
  ids: (string | number)[] | Frag,
  cols: string[],
): Promise<Map<string, TrRow[]>> {
  const out = new Map<string, TrRow[]>();
  if (Array.isArray(ids) && !ids.length) return out;
  const sql = db();
  // shortcut: master_id compared as text (tiny tables); add typed arrays if tables grow large.
  const which = Array.isArray(ids)
    ? sql`master_id::text = any(${ids.map(String)}::text[])`
    : sql`master_id in (${ids})`;
  const rows = await sql<(TrRow & { master: string })[]>`
    select master_id::text as master, language_code, ${sql(cols)}
    from ${sql(table)}
    where ${which}
    order by id`;
  for (const r of rows) {
    const list = out.get(r.master) ?? [];
    list.push(r);
    out.set(r.master, list);
  }
  return out;
}

export type Place = {
  id: number;
  country: string | null;
  is_region: boolean;
  tr: TrRow[];
};

export async function loadPlaces(ids: number[]): Promise<Map<number, Place>> {
  const out = new Map<number, Place>();
  const unique = [...new Set(ids)];
  if (!unique.length) return out;
  const [rows, tr] = await Promise.all([
    db()<{ id: number; country: string | null; is_region: boolean }[]>`
      select id::int as id, country, is_region from astrophotography_place
      where id::text = any(${unique.map(String)}::text[])`,
    loadTranslations("astrophotography_place_translation", unique, ["name"]),
  ]);
  for (const r of rows) out.set(r.id, { ...r, tr: tr.get(String(r.id)) ?? [] });
  return out;
}

/** Place.is_country: a country node has no source (default-language) name. */
export const isCountry = (p: Place) =>
  !!p.country && !p.is_region && !(p.tr.find((r) => r.language_code === "en")?.name ?? "");

/** PlaceSerializer.to_representation */
export function placeJson(p: Place | undefined, ctx: Ctx) {
  if (!p) return null;
  return {
    id: p.id,
    name: isCountry(p) ? "" : translateField(p.tr, "name", ctx.lang, ctx.active),
    country: countryName(p.country, ctx.active),
  };
}

/** TagSerializer name/slug (any-language fallback, request language). */
export const tagJson = (tr: TrRow[], ctx: Ctx) => ({
  name: getTranslation(tr, "name", ctx.lang ?? ""),
  slug: getTranslation(tr, "slug", ctx.lang ?? ""),
});
