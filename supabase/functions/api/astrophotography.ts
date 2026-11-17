// astrophotography app: AstroImageViewSet, TagsView, MainPageBackgroundImageView,
// MainPageLocationViewSet, TravelHighlightsBySlugView, CelestialObjectCategoriesView,
// ImageURLViewSet and AstroImageSecureView.
import { db, type Frag } from "./db.ts";
import { adventureDate, dateSlug, drfDateTime, parseDateSlug, storyPreview } from "./format.ts";
import { type Ctx, detail, htmlError, json, qget } from "./http.ts";
import {
  activeLang,
  COUNTRY_BY_NAME,
  COUNTRY_CODES,
  countryName,
  DEFAULT_LANG,
  getTranslation,
  translateField,
  type TrRow,
} from "./i18n.ts";
import {
  isCountry,
  loadPlaces,
  loadTranslations,
  type Place,
  placeJson,
  tagJson,
} from "./loaders.ts";
import { loadVariants, variantPayload } from "./media.ts";
import { envelope, pageLink, pageSize, resolvePage } from "./pagination.ts";
import { r2 } from "./r2.ts";
import { signedParams, validateSigned } from "./signing.ts";

type Json = Record<string, unknown>;

const FALLBACK_URL_SLUG = "explore";
const CATEGORIES = [
  "Landscape",
  "Deep Sky",
  "Startrails",
  "Solar System",
  "Milky Way",
  "Northern Lights",
];

// Every operand is parenthesised so mixed and/or trees keep their meaning.
export const and = (parts: Frag[]) => parts.reduce((a, b) => db()`(${a}) and (${b})`, db()`true`);
export const or = (parts: Frag[]) => parts.reduce((a, b) => db()`(${a}) or (${b})`, db()`false`);
/** Django escapes LIKE wildcards for icontains. */
const likeTerm = (s: string) => `%${s.replace(/[\\%_]/g, (c) => "\\" + c)}%`;
const uuidRe = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;

// ---------------------------------------------------------------- images

type ImageRow = {
  id: string;
  slug: string;
  capture_date: string;
  celestial_object: string;
  created_epoch: string;
  zoom: boolean;
  astrobin_url: string;
  place_id: number | null;
};

const imageCols = () =>
  db()`a.id::text as id, a.slug, a.capture_date::text as capture_date, a.celestial_object,
    extract(epoch from a.created_at)::text as created_epoch, a.zoom, a.astrobin_url,
    a.place_id::int as place_id`;

/** AstroImageQuerySet.for_gallery: joins + where for the query params (duplicates included). */
export function galleryFilter(url: URL): { joins: Frag[]; where: Frag } {
  const sql = db();
  const get = (k: string) => qget(url, k) || null;
  const joins: Frag[] = [];
  const conds: Frag[] = [];

  const category = get("filter");
  if (category) conds.push(sql`a.celestial_object = ${category}`);

  const tag = get("tag");
  if (tag) {
    conds.push(sql`exists (
      select 1 from astrophotography_astroimage_tags it
      where it.astroimage_id = a.id and it.tag_id in (
        select master_id from astrophotography_tag_translation where slug = ${tag}))`);
  }

  const travel = get("travel");
  if (travel) {
    // Same row multiplication as DRF's join on place translations (one row per translation).
    joins.push(sql`left join astrophotography_place p1 on p1.id = a.place_id
      left join astrophotography_place_translation pt1 on pt1.master_id = p1.id`);
    const lower = travel.toLowerCase();
    let code = COUNTRY_CODES.get(lower) ?? COUNTRY_BY_NAME.get(lower);
    if (!code) {
      for (const [name, c] of COUNTRY_BY_NAME) {
        if (name.includes(lower)) {
          code = c;
          break;
        }
      }
    }
    const parts = [sql`upper(pt1.name) like upper(${likeTerm(travel)})`];
    if (code) parts.push(sql`p1.country = ${code}`);
    else parts.push(sql`upper(p1.country) like upper(${likeTerm(travel)})`);
    conds.push(or(parts));
  }

  const country = get("country");
  if (country) {
    const place = get("place");
    joins.push(sql`join astrophotography_place p2 on p2.id = a.place_id`);
    conds.push(sql`p2.country = ${country}`);
    if (place) {
      joins.push(sql`left join astrophotography_place_translation pt2 on pt2.master_id = p2.id`);
      conds.push(sql`upper(pt2.name) = upper(${place})`);
    }
  }
  return { joins, where: and(conds) };
}

