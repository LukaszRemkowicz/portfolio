// Contract check: same paths/params against the DRF baseline and the Edge Function, deep-compare.
//   BASELINE_URL (default http://localhost:8000)  FUNCTION_URL (default http://localhost:8001)
// Only the origin of API links (any host), the function base path and the `s`/`e` signature params are normalised.
// A random `cb` param is added to every request so DRF's 30-day DB response cache (which also
// stores absolute URLs) cannot answer; both sides receive the same value.
const BASELINE = Deno.env.get("BASELINE_URL") ?? "http://localhost:8000";
const FUNCTION = Deno.env.get("FUNCTION_URL") ?? "http://localhost:8001";
// Against the deployed function the Supabase gateway answers some cases itself: it rewrites
// text/html to text/plain and rejects malformed %-encoding with 400 before the function runs.
const DEPLOYED = new URL(FUNCTION).pathname.startsWith("/functions/v1/");
// Sent to both sides like the FE Worker does (DRF ignores it).
const SECRET = Deno.env.get("API_ORIGIN_SECRET") ?? "";
const cb = crypto.randomUUID().slice(0, 8);
const pause = () => new Promise((r) => setTimeout(r, 150));

type Json = unknown;

/** Normalise origin, function base path and signature params inside every string. */
export function normalize(v: Json): Json {
  if (typeof v === "string") {
    return v
      .replace(
        /https?:\/\/[\w.-]+(:\d+)?(\/functions\/v1\/api)?(?=\/(v1|image-files|image-urls)\/)/g,
        "<ORIGIN>",
      )
      .replace(/([?&])s=[0-9a-f]{64}&e=\d+/g, "$1s=<SIG>&e=<EXP>");
  }
  if (Array.isArray(v)) return v.map(normalize);
  if (v && typeof v === "object") {
    return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, normalize(x)]));
  }
  return v;
}

/** Deep compare; returns human-readable differences (path: baseline != function). */
export function diff(a: Json, b: Json, path = "$"): string[] {
  if (Object.is(a, b)) return [];
  const bothObj = a && b && typeof a === "object" && typeof b === "object";
  if (!bothObj || Array.isArray(a) !== Array.isArray(b)) {
    return [`${path}: ${short(a)} != ${short(b)}`];
  }
  const out: string[] = [];
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) out.push(`${path}: length ${a.length} != ${b.length}`);
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      out.push(...diff(a[i], b[i], `${path}[${i}]`));
    }
    return out;
  }
  const oa = a as Record<string, Json>;
  const ob = b as Record<string, Json>;
  for (const k of new Set([...Object.keys(oa), ...Object.keys(ob)])) {
    if (!(k in oa)) out.push(`${path}.${k}: missing in baseline`);
    else if (!(k in ob)) out.push(`${path}.${k}: missing in function`);
    else out.push(...diff(oa[k], ob[k], `${path}.${k}`));
  }
  return out;
}

const short = (v: Json) => {
  const s = JSON.stringify(v) ?? "undefined";
  return s.length > 90 ? s.slice(0, 90) + "..." : s;
};

const withCb = (path: string) => `${path}${path.includes("?") ? "&" : "?"}cb=${cb}`;

type Res = { status: number; type: string; body: Json; location: string; cache: string };

async function call(origin: string, path: string, prefix: string, raw = false): Promise<Res> {
  const res = await fetch(origin + prefix + (raw ? path : withCb(path)), {
    redirect: "manual",
    headers: { "x-origin-secret": SECRET },
  });
  const type = (res.headers.get("content-type") ?? "").split(";")[0];
  const text = await res.text();
  let body: Json = text.length > 0 ? "<non-json body>" : "";
  if (type === "application/json") body = JSON.parse(text);
  return {
    status: res.status,
    type,
    body,
    location: res.headers.get("location") ?? "",
    cache: res.headers.get("cache-control") ?? "",
  };
}

let pass = 0;
let fail = 0;
const failures: string[] = [];

async function check(name: string, path: string, opts: { prefix?: string } = {}) {
  const a = await call(BASELINE, path, "");
  await pause();
  const b = await call(FUNCTION, path, opts.prefix ?? "");
  const problems: string[] = [];
  if (a.status !== b.status) problems.push(`status ${a.status} != ${b.status}`);
  const gatewayPlain = DEPLOYED && a.type === "text/html" && b.type === "text/plain";
  if (a.type !== b.type && !gatewayPlain) problems.push(`content-type ${a.type} != ${b.type}`);
  if (a.status === b.status && a.type === "application/json") {
    problems.push(...diff(normalize(a.body), normalize(b.body)).slice(0, 6));
  }
  report(name, path, problems);
}