const fromJoins = (joins: Frag[]) =>
  joins.reduce((a, b) => db()`${a} ${b}`, db()`astrophotography_astroimage a`);

async function loadImageTags(ids: string[]): Promise<Map<string, string[]>> {
  const rows = await db()<{ img: string; tag: string }[]>`
    select astroimage_id::text as img, tag_id::text as tag
    from astrophotography_astroimage_tags
    where astroimage_id::text = any(${ids}::text[]) order by id`;
  const out = new Map<string, string[]>();
  for (const r of rows) out.set(r.img, [...(out.get(r.img) ?? []), r.tag]);
  return out;
}

const EQUIPMENT = ["camera", "lens", "telescope", "tracker", "tripod"] as const;

async function loadEquipment(ids: string[]): Promise<Map<string, Record<string, string[]>>> {
  const sql = db();
  const out = new Map<string, Record<string, string[]>>();
  const perKind = await Promise.all(EQUIPMENT.map((kind) =>
    sql<{ img: string; model: string }[]>`
      select t.astroimage_id::text as img, e.model
      from ${sql("astrophotography_astroimage_" + kind)} t
      join ${sql("astrophotography_" + kind)} e on e.id = t.${sql(kind + "_id")}
      where t.astroimage_id::text = any(${ids}::text[]) order by t.id`
  ));
  for (const [i, kind] of EQUIPMENT.entries()) {
    for (const r of perKind[i]) {
      const entry = out.get(r.img) ?? {};
      entry[kind] = [...(entry[kind] ?? []), r.model];
      out.set(r.img, entry);
    }
  }
  return out;
}

/** AstroImageSerializer (list/card) or AstroImageDetailSerializer (detail) for the rows. */
async function serializeImages(
  rows: ImageRow[],
  ctx: Ctx,
  opts: { detail: boolean },
): Promise<Json[]> {
  if (!rows.length) return [];
  const ids = rows.map((r) => r.id);
  const trCols = ["name", "description", "exposure_details", "processing_details"];
  const [tr, places, imageTags, tagTr, variants, equipment] = await Promise.all([
    loadTranslations("astrophotography_astroimage_translation", ids, trCols),
    loadPlaces(rows.flatMap((r) => r.place_id ?? [])),
    loadImageTags(ids),
    loadTranslations(
      "astrophotography_tag_translation",
      db()`select tag_id from astrophotography_astroimage_tags
        where astroimage_id::text = any(${ids}::text[])`,
      ["name", "slug"],
    ),
    loadVariants("astrophotography", "astroimage", ids),
    opts.detail ? loadEquipment(ids) : Promise.resolve(new Map<string, Record<string, string[]>>()),
  ]);
  return rows.map((r) => {
    const rowsTr = tr.get(r.id) ?? [];
    const field = (f: string) => translateField(rowsTr, f, ctx.lang, ctx.active);
    const payload = variantPayload(
      variants.get(r.id) ?? [],
      "thumbnail",
      560,
      ctx.cfg.publicDomain,
    );
    const base: Json = {
      pk: r.id,
      slug: r.slug,
      name: field("name"),
      tags: (imageTags.get(r.id) ?? []).map((t) => tagJson(tagTr.get(t) ?? [], ctx)),
      place: placeJson(r.place_id === null ? undefined : places.get(r.place_id), ctx),
      capture_date: r.capture_date,
      celestial_object: r.celestial_object,
      created_at: drfDateTime(r.created_epoch),
      description: field("description"),
    };
    if (!opts.detail) return { ...base, ...payload };
    const eq = equipment.get(r.id) ?? {};
    return {
      ...base,
      process: r.zoom,
      camera: eq.camera ?? [],
      lens: eq.lens ?? [],
      telescope: eq.telescope ?? [],
      tracker: eq.tracker ?? [],
      tripod: eq.tripod ?? [],
      exposure_details: field("exposure_details"),
      processing_details: field("processing_details"),
      astrobin_url: r.astrobin_url,
      fallback_image: payload.fallback_image,
    };
  });
}

/** GET /v1/astroimages/ */
export async function listImages(ctx: Ctx): Promise<Response> {
  const sql = db();
  const { joins, where } = galleryFilter(ctx.url);
  const from = fromJoins(joins);
  const size = pageSize(qget(ctx.url, "limit"));
  const raw = qget(ctx.url, "page");
  const countQuery = () =>
    sql<{ count: number }[]>`select count(*)::int as count from ${from} where ${where}`;
  const pageRows = (page: number) =>
    sql<ImageRow[]>`
      select ${imageCols()} from ${from} where ${where}
      order by a.created_at desc, a.id desc limit ${size} offset ${(page - 1) * size}`;
  // A numeric page is known before the count, so both queries share one round trip.
  const guess = raw === "last" ? null : resolvePage(raw, Number.MAX_SAFE_INTEGER, size);
  if (raw !== "last" && guess === null) return detail("Invalid page.", 404);
  let count: number;
  let rows: ImageRow[];
  if (guess !== null) [[{ count }], rows] = await Promise.all([countQuery(), pageRows(guess)]);
  else {
    [{ count }] = await countQuery();
    rows = await pageRows(resolvePage(raw, count, size)!);
  }
  const page = resolvePage(raw, count, size);
  if (page === null) return detail("Invalid page.", 404);
  const results = await serializeImages(rows, ctx, { detail: false });
  return json(
    envelope(results, count, page, size, (p) => pageLink(ctx.base, ctx.path, ctx.url, p)),
  );
}

/** GET /v1/astroimages/latest/ */
export async function latestImages(ctx: Ctx): Promise<Response> {
  const { joins, where } = galleryFilter(ctx.url);
  const rows = await db()<ImageRow[]>`
    select ${imageCols()} from ${fromJoins(joins)} where ${where}
    order by a.created_at desc, a.capture_date desc limit 9`;
  return json(await serializeImages(rows, ctx, { detail: false }));
}

/** GET /v1/astroimages/<slug>/ (lookup is restricted by the same gallery filters, as in DRF) */
export async function imageDetail(ctx: Ctx, slug: string): Promise<Response> {
  const { joins, where } = galleryFilter(ctx.url);
  const rows = await db()<ImageRow[]>`
    select ${imageCols()} from ${fromJoins(joins)} where ${where} and a.slug = ${slug} limit 1`;
  if (!rows.length) return detail("No AstroImage matches the given query.", 404);
  return json((await serializeImages(rows, ctx, { detail: true }))[0]);
}

/** GET /v1/categories/ */
export const categories = () => json(CATEGORIES);

// ---------------------------------------------------------------- tags

/** GET /v1/tags/ (TagsView + Tag.objects.with_stats) */
export async function tags(ctx: Ctx): Promise<Response> {
  const sql = db();
  const category = qget(ctx.url, "filter") || null;
  const latest = (qget(ctx.url, "latest") ?? "false").toLowerCase() === "true";
  const scope = latest
    ? sql`and t.id in (select tag_id from core_landingpagesettings_latest_filters
        where landingpagesettings_id = (select max(id) from core_landingpagesettings))`
    : sql``;
  const rowsQuery = sql<{ id: string; count: number }[]>`
    select * from (
      select t.id::text as id, t.id as raw_id,
        (count(distinct a.id) filter (
          where ${category}::text is null or a.celestial_object = ${category}))::int as count
      from astrophotography_tag t
      join astrophotography_astroimage_tags it on it.tag_id = t.id
      join astrophotography_astroimage a on a.id = it.astroimage_id
      where true ${scope}
      group by t.id) s
    where count > 0 order by count desc, raw_id`;
  const [rows, tr] = await Promise.all([
    rowsQuery,
    loadTranslations("astrophotography_tag_translation", sql`select id from astrophotography_tag`, [
      "name",
      "slug",
    ]),
  ]);
  return json(
    rows.map((r) => ({ ...tagJson(tr.get(r.id) ?? [], ctx), count: r.count })),
  );
}

// ---------------------------------------------------------------- background