function report(name: string, path: string, problems: string[]) {
  if (problems.length === 0) {
    pass++;
    console.log(`PASS ${name}  ${path}`);
  } else {
    fail++;
    console.log(`FAIL ${name}  ${path}\n     ${problems.join("\n     ")}`);
    failures.push(name);
  }
}

/** Signed-link flow: link from each side, request it without following the redirect. */
async function checkServe(pk: string, slug: string) {
  const link = async (origin: string) => {
    const r = await call(origin, `/image-urls/?ids=${pk}`, "");
    const url = new URL((r.body as Record<string, string>)[pk]);
    // Links may carry the function base path or point at the site; request the logical path.
    const path = url.pathname.replace(/^\/functions\/v1\/api(?=\/)/, "");
    return call(origin, path + url.search, "", true);
  };
  const a = await link(BASELINE);
  await pause();
  const b = await link(FUNCTION);
  const p: string[] = [];
  if (a.status !== b.status) p.push(`status ${a.status} != ${b.status}`);
  if (a.cache !== b.cache) p.push(`cache-control "${a.cache}" != "${b.cache}"`);
  const where = (
    l: string,
  ) => (l ? new URL(l, "http://x").origin + new URL(l, "http://x").pathname : "");
  if (where(a.location) !== where(b.location)) {
    p.push(`location ${where(a.location)} != ${where(b.location)}`);
  }
  report("serve", `/image-files/${slug}/serve/ (signed)`, p);
}

type ListPage = { results: { slug: string; pk: string }[] };
type Highlight = { country_slug: string; place_slug: string; date_slug: string };

const get = async (path: string) => (await call(BASELINE, path, "")).body;
const langs = ["en", "pl"];
const q = (path: string, lang: string | null, extra = "") =>
  `${path}${path.includes("?") ? "&" : "?"}${
    [lang ? `lang=${lang}` : "", extra].filter(Boolean).join("&")
  }`
    .replace(/[?&]$/, "");

// ---- discover real slugs from the baseline
const list = (await get("/v1/astroimages/?limit=48")) as ListPage;
const slugs = list.results.map((r) => r.slug);
const tagList = (await get("/v1/tags/")) as { slug: string }[];
const highlights = (await get("/v1/travel-highlights/")) as Highlight[];
const first = list.results[0];