/** GET /v1/background/ */
export async function background(ctx: Ctx): Promise<Response> {
  const sql = db();
  const [rows, variants] = await Promise.all([
    sql<{ id: string }[]>`
      select id::text as id from astrophotography_mainpagebackgroundimage order by created_at desc`,
    loadVariants(
      "astrophotography",
      "mainpagebackgroundimage",
      sql`select id::text from astrophotography_mainpagebackgroundimage`,
    ),
  ]);
  for (const r of rows) {
    const payload = variantPayload(variants.get(r.id) ?? [], "hero", 2560, ctx.cfg.publicDomain);
    if (payload.fallback_image) return json(payload);
  }
  return json({ fallback_image: null, variants: { hero: [] } });
}

// ---------------------------------------------------------------- travel highlights

type Loc = {
  id: number;
  place_id: number | null;
  country_slug: string;
  place_slug: string | null;
  bg_id: string | null;
  lower: string | null;
  upper: string | null;
  created_epoch: string;
};

const locCols = () =>
  db()`m.id::int as id, m.place_id::int as place_id, m.country_slug, m.place_slug,
    m.background_image_id::text as bg_id, lower(m.adventure_date)::text as lower,
    upper(m.adventure_date)::text as upper,
    extract(epoch from m.created_at)::text as created_epoch`;

/** Place.image_scope: SQL condition on `a.place_id` for a destination (countries, nested regions). */
// Returns a wrapper: awaiting a bare postgres fragment would execute it.
async function imageScope(place: Place, visited = new Set<number>()): Promise<{ frag: Frag }> {
  const sql = db();
  if (visited.has(place.id)) return { frag: sql`false` };
  visited.add(place.id);
  const byCountry = sql`a.place_id in (select id from astrophotography_place where country = ${
    place.country ?? ""
  })`;
  if (isCountry(place)) return { frag: byCountry };
  if (place.is_region) {
    const subs = await sql<{ id: number }[]>`
      select to_place_id::int as id from astrophotography_place_sub_places
      where from_place_id = ${place.id}`;
    if (subs.length) {
      const children = await loadPlaces(subs.map((s) => s.id));
      const scopes = await Promise.all(subs.map((s) => {
        const child = children.get(s.id);
        return child ? imageScope(child, visited) : null;
      }));
      const parts = [sql`a.place_id = ${place.id}`];
      for (const s of scopes) if (s) parts.push(s.frag);
      return { frag: or(parts) };
    }
    if (place.country) return { frag: byCountry };
  }
  return { frag: sql`a.place_id = ${place.id}` };
}

/** AstroImage.objects.for_travel_highlight */
async function travelImages(loc: Loc, place: Place | undefined): Promise<ImageRow[]> {
  const sql = db();
  let scope: Frag;
  if (place) scope = (await imageScope(place)).frag;
  else {
    // Legacy country tours without a destination.
    const iso = COUNTRY_CODES.get(loc.country_slug) ?? COUNTRY_BY_NAME.get(loc.country_slug);
    scope = iso
      ? sql`a.place_id in (select id from astrophotography_place where country = ${iso})`
      : sql`false`;
  }
  const dates: Frag[] = [scope];
  if (loc.lower) dates.push(sql`a.capture_date >= ${loc.lower}::date`);
  if (loc.upper) dates.push(sql`a.capture_date < ${loc.upper}::date`);
  return await sql<ImageRow[]>`
    select ${imageCols()} from astrophotography_astroimage a
    where (${and(dates)}) or a.id in (
      select astroimage_id from astrophotography_mainpagelocation_images
      where mainpagelocation_id = ${loc.id})
    order by a.created_at desc`;
}

/** MainPageLocation.get_full_location */
function fullLocation(rows: TrRow[], place: Place | undefined, language: string): string {
  let name = getTranslation(rows, "highlight_name", language, { allowAny: false });
  if (!name) {
    if (language === DEFAULT_LANG && place) {
      name = translateField(place.tr, "name", null, "en") ?? "";
    } else return "";
  }
  const country = place?.country ? countryName(place.country, activeLang(language)) : "";
  return [...new Set([name, country].filter(Boolean))].join(", ");
}

type LocData = { tr: Map<string, TrRow[]>; bgVariants: Awaited<ReturnType<typeof loadVariants>> };

/** Translations and background variants of the locations (one round trip). */
async function loadLocationData(locs: Loc[]): Promise<LocData> {
  const [tr, bgVariants] = await Promise.all([
    loadTranslations(
      "astrophotography_mainpagelocation_translation",
      locs.map((l) => l.id),
      ["highlight_name", "highlight_title", "story"],
    ),
    loadVariants("astrophotography", "astroimage", locs.flatMap((l) => l.bg_id ?? [])),
  ]);
  return { tr, bgVariants };
}

/** MainPageLocationSerializer / TravelHighlightDetailSerializer fields; `images` are precomputed. */
function serializeLocations(
  locs: Loc[],
  places: Map<number, Place>,
  images: Map<number, Json[]>,
  { tr, bgVariants }: LocData,
  ctx: Ctx,
): Json[] {
  const language = ctx.lang || DEFAULT_LANG;
  return locs.map((loc) => {
    const rows = tr.get(String(loc.id)) ?? [];
    const place = loc.place_id === null ? undefined : places.get(loc.place_id);
    const t = (f: string) => getTranslation(rows, f, language, { allowAny: false });
    const bg = loc.bg_id
      ? variantPayload(bgVariants.get(loc.bg_id) ?? [], "detail", 1920, ctx.cfg.publicDomain)
        .fallback_image
      : null;
    return {
      pk: loc.id,
      place: placeJson(place, ctx),
      place_slug: loc.place_slug || FALLBACK_URL_SLUG,
      country_slug: loc.country_slug || FALLBACK_URL_SLUG,
      date_slug: dateSlug(loc.lower!),
      highlight_name: t("highlight_name"),
      highlight_title: t("highlight_title"),
      full_location: fullLocation(rows, place, language),
      story_preview: storyPreview(t("story")),
      adventure_date: adventureDate(loc.lower, loc.upper),
      story: t("story"),
      background_image: bg?.url ?? "",
      images: images.get(loc.id) ?? [],
      adventure_date_raw: loc.lower,
      created_at: drfDateTime(loc.created_epoch),
    };
  });
}

/** GET /v1/travel-highlights/ */
export async function travelHighlights(ctx: Ctx): Promise<Response> {
  const sql = db();
  const [locs, linked] = await Promise.all([
    sql<Loc[]>`
      select ${locCols()} from astrophotography_mainpagelocation m
      where m.is_active order by m.adventure_date desc`,
    sql<(ImageRow & { loc: number })[]>`
      select ${imageCols()}, mi.mainpagelocation_id::int as loc
      from astrophotography_mainpagelocation_images mi
      join astrophotography_astroimage a on a.id = mi.astroimage_id
      where mi.mainpagelocation_id in (
        select id from astrophotography_mainpagelocation where is_active)
      order by a.created_at desc`,
  ]);
  if (!locs.length) return json([]);
  const unique = [...new Map(linked.map((r) => [r.id, r])).values()];
  const [places, serialized, data] = await Promise.all([
    loadPlaces(locs.flatMap((l) => l.place_id ?? [])),
    serializeImages(unique, ctx, { detail: false }),
    loadLocationData(locs),
  ]);
  const byId = new Map(unique.map((r, i) => [r.id, serialized[i]]));
  const images = new Map<number, Json[]>();
  for (const r of linked) images.set(r.loc, [...(images.get(r.loc) ?? []), byId.get(r.id)!]);
  return json(serializeLocations(locs, places, images, data, ctx));
}