for (const lang of langs) {
  await check(`profile ${lang}`, q("/v1/profile/", lang));
  await check(`background ${lang}`, q("/v1/background/", lang));
  await check(`tags ${lang}`, q("/v1/tags/", lang));
  await check(`tags filter ${lang}`, q("/v1/tags/", lang, "filter=Landscape"));
  await check(`tags latest ${lang}`, q("/v1/tags/", lang, "latest=true"));
  await check(`tags latest+filter ${lang}`, q("/v1/tags/", lang, "latest=true&filter=Milky%20Way"));
  await check(`gallery p1 ${lang}`, q("/v1/astroimages/", lang, "limit=15&page=1"));
  await check(`gallery p2 limit2 ${lang}`, q("/v1/astroimages/", lang, "limit=2&page=2"));
  await check(`gallery p3 limit2 ${lang}`, q("/v1/astroimages/", lang, "limit=2&page=3"));
  await check(`gallery last ${lang}`, q("/v1/astroimages/", lang, "limit=20&page=last"));
  await check(`gallery filter ${lang}`, q("/v1/astroimages/", lang, "filter=Deep%20Sky&limit=15"));
  await check(
    `gallery tag ${lang}`,
    q("/v1/astroimages/", lang, `tag=${encodeURIComponent(tagList[0].slug)}&limit=15`),
  );
  await check(
    `gallery tag2 ${lang}`,
    q("/v1/astroimages/", lang, `tag=${encodeURIComponent(tagList[1].slug)}&filter=Landscape`),
  );
  await check(`gallery travel ${lang}`, q("/v1/astroimages/", lang, "travel=spain&limit=15"));
  await check(`gallery travel 2 ${lang}`, q("/v1/astroimages/", lang, "travel=zafra&limit=15"));
  await check(`latest ${lang}`, q("/v1/astroimages/latest/", lang));
  await check(`latest filter ${lang}`, q("/v1/astroimages/latest/", lang, "filter=Landscape"));
  for (const slug of slugs.slice(0, 3)) {
    await check(`detail ${slug} ${lang}`, q(`/v1/astroimages/${slug}/`, lang));
  }
  await check(`travel-highlights ${lang}`, q("/v1/travel-highlights/", lang));
  for (const h of highlights) {
    await check(
      `travel ${h.place_slug} ${lang}`,
      q(`/v1/travel/${h.country_slug}/${h.place_slug}/${h.date_slug}/`, lang),
    );
  }
  await check(
    `gallery travel+filter ${lang}`,
    q("/v1/astroimages/", lang, "travel=spain&filter=Landscape"),
  );
  await check(
    `gallery travel+country ${lang}`,
    q("/v1/astroimages/", lang, "travel=spain&country=ES"),
  );
  await check(
    `gallery travel+tag ${lang}`,
    q("/v1/astroimages/", lang, `travel=spain&tag=${encodeURIComponent(tagList[0].slug)}`),
  );
  await check(
    `detail with travel filter ${lang}`,
    q(
      `/v1/astroimages/${slugs[0]}/`,
      lang,
      `travel=${encodeURIComponent(highlights[0].place_slug)}`,
    ),
  );
}
// no `lang` (default language) and misc
await check("settings", "/v1/settings/");
await check("categories", "/v1/categories/");
await check("gallery default", "/v1/astroimages/?limit=3");
await check("profile default", "/v1/profile/");
await check("tags default", "/v1/tags/");
await check("travel-highlights default", "/v1/travel-highlights/");
await check("detail default", `/v1/astroimages/${slugs[1]}/`);
await check(
  "travel explore date",
  `/v1/travel/${highlights[0].country_slug}/${highlights[0].place_slug}/explore/`,
);
await check(
  "travel by legacy/other highlight",
  `/v1/travel/${highlights.at(-1)!.country_slug}/${highlights.at(-1)!.place_slug}/${
    highlights.at(-1)!.date_slug
  }/`,
);
// errors
await check("404 image", "/v1/astroimages/nope/");
await check("404 travel", "/v1/travel/spain/nothing/aug2026/");
await check("404 travel bad date", "/v1/travel/spain/nothing/zzz/");
await check("404 page", "/v1/astroimages/?page=999");
await check("empty page param", "/v1/astroimages/?page=&limit=3");
if (!DEPLOYED) await check("bad percent-encoding slug", "/v1/astroimages/%ZZ/");
await check("404 page abc", "/v1/astroimages/?page=abc");
await check("limit 0", "/v1/astroimages/?limit=0");
await check("limit 100", "/v1/astroimages/?limit=100");
await check("empty filter", "/v1/astroimages/?filter=Nothing");
await check("shop (disabled)", "/v1/shop/products/");
await check("v1 unknown", "/v1/nothing/");
await check("non-v1 unknown", "/nothing");
await check("health", "/health");
// XML: only status and content-type are compared (body data differs per backend).
await check("sitemap", "/sitemap.xml");
// signed media
await check("image-urls", `/image-urls/?ids=${first.pk}`);
await check("image-urls pl", `/image-urls/?ids=${first.pk}&lang=pl`);
await check("image-urls retrieve", `/image-urls/${first.slug}/`);
await check("image-urls retrieve 404", "/image-urls/nope/");
await check("image-urls missing ids", "/image-urls/");
await check("image-urls empty ids", "/image-urls/?ids=");
await check("image-urls two ids", "/image-urls/?ids=a,b");
await check("serve no signature", `/image-files/${first.slug}/serve/`);
await check("serve bad signature", `/image-files/${first.slug}/serve/?s=abc&e=99999999999`);
await check("serve expired", `/image-files/${first.slug}/serve/?s=${"0".repeat(64)}&e=1`);
await checkServe(first.pk, first.slug);
// function mounted under its deployed prefix (links must carry /functions/v1/api)
// The deployed URL already carries the runtime's `/api` prefix; only a local run must add it.
if (!DEPLOYED) {
  await check("prefix /api pagination", "/v1/astroimages/?limit=2&lang=en", { prefix: "/api" });
  await check("prefix /api image-urls", `/image-urls/?ids=${first.pk}`, { prefix: "/api" });
}

console.log(`\nSUMMARY: ${pass} PASS, ${fail} FAIL (${pass + fail} cases)`);
if (fail) {
  console.log(`Failed: ${failures.join("; ")}`);
  Deno.exit(1);
}