/** GET /v1/travel/<country>/<place>/<date>/ (MainPageLocationQuerySet.by_slugs + .get()) */
export async function travelBySlugs(
  ctx: Ctx,
  country: string,
  place: string,
  date: string,
): Promise<Response> {
  const sql = db();
  const notFound = () => detail("No highlight found for these parameters.", 404);
  const conds: Frag[] = [sql`m.is_active`];
  if (date !== FALLBACK_URL_SLUG) {
    const range = parseDateSlug(date);
    if (!range) return notFound();
    conds.push(sql`m.adventure_date && daterange(${range[0]}::date, ${range[1]}::date, '[)')`);
  }
  const base = and(conds);
  const placeCond = place === FALLBACK_URL_SLUG
    ? sql`(m.place_slug = '' or m.place_slug is null)`
    : sql`m.place_slug = ${place}`;
  const countryCond = country === FALLBACK_URL_SLUG ? "" : country;
  let locs = await sql<Loc[]>`
    select ${locCols()} from astrophotography_mainpagelocation m
    where ${base} and m.country_slug = ${countryCond} and ${placeCond} limit 2`;
  if (!locs.length) {
    locs = await sql<Loc[]>`
      select ${locCols()} from astrophotography_mainpagelocation m
      where ${base} and m.legacy_slugs @> ${JSON.stringify([{ country, place }])}::jsonb limit 2`;
  }
  if (locs.length !== 1) return notFound();
  const loc = locs[0];
  const dataPending = loadLocationData([loc]);
  dataPending.catch(() => {}); // awaited below; avoids an unhandled rejection meanwhile
  const places = await loadPlaces(loc.place_id === null ? [] : [loc.place_id]);
  const rows = await travelImages(
    loc,
    loc.place_id === null ? undefined : places.get(loc.place_id),
  );
  const [serialized, data] = await Promise.all([
    serializeImages(rows, ctx, { detail: false }),
    dataPending,
  ]);
  const images = new Map([[loc.id, serialized]]);
  return json(serializeLocations([loc], places, images, data, ctx)[0]);
}

// ---------------------------------------------------------------- signed media

const signedUrl = async (ctx: Ctx, slug: string) => {
  const { s, e } = await signedParams(ctx.cfg.signingKey, slug, ctx.cfg.signedExpiration);
  return `${ctx.base}/image-files/${slug}/serve/?s=${s}&e=${e}`;
};

/** GET /image-urls/?ids=<pk> */
export async function imageUrls(ctx: Ctx): Promise<Response> {
  const idsParam = qget(ctx.url, "ids");
  if (idsParam === null) return detail("Query parameter 'ids' is required.", 400);
  const ids = idsParam.split(",").map((x) => x.trim()).filter(Boolean);
  if (!ids.length) return detail("Query parameter 'ids' must include at least one image id.", 400);
  if (ids.length !== 1) {
    return detail("Query parameter 'ids' may include exactly one image id.", 400);
  }
  // DRF answers 500 for a malformed UUID; an unknown id maps to an empty object instead.
  if (!uuidRe.test(ids[0])) return json({});
  let rows: { id: string; slug: string }[];
  try {
    rows = await db()<{ id: string; slug: string }[]>`
      select id::text as id, slug from astrophotography_astroimage where id = ${ids[0]}::uuid`;
  } catch (err) {
    if ((err as { code?: string }).code === "22P02") return json({}); // uuid cast failed
    throw err;
  }
  const out: Record<string, string> = {};
  for (const r of rows) out[r.id] = await signedUrl(ctx, r.slug);
  return json(out);
}

/** GET /image-urls/<slug>/ */
export async function imageUrl(ctx: Ctx, slug: string): Promise<Response> {
  const rows = await db()<{ slug: string }[]>`
    select slug from astrophotography_astroimage where slug = ${slug}`;
  if (!rows.length) return detail("No AstroImage matches the given query.", 404);
  return json({ url: await signedUrl(ctx, slug) });
}

/** GET /image-files/<slug>/serve/: validate signature, 302 to a short-lived R2 presigned GET. */
export async function serveImage(ctx: Ctx, slug: string): Promise<Response> {
  const s = qget(ctx.url, "s");
  const e = qget(ctx.url, "e");
  if (!s || !e) return htmlError(403, "Forbidden", "Missing signature parameters.");
  if (!(await validateSigned(ctx.cfg.signingKey, slug, s, e))) {
    return htmlError(
      403,
      "Forbidden",
      "The link has expired or is invalid. Please refresh the page.",
    );
  }
  const rows = await db()<{ file: string }[]>`
    select v.file
    from astrophotography_astroimage a
    join core_imagevariant v on v.object_id = a.id::text
    join django_content_type ct on ct.id = v.content_type_id
      and ct.app_label = 'astrophotography' and ct.model = 'astroimage'
    where a.slug = ${slug} and v.role = 'high_resolution' and v.file <> ''
    order by v.role, v.width desc limit 1`;
  if (!rows.length) return htmlError(404, "Not Found", "File not found.");
  const location = await r2.presignGet(ctx.cfg.r2, rows[0].file);
  return new Response(null, {
    status: 302,
    headers: { location, "cache-control": "private, no-store, max-age=0" },
  });
}
